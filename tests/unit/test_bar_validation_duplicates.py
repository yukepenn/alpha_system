from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from alpha_system.data.validation import validate_bars


def _valid_bar(bar_index: int = 0, **overrides: object) -> dict[str, object]:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc) + timedelta(
        minutes=bar_index
    )
    end = start + timedelta(minutes=1)
    record: dict[str, object] = {
        "instrument_id": "SYNTH-1",
        "session_id": "2026-01-02_RTH",
        "bar_index": bar_index,
        "bar_start_ts": start,
        "bar_end_ts": end,
        "event_ts": end,
        "available_ts": end,
        "open": Decimal("100"),
        "high": Decimal("101"),
        "low": Decimal("99"),
        "close": Decimal("100.5"),
        "volume": Decimal("1000"),
        "vwap": Decimal("100.25"),
        "trade_count": 10,
        "bid": Decimal("100.4"),
        "ask": Decimal("100.6"),
        "spread": Decimal("0.2"),
        "source_version": "src:v1",
        "data_version": "data:v1",
        "quality_flags": (),
    }
    record.update(overrides)
    return record


def test_duplicate_instrument_session_bar_index_is_rejected() -> None:
    result = validate_bars([_valid_bar(0), _valid_bar(0)])

    assert "duplicate_bar_index_key" in {issue.code for issue in result.issues}


def test_duplicate_instrument_session_bar_start_is_rejected() -> None:
    first = _valid_bar(0)
    second = _valid_bar(1, bar_start_ts=first["bar_start_ts"])

    result = validate_bars([first, second])

    assert "duplicate_bar_timestamp_key" in {
        issue.code for issue in result.issues
    }
