from __future__ import annotations

import pytest

from alpha_system.l2.features import compute_top5_imbalance
from alpha_system.l2.fixtures import synthetic_l2_snapshot_rows


def test_top5_imbalance_aggregates_five_synthetic_levels() -> None:
    value = compute_top5_imbalance(synthetic_l2_snapshot_rows())

    assert value.factor_id == "l2_top5_imbalance"
    assert value.value == pytest.approx(-0.2)
