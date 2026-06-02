from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from alpha_system.data.validation import validate_bar


def _valid_bar(**overrides: object) -> dict[str, object]:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc)
    end = start + timedelta(minutes=1)
    record: dict[str, object] = {
        "instrument_id": "SYNTH-1",
        "session_id": "2026-01-02_RTH",
        "bar_index": 0,
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


def test_valid_bid_ask_spread_passes() -> None:
    assert validate_bar(_valid_bar()).valid


def test_bid_must_not_exceed_ask() -> None:
    result = validate_bar(
        _valid_bar(bid=Decimal("101"), ask=Decimal("100"), spread=Decimal("1"))
    )

    assert "bid_above_ask" in {issue.code for issue in result.issues}


def test_spread_must_match_ask_minus_bid() -> None:
    result = validate_bar(_valid_bar(spread=Decimal("0.5")))

    assert "spread_mismatch" in {issue.code for issue in result.issues}


def test_spread_must_be_nonnegative() -> None:
    result = validate_bar(_valid_bar(spread=Decimal("-0.1")))

    assert "negative_spread" in {issue.code for issue in result.issues}
