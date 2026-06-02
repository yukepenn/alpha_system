from __future__ import annotations

import pytest

from alpha_system.research.ic import ic_decay


def test_ic_decay_orders_horizons_and_reports_slope() -> None:
    observations = [
        {"factor_value": 1, "label_value": 1, "horizon_seconds": 60},
        {"factor_value": 2, "label_value": 2, "horizon_seconds": 60},
        {"factor_value": 1, "label_value": 2, "horizon_seconds": 300},
        {"factor_value": 2, "label_value": 1, "horizon_seconds": 300},
    ]

    result = ic_decay(observations)

    assert result["by_horizon"]["60"]["pearson_ic"] == pytest.approx(1.0)
    assert result["by_horizon"]["300"]["pearson_ic"] == pytest.approx(-1.0)
    assert result["decay_slope_per_second"] == pytest.approx(-2 / 240)
