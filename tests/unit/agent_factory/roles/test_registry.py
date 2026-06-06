from __future__ import annotations

from pathlib import Path

import pytest

import alpha_system.agent_factory.roles as roles_package
import alpha_system.agent_factory.roles.registry as registry_module
from alpha_system.agent_factory.roles.contracts import AgentRole
from alpha_system.agent_factory.roles.registry import RoleRegistry


def test_registry_discovers_registered_role() -> None:
    registry = RoleRegistry()
    role = valid_role("scoped_role")

    registered = registry.register(role)

    assert registered is role
    assert registry.get("scoped_role") is role
    assert registry.all_roles() == (role,)
    assert registry.role_ids() == ("scoped_role",)


def test_module_level_registry_supports_import_time_self_registration() -> None:
    role = valid_role("module_level_role")

    registered = registry_module.register(role)

    assert registered is role
    assert registry_module.get("module_level_role") is role
    assert "module_level_role" in registry_module.role_ids()


def test_registry_rejects_duplicate_role_ids() -> None:
    registry = RoleRegistry()
    registry.register(valid_role("duplicate_role"))

    with pytest.raises(ValueError):
        registry.register(valid_role("duplicate_role"))


def test_registry_rejects_malformed_contract() -> None:
    registry = RoleRegistry()

    with pytest.raises(TypeError):
        registry.register(object())  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        valid_role("bad_heavy_ref", readable_inputs=("data/cache/example.feather",))


def test_registry_and_package_import_no_concrete_role_modules() -> None:
    package_text = Path(roles_package.__file__).read_text(encoding="utf-8")
    registry_text = Path(registry_module.__file__).read_text(encoding="utf-8")
    combined = f"{package_text}\n{registry_text}"

    concrete_role_modules = {
        "research_director",
        "hypothesis_scout",
        "alpha_spec_critic",
        "data_contract_auditor",
        "feature_engineer",
        "label_engineer",
        "no_lookahead_auditor",
        "diagnostics_runner",
        "statistical_reviewer",
        "librarian",
    }
    assert not any(module_name in combined for module_name in concrete_role_modules)


def valid_role(
    role_id: str,
    *,
    readable_inputs: tuple[str, ...] = ("handoff_ref",),
) -> AgentRole:
    return AgentRole(
        role_id=role_id,
        name="Scoped Role",
        purpose="Declare one scoped role contract.",
        readable_inputs=readable_inputs,
        callable_tools=("tool.ref",),
        producible_outputs=("output_ref",),
        allowed_decisions=("request_revision",),
        forbidden_decisions=("self_approval", "self_promotion", "registry_write"),
        handoff_format=("summary", "decision"),
        reviewer_independence=("drafter != approver",),
        failure_modes=("malformed_contract",),
    )
