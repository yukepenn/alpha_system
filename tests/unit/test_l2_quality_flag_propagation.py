from __future__ import annotations

from alpha_system.l2.features import compute_top_of_book_spread
from alpha_system.l2.fixtures import synthetic_l2_snapshot_with_quality_flag


def test_l2_input_quality_flags_propagate_to_feature_value() -> None:
    value = compute_top_of_book_spread(synthetic_l2_snapshot_with_quality_flag())

    assert "stale_quote" in value.quality_flags
