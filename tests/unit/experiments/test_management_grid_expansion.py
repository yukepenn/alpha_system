from __future__ import annotations

from alpha_system.experiments.management_grid import (
    ManagementGridSpec,
    count_management_grid_combinations,
    expand_management_grid,
)


def test_management_grid_expands_supported_management_dimensions() -> None:
    spec = ManagementGridSpec.from_mapping(_payload())

    assert spec.combination_count == 2
    assert count_management_grid_combinations(spec.parameter_space) == 2
    expansion = expand_management_grid(
        grid_id=spec.grid_id,
        parameter_space=spec.parameter_space,
        max_combinations=spec.max_combinations,
    )

    assert expansion.combination_count == 2
    assert len(expansion.configurations) == 2
    assert expansion.parameter_paths == (
        "management.breakeven_stop.trigger_r",
        "management.cooldown.bars",
        "management.fixed_stop.stop_pct",
        "management.laddered_partial_take_profit.steps",
        "management.max_holding_bars.max_bars",
        "management.target_r_multiple.r_multiple",
        "management.trailing_stop.trail_r",
        "execution.fixed_bps",
    )


def _payload() -> dict[str, object]:
    return {
        "grid_id": "expansion",
        "run_id": "management_expansion",
        "strategy_version": "strategy:v1",
        "data_version": "data:v1",
        "max_combinations": 2,
        "survivors": [_survivor()],
        "parameter_space": {
            "management": {
                "fixed_stop.stop_pct": ["0.01"],
                "target_r_multiple.r_multiple": ["1"],
                "laddered_partial_take_profit.steps": [
                    [{"label": "half_at_1r", "threshold_r": "1", "exit_fraction": "0.5"}]
                ],
                "trailing_stop.trail_r": ["1"],
                "breakeven_stop.trigger_r": ["1"],
                "max_holding_bars.max_bars": [3],
                "cooldown.bars": [1],
            },
            "execution": {"fixed_bps": ["1", "2"]},
        },
    }


def _survivor() -> dict[str, object]:
    return {
        "candidate_id": "candidate:expansion",
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
        "source_grid_config_hash": "hash-expansion",
        "survivor_eligibility_reason": "passed diagnostics and baseline review",
        "warnings": [],
        "review_status": "PASS_WITH_WARNINGS",
        "allowed_management_grid_scope": {
            "management_parameters": [
                "management.fixed_stop.stop_pct",
                "management.target_r_multiple.r_multiple",
                "management.laddered_partial_take_profit.steps",
                "management.trailing_stop.trail_r",
                "management.breakeven_stop.trigger_r",
                "management.max_holding_bars.max_bars",
                "management.cooldown.bars",
            ],
            "execution_parameters": ["execution.fixed_bps"],
            "max_combinations": 2,
        },
    }
