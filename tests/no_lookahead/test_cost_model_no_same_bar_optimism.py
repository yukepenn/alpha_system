from __future__ import annotations

from decimal import Decimal

from alpha_system.backtest.conservative_semantics import (
    resolve_same_bar_stop_target,
    signal_fill_bar_is_allowed,
)
from alpha_system.backtest.execution_config import fixture_zero_cost_execution_config
from alpha_system.backtest.reference import run_reference_backtest
from tests.fixtures.backtest_reference import SYNTH_INSTRUMENT_MULTIPLIERS, signal_record, synthetic_bar


def test_cost_model_does_not_enable_same_bar_signal_execution() -> None:
    bars = [
        synthetic_bar(0, open_price="100", high="101", low="99", close="100"),
        synthetic_bar(1, open_price="101", high="102", low="100", close="101"),
        synthetic_bar(2, open_price="102", high="103", low="101", close="102"),
    ]

    result = run_reference_backtest(
        bars=bars,
        signals=[signal_record(0, "entry"), signal_record(1, "exit")],
        config=fixture_zero_cost_execution_config(),
        run_id="no-same-bar-cost-model",
        instrument_multipliers=SYNTH_INSTRUMENT_MULTIPLIERS,
    )

    assert result.trades[0].entry_bar_index == 1
    assert signal_fill_bar_is_allowed(signal_bar_index=0, fill_bar_index=1)
    assert not signal_fill_bar_is_allowed(signal_bar_index=0, fill_bar_index=0)


def test_same_bar_stop_target_ordering_is_adverse_first() -> None:
    outcome = resolve_same_bar_stop_target(
        direction="long",
        entry_price=Decimal("100"),
        high=Decimal("103"),
        low=Decimal("97"),
        stop_loss_pct=Decimal("0.01"),
        target_profit_pct=Decimal("0.01"),
    )

    assert outcome is not None
    assert outcome.reason == "stop_loss"
    assert outcome.ambiguous is True
