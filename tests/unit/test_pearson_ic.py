from __future__ import annotations

import pytest

from alpha_system.research.ic import pearson_ic


def test_pearson_ic_perfect_positive() -> None:
    result = pearson_ic([1, 2, 3, 4], [2, 4, 6, 8])

    assert result["n"] == 4
    assert result["ic"] == pytest.approx(1.0)


def test_pearson_ic_rejects_constant_or_missing_pairs() -> None:
    constant = pearson_ic([1, 1, 1], [1, 2, 3])
    sparse = pearson_ic([None, "bad"], [1, 2])

    assert constant["ic"] is None
    assert sparse == {"ic": None, "n": 0}
