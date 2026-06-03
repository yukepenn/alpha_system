from __future__ import annotations

import pytest

from alpha_system.experiments.management_grid import (
    ManagementGridConfigError,
    ManagementGridExpansionError,
    ManagementGridSpec,
    expand_management_grid,
)


def test_management_grid_rejects_unbounded_parameter_value() -> None:
    payload = _payload()
    payload["parameter_space"] = {"management": {"fixed_stop.stop_pct": "*"}}

    with pytest.raises(ManagementGridConfigError, match="unbounded"):
        ManagementGridSpec.from_mapping(payload)


def test_management_grid_rejects_open_ended_mapping_without_values() -> None:
    payload = _payload()
    payload["parameter_space"] = {"management": {"fixed_stop.stop_pct": {"start": "0.01"}}}

    with pytest.raises(ManagementGridConfigError, match="explicit values"):
        ManagementGridSpec.from_mapping(payload)


def test_management_grid_limit_error_carries_visible_rejection() -> None:
    with pytest.raises(ManagementGridExpansionError) as error:
        expand_management_grid(
            grid_id="overflow",
            max_combinations=1,
            parameter_space={
                "management": {
                    "fixed_stop.stop_pct": ["0.01", "0.02"],
                    "cooldown.bars": [1],
                }
            },
        )

    assert error.value.count == 2
    assert error.value.max_combinations == 1
    assert error.value.rejected_configs
    assert "expands to 2 combinations" in error.value.rejected_configs[0].reason


def _payload() -> dict[str, object]:
    return {
        "grid_id": "limits",
        "run_id": "management_limits",
        "strategy_version": "strategy:v1",
        "data_version": "data:v1",
        "max_combinations": 2,
        "survivors": [
            {
                "candidate_id": "candidate:limits",
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
                "source_grid_config_hash": "hash-limits",
                "survivor_eligibility_reason": "passed diagnostics and baseline review",
                "warnings": [],
                "review_status": "PASS",
                "allowed_management_grid_scope": {
                    "management_parameters": ["management.fixed_stop.stop_pct"],
                    "max_combinations": 2,
                },
            }
        ],
        "parameter_space": {"management": {"fixed_stop.stop_pct": ["0.01"]}},
    }
