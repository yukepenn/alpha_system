# Agent Factory Naming and Index Policy

## Purpose

This document defines the stable naming and index conventions for the
`alpha_system.agent_factory` contract layer. AGENT-P02 creates only package,
test, docs, and template skeletons. Later phases add contracts into these
locations without moving shared roots.

The Agent Factory remains contracts-only and local-first. These conventions do
not authorize autonomous agents, continuous runners, alpha search, data access,
external provider calls, broker scope, or paper/live behavior.

## Package Layout

The importable package root is `src/alpha_system/agent_factory/`.

Subpackages are reserved as follows:

| Subpackage | Future responsibility |
| --- | --- |
| `roles/` | Role contract modules for the Agent Factory roster. |
| `permissions/` | Permission matrix and access policy contracts. |
| `tools/` | Agent-facing tool contract and structured-output contracts. |
| `queue/` | Research task and queue contract modules. |
| `separation/` | Separation-of-duties and no-self-review contracts. |
| `records/` | Agent decision, invocation, and handoff record contracts. |
| `memory/` | Rejected-idea and research-memory contracts. |
| `dry_run/` | Bounded non-alpha dry-run harness modules. |

Each subpackage is a real Python package with `__init__.py`. Empty skeleton
`__init__.py` files expose only a module docstring and `__all__`; they must not
import modules that have not been created yet.

## Module Naming

- Python module files use `snake_case.py`.
- Test modules mirror source modules as `test_<module>.py`.
- One role contract lives in one role module, for example
  `roles/research_director.py`.
- Shared contract modules use descriptive nouns, for example
  `permissions/matrix.py`, `tools/registry.py`, or `queue/research_task.py`.
- Avoid generic names such as `common.py`, `helpers.py`, or `utils.py` unless a
  later spec explicitly authorizes the shared abstraction and its ownership.
- Role, permission, tool, queue, record, memory, and dry-run behavior must be
  added by the phase that owns that contract. Skeleton roots do not imply
  behavior.

## Test Layout

Unit tests mirror the package layout under `tests/unit/agent_factory/`:

```text
tests/unit/agent_factory/
  roles/test_<module>.py
  permissions/test_<module>.py
  tools/test_<module>.py
  queue/test_<module>.py
  separation/test_<module>.py
  records/test_<module>.py
  memory/test_<module>.py
  dry_run/test_<module>.py
```

Conformance tests for package shape may live directly under
`tests/unit/agent_factory/`. Behavior tests belong next to the subpackage they
exercise.

## Docs Layout

Durable Agent Factory docs live under `docs/agent_factory/`.

Reserved paths:

- `docs/agent_factory/README.md`: docs root and navigation.
- `docs/agent_factory/OVERVIEW.md`: campaign overview and safety posture.
- `docs/agent_factory/PREFLIGHT_GATES.md`: AGENT-P01 entry gate semantics.
- `docs/agent_factory/NAMING.md`: this naming and index policy.
- `docs/agent_factory/roles/<role>.md`: one operator-facing role doc per role.
- `docs/agent_factory/tools/<tool>.md`: one operator-facing tool doc per tool
  family when authorized.
- `docs/agent_factory/operators/`: operator workflow docs when AGENT-P20 adds
  them.

Doc file names use `snake_case.md` except established all-caps policy documents
such as `README.md`, `OVERVIEW.md`, `PREFLIGHT_GATES.md`, and `NAMING.md`.

## Templates Layout

Reusable Agent Factory templates live under `templates/agent_factory/`.

Reserved paths:

- `templates/agent_factory/README.md`: templates root index.
- `templates/agent_factory/roles/<role>.md`: role prompt or role operating
  template files added by later role/prompt phases.
- `templates/agent_factory/prompts/README.md`: the prompt source-of-truth index
  added by AGENT-P19.
- `templates/agent_factory/prompts/<prompt_name>.md`: indexed prompt assets
  added by AGENT-P19.
- `templates/agent_factory/research_task.template.yaml`: research task template
  added by AGENT-P06.
- `templates/agent_factory/agent_handoff.template.md`: handoff template added by
  AGENT-P17.

AGENT-P02 creates only the templates root README. It does not create per-role,
per-prompt, research-task, or handoff templates.

## Source-of-Truth Index Rule

Prompt and operator-facing docs must have a single durable index before they are
consumed by later phases.

- Prompt assets are indexed only by
  `templates/agent_factory/prompts/README.md` once AGENT-P19 creates it.
- Agent Factory docs are indexed from `docs/agent_factory/README.md`, with
  detailed topic docs under `docs/agent_factory/**`.
- Role docs use `docs/agent_factory/roles/<role>.md` and must link to the
  matching role module and any matching prompt template after those assets
  exist.
- New prompt or docs files must be added to the relevant index in the same
  phase that creates them.
- Do not create scattered, unindexed prompt files. Do not treat templates as
  source data or evidence.

The index rule is structural only. It does not approve a prompt for autonomous
use, production deployment, alpha search, or broker/paper/live execution.
