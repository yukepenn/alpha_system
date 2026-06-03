from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from alpha_system.core.enums import BookSide, L2EventType
from alpha_system.l2.validation import validate_l2_delta, validate_l2_snapshot


def _snapshot() -> dict[str, object]:
    event_ts = datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc)
    return {
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


def _delta() -> dict[str, object]:
    record = _snapshot()
    record.update({"sequence_id": 1, "action": L2EventType.UPDATE})
    return record


def test_available_ts_is_required_on_snapshot_records() -> None:
    record = _snapshot()
    del record["available_ts"]

    result = validate_l2_snapshot(record)

    assert "missing_required_field" in {issue.code for issue in result.issues}
    assert "available_ts" in {issue.field for issue in result.issues}


def test_available_ts_is_required_on_delta_records() -> None:
    record = _delta()
    del record["available_ts"]

    result = validate_l2_delta(record)

    assert "missing_required_field" in {issue.code for issue in result.issues}
    assert "available_ts" in {issue.field for issue in result.issues}
