from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from alpha_system.runtime.contracts.run_record import RunRejectionReason, StudyRunResultState
from alpha_system.runtime.diagnostics.contracts import DiagnosticsFamily, DiagnosticsRunSpecRef
from alpha_system.runtime.diagnostics.report import (
    DiagnosticsQualityGate,
    DiagnosticsQualityGateStatus,
    DiagnosticsReport,
    DiagnosticsReportContractError,
)


def test_diagnostics_report_is_descriptive_non_promotional_and_value_free() -> None:
    report = _report()
    same_report = _report()

    assert report.status is StudyRunResultState.DIAGNOSTICS_COMPLETE
    assert report.report_hash == same_report.report_hash
    assert hash(report)

    payload = report.to_dict()
    assert payload["descriptive_only"] is True
    assert payload["non_promotional"] is True
    assert payload["raw_or_heavy_data_embedded"] is False
    assert payload["diagnostic_pass_is_alpha_validation"] is False
    assert payload["value_free"] is True
    assert payload["limitations"] == [
        "Synthetic summary-only fixture; diagnostics do not validate alpha."
    ]
    assert payload["quality_gates"][0]["status"] == "PASS"
    assert "values" not in str(payload)
    assert "provider_rows" not in str(payload)
    assert "canonical_bars" not in str(payload)

    with pytest.raises(FrozenInstanceError):
        report.report_kind = "changed"  # type: ignore[misc]


def test_quality_gate_shape_is_scalar_only() -> None:
    gate = DiagnosticsQualityGate(
        gate_id="coverage_gate",
        name="Coverage gate",
        status=DiagnosticsQualityGateStatus.WARN,
        summary="Coverage is below the preferred descriptive threshold.",
        metric_refs={"coverage_ratio": 0.88, "threshold_ref": "diagnostics_quality_v1"},
        limitations=("Synthetic scalar summary only.",),
    )

    assert gate.metric_refs == {"coverage_ratio": 0.88, "threshold_ref": "diagnostics_quality_v1"}
    assert gate.to_dict()["limitations"] == ["Synthetic scalar summary only."]

    with pytest.raises(DiagnosticsReportContractError):
        DiagnosticsQualityGate(
            gate_id="raw_rows",
            name="Raw rows",
            status="PASS",
            summary="Invalid gate.",
            metric_refs={"provider_rows": 12},
        )


def test_report_requires_limitations_coverage_and_quality_summary() -> None:
    with pytest.raises(DiagnosticsReportContractError, match="limitations"):
        _report(limitations=())

    with pytest.raises(DiagnosticsReportContractError, match="coverage_summary"):
        _report(coverage_summary={})

    with pytest.raises(DiagnosticsReportContractError, match="quality_summary"):
        _report(quality_summary={})


@pytest.mark.parametrize(
    "overrides",
    [
        {"coverage_summary": {"provider_rows": 100}},
        {"quality_summary": {"score_array": [0.1, 0.2]}},
        {"lineage_refs": {"report_artifact": "diagnostics/raw-values.parquet"}},
        {"report_metadata": {"label_values": "not allowed"}},
    ],
)
def test_report_rejects_raw_value_arrays_and_heavy_data_refs(overrides: dict[str, object]) -> None:
    with pytest.raises(DiagnosticsReportContractError):
        _report(**overrides)


def test_report_rejects_promotional_claim_language() -> None:
    with pytest.raises(DiagnosticsReportContractError, match="promotional claims"):
        _report(limitations=("This factor is tradable.",))

    with pytest.raises(DiagnosticsReportContractError, match="promotional claims"):
        _report(quality_summary={"interpretation": "alpha validated"})


@pytest.mark.parametrize(
    "failure_state",
    [
        StudyRunResultState.DIAGNOSTICS_FAILED,
        StudyRunResultState.REJECTED,
        StudyRunResultState.INCONCLUSIVE,
        StudyRunResultState.BLOCKED,
    ],
)
def test_failed_report_requires_visible_rejection_reason(
    failure_state: StudyRunResultState,
) -> None:
    with pytest.raises(DiagnosticsReportContractError, match="visible rejection reason"):
        _report(status=failure_state)

    report = _report(
        status=failure_state,
        rejection_reasons=[
            RunRejectionReason(
                code="low_sample",
                message="Diagnostics could not produce a reliable descriptive summary.",
            )
        ],
    )

    assert report.to_dict()["rejection_reason_records"] == [
        {
            "code": "low_sample",
            "message": "Diagnostics could not produce a reliable descriptive summary.",
        }
    ]


def test_report_ref_links_to_diagnostics_run_record_without_values() -> None:
    ref = _report().to_ref()

    assert ref.report_id.startswith("dreport_")
    assert ref.report_hash
    assert ref.to_dict() == {
        "report_id": ref.report_id,
        "report_hash": ref.report_hash,
        "report_kind": "factor_diagnostics_summary",
    }


def _report(**overrides: object) -> DiagnosticsReport:
    values: dict[str, object] = {
        "report_kind": "factor_diagnostics_summary",
        "diagnostics_family": DiagnosticsFamily.FACTOR,
        "diagnostics_run_spec_ref": _diagnostics_spec_ref(),
        "status": StudyRunResultState.DIAGNOSTICS_COMPLETE,
        "lineage_refs": {
            "diagnostics_run_spec_id": "dspec_" + "1" * 24,
            "study_run_spec_id": "srun_" + "2" * 24,
            "dataset_version_id": "dsv_synthetic_feature_label_fixture_v1",
            "feature_pack_ref": "feature_pack_v1",
            "label_pack_ref": "label_pack_v1",
            "runtime_plan_ref": "rplan_" + "3" * 24,
        },
        "coverage_summary": {
            "coverage_ratio": 0.97,
            "missingness_rate": 0.03,
            "sample_count": 240,
        },
        "quality_summary": {
            "diagnostic_pass": True,
            "gate_count": 1,
            "failing_gate_count": 0,
        },
        "limitations": ("Synthetic summary-only fixture; diagnostics do not validate alpha.",),
        "quality_gates": [
            DiagnosticsQualityGate(
                gate_id="coverage_gate",
                name="Coverage gate",
                status=DiagnosticsQualityGateStatus.PASS,
                summary="Coverage summary meets the descriptive gate threshold.",
                metric_refs={"coverage_ratio": 0.97, "threshold_ref": "diagnostics_quality_v1"},
            )
        ],
        "rejection_reasons": (),
        "report_metadata": {"generated_by": "rt_p06_contract_test"},
    }
    values.update(overrides)
    return DiagnosticsReport(**values)  # type: ignore[arg-type]


def _diagnostics_spec_ref() -> DiagnosticsRunSpecRef:
    return DiagnosticsRunSpecRef(
        diagnostics_run_spec_id="dspec_" + "1" * 24,
        content_hash="4" * 64,
    )
