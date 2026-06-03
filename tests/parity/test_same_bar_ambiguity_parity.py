from __future__ import annotations

from tests.parity.helpers import assert_accelerated


def test_same_bar_ambiguity_parity_remains_adverse_first() -> None:
    result = assert_accelerated("same_bar_ambiguity")

    trade = result.fast_run.trades[0]
    assert trade.exit_reason == "stop_loss"
    assert trade.net_pnl < 0
