"""Feature quality and coverage reports for registered local feature values.

The reports in this module consume FLF-P14 registry records and locally
materialized FLF-P13 feature values (JSONL audit/small tier or the research-scale
Parquet value store, resolved through the registry handle). They do not
materialize features, read raw provider files, or call external providers.
"""

from __future__ import annotations

import json
import math
import os
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from alpha_system.core import value_store as value_store_module
from alpha_system.core.value_store import DataDependencyError
from alpha_system.features.contracts import FrozenJsonMapping
from alpha_system.features.registry import FeatureRegistry, FeatureRegistryRecord
from alpha_system.features.request_gate import EquivalentFeatureGroup
from alpha_system.governance.serialization import JsonValue, canonical_serialize

MISSING_BBO_TOKEN = "missing_bbo"
BBO_QUARANTINED_TOKEN = "bbo_quarantined"
UNKNOWN_SESSION = "UNKNOWN_SESSION"
UNKNOWN_SYMBOL = "UNKNOWN_SYMBOL"


class FeatureReportError(ValueError):
    """Raised when feature report inputs are not registry/report objects."""


class FeatureReportSeverity(StrEnum):
    """Machine-readable report status partition."""

    BLOCKING = "blocking"
    NON_BLOCKING = "non_blocking"


class FeaturePartitionRole(StrEnum):
    """Supported feature coverage partition semantics."""

    DEVELOPMENT = "development"
    VALIDATION = "validation"
    LOCKED_TEST_CANDIDATE = "locked_test_candidate"
    UNCLASSIFIED = "unclassified"


@dataclass(frozen=True, slots=True)
class FeatureReportFinding:
    """One machine-readable quality or coverage finding."""

    code: str
    severity: FeatureReportSeverity | str
    message: str
    detail: Mapping[str, Any] | FrozenJsonMapping = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", _require_text(self.code, "code"))
        object.__setattr__(
            self,
            "severity",
            _coerce_severity(self.severity, "severity"),
        )
        object.__setattr__(self, "message", _require_text(self.message, "message"))
        object.__setattr__(
            self,
            "detail",
            _freeze_mapping(self.detail, "detail"),
        )

    @property
    def is_blocking(self) -> bool:
        """Return whether the finding belongs to the blocking partition."""

        return self.severity is FeatureReportSeverity.BLOCKING

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a stable JSON-compatible finding payload."""

        return {
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
            "detail": self.detail.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class CoverageBucket:
    """Observed count and timestamp span for one coverage dimension value."""

    key: str
    count: int
    first_event_ts: datetime | None = None
    last_event_ts: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "key", _require_text(self.key, "key"))
        object.__setattr__(self, "count", _require_nonnegative_int(self.count, "count"))
        if self.first_event_ts is not None:
            object.__setattr__(
                self,
                "first_event_ts",
                _require_aware_datetime(self.first_event_ts, "first_event_ts"),
            )
        if self.last_event_ts is not None:
            object.__setattr__(
                self,
                "last_event_ts",
                _require_aware_datetime(self.last_event_ts, "last_event_ts"),
            )
        if (
            self.first_event_ts is not None
            and self.last_event_ts is not None
            and self.first_event_ts > self.last_event_ts
        ):
            raise FeatureReportError("CoverageBucket first_event_ts must not follow last_event_ts")

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a stable JSON-compatible bucket payload."""

        return {
            "key": self.key,
            "count": self.count,
            "first_event_ts": self.first_event_ts.isoformat()
            if self.first_event_ts is not None
            else None,
            "last_event_ts": self.last_event_ts.isoformat()
            if self.last_event_ts is not None
            else None,
        }


@dataclass(frozen=True, slots=True)
class FeatureQualityReport:
    """Descriptive quality evidence for one registered feature version."""

    feature_id: str
    feature_version_id: str
    feature_request_id: str
    dataset_version_id: str
    partition_id: str
    materialization_output_path: str
    record_count: int
    valid_value_record_count: int
    nan_record_count: int
    nan_rate: float
    constant_feature: bool
    distinct_observed_values: int
    missing_bbo_count: int
    bbo_quarantined_count: int
    available_ts_missing_count: int
    available_ts_invalid_count: int
    available_ts_before_event_count: int
    duplicate_exposure_status: str
    equivalent_feature_groups: tuple[EquivalentFeatureGroup, ...] = ()
    blocking: tuple[FeatureReportFinding, ...] = ()
    non_blocking: tuple[FeatureReportFinding, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "feature_id", _require_text(self.feature_id, "feature_id"))
        object.__setattr__(
            self,
            "feature_version_id",
            _require_text(self.feature_version_id, "feature_version_id"),
        )
        object.__setattr__(
            self,
            "feature_request_id",
            _require_text(self.feature_request_id, "feature_request_id"),
        )
        object.__setattr__(
            self,
            "dataset_version_id",
            _require_text(self.dataset_version_id, "dataset_version_id"),
        )
        object.__setattr__(self, "partition_id", _require_text(self.partition_id, "partition_id"))
        object.__setattr__(
            self,
            "materialization_output_path",
            _require_text(self.materialization_output_path, "materialization_output_path"),
        )
        for field_name in (
            "record_count",
            "valid_value_record_count",
            "nan_record_count",
            "distinct_observed_values",
            "missing_bbo_count",
            "bbo_quarantined_count",
            "available_ts_missing_count",
            "available_ts_invalid_count",
            "available_ts_before_event_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_int(getattr(self, field_name), field_name),
            )
        if not isinstance(self.nan_rate, float | int) or not math.isfinite(self.nan_rate):
            raise FeatureReportError("nan_rate must be a finite number")
        if self.nan_rate < 0 or self.nan_rate > 1:
            raise FeatureReportError("nan_rate must be between 0 and 1")
        object.__setattr__(self, "nan_rate", float(self.nan_rate))
        object.__setattr__(
            self,
            "constant_feature",
            _require_bool(self.constant_feature, "constant_feature"),
        )
        object.__setattr__(
            self,
            "duplicate_exposure_status",
            _require_text(self.duplicate_exposure_status, "duplicate_exposure_status"),
        )
        object.__setattr__(
            self,
            "equivalent_feature_groups",
            _equivalent_feature_groups(self.equivalent_feature_groups),
        )
        object.__setattr__(self, "blocking", _finding_tuple(self.blocking, "blocking"))
        object.__setattr__(
            self,
            "non_blocking",
            _finding_tuple(self.non_blocking, "non_blocking"),
        )
        if any(not finding.is_blocking for finding in self.blocking):
            raise FeatureReportError("blocking findings must have blocking severity")
        if any(finding.is_blocking for finding in self.non_blocking):
            raise FeatureReportError("non_blocking findings must not have blocking severity")

    @classmethod
    def from_registry_record(
        cls,
        record: FeatureRegistryRecord,
        *,
        alpha_data_root: str | Path | None = None,
        env: Mapping[str, str] | None = None,
    ) -> FeatureQualityReport:
        """Build a quality report for one registered feature version."""

        record = _require_registry_record(record)
        observations, load_blocking, load_non_blocking = _load_feature_observations(
            record,
            alpha_data_root=alpha_data_root,
            env=env,
        )
        blocking = list(load_blocking)
        non_blocking = list(load_non_blocking)
        blocking.extend(_registry_consistency_findings(record, observations))

        missing_available = sum(1 for item in observations if item.available_ts_missing)
        invalid_available = sum(1 for item in observations if item.available_ts_invalid)
        available_before_event = sum(1 for item in observations if item.available_ts_before_event)
        valid_records = tuple(item for item in observations if item.has_valid_record_shape)
        nan_count = sum(1 for item in observations if _value_has_null_or_nan(item.value))
        nan_rate = nan_count / len(observations) if observations else 0.0
        missing_bbo_count = sum(
            1 for item in observations if MISSING_BBO_TOKEN in item.quality_flags
        )
        bbo_quarantined_count = sum(
            1 for item in observations if BBO_QUARANTINED_TOKEN in item.quality_flags
        )
        distinct_values = {
            fingerprint
            for item in observations
            if not _value_has_null_or_nan(item.value)
            for fingerprint in (_value_fingerprint(item.value),)
            if fingerprint
        }
        constant_feature = len(distinct_values) == 1 and (
            len(observations) - nan_count
        ) > 1

        if not observations:
            blocking.append(
                _blocking(
                    "NO_FEATURE_VALUE_ROWS",
                    "No materialized value rows were found for the registered feature.",
                    {"expected_count": record.value_record_count},
                )
            )
        if nan_count:
            non_blocking.append(
                _non_blocking(
                    "NAN_RATE_RECORDED",
                    "Null or NaN-like feature values were observed.",
                    {"nan_record_count": nan_count, "nan_rate": nan_rate},
                )
            )
        if constant_feature:
            non_blocking.append(
                _non_blocking(
                    "CONSTANT_FEATURE_DETECTED",
                    "The observed non-missing values are constant.",
                    {"distinct_observed_values": len(distinct_values)},
                )
            )
        if missing_bbo_count or bbo_quarantined_count:
            non_blocking.append(
                _non_blocking(
                    "MISSING_BBO_EXPOSURE_RECORDED",
                    "BBO missingness or quarantine flags were surfaced in feature values.",
                    {
                        "missing_bbo_count": missing_bbo_count,
                        "bbo_quarantined_count": bbo_quarantined_count,
                    },
                )
            )
        if record.duplicate_exposure_report.has_blocking_findings:
            blocking.append(
                _blocking(
                    "DUPLICATE_EXPOSURE_BLOCKING_RECORDED",
                    "The registry duplicate-exposure report contains blocking findings.",
                    {
                        "equivalent_feature_group_count": len(
                            record.duplicate_exposure_report.equivalent_feature_groups
                        )
                    },
                )
            )
        elif record.duplicate_exposure_report.has_findings:
            non_blocking.append(
                _non_blocking(
                    "EQUIVALENT_EXPOSURE_RECORDED",
                    "Equivalent exposure groups are present in the registry evidence.",
                    {
                        "equivalent_feature_group_count": len(
                            record.duplicate_exposure_report.equivalent_feature_groups
                        )
                    },
                )
            )

        return cls(
            feature_id=record.feature_spec.feature_id,
            feature_version_id=record.feature_version_id,
            feature_request_id=record.feature_request_id,
            dataset_version_id=record.dataset_version_id,
            partition_id=record.partition_id,
            materialization_output_path=record.materialization_output_path,
            record_count=len(observations),
            valid_value_record_count=len(valid_records),
            nan_record_count=nan_count,
            nan_rate=nan_rate,
            constant_feature=constant_feature,
            distinct_observed_values=len(distinct_values),
            missing_bbo_count=missing_bbo_count,
            bbo_quarantined_count=bbo_quarantined_count,
            available_ts_missing_count=missing_available,
            available_ts_invalid_count=invalid_available,
            available_ts_before_event_count=available_before_event,
            duplicate_exposure_status=record.duplicate_exposure_status,
            equivalent_feature_groups=record.duplicate_exposure_report.equivalent_feature_groups,
            blocking=tuple(blocking),
            non_blocking=tuple(non_blocking),
        )

    @property
    def has_blocking_findings(self) -> bool:
        """Return whether the report contains blocking defects."""

        return bool(self.blocking)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a stable JSON-compatible quality report payload."""

        return {
            "report_type": "FeatureQualityReport",
            "feature_id": self.feature_id,
            "feature_version_id": self.feature_version_id,
            "feature_request_id": self.feature_request_id,
            "dataset_version_id": self.dataset_version_id,
            "partition_id": self.partition_id,
            "materialization_output_path": self.materialization_output_path,
            "metrics": {
                "record_count": self.record_count,
                "valid_value_record_count": self.valid_value_record_count,
                "nan_record_count": self.nan_record_count,
                "nan_rate": self.nan_rate,
                "constant_feature": self.constant_feature,
                "distinct_observed_values": self.distinct_observed_values,
                "missing_bbo_count": self.missing_bbo_count,
                "bbo_quarantined_count": self.bbo_quarantined_count,
                "available_ts_missing_count": self.available_ts_missing_count,
                "available_ts_invalid_count": self.available_ts_invalid_count,
                "available_ts_before_event_count": self.available_ts_before_event_count,
            },
            "duplicate_exposure_status": self.duplicate_exposure_status,
            "equivalent_feature_groups": [
                group.to_dict() for group in self.equivalent_feature_groups
            ],
            "blocking": [finding.to_dict() for finding in self.blocking],
            "non_blocking": [finding.to_dict() for finding in self.non_blocking],
        }


@dataclass(frozen=True, slots=True)
class FeatureCoverageReport:
    """Descriptive coverage evidence for one registered feature version."""

    feature_id: str
    feature_version_id: str
    feature_request_id: str
    dataset_version_id: str
    partition_id: str
    partition_role: FeaturePartitionRole | str
    materialization_output_path: str
    record_count: int
    symbol_coverage: tuple[CoverageBucket, ...]
    session_coverage: tuple[CoverageBucket, ...]
    partition_coverage: tuple[CoverageBucket, ...]
    expected_symbols: tuple[str, ...] = ()
    expected_sessions: tuple[str, ...] = ()
    expected_partitions: tuple[str, ...] = ()
    duplicate_exposure_status: str = ""
    equivalent_feature_groups: tuple[EquivalentFeatureGroup, ...] = ()
    blocking: tuple[FeatureReportFinding, ...] = ()
    non_blocking: tuple[FeatureReportFinding, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "feature_id", _require_text(self.feature_id, "feature_id"))
        object.__setattr__(
            self,
            "feature_version_id",
            _require_text(self.feature_version_id, "feature_version_id"),
        )
        object.__setattr__(
            self,
            "feature_request_id",
            _require_text(self.feature_request_id, "feature_request_id"),
        )
        object.__setattr__(
            self,
            "dataset_version_id",
            _require_text(self.dataset_version_id, "dataset_version_id"),
        )
        object.__setattr__(self, "partition_id", _require_text(self.partition_id, "partition_id"))
        object.__setattr__(
            self,
            "partition_role",
            _coerce_partition_role(self.partition_role),
        )
        object.__setattr__(
            self,
            "materialization_output_path",
            _require_text(self.materialization_output_path, "materialization_output_path"),
        )
        object.__setattr__(
            self,
            "record_count",
            _require_nonnegative_int(self.record_count, "record_count"),
        )
        object.__setattr__(
            self,
            "symbol_coverage",
            _bucket_tuple(self.symbol_coverage, "symbol_coverage"),
        )
        object.__setattr__(
            self,
            "session_coverage",
            _bucket_tuple(self.session_coverage, "session_coverage"),
        )
        object.__setattr__(
            self,
            "partition_coverage",
            _bucket_tuple(self.partition_coverage, "partition_coverage"),
        )
        object.__setattr__(
            self,
            "expected_symbols",
            _text_tuple(self.expected_symbols, "expected_symbols", allow_empty=True),
        )
        object.__setattr__(
            self,
            "expected_sessions",
            _text_tuple(self.expected_sessions, "expected_sessions", allow_empty=True),
        )
        object.__setattr__(
            self,
            "expected_partitions",
            _text_tuple(self.expected_partitions, "expected_partitions", allow_empty=True),
        )
        object.__setattr__(
            self,
            "duplicate_exposure_status",
            _require_text(self.duplicate_exposure_status, "duplicate_exposure_status"),
        )
        object.__setattr__(
            self,
            "equivalent_feature_groups",
            _equivalent_feature_groups(self.equivalent_feature_groups),
        )
        object.__setattr__(self, "blocking", _finding_tuple(self.blocking, "blocking"))
        object.__setattr__(
            self,
            "non_blocking",
            _finding_tuple(self.non_blocking, "non_blocking"),
        )
        if any(not finding.is_blocking for finding in self.blocking):
            raise FeatureReportError("blocking findings must have blocking severity")
        if any(finding.is_blocking for finding in self.non_blocking):
            raise FeatureReportError("non_blocking findings must not have blocking severity")

    @classmethod
    def from_registry_record(
        cls,
        record: FeatureRegistryRecord,
        *,
        alpha_data_root: str | Path | None = None,
        env: Mapping[str, str] | None = None,
    ) -> FeatureCoverageReport:
        """Build a coverage report for one registered feature version."""

        record = _require_registry_record(record)
        observations, load_blocking, load_non_blocking = _load_feature_observations(
            record,
            alpha_data_root=alpha_data_root,
            env=env,
        )
        blocking = list(load_blocking)
        non_blocking = list(load_non_blocking)
        blocking.extend(_registry_consistency_findings(record, observations))

        metadata = _coverage_metadata(record.registry_metadata.to_dict())
        expected_symbols = _coverage_expectations(metadata, "symbols")
        expected_sessions = _coverage_expectations(metadata, "sessions")
        expected_partitions = _coverage_expectations(metadata, "partitions")
        if not expected_partitions:
            expected_partitions = (record.partition_id,)
        documented_symbol_gaps = _documented_gaps(metadata, "symbols")
        documented_session_gaps = _documented_gaps(metadata, "sessions")
        documented_partition_gaps = _documented_gaps(metadata, "partitions")

        symbol_coverage = _coverage_buckets(
            ((item.symbol_id, item.event_ts) for item in observations),
            fallback_key=UNKNOWN_SYMBOL,
        )
        session_coverage = _coverage_buckets(
            ((item.session_id, item.event_ts) for item in observations),
            fallback_key=UNKNOWN_SESSION,
        )
        partition_coverage = _coverage_buckets(
            ((item.partition_id, item.event_ts) for item in observations),
            fallback_key=record.partition_id,
        )

        if not observations:
            blocking.append(
                _blocking(
                    "NO_FEATURE_VALUE_ROWS",
                    "No materialized value rows were found for the registered feature.",
                    {"expected_count": record.value_record_count},
                )
            )
        if not expected_symbols:
            blocking.append(
                _blocking(
                    "SYMBOL_COVERAGE_EXPECTATIONS_MISSING",
                    "Expected symbol coverage is not documented in registry metadata.",
                )
            )
        if not expected_sessions:
            blocking.append(
                _blocking(
                    "SESSION_COVERAGE_EXPECTATIONS_MISSING",
                    "Expected session coverage is not documented in registry metadata.",
                )
            )
        partition_role = _partition_role_for(record.partition_id)
        if partition_role is FeaturePartitionRole.UNCLASSIFIED:
            blocking.append(
                _blocking(
                    "UNCLASSIFIED_PARTITION",
                    "The registered partition does not map to a supported feature partition role.",
                    {"partition_id": record.partition_id},
                )
            )

        blocking.extend(
            _coverage_gap_findings(
                dimension="symbol",
                expected=expected_symbols,
                observed=tuple(bucket.key for bucket in symbol_coverage),
                documented_gaps=documented_symbol_gaps,
            )
        )
        blocking.extend(
            _coverage_gap_findings(
                dimension="session",
                expected=expected_sessions,
                observed=tuple(bucket.key for bucket in session_coverage),
                documented_gaps=documented_session_gaps,
            )
        )
        blocking.extend(
            _coverage_gap_findings(
                dimension="partition",
                expected=expected_partitions,
                observed=tuple(bucket.key for bucket in partition_coverage),
                documented_gaps=documented_partition_gaps,
            )
        )
        non_blocking.extend(
            _documented_gap_findings(
                dimension="symbol",
                expected=expected_symbols,
                observed=tuple(bucket.key for bucket in symbol_coverage),
                documented_gaps=documented_symbol_gaps,
            )
        )
        non_blocking.extend(
            _documented_gap_findings(
                dimension="session",
                expected=expected_sessions,
                observed=tuple(bucket.key for bucket in session_coverage),
                documented_gaps=documented_session_gaps,
            )
        )
        non_blocking.extend(
            _documented_gap_findings(
                dimension="partition",
                expected=expected_partitions,
                observed=tuple(bucket.key for bucket in partition_coverage),
                documented_gaps=documented_partition_gaps,
            )
        )
        if UNKNOWN_SESSION in {bucket.key for bucket in session_coverage}:
            blocking.append(
                _blocking(
                    "SESSION_COVERAGE_UNRESOLVED",
                    "One or more value rows do not expose a session identifier.",
                    {"session_bucket": UNKNOWN_SESSION},
                )
            )
        if record.duplicate_exposure_report.has_blocking_findings:
            blocking.append(
                _blocking(
                    "DUPLICATE_EXPOSURE_BLOCKING_RECORDED",
                    "The registry duplicate-exposure report contains blocking findings.",
                    {
                        "equivalent_feature_group_count": len(
                            record.duplicate_exposure_report.equivalent_feature_groups
                        )
                    },
                )
            )
        elif record.duplicate_exposure_report.has_findings:
            non_blocking.append(
                _non_blocking(
                    "EQUIVALENT_EXPOSURE_RECORDED",
                    "Equivalent exposure groups are present in the registry evidence.",
                    {
                        "equivalent_feature_group_count": len(
                            record.duplicate_exposure_report.equivalent_feature_groups
                        )
                    },
                )
            )

        return cls(
            feature_id=record.feature_spec.feature_id,
            feature_version_id=record.feature_version_id,
            feature_request_id=record.feature_request_id,
            dataset_version_id=record.dataset_version_id,
            partition_id=record.partition_id,
            partition_role=partition_role,
            materialization_output_path=record.materialization_output_path,
            record_count=len(observations),
            symbol_coverage=symbol_coverage,
            session_coverage=session_coverage,
            partition_coverage=partition_coverage,
            expected_symbols=expected_symbols,
            expected_sessions=expected_sessions,
            expected_partitions=expected_partitions,
            duplicate_exposure_status=record.duplicate_exposure_status,
            equivalent_feature_groups=record.duplicate_exposure_report.equivalent_feature_groups,
            blocking=tuple(blocking),
            non_blocking=tuple(non_blocking),
        )

    @property
    def has_blocking_findings(self) -> bool:
        """Return whether the report contains blocking defects."""

        return bool(self.blocking)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a stable JSON-compatible coverage report payload."""

        return {
            "report_type": "FeatureCoverageReport",
            "feature_id": self.feature_id,
            "feature_version_id": self.feature_version_id,
            "feature_request_id": self.feature_request_id,
            "dataset_version_id": self.dataset_version_id,
            "partition_id": self.partition_id,
            "partition_role": self.partition_role.value,
            "materialization_output_path": self.materialization_output_path,
            "record_count": self.record_count,
            "symbol_coverage": [bucket.to_dict() for bucket in self.symbol_coverage],
            "session_coverage": [bucket.to_dict() for bucket in self.session_coverage],
            "partition_coverage": [bucket.to_dict() for bucket in self.partition_coverage],
            "expected_symbols": list(self.expected_symbols),
            "expected_sessions": list(self.expected_sessions),
            "expected_partitions": list(self.expected_partitions),
            "duplicate_exposure_status": self.duplicate_exposure_status,
            "equivalent_feature_groups": [
                group.to_dict() for group in self.equivalent_feature_groups
            ],
            "blocking": [finding.to_dict() for finding in self.blocking],
            "non_blocking": [finding.to_dict() for finding in self.non_blocking],
        }


def build_feature_quality_report(
    record: FeatureRegistryRecord,
    *,
    alpha_data_root: str | Path | None = None,
    env: Mapping[str, str] | None = None,
) -> FeatureQualityReport:
    """Build a quality report for one registered feature."""

    return FeatureQualityReport.from_registry_record(
        record,
        alpha_data_root=alpha_data_root,
        env=env,
    )


def build_feature_coverage_report(
    record: FeatureRegistryRecord,
    *,
    alpha_data_root: str | Path | None = None,
    env: Mapping[str, str] | None = None,
) -> FeatureCoverageReport:
    """Build a coverage report for one registered feature."""

    return FeatureCoverageReport.from_registry_record(
        record,
        alpha_data_root=alpha_data_root,
        env=env,
    )


def registered_feature_records(registry: FeatureRegistry) -> tuple[FeatureRegistryRecord, ...]:
    """Resolve all records visible through the FeatureRegistry duplicate view."""

    if not isinstance(registry, FeatureRegistry):
        raise FeatureReportError("registered_feature_records requires a FeatureRegistry")
    version_ids = sorted(
        {
            str(
                _mapping_payload(entry.get("metadata", {}), "metadata").get(
                    "feature_version_id",
                    entry.get("factor_version", ""),
                )
            )
            for entry in registry.read_factor_versions()
        }
    )
    records: list[FeatureRegistryRecord] = []
    for version_id in version_ids:
        if not version_id:
            continue
        record = registry.resolve_feature(version_id)
        if record is not None:
            records.append(record)
    return tuple(records)


def build_registered_feature_quality_reports(
    registry: FeatureRegistry,
    *,
    alpha_data_root: str | Path | None = None,
    env: Mapping[str, str] | None = None,
) -> tuple[FeatureQualityReport, ...]:
    """Build quality reports for every registered feature visible in the registry."""

    return tuple(
        FeatureQualityReport.from_registry_record(
            record,
            alpha_data_root=alpha_data_root,
            env=env,
        )
        for record in registered_feature_records(registry)
    )


def build_registered_feature_coverage_reports(
    registry: FeatureRegistry,
    *,
    alpha_data_root: str | Path | None = None,
    env: Mapping[str, str] | None = None,
) -> tuple[FeatureCoverageReport, ...]:
    """Build coverage reports for every registered feature visible in the registry."""

    return tuple(
        FeatureCoverageReport.from_registry_record(
            record,
            alpha_data_root=alpha_data_root,
            env=env,
        )
        for record in registered_feature_records(registry)
    )


@dataclass(frozen=True, slots=True)
class _FeatureValueObservation:
    line_number: int
    feature_version_id: str
    symbol_id: str
    session_id: str
    partition_id: str
    event_ts: datetime | None
    available_ts: datetime | None
    value: object
    quality_flags: tuple[str, ...]
    available_ts_missing: bool
    available_ts_invalid: bool
    available_ts_before_event: bool

    @property
    def has_valid_record_shape(self) -> bool:
        return (
            bool(self.feature_version_id)
            and self.symbol_id != UNKNOWN_SYMBOL
            and self.event_ts is not None
            and self.available_ts is not None
            and not self.available_ts_missing
            and not self.available_ts_invalid
            and not self.available_ts_before_event
        )


def _load_feature_observations(
    record: FeatureRegistryRecord,
    *,
    alpha_data_root: str | Path | None,
    env: Mapping[str, str] | None,
) -> tuple[
    tuple[_FeatureValueObservation, ...],
    tuple[FeatureReportFinding, ...],
    tuple[FeatureReportFinding, ...],
]:
    path, path_findings = _resolve_materialization_path(
        record,
        alpha_data_root=alpha_data_root,
        env=env,
    )
    blocking = list(path_findings)
    non_blocking: list[FeatureReportFinding] = []
    if path is None:
        return (), tuple(blocking), tuple(non_blocking)
    value_path, value_format, value_path_findings = _resolve_value_store_path(
        record,
        materialization_path=path,
        alpha_data_root=alpha_data_root,
        env=env,
    )
    blocking.extend(value_path_findings)
    if value_path is None:
        return (), tuple(blocking), tuple(non_blocking)
    if value_format == "parquet":
        observations = _load_parquet_feature_observations(value_path, record, blocking)
    else:
        observations = _load_jsonl_feature_observations(value_path, record, blocking)
    return _sort_observations(observations, record), tuple(blocking), tuple(non_blocking)


def _load_jsonl_feature_observations(
    path: Path,
    record: FeatureRegistryRecord,
    blocking: list[FeatureReportFinding],
) -> list[_FeatureValueObservation]:
    observations: list[_FeatureValueObservation] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        blocking.append(
            _blocking(
                "MATERIALIZATION_OUTPUT_UNREADABLE",
                "The registered materialization output path could not be read.",
                {"path": path.as_posix(), "error": str(exc)},
            )
        )
        return observations

    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            blocking.append(
                _blocking(
                    "MATERIALIZATION_JSON_INVALID",
                    "A materialized feature value line is not valid JSON.",
                    {"line_number": line_number, "error": str(exc)},
                )
            )
            continue
        if not isinstance(payload, Mapping):
            blocking.append(
                _blocking(
                    "MATERIALIZATION_ROW_INVALID",
                    "A materialized feature value line is not a JSON object.",
                    {"line_number": line_number},
                )
            )
            continue
        if payload.get("record_type") != "feature_value":
            continue
        value_payload = payload.get("value")
        if not isinstance(value_payload, Mapping):
            blocking.append(
                _blocking(
                    "FEATURE_VALUE_PAYLOAD_INVALID",
                    "A feature_value row has no object-valued value payload.",
                    {"line_number": line_number},
                )
            )
            continue
        row_version_id = str(value_payload.get("feature_version_id", "")).strip()
        if row_version_id != record.feature_version_id:
            continue
        observations.append(
            _observation_from_payload(
                line_number=line_number,
                payload=payload,
                value_payload=value_payload,
                record=record,
                blocking=blocking,
            )
        )
    return observations


def _load_parquet_feature_observations(
    path: Path,
    record: FeatureRegistryRecord,
    blocking: list[FeatureReportFinding],
) -> list[_FeatureValueObservation]:
    observations: list[_FeatureValueObservation] = []
    try:
        rows = value_store_module.load_parquet_values(path)
    except DataDependencyError as exc:
        blocking.append(
            _blocking(
                "MATERIALIZATION_PARQUET_DEPENDENCY_MISSING",
                "The registered Parquet value store requires an unavailable dependency.",
                {"path": path.as_posix(), "error": str(exc)},
            )
        )
        return observations
    except (OSError, ValueError) as exc:
        blocking.append(
            _blocking(
                "MATERIALIZATION_PARQUET_UNREADABLE",
                "The registered Parquet value store could not be read.",
                {"path": path.as_posix(), "error": str(exc)},
            )
        )
        return observations
    for row_number, value_payload in enumerate(rows, start=1):
        if not isinstance(value_payload, Mapping):
            blocking.append(
                _blocking(
                    "FEATURE_VALUE_PAYLOAD_INVALID",
                    "A parquet feature value row is not an object.",
                    {"line_number": row_number},
                )
            )
            continue
        row_version_id = str(value_payload.get("feature_version_id", "")).strip()
        if row_version_id != record.feature_version_id:
            continue
        observations.append(
            _observation_from_payload(
                line_number=row_number,
                payload={
                    "dataset_version_id": record.dataset_version_id,
                    "partition_id": record.partition_id,
                },
                value_payload=value_payload,
                record=record,
                blocking=blocking,
            )
        )
    return observations


def _sort_observations(
    observations: list[_FeatureValueObservation],
    record: FeatureRegistryRecord,
) -> tuple[_FeatureValueObservation, ...]:
    return tuple(
        sorted(
            observations,
            key=lambda item: (
                item.event_ts or datetime.min.replace(tzinfo=record.first_event_ts.tzinfo),
                item.symbol_id,
                item.line_number,
            ),
        )
    )


def _observation_from_payload(
    *,
    line_number: int,
    payload: Mapping[str, object],
    value_payload: Mapping[str, object],
    record: FeatureRegistryRecord,
    blocking: list[FeatureReportFinding],
) -> _FeatureValueObservation:
    symbol_id = _optional_text(value_payload.get("entity_id")) or UNKNOWN_SYMBOL
    if symbol_id == UNKNOWN_SYMBOL:
        blocking.append(
            _blocking(
                "FEATURE_VALUE_ENTITY_MISSING",
                "A materialized feature value row is missing entity_id.",
                {"line_number": line_number},
            )
        )
    event_ts, event_error = _parse_datetime(value_payload.get("event_ts"))
    if event_error:
        blocking.append(
            _blocking(
                "FEATURE_VALUE_EVENT_TS_INVALID",
                "A materialized feature value row has an invalid event_ts.",
                {"line_number": line_number, "error": event_error},
            )
        )
    available_raw = value_payload.get("available_ts")
    available_missing = available_raw is None
    available_ts, available_error = _parse_datetime(available_raw)
    if available_missing:
        blocking.append(
            _blocking(
                "FEATURE_VALUE_AVAILABLE_TS_MISSING",
                "A materialized feature value row is missing available_ts.",
                {"line_number": line_number},
            )
        )
    elif available_error:
        blocking.append(
            _blocking(
                "FEATURE_VALUE_AVAILABLE_TS_INVALID",
                "A materialized feature value row has an invalid available_ts.",
                {"line_number": line_number, "error": available_error},
            )
        )
    available_before_event = (
        available_ts is not None and event_ts is not None and available_ts < event_ts
    )
    if available_before_event:
        blocking.append(
            _blocking(
                "FEATURE_VALUE_AVAILABLE_TS_PRECEDES_EVENT_TS",
                "A materialized feature value row has available_ts before event_ts.",
                {"line_number": line_number},
            )
        )

    row_dataset_version = _optional_text(payload.get("dataset_version_id"))
    if row_dataset_version and row_dataset_version != record.dataset_version_id:
        blocking.append(
            _blocking(
                "FEATURE_VALUE_DATASET_VERSION_MISMATCH",
                "A materialized feature value row does not match registry dataset_version_id.",
                {
                    "line_number": line_number,
                    "row_dataset_version_id": row_dataset_version,
                    "registry_dataset_version_id": record.dataset_version_id,
                },
            )
        )
    row_partition = _optional_text(payload.get("partition_id")) or record.partition_id
    if row_partition != record.partition_id:
        blocking.append(
            _blocking(
                "FEATURE_VALUE_PARTITION_MISMATCH",
                "A materialized feature value row does not match registry partition_id.",
                {
                    "line_number": line_number,
                    "row_partition_id": row_partition,
                    "registry_partition_id": record.partition_id,
                },
            )
        )
    quality_flags = _quality_flags(value_payload.get("quality_flags"), line_number, blocking)
    value = value_payload.get("value")
    return _FeatureValueObservation(
        line_number=line_number,
        feature_version_id=record.feature_version_id,
        symbol_id=symbol_id,
        session_id=_session_id(value, quality_flags),
        partition_id=row_partition,
        event_ts=event_ts,
        available_ts=available_ts,
        value=value,
        quality_flags=quality_flags,
        available_ts_missing=available_missing,
        available_ts_invalid=bool(available_error),
        available_ts_before_event=available_before_event,
    )


def _resolve_materialization_path(
    record: FeatureRegistryRecord,
    *,
    alpha_data_root: str | Path | None,
    env: Mapping[str, str] | None,
) -> tuple[Path | None, tuple[FeatureReportFinding, ...]]:
    return _resolve_materialization_path_text(
        record.materialization_output_path,
        alpha_data_root=alpha_data_root,
        env=env,
    )


def _resolve_materialization_path_text(
    materialization_output_path: str,
    *,
    alpha_data_root: str | Path | None,
    env: Mapping[str, str] | None,
) -> tuple[Path | None, tuple[FeatureReportFinding, ...]]:
    findings: list[FeatureReportFinding] = []
    path = Path(materialization_output_path)
    root_value = alpha_data_root
    if root_value is None:
        source = os.environ if env is None else env
        root_value = source.get("ALPHA_DATA_ROOT")
    root = Path(root_value).expanduser().resolve(strict=False) if root_value else None
    if not path.is_absolute():
        if root is None:
            findings.append(
                _blocking(
                    "ALPHA_DATA_ROOT_REQUIRED",
                    "A relative materialization output path requires ALPHA_DATA_ROOT.",
                    {"materialization_output_path": materialization_output_path},
                )
            )
            return None, tuple(findings)
        path = root / path
    path = path.expanduser().resolve(strict=False)
    if root is not None and not path.is_relative_to(root):
        findings.append(
            _blocking(
                "MATERIALIZATION_OUTPUT_OUTSIDE_ALPHA_DATA_ROOT",
                "The registered materialization output path is outside ALPHA_DATA_ROOT.",
                {"path": path.as_posix(), "alpha_data_root": root.as_posix()},
            )
        )
        return path, tuple(findings)
    return path, tuple(findings)


def _resolve_value_store_path(
    record: FeatureRegistryRecord,
    *,
    materialization_path: Path,
    alpha_data_root: str | Path | None,
    env: Mapping[str, str] | None,
) -> tuple[Path | None, str, tuple[FeatureReportFinding, ...]]:
    findings: list[FeatureReportFinding] = []
    if record.parquet_path:
        parquet_path, parquet_findings = _resolve_materialization_path_text(
            record.parquet_path,
            alpha_data_root=alpha_data_root,
            env=env,
        )
        findings.extend(parquet_findings)
        if parquet_path is None:
            return None, "", tuple(findings)
        if not parquet_path.exists():
            findings.append(
                _blocking(
                    "MATERIALIZATION_PARQUET_MISSING",
                    "The registered Parquet value store path does not exist.",
                    {"path": parquet_path.as_posix()},
                )
            )
            return None, "", tuple(findings)
        return parquet_path, "parquet", tuple(findings)

    parquet_sibling = (
        materialization_path
        if materialization_path.suffix == ".parquet"
        else materialization_path.with_name("values.parquet")
    )
    if parquet_sibling.exists():
        return parquet_sibling, "parquet", tuple(findings)

    jsonl_path = (
        materialization_path
        if materialization_path.suffix == ".jsonl"
        else materialization_path.with_name("values.jsonl")
    )
    if jsonl_path.exists():
        return jsonl_path, "jsonl", tuple(findings)

    findings.append(
        _blocking(
            "MATERIALIZATION_OUTPUT_MISSING",
            "No supported materialized value store was found for the registered feature.",
            {
                "materialization_output_path": materialization_path.as_posix(),
                "jsonl_path": jsonl_path.as_posix(),
                "parquet_path": parquet_sibling.as_posix(),
            },
        )
    )
    return None, "", tuple(findings)


def _registry_consistency_findings(
    record: FeatureRegistryRecord,
    observations: tuple[_FeatureValueObservation, ...],
) -> tuple[FeatureReportFinding, ...]:
    findings: list[FeatureReportFinding] = []
    if len(observations) != record.value_record_count:
        findings.append(
            _blocking(
                "REGISTRY_VALUE_RECORD_COUNT_MISMATCH",
                "Observed feature value row count does not match registry metadata.",
                {
                    "observed_count": len(observations),
                    "registry_count": record.value_record_count,
                },
            )
        )
    valid_event_ts = tuple(item.event_ts for item in observations if item.event_ts is not None)
    valid_available_ts = tuple(
        item.available_ts for item in observations if item.available_ts is not None
    )
    if valid_event_ts:
        first_event_ts = min(valid_event_ts)
        last_event_ts = max(valid_event_ts)
        if first_event_ts != record.first_event_ts or last_event_ts != record.last_event_ts:
            findings.append(
                _blocking(
                    "REGISTRY_EVENT_TS_SPAN_MISMATCH",
                    "Observed event_ts span does not match registry metadata.",
                    {
                        "observed_first_event_ts": first_event_ts.isoformat(),
                        "observed_last_event_ts": last_event_ts.isoformat(),
                        "registry_first_event_ts": record.first_event_ts.isoformat(),
                        "registry_last_event_ts": record.last_event_ts.isoformat(),
                    },
                )
            )
    if valid_available_ts:
        first_available_ts = min(valid_available_ts)
        last_available_ts = max(valid_available_ts)
        if (
            first_available_ts != record.first_available_ts
            or last_available_ts != record.last_available_ts
        ):
            findings.append(
                _blocking(
                    "REGISTRY_AVAILABLE_TS_SPAN_MISMATCH",
                    "Observed available_ts span does not match registry metadata.",
                    {
                        "observed_first_available_ts": first_available_ts.isoformat(),
                        "observed_last_available_ts": last_available_ts.isoformat(),
                        "registry_first_available_ts": record.first_available_ts.isoformat(),
                        "registry_last_available_ts": record.last_available_ts.isoformat(),
                    },
                )
            )
    return tuple(findings)


def _coverage_buckets(
    rows: Iterable[tuple[str, datetime | None]],
    *,
    fallback_key: str,
) -> tuple[CoverageBucket, ...]:
    counts: Counter[str] = Counter()
    event_ts_by_key: dict[str, list[datetime]] = {}
    for key, event_ts in rows:
        normalized = _optional_text(key) or fallback_key
        counts[normalized] += 1
        if event_ts is not None:
            event_ts_by_key.setdefault(normalized, []).append(event_ts)
    buckets = []
    for key in sorted(counts):
        timestamps = event_ts_by_key.get(key, [])
        buckets.append(
            CoverageBucket(
                key=key,
                count=counts[key],
                first_event_ts=min(timestamps) if timestamps else None,
                last_event_ts=max(timestamps) if timestamps else None,
            )
        )
    return tuple(buckets)


def _coverage_gap_findings(
    *,
    dimension: str,
    expected: tuple[str, ...],
    observed: tuple[str, ...],
    documented_gaps: frozenset[str],
) -> tuple[FeatureReportFinding, ...]:
    findings: list[FeatureReportFinding] = []
    observed_set = set(observed)
    for item in expected:
        if item in observed_set or item in documented_gaps:
            continue
        findings.append(
            _blocking(
                f"UNDOCUMENTED_{dimension.upper()}_COVERAGE_GAP",
                f"Expected {dimension} coverage is missing without a documented gap.",
                {f"{dimension}_id": item},
            )
        )
    return tuple(findings)


def _documented_gap_findings(
    *,
    dimension: str,
    expected: tuple[str, ...],
    observed: tuple[str, ...],
    documented_gaps: frozenset[str],
) -> tuple[FeatureReportFinding, ...]:
    findings: list[FeatureReportFinding] = []
    observed_set = set(observed)
    for item in expected:
        if item not in observed_set and item in documented_gaps:
            findings.append(
                _non_blocking(
                    f"DOCUMENTED_{dimension.upper()}_COVERAGE_GAP",
                    f"Expected {dimension} coverage is absent and documented.",
                    {f"{dimension}_id": item},
                )
            )
    return tuple(findings)


def _coverage_metadata(metadata: Mapping[str, object]) -> Mapping[str, object]:
    for key in ("feature_report", "coverage_expectations", "coverage"):
        nested = metadata.get(key)
        if isinstance(nested, Mapping):
            if key == "feature_report":
                coverage = nested.get("coverage") or nested.get("coverage_expectations")
                if isinstance(coverage, Mapping):
                    return coverage
            else:
                return nested
    return {}


def _coverage_expectations(metadata: Mapping[str, object], dimension: str) -> tuple[str, ...]:
    singular = dimension[:-1] if dimension.endswith("s") else dimension
    for key in (f"expected_{dimension}", dimension, f"{singular}_ids"):
        value = metadata.get(key)
        if value is not None:
            return _sorted_text_values(value)
    return ()


def _documented_gaps(metadata: Mapping[str, object], dimension: str) -> frozenset[str]:
    singular = dimension[:-1] if dimension.endswith("s") else dimension
    for key in (
        "documented_gaps",
        f"documented_{dimension}_gaps",
        f"documented_{singular}_gaps",
    ):
        value = metadata.get(key)
        if isinstance(value, Mapping):
            nested = value.get(dimension) or value.get(singular)
            if nested is not None:
                return frozenset(_sorted_text_values(nested))
        if value is not None and key != "documented_gaps":
            return frozenset(_sorted_text_values(value))
    return frozenset()


def _partition_role_for(partition_id: str) -> FeaturePartitionRole:
    normalized = _normalize_token(partition_id)
    if "locked_test_candidate" in normalized or "locked_test" in normalized:
        return FeaturePartitionRole.LOCKED_TEST_CANDIDATE
    if "validation" in normalized:
        return FeaturePartitionRole.VALIDATION
    if "development" in normalized or normalized in {"dev", "train"}:
        return FeaturePartitionRole.DEVELOPMENT
    return FeaturePartitionRole.UNCLASSIFIED


def _session_id(value: object, quality_flags: tuple[str, ...]) -> str:
    if isinstance(value, Mapping):
        for key in (
            "session_id",
            "session_label",
            "session",
            "trading_session",
        ):
            session = _optional_text(value.get(key))
            if session:
                return session.upper()
    for flag in quality_flags:
        for prefix in ("session:", "session=", "session_id:", "session_id="):
            if flag.startswith(prefix):
                session = _optional_text(flag.removeprefix(prefix))
                if session:
                    return session.upper()
    return UNKNOWN_SESSION


def _quality_flags(
    value: object,
    line_number: int,
    blocking: list[FeatureReportFinding],
) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, Sequence):
        blocking.append(
            _blocking(
                "FEATURE_VALUE_QUALITY_FLAGS_INVALID",
                "A materialized feature value row has invalid quality_flags.",
                {"line_number": line_number},
            )
        )
        return ()
    flags: list[str] = []
    for item in value:
        flag = _optional_text(item)
        if not flag:
            blocking.append(
                _blocking(
                    "FEATURE_VALUE_QUALITY_FLAG_INVALID",
                    "A materialized feature value row has a non-text quality flag.",
                    {"line_number": line_number},
                )
            )
            continue
        flags.append(flag.lower())
    return tuple(sorted(set(flags)))


def _parse_datetime(value: object) -> tuple[datetime | None, str]:
    if not isinstance(value, str) or not value.strip():
        return None, "timestamp must be a non-empty ISO-8601 string"
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        return None, str(exc)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None, "timestamp must be timezone-aware"
    return parsed, ""


def _value_has_null_or_nan(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, float):
        return not math.isfinite(value)
    if isinstance(value, Mapping):
        return any(_value_has_null_or_nan(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return any(_value_has_null_or_nan(item) for item in value)
    return False


def _value_fingerprint(value: object) -> str:
    try:
        return canonical_serialize(_json_value(value))
    except (TypeError, ValueError):
        return repr(value)


def _json_value(value: object) -> JsonValue:
    if value is None or isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [_json_value(item) for item in value]
    return str(value)


def _blocking(
    code: str,
    message: str,
    detail: Mapping[str, Any] | None = None,
) -> FeatureReportFinding:
    return FeatureReportFinding(
        code=code,
        severity=FeatureReportSeverity.BLOCKING,
        message=message,
        detail=detail or {},
    )


def _non_blocking(
    code: str,
    message: str,
    detail: Mapping[str, Any] | None = None,
) -> FeatureReportFinding:
    return FeatureReportFinding(
        code=code,
        severity=FeatureReportSeverity.NON_BLOCKING,
        message=message,
        detail=detail or {},
    )


def _require_registry_record(record: FeatureRegistryRecord) -> FeatureRegistryRecord:
    if not isinstance(record, FeatureRegistryRecord):
        raise FeatureReportError("feature reports require a FeatureRegistryRecord")
    return record


def _equivalent_feature_groups(
    groups: Iterable[EquivalentFeatureGroup],
) -> tuple[EquivalentFeatureGroup, ...]:
    values = tuple(groups)
    for group in values:
        if not isinstance(group, EquivalentFeatureGroup):
            raise FeatureReportError("equivalent_feature_groups must contain views")
    return values


def _finding_tuple(
    findings: Iterable[FeatureReportFinding],
    field_name: str,
) -> tuple[FeatureReportFinding, ...]:
    values = tuple(findings)
    for finding in values:
        if not isinstance(finding, FeatureReportFinding):
            raise FeatureReportError(f"{field_name} must contain FeatureReportFinding")
    return values


def _bucket_tuple(
    buckets: Iterable[CoverageBucket],
    field_name: str,
) -> tuple[CoverageBucket, ...]:
    values = tuple(buckets)
    for bucket in values:
        if not isinstance(bucket, CoverageBucket):
            raise FeatureReportError(f"{field_name} must contain CoverageBucket")
    return values


def _freeze_mapping(
    value: Mapping[str, Any] | FrozenJsonMapping,
    field_name: str,
) -> FrozenJsonMapping:
    if isinstance(value, FrozenJsonMapping):
        return value
    return FrozenJsonMapping.from_mapping(value, field_name=field_name)


def _mapping_payload(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise FeatureReportError(f"{field_name} must be a mapping")
    return value


def _coerce_severity(value: FeatureReportSeverity | str, field_name: str) -> FeatureReportSeverity:
    try:
        if isinstance(value, FeatureReportSeverity):
            return value
        return FeatureReportSeverity(_require_text(value, field_name))
    except ValueError as exc:
        raise FeatureReportError(f"{field_name} must be blocking or non_blocking") from exc


def _coerce_partition_role(value: FeaturePartitionRole | str) -> FeaturePartitionRole:
    try:
        if isinstance(value, FeaturePartitionRole):
            return value
        return FeaturePartitionRole(_require_text(value, "partition_role"))
    except ValueError as exc:
        raise FeatureReportError("partition_role is not supported") from exc


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise FeatureReportError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise FeatureReportError(f"{field_name} must be non-empty")
    return normalized


def _optional_text(value: object) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        return ""
    return value.strip()


def _text_tuple(
    value: Iterable[object],
    field_name: str,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(value, str):
        raise FeatureReportError(f"{field_name} must be a sequence")
    values = tuple(_require_text(item, field_name) for item in value)
    if not values and not allow_empty:
        raise FeatureReportError(f"{field_name} must not be empty")
    return values


def _sorted_text_values(value: object) -> tuple[str, ...]:
    if isinstance(value, Mapping):
        raw_values = value.keys()
    elif isinstance(value, str):
        raw_values = (value,)
    elif isinstance(value, Sequence):
        raw_values = value
    else:
        return ()
    normalized = {_optional_text(item) for item in raw_values}
    return tuple(sorted(item for item in normalized if item))


def _require_nonnegative_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise FeatureReportError(f"{field_name} must be a non-negative integer")
    return value


def _require_bool(value: object, field_name: str) -> bool:
    if type(value) is not bool:
        raise FeatureReportError(f"{field_name} must be a bool")
    return value


def _require_aware_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise FeatureReportError(f"{field_name} must be a timezone-aware datetime")
    return value


def _normalize_token(value: str) -> str:
    return value.strip().casefold().replace("-", "_")


__all__ = [
    "BBO_QUARANTINED_TOKEN",
    "MISSING_BBO_TOKEN",
    "CoverageBucket",
    "FeatureCoverageReport",
    "FeaturePartitionRole",
    "FeatureQualityReport",
    "FeatureReportError",
    "FeatureReportFinding",
    "FeatureReportSeverity",
    "build_feature_coverage_report",
    "build_feature_quality_report",
    "build_registered_feature_coverage_reports",
    "build_registered_feature_quality_reports",
    "registered_feature_records",
]
