from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from alpha_system.data.foundation.quotes import (
    CANONICAL_BBO_RECORD_FIELDS,
    MISSING_BBO_QUALITY_FLAG,
    CanonicalBBORecord,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError


def _timestamps() -> dict[str, datetime]:
    start = datetime(2026, 6, 1, 14, 30, tzinfo=UTC)
    return {
        "bar_start_ts": start,
        "bar_end_ts": start + timedelta(minutes=1),
        "event_ts": start + timedelta(minutes=1),
        "available_ts": start + timedelta(minutes=1, seconds=1),
        "ingested_at": start + timedelta(minutes=2),
    }


def _bbo_values(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "instrument_id": "inst_synth_es",
        "contract_id": "fut_es_202606",
        "series_id": "series_es_front_unadjusted",
        **_timestamps(),
        "bid": "5000.00",
        "ask": "5000.25",
        "bid_size": "12",
        "ask_size": "8",
        "mid": "5000.125",
        "spread": "0.25",
        "source": "dsrc_databento_historical",
        "source_request_id": "hrs_synthetic_canonical_bbo",
        "data_version": "canonical-bbo-v1",
        "quality_flags": (),
        "session_label": "ETH",
        "spread_ticks": "1",
        "microprice": "5000.10",
        "bid_order_count": 3,
        "ask_order_count": 2,
    }
    values.update(overrides)
    return values


def test_canonical_bbo_round_trips_and_exposes_required_fields() -> None:
    record = CanonicalBBORecord.from_mapping(_bbo_values())
    mapping = record.to_mapping()
    round_tripped = CanonicalBBORecord.from_mapping(mapping)

    assert {field.name for field in fields(CanonicalBBORecord)} == set(
        CANONICAL_BBO_RECORD_FIELDS
    )
    assert set(mapping) == set(CANONICAL_BBO_RECORD_FIELDS)
    assert round_tripped == record
    assert record.mid == Decimal("5000.125")
    assert record.spread == Decimal("0.25")
    assert record.available_ts >= record.event_ts >= record.bar_end_ts

    with pytest.raises(FrozenInstanceError):
        record.available_ts = record.event_ts  # type: ignore[misc]


def test_canonical_bbo_rejects_crossed_quote() -> None:
    with pytest.raises(DataFoundationValidationError, match="ask"):
        CanonicalBBORecord.from_mapping(
            _bbo_values(ask="4999.75", mid="4999.875", spread="0")
        )


def test_canonical_bbo_missing_available_ts_blocks_construction() -> None:
    values = _bbo_values()
    del values["available_ts"]

    with pytest.raises(DataFoundationValidationError, match="available_ts"):
        CanonicalBBORecord.from_mapping(values)

    with pytest.raises(DataFoundationValidationError, match="available_ts"):
        CanonicalBBORecord.from_mapping(_bbo_values(available_ts=None))


def test_canonical_bbo_rejects_ingested_at_as_available_ts() -> None:
    times = _timestamps()

    with pytest.raises(DataFoundationValidationError, match="ingested_at"):
        CanonicalBBORecord.from_mapping(_bbo_values(ingested_at=times["available_ts"]))


def test_missing_bbo_must_be_explicitly_flagged_and_not_forward_filled() -> None:
    missing_record = CanonicalBBORecord.from_mapping(
        _bbo_values(
            bid="0",
            ask="0",
            bid_size="0",
            ask_size="0",
            mid="0",
            spread="0",
            quality_flags=(MISSING_BBO_QUALITY_FLAG,),
            spread_ticks=None,
            microprice=None,
            bid_order_count=0,
            ask_order_count=0,
        )
    )

    assert missing_record.quality_flags == (MISSING_BBO_QUALITY_FLAG,)
    assert missing_record.bid == missing_record.ask == Decimal("0")

    with pytest.raises(DataFoundationValidationError, match="missing_bbo"):
        CanonicalBBORecord.from_mapping(
            _bbo_values(
                bid="0",
                ask="0",
                bid_size="0",
                ask_size="0",
                mid="0",
                spread="0",
                spread_ticks=None,
                microprice=None,
            )
        )

    with pytest.raises(DataFoundationValidationError, match="missing_bbo"):
        CanonicalBBORecord.from_mapping(
            _bbo_values(quality_flags=(MISSING_BBO_QUALITY_FLAG,))
        )


def test_canonical_bbo_from_mapping_rejects_unknown_and_missing_fields() -> None:
    with pytest.raises(DataFoundationValidationError, match="unsupported fields"):
        CanonicalBBORecord.from_mapping(_bbo_values(provider_ts="2026-06-01T14:31:00Z"))

    values = _bbo_values()
    del values["bid"]

    with pytest.raises(DataFoundationValidationError, match="bid"):
        CanonicalBBORecord.from_mapping(values)
