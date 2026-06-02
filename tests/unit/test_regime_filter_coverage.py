from __future__ import annotations

import pytest

from alpha_system.research.regimes import false_rejection_rate, regime_filter_coverage


def test_regime_filter_coverage_and_false_rejection() -> None:
    rows = [
        {"regime_filter": True, "forward_return": 0.02},
        {"regime_filter": False, "forward_return": 0.03},
        {"regime_filter": False, "forward_return": -0.01},
        {"regime_filter": True, "forward_return": -0.02},
    ]

    coverage = regime_filter_coverage(rows)
    rejection = false_rejection_rate(rows)

    assert coverage["coverage"] == pytest.approx(0.5)
    assert rejection["false_rejection_rate"] == pytest.approx(0.5)
