from __future__ import annotations

import csv
from pathlib import Path

from alpha_system.experiments.grid_config import GridSpec
from alpha_system.experiments.runner import run_grid


def test_grid_fast_path_unsupported_features_route_to_reference_fallback(tmp_path: Path) -> None:
    result = run_grid(GridSpec.from_mapping(_payload(tmp_path)))
    rows = list(csv.DictReader(Path(result.output_paths.leaderboard_path).open()))

    assert result.completed_count == 1
    assert rows[0]["engine_requested"] == "fast"
    assert rows[0]["engine_used"] == "reference_fallback"
    assert any("reference fallback" in warning for warning in result.warnings)


def _payload(tmp_path: Path) -> dict[str, object]:
    return {
        "grid_id": "reference_fallback",
        "run_id": "grid_reference_fallback",
        "strategy_version": "strategy:v1",
        "data_version": "data:v1",
        "factor_versions": {"fixture_factor": "v1"},
        "label_versions": {"fixture_label": "v1"},
        "engine": "fast",
        "fast_path_features": ["slippage", "simple_long"],
        "reference_fallback": True,
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
