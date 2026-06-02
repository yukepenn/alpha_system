from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from alpha_system.research.diagnostics import DiagnosticsError, align_factor_values_to_labels
from alpha_system.research.study_config import StudyConfig


def test_diagnostics_reject_misaligned_label_version() -> None:
    config = _config()
    label = _label(label_version="labels:v2")

    with pytest.raises(DiagnosticsError, match="misaligned"):
        align_factor_values_to_labels([_factor()], [label], config)


def test_diagnostics_requires_instrument_session_and_horizon_alignment() -> None:
    config = _config()
    missing_session = align_factor_values_to_labels(
        [_factor(session_id="XNYS:2026-01-03:regular")],
        [_label()],
        config,
    )

    assert missing_session.missing_label_count == 1
    assert missing_session.observations == ()

    horizon_config = config.with_overrides(horizon_seconds=300)
    with pytest.raises(DiagnosticsError, match="no matching labels"):
        align_factor_values_to_labels([_factor()], [_label()], horizon_config)


def _config() -> StudyConfig:
    return StudyConfig.from_mapping(
        {
            "study_id": "alignment",
            "factor_id": "fixture_close_delta",
            "factor_version": "v1",
            "label_id": "forward_return_1m",
            "label_version": "labels:v1",
            "data_version": "data:v1",
            "factor_values_path": "/tmp/factors.jsonl",
            "labels_path": "/tmp/labels.jsonl",
            "horizon_seconds": 60,
            "sample_size_thresholds": {"min_total": 1, "max_missing_label_rate": 1},
        }
    )


def _event_ts() -> datetime:
    return datetime(2026, 1, 2, 14, 31, tzinfo=timezone.utc)


def _factor(*, session_id: str = "XNYS:2026-01-02:regular") -> dict[str, object]:
    event_ts = _event_ts()
    return {
        "factor_id": "fixture_close_delta",
        "factor_version": "v1",
        "instrument_id": "SYNTH",
        "event_ts": event_ts.isoformat().replace("+00:00", "Z"),
        "available_ts": (event_ts + timedelta(seconds=5)).isoformat().replace("+00:00", "Z"),
        "session_id": session_id,
        "bar_index": 1,
        "value": 1.0,
        "normalized_value": 1.0,
        "quality_flags": ["synthetic"],
        "data_version": "data:v1",
        "compute_version": "test",
    }


def _label(*, label_version: str = "labels:v1") -> dict[str, object]:
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
            "label_version": label_version,
            "horizon_end_ts": horizon_end.isoformat().replace("+00:00", "Z"),
            "required_future_bars": 1,
            "observed_future_bars": 1,
        },
        "data_version": "data:v1",
        "label_available_ts": (event_ts + timedelta(seconds=65)).isoformat().replace("+00:00", "Z"),
    }
