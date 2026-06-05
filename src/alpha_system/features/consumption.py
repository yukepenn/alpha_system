"""Accepted DatasetVersion consumption surface for feature and label code.

This module is intentionally thin. It resolves one DatasetVersion from the
foundation registry, validates the supplied acceptance evidence, gates partition
use, and reconstructs canonical records from mappings. It does not read data
files, call providers, or materialize feature or label values.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from alpha_system.data.foundation.bars import CanonicalBarRecord
from alpha_system.data.foundation.datasets import (
    DATASET_VERSION_ADMISSIBLE_STATES,
    CoverageReport,
    DataQualityReport,
    DatasetPartitionPlan,
    DatasetVersion,
    require_governance_metadata_for_locked_partition_use,
)
from alpha_system.data.foundation.grid import DenseGridBarRecord
from alpha_system.data.foundation.quotes import CanonicalBBORecord
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.data.foundation.version_registry import resolve_dataset_version

ACCEPTED_DATASET_VERSION_STATES: frozenset[str] = frozenset(
    DATASET_VERSION_ADMISSIBLE_STATES
)


@dataclass(frozen=True, slots=True)
class AcceptedDatasetVersion:
    """Validated handle for one accepted DatasetVersion.

    The handle represents exactly one DatasetVersion provenance line. Callers
    that need multiple inputs must resolve them independently and keep their ids
    distinct.
    """

    registry_path: str | Path
    dataset_version: DatasetVersion
    lifecycle_state: str
    quality_report: DataQualityReport
    coverage_report: CoverageReport

    @property
    def dataset_version_id(self) -> str:
        """Return the accepted DatasetVersion id."""

        return self.dataset_version.dataset_version_id

    @property
    def source(self) -> str:
        """Return the DatasetVersion source id."""

        return self.dataset_version.source

    def require_partition_access(
        self,
        *,
        partition_id: object,
        purpose: object,
        governance_metadata: Mapping[str, object] | None = None,
        partition_plan: DatasetPartitionPlan | None = None,
    ) -> bool:
        """Apply the canonical locked-partition gate for this consumption use."""

        return require_partition_access(
            partition_id=partition_id,
            purpose=purpose,
            governance_metadata=governance_metadata,
            partition_plan=partition_plan,
        )

    def canonical_bars_from_mappings(
        self,
        rows: Iterable[Mapping[str, object]],
        *,
        partition_id: object,
        purpose: object,
        governance_metadata: Mapping[str, object] | None = None,
        partition_plan: DatasetPartitionPlan | None = None,
    ) -> tuple[CanonicalBarRecord, ...]:
        """Reconstruct canonical OHLCV records for this accepted version."""

        return canonical_bars_from_mappings(
            self,
            rows,
            partition_id=partition_id,
            purpose=purpose,
            governance_metadata=governance_metadata,
            partition_plan=partition_plan,
        )

    def canonical_bbos_from_mappings(
        self,
        rows: Iterable[Mapping[str, object]],
        *,
        partition_id: object,
        purpose: object,
        governance_metadata: Mapping[str, object] | None = None,
        partition_plan: DatasetPartitionPlan | None = None,
    ) -> tuple[CanonicalBBORecord, ...]:
        """Reconstruct canonical BBO records for this accepted version."""

        return canonical_bbos_from_mappings(
            self,
            rows,
            partition_id=partition_id,
            purpose=purpose,
            governance_metadata=governance_metadata,
            partition_plan=partition_plan,
        )

    def dense_grid_bars_from_mappings(
        self,
        rows: Iterable[Mapping[str, object]],
        *,
        partition_id: object,
        purpose: object,
        governance_metadata: Mapping[str, object] | None = None,
        partition_plan: DatasetPartitionPlan | None = None,
    ) -> tuple[DenseGridBarRecord, ...]:
        """Reconstruct dense-grid OHLCV records for this accepted version."""

        return dense_grid_bars_from_mappings(
            self,
            rows,
            partition_id=partition_id,
            purpose=purpose,
            governance_metadata=governance_metadata,
            partition_plan=partition_plan,
        )


def resolve_accepted_dataset_version(
    registry_path: str | Path,
    dataset_version_id: object,
    *,
    lifecycle_state: object,
    quality_report: DataQualityReport,
    coverage_report: CoverageReport,
    source_manifest: object,
    code_hash: object,
    config_hash: object,
) -> AcceptedDatasetVersion:
    """Resolve and validate one accepted DatasetVersion from the registry.

    Missing registry records, non-admissible lifecycle states, blocking quality,
    blocking coverage, or mismatched reproducibility evidence all raise
    ``DataFoundationValidationError``.
    """

    dataset_version = resolve_dataset_version(registry_path, dataset_version_id)
    if dataset_version is None:
        msg = "DatasetVersion not found or not admissible for feature/label consumption"
        raise DataFoundationValidationError(msg)

    state = _normalize_lifecycle_state(lifecycle_state)
    dataset_version.require_lifecycle_prerequisites(
        state,
        quality_report=quality_report,
        coverage_report=coverage_report,
        source_manifest=source_manifest,
        code_hash=code_hash,
        config_hash=config_hash,
    )
    return AcceptedDatasetVersion(
        registry_path=registry_path,
        dataset_version=dataset_version,
        lifecycle_state=state,
        quality_report=quality_report,
        coverage_report=coverage_report,
    )


def require_partition_access(
    *,
    partition_id: object,
    purpose: object,
    governance_metadata: Mapping[str, object] | None = None,
    partition_plan: DatasetPartitionPlan | None = None,
) -> bool:
    """Route partition use through the data-foundation governance metadata gate."""

    return require_governance_metadata_for_locked_partition_use(
        partition_id=partition_id,
        purpose=purpose,
        governance_metadata=governance_metadata,
        plan=partition_plan,
    )


def canonical_bars_from_mappings(
    accepted_version: AcceptedDatasetVersion,
    rows: Iterable[Mapping[str, object]],
    *,
    partition_id: object,
    purpose: object,
    governance_metadata: Mapping[str, object] | None = None,
    partition_plan: DatasetPartitionPlan | None = None,
) -> tuple[CanonicalBarRecord, ...]:
    """Reconstruct canonical OHLCV records only after version and partition gates."""

    accepted = _require_accepted_version(accepted_version)
    accepted.require_partition_access(
        partition_id=partition_id,
        purpose=purpose,
        governance_metadata=governance_metadata,
        partition_plan=partition_plan,
    )
    records = tuple(
        CanonicalBarRecord.from_mapping(_require_mapping(row, "CanonicalBarRecord"))
        for row in rows
    )
    for record in records:
        _require_record_data_version(record.data_version, accepted)
    return records


def canonical_bbos_from_mappings(
    accepted_version: AcceptedDatasetVersion,
    rows: Iterable[Mapping[str, object]],
    *,
    partition_id: object,
    purpose: object,
    governance_metadata: Mapping[str, object] | None = None,
    partition_plan: DatasetPartitionPlan | None = None,
) -> tuple[CanonicalBBORecord, ...]:
    """Reconstruct canonical BBO records only after version and partition gates."""

    accepted = _require_accepted_version(accepted_version)
    accepted.require_partition_access(
        partition_id=partition_id,
        purpose=purpose,
        governance_metadata=governance_metadata,
        partition_plan=partition_plan,
    )
    records = tuple(
        CanonicalBBORecord.from_mapping(_require_mapping(row, "CanonicalBBORecord"))
        for row in rows
    )
    for record in records:
        _require_record_data_version(record.data_version, accepted)
    return records


def dense_grid_bars_from_mappings(
    accepted_version: AcceptedDatasetVersion,
    rows: Iterable[Mapping[str, object]],
    *,
    partition_id: object,
    purpose: object,
    governance_metadata: Mapping[str, object] | None = None,
    partition_plan: DatasetPartitionPlan | None = None,
) -> tuple[DenseGridBarRecord, ...]:
    """Reconstruct dense-grid OHLCV records only after version and partition gates."""

    accepted = _require_accepted_version(accepted_version)
    accepted.require_partition_access(
        partition_id=partition_id,
        purpose=purpose,
        governance_metadata=governance_metadata,
        partition_plan=partition_plan,
    )
    records = tuple(
        DenseGridBarRecord.from_mapping(_require_mapping(row, "DenseGridBarRecord"))
        for row in rows
    )
    for record in records:
        _require_record_data_version(record.data_version, accepted)
    return records


def _normalize_lifecycle_state(value: object) -> str:
    if not isinstance(value, str):
        msg = "DatasetVersion lifecycle_state must be a non-empty string"
        raise DataFoundationValidationError(msg)
    state = value.strip().upper()
    if not state:
        msg = "DatasetVersion lifecycle_state must be a non-empty string"
        raise DataFoundationValidationError(msg)
    if state not in ACCEPTED_DATASET_VERSION_STATES:
        allowed = ", ".join(sorted(ACCEPTED_DATASET_VERSION_STATES))
        msg = f"DatasetVersion lifecycle_state must be one of {allowed}"
        raise DataFoundationValidationError(msg)
    return state


def _require_accepted_version(value: object) -> AcceptedDatasetVersion:
    if not isinstance(value, AcceptedDatasetVersion):
        msg = "canonical record consumption requires an AcceptedDatasetVersion handle"
        raise DataFoundationValidationError(msg)
    return value


def _require_mapping(value: object, record_name: str) -> Mapping[str, object]:
    if isinstance(value, str) or not isinstance(value, Mapping):
        msg = f"{record_name} rows must be canonical mappings"
        raise DataFoundationValidationError(msg)
    return value


def _require_record_data_version(
    record_data_version: object,
    accepted_version: AcceptedDatasetVersion,
) -> None:
    if record_data_version != accepted_version.dataset_version_id:
        msg = "canonical record data_version must match the accepted DatasetVersion"
        raise DataFoundationValidationError(msg)


__all__ = [
    "ACCEPTED_DATASET_VERSION_STATES",
    "AcceptedDatasetVersion",
    "canonical_bars_from_mappings",
    "canonical_bbos_from_mappings",
    "dense_grid_bars_from_mappings",
    "require_partition_access",
    "resolve_accepted_dataset_version",
]
