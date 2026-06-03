from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from alpha_system.core.enums import BookSide, L2EventType
from alpha_system.l2.timestamps import (
    is_l2_record_available,
    l2_research_order_key,
    l2_source_event_order_key,
    l2_timestamps_are_ordered,
)
from alpha_system.l2.validation import validate_l2_delta


def _valid_delta(**overrides: object) -> dict[str, object]:
    event_ts = datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc)
    record: dict[str, object] = {
        "instrument_id": "SYNTH-L2-1",
        "session_id": "2026-01-02_RTH",
        "event_ts": event_ts,
        "receive_ts": event_ts + timedelta(milliseconds=5),
        "available_ts": event_ts + timedelta(milliseconds=10),
        "sequence_id": 1,
        "action": L2EventType.UPDATE,
        "book_level": 1,
        "side": BookSide.BID,
        "price": Decimal("100.01"),
        "size": Decimal("10"),
        "order_count": 2,
        "data_version": "data:l2:synthetic:v1",
        "quality_flags": (),
    }
    record.update(overrides)
    return record


def test_l2_records_are_usable_only_at_or_after_available_ts() -> None:
    record = _valid_delta()
    available_ts = record["available_ts"]
    assert isinstance(available_ts, datetime)

    assert not is_l2_record_available(
        record,
        as_of=available_ts - timedelta(microseconds=1),
    )
    assert is_l2_record_available(record, as_of=available_ts)


def test_l2_timestamp_ordering_rejects_available_before_receive() -> None:
    event_ts = datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc)
    result = validate_l2_delta(
        _valid_delta(
            event_ts=event_ts,
            receive_ts=event_ts + timedelta(milliseconds=10),
            available_ts=event_ts + timedelta(milliseconds=5),
        )
    )

    assert "available_before_receive" in {issue.code for issue in result.issues}
    assert not l2_timestamps_are_ordered(
        _valid_delta(
            event_ts=event_ts,
            receive_ts=event_ts + timedelta(milliseconds=10),
            available_ts=event_ts + timedelta(milliseconds=5),
        )
    )


def test_l2_research_order_uses_available_ts_before_event_ts() -> None:
    event_ts = datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc)
    early_event_late_available = _valid_delta(
        event_ts=event_ts,
        receive_ts=event_ts + timedelta(milliseconds=20),
        available_ts=event_ts + timedelta(milliseconds=30),
        sequence_id=1,
    )
    later_event_early_available = _valid_delta(
        event_ts=event_ts + timedelta(milliseconds=5),
        receive_ts=event_ts + timedelta(milliseconds=10),
        available_ts=event_ts + timedelta(milliseconds=15),
        sequence_id=2,
    )

    assert l2_research_order_key(later_event_early_available) < l2_research_order_key(
        early_event_late_available
    )
    assert l2_source_event_order_key(early_event_late_available) < (
        l2_source_event_order_key(later_event_early_available)
    )
