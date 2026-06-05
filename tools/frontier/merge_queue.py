"""Serial merge-queue ordering for Frontier Workflow 2 parallel waves.

Phases may *build* (spec -> execute -> validate -> review -> done-check -> commit
-> push -> PR -> CI) in parallel inside isolated worktrees, but they must *merge*
to the protected default branch one at a time. This module computes the
deterministic serial order in which build-complete phases should be merged.

It is pure (standard library only, no git/GitHub/network) so the ordering policy
can be unit tested in isolation. The actual ``gh pr merge`` execution, gate
re-evaluation against the moving base, and worktree cleanup remain in the driver
and ``merge_gate``/``github_utils`` layers.

Ordering policy (deterministic):

1. A phase never merges before a dependency that is also waiting in the queue.
2. Phases sharing a ``merge_group`` are kept adjacent when dependencies allow it,
   so a logical group lands as a contiguous block.
3. Declaration/input order is the stable tiebreaker.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from tools.frontier.dag_scheduler import SchedulerPhase, normalize_phases

# Status set by the parallel coordinator when a phase has built + passed CI and
# its merge gate is ready to be evaluated, but the actual merge is deferred to
# the serial queue. Importable by the driver so both layers agree on the string.
MERGE_READY: str = "MERGE_READY"

# Statuses that mean "this phase still needs to be merged by the queue".
MERGEABLE_STATUSES: frozenset[str] = frozenset({MERGE_READY})


def mergeable_candidates(phases: Sequence[Any]) -> list[SchedulerPhase]:
    """Return the phases currently waiting to merge (status MERGE_READY)."""

    return [p for p in normalize_phases(phases) if p.status in MERGEABLE_STATUSES]


def serial_merge_order(
    candidates: Sequence[Any],
    *,
    completed_ids: Sequence[str] = (),
) -> list[str]:
    """Compute the serial merge order for ``candidates``.

    ``candidates`` are the build-complete phases to merge (any phase objects /
    mappings accepted). ``completed_ids`` are phases already merged this run;
    their ids are treated as satisfied dependencies. Dependencies that are not in
    the candidate set and not in ``completed_ids`` are assumed already landed
    (they could only be there if they passed earlier), so they do not block.

    Returns a list of phase ids in the order they should be merged.
    """

    normalized = normalize_phases(candidates)
    order_index = {p.phase_id: i for i, p in enumerate(normalized)}
    by_id = {p.phase_id: p for p in normalized}
    candidate_ids = set(by_id)
    done: set[str] = set(completed_ids)

    def deps_ready(phase: SchedulerPhase) -> bool:
        for dep in phase.dependencies:
            # Only dependencies that are themselves queued can block ordering;
            # anything outside the candidate set is assumed already merged.
            if dep in candidate_ids and dep not in done:
                return False
        return True

    emitted: list[str] = []
    remaining = list(normalized)
    last_group: str | None = None

    while remaining:
        ready = [p for p in remaining if deps_ready(p)]
        if not ready:
            # Cyclic/unsatisfiable within candidates: fall back to stable input
            # order for the rest so the queue always makes progress.
            ready = list(remaining)

        def sort_key(p: SchedulerPhase) -> tuple[int, int]:
            # Prefer continuing the current merge_group, then input order.
            group_pref = 0 if (last_group is not None and p.merge_group == last_group) else 1
            return (group_pref, order_index[p.phase_id])

        chosen = min(ready, key=sort_key)
        emitted.append(chosen.phase_id)
        done.add(chosen.phase_id)
        last_group = chosen.merge_group
        remaining = [p for p in remaining if p.phase_id != chosen.phase_id]

    return emitted


def next_to_merge(
    candidates: Sequence[Any],
    *,
    completed_ids: Sequence[str] = (),
) -> str | None:
    """Return the next phase id to merge, or None when the queue is empty."""

    order = serial_merge_order(candidates, completed_ids=completed_ids)
    return order[0] if order else None
