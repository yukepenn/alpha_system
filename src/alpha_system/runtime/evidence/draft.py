"""EvidenceDraft builder for governance EvidenceBundle inputs.

The draft is a descriptive, value-free assembly layer. It consumes runtime
reports and governance primitives by import and emits a payload that the real
``alpha_system.governance.evidence_bundle`` surface accepts.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

from alpha_system.governance.evidence_bundle import (
    EvidenceArtifactManifestEntry,
    EvidenceBundle,
    create_evidence_bundle,
)
from alpha_system.governance.serialization import (
    GovernanceSerializationError,
    JsonValue,
    canonical_serialize,
    deserialize,
)
from alpha_system.governance.serialization import (
    content_hash as governance_content_hash,
)
from alpha_system.governance.trial_ledger import TrialLedgerRecord
from alpha_system.runtime.audit.no_lookahead import (
    NoLookaheadAuditOutcome,
    NoLookaheadAuditResult,
)
from alpha_system.runtime.contracts.manifest import StudyRunManifest
from alpha_system.runtime.contracts.run_record import (
    RuntimeArtifactRef,
    StudyRunRecord,
    StudyRunResultState,
)
from alpha_system.runtime.cost.report import CostSensitivityReport
from alpha_system.runtime.decisions import (
    FORWARD_DECISION_STATES,
    RejectionReasonRecord,
    RuntimeDecision,
    RuntimeDecisionStage,
    RuntimeDecisionState,
    normalize_rejection_reason,
)
from alpha_system.runtime.grid.contracts import (
    BoundedGridOutcome,
    BoundedGridRunRecord,
    VariantBudget,
)
from alpha_system.runtime.probe.report import SignalProbeReport

EVIDENCE_DRAFT_SCHEMA = "alpha_system.runtime.evidence_draft.v1"
EVIDENCE_DRAFT_ID_PREFIX = "edraft"

type JsonScalar = None | bool | int | float | str
type JsonObject = dict[str, JsonValue]

DEFAULT_LIMITATIONS: tuple[str, ...] = (
    "EvidenceDraft is an evidence input, not a candidate.",
    "Fast-path screening is not Reference truth.",
    "Diagnostic PASS is not alpha validation.",
    "EvidenceDraft is descriptive only and makes no alpha, tradability, or profitability claim.",
)
GOVERNANCE_EVIDENCE_BUNDLE_SURFACE = (
    "alpha_system.governance.evidence_bundle.create_evidence_bundle"
)
GOVERNANCE_TRIAL_LEDGER_SURFACE = "alpha_system.governance.trial_ledger.TrialLedgerRecord"
REVIEWER_VERDICT_PENDING_REF = "review_pending_for_rt_p16_yellow_lane"
REQUIRED_COST_PROFILES = frozenset({"base", "double_cost"})

FORBIDDEN_SUMMARY_KEY_TOKENS: tuple[str, ...] = (
    "array",
    "canonical_bars",
    "dataframe",
    "feature_values",
    "label_values",
    "market_values",
    "provider_rows",
    "raw_values",
    "rows",
    "series",
    "value_array",
    "value_table",
    "values",
)
PROMOTIONAL_CLAIM_PHRASES: tuple[str, ...] = (
    "alpha validated",
    "candidate approved",
    "factor promoted",
    "live ready",
    "paper ready",
    "portfolio ready",
    "production ready",
    "production-ready",
    "profitable",
    "promoted factor",
    "strategy ready",
    "tradable",
    "validated alpha",
)
VAGUE_TEXT = frozenset(
    {
        "",
        "-",
        "n/a",
        "na",
        "none",
        "null",
        "tbd",
        "todo",
        "unknown",
        "placeholder",
        "to be defined",
        "to be determined",
    }
)


class EvidenceDraftContractError(ValueError):
    """Raised when an EvidenceDraft would hide state or embed value-bearing data."""


@dataclass(frozen=True, slots=True, init=False)
class EvidenceSectionSummary:
    """Reference and scalar summary for one upstream runtime evidence section."""

    section_name: str
    source_type: str
    source_id: str
    source_hash: str
    status: str
    summary_json: str
    limitations: tuple[str, ...]
    rejection_reasons: tuple[RejectionReasonRecord, ...]

    def __init__(
        self,
        *,
        section_name: str,
        source_type: str,
        source_id: str,
        source_hash: str,
        status: str,
        summary: Mapping[str, Any],
        limitations: Sequence[str] = (),
        rejection_reasons: Sequence[RejectionReasonRecord | Mapping[str, Any]] = (),
    ) -> None:
        normalized_reasons = tuple(_coerce_rejection_reason(reason) for reason in rejection_reasons)
        object.__setattr__(self, "section_name", _required_text(section_name, "section_name"))
        object.__setattr__(self, "source_type", _required_text(source_type, "source_type"))
        object.__setattr__(self, "source_id", _required_text(source_id, "source_id"))
        object.__setattr__(self, "source_hash", _required_text(source_hash, "source_hash"))
        object.__setattr__(self, "status", _required_text(status, "status"))
        object.__setattr__(self, "summary_json", _canonical_summary(summary, "summary"))
        object.__setattr__(self, "limitations", _text_tuple(limitations, "limitations"))
        object.__setattr__(self, "rejection_reasons", normalized_reasons)

    @property
    def summary(self) -> JsonObject:
        """Return the section summary as a defensive mapping."""

        return _json_dict(self.summary_json, field="summary")

    def to_dict(self) -> JsonObject:
        """Return a governance-safe summary for this section."""

        payload: dict[str, JsonValue] = {
            "section_name": self.section_name,
            "source_type": self.source_type,
            "source_ref": {
                "source_id": self.source_id,
                "source_hash": self.source_hash,
            },
            "status": self.status,
            "summary": self.summary,
            "limitations": list(self.limitations)
            if self.limitations
            else ["No section-local limitation supplied."],
            "descriptive_only": True,
            "promotion_basis_allowed": False,
        }
        if self.rejection_reasons:
            payload["rejection_reason_records"] = [
                _reason_payload(reason) for reason in self.rejection_reasons
            ]
        else:
            payload["reason_visibility"] = (
                "no_terminal_rejection_reason_applicable_for_forward_section"
            )
        return cast(JsonObject, payload)


@dataclass(frozen=True, slots=True, init=False)
class EvidenceDraft:
    """Immutable descriptive draft that feeds governance EvidenceBundle inputs."""

    draft_id: str
    run_id: str
    alpha_spec_id: str
    study_spec_id: str
    trial_ids: tuple[str, ...]
    decision: RuntimeDecision
    sections: tuple[EvidenceSectionSummary, ...]
    limitations: tuple[str, ...]
    artifact_manifest: tuple[EvidenceArtifactManifestEntry, ...]
    governance_evidence_input_json: str
    governance_evidence_bundle_id: str
    draft_hash: str
    descriptive_only: bool
    not_a_candidate: bool
    not_reference_truth: bool
    not_finalized_evidence_bundle: bool

    def __init__(
        self,
        *,
        run_id: str,
        alpha_spec_id: str,
        study_spec_id: str,
        trial_ids: Sequence[str],
        decision: RuntimeDecision,
        sections: Sequence[EvidenceSectionSummary],
        limitations: Sequence[str],
        artifact_manifest: Sequence[EvidenceArtifactManifestEntry],
        governance_evidence_bundle: EvidenceBundle,
    ) -> None:
        normalized_run_id = _required_text(run_id, "run_id")
        normalized_sections = tuple(_coerce_section(section) for section in sections)
        if not normalized_sections:
            raise EvidenceDraftContractError("EvidenceDraft requires at least one section summary")
        normalized_limitations = _text_tuple(limitations, "limitations")
        if not normalized_limitations:
            raise EvidenceDraftContractError("EvidenceDraft limitations must not be empty")
        normalized_artifacts = tuple(_coerce_artifact_entry(entry) for entry in artifact_manifest)
        if not normalized_artifacts:
            raise EvidenceDraftContractError("EvidenceDraft artifact manifest must not be empty")
        if not isinstance(decision, RuntimeDecision):
            raise EvidenceDraftContractError("decision must be a RuntimeDecision")
        normalized_trial_ids = tuple(_required_text(trial_id, "trial_id") for trial_id in trial_ids)
        if not normalized_trial_ids:
            raise EvidenceDraftContractError("EvidenceDraft requires at least one trial id")
        if not isinstance(governance_evidence_bundle, EvidenceBundle):
            raise EvidenceDraftContractError(
                "governance_evidence_bundle must come from governance.evidence_bundle"
            )

        evidence_payload = governance_evidence_bundle.to_dict()
        evidence_json = _canonical_json(evidence_payload, "governance_evidence_input")
        hash_payload = {
            "schema": EVIDENCE_DRAFT_SCHEMA,
            "run_id": normalized_run_id,
            "alpha_spec_id": _required_text(alpha_spec_id, "alpha_spec_id"),
            "study_spec_id": _required_text(study_spec_id, "study_spec_id"),
            "trial_ids": list(normalized_trial_ids),
            "decision": decision.to_dict(),
            "sections": [section.to_dict() for section in normalized_sections],
            "limitations": list(normalized_limitations),
            "artifact_manifest": [entry.to_dict() for entry in normalized_artifacts],
            "governance_evidence_bundle_id": governance_evidence_bundle.evidence_bundle_id,
            "descriptive_only": True,
            "not_a_candidate": True,
            "not_reference_truth": True,
            "not_finalized_evidence_bundle": True,
            "promotion_basis_allowed": False,
        }
        digest = governance_content_hash(cast(JsonValue, hash_payload))

        object.__setattr__(self, "draft_id", f"{EVIDENCE_DRAFT_ID_PREFIX}_{digest[:24]}")
        object.__setattr__(self, "run_id", normalized_run_id)
        object.__setattr__(self, "alpha_spec_id", _required_text(alpha_spec_id, "alpha_spec_id"))
        object.__setattr__(self, "study_spec_id", _required_text(study_spec_id, "study_spec_id"))
        object.__setattr__(self, "trial_ids", normalized_trial_ids)
        object.__setattr__(self, "decision", decision)
        object.__setattr__(self, "sections", normalized_sections)
        object.__setattr__(self, "limitations", normalized_limitations)
        object.__setattr__(self, "artifact_manifest", normalized_artifacts)
        object.__setattr__(self, "governance_evidence_input_json", evidence_json)
        object.__setattr__(
            self,
            "governance_evidence_bundle_id",
            governance_evidence_bundle.evidence_bundle_id,
        )
        object.__setattr__(self, "draft_hash", digest)
        object.__setattr__(self, "descriptive_only", True)
        object.__setattr__(self, "not_a_candidate", True)
        object.__setattr__(self, "not_reference_truth", True)
        object.__setattr__(self, "not_finalized_evidence_bundle", True)

    @property
    def decision_state(self) -> RuntimeDecisionState:
        """Return the draft decision state."""

        return self.decision.state

    @property
    def terminal_rejection_reasons(self) -> tuple[RejectionReasonRecord, ...]:
        """Return visible terminal reasons when the draft is rejected or blocked."""

        return self.decision.reasons

    def to_governance_evidence_input(self) -> JsonObject:
        """Return the payload accepted by the governance EvidenceBundle primitive."""

        return _json_dict(self.governance_evidence_input_json, field="governance_evidence_input")

    def validate_with_governance_evidence_bundle(self) -> EvidenceBundle:
        """Validate this draft's evidence input through the real governance primitive."""

        return EvidenceBundle.from_mapping(self.to_governance_evidence_input())

    def to_dict(self) -> JsonObject:
        """Return the descriptive draft payload without raw or heavy data."""

        payload: dict[str, JsonValue] = {
            "schema": EVIDENCE_DRAFT_SCHEMA,
            "draft_id": self.draft_id,
            "run_id": self.run_id,
            "alpha_spec_id": self.alpha_spec_id,
            "study_spec_id": self.study_spec_id,
            "trial_ids": list(self.trial_ids),
            "decision": cast(JsonValue, self.decision.to_dict()),
            "sections": [section.to_dict() for section in self.sections],
            "limitations": list(self.limitations),
            "artifact_manifest": [entry.to_dict() for entry in self.artifact_manifest],
            "governance_evidence_bundle_id": self.governance_evidence_bundle_id,
            "draft_hash": self.draft_hash,
            "descriptive_only": True,
            "not_a_candidate": True,
            "not_reference_truth": True,
            "not_finalized_evidence_bundle": True,
            "promotion_basis_allowed": False,
            "raw_or_heavy_data_embedded": False,
        }
        return cast(JsonObject, payload)


def build_evidence_draft(
    *,
    alpha_spec_id: str,
    study_spec_id: str,
    trial_refs: Sequence[str | TrialLedgerRecord],
    study_run_manifest: StudyRunManifest,
    study_run_record: StudyRunRecord,
    negative_control_results: Sequence[Mapping[str, Any]],
    factor_diagnostics_report: object | None = None,
    label_diagnostics_report: object | None = None,
    session_split_report: object | None = None,
    regime_split_report: object | None = None,
    cross_market_diagnostics_report: object | None = None,
    cost_sensitivity_report: CostSensitivityReport | None = None,
    signal_probe_report: SignalProbeReport | None = None,
    bounded_grid_record: BoundedGridRunRecord | None = None,
    no_lookahead_audit_result: NoLookaheadAuditResult | Mapping[str, Any] | None = None,
    decision: RuntimeDecision | Mapping[str, Any] | None = None,
    rejection_reasons: Sequence[RejectionReasonRecord | Mapping[str, Any]] = (),
    limitations: Sequence[str] = (),
    artifact_manifest: Sequence[EvidenceArtifactManifestEntry | Mapping[str, Any]] = (),
    reviewer_verdict_reference: str = REVIEWER_VERDICT_PENDING_REF,
) -> EvidenceDraft:
    """Build a descriptive EvidenceDraft and governance-accepted evidence input."""

    _require_manifest(study_run_manifest)
    _require_record(study_run_record)
    runtime_decision = _coerce_decision(
        decision=decision,
        rejection_reasons=rejection_reasons,
        study_run_record=study_run_record,
    )

    reports = (
        ("factor_diagnostics", factor_diagnostics_report),
        ("label_diagnostics", label_diagnostics_report),
        ("session_split_diagnostics", session_split_report),
        ("regime_split_diagnostics", regime_split_report),
        ("cross_market_diagnostics", cross_market_diagnostics_report),
    )
    sections: list[EvidenceSectionSummary] = [
        _report_section(section_name=name, report=report)
        for name, report in reports
        if report is not None
    ]

    if cost_sensitivity_report is not None:
        sections.append(_cost_section(cost_sensitivity_report))
    if signal_probe_report is not None:
        if cost_sensitivity_report is None:
            raise EvidenceDraftContractError(
                "SignalProbeReport references require a CostSensitivityReport"
            )
        _assert_probe_cost_ref(signal_probe_report, cost_sensitivity_report)
        sections.append(_signal_probe_section(signal_probe_report))
    if bounded_grid_record is not None:
        sections.append(_bounded_grid_section(bounded_grid_record))
    if no_lookahead_audit_result is not None:
        sections.append(_no_lookahead_section(no_lookahead_audit_result))

    if runtime_decision.state in FORWARD_DECISION_STATES:
        if cost_sensitivity_report is None:
            raise EvidenceDraftContractError(
                "EVIDENCE_DRAFT_READY requires a CostSensitivityReport summary"
            )
        if no_lookahead_audit_result is None:
            raise EvidenceDraftContractError(
                "EVIDENCE_DRAFT_READY requires a NoLookaheadRuntimeAudit result"
            )
        if not any(name for name, report in reports if report is not None):
            raise EvidenceDraftContractError(
                "EVIDENCE_DRAFT_READY requires at least one diagnostics report summary"
            )

    if not sections:
        sections.append(_decision_only_section(runtime_decision, study_run_record))

    normalized_limitations = _merged_limitations(
        DEFAULT_LIMITATIONS,
        limitations,
        *(section.limitations for section in sections),
    )
    trial_ids = _coerce_trial_ids(trial_refs)
    artifacts = _artifact_manifest_entries(
        explicit=artifact_manifest,
        study_run_record=study_run_record,
    )
    diagnostics_summary = _diagnostics_summary(
        runtime_decision=runtime_decision,
        study_run_manifest=study_run_manifest,
        study_run_record=study_run_record,
        sections=sections,
    )

    evidence_bundle = create_evidence_bundle(
        alpha_spec_id=alpha_spec_id,
        study_spec_id=study_spec_id,
        trial_ids=list(trial_ids),
        data_version=study_run_manifest.dataset_version_id,
        factor_version=_joined_pack_ids(
            [ref.pack_id for ref in study_run_manifest.feature_pack_versions],
            field="factor_version",
        ),
        label_version=_joined_pack_ids(
            [ref.pack_id for ref in study_run_manifest.label_pack_versions],
            field="label_version",
        ),
        code_hash=study_run_manifest.code_content_hash,
        config_hash=study_run_manifest.config_hash,
        diagnostics_summary=diagnostics_summary,
        negative_control_results=[
            _pruned_mapping(result, field=f"negative_control_results[{index}]")
            for index, result in enumerate(
                _require_non_empty_sequence(
                    negative_control_results,
                    "negative_control_results",
                )
            )
        ],
        limitations=list(normalized_limitations),
        artifact_manifest=list(artifacts),
        reviewer_verdict_reference=reviewer_verdict_reference,
    )
    return EvidenceDraft(
        run_id=study_run_manifest.run_id,
        alpha_spec_id=alpha_spec_id,
        study_spec_id=study_spec_id,
        trial_ids=trial_ids,
        decision=runtime_decision,
        sections=tuple(sections),
        limitations=normalized_limitations,
        artifact_manifest=artifacts,
        governance_evidence_bundle=evidence_bundle,
    )


def _report_section(*, section_name: str, report: object) -> EvidenceSectionSummary:
    ref = _object_ref(report)
    summary: dict[str, Any] = {
        "report_ref": ref,
        "status": _state_text(_first_attr(report, "status")),
        "section_summary_policy": "references_and_scalar_summaries_only",
    }
    coverage = _first_attr(report, "coverage_summary")
    if isinstance(coverage, Mapping) and coverage:
        summary["coverage_summary"] = coverage
    quality = _first_attr(report, "quality_summary")
    if isinstance(quality, Mapping) and quality:
        summary["quality_summary"] = quality
    if section_name in {"session_split_diagnostics", "regime_split_diagnostics"}:
        split_count = len(tuple(getattr(report, "split_summaries", ())))
        summary["split_summary_count"] = split_count
    if section_name == "cross_market_diagnostics":
        sync = getattr(report, "timestamp_sync_summary", None)
        if isinstance(sync, Mapping) and sync:
            summary["timestamp_sync_summary"] = sync

    return EvidenceSectionSummary(
        section_name=section_name,
        source_type=type(report).__name__,
        source_id=_required_text(ref["source_id"], "report.source_id"),
        source_hash=_required_text(ref["source_hash"], "report.source_hash"),
        status=_state_text(_first_attr(report, "status")),
        summary=summary,
        limitations=_limitations_from(report),
        rejection_reasons=_normalize_report_reasons(report),
    )


def _cost_section(report: CostSensitivityReport) -> EvidenceSectionSummary:
    if not isinstance(report, CostSensitivityReport):
        raise EvidenceDraftContractError("cost_sensitivity_report must be CostSensitivityReport")
    profile_names = {summary.profile_name for summary in report.profile_summaries}
    missing = REQUIRED_COST_PROFILES - profile_names
    if missing:
        raise EvidenceDraftContractError(
            f"cost sensitivity summary missing required profiles: {', '.join(sorted(missing))}"
        )
    if report.slippage_labeled_proxy is not True:
        raise EvidenceDraftContractError("slippage must be carried as a labeled proxy")
    if any(summary.promotion_basis_allowed for summary in report.profile_summaries):
        raise EvidenceDraftContractError("cost stress cannot be a promotion basis")

    base_summary = _profile_summary(report, "base")
    double_summary = _profile_summary(report, "double_cost")
    ref = _object_ref(report)
    return EvidenceSectionSummary(
        section_name="cost_sensitivity",
        source_type=type(report).__name__,
        source_id=ref["source_id"],
        source_hash=ref["source_hash"],
        status=_state_text(report.status),
        summary={
            "report_ref": ref,
            "status": _state_text(report.status),
            "required_profiles": sorted(REQUIRED_COST_PROFILES),
            "profile_names": sorted(profile_names),
            "base_cost_summary": base_summary,
            "double_cost_summary": double_summary,
            "cost_model_version": report.cost_model_version.to_dict(),
            "slippage_labeled_proxy": True,
            "zero_cost_diagnostic_only": report.cost_model_version.zero_cost_diagnostic_only,
            "promotion_basis_allowed": False,
        },
        limitations=report.limitations,
        rejection_reasons=_normalize_report_reasons(report),
    )


def _signal_probe_section(report: SignalProbeReport) -> EvidenceSectionSummary:
    if not isinstance(report, SignalProbeReport):
        raise EvidenceDraftContractError("signal_probe_report must be SignalProbeReport")
    ref = _object_ref(report)
    return EvidenceSectionSummary(
        section_name="signal_probe",
        source_type=type(report).__name__,
        source_id=ref["source_id"],
        source_hash=ref["source_hash"],
        status=_state_text(report.status),
        summary={
            "report_ref": ref,
            "status": _state_text(report.status),
            "cost_sensitivity_report_ref": report.cost_sensitivity_report_ref.to_dict(),
            "cost_stress_evidence_state": report.cost_stress_evidence_state,
            "threshold_summary_count": len(report.threshold_summaries),
            "fast_path_screening": True,
            "not_strategy_validation": True,
            "not_a_candidate": True,
            "promotion_basis_allowed": False,
        },
        limitations=report.limitations,
        rejection_reasons=_normalize_report_reasons(report),
    )


def _bounded_grid_section(record: BoundedGridRunRecord) -> EvidenceSectionSummary:
    if not isinstance(record, BoundedGridRunRecord):
        raise EvidenceDraftContractError("bounded_grid_record must be BoundedGridRunRecord")
    reasons = (
        tuple(_coerce_rejection_reason(reason) for reason in _grid_rejection_records(record))
        if record.guard_outcome is BoundedGridOutcome.GUARD_REJECTED
        else ()
    )
    budget_summary = (
        _variant_budget_summary(record.variant_budget)
        if record.variant_budget is not None
        else {"budget_state": "not_available_because_grid_spec_failed_before_budget_resolution"}
    )
    return EvidenceSectionSummary(
        section_name="bounded_grid",
        source_type=type(record).__name__,
        source_id=record.record_id,
        source_hash=record.content_hash,
        status=record.guard_outcome.value,
        summary={
            "record_ref": {
                "record_id": record.record_id,
                "content_hash": record.content_hash,
            },
            "guard_outcome": record.guard_outcome.value,
            "variant_budget": budget_summary,
            "realized_variant_count": (
                "not_available_because_grid_was_rejected_before_count"
                if record.realized_variant_count is None
                else record.realized_variant_count
            ),
            "partition_scope_count": len(record.partition_scope_ids),
            "overfit_warning_count": record.overfit_warning_count,
            "repeated_run_index": record.repeated_run_index,
            "bounded": True,
            "promotion_basis_allowed": False,
        },
        limitations=("Bounded-grid records are descriptive and are not promotion decisions.",),
        rejection_reasons=reasons,
    )


def _no_lookahead_section(
    result: NoLookaheadAuditResult | Mapping[str, Any],
) -> EvidenceSectionSummary:
    audit = _coerce_no_lookahead_result(result)
    reasons = tuple(
        normalize_rejection_reason(reason, stage=RuntimeDecisionStage.NO_LOOKAHEAD_AUDIT)
        for reason in audit.reasons
    )
    source_hash = governance_content_hash(cast(JsonValue, audit.to_dict()))
    summary: dict[str, Any] = {
        "outcome": audit.outcome.value,
        "accepted": audit.accepted,
        "integrity_only": True,
        "not_alpha_validation": True,
        "not_strategy_validation": True,
        "not_a_candidate": True,
    }
    if reasons:
        summary["rejection_reason_count"] = len(reasons)
    else:
        summary["reason_visibility"] = "point_in_time_safe_audit_has_no_rejection_reasons"
    return EvidenceSectionSummary(
        section_name="no_lookahead_audit",
        source_type=type(audit).__name__,
        source_id=f"no_lookahead_{audit.outcome.value.lower()}",
        source_hash=source_hash,
        status=audit.outcome.value,
        summary=summary,
        limitations=("No-lookahead audit is integrity evidence only and is not alpha validation.",),
        rejection_reasons=reasons,
    )


def _decision_only_section(
    decision: RuntimeDecision,
    study_run_record: StudyRunRecord,
) -> EvidenceSectionSummary:
    return EvidenceSectionSummary(
        section_name="terminal_decision_visibility",
        source_type=type(study_run_record).__name__,
        source_id=study_run_record.record_id,
        source_hash=study_run_record.record_hash,
        status=decision.state.value,
        summary={
            "study_run_record_ref": _study_run_record_ref(study_run_record),
            "decision_state": decision.state.value,
            "terminal_reason_count": len(decision.reasons),
            "visibility_policy": "terminal_reasons_remain_visible_in_evidence_draft",
        },
        limitations=("Terminal drafts are visibility records and are not candidates.",),
        rejection_reasons=decision.reasons,
    )


def _diagnostics_summary(
    *,
    runtime_decision: RuntimeDecision,
    study_run_manifest: StudyRunManifest,
    study_run_record: StudyRunRecord,
    sections: Sequence[EvidenceSectionSummary],
) -> JsonObject:
    payload: dict[str, Any] = {
        "draft_contract": {
            "schema": EVIDENCE_DRAFT_SCHEMA,
            "runtime_state": runtime_decision.state.value,
            "descriptive_only": True,
            "not_a_candidate": True,
            "not_reference_truth": True,
            "not_finalized_evidence_bundle": True,
            "promotion_basis_allowed": False,
        },
        "decision": _decision_summary(runtime_decision),
        "study_run_manifest": _manifest_summary(study_run_manifest),
        "study_run_record": _study_run_record_summary(study_run_record),
        "evidence_sections": [section.to_dict() for section in sections],
        "governance_consumption": {
            "evidence_bundle_surface": GOVERNANCE_EVIDENCE_BUNDLE_SURFACE,
            "trial_ledger_surface": GOVERNANCE_TRIAL_LEDGER_SURFACE,
            "consumed_not_duplicated": True,
        },
        "payload_policy": {
            "summary_only": True,
            "version_ids_and_references_only": True,
            "raw_or_heavy_payload_embedded": False,
        },
    }
    return _pruned_mapping(payload, field="diagnostics_summary")


def _decision_summary(decision: RuntimeDecision) -> JsonObject:
    payload: dict[str, Any] = {
        "state": decision.state.value,
        "source_state": decision.source_state or "evidence_draft_builder_assigned_forward_state",
    }
    if decision.reasons:
        payload["visible_rejection_reasons"] = [
            _reason_payload(reason) for reason in decision.reasons
        ]
    else:
        payload["reason_visibility"] = "no_terminal_reasons_for_evidence_draft_ready"
    return _pruned_mapping(payload, field="decision")


def _manifest_summary(manifest: StudyRunManifest) -> JsonObject:
    return _pruned_mapping(
        {
            "manifest_id": manifest.manifest_id,
            "manifest_hash": manifest.manifest_hash,
            "run_id": manifest.run_id,
            "dataset_version_id": manifest.dataset_version_id,
            "dataset_version_hash": manifest.dataset_version_hash,
            "dataset_admissibility_state": manifest.dataset_admissibility_state,
            "feature_pack_count": len(manifest.feature_pack_versions),
            "label_pack_count": len(manifest.label_pack_versions),
            "feature_pack_ids": [ref.pack_id for ref in manifest.feature_pack_versions],
            "label_pack_ids": [ref.pack_id for ref in manifest.label_pack_versions],
            "code_version": manifest.code_version,
            "code_content_hash": manifest.code_content_hash,
            "config_version": manifest.config_version,
            "config_hash": manifest.config_hash,
            "cost_model_version": manifest.cost_model_version
            or "cost_model_version_recorded_in_cost_sensitivity_section",
        },
        field="study_run_manifest",
    )


def _study_run_record_summary(record: StudyRunRecord) -> JsonObject:
    return _pruned_mapping(
        {
            "record_id": record.record_id,
            "run_id": record.run_id,
            "record_hash": record.record_hash,
            "result_state": record.result_state.value,
            "artifact_ref_count": len(record.artifact_refs),
            "manifest_ref": record.manifest_ref.to_dict(),
            "study_run_spec_ref": record.study_run_spec_ref.to_dict(),
            "visible_rejection_reason_count": len(record.rejection_reasons),
        },
        field="study_run_record",
    )


def _coerce_decision(
    *,
    decision: RuntimeDecision | Mapping[str, Any] | None,
    rejection_reasons: Sequence[RejectionReasonRecord | Mapping[str, Any]],
    study_run_record: StudyRunRecord,
) -> RuntimeDecision:
    if decision is not None:
        normalized = (
            decision
            if isinstance(decision, RuntimeDecision)
            else RuntimeDecision.from_dict(decision)
        )
        if normalized.state in FORWARD_DECISION_STATES:
            return RuntimeDecision(
                state=RuntimeDecisionState.EVIDENCE_DRAFT_READY,
                source_state=normalized.state.value,
            )
        return normalized

    if rejection_reasons:
        return RuntimeDecision.from_reasons(
            tuple(_coerce_rejection_reason(reason) for reason in rejection_reasons)
        )

    if study_run_record.result_state in {
        StudyRunResultState.DIAGNOSTICS_FAILED,
        StudyRunResultState.REJECTED,
        StudyRunResultState.INCONCLUSIVE,
        StudyRunResultState.BLOCKED,
    }:
        reasons = tuple(
            normalize_rejection_reason(
                reason,
                stage=RuntimeDecisionStage.DIAGNOSTICS,
                decision_state=study_run_record.result_state,
            )
            for reason in study_run_record.rejection_reasons
        )
        return RuntimeDecision(state=study_run_record.result_state, reasons=reasons)

    return RuntimeDecision(state=RuntimeDecisionState.EVIDENCE_DRAFT_READY)


def _artifact_manifest_entries(
    *,
    explicit: Sequence[EvidenceArtifactManifestEntry | Mapping[str, Any]],
    study_run_record: StudyRunRecord,
) -> tuple[EvidenceArtifactManifestEntry, ...]:
    if explicit:
        return tuple(_coerce_artifact_entry(entry) for entry in explicit)
    if study_run_record.artifact_refs:
        return tuple(_artifact_from_runtime_ref(ref) for ref in study_run_record.artifact_refs)
    return (
        EvidenceArtifactManifestEntry.from_mapping(
            {
                "logical_name": "study_run_manifest",
                "role": "study_run_manifest_reference",
                "reference": f"runtime-manifests/{study_run_record.manifest_ref.manifest_id}",
                "content_hash": study_run_record.manifest_ref.manifest_hash,
            }
        ),
    )


def _artifact_from_runtime_ref(ref: RuntimeArtifactRef) -> EvidenceArtifactManifestEntry:
    return EvidenceArtifactManifestEntry.from_mapping(
        {
            "logical_name": ref.artifact_id,
            "role": "runtime_summary_reference",
            "reference": ref.location,
            "content_hash": ref.content_hash,
        }
    )


def _coerce_artifact_entry(
    value: EvidenceArtifactManifestEntry | Mapping[str, Any],
) -> EvidenceArtifactManifestEntry:
    if isinstance(value, EvidenceArtifactManifestEntry):
        return value
    if isinstance(value, Mapping):
        return EvidenceArtifactManifestEntry.from_mapping(value)
    raise EvidenceDraftContractError(
        "artifact entry must be EvidenceArtifactManifestEntry or mapping, "
        f"got {type(value).__name__}"
    )


def _coerce_trial_ids(trial_refs: Sequence[str | TrialLedgerRecord]) -> tuple[str, ...]:
    if isinstance(trial_refs, str) or not isinstance(trial_refs, Sequence) or not trial_refs:
        raise EvidenceDraftContractError("trial_refs must be a non-empty sequence")
    ids: list[str] = []
    for index, ref in enumerate(trial_refs):
        if isinstance(ref, TrialLedgerRecord):
            ids.append(ref.trial_id)
        elif isinstance(ref, str):
            ids.append(ref)
        else:
            raise EvidenceDraftContractError(
                f"trial_refs[{index}] must be TrialLedgerRecord or trial id string"
            )
    return tuple(ids)


def _profile_summary(report: CostSensitivityReport, profile_name: str) -> JsonObject:
    for summary in report.profile_summaries:
        if summary.profile_name == profile_name:
            return _pruned_mapping(summary.to_dict(), field=f"cost_profile.{profile_name}")
    raise EvidenceDraftContractError(f"missing cost profile summary: {profile_name}")


def _assert_probe_cost_ref(
    probe_report: SignalProbeReport,
    cost_report: CostSensitivityReport,
) -> None:
    if probe_report.cost_sensitivity_report_ref.to_dict() != cost_report.to_ref().to_dict():
        raise EvidenceDraftContractError(
            "SignalProbeReport cost_sensitivity_report_ref must match the supplied "
            "CostSensitivityReport"
        )


def _grid_rejection_records(record: BoundedGridRunRecord) -> tuple[RejectionReasonRecord, ...]:
    return tuple(
        normalize_rejection_reason(
            reason,
            stage=RuntimeDecisionStage.BOUNDED_GRID,
            decision_state=(
                RuntimeDecisionState.INCONCLUSIVE
                if str(reason.decision_state) == "INPUTS_INCONCLUSIVE"
                else RuntimeDecisionState.REJECTED
            ),
        )
        for reason in record.rejection_reasons
    )


def _variant_budget_summary(value: VariantBudget) -> JsonObject:
    return _pruned_mapping(value.to_dict(), field="variant_budget")


def _coerce_no_lookahead_result(
    value: NoLookaheadAuditResult | Mapping[str, Any],
) -> NoLookaheadAuditResult:
    if isinstance(value, NoLookaheadAuditResult):
        return value
    if not isinstance(value, Mapping):
        raise EvidenceDraftContractError("no_lookahead_audit_result must be an audit result")
    outcome = value.get("outcome")
    reasons = tuple(value.get("reasons", ()))
    return NoLookaheadAuditResult(outcome=NoLookaheadAuditOutcome(str(outcome)), reasons=reasons)


def _normalize_report_reasons(report: object) -> tuple[RejectionReasonRecord, ...]:
    reasons = getattr(report, "rejection_reasons", ())
    if not reasons:
        return ()
    return tuple(
        normalize_rejection_reason(
            reason,
            stage=_stage_from_section_type(type(report).__name__),
            decision_state=_state_text(getattr(report, "status", RuntimeDecisionState.REJECTED)),
        )
        for reason in reasons
    )


def _stage_from_section_type(source_type: str) -> RuntimeDecisionStage:
    lowered = source_type.lower()
    if "probe" in lowered:
        return RuntimeDecisionStage.SIGNAL_PROBE
    if "cost" in lowered:
        return RuntimeDecisionStage.COST_STRESS
    if "grid" in lowered:
        return RuntimeDecisionStage.BOUNDED_GRID
    return RuntimeDecisionStage.DIAGNOSTICS


def _object_ref(value: object) -> dict[str, str]:
    to_ref = getattr(value, "to_ref", None)
    if callable(to_ref):
        ref = to_ref()
        to_dict = getattr(ref, "to_dict", None)
        if callable(to_dict):
            payload = to_dict()
            return {
                "source_id": _required_text(
                    payload.get("report_id")
                    or payload.get("record_id")
                    or payload.get("signal_probe_spec_id")
                    or payload.get("diagnostics_run_spec_id")
                    or payload.get("bounded_grid_spec_id"),
                    "source_id",
                ),
                "source_hash": _required_text(
                    payload.get("report_hash") or payload.get("content_hash"),
                    "source_hash",
                ),
                "source_kind": _required_text(
                    payload.get("report_kind") or type(value).__name__,
                    "source_kind",
                ),
            }
    for id_attr, hash_attr in (
        ("report_id", "report_hash"),
        ("record_id", "content_hash"),
        ("record_id", "record_hash"),
    ):
        source_id = _first_attr(value, id_attr)
        source_hash = _first_attr(value, hash_attr)
        if source_id is not None and source_hash is not None:
            return {
                "source_id": _required_text(source_id, "source_id"),
                "source_hash": _required_text(source_hash, "source_hash"),
                "source_kind": type(value).__name__,
            }
    raise EvidenceDraftContractError(f"{type(value).__name__} does not expose a report reference")


def _first_attr(value: object, name: str) -> Any:
    if hasattr(value, name):
        return getattr(value, name)
    for nested in ("report", "diagnostics_report", "common_report"):
        child = getattr(value, nested, None)
        if child is not None and hasattr(child, name):
            return getattr(child, name)
    return None


def _limitations_from(value: object) -> tuple[str, ...]:
    limitations = _first_attr(value, "limitations")
    if limitations is None:
        return ()
    return _text_tuple(limitations, "limitations")


def _study_run_record_ref(record: StudyRunRecord) -> JsonObject:
    return {
        "record_id": record.record_id,
        "run_id": record.run_id,
        "record_hash": record.record_hash,
        "result_state": record.result_state.value,
    }


def _reason_payload(reason: RejectionReasonRecord) -> JsonObject:
    return _pruned_mapping(reason.to_dict(), field="rejection_reason")


def _coerce_rejection_reason(
    value: RejectionReasonRecord | Mapping[str, Any],
) -> RejectionReasonRecord:
    if isinstance(value, RejectionReasonRecord):
        return value
    if isinstance(value, Mapping):
        return normalize_rejection_reason(value)
    raise EvidenceDraftContractError(
        f"rejection reason must be RejectionReasonRecord or mapping, got {type(value).__name__}"
    )


def _coerce_section(value: EvidenceSectionSummary) -> EvidenceSectionSummary:
    if isinstance(value, EvidenceSectionSummary):
        return value
    raise EvidenceDraftContractError("sections must contain EvidenceSectionSummary objects")


def _require_manifest(value: StudyRunManifest) -> None:
    if not isinstance(value, StudyRunManifest):
        raise EvidenceDraftContractError("study_run_manifest must be StudyRunManifest")


def _require_record(value: StudyRunRecord) -> None:
    if not isinstance(value, StudyRunRecord):
        raise EvidenceDraftContractError("study_run_record must be StudyRunRecord")


def _joined_pack_ids(values: Sequence[str], *, field: str) -> str:
    if not values:
        raise EvidenceDraftContractError(f"{field} requires at least one version id")
    return ";".join(_required_text(value, field) for value in values)


def _state_text(value: object) -> str:
    if hasattr(value, "value"):
        return _required_text(getattr(value, "value"), "state")
    return _required_text(value, "state")


def _merged_limitations(*groups: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    merged: list[str] = []
    for group in groups:
        for item in _text_tuple(group, "limitations"):
            if item not in seen:
                merged.append(item)
                seen.add(item)
    return tuple(merged)


def _require_non_empty_sequence(value: Sequence[Any], field: str) -> Sequence[Any]:
    if isinstance(value, str) or not isinstance(value, Sequence) or not value:
        raise EvidenceDraftContractError(f"{field} must be a non-empty sequence")
    return value


def _text_tuple(values: Sequence[str], field: str) -> tuple[str, ...]:
    if isinstance(values, str):
        raise EvidenceDraftContractError(f"{field} must be a sequence of text")
    return tuple(_required_text(value, f"{field}[{index}]") for index, value in enumerate(values))


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvidenceDraftContractError(f"{field} is required")
    text = value.strip()
    lowered = text.lower()
    if lowered in VAGUE_TEXT:
        raise EvidenceDraftContractError(f"{field} must be explicit")
    if any(phrase in lowered for phrase in PROMOTIONAL_CLAIM_PHRASES):
        raise EvidenceDraftContractError(f"{field} must not make promotional claims")
    return text


def _canonical_summary(value: Mapping[str, Any], field: str) -> str:
    return _canonical_json(_pruned_mapping(value, field=field), field)


def _canonical_json(value: Mapping[str, Any], field: str) -> str:
    try:
        return canonical_serialize(cast(JsonValue, dict(value)))
    except GovernanceSerializationError as exc:
        raise EvidenceDraftContractError(f"{field} must be canonical JSON: {exc}") from exc


def _json_dict(text: str, *, field: str) -> JsonObject:
    try:
        value = deserialize(text)
    except GovernanceSerializationError as exc:
        raise EvidenceDraftContractError(f"{field} must be serialized JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise EvidenceDraftContractError(f"{field} must serialize to a mapping")
    return cast(JsonObject, value)


def _pruned_mapping(value: Mapping[str, Any], *, field: str) -> JsonObject:
    if not isinstance(value, Mapping):
        raise EvidenceDraftContractError(f"{field} must be a mapping")
    normalized: dict[str, JsonValue] = {}
    for key, item in value.items():
        normalized_key = _checked_key(key, field=field)
        pruned = _pruned_json_value(item, field=f"{field}.{normalized_key}")
        if pruned is not None:
            normalized[normalized_key] = pruned
    if not normalized:
        raise EvidenceDraftContractError(f"{field} must not be empty")
    return normalized


def _pruned_json_value(value: Any, *, field: str) -> JsonValue | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise EvidenceDraftContractError(f"{field} must be finite")
        return value
    if isinstance(value, str):
        return _required_text(value, field)
    if isinstance(value, Mapping):
        pruned = _pruned_mapping(value, field=field)
        return cast(JsonValue, pruned)
    if isinstance(value, Sequence) and not isinstance(value, str):
        items: list[JsonValue] = []
        for index, item in enumerate(value):
            pruned = _pruned_json_value(item, field=f"{field}[{index}]")
            if pruned is not None:
                items.append(pruned)
        if not items:
            return None
        return items
    raise EvidenceDraftContractError(
        f"{field} must be JSON-compatible summary metadata, got {type(value).__name__}"
    )


def _checked_key(value: object, *, field: str) -> str:
    text = _required_text(value, f"{field}.key")
    normalized = text.lower().replace("-", "_")
    if any(token in normalized for token in FORBIDDEN_SUMMARY_KEY_TOKENS):
        raise EvidenceDraftContractError(f"{field} must not include raw or value-bearing keys")
    return text
