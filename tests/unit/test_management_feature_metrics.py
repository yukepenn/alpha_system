from __future__ import annotations

import pytest

from alpha_system.research.management_features import management_feature_summary


def test_management_feature_metrics_are_diagnostic_statistics() -> None:
    rows = [
        {
            "target_before_stop": True,
            "stop_before_target": False,
            "time_to_target": 2,
            "time_to_stop": None,
            "mfe": 0.05,
            "forward_return": 0.02,
        },
        {
            "target_before_stop": False,
            "stop_before_target": True,
            "time_to_target": None,
            "time_to_stop": 1,
            "mfe": 0.01,
            "forward_return": -0.02,
        },
    ]

    summary = management_feature_summary(rows)

    assert summary["target_before_stop"]["probability"] == pytest.approx(0.5)
    assert summary["time_to_target"]["mean_bars"] == pytest.approx(2)
    assert summary["time_to_stop"]["mean_bars"] == pytest.approx(1)
    assert summary["breakeven_usefulness"]["usefulness_rate"] == pytest.approx(1.0)
    assert summary["trailing_stop_usefulness"]["usefulness_rate"] == pytest.approx(1.0)
