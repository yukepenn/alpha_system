from __future__ import annotations

from tests.parity.helpers import assert_reference_fallback


def test_slippage_parity_routes_to_reference_fallback() -> None:
    result = assert_reference_fallback("slippage")

    parameters = result.fast_run.result.manifest["parameters"]
    assert parameters["slippage_model"]["components"][0]["bps"] == "25"
    assert "slippage" in result.fast_run.unsupported_features
