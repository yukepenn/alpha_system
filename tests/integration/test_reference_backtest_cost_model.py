from __future__ import annotations

from decimal import Decimal

from alpha_system.backtest.costs import BpsCost, CompositeCostModel
from alpha_system.backtest.execution_config import ExecutionConfig, fixture_zero_cost_execution_config
from alpha_system.backtest.reference import run_reference_backtest
from tests.fixtures.backtest_reference import signal_record, synthetic_bars


def test_reference_backtest_consumes_configured_cost_model() -> None:
    costly = ExecutionConfig(
        cost_model=CompositeCostModel(models=(BpsCost(Decimal("100")),)),
    )
    zero = fixture_zero_cost_execution_config()
    signals = [signal_record(0, "entry"), signal_record(1, "exit")]

    costly_result = run_reference_backtest(
        bars=synthetic_bars(4),
        signals=signals,
        config=costly,
        run_id="costly-reference",
    )
    zero_result = run_reference_backtest(
        bars=synthetic_bars(4),
        signals=signals,
        config=zero,
        run_id="zero-reference",
    )

    assert costly_result.summary.costs > zero_result.summary.costs
    assert zero_result.summary.costs == Decimal("0")
    assert costly_result.fills[0].price == Decimal("101.01")
    assert costly_result.manifest["parameters"]["cost_model"]["components"][0]["bps"] == "100"
