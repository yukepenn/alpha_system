from __future__ import annotations

import pytest

from alpha_system.experiments.candidate_policy import (
    CandidateEligibilityError,
    assert_candidate_eligible,
    evaluate_candidate_eligibility,
)
from alpha_system.experiments.survivors import SurvivorRecord


def test_survivor_eligibility_gate_accepts_reviewed_in_scope_candidate() -> None:
    survivor = SurvivorRecord.from_mapping(_survivor())

    decision = evaluate_candidate_eligibility(
        survivor,
        parameter_paths=("management.fixed_stop.stop_pct", "execution.fixed_bps"),
        max_combinations=2,
    )

    assert decision.eligible is True
    assert decision.reasons == ()


def test_survivor_eligibility_gate_rejects_out_of_scope_parameter() -> None:
    survivor = SurvivorRecord.from_mapping(_survivor())

    with pytest.raises(CandidateEligibilityError) as error:
        assert_candidate_eligible(
            survivor,
            parameter_paths=("management.trailing_stop.trail_r",),
            max_combinations=2,
        )

    assert "requested parameters exceed survivor scope" in str(error.value)


def _survivor() -> dict[str, object]:
    return {
        "candidate_id": "candidate:gate",
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
        "source_grid_config_hash": "hash-gate",
        "survivor_eligibility_reason": "passed diagnostics and baseline review",
        "warnings": [],
        "review_status": "PASS_WITH_WARNINGS",
        "allowed_management_grid_scope": {
            "management_parameters": ["management.fixed_stop.stop_pct"],
            "execution_parameters": ["execution.fixed_bps"],
            "max_combinations": 2,
        },
    }
