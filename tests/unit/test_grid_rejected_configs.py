from __future__ import annotations

import csv
from pathlib import Path

from alpha_system.experiments.grid_config import GridSpec
from alpha_system.experiments.runner import run_grid


def test_grid_run_writes_rejected_configs_file(tmp_path: Path) -> None:
    result = run_grid(GridSpec.from_mapping(_payload(tmp_path)))

    rows = list(csv.DictReader(Path(result.output_paths.rejected_configs_path).open()))

    assert result.rejected_count == 1
    assert len(rows) == 1
    assert rows[0]["config_id"] == "cfg_000002"
    assert rows[0]["status"] == "rejected"


def _payload(tmp_path: Path) -> dict[str, object]:
    return {
        "grid_id": "rejections",
        "run_id": "grid_rejections",
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
        "rejection_rules": [
            {"when": {"strategy.direction": "short"}, "reason": "short side withheld for review"}
        ],
    }
