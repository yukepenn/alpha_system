"""End-to-end synthetic Research Runtime dry run.

The dry run is a local orchestration smoke. It sequences the existing runtime
contracts and report builders over tiny synthetic fixtures; it does not add
diagnostic, cost, grid, audit, evidence, or handoff math.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from alpha_system.data.foundation.datasets import DatasetVersion
from alpha_system.experiments.limits import CombinationLimit
from alpha_system.governance.alpha_spec import (
    AlphaSpec,
    generate_alpha_spec_id,
)
from alpha_system.governance.ids import GovernanceIdKind, generate_governance_id
from alpha_system.governance.study_input_pack import StudyInputPack
from alpha_system.governance.study_spec import StudySpec, generate_study_spec_id
from alpha_system.runtime.audit.no_lookahead import (
    NoLookaheadAuditOutcome,
    NoLookaheadAuditResult,
    NoLookaheadRuntimeAudit,
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
from alpha_system.runtime.contracts.plan import DOUBLE_COST_PROFILE, validate_runtime_plan
from alpha_system.runtime.contracts.run_record import StudyRunRecord, StudyRunResultState
from alpha_system.runtime.contracts.run_spec import RuntimeRequest, StudyRunSpec
from alpha_system.runtime.cost import CostModelVersion, CostStressSpec
from alpha_system.runtime.cost.runtime import build_cost_sensitivity_report
from alpha_system.runtime.decisions import (
    RejectionReasonCode,
    RejectionReasonRecord,
    RuntimeDecision,
    RuntimeDecisionStage,
    RuntimeDecisionState,
    normalize_rejection_reason,
    normalize_rejection_reasons,
)
from alpha_system.runtime.diagnostics.contracts import DiagnosticsFamily, DiagnosticsRunSpec
from alpha_system.runtime.diagnostics.cross_market.runtime import (
    build_cross_market_diagnostics_run,
)
from alpha_system.runtime.diagnostics.factor import (
    FactorDiagnosticsThresholds,
    build_factor_diagnostics_run,
)
from alpha_system.runtime.diagnostics.label.runtime import (
    LabelDiagnosticsConfig,
    build_label_diagnostics_report,
)
from alpha_system.runtime.diagnostics.report import DiagnosticsReport
from alpha_system.runtime.diagnostics.splits import build_split_diagnostics_reports
from alpha_system.runtime.entry_contract import (
    RuntimeEntryRequest,
    RuntimeEntryResult,
    RuntimeEntryStatus,
    evaluate_runtime_entry_request,
)
from alpha_system.runtime.evidence import EvidenceDraft, build_evidence_draft
from alpha_system.runtime.grid import (
    BoundedGridOutcome,
    BoundedGridRunRecord,
    BoundedGridValidationResult,
    VariantBudget,
    validate_bounded_grid_request,
)
from alpha_system.runtime.handoff import (
    REFERENCE_VALIDATION_REQUIRED,
    ReferenceCandidateHandoff,
    build_reference_candidate_handoff,
)
from alpha_system.runtime.input_resolver import (
    FeatureLabelPackResolver,
    RuntimeInputPack,
    RuntimeInputResolutionResult,
    resolve_runtime_input_pack,
)
from alpha_system.runtime.probe import (
    DirectionPolicy,
    FillPolicy,
    SignalFeatureRef,
    SignalLabelRef,
    SignalProbeObservation,
    SignalProbeReport,
    SignalProbeSpec,
    build_next_bar_position_series,
    run_signal_probe,
)
from alpha_system.runtime.tool_results import (
    RuntimeDiagnosticsSummary,
    RuntimeRunSummary,
    RuntimeToolResult,
)

RUN_ID = "run_rt_p25_synthetic_dry_run"
DATASET_VERSION_ID = "dsv_synthetic_cross_market_fixture_v1"
FEATURE_REQUEST_ID = "freq_eb180e1226ce34c048c7e6eb"
LABEL_SPEC_ID = "lspec_8663589ca7a9f1e5859289c7"
FEATURE_VERSION_ID = "fver_" + "a" * 64
LABEL_VERSION_ID = "lver_" + "b" * 64
BASE_TS = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
FIXTURE_ROOT = Path("tests/fixtures/runtime")
DEVELOPMENT_SCOPE = {
    "partition_id": "development",
    "start": "2018-01-01",
    "end": "2022-12-31",
}
SESSION_SCOPE = {
    "session": "rth_and_eth",
    "rth": {"start": "09:30", "end": "16:00"},
    "eth": {"start": "16:00", "end": "09:30"},
}
DATASET_SCOPE = {
    "instrument_universe": ["ES", "NQ", "RTY"],
    "source": "tiny synthetic runtime fixture metadata, not real market data",
    "time_range": "2018-01-01 through 2022-12-31 synthetic timestamps",
}
PROHIBITED_MVP_STATES = frozenset(
    {
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
)
_NO_LOOKAHEAD_AUDIT_COVERAGE = (
    "available_ts",
    "label_available_ts",
    "same_bar_fills",
    "locked_test_metadata",
)

DatasetVersionResolver = Callable[[str | Path, object], DatasetVersion | None]


@dataclass(frozen=True, slots=True)
class RuntimeDryRunConfig:
    """Configuration for the local synthetic dry run."""

    fixture_root: Path = FIXTURE_ROOT
    registry_path: str | Path = "tests/fixtures/runtime/synthetic_registry.json"
    include_alpha_spec: bool = True
    include_study_spec: bool = True
    dataset_lifecycle_state: str = "READY_FOR_RESEARCH"


@dataclass(frozen=True, slots=True)
class RuntimeDryRunResult:
    """Structured dry-run output with agent-facing summaries and terminal state."""

    dry_run_status: str
    terminal_decision_state: RuntimeDecisionState
    run_id: str
    entry_result: RuntimeEntryResult
    input_resolution_result: RuntimeInputResolutionResult | None
    run_summary: RuntimeRunSummary | None
    tool_result: RuntimeToolResult | None
    rejection_reasons: tuple[RejectionReasonRecord, ...]
    warning_reasons: tuple[str, ...] = ()
    no_lookahead_audit_coverage: tuple[str, ...] = ()
    runtime_input_pack: RuntimeInputPack | None = None
    bounded_grid_result: BoundedGridValidationResult | None = None
    no_lookahead_audit_result: NoLookaheadAuditResult | None = None
    cost_sensitivity_report: object | None = None
    signal_probe_report: SignalProbeReport | None = None
    evidence_draft: EvidenceDraft | None = None
    reference_handoff: ReferenceCandidateHandoff | None = None
    runtime_artifact_manifest: RuntimeArtifactManifest | None = None

    @property
    def pass_with_warnings_recorded(self) -> bool:
        """Return whether this dry run truthfully used a warnings status."""

        return self.dry_run_status == "PASS_WITH_WARNINGS"

    @property
    def executed(self) -> bool:
        """Return true only when the governed runtime progressed past input resolution."""

        return self.runtime_input_pack is not None

    def to_dict(self) -> dict[str, object]:
        """Return a value-free dry-run payload."""

        return {
            "dry_run_status": self.dry_run_status,
            "terminal_decision_state": self.terminal_decision_state.value,
            "run_id": self.run_id,
            "executed": self.executed,
            "pass_with_warnings_recorded": self.pass_with_warnings_recorded,
            "warning_reasons": list(self.warning_reasons),
            "no_lookahead_audit_coverage": list(self.no_lookahead_audit_coverage),
            "entry_status": self.entry_result.status.value,
            "input_resolution_status": None
            if self.input_resolution_result is None
            else self.input_resolution_result.status.value,
            "rejection_reasons": [reason.to_dict() for reason in self.rejection_reasons],
            "tool_result": None if self.tool_result is None else self.tool_result.to_dict(),
            "run_summary": None if self.run_summary is None else self.run_summary.to_dict(),
            "bounded_grid": None
            if self.bounded_grid_result is None
            else self.bounded_grid_result.to_dict(),
            "no_lookahead_audit": None
            if self.no_lookahead_audit_result is None
            else self.no_lookahead_audit_result.to_dict(),
            "evidence_draft": None if self.evidence_draft is None else self.evidence_draft.to_dict(),
            "reference_handoff": None
            if self.reference_handoff is None
            else self.reference_handoff.to_dict(),
            "raw_or_heavy_data_embedded": False,
        }


@dataclass(frozen=True, slots=True)
class _ResolvedSpecs:
    alpha_spec: AlphaSpec | None
    study_spec: StudySpec | None
    study_input_pack: StudyInputPack | None


@dataclass(frozen=True, slots=True)
class _DiagnosticsBundle:
    factor_report: object
    label_report: object
    session_report: object
    regime_report: object
    cross_market_report: object
    common_reports: tuple[DiagnosticsReport, ...]


def run_runtime_dry_run(config: RuntimeDryRunConfig | None = None) -> RuntimeDryRunResult:
    """Run the full local synthetic runtime orchestration smoke."""

    active_config = config or RuntimeDryRunConfig()
    warnings = _warning_reasons(active_config)
    specs = _resolved_specs(active_config)
    entry_result = evaluate_runtime_entry_request(_entry_request(specs, active_config))
    if not entry_result.resolved:
        return _blocked_before_run(
            entry_result=entry_result,
            input_resolution_result=None,
            warnings=warnings,
            stage=RuntimeDecisionStage.INPUTS,
        )

    input_resolution = resolve_runtime_input_pack(
        entry_result,
        registry_path=active_config.registry_path,
        dataset_lifecycle_state=active_config.dataset_lifecycle_state,
        feature_pack_refs=(FEATURE_VERSION_ID,),
        label_pack_refs=(LABEL_VERSION_ID,),
        partition_scope=DEVELOPMENT_SCOPE,
        session_scope=SESSION_SCOPE,
        feature_label_resolver=_feature_label_resolver(),
        dataset_version_resolver=_synthetic_dataset_version_resolver,
    )
    if not input_resolution.resolved or input_resolution.input_pack is None:
        return _blocked_before_run(
            entry_result=entry_result,
            input_resolution_result=input_resolution,
            warnings=warnings,
            stage=RuntimeDecisionStage.INPUTS,
        )

    if specs.alpha_spec is None or specs.study_spec is None or specs.study_input_pack is None:
        return _blocked_before_run(
            entry_result=entry_result,
            input_resolution_result=input_resolution,
            warnings=warnings,
            stage=RuntimeDecisionStage.INPUTS,
        )

    runtime_request = RuntimeRequest(
        alpha_spec=specs.alpha_spec,
        study_spec=specs.study_spec,
        study_input_pack=specs.study_input_pack,
        target_dataset_version_id=DATASET_VERSION_ID,
        runtime_input_pack=input_resolution.input_pack,
        request_metadata={"runtime_dry_run": "RT-P25 synthetic fixture orchestration"},
    )
    plan_result = validate_runtime_plan(
        runtime_request=runtime_request,
        partition_scope=DEVELOPMENT_SCOPE,
        session_scope=SESSION_SCOPE,
        include_signal_probe=True,
        variant_grid_ref="rt_p25_synthetic_bounded_probe_grid",
        variant_budget=CombinationLimit(4),
        cost_stress_profiles=("base", DOUBLE_COST_PROFILE),
        plan_metadata={"dry_run": "rt_p25"},
    )
    if not plan_result.validated or plan_result.plan is None:
        return _blocked_before_run(
            entry_result=entry_result,
            input_resolution_result=input_resolution,
            warnings=warnings,
            stage=RuntimeDecisionStage.RUNTIME_STOP,
            reasons=plan_result.reasons,
        )

    study_run_spec = StudyRunSpec(
        runtime_request=runtime_request,
        runtime_plan=plan_result.plan,
        run_metadata={"dry_run": "rt_p25_synthetic_fixture"},
    )
    diagnostics = _run_diagnostics(
        study_run_spec=study_run_spec,
        runtime_plan=plan_result.plan,
        runtime_input_pack=input_resolution.input_pack,
        fixture_root=active_config.fixture_root,
    )
    cost_model_version = CostModelVersion(bbo_available=True)
    cost_stress_spec = CostStressSpec(cost_model_version=cost_model_version)
    signal_probe_spec = _signal_probe_spec(
        runtime_input_pack=input_resolution.input_pack,
        cost_stress_spec=cost_stress_spec,
    )
    probe_observations = _probe_observations(active_config.fixture_root)
    cost_diagnostics_spec = _diagnostics_spec(
        DiagnosticsFamily.COST,
        study_run_spec=study_run_spec,
        runtime_plan=plan_result.plan,
    )
    signal_probe_report = run_signal_probe(
        signal_probe_spec=signal_probe_spec,
        observations=probe_observations,
        cost_diagnostics_run_spec=cost_diagnostics_spec,
        lineage_refs=_lineage_refs(input_resolution.input_pack, study_run_spec),
    )
    cost_sensitivity_report = _cost_report_for_primary_probe(
        signal_probe_spec=signal_probe_spec,
        observations=probe_observations,
        cost_diagnostics_spec=cost_diagnostics_spec,
        runtime_input_pack=input_resolution.input_pack,
        study_run_spec=study_run_spec,
    )
    if signal_probe_report.cost_sensitivity_report_ref != cost_sensitivity_report.to_ref():
        return _terminal_result(
            entry_result=entry_result,
            input_resolution_result=input_resolution,
            terminal_state=RuntimeDecisionState.BLOCKED,
            reasons=(
                _reason(
                    code=RejectionReasonCode.BLOCKED_BY_POLICY,
                    message="Signal probe and cost stress references did not match.",
                    stage=RuntimeDecisionStage.COST_STRESS,
                    source_code="signal_probe_cost_ref_mismatch",
                    decision_state=RuntimeDecisionState.BLOCKED,
                ),
            ),
            warnings=warnings,
            runtime_input_pack=input_resolution.input_pack,
        )

    bounded_grid = validate_bounded_grid_request(
        run_id=RUN_ID,
        binding_ref={
            "alpha_spec_ref": runtime_request.alpha_spec_ref,
            "study_spec_ref": runtime_request.study_spec_ref,
            "study_run_spec_id": study_run_spec.study_run_spec_id,
            "study_run_spec_content_hash": study_run_spec.content_hash,
            "signal_probe_spec_id": signal_probe_spec.signal_probe_spec_id,
            "signal_probe_spec_content_hash": signal_probe_spec.content_hash,
        },
        parameter_axes={
            "direction_policy": ["long_short_flat"],
            "threshold": ["0.5", "0.55"],
        },
        variant_budget=VariantBudget(max_variants=4, max_grid_points=4),
        partition_scope=("development", "validation"),
        partition_purpose="development_validation_grid_selection",
    )
    audit_result = NoLookaheadRuntimeAudit().evaluate(
        runtime_input_pack=input_resolution.input_pack,
        decision_ts="2026-01-06T16:15:00+00:00",
        signal_probe_spec=signal_probe_spec,
        signal_probe_report=signal_probe_report,
        feature_inputs=_audit_feature_inputs(),
        label_inputs=_audit_label_inputs(),
        live_feature_windows=_audit_live_feature_windows(),
        probe_fill_records=_probe_fill_records(signal_probe_spec, probe_observations),
        partition_scope=DEVELOPMENT_SCOPE,
        partition_purpose="development_validation_grid_selection",
        governance_metadata={},
    )

    terminal = _terminal_pre_evidence_decision(
        diagnostics=diagnostics,
        cost_sensitivity_report=cost_sensitivity_report,
        signal_probe_report=signal_probe_report,
        bounded_grid=bounded_grid,
        audit_result=audit_result,
    )
    if terminal is not None:
        state, reasons = terminal
        return _terminal_result(
            entry_result=entry_result,
            input_resolution_result=input_resolution,
            terminal_state=state,
            reasons=reasons,
            warnings=warnings,
            runtime_input_pack=input_resolution.input_pack,
            bounded_grid_result=bounded_grid,
            no_lookahead_audit_result=audit_result,
            cost_sensitivity_report=cost_sensitivity_report,
            signal_probe_report=signal_probe_report,
        )

    manifest = _study_run_manifest(
        runtime_input_pack=input_resolution.input_pack,
        cost_model_version=cost_model_version,
    )
    artifact_manifest = _runtime_artifact_manifest()
    pre_evidence_record = _study_run_record(
        manifest=manifest,
        study_run_spec=study_run_spec,
        result_state=StudyRunResultState.COST_STRESS_COMPLETE,
        artifact_manifest=artifact_manifest,
    )
    evidence_draft = build_evidence_draft(
        alpha_spec_id=runtime_request.alpha_spec_ref,
        study_spec_id=runtime_request.study_spec_ref,
        trial_refs=(_trial_id(),),
        study_run_manifest=manifest,
        study_run_record=pre_evidence_record,
        negative_control_results=_negative_control_results(),
        factor_diagnostics_report=diagnostics.factor_report,
        label_diagnostics_report=diagnostics.label_report,
        session_split_report=diagnostics.session_report,
        regime_split_report=diagnostics.regime_report,
        cross_market_diagnostics_report=diagnostics.cross_market_report,
        cost_sensitivity_report=cost_sensitivity_report,
        signal_probe_report=signal_probe_report,
        bounded_grid_record=bounded_grid.record,
        no_lookahead_audit_result=audit_result,
        limitations=("RT-P25 synthetic dry-run summary only.",),
    )
    reference_handoff = build_reference_candidate_handoff(
        alpha_spec_id=runtime_request.alpha_spec_ref,
        study_spec_id=runtime_request.study_spec_ref,
        evidence_draft=evidence_draft,
        study_run_manifest=manifest,
        runtime_artifact_manifest=artifact_manifest,
        cost_sensitivity_report=cost_sensitivity_report,
        no_lookahead_audit_result=audit_result,
        factor_diagnostics_report=diagnostics.factor_report,
        label_diagnostics_report=diagnostics.label_report.diagnostics_report,
        session_split_report=diagnostics.session_report,
        regime_split_report=diagnostics.regime_report,
        cross_market_diagnostics_report=diagnostics.cross_market_report,
        signal_probe_report=signal_probe_report,
        bounded_grid_record=bounded_grid.record,
        limitations=("RT-P25 synthetic dry-run handoff only.",),
    )

    final_record = _study_run_record(
        manifest=manifest,
        study_run_spec=study_run_spec,
        result_state=reference_handoff.decision_state.value,
        artifact_manifest=artifact_manifest,
    )
    tool_result = RuntimeToolResult.from_study_run_record(
        study_run_record=final_record,
        manifest=manifest,
        diagnostics_summary=RuntimeDiagnosticsSummary.from_reports(diagnostics.common_reports),
        cost_summary=cost_sensitivity_report,
        next_required_gate=REFERENCE_VALIDATION_REQUIRED,
    )
    run_summary = RuntimeRunSummary.from_tool_result(tool_result)
    return RuntimeDryRunResult(
        dry_run_status="PASS_WITH_WARNINGS" if warnings else "PASS",
        terminal_decision_state=reference_handoff.decision_state,
        run_id=RUN_ID,
        entry_result=entry_result,
        input_resolution_result=input_resolution,
        run_summary=run_summary,
        tool_result=tool_result,
        rejection_reasons=reference_handoff.terminal_rejection_reasons,
        warning_reasons=warnings,
        no_lookahead_audit_coverage=_NO_LOOKAHEAD_AUDIT_COVERAGE,
        runtime_input_pack=input_resolution.input_pack,
        bounded_grid_result=bounded_grid,
        no_lookahead_audit_result=audit_result,
        cost_sensitivity_report=cost_sensitivity_report,
        signal_probe_report=signal_probe_report,
        evidence_draft=evidence_draft,
        reference_handoff=reference_handoff,
        runtime_artifact_manifest=artifact_manifest,
    )


def _resolved_specs(config: RuntimeDryRunConfig) -> _ResolvedSpecs:
    alpha_spec = _alpha_spec() if config.include_alpha_spec else None
    study_spec = (
        _study_spec(alpha_spec.alpha_spec_id)
        if alpha_spec is not None and config.include_study_spec
        else None
    )
    pack = _study_input_pack(alpha_spec.alpha_spec_id) if alpha_spec and study_spec else None
    return _ResolvedSpecs(alpha_spec=alpha_spec, study_spec=study_spec, study_input_pack=pack)


def _entry_request(
    specs: _ResolvedSpecs,
    config: RuntimeDryRunConfig,
) -> RuntimeEntryRequest:
    return RuntimeEntryRequest(
        alpha_spec_ref=None if specs.alpha_spec is None else specs.alpha_spec.alpha_spec_id,
        study_spec_ref=None if specs.study_spec is None else specs.study_spec.study_spec_id,
        study_input_pack=specs.study_input_pack,
        target_dataset_version_id=DATASET_VERSION_ID,
        dataset_scope=DATASET_SCOPE,
        partition_scope=DEVELOPMENT_SCOPE,
        expected_dataset_lifecycle_state=config.dataset_lifecycle_state,
        dataset_version_source_family="databento",
        request_metadata={"fixture": "rt_p25_synthetic_dry_run"},
    )


def _run_diagnostics(
    *,
    study_run_spec: StudyRunSpec,
    runtime_plan: object,
    runtime_input_pack: RuntimeInputPack,
    fixture_root: Path,
) -> _DiagnosticsBundle:
    factor_spec = _diagnostics_spec(
        DiagnosticsFamily.FACTOR,
        study_run_spec=study_run_spec,
        runtime_plan=runtime_plan,
    )
    label_spec = _diagnostics_spec(
        DiagnosticsFamily.LABEL,
        study_run_spec=study_run_spec,
        runtime_plan=runtime_plan,
    )
    splits_spec = _diagnostics_spec(
        DiagnosticsFamily.SPLITS,
        study_run_spec=study_run_spec,
        runtime_plan=runtime_plan,
    )
    cross_market_spec = _diagnostics_spec(
        DiagnosticsFamily.CROSS_MARKET,
        study_run_spec=study_run_spec,
        runtime_plan=runtime_plan,
    )
    factor_result = build_factor_diagnostics_run(
        diagnostics_run_spec=factor_spec,
        observations=_factor_observations(fixture_root),
        lineage_refs=_lineage_refs(runtime_input_pack, study_run_spec),
        thresholds=FactorDiagnosticsThresholds(
            min_observations=4,
            max_outlier_rate=1.0,
            bucket_count=2,
            min_populated_buckets=2,
        ),
    )
    label_report = build_label_diagnostics_report(
        diagnostics_run_spec=label_spec,
        runtime_input_pack=runtime_input_pack,
        feature_quality_reports=(_feature_quality_report(runtime_input_pack),),
        feature_coverage_reports=(_feature_coverage_report(runtime_input_pack),),
        label_audit_reports=(_label_audit_report(runtime_input_pack),),
        label_observations=_label_observations(),
        label_profiles=_label_profiles(runtime_input_pack),
        config=LabelDiagnosticsConfig(min_sample_count=4),
    )
    session_report, regime_report = build_split_diagnostics_reports(
        diagnostics_run_spec_ref=splits_spec,
        runtime_input_pack=runtime_input_pack,
        observations=_json_fixture(
            fixture_root / "diagnostics" / "splits" / "synthetic_observations.json"
        ),
        min_sample_count=1,
    )
    cross_market_result = build_cross_market_diagnostics_run(
        diagnostics_run_spec=cross_market_spec,
        runtime_input_pack=runtime_input_pack,
        observations=_cross_market_observations(fixture_root),
    )
    return _DiagnosticsBundle(
        factor_report=factor_result.report,
        label_report=label_report,
        session_report=session_report,
        regime_report=regime_report,
        cross_market_report=cross_market_result.report,
        common_reports=(
            factor_result.report.report,
            label_report.diagnostics_report,
            session_report.common_report,
            regime_report.common_report,
            cross_market_result.report.diagnostics_report,
        ),
    )


def _diagnostics_spec(
    family: DiagnosticsFamily,
    *,
    study_run_spec: StudyRunSpec,
    runtime_plan: object,
) -> DiagnosticsRunSpec:
    return DiagnosticsRunSpec(
        diagnostics_family=family,
        study_run_spec=study_run_spec,
        runtime_plan=runtime_plan,
        spec_metadata={"requested_by": "rt_p25_synthetic_dry_run"},
    )


def _signal_probe_spec(
    *,
    runtime_input_pack: RuntimeInputPack,
    cost_stress_spec: CostStressSpec,
) -> SignalProbeSpec:
    return SignalProbeSpec(
        alpha_spec_ref=runtime_input_pack.alpha_spec_ref,
        study_spec_ref=runtime_input_pack.study_spec_ref,
        runtime_input_pack=runtime_input_pack,
        feature_ref=SignalFeatureRef.from_feature_pack(
            runtime_input_pack.feature_packs[0],
            signal_name="synthetic_zscore",
        ),
        label_ref=SignalLabelRef.from_label_pack(
            runtime_input_pack.label_packs[0],
            label_name="forward_return",
            horizon="5m",
        ),
        direction_policy=DirectionPolicy.LONG_SHORT_FLAT,
        thresholds=("0.5", "0.55"),
        primary_threshold="0.5",
        fill_policy=FillPolicy(),
        cost_stress_spec=cost_stress_spec,
        spec_metadata={"fixture": "rt_p25 synthetic signal probe"},
    )


def _cost_report_for_primary_probe(
    *,
    signal_probe_spec: SignalProbeSpec,
    observations: Sequence[Mapping[str, Any]],
    cost_diagnostics_spec: DiagnosticsRunSpec,
    runtime_input_pack: RuntimeInputPack,
    study_run_spec: StudyRunSpec,
):
    rows = tuple(SignalProbeObservation.from_mapping(row) for row in observations)
    series = build_next_bar_position_series(
        rows,
        threshold=signal_probe_spec.primary_threshold,
        direction_policy=signal_probe_spec.direction_policy,
        fill_policy=signal_probe_spec.fill_policy,
    )
    return build_cost_sensitivity_report(
        diagnostics_run_spec=cost_diagnostics_spec,
        fills=series.to_cost_fill_mappings(rows),
        lineage_refs=_signal_probe_lineage_refs(
            runtime_input_pack=runtime_input_pack,
            study_run_spec=study_run_spec,
            signal_probe_spec=signal_probe_spec,
        ),
        cost_stress_spec=signal_probe_spec.cost_stress_spec,
    )


def _terminal_pre_evidence_decision(
    *,
    diagnostics: _DiagnosticsBundle,
    cost_sensitivity_report: object,
    signal_probe_report: SignalProbeReport,
    bounded_grid: BoundedGridValidationResult,
    audit_result: NoLookaheadAuditResult,
) -> tuple[RuntimeDecisionState, tuple[RejectionReasonRecord, ...]] | None:
    report_reasons: list[RejectionReasonRecord] = []
    for report in diagnostics.common_reports:
        if report.status is not StudyRunResultState.DIAGNOSTICS_COMPLETE:
            report_reasons.extend(
                normalize_rejection_reasons(
                    report.rejection_reasons,
                    stage=RuntimeDecisionStage.DIAGNOSTICS,
                    decision_state=report.status,
                )
            )
    if getattr(cost_sensitivity_report, "status", None) is not StudyRunResultState.DIAGNOSTICS_COMPLETE:
        report_reasons.extend(
            normalize_rejection_reasons(
                cost_sensitivity_report.rejection_reasons,
                stage=RuntimeDecisionStage.COST_STRESS,
                decision_state=cost_sensitivity_report.status,
            )
        )
    if signal_probe_report.status is not StudyRunResultState.SIGNAL_PROBE_COMPLETE:
        report_reasons.extend(
            normalize_rejection_reasons(
                signal_probe_report.rejection_reasons,
                stage=RuntimeDecisionStage.SIGNAL_PROBE,
                decision_state=signal_probe_report.status,
            )
        )
    if bounded_grid.status is not BoundedGridOutcome.GUARD_PASSED:
        report_reasons.extend(
            normalize_rejection_reasons(
                bounded_grid.record.rejection_reasons,
                stage=RuntimeDecisionStage.BOUNDED_GRID,
                decision_state=RuntimeDecisionState.BLOCKED,
            )
        )
    if audit_result.outcome is not NoLookaheadAuditOutcome.POINT_IN_TIME_SAFE:
        report_reasons.extend(
            normalize_rejection_reasons(
                audit_result.runtime_entry_reasons,
                stage=RuntimeDecisionStage.NO_LOOKAHEAD_AUDIT,
                decision_state=RuntimeDecisionState.BLOCKED,
            )
        )
    if not report_reasons:
        return None
    decision = RuntimeDecision.from_reasons(tuple(_dedupe_records(report_reasons)))
    return decision.state, decision.reasons


def _blocked_before_run(
    *,
    entry_result: RuntimeEntryResult,
    input_resolution_result: RuntimeInputResolutionResult | None,
    warnings: tuple[str, ...],
    stage: RuntimeDecisionStage,
    reasons: Sequence[object] | None = None,
) -> RuntimeDryRunResult:
    source_reasons = tuple(reasons or ())
    if not source_reasons:
        source_reasons = (
            input_resolution_result.reasons
            if input_resolution_result is not None
            else entry_result.reasons
        )
    normalized = normalize_rejection_reasons(
        source_reasons,
        stage=stage,
        decision_state=RuntimeDecisionState.BLOCKED,
    )
    return RuntimeDryRunResult(
        dry_run_status="BLOCKED",
        terminal_decision_state=RuntimeDecisionState.BLOCKED,
        run_id=RUN_ID,
        entry_result=entry_result,
        input_resolution_result=input_resolution_result,
        run_summary=None,
        tool_result=None,
        rejection_reasons=tuple(_dedupe_records(normalized)),
        warning_reasons=warnings,
        no_lookahead_audit_coverage=(),
    )


def _terminal_result(
    *,
    entry_result: RuntimeEntryResult,
    input_resolution_result: RuntimeInputResolutionResult,
    terminal_state: RuntimeDecisionState,
    reasons: Sequence[RejectionReasonRecord],
    warnings: tuple[str, ...],
    runtime_input_pack: RuntimeInputPack,
    bounded_grid_result: BoundedGridValidationResult | None = None,
    no_lookahead_audit_result: NoLookaheadAuditResult | None = None,
    cost_sensitivity_report: object | None = None,
    signal_probe_report: SignalProbeReport | None = None,
) -> RuntimeDryRunResult:
    return RuntimeDryRunResult(
        dry_run_status=terminal_state.value,
        terminal_decision_state=terminal_state,
        run_id=RUN_ID,
        entry_result=entry_result,
        input_resolution_result=input_resolution_result,
        run_summary=None,
        tool_result=None,
        rejection_reasons=tuple(reasons),
        warning_reasons=warnings,
        no_lookahead_audit_coverage=_NO_LOOKAHEAD_AUDIT_COVERAGE,
        runtime_input_pack=runtime_input_pack,
        bounded_grid_result=bounded_grid_result,
        no_lookahead_audit_result=no_lookahead_audit_result,
        cost_sensitivity_report=cost_sensitivity_report,
        signal_probe_report=signal_probe_report,
    )


def _reason(
    *,
    code: RejectionReasonCode,
    message: str,
    stage: RuntimeDecisionStage,
    source_code: str,
    decision_state: RuntimeDecisionState,
    source_id: str | None = None,
) -> RejectionReasonRecord:
    return RejectionReasonRecord(
        code=code,
        message=message,
        decision_state=decision_state,
        stage=stage,
        source_code=source_code,
        source_id=source_id,
    )


def _warning_reasons(config: RuntimeDryRunConfig) -> tuple[str, ...]:
    warnings: list[str] = []
    if not Path(config.registry_path).exists():
        warnings.append(
            "local registry/data absent; used in-memory synthetic DatasetVersion and pack resolvers"
        )
    return tuple(warnings)


def _alpha_spec() -> AlphaSpec:
    payload: dict[str, Any] = {
        "hypothesis_id": "hyp_" + "a" * 24,
        "target_instruments": ["ES synthetic fixture", "NQ synthetic fixture", "RTY synthetic fixture"],
        "data_assumptions": {"dataset": "accepted synthetic DatasetVersion metadata only"},
        "factor_inputs": ["registered synthetic feature request fixture"],
        "label_references": [LABEL_SPEC_ID],
        "exclusion_rules": ["Exclude provider calls, broker access, and order routing."],
        "timestamp_assumptions": {"availability": "available_ts precedes feature use"},
        "cost_assumptions": {"stress": "base plus double_cost profiles required"},
        "expected_failure_modes": ["fail closed on missing specs or unsafe availability"],
        "promotion_criteria": ["No candidate or validation claim is made by this dry run."],
        "created_by": "rt-p25-runtime-dry-run",
        "created_at": datetime(2026, 1, 1, tzinfo=UTC).isoformat(),
    }
    payload["alpha_spec_id"] = generate_alpha_spec_id(payload)
    return AlphaSpec.from_mapping(payload)


def _study_spec(alpha_spec_id: str) -> StudySpec:
    payload: dict[str, Any] = {
        "alpha_spec_id": alpha_spec_id,
        "label_spec_id": LABEL_SPEC_ID,
        "dataset_scope": DATASET_SCOPE,
        "split_protocol": {"method": "fixed development and validation campaign partitions"},
        "metrics": ["tier_0_diagnostics", "signal_probe_proxy_summaries"],
        "cost_assumptions": {"profile": "base plus double_cost stress"},
        "variant_budget": 4,
        "locked_test_policy": {"policy": "locked-test selection is forbidden"},
        "negative_controls": ["synthetic no-lookahead guard"],
        "stopping_rules": ["stop on missing specs, missing availability, or unsafe partition use"],
    }
    payload["study_spec_id"] = generate_study_spec_id(payload)
    return StudySpec.from_mapping(payload)


def _study_input_pack(alpha_spec_id: str) -> StudyInputPack:
    return StudyInputPack(
        feature_request_ids=[FEATURE_REQUEST_ID],
        label_spec_ids=[LABEL_SPEC_ID],
        alpha_spec_id=alpha_spec_id,
        dataset_scope=DATASET_SCOPE,
    )


def _synthetic_dataset_version_resolver(
    registry_path: str | Path,
    dataset_version_id: object,
) -> DatasetVersion | None:
    _ = registry_path
    if dataset_version_id != DATASET_VERSION_ID:
        return None
    return DatasetVersion(
        dataset_version_id=DATASET_VERSION_ID,
        source="databento",
        symbol_universe=("ES", "NQ", "RTY"),
        bar_size="1m",
        what_to_show="TRADES",
        start_ts=datetime(2018, 1, 1, tzinfo=UTC),
        end_ts=datetime(2022, 12, 31, tzinfo=UTC),
        contract_universe=("ESM6", "NQM6", "RTYM6"),
        roll_policy_id="synthetic_rt_p25_roll_policy",
        manifest_hash="0" * 64,
        code_hash="1" * 64,
        config_hash="2" * 64,
        quality_report_hash="3" * 64,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _feature_label_resolver() -> FeatureLabelPackResolver:
    return FeatureLabelPackResolver(
        feature_store=_FeatureStore({FEATURE_VERSION_ID: _FeatureRecord()}),
        label_registry=_LabelRegistry({LABEL_VERSION_ID: _LabelRecord()}),
    )


@dataclass(frozen=True, slots=True)
class _Inputs:
    fields: tuple[str, ...] = ("close", "volume")
    input_views: tuple[str, ...] = ("canonical_ohlcv",)


@dataclass(frozen=True, slots=True)
class _FeatureSpec:
    feature_request_id: str = FEATURE_REQUEST_ID
    live: bool = True
    inputs: _Inputs = _Inputs()


@dataclass(frozen=True, slots=True)
class _FeatureRecord:
    feature_version_id: str = FEATURE_VERSION_ID
    feature_request_id: str = FEATURE_REQUEST_ID
    feature_set_id: str = "fset_rt_p25_synthetic"
    feature_set_version: str = "1"
    dataset_version_id: str = DATASET_VERSION_ID
    partition_id: str = "development"
    materialization_plan_id: str = "rt_p25_synthetic_feature_plan"
    first_event_ts: datetime = BASE_TS
    last_event_ts: datetime = BASE_TS + timedelta(minutes=5)
    first_available_ts: datetime = BASE_TS + timedelta(seconds=5)
    last_available_ts: datetime = BASE_TS + timedelta(minutes=5, seconds=5)
    lifecycle_state: str = "REGISTERED"
    feature_spec: _FeatureSpec = _FeatureSpec()


@dataclass(frozen=True, slots=True)
class _LabelRecord:
    label_version_id: str = LABEL_VERSION_ID
    label_spec_id: str = LABEL_SPEC_ID
    label_id: str = "forward_return_5m"
    dataset_version_id: str = DATASET_VERSION_ID
    partition_id: str = "development"
    materialization_plan_id: str = "rt_p25_synthetic_label_plan"
    first_event_ts: datetime = BASE_TS
    last_event_ts: datetime = BASE_TS + timedelta(minutes=5)
    first_label_available_ts: datetime = BASE_TS + timedelta(minutes=5)
    last_label_available_ts: datetime = BASE_TS + timedelta(minutes=10)
    lifecycle_state: str = "REGISTERED"


class _FeatureStore:
    def __init__(self, records: Mapping[str, _FeatureRecord]) -> None:
        self._records = dict(records)

    def resolve_feature_by_version(self, feature_version_id: str) -> _FeatureRecord | None:
        return self._records.get(feature_version_id)


class _LabelRegistry:
    def __init__(self, records: Mapping[str, _LabelRecord]) -> None:
        self._records = dict(records)

    def resolve_label_by_version(self, label_version_id: str) -> _LabelRecord | None:
        return self._records.get(label_version_id)


def _json_fixture(path: Path) -> tuple[dict[str, Any], ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"synthetic fixture must contain a list: {path}")
    return tuple(dict(item) for item in payload)


def _probe_observations(fixture_root: Path) -> tuple[dict[str, Any], ...]:
    rows = _json_fixture(fixture_root / "probe" / "synthetic_signal_probe_rows.json")
    return tuple(
        {
            **row,
            "bid": "0.99",
            "ask": "1.01",
            "spread": "0.02",
            "multiplier": "1",
        }
        for row in rows
    )


def _factor_observations(fixture_root: Path) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "factor_value": row["feature_value"],
            "label_value": row["label_value"],
            "available_ts": row["available_ts"],
            "label_available_ts": row["label_available_ts"],
            "horizon_seconds": 300,
        }
        for row in _probe_observations(fixture_root)
    )


def _cross_market_observations(fixture_root: Path) -> tuple[dict[str, Any], ...]:
    return tuple(
        {**row, "data_version": DATASET_VERSION_ID}
        for row in _json_fixture(
            fixture_root / "diagnostics" / "cross_market" / "synthetic_observations.json"
        )
    )


def _label_observations() -> tuple[dict[str, object], ...]:
    outcomes = (0.02, -0.01, 0.03, -0.02)
    rows: list[dict[str, object]] = []
    for index, outcome in enumerate(outcomes):
        event_ts = BASE_TS + timedelta(minutes=index)
        horizon_end = event_ts + timedelta(minutes=5)
        rows.append(
            {
                "label_outcome": outcome,
                "event_ts": event_ts.isoformat(),
                "horizon_end_ts": horizon_end.isoformat(),
                "label_available_ts": (horizon_end + timedelta(seconds=1)).isoformat(),
                "horizon_seconds": 300,
                "event_trigger": True,
                "mfe": abs(outcome) + 0.01,
                "mae": -abs(outcome),
                "target_before_stop": index % 2 == 0,
                "path_ambiguity": index == 3,
                "cost_model_ref": "rt_p25_spread_plus_bps_fixture",
                "cost_adjusted": True,
            }
        )
    return tuple(rows)


def _feature_quality_report(input_pack: RuntimeInputPack) -> dict[str, object]:
    return {
        "report_type": "FeatureQualityReport",
        "feature_id": "rt_p25_synthetic_signal",
        "feature_version_id": FEATURE_VERSION_ID,
        "dataset_version_id": input_pack.dataset_version_id,
        "partition_id": "development",
        "metrics": {
            "record_count": 4,
            "missing_bbo_count": 0,
            "bbo_quarantined_count": 0,
            "available_ts_missing_count": 0,
            "available_ts_invalid_count": 0,
            "available_ts_before_event_count": 0,
            "synthetic_no_trade_count": 0,
        },
        "blocking": [],
        "non_blocking": [],
    }


def _feature_coverage_report(input_pack: RuntimeInputPack) -> dict[str, object]:
    return {
        "report_type": "FeatureCoverageReport",
        "feature_id": "rt_p25_synthetic_signal",
        "feature_version_id": FEATURE_VERSION_ID,
        "dataset_version_id": input_pack.dataset_version_id,
        "partition_id": "development",
        "symbol_coverage": [{"key": "ES", "count": 4}],
        "session_coverage": [{"key": "RTH", "count": 4}],
        "partition_coverage": [{"key": "development", "count": 4}],
        "blocking": [],
        "non_blocking": [],
    }


def _label_audit_report(input_pack: RuntimeInputPack) -> dict[str, object]:
    return {
        "report_type": "LabelLeakageAuditReport",
        "label_version_id": LABEL_VERSION_ID,
        "label_id": "forward_return_5m",
        "label_spec_id": LABEL_SPEC_ID,
        "dataset_version_id": input_pack.dataset_version_id,
        "partition_id": "development",
        "lifecycle_state": "REGISTERED",
        "availability_time": (BASE_TS + timedelta(minutes=5)).isoformat(),
        "status": "CLEAN",
        "blocked": False,
        "clean": True,
        "value_records_checked": 4,
        "blocking_finding_count": 0,
        "non_blocking_finding_count": 0,
        "findings": [],
        "coverage": {
            "symbol_coverage": [{"key": "ES", "count": 4}],
            "session_coverage": [{"key": "RTH", "count": 4}],
            "partition_coverage": [{"key": "development", "count": 4}],
        },
        "blocking": [],
        "non_blocking": [],
    }


def _label_profiles(input_pack: RuntimeInputPack) -> tuple[dict[str, object], ...]:
    return (
        {
            "label_version_id": input_pack.label_packs[0].label_version_id,
            "cost_model_ref": "rt_p25_spread_plus_bps_fixture",
            "cost_adjustment_ref": "rt_p25_fixture_cost_adjustment",
            "cost_adjusted": True,
        },
    )


def _audit_feature_inputs() -> tuple[dict[str, object], ...]:
    return (
        {
            "event_ts": BASE_TS.isoformat(),
            "available_ts": (BASE_TS + timedelta(seconds=5)).isoformat(),
            "decision_ts": (BASE_TS + timedelta(minutes=6)).isoformat(),
            "field": "synthetic_zscore",
        },
    )


def _audit_label_inputs() -> tuple[dict[str, object], ...]:
    return (
        {
            "event_ts": BASE_TS.isoformat(),
            "label_available_ts": (BASE_TS + timedelta(minutes=5)).isoformat(),
            "label_id": "forward_return_5m",
        },
    )


def _audit_live_feature_windows() -> tuple[dict[str, object], ...]:
    return (
        {
            "window_type": "trailing",
            "lookback_bars": 5,
            "lookahead_bars": 0,
            "centered": False,
        },
    )


def _probe_fill_records(
    signal_probe_spec: SignalProbeSpec,
    observations: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, object], ...]:
    rows = tuple(SignalProbeObservation.from_mapping(row) for row in observations)
    series = build_next_bar_position_series(
        rows,
        threshold=signal_probe_spec.primary_threshold,
        direction_policy=signal_probe_spec.direction_policy,
        fill_policy=signal_probe_spec.fill_policy,
    )
    return tuple(fill.to_dict() for fill in series.fills)


def _study_run_manifest(
    *,
    runtime_input_pack: RuntimeInputPack,
    cost_model_version: CostModelVersion,
) -> StudyRunManifest:
    feature_refs = tuple(
        FeaturePackVersionRef(
            pack_id=pack.feature_version_id,
            content_hash="4" * 64,
            lineage_ref=f"{pack.materialization_plan_id}_lineage",
            available_ts_ref=f"{pack.feature_version_id}.available_ts",
        )
        for pack in runtime_input_pack.feature_packs
    )
    label_refs = tuple(
        LabelPackVersionRef(
            pack_id=pack.label_version_id,
            content_hash="5" * 64,
            lineage_ref=f"{pack.materialization_plan_id}_lineage",
            label_available_ts_ref=f"{pack.label_version_id}.label_available_ts",
        )
        for pack in runtime_input_pack.label_packs
    )
    return StudyRunManifest(
        run_id=RUN_ID,
        dataset_version_id=runtime_input_pack.dataset_version_id,
        dataset_version_hash=runtime_input_pack.dataset_reproducibility_hashes[0][1],
        dataset_lineage_ref="rt_p25_synthetic_dataset_lineage",
        dataset_admissibility_state=runtime_input_pack.dataset_lifecycle_state,
        feature_pack_versions=feature_refs,
        label_pack_versions=label_refs,
        code_version="rt_p25_synthetic_code_version",
        code_content_hash="6" * 64,
        config_version="rt_p25_synthetic_config",
        config_hash="7" * 64,
        cost_model_version=cost_model_version.cost_model_version_id,
        cost_model_hash=cost_model_version.content_hash,
    )


def _runtime_artifact_manifest() -> RuntimeArtifactManifest:
    return RuntimeArtifactManifest(
        run_id=RUN_ID,
        entries=(
            RuntimeArtifactEntry(
                artifact_id="rt_p25_dry_run_summary",
                kind="diagnostic_summary",
                location="summaries/rt-p25-runtime-dry-run-summary.json",
                content_hash="8" * 64,
                size_bytes=2048,
            ),
        ),
    )


def _study_run_record(
    *,
    manifest: StudyRunManifest,
    study_run_spec: StudyRunSpec,
    result_state: StudyRunResultState | RuntimeDecisionState | str,
    artifact_manifest: RuntimeArtifactManifest,
) -> StudyRunRecord:
    return StudyRunRecord(
        run_id=manifest.run_id,
        study_run_spec_ref=study_run_spec,
        result_state=result_state.value if isinstance(result_state, RuntimeDecisionState) else result_state,
        manifest_ref=manifest,
        artifact_refs=(artifact_manifest,),
    )


def _negative_control_results() -> tuple[dict[str, object], ...]:
    return (
        {
            "control_id": "rt_p25_synthetic_no_lookahead_guard",
            "status": "completed",
            "summary_only": True,
            "raw_or_heavy_data_embedded": False,
        },
    )


def _trial_id() -> str:
    return generate_governance_id(
        GovernanceIdKind.TRIAL_LEDGER_RECORD,
        {"name": "rt_p25_synthetic_dry_run"},
    )


def _lineage_refs(
    runtime_input_pack: RuntimeInputPack,
    study_run_spec: StudyRunSpec,
) -> dict[str, str]:
    return {
        "run_id": RUN_ID,
        "study_run_spec_id": study_run_spec.study_run_spec_id,
        "runtime_plan_id": study_run_spec.runtime_plan.plan_id,
        "dataset_version_id": runtime_input_pack.dataset_version_id,
        "feature_pack_ref": runtime_input_pack.feature_packs[0].feature_version_id,
        "label_pack_ref": runtime_input_pack.label_packs[0].label_version_id,
    }


def _signal_probe_lineage_refs(
    *,
    runtime_input_pack: RuntimeInputPack,
    study_run_spec: StudyRunSpec,
    signal_probe_spec: SignalProbeSpec,
) -> dict[str, str]:
    lineage = _lineage_refs(runtime_input_pack, study_run_spec)
    lineage.setdefault("signal_probe_spec_id", signal_probe_spec.signal_probe_spec_id)
    lineage.setdefault("alpha_spec_ref", signal_probe_spec.alpha_spec_ref)
    lineage.setdefault("study_spec_ref", signal_probe_spec.study_spec_ref)
    lineage.setdefault(
        "cost_model_version_id",
        signal_probe_spec.cost_stress_spec.cost_model_version.cost_model_version_id,
    )
    return lineage


def _dedupe_records(
    reasons: Sequence[RejectionReasonRecord],
) -> tuple[RejectionReasonRecord, ...]:
    seen: set[tuple[str, str, str]] = set()
    result: list[RejectionReasonRecord] = []
    for reason in reasons:
        key = (reason.code.value, reason.stage, reason.source_code)
        if key in seen:
            continue
        seen.add(key)
        result.append(reason)
    return tuple(result)


__all__ = [
    "PROHIBITED_MVP_STATES",
    "RuntimeDryRunConfig",
    "RuntimeDryRunResult",
    "run_runtime_dry_run",
]
