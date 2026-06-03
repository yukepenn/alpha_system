from __future__ import annotations

from tests.parity.helpers import assert_accelerated


def test_no_trade_parity_matches_reference() -> None:
    result = assert_accelerated("no_trade")

    assert result.reference_result.summary.total_trades == 0
    assert result.fast_run.summary.total_trades == 0
    assert result.fast_run.result.output_paths is None
