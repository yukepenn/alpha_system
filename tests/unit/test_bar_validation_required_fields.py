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


def test_valid_bar_has_no_required_field_issues() -> None:
    assert validate_bar(_valid_bar()).valid


def test_missing_required_field_is_reported() -> None:
    record = _valid_bar()
    del record["available_ts"]

    result = validate_bar(record)

    assert not result.valid
    assert "missing_required_field" in {issue.code for issue in result.issues}
    assert "available_ts" in {issue.field for issue in result.issues}


def test_blank_versions_and_keys_are_rejected() -> None:
    result = validate_bar(
        _valid_bar(
            instrument_id="",
            session_id=" ",
            source_version="",
            data_version=" ",
        )
    )

    codes = {issue.code for issue in result.issues}
    assert "missing_bar_key" in codes
    assert "missing_version" in codes
