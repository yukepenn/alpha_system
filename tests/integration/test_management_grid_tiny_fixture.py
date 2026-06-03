from __future__ import annotations

from pathlib import Path

from alpha_system.experiments.management_grid import ManagementGridSpec, run_management_grid
from alpha_system.experiments.management_outputs import REQUIRED_MANAGEMENT_OUTPUT_FILENAMES


def test_management_grid_tiny_fixture_runs_deterministically(tmp_path: Path) -> None:
    result = run_management_grid(ManagementGridSpec.from_mapping(_payload(tmp_path)))
    output_dir = Path(result.output_paths.output_dir)

    assert result.completed_count == 2
    assert result.rejected_count == 0
    assert sorted(path.name for path in output_dir.iterdir()) == sorted(REQUIRED_MANAGEMENT_OUTPUT_FILENAMES)
    assert Path(result.output_paths.leaderboard_path).read_text(encoding="utf-8").count("\n") == 3


def _payload(tmp_path: Path) -> dict[str, object]:
    return {
        "grid_id": "tiny_fixture",
        "run_id": "management_tiny_fixture",
        "strategy_version": "strategy:v1",
        "data_version": "data:v1",
        "output_dir": (tmp_path / "management").as_posix(),
        "max_combinations": 2,
        "survivors": [_survivor()],
        "parameter_space": {
            "management": {"fixed_stop.stop_pct": ["0.01", "0.02"]},
            "execution": {"fixed_bps": ["1"]},
        },
    }


def _survivor() -> dict[str, object]:
    return {
        "candidate_id": "candidate:tiny-fixture",
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
        "source_grid_config_hash": "hash-tiny-fixture",
        "survivor_eligibility_reason": "passed diagnostics and baseline review",
        "warnings": [],
        "review_status": "PASS",
        "allowed_management_grid_scope": {
            "management_parameters": ["management.fixed_stop.stop_pct"],
            "execution_parameters": ["execution.fixed_bps"],
            "max_combinations": 2,
        },
    }
