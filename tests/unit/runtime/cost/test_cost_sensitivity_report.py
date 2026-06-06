from __future__ import annotations

from decimal import Decimal

import pytest

from alpha_system.runtime.contracts.run_record import StudyRunResultState
from alpha_system.runtime.cost.report import (
    COST_SENSITIVITY_REPORT_KIND,
    CostProfileSummary,
    CostSensitivityReport,
    CostSensitivityReportError,
    CostSessionSummary,
)
from alpha_system.runtime.diagnostics.contracts import DiagnosticsFamily, DiagnosticsRunSpecRef
from alpha_system.runtime.diagnostics.report import DiagnosticsReport


def test_cost_sensitivity_report_wraps_shared_diagnostics_shape() -> None:
    report = CostSensitivityReport(
        diagnostics_report=_diagnostics_report(),
        cost_model_version=_version(),
        profile_summaries=(
            _profile("base", Decimal("1")),
            _profile("stress_1", Decimal("1.25")),
            _profile("stress_2", Decimal("1.5")),
            _profile("double_cost", Decimal("2")),
        ),
        session_breakdown=(
            CostSessionSummary(
                profile_name="base",
                session_label="RTH",
                fill_count=1,
                cost_total=Decimal("1"),
                slippage_proxy_total=Decimal("0.5"),
                combined_cost_slippage_proxy=Decimal("1.5"),
                session_cost_multiplier=Decimal("1"),
                session_slippage_multiplier=Decimal("1"),
            ),
        ),
        cost_gradient_items=(("double_to_base_combined_ratio", "2"),),
        slippage_labeled_proxy=True,
        bbo_spread_crossing_used=False,
        bbo_unavailable_fallback_used=True,
    )

    payload = report.to_dict()
    assert report.status is StudyRunResultState.DIAGNOSTICS_COMPLETE
    assert payload["report_type"] == "CostSensitivityReport"
    assert payload["descriptive_only"] is True
    assert payload["non_promotional"] is True
    assert payload["slippage_labeled_proxy"] is True
    assert payload["promotion_basis_allowed"] is False
    assert payload["double_cost_summary"]["profile_name"] == "double_cost"


def test_cost_sensitivity_report_requires_proxy_label_and_double_cost() -> None:
    with pytest.raises(CostSensitivityReportError, match="double_cost"):
        CostSensitivityReport(
            diagnostics_report=_diagnostics_report(),
            cost_model_version=_version(),
            profile_summaries=(_profile("base", Decimal("1")),),
            session_breakdown=(),
            cost_gradient_items=(),
        )

    with pytest.raises(CostSensitivityReportError, match="proxy"):
        CostSensitivityReport(
            diagnostics_report=_diagnostics_report(),
            cost_model_version=_version(),
            profile_summaries=(
                _profile("base", Decimal("1")),
                _profile("stress_1", Decimal("1.25")),
                _profile("stress_2", Decimal("1.5")),
                _profile("double_cost", Decimal("2")),
            ),
            session_breakdown=(),
            cost_gradient_items=(),
            slippage_labeled_proxy=False,
        )


def _profile(name: str, multiplier: Decimal) -> CostProfileSummary:
    return CostProfileSummary(
        profile_name=name,
        fill_count=1,
        bbo_fill_count=0,
        cost_total=multiplier,
        slippage_proxy_total=multiplier,
        combined_cost_slippage_proxy=multiplier * 2,
        cost_multiplier=multiplier,
        slippage_multiplier=multiplier,
        bbo_spread_crossing_used=False,
        bbo_unavailable_fallback_used=True,
        zero_cost_diagnostic_only=False,
    )


def _diagnostics_report() -> DiagnosticsReport:
    return DiagnosticsReport(
        report_kind=COST_SENSITIVITY_REPORT_KIND,
        diagnostics_family=DiagnosticsFamily.COST,
        diagnostics_run_spec_ref=DiagnosticsRunSpecRef(
            diagnostics_run_spec_id="dspec_" + "1" * 24,
            content_hash="2" * 64,
        ),
        status=StudyRunResultState.DIAGNOSTICS_COMPLETE,
        lineage_refs={"cost_model_version_id": "cmv_" + "3" * 24},
        coverage_summary={"fill_count": 1, "profile_count": 4},
        quality_summary={"double_cost_present": True, "slippage_labeled_proxy": True},
        limitations=("Cost stress is descriptive only.",),
    )


def _version():
    from alpha_system.runtime.cost import CostModelVersion

    return CostModelVersion.from_mappings(
        cost_model_descriptor={"model": "bps_cost", "bps": "1.0"},
        slippage_model_descriptor={"model": "bps", "bps": "0.5"},
        bbo_available=False,
    )
