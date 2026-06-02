"""Deterministic position and PnL accounting for the reference engine."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from typing import Any

from alpha_system.backtest.fills import ReferenceFill
from alpha_system.core.enums import Direction


class AccountingError(ValueError):
    """Raised when accounting state would become ambiguous."""


@dataclass(frozen=True, slots=True)
class Position:
    """One open reference position."""

    instrument_id: str
    session_id: str
    direction: Direction
    quantity: Decimal
    entry_price: Decimal
    entry_ts: datetime
    entry_bar_index: int
    entry_signal_id: str | None
    entry_order_id: str
    entry_fill_id: str
    entry_cost: Decimal
    strategy_id: str
    strategy_version: str
    data_version: str
    factor_versions: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class ClosedPosition:
    """A completed position with deterministic accounting fields."""

    position: Position
    exit_fill: ReferenceFill
    gross_pnl: Decimal
    costs: Decimal
    net_pnl: Decimal


@dataclass(frozen=True, slots=True)
class AccountState:
    """Immutable-ish account state updated by fills."""

    initial_cash: Decimal = Decimal("100000")
    realized_pnl: Decimal = Decimal("0")
    positions: Mapping[str, Position] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "initial_cash", _decimal(self.initial_cash))
        object.__setattr__(self, "realized_pnl", _decimal(self.realized_pnl))
        object.__setattr__(self, "positions", dict(self.positions or {}))

    @property
    def open_positions(self) -> Mapping[str, Position]:
        return dict(self.positions or {})

    def open_position(
        self,
        fill: ReferenceFill,
        *,
        strategy_id: str,
        strategy_version: str,
        data_version: str,
        factor_versions: Mapping[str, str],
    ) -> "AccountState":
        """Open one position for an instrument."""
        positions = dict(self.open_positions)
        if fill.instrument_id in positions:
            msg = f"position already open for {fill.instrument_id}"
            raise AccountingError(msg)
        positions[fill.instrument_id] = Position(
            instrument_id=fill.instrument_id,
            session_id=fill.session_id,
            direction=fill.direction,
            quantity=fill.quantity,
            entry_price=fill.price,
            entry_ts=fill.fill_ts,
            entry_bar_index=fill.bar_index,
            entry_signal_id=fill.signal_id,
            entry_order_id=fill.order_id,
            entry_fill_id=fill.fill_id,
            entry_cost=fill.cost,
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            data_version=data_version,
            factor_versions=dict(factor_versions),
        )
        return replace(self, positions=positions)

    def close_position(self, fill: ReferenceFill) -> tuple["AccountState", ClosedPosition]:
        """Close one position and return updated state plus accounting result."""
        positions = dict(self.open_positions)
        position = positions.pop(fill.instrument_id, None)
        if position is None:
            msg = f"no position open for {fill.instrument_id}"
            raise AccountingError(msg)
        gross_pnl = realized_pnl_for(
            direction=position.direction,
            entry_price=position.entry_price,
            exit_price=fill.price,
            quantity=position.quantity,
        )
        costs = position.entry_cost + fill.cost
        net_pnl = gross_pnl - costs
        closed = ClosedPosition(
            position=position,
            exit_fill=fill,
            gross_pnl=gross_pnl,
            costs=costs,
            net_pnl=net_pnl,
        )
        return (
            replace(self, realized_pnl=self.realized_pnl + net_pnl, positions=positions),
            closed,
        )

    def unrealized_pnl(self, marks: Mapping[str, Decimal]) -> Decimal:
        """Return mark-to-market unrealized PnL for open positions."""
        total = Decimal("0")
        for instrument_id, position in self.open_positions.items():
            mark = marks.get(instrument_id, position.entry_price)
            total += realized_pnl_for(
                direction=position.direction,
                entry_price=position.entry_price,
                exit_price=mark,
                quantity=position.quantity,
            ) - position.entry_cost
        return total

    def total_equity(self, marks: Mapping[str, Decimal]) -> Decimal:
        return self.initial_cash + self.realized_pnl + self.unrealized_pnl(marks)


def realized_pnl_for(
    *,
    direction: Direction,
    entry_price: Decimal,
    exit_price: Decimal,
    quantity: Decimal,
) -> Decimal:
    """Return gross realized PnL for a long or short position."""
    if direction is Direction.LONG:
        return (exit_price - entry_price) * quantity
    if direction is Direction.SHORT:
        return (entry_price - exit_price) * quantity
    msg = "PnL requires long or short direction"
    raise AccountingError(msg)


def _decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))
