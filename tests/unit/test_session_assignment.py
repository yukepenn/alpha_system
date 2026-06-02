from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

from alpha_system.data.calendar import load_calendar_config
from alpha_system.data.quality import OUT_OF_SESSION_FLAG
from alpha_system.data.sessionize import sessionize_bars


CALENDAR_PATH = Path("configs/data/calendars/synthetic_exchange.json")


def _bar(start: datetime) -> dict[str, object]:
    end = start + timedelta(minutes=1)
    return {
        "instrument_id": "SYNTH-1",
        "session_id": "",
        "bar_index": -1,
        "bar_start_ts": start,
        "bar_end_ts": end,
        "event_ts": end,
        "available_ts": end + timedelta(seconds=5),
        "open": Decimal("10"),
        "high": Decimal("11"),
        "low": Decimal("9"),
        "close": Decimal("10.5"),
        "volume": Decimal("100"),
        "vwap": Decimal("10.25"),
        "trade_count": 1,
        "bid": Decimal("10.4"),
        "ask": Decimal("10.6"),
        "spread": Decimal("0.2"),
        "source_version": "synthetic:v1",
        "data_version": "synthetic:v1",
        "quality_flags": (),
    }


def test_bars_are_assigned_to_deterministic_session_id() -> None:
    calendar = load_calendar_config(CALENDAR_PATH)
    zone = ZoneInfo("America/New_York")
    rows = sessionize_bars(
        (
            _bar(datetime(2026, 1, 2, 9, 30, tzinfo=zone)),
            _bar(datetime(2026, 1, 2, 9, 31, tzinfo=zone)),
        ),
        calendar,
    )

    assert rows[0]["session_id"] == "SYNTH_EXCHANGE:2026-01-02:regular"
    assert rows[1]["session_id"] == "SYNTH_EXCHANGE:2026-01-02:regular"
    assert rows[0]["bar_index"] == 0
    assert rows[1]["bar_index"] == 1


def test_outside_session_bars_are_not_silently_assigned() -> None:
    calendar = load_calendar_config(CALENDAR_PATH)
    zone = ZoneInfo("America/New_York")
    rows = sessionize_bars(
        (_bar(datetime(2026, 1, 2, 9, 29, tzinfo=zone)),),
        calendar,
    )

    assert rows[0]["session_id"] == ""
    assert rows[0]["bar_index"] == -1
    assert OUT_OF_SESSION_FLAG in rows[0]["quality_flags"]
