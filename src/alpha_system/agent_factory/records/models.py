"""Value-free Agent Factory activity record contracts."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Any

from alpha_system.agent_factory.permissions.matrix import ROSTER_ROLE_IDS
from alpha_system.agent_factory.queue.models import ResearchTaskStatus
from alpha_system.agent_factory.separation.enforcement import SeparationRuleResult
from alpha_system.agent_factory.tools.results import (
    FORBIDDEN_HEAVY_SUFFIXES,
    FORBIDDEN_RESULT_MARKERS,
    RAW_OBJECT_MODULE_PREFIXES,
    AgentToolResult,
    AgentToolStatus,
)

MAX_RECORD_TEXT_LENGTH = 2048
MAX_RECORD_TUPLE_LENGTH = 50
CONTRACT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_.:-]*$")
VERSION_LABEL_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.:-]*$")

FORBIDDEN_RECORD_MARKERS: tuple[str, ...] = FORBIDDEN_RESULT_MARKERS + (
    "embedded_values",
    "embedded values",
    "value_array",
    "value array",
    "feature_values",
    "label_values",
    "runtime_values",
    "market_values",
    "array values",
    "list[float]",
    "list[int]",
    "db blob",
    "binary blob",
)

class AgentRunStatus(StrEnum):
    """Bounded lifecycle statuses for one Agent Factory run record."""

    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AgentDecisionClassification(StrEnum):
    """Whether a decision is inside or outside the role's allowed boundary."""

    ALLOWED = "ALLOWED"
    FORBIDDEN = "FORBIDDEN"


@dataclass(frozen=True, slots=True)
class AgentRunRecord:
    """One bounded agent run linked to a request and queue/task ref."""

    run_id: str
    role_id: str
    request_id: str
    status: AgentRunStatus
    queue_ref: str | None
    task_ref: str | None
    task_status: ResearchTaskStatus | None
    started_at_ref: str
    ended_at_ref: str | None
    summary: str
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_record_id("run_id", self.run_id, "agent_run:")
        _validate_role_id("role_id", self.role_id)
        _validate_identifier("request_id", self.request_id)
        object.__setattr__(
            self,
            "status",
            _coerce_enum(AgentRunStatus, self.status, "status"),
        )
        _validate_optional_identifier("queue_ref", self.queue_ref)
        _validate_optional_identifier("task_ref", self.task_ref)
        if self.queue_ref is None and self.task_ref is None:
            raise ValueError("AgentRunRecord requires a queue_ref or task_ref")
        object.__setattr__(
            self,
            "task_status",
            _coerce_optional_enum(ResearchTaskStatus, self.task_status, "task_status"),
        )
        _validate_identifier("started_at_ref", self.started_at_ref)
        _validate_optional_identifier("ended_at_ref", self.ended_at_ref)
        if self.status is AgentRunStatus.RUNNING and self.ended_at_ref is not None:
            raise ValueError("RUNNING AgentRunRecord must not have an ended_at_ref")
        if self.status is not AgentRunStatus.RUNNING and self.ended_at_ref is None:
            raise ValueError("finished AgentRunRecord requires ended_at_ref")
        _validate_text("summary", self.summary)
        _validate_identifier_tuple("limitations", self.limitations, allow_empty=False)


@dataclass(frozen=True, slots=True)
class AgentDecisionRecord:
    """One role decision with fail-closed classification and next gate."""

    decision_id: str
    run_id: str
    role_id: str
    request_id: str
    decision_kind: str
    classification: AgentDecisionClassification
    rationale_summary: str
    next_required_gate: str
    separation_results: tuple[SeparationRuleResult, ...] = ()

    def __post_init__(self) -> None:
        _validate_record_id("decision_id", self.decision_id, "agent_decision:")
        _validate_record_id("run_id", self.run_id, "agent_run:")
        _validate_role_id("role_id", self.role_id)
        _validate_identifier("request_id", self.request_id)
        _validate_identifier("decision_kind", self.decision_kind)
        object.__setattr__(
            self,
            "classification",
            _coerce_enum(
                AgentDecisionClassification,
                self.classification,
                "classification",
            ),
        )
        _validate_text("rationale_summary", self.rationale_summary)
        _validate_identifier("next_required_gate", self.next_required_gate)
        _validate_separation_results(self.separation_results)


@dataclass(frozen=True, slots=True)
class ToolInvocationRecord:
    """One agent-facing tool call and the structured result it produced."""

    invocation_id: str
    tool_name: str
    caller_role_id: str
    request_id: str
    started_at_ref: str
    ended_at_ref: str
    input_refs: tuple[str, ...]
    result: AgentToolResult
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_record_id("invocation_id", self.invocation_id, "tool_invocation:")
        _validate_tool_name("tool_name", self.tool_name)
        _validate_role_id("caller_role_id", self.caller_role_id)
        _validate_identifier("request_id", self.request_id)
        _validate_identifier("started_at_ref", self.started_at_ref)
        _validate_identifier("ended_at_ref", self.ended_at_ref)
        _validate_identifier_tuple("input_refs", self.input_refs, allow_empty=False)
        _validate_type("result", self.result, AgentToolResult)
        _validate_identifier_tuple("limitations", self.limitations, allow_empty=False)
        _validate_registered_tool_call(self.tool_name, self.caller_role_id)
        if self.result.role != self.caller_role_id:
            raise ValueError("AgentToolResult role must match caller_role_id")
        if self.result.request_id != self.request_id:
            raise ValueError("AgentToolResult request_id must match invocation request_id")

    @property
    def result_status(self) -> AgentToolStatus:
        """Return the structured tool-result status for audit views."""

        return self.result.status

    @property
    def result_refs(self) -> tuple[str, ...]:
        """Return ids and refs carried by the structured tool result."""

        refs: list[str] = []
        for ref in (
            self.result.alpha_spec_id,
            self.result.study_spec_id,
            self.result.dataset_version_id,
            self.result.runtime_run_id,
        ):
            if ref is not None:
                refs.append(ref)
        refs.extend(self.result.feature_pack_refs)
        refs.extend(self.result.label_pack_refs)
        refs.extend(self.result.artifacts)
        return tuple(refs)


@dataclass(frozen=True, slots=True)
class AgentHandoff:
    """Structured handoff linking one decision to tool invocations and spec refs."""

    handoff_id: str
    from_role_id: str
    to_role_id: str | None
    request_id: str
    decision: AgentDecisionRecord
    tool_invocations: tuple[ToolInvocationRecord, ...]
    alpha_spec_id: str | None
    study_spec_id: str | None
    dataset_version_id: str | None
    feature_pack_refs: tuple[str, ...]
    label_pack_refs: tuple[str, ...]
    runtime_run_id: str | None
    blocking_findings: tuple[str, ...]
    next_required_gate: str
    summary: str
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_record_id("handoff_id", self.handoff_id, "agent_handoff:")
        _validate_role_id("from_role_id", self.from_role_id)
        _validate_optional_role_id("to_role_id", self.to_role_id)
        _validate_identifier("request_id", self.request_id)
        _validate_type("decision", self.decision, AgentDecisionRecord)
        _validate_record_tuple(
            "tool_invocations",
            self.tool_invocations,
            ToolInvocationRecord,
            allow_empty=False,
        )
        _validate_optional_identifier("alpha_spec_id", self.alpha_spec_id)
        _validate_optional_identifier("study_spec_id", self.study_spec_id)
        _validate_optional_identifier("dataset_version_id", self.dataset_version_id)
        _validate_identifier_tuple("feature_pack_refs", self.feature_pack_refs, allow_empty=True)
        _validate_identifier_tuple("label_pack_refs", self.label_pack_refs, allow_empty=True)
        _validate_optional_identifier("runtime_run_id", self.runtime_run_id)
        _validate_identifier_tuple("blocking_findings", self.blocking_findings, allow_empty=True)
        _validate_identifier("next_required_gate", self.next_required_gate)
        _validate_text("summary", self.summary)
        _validate_identifier_tuple("limitations", self.limitations, allow_empty=False)
        self._validate_linkage()

    @property
    def decision_ref(self) -> str:
        """Return the linked decision id."""

        return self.decision.decision_id

    @property
    def tool_invocation_refs(self) -> tuple[str, ...]:
        """Return linked tool invocation ids in order."""

        return tuple(invocation.invocation_id for invocation in self.tool_invocations)

    @property
    def spec_refs(self) -> tuple[str, ...]:
        """Return the handoff's AlphaSpec, StudySpec, dataset, pack, and runtime refs."""

        refs: list[str] = []
        for ref in (
            self.alpha_spec_id,
            self.study_spec_id,
            self.dataset_version_id,
            self.runtime_run_id,
        ):
            if ref is not None:
                refs.append(ref)
        refs.extend(self.feature_pack_refs)
        refs.extend(self.label_pack_refs)
        return tuple(refs)

    def _validate_linkage(self) -> None:
        if self.decision.role_id != self.from_role_id:
            raise ValueError("handoff from_role_id must match decision role_id")
        if self.decision.request_id != self.request_id:
            raise ValueError("handoff request_id must match decision request_id")
        if not self.spec_refs:
            raise ValueError("AgentHandoff requires at least one spec, pack, or runtime ref")

        for invocation in self.tool_invocations:
            if invocation.caller_role_id != self.from_role_id:
                raise ValueError("handoff tool invocation caller must match from_role_id")
            if invocation.request_id != self.request_id:
                raise ValueError("handoff tool invocation request_id must match request_id")

        _validate_optional_ref_in_tool_results(
            "alpha_spec_id",
            self.alpha_spec_id,
            self.tool_invocations,
        )
        _validate_optional_ref_in_tool_results(
            "study_spec_id",
            self.study_spec_id,
            self.tool_invocations,
        )
        _validate_optional_ref_in_tool_results(
            "dataset_version_id",
            self.dataset_version_id,
            self.tool_invocations,
        )
        _validate_optional_ref_in_tool_results(
            "runtime_run_id",
            self.runtime_run_id,
            self.tool_invocations,
        )
        _validate_ref_subset_in_tool_results(
            "feature_pack_refs",
            self.feature_pack_refs,
            self.tool_invocations,
        )
        _validate_ref_subset_in_tool_results(
            "label_pack_refs",
            self.label_pack_refs,
            self.tool_invocations,
        )


@dataclass(frozen=True, slots=True)
class AgentAuditLog:
    """Ordered append-style audit refs for one agent activity lifecycle."""

    audit_log_id: str
    request_id: str
    run_refs: tuple[str, ...]
    decision_refs: tuple[str, ...]
    handoff_refs: tuple[str, ...]
    tool_invocation_refs: tuple[str, ...]
    version_refs: tuple[str, ...]
    ordered_activity_refs: tuple[str, ...]
    summary: str
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_record_id("audit_log_id", self.audit_log_id, "agent_audit:")
        _validate_identifier("request_id", self.request_id)
        _validate_prefixed_ref_tuple("run_refs", self.run_refs, "agent_run:", allow_empty=False)
        _validate_prefixed_ref_tuple(
            "decision_refs",
            self.decision_refs,
            "agent_decision:",
            allow_empty=True,
        )
        _validate_prefixed_ref_tuple(
            "handoff_refs",
            self.handoff_refs,
            "agent_handoff:",
            allow_empty=True,
        )
        _validate_prefixed_ref_tuple(
            "tool_invocation_refs",
            self.tool_invocation_refs,
            "tool_invocation:",
            allow_empty=True,
        )
        _validate_version_refs(self.version_refs)
        _validate_identifier_tuple(
            "ordered_activity_refs",
            self.ordered_activity_refs,
            allow_empty=False,
        )
        _validate_text("summary", self.summary)
        _validate_identifier_tuple("limitations", self.limitations, allow_empty=False)
        self._validate_ordered_refs()

    def append_ordered_ref(self, record_ref: str) -> AgentAuditLog:
        """Return a new audit log with an already declared ref appended."""

        _validate_identifier("record_ref", record_ref)
        if record_ref in self.ordered_activity_refs:
            raise ValueError("record_ref already exists in ordered_activity_refs")
        if record_ref not in self._known_refs():
            raise ValueError("record_ref must already be declared in a ref tuple")
        return replace(
            self,
            ordered_activity_refs=self.ordered_activity_refs + (record_ref,),
        )

    def _known_refs(self) -> set[str]:
        return set(
            self.run_refs
            + self.decision_refs
            + self.handoff_refs
            + self.tool_invocation_refs
            + self.version_refs
        )

    def _validate_ordered_refs(self) -> None:
        ordered = set(self.ordered_activity_refs)
        activity_refs = set(
            self.run_refs + self.decision_refs + self.handoff_refs + self.tool_invocation_refs
        )
        missing = activity_refs.difference(ordered)
        if missing:
            raise ValueError(f"ordered_activity_refs missing activity refs: {sorted(missing)}")
        unknown = ordered.difference(self._known_refs())
        if unknown:
            raise ValueError(f"ordered_activity_refs contains unknown refs: {sorted(unknown)}")


@dataclass(frozen=True, slots=True)
class AgentPromptVersion:
    """Version stamp for an Agent Factory prompt asset."""

    prompt_version_id: str
    role_id: str
    prompt_ref: str
    template_ref: str
    version_label: str
    change_summary: str
    approved_by_ref: str
    effective_from_ref: str
    supersedes_prompt_version_id: str | None
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_record_id("prompt_version_id", self.prompt_version_id, "prompt_version:")
        _validate_role_id("role_id", self.role_id)
        _validate_identifier("prompt_ref", self.prompt_ref)
        _validate_identifier("template_ref", self.template_ref)
        _validate_version_label("version_label", self.version_label)
        _validate_text("change_summary", self.change_summary)
        _validate_identifier("approved_by_ref", self.approved_by_ref)
        _validate_identifier("effective_from_ref", self.effective_from_ref)
        _validate_optional_record_id(
            "supersedes_prompt_version_id",
            self.supersedes_prompt_version_id,
            "prompt_version:",
        )
        _validate_identifier_tuple("limitations", self.limitations, allow_empty=False)


@dataclass(frozen=True, slots=True)
class AgentRoleVersion:
    """Version stamp for an Agent Factory role contract."""

    role_version_id: str
    role_id: str
    role_contract_ref: str
    version_label: str
    change_summary: str
    approved_by_ref: str
    effective_from_ref: str
    supersedes_role_version_id: str | None
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_record_id("role_version_id", self.role_version_id, "role_version:")
        _validate_role_id("role_id", self.role_id)
        _validate_identifier("role_contract_ref", self.role_contract_ref)
        _validate_version_label("version_label", self.version_label)
        _validate_text("change_summary", self.change_summary)
        _validate_identifier("approved_by_ref", self.approved_by_ref)
        _validate_identifier("effective_from_ref", self.effective_from_ref)
        _validate_optional_record_id(
            "supersedes_role_version_id",
            self.supersedes_role_version_id,
            "role_version:",
        )
        _validate_identifier_tuple("limitations", self.limitations, allow_empty=False)


@dataclass(frozen=True, slots=True)
class AgentPermissionVersion:
    """Version stamp for an Agent Factory permission matrix entry."""

    permission_version_id: str
    role_id: str
    permission_matrix_ref: str
    version_label: str
    change_summary: str
    approved_by_ref: str
    effective_from_ref: str
    supersedes_permission_version_id: str | None
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_record_id(
            "permission_version_id",
            self.permission_version_id,
            "permission_version:",
        )
        _validate_role_id("role_id", self.role_id)
        _validate_identifier("permission_matrix_ref", self.permission_matrix_ref)
        _validate_version_label("version_label", self.version_label)
        _validate_text("change_summary", self.change_summary)
        _validate_identifier("approved_by_ref", self.approved_by_ref)
        _validate_identifier("effective_from_ref", self.effective_from_ref)
        _validate_optional_record_id(
            "supersedes_permission_version_id",
            self.supersedes_permission_version_id,
            "permission_version:",
        )
        _validate_identifier_tuple("limitations", self.limitations, allow_empty=False)


def _coerce_enum[EnumT: StrEnum](
    enum_type: type[EnumT],
    value: object,
    field_name: str,
) -> EnumT:
    _reject_raw_object(field_name, value)
    if isinstance(value, enum_type):
        return value
    if isinstance(value, str):
        _validate_text(field_name, value)
        try:
            return enum_type(value)
        except ValueError as error:
            raise ValueError(f"{field_name} is not a valid {enum_type.__name__}") from error
    raise TypeError(f"{field_name} must be a {enum_type.__name__}")


def _coerce_optional_enum[EnumT: StrEnum](
    enum_type: type[EnumT],
    value: object,
    field_name: str,
) -> EnumT | None:
    if value is None:
        return None
    return _coerce_enum(enum_type, value, field_name)


def _validate_registered_tool_call(tool_name: str, caller_role_id: str) -> None:
    from alpha_system.agent_factory.tools.registry import resolve

    resolve(tool_name, caller_role_id)


def _validate_optional_ref_in_tool_results(
    field_name: str,
    value: str | None,
    invocations: tuple[ToolInvocationRecord, ...],
) -> None:
    if value is None:
        return
    found = False
    for invocation in invocations:
        result_value = getattr(invocation.result, field_name)
        if result_value == value:
            found = True
            break
    if not found:
        raise ValueError(f"{field_name} must be carried by at least one tool result")


def _validate_ref_subset_in_tool_results(
    field_name: str,
    values: tuple[str, ...],
    invocations: tuple[ToolInvocationRecord, ...],
) -> None:
    if not values:
        return
    result_refs: set[str] = set()
    for invocation in invocations:
        result_refs.update(getattr(invocation.result, field_name))
    missing = set(values).difference(result_refs)
    if missing:
        raise ValueError(f"{field_name} contains refs absent from tool results: {sorted(missing)}")


def _validate_record_tuple(
    field_name: str,
    value: object,
    expected_type: type[object],
    *,
    allow_empty: bool,
) -> None:
    _reject_raw_object(field_name, value)
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple[{expected_type.__name__}, ...]")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must be non-empty")
    if len(value) > MAX_RECORD_TUPLE_LENGTH:
        raise ValueError(f"{field_name} exceeds record tuple cap")
    for item in value:
        _validate_type(field_name, item, expected_type)


def _validate_separation_results(value: object) -> None:
    _reject_raw_object("separation_results", value)
    if not isinstance(value, tuple):
        raise TypeError("separation_results must be a tuple[SeparationRuleResult, ...]")
    if len(value) > MAX_RECORD_TUPLE_LENGTH:
        raise ValueError("separation_results exceeds record tuple cap")
    rule_ids: set[str] = set()
    for result in value:
        _validate_type("separation_results", result, SeparationRuleResult)
        if result.rule_id in rule_ids:
            raise ValueError("separation_results must not contain duplicate rule_id values")
        rule_ids.add(result.rule_id)


def _validate_prefixed_ref_tuple(
    field_name: str,
    value: object,
    prefix: str,
    *,
    allow_empty: bool,
) -> None:
    _validate_identifier_tuple(field_name, value, allow_empty=allow_empty)
    for item in value:
        if not item.startswith(prefix):
            raise ValueError(f"{field_name} values must start with {prefix}")


def _validate_version_refs(value: object) -> None:
    _validate_identifier_tuple("version_refs", value, allow_empty=True)
    allowed_prefixes = ("prompt_version:", "role_version:", "permission_version:")
    for item in value:
        if not item.startswith(allowed_prefixes):
            raise ValueError("version_refs must use prompt, role, or permission version refs")


def _validate_record_id(field_name: str, value: object, prefix: str) -> None:
    _validate_identifier(field_name, value)
    if not value.startswith(prefix):
        raise ValueError(f"{field_name} must start with {prefix}")


def _validate_optional_record_id(field_name: str, value: object, prefix: str) -> None:
    if value is None:
        return
    _validate_record_id(field_name, value, prefix)


def _validate_tool_name(field_name: str, value: object) -> None:
    _validate_identifier(field_name, value)
    if "." not in value:
        raise ValueError(f"{field_name} must be a dotted tool id")


def _validate_role_id(field_name: str, value: object) -> None:
    _validate_identifier(field_name, value)
    if value not in ROSTER_ROLE_IDS:
        raise ValueError(f"{field_name} contains an unknown Agent Factory role id")


def _validate_optional_role_id(field_name: str, value: object) -> None:
    if value is None:
        return
    _validate_role_id(field_name, value)


def _validate_identifier_tuple(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> None:
    _reject_raw_object(field_name, value)
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple[str, ...]")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must be non-empty")
    if len(value) > MAX_RECORD_TUPLE_LENGTH:
        raise ValueError(f"{field_name} exceeds record tuple cap")
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must not contain duplicates")
    for item in value:
        _validate_identifier(field_name, item)


def _validate_optional_identifier(field_name: str, value: object) -> None:
    if value is None:
        return
    _validate_identifier(field_name, value)


def _validate_identifier(field_name: str, value: object) -> None:
    _validate_text(field_name, value)
    if not CONTRACT_ID_PATTERN.fullmatch(value):
        raise ValueError(f"{field_name} must be a stable declarative identifier")


def _validate_version_label(field_name: str, value: object) -> None:
    _validate_text(field_name, value)
    if not VERSION_LABEL_PATTERN.fullmatch(value):
        raise ValueError(f"{field_name} must be a stable version label")


def _validate_text(field_name: str, value: object) -> None:
    _reject_raw_object(field_name, value)
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a str")
    if value != value.strip() or not value:
        raise ValueError(f"{field_name} must be non-empty without surrounding whitespace")
    if len(value) > MAX_RECORD_TEXT_LENGTH:
        raise ValueError(f"{field_name} exceeds record text length")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{field_name} must be a single-line record string")
    lowered = value.lower()
    if any(marker in lowered for marker in FORBIDDEN_RECORD_MARKERS):
        raise ValueError(f"{field_name} contains a forbidden raw/heavy payload marker")
    if any(suffix in lowered for suffix in FORBIDDEN_HEAVY_SUFFIXES):
        raise ValueError(f"{field_name} contains a forbidden heavy artifact reference")


def _validate_type(field_name: str, value: object, expected_type: type[object]) -> None:
    _reject_raw_object(field_name, value)
    if not isinstance(value, expected_type):
        raise TypeError(f"{field_name} must be a {expected_type.__name__}")


def _reject_raw_object(field_name: str, value: Any) -> None:
    if isinstance(value, (bytes, bytearray, memoryview)):
        raise TypeError(f"{field_name} must not contain bytes")
    if isinstance(value, (list, dict, set)):
        raise TypeError(f"{field_name} must not contain mutable collections")
    module_root = type(value).__module__.split(".", 1)[0]
    if module_root in RAW_OBJECT_MODULE_PREFIXES:
        raise TypeError(f"{field_name} must not contain dataframe or array objects")
