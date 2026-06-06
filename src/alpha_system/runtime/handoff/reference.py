"""Reference candidate handoff builder.

The handoff is a reference-only package for a future, separately authorized
Reference validation step. It does not run Reference validation, promote a
factor, create a strategy candidate, or make alpha/trading claims.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, cast

from alpha_system.governance.serialization import JsonValue
from alpha_system.governance.serialization import content_hash as governance_content_hash
from alpha_system.runtime.audit.no_lookahead import (
    NoLookaheadAuditOutcome,
    NoLookaheadAuditReason,
    NoLookaheadAuditResult,
)
from alpha_system.runtime.contracts.artifacts import RuntimeArtifactManifest
from alpha_system.runtime.contracts.manifest import (
    FeaturePackVersionRef,
    LabelPackVersionRef,
    StudyRunManifest,
)
from alpha_system.runtime.cost.model_version import CostModelVersion
from alpha_system.runtime.cost.report import CostProfileSummary, CostSensitivityReport
from alpha_system.runtime.decisions import (
    FORWARD_DECISION_STATES,
    RejectionReasonCode,
    RejectionReasonRecord,
    RuntimeDecision,
    RuntimeDecisionStage,
    RuntimeDecisionState,
    normalize_rejection_reason,
)
from alpha_system.runtime.evidence import EvidenceDraft

REFERENCE_CANDIDATE_HANDOFF_SCHEMA = "alpha_system.runtime.handoff.reference_candidate.v1"
REFERENCE_CANDIDATE_HANDOFF_ID_PREFIX = "rhandoff"
REFERENCE_VALIDATION_REQUIRED = "REFERENCE_VALIDATION_REQUIRED"
REQUIRED_COST_PROFILES = frozenset({"base", "double_cost"})

DEFAULT_LIMITATIONS: tuple[str, ...] = (
    "ReferenceCandidateHandoff is a handoff package only.",
    "ReferenceCandidateHandoff is not Reference validation.",
    "Fast-path screening is not Reference truth.",
    "No strategy has been validated by this handoff.",
    "This handoff makes no alpha, tradability, or profitability claim.",
)

type JsonObject = dict[str, JsonValue]


class ReferenceCandidateHandoffContractError(ValueError):
    """Raised when a ReferenceCandidateHandoff would hide an invalid state."""


@dataclass(frozen=True, slots=True, init=False)
class RuntimeObjectRef:
    """Stable reference to an upstream runtime object."""

    role: str
    source_type: str
    source_id: str
    source_hash: str
    status: str | None

    def __init__(
        self,
        *,
        role: str,
        source_type: str,
        source_id: str,
        source_hash: str,
        status: str | None = None,
    ) -> None:
        object.__setattr__(self, "role", _required_text(role, "role"))
        object.__setattr__(self, "source_type", _required_text(source_type, "source_type"))
        object.__setattr__(self, "source_id", _required_text(source_id, "source_id"))
        object.__setattr__(self, "source_hash", _required_text(source_hash, "source_hash"))
        object.__setattr__(
            self,
            "status",
            None if status is None else _required_text(status, "status"),
        )

    def to_dict(self) -> dict[str, str]:
        """Return a reference-only payload."""

        payload = {
            "role": self.role,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "source_hash": self.source_hash,
        }
        if self.status is not None:
            payload["status"] = self.status
        return payload


@dataclass(frozen=True, slots=True, init=False)
class VersionPackRef:
    """Reference-only feature or label pack version lineage."""

    pack_role: str
    pack_id: str
    content_hash: str
    lineage_ref: str
    availability_ref: str

    def __init__(
        self,
        *,
        pack_role: str,
        pack_id: str,
        content_hash: str,
        lineage_ref: str,
        availability_ref: str,
    ) -> None:
        object.__setattr__(self, "pack_role", _required_text(pack_role, "pack_role"))
        object.__setattr__(self, "pack_id", _required_text(pack_id, "pack_id"))
        object.__setattr__(self, "content_hash", _required_text(content_hash, "content_hash"))
        object.__setattr__(self, "lineage_ref", _required_text(lineage_ref, "lineage_ref"))
        object.__setattr__(
            self,
            "availability_ref",
            _required_text(availability_ref, "availability_ref"),
        )

    @classmethod
    def from_feature_pack(cls, value: FeaturePackVersionRef) -> VersionPackRef:
        """Build a version ref from an RT-P05 feature-pack manifest ref."""

        return cls(
            pack_role="feature_pack",
            pack_id=value.pack_id,
            content_hash=value.content_hash,
            lineage_ref=value.lineage_ref,
            availability_ref=value.available_ts_ref,
        )

    @classmethod
    def from_label_pack(cls, value: LabelPackVersionRef) -> VersionPackRef:
        """Build a version ref from an RT-P05 label-pack manifest ref."""

        return cls(
            pack_role="label_pack",
            pack_id=value.pack_id,
            content_hash=value.content_hash,
            lineage_ref=value.lineage_ref,
            availability_ref=value.label_available_ts_ref,
        )

    def to_dict(self) -> dict[str, str]:
        """Return the reference-only pack lineage."""

        return {
            "pack_role": self.pack_role,
            "pack_id": self.pack_id,
            "content_hash": self.content_hash,
            "lineage_ref": self.lineage_ref,
            "availability_ref": self.availability_ref,
        }


@dataclass(frozen=True, slots=True, init=False)
class VersionLineageSnapshot:
    """Reference-only dataset, feature, label, code, config, and cost lineage."""

    dataset_version_id: str
    dataset_version_hash: str
    dataset_lineage_ref: str
    dataset_admissibility_state: str
    feature_pack_versions: tuple[VersionPackRef, ...]
    label_pack_versions: tuple[VersionPackRef, ...]
    code_version: str
    code_content_hash: str
    config_version: str
    config_hash: str
    cost_model_version: str | None
    cost_model_hash: str | None

    def __init__(self, *, study_run_manifest: StudyRunManifest) -> None:
        if not isinstance(study_run_manifest, StudyRunManifest):
            raise ReferenceCandidateHandoffContractError(
                "study_run_manifest must be a StudyRunManifest"
            )
        feature_refs = tuple(
            VersionPackRef.from_feature_pack(ref)
            for ref in study_run_manifest.feature_pack_versions
        )
        label_refs = tuple(
            VersionPackRef.from_label_pack(ref) for ref in study_run_manifest.label_pack_versions
        )
        object.__setattr__(
            self,
            "dataset_version_id",
            _required_text(study_run_manifest.dataset_version_id, "dataset_version_id"),
        )
        object.__setattr__(
            self,
            "dataset_version_hash",
            _required_text(study_run_manifest.dataset_version_hash, "dataset_version_hash"),
        )
        object.__setattr__(
            self,
            "dataset_lineage_ref",
            _required_text(study_run_manifest.dataset_lineage_ref, "dataset_lineage_ref"),
        )
        object.__setattr__(
            self,
            "dataset_admissibility_state",
            _required_text(
                study_run_manifest.dataset_admissibility_state,
                "dataset_admissibility_state",
            ),
        )
        object.__setattr__(self, "feature_pack_versions", feature_refs)
        object.__setattr__(self, "label_pack_versions", label_refs)
        object.__setattr__(
            self,
            "code_version",
            _required_text(study_run_manifest.code_version, "code_version"),
        )
        object.__setattr__(
            self,
            "code_content_hash",
            _required_text(study_run_manifest.code_content_hash, "code_content_hash"),
        )
        object.__setattr__(
            self,
            "config_version",
            _required_text(study_run_manifest.config_version, "config_version"),
        )
        object.__setattr__(
            self,
            "config_hash",
            _required_text(study_run_manifest.config_hash, "config_hash"),
        )
        object.__setattr__(
            self,
            "cost_model_version",
            None
            if study_run_manifest.cost_model_version is None
            else _required_text(study_run_manifest.cost_model_version, "cost_model_version"),
        )
        object.__setattr__(
            self,
            "cost_model_hash",
            None
            if study_run_manifest.cost_model_hash is None
            else _required_text(study_run_manifest.cost_model_hash, "cost_model_hash"),
        )

    def to_dict(self) -> dict[str, object]:
        """Return lineage references without raw or heavy data."""

        return {
            "dataset_version_id": self.dataset_version_id,
            "dataset_version_hash": self.dataset_version_hash,
            "dataset_lineage_ref": self.dataset_lineage_ref,
            "dataset_admissibility_state": self.dataset_admissibility_state,
            "feature_pack_versions": [ref.to_dict() for ref in self.feature_pack_versions],
            "label_pack_versions": [ref.to_dict() for ref in self.label_pack_versions],
            "code_version": self.code_version,
            "code_content_hash": self.code_content_hash,
            "config_version": self.config_version,
            "config_hash": self.config_hash,
            "cost_model_version": self.cost_model_version,
            "cost_model_hash": self.cost_model_hash,
            "value_free": True,
        }


@dataclass(frozen=True, slots=True, init=False)
class CostProfileRef:
    """Scalar reference summary for one required cost-stress profile."""

    profile_name: str
    cost_multiplier: str
    slippage_multiplier: str
    zero_cost_diagnostic_only: bool
    promotion_basis_allowed: bool

    def __init__(self, *, profile_summary: CostProfileSummary) -> None:
        if not isinstance(profile_summary, CostProfileSummary):
            raise ReferenceCandidateHandoffContractError(
                "profile_summary must be CostProfileSummary"
            )
        object.__setattr__(
            self,
            "profile_name",
            _required_text(profile_summary.profile_name, "profile_name"),
        )
        object.__setattr__(
            self,
            "cost_multiplier",
            _decimal_text(profile_summary.cost_multiplier),
        )
        object.__setattr__(
            self,
            "slippage_multiplier",
            _decimal_text(profile_summary.slippage_multiplier),
        )
        object.__setattr__(
            self,
            "zero_cost_diagnostic_only",
            bool(profile_summary.zero_cost_diagnostic_only),
        )
        if profile_summary.promotion_basis_allowed is not False:
            raise ReferenceCandidateHandoffContractError(
                "cost profile cannot permit promotion basis"
            )
        object.__setattr__(self, "promotion_basis_allowed", False)

    def to_dict(self) -> dict[str, object]:
        """Return scalar profile metadata only."""

        return {
            "profile_name": self.profile_name,
            "cost_multiplier": self.cost_multiplier,
            "slippage_multiplier": self.slippage_multiplier,
            "zero_cost_diagnostic_only": self.zero_cost_diagnostic_only,
            "promotion_basis_allowed": False,
        }


@dataclass(frozen=True, slots=True, init=False)
class ReferenceRequirement:
    """Future gate declaration for a separately authorized Reference step."""

    next_required_gate: str
    future_authorization_required: bool
    reference_validation_performed: bool
    handoff_only: bool
    max_current_state: str

    def __init__(self) -> None:
        object.__setattr__(self, "next_required_gate", REFERENCE_VALIDATION_REQUIRED)
        object.__setattr__(self, "future_authorization_required", True)
        object.__setattr__(self, "reference_validation_performed", False)
        object.__setattr__(self, "handoff_only", True)
        object.__setattr__(
            self,
            "max_current_state",
            RuntimeDecisionState.REFERENCE_HANDOFF_READY.value,
        )

    def to_dict(self) -> dict[str, object]:
        """Return the future Reference gate requirements."""

        return {
            "next_required_gate": self.next_required_gate,
            "future_authorization_required": self.future_authorization_required,
            "reference_validation_performed": self.reference_validation_performed,
            "handoff_only": self.handoff_only,
            "max_current_state": self.max_current_state,
        }


@dataclass(frozen=True, slots=True, init=False)
class ReferenceCandidateHandoff:
    """Immutable handoff-only package for future Reference validation."""

    handoff_id: str
    run_id: str
    alpha_spec_id: str
    study_spec_id: str
    decision: RuntimeDecision
    evidence_draft_ref: RuntimeObjectRef
    study_run_manifest_ref: RuntimeObjectRef
    runtime_artifact_manifest_ref: RuntimeObjectRef
    no_lookahead_audit_ref: RuntimeObjectRef | None
    diagnostics_report_refs: tuple[RuntimeObjectRef, ...]
    version_lineage: VersionLineageSnapshot
    cost_model_version_ref: RuntimeObjectRef | None
    cost_profile_refs: tuple[CostProfileRef, ...]
    reference_requirements: ReferenceRequirement
    limitations: tuple[str, ...]
    handoff_hash: str
    strategy_not_validated: bool
    descriptive_only: bool
    not_reference_validation: bool
    not_promotion: bool
    not_alpha_validation: bool

    def __init__(
        self,
        *,
        run_id: str,
        alpha_spec_id: str,
        study_spec_id: str,
        decision: RuntimeDecision,
        evidence_draft_ref: RuntimeObjectRef,
        study_run_manifest_ref: RuntimeObjectRef,
        runtime_artifact_manifest_ref: RuntimeObjectRef,
        no_lookahead_audit_ref: RuntimeObjectRef | None,
        diagnostics_report_refs: Sequence[RuntimeObjectRef],
        version_lineage: VersionLineageSnapshot,
        cost_model_version_ref: RuntimeObjectRef | None,
        cost_profile_refs: Sequence[CostProfileRef],
        limitations: Sequence[str],
    ) -> None:
        if not isinstance(decision, RuntimeDecision):
            raise ReferenceCandidateHandoffContractError("decision must be a RuntimeDecision")
        if decision.state in FORWARD_DECISION_STATES and (
            decision.state is not RuntimeDecisionState.REFERENCE_HANDOFF_READY
        ):
            raise ReferenceCandidateHandoffContractError(
                "ReferenceCandidateHandoff forward state is capped at REFERENCE_HANDOFF_READY"
            )
        normalized_profiles = tuple(_coerce_cost_profile_ref(ref) for ref in cost_profile_refs)
        if decision.state is RuntimeDecisionState.REFERENCE_HANDOFF_READY:
            if cost_model_version_ref is None:
                raise ReferenceCandidateHandoffContractError(
                    "REFERENCE_HANDOFF_READY requires a CostModelVersion reference"
                )
            profile_names = {ref.profile_name for ref in normalized_profiles}
            missing = REQUIRED_COST_PROFILES - profile_names
            if missing:
                raise ReferenceCandidateHandoffContractError(
                    "REFERENCE_HANDOFF_READY missing cost profiles: " + ", ".join(sorted(missing))
                )
            if no_lookahead_audit_ref is None or (
                no_lookahead_audit_ref.status != NoLookaheadAuditOutcome.POINT_IN_TIME_SAFE.value
            ):
                raise ReferenceCandidateHandoffContractError(
                    "REFERENCE_HANDOFF_READY requires a passed NoLookaheadRuntimeAudit"
                )

        normalized_refs = tuple(_coerce_runtime_ref(ref) for ref in diagnostics_report_refs)
        normalized_limitations = _text_tuple(
            (*DEFAULT_LIMITATIONS, *tuple(limitations)),
            field="limitations",
        )
        requirement = ReferenceRequirement()
        payload = _handoff_payload(
            run_id=_required_text(run_id, "run_id"),
            alpha_spec_id=_required_text(alpha_spec_id, "alpha_spec_id"),
            study_spec_id=_required_text(study_spec_id, "study_spec_id"),
            decision=decision,
            evidence_draft_ref=_coerce_runtime_ref(evidence_draft_ref),
            study_run_manifest_ref=_coerce_runtime_ref(study_run_manifest_ref),
            runtime_artifact_manifest_ref=_coerce_runtime_ref(runtime_artifact_manifest_ref),
            no_lookahead_audit_ref=(
                None
                if no_lookahead_audit_ref is None
                else _coerce_runtime_ref(no_lookahead_audit_ref)
            ),
            diagnostics_report_refs=normalized_refs,
            version_lineage=version_lineage,
            cost_model_version_ref=(
                None
                if cost_model_version_ref is None
                else _coerce_runtime_ref(cost_model_version_ref)
            ),
            cost_profile_refs=normalized_profiles,
            reference_requirements=requirement,
            limitations=normalized_limitations,
        )
        digest = governance_content_hash(cast(JsonValue, payload))

        object.__setattr__(
            self, "handoff_id", f"{REFERENCE_CANDIDATE_HANDOFF_ID_PREFIX}_{digest[:24]}"
        )
        object.__setattr__(self, "run_id", _required_text(run_id, "run_id"))
        object.__setattr__(self, "alpha_spec_id", _required_text(alpha_spec_id, "alpha_spec_id"))
        object.__setattr__(self, "study_spec_id", _required_text(study_spec_id, "study_spec_id"))
        object.__setattr__(self, "decision", decision)
        object.__setattr__(self, "evidence_draft_ref", _coerce_runtime_ref(evidence_draft_ref))
        object.__setattr__(
            self,
            "study_run_manifest_ref",
            _coerce_runtime_ref(study_run_manifest_ref),
        )
        object.__setattr__(
            self,
            "runtime_artifact_manifest_ref",
            _coerce_runtime_ref(runtime_artifact_manifest_ref),
        )
        object.__setattr__(
            self,
            "no_lookahead_audit_ref",
            None if no_lookahead_audit_ref is None else _coerce_runtime_ref(no_lookahead_audit_ref),
        )
        object.__setattr__(self, "diagnostics_report_refs", normalized_refs)
        object.__setattr__(self, "version_lineage", version_lineage)
        object.__setattr__(
            self,
            "cost_model_version_ref",
            None if cost_model_version_ref is None else _coerce_runtime_ref(cost_model_version_ref),
        )
        object.__setattr__(self, "cost_profile_refs", normalized_profiles)
        object.__setattr__(self, "reference_requirements", requirement)
        object.__setattr__(self, "limitations", normalized_limitations)
        object.__setattr__(self, "handoff_hash", digest)
        object.__setattr__(self, "strategy_not_validated", True)
        object.__setattr__(self, "descriptive_only", True)
        object.__setattr__(self, "not_reference_validation", True)
        object.__setattr__(self, "not_promotion", True)
        object.__setattr__(self, "not_alpha_validation", True)

    @property
    def decision_state(self) -> RuntimeDecisionState:
        """Return the handoff decision state."""

        return self.decision.state

    @property
    def terminal_rejection_reasons(self) -> tuple[RejectionReasonRecord, ...]:
        """Return visible terminal reasons when the handoff cannot proceed."""

        return self.decision.reasons

    def to_dict(self) -> JsonObject:
        """Return the handoff payload without raw or heavy data."""

        payload = _handoff_payload(
            run_id=self.run_id,
            alpha_spec_id=self.alpha_spec_id,
            study_spec_id=self.study_spec_id,
            decision=self.decision,
            evidence_draft_ref=self.evidence_draft_ref,
            study_run_manifest_ref=self.study_run_manifest_ref,
            runtime_artifact_manifest_ref=self.runtime_artifact_manifest_ref,
            no_lookahead_audit_ref=self.no_lookahead_audit_ref,
            diagnostics_report_refs=self.diagnostics_report_refs,
            version_lineage=self.version_lineage,
            cost_model_version_ref=self.cost_model_version_ref,
            cost_profile_refs=self.cost_profile_refs,
            reference_requirements=self.reference_requirements,
            limitations=self.limitations,
        )
        payload["handoff_id"] = self.handoff_id
        payload["handoff_hash"] = self.handoff_hash
        return cast(JsonObject, payload)


def build_reference_candidate_handoff(
    *,
    alpha_spec_id: str,
    study_spec_id: str,
    evidence_draft: EvidenceDraft,
    study_run_manifest: StudyRunManifest,
    runtime_artifact_manifest: RuntimeArtifactManifest,
    cost_sensitivity_report: CostSensitivityReport | None,
    no_lookahead_audit_result: NoLookaheadAuditResult | Mapping[str, Any] | None,
    factor_diagnostics_report: object | None = None,
    label_diagnostics_report: object | None = None,
    session_split_report: object | None = None,
    regime_split_report: object | None = None,
    cross_market_diagnostics_report: object | None = None,
    signal_probe_report: object | None = None,
    bounded_grid_record: object | None = None,
    diagnostics_reports: Sequence[object] = (),
    decision: RuntimeDecision | Mapping[str, Any] | None = None,
    rejection_reasons: Sequence[RejectionReasonRecord | Mapping[str, Any]] = (),
    limitations: Sequence[str] = (),
) -> ReferenceCandidateHandoff:
    """Build a reference-only handoff package or a visible terminal outcome."""

    _require_evidence_draft(evidence_draft)
    _require_manifest(study_run_manifest)
    _require_artifact_manifest(runtime_artifact_manifest)
    runtime_decision = _resolved_decision(
        evidence_draft=evidence_draft,
        decision=decision,
        rejection_reasons=rejection_reasons,
        cost_sensitivity_report=cost_sensitivity_report,
        no_lookahead_audit_result=no_lookahead_audit_result,
    )

    audit = _coerce_audit_result(no_lookahead_audit_result)
    cost_profiles = (
        _cost_profile_refs(cost_sensitivity_report)
        if isinstance(cost_sensitivity_report, CostSensitivityReport)
        else ()
    )
    cost_model_ref = (
        _cost_model_version_ref(cost_sensitivity_report.cost_model_version)
        if isinstance(cost_sensitivity_report, CostSensitivityReport)
        else None
    )
    audit_ref = None if audit is None else _audit_ref(audit)
    report_refs = _report_refs(
        evidence_draft=evidence_draft,
        reports=(
            factor_diagnostics_report,
            label_diagnostics_report,
            session_split_report,
            regime_split_report,
            cross_market_diagnostics_report,
            cost_sensitivity_report,
            signal_probe_report,
            bounded_grid_record,
            *tuple(diagnostics_reports),
        ),
        audit_ref=audit_ref,
    )

    return ReferenceCandidateHandoff(
        run_id=study_run_manifest.run_id,
        alpha_spec_id=alpha_spec_id,
        study_spec_id=study_spec_id,
        decision=runtime_decision,
        evidence_draft_ref=_evidence_draft_ref(evidence_draft),
        study_run_manifest_ref=_study_run_manifest_ref(study_run_manifest),
        runtime_artifact_manifest_ref=_runtime_artifact_manifest_ref(runtime_artifact_manifest),
        no_lookahead_audit_ref=audit_ref,
        diagnostics_report_refs=report_refs,
        version_lineage=VersionLineageSnapshot(study_run_manifest=study_run_manifest),
        cost_model_version_ref=cost_model_ref,
        cost_profile_refs=cost_profiles,
        limitations=limitations,
    )


def _resolved_decision(
    *,
    evidence_draft: EvidenceDraft,
    decision: RuntimeDecision | Mapping[str, Any] | None,
    rejection_reasons: Sequence[RejectionReasonRecord | Mapping[str, Any]],
    cost_sensitivity_report: CostSensitivityReport | None,
    no_lookahead_audit_result: NoLookaheadAuditResult | Mapping[str, Any] | None,
) -> RuntimeDecision:
    if decision is not None:
        normalized = (
            decision
            if isinstance(decision, RuntimeDecision)
            else RuntimeDecision.from_dict(decision)
        )
        if normalized.state in FORWARD_DECISION_STATES:
            return _ready_or_blocked_decision(
                evidence_draft=evidence_draft,
                source_state=normalized.state.value,
                cost_sensitivity_report=cost_sensitivity_report,
                no_lookahead_audit_result=no_lookahead_audit_result,
            )
        return normalized
    if rejection_reasons:
        return RuntimeDecision.from_reasons(
            tuple(_coerce_reason(reason) for reason in rejection_reasons)
        )
    if evidence_draft.decision.state not in FORWARD_DECISION_STATES:
        return evidence_draft.decision
    return _ready_or_blocked_decision(
        evidence_draft=evidence_draft,
        source_state=evidence_draft.decision.state.value,
        cost_sensitivity_report=cost_sensitivity_report,
        no_lookahead_audit_result=no_lookahead_audit_result,
    )


def _ready_or_blocked_decision(
    *,
    evidence_draft: EvidenceDraft,
    source_state: str,
    cost_sensitivity_report: CostSensitivityReport | None,
    no_lookahead_audit_result: NoLookaheadAuditResult | Mapping[str, Any] | None,
) -> RuntimeDecision:
    if evidence_draft.decision.state is not RuntimeDecisionState.EVIDENCE_DRAFT_READY:
        return RuntimeDecision(
            state=RuntimeDecisionState.BLOCKED,
            reasons=(
                _blocked_reason(
                    message="Reference handoff requires an upstream EVIDENCE_DRAFT_READY decision.",
                    stage=RuntimeDecisionStage.RUNTIME_STOP,
                    source_code="evidence_draft_not_ready_for_reference_handoff",
                    source_id=evidence_draft.draft_id,
                ),
            ),
            source_state=source_state,
        )

    precondition_reasons = (
        *_cost_precondition_reasons(cost_sensitivity_report),
        *_audit_precondition_reasons(no_lookahead_audit_result),
    )
    if precondition_reasons:
        return RuntimeDecision(
            state=RuntimeDecisionState.BLOCKED,
            reasons=precondition_reasons,
            source_state=source_state,
        )
    return RuntimeDecision(
        state=RuntimeDecisionState.REFERENCE_HANDOFF_READY,
        source_state=source_state,
    )


def _cost_precondition_reasons(
    report: CostSensitivityReport | None,
) -> tuple[RejectionReasonRecord, ...]:
    if report is None:
        return (
            _blocked_reason(
                message="Reference handoff requires a CostSensitivityReport.",
                stage=RuntimeDecisionStage.COST_STRESS,
                source_code="missing_cost_sensitivity_report",
            ),
        )
    if not isinstance(report, CostSensitivityReport):
        return (
            _blocked_reason(
                message="Reference handoff cost stress must be a CostSensitivityReport.",
                stage=RuntimeDecisionStage.COST_STRESS,
                source_code="invalid_cost_sensitivity_report_type",
            ),
        )
    if not isinstance(report.cost_model_version, CostModelVersion):
        return (
            _blocked_reason(
                message="Reference handoff requires a CostModelVersion.",
                stage=RuntimeDecisionStage.COST_STRESS,
                source_code="missing_cost_model_version",
            ),
        )
    profile_names = {summary.profile_name for summary in report.profile_summaries}
    missing = REQUIRED_COST_PROFILES - profile_names
    if missing:
        return (
            _blocked_reason(
                message="Reference handoff requires base and double_cost cost profiles.",
                stage=RuntimeDecisionStage.COST_STRESS,
                source_code="missing_required_cost_profiles",
                source_id=",".join(sorted(missing)),
            ),
        )
    if report.slippage_labeled_proxy is not True:
        return (
            _blocked_reason(
                message="Reference handoff requires slippage to be labeled as a proxy.",
                stage=RuntimeDecisionStage.COST_STRESS,
                source_code="slippage_not_labeled_proxy",
            ),
        )
    return ()


def _audit_precondition_reasons(
    result: NoLookaheadAuditResult | Mapping[str, Any] | None,
) -> tuple[RejectionReasonRecord, ...]:
    audit = _coerce_audit_result(result)
    if audit is None:
        return (
            _blocked_reason(
                message="Reference handoff requires a passed NoLookaheadRuntimeAudit result.",
                stage=RuntimeDecisionStage.NO_LOOKAHEAD_AUDIT,
                source_code="missing_no_lookahead_audit_result",
            ),
        )
    if audit.accepted:
        return ()
    if audit.reasons:
        return tuple(
            normalize_rejection_reason(
                reason,
                stage=RuntimeDecisionStage.NO_LOOKAHEAD_AUDIT,
                decision_state=RuntimeDecisionState.BLOCKED,
            )
            for reason in audit.reasons
        )
    return (
        _blocked_reason(
            message="Reference handoff requires a passed NoLookaheadRuntimeAudit result.",
            stage=RuntimeDecisionStage.NO_LOOKAHEAD_AUDIT,
            source_code="no_lookahead_audit_not_accepted",
        ),
    )


def _cost_profile_refs(report: CostSensitivityReport) -> tuple[CostProfileRef, ...]:
    profile_by_name = {summary.profile_name: summary for summary in report.profile_summaries}
    return tuple(
        CostProfileRef(profile_summary=profile_by_name[name])
        for name in sorted(REQUIRED_COST_PROFILES)
        if name in profile_by_name
    )


def _cost_model_version_ref(value: CostModelVersion) -> RuntimeObjectRef:
    return RuntimeObjectRef(
        role="cost_model_version",
        source_type=type(value).__name__,
        source_id=value.cost_model_version_id,
        source_hash=value.content_hash,
        status="slippage_proxy_labeled",
    )


def _evidence_draft_ref(value: EvidenceDraft) -> RuntimeObjectRef:
    return RuntimeObjectRef(
        role="evidence_draft",
        source_type=type(value).__name__,
        source_id=value.draft_id,
        source_hash=value.draft_hash,
        status=value.decision.state.value,
    )


def _study_run_manifest_ref(value: StudyRunManifest) -> RuntimeObjectRef:
    return RuntimeObjectRef(
        role="study_run_manifest",
        source_type=type(value).__name__,
        source_id=value.manifest_id,
        source_hash=value.manifest_hash,
        status=value.dataset_admissibility_state,
    )


def _runtime_artifact_manifest_ref(value: RuntimeArtifactManifest) -> RuntimeObjectRef:
    return RuntimeObjectRef(
        role="runtime_artifact_manifest",
        source_type=type(value).__name__,
        source_id=value.manifest_id,
        source_hash=value.manifest_hash,
        status=f"entry_count={len(value.entries)}",
    )


def _audit_ref(value: NoLookaheadAuditResult) -> RuntimeObjectRef:
    return RuntimeObjectRef(
        role="no_lookahead_runtime_audit",
        source_type=type(value).__name__,
        source_id=f"no_lookahead_{value.outcome.value.lower()}",
        source_hash=governance_content_hash(cast(JsonValue, value.to_dict())),
        status=value.outcome.value,
    )


def _report_refs(
    *,
    evidence_draft: EvidenceDraft,
    reports: Sequence[object | None],
    audit_ref: RuntimeObjectRef | None,
) -> tuple[RuntimeObjectRef, ...]:
    refs: list[RuntimeObjectRef] = []
    for report in reports:
        if report is None:
            continue
        refs.append(_object_ref(report))
    if not refs:
        refs.extend(_section_refs(evidence_draft))
    if audit_ref is not None:
        refs.append(audit_ref)
    return _dedupe_refs(refs)


def _section_refs(evidence_draft: EvidenceDraft) -> tuple[RuntimeObjectRef, ...]:
    refs: list[RuntimeObjectRef] = []
    for section in evidence_draft.sections:
        refs.append(
            RuntimeObjectRef(
                role=section.section_name,
                source_type=section.source_type,
                source_id=section.source_id,
                source_hash=section.source_hash,
                status=section.status,
            )
        )
    return tuple(refs)


def _object_ref(value: object) -> RuntimeObjectRef:
    to_ref = getattr(value, "to_ref", None)
    if callable(to_ref):
        ref = to_ref()
        payload = ref.to_dict() if hasattr(ref, "to_dict") else {}
        if isinstance(payload, Mapping):
            source_id = (
                payload.get("report_id") or payload.get("record_id") or payload.get("source_id")
            )
            source_hash = (
                payload.get("report_hash")
                or payload.get("record_hash")
                or payload.get("source_hash")
            )
            role = payload.get("report_kind") or payload.get("role") or type(value).__name__
            if source_id is not None and source_hash is not None:
                return RuntimeObjectRef(
                    role=str(role),
                    source_type=type(value).__name__,
                    source_id=str(source_id),
                    source_hash=str(source_hash),
                    status=_optional_state_text(getattr(value, "status", None)),
                )
    for id_attr, hash_attr, role in (
        ("report_id", "report_hash", "report"),
        ("record_id", "record_hash", "record"),
        ("record_id", "content_hash", "record"),
        ("draft_id", "draft_hash", "evidence_draft"),
    ):
        source_id = getattr(value, id_attr, None)
        source_hash = getattr(value, hash_attr, None)
        if source_id is not None and source_hash is not None:
            return RuntimeObjectRef(
                role=str(getattr(value, "report_kind", role)),
                source_type=type(value).__name__,
                source_id=str(source_id),
                source_hash=str(source_hash),
                status=_optional_state_text(getattr(value, "status", None)),
            )
    raise ReferenceCandidateHandoffContractError(
        f"cannot build a reference for {type(value).__name__}"
    )


def _dedupe_refs(refs: Sequence[RuntimeObjectRef]) -> tuple[RuntimeObjectRef, ...]:
    ordered: list[RuntimeObjectRef] = []
    seen: set[tuple[str, str, str]] = set()
    for ref in refs:
        key = (ref.role, ref.source_id, ref.source_hash)
        if key in seen:
            continue
        ordered.append(ref)
        seen.add(key)
    return tuple(ordered)


def _coerce_audit_result(
    value: NoLookaheadAuditResult | Mapping[str, Any] | None,
) -> NoLookaheadAuditResult | None:
    if value is None:
        return None
    if isinstance(value, NoLookaheadAuditResult):
        return value
    if isinstance(value, Mapping):
        outcome = value.get("outcome")
        reasons = value.get("rejection_reason_records", ())
        if outcome == NoLookaheadAuditOutcome.POINT_IN_TIME_SAFE.value and not reasons:
            return NoLookaheadAuditResult(outcome=NoLookaheadAuditOutcome.POINT_IN_TIME_SAFE)
        if isinstance(reasons, Sequence) and not isinstance(reasons, str):
            return NoLookaheadAuditResult(
                outcome=NoLookaheadAuditOutcome.REJECTED,
                reasons=tuple(_audit_reason_from_mapping(reason) for reason in reasons),
            )
    raise ReferenceCandidateHandoffContractError(
        "no_lookahead_audit_result must be NoLookaheadAuditResult or its stable mapping"
    )


def _audit_reason_from_mapping(value: object) -> NoLookaheadAuditReason:
    if not isinstance(value, Mapping):
        raise ReferenceCandidateHandoffContractError("audit rejection reasons must be mappings")
    return NoLookaheadAuditReason(
        code=str(value.get("code")),
        category=str(value.get("category")),
        message=str(value.get("message")),
        field=str(value.get("field")),
        expected=str(value.get("expected")),
        actual=str(value.get("actual")),
        decision_state=str(value.get("decision_state", "INPUTS_BLOCKED")),
    )


def _handoff_payload(
    *,
    run_id: str,
    alpha_spec_id: str,
    study_spec_id: str,
    decision: RuntimeDecision,
    evidence_draft_ref: RuntimeObjectRef,
    study_run_manifest_ref: RuntimeObjectRef,
    runtime_artifact_manifest_ref: RuntimeObjectRef,
    no_lookahead_audit_ref: RuntimeObjectRef | None,
    diagnostics_report_refs: Sequence[RuntimeObjectRef],
    version_lineage: VersionLineageSnapshot,
    cost_model_version_ref: RuntimeObjectRef | None,
    cost_profile_refs: Sequence[CostProfileRef],
    reference_requirements: ReferenceRequirement,
    limitations: Sequence[str],
) -> JsonObject:
    payload: dict[str, object] = {
        "schema": REFERENCE_CANDIDATE_HANDOFF_SCHEMA,
        "run_id": run_id,
        "alpha_spec_id": alpha_spec_id,
        "study_spec_id": study_spec_id,
        "decision": decision.to_dict(),
        "evidence_draft_ref": evidence_draft_ref.to_dict(),
        "study_run_manifest_ref": study_run_manifest_ref.to_dict(),
        "runtime_artifact_manifest_ref": runtime_artifact_manifest_ref.to_dict(),
        "no_lookahead_audit_ref": None
        if no_lookahead_audit_ref is None
        else no_lookahead_audit_ref.to_dict(),
        "diagnostics_report_refs": [ref.to_dict() for ref in diagnostics_report_refs],
        "version_lineage": version_lineage.to_dict(),
        "cost_stress": None
        if cost_model_version_ref is None
        else {
            "cost_model_version_ref": cost_model_version_ref.to_dict(),
            "required_profiles": sorted(REQUIRED_COST_PROFILES),
            "profile_refs": [ref.to_dict() for ref in cost_profile_refs],
            "slippage_labeled_proxy": True,
            "promotion_basis_allowed": False,
        },
        "reference_requirements": reference_requirements.to_dict(),
        "limitations": list(limitations),
        "strategy_not_validated": True,
        "descriptive_only": True,
        "not_reference_validation": True,
        "not_promotion": True,
        "not_alpha_validation": True,
        "promotion_basis_allowed": False,
        "raw_or_heavy_data_embedded": False,
    }
    return cast(JsonObject, payload)


def _blocked_reason(
    *,
    message: str,
    stage: RuntimeDecisionStage,
    source_code: str,
    source_id: str | None = None,
) -> RejectionReasonRecord:
    return RejectionReasonRecord(
        code=RejectionReasonCode.BLOCKED_BY_POLICY,
        message=message,
        decision_state=RuntimeDecisionState.BLOCKED,
        stage=stage,
        source_code=source_code,
        source_id=source_id,
    )


def _coerce_reason(value: RejectionReasonRecord | Mapping[str, Any]) -> RejectionReasonRecord:
    if isinstance(value, RejectionReasonRecord):
        return value
    if isinstance(value, Mapping):
        return RejectionReasonRecord.from_dict(value)
    raise ReferenceCandidateHandoffContractError(
        f"rejection reason must be RejectionReasonRecord, got {type(value).__name__}"
    )


def _coerce_runtime_ref(value: RuntimeObjectRef) -> RuntimeObjectRef:
    if not isinstance(value, RuntimeObjectRef):
        raise ReferenceCandidateHandoffContractError("runtime object refs must be RuntimeObjectRef")
    return value


def _coerce_cost_profile_ref(value: CostProfileRef) -> CostProfileRef:
    if not isinstance(value, CostProfileRef):
        raise ReferenceCandidateHandoffContractError("cost profile refs must be CostProfileRef")
    return value


def _require_evidence_draft(value: EvidenceDraft) -> None:
    if not isinstance(value, EvidenceDraft):
        raise ReferenceCandidateHandoffContractError("evidence_draft must be EvidenceDraft")


def _require_manifest(value: StudyRunManifest) -> None:
    if not isinstance(value, StudyRunManifest):
        raise ReferenceCandidateHandoffContractError("study_run_manifest must be StudyRunManifest")


def _require_artifact_manifest(value: RuntimeArtifactManifest) -> None:
    if not isinstance(value, RuntimeArtifactManifest):
        raise ReferenceCandidateHandoffContractError(
            "runtime_artifact_manifest must be RuntimeArtifactManifest"
        )


def _text_tuple(values: Sequence[str], *, field: str) -> tuple[str, ...]:
    if isinstance(values, str):
        raise ReferenceCandidateHandoffContractError(f"{field} must be a finite sequence")
    normalized = tuple(_required_text(value, f"{field}[]") for value in values)
    if not normalized:
        raise ReferenceCandidateHandoffContractError(f"{field} must not be empty")
    return normalized


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReferenceCandidateHandoffContractError(f"{field} is required")
    return value.strip()


def _optional_state_text(value: object) -> str | None:
    if value is None:
        return None
    if hasattr(value, "value"):
        return str(getattr(value, "value"))
    return str(value)


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")


__all__ = [
    "REFERENCE_CANDIDATE_HANDOFF_SCHEMA",
    "REFERENCE_VALIDATION_REQUIRED",
    "ReferenceCandidateHandoff",
    "ReferenceCandidateHandoffContractError",
    "ReferenceRequirement",
    "RuntimeObjectRef",
    "VersionLineageSnapshot",
    "build_reference_candidate_handoff",
]
