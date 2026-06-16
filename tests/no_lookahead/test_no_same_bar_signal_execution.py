from __future__ import annotations

from alpha_system.backtest.reference import run_reference_backtest
from tests.fixtures.backtest_reference import SYNTH_INSTRUMENT_MULTIPLIERS, signal_record, synthetic_bars, zero_cost_config


def test_signal_on_bar_never_executes_inside_same_bar_by_default() -> None:
    result = run_reference_backtest(
        bars=synthetic_bars(4),
        signals=[
            signal_record(1, "entry", signal_id="entry-on-bar-one"),
            signal_record(2, "exit", signal_id="exit-on-bar-two"),
        ],
        config=zero_cost_config(),
        run_id="no-same-bar",
        instrument_multipliers=SYNTH_INSTRUMENT_MULTIPLIERS,
    )

    trade = result.trades[0]

    assert trade.entry_bar_index == 2
    assert trade.entry_bar_index != 1
    assert trade.exit_bar_index == 3
    assert trade.exit_bar_index != 2
