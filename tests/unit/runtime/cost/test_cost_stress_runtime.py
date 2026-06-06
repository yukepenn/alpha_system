from __future__ import annotations

import json
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from alpha_system.runtime.contracts.run_record import StudyRunResultState
from alpha_system.runtime.cost import (
    CostModelVersion,
    CostStressSpec,
    build_cost_sensitivity_report,
    load_cost_stress_config,
)
from alpha_system.runtime.cost import runtime as cost_runtime
from alpha_system.runtime.cost.runtime import CostStressThresholds
from alpha_system.runtime.diagnostics.contracts import DiagnosticsRunSpecRef

FIXTURE_ROOT = Path("tests/fixtures/runtime/cost")
CONFIG_PATH = Path("configs/runtime/cost/default_cost_stress.json")


def test_runtime_consumes_backtest_primitives_and_produces_monotone_profiles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    version = _bbo_version()
    calls: list[str] = []
    original_cost_from_mapping = cost_runtime.costs.cost_model_from_mapping
    original_slippage_from_mapping = cost_runtime.slippage.slippage_model_from_mapping

    def cost_from_mapping(payload: Mapping[str, Any] | None):
        calls.append("cost_model_from_mapping")
        return original_cost_from_mapping(payload)

    def slippage_from_mapping(payload: Mapping[str, Any] | None):
        calls.append("slippage_model_from_mapping")
        return original_slippage_from_mapping(payload)

    monkeypatch.setattr(cost_runtime.costs, "cost_model_from_mapping", cost_from_mapping)
    monkeypatch.setattr(
        cost_runtime.slippage,
        "slippage_model_from_mapping",
        slippage_from_mapping,
    )

    report = _report(version, _fixture("synthetic_fills.json"))

    assert calls == ["cost_model_from_mapping", "slippage_model_from_mapping"]
    assert report.status is StudyRunResultState.DIAGNOSTICS_COMPLETE
    assert report.slippage_labeled_proxy is True
    assert report.bbo_spread_crossing_used is True
    assert report.bbo_unavailable_fallback_used is False
    assert [summary.profile_name for summary in report.profile_summaries] == [
        "base",
        "stress_1",
        "stress_2",
        "double_cost",
    ]
    combined = [summary.combined_cost_slippage_proxy for summary in report.profile_summaries]
    assert combined == sorted(combined)
    assert report.double_cost_summary.combined_cost_slippage_proxy > combined[0]
    assert "alpha_system.backtest.costs" in report.diagnostics_report.report_metadata[
        "orchestrated_backtest_primitives"
    ]


def test_runtime_uses_bps_fallback_marker_when_bbo_is_absent() -> None:
    report = _report(_bps_version(), _fixture("synthetic_fills_no_bbo.json"))

    assert report.status is StudyRunResultState.DIAGNOSTICS_COMPLETE
    assert report.bbo_spread_crossing_used is False
    assert report.bbo_unavailable_fallback_used is True
    assert report.diagnostics_report.coverage_summary["bbo_fill_count"] == 0


def test_session_penalty_config_is_applied_from_data() -> None:
    report = _report(_bps_version(), _fixture("synthetic_fills_no_bbo.json"))
    base_sessions = {
        summary.session_label: summary
        for summary in report.session_breakdown
        if summary.profile_name == "base"
    }

    assert (
        base_sessions["ETH"].session_cost_multiplier
        > base_sessions["RTH"].session_cost_multiplier
    )
    assert (
        base_sessions["ETH"].combined_cost_slippage_proxy
        > base_sessions["RTH"].combined_cost_slippage_proxy
    )


def test_fragile_result_carries_rejection_reason_and_stays_visible() -> None:
    report = _report(
        _bps_version(),
        _fixture("synthetic_fills_no_bbo.json"),
        thresholds=CostStressThresholds(max_double_cost_to_base_ratio=Decimal("1.5")),
    )

    assert report.status is StudyRunResultState.DIAGNOSTICS_FAILED
    assert report.rejection_reason is not None
    assert report.rejection_reason.code == "cost_fragile"
    assert report.to_dict()["rejection_reason_records"][0]["code"] == "cost_fragile"


def test_low_sample_result_is_visible_inconclusive() -> None:
    report = _report(
        _bps_version(),
        _fixture("synthetic_fills_no_bbo.json")[:1],
        thresholds=CostStressThresholds(min_fill_count=2),
    )

    assert report.status is StudyRunResultState.INCONCLUSIVE
    assert report.rejection_reason is not None
    assert report.rejection_reason.code == "low_sample"
    assert report.to_dict()["profile_summaries"][0]["fill_count"] == 1


def test_zero_cost_is_diagnostic_only_and_never_promotion_basis() -> None:
    report = _report(
        CostModelVersion.from_mappings(
            cost_model_descriptor={"model": "zero_cost", "fixture_only": True},
            slippage_model_descriptor={"model": "none", "fixture_only": True},
            bbo_available=False,
        ),
        _fixture("synthetic_fills_no_bbo.json"),
    )

    assert report.status is StudyRunResultState.DIAGNOSTICS_COMPLETE
    assert report.cost_model_version.zero_cost_diagnostic_only is True
    assert report.double_cost_summary.combined_cost_slippage_proxy == 0
    assert report.to_dict()["zero_cost_diagnostic_only"] is True
    assert report.to_dict()["promotion_basis_allowed"] is False
    assert all(summary.promotion_basis_allowed is False for summary in report.profile_summaries)


def _report(
    version: CostModelVersion,
    fills: list[dict[str, object]],
    *,
    thresholds: CostStressThresholds | None = None,
):
    return build_cost_sensitivity_report(
        diagnostics_run_spec=_diagnostics_spec_ref(),
        fills=fills,
        lineage_refs={
            "study_run_spec_id": "srun_" + "3" * 24,
            "dataset_version_id": "dsv_rt_p11_synthetic_fixture",
        },
        cost_stress_spec=CostStressSpec.from_mapping(
            load_cost_stress_config(CONFIG_PATH),
            cost_model_version=version,
        ),
        thresholds=thresholds,
    )


def _bbo_version() -> CostModelVersion:
    return CostModelVersion.from_mappings(
        cost_model_descriptor={
            "model": "composite",
            "components": [
                {"model": "spread_cost", "assumption": "half_spread"},
                {"model": "bps_cost", "bps": "1.0"},
            ],
        },
        slippage_model_descriptor={
            "model": "composite",
            "components": [
                {"model": "spread_sensitive", "spread_fraction": "0.25", "fallback_bps": "0.5"}
            ],
        },
        bbo_available=True,
    )


def _bps_version() -> CostModelVersion:
    return CostModelVersion.from_mappings(
        cost_model_descriptor={"model": "bps_cost", "bps": "1.0"},
        slippage_model_descriptor={"model": "bps", "bps": "0.5"},
        bbo_available=False,
    )


def _diagnostics_spec_ref() -> DiagnosticsRunSpecRef:
    return DiagnosticsRunSpecRef(
        diagnostics_run_spec_id="dspec_" + "1" * 24,
        content_hash="2" * 64,
    )


def _fixture(name: str) -> list[dict[str, object]]:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))
