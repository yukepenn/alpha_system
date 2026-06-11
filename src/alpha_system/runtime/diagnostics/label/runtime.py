"""Label diagnostics runtime built on shared diagnostics contracts.

The runtime summarizes resolved, local label diagnostics inputs. It delegates
feature/label alignment, leakage, and missingness checks to
``alpha_system.research.feature_label_diagnostics`` and path summaries to
``alpha_system.research.events``. It does not materialize labels, call
providers, or expose label outcomes as live feature inputs.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from alpha_system.research.events import post_event_mfe_mae, target_before_stop_probability
from alpha_system.research.feature_label_diagnostics import (
    FeatureLabelDiagnosticsError,
    FeatureLabelDiagnosticsReport,
    build_feature_label_diagnostics,
)
from alpha_system.runtime.contracts.run_record import RunRejectionReason, StudyRunResultState
from alpha_system.runtime.diagnostics.contracts import (
    DiagnosticsFamily,
    DiagnosticsRunRecord,
    DiagnosticsRunSpec,
    DiagnosticsRunSpecRef,
)
from alpha_system.runtime.diagnostics.report import (
    DiagnosticsQualityGate,
    DiagnosticsQualityGateStatus,
    DiagnosticsReport,
)
from alpha_system.runtime.diagnostics.splits.n_eff import (
    NEffSampleReportingError,
    build_n_eff_sample_report,
)
from alpha_system.runtime.entry_contract import ACCEPTED_DATASET_VERSION_LIFECYCLE_STATES
from alpha_system.runtime.input_resolver import RuntimeInputPack

JsonScalar = None | bool | int | float | str
ScalarSummary = tuple[tuple[str, JsonScalar], ...]

LABEL_DIAGNOSTICS_REPORT_KIND = "label_diagnostics_summary"
DEFAULT_LIMITATIONS = (
    "Descriptive label diagnostics only; quality gates are not promotion decisions.",
    "The runtime summarizes supplied diagnostics and references; it does not materialize labels.",
    "Coverage and leakage results depend on upstream registered label audits and input resolution.",
)
LABEL_AS_FEATURE_REFERENCE_TOKENS = frozenset(
    {
        "label",
        "label_available_ts",
        "label_outcome",
        "label_value",
        "horizon_end_ts",
        "target",
    }
)


class LabelDiagnosticsRuntimeError(ValueError):
    """Raised when the label diagnostics runtime cannot build a valid report."""


@dataclass(frozen=True, slots=True)
class LabelDiagnosticsConfig:
    """Fail-closed scalar thresholds for label diagnostics summaries."""

    min_sample_count: int = 1
    max_majority_class_share: float = 0.95
    min_horizon_coverage_ratio: float = 0.80
    require_label_audit: bool = True
    require_feature_label_coverage: bool = True
    require_cost_adjustment_metadata: bool = True
    allow_missing_path_metrics: bool = True
    limitations: tuple[str, ...] = DEFAULT_LIMITATIONS

    def __post_init__(self) -> None:
        if isinstance(self.min_sample_count, bool) or self.min_sample_count < 1:
            raise LabelDiagnosticsRuntimeError("min_sample_count must be a positive integer")
        _ratio(self.max_majority_class_share, "max_majority_class_share")
        _ratio(self.min_horizon_coverage_ratio, "min_horizon_coverage_ratio")
        if not self.limitations:
            raise LabelDiagnosticsRuntimeError("limitations must not be empty")
        object.__setattr__(
            self,
            "limitations",
            tuple(_text(item, "limitations") for item in self.limitations),
        )


@dataclass(frozen=True, slots=True)
class LabelDiagnosticsReport:
    """Label-specific diagnostics report plus visible runtime record."""

    diagnostics_report: DiagnosticsReport
    diagnostics_run_record: DiagnosticsRunRecord
    distribution_summary_items: ScalarSummary
    horizon_coverage_items: ScalarSummary
    class_balance_items: ScalarSummary
    mfe_mae_summary_items: ScalarSummary
    path_ambiguity_summary_items: ScalarSummary
    label_available_ts_validity_items: ScalarSummary
    cost_adjustment_sanity_items: ScalarSummary
    coverage_missingness_items: ScalarSummary
    n_eff_report: Mapping[str, object] | None = None

    @property
    def distribution_summary(self) -> dict[str, JsonScalar]:
        return _items_to_dict(self.distribution_summary_items)

    @property
    def horizon_coverage(self) -> dict[str, JsonScalar]:
        return _items_to_dict(self.horizon_coverage_items)

    @property
    def class_balance(self) -> dict[str, JsonScalar]:
        return _items_to_dict(self.class_balance_items)

    @property
    def mfe_mae_summary(self) -> dict[str, JsonScalar]:
        return _items_to_dict(self.mfe_mae_summary_items)

    @property
    def path_ambiguity_summary(self) -> dict[str, JsonScalar]:
        return _items_to_dict(self.path_ambiguity_summary_items)

    @property
    def label_available_ts_validity(self) -> dict[str, JsonScalar]:
        return _items_to_dict(self.label_available_ts_validity_items)

    @property
    def cost_adjustment_sanity(self) -> dict[str, JsonScalar]:
        return _items_to_dict(self.cost_adjustment_sanity_items)

    @property
    def coverage_missingness(self) -> dict[str, JsonScalar]:
        return _items_to_dict(self.coverage_missingness_items)

    @property
    def status(self) -> StudyRunResultState:
        return self.diagnostics_report.status

    @property
    def rejection_reasons(self) -> tuple[RunRejectionReason, ...]:
        return self.diagnostics_report.rejection_reasons

    def to_dict(self) -> dict[str, object]:
        """Return a value-free label diagnostics payload."""

        payload = self.diagnostics_report.to_dict()
        payload.update(
            {
                "label_distribution_summary": self.distribution_summary,
                "label_horizon_coverage": self.horizon_coverage,
                "label_class_balance": self.class_balance,
                "label_mfe_mae_summary": self.mfe_mae_summary,
                "label_path_ambiguity_summary": self.path_ambiguity_summary,
                "label_available_ts_validity": self.label_available_ts_validity,
                "label_cost_adjustment_sanity": self.cost_adjustment_sanity,
                "label_coverage_missingness": self.coverage_missingness,
                "diagnostics_run_record": self.diagnostics_run_record.to_dict(),
            }
        )
        if self.n_eff_report is not None:
            payload["label_n_eff_report"] = dict(self.n_eff_report)
        return payload


def build_label_diagnostics_report(
    *,
    diagnostics_run_spec: DiagnosticsRunSpec | DiagnosticsRunSpecRef | Mapping[str, Any],
    runtime_input_pack: RuntimeInputPack,
    feature_quality_reports: Iterable[Mapping[str, Any]] = (),
    feature_coverage_reports: Iterable[Mapping[str, Any]] = (),
    label_audit_reports: Iterable[Mapping[str, Any]] = (),
    label_observations: Iterable[Mapping[str, Any]] = (),
    label_profiles: Iterable[Mapping[str, Any]] | Mapping[str, Any] = (),
    live_feature_references: Iterable[Any] | Mapping[str, Any] = (),
    n_eff_overlap_metadata: Any = None,
    walk_forward_metadata: Any = None,
    config: LabelDiagnosticsConfig | Mapping[str, Any] | None = None,
) -> LabelDiagnosticsReport:
    """Build a descriptive label diagnostics report from resolved runtime inputs."""

    active_config = _coerce_config(config)
    spec_ref = _diagnostics_spec_ref(diagnostics_run_spec)
    _require_label_family(diagnostics_run_spec)

    reasons: list[RunRejectionReason] = []
    _extend_unique(reasons, _runtime_input_reasons(runtime_input_pack))

    observations = _observation_mappings(label_observations, reasons)
    profiles = _profile_mappings(label_profiles, reasons)
    _extend_unique(reasons, _label_availability_reasons(observations))
    _extend_unique(
        reasons,
        _label_as_feature_reference_reasons(
            live_feature_references=live_feature_references,
            runtime_input_pack=runtime_input_pack,
        ),
    )

    feature_label_report = _build_feature_label_report(
        feature_quality_reports=feature_quality_reports,
        feature_coverage_reports=feature_coverage_reports,
        label_audit_reports=label_audit_reports,
        reasons=reasons,
    )
    if feature_label_report is not None:
        _extend_unique(
            reasons,
            _feature_label_report_reasons(
                feature_label_report,
                config=active_config,
            ),
        )

    distribution = _distribution_summary(observations)
    class_balance = _class_balance_summary(distribution)
    horizon = _horizon_coverage_summary(observations)
    mfe_mae = _mfe_mae_summary(observations)
    path_ambiguity = _path_ambiguity_summary(observations)
    cost_sanity = _cost_adjustment_sanity(observations=observations, profiles=profiles)
    n_eff_report, n_eff_reasons = _n_eff_report(
        observations=observations,
        n_eff_overlap_metadata=n_eff_overlap_metadata,
        walk_forward_metadata=walk_forward_metadata,
    )
    _extend_unique(reasons, n_eff_reasons)
    availability = _availability_summary(
        runtime_input_pack=runtime_input_pack,
        observations=observations,
        reasons=reasons,
    )
    coverage_missingness = _coverage_missingness_summary(
        feature_label_report=feature_label_report,
        distribution_summary=distribution,
    )

    _extend_unique(
        reasons,
        _summary_reasons(
            distribution_summary=distribution,
            class_balance=class_balance,
            horizon_coverage=horizon,
            cost_sanity=cost_sanity,
            config=active_config,
        ),
    )

    status = _status_from_reasons(reasons)
    gates = _quality_gates(
        status=status,
        distribution_summary=distribution,
        class_balance=class_balance,
        horizon_coverage=horizon,
        mfe_mae_summary=mfe_mae,
        path_ambiguity_summary=path_ambiguity,
        availability_summary=availability,
        cost_sanity=cost_sanity,
        coverage_missingness=coverage_missingness,
        feature_label_report=feature_label_report,
        config=active_config,
    )
    failing_gate_count = sum(
        1 for gate in gates if gate.status is DiagnosticsQualityGateStatus.FAIL
    )
    inconclusive_gate_count = sum(
        1 for gate in gates if gate.status is DiagnosticsQualityGateStatus.INCONCLUSIVE
    )
    quality_summary = _summary_items(
        {
            "diagnostic_complete": status is StudyRunResultState.DIAGNOSTICS_COMPLETE,
            "gate_count": len(gates),
            "failing_gate_count": failing_gate_count,
            "inconclusive_gate_count": inconclusive_gate_count,
            "sample_count": distribution["sample_count"],
            "observed_outcome_count": distribution["observed_outcome_count"],
            "class_count": class_balance["class_count"],
            "majority_class_share": class_balance["majority_class_share"],
            "horizon_count": horizon["horizon_count"],
            "mfe_sample_count": mfe_mae["mfe_sample_count"],
            "mae_sample_count": mfe_mae["mae_sample_count"],
            "path_ambiguous_count": path_ambiguity["ambiguous_path_count"],
            "label_available_ts_valid": availability["label_available_ts_valid"],
            "cost_model_declared_count": cost_sanity["cost_model_declared_count"],
            "rejection_reason_count": len(reasons),
        }
    )
    coverage_summary = _summary_items(
        {
            "label_pack_count": len(runtime_input_pack.label_packs),
            "audit_label_count": coverage_missingness["audit_label_count"],
            "sample_count": distribution["sample_count"],
            "missing_outcome_count": distribution["missing_outcome_count"],
            "missing_outcome_rate": distribution["missing_outcome_rate"],
            "shared_dataset_ref_count": coverage_missingness["shared_dataset_ref_count"],
            "shared_partition_ref_count": coverage_missingness["shared_partition_ref_count"],
            "symbol_overlap_count": coverage_missingness["symbol_overlap_count"],
            "session_overlap_count": coverage_missingness["session_overlap_count"],
            "partition_overlap_count": coverage_missingness["partition_overlap_count"],
            "missing_bbo_count": coverage_missingness["missing_bbo_count"],
            "bbo_quarantined_count": coverage_missingness["bbo_quarantined_count"],
            "synthetic_no_trade_count": coverage_missingness["synthetic_no_trade_count"],
        }
    )

    report_metadata: dict[str, JsonScalar] = {
        "uses_research_feature_label_diagnostics": True,
        "uses_research_events_post_event_mfe_mae": True,
        "uses_research_events_target_before_stop_probability": True,
        "label_materialization_performed": False,
        "external_provider_call_performed": False,
    }
    if n_eff_overlap_metadata is not None or walk_forward_metadata is not None:
        report_metadata["n_eff_reporting"] = "reported" if n_eff_report is not None else "failed"

    report = DiagnosticsReport(
        report_kind=LABEL_DIAGNOSTICS_REPORT_KIND,
        diagnostics_family=DiagnosticsFamily.LABEL,
        diagnostics_run_spec_ref=spec_ref,
        status=status,
        lineage_refs=_lineage_refs(spec_ref, runtime_input_pack),
        coverage_summary=_items_to_dict(coverage_summary),
        quality_summary=_items_to_dict(quality_summary),
        limitations=active_config.limitations,
        quality_gates=gates,
        rejection_reasons=tuple(reasons),
        report_metadata=report_metadata,
    )
    record = DiagnosticsRunRecord(
        diagnostics_run_spec_ref=spec_ref,
        status=status,
        report_ref=report.to_ref(),
        rejection_reasons=tuple(reasons),
    )
    return LabelDiagnosticsReport(
        diagnostics_report=report,
        diagnostics_run_record=record,
        distribution_summary_items=_summary_items(distribution),
        horizon_coverage_items=_summary_items(horizon),
        class_balance_items=_summary_items(class_balance),
        mfe_mae_summary_items=_summary_items(mfe_mae),
        path_ambiguity_summary_items=_summary_items(path_ambiguity),
        label_available_ts_validity_items=_summary_items(availability),
        cost_adjustment_sanity_items=_summary_items(cost_sanity),
        coverage_missingness_items=_summary_items(coverage_missingness),
        n_eff_report=n_eff_report,
    )


def _coerce_config(
    value: LabelDiagnosticsConfig | Mapping[str, Any] | None,
) -> LabelDiagnosticsConfig:
    if value is None:
        return LabelDiagnosticsConfig()
    if isinstance(value, LabelDiagnosticsConfig):
        return value
    if isinstance(value, Mapping):
        return LabelDiagnosticsConfig(**dict(value))
    raise LabelDiagnosticsRuntimeError("config must be LabelDiagnosticsConfig or mapping")


def _diagnostics_spec_ref(
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
    raise LabelDiagnosticsRuntimeError("diagnostics_run_spec is required")


def _require_label_family(
    value: DiagnosticsRunSpec | DiagnosticsRunSpecRef | Mapping[str, Any],
) -> None:
    if (
        isinstance(value, DiagnosticsRunSpec)
        and value.diagnostics_family is not DiagnosticsFamily.LABEL
    ):
        raise LabelDiagnosticsRuntimeError("Label diagnostics require DiagnosticsFamily.LABEL")


def _runtime_input_reasons(runtime_input_pack: RuntimeInputPack) -> tuple[RunRejectionReason, ...]:
    reasons: list[RunRejectionReason] = []
    if not isinstance(runtime_input_pack, RuntimeInputPack):
        return (
            _reason(
                "data_unavailable",
                "Label diagnostics require a resolved RuntimeInputPack.",
            ),
        )
    if runtime_input_pack.dataset_lifecycle_state not in ACCEPTED_DATASET_VERSION_LIFECYCLE_STATES:
        reasons.append(
            _reason(
                "data_unavailable",
                "Label diagnostics require an accepted DatasetVersion lifecycle state.",
            )
        )
    if not runtime_input_pack.alpha_spec_ref or not runtime_input_pack.study_spec_ref:
        reasons.append(
            _reason(
                "data_unavailable",
                "Label diagnostics require bound AlphaSpec and StudySpec references.",
            )
        )
    study_input_pack = runtime_input_pack.study_input_pack
    if study_input_pack.get("alpha_spec_id") != runtime_input_pack.alpha_spec_ref:
        reasons.append(
            _reason(
                "data_unavailable",
                "RuntimeInputPack StudyInputPack must bind the same AlphaSpec reference.",
            )
        )
    if not study_input_pack.get("label_spec_ids"):
        reasons.append(
            _reason(
                "data_unavailable",
                "RuntimeInputPack StudyInputPack must include at least one label spec reference.",
            )
        )
    if not runtime_input_pack.label_packs:
        reasons.append(
            _reason(
                "data_unavailable",
                "Label diagnostics require at least one registered label pack handle.",
            )
        )

    for label_pack in runtime_input_pack.label_packs:
        first_event = _datetime(label_pack.first_event_ts)
        last_event = _datetime(label_pack.last_event_ts)
        first_available = _datetime(label_pack.first_label_available_ts)
        last_available = _datetime(label_pack.last_label_available_ts)
        if None in (first_event, last_event, first_available, last_available):
            reasons.append(
                _reason(
                    "leakage_risk",
                    "Label pack handles must carry timezone-aware label_available_ts bounds.",
                )
            )
            continue
        assert first_event is not None
        assert last_event is not None
        assert first_available is not None
        assert last_available is not None
        if first_available < first_event or last_available < last_event:
            reasons.append(
                _reason(
                    "leakage_risk",
                    "Label pack label_available_ts bounds must not precede label event timestamps.",
                )
            )
    return tuple(reasons)


def _observation_mappings(
    values: Iterable[Mapping[str, Any]],
    reasons: list[RunRejectionReason],
) -> tuple[Mapping[str, Any], ...]:
    try:
        return _mapping_iterable(values, "label_observations")
    except LabelDiagnosticsRuntimeError as exc:
        _append_unique(reasons, _reason("weak_diagnostics", str(exc)))
        return ()


def _profile_mappings(
    values: Iterable[Mapping[str, Any]] | Mapping[str, Any],
    reasons: list[RunRejectionReason],
) -> tuple[Mapping[str, Any], ...]:
    if isinstance(values, Mapping):
        return (values,) if values else ()
    try:
        return _mapping_iterable(values, "label_profiles")
    except LabelDiagnosticsRuntimeError as exc:
        _append_unique(reasons, _reason("weak_diagnostics", str(exc)))
        return ()


def _mapping_iterable(
    values: Iterable[Mapping[str, Any]],
    field_name: str,
) -> tuple[Mapping[str, Any], ...]:
    if isinstance(values, str) or not isinstance(values, Iterable):
        raise LabelDiagnosticsRuntimeError(f"{field_name} must be an iterable of mappings")
    output: list[Mapping[str, Any]] = []
    for item in values:
        if not isinstance(item, Mapping):
            raise LabelDiagnosticsRuntimeError(f"{field_name} entries must be mappings")
        output.append(item)
    return tuple(output)


def _build_feature_label_report(
    *,
    feature_quality_reports: Iterable[Mapping[str, Any]],
    feature_coverage_reports: Iterable[Mapping[str, Any]],
    label_audit_reports: Iterable[Mapping[str, Any]],
    reasons: list[RunRejectionReason],
) -> FeatureLabelDiagnosticsReport | None:
    try:
        return build_feature_label_diagnostics(
            feature_quality_reports=feature_quality_reports,
            feature_coverage_reports=feature_coverage_reports,
            label_audit_reports=label_audit_reports,
        )
    except FeatureLabelDiagnosticsError as exc:
        _append_unique(
            reasons,
            _reason("weak_diagnostics", f"Feature/label diagnostics primitive failed: {exc}"),
        )
        return None


def _feature_label_report_reasons(
    report: FeatureLabelDiagnosticsReport,
    *,
    config: LabelDiagnosticsConfig,
) -> tuple[RunRejectionReason, ...]:
    reasons: list[RunRejectionReason] = []
    if config.require_label_audit and report.availability_alignment.label_audit_count == 0:
        reasons.append(
            _reason("data_unavailable", "Label audit reports are required for label diagnostics.")
        )
    if config.require_feature_label_coverage and report.coverage_overlap.blocking:
        reasons.append(
            _reason(
                "weak_diagnostics",
                "Feature/label coverage overlap diagnostics reported blocking findings.",
            )
        )
    if report.availability_alignment.label_available_ts_finding_count:
        reasons.append(
            _reason(
                "leakage_risk",
                "Label audit reports contain label_available_ts blocking findings.",
            )
        )
    if report.availability_alignment.label_as_feature_finding_count:
        reasons.append(
            _reason(
                "leakage_risk",
                "Label audit reports found a label reachable as a live feature input.",
            )
        )
    if report.blocked and not reasons:
        reasons.append(
            _reason("weak_diagnostics", "Feature/label diagnostics reported blocking findings.")
        )
    return tuple(reasons)


def _label_availability_reasons(
    observations: tuple[Mapping[str, Any], ...],
) -> tuple[RunRejectionReason, ...]:
    reasons: list[RunRejectionReason] = []
    for row in observations:
        label_available_ts = _datetime(row.get("label_available_ts"))
        if label_available_ts is None:
            reasons.append(
                _reason(
                    "leakage_risk",
                    "Every label diagnostic observation must carry label_available_ts.",
                )
            )
            continue
        event_ts = _datetime(row.get("event_ts"))
        horizon_end_ts = _datetime(row.get("horizon_end_ts"))
        known_ts = _datetime(row.get("value_known_ts"))
        if event_ts is not None and label_available_ts < event_ts:
            reasons.append(
                _reason(
                    "leakage_risk",
                    "label_available_ts must not precede the label event timestamp.",
                )
            )
        if horizon_end_ts is not None and label_available_ts < horizon_end_ts:
            reasons.append(
                _reason(
                    "leakage_risk",
                    "label_available_ts must not precede horizon_end_ts.",
                )
            )
        if known_ts is not None and known_ts < label_available_ts:
            reasons.append(
                _reason(
                    "leakage_risk",
                    "Label outcome known timestamp must not precede label_available_ts.",
                )
            )
    return tuple(reasons)


def _label_as_feature_reference_reasons(
    *,
    live_feature_references: Iterable[Any] | Mapping[str, Any],
    runtime_input_pack: RuntimeInputPack,
) -> tuple[RunRejectionReason, ...]:
    references = tuple(_flatten_reference_strings(live_feature_references))
    if not references:
        return ()
    label_refs = (
        {_normalize_ref(label_pack.label_id) for label_pack in runtime_input_pack.label_packs}
        | {
            _normalize_ref(label_pack.label_version_id)
            for label_pack in runtime_input_pack.label_packs
        }
        | {
            _normalize_ref(label_pack.label_spec_id)
            for label_pack in runtime_input_pack.label_packs
        }
    )
    for reference in references:
        normalized = _normalize_ref(reference)
        tokens = {
            token for token in normalized.replace(".", " ").replace("/", " ").split() if token
        }
        if tokens.intersection(LABEL_AS_FEATURE_REFERENCE_TOKENS):
            return (
                _reason(
                    "leakage_risk",
                    "Live feature references include label-only fields.",
                ),
            )
        if any(label_ref and label_ref in normalized for label_ref in label_refs):
            return (
                _reason(
                    "leakage_risk",
                    "Live feature references include a registered label identity.",
                ),
            )
    return ()


def _distribution_summary(observations: tuple[Mapping[str, Any], ...]) -> dict[str, JsonScalar]:
    classes: list[str] = []
    numeric_count = 0
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    missing_count = 0
    for row in observations:
        outcome = _outcome(row)
        if outcome is None:
            missing_count += 1
            continue
        numeric = _float(outcome)
        if numeric is None:
            classes.append(str(outcome).strip().lower())
            continue
        numeric_count += 1
        if numeric > 0:
            positive_count += 1
            classes.append("positive")
        elif numeric < 0:
            negative_count += 1
            classes.append("negative")
        else:
            neutral_count += 1
            classes.append("neutral")

    observed_count = len(classes)
    missing_rate = None if not observations else missing_count / len(observations)
    class_counts = Counter(classes)
    majority_count = max(class_counts.values(), default=0)
    minority_count = min(class_counts.values(), default=0)
    return {
        "sample_count": len(observations),
        "observed_outcome_count": observed_count,
        "missing_outcome_count": missing_count,
        "missing_outcome_rate": missing_rate,
        "numeric_outcome_count": numeric_count,
        "positive_outcome_count": positive_count,
        "negative_outcome_count": negative_count,
        "neutral_outcome_count": neutral_count,
        "class_count": len(class_counts),
        "majority_class_count": majority_count,
        "minority_class_count": minority_count,
    }


def _class_balance_summary(distribution_summary: Mapping[str, JsonScalar]) -> dict[str, JsonScalar]:
    observed = _int(distribution_summary["observed_outcome_count"])
    majority = _int(distribution_summary["majority_class_count"])
    minority = _int(distribution_summary["minority_class_count"])
    return {
        "class_count": distribution_summary["class_count"],
        "majority_class_count": majority,
        "minority_class_count": minority,
        "majority_class_share": None if observed == 0 else majority / observed,
        "minority_class_share": None if observed == 0 else minority / observed,
        "observed_outcome_count": observed,
    }


def _horizon_coverage_summary(
    observations: tuple[Mapping[str, Any], ...],
) -> dict[str, JsonScalar]:
    horizons = [horizon for row in observations if (horizon := _horizon_seconds(row)) is not None]
    counts = Counter(horizons)
    min_count = min(counts.values(), default=0)
    max_count = max(counts.values(), default=0)
    return {
        "horizon_count": len(counts),
        "horizon_sample_count": len(horizons),
        "missing_horizon_count": len(observations) - len(horizons),
        "min_horizon_seconds": min(horizons) if horizons else None,
        "max_horizon_seconds": max(horizons) if horizons else None,
        "min_horizon_sample_count": min_count,
        "max_horizon_sample_count": max_count,
        "horizon_coverage_ratio": None if max_count == 0 else min_count / max_count,
    }


def _mfe_mae_summary(observations: tuple[Mapping[str, Any], ...]) -> dict[str, JsonScalar]:
    rows = _event_rows(observations)
    summary = post_event_mfe_mae(rows)
    return {
        "event_count": summary["event_count"],
        "mfe_sample_count": summary["mfe_n"],
        "mean_mfe": summary["mean_mfe"],
        "mae_sample_count": summary["mae_n"],
        "mean_mae": summary["mean_mae"],
    }


def _path_ambiguity_summary(
    observations: tuple[Mapping[str, Any], ...],
) -> dict[str, JsonScalar]:
    rows = _event_rows(observations)
    probability = target_before_stop_probability(rows)
    ambiguous_count = sum(1 for row in observations if _path_ambiguous(row))
    path_metric_count = sum(
        1
        for row in observations
        if row.get("target_before_stop") is not None
        or row.get("path_ambiguity") is not None
        or row.get("ordering") is not None
    )
    return {
        "path_metric_sample_count": path_metric_count,
        "target_before_stop_event_count": probability["event_count"],
        "target_before_stop_probability": probability["target_before_stop_probability"],
        "ambiguous_path_count": ambiguous_count,
        "ambiguous_path_rate": None if not observations else ambiguous_count / len(observations),
    }


def _cost_adjustment_sanity(
    *,
    observations: tuple[Mapping[str, Any], ...],
    profiles: tuple[Mapping[str, Any], ...],
) -> dict[str, JsonScalar]:
    sources = (*profiles, *observations)
    declared_count = sum(1 for item in sources if _cost_declared(item))
    adjusted_count = sum(1 for item in sources if _cost_adjusted(item))
    warning_count = sum(1 for item in sources if _cost_warning(item))
    return {
        "profile_count": len(profiles),
        "cost_model_declared_count": declared_count,
        "cost_adjusted_label_count": adjusted_count,
        "cost_warning_count": warning_count,
        "cost_adjustment_sanity": "declared" if declared_count else "missing",
    }


def _n_eff_report(
    *,
    observations: tuple[Mapping[str, Any], ...],
    n_eff_overlap_metadata: Any,
    walk_forward_metadata: Any,
) -> tuple[dict[str, object] | None, tuple[RunRejectionReason, ...]]:
    if n_eff_overlap_metadata is None and walk_forward_metadata is None:
        return None, ()
    try:
        return (
            build_n_eff_sample_report(
                rows=len(observations),
                horizon_overlap_metadata=n_eff_overlap_metadata,
                observations=observations,
                walk_forward_metadata=walk_forward_metadata,
            ),
            (),
        )
    except NEffSampleReportingError as exc:
        return (
            None,
            (
                _reason(
                    "n_eff_overlap_metadata_unavailable",
                    f"N_eff reporting failed closed: {exc}",
                ),
            ),
        )


def _availability_summary(
    *,
    runtime_input_pack: RuntimeInputPack,
    observations: tuple[Mapping[str, Any], ...],
    reasons: Sequence[RunRejectionReason],
) -> dict[str, JsonScalar]:
    label_available_ts_count = sum(
        1 for row in observations if _datetime(row.get("label_available_ts")) is not None
    )
    return {
        "label_pack_count": len(runtime_input_pack.label_packs),
        "label_available_ts_observation_count": label_available_ts_count,
        "label_available_ts_missing_count": len(observations) - label_available_ts_count,
        "label_available_ts_valid": not any(reason.code == "leakage_risk" for reason in reasons),
        "label_as_feature_reference_detected": any(
            reason.code == "leakage_risk" for reason in reasons
        ),
    }


def _coverage_missingness_summary(
    *,
    feature_label_report: FeatureLabelDiagnosticsReport | None,
    distribution_summary: Mapping[str, JsonScalar],
) -> dict[str, JsonScalar]:
    if feature_label_report is None:
        return {
            "feature_label_status": "unavailable",
            "audit_label_count": 0,
            "shared_dataset_ref_count": 0,
            "shared_partition_ref_count": 0,
            "symbol_overlap_count": 0,
            "session_overlap_count": 0,
            "partition_overlap_count": 0,
            "missing_bbo_count": 0,
            "bbo_quarantined_count": 0,
            "synthetic_no_trade_count": 0,
            "missing_outcome_count": distribution_summary["missing_outcome_count"],
            "missing_outcome_rate": distribution_summary["missing_outcome_rate"],
        }
    return {
        "feature_label_status": feature_label_report.status.value,
        "audit_label_count": feature_label_report.availability_alignment.label_audit_count,
        "shared_dataset_ref_count": len(
            feature_label_report.availability_alignment.shared_dataset_versions
        ),
        "shared_partition_ref_count": len(
            feature_label_report.availability_alignment.shared_partitions
        ),
        "symbol_overlap_count": len(
            feature_label_report.coverage_overlap.dimension("symbol").shared_values
        ),
        "session_overlap_count": len(
            feature_label_report.coverage_overlap.dimension("session").shared_values
        ),
        "partition_overlap_count": len(
            feature_label_report.coverage_overlap.dimension("partition").shared_values
        ),
        "missing_bbo_count": feature_label_report.missingness_exposure.missing_bbo_count,
        "bbo_quarantined_count": feature_label_report.missingness_exposure.bbo_quarantined_count,
        "synthetic_no_trade_count": (
            feature_label_report.missingness_exposure.synthetic_no_trade_count
        ),
        "missing_outcome_count": distribution_summary["missing_outcome_count"],
        "missing_outcome_rate": distribution_summary["missing_outcome_rate"],
    }


def _summary_reasons(
    *,
    distribution_summary: Mapping[str, JsonScalar],
    class_balance: Mapping[str, JsonScalar],
    horizon_coverage: Mapping[str, JsonScalar],
    cost_sanity: Mapping[str, JsonScalar],
    config: LabelDiagnosticsConfig,
) -> tuple[RunRejectionReason, ...]:
    reasons: list[RunRejectionReason] = []
    observed = _int(distribution_summary["observed_outcome_count"])
    if observed < config.min_sample_count:
        reasons.append(
            _reason(
                "low_sample",
                "Label diagnostics observed sample count is below the configured minimum.",
            )
        )
    majority_share = _optional_float(class_balance["majority_class_share"])
    if majority_share is not None and majority_share > config.max_majority_class_share:
        reasons.append(
            _reason(
                "weak_diagnostics",
                "Label class balance exceeds the configured majority share.",
            )
        )
    if _int(horizon_coverage["horizon_count"]) == 0:
        reasons.append(_reason("inconclusive", "Label horizon coverage is unavailable."))
    horizon_ratio = _optional_float(horizon_coverage["horizon_coverage_ratio"])
    if horizon_ratio is not None and horizon_ratio < config.min_horizon_coverage_ratio:
        reasons.append(
            _reason("weak_diagnostics", "Label horizon coverage is below the configured ratio.")
        )
    if config.require_cost_adjustment_metadata and not _int(
        cost_sanity["cost_model_declared_count"]
    ):
        reasons.append(
            _reason(
                "weak_diagnostics",
                "Label diagnostics require declared cost-adjustment metadata.",
            )
        )
    return tuple(reasons)


def _quality_gates(
    *,
    status: StudyRunResultState,
    distribution_summary: Mapping[str, JsonScalar],
    class_balance: Mapping[str, JsonScalar],
    horizon_coverage: Mapping[str, JsonScalar],
    mfe_mae_summary: Mapping[str, JsonScalar],
    path_ambiguity_summary: Mapping[str, JsonScalar],
    availability_summary: Mapping[str, JsonScalar],
    cost_sanity: Mapping[str, JsonScalar],
    coverage_missingness: Mapping[str, JsonScalar],
    feature_label_report: FeatureLabelDiagnosticsReport | None,
    config: LabelDiagnosticsConfig,
) -> tuple[DiagnosticsQualityGate, ...]:
    availability_status = (
        DiagnosticsQualityGateStatus.FAIL
        if not availability_summary["label_available_ts_valid"]
        else DiagnosticsQualityGateStatus.PASS
    )
    observed = _int(distribution_summary["observed_outcome_count"])
    distribution_status = (
        DiagnosticsQualityGateStatus.INCONCLUSIVE
        if observed < config.min_sample_count
        else DiagnosticsQualityGateStatus.PASS
    )
    majority_share = _optional_float(class_balance["majority_class_share"])
    balance_status = (
        DiagnosticsQualityGateStatus.FAIL
        if majority_share is not None and majority_share > config.max_majority_class_share
        else distribution_status
    )
    horizon_ratio = _optional_float(horizon_coverage["horizon_coverage_ratio"])
    horizon_status = (
        DiagnosticsQualityGateStatus.INCONCLUSIVE
        if _int(horizon_coverage["horizon_count"]) == 0
        else DiagnosticsQualityGateStatus.FAIL
        if horizon_ratio is not None and horizon_ratio < config.min_horizon_coverage_ratio
        else DiagnosticsQualityGateStatus.PASS
    )
    path_has_metrics = bool(
        _int(mfe_mae_summary["mfe_sample_count"])
        or _int(mfe_mae_summary["mae_sample_count"])
        or _int(path_ambiguity_summary["path_metric_sample_count"])
    )
    path_status = (
        DiagnosticsQualityGateStatus.WARN
        if not path_has_metrics and config.allow_missing_path_metrics
        else DiagnosticsQualityGateStatus.INCONCLUSIVE
        if not path_has_metrics
        else DiagnosticsQualityGateStatus.PASS
    )
    cost_status = (
        DiagnosticsQualityGateStatus.FAIL
        if config.require_cost_adjustment_metadata
        and not _int(cost_sanity["cost_model_declared_count"])
        else DiagnosticsQualityGateStatus.WARN
        if _int(cost_sanity["cost_warning_count"])
        else DiagnosticsQualityGateStatus.PASS
    )
    feature_label_status = (
        DiagnosticsQualityGateStatus.FAIL
        if feature_label_report is None or feature_label_report.blocked
        else DiagnosticsQualityGateStatus.PASS
    )
    if (
        status is StudyRunResultState.INCONCLUSIVE
        and feature_label_status is DiagnosticsQualityGateStatus.PASS
    ):
        feature_label_status = DiagnosticsQualityGateStatus.WARN

    return (
        _gate(
            "label_availability_gate",
            "Label availability gate",
            availability_status,
            "label_available_ts and label-as-feature checks are summarized.",
            {
                "label_pack_count": availability_summary["label_pack_count"],
                "label_available_ts_missing_count": availability_summary[
                    "label_available_ts_missing_count"
                ],
            },
        ),
        _gate(
            "label_distribution_gate",
            "Label distribution gate",
            distribution_status,
            "Label distribution is summarized from scalar diagnostic observations.",
            {
                "sample_count": distribution_summary["sample_count"],
                "observed_outcome_count": distribution_summary["observed_outcome_count"],
                "missing_outcome_count": distribution_summary["missing_outcome_count"],
            },
        ),
        _gate(
            "label_class_balance_gate",
            "Label class balance gate",
            balance_status,
            "Class balance is summarized without embedding label outcomes.",
            {
                "class_count": class_balance["class_count"],
                "majority_class_share": class_balance["majority_class_share"],
                "threshold_ref": "label_diagnostics_config.max_majority_class_share",
            },
        ),
        _gate(
            "label_horizon_gate",
            "Label horizon gate",
            horizon_status,
            "Horizon coverage is summarized across supplied diagnostics observations.",
            {
                "horizon_count": horizon_coverage["horizon_count"],
                "horizon_coverage_ratio": horizon_coverage["horizon_coverage_ratio"],
                "threshold_ref": "label_diagnostics_config.min_horizon_coverage_ratio",
            },
        ),
        _gate(
            "label_path_gate",
            "Label path gate",
            path_status,
            "MFE, MAE, and path ambiguity are summarized through research event helpers.",
            {
                "mfe_sample_count": mfe_mae_summary["mfe_sample_count"],
                "mae_sample_count": mfe_mae_summary["mae_sample_count"],
                "ambiguous_path_count": path_ambiguity_summary["ambiguous_path_count"],
            },
        ),
        _gate(
            "label_cost_gate",
            "Label cost gate",
            cost_status,
            "Cost-adjustment metadata presence is checked descriptively.",
            {
                "cost_model_declared_count": cost_sanity["cost_model_declared_count"],
                "cost_adjusted_label_count": cost_sanity["cost_adjusted_label_count"],
                "cost_warning_count": cost_sanity["cost_warning_count"],
            },
        ),
        _gate(
            "label_coverage_missingness_gate",
            "Label coverage and missingness gate",
            feature_label_status,
            "Feature/label coverage and missingness are delegated to the research primitive.",
            {
                "audit_label_count": coverage_missingness["audit_label_count"],
                "shared_dataset_ref_count": coverage_missingness["shared_dataset_ref_count"],
                "missing_outcome_count": coverage_missingness["missing_outcome_count"],
            },
        ),
    )


def _gate(
    gate_id: str,
    name: str,
    status: DiagnosticsQualityGateStatus,
    summary: str,
    metric_refs: Mapping[str, JsonScalar],
) -> DiagnosticsQualityGate:
    return DiagnosticsQualityGate(
        gate_id=gate_id,
        name=name,
        status=status,
        summary=summary,
        metric_refs=metric_refs,
        limitations=("Scalar summary only; no runtime label outcomes are embedded.",),
    )


def _status_from_reasons(reasons: Sequence[RunRejectionReason]) -> StudyRunResultState:
    codes = {reason.code for reason in reasons}
    if "leakage_risk" in codes:
        return StudyRunResultState.REJECTED
    if codes.intersection(
        {"data_unavailable", "weak_diagnostics", "n_eff_overlap_metadata_unavailable"}
    ):
        return StudyRunResultState.DIAGNOSTICS_FAILED
    if codes.intersection({"low_sample", "inconclusive"}):
        return StudyRunResultState.INCONCLUSIVE
    return StudyRunResultState.DIAGNOSTICS_COMPLETE


def _lineage_refs(
    spec_ref: DiagnosticsRunSpecRef,
    runtime_input_pack: RuntimeInputPack,
) -> dict[str, str]:
    first_label_pack = runtime_input_pack.label_packs[0] if runtime_input_pack.label_packs else None
    return {
        "diagnostics_run_spec_id": spec_ref.diagnostics_run_spec_id,
        "study_run_spec_id": "bound_by_" + spec_ref.diagnostics_run_spec_id,
        "runtime_plan_ref": "bound_by_diagnostics_run_spec",
        "alpha_spec_ref": runtime_input_pack.alpha_spec_ref,
        "study_spec_ref": runtime_input_pack.study_spec_ref,
        "dataset_version_id": runtime_input_pack.dataset_version_id,
        "label_pack_ref": (
            "unavailable" if first_label_pack is None else first_label_pack.label_version_id
        ),
    }


def _event_rows(observations: tuple[Mapping[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    for item in observations:
        row = dict(item)
        row.setdefault("event_trigger", True)
        rows.append(row)
    return tuple(rows)


def _outcome(row: Mapping[str, Any]) -> object | None:
    for key in ("label_outcome", "class_label", "outcome_label", "label_value", "forward_return"):
        if key in row:
            value = row.get(key)
            if value is None or value == "":
                return None
            return value
    return None


def _horizon_seconds(row: Mapping[str, Any]) -> int | None:
    for key in ("horizon_seconds", "horizon", "horizon_sec"):
        if key not in row:
            continue
        value = row.get(key)
        if isinstance(value, timedelta):
            return int(value.total_seconds())
        if isinstance(value, int | float) and not isinstance(value, bool):
            return int(value)
        if isinstance(value, str):
            text = value.strip().lower()
            if not text:
                return None
            try:
                if text.endswith("ms"):
                    return max(0, int(float(text[:-2]) / 1000))
                if text.endswith("s"):
                    return int(float(text[:-1]))
                if text.endswith("m"):
                    return int(float(text[:-1]) * 60)
                if text.endswith("h"):
                    return int(float(text[:-1]) * 3600)
                return int(float(text))
            except ValueError:
                return None
    event_ts = _datetime(row.get("event_ts"))
    horizon_end_ts = _datetime(row.get("horizon_end_ts"))
    if event_ts is None or horizon_end_ts is None:
        return None
    return int((horizon_end_ts - event_ts).total_seconds())


def _path_ambiguous(row: Mapping[str, Any]) -> bool:
    if row.get("path_ambiguity") is True:
        return True
    ordering = str(row.get("ordering", "")).strip().lower()
    return ordering in {"ambiguous", "simultaneous", "unresolved", "target_and_stop_same_bar"}


def _cost_declared(item: Mapping[str, Any]) -> bool:
    return any(
        key in item and item.get(key) not in (None, "", {})
        for key in (
            "cost_adjustment",
            "cost_adjustment_ref",
            "cost_model",
            "cost_model_ref",
            "cost_profile",
        )
    )


def _cost_adjusted(item: Mapping[str, Any]) -> bool:
    if item.get("cost_adjusted") is True or item.get("cost_adjustment_applied") is True:
        return True
    return "cost_adjusted" in str(item.get("label_type", "")).lower()


def _cost_warning(item: Mapping[str, Any]) -> bool:
    for key in ("cost_model", "cost_profile", "cost_model_ref"):
        value = item.get(key)
        if isinstance(value, str) and "zero" in value.lower():
            return True
        if isinstance(value, Mapping) and any(
            str(nested).strip().lower() in {"0", "0.0", "zero"} for nested in value.values()
        ):
            return True
    return False


def _flatten_reference_strings(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Mapping):
        output: list[str] = []
        for key, item in value.items():
            output.append(str(key))
            output.extend(_flatten_reference_strings(item))
        return tuple(output)
    if isinstance(value, Sequence) and not isinstance(value, bytes | bytearray):
        output: list[str] = []
        for item in value:
            output.extend(_flatten_reference_strings(item))
        return tuple(output)
    if isinstance(value, Iterable):
        output = []
        for item in value:
            output.extend(_flatten_reference_strings(item))
        return tuple(output)
    return (str(value),)


def _summary_items(values: Mapping[str, object]) -> ScalarSummary:
    return tuple(sorted((str(key), _scalar(value, str(key))) for key, value in values.items()))


def _items_to_dict(items: ScalarSummary) -> dict[str, JsonScalar]:
    return {key: value for key, value in items}


def _scalar(value: object, field: str) -> JsonScalar:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise LabelDiagnosticsRuntimeError(f"{field} must be finite")
        return value
    if isinstance(value, str):
        return _text(value, field)
    raise LabelDiagnosticsRuntimeError(f"{field} must be scalar")


def _datetime(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        active = value
    elif isinstance(value, str):
        try:
            active = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if active.tzinfo is None or active.utcoffset() is None:
        return None
    return active.astimezone(UTC)


def _float(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        active = float(value)
    except (TypeError, ValueError):
        return None
    return active if math.isfinite(active) else None


def _optional_float(value: object) -> float | None:
    return _float(value)


def _int(value: object) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return int(value)
    return 0


def _ratio(value: float, field: str) -> float:
    active = _float(value)
    if active is None or active < 0 or active > 1:
        raise LabelDiagnosticsRuntimeError(f"{field} must be in [0, 1]")
    return active


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LabelDiagnosticsRuntimeError(f"{field} must be non-empty text")
    return value.strip()


def _normalize_ref(value: object) -> str:
    return " ".join(str(value).strip().lower().split())


def _reason(code: str, message: str) -> RunRejectionReason:
    return RunRejectionReason(code=code, message=message)


def _append_unique(reasons: list[RunRejectionReason], reason: RunRejectionReason) -> None:
    if not any(item.code == reason.code and item.message == reason.message for item in reasons):
        reasons.append(reason)


def _extend_unique(
    reasons: list[RunRejectionReason],
    new_reasons: Iterable[RunRejectionReason],
) -> None:
    for reason in new_reasons:
        _append_unique(reasons, reason)


__all__ = [
    "LABEL_DIAGNOSTICS_REPORT_KIND",
    "LabelDiagnosticsConfig",
    "LabelDiagnosticsReport",
    "LabelDiagnosticsRuntimeError",
    "build_label_diagnostics_report",
]
