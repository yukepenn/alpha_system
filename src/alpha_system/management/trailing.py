"""Breakeven and trailing stop updates."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Any

from alpha_system.core.enums import Direction
from alpha_system.management.spec import BreakevenStopSpec, TrailingStopSpec
from alpha_system.management.state import ManagedPositionState
from alpha_system.management.targets import favorable_price_hit, threshold_r_price


def breakeven_stop_update(
    state: ManagedPositionState,
    spec: BreakevenStopSpec,
    bar: Mapping[str, Any],
) -> Decimal | None:
    """Return a breakeven stop update, or the active stop if unchanged."""
    if not spec.enabled or spec.trigger_r is None or state.risk_per_unit is None:
        return state.active_stop_price
    trigger_price = threshold_r_price(
        state.direction,
        state.entry_price,
        state.risk_per_unit,
        spec.trigger_r,
    )
    if not favorable_price_hit(state.direction, trigger_price, bar):
        return state.active_stop_price
    offset = state.risk_per_unit * spec.offset_r
    if state.direction is Direction.LONG:
        candidate = state.entry_price + offset
        return _more_protective_long(state.active_stop_price, candidate)
    if state.direction is Direction.SHORT:
        candidate = state.entry_price - offset
        return _more_protective_short(state.active_stop_price, candidate)
    return state.active_stop_price


def trailing_stop_update(
    state: ManagedPositionState,
    spec: TrailingStopSpec,
    bar: Mapping[str, Any],
) -> Decimal | None:
    """Return a trailing stop update, or the active stop if unchanged."""
    if not spec.enabled:
        return state.active_stop_price
    updated = state.with_watermarks(high=_decimal(bar["high"]), low=_decimal(bar["low"]))
    if spec.trail_pct is not None:
        if updated.direction is Direction.LONG and updated.high_watermark is not None:
            candidate = updated.high_watermark * (Decimal("1") - spec.trail_pct)
            return _more_protective_long(updated.active_stop_price, candidate)
        if updated.direction is Direction.SHORT and updated.low_watermark is not None:
            candidate = updated.low_watermark * (Decimal("1") + spec.trail_pct)
            return _more_protective_short(updated.active_stop_price, candidate)
    if spec.trail_r is not None and updated.risk_per_unit is not None:
        distance = updated.risk_per_unit * spec.trail_r
        if updated.direction is Direction.LONG and updated.high_watermark is not None:
            candidate = updated.high_watermark - distance
            return _more_protective_long(updated.active_stop_price, candidate)
        if updated.direction is Direction.SHORT and updated.low_watermark is not None:
            candidate = updated.low_watermark + distance
            return _more_protective_short(updated.active_stop_price, candidate)
    return updated.active_stop_price


def update_protective_stop_for_next_bar(
    state: ManagedPositionState,
    *,
    breakeven: BreakevenStopSpec,
    trailing: TrailingStopSpec,
    bar: Mapping[str, Any],
) -> ManagedPositionState:
    """Apply stop movement after exits so updates affect the next bar."""
    updated = state.with_watermarks(high=_decimal(bar["high"]), low=_decimal(bar["low"]))
    breakeven_price = breakeven_stop_update(updated, breakeven, bar)
    with_breakeven = updated.with_stop(breakeven_price)
    trailing_price = trailing_stop_update(with_breakeven, trailing, bar)
    return with_breakeven.with_stop(trailing_price)


def _more_protective_long(current: Decimal | None, candidate: Decimal) -> Decimal:
    if current is None:
        return candidate
    return max(current, candidate)


def _more_protective_short(current: Decimal | None, candidate: Decimal) -> Decimal:
    if current is None:
        return candidate
    return min(current, candidate)


def _decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))
