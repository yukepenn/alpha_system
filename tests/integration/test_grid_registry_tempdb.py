from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from alpha_system.experiments.grid_config import GridSpec
from alpha_system.experiments.runner import run_grid


def test_grid_run_records_registry_row_in_tempdb(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    result = run_grid(GridSpec.from_mapping(_payload(tmp_path, registry_path)))

    assert result.registry_written is True
    with sqlite3.connect(registry_path) as connection:
        row = connection.execute(
            """
            SELECT run_id, engine_version, data_version, factor_versions_json,
                   label_versions_json, artifact_paths_json, decision_status
            FROM grid_runs
            """
        ).fetchone()

    assert row[0] == "grid_registry"
    assert row[1] == "strategy_grid_mvp_v1"
    assert row[2] == "data:v1"
    assert json.loads(row[3]) == {"fixture_factor": "v1"}
    assert json.loads(row[4]) == {"fixture_label": "v1"}
    assert "leaderboard_path" in json.loads(row[5])
    assert row[6] == "grid_recorded"


def _payload(tmp_path: Path, registry_path: Path) -> dict[str, object]:
    return {
        "grid_id": "registry",
        "run_id": "grid_registry",
        "strategy_version": "strategy:v1",
        "data_version": "data:v1",
        "factor_versions": {"fixture_factor": "v1"},
        "label_versions": {"fixture_label": "v1"},
        "output_dir": (tmp_path / "grid").as_posix(),
        "registry_path": registry_path.as_posix(),
        "max_combinations": 1,
        "parameter_space": {
            "factor": {"lookback": [2]},
            "strategy": {"direction": ["long"]},
            "risk": {"default_quantity": ["1"]},
            "management": {"eod_flat": [True]},
            "execution": {"fixed_bps": ["1"]},
        },
    }
