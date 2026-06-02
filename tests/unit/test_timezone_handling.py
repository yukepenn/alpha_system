from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from alpha_system.data.calendar import TradingCalendar
from alpha_system.data.sessionize import sessionize_bars


def _calendar() -> TradingCalendar:
    return TradingCalendar.from_config(
        {
            "calendar_id": "SYNTH_CENTRAL",
            "timezone": "America/Chicago",
            "regular_session": {"open": "08:30", "close": "08:32"},
            "sessions": [{"trading_date": "2026-01-02"}],
        }
    )


def _bar(start: datetime) -> dict[str, object]:
    end = start + timedelta(minutes=1)
    return {
        "instrument_id": "SYNTH-C",
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


def test_session_lookup_uses_exchange_timezone() -> None:
    calendar = _calendar()
    session = calendar.session_for_date(datetime(2026, 1, 2).date())

    assert session.open_ts.tzinfo is not None
    assert session.timezone == "America/Chicago"
    assert session.open_ts.astimezone(timezone.utc) == datetime(
        2026,
        1,
        2,
        14,
        30,
        tzinfo=timezone.utc,
    )


def test_utc_bar_is_assigned_by_exchange_local_time() -> None:
    calendar = _calendar()
    rows = sessionize_bars(
        (_bar(datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc)),),
        calendar,
    )

    assert rows[0]["session_id"] == "SYNTH_CENTRAL:2026-01-02:regular"
    assert rows[0]["bar_index"] == 0
    assert rows[0]["timezone"] == "America/Chicago"
