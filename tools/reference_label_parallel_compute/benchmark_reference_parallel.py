"""Bounded real benchmark for reference-label worker parallelism.

This module times the real scaleout label driver over a bounded cost_adjusted
unit grid. It writes only value-free markdown evidence; benchmark values,
registries, manifests, and checkpoints stay under the local data root.
"""

from __future__ import annotations

import argparse
import os
import resource
import sqlite3
from collections.abc import Callable, Iterable, Mapping, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from alpha_system.data.foundation.datasets import (
    DatasetAcceptanceState,
    resolve_dataset_acceptance_lock,
)
from alpha_system.data.foundation.rolls import (
    build_analytic_cme_equity_index_quarterly_roll_calendar,
)
from alpha_system.features.scaleout import ScaleoutTarget
from alpha_system.features.scaleout import driver as scaleout_driver

DEFAULT_ALPHA_DATA_ROOT = Path("~/alpha_data/alpha_system").expanduser()
DEFAULT_CONFIG = Path("configs/labels/scaleout/cost_adjusted.json")
DEFAULT_SUMMARY_OUT = Path(
    "research/reference_label_parallel_compute_v1/benchmark/benchmark_summary.md"
)
DEFAULT_WORKERS = (1, 2, 4, 8)
DEFAULT_INITIAL_SYMBOLS = ("ES",)
DEFAULT_INITIAL_YEARS = (2024,)
MIN_UNITS = 8
RELEASE_SPEEDUP_THRESHOLD = 3.0
BENCHMARK_NAMESPACE_PREFIX = "rlpc_p03_benchmark_"
CANONICAL_RELATIVE_ROOT = Path("databento") / "canonical" / "glbx_mdp3"
LABEL_REGISTRY_RELATIVE_PATH = Path("registry") / "labels.sqlite"
PRODUCTION_LABEL_VALUE_RELATIVE_PATH = Path("labels")
THREAD_CAP_ENV = {
    "POLARS_MAX_THREADS": "2",
    "OMP_NUM_THREADS": "2",
    "OPENBLAS_NUM_THREADS": "2",
    "NUMEXPR_MAX_THREADS": "2",
}
ELIGIBLE_ACCEPTANCE_STATES = {
    DatasetAcceptanceState.ACCEPTED.value,
    DatasetAcceptanceState.ACCEPTED_WITH_WARNINGS.value,
}


class BenchmarkError(ValueError):
    """Raised when the bounded real benchmark cannot proceed truthfully."""


class RealDataUnavailable(BenchmarkError):
    """Raised when a required local real-data path is absent."""


@dataclass(frozen=True, slots=True)
class CanonicalSliceEvidence:
    """Value-free facts read from canonical OHLCV files."""

    row_count: int
    session_gap_count: int
    max_gap_minutes: int
    raw_contract_transitions: int
    dataset_paths_checked: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SliceDefinition:
    """Self-validating bounded benchmark slice."""

    config_path: str
    family: str
    symbols: tuple[str, ...]
    years: tuple[int, ...]
    horizons: tuple[str, ...]
    label_ids: tuple[str, ...]
    unit_ids: tuple[str, ...]
    ohlcv_dataset_version_ids: tuple[str, ...]
    bbo_dataset_version_ids: tuple[str, ...]
    canonical_ohlcv_rows: int
    session_gap_count: int
    max_gap_minutes: int
    roll_event_count: int
    roll_event_dates: tuple[str, ...]
    raw_contract_transitions: int
    widened: bool = False

    @property
    def unit_count(self) -> int:
        return len(self.unit_ids)


@dataclass(frozen=True, slots=True)
class DeterminismResult:
    """Order-normalized equality result against the worker-1 baseline."""

    matches_baseline: bool
    record_count_matches: bool
    label_version_ids_match: bool
    content_hashes_match: bool
    row_counts_match: bool
    baseline_record_count: int
    compared_record_count: int

    @classmethod
    def baseline(cls, record_count: int) -> DeterminismResult:
        return cls(
            matches_baseline=True,
            record_count_matches=True,
            label_version_ids_match=True,
            content_hashes_match=True,
            row_counts_match=True,
            baseline_record_count=record_count,
            compared_record_count=record_count,
        )


@dataclass(slots=True)
class TimingProbe:
    """Parent-process timing wrapper around the real scaleout driver."""

    worker_stage_seconds: float = 0.0
    inline_compute_seconds: float = 0.0
    serial_registration_seconds: float = 0.0
    registration_calls: int = 0


@dataclass(frozen=True, slots=True)
class WorkerCellResult:
    """Value-free benchmark result for one requested worker count."""

    requested_workers: int
    effective_workers: int
    threads_per_worker: int
    elapsed_seconds: float
    units_per_second: float
    speedup_vs_1: float
    worker_compute_seconds: float
    serial_registration_seconds: float
    overhead_seconds: float
    peak_rss_mib: float
    registry_rows_before: int
    registry_rows_after: int
    registry_delta_rows: int
    completed_units: int
    failed_units: int
    skipped_units: int
    label_version_count: int
    total_row_count: int
    reductions: tuple[str, ...]
    determinism: DeterminismResult


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """Complete value-free benchmark output."""

    generated_at: str
    namespace_name: str
    namespace_pattern: str
    slice_definition: SliceDefinition
    cells: tuple[WorkerCellResult, ...]
    production_registry_rows_before: int
    production_registry_rows_after: int
    release_decision: str
    diagnosis: str
    driver_entrypoint: str

    @property
    def production_registry_delta_rows(self) -> int:
        return self.production_registry_rows_after - self.production_registry_rows_before


def resolve_real_driver() -> Callable[..., Any]:
    """Return the real scaleout driver entrypoint used by the harness."""

    return scaleout_driver.run_scaleout


def default_namespace_name(now: datetime | None = None) -> str:
    current = now or datetime.now(UTC)
    return BENCHMARK_NAMESPACE_PREFIX + current.strftime("%Y%m%dT%H%M%SZ")


def resolve_alpha_data_root(value: str | Path | None) -> Path:
    raw = value or os.environ.get("ALPHA_DATA_ROOT") or DEFAULT_ALPHA_DATA_ROOT
    return Path(raw).expanduser().resolve(strict=False)


def resolve_canonical_root(alpha_data_root: Path, value: str | Path | None) -> Path:
    if value is not None:
        return Path(value).expanduser().resolve(strict=False)
    return alpha_data_root / CANONICAL_RELATIVE_ROOT


def resolve_dataset_registry(alpha_data_root: Path, value: str | Path | None) -> Path:
    if value is not None:
        return Path(value).expanduser().resolve(strict=False)
    return alpha_data_root / "registry" / "datasets.sqlite"


def resolve_benchmark_root(alpha_data_root: Path, namespace: str | Path | None) -> Path:
    namespace_value = str(namespace) if namespace is not None else default_namespace_name()
    namespace_path = Path(namespace_value).expanduser()
    root = namespace_path if namespace_path.is_absolute() else alpha_data_root / namespace_path
    return root.resolve(strict=False)


def require_real_data_paths(
    *,
    alpha_data_root: Path,
    canonical_root: Path,
    dataset_registry_path: Path,
) -> None:
    missing = [
        path
        for path in (alpha_data_root, canonical_root, dataset_registry_path)
        if not path.exists()
    ]
    if missing:
        raise RealDataUnavailable(
            "required real data path is absent: "
            + ", ".join(path.as_posix() for path in missing)
        )


def skip_if_real_data_unavailable(
    *,
    alpha_data_root: Path,
    canonical_root: Path,
    dataset_registry_path: Path,
) -> None:
    """Pytest helper for optional real-data paths."""

    try:
        require_real_data_paths(
            alpha_data_root=alpha_data_root,
            canonical_root=canonical_root,
            dataset_registry_path=dataset_registry_path,
        )
    except RealDataUnavailable as exc:
        import pytest

        pytest.skip(str(exc))


def ensure_benchmark_namespace_is_isolated(
    *,
    alpha_data_root: Path,
    benchmark_root: Path,
) -> None:
    production_registry = alpha_data_root / LABEL_REGISTRY_RELATIVE_PATH
    production_values = alpha_data_root / PRODUCTION_LABEL_VALUE_RELATIVE_PATH
    root = benchmark_root.resolve(strict=False)
    forbidden = {
        alpha_data_root.resolve(strict=False),
        production_registry.resolve(strict=False),
        production_registry.parent.resolve(strict=False),
        production_values.resolve(strict=False),
    }
    if root in forbidden:
        raise BenchmarkError("benchmark namespace resolves to a production registry/value path")
    if root.name.startswith(BENCHMARK_NAMESPACE_PREFIX) is False:
        raise BenchmarkError(
            "benchmark namespace must start with "
            f"{BENCHMARK_NAMESPACE_PREFIX!r}: {root.name}"
        )
    benchmark_registry = root / "workers_1" / LABEL_REGISTRY_RELATIVE_PATH
    if benchmark_registry.resolve(strict=False) == production_registry.resolve(strict=False):
        raise BenchmarkError("benchmark registry path resolves to production labels.sqlite")


def assert_namespace_empty(benchmark_root: Path) -> None:
    if not benchmark_root.exists():
        return
    try:
        next(benchmark_root.iterdir())
    except StopIteration:
        return
    raise BenchmarkError(
        "benchmark namespace already contains files; choose a fresh "
        f"{BENCHMARK_NAMESPACE_PREFIX}<UTCSTAMP> namespace"
    )


def select_self_validating_slice(
    *,
    config: Any,
    config_path: Path,
    canonical_root: Path,
    dataset_registry_path: Path,
    initial_symbols: Sequence[str] = DEFAULT_INITIAL_SYMBOLS,
    initial_years: Sequence[int] = DEFAULT_INITIAL_YEARS,
    min_units: int = MIN_UNITS,
) -> tuple[ScaleoutTarget, SliceDefinition]:
    """Select the smallest configured slice that satisfies the real-data gate."""

    errors: list[str] = []
    candidates = _slice_candidates(config, initial_symbols=initial_symbols, initial_years=initial_years)
    for symbols, years, widened in candidates:
        target = ScaleoutTarget(symbols=tuple(symbols), years=tuple(years))
        units = scaleout_driver.build_scaleout_units(config, target=target)
        runnable = tuple(
            unit
            for unit in units
            if _unit_has_eligible_persisted_locks(unit, dataset_registry_path)
        )
        evidence = _canonical_slice_evidence(runnable, canonical_root)
        roll_dates = _roll_event_dates(symbols, years)
        definition = _slice_definition(
            config=config,
            config_path=config_path,
            units=runnable,
            evidence=evidence,
            roll_event_dates=roll_dates,
            widened=widened,
        )
        missing = validate_slice_definition(definition, min_units=min_units)
        if not missing:
            return target, definition
        errors.append(
            f"symbols={','.join(symbols)} years={','.join(str(y) for y in years)} "
            f"missing={'; '.join(missing)}"
        )
    raise BenchmarkError(
        "could not select a self-validating bounded cost_adjusted slice after widening: "
        + " | ".join(errors)
    )


def validate_slice_definition(
    definition: SliceDefinition,
    *,
    min_units: int = MIN_UNITS,
) -> tuple[str, ...]:
    missing: list[str] = []
    if definition.unit_count < min_units:
        missing.append(f"at least {min_units} runnable units required")
    if definition.roll_event_count < 1:
        missing.append("at least one contract-roll event is required")
    if definition.session_gap_count < 1:
        missing.append("at least one session/maintenance gap is required")
    return tuple(missing)


def run_benchmark(
    *,
    workers: Sequence[int] = DEFAULT_WORKERS,
    out: Path = DEFAULT_SUMMARY_OUT,
    alpha_data_root: Path | None = None,
    dataset_registry_path: Path | None = None,
    canonical_root: Path | None = None,
    benchmark_namespace: str | Path | None = None,
    config_path: Path = DEFAULT_CONFIG,
) -> BenchmarkResult:
    """Run the bounded real benchmark and write the value-free summary."""

    resolved_alpha_root = resolve_alpha_data_root(alpha_data_root)
    resolved_canonical = resolve_canonical_root(resolved_alpha_root, canonical_root)
    resolved_dataset_registry = resolve_dataset_registry(
        resolved_alpha_root, dataset_registry_path
    )
    require_real_data_paths(
        alpha_data_root=resolved_alpha_root,
        canonical_root=resolved_canonical,
        dataset_registry_path=resolved_dataset_registry,
    )
    benchmark_root = resolve_benchmark_root(resolved_alpha_root, benchmark_namespace)
    ensure_benchmark_namespace_is_isolated(
        alpha_data_root=resolved_alpha_root,
        benchmark_root=benchmark_root,
    )
    assert_namespace_empty(benchmark_root)

    config = scaleout_driver.load_scaleout_config(config_path)
    if config.family != "cost_adjusted":
        raise BenchmarkError("RLPC-P03 benchmark requires the cost_adjusted label config")
    target, slice_definition = select_self_validating_slice(
        config=config,
        config_path=config_path,
        canonical_root=resolved_canonical,
        dataset_registry_path=resolved_dataset_registry,
    )

    previous_env = _apply_thread_caps()
    production_registry = resolved_alpha_root / LABEL_REGISTRY_RELATIVE_PATH
    production_before = count_label_registry_rows(production_registry, read_only=True)
    baseline_records: tuple[tuple[object, ...], ...] | None = None
    baseline_units_per_second = 0.0
    cells: list[WorkerCellResult] = []
    try:
        for requested_workers in workers:
            cell_root = benchmark_root / f"workers_{requested_workers}"
            cell = _run_worker_cell(
                config=config,
                target=target,
                alpha_root=cell_root,
                dataset_registry_path=resolved_dataset_registry,
                canonical_root=resolved_canonical,
                requested_workers=int(requested_workers),
                baseline_records=baseline_records,
                baseline_units_per_second=baseline_units_per_second,
            )
            if baseline_records is None:
                baseline_records = _determinism_records_from_summary(cell.summary)
                baseline_units_per_second = cell.result.units_per_second
            cells.append(cell.result)
    finally:
        _restore_thread_caps(previous_env)
    production_after = count_label_registry_rows(production_registry, read_only=True)
    release_decision = release_decision_for_cells(cells)
    diagnosis = diagnosis_for_cells(cells)
    result = BenchmarkResult(
        generated_at=datetime.now(UTC).isoformat(),
        namespace_name=benchmark_root.name,
        namespace_pattern=f"$ALPHA_DATA_ROOT/{BENCHMARK_NAMESPACE_PREFIX}<UTCSTAMP>/workers_N",
        slice_definition=slice_definition,
        cells=tuple(cells),
        production_registry_rows_before=production_before,
        production_registry_rows_after=production_after,
        release_decision=release_decision,
        diagnosis=diagnosis,
        driver_entrypoint="alpha_system.features.scaleout.driver.run_scaleout",
    )
    if result.production_registry_delta_rows != 0:
        raise BenchmarkError(
            "production label registry row count changed during benchmark: "
            f"{result.production_registry_delta_rows}"
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_markdown(result), encoding="utf-8")
    return result


@dataclass(frozen=True, slots=True)
class _WorkerCell:
    result: WorkerCellResult
    summary: Any


def _run_worker_cell(
    *,
    config: Any,
    target: ScaleoutTarget,
    alpha_root: Path,
    dataset_registry_path: Path,
    canonical_root: Path,
    requested_workers: int,
    baseline_records: tuple[tuple[object, ...], ...] | None,
    baseline_units_per_second: float,
) -> _WorkerCell:
    logs: list[str] = []
    registry_path = alpha_root / LABEL_REGISTRY_RELATIVE_PATH
    registry_before = count_label_registry_rows(registry_path, read_only=False)
    timing = TimingProbe()
    start_rss = _peak_rss_mib()
    started = perf_counter()
    with _DriverTimingContext(timing):
        summary = resolve_real_driver()(
            config,
            alpha_data_root=alpha_root,
            dataset_registry_path=dataset_registry_path,
            canonical_root=canonical_root,
            rollout="bounded-real",
            execute=True,
            bounded_year=target.years[0] if len(target.years) == 1 else None,
            engine="reference",
            workers=requested_workers,
            target=target,
            log=logs.append,
        )
    elapsed = perf_counter() - started
    registry_after = count_label_registry_rows(registry_path, read_only=False)
    if summary.failed_count:
        messages = "; ".join(
            record.message for record in summary.records if record.status == "failed"
        )
        raise BenchmarkError(
            f"worker cell {requested_workers} failed {summary.failed_count} units: {messages}"
        )
    if summary.skipped_count:
        raise BenchmarkError(
            f"worker cell {requested_workers} skipped {summary.skipped_count} units; "
            "benchmark timings require fresh real computation"
        )
    completed = summary.completed_count
    if completed <= 0:
        raise BenchmarkError(f"worker cell {requested_workers} completed no units")
    units_per_second = completed / elapsed if elapsed > 0 else 0.0
    if baseline_records is None:
        determinism = DeterminismResult.baseline(completed)
        speedup = 1.0
    else:
        current_records = _determinism_records_from_summary(summary)
        determinism = compare_determinism_records(
            baseline_records=baseline_records,
            current_records=current_records,
        )
        speedup = units_per_second / baseline_units_per_second if baseline_units_per_second else 0.0
    worker_compute = (
        timing.worker_stage_seconds
        if summary.worker_plan.parallel_enabled
        else timing.inline_compute_seconds
    )
    registration = timing.serial_registration_seconds
    overhead = max(0.0, elapsed - worker_compute - registration)
    reductions = tuple(dict.fromkeys((*summary.worker_plan.reductions, *logs)))
    result = WorkerCellResult(
        requested_workers=requested_workers,
        effective_workers=summary.worker_plan.effective_workers,
        threads_per_worker=summary.worker_plan.threads_per_worker,
        elapsed_seconds=elapsed,
        units_per_second=units_per_second,
        speedup_vs_1=speedup,
        worker_compute_seconds=worker_compute,
        serial_registration_seconds=registration,
        overhead_seconds=overhead,
        peak_rss_mib=max(start_rss, _peak_rss_mib()),
        registry_rows_before=registry_before,
        registry_rows_after=registry_after,
        registry_delta_rows=registry_after - registry_before,
        completed_units=completed,
        failed_units=summary.failed_count,
        skipped_units=summary.skipped_count,
        label_version_count=sum(len(record.label_version_ids) for record in summary.records),
        total_row_count=sum(record.row_count for record in summary.records),
        reductions=reductions,
        determinism=determinism,
    )
    if not result.determinism.matches_baseline:
        raise BenchmarkError(
            f"determinism spot-check failed for requested workers={requested_workers}"
        )
    return _WorkerCell(result=result, summary=summary)


class _DriverTimingContext(AbstractContextManager["_DriverTimingContext"]):
    def __init__(self, timing: TimingProbe) -> None:
        self._timing = timing
        self._original_stage = scaleout_driver._compute_reference_label_stage_outputs_in_workers
        self._original_compute = scaleout_driver._compute_reference_label_unit_output
        self._original_register = scaleout_driver._register_reference_label_worker_output

    def __enter__(self) -> _DriverTimingContext:
        timing = self._timing
        original_stage = self._original_stage
        original_compute = self._original_compute
        original_register = self._original_register

        def timed_stage(*args: Any, **kwargs: Any) -> Any:
            started = perf_counter()
            try:
                return original_stage(*args, **kwargs)
            finally:
                timing.worker_stage_seconds += perf_counter() - started

        def timed_compute(*args: Any, **kwargs: Any) -> Any:
            started = perf_counter()
            try:
                return original_compute(*args, **kwargs)
            finally:
                timing.inline_compute_seconds += perf_counter() - started

        def timed_register(*args: Any, **kwargs: Any) -> Any:
            started = perf_counter()
            try:
                return original_register(*args, **kwargs)
            finally:
                timing.serial_registration_seconds += perf_counter() - started
                timing.registration_calls += 1

        scaleout_driver._compute_reference_label_stage_outputs_in_workers = timed_stage
        scaleout_driver._compute_reference_label_unit_output = timed_compute
        scaleout_driver._register_reference_label_worker_output = timed_register
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> bool:
        scaleout_driver._compute_reference_label_stage_outputs_in_workers = self._original_stage
        scaleout_driver._compute_reference_label_unit_output = self._original_compute
        scaleout_driver._register_reference_label_worker_output = self._original_register
        return False


def _determinism_records_from_summary(summary: Any) -> tuple[tuple[object, ...], ...]:
    records = []
    for record in summary.records:
        if record.status != "completed":
            continue
        records.append(
            (
                record.unit.unit_id,
                record.unit.symbol,
                record.unit.year,
                record.unit.horizon,
                tuple(record.label_version_ids),
                record.content_hash,
                record.row_count,
            )
        )
    return tuple(sorted(records))


def compare_determinism_records(
    *,
    baseline_records: tuple[tuple[object, ...], ...],
    current_records: tuple[tuple[object, ...], ...],
) -> DeterminismResult:
    record_count_matches = len(baseline_records) == len(current_records)
    label_version_ids_match = tuple(item[:5] for item in baseline_records) == tuple(
        item[:5] for item in current_records
    )
    content_hashes_match = tuple(item[5] for item in baseline_records) == tuple(
        item[5] for item in current_records
    )
    row_counts_match = tuple(item[6] for item in baseline_records) == tuple(
        item[6] for item in current_records
    )
    matches = (
        record_count_matches
        and label_version_ids_match
        and content_hashes_match
        and row_counts_match
    )
    return DeterminismResult(
        matches_baseline=matches,
        record_count_matches=record_count_matches,
        label_version_ids_match=label_version_ids_match,
        content_hashes_match=content_hashes_match,
        row_counts_match=row_counts_match,
        baseline_record_count=len(baseline_records),
        compared_record_count=len(current_records),
    )


def release_decision_for_cells(cells: Sequence[WorkerCellResult]) -> str:
    cell_8 = next((cell for cell in cells if cell.requested_workers == 8), None)
    if cell_8 is not None and cell_8.speedup_vs_1 >= RELEASE_SPEEDUP_THRESHOLD:
        return "RELEASED: workers=8"
    return "NOT_RELEASED"


def diagnosis_for_cells(cells: Sequence[WorkerCellResult]) -> str:
    cell_8 = next((cell for cell in cells if cell.requested_workers == 8), None)
    if cell_8 is None:
        return "workers=8 cell missing; release threshold cannot be evaluated"
    if cell_8.speedup_vs_1 >= RELEASE_SPEEDUP_THRESHOLD:
        return "8-worker throughput met the >=3.0x release threshold on the bounded grid."
    registration_share = (
        cell_8.serial_registration_seconds / cell_8.elapsed_seconds
        if cell_8.elapsed_seconds > 0
        else 0.0
    )
    compute_share = (
        cell_8.worker_compute_seconds / cell_8.elapsed_seconds
        if cell_8.elapsed_seconds > 0
        else 0.0
    )
    if registration_share >= 0.35:
        reason = "serial registration ceiling"
    elif compute_share >= 0.65:
        reason = "worker compute/IO bound"
    else:
        reason = "process orchestration and fixed overhead"
    return (
        f"{reason}: workers=8 speedup was {cell_8.speedup_vs_1:.2f}x, below "
        f"the {RELEASE_SPEEDUP_THRESHOLD:.1f}x gate; backlog section 6 option 2 remains "
        "the recorded escalation."
    )


def render_markdown(result: BenchmarkResult) -> str:
    decision_lines = [f"Release decision: {result.release_decision}"]
    lines = [
        "# RLPC-P03 Reference Label Parallel Benchmark Summary",
        "",
        "Value-free benchmark summary. It contains no label values, market prices,",
        "canonical rows, Parquet payloads, SQLite content, provider responses,",
        "logs, or run artifacts.",
        "",
        f"- Campaign: `REFERENCE_LABEL_PARALLEL_COMPUTE_V1`",
        f"- Phase: `RLPC-P03`",
        f"- Generated at: `{result.generated_at}`",
        f"- Driver entrypoint: `{result.driver_entrypoint}`",
        f"- Benchmark namespace: `{result.namespace_pattern}`",
        f"- Local namespace name: `{result.namespace_name}`",
        f"- Production registry row delta: `{result.production_registry_delta_rows}`",
        "- Rollout timed: `bounded-real` only; full-window timing occurred: `false`",
        "- Thread cap env per cell: `POLARS_MAX_THREADS=2 OMP_NUM_THREADS=2 "
        "OPENBLAS_NUM_THREADS=2 NUMEXPR_MAX_THREADS=2`",
        "",
        "## Slice Definition",
        "",
        f"- Config: `{result.slice_definition.config_path}`",
        f"- Family: `{result.slice_definition.family}`",
        f"- Symbols: `{', '.join(result.slice_definition.symbols)}`",
        f"- Years: `{', '.join(str(year) for year in result.slice_definition.years)}`",
        f"- Horizons: `{', '.join(result.slice_definition.horizons)}`",
        f"- Label ids: `{', '.join(result.slice_definition.label_ids)}`",
        f"- Runnable units: `{result.slice_definition.unit_count}`",
        f"- Unit ids: `{', '.join(result.slice_definition.unit_ids)}`",
        f"- OHLCV DatasetVersions: `{', '.join(result.slice_definition.ohlcv_dataset_version_ids)}`",
        f"- BBO DatasetVersions: `{', '.join(result.slice_definition.bbo_dataset_version_ids)}`",
        f"- Canonical OHLCV rows inspected: `{result.slice_definition.canonical_ohlcv_rows}`",
        f"- Analytic CME roll events in selected year(s): `{result.slice_definition.roll_event_count}`",
        f"- Roll event dates: `{', '.join(result.slice_definition.roll_event_dates)}`",
        f"- Raw contract/id transitions observed in canonical rows: `{result.slice_definition.raw_contract_transitions}`",
        f"- Session/maintenance gaps observed: `{result.slice_definition.session_gap_count}`",
        f"- Max timestamp gap minutes: `{result.slice_definition.max_gap_minutes}`",
        f"- Slice widened from initial ES/2024: `{str(result.slice_definition.widened).lower()}`",
        "",
        "Roll self-validation uses the configured analytic CME equity-index quarterly",
        "roll calendar because these canonical front-continuous rows keep stable",
        "contract_id/instrument_id identifiers; timestamp gaps are measured directly",
        "from canonical OHLCV rows.",
        "",
        "## Worker Sweep",
        "",
        "| Requested | Effective | Driver Plan Threads/Worker | Elapsed (s) | Units/s | Speedup vs 1 | Worker Compute (s) | Serial Registration (s) | Overhead (s) | Peak RSS MiB | Registry Delta | Completed | Label Versions | Rows | Determinism |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for cell in result.cells:
        lines.append(
            "| "
            + " | ".join(
                (
                    str(cell.requested_workers),
                    str(cell.effective_workers),
                    str(cell.threads_per_worker),
                    f"{cell.elapsed_seconds:.6f}",
                    f"{cell.units_per_second:.4f}",
                    f"{cell.speedup_vs_1:.2f}",
                    f"{cell.worker_compute_seconds:.6f}",
                    f"{cell.serial_registration_seconds:.6f}",
                    f"{cell.overhead_seconds:.6f}",
                    f"{cell.peak_rss_mib:.2f}",
                    str(cell.registry_delta_rows),
                    str(cell.completed_units),
                    str(cell.label_version_count),
                    str(cell.total_row_count),
                    "PASS" if cell.determinism.matches_baseline else "FAIL",
                )
            )
            + " |"
        )
        for reduction in cell.reductions:
            lines.append(
                f"- Requested `{cell.requested_workers}` worker reduction/log: `{reduction}`"
            )
    lines.extend(
        [
            "",
            "## Determinism Spot-Check",
            "",
            "| Requested | Record Count Match | label_version_id Match | Content Hash Match | Row Count Match | Compared Records |",
            "| ---: | --- | --- | --- | --- | ---: |",
        ]
    )
    for cell in result.cells:
        det = cell.determinism
        lines.append(
            "| "
            + " | ".join(
                (
                    str(cell.requested_workers),
                    "yes" if det.record_count_matches else "no",
                    "yes" if det.label_version_ids_match else "no",
                    "yes" if det.content_hashes_match else "no",
                    "yes" if det.row_counts_match else "no",
                    str(det.compared_record_count),
                )
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Release Gate",
            "",
            decision_lines[0],
            "",
            f"Diagnosis: {result.diagnosis}",
            "",
            "Speedup is wall-clock units/sec at requested workers=N divided by",
            "wall-clock units/sec for requested workers=1 on the same bounded unit grid.",
        ]
    )
    return "\n".join(lines) + "\n"


def count_label_registry_rows(registry_path: Path, *, read_only: bool) -> int:
    if not registry_path.exists():
        return 0
    if read_only:
        uri = f"file:{registry_path.as_posix()}?mode=ro"
        connection = sqlite3.connect(uri, uri=True)
    else:
        connection = sqlite3.connect(registry_path)
    try:
        row = connection.execute(
            "SELECT COUNT(*) FROM label_registry_records"
        ).fetchone()
    except sqlite3.Error:
        return 0
    finally:
        connection.close()
    return int(row[0]) if row is not None else 0


def _slice_candidates(
    config: Any,
    *,
    initial_symbols: Sequence[str],
    initial_years: Sequence[int],
) -> Iterable[tuple[tuple[str, ...], tuple[int, ...], bool]]:
    symbols = tuple(symbol for symbol in initial_symbols if symbol in config.symbols)
    years = tuple(year for year in initial_years if year in config.years)
    if symbols and years:
        yield symbols, years[:1], False
    all_symbols = tuple(config.symbols)
    accepted_years = tuple(year for year in config.years if year >= 2019)
    if years:
        yield all_symbols, years[:1], True
    for year in accepted_years:
        if symbols:
            yield symbols, (year,), True
        yield all_symbols, (year,), True


def _unit_has_eligible_persisted_locks(unit: Any, dataset_registry_path: Path) -> bool:
    for dataset in unit.input_datasets:
        lock = resolve_dataset_acceptance_lock(
            dataset_registry_path, dataset.dataset_version_id
        )
        if lock is None or lock.state.value not in ELIGIBLE_ACCEPTANCE_STATES:
            return False
    return True


def _canonical_slice_evidence(
    units: Sequence[Any],
    canonical_root: Path,
) -> CanonicalSliceEvidence:
    datasets = {
        (dataset.schema_id, dataset.dataset_version_id, unit.symbol)
        for unit in units
        for dataset in unit.input_datasets
        if dataset.schema_id == "ohlcv_1m"
    }
    row_count = 0
    gap_count = 0
    max_gap = 0
    transitions = 0
    checked: list[str] = []
    for schema_id, dataset_version_id, symbol in sorted(datasets):
        path = canonical_root / dataset_version_id / f"schema={schema_id}" / f"root={symbol}" / "part-00000.parquet"
        if not path.exists():
            raise RealDataUnavailable(f"canonical OHLCV slice path is absent: {path}")
        checked.append(
            f"{dataset_version_id}/schema={schema_id}/root={symbol}/part-00000.parquet"
        )
        stats = _ohlcv_gap_and_roll_stats(path)
        row_count += stats.row_count
        gap_count += stats.session_gap_count
        max_gap = max(max_gap, stats.max_gap_minutes)
        transitions += stats.raw_contract_transitions
    return CanonicalSliceEvidence(
        row_count=row_count,
        session_gap_count=gap_count,
        max_gap_minutes=max_gap,
        raw_contract_transitions=transitions,
        dataset_paths_checked=tuple(checked),
    )


def _ohlcv_gap_and_roll_stats(path: Path) -> CanonicalSliceEvidence:
    try:
        import polars as pl
    except ImportError as exc:
        raise RealDataUnavailable("polars is required to inspect canonical Parquet") from exc
    lazy = pl.scan_parquet(path).select(["bar_start_ts", "contract_id"])
    data = lazy.select(
        [
            pl.len().alias("row_count"),
            (
                pl.col("bar_start_ts")
                .str.to_datetime(format="%Y-%m-%dT%H:%M:%S%z", strict=False)
                .diff()
                .dt.total_minutes()
                .gt(1)
                .sum()
            ).alias("session_gap_count"),
            (
                pl.col("bar_start_ts")
                .str.to_datetime(format="%Y-%m-%dT%H:%M:%S%z", strict=False)
                .diff()
                .dt.total_minutes()
                .max()
            ).alias("max_gap_minutes"),
            (
                (pl.col("contract_id") != pl.col("contract_id").shift(1))
                .fill_null(False)
                .sum()
            ).alias("raw_contract_transitions"),
        ]
    ).collect()
    row = data.to_dicts()[0]
    return CanonicalSliceEvidence(
        row_count=int(row["row_count"] or 0),
        session_gap_count=int(row["session_gap_count"] or 0),
        max_gap_minutes=int(row["max_gap_minutes"] or 0),
        raw_contract_transitions=int(row["raw_contract_transitions"] or 0),
        dataset_paths_checked=(path.name,),
    )


def _roll_event_dates(symbols: Sequence[str], years: Sequence[int]) -> tuple[str, ...]:
    if not symbols or not years:
        return ()
    records = build_analytic_cme_equity_index_quarterly_roll_calendar(
        root_symbols=tuple(symbols),
        start_year=min(years),
        end_year=max(years),
    )
    selected_years = set(years)
    dates = sorted(
        {
            record.roll_date.isoformat()
            for record in records
            if record.roll_date.year in selected_years
        }
    )
    return tuple(dates)


def _slice_definition(
    *,
    config: Any,
    config_path: Path,
    units: Sequence[Any],
    evidence: CanonicalSliceEvidence,
    roll_event_dates: tuple[str, ...],
    widened: bool,
) -> SliceDefinition:
    ohlcv_ids = sorted(
        {
            dataset.dataset_version_id
            for unit in units
            for dataset in unit.input_datasets
            if dataset.schema_id == "ohlcv_1m"
        }
    )
    bbo_ids = sorted(
        {
            dataset.dataset_version_id
            for unit in units
            for dataset in unit.input_datasets
            if dataset.schema_id == "bbo_1m"
        }
    )
    return SliceDefinition(
        config_path=config_path.as_posix(),
        family=config.family,
        symbols=tuple(sorted({unit.symbol for unit in units})),
        years=tuple(sorted({unit.year for unit in units})),
        horizons=tuple(sorted({unit.horizon for unit in units}, key=_horizon_sort_key)),
        label_ids=tuple(config.label_names),
        unit_ids=tuple(unit.unit_id for unit in units),
        ohlcv_dataset_version_ids=tuple(ohlcv_ids),
        bbo_dataset_version_ids=tuple(bbo_ids),
        canonical_ohlcv_rows=evidence.row_count,
        session_gap_count=evidence.session_gap_count,
        max_gap_minutes=evidence.max_gap_minutes,
        roll_event_count=len(roll_event_dates),
        roll_event_dates=roll_event_dates,
        raw_contract_transitions=evidence.raw_contract_transitions,
        widened=widened,
    )


def _horizon_sort_key(value: str) -> tuple[int, str]:
    if value.endswith("m") and value[:-1].isdigit():
        return (int(value[:-1]), value)
    return (10_000, value)


def _apply_thread_caps() -> dict[str, str | None]:
    previous = {name: os.environ.get(name) for name in THREAD_CAP_ENV}
    os.environ.update(THREAD_CAP_ENV)
    return previous


def _restore_thread_caps(previous: Mapping[str, str | None]) -> None:
    for name, value in previous.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value


def _peak_rss_mib() -> float:
    parent = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    children = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    # Linux reports ru_maxrss in KiB.
    return max(parent, children) / 1024.0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the RLPC-P03 bounded real reference-label worker benchmark."
    )
    parser.add_argument("--workers", nargs="+", type=int, default=list(DEFAULT_WORKERS))
    parser.add_argument("--out", type=Path, default=DEFAULT_SUMMARY_OUT)
    parser.add_argument("--alpha-data-root", type=Path, default=None)
    parser.add_argument("--dataset-registry", type=Path, default=None)
    parser.add_argument("--canonical-root", type=Path, default=None)
    parser.add_argument(
        "--benchmark-namespace",
        default=None,
        help=(
            "Namespace name or absolute path. Must start with "
            f"{BENCHMARK_NAMESPACE_PREFIX!r}; defaults to a UTC-stamped namespace."
        ),
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = run_benchmark(
            workers=tuple(args.workers),
            out=args.out,
            alpha_data_root=args.alpha_data_root,
            dataset_registry_path=args.dataset_registry,
            canonical_root=args.canonical_root,
            benchmark_namespace=args.benchmark_namespace,
            config_path=args.config,
        )
    except BenchmarkError as exc:
        print(f"benchmark error: {exc}")
        return 2
    print(f"wrote {args.out}")
    print(f"Release decision: {result.release_decision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
