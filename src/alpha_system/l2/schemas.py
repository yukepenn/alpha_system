"""Design-only Level-2 snapshot and event/delta schema metadata."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Mapping

from alpha_system.core.enums import BookSide, L2EventType


L2_SCHEMA_VERSION = "l2_readiness_schema_v1"
L2_SNAPSHOT_SCHEMA_ID = "l2_snapshot_v1"
L2_EVENT_DELTA_SCHEMA_ID = "l2_event_delta_v1"

MIN_BOOK_LEVEL = 1
MAX_BOOK_LEVEL = 50

VALID_L2_SIDES: tuple[str, ...] = tuple(side.value for side in BookSide)
VALID_L2_UPDATE_ACTIONS: tuple[str, ...] = tuple(action.value for action in L2EventType)

REQUIRED_L2_SNAPSHOT_FIELDS: tuple[str, ...] = (
    "instrument_id",
    "session_id",
    "event_ts",
    "receive_ts",
    "available_ts",
    "book_level",
    "side",
    "price",
    "size",
    "order_count",
    "data_version",
    "quality_flags",
)

REQUIRED_L2_EVENT_DELTA_FIELDS: tuple[str, ...] = (
    "instrument_id",
    "session_id",
    "event_ts",
    "receive_ts",
    "available_ts",
    "sequence_id",
    "action",
    "book_level",
    "side",
    "price",
    "size",
    "order_count",
    "data_version",
    "quality_flags",
)


@dataclass(frozen=True, slots=True)
class L2Field:
    """One L2 schema field and its in-memory Python representation."""

    name: str
    python_type: type[Any]
    required: bool = True
    nullable: bool = False
    enum_values: tuple[str, ...] = ()
    description: str = ""


@dataclass(frozen=True, slots=True, kw_only=True)
class L2SnapshotSchemaRecord:
    """One design-only L2 snapshot table row at one book level."""

    instrument_id: str
    session_id: str
    event_ts: datetime
    receive_ts: datetime
    available_ts: datetime
    book_level: int
    side: BookSide
    price: Decimal
    size: Decimal
    order_count: int | None
    data_version: str
    quality_flags: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class L2EventDeltaSchemaRecord:
    """One design-only L2 event/delta table row."""

    instrument_id: str
    session_id: str
    event_ts: datetime
    receive_ts: datetime
    available_ts: datetime
    sequence_id: int | None
    action: L2EventType
    book_level: int | None
    side: BookSide
    price: Decimal
    size: Decimal
    order_count: int | None
    data_version: str
    quality_flags: tuple[str, ...]


L2_SNAPSHOT_FIELDS: tuple[L2Field, ...] = (
    L2Field(
        "instrument_id",
        str,
        description="Stable instrument identifier from the instrument master.",
    ),
    L2Field("session_id", str, description="Assigned session identifier."),
    L2Field(
        "event_ts",
        datetime,
        description="Exchange/source event timestamp for the book state.",
    ),
    L2Field(
        "receive_ts",
        datetime,
        description="Local or feed receive timestamp for the record.",
    ),
    L2Field(
        "available_ts",
        datetime,
        description="Earliest timestamp downstream research may use the record.",
    ),
    L2Field(
        "book_level",
        int,
        description="One-based depth level within the bounded design schema.",
    ),
    L2Field(
        "side",
        str,
        enum_values=VALID_L2_SIDES,
        description="Bid or ask side.",
    ),
    L2Field("price", Decimal, description="Quoted price at this side/level."),
    L2Field("size", Decimal, description="Aggregate size at this side/level."),
    L2Field(
        "order_count",
        int,
        nullable=True,
        description="Displayed order count when the source provides it.",
    ),
    L2Field("data_version", str, description="Version id for the L2 source slice."),
    L2Field(
        "quality_flags",
        tuple,
        description="Tuple of string data-quality flags, empty when clean.",
    ),
)

L2_EVENT_DELTA_FIELDS: tuple[L2Field, ...] = (
    L2Field(
        "instrument_id",
        str,
        description="Stable instrument identifier from the instrument master.",
    ),
    L2Field("session_id", str, description="Assigned session identifier."),
    L2Field(
        "event_ts",
        datetime,
        description="Exchange/source event timestamp for the update.",
    ),
    L2Field(
        "receive_ts",
        datetime,
        description="Local or feed receive timestamp for the update.",
    ),
    L2Field(
        "available_ts",
        datetime,
        description="Earliest timestamp downstream research may use the update.",
    ),
    L2Field(
        "sequence_id",
        int,
        nullable=True,
        description="Monotonic source sequence id when the source provides it.",
    ),
    L2Field(
        "action",
        str,
        enum_values=VALID_L2_UPDATE_ACTIONS,
        description="Update action: add, update, delete, or clear.",
    ),
    L2Field(
        "book_level",
        int,
        nullable=True,
        description="One-based depth level when the action targets a level.",
    ),
    L2Field(
        "side",
        str,
        enum_values=VALID_L2_SIDES,
        description="Bid or ask side.",
    ),
    L2Field("price", Decimal, description="Quoted price for the update."),
    L2Field("size", Decimal, description="Aggregate size after the update."),
    L2Field(
        "order_count",
        int,
        nullable=True,
        description="Displayed order count when the source provides it.",
    ),
    L2Field("data_version", str, description="Version id for the L2 source slice."),
    L2Field(
        "quality_flags",
        tuple,
        description="Tuple of string data-quality flags, empty when clean.",
    ),
)

L2_SNAPSHOT_SCHEMA: Mapping[str, L2Field] = {
    field.name: field for field in L2_SNAPSHOT_FIELDS
}
L2_EVENT_DELTA_SCHEMA: Mapping[str, L2Field] = {
    field.name: field for field in L2_EVENT_DELTA_FIELDS
}


def l2_snapshot_columns() -> tuple[str, ...]:
    """Return L2 snapshot columns in stable schema order."""
    return REQUIRED_L2_SNAPSHOT_FIELDS


def l2_event_delta_columns() -> tuple[str, ...]:
    """Return L2 event/delta columns in stable schema order."""
    return REQUIRED_L2_EVENT_DELTA_FIELDS


def missing_l2_snapshot_fields(record: Mapping[str, Any]) -> tuple[str, ...]:
    """Return absent L2 snapshot fields."""
    return tuple(field for field in REQUIRED_L2_SNAPSHOT_FIELDS if field not in record)


def missing_l2_event_delta_fields(record: Mapping[str, Any]) -> tuple[str, ...]:
    """Return absent L2 event/delta fields."""
    return tuple(
        field for field in REQUIRED_L2_EVENT_DELTA_FIELDS if field not in record
    )
