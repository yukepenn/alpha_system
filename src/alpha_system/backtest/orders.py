"""Internal research-only order intents for the reference backtest engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any

from alpha_system.core.enums import Direction


class OrderIntent(str, Enum):
    """Reference-engine intent type, not a broker/live order lifecycle."""

    ENTRY = "entry"
    EXIT = "exit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    EOD_FLAT = "eod_flat"


@dataclass(frozen=True, slots=True, kw_only=True)
class ReferenceOrder:
    """Deterministic internal order intent created from signals or policy."""

    order_id: str
    signal_id: str | None
    instrument_id: str
    session_id: str
    origin_bar_index: int
    earliest_bar_index: int
    available_ts: datetime
    intent: OrderIntent
    direction: Direction
    quantity: Decimal

    def to_dict(self) -> dict[str, Any]:
        return {
            "order_id": self.order_id,
            "signal_id": self.signal_id,
            "instrument_id": self.instrument_id,
            "session_id": self.session_id,
            "origin_bar_index": self.origin_bar_index,
            "earliest_bar_index": self.earliest_bar_index,
            "available_ts": _datetime_text(self.available_ts),
            "intent": self.intent.value,
            "direction": self.direction.value,
            "quantity": str(self.quantity),
        }


def order_id_for(
    *,
    run_id: str,
    signal_id: str | None,
    instrument_id: str,
    session_id: str,
    bar_index: int,
    intent: OrderIntent,
) -> str:
    """Return a stable internal order id."""
    signal_part = signal_id or "policy"
    return f"{run_id}:{instrument_id}:{session_id}:{bar_index}:{intent.value}:{signal_part}"


def _datetime_text(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
