from __future__ import annotations

from datetime import UTC, datetime

import pytest

from tools.label_compute_fast_path.baseline_benchmark import BenchmarkResult
from tools.label_compute_fast_path.benchmark_gate import (
    ENGINE_BLOCKED,
    ENGINE_FAST,
    ENGINE_REFERENCE,
    BenchmarkGateError,
    BenchmarkPayload,
    BenchmarkWindow,
    CoverageCheck,
    FamilyBenchmark,
    ProductionWorkerPolicy,
    SliceValidation,
    WorkerResult,
    evaluate_gate_status,
    extrapolate_runtime_seconds,
    render_summary_markdown,
    select_family_engine_policies,
    validate_report_fields,
    validate_slice_self_coverage,
)


def test_benchmark_gate_extrapolates_runtime() -> None:
    assert extrapolate_runtime_seconds(1_000, 250.0) == 4.0

    with pytest.raises(BenchmarkGateError, match="full_window_rows"):
        extrapolate_runtime_seconds(-1, 250.0)
    with pytest.raises(BenchmarkGateError, match="rows_per_sec"):
        extrapolate_runtime_seconds(1_000, 0.0)


def test_benchmark_gate_requires_roll_and_gap_coverage() -> None:
    validate_slice_self_coverage(roll_event_count=1, maintenance_gap_count=1)

    with pytest.raises(BenchmarkGateError, match="contract-roll"):
        validate_slice_self_coverage(roll_event_count=0, maintenance_gap_count=1)
    with pytest.raises(BenchmarkGateError, match="session/maintenance gap"):
        validate_slice_self_coverage(roll_event_count=1, maintenance_gap_count=0)


def test_benchmark_gate_report_fields_are_required() -> None:
    fields = {
        "elapsed": 1.0,
        "rows_per_sec": 2.0,
        "canonical_reads_per_symbol_year": 1.0,
        "labels_per_read": 3.0,
        "file_counts": 4,
        "registry_deltas": 5,
        "full_accepted_window_runtime_estimate": 6.0,
        "speedup_vs_reference": 7.0,
        "selected_production_worker_policy": "workers=2",
    }
    validate_report_fields(fields)

    missing = dict(fields)
    missing.pop("labels_per_read")
    with pytest.raises(BenchmarkGateError, match="labels_per_read"):
        validate_report_fields(missing)


def test_coverage_check_blocks_when_production_surface_is_narrower() -> None:
    complete = CoverageCheck(
        family="fixed_base",
        required_definition_count=6,
        production_definition_count=6,
        production_unit_count=6,
    )
    incomplete = CoverageCheck(
        family="path",
        required_definition_count=28,
        production_definition_count=4,
        production_unit_count=4,
    )

    assert complete.status == "PASS"
    assert incomplete.status == "BLOCKED_PRODUCTION_WIRING"


def _worker_result(**overrides: object) -> WorkerResult:
    fields: dict[str, object] = {
        "family": "path",
        "requested_workers": 4,
        "effective_workers": 4,
        "threads_per_worker": 2,
        "elapsed_seconds": 1.25,
        "fast_compute_seconds": 0.25,
        "registration_seconds": 0.10,
        "parity_seconds": 0.90,
        "label_row_evaluations": 1_000,
        "records_emitted": 900,
        "rows_per_second": 4_000.0,
        "reference_rows_per_second": 500.0,
        "canonical_reads_per_symbol_year": 4.0,
        "labels_per_read": 1.0,
        "file_count": 4,
        "registry_delta": 4,
        "full_window_runtime_estimate_seconds": 10.0,
        "speedup_vs_reference": 8.0,
        "resolver_smoke": "PASS 4/4",
        "parity_result": "PASS",
        "peak_memory_kib": 12345,
        "worker_reductions": (),
    }
    fields.update(overrides)
    return WorkerResult(**fields)  # type: ignore[arg-type]


def test_worker_result_discloses_component_timings_separately() -> None:
    """Regression for LCFP-P08 finding 5: parity/registration must never be
    folded into the fast throughput claim. The throughput basis is the fast
    compute component; parity confirmation re-runs the reference engine and
    is reported as its own component."""

    result = _worker_result()
    payload = result.to_dict()
    assert payload["fast_compute_seconds"] == 0.25
    assert payload["registration_seconds"] == 0.10
    assert payload["parity_seconds"] == 0.90
    assert payload["elapsed_seconds"] == 1.25
    # Throughput derives from compute time only (1000 rows / 0.25 s), not from
    # the parity-contaminated total (1000 / 1.25 = 800 would be wrong).
    assert result.rows_per_second == pytest.approx(
        result.label_row_evaluations / result.fast_compute_seconds
    )
    assert result.rows_per_second != pytest.approx(
        result.label_row_evaluations / result.elapsed_seconds
    )
    # Speedup is compute vs compute against the same-process reference rerun.
    assert result.speedup_vs_reference == pytest.approx(
        result.rows_per_second / result.reference_rows_per_second
    )


def _family(family: str, *results: WorkerResult) -> FamilyBenchmark:
    required = {
        "fixed_base": 6,
        "fixed_extended": 3,
        "close_out": 2,
        "cost_adjusted": 18,
        "path": 28,
    }.get(family, 1)
    return FamilyBenchmark(
        family=family,
        coverage=CoverageCheck(
            family=family,
            required_definition_count=required,
            production_definition_count=required,
            production_unit_count=1,
        ),
        results=tuple(results),
    )


def test_path_fast_and_cheap_slow_selects_per_family_engines_without_blocking() -> None:
    """Amended LCFP-P08 criterion: cheap families at or below 1.0x do NOT block;
    they become documented reference-engine selections, while the path family
    selects fast at its best stable worker count."""

    path = _family(
        "path",
        _worker_result(
            family="path",
            requested_workers=1,
            effective_workers=1,
            rows_per_second=2_000.0,
            speedup_vs_reference=3.12,
        ),
        _worker_result(
            family="path",
            requested_workers=4,
            effective_workers=4,
            rows_per_second=4_000.0,
            speedup_vs_reference=10.29,
        ),
    )
    cheap = _family(
        "fixed_extended",
        _worker_result(
            family="fixed_extended",
            requested_workers=1,
            effective_workers=1,
            rows_per_second=300.0,
            speedup_vs_reference=0.53,
        ),
        _worker_result(
            family="fixed_extended",
            requested_workers=4,
            effective_workers=4,
            rows_per_second=250.0,
            speedup_vs_reference=0.36,
        ),
    )

    policies = select_family_engine_policies((path, cheap))
    status, reasons = evaluate_gate_status(policies)

    assert status == "COMPLETE"
    assert reasons == ()
    by_family = {policy.family: policy for policy in policies}
    path_policy = by_family["path"]
    assert path_policy.selected_engine == ENGINE_FAST
    assert path_policy.requested_workers == 4
    assert path_policy.measured_speedup == pytest.approx(10.29)
    cheap_policy = by_family["fixed_extended"]
    assert cheap_policy.selected_engine == ENGINE_REFERENCE
    assert cheap_policy.requested_workers is None
    assert cheap_policy.measured_speedup == pytest.approx(0.53)
    # Honest component-timing documentation rides with the reference selection.
    assert "fast_compute=" in cheap_policy.rationale
    assert "registration=" in cheap_policy.rationale
    assert "parity=" in cheap_policy.rationale


def test_path_not_materially_faster_remains_a_hard_speedup_block() -> None:
    path = _family(
        "path", _worker_result(family="path", speedup_vs_reference=0.95)
    )
    cheap = _family(
        "fixed_base", _worker_result(family="fixed_base", speedup_vs_reference=0.40)
    )

    policies = select_family_engine_policies((path, cheap))
    status, reasons = evaluate_gate_status(policies)

    assert status == "BLOCKED_SPEEDUP"
    assert any("`path`" in reason for reason in reasons)
    # The cheap family is a documented reference selection, not a block.
    assert not any("fixed_base" in reason for reason in reasons)

    # Exactly 1.0x is not materially faster: still a hard block for path.
    boundary = select_family_engine_policies(
        (_family("path", _worker_result(family="path", speedup_vs_reference=1.0)),)
    )
    assert boundary[0].selected_engine == ENGINE_REFERENCE
    status, _ = evaluate_gate_status(boundary)
    assert status == "BLOCKED_SPEEDUP"


def test_parity_failure_blocks_regardless_of_speedup() -> None:
    # run_benchmark records a parity/runner failure as a blocked reason; any
    # blocked reason forces a blocked status even when measured speedups win.
    path = _family("path", _worker_result(family="path", speedup_vs_reference=10.0))
    policies = select_family_engine_policies((path,))
    status, reasons = evaluate_gate_status(
        policies,
        blocked_reasons=(
            "`path` worker `4` failed through the real fast runner: parity",
        ),
    )
    assert status == "BLOCKED_PRODUCTION_WIRING"
    assert any("parity" in reason for reason in reasons)

    # Defensively, a family with no parity+resolver-passing cell can never be
    # selected even without a recorded reason.
    failed = _family(
        "path",
        _worker_result(family="path", parity_result="BLOCKED", speedup_vs_reference=10.0),
    )
    policies = select_family_engine_policies((failed,))
    assert policies[0].selected_engine == ENGINE_BLOCKED
    status, reasons = evaluate_gate_status(policies)
    assert status == "BLOCKED_PRODUCTION_WIRING"
    assert any("`path`" in reason for reason in reasons)

    # Resolver smoke failures equally bar a fast selection.
    no_resolver = _family(
        "path",
        _worker_result(family="path", resolver_smoke="NOT_RUN", speedup_vs_reference=10.0),
    )
    assert select_family_engine_policies((no_resolver,))[0].selected_engine == ENGINE_BLOCKED


def test_worker_policy_status_is_not_released_while_blocked() -> None:
    from tools.label_compute_fast_path.benchmark_gate import _select_worker_policy

    families = (_family("path", _worker_result(family="path")),)
    assert _select_worker_policy(families, blocked=True).status == "NOT_RELEASED_WHILE_BLOCKED"
    assert _select_worker_policy(families, blocked=False).status == "SELECTED"


def test_summary_renders_per_family_engine_policy_table() -> None:
    path = _family(
        "path",
        _worker_result(
            family="path", requested_workers=4, effective_workers=4, speedup_vs_reference=8.0
        ),
    )
    cheap = _family(
        "fixed_extended",
        _worker_result(
            family="fixed_extended",
            requested_workers=1,
            effective_workers=1,
            speedup_vs_reference=0.53,
        ),
    )
    policies = select_family_engine_policies((path, cheap))
    status, reasons = evaluate_gate_status(policies)
    payload = BenchmarkPayload(
        status=status,
        generated_at=datetime(2026, 6, 10, tzinfo=UTC),
        window=BenchmarkWindow(),
        slice_validation=SliceValidation(
            ohlcv_dataset_version_id="dsv_ohlcv",
            bbo_dataset_version_id="dsv_bbo",
            ohlcv_row_count=100,
            bbo_row_count=100,
            roll_event_count=1,
            maintenance_gap_count=2,
        ),
        reference_results=(),
        families=(path, cheap),
        selected_policy=ProductionWorkerPolicy(
            requested_workers=4,
            effective_workers_observed=4,
            thread_control={"POLARS_MAX_THREADS": "2"},
            rationale="synthetic unit test",
            status="SELECTED",
        ),
        scratch_root_name="lcfp_p08_benchmark_synthetic",
        family_policies=policies,
        blocked_reasons=reasons,
    )

    text = render_summary_markdown(payload)

    assert "`COMPLETE`" in text
    assert "## Production Engine + Worker Policy" in text
    assert "| Family | Selected Engine | Workers | Measured Speedup | Rationale |" in text
    assert "| `path` | `fast` | 4 | 8.00 |" in text
    assert "| `fixed_extended` | `reference` | n/a | 0.53 |" in text
    # A complete summary releases the policy: no blocked disclaimer.
    assert "NOT RELEASED" not in text


def test_markdown_summary_is_value_free_and_records_blockers() -> None:
    worker = _worker_result(rows_per_second=800.0, speedup_vs_reference=1.6)
    payload = BenchmarkPayload(
        status="BLOCKED_PRODUCTION_WIRING",
        generated_at=datetime(2026, 6, 10, tzinfo=UTC),
        window=BenchmarkWindow(),
        slice_validation=SliceValidation(
            ohlcv_dataset_version_id="dsv_ohlcv",
            bbo_dataset_version_id="dsv_bbo",
            ohlcv_row_count=100,
            bbo_row_count=100,
            roll_event_count=1,
            maintenance_gap_count=2,
        ),
        reference_results=(
            BenchmarkResult(
                family="path",
                definitions=28,
                elapsed_seconds=2.0,
                rows_processed=1_000,
                records_emitted=900,
                full_window_rows_basis=10_000,
            ),
        ),
        families=(
            FamilyBenchmark(
                family="path",
                coverage=CoverageCheck(
                    family="path",
                    required_definition_count=28,
                    production_definition_count=4,
                    production_unit_count=4,
                ),
                results=(worker,),
            ),
        ),
        selected_policy=ProductionWorkerPolicy(
            requested_workers=4,
            effective_workers_observed=4,
            thread_control={"POLARS_MAX_THREADS": "2"},
            rationale="synthetic unit test",
            status="NOT_RELEASED_WHILE_BLOCKED",
        ),
        scratch_root_name="lcfp_p08_benchmark_synthetic",
        blocked_reasons=("`path` production wiring exposes 4/28 definitions.",),
    )

    text = render_summary_markdown(payload)

    assert "`BLOCKED_PRODUCTION_WIRING`" in text
    # Blocked summaries must say the policy is not released for downstream use.
    assert "`NOT_RELEASED_WHILE_BLOCKED`" in text
    assert text.count("NOT RELEASED") == 2  # engine-policy + worker-policy sections
    assert "4/28" in text
    assert "Value policy: value-free summary only" in text
    assert "Speedup is a measured engineering throughput claim only" in text
    assert "label values" in text
    # LCFP-P08 finding 5: component timings must be disclosed in the committed
    # summary, and the throughput basis must be stated as compute-only.
    assert "## Timing Methodology" in text
    assert "Compute (s) | Registration (s) | Parity (s) | Total (s)" in text
    assert "never enters the throughput numbers" in text
