from __future__ import annotations

import csv
from pathlib import Path

from alpha_system.experiments.grid_config import GridSpec
from alpha_system.experiments.runner import run_grid


def test_grid_fast_path_runs_only_after_parity_gate(tmp_path: Path) -> None:
    result = run_grid(GridSpec.from_mapping(_payload(tmp_path)))
    rows = list(csv.DictReader(Path(result.output_paths.leaderboard_path).open()))

    assert result.completed_count == 1
    assert rows[0]["engine_requested"] == "fast"
    assert rows[0]["engine_used"] == "fast"


def _payload(tmp_path: Path) -> dict[str, object]:
    return {
        "grid_id": "fast_gate",
        "run_id": "grid_fast_gate",
        "strategy_version": "strategy:v1",
        "data_version": "data:v1",
        "factor_versions": {"fixture_factor": "v1"},
        "label_versions": {"fixture_label": "v1"},
        "engine": "fast",
        "fast_path_features": ["simple_long", "trade_summary", "equity_curve", "eod_exit", "costs"],
        "output_dir": (tmp_path / "grid").as_posix(),
        "max_combinations": 1,
        "parameter_space": {
            "factor": {"lookback": [2]},
            "strategy": {"direction": ["long"]},
            "risk": {"default_quantity": ["1"]},
            "management": {"eod_flat": [True]},
            "execution": {"fixed_bps": ["1"]},
        },
    }
