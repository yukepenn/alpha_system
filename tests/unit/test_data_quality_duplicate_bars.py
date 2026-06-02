from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from alpha_system.data.calendar import TradingCalendar
from alpha_system.data.quality import DUPLICATE_BAR_FLAG, flag_duplicate_bars
from alpha_system.data.sessionize import sessionize_bars


def _calendar() -> TradingCalendar:
    return TradingCalendar.from_config(
        {
            "calendar_id": "SYNTH_DUP",
            "timezone": "America/New_York",
            "regular_session": {"open": "09:30", "close": "09:32"},
            "sessions": [{"trading_date": "2026-01-02"}],
        }
    )


def _bar(start: datetime) -> dict[str, object]:
    end = start + timedelta(minutes=1)
    return {
        "instrument_id": "SYNTH-D",
        "session_id": "",
        "bar_index": -1,
        "bar_start_ts": start,
        "bar_end_ts": end,
        "event_ts": end,
        "available_ts": end,
        "open": Decimal("1"),
        "high": Decimal("1"),
        "low": Decimal("1"),
        "close": Decimal("1"),
        "volume": Decimal("1"),
        "vwap": Decimal("1"),
        "trade_count": 1,
        "bid": None,
        "ask": None,
        "spread": None,
        "source_version": "synthetic:v1",
        "data_version": "synthetic:v1",
        "quality_flags": (),
    }


def test_duplicate_keys_are_flagged_without_merge() -> None:
    calendar = _calendar()
    zone = ZoneInfo("America/New_York")
    start = datetime(2026, 1, 2, 9, 30, tzinfo=zone)
    sessionized = sessionize_bars((_bar(start), _bar(start)), calendar)

    report = flag_duplicate_bars(sessionized)

    assert len(report.rows) == 2
    assert all(DUPLICATE_BAR_FLAG in row["quality_flags"] for row in report.rows)
    assert {issue.details["key_name"] for issue in report.issues} == {
        "instrument_session_bar_index",
        "instrument_session_bar_start_ts",
    }
