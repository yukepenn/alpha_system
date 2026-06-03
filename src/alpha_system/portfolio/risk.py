"""Portfolio exposure and capital constraint enforcement."""

from __future__ import annotations

from decimal import Decimal

from alpha_system.portfolio.allocation import CapitalAllocationState
from alpha_system.portfolio.sizing import SizeDecision
from alpha_system.portfolio.spec import InsufficientCapitalPolicy, PortfolioSpec, RiskLimitsSpec


class PortfolioRiskError(ValueError):
    """Raised when portfolio limits cannot be evaluated."""


def apply_portfolio_limits(
    decisions: tuple[SizeDecision, ...],
    allocation_state: CapitalAllocationState,
    spec: PortfolioSpec,
) -> tuple[SizeDecision, ...]:
    """Apply deterministic portfolio constraints in a stable order."""
    active = enforce_multi_symbol_constraints(decisions, spec)
    active = enforce_position_percent(active, allocation_state.total_equity, spec.risk_limits)
    active = enforce_gross_exposure(active, allocation_state.total_equity, spec)
    active = enforce_net_exposure(active, allocation_state.total_equity, spec)
    active = enforce_capital_available(active, allocation_state, spec)
    return active


def enforce_position_percent(
    decisions: tuple[SizeDecision, ...],
    equity: Decimal,
    risk_limits: RiskLimitsSpec,
) -> tuple[SizeDecision, ...]:
    limit = risk_limits.max_position_percent
    if limit is None:
        return decisions
    max_notional = equity * limit
    return tuple(
        decision.with_notional(max_notional, equity, "max_position_percent")
        if not decision.rejected and decision.target_notional > max_notional
        else decision
        for decision in decisions
    )


def enforce_gross_exposure(
    decisions: tuple[SizeDecision, ...],
    equity: Decimal,
    spec: PortfolioSpec,
) -> tuple[SizeDecision, ...]:
    limit = spec.max_gross_exposure
    if limit is None:
        return decisions
    active = _active_decisions(decisions)
    gross = sum((decision.target_notional for decision in active), Decimal("0"))
    max_gross = equity * limit
    if gross <= max_gross or gross == 0:
        return decisions
    scale = max_gross / gross
    return tuple(
        decision.with_notional(decision.target_notional * scale, equity, "max_gross_exposure")
        if not decision.rejected and decision.target_notional > 0
        else decision
        for decision in decisions
    )


def enforce_net_exposure(
    decisions: tuple[SizeDecision, ...],
    equity: Decimal,
    spec: PortfolioSpec,
) -> tuple[SizeDecision, ...]:
    limit = spec.max_net_exposure
    if limit is None:
        return decisions
    active = _active_decisions(decisions)
    net = sum((decision.signed_notional for decision in active), Decimal("0"))
    max_net = equity * limit
    if abs(net) <= max_net:
        return decisions
    if net == 0:
        return decisions
    scale = Decimal("0") if max_net == 0 else max_net / abs(net)
    return tuple(
        decision.with_notional(decision.target_notional * scale, equity, "max_net_exposure")
        if not decision.rejected and decision.target_notional > 0
        else decision
        for decision in decisions
    )


def enforce_multi_symbol_constraints(
    decisions: tuple[SizeDecision, ...],
    spec: PortfolioSpec,
) -> tuple[SizeDecision, ...]:
    constraints = spec.multi_symbol_constraints
    seen: set[str] = set()
    output: list[SizeDecision] = []
    max_instruments = constraints.max_active_instruments
    active_instruments: list[str] = []
    for decision in decisions:
        if not decision.instrument_id:
            raise PortfolioRiskError("portfolio decisions require instrument_id")
        repeated = decision.instrument_id in seen and not constraints.allow_repeated_instrument_targets
        seen.add(decision.instrument_id)
        if repeated and decision.target_notional > 0:
            output.append(
                decision.with_notional(Decimal("0"), spec.capital_allocation.starting_equity, "repeated_instrument", rejected=True)
            )
            continue
        if decision.target_notional > 0 and decision.instrument_id not in active_instruments:
            active_instruments.append(decision.instrument_id)
        if (
            max_instruments is not None
            and decision.target_notional > 0
            and decision.instrument_id in active_instruments[max_instruments:]
        ):
            output.append(
                decision.with_notional(Decimal("0"), spec.capital_allocation.starting_equity, "max_active_instruments", rejected=True)
            )
            continue
        output.append(decision)
    return tuple(output)


def enforce_capital_available(
    decisions: tuple[SizeDecision, ...],
    allocation_state: CapitalAllocationState,
    spec: PortfolioSpec,
) -> tuple[SizeDecision, ...]:
    remaining = allocation_state.available_notional(spec.capital_allocation)
    output: list[SizeDecision] = []
    policy = spec.capital_allocation.insufficient_capital_policy
    for decision in decisions:
        if decision.rejected or decision.target_notional == 0:
            output.append(decision)
            continue
        if decision.target_notional <= remaining:
            remaining -= decision.target_notional
            output.append(decision)
            continue
        if policy is InsufficientCapitalPolicy.CAP and remaining > 0:
            output.append(decision.with_notional(remaining, allocation_state.total_equity, "insufficient_capital"))
            remaining = Decimal("0")
            continue
        output.append(
            decision.with_notional(
                Decimal("0"),
                allocation_state.total_equity,
                "insufficient_capital",
                rejected=True,
            )
        )
    return tuple(output)


def _active_decisions(decisions: tuple[SizeDecision, ...]) -> tuple[SizeDecision, ...]:
    return tuple(decision for decision in decisions if not decision.rejected and decision.target_notional > 0)
