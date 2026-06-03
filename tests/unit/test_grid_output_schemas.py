from __future__ import annotations

import csv
import json
from pathlib import Path

from alpha_system.experiments.grid_config import GridSpec
from alpha_system.experiments.grid_outputs import (
    COST_SENSITIVITY_COLUMNS,
    LEADERBOARD_COLUMNS,
    MONTHLY_BREAKDOWN_COLUMNS,
    REJECTED_CONFIG_COLUMNS,
    REQUIRED_OUTPUT_FILENAMES,
)
from alpha_system.experiments.runner import run_grid


def test_grid_output_files_and_headers_match_schema(tmp_path: Path) -> None:
    result = run_grid(GridSpec.from_mapping(_payload(tmp_path)))
    output_dir = Path(result.output_paths.output_dir)

    assert sorted(path.name for path in output_dir.iterdir()) == sorted(REQUIRED_OUTPUT_FILENAMES)
    assert _header(Path(result.output_paths.leaderboard_path)) == LEADERBOARD_COLUMNS
    assert _header(Path(result.output_paths.monthly_breakdown_path)) == MONTHLY_BREAKDOWN_COLUMNS
    assert _header(Path(result.output_paths.cost_sensitivity_path)) == COST_SENSITIVITY_COLUMNS
    assert _header(Path(result.output_paths.rejected_configs_path)) == REJECTED_CONFIG_COLUMNS
    manifest = json.loads(Path(result.output_paths.manifest_path).read_text(encoding="utf-8"))
    assert manifest["artifact_paths"]["leaderboard_path"] == result.output_paths.leaderboard_path


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))


def _payload(tmp_path: Path) -> dict[str, object]:
    return {
        "grid_id": "schemas",
        "run_id": "grid_schemas",
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
            "execution": {"fixed_bps": ["1"]},
        },
    }
