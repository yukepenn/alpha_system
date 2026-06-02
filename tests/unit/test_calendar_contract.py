from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from alpha_system.core.enums import SessionType
from alpha_system.data.calendar import load_calendar_config


CALENDAR_PATH = Path("configs/data/calendars/synthetic_exchange.json")


def test_calendar_config_loads_and_session_fields_are_typed() -> None:
    calendar = load_calendar_config(CALENDAR_PATH)
    session = calendar.session_for_date(date(2026, 1, 2))

    assert session.calendar_id == "SYNTH_EXCHANGE"
    assert isinstance(session.trading_date, date)
    assert isinstance(session.session_id, str)
    assert isinstance(session.open_ts, datetime)
    assert isinstance(session.close_ts, datetime)
    assert isinstance(session.is_holiday, bool)
    assert isinstance(session.is_half_day, bool)
    assert session.session_type is SessionType.REGULAR
    assert session.timezone == "America/New_York"
    assert isinstance(session.quality_flags, tuple)
    assert all(isinstance(flag, str) for flag in session.quality_flags)


def test_holiday_session_contract_record_is_typed() -> None:
    calendar = load_calendar_config(CALENDAR_PATH)
    holiday = calendar.session_for_date(date(2026, 1, 6))

    assert holiday.is_holiday is True
    assert holiday.open_ts == holiday.close_ts
    assert "holiday" in holiday.quality_flags
    assert calendar.trading_session_for_date(date(2026, 1, 6)) is None
