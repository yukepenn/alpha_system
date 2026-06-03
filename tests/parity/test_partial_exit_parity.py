from __future__ import annotations

from tests.parity.helpers import assert_reference_fallback


def test_partial_exit_parity_routes_to_reference_fallback() -> None:
    result = assert_reference_fallback("partial_exit")

    assert result.fast_run.summary.total_trades == 2
    assert result.fast_run.trades[0].exit_reason == "partial_take_profit:half_at_1r"
    assert "partial_exit" in result.fast_run.unsupported_features
