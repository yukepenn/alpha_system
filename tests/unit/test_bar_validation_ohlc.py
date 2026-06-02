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


def test_ohlc_high_must_not_be_below_low() -> None:
    result = validate_bar(_valid_bar(high=Decimal("98"), low=Decimal("99")))

    assert "ohlc_high_low" in {issue.code for issue in result.issues}


def test_open_and_close_must_be_inside_high_low_range() -> None:
    result = validate_bar(
        _valid_bar(open=Decimal("102"), close=Decimal("98"))
    )

    codes = {issue.code for issue in result.issues}
    assert "ohlc_open_range" in codes
    assert "ohlc_close_range" in codes


def test_volume_and_trade_count_must_be_nonnegative() -> None:
    result = validate_bar(
        _valid_bar(volume=Decimal("-1"), trade_count=-1)
    )

    codes = {issue.code for issue in result.issues}
    assert "negative_volume" in codes
    assert "negative_trade_count" in codes
