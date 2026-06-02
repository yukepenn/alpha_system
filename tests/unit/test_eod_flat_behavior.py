from __future__ import annotations

from alpha_system.backtest.reference import run_reference_backtest
from tests.fixtures.backtest_reference import signal_record, synthetic_bars, zero_cost_config


def test_eod_flat_closes_open_position_on_last_session_bar() -> None:
    result = run_reference_backtest(
        bars=synthetic_bars(3),
        signals=[signal_record(0, "entry", signal_id="entry")],
        config=zero_cost_config(eod_flat=True),
        run_id="eod-flat",
    )

    trade = result.trades[0]

    assert trade.exit_reason == "eod_flat"
    assert trade.exit_signal_id is None
    assert trade.exit_bar_index == 2
    assert result.summary.open_positions == 0
