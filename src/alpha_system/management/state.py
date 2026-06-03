"""Deterministic state containers for position management."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal

from alpha_system.backtest.accounting import Position
from alpha_system.core.enums import Direction


@dataclass(frozen=True, slots=True)
class ManagedPositionState:
    """Management-owned state for one open reference position."""

    instrument_id: str
    session_id: str
    direction: Direction
    entry_price: Decimal
    entry_ts: datetime
    entry_bar_index: int
    entry_signal_id: str | None
    entry_order_id: str
    entry_fill_id: str
    initial_quantity: Decimal
    remaining_quantity: Decimal
    entry_cost_remaining: Decimal
    strategy_id: str
    strategy_version: str
    data_version: str
    factor_versions: Mapping[str, str]
    initial_stop_price: Decimal | None = None
    active_stop_price: Decimal | None = None
    high_watermark: Decimal | None = None
    low_watermark: Decimal | None = None
    filled_partial_labels: tuple[str, ...] = ()

    @classmethod
    def from_position(
        cls,
        position: Position,
        *,
        initial_stop_price: Decimal | None,
    ) -> "ManagedPositionState":
        return cls(
            instrument_id=position.instrument_id,
            session_id=position.session_id,
            direction=position.direction,
            entry_price=position.entry_price,
            entry_ts=position.entry_ts,
            entry_bar_index=position.entry_bar_index,
            entry_signal_id=position.entry_signal_id,
            entry_order_id=position.entry_order_id,
            entry_fill_id=position.entry_fill_id,
            initial_quantity=position.quantity,
            remaining_quantity=position.quantity,
            entry_cost_remaining=position.entry_cost,
            strategy_id=position.strategy_id,
            strategy_version=position.strategy_version,
            data_version=position.data_version,
            factor_versions=dict(position.factor_versions),
            initial_stop_price=initial_stop_price,
            active_stop_price=initial_stop_price,
            high_watermark=position.entry_price,
            low_watermark=position.entry_price,
        )

    @property
    def risk_per_unit(self) -> Decimal | None:
        if self.initial_stop_price is None:
            return None
        risk = abs(self.entry_price - self.initial_stop_price)
        if risk <= 0:
            return None
        return risk

    def bars_held_at(self, bar_index: int) -> int:
        return max(0, int(bar_index) - self.entry_bar_index)

    def with_quantity(self, *, remaining_quantity: Decimal, entry_cost_remaining: Decimal) -> "ManagedPositionState":
        return replace(
            self,
            remaining_quantity=remaining_quantity,
            entry_cost_remaining=entry_cost_remaining,
        )

    def with_partial_label(self, label: str) -> "ManagedPositionState":
        labels = tuple((*self.filled_partial_labels, label))
        return replace(self, filled_partial_labels=labels)

    def with_stop(self, stop_price: Decimal | None) -> "ManagedPositionState":
        return replace(self, active_stop_price=stop_price)

    def with_watermarks(self, *, high: Decimal, low: Decimal) -> "ManagedPositionState":
        high_watermark = high if self.high_watermark is None else max(self.high_watermark, high)
        low_watermark = low if self.low_watermark is None else min(self.low_watermark, low)
        return replace(self, high_watermark=high_watermark, low_watermark=low_watermark)


@dataclass(frozen=True, slots=True)
class ManagementRuntimeState:
    """Session-scoped entry gates owned by management."""

    current_session_id: str | None = None
    trades_by_session: Mapping[str, int] | None = None
    cooldown_until_bar_by_session: Mapping[str, int] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "trades_by_session", dict(self.trades_by_session or {}))
        object.__setattr__(self, "cooldown_until_bar_by_session", dict(self.cooldown_until_bar_by_session or {}))

    def for_session(self, session_id: str, *, session_reset: bool) -> "ManagementRuntimeState":
        if self.current_session_id == session_id:
            return self
        if not session_reset:
            return replace(self, current_session_id=session_id)
        return ManagementRuntimeState(
            current_session_id=session_id,
            trades_by_session={session_id: dict(self.trades_by_session or {}).get(session_id, 0)},
            cooldown_until_bar_by_session={},
        )

    def can_enter(
        self,
        *,
        session_id: str,
        bar_index: int,
        max_trades_per_day: int | None,
    ) -> bool:
        trades = dict(self.trades_by_session or {}).get(session_id, 0)
        if max_trades_per_day is not None and trades >= max_trades_per_day:
            return False
        cooldown_until = dict(self.cooldown_until_bar_by_session or {}).get(session_id)
        if cooldown_until is not None and bar_index < cooldown_until:
            return False
        return True

    def record_entry(self, *, session_id: str) -> "ManagementRuntimeState":
        trades = dict(self.trades_by_session or {})
        trades[session_id] = trades.get(session_id, 0) + 1
        return replace(self, trades_by_session=trades, current_session_id=session_id)

    def record_exit(
        self,
        *,
        session_id: str,
        exit_bar_index: int,
        cooldown_bars: int | None,
    ) -> "ManagementRuntimeState":
        if cooldown_bars is None:
            return replace(self, current_session_id=session_id)
        cooldowns = dict(self.cooldown_until_bar_by_session or {})
        cooldowns[session_id] = exit_bar_index + cooldown_bars
        return replace(self, cooldown_until_bar_by_session=cooldowns, current_session_id=session_id)
