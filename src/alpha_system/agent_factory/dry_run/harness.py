"""Bounded, synthetic Agent Factory dry-run harness.

The harness routes one value-free research task through the existing Agent
Factory contracts. It does not instantiate autonomous agents, start a runner,
search for alpha, call providers, or promote anything.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from alpha_system.agent_factory import runtime_bridge
from alpha_system.agent_factory.memory.models import (
    RejectedIdeaMemoryRecord,
    RejectedIdeaMemoryStatus,
    ResearchMemoryRecord,
    ResearchMemoryStatus,
    idea_fingerprint,
    idea_key,
)
from alpha_system.agent_factory.permissions.matrix import ROSTER_ROLE_IDS, permission_for
from alpha_system.agent_factory.queue.models import (
    PROHIBITED_MVP_TASK_STATUSES,
    AgentAssignment,
    ComputeBudget,
    DatasetVersionState,
    FamilyBudgetPolicy,
    QueuePriorityPolicy,
    ResearchBudget,
    ResearchPartition,
    ResearchQueue,
    ResearchTask,
    ResearchTaskStatus,
    RetryPolicy,
    ReviewRequirement,
    VariantBudget,
)
from alpha_system.agent_factory.records.models import (
    AgentDecisionClassification,
    AgentDecisionRecord,
    AgentHandoff,
    AgentRunRecord,
    AgentRunStatus,
    ToolInvocationRecord,
)
from alpha_system.agent_factory.roles import hypothesis_scout
from alpha_system.agent_factory.roles.statistical_reviewer import (
    statistical_review_verdict_result,
)
from alpha_system.agent_factory.separation.enforcement import (
    SeparationRuleResult,
    check_generator_approver_separation,
    check_implementer_reviewer_separation,
    check_librarian_verdict_required,
    check_reviewer_assignment_independent,
)
from alpha_system.agent_factory.separation.wiring import (
    SeparationBundle,
    assemble_validated_bundle,
)
from alpha_system.agent_factory.tools.results import AgentToolResult, AgentToolStatus

REQUEST_ID = "request:agent_p22_dry_run"
QUEUE_ID = "queue:agent_p22_synthetic"
TASK_ID = "research_task:agent_p22_synthetic"
DATASET_VERSION_ID = "dsv_agent_p22_synthetic"
FEATURE_PACK_REF = "feature_pack:agent_p22_seed_feature"
LABEL_PACK_REF = "label_pack:agent_p22_seed_label"
ALPHA_SPEC_ID = "alpha_spec:agent_p22_survivor"
STUDY_SPEC_ID = "study_spec:agent_p22_bound"
RUNTIME_RUN_ID = "runtime_run:agent_p22_synthetic"
SYNTHETIC_REGISTRY_REF = "registry:agent_p22_synthetic"
REVIEWER_VERDICT_REF = "reviewer_verdict:agent_p22_reject"

AGENT_DRY_RUN_ROLE_ROUTE: tuple[str, ...] = (
    "research_director",
    "hypothesis_scout",
    "alpha_spec_critic",
    "data_contract_auditor",
    "feature_engineer",
    "label_engineer",
    "diagnostics_runner",
    "no_lookahead_auditor",
    "statistical_reviewer",
    "librarian",
)

DRY_RUN_FORWARD_STATE_ORDER: tuple[ResearchTaskStatus, ...] = (
    ResearchTaskStatus.DIRECTOR_SCOPED,
    ResearchTaskStatus.ALPHASPEC_DRAFTED,
    ResearchTaskStatus.ALPHASPEC_CRITIQUED,
    ResearchTaskStatus.DATA_CONTRACT_AUDITED,
    ResearchTaskStatus.IMPLEMENTATION_SCOPED,
    ResearchTaskStatus.DIAGNOSTICS_COMPLETE,
    ResearchTaskStatus.NO_LOOKAHEAD_AUDITED,
    ResearchTaskStatus.EVIDENCE_DRAFT_RECORDED,
    ResearchTaskStatus.REFERENCE_HANDOFF_RECORDED,
)
MAX_DRY_RUN_FORWARD_STATE = ResearchTaskStatus.REFERENCE_HANDOFF_RECORDED
DRY_RUN_TERMINAL_STATES: tuple[ResearchTaskStatus, ...] = (
    ResearchTaskStatus.REJECTED,
    ResearchTaskStatus.INCONCLUSIVE,
    ResearchTaskStatus.BLOCKED,
)
PERMITTED_STATISTICAL_DRY_RUN_VERDICTS: tuple[str, ...] = (
    "REJECT",
    "WATCH",
    "INCONCLUSIVE",
)
DRY_RUN_LIMITATIONS: tuple[str, ...] = (
    "synthetic_fixture_only",
    "not_alpha_evidence",
    "no_promotion_reachable",
    "no_broker_live_paper_order_scope",
    "evidence_draft_not_candidate",
    "reference_handoff_not_validation",
)


class DryRunHarnessError(RuntimeError):
    """Raised when the dry-run cannot truthfully complete its bounded route."""


@dataclass(frozen=True, slots=True)
class SyntheticDatasetVersion:
    """Tiny resolver return object for the synthetic fixture DatasetVersion."""

    dataset_version_id: str = DATASET_VERSION_ID
    lifecycle_state: str = DatasetVersionState.READY_FOR_RESEARCH.value


@dataclass(frozen=True, slots=True)
class AgentDryRunReport:
    """Structured output from the single-task Agent Factory dry run."""

    request_id: str
    queue: ResearchQueue
    task: ResearchTask
    role_route: tuple[str, ...]
    separation_bundle: SeparationBundle
    run_records: tuple[AgentRunRecord, ...]
    decision_records: tuple[AgentDecisionRecord, ...]
    tool_results: tuple[AgentToolResult, ...]
    tool_invocations: tuple[ToolInvocationRecord, ...]
    handoffs: tuple[AgentHandoff, ...]
    scout_handoff: hypothesis_scout.AgentHandoff
    prior_rejection_refs: tuple[hypothesis_scout.RejectionReasonRecordRef, ...]
    rejected_idea_memory: RejectedIdeaMemoryRecord
    research_memory: ResearchMemoryRecord
    reachable_task_statuses: tuple[ResearchTaskStatus, ...]
    terminal_state: ResearchTaskStatus
    max_forward_state: ResearchTaskStatus

    @property
    def selected_alpha_spec_id(self) -> str:
        """Return the single synthetic survivor AlphaSpec ref."""

        return ALPHA_SPEC_ID

    @property
    def study_spec_id(self) -> str:
        """Return the bound synthetic StudySpec ref."""

        return STUDY_SPEC_ID

    @property
    def registered_tool_names(self) -> tuple[str, ...]:
        """Return registered tool contracts exercised by invocation records."""

        return tuple(invocation.tool_name for invocation in self.tool_invocations)

    def result_for_role(self, role_id: str) -> AgentToolResult:
        """Return the first result emitted by a role in the dry-run route."""

        for result in self.tool_results:
            if result.role == role_id:
                return result
        raise KeyError(f"no dry-run result for role: {role_id}")


DatasetVersionResolver = Callable[[object, object], object | None]


def run_agent_dry_run(
    *,
    dataset_version_resolver: DatasetVersionResolver | None = None,
) -> AgentDryRunReport:
    """Route one bounded synthetic research task through the Agent Factory contracts."""

    resolver = dataset_version_resolver or synthetic_dataset_version_resolver
    separation_bundle = assemble_validated_bundle()
    known_role_ids = separation_bundle.role_ids

    assignments = _assignments()
    scoped_task = _scoped_task(assignments)
    queue = ResearchQueue(
        queue_id=QUEUE_ID,
        tasks=(scoped_task,),
        priority_policy=QueuePriorityPolicy(policy_id="queue_policy:agent_p22_dry_run"),
        family_budget_policy=FamilyBudgetPolicy(
            max_tasks_per_family=1,
            max_variants_per_family=5,
            max_runtime_minutes_per_family=30,
        ),
        max_tasks=1,
    )

    director_result = _director_result(scoped_task)
    prior_rejection_refs = _prior_rejection_refs()
    drafts = _drafts(scoped_task, assignments["hypothesis_scout"])
    scout_result = hypothesis_scout.build_draft_tool_result(
        request_id=REQUEST_ID,
        task=scoped_task,
        assignment=assignments["hypothesis_scout"],
        drafts=drafts,
        prior_rejections=prior_rejection_refs,
    )
    surfaced_drafts = tuple(
        hypothesis_scout.surface_prior_rejections(draft, prior_rejection_refs) for draft in drafts
    )
    scout_handoff = hypothesis_scout.build_handoff(
        request_id=REQUEST_ID,
        task=scoped_task,
        assignment=assignments["hypothesis_scout"],
        drafts=surfaced_drafts,
        tool_result=scout_result,
    )

    critic_result = _critic_result(
        surfaced_drafts,
        check_generator_approver_separation(
            "alphaspec_draft",
            "hypothesis_scout",
            "alpha_spec_critic",
            known_role_ids=known_role_ids,
        ),
    )
    data_result = _data_contract_result(resolver)
    if data_result.status is not AgentToolStatus.OK:
        return _blocked_report(
            queue=queue,
            task=scoped_task,
            separation_bundle=separation_bundle,
            director_result=director_result,
            scout_result=scout_result,
            scout_handoff=scout_handoff,
            critic_result=critic_result,
            data_result=data_result,
            prior_rejection_refs=prior_rejection_refs,
        )

    feature_result = _feature_result()
    label_result = _label_result()
    diagnostics_result = _diagnostics_result(resolver)
    if diagnostics_result.status is not AgentToolStatus.OK:
        return _blocked_report(
            queue=queue,
            task=scoped_task,
            separation_bundle=separation_bundle,
            director_result=director_result,
            scout_result=scout_result,
            scout_handoff=scout_handoff,
            critic_result=critic_result,
            data_result=data_result,
            prior_rejection_refs=prior_rejection_refs,
            extra_results=(feature_result, label_result, diagnostics_result),
        )

    no_lookahead_result = _no_lookahead_result(diagnostics_result)
    statistical_result = statistical_review_verdict_result(
        REQUEST_ID,
        "REJECT",
        evidence_summary_ref="evidence_summary:agent_p22_dry_run",
        no_lookahead_audit_summary_ref="lookahead_audit:agent_p22_pass",
        no_lookahead_status="PASS",
        alpha_spec_id=ALPHA_SPEC_ID,
        study_spec_id=STUDY_SPEC_ID,
        dataset_version_id=DATASET_VERSION_ID,
        feature_pack_refs=(FEATURE_PACK_REF,),
        label_pack_refs=(LABEL_PACK_REF,),
        runtime_run_id=RUNTIME_RUN_ID,
        rejection_reasons=("dry_run_reject_not_alpha_evidence",),
        blocking_findings=(),
        artifacts=("reviewer_verdict_ref:agent_p22_reject",),
        limitations=DRY_RUN_LIMITATIONS,
    )
    librarian_result = _librarian_result(statistical_result)

    separation_results = _separation_results(known_role_ids)
    run_records = _run_records(
        terminal_state=ResearchTaskStatus.REJECTED,
        target_statuses={
            "research_director": ResearchTaskStatus.DIRECTOR_SCOPED,
            "hypothesis_scout": ResearchTaskStatus.ALPHASPEC_DRAFTED,
            "alpha_spec_critic": ResearchTaskStatus.ALPHASPEC_CRITIQUED,
            "data_contract_auditor": ResearchTaskStatus.DATA_CONTRACT_AUDITED,
            "feature_engineer": ResearchTaskStatus.IMPLEMENTATION_SCOPED,
            "label_engineer": ResearchTaskStatus.IMPLEMENTATION_SCOPED,
            "diagnostics_runner": ResearchTaskStatus.REFERENCE_HANDOFF_RECORDED,
            "no_lookahead_auditor": ResearchTaskStatus.NO_LOOKAHEAD_AUDITED,
            "statistical_reviewer": ResearchTaskStatus.REJECTED,
            "librarian": ResearchTaskStatus.REJECTED,
        },
    )
    decision_records = _decision_records(separation_results)
    invocations = _tool_invocations(
        data_result=data_result,
        feature_result=feature_result,
        label_result=label_result,
        diagnostics_result=diagnostics_result,
        no_lookahead_result=no_lookahead_result,
        statistical_result=statistical_result,
        librarian_result=librarian_result,
    )
    handoffs = _handoffs(decision_records, invocations)
    rejected_memory = _rejected_memory(statistical_result, handoffs, invocations)
    research_memory = _research_memory(rejected_memory, handoffs, invocations)
    report = AgentDryRunReport(
        request_id=REQUEST_ID,
        queue=queue,
        task=scoped_task,
        role_route=AGENT_DRY_RUN_ROLE_ROUTE,
        separation_bundle=separation_bundle,
        run_records=run_records,
        decision_records=decision_records,
        tool_results=(
            director_result,
            scout_result,
            critic_result,
            data_result,
            feature_result,
            label_result,
            diagnostics_result,
            no_lookahead_result,
            statistical_result,
            librarian_result,
        ),
        tool_invocations=invocations,
        handoffs=handoffs,
        scout_handoff=scout_handoff,
        prior_rejection_refs=prior_rejection_refs,
        rejected_idea_memory=rejected_memory,
        research_memory=research_memory,
        reachable_task_statuses=(
            ResearchTaskStatus.DIRECTOR_SCOPED,
            ResearchTaskStatus.ALPHASPEC_DRAFTED,
            ResearchTaskStatus.ALPHASPEC_CRITIQUED,
            ResearchTaskStatus.DATA_CONTRACT_AUDITED,
            ResearchTaskStatus.IMPLEMENTATION_SCOPED,
            ResearchTaskStatus.DIAGNOSTICS_COMPLETE,
            ResearchTaskStatus.NO_LOOKAHEAD_AUDITED,
            ResearchTaskStatus.EVIDENCE_DRAFT_RECORDED,
            ResearchTaskStatus.REFERENCE_HANDOFF_RECORDED,
            ResearchTaskStatus.REJECTED,
        ),
        terminal_state=ResearchTaskStatus.REJECTED,
        max_forward_state=MAX_DRY_RUN_FORWARD_STATE,
    )
    validate_dry_run_report(report)
    return report


def synthetic_dataset_version_resolver(
    _registry_ref: object,
    dataset_version_id: object,
) -> SyntheticDatasetVersion | None:
    """Return the synthetic fixture DatasetVersion when the id matches."""

    if dataset_version_id != DATASET_VERSION_ID:
        return None
    return SyntheticDatasetVersion()


def validate_dry_run_report(report: AgentDryRunReport) -> AgentDryRunReport:
    """Fail closed if a dry-run report violates AGENT-P22 boundaries."""

    if not isinstance(report, AgentDryRunReport):
        raise TypeError("report must be an AgentDryRunReport")
    if report.role_route != AGENT_DRY_RUN_ROLE_ROUTE:
        raise DryRunHarnessError("dry-run role route changed")
    if len(report.queue.tasks) != 1:
        raise DryRunHarnessError("dry-run must contain exactly one ResearchTask")
    if set(report.role_route) != set(ROSTER_ROLE_IDS):
        raise DryRunHarnessError("dry-run route must cover the MVP role roster exactly")
    if report.terminal_state not in DRY_RUN_TERMINAL_STATES:
        raise DryRunHarnessError("dry-run terminal state must be rejected inconclusive or blocked")
    if report.terminal_state is ResearchTaskStatus.REJECTED:
        if report.max_forward_state is not MAX_DRY_RUN_FORWARD_STATE:
            raise DryRunHarnessError("dry-run forward state advanced past reference handoff")
    elif report.max_forward_state not in DRY_RUN_FORWARD_STATE_ORDER:
        raise DryRunHarnessError("blocked dry-run must stop on a known forward state")
    state_values = {state.value for state in report.reachable_task_statuses}
    if state_values.intersection(PROHIBITED_MVP_TASK_STATUSES):
        raise DryRunHarnessError("prohibited MVP state is reachable")
    if ResearchTaskStatus.LIBRARIAN_MEMORY_RECORDED in report.reachable_task_statuses:
        raise DryRunHarnessError("librarian memory is a record output, not a survivor state")
    if any(permission_for(role_id).promotion.can_promote for role_id in report.role_route):
        raise DryRunHarnessError("promotion permission surfaced in dry-run route")
    statistical_result = _optional_result_for_role(report, "statistical_reviewer")
    if statistical_result is not None and statistical_result.status is AgentToolStatus.OK:
        raise DryRunHarnessError("statistical reviewer PASS path is not allowed in dry-run")
    if (
        report.terminal_state is ResearchTaskStatus.REJECTED
        and report.rejected_idea_memory.status is not RejectedIdeaMemoryStatus.REJECTED
    ):
        raise DryRunHarnessError("default dry-run rejection memory must stay rejected")
    if (
        report.terminal_state is ResearchTaskStatus.REJECTED
        and report.research_memory.status is not ResearchMemoryStatus.REJECTED
    ):
        raise DryRunHarnessError("default dry-run research memory must stay rejected")
    return report


def _optional_result_for_role(
    report: AgentDryRunReport,
    role_id: str,
) -> AgentToolResult | None:
    for result in report.tool_results:
        if result.role == role_id:
            return result
    return None


def _assignments() -> dict[str, AgentAssignment]:
    return {
        role_id: AgentAssignment(
            assignment_id=f"assignment:{role_id}",
            task_id=TASK_ID,
            role_id=role_id,
            assignment_scope_ref=f"scope:{role_id}",
        )
        for role_id in AGENT_DRY_RUN_ROLE_ROUTE
    }


def _scoped_task(assignments: dict[str, AgentAssignment]) -> ResearchTask:
    return ResearchTask(
        task_id=TASK_ID,
        task_status=ResearchTaskStatus.DIRECTOR_SCOPED,
        allowed_alpha_family=("microstructure",),
        allowed_dataset_version_id=DATASET_VERSION_ID,
        allowed_dataset_version_state=DatasetVersionState.READY_FOR_RESEARCH,
        allowed_feature_pack_refs=(FEATURE_PACK_REF,),
        allowed_label_pack_refs=(LABEL_PACK_REF,),
        allowed_partitions=(ResearchPartition.DEVELOPMENT, ResearchPartition.VALIDATION),
        blocked_partitions=(),
        research_budget=ResearchBudget(
            variant_budget=VariantBudget(max_variants=5),
            compute_budget=ComputeBudget(max_runtime_minutes=30),
        ),
        review_requirements=(
            ReviewRequirement(
                review_id="review:alphaspec_critic",
                review_kind="alphaspec_critique",
                reviewer_role_id="alpha_spec_critic",
                independent_from_role_ids=("hypothesis_scout",),
                required_before_status=ResearchTaskStatus.ALPHASPEC_CRITIQUED,
            ),
            ReviewRequirement(
                review_id="review:statistical_reviewer",
                review_kind="runtime_evidence_review",
                reviewer_role_id="statistical_reviewer",
                independent_from_role_ids=(
                    "feature_engineer",
                    "label_engineer",
                    "diagnostics_runner",
                ),
                required_before_status=ResearchTaskStatus.REJECTED,
            ),
        ),
        retry_policy=RetryPolicy(max_attempts=0, retry_on_statuses=()),
        next_action="hypothesis_scout_draft",
        partition_governance_metadata_refs=("partition_governance:synthetic_dev_val",),
        priority_rank=1,
        assignments=tuple(assignments[role_id] for role_id in AGENT_DRY_RUN_ROLE_ROUTE),
    )


def _prior_rejection_refs() -> tuple[hypothesis_scout.RejectionReasonRecordRef, ...]:
    return (
        hypothesis_scout.RejectionReasonRecordRef(
            record_ref="rejection_reason:prior_duplicate",
            rejected_idea_ref="alpha_spec:prior_synthetic_duplicate",
            idea_fingerprint="idea:prior_duplicate",
            reason_category="duplicate_exposure",
            summary="Prior synthetic duplicate was rejected by independent review.",
        ),
    )


def _drafts(
    task: ResearchTask,
    assignment: AgentAssignment,
) -> tuple[hypothesis_scout.AlphaSpecDraftRef, ...]:
    return (
        hypothesis_scout.AlphaSpecDraftRef(
            alpha_spec_id="alpha_spec:agent_p22_duplicate",
            task_id=task.task_id,
            assignment_id=assignment.assignment_id,
            alpha_family="microstructure",
            idea_fingerprint="idea:prior_duplicate",
            summary="Synthetic duplicate draft routed for rejection-memory visibility.",
        ),
        hypothesis_scout.AlphaSpecDraftRef(
            alpha_spec_id="alpha_spec:agent_p22_revision",
            task_id=task.task_id,
            assignment_id=assignment.assignment_id,
            alpha_family="microstructure",
            idea_fingerprint="idea:revision_needed",
            summary="Synthetic draft with fixable contract gap for critic revision request.",
        ),
        hypothesis_scout.AlphaSpecDraftRef(
            alpha_spec_id=ALPHA_SPEC_ID,
            task_id=task.task_id,
            assignment_id=assignment.assignment_id,
            alpha_family="microstructure",
            idea_fingerprint="idea:bounded_survivor",
            summary="Synthetic survivor used only to drive downstream contracts.",
        ),
    )


def _director_result(task: ResearchTask) -> AgentToolResult:
    return AgentToolResult(
        status=AgentToolStatus.OK,
        role="research_director",
        request_id=REQUEST_ID,
        alpha_spec_id=None,
        study_spec_id=None,
        dataset_version_id=task.allowed_dataset_version_id,
        feature_pack_refs=task.allowed_feature_pack_refs,
        label_pack_refs=task.allowed_label_pack_refs,
        runtime_run_id=None,
        diagnostics_summary="single bounded ResearchTask scoped with finite budgets.",
        cost_summary=None,
        rejection_reasons=(),
        blocking_findings=(),
        next_required_gate="hypothesis_scout_draft",
        artifacts=(f"research_task_ref:{task.task_id}",),
        limitations=DRY_RUN_LIMITATIONS,
    )


def _critic_result(
    drafts: tuple[hypothesis_scout.AlphaSpecDraftRef, ...],
    separation_result: SeparationRuleResult,
) -> AgentToolResult:
    if not separation_result.is_pass:
        return AgentToolResult(
            status=AgentToolStatus.BLOCKED,
            role="alpha_spec_critic",
            request_id=REQUEST_ID,
            alpha_spec_id=None,
            study_spec_id=None,
            dataset_version_id=DATASET_VERSION_ID,
            feature_pack_refs=(FEATURE_PACK_REF,),
            label_pack_refs=(LABEL_PACK_REF,),
            runtime_run_id=None,
            diagnostics_summary="AlphaSpec critique blocked by separation check.",
            cost_summary=None,
            rejection_reasons=("alphaspec_critic_independence_blocked",),
            blocking_findings=(separation_result.rule_id,),
            next_required_gate="separation_of_duties_reassignment",
            artifacts=(),
            limitations=DRY_RUN_LIMITATIONS,
        )

    rejected = tuple(
        draft.alpha_spec_id for draft in drafts if draft.alpha_spec_id != ALPHA_SPEC_ID
    )
    return AgentToolResult(
        status=AgentToolStatus.WARN,
        role="alpha_spec_critic",
        request_id=REQUEST_ID,
        alpha_spec_id=ALPHA_SPEC_ID,
        study_spec_id=None,
        dataset_version_id=DATASET_VERSION_ID,
        feature_pack_refs=(FEATURE_PACK_REF,),
        label_pack_refs=(LABEL_PACK_REF,),
        runtime_run_id=None,
        diagnostics_summary="Critic rejected or revised most drafts and forwarded one bounded ref.",
        cost_summary=None,
        rejection_reasons=tuple(f"critic_rejected:{alpha_spec_id}" for alpha_spec_id in rejected),
        blocking_findings=(),
        next_required_gate="data_contract_auditor_audit_inputs",
        artifacts=(f"alphaspec_critiqued_ref:{ALPHA_SPEC_ID}",),
        limitations=DRY_RUN_LIMITATIONS,
    )


def _data_contract_result(resolver: DatasetVersionResolver) -> AgentToolResult:
    try:
        resolved = resolver(SYNTHETIC_REGISTRY_REF, DATASET_VERSION_ID)
    except (OSError, ValueError) as exc:
        return _blocked_tool_result(
            role="data_contract_auditor",
            reason=f"dataset_version_resolution_failed:{type(exc).__name__}",
            next_gate="operator_restore_synthetic_registry_summary",
        )
    if resolved is None:
        return _blocked_tool_result(
            role="data_contract_auditor",
            reason="dataset_version_not_found",
            next_gate="operator_restore_synthetic_registry_summary",
        )
    lifecycle_state = getattr(resolved, "lifecycle_state", None)
    if lifecycle_state not in {
        DatasetVersionState.VERSIONED.value,
        DatasetVersionState.READY_FOR_RESEARCH.value,
    }:
        return _blocked_tool_result(
            role="data_contract_auditor",
            reason="dataset_version_not_admissible",
            next_gate="operator_accept_synthetic_datasetversion",
        )
    return AgentToolResult(
        status=AgentToolStatus.OK,
        role="data_contract_auditor",
        request_id=REQUEST_ID,
        alpha_spec_id=ALPHA_SPEC_ID,
        study_spec_id=None,
        dataset_version_id=DATASET_VERSION_ID,
        feature_pack_refs=(FEATURE_PACK_REF,),
        label_pack_refs=(LABEL_PACK_REF,),
        runtime_run_id=None,
        diagnostics_summary="Synthetic DatasetVersion and one seed pack pair are available.",
        cost_summary=None,
        rejection_reasons=(),
        blocking_findings=(),
        next_required_gate="feature_label_engineers_reference_seed_inputs",
        artifacts=(
            f"dataset_version_ref:{DATASET_VERSION_ID}",
            f"feature_pack_ref:{FEATURE_PACK_REF}",
            f"label_pack_ref:{LABEL_PACK_REF}",
        ),
        limitations=DRY_RUN_LIMITATIONS,
    )


def _feature_result() -> AgentToolResult:
    return AgentToolResult(
        status=AgentToolStatus.OK,
        role="feature_engineer",
        request_id=REQUEST_ID,
        alpha_spec_id=ALPHA_SPEC_ID,
        study_spec_id=None,
        dataset_version_id=DATASET_VERSION_ID,
        feature_pack_refs=(FEATURE_PACK_REF,),
        label_pack_refs=(),
        runtime_run_id=None,
        diagnostics_summary="One approved synthetic seed FeaturePack ref selected.",
        cost_summary=None,
        rejection_reasons=(),
        blocking_findings=(),
        next_required_gate="label_engineer_reference_seed_input",
        artifacts=(f"feature_request_ref:{FEATURE_PACK_REF}",),
        limitations=DRY_RUN_LIMITATIONS + ("no_label_as_feature", "no_session_context_features"),
    )


def _label_result() -> AgentToolResult:
    return AgentToolResult(
        status=AgentToolStatus.OK,
        role="label_engineer",
        request_id=REQUEST_ID,
        alpha_spec_id=ALPHA_SPEC_ID,
        study_spec_id=STUDY_SPEC_ID,
        dataset_version_id=DATASET_VERSION_ID,
        feature_pack_refs=(),
        label_pack_refs=(LABEL_PACK_REF,),
        runtime_run_id=None,
        diagnostics_summary="One approved synthetic seed LabelPack ref selected.",
        cost_summary=None,
        rejection_reasons=(),
        blocking_findings=(),
        next_required_gate="diagnostics_runner_request_runtime_bridge",
        artifacts=(f"label_spec_ref:{LABEL_PACK_REF}", f"study_spec_ref:{STUDY_SPEC_ID}"),
        limitations=DRY_RUN_LIMITATIONS + ("no_label_as_feature", "no_session_context_features"),
    )


def _diagnostics_result(resolver: DatasetVersionResolver) -> AgentToolResult:
    return runtime_bridge.adapt_runtime_tool_result(
        _synthetic_runtime_result(),
        role="diagnostics_runner",
        request_id=REQUEST_ID,
        alpha_spec_id=ALPHA_SPEC_ID,
        study_spec_id=STUDY_SPEC_ID,
        registry_path=SYNTHETIC_REGISTRY_REF,
        dataset_lifecycle_state=DatasetVersionState.READY_FOR_RESEARCH.value,
        dataset_version_resolver=resolver,
    )


def _synthetic_runtime_result():
    return runtime_bridge.RuntimeToolResult.from_dict(
        {
            "status": "REFERENCE_HANDOFF_READY",
            "run_id": RUNTIME_RUN_ID,
            "version_ids": {
                "dataset_version_id": DATASET_VERSION_ID,
                "feature_pack_ids": [FEATURE_PACK_REF],
                "label_pack_ids": [LABEL_PACK_REF],
                "code_version": "code_version:agent_p22_dry_run",
                "config_version": "config_version:agent_p22_dry_run",
            },
            "diagnostics_summary": {
                "report_refs": [
                    {
                        "report_id": "report:agent_p22_diagnostics",
                        "report_hash": "hash:agent_p22_diagnostics",
                        "report_kind": "diagnostics",
                    }
                ],
                "coverage_summary": {
                    "report_count": 1,
                    "synthetic_fixture_count": 1,
                },
                "quality_summary": {
                    "warning_count": 1,
                    "dry_run_only": True,
                },
                "limitations": ["synthetic_fixture_only"],
            },
            "cost_summary": {
                "diagnostics_report_ref": {
                    "report_id": "report:agent_p22_cost",
                    "report_hash": "hash:agent_p22_cost",
                    "report_kind": "cost",
                },
                "cost_model_version_id": "cost_model:agent_p22_dry_run",
                "profile_count": 1,
                "double_cost_profile_name": "double_cost",
                "double_cost_combined_cost_slippage_proxy": "proxy_units_only",
                "slippage_labeled_proxy": True,
                "zero_cost_diagnostic_only": True,
                "bbo_spread_crossing_used": False,
                "bbo_unavailable_fallback_used": False,
            },
            "rejection_reasons": [],
            "artifacts": [
                {
                    "artifact_id": "artifact:agent_p22_evidence_draft",
                    "location": "runtime/reports/agent_p22_evidence_draft",
                    "content_hash": "hash:agent_p22_evidence_draft",
                },
                {
                    "artifact_id": "artifact:agent_p22_reference_candidate_handoff",
                    "location": "runtime/reports/agent_p22_reference_candidate_handoff",
                    "content_hash": "hash:agent_p22_reference_candidate_handoff",
                },
            ],
            "next_required_gate": "no_lookahead_auditor_review",
        }
    )


def _no_lookahead_result(diagnostics_result: AgentToolResult) -> AgentToolResult:
    return AgentToolResult(
        status=AgentToolStatus.OK,
        role="no_lookahead_auditor",
        request_id=REQUEST_ID,
        alpha_spec_id=ALPHA_SPEC_ID,
        study_spec_id=STUDY_SPEC_ID,
        dataset_version_id=DATASET_VERSION_ID,
        feature_pack_refs=(FEATURE_PACK_REF,),
        label_pack_refs=(LABEL_PACK_REF,),
        runtime_run_id=diagnostics_result.runtime_run_id,
        diagnostics_summary=(
            "no_lookahead_audit:PASS; checked=available_ts,label_available_ts,"
            "same_bar_fill_policy_ref,locked_test_partition_scope_ref"
        ),
        cost_summary=None,
        rejection_reasons=(),
        blocking_findings=(),
        next_required_gate="statistical_reviewer_independent_review",
        artifacts=("lookahead_audit_ref:agent_p22_pass",),
        limitations=DRY_RUN_LIMITATIONS,
    )


def _librarian_result(statistical_result: AgentToolResult) -> AgentToolResult:
    return AgentToolResult(
        status=AgentToolStatus.REJECTED,
        role="librarian",
        request_id=REQUEST_ID,
        alpha_spec_id=statistical_result.alpha_spec_id,
        study_spec_id=statistical_result.study_spec_id,
        dataset_version_id=statistical_result.dataset_version_id,
        feature_pack_refs=statistical_result.feature_pack_refs,
        label_pack_refs=statistical_result.label_pack_refs,
        runtime_run_id=statistical_result.runtime_run_id,
        diagnostics_summary=(
            "Librarian proposed rejection and research memory records after verdict."
        ),
        cost_summary=None,
        rejection_reasons=statistical_result.rejection_reasons,
        blocking_findings=(),
        next_required_gate="dry_run_terminal_rejected",
        artifacts=(
            "reviewer_verdict_ref:agent_p22_reject",
            "rejected_idea_memory_ref:agent_p22",
            "research_memory_ref:agent_p22",
        ),
        limitations=DRY_RUN_LIMITATIONS + ("proposed_records_only",),
    )


def _blocked_tool_result(role: str, reason: str, next_gate: str) -> AgentToolResult:
    return AgentToolResult(
        status=AgentToolStatus.BLOCKED,
        role=role,
        request_id=REQUEST_ID,
        alpha_spec_id=ALPHA_SPEC_ID,
        study_spec_id=None,
        dataset_version_id=DATASET_VERSION_ID,
        feature_pack_refs=(FEATURE_PACK_REF,),
        label_pack_refs=(LABEL_PACK_REF,),
        runtime_run_id=None,
        diagnostics_summary="Dry-run input availability check blocked truthfully.",
        cost_summary=None,
        rejection_reasons=(reason,),
        blocking_findings=(reason,),
        next_required_gate=next_gate,
        artifacts=(),
        limitations=DRY_RUN_LIMITATIONS,
    )


def _blocked_report(
    *,
    queue: ResearchQueue,
    task: ResearchTask,
    separation_bundle: SeparationBundle,
    director_result: AgentToolResult,
    scout_result: AgentToolResult,
    scout_handoff: hypothesis_scout.AgentHandoff,
    critic_result: AgentToolResult,
    data_result: AgentToolResult,
    prior_rejection_refs: tuple[hypothesis_scout.RejectionReasonRecordRef, ...],
    extra_results: tuple[AgentToolResult, ...] = (),
) -> AgentDryRunReport:
    librarian_result = _blocked_librarian_result(data_result)
    decision_records = _decision_records(_separation_results(separation_bundle.role_ids))
    run_records = _run_records(
        terminal_state=ResearchTaskStatus.BLOCKED,
        target_statuses={
            role_id: ResearchTaskStatus.BLOCKED for role_id in AGENT_DRY_RUN_ROLE_ROUTE
        },
    )
    rejected_memory = _blocked_rejected_memory(librarian_result)
    research_memory = _research_memory(rejected_memory, (), ())
    report = AgentDryRunReport(
        request_id=REQUEST_ID,
        queue=queue,
        task=task,
        role_route=AGENT_DRY_RUN_ROLE_ROUTE,
        separation_bundle=separation_bundle,
        run_records=run_records,
        decision_records=decision_records,
        tool_results=(
            director_result,
            scout_result,
            critic_result,
            data_result,
            *extra_results,
            librarian_result,
        ),
        tool_invocations=(),
        handoffs=(),
        scout_handoff=scout_handoff,
        prior_rejection_refs=prior_rejection_refs,
        rejected_idea_memory=rejected_memory,
        research_memory=research_memory,
        reachable_task_statuses=(ResearchTaskStatus.DIRECTOR_SCOPED, ResearchTaskStatus.BLOCKED),
        terminal_state=ResearchTaskStatus.BLOCKED,
        max_forward_state=ResearchTaskStatus.DIRECTOR_SCOPED,
    )
    validate_dry_run_report(report)
    return report


def _blocked_librarian_result(blocked_result: AgentToolResult) -> AgentToolResult:
    return AgentToolResult(
        status=AgentToolStatus.BLOCKED,
        role="librarian",
        request_id=REQUEST_ID,
        alpha_spec_id=blocked_result.alpha_spec_id,
        study_spec_id=blocked_result.study_spec_id,
        dataset_version_id=blocked_result.dataset_version_id,
        feature_pack_refs=blocked_result.feature_pack_refs,
        label_pack_refs=blocked_result.label_pack_refs,
        runtime_run_id=blocked_result.runtime_run_id,
        diagnostics_summary="Librarian proposed blocked memory after upstream blocked result.",
        cost_summary=None,
        rejection_reasons=blocked_result.rejection_reasons,
        blocking_findings=blocked_result.blocking_findings,
        next_required_gate="dry_run_terminal_blocked",
        artifacts=("rejected_idea_memory_ref:agent_p22_blocked",),
        limitations=DRY_RUN_LIMITATIONS + ("proposed_records_only",),
    )


def _separation_results(known_role_ids: tuple[str, ...]) -> tuple[SeparationRuleResult, ...]:
    return (
        check_generator_approver_separation(
            "alphaspec_draft",
            "hypothesis_scout",
            "alpha_spec_critic",
            known_role_ids=known_role_ids,
        ),
        check_implementer_reviewer_separation(
            "runtime_evidence",
            "diagnostics_runner",
            "statistical_reviewer",
            known_role_ids=known_role_ids,
        ),
        check_reviewer_assignment_independent(
            "runtime_evidence_review",
            "diagnostics_runner",
            "statistical_reviewer",
            known_role_ids=known_role_ids,
        ),
        check_librarian_verdict_required(
            "librarian",
            "memory_update.proposal_after_verdict",
            REVIEWER_VERDICT_REF,
            known_role_ids=known_role_ids,
        ),
    )


def _run_records(
    *,
    terminal_state: ResearchTaskStatus,
    target_statuses: dict[str, ResearchTaskStatus],
) -> tuple[AgentRunRecord, ...]:
    return tuple(
        AgentRunRecord(
            run_id=f"agent_run:{role_id}",
            role_id=role_id,
            request_id=REQUEST_ID,
            status=AgentRunStatus.COMPLETED,
            queue_ref=QUEUE_ID,
            task_ref=TASK_ID,
            task_status=target_statuses.get(role_id, terminal_state),
            started_at_ref=f"time_ref:{role_id}_started",
            ended_at_ref=f"time_ref:{role_id}_ended",
            summary="Dry-run role step emitted structured refs only.",
            limitations=DRY_RUN_LIMITATIONS,
        )
        for role_id in AGENT_DRY_RUN_ROLE_ROUTE
    )


def _decision_records(
    separation_results: tuple[SeparationRuleResult, ...],
) -> tuple[AgentDecisionRecord, ...]:
    decision_kinds = {
        "research_director": "scope_single_task",
        "hypothesis_scout": "draft_alphaspec_refs",
        "alpha_spec_critic": "critique_drafts",
        "data_contract_auditor": "audit_seed_inputs",
        "feature_engineer": "reference_seed_feature",
        "label_engineer": "reference_seed_label",
        "diagnostics_runner": "request_runtime_bridge",
        "no_lookahead_auditor": "audit_no_lookahead",
        "statistical_reviewer": "reject_dry_run_evidence",
        "librarian": "propose_rejection_memory",
    }
    next_gates = {
        "research_director": "hypothesis_scout_draft",
        "hypothesis_scout": "alpha_spec_critic_independent_review",
        "alpha_spec_critic": "data_contract_auditor_audit_inputs",
        "data_contract_auditor": "feature_label_engineers_reference_seed_inputs",
        "feature_engineer": "label_engineer_reference_seed_input",
        "label_engineer": "diagnostics_runner_request_runtime_bridge",
        "diagnostics_runner": "no_lookahead_auditor_review",
        "no_lookahead_auditor": "statistical_reviewer_independent_review",
        "statistical_reviewer": "librarian_record_independent_review_verdict",
        "librarian": "dry_run_terminal_rejected",
    }
    return tuple(
        AgentDecisionRecord(
            decision_id=f"agent_decision:{decision_kinds[role_id]}",
            run_id=f"agent_run:{role_id}",
            role_id=role_id,
            request_id=REQUEST_ID,
            decision_kind=decision_kinds[role_id],
            classification=AgentDecisionClassification.ALLOWED,
            rationale_summary="Dry-run decision stayed inside the role contract.",
            next_required_gate=next_gates[role_id],
            separation_results=_decision_separation(role_id, separation_results),
        )
        for role_id in AGENT_DRY_RUN_ROLE_ROUTE
    )


def _decision_separation(
    role_id: str,
    separation_results: tuple[SeparationRuleResult, ...],
) -> tuple[SeparationRuleResult, ...]:
    if role_id == "alpha_spec_critic":
        return (separation_results[0],)
    if role_id == "statistical_reviewer":
        return (separation_results[1], separation_results[2])
    if role_id == "librarian":
        return (separation_results[3],)
    return ()


def _tool_invocations(
    *,
    data_result: AgentToolResult,
    feature_result: AgentToolResult,
    label_result: AgentToolResult,
    diagnostics_result: AgentToolResult,
    no_lookahead_result: AgentToolResult,
    statistical_result: AgentToolResult,
    librarian_result: AgentToolResult,
) -> tuple[ToolInvocationRecord, ...]:
    return (
        _invocation(
            invocation_id="tool_invocation:registry_resolve_dataset",
            tool_name="registry.resolve_dataset_version",
            role_id="data_contract_auditor",
            input_refs=(TASK_ID, ALPHA_SPEC_ID, DATASET_VERSION_ID),
            result=data_result,
        ),
        _invocation(
            invocation_id="tool_invocation:feature_request",
            tool_name="feature.request",
            role_id="feature_engineer",
            input_refs=(ALPHA_SPEC_ID, DATASET_VERSION_ID, FEATURE_PACK_REF),
            result=feature_result,
        ),
        _invocation(
            invocation_id="tool_invocation:label_validate_spec",
            tool_name="label.validate_spec",
            role_id="label_engineer",
            input_refs=(STUDY_SPEC_ID, DATASET_VERSION_ID, LABEL_PACK_REF),
            result=label_result,
        ),
        _invocation(
            invocation_id="tool_invocation:runtime_run_diagnostics",
            tool_name="runtime.run_diagnostics",
            role_id="diagnostics_runner",
            input_refs=(ALPHA_SPEC_ID, STUDY_SPEC_ID, DATASET_VERSION_ID),
            result=diagnostics_result,
        ),
        _invocation(
            invocation_id="tool_invocation:review_no_lookahead_audit",
            tool_name="review.no_lookahead_audit",
            role_id="no_lookahead_auditor",
            input_refs=(STUDY_SPEC_ID, LABEL_PACK_REF, RUNTIME_RUN_ID),
            result=no_lookahead_result,
        ),
        _invocation(
            invocation_id="tool_invocation:review_statistical_audit",
            tool_name="review.statistical_audit",
            role_id="statistical_reviewer",
            input_refs=(STUDY_SPEC_ID, RUNTIME_RUN_ID, "evidence_summary:agent_p22_dry_run"),
            result=statistical_result,
        ),
        _invocation(
            invocation_id="tool_invocation:memory_record_rejection",
            tool_name="memory.record_rejection",
            role_id="librarian",
            input_refs=(REVIEWER_VERDICT_REF, ALPHA_SPEC_ID, STUDY_SPEC_ID),
            result=librarian_result,
        ),
    )


def _invocation(
    *,
    invocation_id: str,
    tool_name: str,
    role_id: str,
    input_refs: tuple[str, ...],
    result: AgentToolResult,
) -> ToolInvocationRecord:
    return ToolInvocationRecord(
        invocation_id=invocation_id,
        tool_name=tool_name,
        caller_role_id=role_id,
        request_id=REQUEST_ID,
        started_at_ref=f"time_ref:{role_id}_tool_started",
        ended_at_ref=f"time_ref:{role_id}_tool_ended",
        input_refs=input_refs,
        result=result,
        limitations=DRY_RUN_LIMITATIONS,
    )


def _handoffs(
    decisions: tuple[AgentDecisionRecord, ...],
    invocations: tuple[ToolInvocationRecord, ...],
) -> tuple[AgentHandoff, ...]:
    decision_by_role = {decision.role_id: decision for decision in decisions}
    invocation_by_role = {invocation.caller_role_id: invocation for invocation in invocations}
    return tuple(
        _handoff(
            handoff_id=f"agent_handoff:{from_role_id}_to_{to_role_id or 'terminal'}",
            from_role_id=from_role_id,
            to_role_id=to_role_id,
            decision=decision_by_role[from_role_id],
            invocation=invocation_by_role[from_role_id],
            summary=summary,
        )
        for from_role_id, to_role_id, summary in (
            (
                "data_contract_auditor",
                "feature_engineer",
                "Data contract audit handed one admissible synthetic seed input downstream.",
            ),
            (
                "feature_engineer",
                "label_engineer",
                "Feature engineer handed one synthetic seed FeaturePack ref downstream.",
            ),
            (
                "label_engineer",
                "diagnostics_runner",
                "Label engineer handed one synthetic seed LabelPack and StudySpec ref downstream.",
            ),
            (
                "diagnostics_runner",
                "no_lookahead_auditor",
                "Diagnostics runner handed bridged runtime summaries downstream.",
            ),
            (
                "no_lookahead_auditor",
                "statistical_reviewer",
                "No-lookahead auditor handed a PASS integrity summary downstream.",
            ),
            (
                "statistical_reviewer",
                "librarian",
                "Statistical reviewer handed a REJECT verdict downstream.",
            ),
            (
                "librarian",
                None,
                "Librarian proposed rejection memory and ended the dry run.",
            ),
        )
    )


def _handoff(
    *,
    handoff_id: str,
    from_role_id: str,
    to_role_id: str | None,
    decision: AgentDecisionRecord,
    invocation: ToolInvocationRecord,
    summary: str,
) -> AgentHandoff:
    result = invocation.result
    return AgentHandoff(
        handoff_id=handoff_id,
        from_role_id=from_role_id,
        to_role_id=to_role_id,
        request_id=REQUEST_ID,
        decision=decision,
        tool_invocations=(invocation,),
        alpha_spec_id=result.alpha_spec_id,
        study_spec_id=result.study_spec_id,
        dataset_version_id=result.dataset_version_id,
        feature_pack_refs=result.feature_pack_refs,
        label_pack_refs=result.label_pack_refs,
        runtime_run_id=result.runtime_run_id,
        blocking_findings=result.blocking_findings,
        next_required_gate=result.next_required_gate,
        summary=summary,
        limitations=DRY_RUN_LIMITATIONS,
    )


def _memory_candidate() -> dict[str, object]:
    return {
        "title": "agent p22 synthetic survivor",
        "description": "dry-run rejection recorded after independent review verdict",
        "alpha_spec_id": ALPHA_SPEC_ID,
        "study_spec_id": STUDY_SPEC_ID,
    }


def _rejected_memory(
    statistical_result: AgentToolResult,
    handoffs: tuple[AgentHandoff, ...],
    invocations: tuple[ToolInvocationRecord, ...],
) -> RejectedIdeaMemoryRecord:
    candidate = _memory_candidate()
    return RejectedIdeaMemoryRecord(
        memory_id=f"rejected_idea_memory:{idea_key(candidate).removeprefix('idea:')}",
        idea_key=idea_key(candidate),
        idea_fingerprint=idea_fingerprint(candidate),
        status=RejectedIdeaMemoryStatus.REJECTED,
        alpha_spec_id=ALPHA_SPEC_ID,
        originating_role_id="librarian",
        graveyard_rejected_ids=("rej_agentp22synthetic000001",),
        rejection_reasons=statistical_result.rejection_reasons,
        decision_refs=("agent_decision:reject_dry_run_evidence",),
        handoff_refs=tuple(handoff.handoff_id for handoff in handoffs[-2:]),
        tool_invocation_refs=tuple(invocation.invocation_id for invocation in invocations[-2:]),
        spec_refs=(ALPHA_SPEC_ID, STUDY_SPEC_ID),
        next_required_gate="dry_run_terminal_rejected",
        summary="Visible rejected memory row for the synthetic dry-run idea.",
        limitations=DRY_RUN_LIMITATIONS,
    )


def _blocked_rejected_memory(librarian_result: AgentToolResult) -> RejectedIdeaMemoryRecord:
    candidate = _memory_candidate()
    return RejectedIdeaMemoryRecord(
        memory_id=f"rejected_idea_memory:{idea_key(candidate).removeprefix('idea:')}",
        idea_key=idea_key(candidate),
        idea_fingerprint=idea_fingerprint(candidate),
        status=RejectedIdeaMemoryStatus.BLOCKED,
        alpha_spec_id=ALPHA_SPEC_ID,
        originating_role_id="librarian",
        graveyard_rejected_ids=("rej_agentp22synthetic000001",),
        rejection_reasons=librarian_result.rejection_reasons,
        decision_refs=("agent_decision:propose_rejection_memory",),
        handoff_refs=(),
        tool_invocation_refs=(),
        spec_refs=(ALPHA_SPEC_ID,),
        next_required_gate=librarian_result.next_required_gate,
        summary="Visible blocked memory row for the synthetic dry-run idea.",
        limitations=DRY_RUN_LIMITATIONS,
    )


def _research_memory(
    rejected_memory: RejectedIdeaMemoryRecord,
    handoffs: tuple[AgentHandoff, ...],
    invocations: tuple[ToolInvocationRecord, ...],
) -> ResearchMemoryRecord:
    status = (
        ResearchMemoryStatus.REJECTED
        if rejected_memory.status is RejectedIdeaMemoryStatus.REJECTED
        else ResearchMemoryStatus.BLOCKED
    )
    decision_ref = (
        "agent_decision:reject_dry_run_evidence"
        if status is ResearchMemoryStatus.REJECTED
        else "agent_decision:propose_rejection_memory"
    )
    return ResearchMemoryRecord(
        memory_id="research_memory:agent_p22_dry_run",
        idea_key=rejected_memory.idea_key,
        idea_fingerprint=rejected_memory.idea_fingerprint,
        status=status,
        originating_role_id="librarian",
        prior_outcome_summary="Dry-run outcome recorded; linked memory keeps it visible.",
        decision_refs=(decision_ref,),
        handoff_refs=tuple(handoff.handoff_id for handoff in handoffs[-2:]),
        tool_invocation_refs=tuple(invocation.invocation_id for invocation in invocations[-2:]),
        spec_refs=(ALPHA_SPEC_ID, STUDY_SPEC_ID),
        related_rejected_memory_refs=(rejected_memory.memory_id,),
        next_required_gate=rejected_memory.next_required_gate,
        limitations=DRY_RUN_LIMITATIONS,
    )


__all__ = [
    "AGENT_DRY_RUN_ROLE_ROUTE",
    "DATASET_VERSION_ID",
    "DRY_RUN_FORWARD_STATE_ORDER",
    "DRY_RUN_TERMINAL_STATES",
    "MAX_DRY_RUN_FORWARD_STATE",
    "PERMITTED_STATISTICAL_DRY_RUN_VERDICTS",
    "AgentDryRunReport",
    "DryRunHarnessError",
    "SyntheticDatasetVersion",
    "run_agent_dry_run",
    "synthetic_dataset_version_resolver",
    "validate_dry_run_report",
]
