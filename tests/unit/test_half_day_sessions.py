from __future__ import annotations

from datetime import date
from pathlib import Path

from alpha_system.data.calendar import load_calendar_config
from alpha_system.data.sessions import expected_bar_count


CALENDAR_PATH = Path("configs/data/calendars/synthetic_exchange.json")


def test_half_day_uses_early_close_and_short_expected_count() -> None:
    calendar = load_calendar_config(CALENDAR_PATH)
    regular = calendar.session_for_date(date(2026, 1, 2))
    half_day = calendar.session_for_date(date(2026, 1, 5))

    assert regular.is_half_day is False
    assert half_day.is_half_day is True
    assert half_day.close_ts.hour == 9
    assert half_day.close_ts.minute == 32
    assert expected_bar_count(regular) == 5
    assert expected_bar_count(half_day) == 2
