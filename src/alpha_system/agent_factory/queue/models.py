"""Value-free Agent Factory research queue and work-item contracts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, TypeVar

from alpha_system.agent_factory.permissions.matrix import (
    REVIEW_ROLE_IDS,
    ROSTER_ROLE_IDS,
    permission_for,
)
from alpha_system.agent_factory.tools.results import (
    FORBIDDEN_HEAVY_SUFFIXES,
    FORBIDDEN_RESULT_MARKERS,
    RAW_OBJECT_MODULE_PREFIXES,
)

MAX_QUEUE_TEXT_LENGTH = 512
MAX_ALPHA_FAMILIES_PER_TASK = 3
MAX_VARIANTS_PER_TASK = 25
MAX_RUNTIME_MINUTES_PER_TASK = 720
MAX_RETRY_ATTEMPTS = 3
MAX_QUEUE_TASKS = 100
MAX_TASK_PRIORITY_RANK = 10_000
MAX_FAMILY_TASK_CAP = 25
MAX_FAMILY_VARIANT_CAP = 100
MAX_FAMILY_RUNTIME_MINUTES_CAP = 2_880

_CONTRACT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_.:-]*$")
_FORBIDDEN_ALPHA_FAMILY_VALUES: frozenset[str] = frozenset(
    {"*", "all", "any", "all_families", "all_alpha_families", "global"}
)
_FORBIDDEN_RUNNER_MARKERS: tuple[str, ...] = (
    "continuous runner",
    "daily runner",
    "weekly runner",
    "self-feeding",
    "auto enqueue",
    "auto-enqueue",
    "autonomous research running",
)

_EnumT = TypeVar("_EnumT", bound=StrEnum)


class ResearchTaskStatus(StrEnum):
    """Allowed MVP task lifecycle states for a bounded research task."""

    RESEARCH_TASK_QUEUED = "RESEARCH_TASK_QUEUED"
    DIRECTOR_SCOPED = "DIRECTOR_SCOPED"
    HYPOTHESIS_DRAFTED = "HYPOTHESIS_DRAFTED"
    ALPHASPEC_DRAFTED = "ALPHASPEC_DRAFTED"
    ALPHASPEC_CRITIQUED = "ALPHASPEC_CRITIQUED"
    ALPHASPEC_REVISION_REQUESTED = "ALPHASPEC_REVISION_REQUESTED"
    ALPHASPEC_REJECTED = "ALPHASPEC_REJECTED"
    DATA_CONTRACT_AUDITED = "DATA_CONTRACT_AUDITED"
    INPUTS_BLOCKED = "INPUTS_BLOCKED"
    IMPLEMENTATION_SCOPED = "IMPLEMENTATION_SCOPED"
    DIAGNOSTICS_REQUESTED = "DIAGNOSTICS_REQUESTED"
    DIAGNOSTICS_COMPLETE = "DIAGNOSTICS_COMPLETE"
    NO_LOOKAHEAD_AUDITED = "NO_LOOKAHEAD_AUDITED"
    STATISTICAL_REVIEW_PASS = "STATISTICAL_REVIEW_PASS"
    STATISTICAL_REVIEW_WATCH = "STATISTICAL_REVIEW_WATCH"
    STATISTICAL_REVIEW_REJECT = "STATISTICAL_REVIEW_REJECT"
    STATISTICAL_REVIEW_INCONCLUSIVE = "STATISTICAL_REVIEW_INCONCLUSIVE"
    EVIDENCE_DRAFT_RECORDED = "EVIDENCE_DRAFT_RECORDED"
    REFERENCE_HANDOFF_RECORDED = "REFERENCE_HANDOFF_RECORDED"
    LIBRARIAN_MEMORY_RECORDED = "LIBRARIAN_MEMORY_RECORDED"
    REJECTED = "REJECTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    BLOCKED = "BLOCKED"


PROHIBITED_MVP_TASK_STATUSES: frozenset[str] = frozenset(
    {
        "ALPHA_VALIDATED",
        "FACTOR_PROMOTED",
        "STRATEGY_READY",
        "PORTFOLIO_READY",
        "CANDIDATE_PROMOTED",
        "LIVE_READY",
        "PAPER_READY",
        "PROFITABLE",
        "TRADABLE",
        "PRODUCTION_READY",
        "AUTONOMOUS_RESEARCH_RUNNING",
    }
)


class DatasetVersionState(StrEnum):
    """Admissible DatasetVersion states for Agent Factory queue contracts."""

    VERSIONED = "VERSIONED"
    READY_FOR_RESEARCH = "READY_FOR_RESEARCH"


class ResearchPartition(StrEnum):
    """Campaign partition refs carried by a task."""

    DEVELOPMENT = "development"
    VALIDATION = "validation"
    LOCKED_TEST_CANDIDATE = "locked_test_candidate"
    LATEST_SHADOW_CANDIDATE = "latest_shadow_candidate"


class BlockerKind(StrEnum):
    """Structured blocker categories the queue can record without resolving them."""

    INPUTS_BLOCKED = "inputs_blocked"
    LOCKED_TEST_GOVERNANCE_METADATA_REQUIRED = "locked_test_governance_metadata_required"
    FEATURE_LABEL_PARQUET_SINK_REQUIRED = "feature_label_parquet_sink_required"
    SESSION_LABEL_GUARD_FIX_REQUIRED = "session_label_guard_fix_required"
    SCOPE_BLOCKED = "scope_blocked"


@dataclass(frozen=True, slots=True)
class VariantBudget:
    """Finite variant cap for one task."""

    max_variants: int

    def __post_init__(self) -> None:
        _validate_positive_int(
            "max_variants",
            self.max_variants,
            max_value=MAX_VARIANTS_PER_TASK,
        )


@dataclass(frozen=True, slots=True)
class ComputeBudget:
    """Finite runtime cap for one task."""

    max_runtime_minutes: int

    def __post_init__(self) -> None:
        _validate_positive_int(
            "max_runtime_minutes",
            self.max_runtime_minutes,
            max_value=MAX_RUNTIME_MINUTES_PER_TASK,
        )


@dataclass(frozen=True, slots=True)
class ResearchBudget:
    """Composed hard cap for variants and local compute."""

    variant_budget: VariantBudget
    compute_budget: ComputeBudget

    def __post_init__(self) -> None:
        _validate_type("variant_budget", self.variant_budget, VariantBudget)
        _validate_type("compute_budget", self.compute_budget, ComputeBudget)


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Bounded retry declaration; zero attempts means no retry."""

    max_attempts: int
    retry_on_statuses: tuple[ResearchTaskStatus, ...]

    def __post_init__(self) -> None:
        _validate_non_negative_int(
            "max_attempts",
            self.max_attempts,
            max_value=MAX_RETRY_ATTEMPTS,
        )
        object.__setattr__(
            self,
            "retry_on_statuses",
            _coerce_status_tuple("retry_on_statuses", self.retry_on_statuses, allow_empty=True),
        )
        if self.max_attempts == 0 and self.retry_on_statuses:
            raise ValueError("retry_on_statuses must be empty when max_attempts is zero")
        if self.max_attempts > 0 and not self.retry_on_statuses:
            raise ValueError("retry_on_statuses must be explicit when max_attempts is positive")


@dataclass(frozen=True, slots=True)
class ReviewRequirement:
    """Independent review required before a task can advance."""

    review_id: str
    review_kind: str
    reviewer_role_id: str
    independent_from_role_ids: tuple[str, ...]
    required_before_status: ResearchTaskStatus
    satisfied_by_ref: str | None = None

    def __post_init__(self) -> None:
        _validate_identifier("review_id", self.review_id)
        _validate_identifier("review_kind", self.review_kind)
        _validate_role_id("reviewer_role_id", self.reviewer_role_id)
        if self.reviewer_role_id not in REVIEW_ROLE_IDS:
            raise ValueError("reviewer_role_id must be an independent review role")
        _validate_role_tuple(
            "independent_from_role_ids",
            self.independent_from_role_ids,
            allow_empty=False,
        )
        if self.reviewer_role_id in self.independent_from_role_ids:
            raise ValueError("reviewer_role_id must be independent from reviewed roles")
        object.__setattr__(
            self,
            "required_before_status",
            _coerce_task_status(self.required_before_status),
        )
        _validate_optional_identifier("satisfied_by_ref", self.satisfied_by_ref)


@dataclass(frozen=True, slots=True)
class BlockerRecord:
    """Truthful structured blocker record for a task."""

    blocker_id: str
    blocker_kind: BlockerKind
    blocked_refs: tuple[str, ...]
    reason: str
    required_resolution: str
    next_action: str

    def __post_init__(self) -> None:
        _validate_identifier("blocker_id", self.blocker_id)
        object.__setattr__(
            self,
            "blocker_kind",
            _coerce_enum(BlockerKind, self.blocker_kind, "blocker_kind"),
        )
        _validate_identifier_tuple("blocked_refs", self.blocked_refs, allow_empty=False)
        _validate_text("reason", self.reason)
        _validate_text("required_resolution", self.required_resolution)
        _validate_identifier("next_action", self.next_action)


@dataclass(frozen=True, slots=True)
class AgentAssignment:
    """Bind one known role id to one task id without carrying permissions."""

    assignment_id: str
    task_id: str
    role_id: str
    assignment_scope_ref: str

    def __post_init__(self) -> None:
        _validate_identifier("assignment_id", self.assignment_id)
        _validate_identifier("task_id", self.task_id)
        _validate_role_id("role_id", self.role_id)
        _validate_identifier("assignment_scope_ref", self.assignment_scope_ref)
        permission_for(self.role_id)


@dataclass(frozen=True, slots=True)
class ResearchTask:
    """Single bounded unit of Agent Factory research work."""

    task_id: str
    task_status: ResearchTaskStatus
    allowed_alpha_family: tuple[str, ...]
    allowed_dataset_version_id: str
    allowed_dataset_version_state: DatasetVersionState
    allowed_feature_pack_refs: tuple[str, ...]
    allowed_label_pack_refs: tuple[str, ...]
    allowed_partitions: tuple[ResearchPartition, ...]
    blocked_partitions: tuple[ResearchPartition, ...]
    research_budget: ResearchBudget
    review_requirements: tuple[ReviewRequirement, ...]
    retry_policy: RetryPolicy
    next_action: str
    rejection_reason: str | None = None
    blocker: BlockerRecord | None = None
    partition_governance_metadata_refs: tuple[str, ...] = ()
    priority_rank: int = 100
    assignments: tuple[AgentAssignment, ...] = ()

    def __post_init__(self) -> None:
        _validate_identifier("task_id", self.task_id)
        object.__setattr__(self, "task_status", _coerce_task_status(self.task_status))
        _validate_alpha_family_tuple("allowed_alpha_family", self.allowed_alpha_family)
        _validate_identifier("allowed_dataset_version_id", self.allowed_dataset_version_id)
        object.__setattr__(
            self,
            "allowed_dataset_version_state",
            _coerce_enum(
                DatasetVersionState,
                self.allowed_dataset_version_state,
                "allowed_dataset_version_state",
            ),
        )
        _validate_identifier_tuple(
            "allowed_feature_pack_refs",
            self.allowed_feature_pack_refs,
            allow_empty=False,
        )
        _validate_identifier_tuple(
            "allowed_label_pack_refs",
            self.allowed_label_pack_refs,
            allow_empty=False,
        )
        object.__setattr__(
            self,
            "allowed_partitions",
            _coerce_partition_tuple("allowed_partitions", self.allowed_partitions),
        )
        object.__setattr__(
            self,
            "blocked_partitions",
            _coerce_partition_tuple(
                "blocked_partitions",
                self.blocked_partitions,
                allow_empty=True,
            ),
        )
        _validate_type("research_budget", self.research_budget, ResearchBudget)
        _validate_review_requirements(self.review_requirements)
        _validate_type("retry_policy", self.retry_policy, RetryPolicy)
        _validate_identifier("next_action", self.next_action)
        _validate_optional_text("rejection_reason", self.rejection_reason)
        _validate_optional_type("blocker", self.blocker, BlockerRecord)
        _validate_identifier_tuple(
            "partition_governance_metadata_refs",
            self.partition_governance_metadata_refs,
            allow_empty=True,
        )
        _validate_positive_int(
            "priority_rank",
            self.priority_rank,
            max_value=MAX_TASK_PRIORITY_RANK,
        )
        _validate_assignments(self.task_id, self.assignments)
        _validate_partition_policy(
            self.allowed_partitions,
            self.blocked_partitions,
            self.partition_governance_metadata_refs,
        )
        if self.task_status is ResearchTaskStatus.REJECTED and self.rejection_reason is None:
            raise ValueError("rejected tasks require a rejection_reason")
        if self.task_status in {
            ResearchTaskStatus.BLOCKED,
            ResearchTaskStatus.INPUTS_BLOCKED,
        } and self.blocker is None:
            raise ValueError("blocked tasks require a blocker record")


ALL_TASK_STATUSES: tuple[ResearchTaskStatus, ...] = tuple(ResearchTaskStatus)


@dataclass(frozen=True, slots=True)
class QueuePriorityPolicy:
    """Deterministic operator-priority ordering with task-id tie breaking."""

    policy_id: str
    status_order: tuple[ResearchTaskStatus, ...] = ALL_TASK_STATUSES
    tie_breaker: str = "task_id"

    def __post_init__(self) -> None:
        _validate_identifier("policy_id", self.policy_id)
        object.__setattr__(
            self,
            "status_order",
            _coerce_status_tuple("status_order", self.status_order, allow_empty=False),
        )
        _validate_identifier("tie_breaker", self.tie_breaker)
        if self.tie_breaker != "task_id":
            raise ValueError("QueuePriorityPolicy tie_breaker must be task_id")

    def sort_key(self, task: ResearchTask) -> tuple[int, int, str]:
        """Return a deterministic sort key for an already-declared task."""

        _validate_type("task", task, ResearchTask)
        try:
            status_rank = self.status_order.index(task.task_status)
        except ValueError:
            status_rank = len(self.status_order)
        return (task.priority_rank, status_rank, task.task_id)


@dataclass(frozen=True, slots=True)
class FamilyBudgetPolicy:
    """Finite per-family caps across one bounded queue."""

    max_tasks_per_family: int
    max_variants_per_family: int
    max_runtime_minutes_per_family: int

    def __post_init__(self) -> None:
        _validate_positive_int(
            "max_tasks_per_family",
            self.max_tasks_per_family,
            max_value=MAX_FAMILY_TASK_CAP,
        )
        _validate_positive_int(
            "max_variants_per_family",
            self.max_variants_per_family,
            max_value=MAX_FAMILY_VARIANT_CAP,
        )
        _validate_positive_int(
            "max_runtime_minutes_per_family",
            self.max_runtime_minutes_per_family,
            max_value=MAX_FAMILY_RUNTIME_MINUTES_CAP,
        )

    def validate_tasks(self, tasks: tuple[ResearchTask, ...]) -> None:
        """Fail when one alpha family exceeds any queue-level cap."""

        task_counts: dict[str, int] = {}
        variant_counts: dict[str, int] = {}
        runtime_counts: dict[str, int] = {}

        for task in tasks:
            _validate_type("task", task, ResearchTask)
            for family in task.allowed_alpha_family:
                task_counts[family] = task_counts.get(family, 0) + 1
                variant_counts[family] = (
                    variant_counts.get(family, 0)
                    + task.research_budget.variant_budget.max_variants
                )
                runtime_counts[family] = (
                    runtime_counts.get(family, 0)
                    + task.research_budget.compute_budget.max_runtime_minutes
                )

        for family, count in task_counts.items():
            if count > self.max_tasks_per_family:
                raise ValueError(f"family {family} exceeds task cap")
            if variant_counts[family] > self.max_variants_per_family:
                raise ValueError(f"family {family} exceeds variant cap")
            if runtime_counts[family] > self.max_runtime_minutes_per_family:
                raise ValueError(f"family {family} exceeds runtime cap")


@dataclass(frozen=True, slots=True)
class ResearchQueue:
    """Finite operator-declared queue of bounded research tasks."""

    queue_id: str
    tasks: tuple[ResearchTask, ...]
    priority_policy: QueuePriorityPolicy
    family_budget_policy: FamilyBudgetPolicy
    max_tasks: int

    def __post_init__(self) -> None:
        _validate_identifier("queue_id", self.queue_id)
        _validate_task_tuple("tasks", self.tasks, max_tasks=self.max_tasks)
        _validate_type("priority_policy", self.priority_policy, QueuePriorityPolicy)
        _validate_type("family_budget_policy", self.family_budget_policy, FamilyBudgetPolicy)
        _validate_positive_int("max_tasks", self.max_tasks, max_value=MAX_QUEUE_TASKS)
        self.family_budget_policy.validate_tasks(self.tasks)

    def ordered_tasks(self) -> tuple[ResearchTask, ...]:
        """Return the finite queue in deterministic priority order."""

        return tuple(sorted(self.tasks, key=self.priority_policy.sort_key))


def _coerce_task_status(value: object) -> ResearchTaskStatus:
    _reject_raw_object("task_status", value)
    if isinstance(value, str) and value in PROHIBITED_MVP_TASK_STATUSES:
        raise ValueError("task_status is prohibited for the Agent Factory MVP")
    return _coerce_enum(ResearchTaskStatus, value, "task_status")


def _coerce_status_tuple(
    field_name: str,
    value: object,
    *,
    allow_empty: bool = False,
) -> tuple[ResearchTaskStatus, ...]:
    _reject_raw_object(field_name, value)
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple[ResearchTaskStatus, ...]")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must be non-empty")
    statuses = tuple(_coerce_task_status(item) for item in value)
    if len(set(statuses)) != len(statuses):
        raise ValueError(f"{field_name} must not contain duplicates")
    return statuses


def _coerce_partition_tuple(
    field_name: str,
    value: object,
    *,
    allow_empty: bool = False,
) -> tuple[ResearchPartition, ...]:
    _reject_raw_object(field_name, value)
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple[ResearchPartition, ...]")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must be non-empty")
    partitions = tuple(
        _coerce_enum(ResearchPartition, item, field_name) for item in value
    )
    if len(set(partitions)) != len(partitions):
        raise ValueError(f"{field_name} must not contain duplicates")
    return partitions


def _coerce_enum(enum_type: type[_EnumT], value: object, field_name: str) -> _EnumT:
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


def _validate_task_tuple(field_name: str, value: object, *, max_tasks: object) -> None:
    _reject_raw_object(field_name, value)
    _validate_positive_int("max_tasks", max_tasks, max_value=MAX_QUEUE_TASKS)
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple[ResearchTask, ...]")
    if len(value) > max_tasks:
        raise ValueError(f"{field_name} exceeds max_tasks")
    task_ids: set[str] = set()
    for task in value:
        _validate_type(field_name, task, ResearchTask)
        if task.task_id in task_ids:
            raise ValueError(f"{field_name} must not contain duplicate task_id values")
        task_ids.add(task.task_id)


def _validate_review_requirements(value: object) -> None:
    _reject_raw_object("review_requirements", value)
    if not isinstance(value, tuple):
        raise TypeError("review_requirements must be a tuple[ReviewRequirement, ...]")
    if not value:
        raise ValueError("review_requirements must be non-empty")
    review_ids: set[str] = set()
    for requirement in value:
        _validate_type("review_requirements", requirement, ReviewRequirement)
        if requirement.review_id in review_ids:
            raise ValueError("review_requirements must not contain duplicate review_id values")
        review_ids.add(requirement.review_id)


def _validate_assignments(task_id: str, value: object) -> None:
    _reject_raw_object("assignments", value)
    if not isinstance(value, tuple):
        raise TypeError("assignments must be a tuple[AgentAssignment, ...]")
    assignment_ids: set[str] = set()
    role_ids: set[str] = set()
    for assignment in value:
        _validate_type("assignments", assignment, AgentAssignment)
        if assignment.task_id != task_id:
            raise ValueError("assignment task_id must match ResearchTask.task_id")
        if assignment.assignment_id in assignment_ids:
            raise ValueError("assignments must not contain duplicate assignment_id values")
        if assignment.role_id in role_ids:
            raise ValueError("assignments must not contain duplicate role_id values")
        assignment_ids.add(assignment.assignment_id)
        role_ids.add(assignment.role_id)


def _validate_partition_policy(
    allowed_partitions: tuple[ResearchPartition, ...],
    blocked_partitions: tuple[ResearchPartition, ...],
    governance_metadata_refs: tuple[str, ...],
) -> None:
    overlap = set(allowed_partitions).intersection(blocked_partitions)
    if overlap:
        raise ValueError(f"partitions cannot be both allowed and blocked: {sorted(overlap)}")
    if (
        ResearchPartition.LOCKED_TEST_CANDIDATE in allowed_partitions
        and not governance_metadata_refs
    ):
        raise ValueError("locked-test partition requires governance metadata refs")


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


def _validate_alpha_family_tuple(field_name: str, value: object) -> None:
    _validate_identifier_tuple(field_name, value, allow_empty=False)
    if len(value) > MAX_ALPHA_FAMILIES_PER_TASK:
        raise ValueError(f"{field_name} exceeds the small-set family cap")
    for family in value:
        if family.lower() in _FORBIDDEN_ALPHA_FAMILY_VALUES:
            raise ValueError(f"{field_name} cannot be unbounded")


def _validate_role_tuple(field_name: str, value: object, *, allow_empty: bool) -> None:
    _validate_identifier_tuple(field_name, value, allow_empty=allow_empty)
    for role_id in value:
        _validate_role_id(field_name, role_id)


def _validate_role_id(field_name: str, value: object) -> None:
    _validate_identifier(field_name, value)
    if value not in ROSTER_ROLE_IDS:
        raise ValueError(f"{field_name} contains an unknown Agent Factory role id")


def _validate_identifier(field_name: str, value: object) -> None:
    _validate_text(field_name, value)
    if not _CONTRACT_ID_PATTERN.fullmatch(value):
        raise ValueError(f"{field_name} must be a stable declarative identifier")


def _validate_optional_identifier(field_name: str, value: object) -> None:
    if value is None:
        return
    _validate_identifier(field_name, value)


def _validate_optional_text(field_name: str, value: object) -> None:
    if value is None:
        return
    _validate_text(field_name, value)


def _validate_text(field_name: str, value: object) -> None:
    _reject_raw_object(field_name, value)
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a str")
    if value != value.strip() or not value:
        raise ValueError(f"{field_name} must be non-empty without surrounding whitespace")
    if len(value) > MAX_QUEUE_TEXT_LENGTH:
        raise ValueError(f"{field_name} exceeds contract text length")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{field_name} must be a single-line contract string")
    lowered = value.lower()
    if any(marker in lowered for marker in FORBIDDEN_RESULT_MARKERS):
        raise ValueError(f"{field_name} contains a forbidden raw/heavy payload marker")
    if any(suffix in lowered for suffix in FORBIDDEN_HEAVY_SUFFIXES):
        raise ValueError(f"{field_name} contains a forbidden heavy artifact reference")
    if any(marker in lowered for marker in _FORBIDDEN_RUNNER_MARKERS):
        raise ValueError(f"{field_name} contains a prohibited continuous-runner marker")


def _validate_positive_int(field_name: str, value: object, *, max_value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
    if value > max_value:
        raise ValueError(f"{field_name} exceeds the hard finite cap")


def _validate_non_negative_int(field_name: str, value: object, *, max_value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    if value > max_value:
        raise ValueError(f"{field_name} exceeds the hard finite cap")


def _validate_type(field_name: str, value: object, expected_type: type[object]) -> None:
    _reject_raw_object(field_name, value)
    if not isinstance(value, expected_type):
        raise TypeError(f"{field_name} must be a {expected_type.__name__}")


def _validate_optional_type(
    field_name: str,
    value: object,
    expected_type: type[object],
) -> None:
    if value is None:
        return
    _validate_type(field_name, value, expected_type)


def _reject_raw_object(field_name: str, value: Any) -> None:
    if isinstance(value, (bytes, bytearray, memoryview)):
        raise TypeError(f"{field_name} must not contain bytes")
    module_root = type(value).__module__.split(".", 1)[0]
    if module_root in RAW_OBJECT_MODULE_PREFIXES:
        raise TypeError(f"{field_name} must not contain dataframe or array objects")
