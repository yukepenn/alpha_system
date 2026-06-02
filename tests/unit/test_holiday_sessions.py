from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

from alpha_system.data.calendar import load_calendar_config
from alpha_system.data.quality import OUT_OF_SESSION_FLAG, flag_out_of_session_bars


CALENDAR_PATH = Path("configs/data/calendars/synthetic_exchange.json")


def _bar(start: datetime) -> dict[str, object]:
    end = start + timedelta(minutes=1)
    return {
        "instrument_id": "SYNTH-H",
        "session_id": "placeholder",
        "bar_index": 0,
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


def test_holiday_produces_no_trading_session_and_flags_bar() -> None:
    calendar = load_calendar_config(CALENDAR_PATH)
    zone = ZoneInfo("America/New_York")

    assert calendar.trading_session_for_date(datetime(2026, 1, 6).date()) is None

    report = flag_out_of_session_bars(
        (_bar(datetime(2026, 1, 6, 9, 30, tzinfo=zone)),),
        calendar,
    )

    assert report.count(OUT_OF_SESSION_FLAG) == 1
    assert OUT_OF_SESSION_FLAG in report.rows[0]["quality_flags"]
