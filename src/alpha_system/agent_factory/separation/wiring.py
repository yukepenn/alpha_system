"""Validated Agent Factory role and permission wiring for separation checks."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType, ModuleType

from alpha_system.agent_factory.permissions.matrix import (
    HUMAN_APPROVAL_ACTIONS,
    PERMISSIONS_BY_ROLE_ID,
    RED_LANE_ACTIONS,
    ROSTER_ROLE_IDS,
)
from alpha_system.agent_factory.permissions.model import RolePermissions
from alpha_system.agent_factory.roles import alpha_spec_critic as _alpha_spec_critic
from alpha_system.agent_factory.roles import data_contract_auditor as _data_contract_auditor
from alpha_system.agent_factory.roles import diagnostics_runner as _diagnostics_runner
from alpha_system.agent_factory.roles import feature_engineer as _feature_engineer
from alpha_system.agent_factory.roles import hypothesis_scout as _hypothesis_scout
from alpha_system.agent_factory.roles import label_engineer as _label_engineer
from alpha_system.agent_factory.roles import librarian as _librarian
from alpha_system.agent_factory.roles import no_lookahead_auditor as _no_lookahead_auditor
from alpha_system.agent_factory.roles import registry as role_registry
from alpha_system.agent_factory.roles import research_director as _research_director
from alpha_system.agent_factory.roles import statistical_reviewer as _statistical_reviewer
from alpha_system.agent_factory.roles.contracts import AgentRole
from alpha_system.agent_factory.separation.enforcement import (
    GENERATOR_APPROVER_RULE,
    IMPLEMENTER_REVIEWER_RULE,
    LIBRARIAN_VERDICT_RULE,
    REVIEWER_ASSIGNMENT_RULE,
    SeparationRuleResult,
    SeparationStatus,
    blocked_results,
    check_generator_approver_separation,
    check_human_reserved_flags_preserved,
    check_implementer_reviewer_separation,
    check_librarian_verdict_required,
    check_no_promotion_permission,
    check_permission_matrix_coverage,
    check_reviewer_assignment_independent,
    overall_status,
)

CONCRETE_ROLE_MODULES: tuple[ModuleType, ...] = (
    _research_director,
    _hypothesis_scout,
    _alpha_spec_critic,
    _data_contract_auditor,
    _feature_engineer,
    _label_engineer,
    _no_lookahead_auditor,
    _diagnostics_runner,
    _statistical_reviewer,
    _librarian,
)

EXPECTED_MVP_ROLE_IDS: tuple[str, ...] = ROSTER_ROLE_IDS

GENERATOR_APPROVAL_ASSIGNMENTS: tuple[tuple[str, str, str], ...] = (
    ("alphaspec_draft", "hypothesis_scout", "alpha_spec_critic"),
)

IMPLEMENTER_REVIEW_ASSIGNMENTS: tuple[tuple[str, str, str], ...] = (
    ("feature_request", "feature_engineer", "no_lookahead_auditor"),
    ("label_spec", "label_engineer", "no_lookahead_auditor"),
    ("runtime_evidence", "diagnostics_runner", "statistical_reviewer"),
)

REVIEWER_ASSIGNMENTS: tuple[tuple[str, str, str], ...] = (
    ("alphaspec_draft_review", "hypothesis_scout", "alpha_spec_critic"),
    ("runtime_evidence_review", "diagnostics_runner", "statistical_reviewer"),
)

BOUND_VERDICT_REF = "reviewer_verdict:required"


@dataclass(frozen=True, slots=True)
class SeparationBundle:
    """Immutable validated role and permission bundle."""

    roles_by_id: Mapping[str, AgentRole]
    permissions_by_role_id: Mapping[str, RolePermissions]
    rule_results: tuple[SeparationRuleResult, ...]
    status: SeparationStatus

    @property
    def role_ids(self) -> tuple[str, ...]:
        """Return bundled role ids in deterministic order."""

        return tuple(self.roles_by_id)

    @property
    def blocked_results(self) -> tuple[SeparationRuleResult, ...]:
        """Return blocked separation results."""

        return blocked_results(self.rule_results)


class SeparationWiringError(RuntimeError):
    """Raised when the validated wiring bundle is blocked."""

    def __init__(self, results: Iterable[SeparationRuleResult]) -> None:
        blocked = blocked_results(results)
        summary = ", ".join(result.rule_id for result in blocked) or "unknown"
        super().__init__(f"separation wiring blocked: {summary}")
        self.results = tuple(results)
        self.blocked_results = blocked


def assemble_validated_bundle(
    *,
    roles: Iterable[AgentRole] | None = None,
    permissions_by_role_id: Mapping[str, RolePermissions] = PERMISSIONS_BY_ROLE_ID,
    raise_on_blocked: bool = True,
) -> SeparationBundle:
    """Assemble the ten MVP roles with permissions and enforce separation rules."""

    bundled_roles = tuple(roles) if roles is not None else _registered_mvp_roles()
    roles_by_id, role_results = _roles_by_id(bundled_roles)
    known_role_ids = tuple(roles_by_id)
    results: list[SeparationRuleResult] = [*role_results]

    results.append(
        check_permission_matrix_coverage(
            known_role_ids,
            permissions_by_role_id,
            expected_role_ids=EXPECTED_MVP_ROLE_IDS,
        )
    )
    results.extend(_generator_approval_results(known_role_ids))
    results.extend(_implementer_review_results(known_role_ids))
    results.extend(_reviewer_assignment_results(known_role_ids))
    results.append(
        check_no_promotion_permission(
            permissions_by_role_id,
            expected_role_ids=EXPECTED_MVP_ROLE_IDS,
        )
    )
    results.append(
        check_human_reserved_flags_preserved(
            permissions_by_role_id,
            expected_role_ids=EXPECTED_MVP_ROLE_IDS,
            required_human_actions=HUMAN_APPROVAL_ACTIONS,
            required_red_lane_actions=RED_LANE_ACTIONS,
        )
    )
    results.extend(_librarian_verdict_results(permissions_by_role_id, known_role_ids))

    bundle = SeparationBundle(
        roles_by_id=MappingProxyType(dict(roles_by_id)),
        permissions_by_role_id=MappingProxyType(dict(permissions_by_role_id)),
        rule_results=tuple(results),
        status=overall_status(results),
    )
    if raise_on_blocked and bundle.status is SeparationStatus.BLOCKED:
        raise SeparationWiringError(bundle.rule_results)
    return bundle


def _registered_mvp_roles() -> tuple[AgentRole, ...]:
    return tuple(role_registry.get(role_id) for role_id in EXPECTED_MVP_ROLE_IDS)


def _roles_by_id(
    roles: tuple[AgentRole, ...],
) -> tuple[dict[str, AgentRole], tuple[SeparationRuleResult, ...]]:
    by_id: dict[str, AgentRole] = {}
    duplicate_ids: list[str] = []
    malformed_count = 0
    for role in roles:
        if not isinstance(role, AgentRole):
            malformed_count += 1
            continue
        role.validate()
        if role.role_id in by_id:
            duplicate_ids.append(role.role_id)
            continue
        by_id[role.role_id] = role

    results: list[SeparationRuleResult] = []
    if malformed_count:
        results.append(
            SeparationRuleResult.blocked(
                "role_registry_integrity",
                ("unknown",),
                "role registry contains malformed role entries",
            )
        )
    if duplicate_ids:
        results.append(
            SeparationRuleResult.blocked(
                "role_registry_integrity",
                duplicate_ids,
                "role registry contains duplicate role ids",
            )
        )
    return dict(sorted(by_id.items())), tuple(results)


def _generator_approval_results(
    known_role_ids: tuple[str, ...],
) -> tuple[SeparationRuleResult, ...]:
    return tuple(
        check_generator_approver_separation(
            artifact_class,
            generator,
            approver,
            known_role_ids=known_role_ids,
        )
        for artifact_class, generator, approver in GENERATOR_APPROVAL_ASSIGNMENTS
    ) or (
        SeparationRuleResult.blocked(
            GENERATOR_APPROVER_RULE,
            ("unknown",),
            "no generator approval assignments are declared",
        ),
    )


def _implementer_review_results(
    known_role_ids: tuple[str, ...],
) -> tuple[SeparationRuleResult, ...]:
    return tuple(
        check_implementer_reviewer_separation(
            work_item_class,
            implementer,
            reviewer,
            known_role_ids=known_role_ids,
        )
        for work_item_class, implementer, reviewer in IMPLEMENTER_REVIEW_ASSIGNMENTS
    ) or (
        SeparationRuleResult.blocked(
            IMPLEMENTER_REVIEWER_RULE,
            ("unknown",),
            "no implementer review assignments are declared",
        ),
    )


def _reviewer_assignment_results(
    known_role_ids: tuple[str, ...],
) -> tuple[SeparationRuleResult, ...]:
    return tuple(
        check_reviewer_assignment_independent(
            work_item_ref,
            implementer,
            reviewer,
            known_role_ids=known_role_ids,
        )
        for work_item_ref, implementer, reviewer in REVIEWER_ASSIGNMENTS
    ) or (
        SeparationRuleResult.blocked(
            REVIEWER_ASSIGNMENT_RULE,
            ("unknown",),
            "no reviewer assignments are declared",
        ),
    )


def _librarian_verdict_results(
    permissions_by_role_id: Mapping[str, RolePermissions],
    known_role_ids: tuple[str, ...],
) -> tuple[SeparationRuleResult, ...]:
    librarian_permissions = permissions_by_role_id.get("librarian")
    write_permission = getattr(librarian_permissions, "write", None)
    write_scopes = getattr(write_permission, "allowed_scopes", None)
    if not isinstance(write_scopes, tuple) or not write_scopes:
        return (
            SeparationRuleResult.blocked(
                LIBRARIAN_VERDICT_RULE,
                ("librarian",),
                "librarian has no verdict gated write scopes",
            ),
        )
    return tuple(
        check_librarian_verdict_required(
            "librarian",
            write_scope,
            BOUND_VERDICT_REF,
            known_role_ids=known_role_ids,
        )
        for write_scope in write_scopes
    )


__all__ = [
    "BOUND_VERDICT_REF",
    "CONCRETE_ROLE_MODULES",
    "EXPECTED_MVP_ROLE_IDS",
    "GENERATOR_APPROVAL_ASSIGNMENTS",
    "IMPLEMENTER_REVIEW_ASSIGNMENTS",
    "REVIEWER_ASSIGNMENTS",
    "SeparationBundle",
    "SeparationWiringError",
    "assemble_validated_bundle",
]
