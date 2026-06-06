"""Session and regime split diagnostics orchestration."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, time
from typing import Any

from alpha_system.research import regimes
from alpha_system.runtime.contracts.run_record import RunRejectionReason, StudyRunResultState
from alpha_system.runtime.diagnostics.contracts import (
    DiagnosticsFamily,
    DiagnosticsRunSpec,
    DiagnosticsRunSpecRef,
)
from alpha_system.runtime.diagnostics.report import (
    DiagnosticsQualityGate,
    DiagnosticsQualityGateStatus,
    DiagnosticsReport,
)
from alpha_system.runtime.input_resolver import RuntimeInputPack

JsonScalar = None | bool | int | float | str

DEFAULT_MIN_SAMPLE_COUNT = 2

_DEFAULT_SESSION_SPLITS_DATA: tuple[tuple[str, str, str, str], ...] = (
    ("session:RTH", "session", "session_label", "RTH"),
    ("session:ETH", "session", "session_label", "ETH"),
    ("segment:open", "segment", "session_segment", "open"),
    ("segment:mid", "segment", "session_segment", "mid"),
    ("segment:close", "segment", "session_segment", "close"),
)

_DEFAULT_REGIME_SPLITS_DATA: tuple[tuple[str, str, str, str], ...] = (
    ("volatility:low", "volatility", "volatility_bucket", "low"),
    ("volatility:high", "volatility", "volatility_bucket", "high"),
    ("spread:narrow", "spread", "spread_bucket", "narrow"),
    ("spread:wide", "spread", "spread_bucket", "wide"),
    ("liquidity:thin", "liquidity", "liquidity_bucket", "thin"),
    ("liquidity:thick", "liquidity", "liquidity_bucket", "thick"),
    ("trend:trend", "trend", "trend_state", "trend"),
    ("trend:range", "trend", "trend_state", "range"),
)

DEFAULT_RTH_WINDOW = {"start": "09:30", "end": "16:00"}
DEFAULT_SEGMENT_WINDOWS: tuple[Mapping[str, str], ...] = (
    {"name": "open", "start": "09:30", "end": "10:30"},
    {"name": "mid", "start": "10:30", "end": "15:00"},
    {"name": "close", "start": "15:00", "end": "16:00"},
)

_FORBIDDEN_CONDITIONING_FIELDS = {
    "future_return",
    "forward_return",
    "label_available_ts",
    "label_value",
    "outcome",
    "target",
}


class SplitDiagnosticsError(ValueError):
    """Raised when split diagnostics cannot be assembled from safe metadata."""


@dataclass(frozen=True, slots=True)
class SplitDefinition:
    """One metadata-driven split bucket."""

    split_id: str
    family: str
    field: str
    bucket: str
    required: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "split_id", _required_text(self.split_id, "split_id"))
        object.__setattr__(self, "family", _required_text(self.family, "family"))
        object.__setattr__(self, "field", _required_text(self.field, "field"))
        object.__setattr__(self, "bucket", _required_text(self.bucket, "bucket"))
        if type(self.required) is not bool:
            raise SplitDiagnosticsError("required must be a bool")


@dataclass(frozen=True, slots=True)
class SplitBucketSummary:
    """Scalar-only descriptive summary for one split bucket."""

    split_id: str
    family: str
    bucket: str
    conditioning_field: str
    status: str
    sample_count: int
    total_observation_count: int
    coverage_ratio: float | None
    missingness_rate: float | None
    primitive_with_filter_count: int
    primitive_without_filter_count: int
    primitive_retained_count: int
    primitive_total_count: int
    uplift: float | None
    conditional_mean_delta: float | None
    conditional_hit_rate_delta: float | None
    false_rejection_rate: float | None
    rejection_reason_code: str | None = None
    rejection_reason_message: str | None = None

    def to_dict(self) -> dict[str, JsonScalar]:
        """Return a stable scalar-only split summary."""

        return {
            "split_id": self.split_id,
            "family": self.family,
            "bucket": self.bucket,
            "conditioning_field": self.conditioning_field,
            "status": self.status,
            "sample_count": self.sample_count,
            "total_observation_count": self.total_observation_count,
            "coverage_ratio": self.coverage_ratio,
            "missingness_rate": self.missingness_rate,
            "primitive_with_filter_count": self.primitive_with_filter_count,
            "primitive_without_filter_count": self.primitive_without_filter_count,
            "primitive_retained_count": self.primitive_retained_count,
            "primitive_total_count": self.primitive_total_count,
            "uplift": self.uplift,
            "conditional_mean_delta": self.conditional_mean_delta,
            "conditional_hit_rate_delta": self.conditional_hit_rate_delta,
            "false_rejection_rate": self.false_rejection_rate,
            "rejection_reason_code": self.rejection_reason_code,
            "rejection_reason_message": self.rejection_reason_message,
        }


@dataclass(frozen=True, slots=True)
class _SplitDiagnosticsReport:
    common_report: DiagnosticsReport
    split_summaries: tuple[SplitBucketSummary, ...]

    @property
    def report_id(self) -> str:
        return self.common_report.report_id

    @property
    def report_hash(self) -> str:
        return self.common_report.report_hash

    @property
    def report_kind(self) -> str:
        return self.common_report.report_kind

    @property
    def diagnostics_family(self) -> DiagnosticsFamily:
        return self.common_report.diagnostics_family

    @property
    def status(self) -> StudyRunResultState:
        return self.common_report.status

    @property
    def lineage_refs(self) -> dict[str, str]:
        return self.common_report.lineage_refs

    @property
    def coverage_summary(self) -> dict[str, JsonScalar]:
        return self.common_report.coverage_summary

    @property
    def quality_summary(self) -> dict[str, JsonScalar]:
        return self.common_report.quality_summary

    @property
    def limitations(self) -> tuple[str, ...]:
        return self.common_report.limitations

    @property
    def quality_gates(self) -> tuple[DiagnosticsQualityGate, ...]:
        return self.common_report.quality_gates

    @property
    def rejection_reasons(self) -> tuple[RunRejectionReason, ...]:
        return self.common_report.rejection_reasons

    @property
    def report_metadata(self) -> dict[str, JsonScalar]:
        return self.common_report.report_metadata

    def to_ref(self):
        """Return the shared diagnostics report reference."""

        return self.common_report.to_ref()

    def to_dict(self) -> dict[str, object]:
        """Return the shared report payload plus scalar split summaries."""

        payload = self.common_report.to_dict()
        payload["split_summaries"] = [summary.to_dict() for summary in self.split_summaries]
        payload["split_summary_count"] = len(self.split_summaries)
        return payload


@dataclass(frozen=True, slots=True)
class SessionSplitReport(_SplitDiagnosticsReport):
    """Descriptive RTH/ETH and intraday-segment split report."""


@dataclass(frozen=True, slots=True)
class RegimeSplitReport(_SplitDiagnosticsReport):
    """Descriptive volatility/spread/liquidity/trend split report."""


def build_split_diagnostics_reports(
    *,
    diagnostics_run_spec_ref: DiagnosticsRunSpec | DiagnosticsRunSpecRef | Mapping[str, Any],
    runtime_input_pack: RuntimeInputPack | Mapping[str, Any],
    observations: Iterable[Mapping[str, Any]],
    min_sample_count: int = DEFAULT_MIN_SAMPLE_COUNT,
    session_splits: Sequence[SplitDefinition] | None = None,
    regime_splits: Sequence[SplitDefinition] | None = None,
) -> tuple[SessionSplitReport, RegimeSplitReport]:
    """Build both split report families from one resolved runtime input pack."""

    cached_observations = tuple(observations)
    return (
        build_session_split_report(
            diagnostics_run_spec_ref=diagnostics_run_spec_ref,
            runtime_input_pack=runtime_input_pack,
            observations=cached_observations,
            min_sample_count=min_sample_count,
            split_definitions=session_splits,
        ),
        build_regime_split_report(
            diagnostics_run_spec_ref=diagnostics_run_spec_ref,
            runtime_input_pack=runtime_input_pack,
            observations=cached_observations,
            min_sample_count=min_sample_count,
            split_definitions=regime_splits,
        ),
    )


def build_session_split_report(
    *,
    diagnostics_run_spec_ref: DiagnosticsRunSpec | DiagnosticsRunSpecRef | Mapping[str, Any],
    runtime_input_pack: RuntimeInputPack | Mapping[str, Any],
    observations: Iterable[Mapping[str, Any]],
    min_sample_count: int = DEFAULT_MIN_SAMPLE_COUNT,
    split_definitions: Sequence[SplitDefinition] | None = None,
) -> SessionSplitReport:
    """Build the RTH/ETH and intraday segment split diagnostics report."""

    return _build_split_report(
        report_cls=SessionSplitReport,
        report_kind="session_split_diagnostics_summary",
        diagnostics_run_spec_ref=diagnostics_run_spec_ref,
        runtime_input_pack=runtime_input_pack,
        observations=observations,
        split_definitions=split_definitions or default_session_split_definitions(),
        min_sample_count=min_sample_count,
    )


def build_regime_split_report(
    *,
    diagnostics_run_spec_ref: DiagnosticsRunSpec | DiagnosticsRunSpecRef | Mapping[str, Any],
    runtime_input_pack: RuntimeInputPack | Mapping[str, Any],
    observations: Iterable[Mapping[str, Any]],
    min_sample_count: int = DEFAULT_MIN_SAMPLE_COUNT,
    split_definitions: Sequence[SplitDefinition] | None = None,
) -> RegimeSplitReport:
    """Build the volatility/spread/liquidity/trend split diagnostics report."""

    return _build_split_report(
        report_cls=RegimeSplitReport,
        report_kind="regime_split_diagnostics_summary",
        diagnostics_run_spec_ref=diagnostics_run_spec_ref,
        runtime_input_pack=runtime_input_pack,
        observations=observations,
        split_definitions=split_definitions or default_regime_split_definitions(),
        min_sample_count=min_sample_count,
    )


def default_session_split_definitions() -> tuple[SplitDefinition, ...]:
    """Return the default RTH/ETH and open/mid/close split definitions."""

    return tuple(SplitDefinition(*item) for item in _DEFAULT_SESSION_SPLITS_DATA)


def default_regime_split_definitions() -> tuple[SplitDefinition, ...]:
    """Return the default descriptive regime split definitions."""

    return tuple(SplitDefinition(*item) for item in _DEFAULT_REGIME_SPLITS_DATA)


def _build_split_report(
    *,
    report_cls: type[SessionSplitReport] | type[RegimeSplitReport],
    report_kind: str,
    diagnostics_run_spec_ref: DiagnosticsRunSpec | DiagnosticsRunSpecRef | Mapping[str, Any],
    runtime_input_pack: RuntimeInputPack | Mapping[str, Any],
    observations: Iterable[Mapping[str, Any]],
    split_definitions: Sequence[SplitDefinition],
    min_sample_count: int,
) -> SessionSplitReport | RegimeSplitReport:
    _validate_min_sample_count(min_sample_count)
    spec_ref = _coerce_spec_ref(diagnostics_run_spec_ref)
    session_scope = _session_scope(runtime_input_pack)
    all_observations = tuple(observations)
    rows, availability_reasons = _eligible_rows(all_observations)
    definition_reasons = _definition_reasons(split_definitions)
    split_summaries = tuple(
        _summarize_split(
            definition=definition,
            observations=rows,
            session_scope=session_scope,
            min_sample_count=min_sample_count,
        )
        for definition in split_definitions
        if _conditioning_field_allowed(definition.field)
    )

    split_reasons = _split_reasons(split_summaries)
    reasons = tuple(_unique_reasons((*availability_reasons, *definition_reasons, *split_reasons)))
    failed_count = sum(1 for summary in split_summaries if summary.status != "reported")
    reported_count = sum(1 for summary in split_summaries if summary.status == "reported")
    status, gate_status = _report_status(reasons)

    common_report = DiagnosticsReport(
        report_kind=report_kind,
        diagnostics_family=DiagnosticsFamily.SPLITS,
        diagnostics_run_spec_ref=spec_ref,
        status=status,
        lineage_refs=_lineage_refs(runtime_input_pack, spec_ref),
        coverage_summary={
            "total_observation_count": len(all_observations),
            "eligible_observation_count": len(rows),
            "sample_count": sum(summary.sample_count for summary in split_summaries),
            "coverage_ratio": _coverage_ratio(len(rows), len(all_observations)),
            "missingness_rate": _missingness_rate(
                len(all_observations) - len(rows),
                len(all_observations),
            ),
            "minimum_split_sample_count": min_sample_count,
        },
        quality_summary={
            "split_count": len(split_summaries),
            "reported_split_count": reported_count,
            "failed_split_count": failed_count,
            "low_sample_split_count": sum(
                1 for summary in split_summaries if summary.rejection_reason_code == "low_sample"
            ),
            "primitive_call_count": len(split_summaries) * 4,
            "descriptive_only": True,
        },
        limitations=_limitations(),
        quality_gates=[
            DiagnosticsQualityGate(
                gate_id="split_coverage_gate",
                name="Split coverage gate",
                status=gate_status,
                summary=_gate_summary(gate_status),
                metric_refs={
                    "split_count": len(split_summaries),
                    "reported_split_count": reported_count,
                    "failed_split_count": failed_count,
                    "minimum_split_sample_count": min_sample_count,
                },
                limitations=_limitations(),
            )
        ],
        rejection_reasons=reasons,
        report_metadata={
            "conditioning_time_reference": "available_ts",
            "label_outcome_guard": "label_available_ts",
            "orchestrated_primitive_module": "alpha_system.research.regimes",
            "raw_or_heavy_payload": False,
        },
    )
    return report_cls(common_report=common_report, split_summaries=split_summaries)


def _summarize_split(
    *,
    definition: SplitDefinition,
    observations: Sequence[Mapping[str, Any]],
    session_scope: Mapping[str, Any],
    min_sample_count: int,
) -> SplitBucketSummary:
    primitive_rows: list[Mapping[str, Any]] = []
    missing_count = 0
    for row in observations:
        bucket = _bucket_for_row(row, definition=definition, session_scope=session_scope)
        if bucket is None:
            missing_count += 1
            active = False
        else:
            active = _normalized(bucket) == _normalized(definition.bucket)
        primitive_rows.append(_primitive_row(row, active=active))

    coverage = regimes.regime_filter_coverage(primitive_rows)
    uplift = regimes.regime_filter_uplift(primitive_rows)
    false_rejection = regimes.false_rejection_rate(primitive_rows)
    conditional = regimes.conditional_strategy_improvement(primitive_rows)

    sample_count = _int_metric(coverage.get("retained"))
    total_count = _int_metric(coverage.get("total"))
    status = "reported"
    reason_code = None
    reason_message = None
    if sample_count < min_sample_count:
        status = "inconclusive"
        reason_code = "low_sample"
        reason_message = (
            f"{definition.split_id} has {sample_count} observations below the configured "
            f"minimum of {min_sample_count}."
        )
    if total_count == 0:
        status = "inconclusive"
        reason_code = "data_unavailable"
        reason_message = f"{definition.split_id} has no eligible observations."

    return SplitBucketSummary(
        split_id=definition.split_id,
        family=definition.family,
        bucket=definition.bucket,
        conditioning_field=definition.field,
        status=status,
        sample_count=sample_count,
        total_observation_count=total_count,
        coverage_ratio=_float_metric(coverage.get("coverage")),
        missingness_rate=_missingness_rate(missing_count, len(observations)),
        primitive_with_filter_count=_int_metric(uplift.get("with_filter_n")),
        primitive_without_filter_count=_int_metric(uplift.get("without_filter_n")),
        primitive_retained_count=_int_metric(conditional.get("retained_n")),
        primitive_total_count=_int_metric(conditional.get("all_n")),
        uplift=_float_metric(uplift.get("uplift")),
        conditional_mean_delta=_float_metric(conditional.get("mean_return_improvement")),
        conditional_hit_rate_delta=_float_metric(conditional.get("hit_rate_improvement")),
        false_rejection_rate=_float_metric(false_rejection.get("false_rejection_rate")),
        rejection_reason_code=reason_code,
        rejection_reason_message=reason_message,
    )


def _eligible_rows(
    observations: Iterable[Mapping[str, Any]],
) -> tuple[tuple[Mapping[str, Any], ...], tuple[RunRejectionReason, ...]]:
    rows: list[Mapping[str, Any]] = []
    reasons: list[RunRejectionReason] = []
    missing_available = 0
    label_order_violations = 0
    for row in observations:
        available_ts = _parse_datetime(row.get("available_ts"))
        if available_ts is None:
            missing_available += 1
            continue
        label_available_ts = _parse_datetime(row.get("label_available_ts"))
        if label_available_ts is not None and label_available_ts < available_ts:
            label_order_violations += 1
            continue
        rows.append(row)

    if missing_available:
        reasons.append(
            RunRejectionReason(
                code="data_unavailable",
                message=(
                    f"{missing_available} observations lack available_ts and were excluded "
                    "from split conditioning."
                ),
            )
        )
    if label_order_violations:
        reasons.append(
            RunRejectionReason(
                code="leakage_risk",
                message=(
                    f"{label_order_violations} observations have label_available_ts before "
                    "available_ts and were excluded from split conditioning."
                ),
            )
        )
    if not rows:
        reasons.append(
            RunRejectionReason(
                code="data_unavailable",
                message="Split diagnostics require at least one observation with available_ts.",
            )
        )
    return tuple(rows), tuple(reasons)


def _primitive_row(row: Mapping[str, Any], *, active: bool) -> Mapping[str, Any]:
    primitive: dict[str, Any] = {"regime_filter": active}
    for field in ("factor_value", "forward_return", "label_value"):
        if field in row:
            primitive[field] = row[field]
    return primitive


def _bucket_for_row(
    row: Mapping[str, Any],
    *,
    definition: SplitDefinition,
    session_scope: Mapping[str, Any],
) -> str | None:
    if definition.family == "session":
        return _session_label(row, session_scope=session_scope)
    if definition.family == "segment":
        return _session_segment(row, session_scope=session_scope)
    value = row.get(definition.field)
    return None if value is None else str(value)


def _session_label(row: Mapping[str, Any], *, session_scope: Mapping[str, Any]) -> str | None:
    if row.get("session_label") is not None:
        return str(row["session_label"])
    available_ts = _parse_datetime(row.get("available_ts"))
    if available_ts is None:
        return None
    rth_window = _mapping(session_scope.get("rth")) or DEFAULT_RTH_WINDOW
    start = _parse_time(rth_window.get("start"))
    end = _parse_time(rth_window.get("end"))
    if start is None or end is None:
        return None
    return "RTH" if _time_in_window(available_ts.timetz().replace(tzinfo=None), start, end) else "ETH"


def _session_segment(row: Mapping[str, Any], *, session_scope: Mapping[str, Any]) -> str | None:
    if row.get("session_segment") is not None:
        return str(row["session_segment"])
    available_ts = _parse_datetime(row.get("available_ts"))
    if available_ts is None:
        return None
    windows = _segment_windows(session_scope)
    for window in windows:
        name = window.get("name")
        start = _parse_time(window.get("start"))
        end = _parse_time(window.get("end"))
        if name and start is not None and end is not None:
            if _time_in_window(available_ts.timetz().replace(tzinfo=None), start, end):
                return str(name)
    return None


def _segment_windows(session_scope: Mapping[str, Any]) -> tuple[Mapping[str, str], ...]:
    raw_windows = session_scope.get("segments") or session_scope.get("segment_windows")
    if isinstance(raw_windows, Sequence) and not isinstance(raw_windows, str):
        windows: list[Mapping[str, str]] = []
        for item in raw_windows:
            if isinstance(item, Mapping):
                windows.append(
                    {
                        "name": str(item.get("name", "")),
                        "start": str(item.get("start", "")),
                        "end": str(item.get("end", "")),
                    }
                )
        if windows:
            return tuple(windows)
    return DEFAULT_SEGMENT_WINDOWS


def _definition_reasons(
    definitions: Sequence[SplitDefinition],
) -> tuple[RunRejectionReason, ...]:
    reasons: list[RunRejectionReason] = []
    for definition in definitions:
        if not _conditioning_field_allowed(definition.field):
            reasons.append(
                RunRejectionReason(
                    code="leakage_risk",
                    message=(
                        f"{definition.split_id} uses prohibited conditioning field "
                        f"{definition.field}; label and future outcome fields are not split inputs."
                    ),
                )
            )
    return tuple(reasons)


def _conditioning_field_allowed(field: str) -> bool:
    normalized = _normalized(field)
    if normalized in _FORBIDDEN_CONDITIONING_FIELDS:
        return False
    if normalized.startswith("label_"):
        return False
    if normalized.endswith("_label") and normalized != "session_label":
        return False
    return "future" not in normalized


def _split_reasons(summaries: Sequence[SplitBucketSummary]) -> tuple[RunRejectionReason, ...]:
    reasons: list[RunRejectionReason] = []
    for summary in summaries:
        if summary.rejection_reason_code and summary.rejection_reason_message:
            reasons.append(
                RunRejectionReason(
                    code=summary.rejection_reason_code,
                    message=summary.rejection_reason_message,
                )
            )
    return tuple(reasons)


def _unique_reasons(reasons: Sequence[RunRejectionReason]) -> tuple[RunRejectionReason, ...]:
    seen: set[tuple[str, str]] = set()
    unique: list[RunRejectionReason] = []
    for reason in reasons:
        key = (reason.code, reason.message)
        if key not in seen:
            seen.add(key)
            unique.append(reason)
    return tuple(unique)


def _report_status(
    reasons: Sequence[RunRejectionReason],
) -> tuple[StudyRunResultState, DiagnosticsQualityGateStatus]:
    if any(reason.code == "leakage_risk" for reason in reasons):
        return StudyRunResultState.REJECTED, DiagnosticsQualityGateStatus.FAIL
    if reasons:
        return StudyRunResultState.INCONCLUSIVE, DiagnosticsQualityGateStatus.INCONCLUSIVE
    return StudyRunResultState.DIAGNOSTICS_COMPLETE, DiagnosticsQualityGateStatus.PASS


def _gate_summary(status: DiagnosticsQualityGateStatus) -> str:
    if status is DiagnosticsQualityGateStatus.PASS:
        return "Configured split summaries were reported with sufficient descriptive coverage."
    if status is DiagnosticsQualityGateStatus.FAIL:
        return "Split conditioning was rejected because an unsafe conditioning field was requested."
    return "One or more split summaries could not meet the configured descriptive coverage gate."


def _limitations() -> tuple[str, ...]:
    return (
        "Split diagnostics are descriptive summaries of heterogeneity only.",
        "A diagnostics gate result is not validation of an alpha claim.",
        "No recommendation, deployment conclusion, or strategy-conditioning claim is made.",
        "Split assignment uses available_ts metadata and label_available_ts is only an outcome guard.",
    )


def _lineage_refs(
    runtime_input_pack: RuntimeInputPack | Mapping[str, Any],
    spec_ref: DiagnosticsRunSpecRef,
) -> dict[str, str]:
    return {
        "diagnostics_run_spec_id": spec_ref.diagnostics_run_spec_id,
        "dataset_version_id": _pack_text(runtime_input_pack, "dataset_version_id", "unavailable"),
        "alpha_spec_ref": _pack_text(runtime_input_pack, "alpha_spec_ref", "unavailable"),
        "study_spec_ref": _pack_text(runtime_input_pack, "study_spec_ref", "unavailable"),
        "feature_pack_ref": _pack_member_refs(runtime_input_pack, "feature_packs"),
        "label_pack_ref": _pack_member_refs(runtime_input_pack, "label_packs"),
    }


def _pack_text(
    runtime_input_pack: RuntimeInputPack | Mapping[str, Any],
    field: str,
    fallback: str,
) -> str:
    if isinstance(runtime_input_pack, Mapping):
        value = runtime_input_pack.get(field, fallback)
    else:
        value = getattr(runtime_input_pack, field, fallback)
    return fallback if value is None else str(value)


def _pack_member_refs(runtime_input_pack: RuntimeInputPack | Mapping[str, Any], field: str) -> str:
    if isinstance(runtime_input_pack, Mapping):
        members = runtime_input_pack.get(field, ())
    else:
        members = getattr(runtime_input_pack, field, ())
    refs: list[str] = []
    if isinstance(members, Sequence) and not isinstance(members, str):
        for member in members:
            if isinstance(member, Mapping):
                refs.append(str(member.get("feature_version_id") or member.get("label_version_id")))
            else:
                refs.append(
                    str(
                        getattr(
                            member,
                            "feature_version_id",
                            getattr(member, "label_version_id", "unavailable"),
                        )
                    )
                )
    return ",".join(ref for ref in refs if ref and ref != "None") or "none"


def _session_scope(runtime_input_pack: RuntimeInputPack | Mapping[str, Any]) -> Mapping[str, Any]:
    if isinstance(runtime_input_pack, Mapping):
        raw_scope = runtime_input_pack.get("session_scope", {})
        return raw_scope if isinstance(raw_scope, Mapping) else {}
    return runtime_input_pack.session_scope


def _coerce_spec_ref(
    value: DiagnosticsRunSpec | DiagnosticsRunSpecRef | Mapping[str, Any],
) -> DiagnosticsRunSpecRef:
    if isinstance(value, DiagnosticsRunSpec):
        return value.to_ref()
    if isinstance(value, DiagnosticsRunSpecRef):
        return value
    if isinstance(value, Mapping):
        return DiagnosticsRunSpecRef(
            diagnostics_run_spec_id=value.get("diagnostics_run_spec_id"),
            content_hash=value.get("content_hash"),
        )
    raise SplitDiagnosticsError("diagnostics_run_spec_ref must be a diagnostics spec reference")


def _validate_min_sample_count(value: int) -> None:
    if not isinstance(value, int) or value < 1:
        raise SplitDiagnosticsError("min_sample_count must be a positive integer")


def _coverage_ratio(selected_count: int, total_count: int) -> float | None:
    return None if total_count == 0 else selected_count / total_count


def _missingness_rate(missing_count: int, total_count: int) -> float | None:
    return None if total_count == 0 else missing_count / total_count


def _int_metric(value: object) -> int:
    if value is None:
        return 0
    if isinstance(value, bool):
        return int(value)
    return int(value)


def _float_metric(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return float(value)
    return float(value)


def _parse_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _parse_time(value: object) -> time | None:
    if isinstance(value, time):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    parts = value.strip().split(":")
    if len(parts) < 2:
        return None
    try:
        return time(hour=int(parts[0]), minute=int(parts[1]))
    except ValueError:
        return None


def _time_in_window(value: time, start: time, end: time) -> bool:
    if start <= end:
        return start <= value < end
    return value >= start or value < end


def _mapping(value: object) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SplitDiagnosticsError(f"{field} is required")
    return value.strip()


def _normalized(value: object) -> str:
    return str(value).strip().lower().replace("-", "_")


__all__ = [
    "DEFAULT_MIN_SAMPLE_COUNT",
    "RegimeSplitReport",
    "SessionSplitReport",
    "SplitBucketSummary",
    "SplitDefinition",
    "SplitDiagnosticsError",
    "build_regime_split_report",
    "build_session_split_report",
    "build_split_diagnostics_reports",
    "default_regime_split_definitions",
    "default_session_split_definitions",
]
