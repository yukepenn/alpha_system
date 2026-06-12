"""Registry-aware guards for feature pack Parquet value stores."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from alpha_system.core.value_store import compute_value_content_hash, load_parquet_values
from alpha_system.features.registry import (
    FeatureRegistry,
    FeatureRegistryRecord,
    default_feature_registry_path,
)

PACK_AUDIT_CLEAN = "clean"
PACK_AUDIT_STALE_REGISTRY = "stale-registry"
PACK_AUDIT_BENIGN_EXTRA = "benign-extra"
_REMEDIATION = "deprecate first or run full-scope config"


class PackIntegrityError(ValueError):
    """Raised when a registered feature pack path is unsafe to rewrite or consume."""


@dataclass(frozen=True, slots=True)
class FeaturePackAuditEntry:
    """Value-free integrity result for one registered feature Parquet path."""

    parquet_path: str
    status: str
    registered_feature_count: int
    disk_feature_count: int
    missing_registered_feature_version_ids: tuple[str, ...] = ()
    extra_disk_feature_version_ids: tuple[str, ...] = ()
    hash_mismatch_feature_version_ids: tuple[str, ...] = ()
    read_error: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "parquet_path": self.parquet_path,
            "status": self.status,
            "registered_feature_count": self.registered_feature_count,
            "disk_feature_count": self.disk_feature_count,
            "missing_registered_feature_version_ids": list(
                self.missing_registered_feature_version_ids
            ),
            "extra_disk_feature_version_ids": list(self.extra_disk_feature_version_ids),
            "hash_mismatch_feature_version_ids": list(
                self.hash_mismatch_feature_version_ids
            ),
            "read_error": self.read_error,
        }


@dataclass(frozen=True, slots=True)
class FeaturePackAuditSummary:
    """Value-free integrity summary across registered feature pack paths."""

    entries: tuple[FeaturePackAuditEntry, ...]

    @property
    def total_path_count(self) -> int:
        return len(self.entries)

    @property
    def clean_count(self) -> int:
        return self._count_status(PACK_AUDIT_CLEAN)

    @property
    def stale_registry_count(self) -> int:
        return self._count_status(PACK_AUDIT_STALE_REGISTRY)

    @property
    def benign_extra_count(self) -> int:
        return self._count_status(PACK_AUDIT_BENIGN_EXTRA)

    def to_dict(self) -> dict[str, object]:
        return {
            "total_path_count": self.total_path_count,
            "clean_count": self.clean_count,
            "stale_registry_count": self.stale_registry_count,
            "benign_extra_count": self.benign_extra_count,
            "entries": [entry.to_dict() for entry in self.entries],
        }

    def _count_status(self, status: str) -> int:
        return sum(1 for entry in self.entries if entry.status == status)


def require_registered_feature_pack_superset(
    *,
    alpha_data_root: str | Path,
    parquet_path: str | Path,
    incoming_feature_version_ids: Sequence[str],
) -> None:
    """Fail unless an incoming pack contains all REGISTERED fvers for ``parquet_path``."""

    incoming = frozenset(
        _require_feature_version_id(value)
        for value in incoming_feature_version_ids
    )
    registered = registered_features_for_parquet_path(
        alpha_data_root=alpha_data_root,
        parquet_path=parquet_path,
    )
    missing = tuple(
        sorted(
            record.feature_version_id
            for record in registered
            if record.feature_version_id not in incoming
        )
    )
    if missing:
        path = _normalized_path(parquet_path)
        raise PackIntegrityError(
            "registered feature pack overwrite refused: "
            f"path={path}; missing_registered_feature_version_ids="
            f"{', '.join(missing)}; remediation={_REMEDIATION}"
        )


def reconcile_registered_feature_pack_path(
    *,
    alpha_data_root: str | Path,
    parquet_path: str | Path,
) -> None:
    """Assert all REGISTERED fvers for ``parquet_path`` exist on disk with matching hash."""

    registered = registered_features_for_parquet_path(
        alpha_data_root=alpha_data_root,
        parquet_path=parquet_path,
    )
    if not registered:
        return
    entry = audit_feature_pack_records(parquet_path=parquet_path, records=registered)
    if entry.status == PACK_AUDIT_STALE_REGISTRY:
        problems: list[str] = []
        if entry.missing_registered_feature_version_ids:
            problems.append(
                "missing_registered_feature_version_ids="
                + ", ".join(entry.missing_registered_feature_version_ids)
            )
        if entry.hash_mismatch_feature_version_ids:
            problems.append(
                "hash_mismatch_feature_version_ids="
                + ", ".join(entry.hash_mismatch_feature_version_ids)
            )
        if entry.read_error:
            problems.append(f"read_error={entry.read_error}")
        detail = "; ".join(problems) if problems else "registry-vs-disk mismatch"
        raise PackIntegrityError(
            "registered feature pack reconciliation failed: "
            f"path={entry.parquet_path}; {detail}"
        )


def audit_registered_feature_packs(
    *,
    alpha_data_root: str | Path,
) -> FeaturePackAuditSummary:
    """Sweep REGISTERED feature Parquet paths and report value-free mismatch classes."""

    registry = _feature_registry_if_present(alpha_data_root)
    if registry is None:
        return FeaturePackAuditSummary(entries=())
    grouped: dict[str, list[FeatureRegistryRecord]] = defaultdict(list)
    for record in registry.read_registered_parquet_features():
        if record.parquet_path:
            grouped[_normalized_path(record.parquet_path)].append(record)
    entries = tuple(
        audit_feature_pack_records(parquet_path=path, records=tuple(records))
        for path, records in sorted(grouped.items())
    )
    return FeaturePackAuditSummary(entries=entries)


def audit_feature_pack_records(
    *,
    parquet_path: str | Path,
    records: Sequence[FeatureRegistryRecord],
) -> FeaturePackAuditEntry:
    """Audit one parquet path against its REGISTERED feature records."""

    path = _normalized_path(parquet_path)
    registered_ids = frozenset(record.feature_version_id for record in records)
    try:
        disk_rows = load_parquet_values(path)
        disk_ids = frozenset(_feature_ids_from_rows(disk_rows))
        actual_hash = compute_value_content_hash(disk_rows)
    except Exception as exc:  # noqa: BLE001 - audit reports read failures as stale registry
        return FeaturePackAuditEntry(
            parquet_path=path,
            status=PACK_AUDIT_STALE_REGISTRY,
            registered_feature_count=len(registered_ids),
            disk_feature_count=0,
            missing_registered_feature_version_ids=tuple(sorted(registered_ids)),
            hash_mismatch_feature_version_ids=tuple(sorted(registered_ids)),
            read_error=str(exc),
        )

    missing = tuple(sorted(registered_ids - disk_ids))
    extra = tuple(sorted(disk_ids - registered_ids))
    hash_mismatches = tuple(
        sorted(
            record.feature_version_id
            for record in records
            if record.value_content_hash != actual_hash
        )
    )
    if missing or hash_mismatches:
        status = PACK_AUDIT_STALE_REGISTRY
    elif extra:
        status = PACK_AUDIT_BENIGN_EXTRA
    else:
        status = PACK_AUDIT_CLEAN
    return FeaturePackAuditEntry(
        parquet_path=path,
        status=status,
        registered_feature_count=len(registered_ids),
        disk_feature_count=len(disk_ids),
        missing_registered_feature_version_ids=missing,
        extra_disk_feature_version_ids=extra,
        hash_mismatch_feature_version_ids=hash_mismatches,
    )


def registered_features_for_parquet_path(
    *,
    alpha_data_root: str | Path,
    parquet_path: str | Path,
) -> tuple[FeatureRegistryRecord, ...]:
    registry = _feature_registry_if_present(alpha_data_root)
    if registry is None:
        return ()
    return registry.resolve_registered_features_by_parquet_path(parquet_path)


def _feature_registry_if_present(alpha_data_root: str | Path) -> FeatureRegistry | None:
    registry_path = default_feature_registry_path(alpha_data_root=alpha_data_root)
    if not registry_path.exists():
        return None
    return FeatureRegistry(registry_path)


def _feature_ids_from_rows(rows: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    ids: list[str] = []
    for row in rows:
        value = row.get("feature_version_id")
        ids.append(_require_feature_version_id(value))
    return tuple(ids)


def _require_feature_version_id(value: object) -> str:
    if not isinstance(value, str) or not value.startswith("fver_"):
        raise PackIntegrityError("feature value row is missing feature_version_id")
    return value


def _normalized_path(value: str | Path) -> str:
    return Path(value).expanduser().resolve(strict=False).as_posix()


__all__ = [
    "PACK_AUDIT_BENIGN_EXTRA",
    "PACK_AUDIT_CLEAN",
    "PACK_AUDIT_STALE_REGISTRY",
    "FeaturePackAuditEntry",
    "FeaturePackAuditSummary",
    "PackIntegrityError",
    "audit_feature_pack_records",
    "audit_registered_feature_packs",
    "reconcile_registered_feature_pack_path",
    "registered_features_for_parquet_path",
    "require_registered_feature_pack_superset",
]
