from __future__ import annotations

from tests.parity.helpers import assert_accelerated


def test_fixed_stop_parity_matches_reference() -> None:
    result = assert_accelerated("fixed_stop")

    assert result.fast_run.trades[0].exit_reason == "stop_loss"


def test_target_parity_matches_reference() -> None:
    result = assert_accelerated("target")

    assert result.fast_run.trades[0].exit_reason == "take_profit"
