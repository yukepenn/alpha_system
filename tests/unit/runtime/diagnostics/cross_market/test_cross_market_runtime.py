from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from alpha_system.runtime.contracts.run_record import StudyRunResultState
from alpha_system.runtime.diagnostics.contracts import (
    DiagnosticsFamily,
    DiagnosticsRunSpec,
    RuntimePlanRef,
)
from alpha_system.runtime.diagnostics.cross_market import (
    CrossMarketDiagnosticsConfig,
    CrossMarketDiagnosticsReport,
    build_cross_market_diagnostics_run,
    resolve_cross_market_dataset_version,
)
from alpha_system.runtime.diagnostics.cross_market import runtime as cross_market_runtime
from alpha_system.runtime.input_resolver import FeaturePackHandle, LabelPackHandle, RuntimeInputPack

FIXTURE_PATH = (
    Path(__file__).parents[4]
    / "fixtures"
    / "runtime"
    / "diagnostics"
    / "cross_market"
    / "synthetic_observations.json"
)
DATASET_VERSION_ID = "dsv_synthetic_cross_market_fixture_v1"


def test_cross_market_report_is_contract_compliant_and_descriptive() -> None:
    result = build_cross_market_diagnostics_run(
        diagnostics_run_spec=_diagnostics_spec(),
        runtime_input_pack=_runtime_input_pack(),
        observations=_observations(),
    )

    report = result.report
    assert isinstance(report, CrossMarketDiagnosticsReport)
    assert report.status is StudyRunResultState.DIAGNOSTICS_COMPLETE
    assert report.diagnostics_report.diagnostics_family is DiagnosticsFamily.CROSS_MARKET
    assert result.record.status is StudyRunResultState.DIAGNOSTICS_COMPLETE
    assert result.record.report_ref == report.to_ref()
    assert report.rejection_reasons == ()

    payload = report.to_dict()
    assert payload["report_type"] == "CrossMarketDiagnosticsReport"
    assert payload["descriptive_only"] is True
    assert payload["non_promotional"] is True
    assert payload["raw_or_heavy_data_embedded"] is False
    assert payload["diagnostic_pass_is_alpha_validation"] is False
    assert payload["coverage_summary"]["required_symbol_count"] == 3
    assert payload["coverage_summary"]["aligned_snapshot_count"] == 4
    assert payload["cross_market_timestamp_sync"]["synchronized_snapshot_count"] == 4
    assert len(payload["cross_market_symbol_summaries"]) == 3
    assert len(payload["cross_market_pair_summaries"]) == 3
    assert len(payload["cross_market_lead_lag_summaries"]) == 6
    assert len(payload["cross_market_regime_summaries"]) == 6
    assert payload["diagnostics_run_record"]["status"] == "DIAGNOSTICS_COMPLETE"

    rendered = str(payload).lower()
    for prohibited in (
        "alpha validated",
        "validated alpha",
        "tradable",
        "profitable",
        "candidate approved",
        "factor promoted",
        "strategy ready",
        "live ready",
        "paper ready",
        "production ready",
    ):
        assert prohibited not in rendered
    assert "label_value" not in rendered
    assert "provider_rows" not in rendered


def test_cross_market_runtime_delegates_correlation_to_research_primitive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[tuple[float, ...], tuple[str, ...]]] = []

    def correlations_to_existing_factors(
        candidate_values: Any,
        existing_factor_values: dict[str, Any],
    ) -> dict[str, dict[str, float | int | None]]:
        candidate = tuple(float(value) for value in candidate_values)
        calls.append((candidate, tuple(sorted(existing_factor_values))))
        return {
            factor_id: {"pearson": 0.25, "rank": 0.5, "n": len(candidate)}
            for factor_id in existing_factor_values
        }

    monkeypatch.setattr(
        cross_market_runtime.research_correlation,
        "correlations_to_existing_factors",
        correlations_to_existing_factors,
    )

    result = build_cross_market_diagnostics_run(
        diagnostics_run_spec=_diagnostics_spec(),
        runtime_input_pack=_runtime_input_pack(),
        observations=_observations(),
    )

    assert calls
    assert result.report.pair_summaries[0].zero_lag_pearson == 0.25
    assert result.report.pair_summaries[0].zero_lag_rank == 0.5
    assert result.report.lead_lag_summaries[0].pearson == 0.25
    assert result.report.regime_summaries[0].rank == 0.5


def test_unavailable_cross_instrument_input_is_visible_rejection() -> None:
    observations = list(_observations())
    observations[1] = {
        **observations[1],
        "decision_ts": "2026-01-05T14:30:01Z",
    }

    result = build_cross_market_diagnostics_run(
        diagnostics_run_spec=_diagnostics_spec(),
        runtime_input_pack=_runtime_input_pack(),
        observations=observations,
    )

    assert result.report.status is StudyRunResultState.REJECTED
    assert "leakage_risk" in _reason_codes(result.report)
    assert result.record.status is StudyRunResultState.REJECTED
    assert result.report.coverage_summary["unavailable_at_decision_count"] == 1


def test_alignment_uses_exact_timestamps_and_does_not_forward_fill() -> None:
    observations = [
        row
        for row in _observations()
        if (row["event_ts"] == "2026-01-05T14:30:00Z" and row["symbol"] != "RTY")
        or (row["event_ts"] == "2026-01-05T14:31:00Z" and row["symbol"] == "RTY")
    ]

    result = build_cross_market_diagnostics_run(
        diagnostics_run_spec=_diagnostics_spec(),
        runtime_input_pack=_runtime_input_pack(),
        observations=observations,
        config=CrossMarketDiagnosticsConfig(min_aligned_snapshots=1),
    )

    assert result.report.status is StudyRunResultState.DIAGNOSTICS_FAILED
    assert result.report.coverage_summary["aligned_snapshot_count"] == 0
    assert "low_coverage" in _reason_codes(result.report)
    assert "low_sample" in _reason_codes(result.report)


def test_mismatched_feature_pack_dataset_version_is_visible_rejection() -> None:
    pack = _runtime_input_pack()
    mismatched = RuntimeInputPack(
        alpha_spec_ref=pack.alpha_spec_ref,
        study_spec_ref=pack.study_spec_ref,
        study_input_pack=pack.study_input_pack,
        dataset_version_id=pack.dataset_version_id,
        dataset_lifecycle_state=pack.dataset_lifecycle_state,
        dataset_source=pack.dataset_source,
        dataset_reproducibility_hashes=dict(pack.dataset_reproducibility_hashes),
        canonical_input_views=pack.canonical_input_views,
        feature_packs=(
            FeaturePackHandle(
                feature_version_id="feature_rt_p10_mismatch_v1",
                feature_request_id="feature_request_rt_p10",
                feature_set_id="feature_set_rt_p10",
                feature_set_version="1",
                dataset_version_id="dsv_other",
                partition_id="development_partition",
                materialization_plan_id="feature_plan_rt_p10",
                first_event_ts="2026-01-05T14:30:00Z",
                last_event_ts="2026-01-05T14:33:00Z",
                first_available_ts="2026-01-05T14:30:01Z",
                last_available_ts="2026-01-05T14:33:03Z",
                lifecycle_state="VERSIONED",
            ),
        ),
        label_packs=pack.label_packs,
        dataset_scope=pack.dataset_scope,
        partition_scope=pack.partition_scope,
        session_scope=pack.session_scope,
        governance_metadata=pack.governance_metadata,
    )

    result = build_cross_market_diagnostics_run(
        diagnostics_run_spec=_diagnostics_spec(),
        runtime_input_pack=mismatched,
        observations=_observations(),
    )

    assert result.report.status is StudyRunResultState.REJECTED
    assert "data_unavailable" in _reason_codes(result.report)


def test_dataset_version_helper_delegates_to_registry_resolver() -> None:
    calls: list[tuple[str, str]] = []

    class _Dataset:
        symbol_universe = ("ES", "NQ", "RTY")

    def resolver(path: str | Path, dataset_version_id: object):
        calls.append((str(path), str(dataset_version_id)))
        return _Dataset()

    resolved = resolve_cross_market_dataset_version(
        "/tmp/synthetic_registry.sqlite",
        DATASET_VERSION_ID,
        resolver=resolver,
    )

    assert resolved.symbol_universe == ("ES", "NQ", "RTY")
    assert calls == [("/tmp/synthetic_registry.sqlite", DATASET_VERSION_ID)]

    with pytest.raises(cross_market_runtime.CrossMarketDiagnosticsError, match="missing required"):
        resolve_cross_market_dataset_version(
            "/tmp/synthetic_registry.sqlite",
            DATASET_VERSION_ID,
            required_symbols=("ES", "NQ", "RTY"),
            resolver=lambda _path, _dataset_id: type(
                "Dataset", (), {"symbol_universe": ("ES", "NQ")}
            )(),
        )


def _reason_codes(report: CrossMarketDiagnosticsReport) -> set[str]:
    return {reason.code for reason in report.rejection_reasons}


def _observations() -> tuple[dict[str, object], ...]:
    return tuple(json.loads(FIXTURE_PATH.read_text(encoding="utf-8")))


def _diagnostics_spec() -> DiagnosticsRunSpec:
    return DiagnosticsRunSpec(
        diagnostics_family=DiagnosticsFamily.CROSS_MARKET,
        study_run_spec={
            "study_run_spec_id": "srun_" + "1" * 24,
            "content_hash": "2" * 64,
        },
        runtime_plan=RuntimePlanRef(plan_id="rplan_" + "3" * 24, content_hash="4" * 64),
        spec_metadata={"requested_by": "rt_p10_cross_market_diagnostics_test"},
    )


def _runtime_input_pack() -> RuntimeInputPack:
    return RuntimeInputPack(
        alpha_spec_ref="aspec_rt_p10_fixture",
        study_spec_ref="sspec_rt_p10_fixture",
        study_input_pack={
            "alpha_spec_id": "aspec_rt_p10_fixture",
            "study_spec_id": "sspec_rt_p10_fixture",
            "feature_request_ids": ["feature_request_rt_p10"],
            "label_spec_ids": ["label_spec_rt_p10"],
            "dataset_scope": {"symbol_universe": ["ES", "NQ", "RTY"]},
        },
        dataset_version_id=DATASET_VERSION_ID,
        dataset_lifecycle_state="READY_FOR_RESEARCH",
        dataset_source="databento",
        dataset_reproducibility_hashes={"manifest_hash": "0" * 64},
        canonical_input_views=(),
        feature_packs=(
            FeaturePackHandle(
                feature_version_id="feature_rt_p10_fixture_v1",
                feature_request_id="feature_request_rt_p10",
                feature_set_id="feature_set_rt_p10",
                feature_set_version="1",
                dataset_version_id=DATASET_VERSION_ID,
                partition_id="development_partition",
                materialization_plan_id="feature_plan_rt_p10",
                first_event_ts="2026-01-05T14:30:00Z",
                last_event_ts="2026-01-05T14:33:00Z",
                first_available_ts="2026-01-05T14:30:01Z",
                last_available_ts="2026-01-05T14:33:03Z",
                lifecycle_state="VERSIONED",
            ),
        ),
        label_packs=(
            LabelPackHandle(
                label_version_id="label_rt_p10_fixture_v1",
                label_spec_id="label_spec_rt_p10",
                label_id="synthetic_label_rt_p10",
                dataset_version_id=DATASET_VERSION_ID,
                partition_id="development_partition",
                materialization_plan_id="label_plan_rt_p10",
                first_event_ts="2026-01-05T14:30:00Z",
                last_event_ts="2026-01-05T14:33:00Z",
                first_label_available_ts="2026-01-05T14:31:00Z",
                last_label_available_ts="2026-01-05T14:34:00Z",
                lifecycle_state="VERSIONED",
            ),
        ),
        dataset_scope={"symbol_universe": ["ES", "NQ", "RTY"]},
        partition_scope={"partition_id": "development_partition"},
        session_scope={"session": "RTH"},
        governance_metadata={"fixture": "rt_p10"},
    )
