from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import alpha_system.features.scaleout.driver as scaleout_driver
from tools.reference_label_parallel_compute import benchmark_reference_parallel as bench


def test_slice_self_validation_rejects_missing_roll_or_gap() -> None:
    base = bench.SliceDefinition(
        config_path="configs/labels/scaleout/cost_adjusted.json",
        family="cost_adjusted",
        symbols=("ES",),
        years=(2024,),
        horizons=("1m", "3m", "5m", "10m", "15m", "30m", "60m", "120m"),
        label_ids=("cost_adjusted_fwd_ret", "spread_adjusted_fwd_ret"),
        unit_ids=tuple(f"mbu_{index}" for index in range(8)),
        ohlcv_dataset_version_ids=("dsv_ohlcv",),
        bbo_dataset_version_ids=("dsv_bbo",),
        canonical_ohlcv_rows=100,
        session_gap_count=0,
        max_gap_minutes=0,
        roll_event_count=0,
        roll_event_dates=(),
        raw_contract_transitions=0,
    )

    missing = bench.validate_slice_definition(base)

    assert "at least one contract-roll event is required" in missing
    assert "at least one session/maintenance gap is required" in missing


def test_select_slice_widens_or_fails_with_clear_message(monkeypatch: pytest.MonkeyPatch) -> None:
    config = SimpleNamespace(
        config_path=Path("configs/labels/scaleout/cost_adjusted.json"),
        family="cost_adjusted",
        symbols=("ES", "NQ"),
        years=(2024, 2025),
        label_names=("cost_adjusted_fwd_ret", "spread_adjusted_fwd_ret"),
    )

    monkeypatch.setattr(
        bench.scaleout_driver,
        "build_scaleout_units",
        lambda _config, target: tuple(_unit(symbol, year, "1m") for symbol in target.symbols for year in target.years),
    )
    monkeypatch.setattr(bench, "_unit_has_eligible_persisted_locks", lambda *_args: True)
    monkeypatch.setattr(
        bench,
        "_canonical_slice_evidence",
        lambda *_args: bench.CanonicalSliceEvidence(
            row_count=10,
            session_gap_count=0,
            max_gap_minutes=0,
            raw_contract_transitions=0,
            dataset_paths_checked=(),
        ),
    )
    monkeypatch.setattr(bench, "_roll_event_dates", lambda *_args: ())

    with pytest.raises(bench.BenchmarkError, match="after widening"):
        bench.select_self_validating_slice(
            config=config,
            config_path=Path("configs/labels/scaleout/cost_adjusted.json"),
            canonical_root=Path("/tmp/canonical"),
            dataset_registry_path=Path("/tmp/datasets.sqlite"),
        )


def test_benchmark_namespace_rejects_production_paths(tmp_path: Path) -> None:
    alpha_root = tmp_path / "alpha"

    with pytest.raises(bench.BenchmarkError, match="production"):
        bench.ensure_benchmark_namespace_is_isolated(
            alpha_data_root=alpha_root,
            benchmark_root=alpha_root,
        )

    with pytest.raises(bench.BenchmarkError, match="must start"):
        bench.ensure_benchmark_namespace_is_isolated(
            alpha_data_root=alpha_root,
            benchmark_root=alpha_root / "not_the_benchmark",
        )


def test_release_decision_boundary() -> None:
    assert bench.release_decision_for_cells((_cell(8, 3.0),)) == "RELEASED: workers=8"
    assert bench.release_decision_for_cells((_cell(8, 2.999),)) == "NOT_RELEASED"


def test_summary_contains_exactly_one_release_decision_line() -> None:
    result = _benchmark_result(release_decision="NOT_RELEASED")
    markdown = bench.render_markdown(result)

    lines = [line for line in markdown.splitlines() if line.startswith("Release decision:")]
    assert lines == ["Release decision: NOT_RELEASED"]
    assert "backlog" in markdown


def test_real_wiring_guard_resolves_real_driver() -> None:
    assert bench.resolve_real_driver() is scaleout_driver.run_scaleout


def test_real_data_skip_helper_skips_when_data_root_absent(tmp_path: Path) -> None:
    with pytest.raises(pytest.skip.Exception, match="required real data path is absent"):
        bench.skip_if_real_data_unavailable(
            alpha_data_root=tmp_path / "missing_alpha",
            canonical_root=tmp_path / "missing_canonical",
            dataset_registry_path=tmp_path / "missing.sqlite",
        )


def _unit(symbol: str, year: int, horizon: str) -> SimpleNamespace:
    dataset = SimpleNamespace(
        schema_id="ohlcv_1m",
        dataset_version_id=f"dsv_{symbol.lower()}_{year}",
    )
    return SimpleNamespace(
        unit_id=f"mbu_{symbol.lower()}_{year}_{horizon}",
        symbol=symbol,
        year=year,
        horizon=horizon,
        input_datasets=(dataset,),
    )


def _cell(workers: int, speedup: float) -> bench.WorkerCellResult:
    return bench.WorkerCellResult(
        requested_workers=workers,
        effective_workers=workers,
        threads_per_worker=2,
        elapsed_seconds=1.0,
        units_per_second=speedup,
        speedup_vs_1=speedup,
        worker_compute_seconds=0.7,
        serial_registration_seconds=0.2,
        overhead_seconds=0.1,
        peak_rss_mib=128.0,
        registry_rows_before=0,
        registry_rows_after=18,
        registry_delta_rows=18,
        completed_units=9,
        failed_units=0,
        skipped_units=0,
        label_version_count=18,
        total_row_count=100,
        reductions=(),
        determinism=bench.DeterminismResult.baseline(9),
    )


def _benchmark_result(*, release_decision: str) -> bench.BenchmarkResult:
    return bench.BenchmarkResult(
        generated_at="2026-06-11T00:00:00+00:00",
        namespace_name="rlpc_p03_benchmark_20260611T000000Z",
        namespace_pattern="$ALPHA_DATA_ROOT/rlpc_p03_benchmark_<UTCSTAMP>/workers_N",
        slice_definition=bench.SliceDefinition(
            config_path="configs/labels/scaleout/cost_adjusted.json",
            family="cost_adjusted",
            symbols=("ES",),
            years=(2024,),
            horizons=("1m", "3m", "5m", "10m", "15m", "30m", "60m", "120m", "240m"),
            label_ids=("cost_adjusted_fwd_ret", "spread_adjusted_fwd_ret"),
            unit_ids=tuple(f"mbu_{index}" for index in range(9)),
            ohlcv_dataset_version_ids=("dsv_ohlcv",),
            bbo_dataset_version_ids=("dsv_bbo",),
            canonical_ohlcv_rows=100,
            session_gap_count=1,
            max_gap_minutes=60,
            roll_event_count=1,
            roll_event_dates=("2024-06-13",),
            raw_contract_transitions=0,
        ),
        cells=(_cell(1, 1.0), _cell(8, 2.0)),
        production_registry_rows_before=5,
        production_registry_rows_after=5,
        release_decision=release_decision,
        diagnosis=(
            "worker compute/IO bound: workers=8 speedup was 2.00x, below the "
            "3.0x gate; backlog section 6 option 2 remains the recorded escalation."
        ),
        driver_entrypoint="alpha_system.features.scaleout.driver.run_scaleout",
    )
