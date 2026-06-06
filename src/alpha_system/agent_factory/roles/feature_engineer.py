"""Feature Engineer role contract."""

from __future__ import annotations

from alpha_system.agent_factory.permissions.matrix import permission_for
from alpha_system.agent_factory.roles import registry
from alpha_system.agent_factory.roles.contracts import AgentRole

ROLE_ID = "feature_engineer"
FORBIDDEN_TOOL_MARKERS: tuple[str, ...] = (
    "materialize",
    "runtime.",
    "review.",
    "promotion.",
    "broker",
    "paper",
    "live",
)


def _matrix_callable_tools() -> tuple[str, ...]:
    return permission_for(ROLE_ID).tool.allowed_tool_ids


FEATURE_ENGINEER_ROLE = AgentRole(
    role_id=ROLE_ID,
    name="Feature Engineer",
    purpose=(
        "Reference an approved seed feature or draft one bounded FeatureRequest; "
        "never materialize broadly."
    ),
    readable_inputs=(
        "scoped ResearchTask ref",
        "Data Contract Auditor availability refs for approved seed FeaturePack refs",
        "Data Contract Auditor admissible accepted DatasetVersion id ref",
        "approved AlphaSpec ref",
        "governance.feature_request schema ref",
        "prior rejection and library summary refs only",
    ),
    callable_tools=_matrix_callable_tools(),
    producible_outputs=(
        "value-free AgentToolResult artifact ref for bounded FeatureRequest draft",
        "value-free AgentToolResult artifact ref for approved seed feature reference",
        "outputs carry request_id alpha_spec_id dataset_version_id feature_pack_refs next_required_gate limitations",
    ),
    allowed_decisions=(
        "reference one bounded approved seed feature",
        "draft one bounded FeatureRequest within task and budget scope",
        "select next_required_gate for downstream independent review",
    ),
    forbidden_decisions=(
        "self-review or self-approval of feature work",
        "promotion or candidate approval",
        "large-scale or broad feature materialization",
        "committing feature values or value commits",
        "using a label as a feature or label-as-feature",
        "bypassing accepted DatasetVersion policy",
        "reading raw provider data",
        "making external provider calls",
        "runtime bypass or diagnostics execution",
        "session-context features before SESSION_LABEL_GUARD_FIX_V1",
        "value-consuming scans before FEATURE_LABEL_PARQUET_SINK_V1",
        "alpha tradability profitability strategy paper live broker or production claims",
    ),
    handoff_format=(
        "request_id",
        "task_id or scope_ref",
        "alpha_spec_id",
        "feature_request_ref or feature_pack_ref",
        "dataset_version_id",
        "next_required_gate",
        "limitations",
    ),
    reviewer_independence=(
        "Feature Engineer is an implementer and never a reviewer of its own output",
        "feature drafts and references require downstream independent review",
        "Feature Engineer output is never self-approved",
    ),
    failure_modes=(
        "inputs blocked or not admissible",
        "FEATURE_LABEL_PARQUET_SINK_V1 preflight blocker active",
        "SESSION_LABEL_GUARD_FIX_V1 preflight blocker active for session-context features",
        "request exceeds bounded task or budget scope",
        "return structured blocked or limited result refs never a silent pass",
    ),
)

if FEATURE_ENGINEER_ROLE.callable_tools != _matrix_callable_tools():
    raise RuntimeError("feature_engineer callable_tools must match permission matrix")

if any(
    marker in tool_id
    for tool_id in FEATURE_ENGINEER_ROLE.callable_tools
    for marker in FORBIDDEN_TOOL_MARKERS
):
    raise RuntimeError("feature_engineer permission matrix includes a forbidden tool")


def _register_once(role: AgentRole) -> AgentRole:
    try:
        existing = registry.get(role.role_id)
    except KeyError:
        return registry.register(role)
    if existing != role:
        raise RuntimeError("feature_engineer registry entry differs from module contract")
    return existing


REGISTERED_ROLE = _register_once(FEATURE_ENGINEER_ROLE)

__all__ = ["FEATURE_ENGINEER_ROLE", "REGISTERED_ROLE", "ROLE_ID"]
