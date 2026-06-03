from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from alpha_system.core.enums import BookSide
from alpha_system.l2.schemas import VALID_L2_SIDES
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


def test_l2_side_enum_values_are_bid_and_ask() -> None:
    assert VALID_L2_SIDES == ("bid", "ask")


def test_l2_side_accepts_shared_enum_and_serialized_value() -> None:
    assert validate_l2_snapshot(_snapshot(side=BookSide.ASK)).valid
    assert validate_l2_snapshot(_snapshot(side="ask")).valid


def test_l2_side_rejects_unknown_value() -> None:
    result = validate_l2_snapshot(_snapshot(side="both"))

    assert "invalid_side" in {issue.code for issue in result.issues}
