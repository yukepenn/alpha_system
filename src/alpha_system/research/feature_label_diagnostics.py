"""Descriptive feature/label diagnostics composed from existing reports.

This module consumes FLF-P15 feature quality/coverage reports and FLF-P23 label
leakage/availability audit reports. It does not materialize feature or label
values, read provider data, call providers, or duplicate governance checks.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from alpha_system.features.reports import FeatureCoverageReport, FeatureQualityReport
from alpha_system.labels.leakage_audit import LabelLeakageAuditReport

JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]

_LABEL_AS_FEATURE_CHECKS = frozenset({"label_as_feature", "label_identity_as_feature"})
_LABEL_AVAILABILITY_CHECK_TOKENS = (
    "availability_time",
    "label_available_ts",
    "registry_label_available_ts",
)
_FEATURE_AVAILABLE_TS_METRICS = (
    "available_ts_missing_count",
    "available_ts_invalid_count",
    "available_ts_before_event_count",
)
_NO_TRADE_METRICS = (
    "synthetic_no_trade_count",
    "synthetic_dense_grid_no_trade_count",
    "no_trade_count",
    "no_trade_exposure_count",
    "has_trade_false_synthetic_count",
)


class FeatureLabelDiagnosticsError(ValueError):
    """Raised when feature/label diagnostics inputs are malformed."""


class DiagnosticSeverity(StrEnum):
    """Finding severity partition for descriptive diagnostics."""

    BLOCKING = "blocking"
    NON_BLOCKING = "non_blocking"


class DiagnosticStatus(StrEnum):
    """Compact status for the composed diagnostic report."""

    CLEAR = "clear"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class DiagnosticFinding:
    """One row-free diagnostic finding."""

    code: str
    severity: DiagnosticSeverity | str
    message: str
    detail: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", _require_text(self.code, "code"))
        object.__setattr__(self, "severity", _coerce_severity(self.severity))
        object.__setattr__(self, "message", _require_text(self.message, "message"))
        object.__setattr__(self, "detail", _json_mapping(self.detail))

    @property
    def is_blocking(self) -> bool:
        """Return whether the finding belongs to the blocking partition."""

        return self.severity is DiagnosticSeverity.BLOCKING

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a stable JSON-compatible finding payload."""

        return {
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
            "detail": dict(self.detail),
        }


@dataclass(frozen=True, slots=True)
class AvailabilityAlignmentDiagnostic:
    """Feature ``available_ts`` and label ``label_available_ts`` audit summary."""

    feature_report_count: int
    label_audit_count: int
    shared_dataset_versions: tuple[str, ...]
    feature_only_dataset_versions: tuple[str, ...]
    label_only_dataset_versions: tuple[str, ...]
    shared_partitions: tuple[str, ...]
    feature_only_partitions: tuple[str, ...]
    label_only_partitions: tuple[str, ...]
    feature_available_ts_issue_count: int
    label_available_ts_finding_count: int
    label_as_feature_finding_count: int
    blocking: tuple[DiagnosticFinding, ...] = ()
    non_blocking: tuple[DiagnosticFinding, ...] = ()

    @property
    def status(self) -> DiagnosticStatus:
        """Return the alignment status."""

        return DiagnosticStatus.BLOCKED if self.blocking else DiagnosticStatus.CLEAR

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a stable JSON-compatible alignment payload."""

        return {
            "status": self.status.value,
            "feature_report_count": self.feature_report_count,
            "label_audit_count": self.label_audit_count,
            "shared_dataset_versions": list(self.shared_dataset_versions),
            "feature_only_dataset_versions": list(self.feature_only_dataset_versions),
            "label_only_dataset_versions": list(self.label_only_dataset_versions),
            "shared_partitions": list(self.shared_partitions),
            "feature_only_partitions": list(self.feature_only_partitions),
            "label_only_partitions": list(self.label_only_partitions),
            "feature_available_ts_issue_count": self.feature_available_ts_issue_count,
            "label_available_ts_finding_count": self.label_available_ts_finding_count,
            "label_as_feature_finding_count": self.label_as_feature_finding_count,
            "blocking": [finding.to_dict() for finding in self.blocking],
            "non_blocking": [finding.to_dict() for finding in self.non_blocking],
        }


@dataclass(frozen=True, slots=True)
class CoverageDimensionOverlap:
    """Shared and one-sided coverage for one dimension."""

    dimension: str
    feature_values: tuple[str, ...]
    label_values: tuple[str, ...]
    shared_values: tuple[str, ...]
    feature_only_values: tuple[str, ...]
    label_only_values: tuple[str, ...]

    @property
    def has_reported_overlap(self) -> bool:
        """Return whether both sides reported at least one shared value."""

        return bool(self.shared_values)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a stable JSON-compatible coverage-overlap payload."""

        return {
            "dimension": self.dimension,
            "feature_values": list(self.feature_values),
            "label_values": list(self.label_values),
            "shared_values": list(self.shared_values),
            "feature_only_values": list(self.feature_only_values),
            "label_only_values": list(self.label_only_values),
            "feature_value_count": len(self.feature_values),
            "label_value_count": len(self.label_values),
            "shared_value_count": len(self.shared_values),
        }


@dataclass(frozen=True, slots=True)
class CoverageOverlapDiagnostic:
    """Symbol, session, and partition overlap between feature and label reports."""

    dimensions: tuple[CoverageDimensionOverlap, ...]
    blocking: tuple[DiagnosticFinding, ...] = ()
    non_blocking: tuple[DiagnosticFinding, ...] = ()

    @property
    def status(self) -> DiagnosticStatus:
        """Return the coverage-overlap status."""

        return DiagnosticStatus.BLOCKED if self.blocking else DiagnosticStatus.CLEAR

    def dimension(self, name: str) -> CoverageDimensionOverlap:
        """Return one coverage dimension by name."""

        for item in self.dimensions:
            if item.dimension == name:
                return item
        raise FeatureLabelDiagnosticsError(f"coverage dimension not present: {name}")

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a stable JSON-compatible coverage payload."""

        return {
            "status": self.status.value,
            "dimensions": [item.to_dict() for item in self.dimensions],
            "blocking": [finding.to_dict() for finding in self.blocking],
            "non_blocking": [finding.to_dict() for finding in self.non_blocking],
        }


@dataclass(frozen=True, slots=True)
class MissingnessExposureDiagnostic:
    """Descriptive BBO and synthetic no-trade exposure summary."""

    missing_bbo_count: int
    bbo_quarantined_count: int
    synthetic_no_trade_count: int
    synthetic_no_trade_reported: bool
    blocking: tuple[DiagnosticFinding, ...] = ()
    non_blocking: tuple[DiagnosticFinding, ...] = ()

    @property
    def status(self) -> DiagnosticStatus:
        """Return the missingness-exposure status."""

        return DiagnosticStatus.BLOCKED if self.blocking else DiagnosticStatus.CLEAR

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a stable JSON-compatible missingness payload."""

        return {
            "status": self.status.value,
            "missing_bbo_count": self.missing_bbo_count,
            "bbo_quarantined_count": self.bbo_quarantined_count,
            "synthetic_no_trade_count": self.synthetic_no_trade_count,
            "synthetic_no_trade_reported": self.synthetic_no_trade_reported,
            "blocking": [finding.to_dict() for finding in self.blocking],
            "non_blocking": [finding.to_dict() for finding in self.non_blocking],
        }


@dataclass(frozen=True, slots=True)
class FeatureLabelDiagnosticsReport:
    """Unified descriptive feature/label diagnostics."""

    availability_alignment: AvailabilityAlignmentDiagnostic
    coverage_overlap: CoverageOverlapDiagnostic
    missingness_exposure: MissingnessExposureDiagnostic

    @property
    def blocking(self) -> tuple[DiagnosticFinding, ...]:
        """Return every blocking finding across diagnostics."""

        return (
            self.availability_alignment.blocking
            + self.coverage_overlap.blocking
            + self.missingness_exposure.blocking
        )

    @property
    def non_blocking(self) -> tuple[DiagnosticFinding, ...]:
        """Return every non-blocking finding across diagnostics."""

        return (
            self.availability_alignment.non_blocking
            + self.coverage_overlap.non_blocking
            + self.missingness_exposure.non_blocking
        )

    @property
    def status(self) -> DiagnosticStatus:
        """Return the composed report status."""

        return DiagnosticStatus.BLOCKED if self.blocking else DiagnosticStatus.CLEAR

    @property
    def blocked(self) -> bool:
        """Return whether any diagnostic has blocking findings."""

        return self.status is DiagnosticStatus.BLOCKED

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a stable JSON-compatible diagnostics payload."""

        return {
            "report_type": "FeatureLabelDiagnosticsReport",
            "diagnostic_kind": "descriptive_feature_label_diagnostics",
            "status": self.status.value,
            "blocked": self.blocked,
            "availability_alignment": self.availability_alignment.to_dict(),
            "coverage_overlap": self.coverage_overlap.to_dict(),
            "missingness_exposure": self.missingness_exposure.to_dict(),
            "blocking": [finding.to_dict() for finding in self.blocking],
            "non_blocking": [finding.to_dict() for finding in self.non_blocking],
        }


@dataclass(frozen=True, slots=True)
class _ReportFindingView:
    code: str
    severity: DiagnosticSeverity
    message: str
    detail: Mapping[str, JsonValue]


@dataclass(frozen=True, slots=True)
class _FeatureQualityView:
    feature_id: str
    feature_version_id: str
    dataset_version_id: str
    partition_id: str
    metrics: Mapping[str, Any]
    blocking: tuple[_ReportFindingView, ...]
    non_blocking: tuple[_ReportFindingView, ...]


@dataclass(frozen=True, slots=True)
class _FeatureCoverageView:
    feature_id: str
    feature_version_id: str
    dataset_version_id: str
    partition_id: str
    symbols: tuple[str, ...]
    sessions: tuple[str, ...]
    partitions: tuple[str, ...]
    blocking: tuple[_ReportFindingView, ...]
    non_blocking: tuple[_ReportFindingView, ...]


@dataclass(frozen=True, slots=True)
class _LabelAuditView:
    label_id: str
    label_version_id: str
    label_spec_id: str
    dataset_version_id: str
    partition_id: str
    symbols: tuple[str, ...]
    sessions: tuple[str, ...]
    partitions: tuple[str, ...]
    findings: tuple[_ReportFindingView, ...]
    blocked: bool


def build_feature_label_diagnostics(
    *,
    feature_quality_reports: Iterable[FeatureQualityReport | Mapping[str, Any]],
    feature_coverage_reports: Iterable[FeatureCoverageReport | Mapping[str, Any]],
    label_audit_reports: Iterable[LabelLeakageAuditReport | Mapping[str, Any]],
) -> FeatureLabelDiagnosticsReport:
    """Build a unified descriptive diagnostics report from upstream outputs."""

    quality_reports = tuple(
        _feature_quality_view(item)
        for item in _report_iterable(feature_quality_reports, "feature_quality_reports")
    )
    coverage_reports = tuple(
        _feature_coverage_view(item)
        for item in _report_iterable(feature_coverage_reports, "feature_coverage_reports")
    )
    label_audits = tuple(
        _label_audit_view(item)
        for item in _report_iterable(label_audit_reports, "label_audit_reports")
    )
    return FeatureLabelDiagnosticsReport(
        availability_alignment=_availability_alignment(
            quality_reports,
            coverage_reports,
            label_audits,
        ),
        coverage_overlap=_coverage_overlap(coverage_reports, label_audits),
        missingness_exposure=_missingness_exposure(quality_reports),
    )


def _availability_alignment(
    quality_reports: tuple[_FeatureQualityView, ...],
    coverage_reports: tuple[_FeatureCoverageView, ...],
    label_audits: tuple[_LabelAuditView, ...],
) -> AvailabilityAlignmentDiagnostic:
    blocking: list[DiagnosticFinding] = []
    non_blocking: list[DiagnosticFinding] = []
    if not quality_reports:
        blocking.append(
            _blocking(
                "FEATURE_QUALITY_REPORTS_MISSING",
                "Feature quality report input is required.",
            )
        )
    if not coverage_reports:
        blocking.append(
            _blocking(
                "FEATURE_COVERAGE_REPORTS_MISSING",
                "Feature coverage report input is required.",
            )
        )
    if not label_audits:
        blocking.append(
            _blocking(
                "LABEL_AUDIT_REPORTS_MISSING",
                "Label leakage and availability audit input is required.",
            )
        )

    feature_dataset_versions = _sorted_strings(
        item.dataset_version_id for item in (*quality_reports, *coverage_reports)
    )
    label_dataset_versions = _sorted_strings(item.dataset_version_id for item in label_audits)
    feature_partitions = _sorted_strings(
        item.partition_id for item in (*quality_reports, *coverage_reports)
    )
    label_partitions = _sorted_strings(item.partition_id for item in label_audits)
    dataset_overlap = _overlap(feature_dataset_versions, label_dataset_versions)
    partition_overlap = _overlap(feature_partitions, label_partitions)

    if feature_dataset_versions and label_dataset_versions and not dataset_overlap.shared:
        blocking.append(
            _blocking(
                "DATASET_VERSION_OVERLAP_MISSING",
                "Feature reports and label audits do not share a dataset version.",
                {
                    "feature_dataset_versions": list(feature_dataset_versions),
                    "label_dataset_versions": list(label_dataset_versions),
                },
            )
        )
    if feature_partitions and label_partitions and not partition_overlap.shared:
        blocking.append(
            _blocking(
                "PARTITION_OVERLAP_MISSING",
                "Feature reports and label audits do not share a partition.",
                {
                    "feature_partitions": list(feature_partitions),
                    "label_partitions": list(label_partitions),
                },
            )
        )

    feature_available_ts_issue_count = sum(
        _nonnegative_metric(item.metrics, key)
        for item in quality_reports
        for key in _FEATURE_AVAILABLE_TS_METRICS
    )
    if feature_available_ts_issue_count:
        blocking.append(
            _blocking(
                "FEATURE_AVAILABLE_TS_DEFECTS_REPORTED",
                "Feature reports contain available_ts defects.",
                {"issue_count": feature_available_ts_issue_count},
            )
        )

    label_available_findings = tuple(
        finding
        for audit in label_audits
        for finding in audit.findings
        if any(token in finding.code.lower() for token in _LABEL_AVAILABILITY_CHECK_TOKENS)
    )
    label_as_feature_findings = tuple(
        finding
        for audit in label_audits
        for finding in audit.findings
        if finding.code.lower() in _LABEL_AS_FEATURE_CHECKS
    )
    if any(finding.severity is DiagnosticSeverity.BLOCKING for finding in label_available_findings):
        blocking.append(
            _blocking(
                "LABEL_AVAILABLE_TS_AUDIT_BLOCKING_REPORTED",
                "Label audit reports contain label_available_ts or availability-time findings.",
                {"finding_count": len(label_available_findings)},
            )
        )
    if any(finding.severity is DiagnosticSeverity.BLOCKING for finding in label_as_feature_findings):
        blocking.append(
            _blocking(
                "LABEL_REACHABLE_AS_FEATURE_INPUT_REPORTED",
                "Label audit reports found a label reference reachable as a live feature input.",
                {"finding_count": len(label_as_feature_findings)},
            )
        )

    blocked_label_count = sum(1 for audit in label_audits if audit.blocked)
    if blocked_label_count and not label_available_findings and not label_as_feature_findings:
        blocking.append(
            _blocking(
                "LABEL_AUDIT_BLOCKING_REPORTED",
                "Label audit reports contain blocking findings.",
                {"blocked_label_count": blocked_label_count},
            )
        )

    if dataset_overlap.feature_only or dataset_overlap.label_only:
        non_blocking.append(
            _non_blocking(
                "DATASET_VERSION_SCOPE_DIFFERENCE_RECORDED",
                "Feature and label inputs include one-sided dataset-version scope.",
                {
                    "feature_only_dataset_versions": list(dataset_overlap.feature_only),
                    "label_only_dataset_versions": list(dataset_overlap.label_only),
                },
            )
        )
    if partition_overlap.feature_only or partition_overlap.label_only:
        non_blocking.append(
            _non_blocking(
                "PARTITION_SCOPE_DIFFERENCE_RECORDED",
                "Feature and label inputs include one-sided partition scope.",
                {
                    "feature_only_partitions": list(partition_overlap.feature_only),
                    "label_only_partitions": list(partition_overlap.label_only),
                },
            )
        )

    return AvailabilityAlignmentDiagnostic(
        feature_report_count=len(quality_reports) + len(coverage_reports),
        label_audit_count=len(label_audits),
        shared_dataset_versions=dataset_overlap.shared,
        feature_only_dataset_versions=dataset_overlap.feature_only,
        label_only_dataset_versions=dataset_overlap.label_only,
        shared_partitions=partition_overlap.shared,
        feature_only_partitions=partition_overlap.feature_only,
        label_only_partitions=partition_overlap.label_only,
        feature_available_ts_issue_count=feature_available_ts_issue_count,
        label_available_ts_finding_count=len(label_available_findings),
        label_as_feature_finding_count=len(label_as_feature_findings),
        blocking=tuple(blocking),
        non_blocking=tuple(non_blocking),
    )


def _coverage_overlap(
    coverage_reports: tuple[_FeatureCoverageView, ...],
    label_audits: tuple[_LabelAuditView, ...],
) -> CoverageOverlapDiagnostic:
    feature_values = {
        "symbol": _sorted_strings(value for item in coverage_reports for value in item.symbols),
        "session": _sorted_strings(value for item in coverage_reports for value in item.sessions),
        "partition": _sorted_strings(value for item in coverage_reports for value in item.partitions),
    }
    label_values = {
        "symbol": _sorted_strings(value for item in label_audits for value in item.symbols),
        "session": _sorted_strings(value for item in label_audits for value in item.sessions),
        "partition": _sorted_strings(value for item in label_audits for value in item.partitions),
    }
    dimensions: list[CoverageDimensionOverlap] = []
    blocking: list[DiagnosticFinding] = []
    non_blocking: list[DiagnosticFinding] = []

    for dimension in ("symbol", "session", "partition"):
        overlap = _overlap(feature_values[dimension], label_values[dimension])
        dimensions.append(
            CoverageDimensionOverlap(
                dimension=dimension,
                feature_values=feature_values[dimension],
                label_values=label_values[dimension],
                shared_values=overlap.shared,
                feature_only_values=overlap.feature_only,
                label_only_values=overlap.label_only,
            )
        )
        if feature_values[dimension] and not label_values[dimension]:
            blocking.append(
                _blocking(
                    f"LABEL_{dimension.upper()}_COVERAGE_UNREPORTED",
                    f"Label audit outputs do not report {dimension} coverage.",
                    {"feature_values": list(feature_values[dimension])},
                )
            )
            continue
        if feature_values[dimension] and label_values[dimension] and not overlap.shared:
            blocking.append(
                _blocking(
                    f"{dimension.upper()}_COVERAGE_OVERLAP_MISSING",
                    f"Feature and label reports have no shared {dimension} coverage.",
                    {
                        "feature_values": list(feature_values[dimension]),
                        "label_values": list(label_values[dimension]),
                    },
                )
            )
        elif overlap.feature_only or overlap.label_only:
            non_blocking.append(
                _non_blocking(
                    f"{dimension.upper()}_COVERAGE_SCOPE_DIFFERENCE_RECORDED",
                    f"Feature and label reports include one-sided {dimension} coverage.",
                    {
                        "feature_only_values": list(overlap.feature_only),
                        "label_only_values": list(overlap.label_only),
                    },
                )
            )

    return CoverageOverlapDiagnostic(
        dimensions=tuple(dimensions),
        blocking=tuple(blocking),
        non_blocking=tuple(non_blocking),
    )


def _missingness_exposure(
    quality_reports: tuple[_FeatureQualityView, ...],
) -> MissingnessExposureDiagnostic:
    missing_bbo_count = 0
    bbo_quarantined_count = 0
    synthetic_no_trade_count = 0
    synthetic_no_trade_reported = False
    non_blocking: list[DiagnosticFinding] = []

    for report in quality_reports:
        missing_bbo_count += _metric_or_finding_detail(
            report,
            "missing_bbo_count",
            "missing_bbo",
        )
        bbo_quarantined_count += _metric_or_finding_detail(
            report,
            "bbo_quarantined_count",
            "bbo_quarantined",
        )
        report_synthetic_no_trade_reported = False
        for key in _NO_TRADE_METRICS:
            if key in report.metrics:
                report_synthetic_no_trade_reported = True
                synthetic_no_trade_count += _nonnegative_metric(report.metrics, key)
        if not report_synthetic_no_trade_reported:
            detail_count = _metric_or_finding_detail(report, "synthetic_no_trade_count", "no_trade")
            if detail_count:
                report_synthetic_no_trade_reported = True
                synthetic_no_trade_count += detail_count
        synthetic_no_trade_reported = (
            synthetic_no_trade_reported or report_synthetic_no_trade_reported
        )

    if missing_bbo_count or bbo_quarantined_count:
        non_blocking.append(
            _non_blocking(
                "BBO_MISSINGNESS_EXPOSURE_RECORDED",
                "BBO missingness and quarantine exposure is recorded.",
                {
                    "missing_bbo_count": missing_bbo_count,
                    "bbo_quarantined_count": bbo_quarantined_count,
                },
            )
        )
    if synthetic_no_trade_reported:
        non_blocking.append(
            _non_blocking(
                "SYNTHETIC_NO_TRADE_EXPOSURE_RECORDED",
                "Synthetic dense-grid no-trade exposure is recorded.",
                {"synthetic_no_trade_count": synthetic_no_trade_count},
            )
        )
    else:
        non_blocking.append(
            _non_blocking(
                "SYNTHETIC_NO_TRADE_EXPOSURE_NOT_REPORTED",
                "Synthetic dense-grid no-trade exposure was not present in supplied reports.",
            )
        )

    return MissingnessExposureDiagnostic(
        missing_bbo_count=missing_bbo_count,
        bbo_quarantined_count=bbo_quarantined_count,
        synthetic_no_trade_count=synthetic_no_trade_count,
        synthetic_no_trade_reported=synthetic_no_trade_reported,
        blocking=(),
        non_blocking=tuple(non_blocking),
    )


@dataclass(frozen=True, slots=True)
class _Overlap:
    shared: tuple[str, ...]
    feature_only: tuple[str, ...]
    label_only: tuple[str, ...]


def _overlap(feature_values: Iterable[str], label_values: Iterable[str]) -> _Overlap:
    feature_set = frozenset(feature_values)
    label_set = frozenset(label_values)
    return _Overlap(
        shared=_sorted_strings(feature_set.intersection(label_set)),
        feature_only=_sorted_strings(feature_set.difference(label_set)),
        label_only=_sorted_strings(label_set.difference(feature_set)),
    )


def _feature_quality_view(report: FeatureQualityReport | Mapping[str, Any]) -> _FeatureQualityView:
    payload = report.to_dict() if isinstance(report, FeatureQualityReport) else _report_mapping(report)
    metrics = _mapping_or_empty(payload.get("metrics"))
    return _FeatureQualityView(
        feature_id=_field_text(payload, "feature_id"),
        feature_version_id=_field_text(payload, "feature_version_id"),
        dataset_version_id=_field_text(payload, "dataset_version_id"),
        partition_id=_field_text(payload, "partition_id"),
        metrics=metrics,
        blocking=_report_findings(payload.get("blocking"), DiagnosticSeverity.BLOCKING),
        non_blocking=_report_findings(
            payload.get("non_blocking"),
            DiagnosticSeverity.NON_BLOCKING,
        ),
    )


def _feature_coverage_view(
    report: FeatureCoverageReport | Mapping[str, Any],
) -> _FeatureCoverageView:
    payload = report.to_dict() if isinstance(report, FeatureCoverageReport) else _report_mapping(report)
    partition_id = _field_text(payload, "partition_id")
    partitions = _coverage_values(payload, "partition_coverage")
    if not partitions:
        partitions = (partition_id,)
    return _FeatureCoverageView(
        feature_id=_field_text(payload, "feature_id"),
        feature_version_id=_field_text(payload, "feature_version_id"),
        dataset_version_id=_field_text(payload, "dataset_version_id"),
        partition_id=partition_id,
        symbols=_coverage_values(payload, "symbol_coverage"),
        sessions=_coverage_values(payload, "session_coverage"),
        partitions=partitions,
        blocking=_report_findings(payload.get("blocking"), DiagnosticSeverity.BLOCKING),
        non_blocking=_report_findings(
            payload.get("non_blocking"),
            DiagnosticSeverity.NON_BLOCKING,
        ),
    )


def _label_audit_view(report: LabelLeakageAuditReport | Mapping[str, Any]) -> _LabelAuditView:
    payload = report.to_dict() if isinstance(report, LabelLeakageAuditReport) else _report_mapping(report)
    partition_id = _field_text(payload, "partition_id")
    partitions = _coverage_values(payload, "partition_coverage")
    if not partitions:
        partitions = (partition_id,)
    findings = _report_findings(payload.get("findings"), DiagnosticSeverity.BLOCKING)
    return _LabelAuditView(
        label_id=_field_text(payload, "label_id"),
        label_version_id=_field_text(payload, "label_version_id"),
        label_spec_id=_field_text(payload, "label_spec_id"),
        dataset_version_id=_field_text(payload, "dataset_version_id"),
        partition_id=partition_id,
        symbols=_coverage_values(payload, "symbol_coverage"),
        sessions=_coverage_values(payload, "session_coverage"),
        partitions=partitions,
        findings=findings,
        blocked=_bool_field(payload, "blocked") or any(
            finding.severity is DiagnosticSeverity.BLOCKING for finding in findings
        ),
    )


def _report_iterable(value: Iterable[Any], field_name: str) -> tuple[Any, ...]:
    if isinstance(value, str) or not isinstance(value, Iterable):
        raise FeatureLabelDiagnosticsError(f"{field_name} must be an iterable of reports")
    return tuple(value)


def _report_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise FeatureLabelDiagnosticsError("report inputs must be report objects or mappings")
    return value


def _report_findings(
    value: object,
    default_severity: DiagnosticSeverity,
) -> tuple[_ReportFindingView, ...]:
    if value is None:
        return ()
    if isinstance(value, Mapping):
        items: Sequence[object] = (value,)
    elif isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        items = value
    else:
        raise FeatureLabelDiagnosticsError("report findings must be mappings or sequences")
    findings: list[_ReportFindingView] = []
    for item in items:
        if not isinstance(item, Mapping):
            raise FeatureLabelDiagnosticsError("each report finding must be a mapping")
        code = str(item.get("code", item.get("check", ""))).strip()
        if not code:
            raise FeatureLabelDiagnosticsError("report finding requires code or check")
        findings.append(
            _ReportFindingView(
                code=code,
                severity=_coerce_severity(str(item.get("severity", default_severity.value))),
                message=str(item.get("message", "")),
                detail=_json_mapping(_mapping_or_empty(item.get("detail", item.get("offending_reference")))),
            )
        )
    return tuple(findings)


def _coverage_values(payload: Mapping[str, Any], field_name: str) -> tuple[str, ...]:
    value = payload.get(field_name)
    if value is None and isinstance(payload.get("coverage"), Mapping):
        value = _mapping_or_empty(payload.get("coverage")).get(field_name)
    if value is None:
        return ()
    if isinstance(value, Mapping):
        return _sorted_strings(str(key) for key in value)
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        extracted: list[str] = []
        for item in value:
            if isinstance(item, Mapping):
                candidate = item.get("key", item.get("value"))
            else:
                candidate = item
            if candidate is not None:
                extracted.append(str(candidate))
        return _sorted_strings(extracted)
    raise FeatureLabelDiagnosticsError(f"{field_name} must be a sequence or mapping")


def _metric_or_finding_detail(
    report: _FeatureQualityView,
    metric_key: str,
    detail_key: str,
) -> int:
    if metric_key in report.metrics:
        return _nonnegative_metric(report.metrics, metric_key)
    count = 0
    for finding in (*report.blocking, *report.non_blocking):
        if detail_key in finding.detail:
            count += _nonnegative_metric(finding.detail, detail_key)
    return count


def _nonnegative_metric(payload: Mapping[str, Any], key: str) -> int:
    value = payload.get(key, 0)
    if isinstance(value, bool) or not isinstance(value, int | float):
        return 0
    if value < 0:
        raise FeatureLabelDiagnosticsError(f"{key} must be non-negative")
    return int(value)


def _mapping_or_empty(value: object) -> Mapping[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise FeatureLabelDiagnosticsError("expected a mapping payload")
    return value


def _field_text(payload: Mapping[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if value is None and isinstance(payload.get("materialization"), Mapping):
        value = _mapping_or_empty(payload.get("materialization")).get(field_name)
    return _require_text(value, field_name)


def _bool_field(payload: Mapping[str, Any], field_name: str) -> bool:
    value = payload.get(field_name, False)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "blocked", "yes", "1"}
    return False


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FeatureLabelDiagnosticsError(f"{field_name} must be a non-empty string")
    return value.strip()


def _coerce_severity(value: DiagnosticSeverity | str) -> DiagnosticSeverity:
    if isinstance(value, DiagnosticSeverity):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"blocking", "block", "blocked"}:
        return DiagnosticSeverity.BLOCKING
    if normalized in {"non_blocking", "non-blocking", "warning", "info", "clean"}:
        return DiagnosticSeverity.NON_BLOCKING
    raise FeatureLabelDiagnosticsError(f"unsupported diagnostic severity: {value}")


def _blocking(
    code: str,
    message: str,
    detail: Mapping[str, Any] | None = None,
) -> DiagnosticFinding:
    return DiagnosticFinding(
        code=code,
        severity=DiagnosticSeverity.BLOCKING,
        message=message,
        detail=detail or {},
    )


def _non_blocking(
    code: str,
    message: str,
    detail: Mapping[str, Any] | None = None,
) -> DiagnosticFinding:
    return DiagnosticFinding(
        code=code,
        severity=DiagnosticSeverity.NON_BLOCKING,
        message=message,
        detail=detail or {},
    )


def _sorted_strings(values: Iterable[object]) -> tuple[str, ...]:
    return tuple(sorted({str(value).strip() for value in values if str(value).strip()}))


def _json_mapping(value: Mapping[str, Any]) -> dict[str, JsonValue]:
    return {str(key): _json_value(item) for key, item in value.items()}


def _json_value(value: Any) -> JsonValue:
    if value is None or isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Mapping):
        return _json_mapping(value)
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [_json_value(item) for item in value]
    return str(value)


__all__ = [
    "AvailabilityAlignmentDiagnostic",
    "CoverageDimensionOverlap",
    "CoverageOverlapDiagnostic",
    "DiagnosticFinding",
    "DiagnosticSeverity",
    "DiagnosticStatus",
    "FeatureLabelDiagnosticsError",
    "FeatureLabelDiagnosticsReport",
    "MissingnessExposureDiagnostic",
    "build_feature_label_diagnostics",
]
