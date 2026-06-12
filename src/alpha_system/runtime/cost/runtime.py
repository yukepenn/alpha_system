"""Cost-stress runtime orchestration over backtest cost/slippage primitives."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from alpha_system.backtest import costs, slippage
from alpha_system.runtime.contracts.run_record import RunRejectionReason, StudyRunResultState
from alpha_system.runtime.cost.report import (
    COST_SENSITIVITY_REPORT_KIND,
    CostProfileSummary,
    CostSensitivityReport,
    CostSessionSummary,
)
from alpha_system.runtime.cost.spec import CostStressSpec, SessionCostPenalty
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

ZERO = Decimal("0")


class CostStressRuntimeError(ValueError):
    """Raised when cost stress cannot be assembled from valid local inputs."""


@dataclass(frozen=True, slots=True)
class CostStressFill:
    """One resolved synthetic/local fill summary consumed by cost stress."""

    price: Decimal
    quantity: Decimal
    side: str
    bid: Decimal | None = None
    ask: Decimal | None = None
    spread: Decimal | None = None
    multiplier: Decimal = Decimal("1")
    session_label: str = "RTH"
    symbol: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "price", _decimal(self.price, field="price"))
        object.__setattr__(self, "quantity", _decimal(self.quantity, field="quantity"))
        object.__setattr__(self, "multiplier", _decimal(self.multiplier, field="multiplier"))
        object.__setattr__(self, "bid", _optional_decimal(self.bid, field="bid"))
        object.__setattr__(self, "ask", _optional_decimal(self.ask, field="ask"))
        object.__setattr__(self, "spread", _optional_decimal(self.spread, field="spread"))
        object.__setattr__(
            self,
            "session_label",
            _text(self.session_label, field="session_label").upper(),
        )
        if self.symbol is not None:
            object.__setattr__(
                self,
                "symbol",
                _text(self.symbol, field="symbol").upper(),
            )
        # Delegate numeric and side validation to the consumed primitive input contracts.
        self.cost_input()
        self.slippage_input()

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> CostStressFill:
        """Build a fill input from a JSON-compatible mapping."""

        return cls(
            price=_decimal(value.get("price"), field="price"),
            quantity=_decimal(value.get("quantity"), field="quantity"),
            side=_text(value.get("side"), field="side"),
            bid=_optional_decimal(value.get("bid"), field="bid"),
            ask=_optional_decimal(value.get("ask"), field="ask"),
            spread=_optional_decimal(value.get("spread"), field="spread"),
            multiplier=_decimal(value.get("multiplier", "1"), field="multiplier"),
            session_label=_text(
                value.get("session_label", value.get("session", "RTH")),
                field="session_label",
            ),
            symbol=_optional_text(
                value.get("symbol", value.get("root_symbol", value.get("instrument_id"))),
                field="symbol",
            ),
        )

    @property
    def has_bbo_context(self) -> bool:
        """Return whether this fill carries spread or bid/ask context."""

        return self.spread is not None or (self.bid is not None and self.ask is not None)

    def cost_input(self) -> costs.CostInput:
        """Return the consumed primitive cost input."""

        metadata = {} if self.symbol is None else {"symbol": self.symbol}
        return costs.CostInput(
            price=self.price,
            quantity=self.quantity,
            side=self.side,
            bid=self.bid,
            ask=self.ask,
            spread=self.spread,
            multiplier=self.multiplier,
            metadata=metadata,
        )

    def slippage_input(self) -> slippage.SlippageInput:
        """Return the consumed primitive slippage input."""

        return slippage.SlippageInput(
            price=self.price,
            quantity=self.quantity,
            side=self.side,
            bid=self.bid,
            ask=self.ask,
            spread=self.spread,
        )


@dataclass(frozen=True, slots=True)
class CostStressThresholds:
    """Descriptive fail-closed gates for cost sensitivity summaries."""

    min_fill_count: int = 1
    max_double_cost_to_base_ratio: Decimal = Decimal("3.0")

    def __post_init__(self) -> None:
        if isinstance(self.min_fill_count, bool) or self.min_fill_count < 1:
            raise CostStressRuntimeError("min_fill_count must be a positive integer")
        object.__setattr__(
            self,
            "max_double_cost_to_base_ratio",
            _positive_decimal(
                self.max_double_cost_to_base_ratio,
                field="max_double_cost_to_base_ratio",
            ),
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> CostStressThresholds:
        """Build thresholds from config or test data."""

        return cls(
            min_fill_count=int(value.get("min_fill_count", 1)),
            max_double_cost_to_base_ratio=_decimal(
                value.get("max_double_cost_to_base_ratio", "3.0"),
                field="max_double_cost_to_base_ratio",
            ),
        )


def build_cost_sensitivity_report(
    *,
    diagnostics_run_spec: DiagnosticsRunSpec | DiagnosticsRunSpecRef | Mapping[str, Any],
    fills: Iterable[CostStressFill | Mapping[str, Any]],
    lineage_refs: Mapping[str, str],
    cost_stress_spec: CostStressSpec,
    thresholds: CostStressThresholds | Mapping[str, Any] | None = None,
) -> CostSensitivityReport:
    """Build a descriptive CostSensitivityReport from resolved local inputs.

    Cost and slippage amounts are delegated to ``alpha_system.backtest.costs``
    and ``alpha_system.backtest.slippage``. This runtime only scales and
    aggregates the values returned by those primitives across the configured
    profiles and sessions.
    """

    if not isinstance(cost_stress_spec, CostStressSpec):
        raise CostStressRuntimeError("cost_stress_spec must be a CostStressSpec")
    _assert_cost_family(diagnostics_run_spec)

    active_thresholds = _coerce_thresholds(thresholds)
    fill_items = tuple(_coerce_fill(fill) for fill in fills)
    spec_ref = _diagnostics_spec_ref(diagnostics_run_spec)
    cost_model = costs.cost_model_from_mapping(
        cost_stress_spec.cost_model_version.cost_model_descriptor
    )
    slippage_model = slippage.slippage_model_from_mapping(
        cost_stress_spec.cost_model_version.slippage_model_descriptor
    )

    bbo_fill_count = sum(1 for fill in fill_items if fill.has_bbo_context)
    spread_components_configured = _descriptor_has_model(
        cost_stress_spec.cost_model_version.cost_model_descriptor,
        "spread_cost",
    ) or _descriptor_has_model(
        cost_stress_spec.cost_model_version.slippage_model_descriptor,
        "spread_sensitive",
    )
    bbo_spread_crossing_used = (
        cost_stress_spec.cost_model_version.bbo_available
        and bbo_fill_count > 0
        and spread_components_configured
    )
    bbo_unavailable_fallback_used = not bbo_spread_crossing_used

    profile_summaries: list[CostProfileSummary] = []
    session_summaries: list[CostSessionSummary] = []
    for profile in cost_stress_spec.profiles:
        profile_cost_total = ZERO
        profile_slippage_total = ZERO
        session_totals: dict[str, _SessionAccumulator] = {}

        for fill in fill_items:
            penalty = cost_stress_spec.penalty_for(fill.session_label)
            cost_breakdown = cost_model.cost_for_fill(fill.cost_input())
            slippage_result = slippage_model.apply(fill.slippage_input())

            scaled_cost = cost_breakdown.total * profile.cost_multiplier * penalty.cost_multiplier
            scaled_slippage = (
                slippage_result.amount
                * profile.slippage_multiplier
                * penalty.slippage_multiplier
            )
            profile_cost_total += scaled_cost
            profile_slippage_total += scaled_slippage

            accumulator = session_totals.setdefault(
                penalty.session_label,
                _SessionAccumulator(
                    fill_count=0,
                    cost_total=ZERO,
                    slippage_total=ZERO,
                    penalty=penalty,
                ),
            )
            session_totals[penalty.session_label] = accumulator.add(
                cost_total=scaled_cost,
                slippage_total=scaled_slippage,
            )

        combined_total = profile_cost_total + profile_slippage_total
        profile_summaries.append(
            CostProfileSummary(
                profile_name=profile.name,
                fill_count=len(fill_items),
                bbo_fill_count=bbo_fill_count,
                cost_total=profile_cost_total,
                slippage_proxy_total=profile_slippage_total,
                combined_cost_slippage_proxy=combined_total,
                cost_multiplier=profile.cost_multiplier,
                slippage_multiplier=profile.slippage_multiplier,
                bbo_spread_crossing_used=bbo_spread_crossing_used,
                bbo_unavailable_fallback_used=bbo_unavailable_fallback_used,
                zero_cost_diagnostic_only=(
                    cost_stress_spec.cost_model_version.zero_cost_diagnostic_only
                ),
                promotion_basis_allowed=False,
            )
        )
        for label in sorted(session_totals):
            accumulator = session_totals[label]
            session_summaries.append(
                CostSessionSummary(
                    profile_name=profile.name,
                    session_label=label,
                    fill_count=accumulator.fill_count,
                    cost_total=accumulator.cost_total,
                    slippage_proxy_total=accumulator.slippage_total,
                    combined_cost_slippage_proxy=(
                        accumulator.cost_total + accumulator.slippage_total
                    ),
                    session_cost_multiplier=accumulator.penalty.cost_multiplier,
                    session_slippage_multiplier=accumulator.penalty.slippage_multiplier,
                )
            )

    cost_gradient = _cost_gradient(profile_summaries)
    reasons = _rejection_reasons(
        profile_summaries=tuple(profile_summaries),
        thresholds=active_thresholds,
    )
    status = _status_from_reasons(reasons)
    gates = _quality_gates(
        profile_summaries=tuple(profile_summaries),
        thresholds=active_thresholds,
        reasons=reasons,
    )

    diagnostics_report = DiagnosticsReport(
        report_kind=COST_SENSITIVITY_REPORT_KIND,
        diagnostics_family=DiagnosticsFamily.COST,
        diagnostics_run_spec_ref=spec_ref,
        status=status,
        lineage_refs=_lineage_refs(lineage_refs, spec_ref, cost_stress_spec),
        coverage_summary={
            "fill_count": len(fill_items),
            "profile_count": len(profile_summaries),
            "session_count": len({fill.session_label for fill in fill_items}),
            "bbo_available": cost_stress_spec.cost_model_version.bbo_available,
            "bbo_fill_count": bbo_fill_count,
            "bbo_unavailable_fallback_used": bbo_unavailable_fallback_used,
        },
        quality_summary=_quality_summary(
            profile_summaries=tuple(profile_summaries),
            cost_gradient=cost_gradient,
            status=status,
            reason_count=len(reasons),
        ),
        limitations=_limitations(
            bbo_unavailable_fallback_used=bbo_unavailable_fallback_used,
            zero_cost_diagnostic_only=(
                cost_stress_spec.cost_model_version.zero_cost_diagnostic_only
            ),
        ),
        quality_gates=gates,
        rejection_reasons=reasons,
        report_metadata={
            "cost_model_version_id": cost_stress_spec.cost_model_version.cost_model_version_id,
            "session_penalty_config_id": cost_stress_spec.session_penalty_config_id,
            "profile_order": ";".join(cost_stress_spec.profile_names),
            "orchestrated_backtest_primitives": (
                "alpha_system.backtest.costs;alpha_system.backtest.slippage"
            ),
            "slippage_labeled_proxy": True,
            "descriptive_tier": "tier_0_cost_stress",
            "zero_cost_diagnostic_only": (
                cost_stress_spec.cost_model_version.zero_cost_diagnostic_only
            ),
            "promotion_basis_allowed": False,
        },
    )

    return CostSensitivityReport(
        diagnostics_report=diagnostics_report,
        cost_model_version=cost_stress_spec.cost_model_version,
        profile_summaries=tuple(profile_summaries),
        session_breakdown=tuple(session_summaries),
        cost_gradient_items=tuple(cost_gradient.items()),
        slippage_labeled_proxy=True,
        bbo_spread_crossing_used=bbo_spread_crossing_used,
        bbo_unavailable_fallback_used=bbo_unavailable_fallback_used,
    )


@dataclass(frozen=True, slots=True)
class _SessionAccumulator:
    fill_count: int
    cost_total: Decimal
    slippage_total: Decimal
    penalty: SessionCostPenalty

    def add(self, *, cost_total: Decimal, slippage_total: Decimal) -> _SessionAccumulator:
        return _SessionAccumulator(
            fill_count=self.fill_count + 1,
            cost_total=self.cost_total + cost_total,
            slippage_total=self.slippage_total + slippage_total,
            penalty=self.penalty,
        )


def _quality_summary(
    *,
    profile_summaries: tuple[CostProfileSummary, ...],
    cost_gradient: Mapping[str, str | None],
    status: StudyRunResultState,
    reason_count: int,
) -> dict[str, str | int | bool | None]:
    base = _summary_by_profile(profile_summaries)["base"]
    double_cost = _summary_by_profile(profile_summaries)["double_cost"]
    return {
        "diagnostic_complete": status is StudyRunResultState.DIAGNOSTICS_COMPLETE,
        "profile_count": len(profile_summaries),
        "double_cost_present": True,
        "slippage_labeled_proxy": True,
        "base_combined_cost_slippage_proxy": _decimal_text(
            base.combined_cost_slippage_proxy
        ),
        "double_cost_combined_cost_slippage_proxy": _decimal_text(
            double_cost.combined_cost_slippage_proxy
        ),
        "double_to_base_combined_ratio": cost_gradient.get(
            "double_to_base_combined_ratio"
        ),
        "bbo_spread_crossing_used": base.bbo_spread_crossing_used,
        "bbo_unavailable_fallback_used": base.bbo_unavailable_fallback_used,
        "zero_cost_diagnostic_only": base.zero_cost_diagnostic_only,
        "promotion_basis_allowed": False,
        "rejection_reason_count": reason_count,
    }


def _quality_gates(
    *,
    profile_summaries: tuple[CostProfileSummary, ...],
    thresholds: CostStressThresholds,
    reasons: tuple[RunRejectionReason, ...],
) -> tuple[DiagnosticsQualityGate, ...]:
    base = _summary_by_profile(profile_summaries)["base"]
    double_cost = _summary_by_profile(profile_summaries)["double_cost"]
    reason_codes = {reason.code for reason in reasons}
    return (
        DiagnosticsQualityGate(
            gate_id="cost_sample_gate",
            name="Cost stress sample gate",
            status=(
                DiagnosticsQualityGateStatus.INCONCLUSIVE
                if "low_sample" in reason_codes
                else DiagnosticsQualityGateStatus.PASS
            ),
            summary="Cost stress input count is visible against the configured minimum.",
            metric_refs={
                "fill_count": base.fill_count,
                "min_fill_count": thresholds.min_fill_count,
            },
            limitations=("Synthetic and local summaries only.",),
        ),
        DiagnosticsQualityGate(
            gate_id="double_cost_gate",
            name="Double cost profile gate",
            status=DiagnosticsQualityGateStatus.PASS,
            summary="The required double_cost profile is present in the cost-stress summary.",
            metric_refs={
                "double_cost_combined_cost_slippage_proxy": _decimal_text(
                    double_cost.combined_cost_slippage_proxy
                )
            },
        ),
        DiagnosticsQualityGate(
            gate_id="cost_fragility_gate",
            name="Cost fragility gate",
            status=(
                DiagnosticsQualityGateStatus.FAIL
                if "cost_fragile" in reason_codes
                else DiagnosticsQualityGateStatus.PASS
            ),
            summary=(
                "Double-cost sensitivity is compared with the configured descriptive threshold."
            ),
            metric_refs={
                "max_double_cost_to_base_ratio": _decimal_text(
                    thresholds.max_double_cost_to_base_ratio
                ),
            },
            limitations=("A favorable gate is not a promotion decision.",),
        ),
        DiagnosticsQualityGate(
            gate_id="slippage_proxy_gate",
            name="Slippage proxy gate",
            status=DiagnosticsQualityGateStatus.PASS,
            summary="Slippage is explicitly labeled as a proxy in the cost model version.",
            metric_refs={"slippage_labeled_proxy": True},
        ),
    )


def _rejection_reasons(
    *,
    profile_summaries: tuple[CostProfileSummary, ...],
    thresholds: CostStressThresholds,
) -> tuple[RunRejectionReason, ...]:
    reasons: list[RunRejectionReason] = []
    base = _summary_by_profile(profile_summaries)["base"]
    double_cost = _summary_by_profile(profile_summaries)["double_cost"]
    if base.fill_count < thresholds.min_fill_count:
        reasons.append(
            RunRejectionReason(
                code="low_sample",
                message="Cost stress input count is below the configured descriptive minimum.",
            )
        )
    ratio = _safe_ratio(
        double_cost.combined_cost_slippage_proxy,
        base.combined_cost_slippage_proxy,
    )
    if ratio is not None and ratio > thresholds.max_double_cost_to_base_ratio:
        reasons.append(
            RunRejectionReason(
                code="cost_fragile",
                message="Double-cost sensitivity exceeds the configured descriptive threshold.",
            )
        )
    return tuple(reasons)


def _status_from_reasons(reasons: tuple[RunRejectionReason, ...]) -> StudyRunResultState:
    codes = {reason.code for reason in reasons}
    if "cost_fragile" in codes:
        return StudyRunResultState.DIAGNOSTICS_FAILED
    if "low_sample" in codes:
        return StudyRunResultState.INCONCLUSIVE
    return StudyRunResultState.DIAGNOSTICS_COMPLETE


def _cost_gradient(profile_summaries: list[CostProfileSummary]) -> dict[str, str | None]:
    summaries = _summary_by_profile(tuple(profile_summaries))
    ordered = ["base", "stress_1", "stress_2", "double_cost"]
    gradient: dict[str, str | None] = {}
    for left, right in zip(ordered, ordered[1:]):
        left_summary = summaries[left]
        right_summary = summaries[right]
        gradient[f"{left}_to_{right}_combined_delta"] = _decimal_text(
            right_summary.combined_cost_slippage_proxy
            - left_summary.combined_cost_slippage_proxy
        )
        gradient[f"{left}_to_{right}_cost_delta"] = _decimal_text(
            right_summary.cost_total - left_summary.cost_total
        )
        gradient[f"{left}_to_{right}_slippage_proxy_delta"] = _decimal_text(
            right_summary.slippage_proxy_total - left_summary.slippage_proxy_total
        )
    ratio = _safe_ratio(
        summaries["double_cost"].combined_cost_slippage_proxy,
        summaries["base"].combined_cost_slippage_proxy,
    )
    gradient["double_to_base_combined_ratio"] = None if ratio is None else _decimal_text(ratio)
    return gradient


def _limitations(
    *,
    bbo_unavailable_fallback_used: bool,
    zero_cost_diagnostic_only: bool,
) -> tuple[str, ...]:
    limitations = [
        "Cost stress is a descriptive sensitivity summary, not realized execution output.",
        "Slippage is labeled as a proxy and is not a realized fill measurement.",
        "The double_cost profile is required, but passing it is not a promotion decision.",
        (
            "BBO spread crossing is used only when supplied BBO context is present; "
            "no spread is fabricated."
        ),
    ]
    if bbo_unavailable_fallback_used:
        limitations.append(
            "BBO context was unavailable or unused, so the bps fallback marker is visible."
        )
    if zero_cost_diagnostic_only:
        limitations.append(
            "The zero-cost reference is diagnostic-only and cannot be a promotion basis."
        )
    return tuple(limitations)


def _lineage_refs(
    lineage_refs: Mapping[str, str],
    spec_ref: DiagnosticsRunSpecRef,
    cost_stress_spec: CostStressSpec,
) -> dict[str, str]:
    lineage = {str(key): str(value) for key, value in lineage_refs.items()}
    lineage.setdefault("diagnostics_run_spec_id", spec_ref.diagnostics_run_spec_id)
    lineage["cost_model_version_id"] = (
        cost_stress_spec.cost_model_version.cost_model_version_id
    )
    lineage["session_penalty_config_id"] = cost_stress_spec.session_penalty_config_id
    return lineage


def _summary_by_profile(
    profile_summaries: tuple[CostProfileSummary, ...],
) -> dict[str, CostProfileSummary]:
    return {summary.profile_name: summary for summary in profile_summaries}


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator == ZERO:
        return None
    return numerator / denominator


def _descriptor_has_model(value: Mapping[str, Any], model_name: str) -> bool:
    if value.get("model") == model_name:
        return True
    components = value.get("components", ())
    if not isinstance(components, list | tuple):
        return False
    return any(
        isinstance(component, Mapping) and _descriptor_has_model(component, model_name)
        for component in components
    )


def _coerce_fill(value: CostStressFill | Mapping[str, Any]) -> CostStressFill:
    if isinstance(value, CostStressFill):
        return value
    if not isinstance(value, Mapping):
        raise CostStressRuntimeError("fills must contain CostStressFill objects or mappings")
    return CostStressFill.from_mapping(value)


def _coerce_thresholds(
    value: CostStressThresholds | Mapping[str, Any] | None,
) -> CostStressThresholds:
    if value is None:
        return CostStressThresholds()
    if isinstance(value, CostStressThresholds):
        return value
    if isinstance(value, Mapping):
        return CostStressThresholds.from_mapping(value)
    raise CostStressRuntimeError("thresholds must be CostStressThresholds, mapping, or None")


def _assert_cost_family(
    value: DiagnosticsRunSpec | DiagnosticsRunSpecRef | Mapping[str, Any],
) -> None:
    if (
        isinstance(value, DiagnosticsRunSpec)
        and value.diagnostics_family is not DiagnosticsFamily.COST
    ):
        raise CostStressRuntimeError("diagnostics_run_spec must be for the COST family")


def _diagnostics_spec_ref(
    value: DiagnosticsRunSpec | DiagnosticsRunSpecRef | Mapping[str, Any],
) -> DiagnosticsRunSpecRef:
    if isinstance(value, DiagnosticsRunSpec):
        return value.to_ref()
    if isinstance(value, DiagnosticsRunSpecRef):
        return value
    if not isinstance(value, Mapping):
        raise CostStressRuntimeError(
            "diagnostics_run_spec must be DiagnosticsRunSpec, DiagnosticsRunSpecRef, or mapping"
        )
    return DiagnosticsRunSpecRef(
        diagnostics_run_spec_id=value.get("diagnostics_run_spec_id"),
        content_hash=value.get("content_hash"),
    )


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CostStressRuntimeError(f"{field} is required")
    return value.strip()


def _optional_text(value: object, *, field: str) -> str | None:
    if value is None:
        return None
    return _text(value, field=field)


def _decimal(value: object, *, field: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise CostStressRuntimeError(f"{field} must be numeric")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise CostStressRuntimeError(f"{field} must be numeric") from exc


def _optional_decimal(value: object, *, field: str) -> Decimal | None:
    if value is None:
        return None
    return _decimal(value, field=field)


def _positive_decimal(value: object, *, field: str) -> Decimal:
    active = _decimal(value, field=field)
    if active <= ZERO:
        raise CostStressRuntimeError(f"{field} must be positive")
    return active


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")


__all__ = [
    "CostStressFill",
    "CostStressRuntimeError",
    "CostStressThresholds",
    "build_cost_sensitivity_report",
]
