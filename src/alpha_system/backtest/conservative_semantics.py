"""Named conservative execution semantics for Tier 1 research backtests."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any


NEXT_BAR_CONSERVATIVE = "next_bar_conservative"
SAME_BAR_ADVERSE_FIRST = "adverse_first"
MISSING_BID_ASK_FALLBACK_TO_OHLC = "fallback_to_ohlc_with_warning"


class ConservativeSemanticsError(ValueError):
    """Raised when execution semantics would be optimistic or ambiguous."""


class FillIntent(str, Enum):
    """Research fill intent understood by conservative fill models."""

    ENTRY = "entry"
    EXIT = "exit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    EOD_FLAT = "eod_flat"


@dataclass(frozen=True, slots=True)
class ConservativePrice:
    """Resolved price plus provenance for spread/missing-quote handling."""

    price: Decimal
    side: str
    source: str
    used_bid_ask: bool
    missing_bid_ask_fallback: bool
    warning: str | None = None

    def to_dict(self) -> dict[str, str | bool | None]:
        return {
            "price": _decimal_text(self.price),
            "side": self.side,
            "source": self.source,
            "used_bid_ask": self.used_bid_ask,
            "missing_bid_ask_fallback": self.missing_bid_ask_fallback,
            "warning": self.warning,
        }


@dataclass(frozen=True, slots=True)
class StopTargetOutcome:
    """Conservative same-bar stop/target outcome."""

    reason: str
    price: Decimal
    ambiguous: bool

    def to_dict(self) -> dict[str, str | bool]:
        return {
            "reason": self.reason,
            "price": _decimal_text(self.price),
            "ambiguous": self.ambiguous,
        }


def assert_conservative_execution_defaults(
    *,
    execution_timing: str,
    same_bar_policy: str,
    zero_cost_fixture: bool,
) -> None:
    """Validate the non-test defaults required by ASV1-P16."""

    if execution_timing != NEXT_BAR_CONSERVATIVE:
        msg = "default execution must be next_bar_conservative"
        raise ConservativeSemanticsError(msg)
    if same_bar_policy != SAME_BAR_ADVERSE_FIRST:
        msg = "same-bar ambiguity must resolve adverse_first"
        raise ConservativeSemanticsError(msg)
    if zero_cost_fixture:
        msg = "zero-cost execution configs must be fixture/test-only, never defaults"
        raise ConservativeSemanticsError(msg)


def signal_fill_bar_is_allowed(*, signal_bar_index: int, fill_bar_index: int) -> bool:
    """Return whether a signal can fill under default next-bar semantics."""

    return fill_bar_index > signal_bar_index


def conservative_price(
    *,
    direction: str,
    intent: str,
    bar: Mapping[str, Any],
    fallback_field: str = "open",
    missing_bid_ask_policy: str = MISSING_BID_ASK_FALLBACK_TO_OHLC,
) -> ConservativePrice:
    """Resolve the conservative executable side for one 1-minute bar."""

    active_direction = _direction(direction)
    active_intent = _intent(intent)
    side = executable_side(direction=active_direction, intent=active_intent)
    if side == "buy":
        quote_field = "ask"
    else:
        quote_field = "bid"
    quote = bar.get(quote_field)
    if quote is not None:
        return ConservativePrice(
            price=_decimal(quote, quote_field),
            side=side,
            source=quote_field,
            used_bid_ask=True,
            missing_bid_ask_fallback=False,
        )
    if missing_bid_ask_policy != MISSING_BID_ASK_FALLBACK_TO_OHLC:
        msg = f"unsupported missing bid/ask policy: {missing_bid_ask_policy}"
        raise ConservativeSemanticsError(msg)
    price = _decimal(bar[fallback_field], fallback_field)
    return ConservativePrice(
        price=price,
        side=side,
        source=fallback_field,
        used_bid_ask=False,
        missing_bid_ask_fallback=True,
        warning=f"{quote_field} missing; used {fallback_field} by explicit policy",
    )


def executable_side(*, direction: str, intent: str) -> str:
    """Return buy/sell side for a direction and fill intent."""

    active_direction = _direction(direction)
    active_intent = _intent(intent)
    is_entry = active_intent == FillIntent.ENTRY.value
    if active_direction == "long":
        return "buy" if is_entry else "sell"
    return "sell" if is_entry else "buy"


def resolve_same_bar_stop_target(
    *,
    direction: str,
    entry_price: Decimal,
    high: Decimal,
    low: Decimal,
    stop_loss_pct: Decimal | None,
    target_profit_pct: Decimal | None,
) -> StopTargetOutcome | None:
    """Resolve stop/target ambiguity adverse-first from OHLC-only evidence."""

    active_direction = _direction(direction)
    active_entry = _positive_decimal(entry_price, "entry_price")
    high_decimal = _non_negative_decimal(high, "high")
    low_decimal = _non_negative_decimal(low, "low")
    stop_pct = None if stop_loss_pct is None else _positive_decimal(stop_loss_pct, "stop_loss_pct")
    target_pct = None if target_profit_pct is None else _positive_decimal(target_profit_pct, "target_profit_pct")
    if stop_pct is None and target_pct is None:
        return None

    stop_price: Decimal | None = None
    target_price: Decimal | None = None
    stop_hit = False
    target_hit = False
    if active_direction == "long":
        if stop_pct is not None:
            stop_price = active_entry * (Decimal("1") - stop_pct)
            stop_hit = low_decimal <= stop_price
        if target_pct is not None:
            target_price = active_entry * (Decimal("1") + target_pct)
            target_hit = high_decimal >= target_price
    else:
        if stop_pct is not None:
            stop_price = active_entry * (Decimal("1") + stop_pct)
            stop_hit = high_decimal >= stop_price
        if target_pct is not None:
            target_price = active_entry * (Decimal("1") - target_pct)
            target_hit = low_decimal <= target_price

    if stop_hit and target_hit and stop_price is not None:
        return StopTargetOutcome(reason=FillIntent.STOP_LOSS.value, price=stop_price, ambiguous=True)
    if stop_hit and stop_price is not None:
        return StopTargetOutcome(reason=FillIntent.STOP_LOSS.value, price=stop_price, ambiguous=False)
    if target_hit and target_price is not None:
        return StopTargetOutcome(reason=FillIntent.TAKE_PROFIT.value, price=target_price, ambiguous=False)
    return None


def _direction(value: str) -> str:
    active = _text(value, "direction")
    if active not in {"long", "short"}:
        msg = "direction must be long or short"
        raise ConservativeSemanticsError(msg)
    return active


def _intent(value: str) -> str:
    active = _text(value, "intent")
    values = {item.value for item in FillIntent}
    if active not in values:
        msg = f"intent must be one of {sorted(values)}"
        raise ConservativeSemanticsError(msg)
    return active


def _text(value: Any, field_name: str) -> str:
    if hasattr(value, "value"):
        value = value.value
    if not isinstance(value, str) or not value.strip():
        msg = f"{field_name} must be a non-empty string"
        raise ConservativeSemanticsError(msg)
    return value.strip()


def _decimal(value: Any, field_name: str) -> Decimal:
    if isinstance(value, bool):
        msg = f"{field_name} must be numeric"
        raise ConservativeSemanticsError(msg)
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        msg = f"{field_name} must be numeric"
        raise ConservativeSemanticsError(msg) from exc


def _non_negative_decimal(value: Any, field_name: str) -> Decimal:
    active = _decimal(value, field_name)
    if active < Decimal("0"):
        msg = f"{field_name} must be non-negative"
        raise ConservativeSemanticsError(msg)
    return active


def _positive_decimal(value: Any, field_name: str) -> Decimal:
    active = _decimal(value, field_name)
    if active <= Decimal("0"):
        msg = f"{field_name} must be positive"
        raise ConservativeSemanticsError(msg)
    return active


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")
