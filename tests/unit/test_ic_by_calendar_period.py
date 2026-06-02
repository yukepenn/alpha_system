from __future__ import annotations

import pytest

from alpha_system.research.ic import ic_by_calendar_period


def test_ic_by_day_week_month() -> None:
    observations = [
        {"factor_value": 1, "label_value": 1, "event_ts": "2026-01-02T14:31:00Z"},
        {"factor_value": 2, "label_value": 2, "event_ts": "2026-01-02T14:32:00Z"},
        {"factor_value": 1, "label_value": 2, "event_ts": "2026-02-03T14:31:00Z"},
        {"factor_value": 2, "label_value": 1, "event_ts": "2026-02-03T14:32:00Z"},
    ]

    by_day = ic_by_calendar_period(observations, period="day")
    by_week = ic_by_calendar_period(observations, period="week")
    by_month = ic_by_calendar_period(observations, period="month")

    assert by_day["2026-01-02"]["ic"] == pytest.approx(1.0)
    assert by_day["2026-02-03"]["ic"] == pytest.approx(-1.0)
    assert "2026-W01" in by_week
    assert set(by_month) == {"2026-01", "2026-02"}
