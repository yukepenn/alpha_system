from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from alpha_system.experiments.ml import MLRunSpec, run_ml_experiment


def test_ml_run_records_registry_row_in_tempdb(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    output_dir = tmp_path / "ml"

    result = run_ml_experiment(
        MLRunSpec.from_mapping(_payload(output_dir=output_dir, registry_path=registry_path))
    )

    assert result.registry_written is True
    with sqlite3.connect(registry_path) as connection:
        row = connection.execute(
            """
            SELECT run_id, engine_version, data_version, factor_versions_json,
                   label_versions_json, artifact_paths_json, decision_status
            FROM ml_runs
            """
        ).fetchone()

    assert row[0] == "ml_registry"
    assert row[1] == "ml_factor_combination_mvp_v1"
    assert row[2] == "data:v1"
    assert json.loads(row[3]) == {"momentum_3": "factor:v1", "reversal_2": "factor:v1"}
    assert json.loads(row[4]) == {"forward_return_1": "label:v1"}
    assert "manifest_path" in json.loads(row[5])
    assert row[6] == "ml_recorded"


def _payload(*, output_dir: Path, registry_path: Path) -> dict[str, object]:
    return {
        "run_id": "ml_registry",
        "output_dir": output_dir.as_posix(),
        "registry_path": registry_path.as_posix(),
        "feature_set": {
            "feature_set_id": "fixture",
            "data_version": "data:v1",
            "factor_versions": {"momentum_3": "factor:v1", "reversal_2": "factor:v1"},
            "features": [{"factor_id": "momentum_3"}, {"factor_id": "reversal_2"}],
        },
        "label_spec": {"label_id": "forward_return_1", "label_version": "label:v1"},
        "model_spec": {
            "model_id": "ridge",
            "model_type": "ridge_baseline",
            "parameters": {"ridge_l2": 0.1},
        },
        "split": {"split_type": "train_validation", "validation_fraction": 0.34},
        "observations": [
            {
                "instrument": "SYNTH",
                "decision_ts": "2026-01-02T10:00:00Z",
                "label_available_ts": "2026-01-02T09:59:00Z",
                "momentum_3": 0.1,
                "reversal_2": -0.2,
                "forward_return_1": 0.01,
            },
            {
                "instrument": "SYNTH",
                "decision_ts": "2026-01-02T10:01:00Z",
                "label_available_ts": "2026-01-02T10:00:00Z",
                "momentum_3": 0.2,
                "reversal_2": -0.1,
                "forward_return_1": 0.02,
            },
            {
                "instrument": "SYNTH",
                "decision_ts": "2026-01-02T10:02:00Z",
                "label_available_ts": "2026-01-02T10:01:00Z",
                "momentum_3": -0.1,
                "reversal_2": 0.2,
                "forward_return_1": -0.01,
            },
            {
                "instrument": "SYNTH",
                "decision_ts": "2026-01-02T10:03:00Z",
                "label_available_ts": "2026-01-02T10:02:00Z",
                "momentum_3": 0.3,
                "reversal_2": -0.3,
                "forward_return_1": 0.03,
            },
            {
                "instrument": "SYNTH",
                "decision_ts": "2026-01-02T10:04:00Z",
                "label_available_ts": "2026-01-02T10:03:00Z",
                "momentum_3": -0.2,
                "reversal_2": 0.1,
                "forward_return_1": -0.02,
            },
            {
                "instrument": "SYNTH",
                "decision_ts": "2026-01-02T10:05:00Z",
                "label_available_ts": "2026-01-02T10:04:00Z",
                "momentum_3": 0.4,
                "reversal_2": -0.4,
                "forward_return_1": 0.04,
            },
        ],
    }
