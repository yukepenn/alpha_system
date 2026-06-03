from __future__ import annotations

import pytest

from alpha_system.backtest.fast_path import (
    UnsupportedFastPathFeatureError,
    run_fast_path_backtest,
)
from alpha_system.backtest.parity import (
    FastPathGridGateError,
    assert_grid_fast_path_allowed,
    certify_parity,
)
from alpha_system.backtest.parity_cases import parity_case


def test_unsupported_feature_fails_closed_when_fallback_disabled() -> None:
    case = parity_case("partial_exit")

    with pytest.raises(UnsupportedFastPathFeatureError, match="partial_exit"):
        run_fast_path_backtest(
            bars=case.bars,
            signals=case.signals,
            config=case.config,
            management_spec=case.management_spec,
            requested_features=case.features,
            run_id=case.run_id,
            allow_reference_fallback=False,
        )


def test_unknown_feature_fails_closed_without_reference_fallback() -> None:
    case = parity_case("simple_long")

    with pytest.raises(UnsupportedFastPathFeatureError, match="unknown_future_feature"):
        run_fast_path_backtest(
            bars=case.bars,
            signals=case.signals,
            config=case.config,
            requested_features=("unknown_future_feature",),
            run_id=case.run_id,
        )


def test_grid_gate_blocks_reference_fallback_features() -> None:
    certification = certify_parity((parity_case("simple_long"), parity_case("partial_exit")))

    assert_grid_fast_path_allowed(certification, ("simple_long",))
    with pytest.raises(FastPathGridGateError, match="partial_exit"):
        assert_grid_fast_path_allowed(certification, ("partial_exit",))
