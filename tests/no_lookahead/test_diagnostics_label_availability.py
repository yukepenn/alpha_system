from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from alpha_system.research.diagnostics import DiagnosticsError, align_factor_values_to_labels
from alpha_system.research.study_config import StudyConfig


def test_diagnostics_reject_label_available_before_factor_available() -> None:
    config = _config()
    factor = _factor(available_offset=timedelta(minutes=2))
    label = _label(available_offset=timedelta(seconds=65))

    with pytest.raises(DiagnosticsError, match="label_available_ts"):
        align_factor_values_to_labels([factor], [label], config)


def test_diagnostics_accept_label_available_at_or_after_factor_available() -> None:
    config = _config()
    factor = _factor(available_offset=timedelta(seconds=5))
    label = _label(available_offset=timedelta(seconds=65))

    result = align_factor_values_to_labels([factor], [label], config)

    assert len(result.observations) == 1


def _config() -> StudyConfig:
    return StudyConfig.from_mapping(
        {
            "study_id": "availability",
            "factor_id": "fixture_close_delta",
            "factor_version": "v1",
            "label_id": "forward_return_1m",
            "label_version": "labels:v1",
            "data_version": "data:v1",
            "factor_values_path": "/tmp/factors.jsonl",
            "labels_path": "/tmp/labels.jsonl",
            "horizon_seconds": 60,
            "sample_size_thresholds": {"min_total": 1},
        }
    )


def _event_ts() -> datetime:
    return datetime(2026, 1, 2, 14, 31, tzinfo=timezone.utc)


def _factor(*, available_offset: timedelta) -> dict[str, object]:
    event_ts = _event_ts()
    return {
        "factor_id": "fixture_close_delta",
        "factor_version": "v1",
        "instrument_id": "SYNTH",
        "event_ts": event_ts.isoformat().replace("+00:00", "Z"),
        "available_ts": (event_ts + available_offset).isoformat().replace("+00:00", "Z"),
        "session_id": "XNYS:2026-01-02:regular",
        "bar_index": 1,
        "value": 1.0,
        "normalized_value": 1.0,
        "quality_flags": ["synthetic"],
        "data_version": "data:v1",
        "compute_version": "test",
    }


def _label(*, available_offset: timedelta) -> dict[str, object]:
    event_ts = _event_ts()
    horizon_end = event_ts + timedelta(seconds=60)
    return {
        "label_id": "forward_return_1m",
        "instrument_id": "SYNTH",
        "event_ts": event_ts.isoformat().replace("+00:00", "Z"),
        "horizon": 60,
        "label_type": "forward_return_1m",
        "value": 0.01,
        "path_metadata": {
            "session_id": "XNYS:2026-01-02:regular",
            "label_version": "labels:v1",
            "horizon_end_ts": horizon_end.isoformat().replace("+00:00", "Z"),
            "required_future_bars": 1,
            "observed_future_bars": 1,
        },
        "data_version": "data:v1",
        "label_available_ts": (event_ts + available_offset).isoformat().replace("+00:00", "Z"),
    }
