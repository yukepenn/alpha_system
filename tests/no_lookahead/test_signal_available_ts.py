from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from alpha_system.signals.validation import (
    SignalValidationError,
    validate_signal_available_ts,
)


def test_signal_available_ts_respects_input_factor_available_ts() -> None:
    event_ts = datetime(2026, 1, 2, 14, 31, tzinfo=timezone.utc)
    factor = _factor_value(event_ts, event_ts + timedelta(seconds=20))
    signal = _signal_record(event_ts, event_ts + timedelta(seconds=20))

    validated = validate_signal_available_ts(signal, [factor])

    assert validated.available_ts == event_ts + timedelta(seconds=20)


def test_signal_available_ts_rejects_early_availability() -> None:
    event_ts = datetime(2026, 1, 2, 14, 31, tzinfo=timezone.utc)
    factor = _factor_value(event_ts, event_ts + timedelta(seconds=20))
    signal = _signal_record(event_ts, event_ts + timedelta(seconds=5))

    with pytest.raises(SignalValidationError, match="input factor available_ts"):
        validate_signal_available_ts(signal, [factor])


def _signal_record(event_ts: datetime, available_ts: datetime) -> dict[str, object]:
    return {
        "signal_id": "sig-1",
        "instrument_id": "SYNTH",
        "event_ts": event_ts.isoformat().replace("+00:00", "Z"),
        "available_ts": available_ts.isoformat().replace("+00:00", "Z"),
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


def _factor_value(event_ts: datetime, available_ts: datetime) -> dict[str, object]:
    return {
        "factor_id": "fixture_close_delta",
        "factor_version": "v1",
        "instrument_id": "SYNTH",
        "event_ts": event_ts.isoformat().replace("+00:00", "Z"),
        "available_ts": available_ts.isoformat().replace("+00:00", "Z"),
        "session_id": "XNYS:2026-01-02:regular",
        "bar_index": 1,
        "value": 0.8,
        "normalized_value": 0.8,
        "quality_flags": ["synthetic"],
        "data_version": "data:v1",
        "compute_version": "test",
    }
