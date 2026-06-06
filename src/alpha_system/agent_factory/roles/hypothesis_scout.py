"""Hypothesis Scout role contract.

This module declares the contracts-only Hypothesis Scout role. It does not
instantiate an agent, start a loop, execute tools, resolve datasets, or write
registries.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

from alpha_system.agent_factory.permissions.matrix import permission_for
from alpha_system.agent_factory.queue.models import (
    AgentAssignment,
    PROHIBITED_MVP_TASK_STATUSES,
    ResearchTask,
    ResearchTaskStatus,
)
from alpha_system.agent_factory.roles.contracts import AgentRole
from alpha_system.agent_factory.roles.registry import get, register
from alpha_system.agent_factory.tools.results import (
    AgentToolResult,
    AgentToolStatus,
    FORBIDDEN_HEAVY_SUFFIXES,
    FORBIDDEN_RESULT_MARKERS,
    RAW_OBJECT_MODULE_PREFIXES,
)

ROLE_ID = "hypothesis_scout"
MIN_DRAFTS = 3
MAX_DRAFTS = 5
NEXT_REVIEW_GATE = "alpha_spec_critic_independent_review"

CALLABLE_TOOL_IDS: tuple[str, ...] = (
    "memory.lookup_rejected_ideas",
    "library.summarize_prior_work",
    "alphaspec.draft",
)
ALLOWED_TRANSITIONS: tuple[tuple[str, str], ...] = (
    ("HYPOTHESIS_DRAFTED", "ALPHASPEC_DRAFTED"),
    ("HYPOTHESIS_DRAFTED", "INPUTS_BLOCKED"),
    ("HYPOTHESIS_DRAFTED", "BLOCKED"),
)
BRANCH_OR_TERMINAL_STATES: tuple[str, ...] = (
    "ALPHASPEC_REJECTED",
    "INPUTS_BLOCKED",
    "BLOCKED",
)
DEFAULT_LIMITATIONS: tuple[str, ...] = (
    "contract_only_no_agent_instantiated",
    "draft_alphaspec_refs_are_not_implementation_approval",
    "no_alpha_profitability_tradability_or_live_claim",
)

_CONTRACT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_.:-]*$")
_MAX_SCOUT_TEXT_LENGTH = 1024


@dataclass(frozen=True, slots=True)
class RejectionReasonRecordRef:
    """Value-free pointer to a prior rejected-idea reason record."""

    record_ref: str
    rejected_idea_ref: str
    idea_fingerprint: str
    reason_category: str
    summary: str

    def __post_init__(self) -> None:
        _validate_identifier("record_ref", self.record_ref)
        _validate_identifier("rejected_idea_ref", self.rejected_idea_ref)
        _validate_identifier("idea_fingerprint", self.idea_fingerprint)
        _validate_identifier("reason_category", self.reason_category)
        _validate_text("summary", self.summary)


@dataclass(frozen=True, slots=True)
class AlphaSpecDraftRef:
    """Value-free AlphaSpec draft reference produced by the Scout contract."""

    alpha_spec_id: str
    task_id: str
    assignment_id: str
    alpha_family: str
    idea_fingerprint: str
    summary: str
    prior_rejection_reason_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_identifier("alpha_spec_id", self.alpha_spec_id)
        _validate_identifier("task_id", self.task_id)
        _validate_identifier("assignment_id", self.assignment_id)
        _validate_identifier("alpha_family", self.alpha_family)
        _validate_identifier("idea_fingerprint", self.idea_fingerprint)
        _validate_text("summary", self.summary)
        _validate_identifier_tuple(
            "prior_rejection_reason_refs",
            self.prior_rejection_reason_refs,
            allow_empty=True,
        )


@dataclass(frozen=True, slots=True)
class AgentHandoff:
    """AGENT-P08 value-free handoff shape until the shared P17 record exists."""

    role_id: str
    request_id: str
    task_id: str
    assignment_id: str
    decision: str
    source_task_status: str
    target_task_status: str
    alpha_spec_ids: tuple[str, ...]
    consulted_rejection_reason_refs: tuple[str, ...]
    tool_result_request_ids: tuple[str, ...]
    blocking_findings: tuple[str, ...]
    next_required_gate: str
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_identifier("role_id", self.role_id)
        if self.role_id != ROLE_ID:
            raise ValueError("AgentHandoff.role_id must be hypothesis_scout")
        _validate_identifier("request_id", self.request_id)
        _validate_identifier("task_id", self.task_id)
        _validate_identifier("assignment_id", self.assignment_id)
        _validate_identifier("decision", self.decision)
        _validate_task_status_name("source_task_status", self.source_task_status)
        _validate_task_status_name("target_task_status", self.target_task_status)
        if (self.source_task_status, self.target_task_status) not in ALLOWED_TRANSITIONS:
            raise ValueError("AgentHandoff transition is not allowed for hypothesis_scout")
        _validate_identifier_tuple("alpha_spec_ids", self.alpha_spec_ids, allow_empty=False)
        _validate_identifier_tuple(
            "consulted_rejection_reason_refs",
            self.consulted_rejection_reason_refs,
            allow_empty=True,
        )
        _validate_identifier_tuple(
            "tool_result_request_ids",
            self.tool_result_request_ids,
            allow_empty=False,
        )
        _validate_identifier_tuple("blocking_findings", self.blocking_findings, allow_empty=True)
        _validate_identifier("next_required_gate", self.next_required_gate)
        _validate_identifier_tuple("limitations", self.limitations, allow_empty=False)


_ROLE_CONTRACT = AgentRole(
    role_id=ROLE_ID,
    name="Hypothesis Scout",
    purpose="Draft 3-5 value-free AlphaSpec draft refs for one scoped ResearchTask.",
    readable_inputs=(
        "queue.models.ResearchTask scoped task ref",
        "queue.models.AgentAssignment for hypothesis_scout",
        "read_only_rejected_idea_memory_summaries",
        "read_only_research_library_memory_summaries",
        "permissions.matrix.hypothesis_scout entry",
    ),
    callable_tools=CALLABLE_TOOL_IDS,
    producible_outputs=(
        "3-5 governance.alpha_spec.AlphaSpec draft refs",
        "AgentToolResult value-free draft result",
        "AgentHandoff decision_to_draft linkage",
    ),
    allowed_decisions=(
        "draft_alphaspec_content_within_task_family",
        "select_3_to_5_drafts_within_variant_budget",
        "flag_duplicate_prior_rejection_refs",
    ),
    forbidden_decisions=(
        "approve_own_alphaspec",
        "critique_own_alphaspec",
        "implement_code",
        "run_diagnostics",
        "resolve_or_select_datasets",
        "write_any_registry",
        "promote_candidate",
        "claim_alpha_profitability_tradability",
        "exceed_variant_budget",
        "draft_outside_scoped_family_or_partitions",
        "start_loop_or_continuous_runner",
    ),
    handoff_format=(
        "decision_ref",
        "draft_alpha_spec_ids",
        "scoped_research_task_id",
        "agent_assignment_id",
        "consulted_prior_rejection_reason_refs",
        "blocking_findings",
        "next_required_gate",
        "limitations",
    ),
    reviewer_independence=(
        "generator_role_is_hypothesis_scout",
        "approver_role_is_alpha_spec_critic",
        "generator_must_not_equal_approver",
    ),
    failure_modes=(
        "missing_scoped_task_or_assignment_blocks",
        "prior_inputs_unavailable_inputs_blocked",
        "duplicate_prior_rejection_ref_flagged_or_dropped",
        "variant_budget_exceeded_bounded_refusal",
    ),
)

try:
    HypothesisScout = register(_ROLE_CONTRACT)
except ValueError as error:
    if "role_id already registered" not in str(error):
        raise
    HypothesisScout = get(ROLE_ID)


def validate_assignment(task: ResearchTask, assignment: AgentAssignment) -> None:
    """Validate that the assignment scopes the Scout to exactly one task."""

    _validate_task_and_assignment(task, assignment)


def validate_draft_batch(
    drafts: tuple[AlphaSpecDraftRef, ...],
    task: ResearchTask,
) -> tuple[AlphaSpecDraftRef, ...]:
    """Validate 3-5 draft refs and the task VariantBudget bound."""

    if not isinstance(task, ResearchTask):
        raise TypeError("task must be a ResearchTask")
    if not isinstance(drafts, tuple):
        raise TypeError("drafts must be a tuple[AlphaSpecDraftRef, ...]")
    if not (MIN_DRAFTS <= len(drafts) <= MAX_DRAFTS):
        raise ValueError("hypothesis_scout must produce between 3 and 5 drafts")
    if len(drafts) > task.research_budget.variant_budget.max_variants:
        raise ValueError("draft count exceeds the scoped task VariantBudget")

    seen_alpha_spec_ids: set[str] = set()
    for draft in drafts:
        if not isinstance(draft, AlphaSpecDraftRef):
            raise TypeError("drafts must contain only AlphaSpecDraftRef values")
        if draft.alpha_spec_id in seen_alpha_spec_ids:
            raise ValueError("drafts must not contain duplicate alpha_spec_id values")
        seen_alpha_spec_ids.add(draft.alpha_spec_id)
        if draft.task_id != task.task_id:
            raise ValueError("draft task_id must match the scoped ResearchTask")
        if draft.alpha_family not in task.allowed_alpha_family:
            raise ValueError("draft alpha_family must stay inside the scoped task family")
    return drafts


def surface_prior_rejections(
    draft: AlphaSpecDraftRef,
    prior_rejections: tuple[RejectionReasonRecordRef, ...],
) -> AlphaSpecDraftRef:
    """Return the draft with matched prior-rejection refs surfaced."""

    if not isinstance(draft, AlphaSpecDraftRef):
        raise TypeError("draft must be an AlphaSpecDraftRef")
    if not isinstance(prior_rejections, tuple):
        raise TypeError("prior_rejections must be a tuple[RejectionReasonRecordRef, ...]")

    matched_refs: list[str] = list(draft.prior_rejection_reason_refs)
    for record in prior_rejections:
        if not isinstance(record, RejectionReasonRecordRef):
            raise TypeError("prior_rejections must contain RejectionReasonRecordRef values")
        if record.idea_fingerprint == draft.idea_fingerprint:
            matched_refs.append(record.record_ref)

    surfaced_refs = tuple(sorted(set(matched_refs)))
    if surfaced_refs == draft.prior_rejection_reason_refs:
        return draft
    return replace(draft, prior_rejection_reason_refs=surfaced_refs)


def build_draft_tool_result(
    *,
    request_id: str,
    task: ResearchTask,
    assignment: AgentAssignment,
    drafts: tuple[AlphaSpecDraftRef, ...],
    prior_rejections: tuple[RejectionReasonRecordRef, ...] = (),
) -> AgentToolResult:
    """Build the value-free `AgentToolResult` for a bounded draft batch."""

    _validate_identifier("request_id", request_id)
    _validate_task_and_assignment(task, assignment)
    surfaced_drafts = tuple(surface_prior_rejections(draft, prior_rejections) for draft in drafts)
    validate_draft_batch(surfaced_drafts, task)
    surfaced_rejection_refs = tuple(
        sorted(
            {
                rejection_ref
                for draft in surfaced_drafts
                for rejection_ref in draft.prior_rejection_reason_refs
            }
        )
    )
    status = AgentToolStatus.WARN if surfaced_rejection_refs else AgentToolStatus.OK
    next_gate = (
        "alpha_spec_critic_duplicate_review"
        if surfaced_rejection_refs
        else NEXT_REVIEW_GATE
    )
    return AgentToolResult(
        status=status,
        role=ROLE_ID,
        request_id=request_id,
        alpha_spec_id=surfaced_drafts[0].alpha_spec_id,
        study_spec_id=None,
        dataset_version_id=task.allowed_dataset_version_id,
        feature_pack_refs=task.allowed_feature_pack_refs,
        label_pack_refs=task.allowed_label_pack_refs,
        runtime_run_id=None,
        diagnostics_summary=None,
        cost_summary=None,
        rejection_reasons=surfaced_rejection_refs,
        blocking_findings=(),
        next_required_gate=next_gate,
        artifacts=tuple(f"alphaspec_draft_ref:{draft.alpha_spec_id}" for draft in surfaced_drafts),
        limitations=DEFAULT_LIMITATIONS,
    )


def build_handoff(
    *,
    request_id: str,
    task: ResearchTask,
    assignment: AgentAssignment,
    drafts: tuple[AlphaSpecDraftRef, ...],
    tool_result: AgentToolResult,
) -> AgentHandoff:
    """Build the value-free Scout handoff linking decision to draft refs."""

    _validate_identifier("request_id", request_id)
    _validate_task_and_assignment(task, assignment)
    validate_draft_batch(drafts, task)
    if not isinstance(tool_result, AgentToolResult):
        raise TypeError("tool_result must be an AgentToolResult")
    if tool_result.role != ROLE_ID:
        raise ValueError("tool_result must belong to hypothesis_scout")

    consulted_refs = tuple(
        sorted(
            {
                rejection_ref
                for draft in drafts
                for rejection_ref in draft.prior_rejection_reason_refs
            }.union(tool_result.rejection_reasons)
        )
    )
    return AgentHandoff(
        role_id=ROLE_ID,
        request_id=request_id,
        task_id=task.task_id,
        assignment_id=assignment.assignment_id,
        decision="draft_alphaspec_refs_for_independent_review",
        source_task_status=ResearchTaskStatus.HYPOTHESIS_DRAFTED.value,
        target_task_status=ResearchTaskStatus.ALPHASPEC_DRAFTED.value,
        alpha_spec_ids=tuple(draft.alpha_spec_id for draft in drafts),
        consulted_rejection_reason_refs=consulted_refs,
        tool_result_request_ids=(tool_result.request_id,),
        blocking_findings=tool_result.blocking_findings,
        next_required_gate=tool_result.next_required_gate,
        limitations=DEFAULT_LIMITATIONS,
    )


def blocked_missing_task_result(request_id: str) -> AgentToolResult:
    """Return the missing-task fail-closed result shape."""

    _validate_identifier("request_id", request_id)
    return AgentToolResult(
        status=AgentToolStatus.BLOCKED,
        role=ROLE_ID,
        request_id=request_id,
        alpha_spec_id=None,
        study_spec_id=None,
        dataset_version_id=None,
        feature_pack_refs=(),
        label_pack_refs=(),
        runtime_run_id=None,
        diagnostics_summary=None,
        cost_summary=None,
        rejection_reasons=(),
        blocking_findings=("missing_scoped_task_or_assignment",),
        next_required_gate="research_director_scope_task",
        artifacts=(),
        limitations=DEFAULT_LIMITATIONS,
    )


def inputs_blocked_result(
    request_id: str,
    unavailable_inputs: tuple[str, ...],
) -> AgentToolResult:
    """Return the unavailable-inputs fail-closed result shape."""

    _validate_identifier("request_id", request_id)
    _validate_identifier_tuple("unavailable_inputs", unavailable_inputs, allow_empty=False)
    return AgentToolResult(
        status=AgentToolStatus.BLOCKED,
        role=ROLE_ID,
        request_id=request_id,
        alpha_spec_id=None,
        study_spec_id=None,
        dataset_version_id=None,
        feature_pack_refs=(),
        label_pack_refs=(),
        runtime_run_id=None,
        diagnostics_summary=None,
        cost_summary=None,
        rejection_reasons=(),
        blocking_findings=tuple(f"inputs_blocked:{item}" for item in unavailable_inputs),
        next_required_gate="operator_restore_value_free_memory_summaries",
        artifacts=(),
        limitations=DEFAULT_LIMITATIONS,
    )


def permission_matrix_entry():
    """Return the linked P04 permission entry without granting any authority."""

    return permission_for(ROLE_ID)


def _validate_task_and_assignment(task: ResearchTask, assignment: AgentAssignment) -> None:
    if not isinstance(task, ResearchTask):
        raise TypeError("task must be a ResearchTask")
    if not isinstance(assignment, AgentAssignment):
        raise TypeError("assignment must be an AgentAssignment")
    if assignment.role_id != ROLE_ID:
        raise ValueError("assignment.role_id must be hypothesis_scout")
    if assignment.task_id != task.task_id:
        raise ValueError("assignment.task_id must match the scoped ResearchTask")


def _validate_task_status_name(field_name: str, value: object) -> None:
    _validate_text(field_name, value)
    if value in PROHIBITED_MVP_TASK_STATUSES:
        raise ValueError(f"{field_name} uses a prohibited MVP state")
    try:
        ResearchTaskStatus(value)
    except ValueError as error:
        raise ValueError(f"{field_name} must be an allowed ResearchTaskStatus") from error


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
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must not contain duplicates")
    for item in value:
        _validate_identifier(field_name, item)


def _validate_identifier(field_name: str, value: object) -> None:
    _validate_text(field_name, value)
    if not _CONTRACT_ID_PATTERN.fullmatch(value):
        raise ValueError(f"{field_name} must be a stable declarative identifier")


def _validate_text(field_name: str, value: object) -> None:
    _reject_raw_object(field_name, value)
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a str")
    if value != value.strip() or not value:
        raise ValueError(f"{field_name} must be non-empty without surrounding whitespace")
    if len(value) > _MAX_SCOUT_TEXT_LENGTH:
        raise ValueError(f"{field_name} exceeds contract text length")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{field_name} must be a single-line contract string")
    lowered = value.lower()
    if any(marker in lowered for marker in FORBIDDEN_RESULT_MARKERS):
        raise ValueError(f"{field_name} contains a forbidden raw/heavy payload marker")
    if any(suffix in lowered for suffix in FORBIDDEN_HEAVY_SUFFIXES):
        raise ValueError(f"{field_name} contains a forbidden heavy artifact reference")


def _reject_raw_object(field_name: str, value: object) -> None:
    if isinstance(value, (bytes, bytearray, memoryview)):
        raise TypeError(f"{field_name} must not contain bytes")
    module_root = type(value).__module__.split(".", 1)[0]
    if module_root in RAW_OBJECT_MODULE_PREFIXES:
        raise TypeError(f"{field_name} must not contain dataframe or array objects")


__all__ = [
    "ALLOWED_TRANSITIONS",
    "BRANCH_OR_TERMINAL_STATES",
    "CALLABLE_TOOL_IDS",
    "DEFAULT_LIMITATIONS",
    "MAX_DRAFTS",
    "MIN_DRAFTS",
    "NEXT_REVIEW_GATE",
    "ROLE_ID",
    "AgentHandoff",
    "AlphaSpecDraftRef",
    "HypothesisScout",
    "RejectionReasonRecordRef",
    "blocked_missing_task_result",
    "build_draft_tool_result",
    "build_handoff",
    "inputs_blocked_result",
    "permission_matrix_entry",
    "surface_prior_rejections",
    "validate_assignment",
    "validate_draft_batch",
]
