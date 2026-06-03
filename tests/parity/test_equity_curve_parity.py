from __future__ import annotations

from alpha_system.backtest.parity import run_parity_case, stable_result_digest
from alpha_system.backtest.parity_cases import parity_case
from tests.parity.helpers import assert_accelerated


def test_equity_curve_parity_is_deterministic() -> None:
    result = assert_accelerated("equity_curve")
    repeated = run_parity_case(parity_case("equity_curve"))

    assert stable_result_digest(result.fast_run.result) == stable_result_digest(repeated.fast_run.result)
    assert [point.to_dict() for point in result.fast_run.equity_curve] == [
        point.to_dict() for point in result.reference_result.equity_curve
    ]
