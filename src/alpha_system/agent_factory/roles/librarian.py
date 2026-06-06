"""Librarian role contract.

This module declares the contracts-only Librarian role. It references existing
review, rejected-idea memory, promotion-gate, and queue primitives; it does not
write registries, promote work, instantiate an agent, or record raw values.
"""

from __future__ import annotations

from alpha_system.agent_factory.permissions.matrix import permission_for
from alpha_system.agent_factory.queue.models import (
    PROHIBITED_MVP_TASK_STATUSES,
    ResearchTask,
    ResearchTaskStatus,
)
from alpha_system.agent_factory.roles import registry
from alpha_system.agent_factory.roles.contracts import AgentRole
from alpha_system.agent_factory.tools.registry import contract_for
from alpha_system.agent_factory.tools.results import AgentToolResult
from alpha_system.governance.promotion import (
    PROHIBITED_MVP_STATES,
    PromotionDecision,
)
from alpha_system.governance.promotion_gate import (
    PromotionGateContext,
    validate_governance_transition,
)
from alpha_system.governance.rejected_idea import (
    RejectedIdeaRecord,
    ResearchGraveyardLedger,
)
from alpha_system.governance.reviewer_verdict import (
    ReviewerVerdict,
    ReviewerVerdictOutcome,
)

ROLE_ID = "librarian"
LIFECYCLE_STATE = ResearchTaskStatus.LIBRARIAN_MEMORY_RECORDED.value
REQUIRED_VERDICT_INVARIANT = "librarian_needs_reviewer_verdict_ref"
REGISTRY_RECORD_TOOL_NAMES: tuple[str, ...] = (
    "ledger.record_trial",
    "memory.record_rejection",
    "memory.record_watch",
)
FORBIDDEN_TOOL_PREFIXES: tuple[str, ...] = ("promotion.", "registry.")
PROHIBITED_STATE_REFS: tuple[str, ...] = tuple(sorted(PROHIBITED_MVP_TASK_STATUSES))
CONSUMED_GOVERNANCE_PRIMITIVES: tuple[object, ...] = (
    ReviewerVerdict,
    ReviewerVerdictOutcome,
    RejectedIdeaRecord,
    ResearchGraveyardLedger,
    PromotionDecision,
    PromotionGateContext,
    validate_governance_transition,
    PROHIBITED_MVP_STATES,
)
CONSUMED_QUEUE_PRIMITIVES: tuple[object, ...] = (
    ResearchTask,
    ResearchTaskStatus,
    PROHIBITED_MVP_TASK_STATUSES,
)


def _matrix_callable_tools() -> tuple[str, ...]:
    return permission_for(ROLE_ID).tool.allowed_tool_ids


CALLABLE_TOOL_IDS: tuple[str, ...] = _matrix_callable_tools()
REGISTRY_RECORD_TOOL_CONTRACTS = tuple(
    contract_for(tool_name) for tool_name in REGISTRY_RECORD_TOOL_NAMES
)


LIBRARIAN_ROLE = AgentRole(
    role_id=ROLE_ID,
    name="Librarian",
    purpose=(
        "Record decisions, rejected ideas, and proposed memory updates after a reviewer verdict."
    ),
    readable_inputs=(
        "ReviewerVerdict id refs from alpha_system.governance.reviewer_verdict",
        "AgentDecisionRecord AgentHandoffRecord and AgentToolInvocationRecord refs",
        "RejectedIdeaRecord and ResearchGraveyardLedger summary refs",
        "ResearchMemoryRecord proposed-update refs",
        "bounded ResearchTask queue context refs",
        "EvidenceDraft and ReferenceCandidateHandoff structured summary refs only",
    ),
    callable_tools=CALLABLE_TOOL_IDS,
    producible_outputs=(
        "AgentToolResult with LIBRARIAN_MEMORY_RECORDED lifecycle state",
        "AgentToolResult surfacing REJECTED INCONCLUSIVE or BLOCKED review outcomes",
        "proposed decision ledger record refs after reviewer verdict",
        "proposed rejected-idea or watch-memory record refs",
        "duplicate or known-rejection summary refs",
    ),
    allowed_decisions=(
        "propose_memory_records_after_reviewer_verdict_ref_exists",
        "record_decision_rejection_or_watch_refs_through_sanctioned_memory_tools",
        "surface_prior_rejection_reasons_and_duplicate_links",
        "mark_duplicate_or_known_rejection_status",
        "select_next_required_gate_for_missing_verdict_or_duplicate_review",
    ),
    forbidden_decisions=(
        "promote_without_promotiongate",
        "call_promotion_review_or_promote_at_all_in_this_mvp",
        "write_any_registry_without_reviewer_verdict",
        "direct_registry_write_to_feature_label_dataset_or_factor_library",
        "self_promotion_or_self_approval",
        "record_evidencedraft_or_referencecandidatehandoff_as_validation",
        "claim_alpha_tradability_profitability_or_production_readiness",
        "bypass_runtime_or_accepted_datasetversion_boundary",
        "read_raw_provider_data_or_runtime_values",
        "make_external_provider_calls",
        "materialize_feature_label_runtime_or_agent_values",
        "reach_prohibited_mvp_state_alpha_validated_factor_promoted_strategy_ready_portfolio_ready_candidate_promoted_live_ready_paper_ready_profitable_tradable_production_ready_autonomous_research_running",
    ),
    handoff_format=(
        "request_id",
        "task_id",
        "role",
        "reviewer_verdict_ref",
        "source_decision_handoff_or_tool_invocation_refs",
        "rejected_idea_or_research_memory_refs",
        "duplicate_links_or_prior_rejection_reasons",
        "proposed_memory_record_refs",
        "status",
        "next_required_gate",
        "limitations",
    ),
    reviewer_independence=(
        "records_only_after_independent_reviewer_verdict_ref_exists",
        "librarian_needs_reviewer_verdict_ref_invariant_declared_for_agent_p16",
        "librarian_does_not_review_implement_run_diagnostics_or_promote",
        "missing_verdict_yields_blocked_not_registry_write",
    ),
    failure_modes=(
        "BLOCKED when reviewer_verdict_ref is missing",
        "refused when registry write is attempted without verdict",
        "refused when promotion or promotion.review is attempted",
        "duplicate idea detected surfaces existing rejection refs",
        "INCONCLUSIVE when source refs are insufficient",
        "REJECTED WATCH or BLOCKED copied as memory status not alpha evidence",
    ),
)


if LIBRARIAN_ROLE.callable_tools != _matrix_callable_tools():
    raise RuntimeError("librarian callable_tools must match permission matrix")

for _tool_id in (*LIBRARIAN_ROLE.callable_tools, *REGISTRY_RECORD_TOOL_NAMES):
    if _tool_id.startswith(FORBIDDEN_TOOL_PREFIXES):
        raise RuntimeError("librarian cannot call promotion or registry tools")

for _contract in REGISTRY_RECORD_TOOL_CONTRACTS:
    if not _contract.allows(ROLE_ID):
        raise RuntimeError("librarian registry record tool must allow librarian")
    if _contract.output_schema is not AgentToolResult:
        raise RuntimeError("librarian registry record tools must return AgentToolResult")


def _register_once(role: AgentRole) -> AgentRole:
    try:
        existing = registry.get(role.role_id)
    except KeyError:
        return registry.register(role)
    if existing != role:
        raise RuntimeError("librarian registry entry differs from module contract")
    return existing


REGISTERED_ROLE = _register_once(LIBRARIAN_ROLE)

__all__ = [
    "CALLABLE_TOOL_IDS",
    "CONSUMED_GOVERNANCE_PRIMITIVES",
    "CONSUMED_QUEUE_PRIMITIVES",
    "FORBIDDEN_TOOL_PREFIXES",
    "LIBRARIAN_ROLE",
    "LIFECYCLE_STATE",
    "PROHIBITED_STATE_REFS",
    "REGISTERED_ROLE",
    "REGISTRY_RECORD_TOOL_CONTRACTS",
    "REGISTRY_RECORD_TOOL_NAMES",
    "REQUIRED_VERDICT_INVARIANT",
    "ROLE_ID",
]
