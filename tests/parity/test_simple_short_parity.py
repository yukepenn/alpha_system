from __future__ import annotations

from tests.parity.helpers import assert_accelerated


def test_simple_short_parity_matches_reference() -> None:
    result = assert_accelerated("simple_short")

    trade = result.fast_run.trades[0]
    assert trade.direction == "short"
    assert trade.entry_bar_index == 1
    assert trade.exit_bar_index == 3
