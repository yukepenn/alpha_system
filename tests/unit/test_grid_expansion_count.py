from __future__ import annotations

from alpha_system.experiments.grid import count_grid_combinations, expand_grid
from alpha_system.experiments.grid_config import GridSpec


def test_grid_expansion_counts_all_finite_dimensions() -> None:
    spec = GridSpec.from_mapping(_grid_payload())

    assert spec.combination_count == 4
    assert count_grid_combinations(spec.parameter_space) == 4
    expansion = expand_grid(
        grid_id=spec.grid_id,
        parameter_space=spec.parameter_space,
        max_combinations=spec.max_combinations,
    )

    assert expansion.combination_count == 4
    assert len(expansion.configurations) == 4


def _grid_payload() -> dict[str, object]:
    return {
        "grid_id": "unit_grid",
        "run_id": "grid_unit",
        "strategy_id": "grid_fixture_strategy",
        "strategy_version": "strategy:v1",
        "data_version": "data:v1",
        "factor_versions": {"fixture_factor": "v1"},
        "label_versions": {"fixture_label": "v1"},
        "max_combinations": 4,
        "parameter_space": {
            "factor": {"lookback": [2]},
            "strategy": {"direction": ["long", "short"]},
            "risk": {"default_quantity": ["1"]},
            "management": {"eod_flat": [True]},
            "execution": {"fixed_bps": ["1", "2"]},
        },
    }
