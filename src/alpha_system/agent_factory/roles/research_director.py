"""Research Director role contract."""

from __future__ import annotations

from alpha_system.agent_factory.permissions.matrix import permission_for
from alpha_system.agent_factory.roles.contracts import AgentRole
from alpha_system.agent_factory.roles import registry

ROLE_ID = "research_director"


def _matrix_callable_tools() -> tuple[str, ...]:
    return permission_for(ROLE_ID).tool.allowed_tool_ids


RESEARCH_DIRECTOR_ROLE = AgentRole(
    role_id=ROLE_ID,
    name="Research Director",
    purpose=(
        "Scope a single bounded ResearchTask, assign roles, and set budgets within queue policy."
    ),
    readable_inputs=(
        "queued ResearchTask summary refs",
        "ResearchBudget VariantBudget and ComputeBudget refs",
        "QueuePriorityPolicy and FamilyBudgetPolicy refs",
        "prior rejection and library summary refs only",
        "blocked input summary refs only",
    ),
    callable_tools=_matrix_callable_tools(),
    producible_outputs=(
        "research_task.scope_draft ref as an AgentToolResult artifact ref",
        "role assignment refs with request_id and task_id",
        "budget setting refs with next_required_gate and limitations",
    ),
    allowed_decisions=(
        "single task scope within queue policy",
        "budget allocation within ResearchBudget and family policy caps",
        "downstream role assignment for the scoped task",
        "next_required_gate selection for downstream independent review",
    ),
    forbidden_decisions=(
        "approving its own scoping as evidence",
        "promoting any factor or candidate",
        "issuing review verdicts",
        "implementing code",
        "drafting AlphaSpecs",
        "critiquing AlphaSpecs",
        "running diagnostics",
        "starting alpha search",
        "starting a continuous loop",
        "batching multiple tasks",
        "bypassing queue or budget bounds",
        "reading raw provider data",
        "making external provider calls",
        "touching capital risk or live decisions",
    ),
    handoff_format=(
        "request_id",
        "task_id or scope_ref",
        "assigned_role_refs",
        "budget_refs",
        "next_required_gate",
        "limitations",
    ),
    reviewer_independence=(
        "Research Director is not a reviewer implementer or promoter",
        "scoping output requires downstream independent critique or review",
        "Director scoping is never self-approved",
    ),
    failure_modes=(
        "missing or unscoped ResearchTask",
        "budget exceeds queue policy",
        "attempt to assign a promotion or review permission",
        "attempt to loop or batch multiple tasks",
        "blocked input refs",
    ),
)

if RESEARCH_DIRECTOR_ROLE.callable_tools != _matrix_callable_tools():
    raise RuntimeError("research_director callable_tools must match permission matrix")


def _register_once(role: AgentRole) -> AgentRole:
    try:
        existing = registry.get(role.role_id)
    except KeyError:
        return registry.register(role)
    if existing != role:
        raise RuntimeError("research_director registry entry differs from module contract")
    return existing


REGISTERED_ROLE = _register_once(RESEARCH_DIRECTOR_ROLE)

__all__ = ["REGISTERED_ROLE", "RESEARCH_DIRECTOR_ROLE", "ROLE_ID"]
