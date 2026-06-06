from __future__ import annotations

from collections.abc import Callable
from dataclasses import FrozenInstanceError, replace

import pytest

from alpha_system.agent_factory.permissions.model import (
    DataPermission,
    HumanApprovalRequired,
    PromotionPermission,
    RedLaneRequired,
    ReviewPermission,
    RolePermissions,
    ToolPermission,
    WritePermission,
)


def test_role_permissions_default_deny_constructor() -> None:
    permissions = RolePermissions.default_deny("synthetic_role")

    assert permissions.role_id == "synthetic_role"
    assert permissions.is_default_deny
    assert not permissions.tool.allows("runtime.plan")
    assert not permissions.data.allows_scope("accepted_dataset_version_ref")
    assert not permissions.write.allows_scope("agent_record.write")
    assert not permissions.review.can_issue_verdict
    assert not permissions.promotion.can_promote


def test_permission_primitives_are_immutable() -> None:
    permission = ToolPermission(("runtime.plan",))

    with pytest.raises(FrozenInstanceError):
        permission.allowed_tool_ids = ()  # type: ignore[misc]


@pytest.mark.parametrize(
    "factory",
    [
        lambda: ToolPermission(["runtime.plan"]),  # type: ignore[arg-type]
        lambda: DataPermission(["accepted_dataset_version_ref"]),  # type: ignore[arg-type]
        lambda: WritePermission(["agent_record.write"]),  # type: ignore[arg-type]
        lambda: HumanApprovalRequired(["capital_allocation"]),  # type: ignore[arg-type]
        lambda: RedLaneRequired(["external_provider_call"]),  # type: ignore[arg-type]
    ],
)
def test_permission_primitives_reject_mutable_collections(
    factory: Callable[[], object],
) -> None:
    with pytest.raises(TypeError):
        factory()


@pytest.mark.parametrize(
    "bad_value",
    [
        "raw_payload",
        "provider_payload",
        "db_rows",
        "data/raw/example",
        "metadata/example",
        "artifacts/example",
    ],
)
def test_permission_primitives_reject_payload_markers(bad_value: str) -> None:
    with pytest.raises(ValueError):
        ToolPermission((bad_value,))


@pytest.mark.parametrize(
    "bad_scope",
    [
        "raw_access",
        "raw_provider_access",
        "provider_file_ref",
        "direct_file_reader",
        "local_file_reader",
    ],
)
def test_data_permission_rejects_raw_or_provider_scope(bad_scope: str) -> None:
    with pytest.raises(ValueError):
        DataPermission((bad_scope,), accepted_dataset_versions_only=True)


def test_data_permission_requires_accepted_dataset_version_only_grant() -> None:
    with pytest.raises(ValueError):
        DataPermission(("accepted_dataset_version_ref",))

    permission = DataPermission(
        ("accepted_dataset_version_ref",),
        accepted_dataset_versions_only=True,
    )
    assert permission.allows_scope("accepted_dataset_version_ref")
    assert not permission.raw_provider_access


def test_data_permission_rejects_raw_provider_boolean_grant() -> None:
    with pytest.raises(ValueError):
        DataPermission(raw_provider_access=True)


@pytest.mark.parametrize(
    "bad_scope",
    [
        "direct_registry.write",
        "registry.write.direct",
        "featurestore.direct",
        "labelstore.direct",
        "datasetversion_registry.direct",
    ],
)
def test_write_permission_rejects_direct_registry_scope(bad_scope: str) -> None:
    with pytest.raises(ValueError):
        WritePermission((bad_scope,))


def test_write_permission_rejects_direct_registry_boolean_grant() -> None:
    with pytest.raises(ValueError):
        WritePermission(direct_registry_write=True)


def test_review_permission_requires_explicit_independent_scope() -> None:
    with pytest.raises(ValueError):
        ReviewPermission(can_issue_verdict=True)

    with pytest.raises(ValueError):
        ReviewPermission(verdict_scopes=("runtime_evidence_review",))

    with pytest.raises(ValueError):
        ReviewPermission(
            can_issue_verdict=True,
            verdict_scopes=("runtime_evidence_review",),
            independence_required=False,
        )

    permission = ReviewPermission(
        can_issue_verdict=True,
        verdict_scopes=("runtime_evidence_review",),
    )
    assert permission.allows_scope("runtime_evidence_review")


def test_promotion_permission_fails_closed_on_grant() -> None:
    assert not PromotionPermission().can_promote

    with pytest.raises(ValueError):
        PromotionPermission(can_promote=True)


def test_role_permissions_rejects_malformed_role_id_or_wrong_primitive() -> None:
    with pytest.raises(ValueError):
        RolePermissions.default_deny("BadRole")

    with pytest.raises(TypeError):
        RolePermissions(role_id="synthetic_role", tool=object())  # type: ignore[arg-type]


def test_role_permissions_replace_validates_fail_closed() -> None:
    permissions = RolePermissions.default_deny("synthetic_role")

    with pytest.raises(ValueError):
        replace(permissions, data=DataPermission(("accepted_dataset_version_ref",)))
