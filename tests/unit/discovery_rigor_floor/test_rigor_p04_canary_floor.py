from __future__ import annotations

from copy import deepcopy

from alpha_system.governance.canaries import (
    EXECUTABLE_NEGATIVE_CONTROL_TYPES,
    REQUIRED_NEGATIVE_CONTROL_TYPES,
    NegativeControlPassFail,
    NegativeControlType,
    load_default_planted_fake_alpha_fixture,
    run_planted_fake_alpha_canary,
)
from tools.hooks.canary_runner import scenarios


def test_required_negative_controls_are_four_executable_in_catalog_order() -> None:
    assert tuple(control.value for control in EXECUTABLE_NEGATIVE_CONTROL_TYPES) == (
        REQUIRED_NEGATIVE_CONTROL_TYPES
    )
    assert EXECUTABLE_NEGATIVE_CONTROL_TYPES[0] is NegativeControlType.RANDOM_TARGET


def test_planted_fake_alpha_canary_rejects_contaminated_study(tmp_path) -> None:
    result = run_planted_fake_alpha_canary(workspace=tmp_path)

    assert result.rejected is True
    assert result.promotion_outcome == "REJECTED"
    assert result.blocked_gate == "DIAGNOSTICS_RUN->EVIDENCE_READY"
    assert result.blocked_issue_code == "locked_test_contamination_blocks_evidence_ready"
    assert "bar t+1" in result.contamination_mechanism
    assert result.negative_control_result.pass_fail is NegativeControlPassFail.PASS
    assert result.negative_control_result.canary_type is NegativeControlType.FUTURE_SHIFT


def test_decontaminated_planted_fixture_fails_the_canary(tmp_path) -> None:
    fixture = deepcopy(dict(load_default_planted_fake_alpha_fixture()))
    fixture["lookahead_k"] = 0
    labels = fixture["labels"]
    for label in labels:
        label["source_bar_id"] = label["bar_id"]
        label["lookahead_k"] = 0
        label["construction"] = "label_at_t_uses_current_bar_information"

    result = run_planted_fake_alpha_canary(fixture, workspace=tmp_path)

    assert result.rejected is False
    assert result.promotion_outcome == "SURVIVED"
    assert result.negative_control_result.pass_fail is NegativeControlPassFail.FAIL


def test_canary_runner_registers_random_target_and_planted_fake_alpha() -> None:
    by_name = {canary.name: canary for canary in scenarios()}

    assert "governance_random_target" in by_name
    assert by_name["governance_random_target"].expect_block is False
    assert "planted_fake_alpha" in by_name
    assert by_name["planted_fake_alpha"].expect_block is True
