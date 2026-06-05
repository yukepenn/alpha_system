from __future__ import annotations

import pytest

from tools.frontier.dag_scheduler import (
    SchedulerError,
    SchedulerPhase,
    compute_waves,
    next_ready_phase,
    paths_overlap,
    phase_parallel_safety,
    phases_conflict,
    plan_campaign,
    ready_phases,
    validate_graph,
)


def phase(
    phase_id: str,
    *,
    status: str = "PENDING",
    lane: str = "green",
    dependencies: tuple[str, ...] = (),
    parallel_safe: bool = False,
    allowed_paths: tuple[str, ...] = (),
    conflicts_with: tuple[str, ...] = (),
    resource_class: tuple[str, ...] = (),
    must_run_alone: bool = False,
    merge_group: str | None = None,
) -> SchedulerPhase:
    return SchedulerPhase(
        phase_id=phase_id,
        status=status,
        lane=lane,
        dependencies=dependencies,
        parallel_safe=parallel_safe,
        allowed_paths=allowed_paths,
        conflicts_with=conflicts_with,
        resource_class=resource_class,
        must_run_alone=must_run_alone,
        merge_group=merge_group,
    )


def safe(phase_id: str, prefix: str, **kw) -> SchedulerPhase:
    return phase(phase_id, parallel_safe=True, allowed_paths=(f"{prefix}/**",), **kw)


# --- graph validation -------------------------------------------------------


def test_validate_graph_accepts_acyclic() -> None:
    validate_graph([phase("A"), phase("B", dependencies=("A",))])


def test_unknown_dependency_raises() -> None:
    with pytest.raises(SchedulerError, match="unknown dependencies"):
        validate_graph([phase("A", dependencies=("Z",))])


def test_self_dependency_raises() -> None:
    with pytest.raises(SchedulerError, match="depends on itself"):
        validate_graph([phase("A", dependencies=("A",))])


def test_cycle_detected() -> None:
    with pytest.raises(SchedulerError, match="cycle"):
        validate_graph(
            [
                phase("A", dependencies=("C",)),
                phase("B", dependencies=("A",)),
                phase("C", dependencies=("B",)),
            ]
        )


def test_unknown_conflict_raises() -> None:
    with pytest.raises(SchedulerError, match="unknown conflicts_with"):
        validate_graph([phase("A", conflicts_with=("Z",))])


def test_duplicate_id_raises() -> None:
    with pytest.raises(SchedulerError, match="Duplicate phase id"):
        validate_graph([phase("A"), phase("A")])


# --- ready set --------------------------------------------------------------


def test_ready_set_requires_passed_dependencies() -> None:
    phases = [
        phase("A", status="PASS"),
        phase("B", dependencies=("A",)),
        phase("C", dependencies=("B",)),
    ]
    ready = [p.phase_id for p in ready_phases(phases)]
    assert ready == ["B"]  # C blocked because B not passed; A already done


def test_ready_set_empty_when_dependency_blocked() -> None:
    phases = [phase("A", status="BLOCKED"), phase("B", dependencies=("A",))]
    assert ready_phases(phases) == []


def test_next_ready_phase_declaration_order() -> None:
    phases = [phase("A"), phase("B")]
    assert next_ready_phase(phases).phase_id == "A"


def test_pass_with_warnings_satisfies_dependency() -> None:
    phases = [phase("A", status="PASS_WITH_WARNINGS"), phase("B", dependencies=("A",))]
    assert [p.phase_id for p in ready_phases(phases)] == ["B"]


# --- parallel safety --------------------------------------------------------


def test_missing_allowed_paths_blocks_parallel() -> None:
    ok, reason = phase_parallel_safety(phase("A", parallel_safe=True))
    assert not ok
    assert "allowed_paths" in reason


def test_parallel_safe_default_false() -> None:
    ok, reason = phase_parallel_safety(phase("A", allowed_paths=("src/x/**",)))
    assert not ok
    assert "parallel_safe" in reason


def test_must_run_alone_blocks_parallel() -> None:
    ok, reason = phase_parallel_safety(safe("A", "src/x", must_run_alone=True))
    assert not ok
    assert "must_run_alone" in reason


def test_red_lane_not_parallel_by_default() -> None:
    ok, reason = phase_parallel_safety(safe("A", "src/x", lane="red"))
    assert not ok
    assert "RED" in reason
    ok2, _ = phase_parallel_safety(safe("A", "src/x", lane="red"), red_authorized=True)
    assert ok2


def test_active_campaign_path_forces_run_alone() -> None:
    p = phase("A", parallel_safe=True, allowed_paths=("ACTIVE_CAMPAIGN.md",))
    ok, reason = phase_parallel_safety(p)
    assert not ok
    assert "ACTIVE_CAMPAIGN.md" in reason


def test_repo_root_path_forces_run_alone() -> None:
    p = phase("A", parallel_safe=True, allowed_paths=("**",))
    ok, reason = phase_parallel_safety(p)
    assert not ok


# --- conflict detection -----------------------------------------------------


def test_paths_overlap_directory_containment() -> None:
    a = safe("A", "src/alpha/features")
    b = phase("B", parallel_safe=True, allowed_paths=("src/alpha/**",))
    assert paths_overlap(a, b)


def test_disjoint_paths_do_not_overlap() -> None:
    a = safe("A", "src/alpha/features/base")
    b = safe("B", "src/alpha/features/bbo")
    assert not paths_overlap(a, b)


def test_declared_conflicts_block_same_wave() -> None:
    a = safe("A", "src/x", conflicts_with=("B",))
    b = safe("B", "src/y")
    clash, why = phases_conflict(a, b)
    assert clash
    assert "conflicts_with" in why


def test_shared_resource_class_conflicts() -> None:
    a = safe("A", "src/x", resource_class=("databento_live",))
    b = safe("B", "src/y", resource_class=("databento_live",))
    clash, why = phases_conflict(a, b)
    assert clash
    assert "resource_class" in why


# --- wave computation -------------------------------------------------------


def test_disjoint_phases_share_a_wave() -> None:
    phases = [
        safe("ROOT", "src/core", status="PASS"),
        safe("A", "src/features/base", dependencies=("ROOT",)),
        safe("B", "src/features/bbo", dependencies=("ROOT",)),
        safe("C", "src/features/session", dependencies=("ROOT",)),
    ]
    plan = compute_waves(phases)
    assert len(plan.waves) == 1
    assert set(plan.waves[0].phase_ids) == {"A", "B", "C"}
    assert plan.waves[0].parallel


def test_overlapping_paths_split_into_separate_waves() -> None:
    phases = [
        safe("A", "src/features"),
        phase("B", parallel_safe=True, allowed_paths=("src/features/base/**",)),
    ]
    plan = compute_waves(phases)
    # A and B overlap -> cannot share a wave.
    assert len(plan.waves) == 2
    assert any(c for c in plan.conflicts)


def test_max_parallel_caps_wave_width() -> None:
    phases = [
        safe("A", "src/a"),
        safe("B", "src/b"),
        safe("C", "src/c"),
    ]
    plan = compute_waves(phases, max_parallel=2)
    assert plan.max_width == 2
    assert sum(len(w.phase_ids) for w in plan.waves) == 3


def test_non_parallel_safe_phase_runs_alone() -> None:
    phases = [
        phase("BOOT"),  # not parallel_safe -> own wave
        safe("A", "src/a", dependencies=("BOOT",)),
        safe("B", "src/b", dependencies=("BOOT",)),
    ]
    plan = compute_waves(phases)
    assert plan.waves[0].phase_ids == ("BOOT",)
    assert set(plan.waves[1].phase_ids) == {"A", "B"}


def test_dependencies_respected_across_waves() -> None:
    phases = [
        safe("A", "src/a"),
        safe("B", "src/b", dependencies=("A",)),
    ]
    plan = compute_waves(phases)
    assert plan.waves[0].phase_ids == ("A",)
    assert plan.waves[1].phase_ids == ("B",)


def test_blocked_dependency_surfaces_blocked() -> None:
    phases = [
        phase("A", status="BLOCKED"),
        safe("B", "src/b", dependencies=("A",)),
    ]
    plan = compute_waves(phases)
    assert plan.waves == ()
    assert any(pid == "B" for pid, _ in plan.blocked)


def test_must_run_alone_separates_even_when_disjoint() -> None:
    phases = [
        safe("A", "src/a", must_run_alone=True),
        safe("B", "src/b"),
    ]
    plan = compute_waves(phases)
    # A must run alone; B is parallel-safe but ends up in its own wave too.
    assert ("A",) in [w.phase_ids for w in plan.waves]


def test_plan_is_serializable() -> None:
    plan = plan_campaign([safe("A", "src/a"), safe("B", "src/b")])
    data = plan.to_dict()
    assert data["schema_version"] == "frontier-dag-plan-v1"
    assert data["wave_count"] == len(plan.waves)
    assert isinstance(data["waves"], list)


def test_invalid_max_parallel_rejected() -> None:
    with pytest.raises(SchedulerError):
        compute_waves([phase("A")], max_parallel=0)


def test_mapping_inputs_supported() -> None:
    phases = [
        {"phase_id": "A", "status": "PASS"},
        {"phase_id": "B", "dependencies": ["A"]},
    ]
    assert [p.phase_id for p in ready_phases(phases)] == ["B"]


def test_full_sequential_plan_when_nothing_parallel_safe() -> None:
    phases = [phase("A"), phase("B", dependencies=("A",)), phase("C", dependencies=("B",))]
    plan = compute_waves(phases)
    assert [w.phase_ids for w in plan.waves] == [("A",), ("B",), ("C",)]
    assert not plan.has_parallel
