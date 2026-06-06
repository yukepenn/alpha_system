"""Value-free Agent Factory permission contract model."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from alpha_system.agent_factory.roles.contracts import (
    FORBIDDEN_HEAVY_SUFFIXES,
    FORBIDDEN_PAYLOAD_MARKERS,
    MAX_DECLARATIVE_TEXT_LENGTH,
)

_ROLE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
_PERMISSION_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_.:-]*$")
_FORBIDDEN_DATA_SCOPE_MARKERS: tuple[str, ...] = (
    "raw",
    "provider",
    "direct_file",
    "local_file",
)
_FORBIDDEN_WRITE_SCOPE_MARKERS: tuple[str, ...] = (
    "direct_registry",
    "registry.write.direct",
    "featurestore.direct",
    "labelstore.direct",
    "datasetversion_registry.direct",
)


@dataclass(frozen=True, slots=True)
class ToolPermission:
    """Declarative tool ids a role may call.

    Empty means the role may call no tools.
    """

    allowed_tool_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_identifier_tuple("allowed_tool_ids", self.allowed_tool_ids)

    def allows(self, tool_id: str) -> bool:
        """Return whether the exact declarative tool id is allowed."""

        _validate_permission_id("tool_id", tool_id)
        return tool_id in self.allowed_tool_ids


@dataclass(frozen=True, slots=True)
class DataPermission:
    """Declarative accepted-DatasetVersion-only data scope.

    Empty means no data access. Any raw or provider scope fails on construction.
    """

    allowed_scopes: tuple[str, ...] = ()
    accepted_dataset_versions_only: bool = False
    raw_provider_access: bool = False

    def __post_init__(self) -> None:
        _validate_identifier_tuple("allowed_scopes", self.allowed_scopes)
        _validate_bool("accepted_dataset_versions_only", self.accepted_dataset_versions_only)
        _validate_bool("raw_provider_access", self.raw_provider_access)
        if self.raw_provider_access:
            raise ValueError("raw provider access is forbidden")
        for scope in self.allowed_scopes:
            _reject_marker(scope, _FORBIDDEN_DATA_SCOPE_MARKERS, "data scope")
        if self.allowed_scopes and not self.accepted_dataset_versions_only:
            raise ValueError("data grants must be accepted-DatasetVersion-only")

    def allows_scope(self, scope: str) -> bool:
        """Return whether the exact declarative data scope is allowed."""

        _validate_permission_id("scope", scope)
        return scope in self.allowed_scopes


@dataclass(frozen=True, slots=True)
class WritePermission:
    """Declarative write scopes allowed only through sanctioned tool APIs.

    Empty means no write access. Direct registry writes fail on construction.
    """

    allowed_scopes: tuple[str, ...] = ()
    direct_registry_write: bool = False

    def __post_init__(self) -> None:
        _validate_identifier_tuple("allowed_scopes", self.allowed_scopes)
        _validate_bool("direct_registry_write", self.direct_registry_write)
        if self.direct_registry_write:
            raise ValueError("direct registry writes are forbidden")
        for scope in self.allowed_scopes:
            _reject_marker(scope, _FORBIDDEN_WRITE_SCOPE_MARKERS, "write scope")

    def allows_scope(self, scope: str) -> bool:
        """Return whether the exact declarative write scope is allowed."""

        _validate_permission_id("scope", scope)
        return scope in self.allowed_scopes


@dataclass(frozen=True, slots=True)
class ReviewPermission:
    """Declarative review or critique verdict scope."""

    can_issue_verdict: bool = False
    verdict_scopes: tuple[str, ...] = ()
    independence_required: bool = True

    def __post_init__(self) -> None:
        _validate_bool("can_issue_verdict", self.can_issue_verdict)
        _validate_identifier_tuple("verdict_scopes", self.verdict_scopes)
        _validate_bool("independence_required", self.independence_required)
        if self.verdict_scopes and not self.can_issue_verdict:
            raise ValueError("verdict scopes require can_issue_verdict")
        if self.can_issue_verdict and not self.verdict_scopes:
            raise ValueError("review grants require an explicit verdict scope")
        if self.can_issue_verdict and not self.independence_required:
            raise ValueError("review grants require reviewer independence")

    def allows_scope(self, scope: str) -> bool:
        """Return whether the exact declarative review scope is allowed."""

        _validate_permission_id("scope", scope)
        return self.can_issue_verdict and scope in self.verdict_scopes


@dataclass(frozen=True, slots=True)
class PromotionPermission:
    """Declarative promotion permission.

    Promotion grants are outside this campaign, so the only valid state is deny.
    """

    can_promote: bool = False

    def __post_init__(self) -> None:
        _validate_bool("can_promote", self.can_promote)
        if self.can_promote:
            raise ValueError("promotion grants are forbidden in this campaign")


@dataclass(frozen=True, slots=True)
class HumanApprovalRequired:
    """Actions reserved for human risk, capital, or live judgment."""

    required_actions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_identifier_tuple("required_actions", self.required_actions)

    def requires(self, action: str) -> bool:
        """Return whether the exact declarative action requires human approval."""

        _validate_permission_id("action", action)
        return action in self.required_actions


@dataclass(frozen=True, slots=True)
class RedLaneRequired:
    """Actions that would require scoped Red-lane authorization."""

    required_actions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_identifier_tuple("required_actions", self.required_actions)

    def requires(self, action: str) -> bool:
        """Return whether the exact declarative action requires Red lane."""

        _validate_permission_id("action", action)
        return action in self.required_actions


@dataclass(frozen=True, slots=True)
class RolePermissions:
    """Complete permission entry for one Agent Factory role."""

    role_id: str
    tool: ToolPermission = field(default_factory=ToolPermission)
    data: DataPermission = field(default_factory=DataPermission)
    write: WritePermission = field(default_factory=WritePermission)
    review: ReviewPermission = field(default_factory=ReviewPermission)
    promotion: PromotionPermission = field(default_factory=PromotionPermission)
    human_approval: HumanApprovalRequired = field(default_factory=HumanApprovalRequired)
    red_lane: RedLaneRequired = field(default_factory=RedLaneRequired)

    def __post_init__(self) -> None:
        _validate_role_id(self.role_id)
        _validate_primitive("tool", self.tool, ToolPermission)
        _validate_primitive("data", self.data, DataPermission)
        _validate_primitive("write", self.write, WritePermission)
        _validate_primitive("review", self.review, ReviewPermission)
        _validate_primitive("promotion", self.promotion, PromotionPermission)
        _validate_primitive(
            "human_approval",
            self.human_approval,
            HumanApprovalRequired,
        )
        _validate_primitive("red_lane", self.red_lane, RedLaneRequired)

    @classmethod
    def default_deny(cls, role_id: str) -> RolePermissions:
        """Build an explicit role entry with every grant denied."""

        return cls(role_id=role_id)

    @property
    def is_default_deny(self) -> bool:
        """Return true when the entry grants no tool, data, write, review, or promotion."""

        return (
            not self.tool.allowed_tool_ids
            and not self.data.allowed_scopes
            and not self.data.accepted_dataset_versions_only
            and not self.data.raw_provider_access
            and not self.write.allowed_scopes
            and not self.write.direct_registry_write
            and not self.review.can_issue_verdict
            and not self.review.verdict_scopes
            and not self.promotion.can_promote
        )


def _validate_role_id(value: object) -> None:
    _validate_text("role_id", value)
    if not _ROLE_ID_PATTERN.fullmatch(value):
        raise ValueError("role_id must be stable snake_case")


def _validate_identifier_tuple(field_name: str, value: object) -> None:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple[str, ...]")
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must not contain duplicates")
    for item in value:
        _validate_permission_id(field_name, item)


def _validate_permission_id(field_name: str, value: object) -> None:
    _validate_text(field_name, value)
    if not _PERMISSION_ID_PATTERN.fullmatch(value):
        raise ValueError(f"{field_name} must be a stable declarative identifier")


def _validate_text(field_name: str, value: object) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a str")
    if value != value.strip() or not value:
        raise ValueError(f"{field_name} must be non-empty without surrounding whitespace")
    if len(value) > MAX_DECLARATIVE_TEXT_LENGTH:
        raise ValueError(f"{field_name} exceeds declarative text length")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{field_name} must be a single-line declarative string")
    lowered = value.lower()
    if any(marker in lowered for marker in FORBIDDEN_PAYLOAD_MARKERS):
        raise ValueError(f"{field_name} contains a forbidden payload marker")
    if any(suffix in lowered for suffix in FORBIDDEN_HEAVY_SUFFIXES):
        raise ValueError(f"{field_name} contains a forbidden heavy artifact reference")


def _validate_bool(field_name: str, value: object) -> None:
    if not isinstance(value, bool):
        raise TypeError(f"{field_name} must be a bool")


def _validate_primitive(
    field_name: str,
    value: object,
    expected_type: type[object],
) -> None:
    if not isinstance(value, expected_type):
        raise TypeError(f"{field_name} must be a {expected_type.__name__}")


def _reject_marker(value: str, forbidden_markers: tuple[str, ...], label: str) -> None:
    lowered = value.lower()
    if any(marker in lowered for marker in forbidden_markers):
        raise ValueError(f"{label} contains a forbidden grant marker")
