from __future__ import annotations

import pytest

from alpha_system.l2.features import (
    compute_depth_by_side,
    compute_l2_imbalance,
    compute_order_count_by_level,
)
from alpha_system.l2.fixtures import synthetic_l2_snapshot_rows


def test_depth_by_side_sums_displayed_synthetic_depth() -> None:
    bid_depth = compute_depth_by_side(
        synthetic_l2_snapshot_rows(),
        side="bid",
        depth_levels=3,
    )
    ask_depth = compute_depth_by_side(
        synthetic_l2_snapshot_rows(),
        side="ask",
        depth_levels=3,
    )

    assert bid_depth.value == pytest.approx(45.0)
    assert ask_depth.value == pytest.approx(75.0)


def test_depth_imbalance_can_be_parameterized_by_depth() -> None:
    value = compute_l2_imbalance(synthetic_l2_snapshot_rows(), depth_levels=3)

    assert value.value == pytest.approx(-0.25)


def test_order_count_by_level_uses_synthetic_displayed_count() -> None:
    value = compute_order_count_by_level(
        synthetic_l2_snapshot_rows(),
        side="ask",
        level=1,
    )

    assert value.factor_id == "l2_order_count_by_level"
    assert value.value == pytest.approx(3.0)
