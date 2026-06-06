from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import pytest

from alpha_system.governance.evidence_bundle import EvidenceBundle
from alpha_system.governance.ids import GovernanceIdKind, generate_governance_id
from alpha_system.runtime.audit.no_lookahead import (
    NoLookaheadAuditOutcome,
    NoLookaheadAuditResult,
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
from alpha_system.runtime.evidence import (
    EvidenceDraftContractError,
    build_evidence_draft,
)
from alpha_system.runtime.probe.report import SignalProbeReport, ThresholdProbeSummary
from alpha_system.runtime.probe.spec import SignalProbeSpecRef

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


def test_evidence_draft_feeds_governance_evidence_bundle_input() -> None:
    cost_report = _cost_report()
    draft = build_evidence_draft(
        alpha_spec_id=_alpha_spec_id(),
        study_spec_id=_study_spec_id(),
        trial_refs=(_trial_id(),),
        study_run_manifest=_manifest(),
        study_run_record=_study_run_record(),
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
        no_lookahead_audit_result=NoLookaheadAuditResult(
            outcome=NoLookaheadAuditOutcome.POINT_IN_TIME_SAFE
        ),
        negative_control_results=_negative_control_results(),
    )

    bundle = draft.validate_with_governance_evidence_bundle()
    payload = draft.to_governance_evidence_input()

    assert isinstance(bundle, EvidenceBundle)
    assert not isinstance(draft, EvidenceBundle)
    assert payload["evidence_bundle_id"] == draft.governance_evidence_bundle_id
    assert payload["diagnostics_summary"]["governance_consumption"] == {
        "evidence_bundle_surface": (
            "alpha_system.governance.evidence_bundle.create_evidence_bundle"
        ),
        "trial_ledger_surface": "alpha_system.governance.trial_ledger.TrialLedgerRecord",
        "consumed_not_duplicated": True,
    }
    assert draft.decision_state is RuntimeDecisionState.EVIDENCE_DRAFT_READY
    assert draft.not_a_candidate is True
    assert draft.not_reference_truth is True
    assert draft.not_finalized_evidence_bundle is True
    assert hash(draft)


def test_terminal_inconclusive_run_keeps_rejection_reason_visible() -> None:
    reason = RejectionReasonRecord(
        code=RejectionReasonCode.INCONCLUSIVE,
        message="Synthetic runtime study stayed inconclusive at the diagnostics tier.",
        decision_state=RuntimeDecisionState.INCONCLUSIVE,
        stage=RuntimeDecisionStage.DIAGNOSTICS,
        source_code="synthetic_low_sample_inconclusive",
    )

    draft = build_evidence_draft(
        alpha_spec_id=_alpha_spec_id(),
        study_spec_id=_study_spec_id(),
        trial_refs=(_trial_id(),),
        study_run_manifest=_manifest(),
        study_run_record=_study_run_record(
            result_state=StudyRunResultState.INCONCLUSIVE,
            rejection_reasons=(
                RunRejectionReason(
                    code="low_sample_inconclusive",
                    message="Synthetic sample count was too small for a descriptive decision.",
                ),
            ),
        ),
        decision=RuntimeDecision(
            state=RuntimeDecisionState.INCONCLUSIVE,
            reasons=(reason,),
        ),
        negative_control_results=_negative_control_results(),
    )

    payload = draft.to_governance_evidence_input()
    decision = payload["diagnostics_summary"]["decision"]

    assert draft.decision_state is RuntimeDecisionState.INCONCLUSIVE
    assert draft.terminal_rejection_reasons == (reason,)
    assert decision["visible_rejection_reasons"][0]["code"] == "inconclusive"
    assert payload["diagnostics_summary"]["evidence_sections"][0]["section_name"] == (
        "terminal_decision_visibility"
    )


def test_draft_rejects_value_bearing_summary_keys() -> None:
    with pytest.raises(EvidenceDraftContractError, match="value-bearing"):
        build_evidence_draft(
            alpha_spec_id=_alpha_spec_id(),
            study_spec_id=_study_spec_id(),
            trial_refs=(_trial_id(),),
            study_run_manifest=_manifest(),
            study_run_record=_study_run_record(),
            factor_diagnostics_report=_ValueBearingReport(),
            cost_sensitivity_report=_cost_report(),
            no_lookahead_audit_result=NoLookaheadAuditResult(
                outcome=NoLookaheadAuditOutcome.POINT_IN_TIME_SAFE
            ),
            negative_control_results=_negative_control_results(),
        )


def test_cost_discipline_requires_base_and_double_cost_profiles_for_forward_draft() -> None:
    with pytest.raises(EvidenceDraftContractError, match="missing required profiles"):
        build_evidence_draft(
            alpha_spec_id=_alpha_spec_id(),
            study_spec_id=_study_spec_id(),
            trial_refs=(_trial_id(),),
            study_run_manifest=_manifest(),
            study_run_record=_study_run_record(),
            factor_diagnostics_report=_diagnostics_report(
                report_kind="factor_diagnostics_summary",
                family=DiagnosticsFamily.FACTOR,
            ),
            cost_sensitivity_report=_cost_report(include_base=False),
            no_lookahead_audit_result=NoLookaheadAuditResult(
                outcome=NoLookaheadAuditOutcome.POINT_IN_TIME_SAFE
            ),
            negative_control_results=_negative_control_results(),
        )


def test_draft_payload_is_not_candidate_or_promotion() -> None:
    cost_report = _cost_report()
    draft = build_evidence_draft(
        alpha_spec_id=_alpha_spec_id(),
        study_spec_id=_study_spec_id(),
        trial_refs=(_trial_id(),),
        study_run_manifest=_manifest(),
        study_run_record=_study_run_record(),
        factor_diagnostics_report=_diagnostics_report(
            report_kind="factor_diagnostics_summary",
            family=DiagnosticsFamily.FACTOR,
        ),
        cost_sensitivity_report=cost_report,
        signal_probe_report=_signal_probe_report(cost_report),
        no_lookahead_audit_result=NoLookaheadAuditResult(
            outcome=NoLookaheadAuditOutcome.POINT_IN_TIME_SAFE
        ),
        negative_control_results=_negative_control_results(),
    )

    payload = draft.to_dict()
    payload_text = str(payload).lower()

    assert payload["not_a_candidate"] is True
    assert payload["not_finalized_evidence_bundle"] is True
    assert payload["promotion_basis_allowed"] is False
    assert "alpha validated" not in payload_text
    assert "profitable" not in payload_text
    assert "tradable" not in payload_text


def _alpha_spec_id() -> str:
    return generate_governance_id(GovernanceIdKind.ALPHA_SPEC, {"name": "rt_p16_alpha"})


def _study_spec_id() -> str:
    return generate_governance_id(GovernanceIdKind.STUDY_SPEC, {"name": "rt_p16_study"})


def _trial_id() -> str:
    return generate_governance_id(GovernanceIdKind.TRIAL_LEDGER_RECORD, {"name": "rt_p16_trial"})


def _manifest() -> StudyRunManifest:
    return StudyRunManifest(
        run_id="run_rt_p16_synthetic",
        dataset_version_id="dataset_version_rt_p16",
        dataset_version_hash=HASH_A,
        dataset_lineage_ref="dataset_lineage_rt_p16",
        dataset_admissibility_state="READY_FOR_RESEARCH",
        feature_pack_versions=(
            FeaturePackVersionRef(
                pack_id="factor_pack_rt_p16",
                content_hash=HASH_A,
                lineage_ref="feature_lineage_rt_p16",
                available_ts_ref="feature_available_ts_ref_rt_p16",
            ),
        ),
        label_pack_versions=(
            LabelPackVersionRef(
                pack_id="label_pack_rt_p16",
                content_hash=HASH_B,
                lineage_ref="label_lineage_rt_p16",
                label_available_ts_ref="label_available_ts_ref_rt_p16",
            ),
        ),
        code_version="code_version_rt_p16",
        code_content_hash=HASH_A,
        config_version="config_version_rt_p16",
        config_hash=HASH_B,
        cost_model_version="cost_model_version_rt_p16",
        cost_model_hash=HASH_C,
    )


def _study_run_record(
    *,
    result_state: StudyRunResultState = StudyRunResultState.COST_STRESS_COMPLETE,
    rejection_reasons: tuple[RunRejectionReason, ...] = (),
) -> StudyRunRecord:
    manifest = _manifest()
    return StudyRunRecord(
        run_id=manifest.run_id,
        study_run_spec_ref={
            "study_run_spec_id": "study_run_spec_rt_p16",
            "content_hash": HASH_A,
        },
        result_state=result_state,
        manifest_ref=manifest,
        rejection_reasons=rejection_reasons,
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
        lineage_refs={"dataset_version_id": "dataset_version_rt_p16"},
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
            signal_probe_spec_id="signal_probe_spec_rt_p16",
            content_hash=HASH_C,
        ),
        status=StudyRunResultState.SIGNAL_PROBE_COMPLETE,
        lineage_refs={"run_id": "run_rt_p16_synthetic"},
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


@dataclass(frozen=True)
class _Ref:
    def to_dict(self) -> dict[str, str]:
        return {
            "report_id": "raw_report_ref",
            "report_hash": HASH_C,
            "report_kind": "value_bearing_test_report",
        }


class _ValueBearingReport:
    status = StudyRunResultState.DIAGNOSTICS_COMPLETE
    coverage_summary = {"raw_values": "synthetic value payload should be rejected"}
    quality_summary = {"gate_count": 1}
    limitations = ("Synthetic invalid report.",)
    rejection_reasons: tuple[RunRejectionReason, ...] = ()

    def to_ref(self) -> _Ref:
        return _Ref()
