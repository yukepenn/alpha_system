"""Deterministic laddered partial-exit accounting helpers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from alpha_system.backtest.accounting import realized_pnl_for
from alpha_system.core.enums import Direction
from alpha_system.management.spec import LadderedPartialsSpec, PartialTakeProfitStep
from alpha_system.management.targets import favorable_price_hit, threshold_r_price


@dataclass(frozen=True, slots=True)
class PartialExitDecision:
    """One visible laddered partial exit."""

    step: PartialTakeProfitStep
    price: Decimal
    quantity: Decimal


@dataclass(frozen=True, slots=True)
class PartialAccounting:
    """Accounting effects for one partial-exit leg."""

    gross_pnl: Decimal
    allocated_entry_cost: Decimal
    exit_cost: Decimal
    net_pnl: Decimal
    remaining_quantity: Decimal
    remaining_entry_cost: Decimal


def eligible_partial_exits(
    *,
    direction: Direction,
    entry_price: Decimal,
    risk_per_unit: Decimal | None,
    remaining_quantity: Decimal,
    filled_labels: tuple[str, ...],
    spec: LadderedPartialsSpec,
    bar: Mapping[str, Any],
) -> tuple[PartialExitDecision, ...]:
    """Return all not-yet-filled partial exits touched by this bar."""
    if not spec.enabled or risk_per_unit is None or remaining_quantity <= 0:
        return ()
    filled = set(filled_labels)
    decisions: list[PartialExitDecision] = []
    current_remaining = remaining_quantity
    for step in spec.steps:
        if step.label in filled:
            continue
        price = threshold_r_price(direction, entry_price, risk_per_unit, step.threshold_r)
        if not favorable_price_hit(direction, price, bar):
            continue
        quantity = min(current_remaining, remaining_quantity * step.exit_fraction)
        if quantity <= 0:
            continue
        decisions.append(PartialExitDecision(step=step, price=price, quantity=quantity))
        current_remaining -= quantity
    return tuple(decisions)


def account_partial_exit(
    *,
    direction: Direction,
    entry_price: Decimal,
    exit_price: Decimal,
    exit_quantity: Decimal,
    current_quantity: Decimal,
    current_entry_cost: Decimal,
    exit_cost: Decimal,
    multiplier: Decimal = Decimal("1"),
) -> PartialAccounting:
    """Return deterministic accounting effects for a partial close.

    ``multiplier`` is the futures contract dollar multiplier; with the default
    ``1`` gross PnL stays in price points (the reference engine threads the
    per-instrument multiplier so partial-leg PnL is denominated in dollars,
    matching full-exit accounting).
    """
    if exit_quantity <= 0:
        raise ValueError("partial exit quantity must be positive")
    if current_quantity <= 0 or exit_quantity > current_quantity:
        raise ValueError("partial exit quantity must not exceed current position quantity")
    fraction = exit_quantity / current_quantity
    allocated_entry_cost = current_entry_cost * fraction
    remaining_entry_cost = current_entry_cost - allocated_entry_cost
    gross_pnl = realized_pnl_for(
        direction=direction,
        entry_price=entry_price,
        exit_price=exit_price,
        quantity=exit_quantity,
        multiplier=multiplier,
    )
    net_pnl = gross_pnl - allocated_entry_cost - exit_cost
    return PartialAccounting(
        gross_pnl=gross_pnl,
        allocated_entry_cost=allocated_entry_cost,
        exit_cost=exit_cost,
        net_pnl=net_pnl,
        remaining_quantity=current_quantity - exit_quantity,
        remaining_entry_cost=remaining_entry_cost,
    )


def _decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))
