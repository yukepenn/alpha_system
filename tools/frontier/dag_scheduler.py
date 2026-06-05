"""Provider-neutral DAG wave scheduler for Frontier Workflow 2.

This module is the scheduling *brain* for Workflow 2. It is intentionally pure:
it imports only the standard library, performs no I/O, mutates no global state,
and never touches git, GitHub, providers, or the network. It can be unit tested
in isolation and re-used by both the read-only ``plan-dag`` command and the live
Ralph driver.

Responsibilities:

- Build a phase dependency graph and reject cycles, unknown dependencies,
  self-dependencies, and unknown/self conflicts.
- Compute the dependency-satisfied *ready set* (phases whose dependencies have
  all passed and that are still ``PENDING``).
- Partition phases into ordered *waves* where every phase in a wave is
  dependency-satisfied, parallel-safe, mutually non-conflicting, and within an
  optional ``max_parallel`` width.
- Decide, conservatively, whether two phases may run in the same parallel wave
  (declared ``conflicts_with``, ``must_run_alone``, overlapping ``allowed_paths``,
  shared exclusive ``resource_class``, RED lane, and global/coordinator files
  such as ``ACTIVE_CAMPAIGN.md``).

The default policy is conservative: when in doubt, a phase is *not* parallel-safe
and runs alone in its own wave. Sequential behaviour is always a valid plan.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

# Phase statuses that count as "done and passing" for dependency satisfaction.
PASSING_STATUSES: frozenset[str] = frozenset({"PASS", "PASS_WITH_WARNINGS"})

# Lanes that may never be parallelised unless RED scope is explicitly armed.
NON_PARALLEL_LANES: frozenset[str] = frozenset({"red"})

# Files that are global/coordinator-owned: a phase that writes any of these
# cannot share a parallel wave because concurrent branches would race on them.
# ``ACTIVE_CAMPAIGN.md`` is special-cased everywhere (coordinator-only writes),
# but is also listed here so a phase that *declares* it as an allowed path is
# forced to run alone.
DEFAULT_GLOBAL_FILES: frozenset[str] = frozenset(
    {
        "ACTIVE_CAMPAIGN.md",
        "frontier.yaml",
        "campaign.yaml",
        "pyproject.toml",
        "AGENTS.md",
        "CLAUDE.md",
        "README.md",
        "justfile",
        "PROJECT_STATUS.md",
        "PROGRESS.md",
        "CHANGELOG.md",
    }
)

_GLOB_CHARS = set("*?[]")


class SchedulerError(ValueError):
    """Raised when a campaign graph is structurally invalid (cycle, unknown dep)."""


@dataclass(frozen=True)
class SchedulerPhase:
    """Normalized, scheduler-facing view of a single phase.

    Built from either a campaign ``LedgerPhase`` or a run-state phase mapping so
    the same logic serves the read-only planner and the live driver.
    """

    phase_id: str
    status: str = "PENDING"
    lane: str = "green"
    dependencies: tuple[str, ...] = ()
    parallel_safe: bool = False
    allowed_paths: tuple[str, ...] = ()
    forbidden_paths: tuple[str, ...] = ()
    conflicts_with: tuple[str, ...] = ()
    resource_class: tuple[str, ...] = ()
    must_run_alone: bool = False
    merge_group: str | None = None
    name: str | None = None

    @property
    def is_pending(self) -> bool:
        return self.status == "PENDING"

    @property
    def is_passing(self) -> bool:
        return self.status in PASSING_STATUSES


def _clean_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _as_str_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)):
        single = _clean_str(value)
        return (single,) if single else ()
    if isinstance(value, Iterable):
        items: list[str] = []
        for item in value:
            cleaned = _clean_str(item)
            if cleaned:
                items.append(cleaned)
        return tuple(items)
    cleaned = _clean_str(value)
    return (cleaned,) if cleaned else ()


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return default


def phase_from_mapping(data: Mapping[str, Any]) -> SchedulerPhase:
    """Build a :class:`SchedulerPhase` from a run-state phase dict."""

    phase_id = _clean_str(data.get("phase_id") or data.get("id"))
    if not phase_id:
        raise SchedulerError("Phase mapping is missing a phase_id.")
    lane = (_clean_str(data.get("lane")) or "green").lower()
    return SchedulerPhase(
        phase_id=phase_id,
        status=_clean_str(data.get("status")) or "PENDING",
        lane=lane,
        dependencies=_as_str_tuple(data.get("dependencies") or data.get("depends_on")),
        parallel_safe=_as_bool(data.get("parallel_safe"), default=False),
        allowed_paths=_as_str_tuple(data.get("allowed_paths")),
        forbidden_paths=_as_str_tuple(data.get("forbidden_paths")),
        conflicts_with=_as_str_tuple(data.get("conflicts_with")),
        resource_class=_as_str_tuple(data.get("resource_class")),
        must_run_alone=_as_bool(data.get("must_run_alone"), default=False),
        merge_group=_clean_str(data.get("merge_group")),
        name=_clean_str(data.get("name") or data.get("title")),
    )


def phase_from_ledger(phase: Any) -> SchedulerPhase:
    """Build a :class:`SchedulerPhase` from a campaign ``LedgerPhase`` dataclass.

    Reads attributes defensively so callers do not need the new optional fields
    to exist on older ``LedgerPhase`` definitions.
    """

    lane = (_clean_str(getattr(phase, "lane", None)) or "green").lower()
    return SchedulerPhase(
        phase_id=str(getattr(phase, "phase_id")),
        status="PENDING",
        lane=lane,
        dependencies=tuple(getattr(phase, "dependencies", ()) or ()),
        parallel_safe=_as_bool(getattr(phase, "parallel_safe", False), default=False),
        allowed_paths=tuple(getattr(phase, "allowed_paths", ()) or ()),
        forbidden_paths=tuple(getattr(phase, "forbidden_paths", ()) or ()),
        conflicts_with=tuple(getattr(phase, "conflicts_with", ()) or ()),
        resource_class=tuple(getattr(phase, "resource_class", ()) or ()),
        must_run_alone=_as_bool(getattr(phase, "must_run_alone", False), default=False),
        merge_group=_clean_str(getattr(phase, "merge_group", None)),
        name=_clean_str(getattr(phase, "name", None)),
    )


def normalize_phases(phases: Sequence[Any]) -> list[SchedulerPhase]:
    """Coerce a sequence of LedgerPhase / mappings / SchedulerPhase into a list."""

    result: list[SchedulerPhase] = []
    for phase in phases:
        if isinstance(phase, SchedulerPhase):
            result.append(phase)
        elif isinstance(phase, Mapping):
            result.append(phase_from_mapping(phase))
        else:
            result.append(phase_from_ledger(phase))
    return result


def validate_graph(phases: Sequence[SchedulerPhase]) -> None:
    """Validate the dependency/conflict graph; raise :class:`SchedulerError`.

    Checks: unique ids, known dependencies, no self-dependency, known
    ``conflicts_with`` targets, no self-conflict, and acyclic dependencies.
    """

    ids = [phase.phase_id for phase in phases]
    seen: set[str] = set()
    for phase_id in ids:
        if phase_id in seen:
            raise SchedulerError(f"Duplicate phase id in graph: {phase_id}.")
        seen.add(phase_id)
    id_set = set(ids)

    for phase in phases:
        unknown = [dep for dep in phase.dependencies if dep not in id_set]
        if unknown:
            raise SchedulerError(
                f"Phase {phase.phase_id} has unknown dependencies: {', '.join(unknown)}."
            )
        if phase.phase_id in phase.dependencies:
            raise SchedulerError(f"Phase {phase.phase_id} depends on itself.")
        unknown_conflicts = [c for c in phase.conflicts_with if c not in id_set]
        if unknown_conflicts:
            raise SchedulerError(
                f"Phase {phase.phase_id} declares unknown conflicts_with: "
                f"{', '.join(unknown_conflicts)}."
            )
        if phase.phase_id in phase.conflicts_with:
            raise SchedulerError(f"Phase {phase.phase_id} conflicts with itself.")

    cycle = _find_cycle(phases)
    if cycle:
        raise SchedulerError("Dependency cycle detected: " + " -> ".join(cycle))


def _find_cycle(phases: Sequence[SchedulerPhase]) -> list[str] | None:
    graph = {phase.phase_id: list(phase.dependencies) for phase in phases}
    # 0 = unvisited, 1 = on stack, 2 = done
    color: dict[str, int] = {pid: 0 for pid in graph}
    stack: list[str] = []

    def visit(node: str) -> list[str] | None:
        color[node] = 1
        stack.append(node)
        for dep in graph.get(node, ()):  # dep must complete before node
            if dep not in color:
                continue
            if color[dep] == 1:
                # Found a back edge; slice the stack to report the cycle.
                idx = stack.index(dep)
                return stack[idx:] + [dep]
            if color[dep] == 0:
                found = visit(dep)
                if found:
                    return found
        stack.pop()
        color[node] = 2
        return None

    for pid in graph:
        if color[pid] == 0:
            found = visit(pid)
            if found:
                return found
    return None


def dependencies_satisfied(
    phase: SchedulerPhase,
    by_id: Mapping[str, SchedulerPhase],
    *,
    satisfied_ids: set[str] | None = None,
) -> bool:
    """True when every dependency has passed (or is in ``satisfied_ids``)."""

    for dep in phase.dependencies:
        if satisfied_ids is not None and dep in satisfied_ids:
            continue
        dep_phase = by_id.get(dep)
        if dep_phase is None or not dep_phase.is_passing:
            return False
    return True


def ready_phases(phases: Sequence[Any]) -> list[SchedulerPhase]:
    """Return PENDING phases whose dependencies have all passed, in order."""

    normalized = normalize_phases(phases)
    by_id = {phase.phase_id: phase for phase in normalized}
    return [
        phase
        for phase in normalized
        if phase.is_pending and dependencies_satisfied(phase, by_id)
    ]


def next_ready_phase(phases: Sequence[Any]) -> SchedulerPhase | None:
    """First dependency-satisfied PENDING phase in declaration order, or None."""

    ready = ready_phases(phases)
    return ready[0] if ready else None


def _scope_prefix(pattern: str) -> str:
    """Reduce a glob path pattern to its concrete leading directory/file prefix.

    ``src/alpha/features/**`` -> ``src/alpha/features``;
    ``docs/x.md`` -> ``docs/x.md``; ``**`` or ``*`` or ``""`` -> ``""`` (repo root).
    """

    text = pattern.strip().strip("/")
    if not text:
        return ""
    parts: list[str] = []
    for segment in text.split("/"):
        if any(ch in segment for ch in _GLOB_CHARS):
            break
        parts.append(segment)
    return "/".join(parts)


def _prefixes_overlap(a: str, b: str) -> bool:
    if a == b:
        return True
    if a == "" or b == "":
        # One pattern covers the whole repo (or an unbounded glob): conservative.
        return True
    return a.startswith(b + "/") or b.startswith(a + "/")


def _phase_prefixes(phase: SchedulerPhase) -> list[str]:
    return [_scope_prefix(p) for p in phase.allowed_paths]


def paths_overlap(a: SchedulerPhase, b: SchedulerPhase) -> bool:
    """Conservative overlap test between two phases' declared allowed paths."""

    prefixes_a = _phase_prefixes(a)
    prefixes_b = _phase_prefixes(b)
    if not prefixes_a or not prefixes_b:
        # A phase with no declared allowed_paths cannot be proven disjoint.
        return True
    return any(_prefixes_overlap(pa, pb) for pa in prefixes_a for pb in prefixes_b)


def touches_global_file(
    phase: SchedulerPhase,
    *,
    global_files: frozenset[str] = DEFAULT_GLOBAL_FILES,
) -> str | None:
    """Return the first global/coordinator file a phase declares, or None."""

    for pattern in phase.allowed_paths:
        prefix = _scope_prefix(pattern)
        if prefix == "":
            return pattern or "<repo-root>"
        head = prefix.split("/", 1)[0]
        if prefix in global_files or head in global_files or pattern in global_files:
            return prefix
    return None


def phase_parallel_safety(
    phase: SchedulerPhase,
    *,
    red_authorized: bool = False,
    global_files: frozenset[str] = DEFAULT_GLOBAL_FILES,
) -> tuple[bool, str | None]:
    """Whether a phase may *ever* share a parallel wave, with a reason if not."""

    if phase.must_run_alone:
        return False, "declared must_run_alone"
    if not phase.parallel_safe:
        return False, "parallel_safe is not set (default conservative)"
    if not phase.allowed_paths:
        return False, "no allowed_paths declared; cannot prove path isolation"
    if phase.lane in NON_PARALLEL_LANES and not red_authorized:
        return False, f"{phase.lane.upper()} lane requires explicit authorization to parallelize"
    global_hit = touches_global_file(phase, global_files=global_files)
    if global_hit is not None:
        return False, f"declares global/coordinator path {global_hit}; must run alone"
    return True, None


def phases_conflict(
    a: SchedulerPhase,
    b: SchedulerPhase,
) -> tuple[bool, str | None]:
    """Whether two (already parallel-safe) phases may co-run, with a reason."""

    if a.phase_id == b.phase_id:
        return True, "same phase"
    if b.phase_id in a.conflicts_with or a.phase_id in b.conflicts_with:
        return True, "declared conflicts_with"
    shared_resources = set(a.resource_class) & set(b.resource_class)
    if shared_resources:
        return True, f"shared resource_class {sorted(shared_resources)}"
    if paths_overlap(a, b):
        return True, "overlapping allowed_paths"
    return False, None


@dataclass(frozen=True)
class Wave:
    """One ordered execution wave."""

    index: int
    phase_ids: tuple[str, ...]

    @property
    def parallel(self) -> bool:
        return len(self.phase_ids) > 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "phase_ids": list(self.phase_ids),
            "parallel": self.parallel,
            "width": len(self.phase_ids),
        }


@dataclass(frozen=True)
class CampaignPlan:
    """A full, serializable wave plan for a campaign run."""

    waves: tuple[Wave, ...]
    unsafe: tuple[tuple[str, str], ...] = ()  # (phase_id, reason)
    conflicts: tuple[tuple[str, str, str], ...] = ()  # (a, b, reason)
    blocked: tuple[tuple[str, str], ...] = ()  # (phase_id, reason)
    edges: tuple[tuple[str, str], ...] = ()  # (dependency, phase)
    max_parallel: int | None = None
    notes: tuple[str, ...] = ()

    @property
    def max_width(self) -> int:
        return max((len(w.phase_ids) for w in self.waves), default=0)

    @property
    def has_parallel(self) -> bool:
        return any(w.parallel for w in self.waves)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "frontier-dag-plan-v1",
            "max_parallel": self.max_parallel,
            "max_width": self.max_width,
            "has_parallel": self.has_parallel,
            "wave_count": len(self.waves),
            "waves": [w.to_dict() for w in self.waves],
            "unsafe": [{"phase_id": p, "reason": r} for p, r in self.unsafe],
            "conflicts": [
                {"a": a, "b": b, "reason": r} for a, b, r in self.conflicts
            ],
            "blocked": [{"phase_id": p, "reason": r} for p, r in self.blocked],
            "edges": [{"dependency": d, "phase": p} for d, p in self.edges],
            "notes": list(self.notes),
        }


def compute_waves(
    phases: Sequence[Any],
    *,
    max_parallel: int | None = None,
    red_authorized: bool = False,
    global_files: frozenset[str] = DEFAULT_GLOBAL_FILES,
) -> CampaignPlan:
    """Partition PENDING phases into dependency-respecting, conflict-free waves.

    Already-passing phases are treated as satisfied prerequisites. Phases that
    are not parallel-safe (or that conflict with already-packed members) run in
    their own single-phase wave. ``max_parallel`` bounds each wave's width
    (``None`` means unbounded). Dependents of a non-passing, non-pending phase
    (e.g. ``BLOCKED``) are surfaced under ``blocked`` and not scheduled.
    """

    normalized = normalize_phases(phases)
    validate_graph(normalized)
    by_id = {phase.phase_id: phase for phase in normalized}

    if max_parallel is not None and max_parallel < 1:
        raise SchedulerError("max_parallel must be >= 1 when provided.")

    satisfied: set[str] = {p.phase_id for p in normalized if p.is_passing}
    pending = [p for p in normalized if p.is_pending]
    remaining = {p.phase_id for p in pending}

    edges = tuple(
        (dep, p.phase_id) for p in normalized for dep in p.dependencies
    )

    unsafe: list[tuple[str, str]] = []
    safety_cache: dict[str, tuple[bool, str | None]] = {}
    for p in pending:
        safe, reason = phase_parallel_safety(
            p, red_authorized=red_authorized, global_files=global_files
        )
        safety_cache[p.phase_id] = (safe, reason)
        if not safe and reason:
            unsafe.append((p.phase_id, reason))

    waves: list[Wave] = []
    conflicts_found: list[tuple[str, str, str]] = []
    blocked: list[tuple[str, str]] = []
    wave_index = 0
    guard = 0
    guard_limit = len(pending) + 5

    while remaining:
        guard += 1
        if guard > guard_limit:
            # Defensive: validate_graph already rejects cycles, so this only
            # triggers if every remaining phase is blocked by a non-passing dep.
            break

        ready = [
            by_id[pid]
            for pid in (p.phase_id for p in pending)
            if pid in remaining
            and dependencies_satisfied(by_id[pid], by_id, satisfied_ids=satisfied)
        ]
        if not ready:
            for pid in sorted(remaining):
                blocker = _first_unmet_dependency(by_id[pid], by_id, satisfied)
                detail = (
                    f"dependency {blocker} has not passed"
                    if blocker
                    else "unsatisfiable dependencies"
                )
                blocked.append((pid, detail))
            break

        wave_members: list[SchedulerPhase] = []
        for candidate in ready:
            safe, _reason = safety_cache.get(candidate.phase_id, (False, None))
            if not wave_members:
                wave_members.append(candidate)
                if not safe:
                    # Not parallel-safe: it gets a wave to itself.
                    break
                continue
            if not safe:
                continue
            conflict = False
            for member in wave_members:
                clash, why = phases_conflict(candidate, member)
                if clash:
                    conflicts_found.append((candidate.phase_id, member.phase_id, why or "conflict"))
                    conflict = True
                    break
            if conflict:
                continue
            wave_members.append(candidate)
            if max_parallel is not None and len(wave_members) >= max_parallel:
                break

        member_ids = tuple(p.phase_id for p in wave_members)
        waves.append(Wave(index=wave_index, phase_ids=member_ids))
        wave_index += 1
        for pid in member_ids:
            remaining.discard(pid)
            satisfied.add(pid)  # treat as will-pass for downstream planning

    # Deduplicate conflict records (a,b) vs (b,a).
    seen_conflicts: set[frozenset[str]] = set()
    unique_conflicts: list[tuple[str, str, str]] = []
    for a, b, why in conflicts_found:
        key = frozenset({a, b})
        if key in seen_conflicts:
            continue
        seen_conflicts.add(key)
        unique_conflicts.append((a, b, why))

    return CampaignPlan(
        waves=tuple(waves),
        unsafe=tuple(unsafe),
        conflicts=tuple(unique_conflicts),
        blocked=tuple(blocked),
        edges=edges,
        max_parallel=max_parallel,
    )


def _first_unmet_dependency(
    phase: SchedulerPhase,
    by_id: Mapping[str, SchedulerPhase],
    satisfied: set[str],
) -> str | None:
    for dep in phase.dependencies:
        if dep in satisfied:
            continue
        dep_phase = by_id.get(dep)
        if dep_phase is None or not dep_phase.is_passing:
            return dep
    return None


def plan_campaign(
    phases: Sequence[Any],
    *,
    max_parallel: int | None = None,
    red_authorized: bool = False,
    global_files: frozenset[str] = DEFAULT_GLOBAL_FILES,
) -> CampaignPlan:
    """Public entry point: validate the graph and compute the full wave plan."""

    return compute_waves(
        phases,
        max_parallel=max_parallel,
        red_authorized=red_authorized,
        global_files=global_files,
    )
