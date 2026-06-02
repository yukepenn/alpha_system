from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from alpha_system.core.enums import BookSide, L2EventType
from alpha_system.core.schema import contract_field_names
from alpha_system.l2 import contracts as l2_contracts
from alpha_system.l2.contracts import BookLevel, L2EventDelta, L2Snapshot


def test_l2_snapshot_design_fields_present() -> None:
    assert set(contract_field_names(L2Snapshot)).issuperset(
        {
            "snapshot_id",
            "instrument_id",
            "session_id",
            "event_ts",
            "receive_ts",
            "available_ts",
            "book_levels",
            "data_version",
            "quality_flags",
        }
    )


def test_l2_event_delta_design_fields_present() -> None:
    assert set(contract_field_names(L2EventDelta)).issuperset(
        {
            "sequence_number",
            "instrument_id",
            "session_id",
            "event_type",
            "side",
            "level",
            "price",
            "size",
            "order_count",
            "event_ts",
            "receive_ts",
            "available_ts",
            "data_version",
            "quality_flags",
        }
    )


def test_book_level_fields_present() -> None:
    assert set(contract_field_names(BookLevel)).issuperset(
        {"level", "side", "price", "size", "order_count"}
    )


def test_l2_timestamps_are_distinct_design_primitives() -> None:
    event_ts = datetime(2026, 1, 2, 14, 30, 0, tzinfo=timezone.utc)
    receive_ts = event_ts + timedelta(milliseconds=10)
    available_ts = receive_ts + timedelta(milliseconds=5)
    level = BookLevel(
        level=1,
        side=BookSide.BID,
        price=Decimal("100.00"),
        size=Decimal("500"),
        order_count=3,
    )

    snapshot = L2Snapshot(
        snapshot_id="snapshot-1",
        instrument_id="inst-1",
        session_id="session-1",
        event_ts=event_ts,
        receive_ts=receive_ts,
        available_ts=available_ts,
        book_levels=(level,),
        data_version="l2-v1",
        quality_flags=(),
    )
    event_delta = L2EventDelta(
        sequence_number=1,
        instrument_id="inst-1",
        session_id="session-1",
        event_type=L2EventType.UPDATE,
        side=BookSide.BID,
        level=1,
        price=Decimal("100.01"),
        size=Decimal("450"),
        order_count=2,
        event_ts=event_ts,
        receive_ts=receive_ts,
        available_ts=available_ts,
        data_version="l2-v1",
        quality_flags=(),
    )

    assert len({snapshot.event_ts, snapshot.receive_ts, snapshot.available_ts}) == 3
    assert len({event_delta.event_ts, event_delta.receive_ts}) == 2
    assert event_delta.available_ts not in {
        event_delta.event_ts,
        event_delta.receive_ts,
    }


def test_l2_contract_module_is_design_only() -> None:
    forbidden_names = {
        "L2ReplayEngine",
        "QueueModel",
        "PassiveFillModel",
        "L2IngestionClient",
    }

    assert forbidden_names.isdisjoint(set(dir(l2_contracts)))
