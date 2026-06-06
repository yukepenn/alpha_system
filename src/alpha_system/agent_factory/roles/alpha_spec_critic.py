"""AlphaSpec Critic role contract."""

from __future__ import annotations

from alpha_system.agent_factory.roles import registry
from alpha_system.agent_factory.roles.contracts import AgentRole


def build_role() -> AgentRole:
    """Construct the value-free AlphaSpec Critic role declaration."""

    return AgentRole(
        role_id="alpha_spec_critic",
        name="AlphaSpec Critic",
        purpose=(
            "Critique, reject, or request revision on AlphaSpec drafts "
            "independently from the drafter."
        ),
        readable_inputs=(
            "alpha_system.governance.alpha_spec AlphaSpec draft reference by alpha_spec_id",
            "Scoped ResearchTask context reference",
            "RejectedIdeaMemoryRecord summary reference",
            "duplicate_exposure summary reference",
            "ResearchGraveyardLedger summary reference",
            "library summary reference",
        ),
        callable_tools=(
            "alphaspec.critique",
            "alphaspec.request_revision",
            "alphaspec.reject",
        ),
        producible_outputs=(
            "AgentToolResult-shaped critique status ALPHASPEC_CRITIQUED",
            "AgentToolResult-shaped revision status ALPHASPEC_REVISION_REQUESTED",
            "AgentToolResult-shaped rejection status ALPHASPEC_REJECTED",
            "AgentToolResult-shaped block status BLOCKED",
            "AgentToolResult-shaped inconclusive status INCONCLUSIVE",
            "Output fields include alpha_spec_id rejection_reasons",
            "Output fields include blocking_findings next_required_gate",
        ),
        allowed_decisions=(
            "reject_alpha_spec_draft",
            "request_alpha_spec_revision",
            "record_alphaspec_critiqued_lifecycle_step",
        ),
        forbidden_decisions=(
            "self_draft_or_edit_reviewed_alpha_spec",
            "self_review_alpha_spec_authored_by_same_agent",
            "implement_code_or_run_runtime_diagnostics",
            "promote_or_approve_for_candidacy",
            "make_alpha_tradability_profitability_or_strategy_claim",
        ),
        handoff_format=(
            "decision",
            "alpha_spec_id",
            "rejection_reasons",
            "blocking_findings",
            "next_required_gate",
            "reviewer_independence_note",
        ),
        reviewer_independence=(
            "generator_role_id != critic_role_id",
            "alpha_spec_drafter != alpha_spec_critic",
            "AGENT-P16 separation checks enforce generator not approver",
        ),
        failure_modes=(
            "BLOCKED when no AlphaSpec draft is supplied",
            "ALPHASPEC_REJECTED when draft duplicates a prior rejected idea",
            "INCONCLUSIVE when scoped inputs are insufficient",
            "ALPHASPEC_REVISION_REQUESTED when fixable contract gaps are found",
        ),
    )


ALPHA_SPEC_CRITIC: AgentRole = registry.register(build_role())


__all__ = ["ALPHA_SPEC_CRITIC", "build_role"]
