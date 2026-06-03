from __future__ import annotations

from tests.parity.helpers import assert_reference_fallback


def test_cooldown_parity_routes_to_reference_fallback() -> None:
    result = assert_reference_fallback("cooldown")

    assert "cooldown" in result.fast_run.unsupported_features
    assert result.fast_run.summary.open_positions == 0
