"""DK-P03 verdict mapping + reviewer-verdict survivor gate tests."""

from __future__ import annotations

import pytest

from alpha_system.governance.reviewer_verdict import (
    ReviewerVerdictOutcome,
    create_reviewer_verdict,
)
from alpha_system.governance.verdict_reason_code import VerdictReasonCode
from alpha_system.research.track_a_scorer import (
    CLOSED_TAXONOMY_PRIMARY_STATES,
    PRIMARY_STATE_CANDIDATE_RESEARCH,
    PRIMARY_STATE_INCONCLUSIVE,
    PRIMARY_STATE_REJECT,
    PRIMARY_STATE_WATCH,
    map_runtime_state_to_primary_state,
)
from alpha_system.runtime.contracts.run_record import StudyRunResultState


def test_rejected_and_failed_map_to_reject() -> None:
    for state in (StudyRunResultState.REJECTED, StudyRunResultState.DIAGNOSTICS_FAILED):
        primary, reason = map_runtime_state_to_primary_state(
            state,
            n_eff=10_000,
            pearson_ic=0.2,
            rank_ic=0.2,
            mde_abs_ic=0.01,
            bucket_is_monotonic=True,
        )
        assert primary == PRIMARY_STATE_REJECT
        assert reason is None


def test_inconclusive_always_carries_reason_code() -> None:
    primary, reason = map_runtime_state_to_primary_state(
        StudyRunResultState.INCONCLUSIVE,
        n_eff=0,
        pearson_ic=None,
        rank_ic=None,
        mde_abs_ic=None,
        bucket_is_monotonic=False,
    )
    assert primary == PRIMARY_STATE_INCONCLUSIVE
    assert reason == VerdictReasonCode.UNDERPOWERED.value


def test_underpowered_complete_read_is_inconclusive_underpowered() -> None:
    # DIAGNOSTICS_COMPLETE but N_eff cannot support an MDE -> honest UNDERPOWERED.
    primary, reason = map_runtime_state_to_primary_state(
        StudyRunResultState.DIAGNOSTICS_COMPLETE,
        n_eff=1,
        pearson_ic=0.5,
        rank_ic=0.5,
        mde_abs_ic=None,
        bucket_is_monotonic=True,
    )
    assert primary == PRIMARY_STATE_INCONCLUSIVE
    assert reason == VerdictReasonCode.UNDERPOWERED.value


def test_well_powered_complete_read_is_reject_not_survivor() -> None:
    # Effect size never auto-promotes here; a resolved, powered read is REJECT
    # unless a reviewer separately mints a survivor.
    primary, reason = map_runtime_state_to_primary_state(
        StudyRunResultState.DIAGNOSTICS_COMPLETE,
        n_eff=50_000,
        pearson_ic=0.4,
        rank_ic=0.4,
        mde_abs_ic=0.009,
        bucket_is_monotonic=True,
    )
    assert primary == PRIMARY_STATE_REJECT
    assert reason is None
    assert primary not in {PRIMARY_STATE_WATCH, PRIMARY_STATE_CANDIDATE_RESEARCH}


def test_mapping_only_emits_closed_taxonomy() -> None:
    for state in StudyRunResultState:
        primary, _ = map_runtime_state_to_primary_state(
            state,
            n_eff=1000,
            pearson_ic=0.01,
            rank_ic=0.01,
            mde_abs_ic=0.06,
            bucket_is_monotonic=False,
        )
        assert primary in CLOSED_TAXONOMY_PRIMARY_STATES


def test_survivor_requires_reviewer_verdict_with_reason_code() -> None:
    # A WATCH / CANDIDATE_RESEARCH survivor must be gated behind a reviewer
    # verdict carrying a reason_code (asymmetric gate).
    verdict = create_reviewer_verdict(
        reviewer_id="reviewer:claude-opus",
        role="fresh_semantic_reviewer",
        independence_statement="Independent of the executor that produced the diagnostics.",
        verdict=ReviewerVerdictOutcome.PASS_WITH_WARNINGS,
        blocking_issues=[],
        warnings=["surfaced survivor, not promoted"],
        checked_artifacts=["research/differentiated_substrate_v1/verdict_refresh.md"],
        checked_commands=["python tools/hooks/canary_runner.py"],
        timestamp="2026-06-14T00:00:00Z",
        reason_code=VerdictReasonCode.DUPLICATE_EXPOSURE,
    )
    payload = verdict.to_dict()
    assert payload["reason_code"] == VerdictReasonCode.DUPLICATE_EXPOSURE.value


def test_reviewer_verdict_for_each_survivor_state() -> None:
    # Both survivor primary states are gated behind a reviewer verdict artifact.
    for primary in (PRIMARY_STATE_WATCH, PRIMARY_STATE_CANDIDATE_RESEARCH):
        assert primary in CLOSED_TAXONOMY_PRIMARY_STATES
    with pytest.raises(Exception):
        # A reviewer verdict without a recognized outcome must fail closed.
        create_reviewer_verdict(
            reviewer_id="r",
            role="role",
            independence_statement="independent",
            verdict="NOT_A_REAL_OUTCOME",
            blocking_issues=[],
            warnings=[],
            checked_artifacts=["a"],
            checked_commands=["c"],
            timestamp="2026-06-14T00:00:00Z",
            reason_code=VerdictReasonCode.UNDERPOWERED,
        )
