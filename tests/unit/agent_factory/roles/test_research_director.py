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

MODULE_NAME = "alpha_system.agent_factory.roles.research_director"
ROLE_ID = "research_director"
EXPECTED_TOOLS = ("queue.scope_task", "queue.assign_roles", "queue.set_budget")


def test_module_imports_and_registers_research_director_once() -> None:
    before_ids = set(registry_module.role_ids())

    module = importlib.import_module(MODULE_NAME)

    after_ids = registry_module.role_ids()
    assert set(after_ids).difference(before_ids) <= {ROLE_ID}
    assert after_ids.count(ROLE_ID) == 1
    registered = registry_module.get(ROLE_ID)
    assert registered == module.RESEARCH_DIRECTOR_ROLE
    assert registered.role_id == ROLE_ID


def test_repeated_import_or_reload_does_not_duplicate_registration() -> None:
    module = importlib.import_module(MODULE_NAME)

    importlib.import_module(MODULE_NAME)
    reloaded = importlib.reload(module)

    assert registry_module.role_ids().count(ROLE_ID) == 1
    assert registry_module.get(ROLE_ID) == reloaded.RESEARCH_DIRECTOR_ROLE


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
            assert not any(marker in lowered for marker in FORBIDDEN_PAYLOAD_MARKERS)
            assert not any(suffix in lowered for suffix in FORBIDDEN_HEAVY_SUFFIXES)


def test_callable_tools_match_permission_matrix_without_review_or_promotion() -> None:
    role = _registered_role()
    matrix_tools = permission_for(ROLE_ID).tool.allowed_tool_ids

    assert role.callable_tools == EXPECTED_TOOLS
    assert role.callable_tools == matrix_tools
    assert not any(tool.startswith(("review.", "promotion.")) for tool in role.callable_tools)
    assert "review.issue_verdict" not in role.callable_tools
    assert "promotion.review" not in role.callable_tools


def test_forbidden_decisions_cover_out_of_scope_authority() -> None:
    forbidden = " ".join(_registered_role().forbidden_decisions).lower()

    for required_fragment in (
        "approving its own scoping as evidence",
        "promoting any factor or candidate",
        "issuing review verdicts",
        "implementing code",
        "drafting alphaspecs",
        "critiquing alphaspecs",
        "running diagnostics",
        "starting alpha search",
        "continuous loop",
        "bypassing queue or budget bounds",
        "reading raw provider data",
        "external provider calls",
        "capital risk or live decisions",
    ):
        assert required_fragment in forbidden


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
