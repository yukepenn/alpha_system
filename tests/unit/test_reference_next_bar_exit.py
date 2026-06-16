from __future__ import annotations

from alpha_system.backtest.reference import run_reference_backtest
from tests.fixtures.backtest_reference import SYNTH_INSTRUMENT_MULTIPLIERS, signal_record, synthetic_bars, zero_cost_config


def test_reference_exit_signal_fills_on_next_eligible_bar() -> None:
    result = run_reference_backtest(
        bars=synthetic_bars(4),
        signals=[
            signal_record(0, "entry", signal_id="entry"),
            signal_record(1, "exit", signal_id="exit"),
        ],
        config=zero_cost_config(),
        run_id="exit-next-bar",
        instrument_multipliers=SYNTH_INSTRUMENT_MULTIPLIERS,
    )

    trade = result.trades[0]

    assert trade.entry_bar_index == 1
    assert trade.exit_signal_id == "exit"
    assert trade.exit_bar_index == 2
    assert trade.exit_bar_index > 1
