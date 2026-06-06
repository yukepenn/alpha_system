from __future__ import annotations

import importlib
from dataclasses import fields

import alpha_system.agent_factory.roles.alpha_spec_critic as alpha_spec_critic_module
from alpha_system.agent_factory.roles import registry
from alpha_system.agent_factory.roles.contracts import (
    FORBIDDEN_HEAVY_SUFFIXES,
    FORBIDDEN_PAYLOAD_MARKERS,
    AgentRole,
)


def test_alpha_spec_critic_imports_and_registers_once() -> None:
    module = importlib.import_module("alpha_system.agent_factory.roles.alpha_spec_critic")

    role = registry.get("alpha_spec_critic")

    assert module is alpha_spec_critic_module
    assert role is module.ALPHA_SPEC_CRITIC
    assert role.role_id == "alpha_spec_critic"
    assert registry.role_ids().count("alpha_spec_critic") == 1


def test_alpha_spec_critic_contract_fields_are_populated_and_value_free() -> None:
    role = registry.get("alpha_spec_critic")

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


def test_alpha_spec_critic_declares_required_inputs_tools_and_outputs() -> None:
    role = registry.get("alpha_spec_critic")

    assert any("AlphaSpec draft" in item for item in role.readable_inputs)
    assert any("ResearchTask" in item for item in role.readable_inputs)
    assert any("RejectedIdeaMemoryRecord" in item for item in role.readable_inputs)
    assert any("duplicate_exposure" in item for item in role.readable_inputs)
    assert role.callable_tools == (
        "alphaspec.critique",
        "alphaspec.request_revision",
        "alphaspec.reject",
    )
    output_text = " ".join(role.producible_outputs)
    for status in (
        "ALPHASPEC_CRITIQUED",
        "ALPHASPEC_REVISION_REQUESTED",
        "ALPHASPEC_REJECTED",
        "BLOCKED",
        "INCONCLUSIVE",
    ):
        assert status in output_text
    for field_name in (
        "alpha_spec_id",
        "rejection_reasons",
        "blocking_findings",
        "next_required_gate",
    ):
        assert field_name in output_text


def test_alpha_spec_critic_forbids_self_review_implementation_and_promotion() -> None:
    role = registry.get("alpha_spec_critic")

    forbidden_text = " ".join(role.forbidden_decisions).lower()
    assert "self_draft" in forbidden_text
    assert "self_review" in forbidden_text
    assert "implement" in forbidden_text
    assert "diagnostics" in forbidden_text
    assert "promote" in forbidden_text
    assert "tradability" in forbidden_text
    assert "profitability" in forbidden_text
    assert "draft" not in " ".join(role.callable_tools)
    assert "materialize" not in " ".join(role.callable_tools)
    assert "runtime" not in " ".join(role.callable_tools)
    assert "promotion" not in " ".join(role.callable_tools)


def test_alpha_spec_critic_declares_reviewer_independence() -> None:
    role = registry.get("alpha_spec_critic")

    independence_text = " ".join(role.reviewer_independence).lower()
    assert "drafter" in independence_text
    assert "generator" in independence_text
    assert "approver" in independence_text
    assert "!=" in independence_text


def test_alpha_spec_critic_allows_no_promotion_validation_or_candidate_decision() -> None:
    role = registry.get("alpha_spec_critic")

    allowed_text = " ".join(role.allowed_decisions).lower()
    assert "promote" not in allowed_text
    assert "promotion" not in allowed_text
    assert "validated" not in allowed_text
    assert "candidate" not in allowed_text
    assert role.allowed_decisions == (
        "reject_alpha_spec_draft",
        "request_alpha_spec_revision",
        "record_alphaspec_critiqued_lifecycle_step",
    )


def test_alpha_spec_critic_declares_failure_modes() -> None:
    role = registry.get("alpha_spec_critic")

    failure_text = " ".join(role.failure_modes)
    assert "BLOCKED when no AlphaSpec draft is supplied" in failure_text
    assert "ALPHASPEC_REJECTED when draft duplicates a prior rejected idea" in failure_text
    assert "INCONCLUSIVE when scoped inputs are insufficient" in failure_text
