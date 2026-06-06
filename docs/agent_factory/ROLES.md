# Agent Role Contracts

## Purpose

`alpha_system.agent_factory.roles` defines the contracts-only role model for
the Agent Factory. AGENT-P03 adds only the immutable `AgentRole` schema and the
discovery-based role registry. It does not add a concrete role, instantiate an
autonomous agent, start a continuous runner, run alpha search, promote a factor,
or make an alpha, tradability, profitability, broker, paper, live, deployment,
or production claim.

## AgentRole Fields

Each `AgentRole` is a frozen, value-free dataclass. Every field is required and
must be a short declarative string or a non-empty `tuple[str, ...]`.

| Field | Meaning |
| --- | --- |
| `role_id` | Stable snake_case identifier used by registries and policies. |
| `name` | Human-readable role name. |
| `purpose` | One-line mandate for the role. |
| `readable_inputs` | Declarative input kinds or references the role may read. These are names only, not raw data or heavy payloads. |
| `callable_tools` | Declarative tool ids the role may call. Tool contracts are owned by AGENT-P05. |
| `producible_outputs` | Structured output kinds the role may emit. |
| `allowed_decisions` | Decisions the role is allowed to make inside its boundary. |
| `forbidden_decisions` | Decisions or actions the role must never take, such as self-approval, self-promotion, raw access, registry writes, runtime bypass, or alpha/tradability claims. |
| `handoff_format` | Required handoff sections or shape the role must produce. |
| `reviewer_independence` | Declarative independence rules such as drafter not equal to approver or implementer not equal to reviewer. |
| `failure_modes` | Expected fail-closed termination or rejection modes. |

Validation fails closed when a field is missing, empty, mutable where a tuple is
required, multi-line, oversized, or contains raw/heavy payload markers such as
provider payloads, DB rows, raw/canonical/cache paths, artifact paths, or heavy
file references.

## Registry Mechanics

`roles.registry` provides a module-level discovery registry:

- `register(role)` registers an `AgentRole`.
- `get(role_id)` returns a single role by id.
- `all_roles()` returns registered roles in deterministic `role_id` order.
- `role_ids()` returns registered ids in deterministic order.

Duplicate `role_id` registration is rejected. Malformed objects are rejected
before entering the registry.

Later role modules self-register at import time by constructing their contract
and calling the registry:

```python
from alpha_system.agent_factory.roles import AgentRole, register

ROLE = AgentRole(
    role_id="example_role",
    name="Example Role",
    purpose="Declare one bounded role.",
    readable_inputs=("task_ref",),
    callable_tools=("tool.ref",),
    producible_outputs=("handoff_ref",),
    allowed_decisions=("request_revision",),
    forbidden_decisions=("self_approval", "self_promotion"),
    handoff_format=("summary", "decision"),
    reviewer_independence=("drafter != approver",),
    failure_modes=("malformed_contract",),
)

register(ROLE)
```

## No Hard Per-Role Imports

`roles/__init__.py` and `roles/registry.py` must not import any concrete role
module. They export only the model and registry surface. This rule lets the
later role wave add disjoint role modules in parallel: each role phase owns its
own file and self-registers when that file is imported, without editing shared
registry code.

The wiring phase may later choose where concrete roles are imported together.
Until then, the registry remains passive and discovery-based.

## Boundaries

Role contracts are declarations only. They name permitted inputs, tools,
outputs, decisions, handoff sections, independence rules, and failure modes.
They do not carry raw data, canonical data, feature values, label values,
runtime values, agent records, provider responses, logs, caches, local DB
content, or heavy artifacts.

The role model consumes existing runtime, governance, and registry primitives by
reference only. It does not edit those primitives, bypass them, or authorize
broker, paper, live, order, account, deployment, strategy, backtest, portfolio,
or production behavior.
