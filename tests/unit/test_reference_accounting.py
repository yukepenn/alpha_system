from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from alpha_system.backtest.accounting import AccountState, realized_pnl_for
from alpha_system.backtest.fills import FillReason, ReferenceFill
from alpha_system.core.enums import Direction


def test_accounting_computes_long_and_short_pnl_deterministically() -> None:
    assert realized_pnl_for(
        direction=Direction.LONG,
        entry_price=Decimal("100"),
        exit_price=Decimal("101.5"),
        quantity=Decimal("2"),
    ) == Decimal("3.0")
    assert realized_pnl_for(
        direction=Direction.SHORT,
        entry_price=Decimal("100"),
        exit_price=Decimal("98"),
        quantity=Decimal("3"),
    ) == Decimal("6")


def test_account_state_tracks_costs_and_realized_pnl() -> None:
    account = AccountState(initial_cash=Decimal("1000"))
    entry = _fill("entry", Direction.LONG, Decimal("100"), Decimal("1"))
    exit_ = _fill("exit", Direction.LONG, Decimal("105"), Decimal("2"), reason=FillReason.EXIT_SIGNAL)

    account = account.open_position(
        entry,
        strategy_id="strategy",
        strategy_version="v1",
        data_version="data:v1",
        factor_versions={"factor": "v1"},
    )
    account, closed = account.close_position(exit_)

    assert closed.gross_pnl == Decimal("5")
    assert closed.costs == Decimal("3")
    assert closed.net_pnl == Decimal("2")
    assert account.realized_pnl == Decimal("2")


def _fill(
    suffix: str,
    direction: Direction,
    price: Decimal,
    cost: Decimal,
    *,
    reason: FillReason = FillReason.ENTRY_SIGNAL,
) -> ReferenceFill:
    return ReferenceFill(
        fill_id=f"fill-{suffix}",
        order_id=f"order-{suffix}",
        signal_id=f"signal-{suffix}",
        instrument_id="SYNTH",
        session_id="session",
        bar_index=1,
        fill_ts=datetime(2026, 1, 2, 14, 31, tzinfo=timezone.utc),
        direction=direction,
        quantity=Decimal("1"),
        price=price,
        cost=cost,
        reason=reason,
    )
