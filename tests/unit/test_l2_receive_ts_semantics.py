from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from alpha_system.core.enums import BookSide
from alpha_system.l2.timestamps import (
    L2_TIMESTAMP_FIELDS,
    SESSION_ASSIGNMENT_TIMESTAMP_FIELD,
    session_assignment_timestamp,
)
from alpha_system.l2.validation import validate_l2_snapshot


def _snapshot(**overrides: object) -> dict[str, object]:
    event_ts = datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc)
    record: dict[str, object] = {
        "instrument_id": "SYNTH-L2-1",
        "session_id": "2026-01-02_RTH",
        "event_ts": event_ts,
        "receive_ts": event_ts + timedelta(milliseconds=5),
        "available_ts": event_ts + timedelta(milliseconds=10),
        "book_level": 1,
        "side": BookSide.BID,
        "price": Decimal("100.00"),
        "size": Decimal("10"),
        "order_count": None,
        "data_version": "data:l2:synthetic:v1",
        "quality_flags": (),
    }
    record.update(overrides)
    return record


def test_receive_ts_must_not_precede_event_ts() -> None:
    event_ts = datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc)
    result = validate_l2_snapshot(
        _snapshot(
            event_ts=event_ts,
            receive_ts=event_ts - timedelta(milliseconds=1),
            available_ts=event_ts + timedelta(milliseconds=10),
        )
    )

    assert "receive_before_event" in {issue.code for issue in result.issues}


def test_session_assignment_uses_event_ts_not_receive_ts() -> None:
    record = _snapshot()

    assert L2_TIMESTAMP_FIELDS == ("event_ts", "receive_ts", "available_ts")
    assert SESSION_ASSIGNMENT_TIMESTAMP_FIELD == "event_ts"
    assert session_assignment_timestamp(record) == record["event_ts"]
