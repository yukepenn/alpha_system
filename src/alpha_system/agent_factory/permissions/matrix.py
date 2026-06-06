"""Static Agent Factory role permission matrix."""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

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

ROSTER_ROLE_IDS: tuple[str, ...] = (
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
)
REVIEW_ROLE_IDS: frozenset[str] = frozenset(
    {"alpha_spec_critic", "statistical_reviewer"}
)
HUMAN_APPROVAL_ACTIONS: tuple[str, ...] = (
    "risk_judgment",
    "capital_allocation",
    "factor_promotion",
    "paper_trading",
    "live_trading",
    "broker_operation",
    "order_routing",
)
RED_LANE_ACTIONS: tuple[str, ...] = (
    "external_provider_call",
    "production_deployment",
    "paper_trading",
    "live_trading",
    "broker_operation",
    "order_routing",
)

_HUMAN_APPROVAL_REQUIRED = HumanApprovalRequired(HUMAN_APPROVAL_ACTIONS)
_RED_LANE_REQUIRED = RedLaneRequired(RED_LANE_ACTIONS)


def _entry(
    *,
    role_id: str,
    tools: tuple[str, ...],
    data_scopes: tuple[str, ...] = (),
    write_scopes: tuple[str, ...] = (),
    review_scopes: tuple[str, ...] = (),
) -> RolePermissions:
    return RolePermissions(
        role_id=role_id,
        tool=ToolPermission(tools),
        data=DataPermission(
            allowed_scopes=data_scopes,
            accepted_dataset_versions_only=bool(data_scopes),
        ),
        write=WritePermission(write_scopes),
        review=ReviewPermission(
            can_issue_verdict=bool(review_scopes),
            verdict_scopes=review_scopes,
        ),
        promotion=PromotionPermission(),
        human_approval=_HUMAN_APPROVAL_REQUIRED,
        red_lane=_RED_LANE_REQUIRED,
    )


_MATRIX: dict[str, RolePermissions] = {
    "research_director": _entry(
        role_id="research_director",
        tools=("queue.scope_task", "queue.assign_roles", "queue.set_budget"),
        write_scopes=("research_task.scope_draft",),
    ),
    "hypothesis_scout": _entry(
        role_id="hypothesis_scout",
        tools=(
            "memory.lookup_rejected_ideas",
            "library.summarize_prior_work",
            "alphaspec.draft",
        ),
        write_scopes=("alphaspec.draft",),
    ),
    "alpha_spec_critic": _entry(
        role_id="alpha_spec_critic",
        tools=(
            "alphaspec.critique",
            "alphaspec.request_revision",
            "alphaspec.reject",
        ),
        write_scopes=("alphaspec.critique_record",),
        review_scopes=("alphaspec_critique",),
    ),
    "data_contract_auditor": _entry(
        role_id="data_contract_auditor",
        tools=(
            "registry.resolve_dataset_version",
            "registry.list_feature_packs",
            "registry.list_label_packs",
            "registry.audit_admissibility",
        ),
        data_scopes=(
            "accepted_dataset_version_ref",
            "feature_pack_ref",
            "label_pack_ref",
        ),
        write_scopes=("input_audit.record",),
    ),
    "feature_engineer": _entry(
        role_id="feature_engineer",
        tools=(
            "feature.reference_seed_pack",
            "feature.draft_request",
            "feature.validate_request",
        ),
        data_scopes=("accepted_dataset_version_ref", "feature_pack_ref"),
        write_scopes=("feature_request.draft",),
    ),
    "label_engineer": _entry(
        role_id="label_engineer",
        tools=(
            "label.reference_seed_pack",
            "label.draft_spec",
            "label.validate_spec",
        ),
        data_scopes=("accepted_dataset_version_ref", "label_pack_ref"),
        write_scopes=("label_spec.draft",),
    ),
    "no_lookahead_auditor": _entry(
        role_id="no_lookahead_auditor",
        tools=("runtime.audit_no_lookahead", "governance.check_label_leakage"),
        write_scopes=("lookahead_audit.record",),
    ),
    "diagnostics_runner": _entry(
        role_id="diagnostics_runner",
        tools=(
            "runtime.plan",
            "runtime.validate_inputs",
            "runtime.run_diagnostics",
            "runtime.run_label_diagnostics",
            "runtime.run_signal_probe",
            "runtime.run_cost_stress",
            "runtime.summarize",
        ),
        data_scopes=("accepted_dataset_version_ref",),
        write_scopes=("runtime_request.record",),
    ),
    "statistical_reviewer": _entry(
        role_id="statistical_reviewer",
        tools=("review.statistical_evidence", "review.issue_verdict"),
        write_scopes=("statistical_review.record",),
        review_scopes=("runtime_evidence_review",),
    ),
    "librarian": _entry(
        role_id="librarian",
        tools=(
            "ledger.record_decision",
            "ledger.record_rejection",
            "memory.lookup_rejected_ideas",
            "memory.propose_update",
        ),
        write_scopes=(
            "decision_ledger.record_after_verdict",
            "memory_update.proposal_after_verdict",
        ),
    ),
}

PERMISSIONS_BY_ROLE_ID: Mapping[str, RolePermissions] = MappingProxyType(_MATRIX)


def permission_for(role_id: str) -> RolePermissions:
    """Return permissions for a known role, failing closed for all unknown ids."""

    if not isinstance(role_id, str) or not role_id.strip():
        raise ValueError("role_id must be a non-empty str")
    try:
        return PERMISSIONS_BY_ROLE_ID[role_id]
    except KeyError as error:
        raise KeyError(f"unknown role_id: {role_id}") from error


def role_ids() -> tuple[str, ...]:
    """Return matrix role ids in deterministic order."""

    return tuple(sorted(PERMISSIONS_BY_ROLE_ID))


def all_permissions() -> tuple[RolePermissions, ...]:
    """Return every matrix entry in deterministic role_id order."""

    return tuple(PERMISSIONS_BY_ROLE_ID[role_id] for role_id in role_ids())


def _validate_matrix(matrix: Mapping[str, RolePermissions]) -> None:
    expected = set(ROSTER_ROLE_IDS)
    actual = set(matrix)
    if actual != expected:
        raise RuntimeError(f"permission matrix roster mismatch: {actual ^ expected}")
    if len(matrix) != len(ROSTER_ROLE_IDS):
        raise RuntimeError("permission matrix must contain exactly one entry per role")

    for role_id, permissions in matrix.items():
        if permissions.role_id != role_id:
            raise RuntimeError(f"permission entry key mismatch: {role_id}")
        if permissions.data.raw_provider_access:
            raise RuntimeError(f"raw data access grant found for {role_id}")
        if permissions.write.direct_registry_write:
            raise RuntimeError(f"direct registry write grant found for {role_id}")
        if permissions.promotion.can_promote:
            raise RuntimeError(f"promotion grant found for {role_id}")

    review_roles = {
        role_id for role_id, entry in matrix.items() if entry.review.can_issue_verdict
    }
    if review_roles != REVIEW_ROLE_IDS:
        raise RuntimeError(f"review permission mismatch: {review_roles ^ REVIEW_ROLE_IDS}")

    for role_id, permissions in matrix.items():
        for action in HUMAN_APPROVAL_ACTIONS:
            if not permissions.human_approval.requires(action):
                raise RuntimeError(f"missing human approval marker for {role_id}:{action}")
        for action in RED_LANE_ACTIONS:
            if not permissions.red_lane.requires(action):
                raise RuntimeError(f"missing red-lane marker for {role_id}:{action}")


_validate_matrix(_MATRIX)
