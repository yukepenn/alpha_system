"""Deterministic equity-curve construction for reference backtests."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from alpha_system.backtest.accounting import AccountState


EQUITY_CURVE_FIELDS: tuple[str, ...] = (
    "run_id",
    "timestamp",
    "bar_end_ts",
    "instrument_id",
    "session_id",
    "bar_index",
    "cash",
    "realized_pnl",
    "unrealized_pnl",
    "total_equity",
    "open_positions",
)


@dataclass(frozen=True, slots=True)
class EquityPoint:
    """One deterministic equity-curve row."""

    run_id: str
    timestamp: datetime
    bar_end_ts: datetime
    instrument_id: str
    session_id: str
    bar_index: int
    cash: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    total_equity: Decimal
    open_positions: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "timestamp": _datetime_text(self.timestamp),
            "bar_end_ts": _datetime_text(self.bar_end_ts),
            "instrument_id": self.instrument_id,
            "session_id": self.session_id,
            "bar_index": self.bar_index,
            "cash": _decimal_text(self.cash),
            "realized_pnl": _decimal_text(self.realized_pnl),
            "unrealized_pnl": _decimal_text(self.unrealized_pnl),
            "total_equity": _decimal_text(self.total_equity),
            "open_positions": self.open_positions,
        }


def equity_point_for_bar(
    *,
    run_id: str,
    bar: Mapping[str, Any],
    account: AccountState,
    marks: Mapping[str, Decimal],
) -> EquityPoint:
    """Create one equity row after processing a bar."""
    unrealized = account.unrealized_pnl(marks)
    return EquityPoint(
        run_id=run_id,
        timestamp=_datetime(bar["bar_end_ts"]),
        bar_end_ts=_datetime(bar["bar_end_ts"]),
        instrument_id=str(bar["instrument_id"]),
        session_id=str(bar["session_id"]),
        bar_index=int(bar["bar_index"]),
        cash=account.initial_cash + account.realized_pnl,
        realized_pnl=account.realized_pnl,
        unrealized_pnl=unrealized,
        total_equity=account.initial_cash + account.realized_pnl + unrealized,
        open_positions=len(account.open_positions),
    )


def assert_equity_curve_schema(record: EquityPoint | Mapping[str, Any]) -> None:
    payload = record.to_dict() if isinstance(record, EquityPoint) else dict(record)
    fields = tuple(payload)
    if fields != EQUITY_CURVE_FIELDS:
        msg = f"equity curve fields differ from schema: {fields!r}"
        raise ValueError(msg)


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


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")
