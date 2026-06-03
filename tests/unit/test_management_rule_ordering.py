from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from alpha_system.core.enums import Direction
from alpha_system.management.rules import MANAGEMENT_RULE_ORDER
from alpha_system.management.state import ManagedPositionState
from tests.fixtures.backtest_reference import DATA_VERSION, FACTOR_VERSIONS, INSTRUMENT_ID, SESSION_ID


def managed_state(
    *,
    initial_stop: Decimal | None = Decimal("98"),
    entry_bar_index: int = 0,
) -> ManagedPositionState:
    return ManagedPositionState(
        instrument_id=INSTRUMENT_ID,
        session_id=SESSION_ID,
        direction=Direction.LONG,
        entry_price=Decimal("100"),
        entry_ts=datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc),
        entry_bar_index=entry_bar_index,
        entry_signal_id="entry",
        entry_order_id="entry-order",
        entry_fill_id="entry-fill",
        initial_quantity=Decimal("1"),
        remaining_quantity=Decimal("1"),
        entry_cost_remaining=Decimal("0"),
        strategy_id="fixture_strategy",
        strategy_version="v1",
        data_version=DATA_VERSION,
        factor_versions=FACTOR_VERSIONS,
        initial_stop_price=initial_stop,
        active_stop_price=initial_stop,
        high_watermark=Decimal("100"),
        low_watermark=Decimal("100"),
    )


def test_management_rule_order_is_explicit_and_adverse_first() -> None:
    assert MANAGEMENT_RULE_ORDER == (
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
    assert MANAGEMENT_RULE_ORDER.index("active_stop") < MANAGEMENT_RULE_ORDER.index("full_target_r_multiple")
    assert MANAGEMENT_RULE_ORDER.index("active_stop") < MANAGEMENT_RULE_ORDER.index("laddered_partials")
