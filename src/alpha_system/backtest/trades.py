"""Trade journal schema and assembly for reference backtest results."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from alpha_system.backtest.accounting import ClosedPosition
from alpha_system.backtest.fills import FillReason


TRADE_JOURNAL_FIELDS: tuple[str, ...] = (
    "trade_id",
    "run_id",
    "instrument_id",
    "session_id",
    "strategy_id",
    "strategy_version",
    "direction",
    "quantity",
    "entry_signal_id",
    "exit_signal_id",
    "entry_order_id",
    "exit_order_id",
    "entry_ts",
    "exit_ts",
    "entry_bar_index",
    "exit_bar_index",
    "entry_price",
    "exit_price",
    "gross_pnl",
    "costs",
    "net_pnl",
    "exit_reason",
    "data_version",
    "factor_versions",
    "quality_flags",
)


@dataclass(frozen=True, slots=True)
class TradeRecord:
    """One closed-position journal record."""

    trade_id: str
    run_id: str
    instrument_id: str
    session_id: str
    strategy_id: str
    strategy_version: str
    direction: str
    quantity: Decimal
    entry_signal_id: str | None
    exit_signal_id: str | None
    entry_order_id: str
    exit_order_id: str
    entry_ts: datetime
    exit_ts: datetime
    entry_bar_index: int
    exit_bar_index: int
    entry_price: Decimal
    exit_price: Decimal
    gross_pnl: Decimal
    costs: Decimal
    net_pnl: Decimal
    exit_reason: str
    data_version: str
    factor_versions: Mapping[str, str]
    quality_flags: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "trade_id": self.trade_id,
            "run_id": self.run_id,
            "instrument_id": self.instrument_id,
            "session_id": self.session_id,
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "direction": self.direction,
            "quantity": _decimal_text(self.quantity),
            "entry_signal_id": self.entry_signal_id,
            "exit_signal_id": self.exit_signal_id,
            "entry_order_id": self.entry_order_id,
            "exit_order_id": self.exit_order_id,
            "entry_ts": _datetime_text(self.entry_ts),
            "exit_ts": _datetime_text(self.exit_ts),
            "entry_bar_index": self.entry_bar_index,
            "exit_bar_index": self.exit_bar_index,
            "entry_price": _decimal_text(self.entry_price),
            "exit_price": _decimal_text(self.exit_price),
            "gross_pnl": _decimal_text(self.gross_pnl),
            "costs": _decimal_text(self.costs),
            "net_pnl": _decimal_text(self.net_pnl),
            "exit_reason": self.exit_reason,
            "data_version": self.data_version,
            "factor_versions": dict(sorted(self.factor_versions.items())),
            "quality_flags": list(self.quality_flags),
        }


def trade_from_closed_position(
    closed: ClosedPosition,
    *,
    run_id: str,
    sequence: int,
    quality_flags: tuple[str, ...],
) -> TradeRecord:
    """Build a stable trade journal record from accounting state."""
    position = closed.position
    exit_fill = closed.exit_fill
    return TradeRecord(
        trade_id=f"{run_id}:trade:{sequence:06d}",
        run_id=run_id,
        instrument_id=position.instrument_id,
        session_id=position.session_id,
        strategy_id=position.strategy_id,
        strategy_version=position.strategy_version,
        direction=position.direction.value,
        quantity=position.quantity,
        entry_signal_id=position.entry_signal_id,
        exit_signal_id=exit_fill.signal_id,
        entry_order_id=position.entry_order_id,
        exit_order_id=exit_fill.order_id,
        entry_ts=position.entry_ts,
        exit_ts=exit_fill.fill_ts,
        entry_bar_index=position.entry_bar_index,
        exit_bar_index=exit_fill.bar_index,
        entry_price=position.entry_price,
        exit_price=exit_fill.price,
        gross_pnl=closed.gross_pnl,
        costs=closed.costs,
        net_pnl=closed.net_pnl,
        exit_reason=_exit_reason(exit_fill.reason),
        data_version=position.data_version,
        factor_versions=position.factor_versions,
        quality_flags=quality_flags,
    )


def assert_trade_journal_schema(record: TradeRecord | Mapping[str, Any]) -> None:
    payload = record.to_dict() if isinstance(record, TradeRecord) else dict(record)
    fields = tuple(payload)
    if fields != TRADE_JOURNAL_FIELDS:
        msg = f"trade journal fields differ from schema: {fields!r}"
        raise ValueError(msg)


def _exit_reason(reason: FillReason) -> str:
    if reason is FillReason.STOP_LOSS:
        return "stop_loss"
    if reason is FillReason.TAKE_PROFIT:
        return "take_profit"
    if reason is FillReason.EOD_FLAT:
        return "eod_flat"
    return "exit_signal"


def _datetime_text(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")
