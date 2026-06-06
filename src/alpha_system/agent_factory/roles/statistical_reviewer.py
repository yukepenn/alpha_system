"""Statistical Reviewer role contract.

This module declares the contracts-only Statistical Reviewer role. It consumes
the existing governance reviewer verdict primitive and value-free runtime
evidence summary refs, but does not recompute statistics, run diagnostics,
instantiate an agent, promote work, or make alpha claims.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from alpha_system.agent_factory.permissions.matrix import permission_for
from alpha_system.agent_factory.roles import registry
from alpha_system.agent_factory.roles.contracts import AgentRole
from alpha_system.agent_factory.tools.results import AgentToolResult, AgentToolStatus
from alpha_system.governance.reviewer_verdict import (
    ReviewerVerdict,
    ReviewerVerdictOutcome,
)

ROLE_ID = "statistical_reviewer"
MISSING_EVIDENCE_INCONCLUSIVE_GATE = "diagnostics_runner_restore_evidence_summary_refs"
NON_PASS_LOOKAHEAD_BLOCKED_GATE = "no_lookahead_auditor_restore_passed_audit"
MISSING_BOUND_SPEC_BLOCKED_GATE = "research_director_restore_bound_specs"
NEXT_REQUIRED_GATE = "librarian_record_independent_review_verdict"
SEPARATION_OF_DUTIES_GATE = "separation_of_duties_review_reassignment"

STATISTICAL_REVIEW_VERDICTS: tuple[str, ...] = (
    "PASS",
    "REJECT",
    "WATCH",
    "INCONCLUSIVE",
)
VERDICT_STATUS_BY_OUTCOME: Mapping[str, AgentToolStatus] = MappingProxyType(
    {
        "PASS": AgentToolStatus.OK,
        "REJECT": AgentToolStatus.REJECTED,
        "WATCH": AgentToolStatus.WARN,
        "INCONCLUSIVE": AgentToolStatus.INCONCLUSIVE,
    }
)
DEFAULT_LIMITATIONS: tuple[str, ...] = (
    "contract_only_no_agent_instantiated",
    "review_verdict_is_evidence_opinion_not_promotion",
    "dry_run_or_seed_pack_evidence_is_not_alpha",
    "no_alpha_profitability_tradability_or_live_claim",
)


def _matrix_callable_tools() -> tuple[str, ...]:
    return permission_for(ROLE_ID).tool.allowed_tool_ids


CALLABLE_TOOL_IDS: tuple[str, ...] = _matrix_callable_tools()
CONSUMED_PRIMITIVES: tuple[object, ...] = (
    ReviewerVerdict,
    ReviewerVerdictOutcome,
)

STATISTICAL_REVIEWER_ROLE = AgentRole(
    role_id=ROLE_ID,
    name="Statistical Reviewer",
    purpose=(
        "Issue an independent PASS REJECT WATCH or INCONCLUSIVE evidence review verdict; "
        "never implement diagnostics or promote work."
    ),
    readable_inputs=(
        "RuntimeRunSummary and RuntimeToolResult evidence summary refs only",
        "diagnostics_summary and cost_summary value-free fields",
        "upstream no-lookahead audit summary ref and PASS or BLOCKED status",
        "bound alpha_spec_id study_spec_id dataset_version_id",
        "feature_pack_refs label_pack_refs and runtime_run_id refs",
        "AgentToolResult summary refs without raw values or heavy payloads",
    ),
    callable_tools=CALLABLE_TOOL_IDS,
    producible_outputs=(
        "AgentToolResult with PASS as OK REJECT as REJECTED WATCH as WARN",
        "AgentToolResult with INCONCLUSIVE as INCONCLUSIVE",
        "AgentToolResult fields rejection_reasons blocking_findings next_required_gate",
        "AgentToolResult fields artifacts limitations and bound ids",
        "ReviewerVerdict-shaped value-free record for evidence opinion",
        "BLOCKED or INCONCLUSIVE result when evidence audit or bound specs are insufficient",
    ),
    allowed_decisions=(
        "emit_PASS_REJECT_WATCH_or_INCONCLUSIVE_on_bound_lookahead_clean_runtime_evidence",
        "select_librarian_memory_or_human_judgment_next_gate",
        "emit_fail_closed_for_missing_evidence_non_pass_audit_or_missing_specs",
    ),
    forbidden_decisions=(
        "promote_factor_candidate_or_strategy",
        "implement_or_alter_feature_label_alpha_or_study_specs",
        "run_retry_or_reimplement_diagnostics",
        "review_own_implementation_or_own_diagnostics",
        "act_as_feature_label_engineer_or_diagnostics_runner_for_reviewed_evidence",
        "recompute_statistics_from_raw_values_or_bypass_runtime_tool_surface",
        "read_raw_provider_data_or_runtime_values",
        "make_external_provider_calls",
        "write_feature_label_dataset_or_promotion_registry",
        "touch_capital_risk_live_paper_broker_order_or_deployment_decisions",
        "claim_alpha_profitability_tradability_strategy_or_production_readiness",
        "treat_EvidenceDraft_as_candidate_or_ReferenceCandidateHandoff_as_validation",
    ),
    handoff_format=(
        "request_id",
        "role",
        "alpha_spec_id study_spec_id dataset_version_id",
        "feature_pack_refs label_pack_refs runtime_run_id",
        "evidence_summary_ref",
        "no_lookahead_audit_summary_ref",
        "status",
        "rejection_reasons",
        "blocking_findings",
        "next_required_gate",
        "artifacts",
        "limitations",
    ),
    reviewer_independence=(
        "reviewer_role_id != feature_engineer_label_engineer_or_diagnostics_runner_role_id",
        "reviewer_agent_must_not_review_own_work_or_own_diagnostics",
        "verdict_requires_upstream_no_lookahead_audit_PASS_before_forward_lifecycle_advance",
        "WATCH_or_forward_lifecycle_advance_requires_independent_verdict_and_is_not_promotion",
    ),
    failure_modes=(
        "INCONCLUSIVE when runtime evidence summary refs are insufficient never silent PASS",
        "BLOCKED when no-lookahead audit status is not PASS",
        "BLOCKED when bound AlphaSpec or StudySpec is missing",
        "BLOCKED when reviewer independence cannot be established",
        "permission_denied when review tool grant or matrix entry is absent",
    ),
)


def _assert_callable_tools_match_matrix(role: AgentRole) -> None:
    if role.callable_tools != _matrix_callable_tools():
        raise RuntimeError("statistical_reviewer callable_tools must match permission matrix")


_assert_callable_tools_match_matrix(STATISTICAL_REVIEWER_ROLE)


def statistical_review_verdict_result(
    request_id: str,
    verdict: str,
    *,
    evidence_summary_ref: str,
    no_lookahead_audit_summary_ref: str,
    no_lookahead_status: str,
    alpha_spec_id: str,
    study_spec_id: str,
    dataset_version_id: str,
    feature_pack_refs: tuple[str, ...] = (),
    label_pack_refs: tuple[str, ...] = (),
    runtime_run_id: str | None = None,
    diagnostics_summary: str | None = None,
    cost_summary: str | None = None,
    rejection_reasons: tuple[str, ...] = (),
    blocking_findings: tuple[str, ...] = (),
    next_required_gate: str = NEXT_REQUIRED_GATE,
    artifacts: tuple[str, ...] = (),
    limitations: tuple[str, ...] = DEFAULT_LIMITATIONS,
) -> AgentToolResult:
    """Build a value-free review result for one statistical review verdict."""

    outcome = _validate_verdict(verdict)
    request = _validate_required_text("request_id", request_id)
    evidence_ref = _validate_required_text("evidence_summary_ref", evidence_summary_ref)
    audit_ref = _validate_required_text(
        "no_lookahead_audit_summary_ref",
        no_lookahead_audit_summary_ref,
    )
    if _validate_required_text("no_lookahead_status", no_lookahead_status) != "PASS":
        raise ValueError("no_lookahead_status must be PASS for a statistical review verdict")
    alpha_id = _validate_required_text("alpha_spec_id", alpha_spec_id)
    study_id = _validate_required_text("study_spec_id", study_spec_id)
    dataset_id = _validate_required_text("dataset_version_id", dataset_version_id)
    features = _validate_text_tuple("feature_pack_refs", feature_pack_refs)
    labels = _validate_text_tuple("label_pack_refs", label_pack_refs)
    run_id = _validate_optional_text("runtime_run_id", runtime_run_id)
    cost = _validate_optional_text("cost_summary", cost_summary)
    reasons = _validate_text_tuple("rejection_reasons", rejection_reasons)
    findings = _validate_text_tuple("blocking_findings", blocking_findings)
    next_gate = _validate_required_text("next_required_gate", next_required_gate)
    artifact_refs = _append_unique_refs(
        _validate_text_tuple("artifacts", artifacts),
        (
            f"evidence_summary_ref:{evidence_ref}",
            f"no_lookahead_audit_summary_ref:{audit_ref}",
        ),
    )
    result_limitations = _validate_text_tuple(
        "limitations",
        limitations,
        require_non_empty=True,
    )
    if outcome == "REJECT" and not reasons and not findings:
        raise ValueError("REJECT verdict requires rejection reasons or blocking findings")

    summary = diagnostics_summary
    if summary is None:
        summary = (
            f"statistical_review_verdict:{outcome}; evidence_summary_ref:{evidence_ref}; "
            f"no_lookahead_audit_summary_ref:{audit_ref}"
        )

    return AgentToolResult(
        status=VERDICT_STATUS_BY_OUTCOME[outcome],
        role=ROLE_ID,
        request_id=request,
        alpha_spec_id=alpha_id,
        study_spec_id=study_id,
        dataset_version_id=dataset_id,
        feature_pack_refs=features,
        label_pack_refs=labels,
        runtime_run_id=run_id,
        diagnostics_summary=summary,
        cost_summary=cost,
        rejection_reasons=reasons,
        blocking_findings=findings,
        next_required_gate=next_gate,
        artifacts=artifact_refs,
        limitations=result_limitations,
    )


def inconclusive_missing_evidence_result(
    request_id: str,
    missing_refs: tuple[str, ...],
    *,
    alpha_spec_id: str | None = None,
    study_spec_id: str | None = None,
    dataset_version_id: str | None = None,
    feature_pack_refs: tuple[str, ...] = (),
    label_pack_refs: tuple[str, ...] = (),
    runtime_run_id: str | None = None,
    no_lookahead_audit_summary_ref: str | None = None,
) -> AgentToolResult:
    """Return the fail-closed result for insufficient evidence summary refs."""

    missing = _validate_text_tuple("missing_refs", missing_refs, require_non_empty=True)
    artifacts = ()
    if no_lookahead_audit_summary_ref is not None:
        artifacts = (
            "no_lookahead_audit_summary_ref:"
            f"{_validate_required_text('no_lookahead_audit_summary_ref', no_lookahead_audit_summary_ref)}",
        )
    return AgentToolResult(
        status=AgentToolStatus.INCONCLUSIVE,
        role=ROLE_ID,
        request_id=_validate_required_text("request_id", request_id),
        alpha_spec_id=_validate_optional_text("alpha_spec_id", alpha_spec_id),
        study_spec_id=_validate_optional_text("study_spec_id", study_spec_id),
        dataset_version_id=_validate_optional_text("dataset_version_id", dataset_version_id),
        feature_pack_refs=_validate_text_tuple("feature_pack_refs", feature_pack_refs),
        label_pack_refs=_validate_text_tuple("label_pack_refs", label_pack_refs),
        runtime_run_id=_validate_optional_text("runtime_run_id", runtime_run_id),
        diagnostics_summary="Evidence summary refs are insufficient; fail closed.",
        cost_summary=None,
        rejection_reasons=("missing_runtime_evidence_summary_refs",),
        blocking_findings=tuple(f"missing_evidence_summary_ref:{ref}" for ref in missing),
        next_required_gate=MISSING_EVIDENCE_INCONCLUSIVE_GATE,
        artifacts=artifacts,
        limitations=DEFAULT_LIMITATIONS,
    )


def blocked_non_pass_no_lookahead_result(
    request_id: str,
    no_lookahead_status: str,
    *,
    no_lookahead_audit_summary_ref: str,
    alpha_spec_id: str | None = None,
    study_spec_id: str | None = None,
    dataset_version_id: str | None = None,
    feature_pack_refs: tuple[str, ...] = (),
    label_pack_refs: tuple[str, ...] = (),
    runtime_run_id: str | None = None,
) -> AgentToolResult:
    """Return the fail-closed result when the upstream audit has not passed."""

    status = _validate_required_text("no_lookahead_status", no_lookahead_status)
    if status == "PASS":
        raise ValueError("no_lookahead_status must not be PASS for this blocked result")
    audit_ref = _validate_required_text(
        "no_lookahead_audit_summary_ref",
        no_lookahead_audit_summary_ref,
    )
    return AgentToolResult(
        status=AgentToolStatus.BLOCKED,
        role=ROLE_ID,
        request_id=_validate_required_text("request_id", request_id),
        alpha_spec_id=_validate_optional_text("alpha_spec_id", alpha_spec_id),
        study_spec_id=_validate_optional_text("study_spec_id", study_spec_id),
        dataset_version_id=_validate_optional_text("dataset_version_id", dataset_version_id),
        feature_pack_refs=_validate_text_tuple("feature_pack_refs", feature_pack_refs),
        label_pack_refs=_validate_text_tuple("label_pack_refs", label_pack_refs),
        runtime_run_id=_validate_optional_text("runtime_run_id", runtime_run_id),
        diagnostics_summary="No-lookahead audit is not PASS; fail closed before review.",
        cost_summary=None,
        rejection_reasons=("no_lookahead_audit_not_pass",),
        blocking_findings=(f"no_lookahead_audit_status:{status}",),
        next_required_gate=NON_PASS_LOOKAHEAD_BLOCKED_GATE,
        artifacts=(f"no_lookahead_audit_summary_ref:{audit_ref}",),
        limitations=DEFAULT_LIMITATIONS,
    )


def blocked_missing_bound_specs_result(
    request_id: str,
    missing_specs: tuple[str, ...],
    *,
    alpha_spec_id: str | None = None,
    study_spec_id: str | None = None,
    dataset_version_id: str | None = None,
    feature_pack_refs: tuple[str, ...] = (),
    label_pack_refs: tuple[str, ...] = (),
    runtime_run_id: str | None = None,
    evidence_summary_ref: str | None = None,
) -> AgentToolResult:
    """Return the fail-closed result when bound AlphaSpec or StudySpec is absent."""

    missing = _validate_missing_specs(missing_specs)
    artifacts = ()
    if evidence_summary_ref is not None:
        artifacts = (
            f"evidence_summary_ref:{_validate_required_text('evidence_summary_ref', evidence_summary_ref)}",
        )
    return AgentToolResult(
        status=AgentToolStatus.BLOCKED,
        role=ROLE_ID,
        request_id=_validate_required_text("request_id", request_id),
        alpha_spec_id=(
            None
            if "alpha_spec_id" in missing
            else _validate_optional_text("alpha_spec_id", alpha_spec_id)
        ),
        study_spec_id=(
            None
            if "study_spec_id" in missing
            else _validate_optional_text("study_spec_id", study_spec_id)
        ),
        dataset_version_id=_validate_optional_text("dataset_version_id", dataset_version_id),
        feature_pack_refs=_validate_text_tuple("feature_pack_refs", feature_pack_refs),
        label_pack_refs=_validate_text_tuple("label_pack_refs", label_pack_refs),
        runtime_run_id=_validate_optional_text("runtime_run_id", runtime_run_id),
        diagnostics_summary="Bound AlphaSpec or StudySpec is missing; fail closed.",
        cost_summary=None,
        rejection_reasons=("missing_bound_specs",),
        blocking_findings=tuple(f"missing_bound_spec:{spec}" for spec in missing),
        next_required_gate=MISSING_BOUND_SPEC_BLOCKED_GATE,
        artifacts=artifacts,
        limitations=DEFAULT_LIMITATIONS,
    )


def _validate_verdict(verdict: str) -> str:
    value = _validate_required_text("verdict", verdict)
    if value not in STATISTICAL_REVIEW_VERDICTS:
        raise ValueError("verdict must be PASS REJECT WATCH or INCONCLUSIVE")
    return value


def _validate_missing_specs(missing_specs: tuple[str, ...]) -> tuple[str, ...]:
    specs = _validate_text_tuple("missing_specs", missing_specs, require_non_empty=True)
    allowed = {"alpha_spec_id", "study_spec_id"}
    unknown = set(specs).difference(allowed)
    if unknown:
        raise ValueError("missing_specs may include only alpha_spec_id or study_spec_id")
    return specs


def _validate_text_tuple(
    field_name: str,
    value: object,
    *,
    require_non_empty: bool = False,
) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple[str, ...]")
    if require_non_empty and not value:
        raise ValueError(f"{field_name} must be non-empty")
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must not contain duplicates")
    for item in value:
        _validate_required_text(field_name, item)
    return value


def _validate_optional_text(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    return _validate_required_text(field_name, value)


def _validate_required_text(field_name: str, value: object) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a str")
    if value != value.strip() or not value:
        raise ValueError(f"{field_name} must be non-empty without surrounding whitespace")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{field_name} must be a single-line string")
    return value


def _append_unique_refs(
    existing: tuple[str, ...],
    refs: tuple[str, ...],
) -> tuple[str, ...]:
    merged = list(existing)
    for ref in refs:
        if ref not in merged:
            merged.append(ref)
    return tuple(merged)


def _register_once(role: AgentRole) -> AgentRole:
    try:
        existing = registry.get(role.role_id)
    except KeyError:
        return registry.register(role)
    if existing != role:
        raise RuntimeError("statistical_reviewer registry entry differs from module contract")
    return existing


REGISTERED_ROLE = _register_once(STATISTICAL_REVIEWER_ROLE)

__all__ = [
    "CALLABLE_TOOL_IDS",
    "CONSUMED_PRIMITIVES",
    "DEFAULT_LIMITATIONS",
    "MISSING_BOUND_SPEC_BLOCKED_GATE",
    "MISSING_EVIDENCE_INCONCLUSIVE_GATE",
    "NEXT_REQUIRED_GATE",
    "NON_PASS_LOOKAHEAD_BLOCKED_GATE",
    "REGISTERED_ROLE",
    "ROLE_ID",
    "SEPARATION_OF_DUTIES_GATE",
    "STATISTICAL_REVIEWER_ROLE",
    "STATISTICAL_REVIEW_VERDICTS",
    "VERDICT_STATUS_BY_OUTCOME",
    "blocked_missing_bound_specs_result",
    "blocked_non_pass_no_lookahead_result",
    "inconclusive_missing_evidence_result",
    "statistical_review_verdict_result",
]
