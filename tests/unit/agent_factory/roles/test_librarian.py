from __future__ import annotations

import importlib
from dataclasses import fields
from pathlib import Path

import pytest

import alpha_system.agent_factory.roles as roles_package
import alpha_system.agent_factory.roles.registry as registry_module
from alpha_system.agent_factory.permissions.matrix import permission_for
from alpha_system.agent_factory.roles.contracts import (
    FORBIDDEN_HEAVY_SUFFIXES,
    FORBIDDEN_PAYLOAD_MARKERS,
    AgentRole,
)
from alpha_system.agent_factory.tools.contracts import ToolGroup
from alpha_system.agent_factory.tools.registry import contract_for, resolve
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

MODULE_NAME = "alpha_system.agent_factory.roles.librarian"
ROLE_ID = "librarian"
EXPECTED_TOOLS = (
    "ledger.record_decision",
    "ledger.record_rejection",
    "memory.lookup_rejected_ideas",
    "memory.propose_update",
)
EXPECTED_RECORD_TOOL_NAMES = (
    "ledger.record_trial",
    "memory.record_rejection",
    "memory.record_watch",
)


def test_module_imports_and_registers_librarian_once() -> None:
    before_ids = set(registry_module.role_ids())

    module = importlib.import_module(MODULE_NAME)

    after_ids = registry_module.role_ids()
    assert set(after_ids).difference(before_ids) <= {ROLE_ID}
    assert after_ids.count(ROLE_ID) == 1
    registered = registry_module.get(ROLE_ID)
    assert registered == module.LIBRARIAN_ROLE
    assert registered.role_id == ROLE_ID


def test_repeated_import_or_reload_does_not_duplicate_registration() -> None:
    module = importlib.import_module(MODULE_NAME)

    importlib.import_module(MODULE_NAME)
    reloaded = importlib.reload(module)

    assert registry_module.role_ids().count(ROLE_ID) == 1
    assert registry_module.get(ROLE_ID) == reloaded.LIBRARIAN_ROLE


def test_contract_is_populated_and_value_free() -> None:
    role = _registered_role()

    assert isinstance(role, AgentRole)
    assert role.validate() is role
    for field in fields(AgentRole):
        value = getattr(role, field.name)
        values = value if isinstance(value, tuple) else (value,)
        assert values
        for item in values:
            lowered = item.lower()
            assert item
            assert item == item.strip()
            assert "\n" not in item
            assert not any(marker in lowered for marker in FORBIDDEN_PAYLOAD_MARKERS)
            assert not any(suffix in lowered for suffix in FORBIDDEN_HEAVY_SUFFIXES)


def test_callable_tools_match_permission_matrix_and_exclude_forbidden_surfaces() -> None:
    role = _registered_role()
    permissions = permission_for(ROLE_ID)

    assert role.callable_tools == EXPECTED_TOOLS
    assert role.callable_tools == permissions.tool.allowed_tool_ids
    assert permissions.write.allowed_scopes == (
        "decision_ledger.record_after_verdict",
        "memory_update.proposal_after_verdict",
    )
    assert not permissions.write.direct_registry_write
    assert not permissions.review.can_issue_verdict
    assert not permissions.promotion.can_promote
    assert not permissions.data.raw_provider_access
    assert not any(
        tool_id.startswith(("promotion.", "registry.")) for tool_id in role.callable_tools
    )


def test_registry_record_tools_are_librarian_allowed_and_verdict_gated() -> None:
    module = importlib.import_module(MODULE_NAME)

    assert module.REGISTRY_RECORD_TOOL_NAMES == EXPECTED_RECORD_TOOL_NAMES
    for tool_name in module.REGISTRY_RECORD_TOOL_NAMES:
        contract = contract_for(tool_name)
        assert contract.group is ToolGroup.LEDGER_MEMORY_PROMOTION
        assert contract.output_schema is AgentToolResult
        assert contract.allows(ROLE_ID)
        assert "review_verdict_ref" in contract.required_inputs
        assert contract.artifact_policy.value == "local_only"

    assert "promotion.review" not in module.REGISTRY_RECORD_TOOL_NAMES
    with pytest.raises(PermissionError):
        resolve("promotion.review", ROLE_ID)
    with pytest.raises(PermissionError):
        resolve("registry.resolve_dataset_version", ROLE_ID)


def test_role_consumes_governance_primitives_without_reimplementing_them() -> None:
    module = importlib.import_module(MODULE_NAME)

    assert module.CONSUMED_GOVERNANCE_PRIMITIVES == (
        ReviewerVerdict,
        ReviewerVerdictOutcome,
        RejectedIdeaRecord,
        ResearchGraveyardLedger,
        PromotionDecision,
        PromotionGateContext,
        validate_governance_transition,
        PROHIBITED_MVP_STATES,
    )

    source_text = Path(module.__file__).read_text(encoding="utf-8")
    for forbidden_definition in (
        "class ReviewerVerdict",
        "class RejectedIdeaRecord",
        "class ResearchGraveyardLedger",
        "class PromotionDecision",
        "def validate_governance_transition",
    ):
        assert forbidden_definition not in source_text


def test_declares_readable_inputs_outputs_handoff_and_lifecycle_state() -> None:
    module = importlib.import_module(MODULE_NAME)
    role = _registered_role()

    assert module.LIFECYCLE_STATE == "LIBRARIAN_MEMORY_RECORDED"
    readable_text = " ".join(role.readable_inputs)
    for required in (
        "ReviewerVerdict",
        "AgentDecisionRecord",
        "AgentHandoffRecord",
        "AgentToolInvocationRecord",
        "RejectedIdeaRecord",
        "ResearchGraveyardLedger",
        "ResearchTask",
        "EvidenceDraft",
        "ReferenceCandidateHandoff",
    ):
        assert required in readable_text

    output_and_handoff = " ".join((*role.producible_outputs, *role.handoff_format))
    for required in (
        "AgentToolResult",
        "LIBRARIAN_MEMORY_RECORDED",
        "REJECTED",
        "INCONCLUSIVE",
        "BLOCKED",
        "reviewer_verdict_ref",
        "proposed_memory_record_refs",
        "next_required_gate",
        "limitations",
    ):
        assert required in output_and_handoff


def test_forbidden_decisions_cover_promotion_registry_and_no_claim_boundaries() -> None:
    role = _registered_role()
    forbidden = " ".join(role.forbidden_decisions).lower()

    for required_fragment in (
        "promote_without_promotiongate",
        "promotion_review",
        "write_any_registry_without_reviewer_verdict",
        "direct_registry_write",
        "self_promotion",
        "referencecandidatehandoff_as_validation",
        "claim_alpha_tradability_profitability",
        "accepted_datasetversion",
        "raw_provider",
        "external_provider",
        "materialize_feature_label_runtime_or_agent_values",
    ):
        assert required_fragment in forbidden

    for prohibited_state in (
        "alpha_validated",
        "factor_promoted",
        "strategy_ready",
        "portfolio_ready",
        "candidate_promoted",
        "live_ready",
        "paper_ready",
        "profitable",
        "tradable",
        "production_ready",
        "autonomous_research_running",
    ):
        assert prohibited_state in forbidden

    allowed = " ".join(role.allowed_decisions).lower()
    assert "propose_memory_records" in allowed
    assert "promote" not in allowed


def test_declares_records_only_after_reviewer_verdict_invariant_and_failure_modes() -> None:
    module = importlib.import_module(MODULE_NAME)
    role = _registered_role()

    independence = " ".join(role.reviewer_independence).lower()
    failure_modes = " ".join(role.failure_modes).lower()

    assert module.REQUIRED_VERDICT_INVARIANT == "librarian_needs_reviewer_verdict_ref"
    assert "records_only_after_independent_reviewer_verdict_ref_exists" in independence
    assert "librarian_needs_reviewer_verdict_ref" in independence
    assert "does_not_review_implement_run_diagnostics_or_promote" in independence
    assert "blocked" in failure_modes
    assert "reviewer_verdict_ref is missing" in failure_modes
    assert "registry write is attempted without verdict" in failure_modes
    assert "promotion.review is attempted" in failure_modes
    assert "duplicate idea detected" in failure_modes
    assert "not alpha evidence" in failure_modes


def test_import_does_not_require_shared_role_file_edits() -> None:
    importlib.import_module(MODULE_NAME)
    package_text = Path(roles_package.__file__).read_text(encoding="utf-8")
    registry_text = Path(registry_module.__file__).read_text(encoding="utf-8")

    assert ROLE_ID not in package_text
    assert ROLE_ID not in registry_text
    assert registry_module.role_ids().count(ROLE_ID) == 1


def _registered_role() -> AgentRole:
    importlib.import_module(MODULE_NAME)
    return registry_module.get(ROLE_ID)
