from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import pytest

from alpha_system.runtime.contracts.run_record import StudyRunResultState
from alpha_system.runtime.diagnostics.contracts import DiagnosticsRunSpecRef
from alpha_system.runtime.diagnostics.factor import (
    FactorDiagnosticsThresholds,
    build_factor_diagnostics_run,
)
from alpha_system.runtime.diagnostics.factor import runtime as factor_runtime


def test_factor_diagnostics_orchestrates_research_primitives_and_is_summary_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: set[str] = set()

    def pearson_ic(factor_values: Iterable[Any], label_values: Iterable[Any]) -> dict[str, Any]:
        calls.add("pearson_ic")
        assert list(factor_values) == [1.0, 2.0, 3.0, 4.0]
        assert list(label_values) == [0.01, 0.02, 0.03, 0.04]
        return {"ic": 0.5, "n": 4}

    def rank_ic(factor_values: Iterable[Any], label_values: Iterable[Any]) -> dict[str, Any]:
        calls.add("rank_ic")
        assert list(factor_values) == [1.0, 2.0, 3.0, 4.0]
        assert list(label_values) == [0.01, 0.02, 0.03, 0.04]
        return {"ic": 0.75, "n": 4}

    def ic_decay(observations: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
        calls.add("ic_decay")
        assert len(tuple(observations)) == 4
        return {
            "by_horizon": {
                "60": {"pearson_ic": 0.2, "rank_ic": 0.3, "n": 2},
                "120": {"pearson_ic": 0.4, "rank_ic": 0.5, "n": 2},
            },
            "decay_slope_per_second": 0.003333333333333333,
            "n_horizons": 2,
        }

    def bucket_forward_returns(
        observations: Iterable[Mapping[str, Any]],
        *,
        bucket_count: int = 5,
    ) -> list[dict[str, Any]]:
        calls.add("bucket_forward_returns")
        assert len(tuple(observations)) == 4
        assert bucket_count == 2
        return [
            {"bucket": 1, "n": 2, "mean_return": -0.01, "hit_rate": 0.0},
            {"bucket": 2, "n": 2, "mean_return": 0.02, "hit_rate": 1.0},
        ]

    def bucket_monotonicity(bucket_summary: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        calls.add("bucket_monotonicity")
        assert len(bucket_summary) == 2
        return {
            "is_monotonic": True,
            "direction": "increasing",
            "rank_correlation": 1.0,
            "sign_changes": 0,
            "n_buckets": 2,
        }

    def tail_expectancy(bucket_summary: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        calls.add("tail_expectancy")
        assert len(bucket_summary) == 2
        return {
            "tail_expectancy": 0.03,
            "low_tail_mean": -0.01,
            "high_tail_mean": 0.02,
        }

    monkeypatch.setattr(factor_runtime.research_ic, "pearson_ic", pearson_ic)
    monkeypatch.setattr(factor_runtime.research_ic, "rank_ic", rank_ic)
    monkeypatch.setattr(factor_runtime.research_ic, "ic_decay", ic_decay)
    monkeypatch.setattr(
        factor_runtime.research_buckets,
        "bucket_forward_returns",
        bucket_forward_returns,
    )
    monkeypatch.setattr(factor_runtime.research_buckets, "bucket_monotonicity", bucket_monotonicity)
    monkeypatch.setattr(factor_runtime.research_buckets, "tail_expectancy", tail_expectancy)

    result = build_factor_diagnostics_run(
        diagnostics_run_spec=_spec_ref(),
        observations=_rows(),
        lineage_refs=_lineage_refs(),
        thresholds=FactorDiagnosticsThresholds(
            min_observations=4,
            bucket_count=2,
            min_populated_buckets=2,
        ),
    )

    assert calls == {
        "pearson_ic",
        "rank_ic",
        "ic_decay",
        "bucket_forward_returns",
        "bucket_monotonicity",
        "tail_expectancy",
    }
    assert result.report.status is StudyRunResultState.DIAGNOSTICS_COMPLETE
    assert result.record.status is StudyRunResultState.DIAGNOSTICS_COMPLETE
    assert result.record.report_ref == result.report.to_ref()

    payload = result.report.to_dict()
    assert payload["descriptive_only"] is True
    assert payload["non_promotional"] is True
    assert payload["raw_or_heavy_data_embedded"] is False
    assert payload["diagnostic_pass_is_alpha_validation"] is False
    assert payload["report_type"] == "FactorDiagnosticsReport"

    assert result.report.coverage_summary["coverage_ratio"] == 1.0
    assert result.report.coverage_summary["missingness_rate"] == 0.0
    assert result.report.quality_summary["pearson_ic"] == 0.5
    assert result.report.quality_summary["rank_ic"] == 0.75
    assert result.report.quality_summary["bucket_is_monotonic"] is True
    assert result.report.quality_summary["bucket_direction"] == "increasing"
    assert result.report.quality_summary["decay_first_horizon_seconds"] == 60
    assert result.report.quality_summary["decay_last_horizon_seconds"] == 120

    for summary in (payload["coverage_summary"], payload["quality_summary"]):
        assert all(
            item is None or isinstance(item, bool | int | float | str) for item in summary.values()
        )
    assert "bucket_forward_returns" not in str(payload)
    assert "by_horizon" not in str(payload)


def test_missing_available_ts_surfaces_rejection_and_terminal_record() -> None:
    result = build_factor_diagnostics_run(
        diagnostics_run_spec=_spec_ref(),
        observations=[
            {
                "factor_value": 1.0,
                "label_value": 0.01,
                "label_available_ts": "2026-01-02T14:31:00Z",
                "horizon_seconds": 60,
            }
        ],
        lineage_refs=_lineage_refs(),
        thresholds=FactorDiagnosticsThresholds(
            min_observations=1,
            min_coverage_ratio=0.0,
            max_missingness_rate=1.0,
            bucket_count=2,
            min_populated_buckets=1,
        ),
    )

    assert result.report.status is StudyRunResultState.REJECTED
    assert result.record.status is StudyRunResultState.REJECTED
    assert "factor_available_ts_missing" in {
        reason.code for reason in result.report.rejection_reasons
    }
    assert result.record.rejection_reasons == result.report.rejection_reasons


def test_low_coverage_or_high_missingness_surfaces_failed_diagnostics() -> None:
    result = build_factor_diagnostics_run(
        diagnostics_run_spec=_spec_ref(),
        observations=[
            _row(1.0, 0.01, horizon_seconds=60),
            _row(2.0, 0.02, horizon_seconds=120),
            _row(3.0, None, horizon_seconds=60),
            _row(4.0, None, horizon_seconds=120),
        ],
        lineage_refs=_lineage_refs(),
        thresholds=FactorDiagnosticsThresholds(
            min_observations=2,
            min_coverage_ratio=0.75,
            max_missingness_rate=0.25,
            max_outlier_rate=1.0,
            bucket_count=2,
            min_populated_buckets=2,
        ),
    )

    assert result.report.status is StudyRunResultState.DIAGNOSTICS_FAILED
    assert {
        "factor_diagnostics_low_coverage",
        "factor_diagnostics_high_missingness",
    }.issubset({reason.code for reason in result.report.rejection_reasons})
    assert result.report.coverage_summary["coverage_ratio"] == 0.5
    assert result.report.coverage_summary["missingness_rate"] == 0.5


def test_constant_factor_relationship_is_visible_inconclusive() -> None:
    result = build_factor_diagnostics_run(
        diagnostics_run_spec=_spec_ref(),
        observations=[
            _row(1.0, 0.01, horizon_seconds=60),
            _row(1.0, 0.02, horizon_seconds=120),
            _row(1.0, 0.03, horizon_seconds=180),
        ],
        lineage_refs=_lineage_refs(),
        thresholds=FactorDiagnosticsThresholds(
            min_observations=3,
            max_outlier_rate=1.0,
            bucket_count=2,
            min_populated_buckets=2,
        ),
    )

    assert result.report.status is StudyRunResultState.INCONCLUSIVE
    assert "factor_diagnostics_ic_unavailable" in {
        reason.code for reason in result.report.rejection_reasons
    }
    assert result.report.quality_summary["pearson_ic"] is None
    assert result.report.quality_summary["rank_ic"] is None


def _rows() -> tuple[dict[str, object], ...]:
    return (
        _row(1.0, 0.01, horizon_seconds=60),
        _row(2.0, 0.02, horizon_seconds=60),
        _row(3.0, 0.03, horizon_seconds=120),
        _row(4.0, 0.04, horizon_seconds=120),
    )


def _row(
    factor_value: float,
    label_value: float | None,
    *,
    horizon_seconds: int,
) -> dict[str, object]:
    return {
        "factor_value": factor_value,
        "label_value": label_value,
        "available_ts": "2026-01-02T14:30:05Z",
        "label_available_ts": "2026-01-02T14:31:00Z",
        "horizon_seconds": horizon_seconds,
    }


def _spec_ref() -> DiagnosticsRunSpecRef:
    return DiagnosticsRunSpecRef(
        diagnostics_run_spec_id="dspec_" + "1" * 24,
        content_hash="2" * 64,
    )


def _lineage_refs() -> dict[str, str]:
    return {
        "study_run_spec_id": "srun_" + "3" * 24,
        "runtime_plan_id": "rplan_" + "4" * 24,
        "dataset_version_id": "dsv_synthetic_factor_fixture_v1",
        "feature_pack_ref": "feature_pack_synthetic_v1",
        "label_pack_ref": "label_pack_synthetic_v1",
    }
