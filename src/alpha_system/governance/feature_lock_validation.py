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


__all__ = [
    "FeatureLockResolution",
    "FeatureLockValidationError",
    "FeatureLockValidationReport",
    "extract_feature_version_ids",
    "validate_feature_locks",
]
