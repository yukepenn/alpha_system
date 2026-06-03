from __future__ import annotations

import pytest

from alpha_system.l2.features import compute_top1_imbalance
from alpha_system.l2.fixtures import synthetic_l2_snapshot_rows


def test_top1_imbalance_uses_only_level_one_displayed_size() -> None:
    value = compute_top1_imbalance(synthetic_l2_snapshot_rows())

    assert value.factor_id == "l2_top1_imbalance"
    assert value.value == pytest.approx(-0.2)
