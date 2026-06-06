"""No-Lookahead Auditor role contract.

This module declares the contracts-only No-Lookahead Auditor role. It imports
the existing runtime and governance audit primitives but does not reimplement
them, execute diagnostics, resolve data, instantiate an agent, or promote work.
"""

from __future__ import annotations

from alpha_system.agent_factory.permissions.matrix import permission_for
from alpha_system.agent_factory.roles import registry
from alpha_system.agent_factory.roles.contracts import AgentRole
from alpha_system.agent_factory.tools.results import AgentToolResult, AgentToolStatus
from alpha_system.governance.label_leakage_guard import (
    LabelLeakageFinding,
    LabelLeakageResult,
    check_label_leakage,
)
from alpha_system.runtime.audit.no_lookahead import (
    NoLookaheadAuditOutcome,
    NoLookaheadAuditResult,
    NoLookaheadRejectionCategory,
    NoLookaheadRuntimeAudit,
)

ROLE_ID = "no_lookahead_auditor"
MISSING_FIELD_BLOCKED_GATE = "diagnostics_runner_restore_audit_fields"
NEXT_REVIEW_GATE = "statistical_reviewer_independent_review"

REQUIRED_AUDIT_FIELD_REFS: tuple[str, ...] = (
    "available_ts",
    "label_available_ts",
    "same_bar_fill_policy_ref",
    "locked_test_partition_scope_ref",
)
DEFAULT_LIMITATIONS: tuple[str, ...] = (
    "contract_only_no_agent_instantiated",
    "audit_result_is_integrity_gate_not_alpha_validation",
    "no_alpha_profitability_tradability_or_live_claim",
)


def _matrix_callable_tools() -> tuple[str, ...]:
    return permission_for(ROLE_ID).tool.allowed_tool_ids


CALLABLE_TOOL_IDS: tuple[str, ...] = _matrix_callable_tools()
CONSUMED_PRIMITIVES: tuple[object, ...] = (
    NoLookaheadRuntimeAudit,
    NoLookaheadAuditResult,
    NoLookaheadAuditOutcome,
    NoLookaheadRejectionCategory,
    check_label_leakage,
    LabelLeakageResult,
    LabelLeakageFinding,
)

NO_LOOKAHEAD_AUDITOR_ROLE = AgentRole(
    role_id=ROLE_ID,
    name="No-Lookahead Auditor",
    purpose=(
        "Audit runtime output refs for point-in-time integrity and decide lookahead PASS or "
        "BLOCKED."
    ),
    readable_inputs=(
        "RuntimeToolResult or RuntimeRunSummary summary refs",
        "NoLookaheadAuditResult summary refs",
        "LabelLeakageResult and LabelLeakageFinding summary refs",
        "bound AlphaSpec and StudySpec ids",
        "dataset_version_id feature_pack_refs and label_pack_refs",
        "availability same_bar_fill and locked_test discipline refs only",
    ),
    callable_tools=CALLABLE_TOOL_IDS,
    producible_outputs=(
        "AgentToolResult with lookahead PASS carried as OK status",
        "AgentToolResult with BLOCKED status for leakage or missing audit fields",
        "AgentToolResult fields role request_id ids blocking_findings",
        "AgentToolResult fields rejection_reasons next_required_gate artifacts limitations",
    ),
    allowed_decisions=(
        "emit_lookahead_pass_for_clean_runtime_and_label_guard_refs",
        "emit_blocked_for_availability_leakage_same_bar_or_locked_test_violation",
        "select_next_required_gate_for_independent_downstream_review",
    ),
    forbidden_decisions=(
        "promote_factor_candidate_or_strategy",
        "weaken_bypass_or_reimplement_no_lookahead_guard",
        "run_diagnostics_or_retry_runtime_itself",
        "draft_or_critique_alphaspecs",
        "review_own_implementation_or_own_diagnostics",
        "read_raw_provider_data_or_runtime_values",
        "make_external_provider_calls",
        "bypass_runtime_input_resolver_or_tool_surface",
        "write_feature_label_dataset_or_promotion_registry",
        "touch_capital_risk_live_paper_broker_order_or_deployment_decisions",
        "claim_alpha_profitability_tradability_strategy_or_production_readiness",
    ),
    handoff_format=(
        "request_id",
        "role",
        "alpha_spec_id study_spec_id dataset_version_id",
        "runtime_run_summary_ref",
        "no_lookahead_audit_summary_ref",
        "label_leakage_finding_summary_refs",
        "status",
        "blocking_findings",
        "rejection_reasons",
        "next_required_gate",
        "artifacts",
        "limitations",
    ),
    reviewer_independence=(
        "auditor_role_must_not_equal_alphaspec_drafter",
        "auditor_role_must_not_equal_implementation_or_diagnostics_runner",
        "lookahead_audit_requires_independent_downstream_review_before_lifecycle_advance",
    ),
    failure_modes=(
        "BLOCKED on detected available_ts violation",
        "BLOCKED on label_available_ts or label leakage finding",
        "BLOCKED on same_bar_fill or locked_test discipline violation",
        "BLOCKED when required audit fields are missing never silent PASS",
        "INCONCLUSIVE or BLOCKED when audit refs are insufficient",
        "permission_denied_when_tool_surface_or_matrix_grant_is_absent",
    ),
)

if NO_LOOKAHEAD_AUDITOR_ROLE.callable_tools != _matrix_callable_tools():
    raise RuntimeError("no_lookahead_auditor callable_tools must match permission matrix")


def blocked_missing_audit_fields_result(
    request_id: str,
    missing_fields: tuple[str, ...],
    *,
    alpha_spec_id: str | None = None,
    study_spec_id: str | None = None,
    dataset_version_id: str | None = None,
    feature_pack_refs: tuple[str, ...] = (),
    label_pack_refs: tuple[str, ...] = (),
    runtime_run_id: str | None = None,
) -> AgentToolResult:
    """Return the contract-required fail-closed result for missing audit fields."""

    fields = _validate_missing_fields(missing_fields)
    return AgentToolResult(
        status=AgentToolStatus.BLOCKED,
        role=ROLE_ID,
        request_id=request_id,
        alpha_spec_id=alpha_spec_id,
        study_spec_id=study_spec_id,
        dataset_version_id=dataset_version_id,
        feature_pack_refs=feature_pack_refs,
        label_pack_refs=label_pack_refs,
        runtime_run_id=runtime_run_id,
        diagnostics_summary="Required no-lookahead audit fields are missing; fail closed.",
        cost_summary=None,
        rejection_reasons=("missing_required_audit_fields",),
        blocking_findings=tuple(f"missing_required_audit_field:{field}" for field in fields),
        next_required_gate=MISSING_FIELD_BLOCKED_GATE,
        artifacts=(),
        limitations=DEFAULT_LIMITATIONS,
    )


def _validate_missing_fields(missing_fields: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(missing_fields, tuple):
        raise TypeError("missing_fields must be a tuple[str, ...]")
    if not missing_fields:
        raise ValueError("missing_fields must be non-empty")
    if len(set(missing_fields)) != len(missing_fields):
        raise ValueError("missing_fields must not contain duplicates")
    for field in missing_fields:
        if not isinstance(field, str) or field != field.strip() or not field:
            raise ValueError("missing_fields must contain non-empty field refs")
    return missing_fields


def _register_once(role: AgentRole) -> AgentRole:
    try:
        existing = registry.get(role.role_id)
    except KeyError:
        return registry.register(role)
    if existing != role:
        raise RuntimeError("no_lookahead_auditor registry entry differs from module contract")
    return existing


REGISTERED_ROLE = _register_once(NO_LOOKAHEAD_AUDITOR_ROLE)

__all__ = [
    "CALLABLE_TOOL_IDS",
    "CONSUMED_PRIMITIVES",
    "DEFAULT_LIMITATIONS",
    "MISSING_FIELD_BLOCKED_GATE",
    "NEXT_REVIEW_GATE",
    "NO_LOOKAHEAD_AUDITOR_ROLE",
    "REGISTERED_ROLE",
    "REQUIRED_AUDIT_FIELD_REFS",
    "ROLE_ID",
    "blocked_missing_audit_fields_result",
]
