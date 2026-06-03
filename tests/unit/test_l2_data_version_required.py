from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from alpha_system.core.enums import BookSide, L2EventType
from alpha_system.l2.validation import validate_l2_delta, validate_l2_snapshot


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


def _delta(**overrides: object) -> dict[str, object]:
    record = _snapshot()
    record.update({"sequence_id": 1, "action": L2EventType.UPDATE})
    record.update(overrides)
    return record


def test_l2_snapshot_rejects_blank_data_version() -> None:
    result = validate_l2_snapshot(_snapshot(data_version=" "))

    assert "missing_data_version" in {issue.code for issue in result.issues}


def test_l2_delta_requires_data_version_field() -> None:
    record = _delta()
    del record["data_version"]

    result = validate_l2_delta(record)

    assert "data_version" in {issue.field for issue in result.issues}
