"""Timestamp semantics for design-only L2 readiness records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping


EVENT_TS_FIELD = "event_ts"
RECEIVE_TS_FIELD = "receive_ts"
AVAILABLE_TS_FIELD = "available_ts"
SESSION_ASSIGNMENT_TIMESTAMP_FIELD = EVENT_TS_FIELD

L2_TIMESTAMP_FIELDS: tuple[str, ...] = (
    EVENT_TS_FIELD,
    RECEIVE_TS_FIELD,
    AVAILABLE_TS_FIELD,
)


@dataclass(frozen=True, slots=True)
class L2TimestampSemantic:
    """Durable meaning for one L2 timestamp field."""

    field: str
    meaning: str
    ordering_rule: str


L2_TIMESTAMP_SEMANTICS: tuple[L2TimestampSemantic, ...] = (
    L2TimestampSemantic(
        EVENT_TS_FIELD,
        "exchange/source event timestamp when available",
        "must not be after receive_ts or available_ts",
    ),
    L2TimestampSemantic(
        RECEIVE_TS_FIELD,
        "local or feed receive timestamp when available",
        "must be at or after event_ts and at or before available_ts",
    ),
    L2TimestampSemantic(
        AVAILABLE_TS_FIELD,
        "earliest time the research system may use the information",
        "must be at or after event_ts and receive_ts",
    ),
)


def require_l2_timestamp(record: Mapping[str, Any], field: str) -> datetime:
    """Return a timestamp field or raise for absent/non-datetime values."""
    value = record.get(field)
    if not isinstance(value, datetime):
        msg = f"{field} must be a datetime"
        raise TypeError(msg)
    return value


def session_assignment_timestamp(record: Mapping[str, Any]) -> datetime:
    """Return the timestamp used to assign an L2 record to a session."""
    return require_l2_timestamp(record, SESSION_ASSIGNMENT_TIMESTAMP_FIELD)


def l2_timestamp_order_errors(record: Mapping[str, Any]) -> tuple[str, ...]:
    """Return timestamp ordering errors for event/receive/available semantics."""
    event_ts = require_l2_timestamp(record, EVENT_TS_FIELD)
    receive_ts = require_l2_timestamp(record, RECEIVE_TS_FIELD)
    available_ts = require_l2_timestamp(record, AVAILABLE_TS_FIELD)

    errors: list[str] = []
    if receive_ts < event_ts:
        errors.append("receive_ts must be at or after event_ts")
    if available_ts < event_ts:
        errors.append("available_ts must be at or after event_ts")
    if available_ts < receive_ts:
        errors.append("available_ts must be at or after receive_ts")
    return tuple(errors)


def l2_timestamps_are_ordered(record: Mapping[str, Any]) -> bool:
    """Return True when event_ts <= receive_ts <= available_ts."""
    return not l2_timestamp_order_errors(record)


def is_l2_record_available(record: Mapping[str, Any], *, as_of: datetime) -> bool:
    """Return whether an L2 record is usable by research at ``as_of``."""
    return as_of >= require_l2_timestamp(record, AVAILABLE_TS_FIELD)


def _optional_int(record: Mapping[str, Any], field: str) -> int:
    value = record.get(field)
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return -1


def _optional_str(record: Mapping[str, Any], field: str) -> str:
    value = record.get(field)
    if hasattr(value, "value"):
        return str(value.value)
    if isinstance(value, str):
        return value
    return ""


def l2_research_order_key(
    record: Mapping[str, Any],
) -> tuple[datetime, datetime, datetime, int, str, str, int]:
    """Return a deterministic no-lookahead ordering key for research consumers."""
    return (
        require_l2_timestamp(record, AVAILABLE_TS_FIELD),
        require_l2_timestamp(record, RECEIVE_TS_FIELD),
        require_l2_timestamp(record, EVENT_TS_FIELD),
        _optional_int(record, "sequence_id"),
        _optional_str(record, "instrument_id"),
        _optional_str(record, "side"),
        _optional_int(record, "book_level"),
    )


def l2_source_event_order_key(
    record: Mapping[str, Any],
) -> tuple[datetime, datetime, datetime, int, str, str, int]:
    """Return a deterministic source-event ordering key for future replay design."""
    return (
        require_l2_timestamp(record, EVENT_TS_FIELD),
        require_l2_timestamp(record, RECEIVE_TS_FIELD),
        require_l2_timestamp(record, AVAILABLE_TS_FIELD),
        _optional_int(record, "sequence_id"),
        _optional_str(record, "instrument_id"),
        _optional_str(record, "side"),
        _optional_int(record, "book_level"),
    )
