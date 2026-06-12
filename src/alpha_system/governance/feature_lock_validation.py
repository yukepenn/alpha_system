"""Fail-closed validation of feature_version_id locks against a feature registry.

This is a generic, minimal guard. Given a set of feature-pack locks (each a
mapping carrying a ``feature_version_id``), it asserts that every locked
``feature_version_id`` resolves in the sanctioned local feature registry and
returns a structured report. It raises fail-closed when any lock is stale
(unresolvable).

Because feature identity is content-addressed over the computational contract
only (see ``alpha_system.features.contracts.FeatureSpec.to_identity_dict``), a
lock's ``feature_version_id`` is reproducible and registry-state independent.
This guard therefore reliably detects locks that point at versions that were
never registered (or were registered before an identity-affecting change).

This module reads the registry read-only and never writes.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from alpha_system.core.value_store import (
    ValueStoreFormat,
    compute_value_content_hash,
    read_parquet_manifest,
)
from alpha_system.features.contracts import FEATURE_VERSION_PATTERN
from alpha_system.features.registry import FeatureRegistry


class FeatureLockValidationError(ValueError):
    """Raised when feature-lock validation fails closed."""


@dataclass(frozen=True, slots=True)
class FeatureLockResolution:
    """Resolution outcome for one locked feature_version_id."""

    feature_version_id: str
    resolved: bool
    feature_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "feature_version_id": self.feature_version_id,
            "resolved": self.resolved,
            "feature_id": self.feature_id,
        }


@dataclass(frozen=True, slots=True)
class FeatureLockValidationReport:
    """Structured report over a batch of feature-lock resolutions."""

    registry_path: str
    resolutions: tuple[FeatureLockResolution, ...]

    @property
    def stale_lock_ids(self) -> tuple[str, ...]:
        """Return the feature_version_ids that did not resolve in the registry."""

        return tuple(
            resolution.feature_version_id
            for resolution in self.resolutions
            if not resolution.resolved
        )

    @property
    def ok(self) -> bool:
        """Return whether every lock resolved in the sanctioned registry."""

        return not self.stale_lock_ids

    def to_dict(self) -> dict[str, Any]:
        return {
            "registry_path": self.registry_path,
            "lock_count": len(self.resolutions),
            "resolved_count": sum(1 for r in self.resolutions if r.resolved),
            "stale_lock_count": len(self.stale_lock_ids),
            "stale_lock_ids": list(self.stale_lock_ids),
            "ok": self.ok,
            "resolutions": [resolution.to_dict() for resolution in self.resolutions],
        }


@dataclass(frozen=True, slots=True)
class ValueStoreContentHashVerification:
    """Content-hash verification outcome for a registered value store."""

    pack_kind: str
    value_store_format: str
    path: str
    expected_content_hash: str
    actual_content_hash: str

    @property
    def ok(self) -> bool:
        """Return whether the registered hash matched the concrete value store."""

        return self.expected_content_hash == self.actual_content_hash

    def to_dict(self) -> dict[str, Any]:
        return {
            "pack_kind": self.pack_kind,
            "value_store_format": self.value_store_format,
            "path": self.path,
            "expected_content_hash": self.expected_content_hash,
            "actual_content_hash": self.actual_content_hash,
            "ok": self.ok,
        }


def extract_feature_version_ids(
    feature_pack_locks: Sequence[Mapping[str, Any] | str],
) -> tuple[str, ...]:
    """Extract feature_version_id values from a list of feature-pack locks.

    Each lock may be a mapping carrying a ``feature_version_id`` key, or a bare
    feature_version_id string. Invalid or missing ids fail closed.
    """

    if isinstance(feature_pack_locks, str) or not isinstance(feature_pack_locks, Sequence):
        raise FeatureLockValidationError("feature_pack_locks must be a sequence of locks")
    version_ids: list[str] = []
    for index, lock in enumerate(feature_pack_locks):
        if isinstance(lock, str):
            candidate: Any = lock
        elif isinstance(lock, Mapping):
            candidate = lock.get("feature_version_id")
        else:
            raise FeatureLockValidationError(
                f"feature_pack_locks[{index}] must be a mapping or a feature_version_id string"
            )
        if not isinstance(candidate, str) or not candidate.strip():
            raise FeatureLockValidationError(
                f"feature_pack_locks[{index}] is missing a feature_version_id"
            )
        version_id = candidate.strip()
        if FEATURE_VERSION_PATTERN.fullmatch(version_id) is None:
            raise FeatureLockValidationError(
                f"feature_pack_locks[{index}] feature_version_id is malformed: {version_id}"
            )
        version_ids.append(version_id)
    return tuple(version_ids)


def validate_feature_locks(
    feature_pack_locks: Sequence[Mapping[str, Any] | str],
    *,
    registry_path: str | Path,
) -> FeatureLockValidationReport:
    """Resolve every lock against the sanctioned feature registry, fail-closed.

    Returns a structured ``FeatureLockValidationReport``. Raises
    ``FeatureLockValidationError`` if any locked feature_version_id is stale
    (does not resolve in the registry), listing every stale lock id.
    """

    version_ids = extract_feature_version_ids(feature_pack_locks)
    registry = FeatureRegistry(registry_path)
    resolutions: list[FeatureLockResolution] = []
    for version_id in version_ids:
        record = registry.resolve_feature(version_id)
        if record is None:
            resolutions.append(
                FeatureLockResolution(feature_version_id=version_id, resolved=False)
            )
        else:
            resolutions.append(
                FeatureLockResolution(
                    feature_version_id=version_id,
                    resolved=True,
                    feature_id=record.feature_spec.feature_id,
                )
            )
    report = FeatureLockValidationReport(
        registry_path=str(Path(registry_path)),
        resolutions=tuple(resolutions),
    )
    if not report.ok:
        raise FeatureLockValidationError(
            "stale feature-pack lock(s) do not resolve in the sanctioned feature "
            "registry: " + ", ".join(report.stale_lock_ids)
        )
    return report


def verify_registered_value_store_content_hash(
    record: Any,
    *,
    pack_kind: str,
    version_id: str,
) -> ValueStoreContentHashVerification:
    """Fail closed unless a registry record's value-store hash matches storage.

    The helper intentionally uses the shared value-store primitives rather than
    reading manifests or hashing rows ad hoc.
    """

    expected_hash = _required_text(
        getattr(record, "value_content_hash", None),
        f"{pack_kind} registry value_content_hash",
    )
    value_format = ValueStoreFormat(
        _required_text(
            getattr(record, "value_store_format", None),
            f"{pack_kind} registry value_store_format",
        )
    )
    path, path_format = _value_store_path(
        record,
        value_format=value_format,
        pack_kind=pack_kind,
    )
    if path_format is ValueStoreFormat.PARQUET:
        actual_hash = _required_text(
            read_parquet_manifest(path).get("content_hash"),
            f"{pack_kind} parquet manifest content_hash",
        )
    else:
        actual_hash = compute_value_content_hash(_read_jsonl_mappings(path))

    verification = ValueStoreContentHashVerification(
        pack_kind=pack_kind,
        value_store_format=value_format.value,
        path=path.as_posix(),
        expected_content_hash=expected_hash,
        actual_content_hash=actual_hash,
    )
    if not verification.ok:
        raise FeatureLockValidationError(
            f"{pack_kind} value content hash mismatch for {version_id}: "
            f"path={verification.path} expected={verification.expected_content_hash} "
            f"actual={verification.actual_content_hash}"
        )
    return verification


def _value_store_path(
    record: Any,
    *,
    value_format: ValueStoreFormat,
    pack_kind: str,
) -> tuple[Path, ValueStoreFormat]:
    parquet_path = getattr(record, "parquet_path", None)
    if value_format in (ValueStoreFormat.PARQUET, ValueStoreFormat.DUAL) and parquet_path:
        return Path(str(parquet_path)).expanduser().resolve(strict=False), ValueStoreFormat.PARQUET
    jsonl_path = getattr(record, "materialization_output_path", None)
    if value_format in (ValueStoreFormat.JSONL, ValueStoreFormat.DUAL) and jsonl_path:
        return Path(str(jsonl_path)).expanduser().resolve(strict=False), ValueStoreFormat.JSONL
    raise FeatureLockValidationError(
        f"{pack_kind} registered value store is missing a usable path "
        f"for format {value_format.value}"
    )


def _read_jsonl_mappings(path: Path) -> list[dict[str, Any]]:
    import json

    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, Mapping):
            raise FeatureLockValidationError(
                f"JSONL value store row must be a mapping: path={path} line={line_number}"
            )
        rows.append(dict(value))
    return rows


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FeatureLockValidationError(f"{field_name} is required")
    return value.strip()


__all__ = [
    "FeatureLockResolution",
    "FeatureLockValidationError",
    "FeatureLockValidationReport",
    "ValueStoreContentHashVerification",
    "extract_feature_version_ids",
    "validate_feature_locks",
    "verify_registered_value_store_content_hash",
]
