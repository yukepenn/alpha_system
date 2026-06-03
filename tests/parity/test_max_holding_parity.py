from __future__ import annotations

from tests.parity.helpers import assert_reference_fallback


def test_max_holding_parity_routes_to_reference_fallback() -> None:
    result = assert_reference_fallback("max_holding_bars")

    assert result.fast_run.trades[0].exit_reason == "max_holding_bars"
    assert "max_holding_bars" in result.fast_run.unsupported_features
