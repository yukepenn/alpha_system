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

MODULE_NAME = "alpha_system.agent_factory.roles.feature_engineer"
ROLE_ID = "feature_engineer"


def test_module_imports_and_registers_feature_engineer_once() -> None:
    before_ids = set(registry_module.role_ids())

    module = importlib.import_module(MODULE_NAME)

    after_ids = registry_module.role_ids()
    assert set(after_ids).difference(before_ids) <= {ROLE_ID}
    assert after_ids.count(ROLE_ID) == 1
    registered = registry_module.get(ROLE_ID)
    assert registered == module.FEATURE_ENGINEER_ROLE
    assert registered.role_id == ROLE_ID


def test_repeated_import_or_reload_does_not_duplicate_registration() -> None:
    module = importlib.import_module(MODULE_NAME)

    importlib.import_module(MODULE_NAME)
    reloaded = importlib.reload(module)

    assert registry_module.role_ids().count(ROLE_ID) == 1
    assert registry_module.get(ROLE_ID) == reloaded.FEATURE_ENGINEER_ROLE


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

    assert role.callable_tools == permissions.tool.allowed_tool_ids
    assert role.callable_tools == (
        "feature.reference_seed_pack",
        "feature.draft_request",
        "feature.validate_request",
    )
    assert permissions.data.accepted_dataset_versions_only
    assert permissions.data.allowed_scopes == (
        "accepted_dataset_version_ref",
        "feature_pack_ref",
    )
    assert permissions.write.allowed_scopes == ("feature_request.draft",)
    assert not permissions.write.direct_registry_write
    assert not permissions.review.can_issue_verdict
    assert not permissions.promotion.can_promote
    assert not permissions.data.raw_provider_access
    assert not any(
        marker in tool_id
        for tool_id in role.callable_tools
        for marker in (
            "materialize",
            "runtime.",
            "review.",
            "promotion.",
            "broker",
            "paper",
            "live",
        )
    )


def test_forbidden_decisions_cover_required_boundaries_and_blockers() -> None:
    forbidden = " ".join(_registered_role().forbidden_decisions).lower()

    for required_fragment in (
        "self-review",
        "promotion",
        "broad feature materialization",
        "value commits",
        "accepted datasetversion",
        "label-as-feature",
        "raw provider",
        "external provider",
        "runtime bypass",
        "session_label_guard_fix_v1",
        "feature_label_parquet_sink_v1",
        "tradability",
    ):
        assert required_fragment in forbidden


def test_outputs_and_handoff_are_value_free_refs_only() -> None:
    role = _registered_role()
    output_text = " ".join(role.producible_outputs)
    handoff_text = " ".join(role.handoff_format)

    for expected in (
        "AgentToolResult artifact ref",
        "FeatureRequest draft",
        "approved seed feature reference",
        "request_id",
        "alpha_spec_id",
        "dataset_version_id",
        "feature_pack_refs",
        "next_required_gate",
        "limitations",
    ):
        assert expected in f"{output_text} {handoff_text}"

    assert "feature_request_ref or feature_pack_ref" in role.handoff_format
    assert "value" not in " ".join(role.callable_tools)


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
