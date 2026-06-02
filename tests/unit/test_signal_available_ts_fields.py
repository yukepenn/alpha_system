from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from alpha_system.signals.spec import SignalType
from alpha_system.signals.validation import SignalValidationError, validate_signal_record


def test_signal_carries_timing_session_bar_and_quality_metadata() -> None:
    event_ts = datetime(2026, 1, 2, 14, 31, tzinfo=timezone.utc)
    record = validate_signal_record(
        {
            "signal_id": "sig-available",
            "instrument_id": "SYNTH",
            "event_ts": event_ts,
            "available_ts": event_ts + timedelta(seconds=10),
            "session_id": "XNYS:2026-01-02:regular",
            "bar_index": 4,
            "signal_type": "hold",
            "direction": "flat",
            "score": None,
            "confidence": None,
            "desired_exposure": None,
            "strategy_id": "threshold_strategy",
            "strategy_version": "v1",
            "factor_versions": {"fixture_close_delta": "v1"},
            "quality_flags": ("synthetic", "point_in_time"),
            "data_version": "data:v1",
        }
    )

    assert record.event_ts == event_ts
    assert record.available_ts == event_ts + timedelta(seconds=10)
    assert record.session_id == "XNYS:2026-01-02:regular"
    assert record.bar_index == 4
    assert record.signal_type is SignalType.HOLD
    assert record.quality_flags == ("synthetic", "point_in_time")


def test_signal_available_ts_must_not_precede_event_ts() -> None:
    event_ts = datetime(2026, 1, 2, 14, 31, tzinfo=timezone.utc)

    with pytest.raises(SignalValidationError, match="available_ts"):
        validate_signal_record(
            {
                "signal_id": "sig-early",
                "instrument_id": "SYNTH",
                "event_ts": event_ts,
                "available_ts": event_ts - timedelta(seconds=1),
                "session_id": "XNYS:2026-01-02:regular",
                "bar_index": 4,
                "signal_type": "entry",
                "direction": "long",
                "score": 1.0,
                "confidence": 0.5,
                "desired_exposure": 0.1,
                "strategy_id": "threshold_strategy",
                "strategy_version": "v1",
                "factor_versions": {"fixture_close_delta": "v1"},
                "quality_flags": ("synthetic",),
                "data_version": "data:v1",
            }
        )
