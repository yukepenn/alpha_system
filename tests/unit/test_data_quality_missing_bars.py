from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from alpha_system.data.calendar import TradingCalendar
from alpha_system.data.quality import MISSING_BAR_FLAG, flag_missing_bars
from alpha_system.data.sessionize import sessionize_bars


def _calendar() -> TradingCalendar:
    return TradingCalendar.from_config(
        {
            "calendar_id": "SYNTH_MISSING",
            "timezone": "America/New_York",
            "regular_session": {"open": "09:30", "close": "09:33"},
            "sessions": [{"trading_date": "2026-01-02"}],
        }
    )


def _bar(start: datetime) -> dict[str, object]:
    end = start + timedelta(minutes=1)
    return {
        "instrument_id": "SYNTH-M",
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


def test_missing_expected_grid_bar_surfaces_warning_without_fill() -> None:
    calendar = _calendar()
    zone = ZoneInfo("America/New_York")
    sessionized = sessionize_bars(
        (
            _bar(datetime(2026, 1, 2, 9, 30, tzinfo=zone)),
            _bar(datetime(2026, 1, 2, 9, 32, tzinfo=zone)),
        ),
        calendar,
    )

    report = flag_missing_bars(sessionized, calendar)

    assert len(report.rows) == 2
    assert report.count(MISSING_BAR_FLAG) == 1
    assert report.issues[0].bar_start_ts == datetime(
        2026,
        1,
        2,
        9,
        31,
        tzinfo=zone,
    )
    assert "missing_bar_start_ts" in report.issues[0].details
