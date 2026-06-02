from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from alpha_system.data.bar_schema import (
    REQUIRED_BAR_FIELDS,
    canonical_bar_columns,
    contract_alignment_errors,
    field_type_errors,
)


def _valid_bar() -> dict[str, object]:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc)
    end = start + timedelta(minutes=1)
    return {
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


def test_schema_aligns_with_one_minute_bar_contract() -> None:
    assert contract_alignment_errors() == ()
    assert canonical_bar_columns() == REQUIRED_BAR_FIELDS


def test_field_type_errors_accept_normalized_record() -> None:
    assert field_type_errors(_valid_bar()) == ()


def test_field_type_errors_reject_missing_and_wrong_types() -> None:
    record = _valid_bar()
    del record["available_ts"]
    record["bar_index"] = True
    record["quality_flags"] = ["synthetic"]

    errors = field_type_errors(record)

    assert "available_ts is missing" in errors
    assert "bar_index must be int" in errors
    assert "quality_flags must be tuple[str, ...]" in errors
