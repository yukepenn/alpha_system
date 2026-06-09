"""Bounded-real worker-count benchmark for the V1 scaleout producer path.

The benchmark writes materialized values and temporary registries only under
``ALPHA_DATA_ROOT``. The committed artifact is the value-free Markdown summary.
"""

from __future__ import annotations

import argparse
import os
import re
import resource
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _path in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from alpha_system.features.scaleout import ScaleoutTarget, build_scaleout_units, load_scaleout_config
from alpha_system.features.scaleout.driver import (
    _ScaleoutLedger,
    _completed_record_has_registry_truth,
    _execute_stage,
    _resolve_worker_plan,
    _unit_executor_for_family,
)
from tools.feature_compute_fast_path.benchmark_gate import (
    BenchmarkWindow,
    _load_inputs,
    _validate_slice,
    blocked_summary,
)

SUMMARY_PATH = Path(
    "research/feature_compute_fast_path_v1/workers/worker_benchmark_summary.md"
)
DEFAULT_CONFIG_PATH = Path("configs/features/scaleout/base_ohlcv.json")
DEFAULT_WORKERS = (1, 2, 4, 8)
DEFAULT_DATASET_VERSION_ID = "dsv_databento_ohlcv_05404069799decb0"
DEFAULT_CANONICAL_SUBPATH = Path("databento/canonical/glbx_mdp3")
BENCHMARK_WINDOW = BenchmarkWindow()
_QUEUE_WAIT_RE = re.compile(r"registry_queue_wait_seconds=(?P<value>[0-9.]+)")


@dataclass(frozen=True, slots=True)
class WorkerRunResult:
    requested_workers: int
    effective_workers: int
    threads_per_worker: int
    elapsed_seconds: float
    rows_per_sec: float
    canonical_reads: int
    peak_memory_mb: float
    registry_queue_wait_seconds: float
    completed_units: int
    failed_units: int
    skipped_units: int
    content_hashes: tuple[str, ...]
    resolver_smoke_result: str
    parity_result: str
    deterministic_hashes: bool
    reductions: tuple[str, ...]

    @property
    def stable(self) -> bool:
        return (
            self.failed_units == 0
            and self.completed_units > 0
            and self.parity_result == "PASS"
            and self.resolver_smoke_result == "PASS"
            and self.deterministic_hashes
        )


def run_worker_benchmark(
    *,
    alpha_data_root: Path,
    summary_path: Path = SUMMARY_PATH,
    worker_counts: Sequence[int] = DEFAULT_WORKERS,
) -> tuple[WorkerRunResult, ...]:
    if not alpha_data_root.exists():
        _write_blocked(
            summary_path,
            f"ALPHA_DATA_ROOT is absent: {alpha_data_root.as_posix()}",
        )
        return ()
    canonical_root = alpha_data_root / DEFAULT_CANONICAL_SUBPATH
    if not canonical_root.exists():
        _write_blocked(
            summary_path,
            f"canonical root is absent: {canonical_root.as_posix()}",
        )
        return ()
    dataset_registry = alpha_data_root / "registry" / "datasets.sqlite"
    if not dataset_registry.exists():
        _write_blocked(
            summary_path,
            f"DatasetVersion registry is absent: {dataset_registry.as_posix()}",
        )
        return ()

    validation = _validate_slice(BENCHMARK_WINDOW, _load_inputs(canonical_root, BENCHMARK_WINDOW))
    generated_at = datetime.now(UTC)
    run_root = alpha_data_root / f"fcfp_p15_worker_benchmark_{generated_at:%Y%m%dT%H%M%SZ}"
    config = load_scaleout_config(DEFAULT_CONFIG_PATH)
    target = ScaleoutTarget(
        feature_ids=("returns",),
        symbols=("ES", "NQ", "RTY"),
        years=(2024,),
        dataset_version_ids=(DEFAULT_DATASET_VERSION_ID,),
    )
    reference_hashes = _reference_hashes(
        config=config,
        alpha_data_root=run_root / "reference",
        dataset_registry=dataset_registry,
        canonical_root=canonical_root,
        target=target,
    )
    baseline_hashes: tuple[str, ...] | None = None
    results: list[WorkerRunResult] = []
    for workers in worker_counts:
        result = _run_one_worker_count(
            config=config,
            alpha_data_root=run_root / f"workers_{workers}",
            dataset_registry=dataset_registry,
            canonical_root=canonical_root,
            target=target,
            workers=int(workers),
            reference_hashes=reference_hashes,
            baseline_hashes=baseline_hashes,
        )
        if baseline_hashes is None and result.failed_units == 0:
            baseline_hashes = result.content_hashes
        results.append(result)
    _write_summary(
        summary_path,
        results=tuple(results),
        generated_at=generated_at,
        alpha_data_root=alpha_data_root,
        canonical_root=canonical_root,
        run_root=run_root,
        validation=validation,
    )
    return tuple(results)


def _run_one_worker_count(
    *,
    config,
    alpha_data_root: Path,
    dataset_registry: Path,
    canonical_root: Path,
    target: ScaleoutTarget,
    workers: int,
    reference_hashes: tuple[str, ...],
    baseline_hashes: tuple[str, ...] | None,
) -> WorkerRunResult:
    logs: list[str] = []
    start = perf_counter()
    records = _run_benchmark_stage(
        config,
        alpha_data_root=alpha_data_root,
        dataset_registry=dataset_registry,
        canonical_root=canonical_root,
        target=target,
        engine="v1",
        workers=workers,
        log=logs.append,
    )
    elapsed = max(perf_counter() - start, 1e-12)
    rows = sum(record.row_count for record in records if record.status == "completed")
    hashes = tuple(
        sorted(
            str(record.content_hash)
            for record in records
            if record.status == "completed" and record.content_hash
        )
    )
    worker_plan = _resolve_worker_plan(
        workers,
        unit_count=len([record for record in records if record.status != "skipped"]),
        parallel_allowed=True,
    )
    deterministic = baseline_hashes is None or hashes == baseline_hashes
    parity = "PASS" if hashes == reference_hashes else "FAIL"
    resolver_smoke = (
        "PASS"
        if all(
            _completed_record_has_registry_truth(config, record, alpha_data_root, engine="v1")
            for record in records
            if record.status == "completed"
        )
        else "FAIL"
    )
    return WorkerRunResult(
        requested_workers=workers,
        effective_workers=worker_plan.effective_workers,
        threads_per_worker=worker_plan.threads_per_worker,
        elapsed_seconds=elapsed,
        rows_per_sec=rows / elapsed,
        canonical_reads=sum(1 for record in records if record.status == "completed"),
        peak_memory_mb=_peak_memory_mb(),
        registry_queue_wait_seconds=_registry_queue_wait(records),
        completed_units=sum(1 for record in records if record.status == "completed"),
        failed_units=sum(1 for record in records if record.status == "failed"),
        skipped_units=sum(1 for record in records if record.status == "skipped"),
        content_hashes=hashes,
        resolver_smoke_result=resolver_smoke,
        parity_result=parity,
        deterministic_hashes=deterministic,
        reductions=tuple(worker_plan.reductions) + tuple(logs),
    )


def _reference_hashes(
    *,
    config,
    alpha_data_root: Path,
    dataset_registry: Path,
    canonical_root: Path,
    target: ScaleoutTarget,
) -> tuple[str, ...]:
    records = _run_benchmark_stage(
        config,
        alpha_data_root=alpha_data_root,
        dataset_registry=dataset_registry,
        canonical_root=canonical_root,
        engine="reference",
        target=target,
        workers=1,
        log=None,
    )
    return tuple(
        sorted(
            str(record.content_hash)
            for record in records
            if record.status == "completed" and record.content_hash
        )
    )


def _run_benchmark_stage(
    config,
    *,
    alpha_data_root: Path,
    dataset_registry: Path,
    canonical_root: Path,
    target: ScaleoutTarget,
    engine: str,
    workers: int,
    log,
):
    units = _benchmark_units(config, target)
    return _execute_stage(
        config,
        units,
        stage="bounded_real",
        alpha_data_root=alpha_data_root,
        dataset_registry_path=dataset_registry,
        canonical_root=canonical_root,
        ledger=_ScaleoutLedger(alpha_data_root, config),
        executor=_unit_executor_for_family(config.family, engine=engine),
        engine=engine,
        requested_workers=workers,
        parallel_v1_compute=engine == "v1",
        log=log,
    )


def _benchmark_units(config, target: ScaleoutTarget):
    start = BENCHMARK_WINDOW.resolved_start_ts.isoformat()
    end = BENCHMARK_WINDOW.resolved_end_ts.isoformat()
    units = build_scaleout_units(config, target=target)
    narrowed = []
    for unit in units:
        if unit.year != BENCHMARK_WINDOW.year:
            continue
        # partition_id must be a safe path token (alphanumeric + underscore); the
        # driver's own partitions sanitize separators via _render_partition. Build
        # the benchmark partition the same way -- "ES_2024_12_worker_benchmark" --
        # rather than with dots/hyphens ("ES.2024-12..."), which the data-foundation
        # _normalize_id validator rejects ("partition_id must be an alphanumeric
        # identifier"), failing every benchmark unit before it can materialize.
        partition_id=(
            f"{unit.symbol}_{BENCHMARK_WINDOW.year}_"
            f"{BENCHMARK_WINDOW.month:02d}_worker_benchmark"
        )
        narrowed.append(
            replace(
                unit,
                partition_id=partition_id,
                window_start_ts=start,
                window_end_ts=end,
            )
        )
    return tuple(narrowed)


def _registry_queue_wait(records) -> float:
    total = 0.0
    for record in records:
        match = _QUEUE_WAIT_RE.search(record.message)
        if match:
            total += float(match.group("value"))
    return total


def _peak_memory_mb() -> float:
    usage = max(
        resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
    )
    return usage / 1024.0


def _write_blocked(path: Path, reason: str) -> None:
    payload = blocked_summary(_env_alpha_data_root_text(), reason)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# FCFP-P15 Worker Benchmark Summary",
                "",
                f"- Status: `{payload.status}`",
                f"- Blocked reason: {reason}",
                "- Value policy: value-free summary only; no values, Parquet, SQLite, or row-level data are included.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_summary(
    path: Path,
    *,
    results: tuple[WorkerRunResult, ...],
    generated_at: datetime,
    alpha_data_root: Path,
    canonical_root: Path,
    run_root: Path,
    validation,
) -> None:
    stable = tuple(result for result in results if result.stable)
    fastest = min(stable, key=lambda item: item.elapsed_seconds) if stable else None
    status = "COMPLETE" if fastest is not None else "BLOCKED"
    lines = [
        "# FCFP-P15 Worker Benchmark Summary",
        "",
        "- Campaign: `FEATURE_COMPUTE_FAST_PATH_V1`",
        "- Phase: `FCFP-P15`",
        f"- Status: `{status}`",
        f"- Generated at: `{generated_at.isoformat()}`",
        "- Value policy: value-free summary only; no feature values, label values, prices, Parquet payloads, SQLite content, or row-level data are included.",
        f"- Local-only benchmark root: `{run_root.as_posix()}`",
        f"- ALPHA_DATA_ROOT: `{alpha_data_root.as_posix()}`",
        f"- Canonical root: `{canonical_root.as_posix()}`",
        "",
        "## Slice Self-Validation",
        "",
        f"- Contract-roll events: `{validation.roll_event_count}`",
        f"- Session gaps observed: `{validation.session_gap_count}`",
        f"- Raw contract/id transitions observed: `{validation.raw_contract_transition_count}`",
        "",
        "## Results",
        "",
        "| Requested Workers | Effective Workers | Threads/Worker | Elapsed (s) | Rows/s | Canonical Reads | Peak Memory MB | Registry Queue Wait (s) | Resolver Smoke | Parity | Deterministic Hashes | Stable | Reductions |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- |",
    ]
    for result in results:
        lines.append(
            "| {requested} | {effective} | {threads} | {elapsed:.6f} | {rps:.2f} | {reads} | {mem:.2f} | {wait:.6f} | `{resolver}` | `{parity}` | `{det}` | `{stable}` | {reductions} |".format(
                requested=result.requested_workers,
                effective=result.effective_workers,
                threads=result.threads_per_worker,
                elapsed=result.elapsed_seconds,
                rps=result.rows_per_sec,
                reads=result.canonical_reads,
                mem=result.peak_memory_mb,
                wait=result.registry_queue_wait_seconds,
                resolver=result.resolver_smoke_result,
                parity=result.parity_result,
                det="yes" if result.deterministic_hashes else "no",
                stable="yes" if result.stable else "no",
                reductions=(
                    "`" + "; ".join(result.reductions) + "`"
                    if result.reductions
                    else "`none`"
                ),
            )
        )
    lines.extend(["", "## Chosen Stable Worker Count", ""])
    if fastest is None:
        lines.append("- No stable worker count was selected; see failed result rows above.")
    else:
        lines.extend(
            [
                f"- Fastest stable requested worker count: `{fastest.requested_workers}`",
                f"- Effective workers used: `{fastest.effective_workers}`",
                f"- Determinism evidence: content hashes matched the worker-1 baseline for all completed units.",
                f"- Parity evidence: V1 worker content hashes matched the reference-engine bounded units.",
                "- Registry evidence: every completed V1 unit resolved through registry truth after serial official registration.",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _env_alpha_data_root() -> Path | None:
    value = os.environ.get("ALPHA_DATA_ROOT")
    if not value:
        return None
    return Path(value).expanduser().resolve(strict=False)


def _env_alpha_data_root_text() -> str | None:
    root = _env_alpha_data_root()
    return root.as_posix() if root is not None else None


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--alpha-data-root")
    parser.add_argument("--summary-path", default=SUMMARY_PATH.as_posix())
    parser.add_argument("--workers", default=",".join(str(item) for item in DEFAULT_WORKERS))
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    alpha_data_root = (
        Path(args.alpha_data_root).expanduser().resolve(strict=False)
        if args.alpha_data_root
        else _env_alpha_data_root()
    )
    summary_path = Path(args.summary_path)
    if alpha_data_root is None:
        _write_blocked(summary_path, "ALPHA_DATA_ROOT is not set")
        print("BLOCKED: ALPHA_DATA_ROOT is not set")
        return 2
    worker_counts = tuple(
        int(item.strip()) for item in str(args.workers).split(",") if item.strip()
    )
    results = run_worker_benchmark(
        alpha_data_root=alpha_data_root,
        summary_path=summary_path,
        worker_counts=worker_counts,
    )
    if not results or not any(result.stable for result in results):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
