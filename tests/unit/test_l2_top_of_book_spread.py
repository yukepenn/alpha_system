from __future__ import annotations

import pytest

from alpha_system.l2.features import compute_top_of_book_spread
from alpha_system.l2.fixtures import synthetic_l2_snapshot_rows
from alpha_system.l2.quality import L2_FEATURE_FIXTURE_ONLY


def test_top_of_book_spread_uses_synthetic_level_one_bid_ask() -> None:
    value = compute_top_of_book_spread(synthetic_l2_snapshot_rows())

    assert value.value == pytest.approx(0.05)
    assert value.normalized_value is None
    assert L2_FEATURE_FIXTURE_ONLY in value.quality_flags
