from __future__ import annotations

import pytest

from alpha_system.research.ic import rank_ic


def test_rank_ic_handles_inverse_ordering() -> None:
    result = rank_ic([1, 2, 3, 4], [4, 3, 2, 1])

    assert result["n"] == 4
    assert result["ic"] == pytest.approx(-1.0)


def test_rank_ic_uses_average_ranks_for_ties() -> None:
    result = rank_ic([1, 1, 2, 3], [5, 5, 6, 7])

    assert result["ic"] == pytest.approx(1.0)
