from __future__ import annotations

import pytest

from alpha_system.research.regimes import regime_filter_uplift


def test_regime_filter_uplift_compares_retained_to_rejected() -> None:
    rows = [
        {"regime_filter": True, "forward_return": 0.03},
        {"regime_filter": True, "forward_return": 0.01},
        {"regime_filter": False, "forward_return": -0.01},
        {"regime_filter": False, "forward_return": -0.03},
    ]

    result = regime_filter_uplift(rows)

    assert result["with_filter_mean"] == pytest.approx(0.02)
    assert result["without_filter_mean"] == pytest.approx(-0.02)
    assert result["uplift"] == pytest.approx(0.04)
