from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from alpha_system.data.validation import BarValidationConfig, validate_bar


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
        "available_ts": end + timedelta(seconds=5),
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


def test_available_ts_must_respect_configured_latency() -> None:
    config = BarValidationConfig(available_latency=timedelta(seconds=5))
    start = datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc)
    end = start + timedelta(minutes=1)

    valid = validate_bar(
        _valid_bar(available_ts=end + timedelta(seconds=5)),
        config=config,
    )
    invalid = validate_bar(
        _valid_bar(available_ts=end + timedelta(seconds=4)),
        config=config,
    )

    assert valid.valid
    assert "available_before_bar_latency" in {
        issue.code for issue in invalid.issues
    }


def test_bar_start_must_precede_bar_end() -> None:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc)

    result = validate_bar(
        _valid_bar(
            bar_start_ts=start,
            bar_end_ts=start,
            event_ts=start,
            available_ts=start + timedelta(seconds=5),
        )
    )

    assert "bar_interval_order" in {issue.code for issue in result.issues}


def test_event_ts_must_remain_inside_bar_interval() -> None:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc)
    end = start + timedelta(minutes=1)

    result = validate_bar(
        _valid_bar(
            bar_start_ts=start,
            bar_end_ts=end,
            event_ts=end + timedelta(seconds=1),
            available_ts=end + timedelta(seconds=5),
        )
    )

    assert "event_ts_order" in {issue.code for issue in result.issues}
