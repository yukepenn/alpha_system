from __future__ import annotations

from tools.frontier.dag_scheduler import SchedulerPhase
from tools.frontier.merge_queue import (
    MERGE_READY,
    mergeable_candidates,
    next_to_merge,
    serial_merge_order,
)


def ready(phase_id: str, *, dependencies=(), merge_group=None) -> SchedulerPhase:
    return SchedulerPhase(
        phase_id=phase_id,
        status=MERGE_READY,
        dependencies=tuple(dependencies),
        merge_group=merge_group,
    )


def test_mergeable_candidates_filters_status() -> None:
    phases = [
        SchedulerPhase(phase_id="A", status="PASS"),
        ready("B"),
        SchedulerPhase(phase_id="C", status="PENDING"),
    ]
    assert [p.phase_id for p in mergeable_candidates(phases)] == ["B"]


def test_serial_order_preserves_input_order() -> None:
    order = serial_merge_order([ready("A"), ready("B"), ready("C")])
    assert order == ["A", "B", "C"]


def test_dependencies_merge_before_dependents() -> None:
    order = serial_merge_order(
        [ready("B", dependencies=("A",)), ready("A")]
    )
    assert order.index("A") < order.index("B")


def test_merge_group_kept_adjacent() -> None:
    order = serial_merge_order(
        [
            ready("A", merge_group="features"),
            ready("X"),
            ready("B", merge_group="features"),
        ]
    )
    # A and B share a group: B should follow A without X in between.
    assert order.index("B") == order.index("A") + 1


def test_external_dependency_does_not_block() -> None:
    # Dependency D is not in the candidate set (already merged earlier).
    order = serial_merge_order([ready("B", dependencies=("D",))])
    assert order == ["B"]


def test_completed_ids_satisfy_dependencies() -> None:
    order = serial_merge_order(
        [ready("B", dependencies=("A",))], completed_ids=("A",)
    )
    assert order == ["B"]


def test_next_to_merge_returns_head() -> None:
    assert next_to_merge([ready("A"), ready("B")]) == "A"
    assert next_to_merge([]) is None


def test_cycle_within_candidates_still_makes_progress() -> None:
    order = serial_merge_order(
        [ready("A", dependencies=("B",)), ready("B", dependencies=("A",))]
    )
    assert set(order) == {"A", "B"}
