from __future__ import annotations

import pytest

from alpha_system.research.buckets import u_shape_profile


def test_u_shape_profile_compares_edges_to_center() -> None:
    result = u_shape_profile(
        [
            {"bucket": 1, "mean_return": 0.04},
            {"bucket": 2, "mean_return": -0.01},
            {"bucket": 3, "mean_return": 0.05},
        ]
    )

    assert result["is_u_shaped"] is True
    assert result["u_shape_score"] == pytest.approx(0.055)
