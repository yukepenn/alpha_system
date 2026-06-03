from __future__ import annotations

from alpha_system.backtest.parity import run_parity_case, stable_result_digest
from alpha_system.backtest.parity_cases import parity_case
from tests.parity.helpers import assert_accelerated


def test_trade_summary_parity_is_deterministic() -> None:
    result = assert_accelerated("trade_summary")
    repeated = run_parity_case(parity_case("trade_summary"))

    assert stable_result_digest(result.fast_run.result) == stable_result_digest(repeated.fast_run.result)
    assert result.fast_run.summary.to_dict() == result.reference_result.summary.to_dict()
