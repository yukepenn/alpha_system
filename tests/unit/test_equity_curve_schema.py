from __future__ import annotations

from alpha_system.backtest.equity import EQUITY_CURVE_FIELDS, assert_equity_curve_schema
from alpha_system.backtest.reference import run_reference_backtest
from tests.fixtures.backtest_reference import signal_record, synthetic_bars, zero_cost_config


def test_equity_curve_schema_and_determinism() -> None:
    kwargs = {
        "bars": synthetic_bars(4),
        "signals": [signal_record(0, "entry"), signal_record(1, "exit")],
        "config": zero_cost_config(),
        "run_id": "equity-schema",
    }

    first = run_reference_backtest(**kwargs)
    second = run_reference_backtest(**kwargs)

    payload = first.equity_curve[-1].to_dict()
    assert tuple(payload) == EQUITY_CURVE_FIELDS
    assert_equity_curve_schema(payload)
    assert [point.to_dict() for point in first.equity_curve] == [
        point.to_dict() for point in second.equity_curve
    ]
