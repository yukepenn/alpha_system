from __future__ import annotations

import importlib
from dataclasses import fields

import alpha_system.agent_factory.roles.data_contract_auditor as data_contract_auditor_module
from alpha_system.agent_factory.permissions.matrix import permission_for
from alpha_system.agent_factory.roles import registry
from alpha_system.agent_factory.roles.contracts import (
    FORBIDDEN_HEAVY_SUFFIXES,
    FORBIDDEN_PAYLOAD_MARKERS,
    AgentRole,
)


def test_data_contract_auditor_imports_and_registers_once() -> None:
    module = importlib.import_module("alpha_system.agent_factory.roles.data_contract_auditor")

    role = registry.get("data_contract_auditor")

    assert module is data_contract_auditor_module
    assert role is module.DATA_CONTRACT_AUDITOR
    assert role.role_id == "data_contract_auditor"
    assert registry.role_ids().count("data_contract_auditor") == 1


def test_data_contract_auditor_contract_fields_are_populated_and_value_free() -> None:
    role = registry.get("data_contract_auditor")

    assert isinstance(role, AgentRole)
    assert role.validate() is role
    for field in fields(AgentRole):
        value = getattr(role, field.name)
        if isinstance(value, tuple):
            assert value
            items = value
        else:
            assert value
            items = (value,)
        for item in items:
            assert item == item.strip()
            assert "\n" not in item
            lowered = item.lower()
            assert not any(marker in lowered for marker in FORBIDDEN_PAYLOAD_MARKERS)
            assert not any(suffix in lowered for suffix in FORBIDDEN_HEAVY_SUFFIXES)


def test_data_contract_auditor_tools_match_permission_matrix_entry() -> None:
    role = registry.get("data_contract_auditor")

    assert role.callable_tools == permission_for("data_contract_auditor").tool.allowed_tool_ids
    assert role.callable_tools == (
        "registry.resolve_dataset_version",
        "registry.list_feature_packs",
        "registry.list_label_packs",
        "registry.audit_admissibility",
    )


def test_data_contract_auditor_declares_required_inputs_and_outputs() -> None:
    role = registry.get("data_contract_auditor")

    input_text = " ".join(role.readable_inputs)
    assert "ResearchTask" in input_text
    assert "DatasetVersion" in input_text
    assert "FeaturePack" in input_text
    assert "LabelPack" in input_text
    assert "alpha_spec_id" in input_text
    assert "registry" in input_text.lower()

    output_text = " ".join(role.producible_outputs)
    for status in (
        "DATA_CONTRACT_AUDITED",
        "INPUTS_BLOCKED",
        "BLOCKED",
        "INCONCLUSIVE",
    ):
        assert status in output_text
    for field_name in (
        "dataset_version_id",
        "feature_pack_refs",
        "label_pack_refs",
        "blocking_findings",
        "next_required_gate",
        "limitations",
    ):
        assert field_name in output_text


def test_data_contract_auditor_forbids_boundary_violations() -> None:
    role = registry.get("data_contract_auditor")

    forbidden_text = " ".join(role.forbidden_decisions).lower()
    assert "raw" in forbidden_text
    assert "provider" in forbidden_text
    assert "databento" in forbidden_text
    assert "ibkr" in forbidden_text
    assert "write" in forbidden_text
    assert "registry" in forbidden_text
    assert "bypass" in forbidden_text
    assert "resolve_dataset_version" in forbidden_text
    assert "promote" in forbidden_text
    assert "implement" in forbidden_text
    assert "self_review" in forbidden_text
    assert "alpha" in forbidden_text
    assert "tradability" in forbidden_text
    assert "profitability" in forbidden_text


def test_data_contract_auditor_admissible_states_and_tool_denies_are_declared() -> None:
    role = registry.get("data_contract_auditor")

    state_text = " ".join(role.readable_inputs + role.failure_modes)
    assert "VERSIONED" in state_text
    assert "READY_FOR_RESEARCH" in state_text
    for non_admissible_state in ("PROMOTED", "CANDIDATE", "PRODUCTION"):
        assert non_admissible_state not in state_text

    tool_text = " ".join(role.callable_tools).lower()
    for denied_verb in (
        "materialize",
        "promote",
        "runtime",
        "raw",
        "read",
    ):
        assert denied_verb not in tool_text


def test_data_contract_auditor_declares_allowed_decisions_and_handoff() -> None:
    role = registry.get("data_contract_auditor")

    assert role.allowed_decisions == (
        "record_data_contract_audited_lifecycle_step",
        "record_inputs_blocked",
        "input_audit.record through sanctioned tool API",
    )
    assert role.handoff_format == (
        "decision",
        "dataset_version_id",
        "feature_pack_refs",
        "label_pack_refs",
        "admissibility_state",
        "blocking_findings",
        "next_required_gate",
        "reviewer_independence_note",
    )


def test_data_contract_auditor_declares_reviewer_independence_and_failure_modes() -> None:
    role = registry.get("data_contract_auditor")

    independence_text = " ".join(role.reviewer_independence).lower()
    assert "not_drafter" in independence_text
    assert "implementer" in independence_text
    assert "approve_own" in independence_text
    assert "separation" in independence_text

    failure_text = " ".join(role.failure_modes)
    assert "INPUTS_BLOCKED" in failure_text
    assert "BLOCKED when no DatasetVersion reference is supplied" in failure_text
    assert "INCONCLUSIVE when scoped inputs are insufficient" in failure_text
