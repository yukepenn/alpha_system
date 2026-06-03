from __future__ import annotations

import pytest

from alpha_system.l2.features import compute_microprice
from alpha_system.l2.fixtures import synthetic_l2_snapshot_rows


def test_microprice_uses_top_of_book_prices_and_sizes() -> None:
    value = compute_microprice(synthetic_l2_snapshot_rows())

    assert value.factor_id == "l2_microprice"
    assert value.value == pytest.approx(100.02)
