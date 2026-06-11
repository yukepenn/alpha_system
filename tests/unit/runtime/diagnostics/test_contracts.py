from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

import alpha_system.runtime.diagnostics as diagnostics
from alpha_system.runtime.contracts.run_record import RunRejectionReason, StudyRunResultState
from alpha_system.runtime.diagnostics.contracts import (
    DiagnosticsContractError,
    DiagnosticsFamily,
    DiagnosticsHalfLifeProtocol,
    DiagnosticsReportRef,
    DiagnosticsRunRecord,
    DiagnosticsRunSpec,
    RuntimePlanRef,
)


def test_diagnostics_package_surface_exposes_shared_contracts() -> None:
    assert diagnostics.DiagnosticsRunSpec is DiagnosticsRunSpec
    assert diagnostics.DiagnosticsRunRecord is DiagnosticsRunRecord
    assert diagnostics.DiagnosticsFamily is DiagnosticsFamily
    assert diagnostics.DiagnosticsHalfLifeProtocol is DiagnosticsHalfLifeProtocol


def test_diagnostics_run_spec_is_immutable_hashable_and_reference_only() -> None:
    spec = _diagnostics_spec()
    same_spec = _diagnostics_spec()

    assert spec.diagnostics_family is DiagnosticsFamily.FACTOR
    assert spec.requested_state is StudyRunResultState.DIAGNOSTICS_READY
    assert spec.content_hash == same_spec.content_hash
    assert hash(spec)

    payload = spec.to_dict()
    assert payload["value_free"] is True
    assert payload["execution_outcome"] is None
    assert "study_run_spec_ref" in payload
    assert "runtime_plan_ref" in payload
    assert "runtime_plan" not in payload
    assert "values" not in str(payload)
    assert "rows" not in str(payload)

    with pytest.raises(FrozenInstanceError):
        spec.diagnostics_family = DiagnosticsFamily.LABEL  # type: ignore[misc]


def test_diagnostics_run_spec_requires_runtime_plan_ref_for_spec_refs() -> None:
    with pytest.raises(DiagnosticsContractError, match="runtime_plan is required"):
        DiagnosticsRunSpec(
            diagnostics_family=DiagnosticsFamily.FACTOR,
            study_run_spec=_study_run_spec_ref(),
        )


def test_diagnostics_run_spec_rejects_inline_payloads_in_reference_mappings() -> None:
    with pytest.raises(DiagnosticsContractError, match="non-reference fields"):
        DiagnosticsRunSpec(
            diagnostics_family=DiagnosticsFamily.FACTOR,
            study_run_spec={
                **_study_run_spec_ref(),
                "runtime_plan": {"rows": [1, 2, 3]},
            },
            runtime_plan=_runtime_plan_ref(),
        )


def test_diagnostics_record_uses_established_runtime_result_states() -> None:
    record = DiagnosticsRunRecord(
        diagnostics_run_spec_ref=_diagnostics_spec(),
        status=StudyRunResultState.DIAGNOSTICS_RUNNING,
    )

    assert record.status is StudyRunResultState.DIAGNOSTICS_RUNNING
    assert record.to_dict()["status"] == "DIAGNOSTICS_RUNNING"

    with pytest.raises(DiagnosticsContractError):
        DiagnosticsRunRecord(
            diagnostics_run_spec_ref=_diagnostics_spec(),
            status=StudyRunResultState.SIGNAL_PROBE_READY,
        )

    with pytest.raises(DiagnosticsContractError):
        DiagnosticsRunRecord(
            diagnostics_run_spec_ref=_diagnostics_spec(),
            status="ALPHA_VALIDATED",
        )


def test_completed_diagnostics_record_requires_report_ref() -> None:
    with pytest.raises(DiagnosticsContractError, match="requires a diagnostics report ref"):
        DiagnosticsRunRecord(
            diagnostics_run_spec_ref=_diagnostics_spec(),
            status=StudyRunResultState.DIAGNOSTICS_COMPLETE,
        )

    record = DiagnosticsRunRecord(
        diagnostics_run_spec_ref=_diagnostics_spec(),
        status=StudyRunResultState.DIAGNOSTICS_COMPLETE,
        report_ref=_report_ref(),
    )

    assert record.report_ref == _report_ref()
    assert record.to_dict()["report_ref"] == _report_ref().to_dict()


@pytest.mark.parametrize(
    "failure_state",
    [
        StudyRunResultState.DIAGNOSTICS_FAILED,
        StudyRunResultState.REJECTED,
        StudyRunResultState.INCONCLUSIVE,
        StudyRunResultState.BLOCKED,
    ],
)
def test_failed_or_inconclusive_diagnostics_records_keep_rejection_reasons_visible(
    failure_state: StudyRunResultState,
) -> None:
    with pytest.raises(DiagnosticsContractError, match="visible rejection reason"):
        DiagnosticsRunRecord(
            diagnostics_run_spec_ref=_diagnostics_spec(),
            status=failure_state,
        )

    record = DiagnosticsRunRecord(
        diagnostics_run_spec_ref=_diagnostics_spec(),
        status=failure_state,
        rejection_reasons=[
            RunRejectionReason(
                code="weak_diagnostics",
                message="Diagnostics were inconclusive under the configured quality gate.",
            )
        ],
    )

    assert record.rejection_reasons[0].code == "weak_diagnostics"
    assert record.to_dict()["rejection_reason_records"] == [
        {
            "code": "weak_diagnostics",
            "message": "Diagnostics were inconclusive under the configured quality gate.",
        }
    ]


def test_diagnostics_record_rejects_inline_report_values() -> None:
    with pytest.raises(DiagnosticsContractError, match="non-reference fields"):
        DiagnosticsRunRecord(
            diagnostics_run_spec_ref=_diagnostics_spec(),
            status=StudyRunResultState.DIAGNOSTICS_COMPLETE,
            report_ref={
                **_report_ref().to_dict(),
                "provider_rows": [{"not": "allowed"}],
            },
        )


def _diagnostics_spec() -> DiagnosticsRunSpec:
    return DiagnosticsRunSpec(
        diagnostics_family=DiagnosticsFamily.FACTOR,
        study_run_spec=_study_run_spec_ref(),
        runtime_plan=_runtime_plan_ref(),
        spec_metadata={"requested_by": "rt_p06_contract_test"},
    )


def _study_run_spec_ref() -> dict[str, str]:
    return {
        "study_run_spec_id": "srun_" + "1" * 24,
        "content_hash": "2" * 64,
    }


def _runtime_plan_ref() -> RuntimePlanRef:
    return RuntimePlanRef(plan_id="rplan_" + "3" * 24, content_hash="4" * 64)


def _report_ref() -> DiagnosticsReportRef:
    return DiagnosticsReportRef(
        report_id="dreport_" + "5" * 24,
        report_hash="6" * 64,
        report_kind="factor_diagnostics_summary",
    )
