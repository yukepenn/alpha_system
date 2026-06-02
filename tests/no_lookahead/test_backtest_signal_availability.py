from __future__ import annotations

import pytest

from alpha_system.backtest.reference import BacktestTimingError, run_reference_backtest
from tests.fixtures.backtest_reference import signal_record, synthetic_bars, zero_cost_config


def test_signal_available_ts_must_not_precede_origin_bar_availability() -> None:
    bars = synthetic_bars(3, available_delay_seconds=5)
    early_signal = signal_record(0, "entry", available_delay_seconds=0)

    with pytest.raises(BacktestTimingError, match="signal available_ts"):
        run_reference_backtest(
            bars=bars,
            signals=[early_signal],
            config=zero_cost_config(data_latency_seconds=5),
            run_id="signal-availability-fail",
        )
