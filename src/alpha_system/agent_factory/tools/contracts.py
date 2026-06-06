"""Agent-facing tool contract schema."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from alpha_system.agent_factory.permissions.matrix import ROSTER_ROLE_IDS, permission_for
from alpha_system.agent_factory.tools.results import AgentToolResult

MAX_CONTRACT_TEXT_LENGTH = 512
TOOL_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$")
CONTRACT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_.:-]*$")

CONTRACT_GROUP_PREFIXES: dict[str, tuple[str, ...]] = {
    "registry": ("registry.",),
    "feature_label": ("feature.", "label."),
    "runtime": ("runtime.",),
    "review": ("review.",),
    "ledger_memory_promotion": ("ledger.", "evidence.", "memory.", "promotion."),
}
REQUIRED_FORBIDDEN_SIDE_EFFECTS: tuple[str, ...] = (
    "direct_registry_write",
    "raw_provider_access",
    "external_provider_call",
    "raw_or_heavy_result_payload",
    "value_materialization_in_mvp",
    "broker_paper_live_order_scope",
)
FORBIDDEN_CONTRACT_PAYLOAD_MARKERS: tuple[str, ...] = (
    "raw_payload",
    "provider_payload",
    "db_rows",
    "data/raw/",
    "data/canonical/",
    "data/factors/",
    "data/labels/",
    "data/cache/",
    "metadata/",
)
FORBIDDEN_CONTRACT_HEAVY_SUFFIXES: tuple[str, ...] = (
    ".parquet",
    ".arrow",
    ".feather",
    ".dbn",
    ".zst",
    ".sqlite",
    ".sqlite3",
    ".db",
    ".wal",
)


class ToolGroup(StrEnum):
    """Candidate tool groups owned by AGENT-P05."""

    REGISTRY = "registry"
    FEATURE_LABEL = "feature_label"
    RUNTIME = "runtime"
    REVIEW = "review"
    LEDGER_MEMORY_PROMOTION = "ledger_memory_promotion"


class ToolArtifactPolicy(StrEnum):
    """Artifact visibility policy for agent-facing tools."""

    LOCAL_ONLY = "local_only"


class ToolContractStatus(StrEnum):
    """Lifecycle status of a tool contract."""

    MVP = "mvp"
    TARGET = "target"
    FUTURE = "future"


@dataclass(frozen=True, slots=True)
class ToolContract:
    """Immutable declaration of one agent-facing tool boundary."""

    name: str
    group: ToolGroup
    allowed_callers: tuple[str, ...]
    permission_matrix_refs: tuple[str, ...]
    required_inputs: tuple[str, ...]
    output_schema: type[AgentToolResult]
    forbidden_side_effects: tuple[str, ...]
    artifact_policy: ToolArtifactPolicy
    failure_states: tuple[str, ...]
    required_reviewer: str
    reviewer_independence_note: str
    status: ToolContractStatus

    def __post_init__(self) -> None:
        object.__setattr__(self, "group", _coerce_enum(ToolGroup, self.group, "group"))
        object.__setattr__(
            self,
            "artifact_policy",
            _coerce_enum(ToolArtifactPolicy, self.artifact_policy, "artifact_policy"),
        )
        object.__setattr__(
            self,
            "status",
            _coerce_enum(ToolContractStatus, self.status, "status"),
        )
        self.validate()

    def validate(self) -> ToolContract:
        """Fail closed unless the contract is complete and value-free."""

        _validate_tool_name(self.name)
        _validate_group_name_consistency(self.name, self.group)
        _validate_role_tuple("allowed_callers", self.allowed_callers)
        _validate_identifier_tuple("permission_matrix_refs", self.permission_matrix_refs)
        _validate_identifier_tuple("required_inputs", self.required_inputs)
        if self.output_schema is not AgentToolResult:
            raise ValueError("output_schema must be AgentToolResult")
        _validate_identifier_tuple("forbidden_side_effects", self.forbidden_side_effects)
        missing_side_effects = set(REQUIRED_FORBIDDEN_SIDE_EFFECTS).difference(
            self.forbidden_side_effects
        )
        if missing_side_effects:
            raise ValueError(f"forbidden_side_effects missing: {sorted(missing_side_effects)}")
        if self.artifact_policy is not ToolArtifactPolicy.LOCAL_ONLY:
            raise ValueError("artifact_policy must be local_only")
        _validate_identifier_tuple("failure_states", self.failure_states)
        _validate_text("required_reviewer", self.required_reviewer)
        _validate_text("reviewer_independence_note", self.reviewer_independence_note)
        _validate_permission_matrix_cross_refs(
            self.name,
            self.allowed_callers,
            self.permission_matrix_refs,
        )
        return self

    def allows(self, role_id: str) -> bool:
        """Return whether the role is explicitly allowed to call this tool."""

        _validate_text("role_id", role_id)
        return role_id in self.allowed_callers

    def forbids(self, side_effect: str) -> bool:
        """Return whether the named side effect is explicitly forbidden."""

        _validate_identifier("side_effect", side_effect)
        return side_effect in self.forbidden_side_effects


def _coerce_enum(enum_type: type[StrEnum], value: object, field_name: str) -> StrEnum:
    if isinstance(value, enum_type):
        return value
    if isinstance(value, str):
        _validate_text(field_name, value)
        try:
            return enum_type(value)
        except ValueError as error:
            raise ValueError(f"{field_name} is not a valid {enum_type.__name__}") from error
    raise TypeError(f"{field_name} must be a {enum_type.__name__}")


def _validate_group_name_consistency(name: str, group: ToolGroup) -> None:
    prefixes = CONTRACT_GROUP_PREFIXES[group.value]
    if not name.startswith(prefixes):
        raise ValueError(f"tool name {name!r} does not match group {group.value!r}")


def _validate_tool_name(value: object) -> None:
    _validate_text("name", value)
    if not TOOL_NAME_PATTERN.fullmatch(value):
        raise ValueError("name must be a stable dotted tool id")


def _validate_role_tuple(field_name: str, value: object) -> None:
    _validate_identifier_tuple(field_name, value)
    unknown_roles = set(value).difference(ROSTER_ROLE_IDS)
    if unknown_roles:
        raise ValueError(f"{field_name} contains unknown roster roles: {sorted(unknown_roles)}")


def _validate_identifier_tuple(field_name: str, value: object) -> None:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple[str, ...]")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must not contain duplicates")
    for item in value:
        _validate_identifier(field_name, item)


def _validate_identifier(field_name: str, value: object) -> None:
    _validate_text(field_name, value)
    if not CONTRACT_ID_PATTERN.fullmatch(value):
        raise ValueError(f"{field_name} must be a stable declarative identifier")


def _validate_text(field_name: str, value: object) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a str")
    if value != value.strip() or not value:
        raise ValueError(f"{field_name} must be non-empty without surrounding whitespace")
    if len(value) > MAX_CONTRACT_TEXT_LENGTH:
        raise ValueError(f"{field_name} exceeds contract text length")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{field_name} must be a single-line contract string")
    lowered = value.lower()
    if any(marker in lowered for marker in FORBIDDEN_CONTRACT_PAYLOAD_MARKERS):
        raise ValueError(f"{field_name} contains a forbidden payload marker")
    if any(suffix in lowered for suffix in FORBIDDEN_CONTRACT_HEAVY_SUFFIXES):
        raise ValueError(f"{field_name} contains a forbidden heavy artifact reference")


def _validate_permission_matrix_cross_refs(
    tool_name: str,
    allowed_callers: tuple[str, ...],
    permission_matrix_refs: tuple[str, ...],
) -> None:
    for caller in allowed_callers:
        permissions = permission_for(caller)
        if not any(permissions.tool.allows(ref) for ref in permission_matrix_refs):
            raise ValueError(f"{caller} is allowed for {tool_name} without a matching P04 tool ref")
