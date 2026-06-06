"""Diagnostics Runner role contract.

This module declares the contracts-only Diagnostics Runner role. It consumes
the runtime tool-result contracts and CLI command surface by reference; it does
not run diagnostics, compute costs, resolve raw data, instantiate an agent, or
promote work.
"""

from __future__ import annotations

from alpha_system.agent_factory.permissions.matrix import permission_for
from alpha_system.agent_factory.roles import registry
from alpha_system.agent_factory.roles.contracts import AgentRole
from alpha_system.agent_factory.tools.registry import contract_for
from alpha_system.agent_factory.tools.results import AgentToolResult, AgentToolStatus
from alpha_system.cli import runtime as runtime_cli
from alpha_system.runtime.tool_results import RuntimeRunSummary, RuntimeToolResult

ROLE_ID = "diagnostics_runner"
MISSING_STUDY_SPEC_GATE = "research_director_bind_study_spec"
NEXT_REVIEW_GATE = "statistical_reviewer_independent_review"

EXPECTED_RUNTIME_TOOL_IDS: tuple[str, ...] = (
    "runtime.plan",
    "runtime.validate_inputs",
    "runtime.run_diagnostics",
    "runtime.run_label_diagnostics",
    "runtime.run_signal_probe",
    "runtime.run_cost_stress",
    "runtime.build_evidence_draft",
    "runtime.build_reference_handoff",
)

RUNTIME_CLI_COMMANDS: tuple[str, ...] = (
    "alpha runtime plan",
    "alpha runtime validate-inputs",
    "alpha runtime run-diagnostics",
    "alpha runtime run-label-diagnostics",
    "alpha runtime run-signal-probe",
    "alpha runtime run-cost-stress",
    "alpha runtime build-evidence-draft",
    "alpha runtime build-reference-handoff",
)

DEFAULT_LIMITATIONS: tuple[str, ...] = (
    "contract_only_no_agent_instantiated",
    "diagnostic_pass_not_promotion_alpha_or_candidate",
    "evidence_draft_not_candidate_and_reference_handoff_not_validation",
    "no_alpha_profitability_tradability_or_live_claim",
)

CONSUMED_RUNTIME_PRIMITIVES: tuple[object, ...] = (
    RuntimeToolResult,
    RuntimeRunSummary,
    runtime_cli.run_plan,
    runtime_cli.run_validate_inputs,
    runtime_cli.run_diagnostics,
    runtime_cli.run_label_diagnostics,
    runtime_cli.run_signal_probe_command,
    runtime_cli.run_cost_stress,
    runtime_cli.run_build_evidence_draft,
    runtime_cli.run_build_reference_handoff,
)


def _validated_runtime_tool_ids() -> tuple[str, ...]:
    permissions = permission_for(ROLE_ID)
    for tool_id in EXPECTED_RUNTIME_TOOL_IDS:
        contract = contract_for(tool_id)
        if contract.group.value != "runtime":
            raise RuntimeError(f"{tool_id} is not a runtime tool contract")
        if not contract.allows(ROLE_ID):
            raise RuntimeError(f"{ROLE_ID} is not an allowed caller for {tool_id}")
        if not any(permissions.tool.allows(ref) for ref in contract.permission_matrix_refs):
            raise RuntimeError(f"{tool_id} is not backed by a diagnostics_runner permission ref")
    return EXPECTED_RUNTIME_TOOL_IDS


CALLABLE_TOOL_IDS: tuple[str, ...] = _validated_runtime_tool_ids()

DIAGNOSTICS_RUNNER_ROLE = AgentRole(
    role_id=ROLE_ID,
    name="Diagnostics Runner",
    purpose=(
        "Request runtime diagnostics for one bound AlphaSpec and StudySpec within budget."
    ),
    readable_inputs=(
        "bound AlphaSpec id",
        "bound StudySpec id required before diagnostics",
        "resolved admissible DatasetVersion id from resolve_dataset_version",
        "admissible DatasetVersion states VERSIONED and READY_FOR_RESEARCH",
        "seed FeaturePack refs and LabelPack refs",
        "governing ResearchTask ResearchBudget ComputeBudget and VariantBudget refs",
        "RuntimeToolResult and RuntimeRunSummary refs only",
    ),
    callable_tools=CALLABLE_TOOL_IDS,
    producible_outputs=(
        "AgentToolResult fields status role request_id",
        "AgentToolResult fields alpha_spec_id study_spec_id dataset_version_id",
        "AgentToolResult fields feature_pack_refs label_pack_refs runtime_run_id",
        "AgentToolResult fields diagnostics_summary cost_summary",
        "AgentToolResult fields rejection_reasons blocking_findings",
        "AgentToolResult fields next_required_gate artifacts limitations",
        "outputs are structured value-free refs and summaries never raw or heavy payloads",
    ),
    allowed_decisions=(
        "request_diagnostics_within_bound_research_compute_and_variant_budget",
        "report_DIAGNOSTICS_COMPLETE_BLOCKED_or_INCONCLUSIVE",
        "surface_runtime_blocking_findings_rejection_reasons_and_limitations",
        "select_next_required_gate_for_independent_review_or_repair",
    ),
    forbidden_decisions=(
        "promote_factor_candidate_strategy_evidence_or_reference",
        "alter_author_FeatureRequest_LabelSpec_AlphaSpec_or_StudySpec",
        "bypass_runtime_input_resolver_or_tool_surface",
        "invoke_runtime_directly_without_runtime_bridge",
        "reimplement_diagnostics_cost_overfit_or_no_lookahead_logic",
        "read_raw_provider_data_or_call_external_provider",
        "exceed_compute_budget_or_variant_budget",
        "frame_result_as_strategy_validation_alpha_or_candidate",
        "self_review_or_issue_statistical_verdict",
        "write_feature_label_dataset_runtime_or_promotion_registry",
        "touch_capital_risk_live_paper_broker_order_or_deployment_decisions",
    ),
    handoff_format=(
        "AGENT-P17-shaped decision_to_tool_invocation_to_spec_ids",
        "request_id role decision status",
        "alpha_spec_id study_spec_id dataset_version_id",
        "feature_pack_refs label_pack_refs runtime_run_id",
        "runtime_tool_invocation_refs",
        "diagnostics_summary_ref cost_summary_ref",
        "blocking_findings rejection_reasons next_required_gate",
        "artifacts limitations",
    ),
    reviewer_independence=(
        "runner_must_not_equal_promoter",
        "runner_must_not_equal_statistical_reviewer",
        "runner_must_not_self_review_runtime_output",
        "AGENT-P16 separation_of_duties_enforces_independent_reviewer",
    ),
    failure_modes=(
        "BLOCKED when StudySpec is missing or unbound no StudySpec no diagnostics",
        "BLOCKED when DatasetVersion is unresolved or inadmissible",
        "BLOCKED or INCONCLUSIVE when ResearchBudget ComputeBudget or VariantBudget is exhausted",
        "runtime BLOCKED REJECTED or INCONCLUSIVE is surfaced faithfully",
        "runtime bridge unavailable is BLOCKED until AGENT-P21 supplies the bridge",
        "permission_denied_when_runtime_tool_or_matrix_grant_is_absent",
    ),
)

if DIAGNOSTICS_RUNNER_ROLE.callable_tools != _validated_runtime_tool_ids():
    raise RuntimeError("diagnostics_runner callable_tools must match runtime tool contracts")


def blocked_missing_study_spec_result(
    request_id: str,
    *,
    alpha_spec_id: str | None = None,
    dataset_version_id: str | None = None,
    feature_pack_refs: tuple[str, ...] = (),
    label_pack_refs: tuple[str, ...] = (),
) -> AgentToolResult:
    """Return the contract-required fail-closed result for no StudySpec."""

    return AgentToolResult(
        status=AgentToolStatus.BLOCKED,
        role=ROLE_ID,
        request_id=request_id,
        alpha_spec_id=alpha_spec_id,
        study_spec_id=None,
        dataset_version_id=dataset_version_id,
        feature_pack_refs=feature_pack_refs,
        label_pack_refs=label_pack_refs,
        runtime_run_id=None,
        diagnostics_summary="No bound StudySpec supplied; diagnostics request fails closed.",
        cost_summary=None,
        rejection_reasons=("missing_bound_study_spec",),
        blocking_findings=("no_study_spec_no_diagnostics",),
        next_required_gate=MISSING_STUDY_SPEC_GATE,
        artifacts=(),
        limitations=DEFAULT_LIMITATIONS,
    )


def _register_once(role: AgentRole) -> AgentRole:
    try:
        existing = registry.get(role.role_id)
    except KeyError:
        return registry.register(role)
    if existing != role:
        raise RuntimeError("diagnostics_runner registry entry differs from module contract")
    return existing


REGISTERED_ROLE = _register_once(DIAGNOSTICS_RUNNER_ROLE)

__all__ = [
    "CALLABLE_TOOL_IDS",
    "CONSUMED_RUNTIME_PRIMITIVES",
    "DEFAULT_LIMITATIONS",
    "DIAGNOSTICS_RUNNER_ROLE",
    "EXPECTED_RUNTIME_TOOL_IDS",
    "MISSING_STUDY_SPEC_GATE",
    "NEXT_REVIEW_GATE",
    "REGISTERED_ROLE",
    "ROLE_ID",
    "RUNTIME_CLI_COMMANDS",
    "blocked_missing_study_spec_result",
]
