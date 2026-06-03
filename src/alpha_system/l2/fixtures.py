"""Tiny deterministic synthetic L2 fixtures for feature-skeleton tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any


SYNTHETIC_L2_FEATURE_DATA_VERSION = "l2:synthetic:feature-fixture:v1"
SYNTHETIC_L2_INSTRUMENT_ID = "SYNTH_L2_FEATURE"
SYNTHETIC_L2_SESSION_ID = "XNYS:2026-01-02:regular"
SYNTHETIC_L2_EVENT_TS = datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc)


def _snapshot_row(
    *,
    level: int,
    side: str,
    price: str,
    size: str,
    order_count: int | None,
    event_offset_ms: int = 0,
    quality_flags: tuple[str, ...] = (),
) -> dict[str, Any]:
    event_ts = SYNTHETIC_L2_EVENT_TS + timedelta(milliseconds=event_offset_ms)
    receive_ts = event_ts + timedelta(milliseconds=5)
    available_ts = receive_ts + timedelta(milliseconds=5)
    return {
        "instrument_id": SYNTHETIC_L2_INSTRUMENT_ID,
        "session_id": SYNTHETIC_L2_SESSION_ID,
        "event_ts": event_ts,
        "receive_ts": receive_ts,
        "available_ts": available_ts,
        "book_level": level,
        "side": side,
        "price": Decimal(price),
        "size": Decimal(size),
        "order_count": order_count,
        "data_version": SYNTHETIC_L2_FEATURE_DATA_VERSION,
        "quality_flags": quality_flags,
    }


def synthetic_l2_snapshot_rows() -> tuple[dict[str, Any], ...]:
    """Return a tiny complete five-level synthetic L2 snapshot fixture."""
    return (
        _snapshot_row(level=1, side="bid", price="100.00", size="20", order_count=2),
        _snapshot_row(level=1, side="ask", price="100.05", size="30", order_count=3),
        _snapshot_row(level=2, side="bid", price="99.95", size="15", order_count=2),
        _snapshot_row(level=2, side="ask", price="100.10", size="25", order_count=2),
        _snapshot_row(level=3, side="bid", price="99.90", size="10", order_count=1),
        _snapshot_row(level=3, side="ask", price="100.15", size="20", order_count=1),
        _snapshot_row(level=4, side="bid", price="99.85", size="8", order_count=1),
        _snapshot_row(level=4, side="ask", price="100.20", size="10", order_count=1),
        _snapshot_row(level=5, side="bid", price="99.80", size="7", order_count=1),
        _snapshot_row(level=5, side="ask", price="100.25", size="5", order_count=1),
    )


def synthetic_l2_snapshot_with_quality_flag() -> tuple[dict[str, Any], ...]:
    """Return a complete fixture with one propagated quality flag."""
    rows = [dict(row) for row in synthetic_l2_snapshot_rows()]
    rows[0]["quality_flags"] = ("stale_quote",)
    return tuple(rows)


def synthetic_l2_snapshot_missing_ask_level_one() -> tuple[dict[str, Any], ...]:
    """Return a fixture missing the level-one ask side."""
    return tuple(
        row
        for row in synthetic_l2_snapshot_rows()
        if not (row["side"] == "ask" and row["book_level"] == 1)
    )


def synthetic_l2_snapshot_missing_inner_levels() -> tuple[dict[str, Any], ...]:
    """Return a fixture missing some top-five levels but not either side."""
    return tuple(
        row
        for row in synthetic_l2_snapshot_rows()
        if row["book_level"] not in {3, 4}
    )


def _delta_row(
    *,
    sequence_id: int,
    offset_ms: int,
    side: str,
    level: int,
    price: str,
    size: str,
    action: str = "update",
    order_count: int | None = 1,
    quality_flags: tuple[str, ...] = (),
) -> dict[str, Any]:
    event_ts = SYNTHETIC_L2_EVENT_TS + timedelta(milliseconds=offset_ms)
    receive_ts = event_ts + timedelta(milliseconds=5)
    available_ts = receive_ts + timedelta(milliseconds=5)
    return {
        "instrument_id": SYNTHETIC_L2_INSTRUMENT_ID,
        "session_id": SYNTHETIC_L2_SESSION_ID,
        "event_ts": event_ts,
        "receive_ts": receive_ts,
        "available_ts": available_ts,
        "sequence_id": sequence_id,
        "action": action,
        "book_level": level,
        "side": side,
        "price": Decimal(price),
        "size": Decimal(size),
        "order_count": order_count,
        "data_version": SYNTHETIC_L2_FEATURE_DATA_VERSION,
        "quality_flags": quality_flags,
    }


def synthetic_l2_delta_rows() -> tuple[dict[str, Any], ...]:
    """Return tiny synthetic deltas for quote-update-intensity tests."""
    return (
        _delta_row(
            sequence_id=1,
            offset_ms=0,
            side="bid",
            level=1,
            price="100.00",
            size="21",
        ),
        _delta_row(
            sequence_id=2,
            offset_ms=500,
            side="ask",
            level=1,
            price="100.05",
            size="29",
        ),
        _delta_row(
            sequence_id=3,
            offset_ms=1500,
            side="bid",
            level=2,
            price="99.95",
            size="14",
        ),
    )


def synthetic_l2_fixture_metadata() -> dict[str, str]:
    """Return fixture metadata that documents synthetic-only scope."""
    return {
        "data_version": SYNTHETIC_L2_FEATURE_DATA_VERSION,
        "instrument_id": SYNTHETIC_L2_INSTRUMENT_ID,
        "scope": "synthetic fixture only; not real market data",
    }
