from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

from alpha_system.data.calendar import load_calendar_config
from alpha_system.data.sessionize import sessionize_bars


CALENDAR_PATH = Path("configs/data/calendars/synthetic_exchange.json")


def _bar(start: datetime) -> dict[str, object]:
    end = start + timedelta(minutes=1)
    return {
        "instrument_id": "SYNTH-R",
        "session_id": "",
        "bar_index": -1,
        "bar_start_ts": start,
        "bar_end_ts": end,
        "event_ts": end,
        "available_ts": end + timedelta(seconds=1),
        "open": Decimal("1"),
        "high": Decimal("2"),
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


def test_bar_index_resets_at_each_session_open() -> None:
    calendar = load_calendar_config(CALENDAR_PATH)
    zone = ZoneInfo("America/New_York")
    rows = sessionize_bars(
        (
            _bar(datetime(2026, 1, 2, 9, 30, tzinfo=zone)),
            _bar(datetime(2026, 1, 2, 9, 31, tzinfo=zone)),
            _bar(datetime(2026, 1, 5, 9, 30, tzinfo=zone)),
        ),
        calendar,
    )

    assert [row["bar_index"] for row in rows] == [0, 1, 0]
    assert rows[0]["session_id"] != rows[2]["session_id"]
