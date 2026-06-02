from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

from alpha_system.data.calendar import load_calendar_config
from alpha_system.data.quality import MISSING_BAR_FLAG, flag_missing_bars
from alpha_system.data.sessionize import sessionize_bars


CALENDAR_PATH = Path("configs/data/calendars/synthetic_exchange.json")


def _bar(start: datetime) -> dict[str, object]:
    end = start + timedelta(minutes=1)
    return {
        "instrument_id": "SYNTH-NL",
        "session_id": "",
        "bar_index": -1,
        "bar_start_ts": start,
        "bar_end_ts": end,
        "event_ts": end,
        "available_ts": end + timedelta(seconds=5),
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


def test_session_metadata_availability_preserves_bar_ordering() -> None:
    calendar = load_calendar_config(CALENDAR_PATH)
    zone = ZoneInfo("America/New_York")
    latency = timedelta(seconds=5)
    raw = _bar(datetime(2026, 1, 2, 9, 30, tzinfo=zone))
    row = sessionize_bars((raw,), calendar, available_latency=latency)[0]

    assert row["available_ts"] == raw["available_ts"]
    assert row["available_ts"] >= row["bar_end_ts"]
    assert row["session_metadata_available_ts"] >= row["bar_end_ts"] + latency
    assert row["session_metadata_available_ts"] >= row["available_ts"]
    assert row["session_close_available_ts"] >= row["session_close_ts"] + latency
    assert row["session_close_available_ts"] > row["bar_end_ts"]


def test_missing_bar_summary_is_available_only_after_session_close() -> None:
    calendar = load_calendar_config(CALENDAR_PATH)
    zone = ZoneInfo("America/New_York")
    latency = timedelta(seconds=5)
    sessionized = sessionize_bars(
        (
            _bar(datetime(2026, 1, 2, 9, 30, tzinfo=zone)),
            _bar(datetime(2026, 1, 2, 9, 32, tzinfo=zone)),
        ),
        calendar,
        available_latency=latency,
    )

    report = flag_missing_bars(sessionized, calendar, latency=latency)

    assert report.count(MISSING_BAR_FLAG) == 3
    assert report.issues[0].available_ts >= sessionized[0]["session_close_ts"] + latency
