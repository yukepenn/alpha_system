"""Factor diagnostics runtime orchestration over existing research primitives."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from alpha_system.research import buckets as research_buckets
from alpha_system.research import ic as research_ic
from alpha_system.runtime.contracts.run_record import RunRejectionReason, StudyRunResultState
from alpha_system.runtime.diagnostics.contracts import (
    DiagnosticsFamily,
    DiagnosticsRunRecord,
    DiagnosticsRunSpec,
    DiagnosticsRunSpecRef,
    StudyRunRecordRef,
)
from alpha_system.runtime.diagnostics.report import (
    DiagnosticsQualityGate,
    DiagnosticsQualityGateStatus,
    DiagnosticsReport,
)
from alpha_system.runtime.diagnostics.power import (
    build_detection_power_report,
)
from alpha_system.runtime.diagnostics.splits.n_eff import estimate_n_eff
from alpha_system.runtime.diagnostics.splits.walk_forward import (
    WalkForwardSplitConfig,
    WalkForwardSplitError,
    WalkForwardSplitPlan,
    build_walk_forward_split_plan,
    coerce_walk_forward_split_config,
)

FACTOR_DIAGNOSTICS_REPORT_KIND = "factor_diagnostics_summary"
FACTOR_DIAGNOSTICS_THRESHOLD_PROFILE = "factor_diagnostics_default_v1"

JsonScalar = None | bool | int | float | str


class FactorDiagnosticsError(ValueError):
    """Raised when factor diagnostics cannot be assembled from valid references."""


@dataclass(frozen=True, slots=True)
class FactorDiagnosticsThresholds:
    """Synthetic/default descriptive quality thresholds for factor diagnostics."""

    min_observations: int = 3
    min_coverage_ratio: float = 0.8
    max_missingness_rate: float = 0.2
    max_outlier_rate: float = 0.2
    outlier_zscore_threshold: float = 3.0
    bucket_count: int = 5
    min_populated_buckets: int = 2

    def __post_init__(self) -> None:
        _require_positive_int(self.min_observations, field="min_observations")
        _require_ratio(self.min_coverage_ratio, field="min_coverage_ratio")
        _require_ratio(self.max_missingness_rate, field="max_missingness_rate")
        _require_ratio(self.max_outlier_rate, field="max_outlier_rate")
        _require_positive_float(
            self.outlier_zscore_threshold,
            field="outlier_zscore_threshold",
        )
        if self.bucket_count < 2:
            raise FactorDiagnosticsError("bucket_count must be at least 2")
        _require_positive_int(self.min_populated_buckets, field="min_populated_buckets")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> FactorDiagnosticsThresholds:
        """Build thresholds from a JSON-compatible mapping."""

        allowed = {
            "min_observations",
            "min_coverage_ratio",
            "max_missingness_rate",
            "max_outlier_rate",
            "outlier_zscore_threshold",
            "bucket_count",
            "min_populated_buckets",
        }
        extra = set(value) - allowed
        if extra:
            raise FactorDiagnosticsError(
                f"unsupported factor diagnostics threshold fields: {', '.join(sorted(extra))}"
            )
        defaults = cls()
        return cls(
            min_observations=int(value.get("min_observations", defaults.min_observations)),
            min_coverage_ratio=float(value.get("min_coverage_ratio", defaults.min_coverage_ratio)),
            max_missingness_rate=float(
                value.get("max_missingness_rate", defaults.max_missingness_rate)
            ),
            max_outlier_rate=float(value.get("max_outlier_rate", defaults.max_outlier_rate)),
            outlier_zscore_threshold=float(
                value.get("outlier_zscore_threshold", defaults.outlier_zscore_threshold)
            ),
            bucket_count=int(value.get("bucket_count", defaults.bucket_count)),
            min_populated_buckets=int(
                value.get("min_populated_buckets", defaults.min_populated_buckets)
            ),
        )


@dataclass(frozen=True, slots=True)
class FactorDiagnosticsReport:
    """Factor-family specialization of the shared RT-P06 diagnostics report."""

    report: DiagnosticsReport
    walk_forward_plan: WalkForwardSplitPlan | None = None

    @property
    def status(self) -> StudyRunResultState:
        """Return the terminal diagnostics status."""

        return self.report.status

    @property
    def coverage_summary(self) -> dict[str, JsonScalar]:
        """Return scalar coverage, missingness, and outlier summary fields."""

        return self.report.coverage_summary

    @property
    def quality_summary(self) -> dict[str, JsonScalar]:
        """Return scalar IC, RankIC, bucket, and decay summary fields."""

        return self.report.quality_summary

    @property
    def limitations(self) -> tuple[str, ...]:
        """Return explicit report limitations."""

        return self.report.limitations

    @property
    def rejection_reasons(self) -> tuple[RunRejectionReason, ...]:
        """Return visible rejection reasons for failed or inconclusive outcomes."""

        return self.report.rejection_reasons

    def to_ref(self):
        """Return the shared diagnostics report reference."""

        return self.report.to_ref()

    def to_dict(self) -> dict[str, object]:
        """Return a scalar-only factor diagnostics payload."""

        payload = self.report.to_dict()
        payload["report_type"] = "FactorDiagnosticsReport"
        if self.walk_forward_plan is not None:
            payload["walk_forward_metadata"] = self.walk_forward_plan.to_dict()
        return payload


@dataclass(frozen=True, slots=True)
class FactorDiagnosticsRunResult:
    """Factor diagnostics report plus the visible diagnostics run record."""

    report: FactorDiagnosticsReport
    record: DiagnosticsRunRecord

    def to_dict(self) -> dict[str, object]:
        """Return report and record payloads without embedding observations."""

        return {
            "report": self.report.to_dict(),
            "record": self.record.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class _PreparedObservations:
    observations: tuple[dict[str, float | int], ...]
    total_count: int
    usable_pair_count: int
    missing_factor_count: int
    missing_label_count: int
    available_ts_missing_count: int
    label_available_ts_missing_count: int
    numeric_factor_count: int
    outlier_count: int
    outlier_rate: float
    horizon_count: int

    @property
    def coverage_ratio(self) -> float:
        """Return usable factor/label pair coverage over supplied inputs."""

        return 0.0 if self.total_count == 0 else self.usable_pair_count / self.total_count

    @property
    def missingness_rate(self) -> float:
        """Return the fraction of supplied inputs not usable for diagnostics."""

        return 1.0 if self.total_count == 0 else 1.0 - self.coverage_ratio


@dataclass(frozen=True, slots=True)
class _RelationshipSummary:
    pearson_ic: float | None
    rank_ic: float | None
    ic_sample_count: int
    bucket_count: int
    bucket_populated_count: int
    bucket_is_monotonic: bool
    bucket_direction: str
    bucket_rank_correlation: float | None
    bucket_sign_changes: int | None
    tail_expectancy: float | None
    decay_slope_per_second: float | None
    decay_horizon_count: int
    decay_first_horizon_seconds: int | None
    decay_first_pearson_ic: float | None
    decay_last_horizon_seconds: int | None
    decay_last_pearson_ic: float | None


@dataclass(frozen=True, slots=True)
class _Evaluation:
    status: StudyRunResultState
    gates: tuple[DiagnosticsQualityGate, ...]
    rejection_reasons: tuple[RunRejectionReason, ...]


@dataclass(frozen=True, slots=True)
class _WalkForwardEvaluation:
    plan: WalkForwardSplitPlan | None
    gates: tuple[DiagnosticsQualityGate, ...]
    rejection_reasons: tuple[RunRejectionReason, ...]
    coverage_summary: dict[str, JsonScalar]
    quality_summary: dict[str, JsonScalar]
    report_metadata: dict[str, JsonScalar]


def build_factor_diagnostics_run(
    *,
    diagnostics_run_spec: DiagnosticsRunSpec | DiagnosticsRunSpecRef | Mapping[str, Any],
    observations: Iterable[Mapping[str, Any]],
    lineage_refs: Mapping[str, str],
    study_run_record_ref: StudyRunRecordRef | Mapping[str, Any] | None = None,
    thresholds: FactorDiagnosticsThresholds | Mapping[str, Any] | None = None,
    walk_forward_config: WalkForwardSplitConfig | Mapping[str, Any] | None = None,
    horizon_overlap_metadata: Mapping[str, Any] | None = None,
) -> FactorDiagnosticsRunResult:
    """Build a factor diagnostics report and visible diagnostics run record."""

    report = build_factor_diagnostics_report(
        diagnostics_run_spec=diagnostics_run_spec,
        observations=observations,
        lineage_refs=lineage_refs,
        thresholds=thresholds,
        walk_forward_config=walk_forward_config,
        horizon_overlap_metadata=horizon_overlap_metadata,
    )
    record = DiagnosticsRunRecord(
        diagnostics_run_spec_ref=diagnostics_run_spec,
        status=report.status,
        study_run_record_ref=study_run_record_ref,
        report_ref=report.to_ref(),
        rejection_reasons=report.rejection_reasons,
    )
    return FactorDiagnosticsRunResult(report=report, record=record)


def build_factor_diagnostics_report(
    *,
    diagnostics_run_spec: DiagnosticsRunSpec | DiagnosticsRunSpecRef | Mapping[str, Any],
    observations: Iterable[Mapping[str, Any]],
    lineage_refs: Mapping[str, str],
    thresholds: FactorDiagnosticsThresholds | Mapping[str, Any] | None = None,
    walk_forward_config: WalkForwardSplitConfig | Mapping[str, Any] | None = None,
    horizon_overlap_metadata: Mapping[str, Any] | None = None,
) -> FactorDiagnosticsReport:
    """Build a descriptive factor diagnostics report from in-memory inputs.

    IC, RankIC, decay, and bucket summaries are delegated to
    :mod:`alpha_system.research.ic` and :mod:`alpha_system.research.buckets`.
    """

    _assert_factor_family(diagnostics_run_spec)
    active_thresholds = _coerce_thresholds(thresholds)
    prepared = _prepare_observations(observations, active_thresholds)
    relationship = _relationship_summary(prepared, active_thresholds)
    walk_forward = _evaluate_walk_forward(prepared, walk_forward_config)
    evaluation = _evaluate(prepared, relationship, active_thresholds, walk_forward)
    coverage_summary = _coverage_summary(prepared)
    coverage_summary.update(walk_forward.coverage_summary)
    quality_summary = _quality_summary(relationship, evaluation)
    quality_summary.update(walk_forward.quality_summary)
    power_statement = _power_statement(
        relationship=relationship,
        walk_forward=walk_forward,
        lineage_refs=lineage_refs,
        horizon_overlap_metadata=horizon_overlap_metadata,
    )
    quality_summary.update(_power_summary_scalars(power_statement))
    report_metadata = {
        "threshold_profile": FACTOR_DIAGNOSTICS_THRESHOLD_PROFILE,
        "orchestrated_research_primitives": (
            "alpha_system.research.ic;alpha_system.research.buckets"
        ),
        "descriptive_tier": "tier_0_factor_diagnostics",
        "ic_power_statement_reporting": "reported",
    }
    report_metadata.update(walk_forward.report_metadata)

    report = DiagnosticsReport(
        report_kind=FACTOR_DIAGNOSTICS_REPORT_KIND,
        diagnostics_family=DiagnosticsFamily.FACTOR,
        diagnostics_run_spec_ref=diagnostics_run_spec,
        status=evaluation.status,
        lineage_refs=_lineage_refs(lineage_refs, diagnostics_run_spec),
        coverage_summary=coverage_summary,
        quality_summary=quality_summary,
        limitations=_limitations(relationship),
        quality_gates=evaluation.gates,
        rejection_reasons=evaluation.rejection_reasons,
        power_statement=power_statement,
        report_metadata=report_metadata,
    )
    return FactorDiagnosticsReport(report=report, walk_forward_plan=walk_forward.plan)


def _prepare_observations(
    rows: Iterable[Mapping[str, Any]],
    thresholds: FactorDiagnosticsThresholds,
) -> _PreparedObservations:
    observations: list[dict[str, float | int]] = []
    numeric_factors: list[float] = []
    total_count = 0
    missing_factor_count = 0
    missing_label_count = 0
    available_ts_missing_count = 0
    label_available_ts_missing_count = 0

    for row in rows:
        if not isinstance(row, Mapping):
            raise FactorDiagnosticsError(
                f"factor diagnostics observations must be mappings, got {type(row).__name__}"
            )
        total_count += 1
        factor = _numeric(_first_present(row, ("factor_value", "feature_value", "value")))
        label = _numeric(_first_present(row, ("label_value", "forward_return")))
        has_available_ts = not _missing(row.get("available_ts"))
        has_label_available_ts = not _missing(row.get("label_available_ts"))

        if factor is None:
            missing_factor_count += 1
        else:
            numeric_factors.append(factor)
        if label is None:
            missing_label_count += 1
        if not has_available_ts:
            available_ts_missing_count += 1
        if label is not None and not has_label_available_ts:
            label_available_ts_missing_count += 1

        if factor is not None and label is not None and has_available_ts and has_label_available_ts:
            observations.append(
                {
                    "factor_value": factor,
                    "label_value": label,
                    "horizon_seconds": _horizon_seconds(row),
                }
            )

    outlier_count = _outlier_count(numeric_factors, thresholds.outlier_zscore_threshold)
    horizon_count = len({int(row["horizon_seconds"]) for row in observations})
    numeric_factor_count = len(numeric_factors)
    return _PreparedObservations(
        observations=tuple(observations),
        total_count=total_count,
        usable_pair_count=len(observations),
        missing_factor_count=missing_factor_count,
        missing_label_count=missing_label_count,
        available_ts_missing_count=available_ts_missing_count,
        label_available_ts_missing_count=label_available_ts_missing_count,
        numeric_factor_count=numeric_factor_count,
        outlier_count=outlier_count,
        outlier_rate=0.0 if numeric_factor_count == 0 else outlier_count / numeric_factor_count,
        horizon_count=horizon_count,
    )


def _relationship_summary(
    prepared: _PreparedObservations,
    thresholds: FactorDiagnosticsThresholds,
) -> _RelationshipSummary:
    if not prepared.observations:
        return _empty_relationship(thresholds.bucket_count)

    pearson = research_ic.pearson_ic(
        (row["factor_value"] for row in prepared.observations),
        (row["label_value"] for row in prepared.observations),
    )
    rank = research_ic.rank_ic(
        (row["factor_value"] for row in prepared.observations),
        (row["label_value"] for row in prepared.observations),
    )
    decay = research_ic.ic_decay(prepared.observations)
    bucket_summary = research_buckets.bucket_forward_returns(
        prepared.observations,
        bucket_count=thresholds.bucket_count,
    )
    monotonicity = research_buckets.bucket_monotonicity(bucket_summary)
    tail = research_buckets.tail_expectancy(bucket_summary)
    decay_summary = _compact_decay_summary(decay)

    return _RelationshipSummary(
        pearson_ic=_scalar_float(pearson.get("ic")),
        rank_ic=_scalar_float(rank.get("ic")),
        ic_sample_count=int(pearson.get("n") or 0),
        bucket_count=len(bucket_summary),
        bucket_populated_count=sum(
            1
            for item in bucket_summary
            if int(item.get("n") or 0) > 0 and _scalar_float(item.get("mean_return")) is not None
        ),
        bucket_is_monotonic=bool(monotonicity.get("is_monotonic")),
        bucket_direction=str(monotonicity.get("direction") or "insufficient"),
        bucket_rank_correlation=_scalar_float(monotonicity.get("rank_correlation")),
        bucket_sign_changes=_optional_int(monotonicity.get("sign_changes")),
        tail_expectancy=_scalar_float(tail.get("tail_expectancy")),
        decay_slope_per_second=_scalar_float(decay.get("decay_slope_per_second")),
        decay_horizon_count=decay_summary["decay_horizon_count"],
        decay_first_horizon_seconds=decay_summary["decay_first_horizon_seconds"],
        decay_first_pearson_ic=decay_summary["decay_first_pearson_ic"],
        decay_last_horizon_seconds=decay_summary["decay_last_horizon_seconds"],
        decay_last_pearson_ic=decay_summary["decay_last_pearson_ic"],
    )


def _evaluate(
    prepared: _PreparedObservations,
    relationship: _RelationshipSummary,
    thresholds: FactorDiagnosticsThresholds,
    walk_forward: _WalkForwardEvaluation,
) -> _Evaluation:
    rejected: list[RunRejectionReason] = []
    failed: list[RunRejectionReason] = []
    inconclusive: list[RunRejectionReason] = []

    if prepared.total_count == 0:
        inconclusive.append(
            RunRejectionReason(
                code="factor_diagnostics_no_rows",
                message="Factor diagnostics received no in-memory observations to summarize.",
            )
        )
    if prepared.available_ts_missing_count:
        rejected.append(
            RunRejectionReason(
                code="factor_available_ts_missing",
                message="One or more factor inputs omitted available_ts.",
            )
        )
    if prepared.label_available_ts_missing_count:
        rejected.append(
            RunRejectionReason(
                code="factor_label_available_ts_missing",
                message="One or more label inputs omitted label_available_ts.",
            )
        )

    if prepared.total_count and prepared.usable_pair_count < thresholds.min_observations:
        inconclusive.append(
            RunRejectionReason(
                code="factor_diagnostics_insufficient_sample",
                message="Usable factor/label pairs are below the configured descriptive minimum.",
            )
        )
    if prepared.total_count and prepared.coverage_ratio < thresholds.min_coverage_ratio:
        failed.append(
            RunRejectionReason(
                code="factor_diagnostics_low_coverage",
                message="Usable factor/label pair coverage is below the configured threshold.",
            )
        )
    if prepared.total_count and prepared.missingness_rate > thresholds.max_missingness_rate:
        failed.append(
            RunRejectionReason(
                code="factor_diagnostics_high_missingness",
                message="Factor diagnostics missingness exceeds the configured threshold.",
            )
        )
    if prepared.outlier_rate > thresholds.max_outlier_rate:
        failed.append(
            RunRejectionReason(
                code="factor_diagnostics_outlier_rate_high",
                message="Factor outlier rate exceeds the configured descriptive threshold.",
            )
        )
    if prepared.usable_pair_count >= thresholds.min_observations and (
        relationship.pearson_ic is None or relationship.rank_ic is None
    ):
        inconclusive.append(
            RunRejectionReason(
                code="factor_diagnostics_ic_unavailable",
                message="IC or RankIC could not be summarized from the usable pairs.",
            )
        )
    if (
        prepared.usable_pair_count >= thresholds.min_observations
        and relationship.bucket_populated_count < thresholds.min_populated_buckets
    ):
        inconclusive.append(
            RunRejectionReason(
                code="factor_diagnostics_bucket_summary_inconclusive",
                message="Bucket diagnostics have too few populated buckets to summarize.",
            )
        )

    if rejected:
        status = StudyRunResultState.REJECTED
    elif failed:
        status = StudyRunResultState.DIAGNOSTICS_FAILED
    elif inconclusive or walk_forward.rejection_reasons:
        status = StudyRunResultState.INCONCLUSIVE
    else:
        status = StudyRunResultState.DIAGNOSTICS_COMPLETE

    reasons = tuple(rejected + failed + inconclusive + list(walk_forward.rejection_reasons))
    gates = (*_quality_gates(prepared, relationship, thresholds), *walk_forward.gates)
    return _Evaluation(status=status, gates=gates, rejection_reasons=reasons)


def _evaluate_walk_forward(
    prepared: _PreparedObservations,
    walk_forward_config: WalkForwardSplitConfig | Mapping[str, Any] | None,
) -> _WalkForwardEvaluation:
    config = coerce_walk_forward_split_config(walk_forward_config)
    if config is None:
        return _WalkForwardEvaluation(
            plan=None,
            gates=(),
            rejection_reasons=(),
            coverage_summary={},
            quality_summary={},
            report_metadata={"walk_forward_wiring": "disabled"},
        )

    metric_refs = config.to_dict()
    metric_refs["usable_pair_count"] = prepared.usable_pair_count
    try:
        plan = build_walk_forward_split_plan(prepared.usable_pair_count, config=config)
    except WalkForwardSplitError as exc:
        reason = RunRejectionReason(
            code="walk_forward_split_unavailable",
            message=f"Purged/embargoed walk-forward split failed closed: {exc}",
        )
        metric_refs["walk_forward_fold_count"] = 0
        return _WalkForwardEvaluation(
            plan=None,
            gates=(
                DiagnosticsQualityGate(
                    gate_id="factor_walk_forward_gate",
                    name="Walk-forward split gate",
                    status=DiagnosticsQualityGateStatus.INCONCLUSIVE,
                    summary="Requested purged/embargoed walk-forward split could not be built.",
                    metric_refs=metric_refs,
                    limitations=(
                        "No unsplit fallback is used when walk-forward wiring is requested.",
                    ),
                ),
            ),
            rejection_reasons=(reason,),
            coverage_summary={
                "walk_forward_enabled": True,
                "walk_forward_fold_count": 0,
                "walk_forward_sample_count": prepared.usable_pair_count,
            },
            quality_summary={
                "walk_forward_status": "inconclusive",
                "walk_forward_min_fold_count": config.min_fold_count,
            },
            report_metadata={
                "walk_forward_wiring": "enabled",
                "walk_forward_orchestrated_primitives": (
                    "experiments_splits_walk_forward_splits;experiments_splits_apply_purge_embargo"
                ),
            },
        )

    metric_refs.update(plan.scalar_summary())
    return _WalkForwardEvaluation(
        plan=plan,
        gates=(
            DiagnosticsQualityGate(
                gate_id="factor_walk_forward_gate",
                name="Walk-forward split gate",
                status=DiagnosticsQualityGateStatus.PASS,
                summary="Requested purged/embargoed walk-forward split metadata was built.",
                metric_refs=metric_refs,
                limitations=(
                    "Walk-forward folds are diagnostics metadata, not a validation claim.",
                ),
            ),
        ),
        rejection_reasons=(),
        coverage_summary=plan.scalar_summary(),
        quality_summary={
            "walk_forward_status": "reported",
            "walk_forward_fold_count": plan.fold_count,
            "walk_forward_min_fold_count": config.min_fold_count,
        },
        report_metadata={
            "walk_forward_wiring": "enabled",
            "walk_forward_orchestrated_primitives": (
                "experiments_splits_walk_forward_splits;experiments_splits_apply_purge_embargo"
            ),
        },
    )


def _quality_gates(
    prepared: _PreparedObservations,
    relationship: _RelationshipSummary,
    thresholds: FactorDiagnosticsThresholds,
) -> tuple[DiagnosticsQualityGate, ...]:
    coverage_status = (
        DiagnosticsQualityGateStatus.INCONCLUSIVE
        if prepared.total_count == 0
        else _pass_fail(prepared.coverage_ratio >= thresholds.min_coverage_ratio)
    )
    sample_status = (
        DiagnosticsQualityGateStatus.PASS
        if prepared.usable_pair_count >= thresholds.min_observations
        else DiagnosticsQualityGateStatus.INCONCLUSIVE
    )
    ic_status = (
        DiagnosticsQualityGateStatus.PASS
        if relationship.pearson_ic is not None and relationship.rank_ic is not None
        else DiagnosticsQualityGateStatus.INCONCLUSIVE
    )
    bucket_status = (
        DiagnosticsQualityGateStatus.PASS
        if relationship.bucket_populated_count >= thresholds.min_populated_buckets
        else DiagnosticsQualityGateStatus.INCONCLUSIVE
    )
    decay_status = (
        DiagnosticsQualityGateStatus.PASS
        if relationship.decay_horizon_count >= 2 and relationship.decay_slope_per_second is not None
        else DiagnosticsQualityGateStatus.WARN
    )
    availability_status = _pass_fail(
        prepared.available_ts_missing_count == 0 and prepared.label_available_ts_missing_count == 0
    )
    outlier_status = _pass_fail(prepared.outlier_rate <= thresholds.max_outlier_rate)

    return (
        DiagnosticsQualityGate(
            gate_id="factor_availability_gate",
            name="Availability gate",
            status=availability_status,
            summary="Feature available_ts and label_available_ts presence is summarized.",
            metric_refs={
                "available_ts_missing_count": prepared.available_ts_missing_count,
                "label_available_ts_missing_count": prepared.label_available_ts_missing_count,
            },
            limitations=("Full no-lookahead audit remains scoped to a later runtime phase.",),
        ),
        DiagnosticsQualityGate(
            gate_id="factor_coverage_gate",
            name="Coverage gate",
            status=coverage_status,
            summary="Usable factor and label pair coverage is summarized.",
            metric_refs={
                "coverage_ratio": prepared.coverage_ratio,
                "min_coverage_ratio": thresholds.min_coverage_ratio,
            },
        ),
        DiagnosticsQualityGate(
            gate_id="factor_sample_gate",
            name="Sample gate",
            status=sample_status,
            summary="Usable sample size is summarized for descriptive diagnostics.",
            metric_refs={
                "usable_pair_count": prepared.usable_pair_count,
                "min_observations": thresholds.min_observations,
            },
        ),
        DiagnosticsQualityGate(
            gate_id="factor_outlier_gate",
            name="Outlier gate",
            status=outlier_status,
            summary="Factor outlier rate is summarized against the configured threshold.",
            metric_refs={
                "outlier_rate": prepared.outlier_rate,
                "max_outlier_rate": thresholds.max_outlier_rate,
            },
        ),
        DiagnosticsQualityGate(
            gate_id="factor_ic_gate",
            name="IC gate",
            status=ic_status,
            summary="IC and RankIC scalar summaries are delegated to research.ic.",
            metric_refs={
                "pearson_ic": relationship.pearson_ic,
                "rank_ic": relationship.rank_ic,
                "ic_sample_count": relationship.ic_sample_count,
            },
        ),
        DiagnosticsQualityGate(
            gate_id="factor_bucket_gate",
            name="Bucket gate",
            status=bucket_status,
            summary="Bucket return monotonicity summary is delegated to research.buckets.",
            metric_refs={
                "bucket_populated_count": relationship.bucket_populated_count,
                "min_populated_buckets": thresholds.min_populated_buckets,
                "bucket_is_monotonic": relationship.bucket_is_monotonic,
            },
        ),
        DiagnosticsQualityGate(
            gate_id="factor_decay_gate",
            name="Decay gate",
            status=decay_status,
            summary="Decay curve scalar summary is delegated to research.ic.",
            metric_refs={
                "decay_horizon_count": relationship.decay_horizon_count,
                "decay_slope_per_second": relationship.decay_slope_per_second,
            },
            limitations=("Decay slope requires at least two populated horizons.",),
        ),
    )


def _coverage_summary(prepared: _PreparedObservations) -> dict[str, JsonScalar]:
    return {
        "input_count": prepared.total_count,
        "usable_pair_count": prepared.usable_pair_count,
        "coverage_ratio": prepared.coverage_ratio,
        "missingness_rate": prepared.missingness_rate,
        "missing_factor_count": prepared.missing_factor_count,
        "missing_label_count": prepared.missing_label_count,
        "available_ts_missing_count": prepared.available_ts_missing_count,
        "label_available_ts_missing_count": prepared.label_available_ts_missing_count,
        "numeric_factor_count": prepared.numeric_factor_count,
        "outlier_count": prepared.outlier_count,
        "outlier_rate": prepared.outlier_rate,
        "horizon_count": prepared.horizon_count,
    }


def _quality_summary(
    relationship: _RelationshipSummary,
    evaluation: _Evaluation,
) -> dict[str, JsonScalar]:
    gate_statuses = [gate.status for gate in evaluation.gates]
    return {
        "diagnostic_pass": evaluation.status is StudyRunResultState.DIAGNOSTICS_COMPLETE,
        "quality_gate_count": len(evaluation.gates),
        "failing_gate_count": sum(
            1 for status in gate_statuses if status is DiagnosticsQualityGateStatus.FAIL
        ),
        "inconclusive_gate_count": sum(
            1 for status in gate_statuses if status is DiagnosticsQualityGateStatus.INCONCLUSIVE
        ),
        "warning_gate_count": sum(
            1 for status in gate_statuses if status is DiagnosticsQualityGateStatus.WARN
        ),
        "pearson_ic": relationship.pearson_ic,
        "rank_ic": relationship.rank_ic,
        "ic_sample_count": relationship.ic_sample_count,
        "bucket_count": relationship.bucket_count,
        "bucket_populated_count": relationship.bucket_populated_count,
        "bucket_is_monotonic": relationship.bucket_is_monotonic,
        "bucket_direction": relationship.bucket_direction,
        "bucket_rank_correlation": relationship.bucket_rank_correlation,
        "bucket_sign_changes": relationship.bucket_sign_changes,
        "tail_expectancy": relationship.tail_expectancy,
        "decay_slope_per_second": relationship.decay_slope_per_second,
        "decay_horizon_count": relationship.decay_horizon_count,
        "decay_first_horizon_seconds": relationship.decay_first_horizon_seconds,
        "decay_first_pearson_ic": relationship.decay_first_pearson_ic,
        "decay_last_horizon_seconds": relationship.decay_last_horizon_seconds,
        "decay_last_pearson_ic": relationship.decay_last_pearson_ic,
    }


def _power_statement(
    *,
    relationship: _RelationshipSummary,
    walk_forward: _WalkForwardEvaluation,
    lineage_refs: Mapping[str, str],
    horizon_overlap_metadata: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    n_eff = _power_n_eff(relationship, walk_forward, horizon_overlap_metadata)
    return build_detection_power_report(
        stacked_n_eff=n_eff,
        per_factor_inputs=(
            {
                "factor_id": _factor_power_id(lineage_refs),
                "factor_version": _factor_power_version(lineage_refs),
                "n_eff": n_eff,
            },
        ),
    )


def _power_n_eff(
    relationship: _RelationshipSummary,
    walk_forward: _WalkForwardEvaluation,
    horizon_overlap_metadata: Mapping[str, Any] | None = None,
) -> int:
    # Caller-supplied label-horizon overlap metadata makes the IC power N_eff
    # honest about overlapping forward-return windows: a label that looks N bars
    # ahead makes consecutive bar-spaced observations overlap ~N-fold, so the raw
    # row count badly overstates the independent sample. When supplied, discount
    # via the sanctioned overlap-aware estimator (still removing any walk-forward
    # purge/embargo gaps); otherwise preserve the prior raw/purge-embargo paths.
    if horizon_overlap_metadata is not None:
        purge_gap = None if walk_forward.plan is None else walk_forward.plan.config.purge_gap
        embargo_gap = None if walk_forward.plan is None else walk_forward.plan.config.embargo_gap
        return estimate_n_eff(
            relationship.ic_sample_count,
            horizon_overlap_metadata,
            purge_gap=purge_gap,
            embargo_gap=embargo_gap,
        ).n_eff
    if walk_forward.plan is None:
        return relationship.ic_sample_count
    metadata = {
        "horizon_bars": 1,
        "sampling_cadence_bars": 1,
        "discount_factor": 1,
        "metadata_source": "factor_walk_forward_purge_embargo",
    }
    return estimate_n_eff(
        relationship.ic_sample_count,
        metadata,
        purge_gap=walk_forward.plan.config.purge_gap,
        embargo_gap=walk_forward.plan.config.embargo_gap,
    ).n_eff


def _power_summary_scalars(power_statement: Mapping[str, object]) -> dict[str, JsonScalar]:
    stacked = power_statement.get("stacked")
    if not isinstance(stacked, Mapping):
        return {}
    return {
        "ic_power_n_eff": _scalar_int(stacked.get("n_eff")),
        "ic_power_se_ic": _scalar_float(stacked.get("se_ic")),
        "ic_power_mde_abs_ic": _scalar_float(stacked.get("mde_abs_ic")),
        "ic_power_z_multiple": _scalar_float(stacked.get("z_multiple")),
        "ic_power_statement": str(stacked.get("statement", "")),
        "ic_power_statistical_validity_claim": False,
    }


def _factor_power_id(lineage_refs: Mapping[str, str]) -> str:
    for key in ("factor_id", "feature_id", "feature_pack_ref", "feature_pack_version_id"):
        value = lineage_refs.get(key)
        if value:
            return str(value)
    return "declared_factor"


def _factor_power_version(lineage_refs: Mapping[str, str]) -> str:
    for key in ("factor_version", "feature_version", "feature_pack_ref", "feature_pack_version_id"):
        value = lineage_refs.get(key)
        if value:
            return str(value)
    return "declared_factor_version"


def _limitations(relationship: _RelationshipSummary) -> tuple[str, ...]:
    limitations = [
        (
            "Factor diagnostics are descriptive Tier 0 summaries; a diagnostic PASS is "
            "not alpha validation."
        ),
        "The report stores scalar summaries only and does not embed feature or label observations.",
        (
            "IC, RankIC, decay, and bucket summaries are delegated to "
            "alpha_system.research.ic and alpha_system.research.buckets."
        ),
    ]
    if relationship.decay_horizon_count < 2:
        limitations.append("Decay summary has fewer than two populated horizons.")
    return tuple(limitations)


def _lineage_refs(
    lineage_refs: Mapping[str, str],
    diagnostics_run_spec: DiagnosticsRunSpec | DiagnosticsRunSpecRef | Mapping[str, Any],
) -> dict[str, str]:
    refs = {str(key): str(value) for key, value in lineage_refs.items()}
    spec_ref = _diagnostics_run_spec_ref(diagnostics_run_spec)
    refs.setdefault("diagnostics_run_spec_id", spec_ref.diagnostics_run_spec_id)
    if isinstance(diagnostics_run_spec, DiagnosticsRunSpec):
        refs.setdefault(
            "study_run_spec_id",
            diagnostics_run_spec.study_run_spec_ref.study_run_spec_id,
        )
        refs.setdefault("runtime_plan_id", diagnostics_run_spec.runtime_plan_ref.plan_id)
    return refs


def _diagnostics_run_spec_ref(
    diagnostics_run_spec: DiagnosticsRunSpec | DiagnosticsRunSpecRef | Mapping[str, Any],
) -> DiagnosticsRunSpecRef:
    if isinstance(diagnostics_run_spec, DiagnosticsRunSpec):
        return diagnostics_run_spec.to_ref()
    if isinstance(diagnostics_run_spec, DiagnosticsRunSpecRef):
        return diagnostics_run_spec
    if not isinstance(diagnostics_run_spec, Mapping):
        raise FactorDiagnosticsError(
            "diagnostics_run_spec must be DiagnosticsRunSpec, DiagnosticsRunSpecRef, or mapping"
        )
    return DiagnosticsRunSpecRef(
        diagnostics_run_spec_id=diagnostics_run_spec.get("diagnostics_run_spec_id"),
        content_hash=diagnostics_run_spec.get("content_hash"),
    )


def _assert_factor_family(
    diagnostics_run_spec: DiagnosticsRunSpec | DiagnosticsRunSpecRef | Mapping[str, Any],
) -> None:
    if (
        isinstance(diagnostics_run_spec, DiagnosticsRunSpec)
        and diagnostics_run_spec.diagnostics_family is not DiagnosticsFamily.FACTOR
    ):
        raise FactorDiagnosticsError("factor diagnostics require DiagnosticsFamily.FACTOR")


def _coerce_thresholds(
    value: FactorDiagnosticsThresholds | Mapping[str, Any] | None,
) -> FactorDiagnosticsThresholds:
    if value is None:
        return FactorDiagnosticsThresholds()
    if isinstance(value, FactorDiagnosticsThresholds):
        return value
    if not isinstance(value, Mapping):
        raise FactorDiagnosticsError(
            f"thresholds must be FactorDiagnosticsThresholds or mapping, got {type(value).__name__}"
        )
    return FactorDiagnosticsThresholds.from_mapping(value)


def _empty_relationship(bucket_count: int) -> _RelationshipSummary:
    return _RelationshipSummary(
        pearson_ic=None,
        rank_ic=None,
        ic_sample_count=0,
        bucket_count=bucket_count,
        bucket_populated_count=0,
        bucket_is_monotonic=False,
        bucket_direction="insufficient",
        bucket_rank_correlation=None,
        bucket_sign_changes=None,
        tail_expectancy=None,
        decay_slope_per_second=None,
        decay_horizon_count=0,
        decay_first_horizon_seconds=None,
        decay_first_pearson_ic=None,
        decay_last_horizon_seconds=None,
        decay_last_pearson_ic=None,
    )


def _compact_decay_summary(decay: Mapping[str, Any]) -> dict[str, int | float | None]:
    by_horizon = decay.get("by_horizon")
    points: list[tuple[int, float]] = []
    if isinstance(by_horizon, Mapping):
        for horizon, metrics in by_horizon.items():
            if not isinstance(metrics, Mapping):
                continue
            pearson = _scalar_float(metrics.get("pearson_ic"))
            if pearson is not None:
                points.append((int(horizon), pearson))
    points.sort(key=lambda item: item[0])
    if not points:
        return {
            "decay_horizon_count": int(decay.get("n_horizons") or 0),
            "decay_first_horizon_seconds": None,
            "decay_first_pearson_ic": None,
            "decay_last_horizon_seconds": None,
            "decay_last_pearson_ic": None,
        }
    first = points[0]
    last = points[-1]
    return {
        "decay_horizon_count": int(decay.get("n_horizons") or len(points)),
        "decay_first_horizon_seconds": first[0],
        "decay_first_pearson_ic": first[1],
        "decay_last_horizon_seconds": last[0],
        "decay_last_pearson_ic": last[1],
    }


def _outlier_count(values: Sequence[float], threshold: float) -> int:
    if len(values) < 2:
        return 0
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    if variance <= 0:
        return 0
    std = math.sqrt(variance)
    return sum(1 for value in values if abs((value - mean) / std) > threshold)


def _first_present(row: Mapping[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        if key in row and not _missing(row.get(key)):
            return row.get(key)
    return None


def _missing(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _numeric(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        output = float(value)
    except (TypeError, ValueError):
        return None
    return output if math.isfinite(output) else None


def _horizon_seconds(row: Mapping[str, Any]) -> int:
    if "horizon_seconds" in row and not _missing(row.get("horizon_seconds")):
        return int(row["horizon_seconds"])
    if "horizon" in row and not _missing(row.get("horizon")):
        horizon = row["horizon"]
        if hasattr(horizon, "total_seconds"):
            return int(horizon.total_seconds())
        return int(horizon)
    return 0


def _scalar_float(value: Any) -> float | None:
    output = _numeric(value)
    return None if output is None else float(output)


def _scalar_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _pass_fail(condition: bool) -> DiagnosticsQualityGateStatus:
    return DiagnosticsQualityGateStatus.PASS if condition else DiagnosticsQualityGateStatus.FAIL


def _require_positive_int(value: int, *, field: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise FactorDiagnosticsError(f"{field} must be a positive integer")


def _require_ratio(value: float, *, field: str) -> None:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise FactorDiagnosticsError(f"{field} must be a finite ratio")
    active = float(value)
    if not math.isfinite(active) or active < 0.0 or active > 1.0:
        raise FactorDiagnosticsError(f"{field} must be between 0 and 1")


def _require_positive_float(value: float, *, field: str) -> None:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise FactorDiagnosticsError(f"{field} must be a finite positive number")
    if not math.isfinite(float(value)) or float(value) <= 0.0:
        raise FactorDiagnosticsError(f"{field} must be a finite positive number")


__all__ = [
    "FACTOR_DIAGNOSTICS_REPORT_KIND",
    "FACTOR_DIAGNOSTICS_THRESHOLD_PROFILE",
    "FactorDiagnosticsError",
    "FactorDiagnosticsReport",
    "FactorDiagnosticsRunResult",
    "FactorDiagnosticsThresholds",
    "build_factor_diagnostics_report",
    "build_factor_diagnostics_run",
]
