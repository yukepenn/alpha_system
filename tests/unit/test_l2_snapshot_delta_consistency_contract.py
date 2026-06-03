from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from alpha_system.core.enums import BookSide, L2EventType
from alpha_system.l2.validation import validate_l2_snapshot_delta_consistency


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
    event_ts = datetime(2026, 1, 2, 14, 30, 1, tzinfo=timezone.utc)
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
        "size": Decimal("12"),
        "order_count": 2,
        "data_version": "data:l2:synthetic:v1",
        "quality_flags": (),
    }
    record.update(overrides)
    return record


def test_l2_snapshot_delta_consistency_accepts_matching_context() -> None:
    result = validate_l2_snapshot_delta_consistency(
        _snapshot(),
        (_delta(sequence_id=1), _delta(sequence_id=2, price=Decimal("100.02"))),
    )

    assert result.valid


def test_l2_snapshot_delta_consistency_rejects_context_mismatch() -> None:
    result = validate_l2_snapshot_delta_consistency(
        _snapshot(),
        (_delta(data_version="data:l2:synthetic:v2"),),
    )

    assert "snapshot_delta_mismatch" in {issue.code for issue in result.issues}


def test_l2_snapshot_delta_consistency_rejects_before_snapshot() -> None:
    snapshot_event_ts = datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc)
    result = validate_l2_snapshot_delta_consistency(
        _snapshot(event_ts=snapshot_event_ts),
        (
            _delta(
                event_ts=snapshot_event_ts - timedelta(milliseconds=1),
                receive_ts=snapshot_event_ts + timedelta(milliseconds=1),
                available_ts=snapshot_event_ts + timedelta(milliseconds=2),
            ),
        ),
    )

    assert "delta_before_snapshot_event" in {issue.code for issue in result.issues}


def test_l2_snapshot_delta_consistency_requires_monotonic_sequence() -> None:
    result = validate_l2_snapshot_delta_consistency(
        _snapshot(),
        (_delta(sequence_id=2), _delta(sequence_id=2)),
    )

    assert "sequence_id_order" in {issue.code for issue in result.issues}
