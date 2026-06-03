from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"


def test_management_grid_cli_execution_writes_temp_outputs(tmp_path: Path) -> None:
    config_path = tmp_path / "management_grid.json"
    config_path.write_text(json.dumps(_payload(tmp_path), sort_keys=True), encoding="utf-8")
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(SRC_ROOT) if not pythonpath else os.pathsep.join([str(SRC_ROOT), pythonpath])

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alpha_system.cli",
            "management",
            "grid",
            "--config",
            config_path.as_posix(),
            "--json",
        ],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["completed_count"] == 1
    assert Path(payload["output_paths"]["leaderboard_path"]).is_relative_to(tmp_path / "management")


def _payload(tmp_path: Path) -> dict[str, object]:
    return {
        "grid_id": "cli_execution",
        "run_id": "management_cli_execution",
        "strategy_version": "strategy:v1",
        "data_version": "data:v1",
        "output_dir": (tmp_path / "management").as_posix(),
        "max_combinations": 1,
        "survivors": [_survivor()],
        "parameter_space": {
            "management": {"fixed_stop.stop_pct": ["0.01"]},
            "execution": {"fixed_bps": ["1"]},
        },
    }


def _survivor() -> dict[str, object]:
    return {
        "candidate_id": "candidate:cli-execution",
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
        "source_grid_config_hash": "hash-cli-execution",
        "survivor_eligibility_reason": "passed diagnostics and baseline review",
        "warnings": [],
        "review_status": "PASS",
        "allowed_management_grid_scope": {
            "management_parameters": ["management.fixed_stop.stop_pct"],
            "execution_parameters": ["execution.fixed_bps"],
            "max_combinations": 1,
        },
    }
