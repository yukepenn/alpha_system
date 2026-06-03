from __future__ import annotations

from pathlib import Path

from alpha_system.experiments.grid_config import GridSpec
from alpha_system.experiments.runner import run_grid


def test_grid_tiny_fixture_runs_deterministically(tmp_path: Path) -> None:
    result = run_grid(GridSpec.from_mapping(_payload(tmp_path)))

    assert result.completed_count == 2
    assert result.rejected_count == 0
    assert Path(result.output_paths.leaderboard_path).read_text(encoding="utf-8").count("\n") == 3


def _payload(tmp_path: Path) -> dict[str, object]:
    return {
        "grid_id": "tiny_fixture",
        "run_id": "grid_tiny_fixture",
        "strategy_version": "strategy:v1",
        "data_version": "data:v1",
        "factor_versions": {"fixture_factor": "v1"},
        "label_versions": {"fixture_label": "v1"},
        "output_dir": (tmp_path / "grid").as_posix(),
        "max_combinations": 2,
        "parameter_space": {
            "factor": {"lookback": [2]},
            "strategy": {"direction": ["long", "short"]},
            "risk": {"default_quantity": ["1"]},
            "management": {"eod_flat": [True]},
            "execution": {"fixed_bps": ["1"]},
        },
    }
