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
        "instrument_id": "SYNTH-O",
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


def test_pre_open_post_close_and_holiday_bars_are_flagged() -> None:
    calendar = load_calendar_config(CALENDAR_PATH)
    zone = ZoneInfo("America/New_York")
    report = flag_out_of_session_bars(
        (
            _bar(datetime(2026, 1, 2, 9, 29, tzinfo=zone)),
            _bar(datetime(2026, 1, 2, 9, 35, tzinfo=zone)),
            _bar(datetime(2026, 1, 6, 9, 30, tzinfo=zone)),
        ),
        calendar,
    )

    assert len(report.rows) == 3
    assert report.count(OUT_OF_SESSION_FLAG) == 3
    assert all(OUT_OF_SESSION_FLAG in row["quality_flags"] for row in report.rows)
