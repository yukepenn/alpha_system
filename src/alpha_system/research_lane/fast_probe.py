"""Generic fast exploratory probe bridge over already-materialized slices."""

from __future__ import annotations

import multiprocessing as mp
import os
import random
from collections.abc import Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from alpha_system.core.hashing import hash_config
from alpha_system.core.value_store import load_parquet_values
from alpha_system.data.storage import DataDependencyError
from alpha_system.governance.idea_draft import CONTEXT_NOT_EQUAL_TRIGGER, MAIN_EFFECT
from alpha_system.governance.mechanism_card import (
    EXPLORATORY_STAMP,
    MechanismCard,
    validate_mechanism_card,
)
from alpha_system.governance.serialization import JsonValue
from alpha_system.governance.setup_spec import SetupSpec, validate_setup_spec
from alpha_system.governance.surrogate_run import ZERO_PASS_MET
from alpha_system.research.conditional_probe import (
    NET_EXCURSION_OUTCOME,
    NET_EXCURSION_REQUIRED_LABEL_TYPES,
    RECOGNIZED_CONTINUOUS_OUTCOMES,
    ConditionalProbeError,
    build_path_label_observation_set,
    build_surrogate_zero_pass_gate,
    compile_setup_spec_to_conditional_probe,
    continuous_outcome_mean_lift,
    evaluate_setup_conditional_probe,
)
from alpha_system.research.events import target_before_stop_probability
from alpha_system.research_lane.slice_spec import (
    SliceFeatureInput,
    SliceLabelInput,
    SliceSpec,
    SliceSpecError,
)
from alpha_system.runtime.diagnostics.factor.runtime import build_factor_diagnostics_run
from alpha_system.runtime.diagnostics.power import build_ic_power_statement
from alpha_system.runtime.diagnostics.splits.n_eff import (
    estimate_n_eff,
    forward_overlap_block_size,
)
from alpha_system.runtime.input_resolver import (
    DATA_ROOT_PRECONDITION_CODE,
    FeatureLabelPackResolver,
    RuntimeInputResolverError,
)

FAST_PROBE_SCHEMA = "alpha_system.research_lane.fast_probe.v1"
ISSUE_DATA_GAP = "DATA_GAP"
ISSUE_MISSING_DEPENDENCY = "MISSING_DEPENDENCY"
ISSUE_ALPHA_DATA_ROOT_MISSING = "ALPHA_DATA_ROOT_MISSING"
ISSUE_REGISTRY_UNAVAILABLE = "REGISTRY_UNAVAILABLE"
ISSUE_DEPRECATED_PACK_PIN = "DEPRECATED_PACK_PIN"
ISSUE_DATASET_VERSION_MISMATCH = "DATASET_VERSION_MISMATCH"
ISSUE_VALUE_FILE_MISSING = "VALUE_FILE_MISSING"
ISSUE_TRUE_DATA_GAP = "TRUE_DATA_GAP"

# Resolution-adequate standing surrogate budget. The cross-idea FDR gate needs
# ``run_count >= ceil(m / alpha) - 1`` to resolve an FDR-corrected p-value; the
# ``family_fdr_budget`` canary proves the historical hardcoded 64 cannot resolve
# a corrected p (resolution-inadequate). At ``alpha = 0.10`` a run_count of 1000
# is resolution-adequate for family sizes up to ~100. Committed PRODUCTION idea
# YAMLs set ``surrogate_run_count`` to this value; small test fixtures override
# it downward for speed (the count is a configuration knob, not a statistical
# result, so the gate verdict for a given seed/run_count is unaffected).
RESOLUTION_ADEQUATE_SURROGATE_RUNS = 1000

# RAM headroom reserved (bytes) so heavy parallel re-probes do not OOM the box.
# Per the never-idle / RAM-safety doctrine we keep ~12 GiB free; the auto worker
# resolver caps workers so reserved-headroom / (estimated per-worker footprint)
# is respected on top of the CPU cap.
_SURROGATE_RAM_RESERVE_BYTES = 12 * 1024 * 1024 * 1024
# Conservative per-worker resident estimate for one re-probe unit. Used only to
# derive an upper worker bound from available RAM; the true footprint is bounded
# by a single materialized row-set, not the full 1000.
_SURROGATE_PER_WORKER_BYTES = 1024 * 1024 * 1024
# CPU headroom: leave this many cores for the parent + OS so the box stays
# responsive and other harness compute is not starved.
_SURROGATE_CPU_HEADROOM = 2


class FastProbeError(ValueError):
    """Raised when fast-probe inputs are malformed."""


@dataclass(frozen=True, slots=True)
class ResolvedSliceHandles:
    """Value-free resolver output for the requested bounded slice."""

    feature_handles: tuple[Mapping[str, object], ...]
    label_handles: tuple[Mapping[str, object], ...]

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "feature_handles": [dict(handle) for handle in self.feature_handles],
            "label_handles": [dict(handle) for handle in self.label_handles],
        }


@dataclass(frozen=True, slots=True)
class InjectedRows:
    """Mapped in-memory rows for the unchanged probe engines."""

    feature_rows_by_role: Mapping[str, tuple[dict[str, Any], ...]]
    label_rows_by_role: Mapping[str, tuple[dict[str, Any], ...]]

    def row_counts(self) -> dict[str, JsonValue]:
        return {
            "feature_rows": {
                role: len(rows) for role, rows in sorted(self.feature_rows_by_role.items())
            },
            "label_rows": {
                role: len(rows) for role, rows in sorted(self.label_rows_by_role.items())
            },
        }


def fast_probe(
    card: MechanismCard | Mapping[str, Any],
    setup: SetupSpec | Mapping[str, Any] | None,
    slice_spec: SliceSpec | Mapping[str, Any],
    *,
    resolver: FeatureLabelPackResolver | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, JsonValue]:
    """Load one bounded existing slice and run the configured exploratory probe."""

    active_card = _coerce_card(card)
    active_slice = _coerce_slice(slice_spec)
    root = active_slice.resolve_data_root(env=env)
    active_setup = _coerce_setup(setup) if setup is not None else None

    if not root.exists():
        return build_fast_probe_data_gap(
            active_card,
            active_setup,
            active_slice,
            issue_code=ISSUE_ALPHA_DATA_ROOT_MISSING,
            reason=f"ALPHA_DATA_ROOT/data root does not resolve: {root}",
        )
    try:
        active_resolver = resolver or FeatureLabelPackResolver(alpha_data_root=root, env=env)
        handles = _resolve_slice_handles(active_slice, active_resolver)
        injected = _load_injected_rows(root, active_slice)
        _require_non_empty_rows(injected)
    except _DATA_GAP_EXCEPTIONS as exc:
        return build_fast_probe_data_gap(
            active_card,
            active_setup,
            active_slice,
            issue_code=_classify_gap_exception(exc),
            reason=f"bounded slice rows could not be resolved via sanctioned loader: {exc}",
        )

    if active_slice.study_kind == MAIN_EFFECT:
        return _run_main_effect(
            active_card,
            active_slice,
            injected,
            handles=handles,
        )
    if active_slice.study_kind == CONTEXT_NOT_EQUAL_TRIGGER:
        if active_setup is None:
            raise FastProbeError("setup is required for context_not_equal_trigger fast probes")
        return _run_context_not_equal_trigger(
            active_card,
            active_setup,
            active_slice,
            injected,
            handles=handles,
        )
    raise FastProbeError(f"unsupported study_kind: {active_slice.study_kind}")


def build_fast_probe_data_gap(
    card: MechanismCard | Mapping[str, Any],
    setup: SetupSpec | Mapping[str, Any] | None,
    slice_spec: SliceSpec | Mapping[str, Any],
    *,
    issue_code: str = ISSUE_DATA_GAP,
    reason: str,
) -> dict[str, JsonValue]:
    """Build an honest unresolved-input readout without fabricated values."""

    active_card = _coerce_card(card)
    active_slice = _coerce_slice(slice_spec)
    active_setup = _coerce_setup(setup) if setup is not None else None
    factor_id, factor_version = _power_factor(active_slice, active_setup)
    gate = build_surrogate_zero_pass_gate(run_count=0, gate_pass_count=0, error_count=0)
    power = build_ic_power_statement(
        n_eff=0,
        scope="per_factor",
        factor_id=factor_id,
        factor_version=factor_version,
    )
    payload: dict[str, JsonValue] = {
        "schema": FAST_PROBE_SCHEMA,
        "status": "INCONCLUSIVE",
        "issue_code": issue_code,
        "study_kind": active_slice.study_kind,
        "stamp": EXPLORATORY_STAMP,
        "promotion_eligible": False,
        "mechanism_card": active_card.to_dict(),
        "setup_spec": active_setup.to_dict() if active_setup is not None else None,
        "slice_spec": active_slice.to_dict(),
        "row_access": {
            "status": "unresolved",
            "issue_code": issue_code,
            "reason": reason,
            "fabricated_values": False,
        },
        "surrogate_fdr_gate": gate,
        "power": power,
        "created_at": active_slice.created_at,
    }
    payload["readout_id"] = _readout_id("fpgap", payload)
    return payload


def run_label_shuffle_surrogate(
    *,
    setup: SetupSpec | Mapping[str, Any],
    injected: InjectedRows,
    surrogate_runs: int,
    base_seed: int,
    outcome_label_type: str | None = None,
    block_size: int = 1,
    workers: int | None = None,
) -> dict[str, JsonValue]:
    """Run the bounded label-shuffle ZERO_PASS surrogate calibration.

    The ZERO_PASS / FDR structure is identical for the binary and continuous
    paths: count shuffled-label iterations whose |effect| exceeds the observed
    |effect|. Only the per-iteration effect statistic differs. The binary path
    (``outcome_label_type`` None) uses the ``target_before_stop`` probability-share
    delta exactly as before; a continuous outcome uses the conditioned-mean delta
    of that float path outcome.

    ``block_size`` controls the shuffle unit. A forward-overlapping path outcome
    (e.g. a 120-bar MFE path) has consecutive bar-spaced outcomes that overlap
    ~horizon-fold, so a plain row-level permutation destroys that autocorrelation
    and understates the null variance (inflated significance). When
    ``block_size > 1`` we time-order the shuffled outcome values and permute
    NON-OVERLAPPING FIXED-LENGTH BLOCKS instead of individual rows, preserving the
    within-block autocorrelation. When ``block_size <= 1`` this is byte-identical
    to the historical row-level shuffle (the non-overlapping path is unchanged).

    Determinism + parallelism: every surrogate iteration seeds its own RNG with
    ``random.Random(base_seed + run_index)`` — a pure function of ``run_index``
    that is independent of execution order or worker count. The per-surrogate
    unit (block-shuffle + re-probe + effect) is therefore a pure function of the
    immutable inputs and ``run_index``. ``workers`` selects how that map is run:
    ``workers == 1`` runs the byte-for-byte serial loop on the calling process;
    ``workers > 1`` (or ``None`` for the auto cap) dispatches the units across a
    ``ProcessPoolExecutor`` and aggregates the per-run ``(pass, error)``
    increments in ``run_index`` order. Because each unit reseeds locally and the
    pass/error increments are summed in run_index order, the aggregate gate
    (``gate_pass_count``, ``run_count``, ``error_count``, ``observed_effect``,
    ``threshold_verdict``) is byte-identical regardless of ``workers``.
    """

    active_setup = _coerce_setup(setup)
    probe = compile_setup_spec_to_conditional_probe(active_setup)
    context_rows = _feature_rows(injected, "context")
    trigger_rows = _feature_rows(injected, "trigger")
    path_rows = _label_rows(injected, "path")

    # The shuffled label_type(s) and the effect statistic are the only things that
    # differ between binary, single-continuous, and the derived net_excursion path;
    # everything else (seed handling, alignment, FDR gate) stays shared. For
    # net_excursion the null must relocate each event's (mfe, mae) PAIR TOGETHER, so
    # we shuffle BOTH materialized label_types with ONE shared permutation order
    # rather than one label_type.
    shuffle_label_types = _shuffle_label_types(outcome_label_type)

    observed = build_path_label_observation_set(
        probe,
        context_factor_values=context_rows,
        trigger_factor_values=trigger_rows,
        path_labels=path_rows,
        outcome_label_type=outcome_label_type,
    )
    observed_uplift = _surrogate_effect(observed, outcome_label_type)
    active_block_size = max(int(block_size), 1)
    # A single-label outcome (binary or one continuous label_type) under the
    # row-level path (block_size <= 1) preserves the historical ORIGINAL-ORDER
    # value shuffle byte-for-byte. The block path and the joint net_excursion path
    # instead time-order each label_type's rows by event_ts ASCENDING so contiguous
    # non-overlapping blocks line up with the forward overlap autocorrelation; the
    # permuted values are reassigned in that same time order. ``event_ts`` is
    # required on every label row (see _label_rows_from_records / _required), so a
    # missing event_ts would already have failed upstream; the empty-string
    # sentinel only guards against an in-memory fixture that omits it.
    legacy_single_label_row_shuffle = (
        len(shuffle_label_types) == 1 and active_block_size <= 1
    )
    # For net_excursion both label_types share a single permutation order computed
    # over the common per-event count, so the per-event (mfe, mae) pairing is
    # preserved: a given event's two rows always relocate to the same target event.
    target_rows_by_type = {
        label_type: _time_ordered_label_rows(path_rows, label_type)
        for label_type in shuffle_label_types
    }
    shared_event_count = _shared_event_count(target_rows_by_type)
    legacy_target_rows = [
        (index, row)
        for index, row in enumerate(path_rows)
        if row.get("label_type") == shuffle_label_types[0]
    ]

    context = _SurrogateContext(
        probe=probe,
        context_rows=tuple(dict(row) for row in context_rows),
        trigger_rows=tuple(dict(row) for row in trigger_rows),
        path_rows=tuple(dict(row) for row in path_rows),
        legacy_target_rows=tuple(
            (index, dict(row)) for index, row in legacy_target_rows
        ),
        target_rows_by_type={
            label_type: tuple((index, dict(row)) for index, row in rows)
            for label_type, rows in target_rows_by_type.items()
        },
        shared_event_count=shared_event_count,
        active_block_size=active_block_size,
        legacy_single_label_row_shuffle=legacy_single_label_row_shuffle,
        outcome_label_type=outcome_label_type,
        observed_uplift=observed_uplift,
        base_seed=base_seed,
    )

    pass_count, error_count = _run_surrogate_map(
        context,
        surrogate_runs=surrogate_runs,
        workers=workers,
    )

    gate = build_surrogate_zero_pass_gate(
        run_count=surrogate_runs,
        gate_pass_count=pass_count,
        error_count=error_count,
    )
    # Surface the conditioned power + observed effect the surrogate already computed
    # so a NOT-met gate can be classified as a well-powered null (REJECT) vs an
    # underpowered requeue vs a calibration error — the surrogate-blocked early
    # return otherwise carries no power and the verdict cannot tell them apart.
    conditioned_count = len(observed.conditioned_observations)
    if active_block_size > 1 and conditioned_count > 0:
        conditioned_n_eff = estimate_n_eff(
            conditioned_count,
            {
                "horizon_bars": active_block_size,
                "sampling_cadence_bars": 1,
                "discount_factor": active_block_size,
                "metadata_source": "setup_surrogate_conditioned_overlap",
            },
            purge_gap=0,
            embargo_gap=0,
        ).n_eff
    else:
        conditioned_n_eff = conditioned_count
    gate["conditioned_n_eff"] = conditioned_n_eff
    gate["observed_effect"] = None if observed_uplift is None else float(observed_uplift)
    return gate


def _surrogate_effect(observation_set: Any, outcome_label_type: str | None) -> float | None:
    """The conditioned effect statistic for one observation set.

    Binary outcome (``outcome_label_type`` None) uses the ``target_before_stop``
    probability-share delta; a continuous outcome uses the conditioned-mean lift
    of that float path outcome. Top-level (not a closure) so the parallel worker
    can call it without capturing the calling frame.
    """

    if outcome_label_type is None:
        return _conditional_uplift(
            observation_set.conditioned_observations,
            observation_set.aligned_observations,
        )
    lift = continuous_outcome_mean_lift(
        observation_set.conditioned_observations,
        observation_set.aligned_observations,
        outcome_label_type=outcome_label_type,
    )["mean_lift"]
    return None if lift is None else float(lift)


@dataclass(frozen=True, slots=True)
class _SurrogateContext:
    """Immutable, picklable inputs shared by every surrogate iteration.

    Every field is plain data (the compiled ``ConditionalProbeSpec`` is a frozen
    dataclass of plain values; the row collections are tuples of dicts), so the
    whole context pickles cleanly to a ``ProcessPoolExecutor`` worker exactly
    once via the pool initializer. Per-iteration RNG state is NOT stored here: a
    surrogate is reseeded from ``base_seed + run_index`` inside the unit, which
    is what keeps the result independent of worker count and order.
    """

    probe: Any
    context_rows: tuple[Mapping[str, Any], ...]
    trigger_rows: tuple[Mapping[str, Any], ...]
    path_rows: tuple[Mapping[str, Any], ...]
    legacy_target_rows: tuple[tuple[int, Mapping[str, Any]], ...]
    target_rows_by_type: Mapping[str, tuple[tuple[int, Mapping[str, Any]], ...]]
    shared_event_count: int
    active_block_size: int
    legacy_single_label_row_shuffle: bool
    outcome_label_type: str | None
    observed_uplift: float | None
    base_seed: int


def _compute_one_surrogate(context: _SurrogateContext, run_index: int) -> tuple[int, int]:
    """One surrogate unit: ``(pass_increment, error_increment)`` for ``run_index``.

    Pure given ``(context, run_index)``: the RNG is reseeded locally from
    ``base_seed + run_index`` so the block-shuffle, re-probe, and exceedance test
    are identical regardless of which worker (or the serial caller) runs it.
    """

    rng = random.Random(context.base_seed + run_index)
    if context.legacy_single_label_row_shuffle:
        rebuilt = _rebuild_legacy_row_shuffle(
            context.path_rows, context.legacy_target_rows, rng
        )
    else:
        rebuilt = _rebuild_surrogate_path_rows(
            context.path_rows,
            target_rows_by_type=context.target_rows_by_type,
            shared_event_count=context.shared_event_count,
            block_size=context.active_block_size,
            rng=rng,
        )
    try:
        surrogate_observations = build_path_label_observation_set(
            context.probe,
            context_factor_values=context.context_rows,
            trigger_factor_values=context.trigger_rows,
            path_labels=rebuilt,
            outcome_label_type=context.outcome_label_type,
        )
        surrogate_uplift = _surrogate_effect(
            surrogate_observations, context.outcome_label_type
        )
    except ConditionalProbeError:
        return (0, 1)
    if (
        surrogate_uplift is not None
        and context.observed_uplift is not None
        and abs(surrogate_uplift) > abs(context.observed_uplift)
    ):
        return (1, 0)
    return (0, 0)


# Worker-process global set once by the pool initializer so the (potentially
# large) context is pickled to each worker exactly once rather than per task.
_WORKER_SURROGATE_CONTEXT: _SurrogateContext | None = None


def _init_surrogate_worker(context: _SurrogateContext) -> None:
    global _WORKER_SURROGATE_CONTEXT
    _WORKER_SURROGATE_CONTEXT = context


def _compute_one_surrogate_worker(run_index: int) -> tuple[int, int]:
    """Pool-mapped entry point reading the worker-global context.

    Top-level + argument is a single int, so the only per-task payload is the
    run_index; the shared context travels once through the initializer.
    """

    assert _WORKER_SURROGATE_CONTEXT is not None
    return _compute_one_surrogate(_WORKER_SURROGATE_CONTEXT, run_index)


def _run_surrogate_map(
    context: _SurrogateContext,
    *,
    surrogate_runs: int,
    workers: int | None,
) -> tuple[int, int]:
    """Aggregate ``(pass_count, error_count)`` over all surrogate runs.

    Serial (``effective_workers <= 1``) calls the unit in ``run_index`` order on
    the calling process. Parallel maps the unit across a ``ProcessPoolExecutor``
    in chunks and consumes results in ``run_index`` order (``executor.map`` is
    order-preserving). Either way the pass/error increments are summed in
    run_index order, so the totals are byte-identical to the serial path.
    """

    if surrogate_runs <= 0:
        return (0, 0)

    effective_workers = _resolve_surrogate_workers(workers, surrogate_runs)
    if effective_workers <= 1:
        pass_count = 0
        error_count = 0
        for run_index in range(surrogate_runs):
            pass_inc, error_inc = _compute_one_surrogate(context, run_index)
            pass_count += pass_inc
            error_count += error_inc
        return (pass_count, error_count)

    # Chunk so a worker pulls a contiguous run of indices per dispatch; this
    # keeps memory bounded (each worker materializes one re-probe row-set at a
    # time, never all ``surrogate_runs`` at once) while amortizing dispatch.
    chunksize = max(1, surrogate_runs // (effective_workers * 4))
    mp_context = mp.get_context()
    pass_count = 0
    error_count = 0
    with ProcessPoolExecutor(
        max_workers=effective_workers,
        mp_context=mp_context,
        initializer=_init_surrogate_worker,
        initargs=(context,),
    ) as executor:
        for pass_inc, error_inc in executor.map(
            _compute_one_surrogate_worker,
            range(surrogate_runs),
            chunksize=chunksize,
        ):
            pass_count += pass_inc
            error_count += error_inc
    return (pass_count, error_count)


def _resolve_surrogate_workers(workers: int | None, surrogate_runs: int) -> int:
    """Resolve the effective worker count under CPU + RAM headroom caps.

    ``workers == 1`` forces the serial path (debugging / tests). An explicit
    ``workers > 1`` is honored but still clamped to ``surrogate_runs`` and the
    CPU cap. ``workers is None`` auto-selects ``cpu_count - headroom`` clamped by
    a RAM-derived bound (reserved headroom / per-worker estimate) and by
    ``surrogate_runs`` so a tiny calibration never spins up more workers than
    units. The auto cap can never exceed the explicit/CPU bound, so it only ever
    reduces parallelism for safety; it does not change the result.
    """

    if workers is not None:
        if workers <= 1:
            return 1
        return max(1, min(workers, surrogate_runs))

    cpu_total = os.cpu_count() or 1
    cpu_cap = max(1, cpu_total - _SURROGATE_CPU_HEADROOM)
    ram_cap = _ram_worker_cap()
    return max(1, min(cpu_cap, ram_cap, surrogate_runs))


def _ram_worker_cap() -> int:
    """Upper worker bound from available RAM, or the CPU cap when unknown.

    Uses ``/proc/meminfo`` MemAvailable (Linux/WSL2) to bound workers so heavy
    parallel re-probes keep ~``_SURROGATE_RAM_RESERVE_BYTES`` free. When the
    figure is unavailable the RAM cap is non-binding (returns the CPU total) and
    the CPU headroom cap governs.
    """

    cpu_total = os.cpu_count() or 1
    try:
        with open("/proc/meminfo", encoding="ascii") as handle:
            available_kib = 0
            for line in handle:
                if line.startswith("MemAvailable:"):
                    available_kib = int(line.split()[1])
                    break
    except (OSError, ValueError, IndexError):
        return cpu_total
    if available_kib <= 0:
        return cpu_total
    available_bytes = available_kib * 1024
    usable = available_bytes - _SURROGATE_RAM_RESERVE_BYTES
    if usable <= 0:
        return 1
    return max(1, usable // _SURROGATE_PER_WORKER_BYTES)


def _shuffle_label_types(outcome_label_type: str | None) -> tuple[str, ...]:
    """The path-row label_type(s) the surrogate permutes for this outcome.

    Binary (``None``) shuffles ``target_before_stop``; a single continuous outcome
    shuffles its own label_type; the derived ``net_excursion`` shuffles BOTH
    materialized excursion label_types so the per-event (mfe, mae) pair moves
    together under one shared permutation order.
    """

    if outcome_label_type is None:
        return ("target_before_stop",)
    if outcome_label_type == NET_EXCURSION_OUTCOME:
        return NET_EXCURSION_REQUIRED_LABEL_TYPES
    return (outcome_label_type,)


def _rebuild_legacy_row_shuffle(
    path_rows: Sequence[Mapping[str, Any]],
    legacy_target_rows: Sequence[tuple[int, Mapping[str, Any]]],
    rng: random.Random,
) -> list[dict[str, Any]]:
    """Byte-identical historical single-label row shuffle (original path order).

    The shuffled values are taken in ORIGINAL path_rows order, permuted with
    ``rng.shuffle``, and reassigned sequentially to the matching label_type rows in
    that same original order. This preserves the exact legacy RNG consumption and
    value-to-row mapping for the unchanged binary / single-continuous path.
    """

    shuffled_values = [row.get("value") for _, row in legacy_target_rows]
    rng.shuffle(shuffled_values)
    target_indices = {index for index, _ in legacy_target_rows}
    value_iter = iter(shuffled_values)
    rebuilt: list[dict[str, Any]] = []
    for index, row in enumerate(path_rows):
        if index in target_indices:
            rebuilt.append({**row, "value": next(value_iter)})
        else:
            rebuilt.append(dict(row))
    return rebuilt


def _time_ordered_label_rows(
    path_rows: Sequence[Mapping[str, Any]],
    label_type: str,
) -> list[tuple[int, Mapping[str, Any]]]:
    """The (original_index, row) pairs of one label_type, ordered by event_ts ASC.

    The original index preserves the position in ``path_rows`` so reassignment can
    write back to the exact source row regardless of interleaving with other
    label_types.
    """

    indexed = [
        (index, row)
        for index, row in enumerate(path_rows)
        if row.get("label_type") == label_type
    ]
    indexed.sort(key=lambda item: str(item[1].get("event_ts") or ""))
    return indexed


def _shared_event_count(
    target_rows_by_type: Mapping[str, Sequence[tuple[int, Mapping[str, Any]]]],
) -> int:
    """Common per-event row count across the shuffled label_types.

    A single shared permutation can only pair rows coherently when every shuffled
    label_type contributes the same number of time-ordered events; the minimum is
    used so an in-memory fixture with a ragged tail cannot index out of range (the
    surplus tail rows of any one type simply stay in place for that run).
    """

    counts = [len(rows) for rows in target_rows_by_type.values()]
    return min(counts) if counts else 0


def _rebuild_surrogate_path_rows(
    path_rows: Sequence[Mapping[str, Any]],
    *,
    target_rows_by_type: Mapping[str, Sequence[tuple[int, Mapping[str, Any]]]],
    shared_event_count: int,
    block_size: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    """Apply ONE permutation order to every shuffled label_type, pairing preserved.

    ``block_size <= 1`` reproduces the historical row-level shuffle byte-for-byte
    for a single label_type (the permutation is a plain row shuffle). ``> 1`` block-
    permutes non-overlapping fixed-length blocks of the time-ordered positions. The
    SAME permutation order is applied to each label_type in its own event-time
    order, so per-event multi-label values (the net_excursion mfe/mae pair) relocate
    to the same destination event together.
    """

    order = list(range(shared_event_count))
    if block_size <= 1:
        rng.shuffle(order)
    else:
        order = _block_permute(order, block_size, rng)

    # value_by_source[original_index] = the value relocated INTO that source row.
    value_by_source: dict[int, Any] = {}
    for rows in target_rows_by_type.values():
        for dest_pos, src_pos in enumerate(order):
            dest_index = rows[dest_pos][0]
            source_value = rows[src_pos][1].get("value")
            value_by_source[dest_index] = source_value

    rebuilt: list[dict[str, Any]] = []
    for index, row in enumerate(path_rows):
        if index in value_by_source:
            rebuilt.append({**row, "value": value_by_source[index]})
        else:
            rebuilt.append(dict(row))
    return rebuilt


def _block_permute(values: list[Any], block_size: int, rng: random.Random) -> list[Any]:
    """Permute non-overlapping fixed-length blocks; preserve within-block order.

    Partition the time-ordered sequence ``values`` into ceil(N / block_size)
    contiguous non-overlapping blocks (the final block may be shorter), permute
    the ORDER OF THE BLOCKS with ``rng``, then concatenate them back. Within-block
    order is preserved, which is what retains the forward-overlap autocorrelation
    a row-level shuffle would destroy.
    """

    blocks = [values[start : start + block_size] for start in range(0, len(values), block_size)]
    order = list(range(len(blocks)))
    rng.shuffle(order)
    permuted: list[Any] = []
    for block_index in order:
        permuted.extend(blocks[block_index])
    return permuted


def _run_main_effect(
    card: MechanismCard,
    slice_spec: SliceSpec,
    injected: InjectedRows,
    *,
    handles: ResolvedSliceHandles,
) -> dict[str, JsonValue]:
    feature_rows = _feature_rows(injected, "factor", fallback_first=True)
    label_rows = _label_rows(injected, "label", fallback_first=True)
    observations = _align_main_effect_rows(feature_rows, label_rows)
    feature = _first_feature(slice_spec, roles=("factor",))
    spec = {
        "diagnostics_run_spec_id": f"fast_probe_{card.mechanism_id}",
        "content_hash": hash_config(
            {
                "mechanism_id": card.mechanism_id,
                "slice_id": slice_spec.slice_id,
                "study_kind": slice_spec.study_kind,
            }
        ),
    }
    result = build_factor_diagnostics_run(
        diagnostics_run_spec=spec,
        observations=observations,
        lineage_refs={
            "mechanism_id": card.mechanism_id,
            "factor_id": feature.factor_id,
            "slice_id": slice_spec.slice_id,
        },
        horizon_overlap_metadata=_main_effect_overlap_metadata(slice_spec),
    )
    report_payload = result.report.to_dict()
    payload: dict[str, JsonValue] = {
        "schema": FAST_PROBE_SCHEMA,
        "status": "RECORDED",
        "study_kind": MAIN_EFFECT,
        "stamp": EXPLORATORY_STAMP,
        "promotion_eligible": False,
        "mechanism_card": card.to_dict(),
        "setup_spec": None,
        "slice_spec": slice_spec.to_dict(),
        "row_access": _resolved_row_access(injected),
        "resolved_handles": handles.to_dict(),
        "engine": "build_factor_diagnostics_run",
        "readout": {
            "factor_diagnostics_report": report_payload,
            "diagnostics_run_record": result.record.to_dict(),
        },
    }
    payload["readout_id"] = _readout_id("fpmain", payload)
    return payload


def _main_effect_outcome_label_type(slice_spec: SliceSpec) -> str:
    """The forward outcome label_type the main-effect IC is computed against.

    The main-effect probe stacks one observation per bar against a forward
    diagnostic return label (a forward-overlapping outcome by construction). We
    prefer an explicit float ``label_version_map`` binding when present; the
    fallback is the canonical ``forward_return`` family. Either way the result is
    forward-overlapping so the overlap discount is mandatory (the #474 law).
    """

    for binding in slice_spec.label_version_bindings:
        if binding.value_type == "float":
            return binding.label_type
    return "forward_return"


def _main_effect_overlap_metadata(slice_spec: SliceSpec) -> dict[str, JsonValue]:
    """Mandatory label-horizon overlap metadata for honest IC-power N_eff.

    The main-effect probe stacks one observation per bar against a forward label
    that spans the label horizon in bars, so consecutive observations overlap
    ~that many bars and the raw row count overstates the independent sample. The
    outcome is forward-overlapping by construction, so the discount is mandatory:
    we derive the overlap block size from the label horizon via the shared
    fail-closed helper. A genuinely single-bar-ahead label yields block size 1
    (``discount_factor`` 1, no overlap) -- still honest. When the horizon cannot
    be derived the helper RAISES rather than silently falling back to raw rows
    (the #474 law); we never return ``None``/raw here.
    """

    outcome_label_type = _main_effect_outcome_label_type(slice_spec)
    block_size = forward_overlap_block_size(
        outcome_label_type,
        required_future_bars=slice_spec.required_future_bars,
    )
    return {
        "horizon_bars": block_size,
        "sampling_cadence_bars": 1,
        "discount_factor": block_size,
        "metadata_source": "fast_probe_main_effect_label_horizon",
    }


def _run_context_not_equal_trigger(
    card: MechanismCard,
    setup: SetupSpec,
    slice_spec: SliceSpec,
    injected: InjectedRows,
    *,
    handles: ResolvedSliceHandles,
) -> dict[str, JsonValue]:
    outcome_label_type = _resolve_outcome_label_type(slice_spec)
    # A forward-overlapping continuous/derived path outcome (e.g. net_excursion,
    # required_future_bars=120) must use horizon-bar non-overlapping blocks so the
    # label-shuffle null keeps its overlap autocorrelation AND so the conditioned
    # N_eff is discounted (the #474 law). For such an outcome the block size comes
    # from the shared FAIL-CLOSED helper keyed on the outcome label type: if the
    # horizon cannot be derived it RAISES rather than silently collapsing to
    # block_size 1 / raw conditioned N_eff (the latent #474 regression). The
    # binary ``target_before_stop`` path (outcome_label_type None) keeps its prior
    # horizon-bar block expression unchanged.
    if outcome_label_type is not None:
        block_size = forward_overlap_block_size(
            outcome_label_type,
            required_future_bars=slice_spec.required_future_bars,
        )
    else:
        block_size = max(int(slice_spec.required_future_bars or 1), 1)
    surrogate_gate = run_label_shuffle_surrogate(
        setup=setup,
        injected=injected,
        surrogate_runs=slice_spec.surrogate_run_count,
        base_seed=slice_spec.surrogate_base_seed,
        outcome_label_type=outcome_label_type,
        block_size=block_size,
    )
    if str(surrogate_gate.get("threshold_verdict")) != ZERO_PASS_MET:
        # The label-shuffle surrogate-FDR gate is NOT met: the conditioned effect is
        # indistinguishable from shuffled-label noise (or calibration was insufficient).
        # That is an HONEST exploratory outcome, not an error — return INCONCLUSIVE so the
        # loop records a verdict + routes to memory (requeue), never a tradable readout.
        return _build_surrogate_blocked_readout(
            card,
            setup,
            slice_spec,
            injected,
            handles=handles,
            surrogate_gate=surrogate_gate,
        )
    readout = evaluate_setup_conditional_probe(
        setup,
        context_factor_values=_feature_rows(injected, "context"),
        trigger_factor_values=_feature_rows(injected, "trigger"),
        path_labels=_label_rows(injected, "path"),
        family_id=_family_id(card, slice_spec),
        family_budget=_family_budget(card, slice_spec),
        surrogate_run_count=int(surrogate_gate["run_count"]),
        variant_id=_variant_id(card, setup, slice_spec),
        surrogate_gate_pass_count=int(surrogate_gate["gate_pass_count"]),
        surrogate_error_count=int(surrogate_gate["error_count"]),
        label_version=slice_spec.materialized_label_version,
        data_version=slice_spec.data_version,
        outcome_label_type=outcome_label_type,
        outcome_overlap_bars=slice_spec.required_future_bars,
        created_at=slice_spec.created_at,
    )
    readout_payload = readout.to_dict()
    payload: dict[str, JsonValue] = {
        "schema": FAST_PROBE_SCHEMA,
        "status": "RECORDED",
        "study_kind": CONTEXT_NOT_EQUAL_TRIGGER,
        "stamp": EXPLORATORY_STAMP,
        "promotion_eligible": False,
        "mechanism_card": card.to_dict(),
        "setup_spec": setup.to_dict(),
        "slice_spec": slice_spec.to_dict(),
        "row_access": _resolved_row_access(injected),
        "resolved_handles": handles.to_dict(),
        "engine": "evaluate_setup_conditional_probe",
        "readout": readout_payload,
        "surrogate_fdr_gate": readout_payload["surrogate_fdr_gate"],
        "variant_ledger_binding": readout_payload["variant_ledger_binding"],
        "power": readout_payload["power"],
    }
    payload["readout_id"] = readout_payload["readout_id"]
    return payload


def _build_surrogate_blocked_readout(
    card: MechanismCard,
    setup: SetupSpec,
    slice_spec: SliceSpec,
    injected: InjectedRows,
    *,
    handles: ResolvedSliceHandles,
    surrogate_gate: Mapping[str, JsonValue],
) -> dict[str, JsonValue]:
    """Honest INCONCLUSIVE readout when the surrogate-FDR gate is not ZERO_PASS_MET.

    The label-shuffle surrogate found the conditioned effect indistinguishable from
    shuffled-label noise (or calibration was insufficient): a legitimate research null,
    not an error. Return INCONCLUSIVE carrying the real surrogate gate so the loop routes
    it to memory (requeue); promotion_eligible stays False and no tradable metric is read.
    """

    factor_id, factor_version = _power_factor(slice_spec, setup)
    # Carry the conditioned overlap-aware n_eff the surrogate computed (not 0) so a
    # not-met gate can be classified as a well-powered null vs underpowered requeue.
    conditioned_n_eff = int(surrogate_gate.get("conditioned_n_eff") or 0)
    power = build_ic_power_statement(
        n_eff=conditioned_n_eff,
        scope="per_factor",
        factor_id=factor_id,
        factor_version=factor_version,
    )
    issue_code = str(surrogate_gate.get("threshold_verdict") or "surrogate_fdr_not_met")
    payload: dict[str, JsonValue] = {
        "schema": FAST_PROBE_SCHEMA,
        "status": "INCONCLUSIVE",
        "issue_code": issue_code,
        "study_kind": CONTEXT_NOT_EQUAL_TRIGGER,
        "stamp": EXPLORATORY_STAMP,
        "promotion_eligible": False,
        "mechanism_card": card.to_dict(),
        "setup_spec": setup.to_dict(),
        "slice_spec": slice_spec.to_dict(),
        "row_access": _resolved_row_access(injected),
        "resolved_handles": handles.to_dict(),
        "engine": "run_label_shuffle_surrogate",
        "surrogate_fdr_gate": surrogate_gate,
        "power": power,
        "created_at": slice_spec.created_at,
    }
    payload["readout_id"] = _readout_id("fpsg", payload)
    return payload


def _resolve_slice_handles(
    slice_spec: SliceSpec,
    resolver: FeatureLabelPackResolver,
) -> ResolvedSliceHandles:
    feature_handles = ()
    label_handles = ()
    if slice_spec.feature_pack_refs:
        feature_handles = tuple(
            handle.to_dict()
            for handle in resolver.resolve_feature_packs(
                slice_spec.feature_pack_refs,
                expected_dataset_version_id=slice_spec.dataset_version_id,
                expected_feature_request_ids=slice_spec.feature_request_ids,
                partition_id=slice_spec.partition_id,
                # Exploratory lane: horizon-agnostic features (<instr>_<year>_full_year)
                # legitimately serve a horizon-specific runtime; join is no-lookahead on
                # event_ts/available_ts. Labels below stay strict.
                allow_horizon_agnostic_partition=True,
            )
        )
    if slice_spec.label_pack_refs:
        label_handles = tuple(
            handle.to_dict()
            for handle in resolver.resolve_label_packs(
                slice_spec.label_pack_refs,
                expected_dataset_version_id=slice_spec.dataset_version_id,
                expected_label_spec_ids=slice_spec.label_spec_ids,
                partition_id=slice_spec.partition_id,
            )
        )
    return ResolvedSliceHandles(feature_handles=feature_handles, label_handles=label_handles)


def _load_injected_rows(root: Path, slice_spec: SliceSpec) -> InjectedRows:
    feature_rows: dict[str, tuple[dict[str, Any], ...]] = {}
    label_rows: dict[str, tuple[dict[str, Any], ...]] = {}
    for feature in slice_spec.feature_inputs:
        path = _input_path(root, feature.relative_path, field=f"feature[{feature.role}]")
        rows = tuple(
            _factor_rows_from_records(
                load_parquet_values(path),
                feature,
                slice_spec=slice_spec,
            )
        )
        feature_rows[feature.role] = rows
    for label in slice_spec.label_inputs:
        path = _input_path(root, label.relative_path, field=f"label[{label.role}]")
        rows = tuple(
            _label_rows_from_records(
                load_parquet_values(path),
                label,
                slice_spec=slice_spec,
            )
        )
        label_rows[label.role] = rows
    return InjectedRows(feature_rows_by_role=feature_rows, label_rows_by_role=label_rows)


def _factor_rows_from_records(
    records: Sequence[Mapping[str, Any]],
    feature: SliceFeatureInput,
    *,
    slice_spec: SliceSpec,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for bar_index, record in enumerate(sorted(records, key=lambda item: str(item.get("event_ts")))):
        # A feature SET pack holds multiple feature_version_ids; select only the one
        # this role's factor targets (feature.pack_ref == the feature_version_id), so a
        # single factor never gets duplicate rows per (instrument, event_ts) key. Labels
        # already filter by label_version_id symmetrically. Only skip records that
        # actually CARRY a differing feature_version_id; records without the column
        # (single-feature packs, in-memory fixtures) are kept (backward compatible).
        record_fver = record.get("feature_version_id")
        if feature.pack_ref and record_fver and str(record_fver) != feature.pack_ref:
            continue
        numeric = _optional_numeric(record.get("value"))
        if numeric is None:
            continue
        rows.append(
            {
                "factor_id": feature.factor_id,
                "factor_version": feature.factor_version,
                "instrument_id": slice_spec.instrument_id,
                "event_ts": _required(record, "event_ts"),
                "available_ts": record.get("available_ts") or record.get("event_ts"),
                "session_id": slice_spec.session_id,
                "data_version": slice_spec.data_version,
                "bar_index": int(record.get("bar_index", bar_index)),
                "value": numeric,
                "normalized_value": numeric,
                "factor_value": numeric,
                "feature_value": numeric,
            }
        )
    return rows


def _label_rows_from_records(
    records: Sequence[Mapping[str, Any]],
    label: SliceLabelInput,
    *,
    slice_spec: SliceSpec,
) -> list[dict[str, Any]]:
    bindings = slice_spec.label_version_map
    rows: list[dict[str, Any]] = []
    for record in records:
        version_id = str(record.get("label_version_id", ""))
        binding = bindings.get(version_id)
        if binding is None and bindings:
            continue
        label_type = (
            binding.label_type
            if binding is not None
            else str(record.get("label_type") or "forward_return_1m")
        )
        value_type = (
            binding.value_type
            if binding is not None
            else ("bool" if label_type in {"target_before_stop", "stop_before_target"} else "float")
        )
        value = _cast_label_value(record.get("value"), value_type)
        event_ts = _required(record, "event_ts")
        horizon_end_ts = str(
            record.get("horizon_end_ts") or record.get("label_available_ts") or event_ts
        )
        rows.append(
            {
                "label_id": label.label_id,
                "instrument_id": slice_spec.instrument_id,
                "event_ts": event_ts,
                "horizon": _horizon_seconds(slice_spec, record),
                "label_type": label_type,
                "value": value,
                "path_metadata": {
                    "session_id": slice_spec.session_id,
                    "label_version": (
                        slice_spec.materialized_label_version
                        or record.get("materialized_label_version")
                        or version_id
                        or "unversioned"
                    ),
                    "horizon_end_ts": horizon_end_ts,
                    "path_label": label.label_id,
                    "path_label_id": label.label_id,
                    "label_spec_id": label.label_spec_id or label.label_id,
                    "required_future_bars": _required_future_bars(slice_spec, record),
                    "observed_future_bars": _observed_future_bars(slice_spec, record),
                    "insufficient_future": bool(record.get("insufficient_future", False)),
                },
                "data_version": slice_spec.data_version,
                "label_available_ts": _required(record, "label_available_ts"),
            }
        )
    return rows


def _align_main_effect_rows(
    feature_rows: Sequence[Mapping[str, Any]],
    label_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    label_index: dict[tuple[str, str, str, str], Mapping[str, Any]] = {}
    for label in label_rows:
        key = _alignment_key(label)
        if key not in label_index:
            label_index[key] = label
    observations: list[dict[str, Any]] = []
    for feature in feature_rows:
        label = label_index.get(_alignment_key(feature))
        if label is None:
            continue
        observations.append(
            {
                "instrument_id": feature["instrument_id"],
                "event_ts": feature["event_ts"],
                "session_id": feature["session_id"],
                "data_version": feature["data_version"],
                "available_ts": feature["available_ts"],
                "label_available_ts": label["label_available_ts"],
                "factor_id": feature["factor_id"],
                "factor_version": feature["factor_version"],
                "factor_value": feature["value"],
                "feature_value": feature["value"],
                "value": feature["value"],
                "label_value": _label_numeric_value(label["value"]),
                "forward_return": _label_numeric_value(label["value"]),
                "horizon_seconds": int(label["horizon"]),
            }
        )
    if not observations:
        raise ValueError("main_effect fast probe found no aligned feature/label rows")
    return observations


def _require_non_empty_rows(injected: InjectedRows) -> None:
    for role, rows in injected.feature_rows_by_role.items():
        if not rows:
            raise ValueError(f"feature input {role!r} resolved to zero usable rows")
    for role, rows in injected.label_rows_by_role.items():
        if not rows:
            raise ValueError(f"label input {role!r} resolved to zero usable rows")


def _resolved_row_access(injected: InjectedRows) -> dict[str, JsonValue]:
    return {
        "status": "resolved_local_only",
        "reason": (
            "Rows were loaded via core.value_store.load_parquet_values in "
            "research_lane and injected in-memory into unchanged probe engines."
        ),
        "fabricated_values": False,
        "row_counts": injected.row_counts(),
    }


def _input_path(root: Path, relative_path: str | None, *, field: str) -> Path:
    if relative_path is None:
        raise ValueError(f"{field} lacks a relative_path; resolver handles are value-free")
    path = Path(relative_path).expanduser()
    return path if path.is_absolute() else root / path


def _feature_rows(
    injected: InjectedRows,
    role: str,
    *,
    fallback_first: bool = False,
) -> tuple[dict[str, Any], ...]:
    rows = injected.feature_rows_by_role.get(role)
    if rows is None and fallback_first and injected.feature_rows_by_role:
        rows = next(iter(injected.feature_rows_by_role.values()))
    if rows is None:
        raise FastProbeError(f"slice is missing feature role {role!r}")
    return tuple(dict(row) for row in rows)


def _label_rows(
    injected: InjectedRows,
    role: str,
    *,
    fallback_first: bool = False,
) -> tuple[dict[str, Any], ...]:
    rows = injected.label_rows_by_role.get(role)
    if rows is None and fallback_first and injected.label_rows_by_role:
        rows = next(iter(injected.label_rows_by_role.values()))
    if rows is None:
        raise FastProbeError(f"slice is missing label role {role!r}")
    return tuple(dict(row) for row in rows)


def _first_feature(slice_spec: SliceSpec, *, roles: Sequence[str]) -> SliceFeatureInput:
    for role in roles:
        for feature in slice_spec.feature_inputs:
            if feature.role == role:
                return feature
    return slice_spec.feature_inputs[0]


def _alignment_key(row: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row["instrument_id"]),
        str(row["event_ts"]),
        str(row.get("session_id") or row.get("path_metadata", {}).get("session_id")),
        str(row["data_version"]),
    )


def _conditional_uplift(
    conditioned: Sequence[Mapping[str, Any]],
    aligned: Sequence[Mapping[str, Any]],
) -> float | None:
    conditioned_share = target_before_stop_probability(conditioned).get(
        "target_before_stop_probability"
    )
    aligned_share = target_before_stop_probability(aligned).get("target_before_stop_probability")
    if conditioned_share is None or aligned_share is None:
        return None
    return float(conditioned_share) - float(aligned_share)


def _resolve_outcome_label_type(slice_spec: SliceSpec) -> str | None:
    """Validate and return the continuous/derived outcome selector, or None.

    None preserves the degenerate-bool ``target_before_stop`` path exactly. A
    materialized continuous selector (e.g. ``mfe_by_horizon``/``mae_by_horizon``)
    must (a) be a recognized continuous outcome and (b) be present in the slice's
    ``label_version_map`` bound to value_type "float". The DERIVED
    ``net_excursion`` selector is not a materialized label_type: it instead
    requires BOTH ``mfe_by_horizon`` AND ``mae_by_horizon`` to be bound as floats
    (so both buckets will be populated per event for the ``mfe + mae`` derivation).
    """

    selector = slice_spec.outcome_label_type
    if selector is None:
        return None
    if selector not in RECOGNIZED_CONTINUOUS_OUTCOMES:
        allowed = ", ".join(sorted(RECOGNIZED_CONTINUOUS_OUTCOMES))
        raise FastProbeError(
            f"outcome_label_type must be one of the continuous outcomes: {allowed}"
        )
    float_outcomes = {
        binding.label_type
        for binding in slice_spec.label_version_bindings
        if binding.value_type == "float"
    }
    if selector == NET_EXCURSION_OUTCOME:
        missing = [
            label_type
            for label_type in NET_EXCURSION_REQUIRED_LABEL_TYPES
            if label_type not in float_outcomes
        ]
        if missing:
            raise FastProbeError(
                "net_excursion outcome requires both mfe_by_horizon and mae_by_horizon "
                f"bound as float in the slice label_version_map; missing: {', '.join(missing)}"
            )
        return selector
    if selector not in float_outcomes:
        raise FastProbeError(
            "outcome_label_type must be a float label_type present in the slice "
            "label_version_map"
        )
    return selector


def _family_id(card: MechanismCard, slice_spec: SliceSpec) -> str:
    if slice_spec.family_id:
        return slice_spec.family_id
    value = card.duplicate_exposure.get("family_id")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return card.mechanism_id


def _family_budget(card: MechanismCard, slice_spec: SliceSpec) -> int:
    return int(
        slice_spec.family_budget if slice_spec.family_budget is not None else card.variant_budget
    )


def _variant_id(card: MechanismCard, setup: SetupSpec, slice_spec: SliceSpec) -> str | None:
    if slice_spec.variant_id:
        return slice_spec.variant_id
    value = card.duplicate_exposure.get("variant_id")
    if isinstance(value, str) and value.strip() and value.strip() in setup.allowed_variants:
        return value.strip()
    return None


def _power_factor(slice_spec: SliceSpec, setup: SetupSpec | None) -> tuple[str, str]:
    if setup is not None:
        trigger = dict(setup.event_trigger)
        factor_id = str(trigger.get("factor_id") or "")
        factor_version = str(trigger.get("factor_version") or "")
        if factor_id and factor_version:
            return factor_id, factor_version
    feature = slice_spec.feature_inputs[0]
    return feature.factor_id, feature.factor_version


def _horizon_seconds(slice_spec: SliceSpec, record: Mapping[str, Any]) -> int:
    value = record.get("horizon") or record.get("horizon_seconds") or slice_spec.horizon_seconds
    if value is None:
        raise ValueError("label rows require horizon_seconds or slice_spec.horizon_seconds")
    if isinstance(value, str):
        text = value.strip().lower()
        if text.endswith("m"):
            return int(float(text[:-1]) * 60)
        if text.endswith("s"):
            return int(float(text[:-1]))
    return int(value)


def _required_future_bars(slice_spec: SliceSpec, record: Mapping[str, Any]) -> int:
    value = record.get("required_future_bars") or slice_spec.required_future_bars
    if value is None:
        raise ValueError("label rows require required_future_bars")
    return int(value)


def _observed_future_bars(slice_spec: SliceSpec, record: Mapping[str, Any]) -> int:
    value = record.get("observed_future_bars") or _required_future_bars(slice_spec, record)
    return int(value)


def _cast_label_value(value: Any, value_type: str) -> bool | int | float | None:
    if value is None:
        return None
    if value_type == "bool":
        return bool(value)
    if value_type == "int":
        return int(value)
    if value_type == "float":
        return float(value)
    raise ValueError(f"unsupported label value_type: {value_type}")


def _label_numeric_value(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    return float(value)


def _optional_numeric(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Mapping):
        for key in ("normalized_value", "value"):
            if key in value:
                return _optional_numeric(value[key])
        return None
    return float(value)


def _required(record: Mapping[str, Any], field: str) -> Any:
    value = record.get(field)
    if value is None:
        raise ValueError(f"value row is missing {field}")
    return value


def _coerce_card(value: MechanismCard | Mapping[str, Any]) -> MechanismCard:
    if isinstance(value, MechanismCard):
        return validate_mechanism_card(value.to_dict())
    return validate_mechanism_card(value)


def _coerce_setup(value: SetupSpec | Mapping[str, Any]) -> SetupSpec:
    if isinstance(value, SetupSpec):
        return validate_setup_spec(value.to_dict())
    return validate_setup_spec(value)


def _coerce_slice(value: SliceSpec | Mapping[str, Any]) -> SliceSpec:
    if isinstance(value, SliceSpec):
        return SliceSpec.from_mapping(value.to_dict())
    return SliceSpec.from_mapping(value)


def _readout_id(prefix: str, payload: Mapping[str, Any]) -> str:
    return f"{prefix}_{hash_config(payload)[:24]}"


_DATA_GAP_EXCEPTIONS = (
    DataDependencyError,
    RuntimeInputResolverError,
    FileNotFoundError,
    OSError,
    ValueError,
    KeyError,
    SliceSpecError,
)


def _classify_gap_exception(exc: Exception) -> str:
    if isinstance(exc, DataDependencyError):
        return ISSUE_MISSING_DEPENDENCY
    if isinstance(exc, FileNotFoundError):
        return ISSUE_VALUE_FILE_MISSING
    if isinstance(exc, RuntimeInputResolverError):
        code = str(exc.reason.code)
        if code == DATA_ROOT_PRECONDITION_CODE:
            return ISSUE_ALPHA_DATA_ROOT_MISSING
        if code in {"feature_pack_deprecated", "label_pack_deprecated"}:
            return ISSUE_DEPRECATED_PACK_PIN
        if code in {
            "feature_pack_dataset_version_mismatch",
            "label_pack_dataset_version_mismatch",
        }:
            return ISSUE_DATASET_VERSION_MISMATCH
        if code.endswith("_not_found") or code.startswith("missing_"):
            return ISSUE_TRUE_DATA_GAP
        if code.endswith("_resolution_failed") or code.endswith("_resolver_missing"):
            return ISSUE_REGISTRY_UNAVAILABLE
        return code.upper()
    if isinstance(exc, OSError):
        return ISSUE_VALUE_FILE_MISSING
    return ISSUE_DATA_GAP


__all__ = [
    "FAST_PROBE_SCHEMA",
    "ISSUE_ALPHA_DATA_ROOT_MISSING",
    "ISSUE_DATASET_VERSION_MISMATCH",
    "ISSUE_DEPRECATED_PACK_PIN",
    "ISSUE_MISSING_DEPENDENCY",
    "ISSUE_REGISTRY_UNAVAILABLE",
    "ISSUE_TRUE_DATA_GAP",
    "ISSUE_VALUE_FILE_MISSING",
    "RESOLUTION_ADEQUATE_SURROGATE_RUNS",
    "FastProbeError",
    "InjectedRows",
    "ResolvedSliceHandles",
    "build_fast_probe_data_gap",
    "fast_probe",
    "run_label_shuffle_surrogate",
]
