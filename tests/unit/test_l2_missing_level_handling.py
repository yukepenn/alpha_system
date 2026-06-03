from __future__ import annotations

from alpha_system.l2.features import (
    compute_microprice,
    compute_top5_imbalance,
    compute_top_of_book_spread,
)
from alpha_system.l2.fixtures import (
    synthetic_l2_snapshot_missing_ask_level_one,
    synthetic_l2_snapshot_missing_inner_levels,
)
from alpha_system.l2.quality import (
    L2_FEATURE_INCOMPLETE_TOP_OF_BOOK,
    L2_FEATURE_MISSING_LEVEL,
    L2_FEATURE_MISSING_SIDE,
)


def test_missing_top_of_book_side_returns_null_and_flags_quality() -> None:
    rows = synthetic_l2_snapshot_missing_ask_level_one()

    spread = compute_top_of_book_spread(rows)
    microprice = compute_microprice(rows)

    assert spread.value is None
    assert L2_FEATURE_MISSING_SIDE in spread.quality_flags
    assert L2_FEATURE_INCOMPLETE_TOP_OF_BOOK in spread.quality_flags
    assert microprice.value is None
    assert L2_FEATURE_MISSING_SIDE in microprice.quality_flags


def test_missing_inner_levels_are_not_fabricated_and_are_flagged() -> None:
    value = compute_top5_imbalance(synthetic_l2_snapshot_missing_inner_levels())

    assert value.value is not None
    assert L2_FEATURE_MISSING_LEVEL in value.quality_flags
