from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest

from alpha_system.agent_factory.permissions.matrix import (
    HUMAN_APPROVAL_ACTIONS,
    PERMISSIONS_BY_ROLE_ID,
    RED_LANE_ACTIONS,
    ROSTER_ROLE_IDS,
)
from alpha_system.agent_factory.permissions.model import HumanApprovalRequired
from alpha_system.agent_factory.separation.enforcement import (
    GENERATOR_APPROVER_RULE,
    HUMAN_RESERVED_FLAGS_RULE,
    IMPLEMENTER_REVIEWER_RULE,
    LIBRARIAN_VERDICT_RULE,
    PERMISSION_MATRIX_COVERAGE_RULE,
    PROMOTION_PERMISSION_RULE,
    REVIEWER_ASSIGNMENT_RULE,
    SeparationRuleResult,
    SeparationStatus,
    check_generator_approver_separation,
    check_human_reserved_flags_preserved,
    check_implementer_reviewer_separation,
    check_librarian_verdict_required,
    check_no_promotion_permission,
    check_permission_matrix_coverage,
    check_reviewer_assignment_independent,
    overall_status,
)


def test_rule_result_is_structured_value_free() -> None:
    result = SeparationRuleResult.passed(
        GENERATOR_APPROVER_RULE,
        ("hypothesis_scout", "alpha_spec_critic"),
        "alphaspec_draft generator and approver are independent roles",
    )

    assert result.rule_id == GENERATOR_APPROVER_RULE
    assert result.status is SeparationStatus.PASS
    assert result.role_ids == ("hypothesis_scout", "alpha_spec_critic")
    assert result.is_pass
    assert not result.is_blocked


def test_rule_result_rejects_payload_markers() -> None:
    with pytest.raises(ValueError):
        SeparationRuleResult.blocked(
            GENERATOR_APPROVER_RULE,
            ("hypothesis_scout",),
            "blocked by data/raw/example",
        )


def test_generator_cannot_approve_own_artifact() -> None:
    passing = check_generator_approver_separation(
        "alphaspec_draft",
        "hypothesis_scout",
        "alpha_spec_critic",
        known_role_ids=ROSTER_ROLE_IDS,
    )
    blocked = check_generator_approver_separation(
        "alphaspec_draft",
        "hypothesis_scout",
        "hypothesis_scout",
        known_role_ids=ROSTER_ROLE_IDS,
    )

    assert passing.status is SeparationStatus.PASS
    assert blocked.status is SeparationStatus.BLOCKED
    assert blocked.rule_id == GENERATOR_APPROVER_RULE


def test_generator_approver_rule_fails_closed_on_missing_inputs() -> None:
    result = check_generator_approver_separation(
        "",
        "hypothesis_scout",
        "alpha_spec_critic",
        known_role_ids=ROSTER_ROLE_IDS,
    )

    assert result.status is SeparationStatus.BLOCKED


def test_implementer_cannot_review_own_work() -> None:
    passing = check_implementer_reviewer_separation(
        "runtime_evidence",
        "diagnostics_runner",
        "statistical_reviewer",
        known_role_ids=ROSTER_ROLE_IDS,
    )
    blocked = check_implementer_reviewer_separation(
        "runtime_evidence",
        "diagnostics_runner",
        "diagnostics_runner",
        known_role_ids=ROSTER_ROLE_IDS,
    )

    assert passing.status is SeparationStatus.PASS
    assert blocked.status is SeparationStatus.BLOCKED
    assert blocked.rule_id == IMPLEMENTER_REVIEWER_RULE


def test_implementer_reviewer_rule_fails_closed_on_unknown_role() -> None:
    result = check_implementer_reviewer_separation(
        "runtime_evidence",
        "unknown_reviewer",
        "statistical_reviewer",
        known_role_ids=ROSTER_ROLE_IDS,
    )

    assert result.status is SeparationStatus.BLOCKED


def test_no_role_may_hold_promotion_permission() -> None:
    passing = check_no_promotion_permission(
        PERMISSIONS_BY_ROLE_ID,
        expected_role_ids=ROSTER_ROLE_IDS,
    )
    promoted_runner = SimpleNamespace(
        role_id="diagnostics_runner",
        promotion=SimpleNamespace(can_promote=True),
    )
    blocked = check_no_promotion_permission(
        {"diagnostics_runner": promoted_runner},
        expected_role_ids=("diagnostics_runner",),
    )

    assert passing.status is SeparationStatus.PASS
    assert blocked.status is SeparationStatus.BLOCKED
    assert blocked.rule_id == PROMOTION_PERMISSION_RULE
    assert blocked.role_ids == ("diagnostics_runner",)


def test_promotion_rule_fails_closed_on_missing_matrix_entry() -> None:
    result = check_no_promotion_permission({}, expected_role_ids=("diagnostics_runner",))

    assert result.status is SeparationStatus.BLOCKED


def test_reviewer_assignment_cannot_equal_implementer() -> None:
    passing = check_reviewer_assignment_independent(
        "runtime_evidence_review",
        "diagnostics_runner",
        "statistical_reviewer",
        known_role_ids=ROSTER_ROLE_IDS,
    )
    blocked = check_reviewer_assignment_independent(
        "runtime_evidence_review",
        "diagnostics_runner",
        "diagnostics_runner",
        known_role_ids=ROSTER_ROLE_IDS,
    )

    assert passing.status is SeparationStatus.PASS
    assert blocked.status is SeparationStatus.BLOCKED
    assert blocked.rule_id == REVIEWER_ASSIGNMENT_RULE


def test_reviewer_assignment_rule_fails_closed_on_missing_known_roles() -> None:
    result = check_reviewer_assignment_independent(
        "runtime_evidence_review",
        "diagnostics_runner",
        "statistical_reviewer",
        known_role_ids=None,
    )

    assert result.status is SeparationStatus.BLOCKED


def test_librarian_write_requires_bound_reviewer_verdict() -> None:
    passing = check_librarian_verdict_required(
        "librarian",
        "decision_ledger.record_after_verdict",
        "reviewer_verdict:required",
        known_role_ids=ROSTER_ROLE_IDS,
    )
    blocked = check_librarian_verdict_required(
        "librarian",
        "decision_ledger.record_after_verdict",
        None,
        known_role_ids=ROSTER_ROLE_IDS,
    )

    assert passing.status is SeparationStatus.PASS
    assert blocked.status is SeparationStatus.BLOCKED
    assert blocked.rule_id == LIBRARIAN_VERDICT_RULE


def test_librarian_rule_fails_closed_when_role_is_not_librarian() -> None:
    result = check_librarian_verdict_required(
        "statistical_reviewer",
        "decision_ledger.record_after_verdict",
        "reviewer_verdict:required",
        known_role_ids=ROSTER_ROLE_IDS,
    )

    assert result.status is SeparationStatus.BLOCKED


def test_permission_matrix_coverage_requires_complete_entry_per_role() -> None:
    passing = check_permission_matrix_coverage(
        ROSTER_ROLE_IDS,
        PERMISSIONS_BY_ROLE_ID,
        expected_role_ids=ROSTER_ROLE_IDS,
    )
    incomplete = dict(PERMISSIONS_BY_ROLE_ID)
    incomplete.pop("librarian")
    blocked = check_permission_matrix_coverage(
        ROSTER_ROLE_IDS,
        incomplete,
        expected_role_ids=ROSTER_ROLE_IDS,
    )

    assert passing.status is SeparationStatus.PASS
    assert blocked.status is SeparationStatus.BLOCKED
    assert blocked.rule_id == PERMISSION_MATRIX_COVERAGE_RULE


def test_human_reserved_flags_must_be_preserved() -> None:
    passing = check_human_reserved_flags_preserved(
        PERMISSIONS_BY_ROLE_ID,
        expected_role_ids=ROSTER_ROLE_IDS,
        required_human_actions=HUMAN_APPROVAL_ACTIONS,
        required_red_lane_actions=RED_LANE_ACTIONS,
    )
    weakened = dict(PERMISSIONS_BY_ROLE_ID)
    weakened["librarian"] = replace(
        PERMISSIONS_BY_ROLE_ID["librarian"],
        human_approval=HumanApprovalRequired(("risk_judgment",)),
    )
    blocked = check_human_reserved_flags_preserved(
        weakened,
        expected_role_ids=ROSTER_ROLE_IDS,
        required_human_actions=HUMAN_APPROVAL_ACTIONS,
        required_red_lane_actions=RED_LANE_ACTIONS,
    )

    assert passing.status is SeparationStatus.PASS
    assert blocked.status is SeparationStatus.BLOCKED
    assert blocked.rule_id == HUMAN_RESERVED_FLAGS_RULE


def test_overall_status_blocks_empty_or_any_blocked_result() -> None:
    passing = check_generator_approver_separation(
        "alphaspec_draft",
        "hypothesis_scout",
        "alpha_spec_critic",
        known_role_ids=ROSTER_ROLE_IDS,
    )
    blocked = check_generator_approver_separation(
        "alphaspec_draft",
        "hypothesis_scout",
        "hypothesis_scout",
        known_role_ids=ROSTER_ROLE_IDS,
    )

    assert overall_status(()) is SeparationStatus.BLOCKED
    assert overall_status((passing,)) is SeparationStatus.PASS
    assert overall_status((passing, blocked)) is SeparationStatus.BLOCKED
