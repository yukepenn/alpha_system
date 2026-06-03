from __future__ import annotations

import csv
from pathlib import Path

from alpha_system.experiments.grid_config import GridSpec
from alpha_system.experiments.runner import run_grid


def test_grid_rejected_reason_is_visible(tmp_path: Path) -> None:
    payload = {
        "grid_id": "zero_cost_rejection",
        "run_id": "grid_zero_cost_rejection",
        "strategy_version": "strategy:v1",
        "data_version": "data:v1",
        "factor_versions": {"fixture_factor": "v1"},
        "label_versions": {"fixture_label": "v1"},
        "output_dir": (tmp_path / "grid").as_posix(),
        "max_combinations": 1,
        "parameter_space": {
            "factor": {"lookback": [2]},
            "strategy": {"direction": ["long"]},
            "risk": {"default_quantity": ["1"]},
            "management": {"eod_flat": [True]},
            "execution": {"fixed_bps": ["0"], "minimum_cost": ["0"]},
        },
    }

    result = run_grid(GridSpec.from_mapping(payload))
    rows = list(csv.DictReader(Path(result.output_paths.rejected_configs_path).open()))

    assert result.completed_count == 0
    assert "zero execution cost" in rows[0]["reason"]
