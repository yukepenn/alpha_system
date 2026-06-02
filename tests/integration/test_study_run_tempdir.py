from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from alpha_system.research.diagnostics import run_study
from alpha_system.research.study_config import StudyConfig


def test_study_run_writes_summary_and_manifest_to_tempdir(tmp_path: Path) -> None:
    factor_path = _write_jsonl(tmp_path / "factor_values.jsonl", _factor_rows())
    label_path = _write_jsonl(tmp_path / "labels.jsonl", _label_rows())
    output_dir = tmp_path / "study_outputs"
    config = StudyConfig.from_mapping(
        {
            "study_id": "tempdir-study",
            "factor_id": "fixture_close_delta",
            "factor_version": "v1",
            "label_id": "forward_return_1m",
            "label_version": "labels:v1",
            "data_version": "data:v1",
            "factor_values_path": factor_path.as_posix(),
            "labels_path": label_path.as_posix(),
            "horizon_seconds": 60,
            "output_dir": output_dir.as_posix(),
            "manifest_path": (output_dir / "manifest.json").as_posix(),
            "sample_size_thresholds": {"min_total": 2},
            "bucket_count": 2,
        }
    )

    result = run_study(config)

    assert result.summary.sample_size == 4
    assert result.registry_written is False
    assert Path(result.output_paths.summary_path).is_file()
    assert Path(result.output_paths.manifest_path).is_file()
    assert Path(result.output_paths.summary_path).is_relative_to(output_dir)
    summary = json.loads(Path(result.output_paths.summary_path).read_text(encoding="utf-8"))
    assert "directional" in summary["diagnostics"]
    assert "management_features" in summary["diagnostics"]


def _factor_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, value in enumerate([1.0, 2.0, -1.0, -2.0]):
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
    values = [0.03, 0.02, -0.01, -0.02]
    rows: list[dict[str, object]] = []
    for index, value in enumerate(values):
        rows.extend(_label_family(index, value))
    return rows


def _label_family(index: int, forward_return: float) -> list[dict[str, object]]:
    event_ts = _event_ts(index)
    horizon_end = event_ts + timedelta(seconds=60)
    base_metadata = {
        "session_id": "XNYS:2026-01-02:regular",
        "label_version": "labels:v1",
        "horizon_end_ts": _text(horizon_end),
        "required_future_bars": 1,
        "observed_future_bars": 1,
        "entry_bar_index": index,
        "target_hit_bar_index": index + 1,
        "stop_hit_bar_index": index + 1,
    }
    return [
        _label(index, "forward_return_1m", "forward_return_1m", forward_return, base_metadata),
        _label(index, "mfe_by_horizon", "mfe_by_horizon", abs(forward_return) + 0.01, base_metadata),
        _label(index, "mae_by_horizon", "mae_by_horizon", -abs(forward_return), base_metadata),
        _label(index, "target_before_stop", "target_before_stop", forward_return > 0, base_metadata),
        _label(index, "stop_before_target", "stop_before_target", forward_return <= 0, base_metadata),
        _label(
            index,
            "future_spread_liquidity",
            "future_spread_liquidity",
            0.01 + index * 0.01,
            {**base_metadata, "average_spread": str(0.01 + index * 0.01), "total_volume": str(1000 - index * 10), "average_trade_count": 10 + index},
        ),
    ]


def _label(
    index: int,
    label_id: str,
    label_type: str,
    value: object,
    metadata: dict[str, object],
) -> dict[str, object]:
    event_ts = _event_ts(index)
    return {
        "label_id": label_id,
        "instrument_id": "SYNTH",
        "event_ts": _text(event_ts),
        "horizon": 60,
        "label_type": label_type,
        "value": value,
        "path_metadata": metadata,
        "data_version": "data:v1",
        "label_available_ts": _text(event_ts + timedelta(seconds=65)),
    }


def _event_ts(index: int) -> datetime:
    return datetime(2026, 1, 2, 14, 31 + index, tzinfo=timezone.utc)


def _text(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> Path:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    return path
