from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from alpha_system.governance.ids import GovernanceIdKind, generate_governance_id
from alpha_system.runtime.audit.no_lookahead import (
    NoLookaheadAuditOutcome,
    NoLookaheadAuditResult,
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
    RuntimeDecisionStage,
    RuntimeDecisionState,
)
from alpha_system.runtime.diagnostics.contracts import (
    DiagnosticsFamily,
    DiagnosticsRunRecord,
    DiagnosticsRunSpecRef,
)
from alpha_system.runtime.diagnostics.factor.runtime import FactorDiagnosticsReport
from alpha_system.runtime.diagnostics.label.runtime import LabelDiagnosticsReport
from alpha_system.runtime.diagnostics.report import (
    DiagnosticsQualityGate,
    DiagnosticsQualityGateStatus,
    DiagnosticsReport,
)
from alpha_system.runtime.evidence import EvidenceDraft, build_evidence_draft
from alpha_system.runtime.handoff.reference import (
    ReferenceCandidateHandoff,
    build_reference_candidate_handoff,
)
from alpha_system.runtime.probe.report import SignalProbeReport, ThresholdProbeSummary
from alpha_system.runtime.probe.spec import SignalProbeSpecRef
from alpha_system.runtime.reports import (
    RuntimeReportCard,
    RuntimeReportCardError,
    RuntimeRunSummary,
    render_runtime_report_card,
)

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64

PROHIBITED_OUTPUT_TOKENS = (
    "ALPHA_VALIDATED",
    "FACTOR_PROMOTED",
    "STRATEGY_READY",
    "PORTFOLIO_READY",
    "LIVE_READY",
    "PAPER_READY",
    "PROFITABLE",
    "TRADABLE",
    "PRODUCTION_READY",
    "alpha validated",
    "factor promoted",
    "strategy",
    "profitable",
    "tradable",
    "promotion",
)

HEAVY_OUTPUT_TOKENS = (
    ".parquet",
    ".arrow",
    ".feather",
    ".dbn",
    ".zst",
    ".sqlite",
    "canonical_bars",
    "feature_values",
    "feature values",
    "label_values",
    "label values",
    "provider_response",
    "raw_values",
    "raw values",
    "value_array",
    "value_table",
)


def test_runtime_report_card_renders_run_summary_with_fast_path_label() -> None:
    summary = RuntimeRunSummary(
        run_id="run_rt_p23_synthetic",
        status=RuntimeDecisionState.EVIDENCE_DRAFT_READY.value,
        research_spec_id="research_spec_rt_p23",
        study_spec_id="study_spec_rt_p23",
        dataset_version_id="dataset_version_rt_p23",
        feature_pack_version_ids=("feature_pack_rt_p23",),
        label_pack_version_ids=("label_pack_rt_p23",),
        artifact_refs=(
            {
                "artifact_id": "summary_ref_rt_p23",
                "content_hash": HASH_A,
            },
        ),
        limitations=("Synthetic summary fixture only.",),
        next_required_gate="Reference handoff gate",
        fast_path=True,
    )

    card = render_runtime_report_card(summary)

    assert "fast path - non-Reference" in card
    assert "Reference handoff gate" in card
    assert "summary_ref_rt_p23" in card
    _assert_report_card_safe(card)


def test_runtime_report_card_renders_existing_runtime_contract_objects() -> None:
    factor_report = FactorDiagnosticsReport(
        report=_diagnostics_report(
            report_kind="factor_diagnostics_summary",
            family=DiagnosticsFamily.FACTOR,
        )
    )
    label_report = _label_report()
    cost_report = _cost_report()
    reason = RejectionReasonRecord(
        code=RejectionReasonCode.INCONCLUSIVE,
        message="Synthetic fixture stayed inconclusive after diagnostics.",
        decision_state=RuntimeDecisionState.INCONCLUSIVE,
        stage=RuntimeDecisionStage.DIAGNOSTICS,
        source_code="synthetic_inconclusive",
    )
    manifest = _manifest(cost_report)
    evidence_draft = _evidence_draft(cost_report=cost_report, manifest=manifest)
    handoff = _reference_handoff(
        cost_report=cost_report,
        manifest=manifest,
        evidence_draft=evidence_draft,
    )

    renderer = RuntimeReportCard()
    cards = [
        renderer.render(factor_report),
        renderer.render(label_report),
        renderer.render(cost_report),
        renderer.render(reason),
        renderer.render(evidence_draft),
        renderer.render(handoff),
    ]

    assert all("Compact summaries and references only." in card for card in cards)
    assert "draft input - not Reference truth" in cards[4]
    assert "handoff package - not Reference validation" in cards[5]
    assert "ReferenceCandidateHandoff" not in cards[5]
    for card in cards:
        _assert_report_card_safe(card)


def test_report_card_rejects_raw_value_keys_before_rendering() -> None:
    with pytest.raises(RuntimeReportCardError, match="raw or heavy data"):
        RuntimeReportCard().render(
            {
                "status": StudyRunResultState.DIAGNOSTICS_COMPLETE.value,
                "coverage_summary": {
                    "sample_count": 2,
                    "feature_values": "[1, 2]",
                },
            }
        )


def test_report_card_rejects_prohibited_mvp_state_strings() -> None:
    with pytest.raises(RuntimeReportCardError, match="prohibited MVP state"):
        RuntimeRunSummary(
            run_id="run_rt_p23_invalid",
            status="PRODUCTION_READY",
        )


def test_templates_and_report_card_scaffolds_stay_descriptive() -> None:
    paths = (
        *Path("docs/research_runtime/templates").glob("**/*.md"),
        *Path("docs/research_runtime/report_cards").glob("**/*.md"),
    )

    assert paths
    for path in paths:
        text = path.read_text(encoding="utf-8")
        _assert_report_card_safe(text)


def _assert_report_card_safe(card: str) -> None:
    lowered = card.lower()
    upper = card.upper()
    for token in PROHIBITED_OUTPUT_TOKENS:
        assert token.lower() not in lowered
        assert token.upper() not in upper
    for token in HEAVY_OUTPUT_TOKENS:
        assert token.lower() not in lowered


def _alpha_spec_id() -> str:
    return generate_governance_id(GovernanceIdKind.ALPHA_SPEC, {"name": "rt_p23_research"})


def _study_spec_id() -> str:
    return generate_governance_id(GovernanceIdKind.STUDY_SPEC, {"name": "rt_p23_study"})


def _trial_id() -> str:
    return generate_governance_id(
        GovernanceIdKind.TRIAL_LEDGER_RECORD,
        {"name": "rt_p23_trial"},
    )


def _manifest(cost_report: CostSensitivityReport) -> StudyRunManifest:
    return StudyRunManifest(
        run_id="run_rt_p23_synthetic",
        dataset_version_id="dataset_version_rt_p23",
        dataset_version_hash=HASH_A,
        dataset_lineage_ref="dataset_lineage_rt_p23",
        dataset_admissibility_state="READY_FOR_RESEARCH",
        feature_pack_versions=(
            FeaturePackVersionRef(
                pack_id="factor_pack_rt_p23",
                content_hash=HASH_A,
                lineage_ref="feature_lineage_rt_p23",
                available_ts_ref="feature_available_ts_ref_rt_p23",
            ),
        ),
        label_pack_versions=(
            LabelPackVersionRef(
                pack_id="label_pack_rt_p23",
                content_hash=HASH_B,
                lineage_ref="label_lineage_rt_p23",
                label_available_ts_ref="label_available_ts_ref_rt_p23",
            ),
        ),
        code_version="code_version_rt_p23",
        code_content_hash=HASH_A,
        config_version="config_version_rt_p23",
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
            "study_run_spec_id": "study_run_spec_rt_p23",
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
                artifact_id="rt_p23_runtime_summary",
                kind="summary",
                location="runtime_summaries/rt_p23_summary.md",
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


def _reference_handoff(
    *,
    cost_report: CostSensitivityReport,
    manifest: StudyRunManifest,
    evidence_draft: EvidenceDraft,
) -> ReferenceCandidateHandoff:
    return build_reference_candidate_handoff(
        alpha_spec_id=_alpha_spec_id(),
        study_spec_id=_study_spec_id(),
        evidence_draft=evidence_draft,
        study_run_manifest=manifest,
        runtime_artifact_manifest=_artifact_manifest(manifest),
        cost_sensitivity_report=cost_report,
        no_lookahead_audit_result=_passed_audit(),
        factor_diagnostics_report=_diagnostics_report(
            report_kind="factor_diagnostics_summary",
            family=DiagnosticsFamily.FACTOR,
        ),
        label_diagnostics_report=_diagnostics_report(
            report_kind="label_diagnostics_summary",
            family=DiagnosticsFamily.LABEL,
        ),
        signal_probe_report=_signal_probe_report(cost_report),
    )


def _passed_audit() -> NoLookaheadAuditResult:
    return NoLookaheadAuditResult(outcome=NoLookaheadAuditOutcome.POINT_IN_TIME_SAFE)


def _label_report() -> LabelDiagnosticsReport:
    diagnostics = _diagnostics_report(
        report_kind="label_diagnostics_summary",
        family=DiagnosticsFamily.LABEL,
    )
    record = DiagnosticsRunRecord(
        diagnostics_run_spec_ref=diagnostics.diagnostics_run_spec_ref,
        status=StudyRunResultState.DIAGNOSTICS_COMPLETE,
        report_ref=diagnostics.to_ref(),
    )
    return LabelDiagnosticsReport(
        diagnostics_report=diagnostics,
        diagnostics_run_record=record,
        distribution_summary_items=(("class_count", 2),),
        horizon_coverage_items=(("horizon_count", 1),),
        class_balance_items=(("majority_class_share", 0.5),),
        mfe_mae_summary_items=(("path_metric_count", 2),),
        path_ambiguity_summary_items=(("ambiguous_path_count", 0),),
        label_available_ts_validity_items=(("valid_available_ts_count", 2),),
        cost_adjustment_sanity_items=(("cost_adjusted_label_count", 2),),
        coverage_missingness_items=(("missingness_rate", 0.0),),
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
        lineage_refs={"dataset_version_id": "dataset_version_rt_p23"},
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
    )


def _cost_report() -> CostSensitivityReport:
    return CostSensitivityReport(
        diagnostics_report=_diagnostics_report(
            report_kind=COST_SENSITIVITY_REPORT_KIND,
            family=DiagnosticsFamily.COST,
        ),
        cost_model_version=CostModelVersion(bbo_available=True),
        profile_summaries=(
            _profile_summary("base", Decimal("1")),
            _profile_summary("double_cost", Decimal("2")),
        ),
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
            signal_probe_spec_id="signal_probe_spec_rt_p23",
            content_hash=HASH_C,
        ),
        status=StudyRunResultState.SIGNAL_PROBE_COMPLETE,
        lineage_refs={"run_id": "run_rt_p23_synthetic"},
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
            "result_summary": "synthetic control metadata stayed descriptive",
        },
    )
