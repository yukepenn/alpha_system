from __future__ import annotations

from tools.label_compute_fast_path.baseline_benchmark import (
    BenchmarkResult,
    BenchmarkSummary,
    SliceDefinition,
    _full_window_basis,
)


def test_full_window_basis_uses_accepted_futsub_units() -> None:
    assert _full_window_basis("fixed_base") == 79_200_000
    assert _full_window_basis("fixed_extended") == 39_600_000
    assert _full_window_basis("close_out") == 26_400_000
    assert _full_window_basis("cost_adjusted") == 237_600_000
    assert _full_window_basis("path") == 369_600_000


def test_benchmark_result_rates_and_markdown_are_value_free() -> None:
    result = BenchmarkResult(
        family="fixed_base",
        definitions=6,
        elapsed_seconds=2.0,
        rows_processed=100,
        records_emitted=90,
        full_window_rows_basis=1_000,
        notes="synthetic timing only",
    )
    summary = BenchmarkSummary(
        slice_definition=SliceDefinition(
            symbol="ES",
            year=2024,
            start_ts="2024-06-01T00:00:00+00:00",
            end_ts="2024-07-01T00:00:00+00:00",
            ohlcv_dataset_version_id="dsv_ohlcv",
            bbo_dataset_version_id="dsv_bbo",
            ohlcv_row_count=100,
            bbo_row_count=100,
            roll_event_count=1,
            maintenance_gap_count=20,
        ),
        results=(result,),
    )

    assert result.rows_per_second == 50.0
    assert result.full_window_runtime_estimate_seconds == 20.0
    markdown = summary.to_markdown()
    assert "`fixed_base`" in markdown
    assert "Production registry write occurred: `false`" in markdown
    assert "Full-window reference timing occurred: `false`" in markdown
    assert "label values" in markdown
