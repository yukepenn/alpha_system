from __future__ import annotations

import pytest

from alpha_system.research.correlation import correlation_to_existing_factor
from alpha_system.research.stability import (
    monthly_stability,
    regime_stability,
    session_segment_stability,
    time_of_day_stability,
)


def test_stability_helpers_group_intraday_records() -> None:
    rows = [
        {
            "factor_value": 1,
            "label_value": 0.01,
            "event_ts": "2026-01-02T14:31:00Z",
            "bar_index": 0,
            "regime": "open",
        },
        {
            "factor_value": 2,
            "label_value": 0.02,
            "event_ts": "2026-01-02T14:32:00Z",
            "bar_index": 1,
            "regime": "open",
        },
        {
            "factor_value": 3,
            "label_value": -0.01,
            "event_ts": "2026-02-02T14:31:00Z",
            "bar_index": 2,
            "regime": "late",
        },
    ]

    assert time_of_day_stability(rows)["14:31"]["n"] == 2
    assert session_segment_stability(rows, segments=2)["segment_1"]["n"] == 2
    assert set(monthly_stability(rows)) == {"2026-01", "2026-02"}
    assert regime_stability(rows)["open"]["n"] == 2


def test_correlation_to_existing_factor_reports_rank_and_pearson() -> None:
    result = correlation_to_existing_factor([1, 2, 3], [3, 2, 1])

    assert result["n"] == 3
    assert result["pearson"] == pytest.approx(-1.0)
    assert result["rank"] == pytest.approx(-1.0)
