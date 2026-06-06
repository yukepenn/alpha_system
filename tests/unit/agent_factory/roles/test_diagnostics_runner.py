from __future__ import annotations

import importlib
from dataclasses import fields
from pathlib import Path

import alpha_system.agent_factory.roles as roles_package
import alpha_system.agent_factory.roles.registry as registry_module
from alpha_system.agent_factory.permissions.matrix import permission_for
from alpha_system.agent_factory.roles.contracts import (
    FORBIDDEN_HEAVY_SUFFIXES,
    FORBIDDEN_PAYLOAD_MARKERS,
    AgentRole,
)
from alpha_system.agent_factory.tools import registry as tool_registry
from alpha_system.agent_factory.tools.results import (
    AGENT_TOOL_RESULT_FIELDS,
    AgentToolResult,
    AgentToolStatus,
)
from alpha_system.cli import runtime as runtime_cli
from alpha_system.runtime.tool_results import RuntimeRunSummary, RuntimeToolResult

MODULE_NAME = "alpha_system.agent_factory.roles.diagnostics_runner"
ROLE_ID = "diagnostics_runner"
EXPECTED_TOOLS = (
    "runtime.plan",
    "runtime.validate_inputs",
    "runtime.run_diagnostics",
    "runtime.run_label_diagnostics",
    "runtime.run_signal_probe",
    "runtime.run_cost_stress",
    "runtime.build_evidence_draft",
    "runtime.build_reference_handoff",
)


def test_module_imports_and_registers_diagnostics_runner_once() -> None:
    before_ids = set(registry_module.role_ids())

    module = importlib.import_module(MODULE_NAME)

    after_ids = registry_module.role_ids()
    assert set(after_ids).difference(before_ids) <= {ROLE_ID}
    assert after_ids.count(ROLE_ID) == 1
    registered = registry_module.get(ROLE_ID)
    assert registered == module.DIAGNOSTICS_RUNNER_ROLE
    assert registered.role_id == ROLE_ID


def test_repeated_import_or_reload_does_not_duplicate_registration() -> None:
    module = importlib.import_module(MODULE_NAME)

    importlib.import_module(MODULE_NAME)
    reloaded = importlib.reload(module)

    assert registry_module.role_ids().count(ROLE_ID) == 1
    assert registry_module.get(ROLE_ID) == reloaded.DIAGNOSTICS_RUNNER_ROLE


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


def test_callable_tools_are_only_runtime_registry_tools_with_matrix_backing() -> None:
    role = _registered_role()
    permissions = permission_for(ROLE_ID)

    assert role.callable_tools == EXPECTED_TOOLS
    for tool_id in role.callable_tools:
        contract = tool_registry.resolve(tool_id, ROLE_ID)
        assert contract.group.value == "runtime"
        assert contract.name == tool_id
        assert any(permissions.tool.allows(ref) for ref in contract.permission_matrix_refs)

    assert permissions.data.accepted_dataset_versions_only
    assert permissions.data.allowed_scopes == ("accepted_dataset_version_ref",)
    assert permissions.write.allowed_scopes == ("runtime_request.record",)
    assert not permissions.write.direct_registry_write
    assert not permissions.review.can_issue_verdict
    assert not permissions.promotion.can_promote
    assert not permissions.data.raw_provider_access


def test_contract_declares_no_promotion_spec_mutation_or_runtime_bypass_authority() -> None:
    role = _registered_role()
    allowed_text = " ".join(role.allowed_decisions).lower()
    forbidden_text = " ".join(role.forbidden_decisions).lower()

    assert "promote" not in allowed_text
    assert "candidate" not in allowed_text
    assert "author" not in allowed_text
    assert "alter" not in allowed_text
    assert "bypass" not in allowed_text

    for required_fragment in (
        "promote",
        "alter_author_featurerequest_labelspec_alphaspec_or_studyspec",
        "bypass_runtime_input_resolver_or_tool_surface",
        "reimplement_diagnostics_cost_overfit_or_no_lookahead_logic",
        "raw_provider_data",
        "external_provider",
        "variant_budget",
        "strategy_validation_alpha_or_candidate",
        "statistical_verdict",
        "live_paper_broker_order",
    ):
        assert required_fragment in forbidden_text


def test_requires_bound_study_spec_before_diagnostics_and_fails_closed() -> None:
    module = importlib.import_module(MODULE_NAME)
    role = _registered_role()

    input_text = " ".join(role.readable_inputs).lower()
    failure_text = " ".join(role.failure_modes).lower()
    assert "bound studyspec id required before diagnostics" in input_text
    assert "no studyspec no diagnostics" in failure_text

    result = module.blocked_missing_study_spec_result(
        "request:diagnostics_no_study_spec",
        alpha_spec_id="alpha_spec:bounded_seed",
        dataset_version_id="dataset_version:accepted_seed",
        feature_pack_refs=("feature_pack:seed_refs",),
        label_pack_refs=("label_pack:seed_refs",),
    )

    assert isinstance(result, AgentToolResult)
    assert result.status is AgentToolStatus.BLOCKED
    assert result.status is not AgentToolStatus.OK
    assert result.role == ROLE_ID
    assert result.study_spec_id is None
    assert result.rejection_reasons == ("missing_bound_study_spec",)
    assert result.blocking_findings == ("no_study_spec_no_diagnostics",)
    assert result.next_required_gate == module.MISSING_STUDY_SPEC_GATE


def test_outputs_are_agent_tool_result_shape_with_no_raw_or_heavy_data() -> None:
    module = importlib.import_module(MODULE_NAME)
    role = _registered_role()

    output_text = " ".join(role.producible_outputs)
    for field_name in AGENT_TOOL_RESULT_FIELDS:
        assert field_name in output_text

    result = module.blocked_missing_study_spec_result(
        "request:diagnostics_value_free",
        alpha_spec_id="alpha_spec:bounded_seed",
        dataset_version_id="dataset_version:accepted_seed",
        feature_pack_refs=("feature_pack:seed_refs",),
        label_pack_refs=("label_pack:seed_refs",),
    )
    for field_name in AGENT_TOOL_RESULT_FIELDS:
        value = getattr(result, field_name)
        values = value if isinstance(value, tuple) else (value,)
        for item in values:
            if item is None or isinstance(item, AgentToolStatus):
                continue
            lowered = item.lower()
            assert not any(marker in lowered for marker in FORBIDDEN_PAYLOAD_MARKERS)
            assert not any(suffix in lowered for suffix in FORBIDDEN_HEAVY_SUFFIXES)


def test_role_imports_consumed_runtime_primitives_without_reimplementing_them() -> None:
    module = importlib.import_module(MODULE_NAME)

    assert module.CONSUMED_RUNTIME_PRIMITIVES == (
        RuntimeToolResult,
        RuntimeRunSummary,
        runtime_cli.run_plan,
        runtime_cli.run_validate_inputs,
        runtime_cli.run_diagnostics,
        runtime_cli.run_label_diagnostics,
        runtime_cli.run_signal_probe_command,
        runtime_cli.run_cost_stress,
        runtime_cli.run_build_evidence_draft,
        runtime_cli.run_build_reference_handoff,
    )

    source_text = Path(module.__file__).read_text(encoding="utf-8")
    assert "class RuntimeToolResult" not in source_text
    assert "class RuntimeRunSummary" not in source_text
    assert "def run_diagnostics" not in source_text
    for forbidden_reader in (
        "read_parquet",
        "to_parquet",
        "databento",
        "ib_insync",
        "ibapi",
    ):
        assert forbidden_reader not in source_text


def test_reviewer_independence_and_handoff_shape_are_declared() -> None:
    role = _registered_role()

    independence_text = " ".join(role.reviewer_independence).lower()
    assert "runner_must_not_equal_promoter" in independence_text
    assert "runner_must_not_equal_statistical_reviewer" in independence_text
    assert "self_review" in independence_text
    assert "agent-p16" in independence_text

    handoff_text = " ".join(role.handoff_format).lower()
    for required in (
        "decision_to_tool_invocation_to_spec_ids",
        "alpha_spec_id",
        "study_spec_id",
        "dataset_version_id",
        "runtime_tool_invocation_refs",
        "blocking_findings",
        "rejection_reasons",
        "next_required_gate",
        "limitations",
    ):
        assert required in handoff_text


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
