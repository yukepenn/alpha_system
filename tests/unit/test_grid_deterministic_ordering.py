from __future__ import annotations

from alpha_system.experiments.grid import expand_grid
from alpha_system.experiments.grid_config import GridSpec


def test_grid_expansion_uses_discipline_order_then_parameter_name() -> None:
    spec = GridSpec.from_mapping(
        {
            "grid_id": "ordering",
            "strategy_version": "strategy:v1",
            "data_version": "data:v1",
            "factor_versions": {"fixture_factor": "v1"},
            "label_versions": {"fixture_label": "v1"},
            "max_combinations": 2,
            "parameter_space": {
                "execution": {"minimum_cost": ["0"], "fixed_bps": ["1"]},
                "management": {"eod_flat": [True]},
                "risk": {"default_quantity": ["1"]},
                "strategy": {"direction": ["long"]},
                "factor": {"z_window": [3], "lookback": [2]},
            },
        }
    )

    expansion = expand_grid(
        grid_id=spec.grid_id,
        parameter_space=spec.parameter_space,
        max_combinations=spec.max_combinations,
    )

    assert expansion.parameter_paths == (
        "factor.lookback",
        "factor.z_window",
        "strategy.direction",
        "risk.default_quantity",
        "management.eod_flat",
        "execution.fixed_bps",
        "execution.minimum_cost",
    )
