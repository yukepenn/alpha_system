"""LCFP-P08 bounded-real benchmark and readiness gate.

The gate times the P01 reference benchmark on the bounded slice, executes the
real V1 fast-label materializer and serial registry writer on isolated local
data roots, confirms strict resolver smoke, and writes only value-free summary
fields to the repository.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import resource
import sqlite3
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from alpha_system.core.hashing import hash_config
from alpha_system.features.input_views import BBOInputView, OHLCVInputView
from alpha_system.features.scaleout import ScaleoutTarget, build_scaleout_units, load_scaleout_config
from alpha_system.features.scaleout.driver import (
    SCALEOUT_ENGINE_V1,
    ScaleoutConfig,
    ScaleoutUnit,
    _compute_fast_label_stage_outputs_in_workers,
    _compute_fast_label_unit_output,
    _fast_label_definitions_for_unit,
    _fast_label_result_with_records,
    _register_fast_label_worker_output,
    _resolve_worker_plan,
    reset_fast_label_materializer_caches,
)
from alpha_system.labels.fast import FAST_LABEL_PRODUCER_ENGINE_ID, FAST_LABEL_VALUE_SCHEMA_VERSION
from alpha_system.labels.families.cost_adjusted import (
    CostAdjustedLabelDefinition,
    compute_cost_adjusted_label,
)
from alpha_system.labels.families.fixed_horizon import (
    FixedHorizonLabelDefinition,
    compute_fixed_horizon_label,
)
from alpha_system.labels.families.path import PathLabelDefinition, compute_path_label
from alpha_system.labels.registry import LabelRegistry
from alpha_system.labels.version import LabelValueRecord

from tools.label_compute_fast_path import baseline_benchmark as p01

CAMPAIGN_ID = "LABEL_COMPUTE_FAST_PATH_V1"
PHASE_ID = "LCFP-P08"
SUMMARY_PATH = Path("research/label_compute_fast_path_v1/benchmark/benchmark_summary.md")
DEFAULT_CANONICAL_RELATIVE_ROOT = Path("databento") / "canonical" / "glbx_mdp3"
DEFAULT_SYMBOL = "ES"
DEFAULT_YEAR = 2024
DEFAULT_START_TS = "2024-06-01T00:00:00+00:00"
DEFAULT_END_TS = "2024-07-01T00:00:00+00:00"
WORKER_COUNTS = (1, 2, 4, 8)

# Amended LCFP-P08 done-criterion (2026-06-10): the production engine is
# selected PER FAMILY — fast where measured materially faster, reference where
# the reference engine remains faster (both engines are parity-gated, so
# correctness is engine-independent). Only the path family — the campaign's
# motivating reference bottleneck — keeps a hard speed block.
ENGINE_FAST = "fast"
ENGINE_REFERENCE = "reference"
ENGINE_BLOCKED = "blocked"
PATH_FAMILY = "path"
MATERIAL_SPEEDUP_FLOOR = 1.0

FAMILY_CONFIGS: Mapping[str, str] = {
    "fixed_base": "configs/labels/scaleout/fixed_horizon.json",
    "fixed_extended": "configs/labels/scaleout/extended_horizon.json",
    "close_out": "configs/labels/scaleout/session_close_maintenance_flat.json",
    "cost_adjusted": "configs/labels/scaleout/cost_adjusted.json",
    "path": "configs/labels/scaleout/path.json",
}
P01_BASELINE_ROWS_PER_SEC: Mapping[str, float] = {
    "fixed_base": 35030.81,
    "fixed_extended": 37631.52,
    "close_out": 34676.09,
    "cost_adjusted": 85957.67,
    "path": 11108.42,
}
P01_REQUIRED_DEFINITIONS: Mapping[str, int] = {
    "fixed_base": 6,
    "fixed_extended": 3,
    "close_out": 2,
    "cost_adjusted": 18,
    "path": 28,
}
REQUIRED_REPORT_FIELDS = (
    "elapsed",
    "rows_per_sec",
    "canonical_reads_per_symbol_year",
    "labels_per_read",
    "file_counts",
    "registry_deltas",
    "full_accepted_window_runtime_estimate",
    "speedup_vs_reference",
    "selected_production_worker_policy",
)


class BenchmarkGateError(ValueError):
    """Raised when the benchmark gate cannot produce a complete result."""


class ParityError(AssertionError):
    """Raised when real-slice reference and fast label records diverge."""


@dataclass(frozen=True, slots=True)
class BenchmarkWindow:
    """Bounded real slice identity."""

    symbol: str = DEFAULT_SYMBOL
    year: int = DEFAULT_YEAR
    start_ts: str = DEFAULT_START_TS
    end_ts: str = DEFAULT_END_TS

    @property
    def token(self) -> str:
        start = self.start_ts[:7].replace("-", "")
        return f"{self.symbol.upper()}_{start}"


@dataclass(frozen=True, slots=True)
class SliceValidation:
    """Value-free slice self-validation."""

    ohlcv_dataset_version_id: str
    bbo_dataset_version_id: str
    ohlcv_row_count: int
    bbo_row_count: int
    roll_event_count: int
    maintenance_gap_count: int

    def to_dict(self) -> dict[str, int | str]:
        return {
            "ohlcv_dataset_version_id": self.ohlcv_dataset_version_id,
            "bbo_dataset_version_id": self.bbo_dataset_version_id,
            "ohlcv_row_count": self.ohlcv_row_count,
            "bbo_row_count": self.bbo_row_count,
            "roll_event_count": self.roll_event_count,
            "maintenance_gap_count": self.maintenance_gap_count,
        }


@dataclass(frozen=True, slots=True)
class CoverageCheck:
    """Current production wiring coverage against the P01 baseline surface."""

    family: str
    required_definition_count: int
    production_definition_count: int
    production_unit_count: int

    @property
    def status(self) -> str:
        if self.production_definition_count == self.required_definition_count:
            return "PASS"
        return "BLOCKED_PRODUCTION_WIRING"

    def to_dict(self) -> dict[str, int | str]:
        return {
            "family": self.family,
            "required_definition_count": self.required_definition_count,
            "production_definition_count": self.production_definition_count,
            "production_unit_count": self.production_unit_count,
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class WorkerResult:
    """Value-free result for one family at one requested worker count.

    Component timing contract (LCFP-P08 repair): the fast path's timed window
    is split into three explicitly reported components —

    - ``fast_compute_seconds``: the fast producer stage only (panel load,
      vectorized compute, and the unit's Parquet value-store write).
    - ``registration_seconds``: serial keystone registry writes.
    - ``parity_seconds``: parity confirmation, which re-runs the full per-row
      reference engine per definition. It is a correctness gate, not a
      fast-path cost, and never enters the throughput numbers.

    ``rows_per_second`` and ``speedup_vs_reference`` come from
    ``fast_compute_seconds`` against the same-process reference rerun on the
    same rows and definitions (compute vs compute). ``elapsed_seconds`` is the
    total wall window across all three components, reported for transparency.
    """

    family: str
    requested_workers: int
    effective_workers: int
    threads_per_worker: int
    elapsed_seconds: float
    fast_compute_seconds: float
    registration_seconds: float
    parity_seconds: float
    label_row_evaluations: int
    records_emitted: int
    rows_per_second: float
    reference_rows_per_second: float
    canonical_reads_per_symbol_year: float
    labels_per_read: float
    file_count: int
    registry_delta: int
    full_window_runtime_estimate_seconds: float
    speedup_vs_reference: float
    resolver_smoke: str
    parity_result: str
    peak_memory_kib: int | None
    worker_reductions: tuple[str, ...]

    def required_report_fields(self, selected_policy: str) -> dict[str, object]:
        return {
            "elapsed": self.elapsed_seconds,
            "rows_per_sec": self.rows_per_second,
            "canonical_reads_per_symbol_year": self.canonical_reads_per_symbol_year,
            "labels_per_read": self.labels_per_read,
            "file_counts": self.file_count,
            "registry_deltas": self.registry_delta,
            "full_accepted_window_runtime_estimate": (
                self.full_window_runtime_estimate_seconds
            ),
            "speedup_vs_reference": self.speedup_vs_reference,
            "selected_production_worker_policy": selected_policy,
        }

    def to_dict(self) -> dict[str, float | int | str | list[str] | None]:
        return {
            "family": self.family,
            "requested_workers": self.requested_workers,
            "effective_workers": self.effective_workers,
            "threads_per_worker": self.threads_per_worker,
            "elapsed_seconds": self.elapsed_seconds,
            "fast_compute_seconds": self.fast_compute_seconds,
            "registration_seconds": self.registration_seconds,
            "parity_seconds": self.parity_seconds,
            "reference_rows_per_second": self.reference_rows_per_second,
            "label_row_evaluations": self.label_row_evaluations,
            "records_emitted": self.records_emitted,
            "rows_per_second": self.rows_per_second,
            "canonical_reads_per_symbol_year": self.canonical_reads_per_symbol_year,
            "labels_per_read": self.labels_per_read,
            "file_count": self.file_count,
            "registry_delta": self.registry_delta,
            "full_window_runtime_estimate_seconds": (
                self.full_window_runtime_estimate_seconds
            ),
            "speedup_vs_reference": self.speedup_vs_reference,
            "resolver_smoke": self.resolver_smoke,
            "parity_result": self.parity_result,
            "peak_memory_kib": self.peak_memory_kib,
            "worker_reductions": list(self.worker_reductions),
        }


@dataclass(frozen=True, slots=True)
class FamilyBenchmark:
    """All worker-count results for one family."""

    family: str
    coverage: CoverageCheck
    results: tuple[WorkerResult, ...]

    @property
    def selected_result(self) -> WorkerResult:
        candidates = [result for result in self.results if result.parity_result == "PASS"]
        if not candidates:
            raise BenchmarkGateError(f"family {self.family} has no passing worker result")
        return max(candidates, key=lambda result: (result.rows_per_second, result.effective_workers))


@dataclass(frozen=True, slots=True)
class ProductionWorkerPolicy:
    """Selected worker policy for downstream reruns."""

    requested_workers: int
    effective_workers_observed: int
    thread_control: Mapping[str, str]
    rationale: str
    status: str

    def to_dict(self) -> dict[str, object]:
        return {
            "requested_workers": self.requested_workers,
            "effective_workers_observed": self.effective_workers_observed,
            "thread_control": dict(self.thread_control),
            "rationale": self.rationale,
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class FamilyEnginePolicy:
    """Per-family production engine + worker selection (amended LCFP-P08).

    ``selected_engine`` is ``fast`` when the family's best passing worker cell
    measured a fast_compute speedup materially above 1.0x, ``reference`` when
    the reference engine remains faster (honest component timings carried in
    the rationale), and ``blocked`` when no worker cell passed parity and
    resolver smoke so no selection can be released.
    """

    family: str
    selected_engine: str
    requested_workers: int | None
    effective_workers: int | None
    measured_speedup: float | None
    rationale: str

    def to_dict(self) -> dict[str, object]:
        return {
            "family": self.family,
            "selected_engine": self.selected_engine,
            "requested_workers": self.requested_workers,
            "effective_workers": self.effective_workers,
            "measured_speedup": self.measured_speedup,
            "rationale": self.rationale,
        }


@dataclass(frozen=True, slots=True)
class BenchmarkPayload:
    """Complete value-free P08 benchmark payload."""

    status: str
    generated_at: datetime
    window: BenchmarkWindow
    slice_validation: SliceValidation
    reference_results: tuple[p01.BenchmarkResult, ...]
    families: tuple[FamilyBenchmark, ...]
    selected_policy: ProductionWorkerPolicy
    scratch_root_name: str
    family_policies: tuple[FamilyEnginePolicy, ...] = ()
    blocked_reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "alpha_system.label_compute_fast_path.benchmark_gate.v1",
            "campaign_id": CAMPAIGN_ID,
            "phase_id": PHASE_ID,
            "status": self.status,
            "generated_at": self.generated_at.isoformat(),
            "window": {
                "symbol": self.window.symbol.upper(),
                "year": self.window.year,
                "start_ts": self.window.start_ts,
                "end_ts": self.window.end_ts,
            },
            "slice_validation": self.slice_validation.to_dict(),
            "reference_results": [result.to_dict() for result in self.reference_results],
            "families": [
                {
                    "family": family.family,
                    "coverage": family.coverage.to_dict(),
                    "results": [result.to_dict() for result in family.results],
                }
                for family in self.families
            ],
            "selected_policy": self.selected_policy.to_dict(),
            "family_policies": [policy.to_dict() for policy in self.family_policies],
            "scratch_root_name": self.scratch_root_name,
            "blocked_reasons": list(self.blocked_reasons),
        }


def validate_slice_self_coverage(
    *,
    roll_event_count: int,
    maintenance_gap_count: int,
) -> None:
    """Fail closed unless the slice contains roll and session/maintenance gaps."""

    if roll_event_count < 1:
        raise BenchmarkGateError(
            "bounded benchmark slice contains no contract-roll event; widen the slice"
        )
    if maintenance_gap_count < 1:
        raise BenchmarkGateError(
            "bounded benchmark slice contains no session/maintenance gap; widen the slice"
        )


def extrapolate_runtime_seconds(full_window_rows: int, rows_per_sec: float) -> float:
    """Estimate full-window runtime from measured bounded throughput."""

    if full_window_rows < 0:
        raise BenchmarkGateError("full_window_rows must be non-negative")
    if rows_per_sec <= 0 or not math.isfinite(rows_per_sec):
        raise BenchmarkGateError("rows_per_sec must be positive and finite")
    return full_window_rows / rows_per_sec


def validate_report_fields(fields: Mapping[str, object]) -> None:
    """Assert required value-free report fields are present."""

    missing = tuple(field for field in REQUIRED_REPORT_FIELDS if field not in fields)
    if missing:
        raise BenchmarkGateError("benchmark report missing fields: " + ", ".join(missing))


def _best_passing_result(family: FamilyBenchmark) -> WorkerResult | None:
    """Best stable worker cell: parity + resolver smoke passed, highest rows/sec."""

    candidates = [
        result
        for result in family.results
        if result.parity_result == "PASS" and result.resolver_smoke.startswith("PASS")
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda result: (result.rows_per_second, result.effective_workers))


def select_family_engine_policies(
    families: tuple[FamilyBenchmark, ...],
) -> tuple[FamilyEnginePolicy, ...]:
    """Select the production engine + worker policy per family (amended LCFP-P08)."""

    policies: list[FamilyEnginePolicy] = []
    for family in families:
        best = _best_passing_result(family)
        if best is None:
            policies.append(
                FamilyEnginePolicy(
                    family=family.family,
                    selected_engine=ENGINE_BLOCKED,
                    requested_workers=None,
                    effective_workers=None,
                    measured_speedup=None,
                    rationale=(
                        "no worker cell passed parity confirmation and resolver "
                        "smoke; no engine selection is released for this family"
                    ),
                )
            )
        elif best.speedup_vs_reference > MATERIAL_SPEEDUP_FLOOR:
            policies.append(
                FamilyEnginePolicy(
                    family=family.family,
                    selected_engine=ENGINE_FAST,
                    requested_workers=best.requested_workers,
                    effective_workers=best.effective_workers,
                    measured_speedup=best.speedup_vs_reference,
                    rationale=(
                        f"fast compute measured {best.speedup_vs_reference:.2f}x the "
                        "same-process reference rerun at "
                        f"requested_workers={best.requested_workers} "
                        f"(effective {best.effective_workers}); materially faster "
                        "than 1.00x, so the parity-gated fast engine is selected"
                    ),
                )
            )
        else:
            policies.append(
                FamilyEnginePolicy(
                    family=family.family,
                    selected_engine=ENGINE_REFERENCE,
                    requested_workers=None,
                    effective_workers=None,
                    measured_speedup=best.speedup_vs_reference,
                    rationale=(
                        "best passing fast cell measured "
                        f"{best.speedup_vs_reference:.2f}x (<= 1.00x) at "
                        f"requested_workers={best.requested_workers}; component "
                        f"timings: fast_compute={best.fast_compute_seconds:.6f}s, "
                        f"registration={best.registration_seconds:.6f}s, "
                        f"parity={best.parity_seconds:.6f}s; the reference engine "
                        "remains faster and stays selected (both engines are "
                        "parity-gated, so correctness is engine-independent)"
                    ),
                )
            )
    return tuple(policies)


def evaluate_gate_status(
    policies: tuple[FamilyEnginePolicy, ...],
    *,
    blocked_reasons: Sequence[str] = (),
) -> tuple[str, tuple[str, ...]]:
    """Determine the gate status from per-family policies and wiring blocks.

    Hard blocks (status != COMPLETE): production wiring/coverage gaps, any
    family without a parity+resolver-passing cell, and a path family that is
    not measured materially faster than the reference (the campaign's
    motivating bottleneck). Cheap families at or below 1.0x do NOT block; per
    the amended LCFP-P08 criterion they become documented reference-engine
    selections.
    """

    reasons = list(blocked_reasons)
    if reasons:
        return "BLOCKED_PRODUCTION_WIRING", tuple(reasons)
    unselected = tuple(
        policy.family for policy in policies if policy.selected_engine == ENGINE_BLOCKED
    )
    if unselected:
        reasons.append(
            "no engine selection could be released (parity/resolver did not pass) "
            "for: " + ", ".join(f"`{family}`" for family in unselected)
        )
        return "BLOCKED_PRODUCTION_WIRING", tuple(reasons)
    path_policy = next(
        (policy for policy in policies if policy.family == PATH_FAMILY), None
    )
    if path_policy is None or path_policy.selected_engine != ENGINE_FAST:
        measured = (
            "no measurement"
            if path_policy is None or path_policy.measured_speedup is None
            else f"{path_policy.measured_speedup:.2f}x"
        )
        reasons.append(
            f"`{PATH_FAMILY}` (the campaign's motivating reference bottleneck) was "
            f"not measured materially faster on the fast path ({measured} <= "
            "1.00x); the amended LCFP-P08 criterion keeps this a hard block."
        )
        return "BLOCKED_SPEEDUP", tuple(reasons)
    return "COMPLETE", tuple(reasons)


def render_summary_markdown(payload: BenchmarkPayload) -> str:
    """Render the value-free benchmark/readiness summary."""

    lines = [
        "# LCFP-P08 Benchmark + Readiness Summary",
        "",
        f"- Campaign: `{CAMPAIGN_ID}`",
        f"- Phase: `{PHASE_ID}`",
        f"- Status: `{payload.status}`",
        f"- Generated at: `{payload.generated_at.isoformat()}`",
        "- Value policy: value-free summary only; no label values, market prices, "
        "Parquet payloads, SQLite content, or row-level records are included.",
        "- Reference timing: bounded P01 reference runner only; no full-window "
        "reference timing occurred.",
        f"- Benchmark scratch root name: `{payload.scratch_root_name}` "
        "(local-only under `ALPHA_DATA_ROOT`).",
        "",
        "## Bounded Slice",
        "",
        f"- Symbol: `{payload.window.symbol.upper()}`",
        f"- Year: `{payload.window.year}`",
        f"- Window: `{payload.window.start_ts}` to `{payload.window.end_ts}`",
        f"- OHLCV DatasetVersion: `{payload.slice_validation.ohlcv_dataset_version_id}`",
        f"- BBO DatasetVersion: `{payload.slice_validation.bbo_dataset_version_id}`",
        f"- OHLCV rows loaded: `{payload.slice_validation.ohlcv_row_count}`",
        f"- BBO rows loaded: `{payload.slice_validation.bbo_row_count}`",
        f"- Contract-roll events asserted: `{payload.slice_validation.roll_event_count}`",
        "- Session/maintenance gaps asserted: "
        f"`{payload.slice_validation.maintenance_gap_count}`",
    ]
    if payload.blocked_reasons:
        lines.extend(["", "## Readiness Blocks", ""])
        for reason in payload.blocked_reasons:
            lines.append(f"- {reason}")

    lines.extend(
        [
            "",
            "## Coverage",
            "",
            "| Family | Required P01 Definitions | Production Definitions | Units | Status |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )
    for family in payload.families:
        coverage = family.coverage
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{coverage.family}`",
                    str(coverage.required_definition_count),
                    str(coverage.production_definition_count),
                    str(coverage.production_unit_count),
                    f"`{coverage.status}`",
                )
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Timing Methodology",
            "",
            "- The fast path's window is decomposed into three explicitly "
            "reported components: `fast_compute` (panel load + vectorized "
            "compute + the unit's Parquet value-store write), `registration` "
            "(serial keystone registry writes, including hydrating worker "
            "Parquet records), and `parity` (parity confirmation, which "
            "re-runs the full per-row reference engine per definition).",
            "- `rows/sec` and `speedup` use `fast_compute` only, against the "
            "same-process reference rerun on the same rows and definitions "
            "(compute vs compute). Parity confirmation is a correctness gate "
            "and never enters the throughput numbers.",
            "- The reference rows/sec denominator is the bounded rerun in this "
            "process (same machine, same slice); the committed P01 baseline "
            "rows/sec is shown alongside for context only.",
            "- Asymmetry disclosed: the reference denominator times pure "
            "compute over pre-built input views, while `fast_compute` "
            "additionally includes the fast path's canonical panel load, "
            "input adaptation, and Parquet value-store write. The asymmetry "
            "biases against the fast path, never for it. Each "
            "(family, worker-count) cell starts with cold panel caches; "
            "panel-load amortization is measured within a cell only.",
            "",
            "## Reference Baseline Rerun",
            "",
            "| Family | Definitions | Elapsed (s) | Rows/sec | "
            "P01 Committed Rows/sec | Records Emitted |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for result in payload.reference_results:
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{result.family}`",
                    str(result.definitions),
                    f"{result.elapsed_seconds:.6f}",
                    f"{result.rows_per_second:.2f}",
                    f"{P01_BASELINE_ROWS_PER_SEC.get(result.family, 0.0):.2f}",
                    str(result.records_emitted),
                )
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Worker Sweep",
            "",
            "Component timings are disclosed per cell; `Speedup` = fast compute "
            "rows/sec / reference rerun rows/sec (same rows).",
            "",
            "| Family | Requested | Effective | Threads/Worker | Compute (s) | "
            "Registration (s) | Parity (s) | Total (s) | Rows/sec | "
            "Files | Registry Delta | Speedup | Full-Window Estimate (s) | "
            "Resolver | Parity | Peak RSS KiB |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: "
            "| ---: | ---: | ---: | ---: | --- | --- | ---: |",
        ]
    )
    selected_policy_text = f"requested_workers={payload.selected_policy.requested_workers}"
    for family in payload.families:
        for result in family.results:
            validate_report_fields(result.required_report_fields(selected_policy_text))
            lines.append(
                "| "
                + " | ".join(
                    (
                        f"`{result.family}`",
                        str(result.requested_workers),
                        str(result.effective_workers),
                        str(result.threads_per_worker),
                        f"{result.fast_compute_seconds:.6f}",
                        f"{result.registration_seconds:.6f}",
                        f"{result.parity_seconds:.6f}",
                        f"{result.elapsed_seconds:.6f}",
                        f"{result.rows_per_second:.2f}",
                        str(result.file_count),
                        str(result.registry_delta),
                        f"{result.speedup_vs_reference:.2f}",
                        f"{result.full_window_runtime_estimate_seconds:.2f}",
                        f"`{result.resolver_smoke}`",
                        f"`{result.parity_result}`",
                        str(result.peak_memory_kib or ""),
                    )
                )
                + " |"
            )
            if result.worker_reductions:
                lines.append(
                    f"- `{result.family}` requested `{result.requested_workers}` worker "
                    "reduction: "
                    + "; ".join(result.worker_reductions)
                )

    blocked = payload.status != "COMPLETE"
    lines.extend(
        [
            "",
            "## Production Engine + Worker Policy",
            "",
            "Per-family selection per the amended LCFP-P08 criterion: `fast` "
            "where measured materially faster (best passing fast_compute "
            "speedup > 1.0x), `reference` where the reference engine remains "
            "faster (honest component timings in the rationale). Both engines "
            "are parity-gated, so correctness is engine-independent.",
            "",
        ]
    )
    if blocked:
        lines.extend(
            [
                f"- NOT RELEASED: gate status is `{payload.status}`; no engine "
                "or worker policy is released for downstream use until the "
                "block is cleared.",
                "",
            ]
        )
    lines.extend(
        [
            "| Family | Selected Engine | Workers | Measured Speedup | Rationale |",
            "| --- | --- | ---: | ---: | --- |",
        ]
    )
    for policy in payload.family_policies:
        workers = (
            str(policy.requested_workers) if policy.requested_workers is not None else "n/a"
        )
        speedup = (
            f"{policy.measured_speedup:.2f}" if policy.measured_speedup is not None else "n/a"
        )
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{policy.family}`",
                    f"`{policy.selected_engine}`",
                    workers,
                    speedup,
                    policy.rationale,
                )
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Production Worker Policy",
            "",
            f"- Status: `{payload.selected_policy.status}`",
            f"- Selected requested workers: `{payload.selected_policy.requested_workers}`",
            "- Effective workers observed at selection: "
            f"`{payload.selected_policy.effective_workers_observed}`",
            "- Thread controls: "
            + ", ".join(
                f"`{key}={value}`" for key, value in payload.selected_policy.thread_control.items()
            ),
            f"- Rationale: {payload.selected_policy.rationale}",
        ]
    )
    if blocked:
        lines.append(
            f"- NOT RELEASED: gate status is `{payload.status}`; this worker "
            "policy is not released for downstream use until the block is "
            "cleared."
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Speedup is a measured engineering throughput claim only. This summary "
            "does not make any alpha, profitability, tradability, broker, paper, "
            "live, or deployment claim.",
            "",
        ]
    )
    return "\n".join(lines)


def run_benchmark(
    *,
    alpha_data_root: Path,
    canonical_root: Path,
    dataset_registry_path: Path,
    summary_path: Path = SUMMARY_PATH,
    benchmark_root: Path | None = None,
    window: BenchmarkWindow = BenchmarkWindow(),
    worker_counts: Sequence[int] = WORKER_COUNTS,
) -> BenchmarkPayload:
    """Run the bounded-real gate and write the value-free summary."""

    alpha_data_root = alpha_data_root.expanduser().resolve(strict=False)
    canonical_root = canonical_root.expanduser().resolve(strict=False)
    dataset_registry_path = dataset_registry_path.expanduser().resolve(strict=False)
    if not alpha_data_root.exists():
        raise BenchmarkGateError(f"ALPHA_DATA_ROOT is absent: {alpha_data_root}")
    if not canonical_root.exists():
        raise BenchmarkGateError(f"canonical root is absent: {canonical_root}")
    if not dataset_registry_path.exists():
        raise BenchmarkGateError(f"dataset registry is absent: {dataset_registry_path}")

    inventory = p01._load_dataset_inventory(p01.DATASET_INVENTORY_PATH)
    ohlcv_dataset_id = p01._dataset_id(inventory, schema="ohlcv_1m", year=window.year)
    bbo_dataset_id = p01._dataset_id(inventory, schema="bbo_1m", year=window.year)
    ohlcv_mappings = p01.load_canonical_ohlcv_rows(
        canonical_root=canonical_root,
        dataset_version_id=ohlcv_dataset_id,
        symbol=window.symbol,
        start_ts=window.start_ts,
        end_ts=window.end_ts,
        partition_schema="ohlcv_1m",
    )
    bbo_mappings = p01.load_canonical_bbo_rows(
        canonical_root=canonical_root,
        dataset_version_id=bbo_dataset_id,
        symbol=window.symbol,
        start_ts=window.start_ts,
        end_ts=window.end_ts,
        partition_schema="bbo_1m",
    )
    ohlcv_view = OHLCVInputView(tuple(p01._ohlcv_input_row(row) for row in ohlcv_mappings))
    bbo_view = BBOInputView(tuple(p01._bbo_input_row(row) for row in bbo_mappings))
    validation = SliceValidation(
        ohlcv_dataset_version_id=ohlcv_dataset_id,
        bbo_dataset_version_id=bbo_dataset_id,
        ohlcv_row_count=len(ohlcv_view.rows),
        bbo_row_count=len(bbo_view.rows),
        roll_event_count=p01._roll_event_count(window.symbol, window.start_ts, window.end_ts),
        maintenance_gap_count=p01._maintenance_gap_count(ohlcv_view.rows),
    )
    validate_slice_self_coverage(
        roll_event_count=validation.roll_event_count,
        maintenance_gap_count=validation.maintenance_gap_count,
    )

    reference_summary = p01.run_benchmark(
        alpha_data_root=alpha_data_root,
        canonical_root=canonical_root,
        symbol=window.symbol,
        year=window.year,
        start_ts=window.start_ts,
        end_ts=window.end_ts,
        families=("all",),
    )
    root = benchmark_root or _default_benchmark_root(alpha_data_root)
    root.mkdir(parents=True, exist_ok=False)

    reference_rows_per_second = {
        result.family: result.rows_per_second for result in reference_summary.results
    }
    family_results: list[FamilyBenchmark] = []
    blocked_reasons: list[str] = []
    for family, config_path in FAMILY_CONFIGS.items():
        config = load_scaleout_config(config_path)
        units = _benchmark_units(config, window)
        coverage = _coverage_check(family, config, units)
        if coverage.status != "PASS":
            blocked_reasons.append(
                f"`{family}` production wiring exposes "
                f"{coverage.production_definition_count}/"
                f"{coverage.required_definition_count} P01 baseline definitions."
            )
        family_worker_results: list[WorkerResult] = []
        for workers in worker_counts:
            try:
                family_worker_results.append(
                    _run_worker_count(
                        family=family,
                        config=config,
                        units=units,
                        requested_workers=workers,
                        alpha_data_root=root / family / f"workers_{workers}",
                        dataset_registry_path=dataset_registry_path,
                        canonical_root=canonical_root,
                        ohlcv_view=ohlcv_view,
                        bbo_view=bbo_view,
                        slice_row_count=_slice_row_count_for_family(family, validation),
                        reference_rows_per_second=reference_rows_per_second.get(family, 0.0),
                    )
                )
            except Exception as exc:  # noqa: BLE001 - benchmark records the gate failure.
                blocked_reasons.append(
                    f"`{family}` worker `{workers}` failed through the real fast runner: {exc}"
                )
                family_worker_results.append(
                    _blocked_worker_result(
                        family=family,
                        config=config,
                        units=units,
                        requested_workers=workers,
                        slice_row_count=_slice_row_count_for_family(family, validation),
                        reference_rows_per_second=reference_rows_per_second.get(family, 0.0),
                    )
                )
        results = tuple(family_worker_results)
        family_results.append(FamilyBenchmark(family=family, coverage=coverage, results=results))

    family_policies = select_family_engine_policies(tuple(family_results))
    status, blocked_reason_tuple = evaluate_gate_status(
        family_policies, blocked_reasons=blocked_reasons
    )
    selected_policy = _select_worker_policy(
        tuple(family_results), blocked=status != "COMPLETE"
    )

    payload = BenchmarkPayload(
        status=status,
        generated_at=datetime.now(UTC),
        window=window,
        slice_validation=validation,
        reference_results=reference_summary.results,
        families=tuple(family_results),
        selected_policy=selected_policy,
        scratch_root_name=root.name,
        family_policies=family_policies,
        blocked_reasons=blocked_reason_tuple,
    )
    _write_summary(summary_path, payload)
    return payload


def _default_benchmark_root(alpha_data_root: Path) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return alpha_data_root / f"lcfp_p08_benchmark_{stamp}"


def _benchmark_units(config: ScaleoutConfig, window: BenchmarkWindow) -> tuple[ScaleoutUnit, ...]:
    units = build_scaleout_units(
        config,
        target=ScaleoutTarget(symbols=(window.symbol.upper(),), years=(window.year,)),
    )
    if not units:
        raise BenchmarkGateError(f"no production units selected for {config.family}")
    converted: list[ScaleoutUnit] = []
    for unit in units:
        identity = hash_config(
            {
                "source_unit_id": unit.unit_id,
                "window_start_ts": window.start_ts,
                "window_end_ts": window.end_ts,
                "phase_id": PHASE_ID,
            }
        )[:24]
        converted.append(
            replace(
                unit,
                unit_id=f"mbu_lcfp_p08_{identity}",
                partition_id=f"{unit.partition_id}_lcfp_p08_{window.token.lower()}",
                window_start_ts=window.start_ts,
                window_end_ts=window.end_ts,
                feature_set_version=f"{unit.feature_set_version}_lcfp_p08_{window.token.lower()}",
            )
        )
    return tuple(converted)


def _coverage_check(
    family: str,
    config: ScaleoutConfig,
    units: Sequence[ScaleoutUnit],
) -> CoverageCheck:
    production_definitions = sum(len(_fast_label_definitions_for_unit(config, unit)) for unit in units)
    return CoverageCheck(
        family=family,
        required_definition_count=P01_REQUIRED_DEFINITIONS[family],
        production_definition_count=production_definitions,
        production_unit_count=len(units),
    )


def _run_worker_count(
    *,
    family: str,
    config: ScaleoutConfig,
    units: tuple[ScaleoutUnit, ...],
    requested_workers: int,
    alpha_data_root: Path,
    dataset_registry_path: Path,
    canonical_root: Path,
    ohlcv_view: OHLCVInputView,
    bbo_view: BBOInputView,
    slice_row_count: int,
    reference_rows_per_second: float,
) -> WorkerResult:
    """Run one (family, worker-count) cell with separated component timing.

    Three explicit windows: fast COMPUTE (producer stage incl. the unit
    Parquet value-store write), serial REGISTRATION, and PARITY confirmation
    (which re-runs the full reference engine and must never contaminate the
    fast throughput claim — LCFP-P08 reviewer finding 5).
    """

    alpha_data_root.mkdir(parents=True, exist_ok=False)
    # Each (family, worker-count) cell starts cold: cross-cell panel reuse
    # would silently flatter later cells. Amortization is measured only
    # within a cell, which is the production-relevant claim.
    reset_fast_label_materializer_caches()
    registry = LabelRegistry.from_alpha_data_root(alpha_data_root)
    before_count = len(registry.read_label_records())
    worker_plan = _resolve_worker_plan(
        requested_workers,
        unit_count=len(units),
        parallel_allowed=True,
    )
    start_rss = _peak_rss_kib()
    records_emitted = 0
    parquet_paths: set[str] = set()
    label_version_ids: list[str] = []
    parity_stats: list[str] = []

    # Component 1: fast COMPUTE only.
    compute_started = perf_counter()
    outputs: dict[str, Any] = {}
    if worker_plan.parallel_enabled:
        worker_outputs = _compute_fast_label_stage_outputs_in_workers(
            config,
            units,
            alpha_data_root=alpha_data_root,
            dataset_registry_path=dataset_registry_path,
            canonical_root=canonical_root,
            worker_plan=worker_plan,
            force_recompute=True,
        )
        for unit in units:
            output = worker_outputs[unit.unit_id]
            if isinstance(output, BaseException):
                raise BenchmarkGateError(f"{family}/{unit.unit_id} failed: {output}") from output
            outputs[unit.unit_id] = output
    else:
        for unit in units:
            outputs[unit.unit_id] = _compute_fast_label_unit_output(
                config,
                unit,
                alpha_data_root,
                dataset_registry_path,
                canonical_root,
                write_manifest=False,
                include_records=True,
            )
    fast_compute_seconds = perf_counter() - compute_started

    # Component 2: serial keystone registration (includes hydrating worker
    # Parquet records back into memory once for registration + parity reuse).
    registration_started = perf_counter()
    for unit in units:
        output = outputs[unit.unit_id]
        output = replace(
            output,
            materialization_result=_fast_label_result_with_records(
                output.materialization_result
            ),
        )
        outputs[unit.unit_id] = output
        _register_fast_label_worker_output(
            config,
            unit,
            alpha_data_root=alpha_data_root,
            output=output,
        )
        records_emitted += output.materialization_result.record_count
        _collect_output_paths(output.materialization_result, parquet_paths)
        label_version_ids.extend(output.pack.label_version_ids)
    registration_seconds = perf_counter() - registration_started

    # Component 3: parity confirmation (reference re-run; correctness gate).
    parity_started = perf_counter()
    for unit in units:
        output = outputs[unit.unit_id]
        parity_stats.extend(
            _confirm_unit_parity(
                config,
                unit,
                output.materialization_result.records,
                ohlcv_view=ohlcv_view,
                bbo_view=bbo_view,
            )
        )
    parity_seconds = perf_counter() - parity_started

    elapsed = fast_compute_seconds + registration_seconds + parity_seconds
    registry = LabelRegistry.from_alpha_data_root(alpha_data_root)
    after_records = registry.read_label_records()
    resolver_status = _resolver_smoke(registry, tuple(label_version_ids))
    label_evaluations = slice_row_count * sum(
        len(_fast_label_definitions_for_unit(config, unit)) for unit in units
    )
    rows_per_second = (
        label_evaluations / fast_compute_seconds if fast_compute_seconds > 0 else 0.0
    )
    speedup = (
        rows_per_second / reference_rows_per_second if reference_rows_per_second > 0 else 0.0
    )
    peak_rss = _peak_rss_kib()
    return WorkerResult(
        family=family,
        requested_workers=requested_workers,
        effective_workers=worker_plan.effective_workers,
        threads_per_worker=worker_plan.threads_per_worker,
        elapsed_seconds=elapsed,
        fast_compute_seconds=fast_compute_seconds,
        registration_seconds=registration_seconds,
        parity_seconds=parity_seconds,
        label_row_evaluations=label_evaluations,
        records_emitted=records_emitted,
        rows_per_second=rows_per_second,
        reference_rows_per_second=reference_rows_per_second,
        canonical_reads_per_symbol_year=float(len(units)),
        labels_per_read=(
            sum(len(_fast_label_definitions_for_unit(config, unit)) for unit in units)
            / max(len(units), 1)
        ),
        file_count=len(parquet_paths),
        registry_delta=len(after_records) - before_count,
        full_window_runtime_estimate_seconds=extrapolate_runtime_seconds(
            p01._full_window_basis(family),
            rows_per_second,
        ),
        speedup_vs_reference=speedup,
        resolver_smoke=resolver_status,
        parity_result="PASS" if parity_stats else "NOT_RUN",
        peak_memory_kib=max(start_rss, peak_rss) if peak_rss is not None else None,
        worker_reductions=tuple(worker_plan.reductions),
    )


def _blocked_worker_result(
    *,
    family: str,
    config: ScaleoutConfig,
    units: tuple[ScaleoutUnit, ...],
    requested_workers: int,
    slice_row_count: int,
    reference_rows_per_second: float = 0.0,
) -> WorkerResult:
    worker_plan = _resolve_worker_plan(
        requested_workers,
        unit_count=len(units),
        parallel_allowed=True,
    )
    definition_count = sum(len(_fast_label_definitions_for_unit(config, unit)) for unit in units)
    return WorkerResult(
        family=family,
        requested_workers=requested_workers,
        effective_workers=worker_plan.effective_workers,
        threads_per_worker=worker_plan.threads_per_worker,
        elapsed_seconds=0.0,
        fast_compute_seconds=0.0,
        registration_seconds=0.0,
        parity_seconds=0.0,
        reference_rows_per_second=reference_rows_per_second,
        label_row_evaluations=slice_row_count * definition_count,
        records_emitted=0,
        rows_per_second=0.0,
        canonical_reads_per_symbol_year=float(len(units)),
        labels_per_read=definition_count / max(len(units), 1),
        file_count=0,
        registry_delta=0,
        full_window_runtime_estimate_seconds=0.0,
        speedup_vs_reference=0.0,
        resolver_smoke="NOT_RUN",
        parity_result="BLOCKED",
        peak_memory_kib=_peak_rss_kib(),
        worker_reductions=tuple(worker_plan.reductions),
    )


def _collect_output_paths(result: Any, paths: set[str]) -> None:
    handle = result.value_store_handle
    if handle is not None and handle.parquet_path:
        paths.add(str(handle.parquet_path))


def _confirm_unit_parity(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    fast_records: tuple[LabelValueRecord, ...],
    *,
    ohlcv_view: OHLCVInputView,
    bbo_view: BBOInputView,
) -> tuple[str, ...]:
    from tests.unit.feature_compute_fast_path.parity_harness import (
        LabelParityTolerance,
        assert_and_summarize_label_records_match,
    )

    fast_by_version: dict[str, list[LabelValueRecord]] = defaultdict(list)
    for record in fast_records:
        fast_by_version[record.label_version_id].append(record)
    stats: list[str] = []
    tolerance = (
        LabelParityTolerance(
            abs=1e-12,
            rel=1e-12,
            reason="Decimal reference arithmetic is compared to float shared-panel arithmetic",
        )
        if config.family in {"cost_adjusted", "path"}
        else LabelParityTolerance()
    )
    for definition in _fast_label_definitions_for_unit(config, unit):
        reference_records = _reference_records(definition, ohlcv_view=ohlcv_view, bbo_view=bbo_view)
        expected_label_version_id = definition.version.label_version_id
        reference_keys = {
            (record.label_version_id, record.entity_id, record.event_ts)
            for record in reference_records
        }
        fast_keys = {
            (record.label_version_id, record.entity_id, record.event_ts)
            for record in fast_by_version[expected_label_version_id]
        }
        if reference_keys != fast_keys:
            raise ParityError(
                f"{config.family}/{unit.unit_id}/{expected_label_version_id}: "
                f"missing_fast_records={len(reference_keys - fast_keys)} "
                f"extra_fast_records={len(fast_keys - reference_keys)}"
            )
        try:
            summary = assert_and_summarize_label_records_match(
                reference_records,
                tuple(fast_by_version[expected_label_version_id]),
                expected_label_version_id=expected_label_version_id,
                tolerance=tolerance,
            )
        except AssertionError as exc:
            raise ParityError(
                f"{config.family}/{unit.unit_id}/{expected_label_version_id}: {exc}"
            ) from exc
        stats.append(
            f"{expected_label_version_id}:{summary.record_count}:"
            f"{summary.max_abs_diff:.3g}"
        )
    return tuple(stats)


def _reference_records(
    definition: FixedHorizonLabelDefinition | CostAdjustedLabelDefinition | PathLabelDefinition,
    *,
    ohlcv_view: OHLCVInputView,
    bbo_view: BBOInputView,
) -> tuple[LabelValueRecord, ...]:
    if isinstance(definition, FixedHorizonLabelDefinition):
        return tuple(compute_fixed_horizon_label(definition, ohlcv_view))
    if isinstance(definition, CostAdjustedLabelDefinition):
        return tuple(compute_cost_adjusted_label(definition, bbo_view, trade_rows=ohlcv_view.rows))
    if isinstance(definition, PathLabelDefinition):
        return tuple(compute_path_label(definition, ohlcv_view))
    raise BenchmarkGateError(f"unsupported label definition: {type(definition).__name__}")


def _resolver_smoke(registry: LabelRegistry, label_version_ids: tuple[str, ...]) -> str:
    unique_ids = tuple(dict.fromkeys(label_version_ids))
    for label_version_id in unique_ids:
        record = registry.resolve_label_by_version(label_version_id)
        if record is None:
            raise BenchmarkGateError(f"resolver did not find {label_version_id}")
        if record.producer_engine_id != FAST_LABEL_PRODUCER_ENGINE_ID:
            raise BenchmarkGateError("resolved label has non-fast producer provenance")
        if record.value_schema_version != FAST_LABEL_VALUE_SCHEMA_VERSION:
            raise BenchmarkGateError("resolved label has unexpected value schema")
    if registry.resolve_label_by_version("lver_" + "0" * 64) is not None:
        raise BenchmarkGateError("resolver did not fail closed on missing strict id")
    return f"PASS {len(unique_ids)}/{len(unique_ids)}"


def _slice_row_count_for_family(family: str, validation: SliceValidation) -> int:
    if family == "cost_adjusted":
        return validation.bbo_row_count
    return validation.ohlcv_row_count


def _select_worker_policy(
    families: tuple[FamilyBenchmark, ...],
    *,
    blocked: bool,
) -> ProductionWorkerPolicy:
    by_requested: dict[int, list[WorkerResult]] = defaultdict(list)
    for family in families:
        for result in family.results:
            by_requested[result.requested_workers].append(result)
    passing_by_requested = {
        workers: [
            result
            for result in results
            if result.parity_result == "PASS" and result.resolver_smoke.startswith("PASS")
        ]
        for workers, results in by_requested.items()
    }
    passing_by_requested = {
        workers: results for workers, results in passing_by_requested.items() if results
    }
    if not passing_by_requested:
        raise BenchmarkGateError("no worker count completed resolver and parity checks")
    best_workers = max(
        passing_by_requested,
        key=lambda workers: (
            sum(result.rows_per_second for result in passing_by_requested[workers]),
            -workers,
        ),
    )
    representative = max(
        passing_by_requested[best_workers],
        key=lambda result: result.effective_workers,
    )
    status = "NOT_RELEASED_WHILE_BLOCKED" if blocked else "SELECTED"
    if blocked:
        rationale = (
            "Selected by highest aggregate bounded-slice rows/sec among worker "
            "counts that passed resolver smoke and parity. The policy is not "
            "released for downstream reruns while status is blocked."
        )
    else:
        rationale = (
            "Selected by highest aggregate bounded-slice rows/sec among worker "
            "counts that passed resolver smoke and parity."
        )
    return ProductionWorkerPolicy(
        requested_workers=best_workers,
        effective_workers_observed=representative.effective_workers,
        thread_control={
            "POLARS_MAX_THREADS": str(representative.threads_per_worker),
            "OMP_NUM_THREADS": str(representative.threads_per_worker),
            "RAYON_NUM_THREADS": str(representative.threads_per_worker),
            "NUMBA_NUM_THREADS": str(representative.threads_per_worker),
        },
        rationale=rationale,
        status=status,
    )


def _write_summary(path: Path, payload: BenchmarkPayload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_summary_markdown(payload), encoding="utf-8")


def _peak_rss_kib() -> int | None:
    try:
        return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    except (OSError, ValueError):
        return None


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--alpha-data-root", default=os.environ.get("ALPHA_DATA_ROOT"))
    parser.add_argument("--canonical-root")
    parser.add_argument("--dataset-registry")
    parser.add_argument("--benchmark-root")
    parser.add_argument("--summary-out", default=str(SUMMARY_PATH))
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL)
    parser.add_argument("--year", type=int, default=DEFAULT_YEAR)
    parser.add_argument("--start-ts", default=DEFAULT_START_TS)
    parser.add_argument("--end-ts", default=DEFAULT_END_TS)
    parser.add_argument("--workers", type=int, action="append", default=None)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    alpha_data_root = (
        Path(args.alpha_data_root).expanduser()
        if args.alpha_data_root
        else Path("~/alpha_data/alpha_system").expanduser()
    )
    canonical_root = (
        Path(args.canonical_root).expanduser()
        if args.canonical_root
        else alpha_data_root / DEFAULT_CANONICAL_RELATIVE_ROOT
    )
    dataset_registry = (
        Path(args.dataset_registry).expanduser()
        if args.dataset_registry
        else alpha_data_root / "registry" / "datasets.sqlite"
    )
    payload = run_benchmark(
        alpha_data_root=alpha_data_root,
        canonical_root=canonical_root,
        dataset_registry_path=dataset_registry,
        summary_path=Path(args.summary_out),
        benchmark_root=Path(args.benchmark_root).expanduser() if args.benchmark_root else None,
        window=BenchmarkWindow(
            symbol=args.symbol,
            year=args.year,
            start_ts=args.start_ts,
            end_ts=args.end_ts,
        ),
        worker_counts=tuple(args.workers or WORKER_COUNTS),
    )
    if args.format == "json":
        print(json.dumps(payload.to_dict(), indent=2, sort_keys=True))
    else:
        print(render_summary_markdown(payload))
    return 0 if payload.status == "COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
