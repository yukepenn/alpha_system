"""Conservative fill resolution for the reference backtest engine."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any

from alpha_system.backtest.engine_config import ReferenceEngineConfig
from alpha_system.backtest.orders import OrderIntent, ReferenceOrder
from alpha_system.core.enums import Direction


class FillReason(str, Enum):
    """Reference fill reason."""

    ENTRY_SIGNAL = "entry_signal"
    EXIT_SIGNAL = "exit_signal"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    EOD_FLAT = "eod_flat"


@dataclass(frozen=True, slots=True, kw_only=True)
class ReferenceFill:
    """One deterministic fill chosen by the reference engine."""

    fill_id: str
    order_id: str
    signal_id: str | None
    instrument_id: str
    session_id: str
    bar_index: int
    fill_ts: datetime
    direction: Direction
    quantity: Decimal
    price: Decimal
    cost: Decimal
    reason: FillReason

    def to_dict(self) -> dict[str, Any]:
        return {
            "fill_id": self.fill_id,
            "order_id": self.order_id,
            "signal_id": self.signal_id,
            "instrument_id": self.instrument_id,
            "session_id": self.session_id,
            "bar_index": self.bar_index,
            "fill_ts": _datetime_text(self.fill_ts),
            "direction": self.direction.value,
            "quantity": str(self.quantity),
            "price": str(self.price),
            "cost": str(self.cost),
            "reason": self.reason.value,
        }


@dataclass(frozen=True, slots=True)
class StopTargetResolution:
    """Resolved stop/target outcome for one bar, if any."""

    intent: OrderIntent
    reason: FillReason
    price: Decimal
    ambiguous: bool


def resolve_entry_fill(
    order: ReferenceOrder,
    bar: Mapping[str, Any],
    config: ReferenceEngineConfig,
    *,
    multiplier: Decimal = Decimal("1"),
    symbol: str | None = None,
) -> ReferenceFill:
    """Resolve an entry at the conservative executable side of the selected bar."""
    price = _entry_price(order.direction, bar)
    return _fill(
        order,
        bar,
        config,
        price=price,
        reason=FillReason.ENTRY_SIGNAL,
        multiplier=multiplier,
        symbol=symbol,
    )


def resolve_exit_signal_fill(
    order: ReferenceOrder,
    bar: Mapping[str, Any],
    config: ReferenceEngineConfig,
    *,
    multiplier: Decimal = Decimal("1"),
    symbol: str | None = None,
) -> ReferenceFill:
    """Resolve a signal exit at the conservative executable side of the selected bar."""
    price = _exit_price(order.direction, bar)
    return _fill(
        order,
        bar,
        config,
        price=price,
        reason=FillReason.EXIT_SIGNAL,
        multiplier=multiplier,
        symbol=symbol,
    )


def resolve_policy_exit_fill(
    order: ReferenceOrder,
    bar: Mapping[str, Any],
    config: ReferenceEngineConfig,
    *,
    price: Decimal,
    reason: FillReason,
    multiplier: Decimal = Decimal("1"),
    symbol: str | None = None,
) -> ReferenceFill:
    """Resolve a stop, target, or EOD policy exit."""
    return _fill(
        order,
        bar,
        config,
        price=price,
        reason=reason,
        multiplier=multiplier,
        symbol=symbol,
    )


def resolve_stop_target(
    *,
    direction: Direction,
    entry_price: Decimal,
    bar: Mapping[str, Any],
    stop_loss_pct: Decimal | None,
    target_profit_pct: Decimal | None,
) -> StopTargetResolution | None:
    """Resolve same-bar stop/target ambiguity conservatively."""
    if stop_loss_pct is None and target_profit_pct is None:
        return None

    high = _decimal(bar["high"])
    low = _decimal(bar["low"])
    stop_price: Decimal | None = None
    target_price: Decimal | None = None
    stop_hit = False
    target_hit = False

    if direction is Direction.LONG:
        if stop_loss_pct is not None:
            stop_price = entry_price * (Decimal("1") - stop_loss_pct)
            stop_hit = low <= stop_price
        if target_profit_pct is not None:
            target_price = entry_price * (Decimal("1") + target_profit_pct)
            target_hit = high >= target_price
    elif direction is Direction.SHORT:
        if stop_loss_pct is not None:
            stop_price = entry_price * (Decimal("1") + stop_loss_pct)
            stop_hit = high >= stop_price
        if target_profit_pct is not None:
            target_price = entry_price * (Decimal("1") - target_profit_pct)
            target_hit = low <= target_price
    else:
        return None

    if stop_hit and target_hit and stop_price is not None:
        return StopTargetResolution(
            intent=OrderIntent.STOP_LOSS,
            reason=FillReason.STOP_LOSS,
            price=stop_price,
            ambiguous=True,
        )
    if stop_hit and stop_price is not None:
        return StopTargetResolution(
            intent=OrderIntent.STOP_LOSS,
            reason=FillReason.STOP_LOSS,
            price=stop_price,
            ambiguous=False,
        )
    if target_hit and target_price is not None:
        return StopTargetResolution(
            intent=OrderIntent.TAKE_PROFIT,
            reason=FillReason.TAKE_PROFIT,
            price=target_price,
            ambiguous=False,
        )
    return None


def eod_exit_price(direction: Direction, bar: Mapping[str, Any]) -> Decimal:
    """Return the conservative EOD flat exit price."""
    return _exit_price(direction, bar, fallback_field="close")


def _fill(
    order: ReferenceOrder,
    bar: Mapping[str, Any],
    config: ReferenceEngineConfig,
    *,
    price: Decimal,
    reason: FillReason,
    multiplier: Decimal = Decimal("1"),
    symbol: str | None = None,
) -> ReferenceFill:
    cost = _fill_cost(
        config.cost_model,
        bar=bar,
        price=price,
        quantity=order.quantity,
        direction=order.direction,
        multiplier=multiplier,
        symbol=symbol,
    )
    bar_index = int(bar["bar_index"])
    fill_ts = _datetime(bar["bar_start_ts"] if reason in {FillReason.ENTRY_SIGNAL, FillReason.EXIT_SIGNAL} else bar["bar_end_ts"])
    return ReferenceFill(
        fill_id=f"{order.order_id}:fill:{bar_index}:{reason.value}",
        order_id=order.order_id,
        signal_id=order.signal_id,
        instrument_id=str(bar["instrument_id"]),
        session_id=str(bar["session_id"]),
        bar_index=bar_index,
        fill_ts=fill_ts,
        direction=order.direction,
        quantity=order.quantity,
        price=price,
        cost=cost,
        reason=reason,
    )


def _fill_cost(
    cost_model: Any,
    *,
    bar: Mapping[str, Any],
    price: Decimal,
    quantity: Decimal,
    direction: Direction,
    multiplier: Decimal,
    symbol: str | None,
) -> Decimal:
    """Compute the absolute fill cost in dollars.

    A rich ``SupportsCost`` model (``CompositeCostModel`` / ``SpreadCost`` /
    ``FuturesFeeScheduleCost``) is consumed through its full ``cost_for_fill``
    contract so per-contract futures fees, an explicit spread term, and the
    instrument symbol all flow through. The legacy ``fixed_bps`` hook
    (``CostModelConfig``) exposes only ``cost_for_notional``; it is charged on the
    dollar notional ``price * quantity * multiplier`` (back-compatible: with the
    default ``multiplier=1`` this is exactly the prior points notional).
    """
    cost_for_fill = getattr(cost_model, "cost_for_fill", None)
    if callable(cost_for_fill):
        from alpha_system.backtest.costs import CostInput

        metadata: dict[str, Any] = {}
        resolved_symbol = symbol if symbol is not None else bar.get("instrument_id")
        if resolved_symbol is not None:
            metadata["symbol"] = str(resolved_symbol)
        cost_input = CostInput(
            price=price,
            quantity=quantity,
            side="buy" if direction is Direction.LONG else "sell",
            bid=_optional_decimal(bar.get("bid")),
            ask=_optional_decimal(bar.get("ask")),
            spread=_optional_decimal(bar.get("spread")),
            multiplier=multiplier,
            metadata=metadata,
        )
        return cost_for_fill(cost_input).total
    return cost_model.cost_for_notional(price * quantity * multiplier)


def _optional_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    return _decimal(value)


def _entry_price(direction: Direction, bar: Mapping[str, Any]) -> Decimal:
    if direction is Direction.LONG:
        return _side_or_fallback(bar, "ask", "open")
    if direction is Direction.SHORT:
        return _side_or_fallback(bar, "bid", "open")
    msg = "entry fills require long or short direction"
    raise ValueError(msg)


def _exit_price(
    direction: Direction,
    bar: Mapping[str, Any],
    *,
    fallback_field: str = "open",
) -> Decimal:
    if direction is Direction.LONG:
        return _side_or_fallback(bar, "bid", fallback_field)
    if direction is Direction.SHORT:
        return _side_or_fallback(bar, "ask", fallback_field)
    msg = "exit fills require long or short direction"
    raise ValueError(msg)


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


def _datetime_text(value: datetime) -> str:
    return _datetime(value).isoformat().replace("+00:00", "Z")
