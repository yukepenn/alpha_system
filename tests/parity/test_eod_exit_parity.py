from __future__ import annotations

from tests.parity.helpers import assert_accelerated


def test_eod_exit_parity_matches_reference() -> None:
    result = assert_accelerated("eod_exit")

    assert result.fast_run.trades[0].exit_reason == "eod_flat"
    assert result.fast_run.summary.open_positions == 0
