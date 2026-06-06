"""Signal Probe runtime orchestration over existing runtime cost surfaces."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from alpha_system.runtime.contracts.run_record import RunRejectionReason, StudyRunResultState
from alpha_system.runtime.cost import (
    CostSensitivityReport,
    CostStressThresholds,
    build_cost_sensitivity_report,
)
from alpha_system.runtime.diagnostics.contracts import DiagnosticsRunSpec, DiagnosticsRunSpecRef
from alpha_system.runtime.probe.fills import (
    SignalProbeFillError,
    SignalProbeObservation,
    SignalProbePositionSeries,
    build_next_bar_position_series,
)
from alpha_system.runtime.probe.report import SignalProbeReport, ThresholdProbeSummary
from alpha_system.runtime.probe.spec import SignalProbeSpec

ZERO = Decimal("0")
PROBE_LIMITATIONS = (
    "Signal Probe is a Tier 1 descriptive screen, not strategy validation.",
    "Position changes use next-bar or explicit delayed fills; same-bar fills are forbidden.",
    "Cost-aware expectancy is a proxy built from runtime.cost stress summaries.",
    "Slippage remains labeled as a proxy through the attached CostSensitivityReport.",
    "A complete probe is not a candidate, promotion decision, or profitability claim.",
)


class SignalProbeRuntimeError(ValueError):
    """Raised when the probe runner receives an invalid top-level request."""


@dataclass(frozen=True, slots=True)
class _ThresholdRun:
    series: SignalProbePositionSeries
    cost_report: CostSensitivityReport
    expectancy_by_profile: dict[str, Decimal | None]


def run_signal_probe(
    *,
    signal_probe_spec: SignalProbeSpec,
    observations: Iterable[SignalProbeObservation | Mapping[str, Any]],
    cost_diagnostics_run_spec: DiagnosticsRunSpec | DiagnosticsRunSpecRef | Mapping[str, Any],
    lineage_refs: Mapping[str, str],
    cost_thresholds: CostStressThresholds | Mapping[str, Any] | None = None,
) -> SignalProbeReport:
    """Run one bounded simple signal probe and return a descriptive report.

    The runner converts the declared threshold neighborhood into delayed
    long/short/flat positions, delegates generated fill cost stress to
    ``alpha_system.runtime.cost``, and returns scalar proxy summaries only.
    """

    if not isinstance(signal_probe_spec, SignalProbeSpec):
        raise SignalProbeRuntimeError("signal_probe_spec must be a SignalProbeSpec")
    lineage = _lineage_refs(lineage_refs, signal_probe_spec)
    try:
        rows = tuple(_coerce_observation(row) for row in observations)
    except SignalProbeFillError as exc:
        empty_cost = _build_cost_report(
            spec=signal_probe_spec,
            observations=(),
            series=None,
            cost_diagnostics_run_spec=cost_diagnostics_run_spec,
            lineage_refs=lineage,
            cost_thresholds=cost_thresholds,
        )
        return _blocked_report(
            spec=signal_probe_spec,
            lineage_refs=lineage,
            cost_report=empty_cost,
            reasons=(
                RunRejectionReason(
                    code="probe_observation_contract_invalid",
                    message=str(exc),
                ),
            ),
        )
    threshold_runs: list[_ThresholdRun] = []
    errors: list[RunRejectionReason] = []

    for threshold in signal_probe_spec.thresholds:
        try:
            threshold_runs.append(
                _run_threshold(
                    spec=signal_probe_spec,
                    observations=rows,
                    threshold=threshold,
                    cost_diagnostics_run_spec=cost_diagnostics_run_spec,
                    lineage_refs=lineage,
                    cost_thresholds=cost_thresholds,
                )
            )
        except SignalProbeFillError as exc:
            errors.append(
                RunRejectionReason(
                    code="probe_fill_contract_invalid",
                    message=str(exc),
                )
            )
            break

    if errors:
        empty_cost = _build_cost_report(
            spec=signal_probe_spec,
            observations=rows,
            series=None,
            cost_diagnostics_run_spec=cost_diagnostics_run_spec,
            lineage_refs=lineage,
            cost_thresholds=cost_thresholds,
        )
        return _blocked_report(
            spec=signal_probe_spec,
            lineage_refs=lineage,
            cost_report=empty_cost,
            reasons=tuple(errors),
        )

    if not threshold_runs:
        empty_cost = _build_cost_report(
            spec=signal_probe_spec,
            observations=rows,
            series=None,
            cost_diagnostics_run_spec=cost_diagnostics_run_spec,
            lineage_refs=lineage,
            cost_thresholds=cost_thresholds,
        )
        return _blocked_report(
            spec=signal_probe_spec,
            lineage_refs=lineage,
            cost_report=empty_cost,
            reasons=(
                RunRejectionReason(
                    code="probe_observations_missing",
                    message="Signal probe requires at least one local observation.",
                ),
            ),
        )

    primary = _primary_run(threshold_runs, signal_probe_spec.primary_threshold)
    threshold_summaries = tuple(_threshold_summary(item) for item in threshold_runs)
    stability_summary = _stability_summary(threshold_summaries)
    reasons = _probe_rejection_reasons(primary, threshold_summaries)
    status = _probe_status(primary, reasons)

    return SignalProbeReport(
        signal_probe_spec_ref=signal_probe_spec,
        status=status,
        lineage_refs=lineage,
        position_summary=_position_summary(primary.series),
        trade_summary=_trade_summary(primary.series),
        cost_aware_expectancy_proxy=_expectancy_summary(primary.expectancy_by_profile),
        drawdown_proxy=_drawdown_summary(primary.series),
        stability_summary=stability_summary,
        threshold_summaries=threshold_summaries,
        cost_sensitivity_report=primary.cost_report,
        limitations=PROBE_LIMITATIONS,
        rejection_reasons=reasons,
        report_metadata={
            "descriptive_tier": "tier_1_signal_probe",
            "orchestrated_runtime_cost": True,
            "runtime_cost_surface": "alpha_system.runtime.cost",
            "same_bar_optimistic_fill_forbidden": True,
            "cost_stress_required": True,
            "double_cost_required": True,
            "zero_cost_promotion_basis_allowed": False,
        },
    )


def _run_threshold(
    *,
    spec: SignalProbeSpec,
    observations: tuple[SignalProbeObservation, ...],
    threshold: Decimal,
    cost_diagnostics_run_spec: DiagnosticsRunSpec | DiagnosticsRunSpecRef | Mapping[str, Any],
    lineage_refs: Mapping[str, str],
    cost_thresholds: CostStressThresholds | Mapping[str, Any] | None,
) -> _ThresholdRun:
    series = build_next_bar_position_series(
        observations,
        threshold=threshold,
        direction_policy=spec.direction_policy,
        fill_policy=spec.fill_policy,
    )
    cost_report = _build_cost_report(
        spec=spec,
        observations=observations,
        series=series,
        cost_diagnostics_run_spec=cost_diagnostics_run_spec,
        lineage_refs=lineage_refs,
        cost_thresholds=cost_thresholds,
    )
    return _ThresholdRun(
        series=series,
        cost_report=cost_report,
        expectancy_by_profile=_cost_aware_expectancy(series, cost_report),
    )


def _build_cost_report(
    *,
    spec: SignalProbeSpec,
    observations: tuple[SignalProbeObservation, ...],
    series: SignalProbePositionSeries | None,
    cost_diagnostics_run_spec: DiagnosticsRunSpec | DiagnosticsRunSpecRef | Mapping[str, Any],
    lineage_refs: Mapping[str, str],
    cost_thresholds: CostStressThresholds | Mapping[str, Any] | None,
) -> CostSensitivityReport:
    fills = () if series is None else series.to_cost_fill_mappings(observations)
    return build_cost_sensitivity_report(
        diagnostics_run_spec=cost_diagnostics_run_spec,
        fills=fills,
        lineage_refs=lineage_refs,
        cost_stress_spec=spec.cost_stress_spec,
        thresholds=cost_thresholds,
    )


def _blocked_report(
    *,
    spec: SignalProbeSpec,
    lineage_refs: Mapping[str, str],
    cost_report: CostSensitivityReport,
    reasons: tuple[RunRejectionReason, ...],
) -> SignalProbeReport:
    summary = ThresholdProbeSummary(
        threshold=spec.primary_threshold,
        trade_count=0,
        turnover=ZERO,
        gross_expectancy_proxy=None,
        double_cost_expectancy_proxy=None,
        drawdown_proxy=ZERO,
        stable_under_double_cost=False,
    )
    return SignalProbeReport(
        signal_probe_spec_ref=spec,
        status=StudyRunResultState.BLOCKED,
        lineage_refs=lineage_refs,
        position_summary={
            "observation_count": 0,
            "position_count": 0,
            "non_flat_position_count": 0,
            "same_bar_fill_count": 0,
        },
        trade_summary={
            "trade_count": 0,
            "turnover": "0",
            "fill_delay_bars": spec.fill_policy.delay_bars,
        },
        cost_aware_expectancy_proxy={"double_cost_expectancy_proxy": None},
        drawdown_proxy={"drawdown_proxy": "0"},
        stability_summary={
            "threshold_count": len(spec.thresholds),
            "stable_threshold_count": 0,
            "stable_threshold_share": "0",
        },
        threshold_summaries=(summary,),
        cost_sensitivity_report=cost_report,
        limitations=PROBE_LIMITATIONS,
        rejection_reasons=reasons,
        report_metadata={
            "descriptive_tier": "tier_1_signal_probe",
            "orchestrated_runtime_cost": True,
            "same_bar_optimistic_fill_forbidden": True,
            "blocked_before_position_summary": True,
        },
    )


def _probe_rejection_reasons(
    primary: _ThresholdRun,
    threshold_summaries: tuple[ThresholdProbeSummary, ...],
) -> tuple[RunRejectionReason, ...]:
    reasons: list[RunRejectionReason] = []
    if primary.series.trade_count == 0:
        reasons.append(
            RunRejectionReason(
                code="probe_no_trades",
                message=(
                    "Signal probe produced no delayed position changes at the primary threshold."
                ),
            )
        )
    if primary.cost_report.status is StudyRunResultState.DIAGNOSTICS_FAILED:
        reasons.append(
            RunRejectionReason(
                code="cost_stress_failed",
                message="Attached cost stress returned a failed descriptive diagnostics status.",
            )
        )
    elif primary.cost_report.status is not StudyRunResultState.DIAGNOSTICS_COMPLETE:
        reasons.append(
            RunRejectionReason(
                code="cost_stress_inconclusive",
                message="Attached cost stress did not reach DIAGNOSTICS_COMPLETE.",
            )
        )

    double_cost_expectancy = primary.expectancy_by_profile.get("double_cost")
    if double_cost_expectancy is not None and double_cost_expectancy <= ZERO:
        reasons.append(
            RunRejectionReason(
                code="double_cost_expectancy_non_positive",
                message="Primary threshold expectancy proxy is non-positive under double_cost.",
            )
        )

    stable_count = sum(1 for item in threshold_summaries if item.stable_under_double_cost)
    if stable_count == 0:
        reasons.append(
            RunRejectionReason(
                code="parameter_neighborhood_unstable",
                message="No declared threshold stayed positive under the double_cost proxy.",
            )
        )
    return tuple(_dedupe_reasons(reasons))


def _probe_status(
    primary: _ThresholdRun,
    reasons: tuple[RunRejectionReason, ...],
) -> StudyRunResultState:
    codes = {reason.code for reason in reasons}
    if not reasons:
        return StudyRunResultState.SIGNAL_PROBE_COMPLETE
    if "probe_no_trades" in codes or "cost_stress_inconclusive" in codes:
        return StudyRunResultState.INCONCLUSIVE
    if primary.cost_report.status is StudyRunResultState.DIAGNOSTICS_FAILED:
        return StudyRunResultState.REJECTED
    return StudyRunResultState.REJECTED


def _threshold_summary(threshold_run: _ThresholdRun) -> ThresholdProbeSummary:
    double_cost_expectancy = threshold_run.expectancy_by_profile.get("double_cost")
    return ThresholdProbeSummary(
        threshold=threshold_run.series.threshold,
        trade_count=threshold_run.series.trade_count,
        turnover=threshold_run.series.turnover,
        gross_expectancy_proxy=threshold_run.series.gross_expectancy_proxy,
        double_cost_expectancy_proxy=double_cost_expectancy,
        drawdown_proxy=threshold_run.series.drawdown_proxy,
        stable_under_double_cost=(
            double_cost_expectancy is not None and double_cost_expectancy > ZERO
        ),
    )


def _cost_aware_expectancy(
    series: SignalProbePositionSeries,
    cost_report: CostSensitivityReport,
) -> dict[str, Decimal | None]:
    denominator = Decimal(series.trade_count) if series.trade_count > 0 else None
    result: dict[str, Decimal | None] = {}
    for summary in cost_report.profile_summaries:
        if denominator is None:
            result[summary.profile_name] = None
            continue
        result[summary.profile_name] = (
            series.gross_total_proxy - summary.combined_cost_slippage_proxy
        ) / denominator
    return result


def _position_summary(series: SignalProbePositionSeries) -> dict[str, str | int]:
    return {
        "observation_count": series.observation_count,
        "position_count": len(series.positions),
        "non_flat_position_count": sum(1 for position in series.positions if position != 0),
        "long_position_count": sum(1 for position in series.positions if position > 0),
        "short_position_count": sum(1 for position in series.positions if position < 0),
        "same_bar_fill_count": sum(
            1 for fill in series.fills if fill.fill_index == fill.origin_signal_index
        ),
    }


def _trade_summary(series: SignalProbePositionSeries) -> dict[str, str | int]:
    return {
        "trade_count": series.trade_count,
        "turnover": _decimal_text(series.turnover),
        "gross_total_proxy": _decimal_text(series.gross_total_proxy),
        "gross_expectancy_proxy": _optional_decimal_text(series.gross_expectancy_proxy),
    }


def _expectancy_summary(values: Mapping[str, Decimal | None]) -> dict[str, str | None]:
    return {
        f"{profile}_expectancy_proxy": _optional_decimal_text(expectancy)
        for profile, expectancy in values.items()
    }


def _drawdown_summary(series: SignalProbePositionSeries) -> dict[str, str]:
    return {"drawdown_proxy": _decimal_text(series.drawdown_proxy)}


def _stability_summary(
    threshold_summaries: tuple[ThresholdProbeSummary, ...],
) -> dict[str, str | int]:
    stable_count = sum(1 for item in threshold_summaries if item.stable_under_double_cost)
    threshold_count = len(threshold_summaries)
    share = ZERO if threshold_count == 0 else Decimal(stable_count) / Decimal(threshold_count)
    return {
        "threshold_count": threshold_count,
        "stable_threshold_count": stable_count,
        "stable_threshold_share": _decimal_text(share),
        "bounded_threshold_neighborhood": True,
    }


def _primary_run(
    threshold_runs: list[_ThresholdRun],
    primary_threshold: Decimal,
) -> _ThresholdRun:
    for item in threshold_runs:
        if item.series.threshold == primary_threshold:
            return item
    raise SignalProbeRuntimeError("primary threshold was not evaluated")


def _lineage_refs(lineage_refs: Mapping[str, str], spec: SignalProbeSpec) -> dict[str, str]:
    lineage = {str(key): str(value) for key, value in lineage_refs.items()}
    lineage.setdefault("signal_probe_spec_id", spec.signal_probe_spec_id)
    lineage.setdefault("alpha_spec_ref", spec.alpha_spec_ref)
    lineage.setdefault("study_spec_ref", spec.study_spec_ref)
    lineage.setdefault("dataset_version_id", spec.runtime_input_pack.dataset_version_id)
    lineage.setdefault(
        "cost_model_version_id", spec.cost_stress_spec.cost_model_version.cost_model_version_id
    )
    return lineage


def _coerce_observation(
    value: SignalProbeObservation | Mapping[str, Any],
) -> SignalProbeObservation:
    if isinstance(value, SignalProbeObservation):
        return value
    if isinstance(value, Mapping):
        return SignalProbeObservation.from_mapping(value)
    raise SignalProbeRuntimeError("observations must contain mappings or SignalProbeObservation")


def _dedupe_reasons(reasons: list[RunRejectionReason]) -> tuple[RunRejectionReason, ...]:
    seen: set[str] = set()
    result: list[RunRejectionReason] = []
    for reason in reasons:
        if reason.code in seen:
            continue
        seen.add(reason.code)
        result.append(reason)
    return tuple(result)


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")


def _optional_decimal_text(value: Decimal | None) -> str | None:
    return None if value is None else _decimal_text(value)


__all__ = [
    "SignalProbeRuntimeError",
    "run_signal_probe",
]
