from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from alpha_system.experiments.management_grid import ManagementGridSpec, run_management_grid


def test_management_grid_records_registry_row_in_tempdb(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    result = run_management_grid(ManagementGridSpec.from_mapping(_payload(tmp_path, registry_path)))

    assert result.registry_written is True
    with sqlite3.connect(registry_path) as connection:
        row = connection.execute(
            """
            SELECT run_id, engine_version, data_version, factor_versions_json,
                   label_versions_json, artifact_paths_json, decision_status
            FROM grid_runs
            """
        ).fetchone()

    assert row[0] == "management_registry"
    assert row[1] == "management_grid_v1"
    assert row[2] == "data:v1"
    assert json.loads(row[3]) == {"fixture_factor": "v1"}
    assert json.loads(row[4]) == {"fixture_label": "v1"}
    assert "leaderboard_path" in json.loads(row[5])
    assert row[6] == "management_grid_recorded"


def _payload(tmp_path: Path, registry_path: Path) -> dict[str, object]:
    return {
        "grid_id": "registry",
        "run_id": "management_registry",
        "strategy_version": "strategy:v1",
        "data_version": "data:v1",
        "output_dir": (tmp_path / "management").as_posix(),
        "registry_path": registry_path.as_posix(),
        "max_combinations": 1,
        "survivors": [_survivor()],
        "parameter_space": {
            "management": {"fixed_stop.stop_pct": ["0.01"]},
            "execution": {"fixed_bps": ["1"]},
        },
    }


def _survivor() -> dict[str, object]:
    return {
        "candidate_id": "candidate:registry",
        "source_run_id": "grid_source",
        "factor_versions": {"fixture_factor": "v1"},
        "label_versions": {"fixture_label": "v1"},
        "strategy_version": "strategy:v1",
        "baseline_management_config": {
            "management_id": "management:baseline",
            "fixed_stop": {"enabled": True, "stop_pct": "0.02"},
            "eod_exit": True,
        },
        "baseline_portfolio_config": {"portfolio_id": "portfolio:baseline"},
        "source_grid_config_hash": "hash-registry",
        "survivor_eligibility_reason": "passed diagnostics and baseline review",
        "warnings": [],
        "review_status": "PASS",
        "allowed_management_grid_scope": {
            "management_parameters": ["management.fixed_stop.stop_pct"],
            "execution_parameters": ["execution.fixed_bps"],
            "max_combinations": 1,
        },
    }
