"""Rule ordering and bar-level management decisions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from alpha_system.core.enums import Direction
from alpha_system.management.partials import PartialExitDecision, eligible_partial_exits
from alpha_system.management.spec import ManagementSpec
from alpha_system.management.state import ManagedPositionState
from alpha_system.management.stops import stop_hit
from alpha_system.management.targets import favorable_price_hit, target_r_price


MANAGEMENT_RULE_ORDER: tuple[str, ...] = (
    "session_reset",
    "entry_trade_limit",
    "entry_cooldown",
    "active_stop",
    "full_target_r_multiple",
    "laddered_partials",
    "max_holding_bars",
    "time_exit",
    "eod_exit",
    "breakeven_update_for_next_bar",
    "trailing_update_for_next_bar",
)


@dataclass(frozen=True, slots=True)
class ManagementExitDecision:
    """One full-position management exit decision."""

    reason: str
    price: Decimal
    ambiguous_same_bar: bool = False


@dataclass(frozen=True, slots=True)
class ManagementBarDecision:
    """All management effects for one bar."""

    full_exit: ManagementExitDecision | None = None
    partial_exits: tuple[PartialExitDecision, ...] = ()


def evaluate_management_bar(
    state: ManagedPositionState,
    bar: Mapping[str, Any],
    spec: ManagementSpec,
    *,
    is_last_session_bar: bool,
) -> ManagementBarDecision:
    """Evaluate management rules against one 1-minute bar.

    Stop/target ambiguity is resolved before any favorable exit. If a stop and
    target or partial threshold are both touched in the same bar, the full stop
    exit wins.
    """
    active_stop_hit = stop_hit(state.direction, state.active_stop_price, bar)
    target_price = target_r_price(
        state.direction,
        state.entry_price,
        state.risk_per_unit,
        spec.target_r_multiple,
    )
    target_hit = favorable_price_hit(state.direction, target_price, bar)
    partials = eligible_partial_exits(
        direction=state.direction,
        entry_price=state.entry_price,
        risk_per_unit=state.risk_per_unit,
        remaining_quantity=state.remaining_quantity,
        filled_labels=state.filled_partial_labels,
        spec=spec.laddered_partial_take_profit,
        bar=bar,
    )
    favorable_hit = target_hit or bool(partials)
    if active_stop_hit and state.active_stop_price is not None:
        return ManagementBarDecision(
            full_exit=ManagementExitDecision(
                reason="stop_loss",
                price=state.active_stop_price,
                ambiguous_same_bar=favorable_hit,
            )
        )
    if target_hit and target_price is not None:
        return ManagementBarDecision(
            full_exit=ManagementExitDecision(reason="take_profit", price=target_price)
        )
    if partials:
        return ManagementBarDecision(partial_exits=partials)
    max_hold = spec.max_holding_bars.max_bars if spec.max_holding_bars.enabled else None
    if max_hold is not None and state.bars_held_at(int(bar["bar_index"])) >= max_hold:
        return ManagementBarDecision(
            full_exit=ManagementExitDecision(
                reason="max_holding_bars",
                price=conservative_close_price(state.direction, bar),
            )
        )
    if _time_exit_hit(state, bar, spec):
        return ManagementBarDecision(
            full_exit=ManagementExitDecision(
                reason="time_exit",
                price=conservative_close_price(state.direction, bar),
            )
        )
    if spec.eod_exit.enabled and is_last_session_bar:
        return ManagementBarDecision(
            full_exit=ManagementExitDecision(
                reason="eod_exit",
                price=conservative_close_price(state.direction, bar),
            )
        )
    return ManagementBarDecision()


def conservative_close_price(direction: Direction, bar: Mapping[str, Any]) -> Decimal:
    """Return conservative bar-end exit price without broker-order semantics."""
    if direction is Direction.LONG:
        return _side_or_fallback(bar, "bid", "close")
    if direction is Direction.SHORT:
        return _side_or_fallback(bar, "ask", "close")
    raise ValueError("management exit requires long or short direction")


def _time_exit_hit(
    state: ManagedPositionState,
    bar: Mapping[str, Any],
    spec: ManagementSpec,
) -> bool:
    if not spec.time_exit.enabled or spec.time_exit.max_minutes is None:
        return False
    held = _datetime(bar["bar_end_ts"]) - state.entry_ts
    return held >= timedelta(minutes=spec.time_exit.max_minutes)


def _side_or_fallback(bar: Mapping[str, Any], side: str, fallback: str) -> Decimal:
    value = bar.get(side)
    if value is None:
        return _decimal(bar[fallback])
    return _decimal(value)


def _decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        active = value
    else:
        active = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if active.tzinfo is None:
        active = active.replace(tzinfo=timezone.utc)
    return active.astimezone(timezone.utc)
