from __future__ import annotations

from pathlib import Path

import pytest

import alpha_system.agent_factory.tools.registry as registry_module
from alpha_system.agent_factory.tools.contracts import (
    REQUIRED_FORBIDDEN_SIDE_EFFECTS,
    ToolArtifactPolicy,
    ToolContractStatus,
)
from alpha_system.agent_factory.tools.registry import ToolRegistry
from alpha_system.agent_factory.tools.results import AgentToolResult

EXPECTED_GROUPS = {
    "registry",
    "feature_label",
    "runtime",
    "review",
    "ledger_memory_promotion",
}
EXPECTED_TOOLS = {
    "registry.list_datasets",
    "registry.resolve_dataset_version",
    "registry.list_feature_packs",
    "registry.list_label_packs",
    "feature.request",
    "feature.validate_spec",
    "feature.materialize",
    "label.validate_spec",
    "label.materialize",
    "runtime.plan",
    "runtime.validate_inputs",
    "runtime.run_diagnostics",
    "runtime.run_label_diagnostics",
    "runtime.run_signal_probe",
    "runtime.run_cost_stress",
    "runtime.build_evidence_draft",
    "runtime.build_reference_handoff",
    "review.no_lookahead_audit",
    "review.statistical_audit",
    "ledger.record_trial",
    "evidence.build_bundle",
    "memory.record_rejection",
    "memory.record_watch",
    "promotion.review",
}


def test_registry_contains_exact_candidate_tool_surface() -> None:
    assert set(registry_module.groups()) == EXPECTED_GROUPS
    assert set(registry_module.tool_names()) == EXPECTED_TOOLS

    grouped_tools = {
        contract.name
        for group in EXPECTED_GROUPS
        for contract in registry_module.list_by_group(group)
    }
    assert grouped_tools == EXPECTED_TOOLS


def test_every_candidate_contract_has_required_policy_fields() -> None:
    for contract in registry_module.all_contracts():
        assert contract.allowed_callers
        assert contract.required_inputs
        assert contract.output_schema is AgentToolResult
        assert contract.artifact_policy is ToolArtifactPolicy.LOCAL_ONLY
        assert contract.failure_states
        assert contract.required_reviewer
        assert contract.status in {
            ToolContractStatus.MVP,
            ToolContractStatus.TARGET,
            ToolContractStatus.FUTURE,
        }
        assert set(REQUIRED_FORBIDDEN_SIDE_EFFECTS) <= set(contract.forbidden_side_effects)


def test_registry_resolve_is_default_deny_for_unknown_tool_or_caller() -> None:
    allowed = registry_module.resolve("runtime.run_diagnostics", "diagnostics_runner")
    assert allowed.name == "runtime.run_diagnostics"

    with pytest.raises(KeyError):
        registry_module.resolve("runtime.open_unbounded_runner", "diagnostics_runner")

    with pytest.raises(PermissionError):
        registry_module.resolve("runtime.run_diagnostics", "hypothesis_scout")


def test_registry_discovery_does_not_grant_call_authority() -> None:
    discovered = registry_module.contract_for("runtime.run_diagnostics")

    assert discovered.name == "runtime.run_diagnostics"
    assert not discovered.allows("hypothesis_scout")
    with pytest.raises(PermissionError):
        registry_module.resolve(discovered.name, "hypothesis_scout")


def test_direct_registry_writes_are_not_expressible_as_allowed_behavior() -> None:
    for contract in registry_module.all_contracts():
        assert contract.forbids("direct_registry_write")
        assert "direct_registry_write" not in contract.required_inputs
        assert contract.artifact_policy is ToolArtifactPolicy.LOCAL_ONLY


def test_registry_config_round_trips_to_read_only_registry() -> None:
    registry = ToolRegistry.from_config(registry_module.DEFAULT_CONFIG_PATH)

    assert registry.tool_names() == registry_module.tool_names()
    with pytest.raises(TypeError):
        registry._contracts["new.tool"] = registry.contract_for(  # type: ignore[attr-defined,index]
            "runtime.plan"
        )


def test_registry_module_does_not_import_consumed_primitive_packages() -> None:
    registry_text = Path(registry_module.__file__).read_text(encoding="utf-8")

    assert "alpha_system.runtime" not in registry_text
    assert "alpha_system.governance" not in registry_text
    assert "alpha_system.data" not in registry_text
