from __future__ import annotations

from decimal import Decimal

from alpha_system.backtest.reference import run_reference_backtest
from tests.fixtures.backtest_reference import signal_record, synthetic_bar, zero_cost_config


def test_same_bar_stop_target_ambiguity_resolves_adverse_first() -> None:
    bars = [
        synthetic_bar(0, open_price="100", high="101", low="99", close="100"),
        synthetic_bar(1, open_price="100", high="103", low="97", close="101"),
        synthetic_bar(2, open_price="101", high="102", low="100", close="101"),
    ]

    result = run_reference_backtest(
        bars=bars,
        signals=[signal_record(0, "entry", signal_id="entry")],
        config=zero_cost_config(
            stop_loss_pct=Decimal("0.01"),
            target_profit_pct=Decimal("0.01"),
        ),
        run_id="same-bar-adverse",
    )

    trade = result.trades[0]

    assert trade.entry_bar_index == 1
    assert trade.exit_bar_index == 1
    assert trade.exit_reason == "stop_loss"
    assert trade.net_pnl < 0
