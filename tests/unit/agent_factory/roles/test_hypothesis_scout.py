from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from alpha_system.agent_factory.queue.models import (
    AgentAssignment,
    ComputeBudget,
    DatasetVersionState,
    ResearchBudget,
    ResearchPartition,
    ResearchTask,
    ResearchTaskStatus,
    RetryPolicy,
    ReviewRequirement,
    VariantBudget,
)
from alpha_system.agent_factory.roles import registry as registry_module
from alpha_system.agent_factory.roles.hypothesis_scout import (
    ALLOWED_TRANSITIONS,
    BRANCH_OR_TERMINAL_STATES,
    CALLABLE_TOOL_IDS,
    DEFAULT_LIMITATIONS,
    NEXT_REVIEW_GATE,
    ROLE_ID,
    AgentHandoff,
    AlphaSpecDraftRef,
    RejectionReasonRecordRef,
    blocked_missing_task_result,
    build_draft_tool_result,
    build_handoff,
    inputs_blocked_result,
    permission_matrix_entry,
    surface_prior_rejections,
    validate_draft_batch,
)
from alpha_system.agent_factory.tools.results import AgentToolResult, AgentToolStatus


def test_import_self_registers_without_shared_role_module_edits() -> None:
    module = importlib.import_module("alpha_system.agent_factory.roles.hypothesis_scout")

    assert registry_module.get(ROLE_ID) is module.HypothesisScout
    assert ROLE_ID in registry_module.role_ids()

    package_text = Path("src/alpha_system/agent_factory/roles/__init__.py").read_text(
        encoding="utf-8",
    )
    registry_text = Path("src/alpha_system/agent_factory/roles/registry.py").read_text(
        encoding="utf-8",
    )
    assert "hypothesis_scout" not in package_text
    assert "hypothesis_scout" not in registry_text


def test_contract_populates_every_required_role_field() -> None:
    role = registry_module.get(ROLE_ID)

    assert role.name == "Hypothesis Scout"
    assert role.purpose
    assert role.readable_inputs
    assert role.callable_tools == CALLABLE_TOOL_IDS
    assert role.producible_outputs
    assert role.allowed_decisions
    assert role.forbidden_decisions
    assert role.handoff_format
    assert role.reviewer_independence
    assert role.failure_modes
    assert "read_only_rejected_idea_memory_summaries" in role.readable_inputs
    assert "consulted_prior_rejection_reason_refs" in role.handoff_format


def test_decision_bounds_and_permission_matrix_linkage_are_fail_closed() -> None:
    role = registry_module.get(ROLE_ID)
    permissions = permission_matrix_entry()

    assert permissions.role_id == ROLE_ID
    assert tuple(permissions.tool.allowed_tool_ids) == role.callable_tools
    assert permissions.write.allowed_scopes == ("alphaspec.draft",)
    assert not permissions.write.direct_registry_write
    assert not permissions.review.can_issue_verdict
    assert not permissions.promotion.can_promote
    assert not permissions.data.raw_provider_access
    assert not permissions.data.allowed_scopes

    forbidden_text = " ".join(role.forbidden_decisions)
    for denied in (
        "approve_own_alphaspec",
        "critique_own_alphaspec",
        "implement_code",
        "run_diagnostics",
        "resolve_or_select_datasets",
        "write_any_registry",
        "promote_candidate",
        "exceed_variant_budget",
    ):
        assert denied in forbidden_text

    assert "draft_alphaspec_content_within_task_family" in role.allowed_decisions
    assert "runtime.run_diagnostics" not in permissions.tool.allowed_tool_ids
    assert "registry.resolve_dataset_version" not in permissions.tool.allowed_tool_ids


def test_draft_count_is_three_to_five_and_respects_variant_budget() -> None:
    task = synthetic_task(max_variants=5)

    assert validate_draft_batch(synthetic_drafts(3), task) == synthetic_drafts(3)
    assert validate_draft_batch(synthetic_drafts(5), task) == synthetic_drafts(5)

    with pytest.raises(ValueError, match="between 3 and 5"):
        validate_draft_batch(synthetic_drafts(2), task)

    with pytest.raises(ValueError, match="between 3 and 5"):
        validate_draft_batch(synthetic_drafts(6), task)

    with pytest.raises(ValueError, match="VariantBudget"):
        validate_draft_batch(synthetic_drafts(5), synthetic_task(max_variants=4))


def test_value_free_tool_result_handoff_and_drafts_reject_raw_payloads() -> None:
    task = synthetic_task(max_variants=5)
    assignment = synthetic_assignment()
    drafts = synthetic_drafts(3)

    tool_result = build_draft_tool_result(
        request_id="request_scout_001",
        task=task,
        assignment=assignment,
        drafts=drafts,
    )
    assert isinstance(tool_result, AgentToolResult)
    assert tool_result.status is AgentToolStatus.OK
    assert tool_result.role == ROLE_ID
    assert tool_result.alpha_spec_id == drafts[0].alpha_spec_id
    assert tool_result.dataset_version_id == task.allowed_dataset_version_id
    assert tool_result.runtime_run_id is None
    assert tool_result.next_required_gate == NEXT_REVIEW_GATE
    assert tool_result.artifacts == tuple(
        f"alphaspec_draft_ref:{draft.alpha_spec_id}" for draft in drafts
    )
    assert tool_result.limitations == DEFAULT_LIMITATIONS

    handoff = build_handoff(
        request_id="request_scout_001",
        task=task,
        assignment=assignment,
        drafts=drafts,
        tool_result=tool_result,
    )
    assert isinstance(handoff, AgentHandoff)
    assert handoff.alpha_spec_ids == tuple(draft.alpha_spec_id for draft in drafts)
    assert handoff.target_task_status == ResearchTaskStatus.ALPHASPEC_DRAFTED.value
    assert handoff.next_required_gate == NEXT_REVIEW_GATE

    with pytest.raises(ValueError, match="forbidden raw/heavy"):
        AlphaSpecDraftRef(
            alpha_spec_id="aspec_bad_raw_payload",
            task_id=task.task_id,
            assignment_id=assignment.assignment_id,
            alpha_family="microstructure",
            idea_fingerprint="idea_bad_payload",
            summary="raw_payload",
        )

    with pytest.raises(ValueError, match="forbidden heavy"):
        RejectionReasonRecordRef(
            record_ref="rejection_reason_bad",
            rejected_idea_ref="aspec_bad",
            idea_fingerprint="idea_bad_heavy",
            reason_category="duplicate",
            summary="synthetic report pointer example.parquet",
        )


def test_duplicate_prior_rejection_is_surfaced_not_silent() -> None:
    task = synthetic_task(max_variants=5)
    assignment = synthetic_assignment()
    duplicate_record = RejectionReasonRecordRef(
        record_ref="rejection_reason_001",
        rejected_idea_ref="aspec_rejected_001",
        idea_fingerprint="idea_scout_1",
        reason_category="duplicate",
        summary="Synthetic prior duplicate reason.",
    )
    drafts = synthetic_drafts(3)

    surfaced = surface_prior_rejections(drafts[0], (duplicate_record,))
    assert surfaced.prior_rejection_reason_refs == ("rejection_reason_001",)

    tool_result = build_draft_tool_result(
        request_id="request_scout_duplicate_001",
        task=task,
        assignment=assignment,
        drafts=drafts,
        prior_rejections=(duplicate_record,),
    )
    assert tool_result.status is AgentToolStatus.WARN
    assert tool_result.rejection_reasons == ("rejection_reason_001",)
    assert tool_result.next_required_gate == "alpha_spec_critic_duplicate_review"

    handoff = build_handoff(
        request_id="request_scout_duplicate_001",
        task=task,
        assignment=assignment,
        drafts=drafts,
        tool_result=tool_result,
    )
    assert handoff.consulted_rejection_reason_refs == ("rejection_reason_001",)


def test_failure_modes_return_blocked_or_inputs_blocked_shapes() -> None:
    missing_task = blocked_missing_task_result("request_missing_task")
    assert missing_task.status is AgentToolStatus.BLOCKED
    assert missing_task.blocking_findings == ("missing_scoped_task_or_assignment",)
    assert missing_task.next_required_gate == "research_director_scope_task"

    unavailable_inputs = inputs_blocked_result(
        "request_inputs_blocked",
        ("memory.lookup_rejected_ideas", "library.summarize_prior_work"),
    )
    assert unavailable_inputs.status is AgentToolStatus.BLOCKED
    assert unavailable_inputs.blocking_findings == (
        "inputs_blocked:memory.lookup_rejected_ideas",
        "inputs_blocked:library.summarize_prior_work",
    )
    assert unavailable_inputs.next_required_gate == "operator_restore_value_free_memory_summaries"


def test_no_prohibited_states_or_positive_claim_surface() -> None:
    from alpha_system.agent_factory.queue.models import PROHIBITED_MVP_TASK_STATUSES

    reachable_states = {
        state
        for transition in ALLOWED_TRANSITIONS
        for state in transition
    }.union(BRANCH_OR_TERMINAL_STATES)
    assert not reachable_states.intersection(PROHIBITED_MVP_TASK_STATUSES)

    role = registry_module.get(ROLE_ID)
    allowed_surface = " ".join(
        (
            role.purpose,
            *role.producible_outputs,
            *role.allowed_decisions,
            *role.handoff_format,
            *role.reviewer_independence,
        )
    ).lower()
    for positive_claim in (
        "profitable",
        "production_ready",
        "paper_ready",
        "live_ready",
        "factor_promoted",
        "strategy_ready",
        "portfolio_ready",
        "candidate_promoted",
    ):
        assert positive_claim not in allowed_surface
    assert "claim_alpha_profitability_tradability" in role.forbidden_decisions


def synthetic_assignment() -> AgentAssignment:
    return AgentAssignment(
        assignment_id="assignment_scout_001",
        task_id="task_scout_001",
        role_id=ROLE_ID,
        assignment_scope_ref="scope_scout_001",
    )


def synthetic_task(*, max_variants: int) -> ResearchTask:
    assignment = synthetic_assignment()
    return ResearchTask(
        task_id="task_scout_001",
        task_status=ResearchTaskStatus.HYPOTHESIS_DRAFTED,
        allowed_alpha_family=("microstructure",),
        allowed_dataset_version_id="dataset_version_synthetic_001",
        allowed_dataset_version_state=DatasetVersionState.READY_FOR_RESEARCH,
        allowed_feature_pack_refs=("feature_pack_synthetic_001",),
        allowed_label_pack_refs=("label_pack_synthetic_001",),
        allowed_partitions=(ResearchPartition.DEVELOPMENT, ResearchPartition.VALIDATION),
        blocked_partitions=(),
        research_budget=ResearchBudget(
            variant_budget=VariantBudget(max_variants=max_variants),
            compute_budget=ComputeBudget(max_runtime_minutes=30),
        ),
        review_requirements=(
            ReviewRequirement(
                review_id="review_alphaspec_001",
                review_kind="alphaspec_critique",
                reviewer_role_id="alpha_spec_critic",
                independent_from_role_ids=(ROLE_ID,),
                required_before_status=ResearchTaskStatus.ALPHASPEC_CRITIQUED,
            ),
        ),
        retry_policy=RetryPolicy(max_attempts=0, retry_on_statuses=()),
        next_action="hypothesis_scout_draft",
        assignments=(assignment,),
    )


def synthetic_drafts(count: int) -> tuple[AlphaSpecDraftRef, ...]:
    return tuple(
        AlphaSpecDraftRef(
            alpha_spec_id=f"aspec_scout_{index}",
            task_id="task_scout_001",
            assignment_id="assignment_scout_001",
            alpha_family="microstructure",
            idea_fingerprint=f"idea_scout_{index}",
            summary=f"Synthetic value-free AlphaSpec draft {index}.",
        )
        for index in range(1, count + 1)
    )
