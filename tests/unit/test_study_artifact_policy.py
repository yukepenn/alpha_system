from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from alpha_system.research.study_outputs import StudyOutputError, resolve_study_output_dir


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"


def test_study_output_policy_rejects_committed_repo_dirs() -> None:
    with pytest.raises(StudyOutputError, match="artifacts/factor_studies"):
        resolve_study_output_dir(REPO_ROOT / "docs" / "bad_study_output")


def test_study_cli_writes_only_to_temp_paths(tmp_path: Path) -> None:
    factor_path = _write_jsonl(tmp_path / "factor_values.jsonl", _factor_rows())
    label_path = _write_jsonl(tmp_path / "labels.jsonl", _label_rows())
    output_dir = tmp_path / "study_outputs"
    config_path = tmp_path / "study.json"
    config_path.write_text(
        json.dumps(
            {
                "study_id": "artifact-policy",
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
                "sample_size_thresholds": {"min_total": 1},
                "bucket_count": 2,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alpha_system.cli",
            "study",
            "run",
            "--config",
            config_path.as_posix(),
            "--json",
        ],
        cwd=REPO_ROOT,
        env=_env_with_src_path(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert Path(payload["output_paths"]["summary_path"]).is_relative_to(output_dir)
    assert Path(payload["output_paths"]["manifest_path"]).is_relative_to(output_dir)
    repo_outputs = [
        path
        for path in (REPO_ROOT / "artifacts" / "factor_studies").glob("**/*")
        if path.is_file() and path.name not in {"README.md", ".gitkeep"}
    ] if (REPO_ROOT / "artifacts" / "factor_studies").exists() else []
    assert repo_outputs == []


def _env_with_src_path() -> dict[str, str]:
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(SRC_ROOT) if not pythonpath else os.pathsep.join([str(SRC_ROOT), pythonpath])
    )
    return env


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
