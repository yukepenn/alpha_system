from __future__ import annotations

import pytest

from alpha_system.research.buckets import tail_expectancy


def test_tail_expectancy_uses_high_minus_low_tail() -> None:
    result = tail_expectancy(
        [
            {"bucket": 1, "n": 3, "mean_return": -0.01},
            {"bucket": 2, "n": 3, "mean_return": 0.00},
            {"bucket": 3, "n": 3, "mean_return": 0.03},
        ]
    )

    assert result["tail_expectancy"] == pytest.approx(0.04)
    assert result["low_tail_n"] == 3
    assert result["high_tail_n"] == 3
