from __future__ import annotations

from tests.parity.helpers import assert_accelerated


def test_simple_long_parity_matches_reference() -> None:
    result = assert_accelerated("simple_long")

    trade = result.fast_run.trades[0]
    assert trade.direction == "long"
    assert trade.entry_bar_index == 1
    assert trade.exit_bar_index == 3
