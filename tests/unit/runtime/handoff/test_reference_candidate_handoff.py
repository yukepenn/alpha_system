from __future__ import annotations

from decimal import Decimal

from alpha_system.governance.ids import GovernanceIdKind, generate_governance_id
from alpha_system.runtime.audit.no_lookahead import (
    NoLookaheadAuditOutcome,
    NoLookaheadAuditReason,
    NoLookaheadAuditResult,
    NoLookaheadRejectionCategory,
)
from alpha_system.runtime.contracts.artifacts import (
    RuntimeArtifactEntry,
    RuntimeArtifactManifest,
)
from alpha_system.runtime.contracts.manifest import (
    FeaturePackVersionRef,
    LabelPackVersionRef,
    StudyRunManifest,
)
from alpha_system.runtime.contracts.run_record import (
    RunRejectionReason,
    StudyRunRecord,
    StudyRunResultState,
)
from alpha_system.runtime.cost.model_version import CostModelVersion
from alpha_system.runtime.cost.report import (
    COST_SENSITIVITY_REPORT_KIND,
    CostProfileSummary,
    CostSensitivityReport,
    CostSessionSummary,
)
from alpha_system.runtime.decisions import (
    RejectionReasonCode,
    RejectionReasonRecord,
    RuntimeDecision,
    RuntimeDecisionStage,
    RuntimeDecisionState,
)
from alpha_system.runtime.diagnostics.contracts import DiagnosticsFamily, DiagnosticsRunSpecRef
from alpha_system.runtime.diagnostics.report import (
    DiagnosticsQualityGate,
    DiagnosticsQualityGateStatus,
    DiagnosticsReport,
)
from alpha_system.runtime.evidence import EvidenceDraft, build_evidence_draft
from alpha_system.runtime.handoff import (
    REFERENCE_VALIDATION_REQUIRED,
    ReferenceCandidateHandoff,
    build_reference_candidate_handoff,
)
from alpha_system.runtime.probe.report import SignalProbeReport, ThresholdProbeSummary
from alpha_system.runtime.probe.spec import SignalProbeSpecRef

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


def test_reference_handoff_ready_bundles_references_and_gate_requirements() -> None:
    cost_report = _cost_report()
    manifest = _manifest(cost_report)
    draft = _evidence_draft(cost_report=cost_report, manifest=manifest)
    artifact_manifest = _artifact_manifest(manifest)
    audit = _passed_audit()

    handoff = build_reference_candidate_handoff(
        alpha_spec_id=_alpha_spec_id(),
        study_spec_id=_study_spec_id(),
        evidence_draft=draft,
        study_run_manifest=manifest,
        runtime_artifact_manifest=artifact_manifest,
        factor_diagnostics_report=_diagnostics_report(
            report_kind="factor_diagnostics_summary",
            family=DiagnosticsFamily.FACTOR,
        ),
        label_diagnostics_report=_diagnostics_report(
            report_kind="label_diagnostics_summary",
            family=DiagnosticsFamily.LABEL,
        ),
        cost_sensitivity_report=cost_report,
        signal_probe_report=_signal_probe_report(cost_report),
        no_lookahead_audit_result=audit,
        limitations=("Synthetic RT-P17 handoff fixture only.",),
    )

    payload = handoff.to_dict()

    assert isinstance(handoff, ReferenceCandidateHandoff)
    assert handoff.decision_state is RuntimeDecisionState.REFERENCE_HANDOFF_READY
    assert handoff.strategy_not_validated is True
    assert payload["reference_requirements"]["next_required_gate"] == (
        REFERENCE_VALIDATION_REQUIRED
    )
    assert payload["reference_requirements"]["reference_validation_performed"] is False
    assert payload["evidence_draft_ref"]["source_id"] == draft.draft_id
    assert payload["study_run_manifest_ref"]["source_id"] == manifest.manifest_id
    assert payload["runtime_artifact_manifest_ref"]["source_id"] == (artifact_manifest.manifest_id)
    assert payload["version_lineage"]["dataset_version_id"] == manifest.dataset_version_id
    assert payload["version_lineage"]["feature_pack_versions"][0]["availability_ref"] == (
        "feature_available_ts_ref_rt_p17"
    )
    assert payload["version_lineage"]["label_pack_versions"][0]["availability_ref"] == (
        "label_available_ts_ref_rt_p17"
    )
    assert payload["cost_stress"]["cost_model_version_ref"]["source_id"] == (
        cost_report.cost_model_version.cost_model_version_id
    )
    assert {item["profile_name"] for item in payload["cost_stress"]["profile_refs"]} == {
        "base",
        "double_cost",
    }
    assert handoff.not_reference_validation is True
    assert hash(handoff)


def test_missing_cost_stress_blocks_handoff_with_visible_reason() -> None:
    cost_report = _cost_report()
    manifest = _manifest(cost_report)
    draft = _evidence_draft(cost_report=cost_report, manifest=manifest)

    handoff = build_reference_candidate_handoff(
        alpha_spec_id=_alpha_spec_id(),
        study_spec_id=_study_spec_id(),
        evidence_draft=draft,
        study_run_manifest=manifest,
        runtime_artifact_manifest=_artifact_manifest(manifest),
        cost_sensitivity_report=None,
        no_lookahead_audit_result=_passed_audit(),
    )

    reason = handoff.terminal_rejection_reasons[0]

    assert handoff.decision_state is RuntimeDecisionState.BLOCKED
    assert reason.code is RejectionReasonCode.BLOCKED_BY_POLICY
    assert reason.stage == RuntimeDecisionStage.COST_STRESS.value
    assert reason.source_code == "missing_cost_sensitivity_report"
    assert handoff.to_dict()["cost_stress"] is None


def test_missing_base_profile_blocks_handoff_fail_closed() -> None:
    incomplete_cost_report = _cost_report(include_base=False)
    complete_cost_report = _cost_report()
    manifest = _manifest(complete_cost_report)
    draft = _evidence_draft(cost_report=complete_cost_report, manifest=manifest)

    handoff = build_reference_candidate_handoff(
        alpha_spec_id=_alpha_spec_id(),
        study_spec_id=_study_spec_id(),
        evidence_draft=draft,
        study_run_manifest=manifest,
        runtime_artifact_manifest=_artifact_manifest(manifest),
        cost_sensitivity_report=incomplete_cost_report,
        no_lookahead_audit_result=_passed_audit(),
    )

    reason = handoff.terminal_rejection_reasons[0]

    assert handoff.decision_state is RuntimeDecisionState.BLOCKED
    assert reason.source_code == "missing_required_cost_profiles"
    assert reason.source_id == "base"


def test_rejected_no_lookahead_audit_blocks_reference_handoff() -> None:
    cost_report = _cost_report()
    manifest = _manifest(cost_report)
    draft = _evidence_draft(cost_report=cost_report, manifest=manifest)
    audit = NoLookaheadAuditResult(
        outcome=NoLookaheadAuditOutcome.REJECTED,
        reasons=(
            NoLookaheadAuditReason(
                code="feature_available_ts_after_decision_ts",
                category=NoLookaheadRejectionCategory.LEAKAGE_RISK,
                message="Synthetic feature availability violated decision-time ordering.",
                field="feature_inputs[0].available_ts",
                expected="available_ts <= decision_ts",
                actual="available_ts > decision_ts",
            ),
        ),
    )

    handoff = build_reference_candidate_handoff(
        alpha_spec_id=_alpha_spec_id(),
        study_spec_id=_study_spec_id(),
        evidence_draft=draft,
        study_run_manifest=manifest,
        runtime_artifact_manifest=_artifact_manifest(manifest),
        cost_sensitivity_report=cost_report,
        no_lookahead_audit_result=audit,
    )

    payload = handoff.to_dict()

    assert handoff.decision_state is RuntimeDecisionState.BLOCKED
    assert handoff.terminal_rejection_reasons[0].code is RejectionReasonCode.LEAKAGE_RISK
    assert payload["no_lookahead_audit_ref"]["status"] == "REJECTED"
    assert payload["reference_requirements"]["next_required_gate"] == (
        REFERENCE_VALIDATION_REQUIRED
    )


def test_terminal_evidence_draft_stays_terminal_in_handoff() -> None:
    cost_report = _cost_report()
    manifest = _manifest(cost_report)
    reason = RejectionReasonRecord(
        code=RejectionReasonCode.INCONCLUSIVE,
        message="Synthetic diagnostics remained inconclusive.",
        decision_state=RuntimeDecisionState.INCONCLUSIVE,
        stage=RuntimeDecisionStage.DIAGNOSTICS,
        source_code="synthetic_diagnostics_inconclusive",
    )
    draft = build_evidence_draft(
        alpha_spec_id=_alpha_spec_id(),
        study_spec_id=_study_spec_id(),
        trial_refs=(_trial_id(),),
        study_run_manifest=manifest,
        study_run_record=_study_run_record(
            manifest,
            result_state=StudyRunResultState.INCONCLUSIVE,
            rejection_reasons=(
                RunRejectionReason(
                    code="synthetic_diagnostics_inconclusive",
                    message="Synthetic diagnostics remained inconclusive.",
                ),
            ),
        ),
        decision=RuntimeDecision(
            state=RuntimeDecisionState.INCONCLUSIVE,
            reasons=(reason,),
        ),
        negative_control_results=_negative_control_results(),
    )

    handoff = build_reference_candidate_handoff(
        alpha_spec_id=_alpha_spec_id(),
        study_spec_id=_study_spec_id(),
        evidence_draft=draft,
        study_run_manifest=manifest,
        runtime_artifact_manifest=_artifact_manifest(manifest),
        cost_sensitivity_report=None,
        no_lookahead_audit_result=None,
    )

    assert handoff.decision_state is RuntimeDecisionState.INCONCLUSIVE
    assert handoff.terminal_rejection_reasons == (reason,)


def test_handoff_payload_is_scope_honest_and_value_free() -> None:
    cost_report = _cost_report()
    manifest = _manifest(cost_report)
    handoff = build_reference_candidate_handoff(
        alpha_spec_id=_alpha_spec_id(),
        study_spec_id=_study_spec_id(),
        evidence_draft=_evidence_draft(cost_report=cost_report, manifest=manifest),
        study_run_manifest=manifest,
        runtime_artifact_manifest=_artifact_manifest(manifest),
        cost_sensitivity_report=cost_report,
        no_lookahead_audit_result=_passed_audit(),
    )

    payload = handoff.to_dict()
    payload_text = str(payload).lower()

    assert payload["strategy_not_validated"] is True
    assert payload["not_reference_validation"] is True
    assert payload["not_promotion"] is True
    assert payload["not_alpha_validation"] is True
    assert payload["raw_or_heavy_data_embedded"] is False
    assert "alpha validated" not in payload_text
    assert "profitable" not in payload_text
    assert "tradable" not in payload_text
    assert ".parquet" not in payload_text
    assert "feature_values" not in payload_text
    assert "label_values" not in payload_text
    assert "raw_values" not in payload_text


def _alpha_spec_id() -> str:
    return generate_governance_id(GovernanceIdKind.ALPHA_SPEC, {"name": "rt_p17_alpha"})


def _study_spec_id() -> str:
    return generate_governance_id(GovernanceIdKind.STUDY_SPEC, {"name": "rt_p17_study"})


def _trial_id() -> str:
    return generate_governance_id(
        GovernanceIdKind.TRIAL_LEDGER_RECORD,
        {"name": "rt_p17_trial"},
    )


def _passed_audit() -> NoLookaheadAuditResult:
    return NoLookaheadAuditResult(outcome=NoLookaheadAuditOutcome.POINT_IN_TIME_SAFE)


def _manifest(cost_report: CostSensitivityReport) -> StudyRunManifest:
    return StudyRunManifest(
        run_id="run_rt_p17_synthetic",
        dataset_version_id="dataset_version_rt_p17",
        dataset_version_hash=HASH_A,
        dataset_lineage_ref="dataset_lineage_rt_p17",
        dataset_admissibility_state="READY_FOR_RESEARCH",
        feature_pack_versions=(
            FeaturePackVersionRef(
                pack_id="factor_pack_rt_p17",
                content_hash=HASH_A,
                lineage_ref="feature_lineage_rt_p17",
                available_ts_ref="feature_available_ts_ref_rt_p17",
            ),
        ),
        label_pack_versions=(
            LabelPackVersionRef(
                pack_id="label_pack_rt_p17",
                content_hash=HASH_B,
                lineage_ref="label_lineage_rt_p17",
                label_available_ts_ref="label_available_ts_ref_rt_p17",
            ),
        ),
        code_version="code_version_rt_p17",
        code_content_hash=HASH_A,
        config_version="config_version_rt_p17",
        config_hash=HASH_B,
        cost_model_version=cost_report.cost_model_version.cost_model_version_id,
        cost_model_hash=cost_report.cost_model_version.content_hash,
    )


def _study_run_record(
    manifest: StudyRunManifest,
    *,
    result_state: StudyRunResultState = StudyRunResultState.COST_STRESS_COMPLETE,
    rejection_reasons: tuple[RunRejectionReason, ...] = (),
) -> StudyRunRecord:
    return StudyRunRecord(
        run_id=manifest.run_id,
        study_run_spec_ref={
            "study_run_spec_id": "study_run_spec_rt_p17",
            "content_hash": HASH_A,
        },
        result_state=result_state,
        manifest_ref=manifest,
        rejection_reasons=rejection_reasons,
    )


def _artifact_manifest(manifest: StudyRunManifest) -> RuntimeArtifactManifest:
    return RuntimeArtifactManifest(
        run_id=manifest.run_id,
        entries=(
            RuntimeArtifactEntry(
                artifact_id="rt_p17_runtime_summary",
                kind="summary",
                location="runtime_summaries/rt_p17_summary.md",
                content_hash=HASH_C,
                size_bytes=128,
                local_only=True,
                commit_allowed=False,
            ),
        ),
    )


def _evidence_draft(
    *,
    cost_report: CostSensitivityReport,
    manifest: StudyRunManifest,
) -> EvidenceDraft:
    return build_evidence_draft(
        alpha_spec_id=_alpha_spec_id(),
        study_spec_id=_study_spec_id(),
        trial_refs=(_trial_id(),),
        study_run_manifest=manifest,
        study_run_record=_study_run_record(manifest),
        factor_diagnostics_report=_diagnostics_report(
            report_kind="factor_diagnostics_summary",
            family=DiagnosticsFamily.FACTOR,
        ),
        label_diagnostics_report=_diagnostics_report(
            report_kind="label_diagnostics_summary",
            family=DiagnosticsFamily.LABEL,
        ),
        cost_sensitivity_report=cost_report,
        signal_probe_report=_signal_probe_report(cost_report),
        no_lookahead_audit_result=_passed_audit(),
        negative_control_results=_negative_control_results(),
    )


def _diagnostics_report(
    *,
    report_kind: str,
    family: DiagnosticsFamily,
) -> DiagnosticsReport:
    return DiagnosticsReport(
        report_kind=report_kind,
        diagnostics_family=family,
        diagnostics_run_spec_ref=DiagnosticsRunSpecRef(
            diagnostics_run_spec_id=f"diagnostics_spec_{family.value}",
            content_hash=HASH_A,
        ),
        status=StudyRunResultState.DIAGNOSTICS_COMPLETE,
        lineage_refs={"dataset_version_id": "dataset_version_rt_p17"},
        coverage_summary={"sample_count": 8, "coverage_ratio": 1.0},
        quality_summary={"gate_count": 1, "complete": True},
        limitations=("Synthetic diagnostics summary only.",),
        quality_gates=(
            DiagnosticsQualityGate(
                gate_id=f"{family.value}_gate",
                name=f"{family.value} synthetic gate",
                status=DiagnosticsQualityGateStatus.PASS,
                summary="Synthetic gate passed as descriptive metadata only.",
                metric_refs={"sample_count": 8},
                limitations=("Synthetic fixture only.",),
            ),
        ),
        report_metadata={
            "orchestrated_runtime_surface": f"alpha_system.runtime.diagnostics.{family.value}",
        },
    )


def _cost_report(*, include_base: bool = True) -> CostSensitivityReport:
    profile_summaries = [_profile_summary("double_cost", Decimal("2"))]
    if include_base:
        profile_summaries.insert(0, _profile_summary("base", Decimal("1")))
    return CostSensitivityReport(
        diagnostics_report=_diagnostics_report(
            report_kind=COST_SENSITIVITY_REPORT_KIND,
            family=DiagnosticsFamily.COST,
        ),
        cost_model_version=CostModelVersion(bbo_available=True),
        profile_summaries=tuple(profile_summaries),
        session_breakdown=(
            CostSessionSummary(
                profile_name="base",
                session_label="RTH",
                fill_count=2,
                cost_total=Decimal("1"),
                slippage_proxy_total=Decimal("0.5"),
                combined_cost_slippage_proxy=Decimal("1.5"),
                session_cost_multiplier=Decimal("1"),
                session_slippage_multiplier=Decimal("1"),
            ),
        ),
        cost_gradient_items=(("base_to_double_cost_combined_proxy_delta", "1.5"),),
        slippage_labeled_proxy=True,
        bbo_spread_crossing_used=True,
    )


def _profile_summary(profile_name: str, multiplier: Decimal) -> CostProfileSummary:
    return CostProfileSummary(
        profile_name=profile_name,
        fill_count=2,
        bbo_fill_count=2,
        cost_total=multiplier,
        slippage_proxy_total=Decimal("0.5") * multiplier,
        combined_cost_slippage_proxy=Decimal("1.5") * multiplier,
        cost_multiplier=multiplier,
        slippage_multiplier=multiplier,
        bbo_spread_crossing_used=True,
        bbo_unavailable_fallback_used=False,
        zero_cost_diagnostic_only=False,
    )


def _signal_probe_report(cost_report: CostSensitivityReport) -> SignalProbeReport:
    return SignalProbeReport(
        signal_probe_spec_ref=SignalProbeSpecRef(
            signal_probe_spec_id="signal_probe_spec_rt_p17",
            content_hash=HASH_C,
        ),
        status=StudyRunResultState.SIGNAL_PROBE_COMPLETE,
        lineage_refs={"run_id": "run_rt_p17_synthetic"},
        position_summary={"max_position_units": 1},
        trade_summary={"trade_count": 2},
        cost_aware_expectancy_proxy={
            "base_expectancy_proxy": "1.0",
            "double_cost_expectancy_proxy": "0.25",
        },
        drawdown_proxy={"max_drawdown_proxy": "0.5"},
        stability_summary={"stable_under_double_cost": True},
        threshold_summaries=(
            ThresholdProbeSummary(
                threshold=Decimal("0.5"),
                trade_count=2,
                turnover=Decimal("2"),
                gross_expectancy_proxy=Decimal("1"),
                double_cost_expectancy_proxy=Decimal("0.25"),
                drawdown_proxy=Decimal("0.5"),
                stable_under_double_cost=True,
            ),
        ),
        cost_sensitivity_report=cost_report,
        limitations=("Synthetic signal probe fixture only.",),
    )


def _negative_control_results() -> tuple[dict[str, object], ...]:
    return (
        {
            "control_name": "synthetic_negative_control",
            "control_state": "completed_for_metadata_fixture",
            "result_summary": "synthetic control metadata remained non-promotional",
        },
    )
