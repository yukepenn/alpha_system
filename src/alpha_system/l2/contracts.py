"""Design-only Level-2 schema contract primitives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from alpha_system.core.contracts import QualityFlags
from alpha_system.core.enums import BookSide, L2EventType


@dataclass(frozen=True, slots=True, kw_only=True)
class BookLevel:
    level: int
    side: BookSide
    price: Decimal
    size: Decimal
    order_count: int | None


@dataclass(frozen=True, slots=True, kw_only=True)
class L2Snapshot:
    snapshot_id: str
    instrument_id: str
    session_id: str
    event_ts: datetime
    receive_ts: datetime
    available_ts: datetime
    book_levels: tuple[BookLevel, ...]
    data_version: str
    quality_flags: QualityFlags


@dataclass(frozen=True, slots=True, kw_only=True)
class L2EventDelta:
    sequence_number: int
    instrument_id: str
    session_id: str
    event_type: L2EventType
    side: BookSide
    level: int
    price: Decimal
    size: Decimal
    order_count: int | None
    event_ts: datetime
    receive_ts: datetime
    available_ts: datetime
    data_version: str
    quality_flags: QualityFlags
