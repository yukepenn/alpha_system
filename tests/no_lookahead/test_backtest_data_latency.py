from __future__ import annotations

import pytest

from alpha_system.backtest.reference import BacktestTimingError, run_reference_backtest
from tests.fixtures.backtest_reference import SYNTH_INSTRUMENT_MULTIPLIERS, signal_record, synthetic_bars, zero_cost_config


def test_bar_available_ts_must_respect_configured_data_latency() -> None:
    with pytest.raises(BacktestTimingError, match="configured latency"):
        run_reference_backtest(
            bars=synthetic_bars(3, available_delay_seconds=0),
            signals=[signal_record(0, "entry")],
            config=zero_cost_config(data_latency_seconds=5),
            run_id="latency-fail",
            instrument_multipliers=SYNTH_INSTRUMENT_MULTIPLIERS,
        )


def test_signal_executes_on_first_bar_whose_open_is_after_availability() -> None:
    result = run_reference_backtest(
        bars=synthetic_bars(5, available_delay_seconds=5),
        signals=[
            signal_record(0, "entry", available_delay_seconds=5),
            signal_record(2, "exit", available_delay_seconds=5),
        ],
        config=zero_cost_config(data_latency_seconds=5),
        run_id="latency-skip",
        instrument_multipliers=SYNTH_INSTRUMENT_MULTIPLIERS,
    )

    trade = result.trades[0]

    assert trade.entry_bar_index == 2
    assert trade.entry_bar_index > 1
