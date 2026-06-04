from __future__ import annotations

from dataclasses import fields
from datetime import UTC, datetime, timedelta

import pytest

from alpha_system.data.foundation import (
    CANONICAL_BAR_TIMESTAMP_FIELDS,
    CanonicalBarRecord,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError


def _bar_values(**overrides: object) -> dict[str, object]:
    start = datetime(2026, 6, 1, 14, 30, tzinfo=UTC)
    values: dict[str, object] = {
        "instrument_id": "inst_synth_es",
        "contract_id": "fut_es_202606",
        "series_id": "series_es_front_unadjusted",
        "bar_start_ts": start,
        "event_ts": start + timedelta(seconds=30),
        "bar_end_ts": start + timedelta(minutes=1),
        "available_ts": start + timedelta(minutes=1, seconds=5),
        "ingested_at": start + timedelta(minutes=2),
        "open": "5000.25",
        "high": "5001.00",
        "low": "4999.75",
        "close": "5000.50",
        "volume": "100",
        "source": "dsrc_ibkr_historical",
        "source_request_id": "hrs_synthetic_canonical_bars",
        "data_version": "canonical-bars-v1",
        "quality_flags": (),
        "session_label": "ETH",
    }
    values.update(overrides)
    return values


def test_canonical_bar_has_five_separate_timestamp_fields() -> None:
    record = CanonicalBarRecord.from_mapping(_bar_values())
    field_names = {field.name for field in fields(CanonicalBarRecord)}
    timestamp_values = (
        record.bar_start_ts,
        record.event_ts,
        record.bar_end_ts,
        record.available_ts,
        record.ingested_at,
    )

    assert set(CANONICAL_BAR_TIMESTAMP_FIELDS).issubset(field_names)
    assert len(CANONICAL_BAR_TIMESTAMP_FIELDS) == 5
    assert len(timestamp_values) == len(set(timestamp_values))


def test_canonical_bar_available_ts_cannot_precede_bar_end_ts() -> None:
    record = CanonicalBarRecord.from_mapping(_bar_values())

    assert record.available_ts >= record.bar_end_ts
    with pytest.raises(DataFoundationValidationError, match="available_ts"):
        CanonicalBarRecord.from_mapping(
            _bar_values(available_ts=record.bar_end_ts - timedelta(microseconds=1))
        )


def test_canonical_bar_missing_available_ts_is_rejected() -> None:
    values = _bar_values()
    del values["available_ts"]

    with pytest.raises(DataFoundationValidationError, match="available_ts"):
        CanonicalBarRecord.from_mapping(values)
