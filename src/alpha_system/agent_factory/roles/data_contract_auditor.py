"""Data Contract Auditor role contract."""

from __future__ import annotations

from alpha_system.agent_factory.roles import registry
from alpha_system.agent_factory.roles.contracts import AgentRole


def build_role() -> AgentRole:
    """Construct the value-free Data Contract Auditor role declaration."""

    return AgentRole(
        role_id="data_contract_auditor",
        name="Data Contract Auditor",
        purpose=(
            "Verify accepted DatasetVersion and seed pack availability through registry tools."
        ),
        readable_inputs=(
            "Scoped ResearchTask refs for DatasetVersion FeaturePack LabelPack and partitions",
            "Bound AlphaSpec reference by alpha_spec_id",
            "Registry availability and admissibility summary refs only",
            "Admissible DatasetVersion states VERSIONED and READY_FOR_RESEARCH",
        ),
        callable_tools=(
            "registry.resolve_dataset_version",
            "registry.list_feature_packs",
            "registry.list_label_packs",
            "registry.audit_admissibility",
        ),
        producible_outputs=(
            "AgentToolResult-shaped status DATA_CONTRACT_AUDITED for available admissible inputs",
            "AgentToolResult-shaped status INPUTS_BLOCKED for missing or non-admissible inputs",
            "AgentToolResult-shaped status BLOCKED when DatasetVersion ref or registry is absent",
            "AgentToolResult-shaped status INCONCLUSIVE when scoped inputs are insufficient",
            "Output fields include dataset_version_id feature_pack_refs label_pack_refs",
            "Output fields include blocking_findings next_required_gate limitations",
        ),
        allowed_decisions=(
            "record_data_contract_audited_lifecycle_step",
            "record_inputs_blocked",
            "input_audit.record through sanctioned tool API",
        ),
        forbidden_decisions=(
            "read_raw_provider_files_or_provider_responses",
            "call_Databento_IBKR_or_external_providers",
            "write_FeatureStore_LabelStore_or_DatasetVersion_registry_directly",
            "bypass_accepted_DatasetVersion_policy_or_resolve_dataset_version",
            "accept_non_admissible_DatasetVersion_state",
            "promote_implement_or_self_review",
            "make_alpha_tradability_profitability_or_strategy_claim",
        ),
        handoff_format=(
            "decision",
            "dataset_version_id",
            "feature_pack_refs",
            "label_pack_refs",
            "admissibility_state",
            "blocking_findings",
            "next_required_gate",
            "reviewer_independence_note",
        ),
        reviewer_independence=(
            "auditor_role_is_not_drafter_or_implementer",
            "auditor_does_not_approve_own_work",
            "AGENT-P16 separation checks enforce fail-closed reviewer independence",
        ),
        failure_modes=(
            "INPUTS_BLOCKED when DatasetVersion is not VERSIONED or READY_FOR_RESEARCH",
            "INPUTS_BLOCKED when required FeaturePack or LabelPack ref is unavailable",
            "BLOCKED when no DatasetVersion reference is supplied or registry is absent",
            "INCONCLUSIVE when scoped inputs are insufficient to audit",
        ),
    )


DATA_CONTRACT_AUDITOR: AgentRole = registry.register(build_role())


__all__ = ["DATA_CONTRACT_AUDITOR", "build_role"]
