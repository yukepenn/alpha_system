from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from alpha_system.core.enums import Direction
from alpha_system.signals.spec import (
    REQUIRED_SIGNAL_RECORD_FIELDS,
    SIGNAL_RECORD_SCHEMA_FIELDS,
    SignalRecord,
    SignalSpecError,
    SignalType,
    assert_signal_record_schema,
)
from alpha_system.signals.validation import validate_signal_record


def test_signal_record_required_fields_present_and_typed() -> None:
    record = validate_signal_record(_signal_payload())

    assert isinstance(record, SignalRecord)
    assert record.signal_type is SignalType.ENTRY
    assert record.direction is Direction.LONG
    assert isinstance(record.event_ts, datetime)
    assert isinstance(record.available_ts, datetime)
    assert isinstance(record.bar_index, int)
    assert isinstance(record.factor_versions, dict)
    assert isinstance(record.quality_flags, tuple)
    assert set(REQUIRED_SIGNAL_RECORD_FIELDS).issubset(record.to_dict())
    assert tuple(record.to_dict()) == SIGNAL_RECORD_SCHEMA_FIELDS
    assert_signal_record_schema(record)


def test_signal_record_rejects_missing_required_field() -> None:
    payload = _signal_payload()
    payload.pop("instrument_id")

    with pytest.raises(SignalSpecError, match="missing required fields"):
        SignalRecord.from_mapping(payload)


def _signal_payload() -> dict[str, object]:
    event_ts = datetime(2026, 1, 2, 14, 31, tzinfo=timezone.utc)
    return {
        "signal_id": "sig-1",
        "instrument_id": "SYNTH",
        "event_ts": event_ts.isoformat().replace("+00:00", "Z"),
        "available_ts": (event_ts + timedelta(seconds=5)).isoformat().replace("+00:00", "Z"),
        "session_id": "XNYS:2026-01-02:regular",
        "bar_index": 1,
        "signal_type": "entry",
        "direction": "long",
        "score": 0.8,
        "confidence": 0.7,
        "desired_exposure": 0.25,
        "strategy_id": "threshold_strategy",
        "strategy_version": "v1",
        "factor_versions": {"fixture_close_delta": "v1"},
        "quality_flags": ["synthetic"],
        "data_version": "data:v1",
    }
