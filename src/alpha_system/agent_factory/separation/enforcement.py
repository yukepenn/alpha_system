"""Fail-closed separation-of-duties validators for Agent Factory contracts."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from alpha_system.agent_factory.roles.contracts import (
    FORBIDDEN_HEAVY_SUFFIXES,
    FORBIDDEN_PAYLOAD_MARKERS,
    MAX_DECLARATIVE_TEXT_LENGTH,
)

_REF_PATTERN = re.compile(r"^[a-z][a-z0-9_.:-]*$")

GENERATOR_APPROVER_RULE = "generator_approver_separation"
IMPLEMENTER_REVIEWER_RULE = "implementer_reviewer_separation"
PROMOTION_PERMISSION_RULE = "promotion_permission_denied"
REVIEWER_ASSIGNMENT_RULE = "reviewer_assignment_independent"
LIBRARIAN_VERDICT_RULE = "librarian_verdict_required"
PERMISSION_MATRIX_COVERAGE_RULE = "permission_matrix_coverage"
HUMAN_RESERVED_FLAGS_RULE = "human_reserved_flags_preserved"

_UNKNOWN_REF = "unknown"
_ROLE_PERMISSION_FIELDS: tuple[str, ...] = (
    "tool",
    "data",
    "write",
    "review",
    "promotion",
    "human_approval",
    "red_lane",
)


class SeparationStatus(StrEnum):
    """Machine-readable separation check status."""

    PASS = "PASS"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class SeparationRuleResult:
    """Structured, value-free result for one separation rule evaluation."""

    rule_id: str
    status: SeparationStatus
    role_ids: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", SeparationStatus(self.status))
        _validate_ref("rule_id", self.rule_id)
        if not isinstance(self.role_ids, tuple) or not self.role_ids:
            raise ValueError("role_ids must be a non-empty tuple[str, ...]")
        for role_id in self.role_ids:
            _validate_ref("role_ids", role_id)
        _validate_reason(self.reason)

    @classmethod
    def passed(
        cls,
        rule_id: str,
        role_ids: Iterable[str],
        reason: str,
    ) -> SeparationRuleResult:
        """Build a passing value-free rule result."""

        return cls(
            rule_id=rule_id,
            status=SeparationStatus.PASS,
            role_ids=_result_refs(role_ids),
            reason=reason,
        )

    @classmethod
    def blocked(
        cls,
        rule_id: str,
        role_ids: Iterable[str],
        reason: str,
    ) -> SeparationRuleResult:
        """Build a blocked value-free rule result."""

        return cls(
            rule_id=rule_id,
            status=SeparationStatus.BLOCKED,
            role_ids=_result_refs(role_ids),
            reason=reason,
        )

    @property
    def is_pass(self) -> bool:
        """Return whether this rule passed."""

        return self.status is SeparationStatus.PASS

    @property
    def is_blocked(self) -> bool:
        """Return whether this rule blocked."""

        return self.status is SeparationStatus.BLOCKED


def check_generator_approver_separation(
    artifact_class: object,
    generator_role_id: object,
    approver_role_id: object,
    *,
    known_role_ids: Iterable[str] | None,
) -> SeparationRuleResult:
    """Reject when one role both generates and approves an artifact class."""

    artifact = _coerce_ref(artifact_class)
    generator = _coerce_ref(generator_role_id)
    approver = _coerce_ref(approver_role_id)
    roles = _result_refs((generator, approver))
    if artifact is None or generator is None or approver is None:
        return SeparationRuleResult.blocked(
            GENERATOR_APPROVER_RULE,
            roles,
            "artifact generator or approver input is missing or ambiguous",
        )

    known_block = _known_roles_block(
        GENERATOR_APPROVER_RULE,
        (generator, approver),
        known_role_ids,
    )
    if known_block is not None:
        return known_block

    if generator == approver:
        return SeparationRuleResult.blocked(
            GENERATOR_APPROVER_RULE,
            (generator,),
            f"{artifact} generator and approver are the same role",
        )

    return SeparationRuleResult.passed(
        GENERATOR_APPROVER_RULE,
        (generator, approver),
        f"{artifact} generator and approver are independent roles",
    )


def check_implementer_reviewer_separation(
    work_item_class: object,
    implementer_role_id: object,
    reviewer_role_id: object,
    *,
    known_role_ids: Iterable[str] | None,
) -> SeparationRuleResult:
    """Reject when an implementer is also the reviewer for its work class."""

    work_item = _coerce_ref(work_item_class)
    implementer = _coerce_ref(implementer_role_id)
    reviewer = _coerce_ref(reviewer_role_id)
    roles = _result_refs((implementer, reviewer))
    if work_item is None or implementer is None or reviewer is None:
        return SeparationRuleResult.blocked(
            IMPLEMENTER_REVIEWER_RULE,
            roles,
            "work item implementer or reviewer input is missing or ambiguous",
        )

    known_block = _known_roles_block(
        IMPLEMENTER_REVIEWER_RULE,
        (implementer, reviewer),
        known_role_ids,
    )
    if known_block is not None:
        return known_block

    if implementer == reviewer:
        return SeparationRuleResult.blocked(
            IMPLEMENTER_REVIEWER_RULE,
            (implementer,),
            f"{work_item} implementer and reviewer are the same role",
        )

    return SeparationRuleResult.passed(
        IMPLEMENTER_REVIEWER_RULE,
        (implementer, reviewer),
        f"{work_item} implementer and reviewer are independent roles",
    )


def check_no_promotion_permission(
    permissions_by_role_id: object,
    *,
    expected_role_ids: Iterable[str] | None,
) -> SeparationRuleResult:
    """Reject any promotion grant, with Diagnostics Runner checked explicitly."""

    expected = _coerce_known_role_ids(expected_role_ids)
    if expected is None:
        return SeparationRuleResult.blocked(
            PROMOTION_PERMISSION_RULE,
            (_UNKNOWN_REF,),
            "expected role ids are missing or ambiguous",
        )
    if not isinstance(permissions_by_role_id, Mapping):
        return SeparationRuleResult.blocked(
            PROMOTION_PERMISSION_RULE,
            expected,
            "permission matrix is missing or ambiguous",
        )

    offending: list[str] = []
    missing: list[str] = []
    malformed: list[str] = []
    inspected_role_ids = _matrix_role_ids(permissions_by_role_id, expected)
    for role_id in inspected_role_ids:
        entry = permissions_by_role_id.get(role_id)
        if entry is None:
            missing.append(role_id)
            continue
        can_promote = _promotion_grant(entry)
        if can_promote is None:
            malformed.append(role_id)
        elif can_promote:
            offending.append(role_id)

    if missing:
        return SeparationRuleResult.blocked(
            PROMOTION_PERMISSION_RULE,
            missing,
            "promotion check cannot pass because matrix entries are missing",
        )
    if malformed:
        return SeparationRuleResult.blocked(
            PROMOTION_PERMISSION_RULE,
            malformed,
            "promotion check cannot pass because entries are incomplete",
        )
    if offending:
        reason = "promotion permission is granted to a campaign role"
        if "diagnostics_runner" in offending:
            reason = "diagnostics_runner has a forbidden promotion permission grant"
        return SeparationRuleResult.blocked(PROMOTION_PERMISSION_RULE, offending, reason)

    return SeparationRuleResult.passed(
        PROMOTION_PERMISSION_RULE,
        expected,
        "no campaign role has promotion permission",
    )


def check_reviewer_assignment_independent(
    work_item_ref: object,
    implementer_role_id: object,
    reviewer_role_id: object,
    *,
    known_role_ids: Iterable[str] | None,
) -> SeparationRuleResult:
    """Reject a concrete review assignment where reviewer equals implementer."""

    work_item = _coerce_ref(work_item_ref)
    implementer = _coerce_ref(implementer_role_id)
    reviewer = _coerce_ref(reviewer_role_id)
    roles = _result_refs((implementer, reviewer))
    if work_item is None or implementer is None or reviewer is None:
        return SeparationRuleResult.blocked(
            REVIEWER_ASSIGNMENT_RULE,
            roles,
            "work item reviewer assignment is missing or ambiguous",
        )

    known_block = _known_roles_block(
        REVIEWER_ASSIGNMENT_RULE,
        (implementer, reviewer),
        known_role_ids,
    )
    if known_block is not None:
        return known_block

    if implementer == reviewer:
        return SeparationRuleResult.blocked(
            REVIEWER_ASSIGNMENT_RULE,
            (implementer,),
            f"{work_item} reviewer assignment equals implementer",
        )

    return SeparationRuleResult.passed(
        REVIEWER_ASSIGNMENT_RULE,
        (implementer, reviewer),
        f"{work_item} reviewer assignment is independent",
    )


def check_librarian_verdict_required(
    librarian_role_id: object,
    write_scope: object,
    reviewer_verdict_ref: object,
    *,
    known_role_ids: Iterable[str] | None,
) -> SeparationRuleResult:
    """Reject a Librarian write path without a bound reviewer verdict ref."""

    librarian = _coerce_ref(librarian_role_id)
    scope = _coerce_ref(write_scope)
    verdict = _coerce_ref(reviewer_verdict_ref)
    roles = _result_refs((librarian,))
    if librarian is None or scope is None:
        return SeparationRuleResult.blocked(
            LIBRARIAN_VERDICT_RULE,
            roles,
            "librarian write path input is missing or ambiguous",
        )

    known_block = _known_roles_block(LIBRARIAN_VERDICT_RULE, (librarian,), known_role_ids)
    if known_block is not None:
        return known_block

    if librarian != "librarian":
        return SeparationRuleResult.blocked(
            LIBRARIAN_VERDICT_RULE,
            (librarian,),
            "registry write path is not bound to the librarian role",
        )
    if verdict is None:
        return SeparationRuleResult.blocked(
            LIBRARIAN_VERDICT_RULE,
            (librarian,),
            f"{scope} lacks a bound reviewer verdict ref",
        )

    return SeparationRuleResult.passed(
        LIBRARIAN_VERDICT_RULE,
        (librarian,),
        f"{scope} has a bound reviewer verdict ref",
    )


def check_permission_matrix_coverage(
    role_ids: Iterable[str] | None,
    permissions_by_role_id: object,
    *,
    expected_role_ids: Iterable[str] | None,
) -> SeparationRuleResult:
    """Reject missing roles, extra roles, missing entries, or incomplete entries."""

    registered = _coerce_known_role_ids(role_ids)
    expected = _coerce_known_role_ids(expected_role_ids)
    roles = _result_refs(registered or expected)
    if registered is None or expected is None:
        return SeparationRuleResult.blocked(
            PERMISSION_MATRIX_COVERAGE_RULE,
            roles,
            "registered or expected role ids are missing or ambiguous",
        )
    if set(registered) != set(expected):
        return SeparationRuleResult.blocked(
            PERMISSION_MATRIX_COVERAGE_RULE,
            _sorted_refs(set(registered).symmetric_difference(expected)),
            "registered role ids do not match the MVP roster",
        )
    if not isinstance(permissions_by_role_id, Mapping):
        return SeparationRuleResult.blocked(
            PERMISSION_MATRIX_COVERAGE_RULE,
            registered,
            "permission matrix is missing or ambiguous",
        )

    missing: list[str] = []
    incomplete: list[str] = []
    mismatched: list[str] = []
    for role_id in registered:
        entry = permissions_by_role_id.get(role_id)
        if entry is None:
            missing.append(role_id)
            continue
        if getattr(entry, "role_id", None) != role_id:
            mismatched.append(role_id)
        if any(not hasattr(entry, field_name) for field_name in _ROLE_PERMISSION_FIELDS):
            incomplete.append(role_id)

    if missing:
        return SeparationRuleResult.blocked(
            PERMISSION_MATRIX_COVERAGE_RULE,
            missing,
            "registered roles are missing permission matrix entries",
        )
    if mismatched:
        return SeparationRuleResult.blocked(
            PERMISSION_MATRIX_COVERAGE_RULE,
            mismatched,
            "permission matrix entries have mismatched role ids",
        )
    if incomplete:
        return SeparationRuleResult.blocked(
            PERMISSION_MATRIX_COVERAGE_RULE,
            incomplete,
            "permission matrix entries are incomplete",
        )

    return SeparationRuleResult.passed(
        PERMISSION_MATRIX_COVERAGE_RULE,
        registered,
        "every MVP role has a complete permission matrix entry",
    )


def check_human_reserved_flags_preserved(
    permissions_by_role_id: object,
    *,
    expected_role_ids: Iterable[str] | None,
    required_human_actions: Iterable[str] | None,
    required_red_lane_actions: Iterable[str] | None,
) -> SeparationRuleResult:
    """Reject when human-approval or Red-lane markers are absent from entries."""

    expected = _coerce_known_role_ids(expected_role_ids)
    human_actions = _coerce_known_role_ids(required_human_actions)
    red_actions = _coerce_known_role_ids(required_red_lane_actions)
    roles = _result_refs(expected)
    if expected is None or human_actions is None or red_actions is None:
        return SeparationRuleResult.blocked(
            HUMAN_RESERVED_FLAGS_RULE,
            roles,
            "reserved action inputs are missing or ambiguous",
        )
    if not isinstance(permissions_by_role_id, Mapping):
        return SeparationRuleResult.blocked(
            HUMAN_RESERVED_FLAGS_RULE,
            expected,
            "permission matrix is missing or ambiguous",
        )

    offending: list[str] = []
    for role_id in expected:
        entry = permissions_by_role_id.get(role_id)
        if entry is None:
            offending.append(role_id)
            continue
        human_approval = getattr(entry, "human_approval", None)
        red_lane = getattr(entry, "red_lane", None)
        if not _all_required(human_approval, human_actions):
            offending.append(role_id)
            continue
        if not _all_required(red_lane, red_actions):
            offending.append(role_id)

    if offending:
        return SeparationRuleResult.blocked(
            HUMAN_RESERVED_FLAGS_RULE,
            offending,
            "human approval or red lane markers are missing",
        )

    return SeparationRuleResult.passed(
        HUMAN_RESERVED_FLAGS_RULE,
        expected,
        "human approval and red lane markers are preserved",
    )


def overall_status(results: Iterable[SeparationRuleResult]) -> SeparationStatus:
    """Return BLOCKED if any rule result is blocked."""

    materialized = tuple(results)
    if not materialized:
        return SeparationStatus.BLOCKED
    if any(result.status is SeparationStatus.BLOCKED for result in materialized):
        return SeparationStatus.BLOCKED
    return SeparationStatus.PASS


def blocked_results(
    results: Iterable[SeparationRuleResult],
) -> tuple[SeparationRuleResult, ...]:
    """Return blocked results in original order."""

    return tuple(result for result in results if result.status is SeparationStatus.BLOCKED)


def _known_roles_block(
    rule_id: str,
    role_ids: Iterable[str],
    known_role_ids: Iterable[str] | None,
) -> SeparationRuleResult | None:
    known = _coerce_known_role_ids(known_role_ids)
    roles = tuple(role_ids)
    if known is None:
        return SeparationRuleResult.blocked(
            rule_id,
            _result_refs(roles),
            "known role set is missing or ambiguous",
        )
    unknown = tuple(role_id for role_id in roles if role_id not in known)
    if unknown:
        return SeparationRuleResult.blocked(
            rule_id,
            unknown,
            "role is not present in the known MVP roster",
        )
    return None


def _coerce_known_role_ids(values: Iterable[str] | None) -> tuple[str, ...] | None:
    if values is None or isinstance(values, str):
        return None
    materialized = tuple(values)
    if not materialized or len(set(materialized)) != len(materialized):
        return None
    if any(_coerce_ref(value) is None for value in materialized):
        return None
    return materialized


def _matrix_role_ids(
    permissions_by_role_id: Mapping[Any, Any],
    expected_role_ids: tuple[str, ...],
) -> tuple[str, ...]:
    valid_matrix_ids = tuple(
        key for key in permissions_by_role_id if isinstance(key, str) and _coerce_ref(key)
    )
    return _sorted_refs((*expected_role_ids, *valid_matrix_ids))


def _promotion_grant(entry: object) -> bool | None:
    promotion = getattr(entry, "promotion", None)
    can_promote = getattr(promotion, "can_promote", None)
    return can_promote if isinstance(can_promote, bool) else None


def _all_required(marker: object, actions: tuple[str, ...]) -> bool:
    requires = getattr(marker, "requires", None)
    if not callable(requires):
        return False
    try:
        return all(requires(action) for action in actions)
    except Exception:
        return False


def _result_refs(values: Iterable[str | None] | None) -> tuple[str, ...]:
    if values is None:
        return (_UNKNOWN_REF,)
    result = tuple(value for value in values if isinstance(value, str) and _coerce_ref(value))
    return result or (_UNKNOWN_REF,)


def _sorted_refs(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(set(values)))


def _coerce_ref(value: object) -> str | None:
    if not isinstance(value, str) or value != value.strip() or not value:
        return None
    if len(value) > MAX_DECLARATIVE_TEXT_LENGTH:
        return None
    if any(ord(character) < 32 for character in value):
        return None
    lowered = value.lower()
    if any(marker in lowered for marker in FORBIDDEN_PAYLOAD_MARKERS):
        return None
    if any(suffix in lowered for suffix in FORBIDDEN_HEAVY_SUFFIXES):
        return None
    if not _REF_PATTERN.fullmatch(value):
        return None
    return value


def _validate_ref(field_name: str, value: object) -> None:
    if _coerce_ref(value) is None:
        raise ValueError(f"{field_name} must be a stable value-free ref")


def _validate_reason(value: object) -> None:
    if not isinstance(value, str) or value != value.strip() or not value:
        raise ValueError("reason must be a non-empty str")
    if len(value) > MAX_DECLARATIVE_TEXT_LENGTH:
        raise ValueError("reason exceeds declarative text length")
    if any(ord(character) < 32 for character in value):
        raise ValueError("reason must be a single-line declarative string")
    lowered = value.lower()
    if any(marker in lowered for marker in FORBIDDEN_PAYLOAD_MARKERS):
        raise ValueError("reason contains a forbidden payload marker")
    if any(suffix in lowered for suffix in FORBIDDEN_HEAVY_SUFFIXES):
        raise ValueError("reason contains a forbidden heavy artifact reference")


__all__ = [
    "GENERATOR_APPROVER_RULE",
    "HUMAN_RESERVED_FLAGS_RULE",
    "IMPLEMENTER_REVIEWER_RULE",
    "LIBRARIAN_VERDICT_RULE",
    "PERMISSION_MATRIX_COVERAGE_RULE",
    "PROMOTION_PERMISSION_RULE",
    "REVIEWER_ASSIGNMENT_RULE",
    "SeparationRuleResult",
    "SeparationStatus",
    "blocked_results",
    "check_generator_approver_separation",
    "check_human_reserved_flags_preserved",
    "check_implementer_reviewer_separation",
    "check_librarian_verdict_required",
    "check_no_promotion_permission",
    "check_permission_matrix_coverage",
    "check_reviewer_assignment_independent",
    "overall_status",
]
