from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace

import pytest

from alpha_system.agent_factory.queue.models import (
    PROHIBITED_MVP_TASK_STATUSES,
    AgentAssignment,
    BlockerKind,
    BlockerRecord,
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


def test_queue_task_budget_assignment_review_blocker_and_policy_round_trip() -> None:
    task = valid_task(
        assignments=(
            AgentAssignment(
                assignment_id="assignment:director_scope",
                task_id="research_task:seed_scope",
                role_id="research_director",
                assignment_scope_ref="scope:director_declared",
            ),
        )
    )
    queue = valid_queue(tasks=(task,))

    assert queue.queue_id == "queue:synthetic_batch"
    assert queue.max_tasks == 5
    assert queue.ordered_tasks() == (task,)
    assert task.task_status is ResearchTaskStatus.DIRECTOR_SCOPED
    assert task.allowed_alpha_family == ("microstructure_reversion",)
    assert task.allowed_dataset_version_state is DatasetVersionState.VERSIONED
    assert task.allowed_partitions == (
        ResearchPartition.DEVELOPMENT,
        ResearchPartition.VALIDATION,
    )
    assert task.blocked_partitions == (ResearchPartition.LOCKED_TEST_CANDIDATE,)
    assert task.research_budget.variant_budget.max_variants == 2
    assert task.research_budget.compute_budget.max_runtime_minutes == 30
    assert task.review_requirements[0].reviewer_role_id == "alpha_spec_critic"
    assert task.retry_policy.max_attempts == 1
    assert task.blocker is None
    assert task.assignments[0].role_id == "research_director"


def test_research_task_is_immutable() -> None:
    task = valid_task()

    with pytest.raises(FrozenInstanceError):
        task.next_action = "changed"  # type: ignore[misc]


def test_research_task_requires_research_budget_type() -> None:
    with pytest.raises(TypeError):
        replace(valid_task(), research_budget=None)

    with pytest.raises(TypeError):
        replace(valid_task(), research_budget="unlimited")  # type: ignore[arg-type]


@pytest.mark.parametrize("bad_variants", [0, -1, None, 26, "unlimited"])
def test_variant_budget_must_be_finite_positive_and_capped(bad_variants: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        VariantBudget(max_variants=bad_variants)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad_minutes", [0, -1, None, 721, "unlimited"])
def test_compute_budget_must_be_finite_positive_and_capped(bad_minutes: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        ComputeBudget(max_runtime_minutes=bad_minutes)  # type: ignore[arg-type]


def test_research_budget_rejects_absent_budget_parts() -> None:
    with pytest.raises(TypeError):
        ResearchBudget(  # type: ignore[arg-type]
            variant_budget=None,
            compute_budget=ComputeBudget(10),
        )

    with pytest.raises(TypeError):
        ResearchBudget(variant_budget=VariantBudget(1), compute_budget=None)  # type: ignore[arg-type]


def test_contract_surface_is_single_task_bounded() -> None:
    forbidden_fragments = (
        "scheduler",
        "schedule",
        "next_cycle",
        "cycle",
        "auto_enqueue",
        "auto_generate",
        "enqueue_from_results",
        "run_forever",
        "cron",
    )
    classes = (ResearchQueue, ResearchTask, QueuePriorityPolicy)
    public_surface = {
        name
        for contract in classes
        for name in (
            [field.name for field in fields(contract)]
            + [item for item in dir(contract) if not item.startswith("_")]
        )
    }

    assert not any(
        fragment in name for fragment in forbidden_fragments for name in public_surface
    )
    assert "ordered_tasks" in public_surface


@pytest.mark.parametrize("prohibited_status", sorted(PROHIBITED_MVP_TASK_STATUSES))
def test_prohibited_mvp_lifecycle_states_are_rejected(
    prohibited_status: str,
) -> None:
    with pytest.raises(ValueError):
        replace(valid_task(), task_status=prohibited_status)


def test_task_carries_allowed_and_blocked_partitions_and_required_reviews() -> None:
    blocker = BlockerRecord(
        blocker_id="blocker:locked_test_metadata",
        blocker_kind=BlockerKind.LOCKED_TEST_GOVERNANCE_METADATA_REQUIRED,
        blocked_refs=("partition:locked_test_candidate",),
        reason="Locked-test use requires governance contamination metadata.",
        required_resolution="Attach governance contamination metadata before use.",
        next_action="keep_locked_test_blocked",
    )
    task = replace(valid_task(), blocker=blocker)

    assert ResearchPartition.LOCKED_TEST_CANDIDATE in task.blocked_partitions
    assert task.review_requirements == (
        valid_alpha_spec_review(),
        valid_statistical_review(),
    )
    assert task.blocker is blocker


def test_locked_test_allowed_requires_governance_metadata_ref() -> None:
    with pytest.raises(ValueError, match="locked-test"):
        replace(
            valid_task(),
            allowed_partitions=(ResearchPartition.LOCKED_TEST_CANDIDATE,),
            blocked_partitions=(),
            partition_governance_metadata_refs=(),
        )

    task = replace(
        valid_task(),
        allowed_partitions=(ResearchPartition.LOCKED_TEST_CANDIDATE,),
        blocked_partitions=(),
        partition_governance_metadata_refs=("governance_metadata:contamination_audit",),
    )
    assert task.allowed_partitions == (ResearchPartition.LOCKED_TEST_CANDIDATE,)


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    [
        ("allowed_dataset_version_id", "data/raw/es_ticks.parquet"),
        ("allowed_feature_pack_refs", ("feature_pack:seed", "feature_pack:seed")),
        ("allowed_label_pack_refs", ("pandas dataframe payload",)),
        ("next_action", "continuous runner next cycle"),
        ("review_requirements", ["review:mutable"]),
        ("allowed_partitions", ("development", "development")),
        ("assignments", ["assignment:mutable"]),
    ],
)
def test_contracts_reject_raw_heavy_or_unstructured_inputs(
    field_name: str,
    bad_value: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        replace(valid_task(), **{field_name: bad_value})


def test_contracts_reject_bytes_and_dataframe_like_objects() -> None:
    class FakeDataFrame:
        __module__ = "pandas.core.frame"

    with pytest.raises(TypeError):
        replace(valid_task(), allowed_feature_pack_refs=(b"raw-payload",))

    with pytest.raises(TypeError):
        replace(valid_task(), allowed_label_pack_refs=(FakeDataFrame(),))


def test_agent_assignment_binds_role_without_permission_grants() -> None:
    assignment = valid_assignment()
    assignment_fields = {field.name for field in fields(AgentAssignment)}

    assert assignment.role_id == "data_contract_auditor"
    assert assignment_fields == {
        "assignment_id",
        "task_id",
        "role_id",
        "assignment_scope_ref",
    }

    with pytest.raises(ValueError):
        replace(assignment, role_id="unknown_role")


def test_family_budget_policy_caps_per_family_budget_across_queue() -> None:
    task_one = replace(
        valid_task(task_id="research_task:family_one"),
        research_budget=ResearchBudget(VariantBudget(2), ComputeBudget(10)),
    )
    task_two = replace(
        valid_task(task_id="research_task:family_two"),
        research_budget=ResearchBudget(VariantBudget(2), ComputeBudget(10)),
    )

    with pytest.raises(ValueError, match="variant cap"):
        valid_queue(
            tasks=(task_one, task_two),
            family_budget_policy=FamilyBudgetPolicy(
                max_tasks_per_family=3,
                max_variants_per_family=3,
                max_runtime_minutes_per_family=30,
            ),
        )


def test_queue_priority_policy_orders_deterministically() -> None:
    task_low_rank = replace(valid_task(task_id="research_task:low_rank"), priority_rank=2)
    task_high_rank = replace(valid_task(task_id="research_task:high_rank"), priority_rank=1)
    task_tie_a = replace(valid_task(task_id="research_task:a_tie"), priority_rank=3)
    task_tie_b = replace(valid_task(task_id="research_task:b_tie"), priority_rank=3)

    queue = valid_queue(tasks=(task_low_rank, task_tie_b, task_high_rank, task_tie_a))

    assert [task.task_id for task in queue.ordered_tasks()] == [
        "research_task:high_rank",
        "research_task:low_rank",
        "research_task:a_tie",
        "research_task:b_tie",
    ]


def test_research_queue_rejects_unbounded_or_duplicate_tasks() -> None:
    with pytest.raises(ValueError):
        valid_queue(tasks=(valid_task(),), max_tasks=0)

    with pytest.raises(ValueError, match="duplicate"):
        valid_queue(tasks=(valid_task(), valid_task()))


def valid_queue(
    *,
    tasks: tuple[ResearchTask, ...] | None = None,
    family_budget_policy: FamilyBudgetPolicy | None = None,
    max_tasks: int = 5,
) -> ResearchQueue:
    return ResearchQueue(
        queue_id="queue:synthetic_batch",
        tasks=tasks if tasks is not None else (valid_task(),),
        priority_policy=QueuePriorityPolicy(policy_id="priority:director_rank"),
        family_budget_policy=family_budget_policy
        if family_budget_policy is not None
        else FamilyBudgetPolicy(
            max_tasks_per_family=5,
            max_variants_per_family=10,
            max_runtime_minutes_per_family=180,
        ),
        max_tasks=max_tasks,
    )


def valid_task(
    *,
    task_id: str = "research_task:seed_scope",
    assignments: tuple[AgentAssignment, ...] = (),
) -> ResearchTask:
    return ResearchTask(
        task_id=task_id,
        task_status=ResearchTaskStatus.DIRECTOR_SCOPED,
        allowed_alpha_family=("microstructure_reversion",),
        allowed_dataset_version_id="dataset_version:placeholder_seed",
        allowed_dataset_version_state="VERSIONED",
        allowed_feature_pack_refs=("feature_pack:placeholder_seed",),
        allowed_label_pack_refs=("label_pack:placeholder_seed",),
        allowed_partitions=(
            ResearchPartition.DEVELOPMENT,
            ResearchPartition.VALIDATION,
        ),
        blocked_partitions=(ResearchPartition.LOCKED_TEST_CANDIDATE,),
        research_budget=ResearchBudget(
            variant_budget=VariantBudget(max_variants=2),
            compute_budget=ComputeBudget(max_runtime_minutes=30),
        ),
        review_requirements=(
            valid_alpha_spec_review(),
            valid_statistical_review(),
        ),
        retry_policy=RetryPolicy(
            max_attempts=1,
            retry_on_statuses=(ResearchTaskStatus.INCONCLUSIVE,),
        ),
        next_action="alpha_spec_critique",
        assignments=assignments,
    )


def valid_alpha_spec_review() -> ReviewRequirement:
    return ReviewRequirement(
        review_id="review:alpha_spec_critique",
        review_kind="alphaspec_critique",
        reviewer_role_id="alpha_spec_critic",
        independent_from_role_ids=("hypothesis_scout", "research_director"),
        required_before_status=ResearchTaskStatus.ALPHASPEC_CRITIQUED,
    )


def valid_statistical_review() -> ReviewRequirement:
    return ReviewRequirement(
        review_id="review:statistical_evidence",
        review_kind="runtime_evidence_review",
        reviewer_role_id="statistical_reviewer",
        independent_from_role_ids=("diagnostics_runner", "feature_engineer"),
        required_before_status=ResearchTaskStatus.STATISTICAL_REVIEW_INCONCLUSIVE,
    )


def valid_assignment() -> AgentAssignment:
    return AgentAssignment(
        assignment_id="assignment:data_contract_audit",
        task_id="research_task:seed_scope",
        role_id="data_contract_auditor",
        assignment_scope_ref="scope:input_refs_only",
    )
