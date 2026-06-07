from __future__ import annotations

from pathlib import Path

import pytest

from alpha_system.agent_factory.dry_run.harness import (
    AGENT_DRY_RUN_ROLE_ROUTE,
    DRY_RUN_TERMINAL_STATES,
    MAX_DRY_RUN_FORWARD_STATE,
    PERMITTED_STATISTICAL_DRY_RUN_VERDICTS,
    run_agent_dry_run,
    validate_dry_run_report,
)
from alpha_system.agent_factory.memory.models import (
    RejectedIdeaMemoryRecord,
    RejectedIdeaMemoryStatus,
    ResearchMemoryRecord,
    ResearchMemoryStatus,
)
from alpha_system.agent_factory.permissions.matrix import ROSTER_ROLE_IDS, permission_for
from alpha_system.agent_factory.queue.models import (
    PROHIBITED_MVP_TASK_STATUSES,
    ResearchTaskStatus,
)
from alpha_system.agent_factory.records.models import AgentHandoff, ToolInvocationRecord
from alpha_system.agent_factory.separation.enforcement import (
    GENERATOR_APPROVER_RULE,
    IMPLEMENTER_REVIEWER_RULE,
    LIBRARIAN_VERDICT_RULE,
    REVIEWER_ASSIGNMENT_RULE,
    SeparationStatus,
)
from alpha_system.agent_factory.tools.results import (
    FORBIDDEN_HEAVY_SUFFIXES,
    FORBIDDEN_RESULT_MARKERS,
    AgentToolResult,
    AgentToolStatus,
)


def test_dry_run_routes_one_bounded_task_end_to_end_without_promotion() -> None:
    report = run_agent_dry_run()

    assert validate_dry_run_report(report) is report
    assert report.role_route == AGENT_DRY_RUN_ROLE_ROUTE
    assert set(report.role_route) == set(ROSTER_ROLE_IDS)
    assert len(report.queue.tasks) == 1
    assert report.task.research_budget.variant_budget.max_variants == 5
    assert report.task.research_budget.compute_budget.max_runtime_minutes == 30
    assert report.task.allowed_alpha_family == ("microstructure",)
    assert report.terminal_state in DRY_RUN_TERMINAL_STATES
    assert report.terminal_state is ResearchTaskStatus.REJECTED
    assert report.max_forward_state is MAX_DRY_RUN_FORWARD_STATE
    assert ResearchTaskStatus.REFERENCE_HANDOFF_RECORDED in report.reachable_task_statuses
    assert ResearchTaskStatus.LIBRARIAN_MEMORY_RECORDED not in report.reachable_task_statuses
    assert not {state.value for state in report.reachable_task_statuses}.intersection(
        PROHIBITED_MVP_TASK_STATUSES
    )

    assert tuple(result.role for result in report.tool_results) == AGENT_DRY_RUN_ROLE_ROUTE
    assert report.result_for_role("statistical_reviewer").status is AgentToolStatus.REJECTED


def test_separation_permissions_and_handoffs_are_exercised() -> None:
    report = run_agent_dry_run()

    assert report.separation_bundle.status is SeparationStatus.PASS
    assert not report.separation_bundle.blocked_results
    assert all(not permission_for(role_id).promotion.can_promote for role_id in report.role_route)

    rule_ids = {
        result.rule_id
        for decision in report.decision_records
        for result in decision.separation_results
    }
    assert {
        GENERATOR_APPROVER_RULE,
        IMPLEMENTER_REVIEWER_RULE,
        REVIEWER_ASSIGNMENT_RULE,
        LIBRARIAN_VERDICT_RULE,
    } <= rule_ids

    assert report.scout_handoff.target_task_status == ResearchTaskStatus.ALPHASPEC_DRAFTED.value
    assert report.scout_handoff.consulted_rejection_reason_refs == (
        "rejection_reason:prior_duplicate",
    )

    assert report.handoffs
    assert all(isinstance(handoff, AgentHandoff) for handoff in report.handoffs)
    assert all(
        isinstance(invocation, ToolInvocationRecord) for invocation in report.tool_invocations
    )
    assert tuple(invocation.tool_name for invocation in report.tool_invocations) == (
        "registry.resolve_dataset_version",
        "feature.request",
        "label.validate_spec",
        "runtime.run_diagnostics",
        "review.no_lookahead_audit",
        "review.statistical_audit",
        "memory.record_rejection",
    )
    assert all(
        invocation.result.role == invocation.caller_role_id
        for invocation in report.tool_invocations
    )


def test_runtime_bridge_is_the_only_runtime_boundary_and_outputs_are_value_free() -> None:
    report = run_agent_dry_run()
    source = Path("src/alpha_system/agent_factory/dry_run/harness.py").read_text(encoding="utf-8")

    assert "from alpha_system.runtime" not in source
    assert "import alpha_system.runtime" not in source
    assert "runtime_bridge.adapt_runtime_tool_result" in source
    assert "RuntimeToolResult.from_dict" in source

    diagnostics = report.result_for_role("diagnostics_runner")
    assert diagnostics.status is AgentToolStatus.OK
    assert diagnostics.runtime_run_id == "runtime_run:agent_p22_synthetic"
    assert diagnostics.next_required_gate == "no_lookahead_auditor_review"
    assert any("agent_p22_evidence_draft" in artifact for artifact in diagnostics.artifacts)
    assert any(
        "agent_p22_reference_candidate_handoff" in artifact for artifact in diagnostics.artifacts
    )

    for result in report.tool_results:
        assert isinstance(result, AgentToolResult)
        _assert_value_free_result(result)


def test_rejection_memory_is_recorded_after_independent_verdict() -> None:
    report = run_agent_dry_run()
    statistical = report.result_for_role("statistical_reviewer")
    librarian = report.result_for_role("librarian")

    assert statistical.status is AgentToolStatus.REJECTED
    assert statistical.rejection_reasons == ("dry_run_reject_not_alpha_evidence",)
    assert librarian.status is AgentToolStatus.REJECTED
    assert "reviewer_verdict_ref:agent_p22_reject" in librarian.artifacts

    assert isinstance(report.rejected_idea_memory, RejectedIdeaMemoryRecord)
    assert isinstance(report.research_memory, ResearchMemoryRecord)
    assert report.rejected_idea_memory.status is RejectedIdeaMemoryStatus.REJECTED
    assert report.research_memory.status is ResearchMemoryStatus.REJECTED
    assert report.research_memory.related_rejected_memory_refs == (
        report.rejected_idea_memory.memory_id,
    )
    assert report.rejected_idea_memory.rejection_reasons == statistical.rejection_reasons
    assert report.rejected_idea_memory.tool_invocation_refs[-1] == (
        "tool_invocation:memory_record_rejection"
    )


def test_missing_dataset_resolver_degrades_to_truthful_blocked_report() -> None:
    report = run_agent_dry_run(dataset_version_resolver=lambda _path, _id: None)

    assert validate_dry_run_report(report) is report
    assert report.terminal_state is ResearchTaskStatus.BLOCKED
    assert report.max_forward_state is ResearchTaskStatus.DIRECTOR_SCOPED
    assert report.result_for_role("data_contract_auditor").status is AgentToolStatus.BLOCKED
    assert report.tool_invocations == ()
    assert report.handoffs == ()
    assert report.rejected_idea_memory.status is RejectedIdeaMemoryStatus.BLOCKED
    assert report.research_memory.status is ResearchMemoryStatus.BLOCKED
    assert not {state.value for state in report.reachable_task_statuses}.intersection(
        PROHIBITED_MVP_TASK_STATUSES
    )


def test_pass_to_promotion_is_not_reachable() -> None:
    report = run_agent_dry_run()

    assert "PASS" not in PERMITTED_STATISTICAL_DRY_RUN_VERDICTS
    assert ResearchTaskStatus.STATISTICAL_REVIEW_PASS not in report.reachable_task_statuses
    assert "promotion.review" not in report.registered_tool_names
    assert not any(name.startswith("promotion.") for name in report.registered_tool_names)
    assert report.result_for_role("no_lookahead_auditor").status is AgentToolStatus.OK
    assert report.result_for_role("statistical_reviewer").status is not AgentToolStatus.OK


def test_harness_source_has_no_continuous_loop_construct() -> None:
    source = Path("src/alpha_system/agent_factory/dry_run/harness.py").read_text(encoding="utf-8")

    assert "while " not in source


def _assert_value_free_result(result: AgentToolResult) -> None:
    for field_name in result.__dataclass_fields__:
        value = getattr(result, field_name)
        values = value if isinstance(value, tuple) else (value,)
        for item in values:
            if item is None or isinstance(item, AgentToolStatus):
                continue
            lowered = item.lower()
            assert not any(marker in lowered for marker in FORBIDDEN_RESULT_MARKERS)
            assert not any(suffix in lowered for suffix in FORBIDDEN_HEAVY_SUFFIXES)


@pytest.mark.parametrize("verdict", ("REJECT", "WATCH", "INCONCLUSIVE"))
def test_documented_non_pass_verdict_set(verdict: str) -> None:
    assert verdict in PERMITTED_STATISTICAL_DRY_RUN_VERDICTS
