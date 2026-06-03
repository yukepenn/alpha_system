from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from alpha_system.core.enums import BookSide, L2EventType
from alpha_system.l2.schemas import VALID_L2_UPDATE_ACTIONS
from alpha_system.l2.validation import validate_l2_delta


def _delta(**overrides: object) -> dict[str, object]:
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
        "price": Decimal("100.00"),
        "size": Decimal("10"),
        "order_count": None,
        "data_version": "data:l2:synthetic:v1",
        "quality_flags": (),
    }
    record.update(overrides)
    return record


def test_l2_update_action_enum_values_are_declared() -> None:
    assert VALID_L2_UPDATE_ACTIONS == ("add", "update", "delete", "clear")


def test_l2_update_action_accepts_shared_enum_and_serialized_value() -> None:
    assert validate_l2_delta(_delta(action=L2EventType.ADD)).valid
    assert validate_l2_delta(_delta(action="delete")).valid


def test_l2_update_action_rejects_unknown_value() -> None:
    result = validate_l2_delta(_delta(action="replace"))

    assert "invalid_update_action" in {issue.code for issue in result.issues}
