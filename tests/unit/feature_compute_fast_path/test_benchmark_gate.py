from __future__ import annotations

from datetime import UTC, datetime

import pytest

from tools.feature_compute_fast_path.benchmark_gate import (
    BenchmarkError,
    BenchmarkPayload,
    BenchmarkWindow,
    PackResult,
    SliceValidation,
    blocked_summary,
    extrapolate_runtime_seconds,
    render_summary_markdown,
    validate_report_fields,
    validate_slice_self_coverage,
)


def test_benchmark_gate_extrapolates_full_window_runtime() -> None:
    assert extrapolate_runtime_seconds(2_000, 500.0) == 4.0

    with pytest.raises(BenchmarkError, match="full_window_rows"):
        extrapolate_runtime_seconds(-1, 500.0)
    with pytest.raises(BenchmarkError, match="rows_per_sec"):
        extrapolate_runtime_seconds(2_000, 0.0)


def test_benchmark_gate_report_schema_is_required() -> None:
    fields = {
        "elapsed": 1.0,
        "rows_per_sec": 2.0,
        "canonical_reads_per_symbol_year": 1.0,
        "output_features_or_labels_per_read": 3.0,
        "full_accepted_window_runtime_estimate": 4.0,
        "speedup_vs_reference": 5.0,
    }
    validate_report_fields(fields)

    missing_speedup = dict(fields)
    missing_speedup.pop("speedup_vs_reference")
    with pytest.raises(BenchmarkError, match="speedup_vs_reference"):
        validate_report_fields(missing_speedup)


def test_benchmark_gate_slice_self_validation_requires_roll_and_gap() -> None:
    validate_slice_self_coverage(roll_event_count=1, session_gap_count=1)

    with pytest.raises(BenchmarkError, match="contract-roll"):
        validate_slice_self_coverage(roll_event_count=0, session_gap_count=1)
    with pytest.raises(BenchmarkError, match="session gap"):
        validate_slice_self_coverage(roll_event_count=1, session_gap_count=0)


def test_benchmark_gate_blocked_summary_is_value_free_without_data_root() -> None:
    payload = blocked_summary(None, "ALPHA_DATA_ROOT is not set")
    text = render_summary_markdown(payload)

    assert payload.status == "BLOCKED"
    assert "ALPHA_DATA_ROOT is not set" in text
    assert "Parquet" in text
    assert "SQLite" in text


def test_benchmark_gate_complete_summary_contains_required_fields() -> None:
    pack = PackResult(
        pack_id="synthetic_pack",
        kind="features",
        symbols=("ES",),
        slice_row_count=100,
        output_count=4,
        reference_elapsed_seconds=2.0,
        v1_elapsed_seconds=0.5,
        reference_rows_per_sec=50.0,
        v1_rows_per_sec=200.0,
        reference_canonical_reads=4,
        v1_canonical_reads=1,
        canonical_reads_per_symbol_year=1.0,
        output_features_or_labels_per_read=4.0,
        speedup_vs_reference=4.0,
        full_accepted_window_rows=1_000,
        full_accepted_window_runtime_estimate_seconds=5.0,
        extrapolation_basis=(
            "synthetic_pack: 100 bounded synthetic rows measured; "
            "1000 accepted-window rows extrapolated"
        ),
        parity_result="PASS",
        tolerance_notes=(),
    )
    payload = BenchmarkPayload(
        status="COMPLETE",
        generated_at=datetime(2026, 6, 8, tzinfo=UTC),
        alpha_data_root="/tmp/alpha_system_synthetic",
        canonical_root="/tmp/alpha_system_synthetic/databento/canonical/glbx_mdp3",
        window=BenchmarkWindow(year=2024, month=12, symbols=("ES",), primary_symbol="ES"),
        validation=SliceValidation(
            roll_event_count=1,
            raw_contract_transition_count=0,
            session_gap_count=2,
            row_count_by_input={"ohlcv:ES": 100},
            notes=("synthetic coverage note",),
        ),
        packs=(pack,),
    )

    text = render_summary_markdown(payload)

    assert "`COMPLETE`" in text
    assert "Reference Reads" in text
    assert "`speedup_vs_reference`" in text
    assert "synthetic_pack: 100 bounded synthetic rows measured" in text
    validate_report_fields(pack.required_report_fields())


def test_benchmark_gate_parity_blocked_summary_omits_speedup_report() -> None:
    payload = BenchmarkPayload(
        status="BLOCKED_PARITY",
        generated_at=datetime(2026, 6, 8, tzinfo=UTC),
        alpha_data_root="/tmp/alpha_system_synthetic",
        canonical_root="/tmp/alpha_system_synthetic/databento/canonical/glbx_mdp3",
        window=BenchmarkWindow(year=2024, month=12, symbols=("ES",), primary_symbol="ES"),
        validation=SliceValidation(
            roll_event_count=1,
            raw_contract_transition_count=0,
            session_gap_count=1,
            row_count_by_input={"ohlcv:ES": 100},
            notes=(),
        ),
        packs=(),
        blocked_reason="Real-data parity confirmation failed before speedup reporting",
    )

    text = render_summary_markdown(payload)

    assert "`BLOCKED_PARITY`" in text
    assert "Real-data parity confirmation failed" in text
    assert "No speedup or full-window runtime estimate is reported" in text
    assert "## Results" not in text
