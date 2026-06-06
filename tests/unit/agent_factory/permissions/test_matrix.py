from __future__ import annotations

import pytest

from alpha_system.agent_factory.permissions import matrix
from alpha_system.agent_factory.permissions.model import RolePermissions

ROSTER = {
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


def test_matrix_has_exactly_one_entry_per_roster_role() -> None:
    assert set(matrix.role_ids()) == ROSTER
    assert len(matrix.all_permissions()) == len(ROSTER)
    assert {entry.role_id for entry in matrix.all_permissions()} == ROSTER


def test_permission_lookup_fails_closed_for_unknown_or_empty_role_id() -> None:
    with pytest.raises(KeyError):
        matrix.permission_for("nonexistent_role")

    with pytest.raises(ValueError):
        matrix.permission_for("")

    with pytest.raises(ValueError):
        matrix.permission_for("  ")


def test_lookup_returns_immutable_role_permissions() -> None:
    permissions = matrix.permission_for("diagnostics_runner")

    assert isinstance(permissions, RolePermissions)
    assert permissions.role_id == "diagnostics_runner"
    assert permissions.tool.allows("runtime.run_diagnostics")
    assert not permissions.tool.allows("alphaspec.draft")


def test_no_matrix_entry_grants_raw_data_or_direct_registry_write() -> None:
    for permissions in matrix.all_permissions():
        assert not permissions.data.raw_provider_access
        assert not permissions.write.direct_registry_write
        assert all("raw" not in scope for scope in permissions.data.allowed_scopes)
        assert all("provider" not in scope for scope in permissions.data.allowed_scopes)
        assert all(
            "direct_registry" not in scope
            for scope in permissions.write.allowed_scopes
        )


def test_no_role_has_promotion_permission() -> None:
    for permissions in matrix.all_permissions():
        assert not permissions.promotion.can_promote


def test_review_permission_is_confined_to_independent_reviewer_roles() -> None:
    review_roles = {
        permissions.role_id
        for permissions in matrix.all_permissions()
        if permissions.review.can_issue_verdict
    }

    assert review_roles == {"alpha_spec_critic", "statistical_reviewer"}
    assert matrix.permission_for("alpha_spec_critic").review.allows_scope(
        "alphaspec_critique"
    )
    assert matrix.permission_for("statistical_reviewer").review.allows_scope(
        "runtime_evidence_review"
    )
    assert not matrix.permission_for("hypothesis_scout").review.can_issue_verdict
    assert not matrix.permission_for("feature_engineer").review.can_issue_verdict
    assert not matrix.permission_for("label_engineer").review.can_issue_verdict


def test_accepted_dataset_version_only_data_grants_are_explicit() -> None:
    data_roles = {
        permissions.role_id
        for permissions in matrix.all_permissions()
        if permissions.data.allowed_scopes
    }

    assert {
        "data_contract_auditor",
        "feature_engineer",
        "label_engineer",
        "diagnostics_runner",
    } <= data_roles
    for role_id in data_roles:
        permissions = matrix.permission_for(role_id)
        assert permissions.data.accepted_dataset_versions_only
        assert permissions.data.allows_scope("accepted_dataset_version_ref")


def test_human_approval_and_red_lane_flags_cover_reserved_actions() -> None:
    for permissions in matrix.all_permissions():
        assert permissions.human_approval.requires("risk_judgment")
        assert permissions.human_approval.requires("capital_allocation")
        assert permissions.human_approval.requires("factor_promotion")
        assert permissions.human_approval.requires("paper_trading")
        assert permissions.human_approval.requires("live_trading")
        assert permissions.human_approval.requires("broker_operation")
        assert permissions.human_approval.requires("order_routing")

        assert permissions.red_lane.requires("external_provider_call")
        assert permissions.red_lane.requires("production_deployment")
        assert permissions.red_lane.requires("paper_trading")
        assert permissions.red_lane.requires("live_trading")
        assert permissions.red_lane.requires("broker_operation")
        assert permissions.red_lane.requires("order_routing")


def test_matrix_exports_read_only_mapping() -> None:
    with pytest.raises(TypeError):
        mapping = matrix.PERMISSIONS_BY_ROLE_ID
        mapping["new_role"] = RolePermissions.default_deny("new_role")  # type: ignore[index]
