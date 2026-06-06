from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from alpha_system.agent_factory.permissions.matrix import (
    HUMAN_APPROVAL_ACTIONS,
    PERMISSIONS_BY_ROLE_ID,
    RED_LANE_ACTIONS,
    ROSTER_ROLE_IDS,
)
from alpha_system.agent_factory.roles.contracts import AgentRole
from alpha_system.agent_factory.separation.enforcement import (
    GENERATOR_APPROVER_RULE,
    HUMAN_RESERVED_FLAGS_RULE,
    IMPLEMENTER_REVIEWER_RULE,
    LIBRARIAN_VERDICT_RULE,
    PERMISSION_MATRIX_COVERAGE_RULE,
    PROMOTION_PERMISSION_RULE,
    REVIEWER_ASSIGNMENT_RULE,
    SeparationStatus,
)
from alpha_system.agent_factory.separation.wiring import (
    CONCRETE_ROLE_MODULES,
    EXPECTED_MVP_ROLE_IDS,
    SeparationWiringError,
    assemble_validated_bundle,
)


def test_wiring_assembles_exactly_ten_mvp_roles_with_matrix_entries() -> None:
    bundle = assemble_validated_bundle()

    assert bundle.status is SeparationStatus.PASS
    assert set(bundle.role_ids) == set(ROSTER_ROLE_IDS)
    assert len(bundle.role_ids) == 10
    assert set(bundle.permissions_by_role_id) == set(ROSTER_ROLE_IDS)
    assert not bundle.blocked_results
    for role_id in ROSTER_ROLE_IDS:
        role = bundle.roles_by_id[role_id]
        permissions = bundle.permissions_by_role_id[role_id]
        assert isinstance(role, AgentRole)
        assert permissions.role_id == role_id


def test_wiring_imports_all_ten_concrete_role_modules_in_one_place() -> None:
    module_names = {module.__name__.rsplit(".", 1)[-1] for module in CONCRETE_ROLE_MODULES}

    assert EXPECTED_MVP_ROLE_IDS == ROSTER_ROLE_IDS
    assert module_names == set(ROSTER_ROLE_IDS)
    assert len(CONCRETE_ROLE_MODULES) == 10

    roles_package = Path("src/alpha_system/agent_factory/roles/__init__.py")
    registry_module = Path("src/alpha_system/agent_factory/roles/registry.py")
    combined_text = (
        roles_package.read_text(encoding="utf-8")
        + "\n"
        + registry_module.read_text(encoding="utf-8")
    )
    assert not any(role_id in combined_text for role_id in ROSTER_ROLE_IDS)


def test_wiring_runs_all_required_rule_families() -> None:
    bundle = assemble_validated_bundle()
    rule_ids = {result.rule_id for result in bundle.rule_results}

    assert {
        GENERATOR_APPROVER_RULE,
        IMPLEMENTER_REVIEWER_RULE,
        PROMOTION_PERMISSION_RULE,
        REVIEWER_ASSIGNMENT_RULE,
        LIBRARIAN_VERDICT_RULE,
        PERMISSION_MATRIX_COVERAGE_RULE,
        HUMAN_RESERVED_FLAGS_RULE,
    } <= rule_ids
    assert all(result.status is SeparationStatus.PASS for result in bundle.rule_results)


def test_wiring_fails_closed_when_role_is_missing() -> None:
    bundle = assemble_validated_bundle()
    missing_librarian_roles = tuple(
        role for role in bundle.roles_by_id.values() if role.role_id != "librarian"
    )

    blocked = assemble_validated_bundle(
        roles=missing_librarian_roles,
        raise_on_blocked=False,
    )

    assert blocked.status is SeparationStatus.BLOCKED
    assert any(
        result.rule_id == PERMISSION_MATRIX_COVERAGE_RULE
        and result.status is SeparationStatus.BLOCKED
        for result in blocked.rule_results
    )
    with pytest.raises(SeparationWiringError):
        assemble_validated_bundle(roles=missing_librarian_roles)


def test_wiring_fails_closed_when_permission_entry_is_missing() -> None:
    incomplete = dict(PERMISSIONS_BY_ROLE_ID)
    incomplete.pop("diagnostics_runner")

    blocked = assemble_validated_bundle(
        permissions_by_role_id=incomplete,
        raise_on_blocked=False,
    )

    assert blocked.status is SeparationStatus.BLOCKED
    assert any(
        result.rule_id == PERMISSION_MATRIX_COVERAGE_RULE
        and result.role_ids == ("diagnostics_runner",)
        for result in blocked.rule_results
    )


def test_wiring_fails_closed_on_any_promotion_grant() -> None:
    permissions = dict(PERMISSIONS_BY_ROLE_ID)
    diagnostics = permissions["diagnostics_runner"]
    permissions["diagnostics_runner"] = SimpleNamespace(
        role_id="diagnostics_runner",
        tool=diagnostics.tool,
        data=diagnostics.data,
        write=diagnostics.write,
        review=diagnostics.review,
        promotion=SimpleNamespace(can_promote=True),
        human_approval=diagnostics.human_approval,
        red_lane=diagnostics.red_lane,
    )

    blocked = assemble_validated_bundle(
        permissions_by_role_id=permissions,
        raise_on_blocked=False,
    )

    assert blocked.status is SeparationStatus.BLOCKED
    assert any(
        result.rule_id == PROMOTION_PERMISSION_RULE
        and result.role_ids == ("diagnostics_runner",)
        for result in blocked.rule_results
    )


def test_wiring_preserves_human_approval_and_red_lane_flags() -> None:
    bundle = assemble_validated_bundle()

    for permissions in bundle.permissions_by_role_id.values():
        for action in HUMAN_APPROVAL_ACTIONS:
            assert permissions.human_approval.requires(action)
        for action in RED_LANE_ACTIONS:
            assert permissions.red_lane.requires(action)


def test_wiring_fails_closed_when_human_reserved_flag_is_removed() -> None:
    permissions = dict(PERMISSIONS_BY_ROLE_ID)
    permissions["librarian"] = replace(
        permissions["librarian"],
        human_approval=replace(
            permissions["librarian"].human_approval,
            required_actions=("risk_judgment",),
        ),
    )

    blocked = assemble_validated_bundle(
        permissions_by_role_id=permissions,
        raise_on_blocked=False,
    )

    assert blocked.status is SeparationStatus.BLOCKED
    assert any(
        result.rule_id == HUMAN_RESERVED_FLAGS_RULE
        and result.role_ids == ("librarian",)
        for result in blocked.rule_results
    )


def test_wiring_fails_closed_when_librarian_has_no_verdict_gated_write() -> None:
    permissions = dict(PERMISSIONS_BY_ROLE_ID)
    permissions["librarian"] = replace(
        permissions["librarian"],
        write=replace(permissions["librarian"].write, allowed_scopes=()),
    )

    blocked = assemble_validated_bundle(
        permissions_by_role_id=permissions,
        raise_on_blocked=False,
    )

    assert blocked.status is SeparationStatus.BLOCKED
    assert any(
        result.rule_id == LIBRARIAN_VERDICT_RULE
        and result.role_ids == ("librarian",)
        for result in blocked.rule_results
    )
