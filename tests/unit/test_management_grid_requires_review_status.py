from __future__ import annotations

import pytest

from alpha_system.experiments.management_grid import ManagementGridConfigError, ManagementGridSpec


def test_management_grid_requires_survivor_review_status() -> None:
    payload = _payload()
    survivor = dict(payload["survivors"][0])  # type: ignore[index]
    survivor.pop("review_status")
    payload["survivors"] = [survivor]

    with pytest.raises(ManagementGridConfigError, match="review_status"):
        ManagementGridSpec.from_mapping(payload)


def _payload() -> dict[str, object]:
    return {
        "grid_id": "requires_review_status",
        "run_id": "management_requires_review_status",
        "strategy_version": "strategy:v1",
        "data_version": "data:v1",
        "max_combinations": 1,
        "survivors": [
            {
                "candidate_id": "candidate:review-required",
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
                "source_grid_config_hash": "hash-review-required",
                "survivor_eligibility_reason": "passed diagnostics and baseline review",
                "warnings": [],
                "review_status": "PASS",
                "allowed_management_grid_scope": {
                    "management_parameters": ["management.fixed_stop.stop_pct"],
                    "max_combinations": 1,
                },
            }
        ],
        "parameter_space": {"management": {"fixed_stop.stop_pct": ["0.01"]}},
    }
