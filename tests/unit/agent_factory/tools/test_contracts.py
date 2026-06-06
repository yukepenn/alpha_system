from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from alpha_system.agent_factory.tools.contracts import (
    REQUIRED_FORBIDDEN_SIDE_EFFECTS,
    ToolArtifactPolicy,
    ToolContract,
    ToolContractStatus,
    ToolGroup,
)
from alpha_system.agent_factory.tools.registry import all_contracts
from alpha_system.agent_factory.tools.results import AgentToolResult


def test_tool_contract_accepts_complete_value_free_contract() -> None:
    contract = valid_contract()

    assert contract.name == "runtime.run_diagnostics"
    assert contract.group is ToolGroup.RUNTIME
    assert contract.allowed_callers == ("diagnostics_runner",)
    assert contract.permission_matrix_refs == ("runtime.run_diagnostics",)
    assert contract.output_schema is AgentToolResult
    assert contract.artifact_policy is ToolArtifactPolicy.LOCAL_ONLY
    assert contract.status is ToolContractStatus.MVP
    assert contract.allows("diagnostics_runner")
    assert contract.forbids("direct_registry_write")


def test_tool_contract_is_immutable() -> None:
    contract = valid_contract()

    with pytest.raises(FrozenInstanceError):
        contract.name = "runtime.plan"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    [
        ("name", "runtime"),
        ("group", "review"),
        ("allowed_callers", ()),
        ("permission_matrix_refs", ()),
        ("required_inputs", ()),
        ("output_schema", str),
        ("forbidden_side_effects", ("direct_registry_write",)),
        ("artifact_policy", "committed"),
        ("failure_states", ()),
        ("required_reviewer", ""),
        ("reviewer_independence_note", ""),
        ("status", "implemented"),
    ],
)
def test_tool_contract_required_fields_fail_closed(
    field_name: str,
    bad_value: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        replace(valid_contract(), **{field_name: bad_value})


def test_tool_contract_rejects_unknown_or_permissionless_callers() -> None:
    with pytest.raises(ValueError, match="unknown roster"):
        replace(valid_contract(), allowed_callers=("unknown_role",))

    with pytest.raises(ValueError, match="matching P04 tool ref"):
        replace(
            valid_contract(),
            allowed_callers=("hypothesis_scout",),
            permission_matrix_refs=("runtime.run_diagnostics",),
        )


def test_all_registered_contracts_are_complete_agent_tool_result_contracts() -> None:
    for contract in all_contracts():
        assert contract.allowed_callers
        assert contract.permission_matrix_refs
        assert contract.required_inputs
        assert contract.output_schema is AgentToolResult
        assert contract.artifact_policy is ToolArtifactPolicy.LOCAL_ONLY
        assert contract.failure_states
        assert contract.required_reviewer
        assert contract.reviewer_independence_note
        assert contract.status in {
            ToolContractStatus.MVP,
            ToolContractStatus.TARGET,
            ToolContractStatus.FUTURE,
        }
        for side_effect in REQUIRED_FORBIDDEN_SIDE_EFFECTS:
            assert contract.forbids(side_effect)


def valid_contract() -> ToolContract:
    return ToolContract(
        name="runtime.run_diagnostics",
        group=ToolGroup.RUNTIME,
        allowed_callers=("diagnostics_runner",),
        permission_matrix_refs=("runtime.run_diagnostics",),
        required_inputs=("request_id", "study_spec_id", "dataset_version_id"),
        output_schema=AgentToolResult,
        forbidden_side_effects=REQUIRED_FORBIDDEN_SIDE_EFFECTS,
        artifact_policy=ToolArtifactPolicy.LOCAL_ONLY,
        failure_states=("diagnostics_not_executed", "permission_denied"),
        required_reviewer="statistical_reviewer",
        reviewer_independence_note="Diagnostics runner cannot review its own output.",
        status=ToolContractStatus.MVP,
    )
