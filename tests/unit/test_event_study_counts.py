from __future__ import annotations

import pytest

from alpha_system.research.events import event_study, sample_size


def test_event_study_counts_events_and_baseline() -> None:
    rows = [
        {"factor_value": 1, "forward_return": 0.02},
        {"factor_value": 2, "forward_return": 0.04},
        {"factor_value": -1, "forward_return": -0.01},
        {"factor_value": 0, "forward_return": 0.00},
    ]

    result = event_study(rows)
    counts = sample_size(rows)

    assert counts == {"total": 4, "events": 2, "non_events": 2}
    assert result["event_count"] == 2
    assert result["event_mean_return"] == pytest.approx(0.03)
    assert result["non_event_mean_return"] == pytest.approx(-0.005)
