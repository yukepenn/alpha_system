from __future__ import annotations

import pytest

from alpha_system.research.events import post_event_mfe_mae, target_before_stop_probability


def test_event_target_before_stop_probability_and_path_metrics() -> None:
    rows = [
        {"event_trigger": True, "target_before_stop": True, "mfe": 0.04, "mae": -0.01},
        {"event_trigger": True, "target_before_stop": False, "mfe": 0.01, "mae": -0.03},
        {"event_trigger": False, "target_before_stop": True, "mfe": 0.10, "mae": -0.01},
    ]

    probability = target_before_stop_probability(rows)
    path = post_event_mfe_mae(rows)

    assert probability["target_before_stop_probability"] == pytest.approx(0.5)
    assert path["mean_mfe"] == pytest.approx(0.025)
    assert path["mean_mae"] == pytest.approx(-0.02)
