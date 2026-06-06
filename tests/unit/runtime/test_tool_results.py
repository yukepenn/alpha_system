from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from alpha_system.runtime.contracts.artifacts import RuntimeArtifactEntry, RuntimeArtifactManifest
from alpha_system.runtime.contracts.manifest import StudyRunManifest
from alpha_system.runtime.contracts.run_record import StudyRunRecord, StudyRunResultState
from alpha_system.runtime.cost.report import (
    COST_SENSITIVITY_REPORT_KIND,
    CostProfileSummary,
    CostSensitivityReport,
    CostSessionSummary,
)
from alpha_system.runtime.decisions import (
    RejectionReasonCode,
    RejectionReasonRecord,
    RuntimeDecisionStage,
    RuntimeDecisionState,
)
from alpha_system.runtime.diagnostics.contracts import DiagnosticsFamily, DiagnosticsRunSpecRef
from alpha_system.runtime.diagnostics.report import DiagnosticsQualityGate, DiagnosticsReport
from alpha_system.runtime.tool_results import (
    RuntimeRunSummary,
    RuntimeToolResult,
    RuntimeToolResultContractError,
    RuntimeVersionIds,
)

PROHIBITED_MVP_STATES = {
    "ALPHA_VALIDATED",
    "FACTOR_PROMOTED",
    "STRATEGY_READY",
    "PORTFOLIO_READY",
    "LIVE_READY",
    "PAPER_READY",
    "PROFITABLE",
    "TRADABLE",
    "PRODUCTION_READY",
}


def test_tool_results_module_imports_and_contracts_are_value_free() -> None:
    result = _tool_result()
    same_result = _tool_result()
    summary = RuntimeRunSummary.from_tool_result(result)

    assert result.status is RuntimeDecisionState.COST_STRESS_COMPLETE
    assert result.version_ids == RuntimeVersionIds.from_manifest(_manifest())
    assert result == same_result
    assert hash(result)
    assert summary.to_dict() == result.to_dict()

    payload = result.to_dict()
    assert set(payload) == {
        "status",
        "run_id",
        "version_ids",
        "diagnostics_summary",
        "cost_summary",
        "rejection_reasons",
        "artifacts",
        "next_required_gate",
    }
    assert payload["diagnostics_summary"]["report_refs"][0]["report_kind"] == (
        "factor_diagnostics_summary"
    )
    assert payload["cost_summary"]["slippage_labeled_proxy"] is True
    assert payload["artifacts"] == [
        {
            "artifact_id": "diagnostic_summary",
            "location": "summaries/diagnostic-summary.json",
            "content_hash": "6" * 64,
        }
    ]
    assert "feature_values" not in str(payload)
    assert "label_values" not in str(payload)
    assert "canonical_bars" not in str(payload)
    assert "provider_payload" not in str(payload)
    assert ".parquet" not in str(payload)

    with pytest.raises(FrozenInstanceError):
        result.run_id = "changed"  # type: ignore[misc]


def test_tool_result_consumes_existing_run_record_and_manifest_contracts() -> None:
    record = StudyRunRecord(
        run_id="run_rt_p22_fixture",
        study_run_spec_ref={
            "study_run_spec_id": "srun_" + "1" * 24,
            "content_hash": "2" * 64,
        },
        result_state=StudyRunResultState.COST_STRESS_COMPLETE,
        manifest_ref=_manifest(),
        artifact_refs=[_artifact_manifest()],
    )

    result = RuntimeToolResult.from_study_run_record(
        study_run_record=record,
        manifest=_manifest(),
        diagnostics_summary=_diagnostics_report(),
        cost_summary=_cost_report(),
        next_required_gate="human_review",
    )

    assert result.run_id == record.run_id
    assert result.status is RuntimeDecisionState.COST_STRESS_COMPLETE
    assert result.artifacts[0].artifact_id == "diagnostic_summary"


@pytest.mark.parametrize("state", list(RuntimeDecisionState))
def test_status_is_closed_to_runtime_decision_states(state: RuntimeDecisionState) -> None:
    reasons = (
        (_reason(state),)
        if state
        in {
            RuntimeDecisionState.REJECTED,
            RuntimeDecisionState.INCONCLUSIVE,
            RuntimeDecisionState.BLOCKED,
        }
        else ()
    )

    result = _tool_result(status=state, rejection_reasons=reasons)

    assert result.status is state


@pytest.mark.parametrize("prohibited_state", sorted(PROHIBITED_MVP_STATES))
def test_prohibited_mvp_states_are_not_representable(prohibited_state: str) -> None:
    with pytest.raises(ValueError):
        _tool_result(status=prohibited_state)

    assert prohibited_state not in {state.value for state in RuntimeDecisionState}


def test_terminal_tool_results_require_matching_visible_reason_records() -> None:
    with pytest.raises(RuntimeToolResultContractError, match="require visible reasons"):
        _tool_result(status=RuntimeDecisionState.REJECTED)

    with pytest.raises(RuntimeToolResultContractError, match="must not carry rejection reasons"):
        _tool_result(
            status=RuntimeDecisionState.DIAGNOSTICS_COMPLETE,
            rejection_reasons=(_reason(RuntimeDecisionState.REJECTED),),
        )

    with pytest.raises(RuntimeToolResultContractError, match="must match"):
        _tool_result(
            status=RuntimeDecisionState.BLOCKED,
            rejection_reasons=(_reason(RuntimeDecisionState.REJECTED),),
        )

    result = _tool_result(
        status=StudyRunResultState.DIAGNOSTICS_FAILED,
        rejection_reasons=(_reason(RuntimeDecisionState.REJECTED),),
    )

    assert result.status is RuntimeDecisionState.REJECTED
    assert result.to_dict()["rejection_reasons"][0]["decision_state"] == "REJECTED"


@pytest.mark.parametrize(
    "overrides",
    [
        {
            "diagnostics_summary": {
                "coverage_summary": {"feature_values": 3},
                "quality_summary": {},
                "limitations": (),
            }
        },
        {
            "diagnostics_summary": {
                "coverage_summary": {"sample_count": [1, 2, 3]},
                "quality_summary": {},
                "limitations": (),
            }
        },
        {
            "artifacts": [
                {
                    "artifact_id": "raw_provider_payload",
                    "location": "summaries/provider-response.json",
                    "content_hash": "7" * 64,
                    "provider_payload": {"rows": [1]},
                }
            ]
        },
        {
            "artifacts": [
                {
                    "artifact_id": "heavy_values",
                    "location": "summaries/raw-values.parquet",
                    "content_hash": "8" * 64,
                }
            ]
        },
        {
            "version_ids": {
                "dataset_version_id": "data/raw/provider-dump",
                "feature_pack_ids": ["feature_pack_v1"],
                "label_pack_ids": ["label_pack_v1"],
                "code_version": "git:abcdef1234567890",
                "config_version": "config_runtime_fixture_v1",
            }
        },
        {
            "cost_summary": {
                "diagnostics_report_ref": {
                    "report_id": "dreport_fixture",
                    "report_hash": "9" * 64,
                    "report_kind": COST_SENSITIVITY_REPORT_KIND,
                },
                "cost_model_version_id": "cmv_fixture",
                "profile_count": 4,
                "double_cost_profile_name": "double_cost",
                "double_cost_combined_cost_slippage_proxy": "4",
                "slippage_labeled_proxy": False,
            }
        },
    ],
)
def test_tool_results_reject_raw_value_arrays_provider_payloads_and_heavy_artifacts(
    overrides: dict[str, object],
) -> None:
    with pytest.raises(RuntimeToolResultContractError):
        _tool_result(**overrides)


def test_from_dict_rejects_non_contract_fields() -> None:
    payload = _tool_result().to_dict()
    payload["canonical_bars"] = [{"ts": "not allowed"}]

    with pytest.raises(RuntimeToolResultContractError, match="unsupported or value-bearing"):
        RuntimeToolResult.from_dict(payload)


def _tool_result(**overrides: object) -> RuntimeToolResult:
    values: dict[str, object] = {
        "status": RuntimeDecisionState.COST_STRESS_COMPLETE,
        "run_id": "run_rt_p22_fixture",
        "version_ids": _manifest(),
        "diagnostics_summary": _diagnostics_report(),
        "cost_summary": _cost_report(),
        "rejection_reasons": (),
        "artifacts": [_artifact_manifest()],
        "next_required_gate": "human_review",
    }
    values.update(overrides)
    return RuntimeToolResult(**values)  # type: ignore[arg-type]


def _manifest() -> StudyRunManifest:
    return StudyRunManifest(
        run_id="run_rt_p22_fixture",
        dataset_version_id="dsv_synthetic_runtime_fixture_v1",
        dataset_version_hash="0" * 64,
        dataset_lineage_ref="dataset_lineage_fixture_v1",
        dataset_admissibility_state="VERSIONED",
        feature_pack_versions=[
            {
                "pack_id": "feature_pack_v1",
                "content_hash": "1" * 64,
                "lineage_ref": "feature_lineage_v1",
                "available_ts_ref": "features.available_ts",
            }
        ],
        label_pack_versions=[
            {
                "pack_id": "label_pack_v1",
                "content_hash": "2" * 64,
                "lineage_ref": "label_lineage_v1",
                "label_available_ts_ref": "labels.label_available_ts",
            }
        ],
        code_version="git:abcdef1234567890",
        code_content_hash="3" * 64,
        config_version="config_runtime_fixture_v1",
        config_hash="4" * 64,
        cost_model_version="cmv_fixture_v1",
        cost_model_hash="5" * 64,
    )


def _artifact_manifest() -> RuntimeArtifactManifest:
    return RuntimeArtifactManifest(
        run_id="run_rt_p22_fixture",
        entries=[
            RuntimeArtifactEntry(
                artifact_id="diagnostic_summary",
                kind="diagnostic_summary",
                location="summaries/diagnostic-summary.json",
                content_hash="6" * 64,
                size_bytes=512,
            )
        ],
    )


def _diagnostics_report() -> DiagnosticsReport:
    return DiagnosticsReport(
        report_kind="factor_diagnostics_summary",
        diagnostics_family=DiagnosticsFamily.FACTOR,
        diagnostics_run_spec_ref=_diagnostics_spec_ref("1"),
        status=StudyRunResultState.DIAGNOSTICS_COMPLETE,
        lineage_refs={
            "diagnostics_run_spec_id": "dspec_" + "1" * 24,
            "study_run_spec_id": "srun_" + "2" * 24,
            "dataset_version_id": "dsv_synthetic_runtime_fixture_v1",
            "feature_pack_ref": "feature_pack_v1",
            "label_pack_ref": "label_pack_v1",
        },
        coverage_summary={
            "coverage_ratio": 0.97,
            "missingness_rate": 0.03,
            "sample_count": 240,
        },
        quality_summary={
            "diagnostic_pass": True,
            "gate_count": 1,
            "failing_gate_count": 0,
        },
        limitations=("Synthetic summary only; diagnostics do not validate alpha.",),
        quality_gates=[
            DiagnosticsQualityGate(
                gate_id="coverage_gate",
                name="Coverage gate",
                status="PASS",
                summary="Coverage summary meets the descriptive gate threshold.",
                metric_refs={"coverage_ratio": 0.97, "threshold_ref": "diagnostics_quality_v1"},
            )
        ],
    )


def _cost_report() -> CostSensitivityReport:
    return CostSensitivityReport(
        diagnostics_report=DiagnosticsReport(
            report_kind=COST_SENSITIVITY_REPORT_KIND,
            diagnostics_family=DiagnosticsFamily.COST,
            diagnostics_run_spec_ref=_diagnostics_spec_ref("2"),
            status=StudyRunResultState.DIAGNOSTICS_COMPLETE,
            lineage_refs={"cost_model_version_id": "cmv_" + "3" * 24},
            coverage_summary={"fill_count": 1, "profile_count": 4},
            quality_summary={"double_cost_present": True, "slippage_labeled_proxy": True},
            limitations=("Cost stress is descriptive only.",),
        ),
        cost_model_version=_cost_model_version(),
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


def _cost_model_version():
    from alpha_system.runtime.cost import CostModelVersion

    return CostModelVersion.from_mappings(
        cost_model_descriptor={"model": "bps_cost", "bps": "1.0"},
        slippage_model_descriptor={"model": "bps", "bps": "0.5"},
        bbo_available=False,
    )


def _diagnostics_spec_ref(seed: str) -> DiagnosticsRunSpecRef:
    return DiagnosticsRunSpecRef(
        diagnostics_run_spec_id="dspec_" + seed * 24,
        content_hash=seed * 64,
    )


def _reason(state: RuntimeDecisionState) -> RejectionReasonRecord:
    code = {
        RuntimeDecisionState.BLOCKED: RejectionReasonCode.BLOCKED_BY_POLICY,
        RuntimeDecisionState.INCONCLUSIVE: RejectionReasonCode.INCONCLUSIVE,
    }.get(state, RejectionReasonCode.WEAK_DIAGNOSTICS)
    return RejectionReasonRecord(
        code=code,
        message="Synthetic runtime tool result reason remains visible.",
        decision_state=state,
        stage=RuntimeDecisionStage.DIAGNOSTICS,
        source_code=f"source_{code.value}",
    )
