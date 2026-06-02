from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from alpha_system.research.diagnostics import run_study
from alpha_system.research.study_config import StudyConfig


def test_study_records_study_and_factor_validation_runs_in_temp_registry(tmp_path: Path) -> None:
    factor_path = _write_jsonl(tmp_path / "factor_values.jsonl", _factor_rows())
    label_path = _write_jsonl(tmp_path / "labels.jsonl", _label_rows())
    registry_path = tmp_path / "registry.sqlite3"
    output_dir = tmp_path / "study_outputs"
    config = StudyConfig.from_mapping(
        {
            "study_id": "registry-study",
            "factor_id": "fixture_close_delta",
            "factor_version": "v1",
            "label_id": "forward_return_1m",
            "label_version": "labels:v1",
            "data_version": "data:v1",
            "factor_values_path": factor_path.as_posix(),
            "labels_path": label_path.as_posix(),
            "horizon_seconds": 60,
            "output_dir": output_dir.as_posix(),
            "registry_path": registry_path.as_posix(),
            "sample_size_thresholds": {"min_total": 1},
            "bucket_count": 2,
        }
    )

    result = run_study(config)

    assert result.registry_written is True
    with sqlite3.connect(registry_path) as connection:
        study_count = connection.execute("SELECT count(*) FROM study_runs").fetchone()[0]
        validation_count = connection.execute("SELECT count(*) FROM factor_validation_runs").fetchone()[0]
        status = connection.execute("SELECT decision_status FROM study_runs").fetchone()[0]
    assert study_count == 1
    assert validation_count == 1
    assert status == "diagnostic_recorded"


def _factor_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, value in enumerate([1.0, 2.0]):
        event_ts = _event_ts(index)
        rows.append(
            {
                "factor_id": "fixture_close_delta",
                "factor_version": "v1",
                "instrument_id": "SYNTH",
                "event_ts": _text(event_ts),
                "available_ts": _text(event_ts + timedelta(seconds=5)),
                "session_id": "XNYS:2026-01-02:regular",
                "bar_index": index,
                "value": value,
                "normalized_value": value,
                "quality_flags": ["synthetic"],
                "data_version": "data:v1",
                "compute_version": "test",
            }
        )
    return rows


def _label_rows() -> list[dict[str, object]]:
    rows = []
    for index, value in enumerate([0.01, 0.02]):
        event_ts = _event_ts(index)
        rows.append(
            {
                "label_id": "forward_return_1m",
                "instrument_id": "SYNTH",
                "event_ts": _text(event_ts),
                "horizon": 60,
                "label_type": "forward_return_1m",
                "value": value,
                "path_metadata": {
                    "session_id": "XNYS:2026-01-02:regular",
                    "label_version": "labels:v1",
                    "horizon_end_ts": _text(event_ts + timedelta(seconds=60)),
                    "required_future_bars": 1,
                    "observed_future_bars": 1,
                },
                "data_version": "data:v1",
                "label_available_ts": _text(event_ts + timedelta(seconds=65)),
            }
        )
    return rows


def _event_ts(index: int) -> datetime:
    return datetime(2026, 1, 2, 14, 31 + index, tzinfo=timezone.utc)


def _text(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> Path:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    return path
