# ALPHA_AGENT_FACTORY_MVP Phase Plan

## Purpose

This phase plan is the human-readable contract for `ALPHA_AGENT_FACTORY_MVP`, the **controlled AI
Alpha Research Team layer** over the completed Governance + Feature/Label + Research Runtime stack.
It defines, as **contracts only**, the agent role model, permission matrix, tool contracts, research
queue, separation-of-duties enforcement, agent/decision/handoff records, rejected-idea memory,
prompt assets, a runtime tool integration bridge, and a bounded non-alpha dry-run harness — by
**driving existing primitives** (`alpha_system.runtime.tool_results`, `alpha_system.cli.runtime`,
`alpha_system.governance.*`, `alpha_system.data.foundation.version_registry.resolve_dataset_version`),
never re-implementing or editing them. It does **not** instantiate any autonomous agent, run a
continuous research runner, conduct alpha search, promote a factor, validate a strategy, or make any
alpha/tradability/profitability claim. Every structured field below is derived from `campaign.yaml`;
the two files must agree.

## Campaign Invariants

- Contracts only — no autonomous agent is instantiated; no continuous research runner is created.
- Agents **drive** the runtime/governance/registry primitives and never duplicate or edit them.
- Every agent role has an explicit permission-matrix entry (`ToolPermission`/`DataPermission`/`WritePermission`/`ReviewPermission`/`PromotionPermission`/`HumanApprovalRequired`/`RedLaneRequired`); default-deny, fail-closed.
- Separation of duties: generator cannot approve, implementer cannot review, diagnostics runner cannot promote, reviewer is not the implementer, librarian cannot write a registry without a reviewer verdict.
- All agent-facing tool outputs are **structured and value-free** — they carry summaries, version ids, statuses, rejection reasons, artifact refs, and the next required gate, never raw or heavy data.
- Agents call the Research Runtime through `RuntimeToolResult` / `RuntimeRunSummary` (and `alpha runtime`); they resolve inputs via `resolve_dataset_version`; no raw provider access; no external provider calls.
- `no AlphaSpec → no implementation`; `no StudySpec → no diagnostics`; `no EvidenceBundle → no candidate`; `no TrialLedger → no promotion`; `no reviewer verdict → no factor library entry`.
- Preflight gates: seed FeaturePack/LabelPack exists; runtime real smoke PASS; `FEATURE_LABEL_PARQUET_SINK_V1` status; `SESSION_LABEL_GUARD_FIX_V1` status.
- Large-scale value-consuming studies are blocked until `FEATURE_LABEL_PARQUET_SINK_V1`; session-context features are blocked until `SESSION_LABEL_GUARD_FIX_V1`.
- A seed-pack/synthetic dry-run is not alpha evidence; an EvidenceDraft is not a candidate; a ReferenceCandidateHandoff is not Reference validation; the human owns risk/capital/live judgment.
- Local-only and deterministic; no broker/live/paper/order/account scope; no committed raw/canonical/feature/label/runtime/agent values, heavy artifacts, or local DBs.

## Global Phase Rules

### Workflow Rules

- Workflow 2 strict order: `RUN_INIT → CAMPAIGN_LOAD → PHASE_SELECT → SPEC_GENERATE → SPEC_VALIDATE → WORKTREE_CREATE → CODEX_EXECUTE → CHECKS_RUN → HANDOFF_VALIDATE → CLAUDE_REVIEW → VERDICT_PARSE → PR_CREATE → CI_WAIT → MERGE_GATE → MERGE → DONE_CHECK → NEXT_PHASE → CAMPAIGN_DONE_CHECK → RUN_SUMMARY`.
- Each phase requires a spec, runs its checks, writes a handoff, and (YELLOW) a fresh Claude review with `verdict.json`.

### DAG Wave Scheduler Rules

- `mode: dag_wave`, `parallel_execution: true`, `max_parallel_phases: 3`, `merge_queue: serial`, `update_active_campaign: coordinator_only`.
- A phase is parallel-safe **only** if it sets `parallel_safe: true`, declares disjoint `allowed_paths`, sets `must_run_alone: false`, declares no global/coordinator file, and is not RED. Otherwise it runs alone.
- Phase branches never write `ACTIVE_CAMPAIGN.md` in parallel mode; the pointer is coordinator-owned. No phase lists `ACTIVE_CAMPAIGN.md` in `allowed_paths`.
- Parallel-safe phases omit `runs/**` from `allowed_paths` (it is a shared local-only path); run-alone phases may list it.
- Preview with `just frontier-plan ALPHA_AGENT_FACTORY_MVP`; mock with `just frontier-run-parallel-mock ALPHA_AGENT_FACTORY_MVP 3` before the first live parallel run.

### Repo Path Rules

- The active repo and worktrees run under the WSL2 Linux filesystem at `~/projects/alpha_system`; `/mnt/c`, OneDrive, Dropbox, Google Drive, Windows-synced folders, network drives, and temp dirs are forbidden.

### Git Rules

- Explicit staging only; `git add .` / `git add -A` forbidden; no force push; commit format `<campaign_id>/<phase_id>: <summary>`.

### Artifact Rules

- `runs/**` is local-only and never staged. Never commit raw/canonical/feature/label/runtime/agent values, parquet/arrow/feather/dbn/zst, provider responses, local DBs, logs, caches, or heavy artifacts. Tiny synthetic documented fixtures under `tests/**/fixtures/**` are the only data-like exception.

### Domain Boundary Rules

- `agent_factory` consumes `runtime.*`, `governance.*`, `research.*`, `experiments.*`, `backtest.*`, `features.*`, `labels.*`, and `data.foundation.*`; it must not edit those packages (they are in each phase's `forbidden_paths`). No broker/live/paper/order/account scope; no autonomous agent; no alpha search; no factor/strategy promotion.

### Review Rules

- YELLOW phases require a fresh Claude Opus 4.8 xhigh review and a `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`} to merge. The implementer cannot self-approve.

### Repair Rules

- Bounded repair, max 2 attempts; repair attempts recorded under `runs/<run_id>/phases/<phase_id>/repair_attempts/`; fake completion forbidden.

### Validation Rules

- Run the narrowest meaningful check first, broaden when shared behavior changes, and record skipped checks with the reason. Default commands: `python tools/verify.py --smoke` / `--all`, `python tools/hooks/canary_runner.py`.

## Phase Table Summary

| Phase | Name | Lane | Deps | Parallel-safe | Merge group |
| --- | --- | --- | --- | --- | --- |
| `AGENT-P00` | Agent Factory Campaign Bootstrap | GREEN | — | false | bootstrap |
| `AGENT-P01` | Agent Factory Entry Contract and Preflight Gates | YELLOW | AGENT-P00 | false | foundation |
| `AGENT-P02` | Agent Factory Package, Docs, and Template Skeleton and Naming | YELLOW | AGENT-P01 | false | foundation |
| `AGENT-P03` | Agent Role Contract Model | YELLOW | AGENT-P02 | false | foundation |
| `AGENT-P04` | Agent Permission Matrix and Tool Access Policy | YELLOW | AGENT-P03 | false | foundation |
| `AGENT-P05` | Tool Contract Registry and Structured Outputs | YELLOW | AGENT-P04 | false | foundation |
| `AGENT-P06` | Research Queue and Work Item Contracts | YELLOW | AGENT-P05 | false | foundation |
| `AGENT-P07` | Research Director Role Contract | YELLOW | AGENT-P06 | true | agent_roles |
| `AGENT-P08` | Hypothesis Scout Role Contract | YELLOW | AGENT-P06 | true | agent_roles |
| `AGENT-P09` | AlphaSpec Critic Role Contract | YELLOW | AGENT-P06 | true | agent_roles |
| `AGENT-P10` | Data Contract Auditor Role Contract | YELLOW | AGENT-P06 | true | agent_roles |
| `AGENT-P11` | Feature Engineer and Label Engineer Role Contracts | YELLOW | AGENT-P06 | true | agent_roles |
| `AGENT-P12` | No-Lookahead Auditor Role Contract | YELLOW | AGENT-P06 | true | agent_roles |
| `AGENT-P13` | Diagnostics Runner Role Contract | YELLOW | AGENT-P06 | true | agent_roles |
| `AGENT-P14` | Statistical Reviewer Role Contract | YELLOW | AGENT-P06 | true | agent_roles |
| `AGENT-P15` | Librarian and Memory Update Role Contract | YELLOW | AGENT-P06 | true | agent_roles |
| `AGENT-P16` | Separation-of-Duties and No-Self-Review Enforcement | YELLOW | AGENT-P07..P15 | false | integration |
| `AGENT-P17` | Agent Handoff and Tool Invocation Records | YELLOW | AGENT-P16 | false | integration |
| `AGENT-P18` | Rejected-Idea Memory and Research Memory | YELLOW | AGENT-P17 | false | integration |
| `AGENT-P19` | Agent Prompt and Skill Assets | YELLOW | AGENT-P18 | true | assets |
| `AGENT-P20` | Agent Factory Docs and Operator Guide | YELLOW | AGENT-P18 | true | assets |
| `AGENT-P21` | Runtime Tool Integration Bridge | YELLOW | AGENT-P18 | true | assets |
| `AGENT-P22` | Agent Dry-Run Harness | YELLOW | AGENT-P19, AGENT-P20, AGENT-P21 | false | closeout |
| `AGENT-P23` | Seed-Pack and Synthetic Dry Run | YELLOW | AGENT-P22 | false | closeout |
| `AGENT-P24` | Workflow 2 DAG Integration and Parallel Plan | YELLOW | AGENT-P23 | false | closeout |
| `AGENT-P25` | Acceptance Audit and Closeout | YELLOW | AGENT-P24 | false | closeout |

## Parallel Wave Summary

Waves are computed by the DAG scheduler from dependencies plus DAG metadata; the shape below is the
intended plan (`just frontier-plan` previews exact waves, and at `max_parallel_phases: 3` each
parallel group is split into sub-waves of three):

- **Wave 0 — sequential bootstrap + core contracts (run-alone):** AGENT-P00 → AGENT-P01 → AGENT-P02 → AGENT-P03 → AGENT-P04 → AGENT-P05 → AGENT-P06.
- **Wave 1 — parallel role contracts (disjoint `allowed_paths`):** AGENT-P07, AGENT-P08, AGENT-P09, AGENT-P10, AGENT-P11, AGENT-P12, AGENT-P13, AGENT-P14, AGENT-P15.
- **Wave 2 — sequential enforcement / records / memory (run-alone):** AGENT-P16 → AGENT-P17 → AGENT-P18.
- **Wave 3 — parallel assets + runtime bridge (disjoint `allowed_paths`):** AGENT-P19, AGENT-P20, AGENT-P21.
- **Wave 4 — sequential dry-run + closeout (run-alone):** AGENT-P22 → AGENT-P23 → AGENT-P24 → AGENT-P25.

## Acceptance Gate Summary

Each of the 26 phases belongs to exactly one acceptance gate:

| Gate | Phases |
| --- | --- |
| `bootstrap_and_entry` | AGENT-P00, AGENT-P01, AGENT-P02 |
| `core_contracts` | AGENT-P03, AGENT-P04, AGENT-P05, AGENT-P06 |
| `agent_roles` | AGENT-P07, AGENT-P08, AGENT-P09, AGENT-P10, AGENT-P11, AGENT-P12, AGENT-P13, AGENT-P14, AGENT-P15 |
| `enforcement_and_records` | AGENT-P16, AGENT-P17, AGENT-P18 |
| `assets_and_bridge` | AGENT-P19, AGENT-P20, AGENT-P21 |
| `dry_run_and_closeout` | AGENT-P22, AGENT-P23, AGENT-P24, AGENT-P25 |

Final verdict ∈ {`COMPLETE`, `COMPLETE_WITH_WARNINGS`, `BLOCKED`}.

# Detailed Phase Specs

## AGENT-P00 — Agent Factory Campaign Bootstrap

### Phase ID
`AGENT-P00`
### Phase Name
Agent Factory Campaign Bootstrap
### Lane
GREEN
### Dependencies
None
### DAG Scheduling
- `parallel_safe`: `false`; `must_run_alone`: `true`; `conflicts_with`: `[]`; `resource_class`: `[]`; `merge_group`: `bootstrap`
### Purpose
Lay down the campaign control surface and the `docs/agent_factory/` docs root so Workflow 2 can load and schedule the campaign.
### Scope
- Create the six campaign contract files and `docs/agent_factory/README.md` + `OVERVIEW.md`.
- Confirm the root `ACTIVE_CAMPAIGN.md` points to this campaign and no campaign-local pointer exists.
### Non-Goals
- No agent_factory code. No agent instantiation. No data access.
### Expected Files / Directories
- `campaigns/ALPHA_AGENT_FACTORY_MVP/**`
- `docs/agent_factory/README.md`, `docs/agent_factory/OVERVIEW.md`
- `handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P00.md` (commit-eligible handoff)
- `reviews/ALPHA_AGENT_FACTORY_MVP/AGENT-P00/**`
### Forbidden Changes
Out-of-scope domains, all data/heavy-artifact paths, the consumed primitive packages (`runtime/**`, `governance/**`, `experiments/**`, `backtest/**`, `research/**`, `features/**`, `labels/**`, `data/**`, `cli/**`), and `ACTIVE_CAMPAIGN.md`. The full `forbidden_paths` list is in `campaign.yaml`.
### Validation Commands
```bash
git status --short
test -f ACTIVE_CAMPAIGN.md
test -f campaigns/ALPHA_AGENT_FACTORY_MVP/GOAL.md
test -f campaigns/ALPHA_AGENT_FACTORY_MVP/PHASE_PLAN.md
test -f campaigns/ALPHA_AGENT_FACTORY_MVP/campaign.yaml
test -f campaigns/ALPHA_AGENT_FACTORY_MVP/ACCEPTANCE.md
test -f campaigns/ALPHA_AGENT_FACTORY_MVP/RISK_REGISTER.md
test -f campaigns/ALPHA_AGENT_FACTORY_MVP/RUNBOOK.md
test '!' -f campaigns/ALPHA_AGENT_FACTORY_MVP/ACTIVE_CAMPAIGN.md
test -f handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P00.md
grep -q "ALPHA_AGENT_FACTORY_MVP" ACTIVE_CAMPAIGN.md
python tools/verify.py --smoke
git ls-files runs
```
### Artifact Policy
Commit only: campaign control + overview docs; commit-eligible handoff. Explicit staging only. Never commit raw/canonical/feature/label/runtime/agent values, heavy artifacts, provider responses, local DBs, logs, caches, or `runs/**`.
### Done Criteria
- All six campaign files present and `campaign.yaml` parses.
- No `campaigns/ALPHA_AGENT_FACTORY_MVP/ACTIVE_CAMPAIGN.md` exists.
- Bootstrap handoff present; artifact audit clean.
### Handoff Requirements
Write `handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P00.md` with the exact staged file list, `git status --short`, commands run with results, checks, artifact-audit confirmation, and any caveats.
### Review Requirements
GREEN: Claude review optional unless the phase requires it; checks + handoff + artifact audit still required.
### Auto-Merge Eligibility
Eligible when checks pass, handoff valid, artifact policy passes, no forbidden paths staged, and no STOP file.

## AGENT-P01 — Agent Factory Entry Contract and Preflight Gates

### Phase ID
`AGENT-P01`
### Phase Name
Agent Factory Entry Contract and Preflight Gates
### Lane
YELLOW
### Dependencies
AGENT-P00
### DAG Scheduling
- `parallel_safe`: `false`; `must_run_alone`: `true`; `merge_group`: `foundation`
### Purpose
Establish the single sanctioned Agent Factory entry contract that encodes the four preflight gates and fails closed on missing prerequisites.
### Scope
- `agent_factory.entry_contract` with an `AgentFactoryPreflight` that checks: a real seed FeaturePack/LabelPack exists (via the registries under `ALPHA_DATA_ROOT`); the runtime real smoke PASSED (`real_dataset_version_smoke_ran`); `FEATURE_LABEL_PARQUET_SINK_V1` status; `SESSION_LABEL_GUARD_FIX_V1` status.
- Returns a structured `PREFLIGHT_PASS` / `PREFLIGHT_WARN` / `PREFLIGHT_BLOCKED` result; degrades to a truthful warning (not a hard crash) when local registries are absent (clean checkout / CI).
### Non-Goals
- No role/permission/tool/queue logic. No autonomous agent. No data materialization.
### Expected Files / Directories
- `src/alpha_system/agent_factory/__init__.py`, `src/alpha_system/agent_factory/entry_contract.py`
- `tests/unit/agent_factory/__init__.py`, `tests/unit/agent_factory/test_entry_contract.py`
- `docs/agent_factory/PREFLIGHT_GATES.md`, `configs/agent_factory/**`
- handoff + reviews
### Forbidden Changes
All consumed primitive packages and data/heavy/db paths (see `campaign.yaml` `forbidden_paths`).
### Validation Commands
```bash
git status --short
python -c "import alpha_system.agent_factory.entry_contract"
python tools/verify.py --smoke
python -m pytest tests/unit/agent_factory -q
test -f docs/agent_factory/PREFLIGHT_GATES.md
git ls-files runs
```
### Artifact Policy
Commit only: entry contract + preflight gates, tests, docs, configs. Explicit staging only.
### Done Criteria
- `entry_contract` imports and exposes the four preflight gate checks; fail-closed; unit tests pass on synthetic fixtures.
- `docs/agent_factory/PREFLIGHT_GATES.md` documents each gate and its blocker semantics.
### Handoff Requirements
Standard handoff with staged file list, checks, artifact audit, caveats.
### Review Requirements
YELLOW: fresh Claude Opus 4.8 xhigh review + `verdict.json` ∈ {PASS, PASS_WITH_WARNINGS}.
### Auto-Merge Eligibility
Eligible after review PASS/PASS_WITH_WARNINGS through the serial merge queue.

## AGENT-P02 — Agent Factory Package, Docs, and Template Skeleton and Naming

### Phase ID
`AGENT-P02`
### Phase Name
Agent Factory Package, Docs, and Template Skeleton and Naming
### Lane
YELLOW
### Dependencies
AGENT-P01
### DAG Scheduling
- `parallel_safe`: `false`; `must_run_alone`: `true`; `merge_group`: `foundation`
### Purpose
Create the importable `agent_factory` package skeleton (subpackages), the docs naming conventions, and the templates root so later disjoint phases can add files without touching shared modules.
### Scope
- Skeleton subpackages with `__init__.py`: `roles/`, `permissions/`, `tools/`, `queue/`, `separation/`, `records/`, `memory/`, `dry_run/`.
- `docs/agent_factory/NAMING.md` (naming conventions, source-of-truth index policy) and `templates/agent_factory/README.md`.
### Non-Goals
- No role/permission/tool logic yet. No autonomous agent.
### Expected Files / Directories
- `src/alpha_system/agent_factory/**` (skeleton `__init__.py` files)
- `tests/unit/agent_factory/**`
- `docs/agent_factory/NAMING.md`, `templates/agent_factory/README.md`, `configs/agent_factory/**`
- handoff + reviews
### Forbidden Changes
Consumed primitives, data/heavy/db paths, `ACTIVE_CAMPAIGN.md`.
### Validation Commands
```bash
git status --short
python -c "import alpha_system.agent_factory"
python tools/verify.py --smoke
python -m pytest tests/unit/agent_factory -q
test -f docs/agent_factory/NAMING.md
test -f templates/agent_factory/README.md
git ls-files runs
```
### Artifact Policy
Commit only: package skeleton, naming conventions, tests, docs. Explicit staging only.
### Done Criteria
- `import alpha_system.agent_factory` and each subpackage import succeed; conformance test for subpackage `__all__`/exports passes.
- Naming + index conventions documented.
### Handoff Requirements
Standard handoff.
### Review Requirements
YELLOW: fresh Claude review + verdict.
### Auto-Merge Eligibility
Eligible after review PASS/PASS_WITH_WARNINGS.

## AGENT-P03 — Agent Role Contract Model

### Phase ID
`AGENT-P03`
### Phase Name
Agent Role Contract Model
### Lane
YELLOW
### Dependencies
AGENT-P02
### DAG Scheduling
- `parallel_safe`: `false`; `must_run_alone`: `true`; `merge_group`: `foundation`
### Purpose
Define the `AgentRole` contract model and a discovery-based role registry so the parallel role phases can each add a role file without editing shared modules.
### Scope
- `roles/contracts.py` (`AgentRole` dataclass: purpose, readable inputs, callable tools, producible outputs, allowed/forbidden decisions, handoff format, reviewer-independence rules, failure modes) and `roles/registry.py` (registration/discovery; no hard per-role imports in `roles/__init__.py`).
### Non-Goals
- No concrete roles. No permission matrix. No autonomous agent.
### Expected Files / Directories
- `src/alpha_system/agent_factory/roles/__init__.py`, `roles/contracts.py`, `roles/registry.py`
- `tests/unit/agent_factory/roles/__init__.py`, `roles/test_contracts.py`, `roles/test_registry.py`
- `docs/agent_factory/ROLES.md`
- handoff + reviews
### Forbidden Changes
Consumed primitives, data/heavy/db paths.
### Validation Commands
```bash
git status --short
python -c "import alpha_system.agent_factory.roles.contracts, alpha_system.agent_factory.roles.registry"
python tools/verify.py --smoke
python -m pytest tests/unit/agent_factory/roles -q
test -f docs/agent_factory/ROLES.md
git ls-files runs
```
### Artifact Policy
Commit only: AgentRole contract model + registry, tests, docs. Explicit staging only.
### Done Criteria
- Role model + registry import and round-trip; registry supports discovery without importing concrete roles; `ROLES.md` documents the model.
### Handoff Requirements
Standard handoff.
### Review Requirements
YELLOW: fresh Claude review + verdict.
### Auto-Merge Eligibility
Eligible after review PASS/PASS_WITH_WARNINGS.

## AGENT-P04 — Agent Permission Matrix and Tool Access Policy

### Phase ID
`AGENT-P04`
### Phase Name
Agent Permission Matrix and Tool Access Policy
### Lane
YELLOW
### Dependencies
AGENT-P03
### DAG Scheduling
- `parallel_safe`: `false`; `must_run_alone`: `true`; `merge_group`: `foundation`
### Purpose
Define the strict, fail-closed permission model and the role→permission matrix.
### Scope
- `permissions/model.py` (`ToolPermission`, `DataPermission`, `WritePermission`, `ReviewPermission`, `PromotionPermission`, `HumanApprovalRequired`, `RedLaneRequired`) and `permissions/matrix.py` (default-deny matrix data covering every roster role).
### Non-Goals
- No concrete role logic. No autonomous agent.
### Expected Files / Directories
- `src/alpha_system/agent_factory/permissions/__init__.py`, `permissions/model.py`, `permissions/matrix.py`
- `tests/unit/agent_factory/permissions/__init__.py`, `permissions/test_model.py`, `permissions/test_matrix.py`
- `docs/agent_factory/PERMISSIONS.md`, `configs/agent_factory/permissions/**`
- handoff + reviews
### Forbidden Changes
Consumed primitives, data/heavy/db paths.
### Validation Commands
```bash
git status --short
python -c "import alpha_system.agent_factory.permissions.model, alpha_system.agent_factory.permissions.matrix"
python tools/verify.py --smoke
python -m pytest tests/unit/agent_factory/permissions -q
test -f docs/agent_factory/PERMISSIONS.md
git ls-files runs
```
### Artifact Policy
Commit only: permission matrix model + fail-closed matrix data, tests, docs, configs. Explicit staging only.
### Done Criteria
- Default-deny permission model; every roster role has explicit entries; tests assert no-raw-data, no-direct-registry-write, and human-approval/red-lane flags; `PERMISSIONS.md` documents the matrix.
### Handoff Requirements
Standard handoff.
### Review Requirements
YELLOW: fresh Claude review + verdict.
### Auto-Merge Eligibility
Eligible after review PASS/PASS_WITH_WARNINGS.

## AGENT-P05 — Tool Contract Registry and Structured Outputs

### Phase ID
`AGENT-P05`
### Phase Name
Tool Contract Registry and Structured Outputs
### Lane
YELLOW
### Dependencies
AGENT-P04
### DAG Scheduling
- `parallel_safe`: `false`; `must_run_alone`: `true`; `merge_group`: `foundation`
### Purpose
Define the agent-facing tool contract registry and the structured, value-free tool-result output type that all tools must return.
### Scope
- `tools/contracts.py` (tool contract: allowed callers, required inputs, output schema, forbidden side effects, local-only artifact policy, failure states, required reviewer, MVP/target/future flag), `tools/registry.py` (allowed-tool registry; default-deny), `tools/results.py` (`AgentToolResult` with the structured fields: status, role, request_id, alpha_spec_id, study_spec_id, dataset_version_id, feature_pack_refs, label_pack_refs, runtime_run_id, diagnostics_summary, cost_summary, rejection_reasons, blocking_findings, next_required_gate, artifacts, limitations).
### Non-Goals
- No tool *implementations* that execute the runtime (the bridge in AGENT-P21 does that); no autonomous agent; no raw data in any result.
### Expected Files / Directories
- `src/alpha_system/agent_factory/tools/__init__.py`, `tools/contracts.py`, `tools/registry.py`, `tools/results.py`
- `tests/unit/agent_factory/tools/__init__.py`, `tools/test_contracts.py`, `tools/test_registry.py`, `tools/test_results.py`
- `docs/agent_factory/TOOLS.md`, `configs/agent_factory/tools/**`
- handoff + reviews
### Forbidden Changes
Consumed primitives, data/heavy/db paths.
### Validation Commands
```bash
git status --short
python -c "import alpha_system.agent_factory.tools.contracts, alpha_system.agent_factory.tools.registry, alpha_system.agent_factory.tools.results"
python tools/verify.py --smoke
python -m pytest tests/unit/agent_factory/tools -q
test -f docs/agent_factory/TOOLS.md
git ls-files runs
```
### Artifact Policy
Commit only: tool contract registry + structured value-free outputs, tests, docs, configs. Explicit staging only.
### Done Criteria
- All candidate tool groups (registry/feature_label/runtime/review/ledger_memory_promotion) are described with allowed callers, inputs, output schema, side effects, MVP/target/future status; `AgentToolResult` rejects raw/heavy payloads; `TOOLS.md` documents the registry.
### Handoff Requirements
Standard handoff.
### Review Requirements
YELLOW: fresh Claude review + verdict.
### Auto-Merge Eligibility
Eligible after review PASS/PASS_WITH_WARNINGS.

## AGENT-P06 — Research Queue and Work Item Contracts

### Phase ID
`AGENT-P06`
### Phase Name
Research Queue and Work Item Contracts
### Lane
YELLOW
### Dependencies
AGENT-P05
### DAG Scheduling
- `parallel_safe`: `false`; `must_run_alone`: `true`; `merge_group`: `foundation`
### Purpose
Define the bounded research-queue objects that scope agent work without becoming a continuous autonomous runner.
### Scope
- `queue/models.py`: `ResearchQueue`, `ResearchTask`, `AgentAssignment`, `ResearchBudget`, `VariantBudget`, `ComputeBudget`, `ReviewRequirement`, `BlockerRecord`, `QueuePriorityPolicy`, `FamilyBudgetPolicy` (task status, allowed alpha family, allowed DatasetVersion/FeaturePack/LabelPack, allowed/blocked partitions, max variants, max runtime budget, required reviews, retry policy, rejection reason, next action).
### Non-Goals
- No continuous daily/weekly loop (that is `ALPHA_AGENT_RESEARCH_RUNNER_V1`); no autonomous agent.
### Expected Files / Directories
- `src/alpha_system/agent_factory/queue/__init__.py`, `queue/models.py`
- `tests/unit/agent_factory/queue/__init__.py`, `queue/test_models.py`
- `docs/agent_factory/RESEARCH_QUEUE.md`, `templates/agent_factory/research_task.template.yaml`
- handoff + reviews
### Forbidden Changes
Consumed primitives, data/heavy/db paths.
### Validation Commands
```bash
git status --short
python -c "import alpha_system.agent_factory.queue.models"
python tools/verify.py --smoke
python -m pytest tests/unit/agent_factory/queue -q
test -f docs/agent_factory/RESEARCH_QUEUE.md
git ls-files runs
```
### Artifact Policy
Commit only: research-queue/work-item contracts, tests, docs, template. Explicit staging only.
### Done Criteria
- Queue/work-item contracts import and validate; budgets bound variants/runtime; a task carries allowed/blocked partitions and required reviews; the contract is single-task-bounded (no continuous runner); `RESEARCH_QUEUE.md` documents the schema.
### Handoff Requirements
Standard handoff.
### Review Requirements
YELLOW: fresh Claude review + verdict.
### Auto-Merge Eligibility
Eligible after review PASS/PASS_WITH_WARNINGS.

## Agent Role Phases (AGENT-P07 … AGENT-P15) — Common Contract

The nine role phases below are the **parallel role-contract wave**. Each:

- depends only on `AGENT-P06`; `parallel_safe: true`; `must_run_alone: false`; `merge_group: agent_roles`.
- writes only its **own disjoint files** (role module, test, doc, prompt template) and **does not edit** `roles/__init__.py` or `roles/registry.py`; the role self-registers via the AGENT-P03 registry.
- omits `runs/**` from `allowed_paths` (parallel-safe).
- defines the role contract with: **purpose**, **readable inputs**, **callable tools**, **producible outputs**, **allowed decisions**, **forbidden decisions/actions**, **required handoff format**, **reviewer-independence rules**, and **expected failure/rejection modes**.
- forbids the same consumed-primitive and data/heavy/db paths (`campaign.yaml` `forbidden_paths`).
- Validation pattern: `git status --short`; `python -c "import alpha_system.agent_factory.roles.<role>"`; `python tools/verify.py --smoke`; `python -m pytest tests/unit/agent_factory/roles/test_<role>.py -q`; `test -f docs/agent_factory/roles/<role>.md`; `git ls-files runs`.
- YELLOW review + verdict required; auto-merge through the serial merge queue.

### AGENT-P07 — Research Director Role Contract
Purpose: scope a single bounded `ResearchTask`, assign roles, set budgets within queue policy. May decide task scope/budget; may **not** approve its own scoping as evidence, promote, issue review verdicts, or start alpha search. Files: `roles/research_director.py`, `tests/unit/agent_factory/roles/test_research_director.py`, `docs/agent_factory/roles/research_director.md`, `templates/agent_factory/roles/research_director.md`.

### AGENT-P08 — Hypothesis Scout Role Contract
Purpose: draft 3–5 `AlphaSpec` drafts for a scoped task, consulting rejected-idea + library summaries. May decide draft content; may **not** approve its own AlphaSpec, implement code, run diagnostics, or promote. Files: `roles/hypothesis_scout.py` (+ test, doc, prompt template).

### AGENT-P09 — AlphaSpec Critic Role Contract
Purpose: critique / reject / request revision on AlphaSpec drafts, independent of the drafter. May decide reject/request-revision; may **not** implement, promote, or draft the spec it reviews. Files: `roles/alpha_spec_critic.py` (+ test, doc, prompt template).

### AGENT-P10 — Data Contract Auditor Role Contract
Purpose: verify seed DatasetVersion/FeaturePack/LabelPack availability and admissibility via registry tools (`resolve_dataset_version`). May decide inputs available/blocked; may **not** access raw provider data, write registries, or bypass accepted-DatasetVersion policy. Files: `roles/data_contract_auditor.py` (+ test, doc, prompt template).

### AGENT-P11 — Feature Engineer and Label Engineer Role Contracts
Purpose: reference approved seed features/labels or draft a bounded `FeatureRequest` / `LabelSpec`; never materialize broadly. May decide bounded reference/request/spec; may **not** self-review, run promotion, perform large-scale materialization, commit values, or use label-as-feature. Files: `roles/feature_engineer.py`, `roles/label_engineer.py` (+ two tests, two docs, two prompt templates). This phase owns **two** disjoint role files.

### AGENT-P12 — No-Lookahead Auditor Role Contract
Purpose: audit runtime outputs for `available_ts`/`label_available_ts`/same-bar-fill/locked-test discipline via `runtime.audit.no_lookahead` + `governance.label_leakage_guard`. May decide lookahead PASS/BLOCKED; may **not** promote or weaken the guard. Files: `roles/no_lookahead_auditor.py` (+ test, doc, prompt template).

### AGENT-P13 — Diagnostics Runner Role Contract
Purpose: invoke the Research Runtime (`RuntimeToolResult`/`RuntimeRunSummary`, `alpha runtime`) for a bound `StudySpec`. May decide to request diagnostics within budget; may **not** promote, alter feature/label/alpha/study specs, or bypass the runtime. Files: `roles/diagnostics_runner.py` (+ test, doc, prompt template).

### AGENT-P14 — Statistical Reviewer Role Contract
Purpose: issue an independent PASS/REJECT/WATCH/INCONCLUSIVE review on runtime evidence. May decide the verdict; may **not** implement or be the implementer it reviews. Files: `roles/statistical_reviewer.py` (+ test, doc, prompt template).

### AGENT-P15 — Librarian and Memory Update Role Contract
Purpose: record agent decisions, rejected ideas, and proposed memory updates **after** a reviewer verdict. May decide to propose memory records; may **not** promote without PromotionGate or write a registry without a reviewer verdict. Files: `roles/librarian.py` (+ test, doc, prompt template).

## AGENT-P16 — Separation-of-Duties and No-Self-Review Enforcement

### Phase ID
`AGENT-P16`
### Phase Name
Separation-of-Duties and No-Self-Review Enforcement
### Lane
YELLOW
### Dependencies
AGENT-P07, AGENT-P08, AGENT-P09, AGENT-P10, AGENT-P11, AGENT-P12, AGENT-P13, AGENT-P14, AGENT-P15
### DAG Scheduling
- `parallel_safe`: `false`; `must_run_alone`: `true`; `merge_group`: `integration`
### Purpose
Assemble all role contracts into the registry/permission matrix and enforce separation of duties in code, fail-closed.
### Scope
- `separation/enforcement.py` (generator≠approver, implementer≠reviewer, runner≠promoter, reviewer≠implementer, librarian needs a verdict) and `separation/wiring.py` (assembles the role registry + permission matrix; the only module that imports all roles).
### Non-Goals
- No autonomous agent. No new role logic.
### Expected Files / Directories
- `src/alpha_system/agent_factory/separation/__init__.py`, `separation/enforcement.py`, `separation/wiring.py`
- `tests/unit/agent_factory/separation/__init__.py`, `separation/test_enforcement.py`, `separation/test_wiring.py`
- `docs/agent_factory/SEPARATION_OF_DUTIES.md`
- handoff + reviews
### Forbidden Changes
Consumed primitives, data/heavy/db paths; does not edit the role modules themselves.
### Validation Commands
```bash
git status --short
python -c "import alpha_system.agent_factory.separation.enforcement, alpha_system.agent_factory.separation.wiring"
python tools/verify.py --smoke
python -m pytest tests/unit/agent_factory/separation -q
test -f docs/agent_factory/SEPARATION_OF_DUTIES.md
git ls-files runs
```
### Artifact Policy
Commit only: separation enforcement + wiring, tests, docs. Explicit staging only.
### Done Criteria
- Wiring registers all ten roles; enforcement tests prove each separation rule fails closed; `SEPARATION_OF_DUTIES.md` documents the rules.
### Handoff Requirements
Standard handoff.
### Review Requirements
YELLOW: fresh Claude review + verdict.
### Auto-Merge Eligibility
Eligible after review PASS/PASS_WITH_WARNINGS.

## AGENT-P17 — Agent Handoff and Tool Invocation Records

### Phase ID
`AGENT-P17`
### Phase Name
Agent Handoff and Tool Invocation Records
### Lane
YELLOW
### Dependencies
AGENT-P16
### DAG Scheduling
- `parallel_safe`: `false`; `must_run_alone`: `true`; `merge_group`: `integration`
### Purpose
Define the durable record contracts that log what each agent did, linking decisions to tools and specs.
### Scope
- `records/models.py`: `AgentRunRecord`, `AgentDecisionRecord`, `AgentHandoff`, `ToolInvocationRecord`, `AgentAuditLog`, `AgentPromptVersion`, `AgentRoleVersion`, `AgentPermissionVersion`.
### Non-Goals
- No autonomous agent; no registry writes; records are value-free contracts.
### Expected Files / Directories
- `src/alpha_system/agent_factory/records/__init__.py`, `records/models.py`
- `tests/unit/agent_factory/records/__init__.py`, `records/test_models.py`
- `docs/agent_factory/HANDOFFS.md`, `templates/agent_factory/agent_handoff.template.md`
- handoff + reviews
### Forbidden Changes
Consumed primitives, data/heavy/db paths.
### Validation Commands
```bash
git status --short
python -c "import alpha_system.agent_factory.records.models"
python tools/verify.py --smoke
python -m pytest tests/unit/agent_factory/records -q
test -f docs/agent_factory/HANDOFFS.md
git ls-files runs
```
### Artifact Policy
Commit only: record contracts, tests, docs, handoff template. Explicit staging only.
### Done Criteria
- Record contracts import and validate; an `AgentHandoff` links decision → tool invocation → spec ids; version records support prompt/role/permission versioning; `HANDOFFS.md` documents them.
### Handoff Requirements
Standard handoff.
### Review Requirements
YELLOW: fresh Claude review + verdict.
### Auto-Merge Eligibility
Eligible after review PASS/PASS_WITH_WARNINGS.

## AGENT-P18 — Rejected-Idea Memory and Research Memory

### Phase ID
`AGENT-P18`
### Phase Name
Rejected-Idea Memory and Research Memory
### Lane
YELLOW
### Dependencies
AGENT-P17
### DAG Scheduling
- `parallel_safe`: `false`; `must_run_alone`: `true`; `merge_group`: `integration`
### Purpose
Define rejected-idea + research memory contracts that keep failures visible and prevent duplicate idea churn, consuming the governance graveyard.
### Scope
- `memory/models.py`: `RejectedIdeaMemoryRecord`, `ResearchMemoryRecord` (consume `governance.rejected_idea` / `ResearchGraveyardLedger`); duplicate-idea avoidance; prior-rejection-reason surfacing; linking agent decisions to tools and specs.
### Non-Goals
- No full FactorLibrary / AlphaBook (later campaigns); no registry writes; no promotion.
### Expected Files / Directories
- `src/alpha_system/agent_factory/memory/__init__.py`, `memory/models.py`
- `tests/unit/agent_factory/memory/__init__.py`, `memory/test_models.py`
- `docs/agent_factory/REJECTION_MEMORY.md`
- handoff + reviews
### Forbidden Changes
Consumed primitives (including `governance/**`, which is imported not edited), data/heavy/db paths.
### Validation Commands
```bash
git status --short
python -c "import alpha_system.agent_factory.memory.models"
python tools/verify.py --smoke
python -m pytest tests/unit/agent_factory/memory -q
test -f docs/agent_factory/REJECTION_MEMORY.md
git ls-files runs
```
### Artifact Policy
Commit only: memory contracts, tests, docs. Explicit staging only.
### Done Criteria
- Memory contracts import and validate; duplicate detection works on synthetic fixtures; prior rejection reasons are surfaced; the contract consumes (does not duplicate) the governance graveyard; `REJECTION_MEMORY.md` documents the model.
### Handoff Requirements
Standard handoff.
### Review Requirements
YELLOW: fresh Claude review + verdict.
### Auto-Merge Eligibility
Eligible after review PASS/PASS_WITH_WARNINGS.

## AGENT-P19 — Agent Prompt and Skill Assets

### Phase ID
`AGENT-P19`
### Phase Name
Agent Prompt and Skill Assets
### Lane
YELLOW
### Dependencies
AGENT-P18
### DAG Scheduling
- `parallel_safe`: `true`; `must_run_alone`: `false`; `merge_group`: `assets`
### Purpose
Provide durable, indexed agent prompt / skill templates with a single source-of-truth index, so prompts are not scattered.
### Scope
- `templates/agent_factory/prompts/**` (per-role operating prompt templates) and `templates/agent_factory/prompts/README.md` (source-of-truth index).
### Non-Goals
- No live Claude Code subagent registration (prompts are templates, not `.claude/agents/` entries); no autonomous agent.
### Expected Files / Directories
- `templates/agent_factory/prompts/**` (including `README.md`)
- handoff + reviews
### Forbidden Changes
Consumed primitives, data/heavy/db paths; disjoint from `docs/agent_factory/**` (owned by AGENT-P20 in the same wave) and `src/**` (AGENT-P21).
### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
test -f templates/agent_factory/prompts/README.md
test -d templates/agent_factory/prompts
git ls-files runs
```
### Artifact Policy
Commit only: indexed prompt/skill templates. Explicit staging only.
### Done Criteria
- Prompt templates exist for the roster with a `README.md` index; no scattered unindexed prompts elsewhere.
### Handoff Requirements
Standard handoff.
### Review Requirements
YELLOW: fresh Claude review + verdict.
### Auto-Merge Eligibility
Eligible after review PASS/PASS_WITH_WARNINGS.

## AGENT-P20 — Agent Factory Docs and Operator Guide

### Phase ID
`AGENT-P20`
### Phase Name
Agent Factory Docs and Operator Guide
### Lane
YELLOW
### Dependencies
AGENT-P18
### DAG Scheduling
- `parallel_safe`: `true`; `must_run_alone`: `false`; `merge_group`: `assets`
### Purpose
Write the Agent Factory operator guide and the Core-Alpha-Pilot readiness doc.
### Scope
- `docs/agent_factory/GUIDE.md` (how the contracts fit together), `docs/agent_factory/OPERATOR.md` (operating the dry-run + interpreting structured tool results), `docs/agent_factory/NEXT_CORE_ALPHA_PILOT_READINESS.md` (what `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` needs).
### Non-Goals
- No code; disjoint from AGENT-P19 (templates) and AGENT-P21 (src + `RUNTIME_BRIDGE.md`).
### Expected Files / Directories
- `docs/agent_factory/GUIDE.md`, `docs/agent_factory/OPERATOR.md`, `docs/agent_factory/NEXT_CORE_ALPHA_PILOT_READINESS.md`
- handoff + reviews
### Forbidden Changes
Consumed primitives, data/heavy/db paths; does not touch the specific docs files owned by other waves' phases.
### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
test -f docs/agent_factory/GUIDE.md
test -f docs/agent_factory/OPERATOR.md
test -f docs/agent_factory/NEXT_CORE_ALPHA_PILOT_READINESS.md
git ls-files runs
```
### Artifact Policy
Commit only: operator guide + readiness doc. Explicit staging only.
### Done Criteria
- Guide, operator doc, and readiness doc present; no-claims language; readiness doc names the remaining preflight blockers.
### Handoff Requirements
Standard handoff.
### Review Requirements
YELLOW: fresh Claude review + verdict.
### Auto-Merge Eligibility
Eligible after review PASS/PASS_WITH_WARNINGS.

## AGENT-P21 — Runtime Tool Integration Bridge

### Phase ID
`AGENT-P21`
### Phase Name
Runtime Tool Integration Bridge
### Lane
YELLOW
### Dependencies
AGENT-P18
### DAG Scheduling
- `parallel_safe`: `true`; `must_run_alone`: `false`; `merge_group`: `assets`
### Purpose
Implement the single bridge that adapts runtime structured outputs into agent tool results — the only place that imports the runtime tool surface.
### Scope
- `runtime_bridge.py`: adapts `alpha_system.runtime.tool_results.RuntimeToolResult` / `RuntimeRunSummary` into the `AgentToolResult` shape; **imports** the runtime, never edits it; resolves inputs through `resolve_dataset_version`; embeds no raw/heavy data.
### Non-Goals
- No diagnostics re-implementation; no runtime edits; no autonomous agent.
### Expected Files / Directories
- `src/alpha_system/agent_factory/runtime_bridge.py`
- `tests/unit/agent_factory/test_runtime_bridge.py`
- `docs/agent_factory/RUNTIME_BRIDGE.md`
- handoff + reviews
### Forbidden Changes
`src/alpha_system/runtime/**` (consumed, never edited) and all other consumed primitives / data paths.
### Validation Commands
```bash
git status --short
python -c "import alpha_system.agent_factory.runtime_bridge"
python tools/verify.py --smoke
python -m pytest tests/unit/agent_factory/test_runtime_bridge.py -q
test -f docs/agent_factory/RUNTIME_BRIDGE.md
git ls-files runs
```
### Artifact Policy
Commit only: runtime bridge, test, docs. Explicit staging only.
### Done Criteria
- Bridge imports the runtime tool-result contracts and maps them to value-free `AgentToolResult`s; tests assert no raw/heavy data and that the runtime package is not modified; `RUNTIME_BRIDGE.md` documents the adapter.
### Handoff Requirements
Standard handoff.
### Review Requirements
YELLOW: fresh Claude review + verdict.
### Auto-Merge Eligibility
Eligible after review PASS/PASS_WITH_WARNINGS.

## AGENT-P22 — Agent Dry-Run Harness

### Phase ID
`AGENT-P22`
### Phase Name
Agent Dry-Run Harness
### Lane
YELLOW
### Dependencies
AGENT-P19, AGENT-P20, AGENT-P21
### DAG Scheduling
- `parallel_safe`: `false`; `must_run_alone`: `true`; `merge_group`: `closeout`
### Purpose
Build the bounded, non-alpha dry-run harness that routes roles → tools → runtime bridge → rejection memory on synthetic fixtures, proving the machinery (not alpha).
### Scope
- `dry_run/harness.py`: orchestrates the lifecycle (Director scopes → Scout drafts → Critic rejects/revises → Data Contract Auditor checks → Feature/Label Engineer reference a bounded input → Diagnostics Runner invokes runtime via the bridge → No-Lookahead Auditor reviews → Statistical Reviewer issues REJECT/WATCH/INCONCLUSIVE → Librarian records rejection memory). No promotion; synthetic fixtures only.
### Non-Goals
- No alpha; no real data dependency; no promotion; no autonomous loop.
### Expected Files / Directories
- `src/alpha_system/agent_factory/dry_run/__init__.py`, `dry_run/harness.py`
- `tests/unit/agent_factory/dry_run/__init__.py`, `dry_run/test_harness.py`
- `docs/agent_factory/DRY_RUN.md`
- handoff + reviews
### Forbidden Changes
Consumed primitives, data/heavy/db paths.
### Validation Commands
```bash
git status --short
python -c "import alpha_system.agent_factory.dry_run.harness"
python tools/verify.py --smoke
python -m pytest tests/unit/agent_factory/dry_run -q
test -f docs/agent_factory/DRY_RUN.md
git ls-files runs
```
### Artifact Policy
Commit only: dry-run harness, tests, docs. Explicit staging only.
### Done Criteria
- Harness runs end-to-end on synthetic fixtures; routing/permissions/handoffs/rejection-memory exercised; no promotion reachable; `DRY_RUN.md` documents the flow and explicitly states the run is not alpha evidence.
### Handoff Requirements
Standard handoff.
### Review Requirements
YELLOW: fresh Claude review + verdict.
### Auto-Merge Eligibility
Eligible after review PASS/PASS_WITH_WARNINGS.

## AGENT-P23 — Seed-Pack and Synthetic Dry Run

### Phase ID
`AGENT-P23`
### Phase Name
Seed-Pack and Synthetic Dry Run
### Lane
YELLOW
### Dependencies
AGENT-P22
### DAG Scheduling
- `parallel_safe`: `false`; `must_run_alone`: `true`; `merge_group`: `closeout`
### Purpose
Run the integration dry run over synthetic fixtures (and the local seed packs when present), recording a truthful `PASS_WITH_WARNINGS`.
### Scope
- `tests/integration/agent_factory/test_dry_run.py` (degrades to synthetic fixtures when `ALPHA_DATA_ROOT` / seed registries are absent) and `docs/agent_factory/DRY_RUN_RESULTS.md` (records the dry-run outcome with explicit limitations; seed-pack dry-run is not alpha evidence).
### Non-Goals
- No alpha claims; no promotion; no large-scale value-consuming scan.
### Expected Files / Directories
- `tests/integration/agent_factory/__init__.py`, `tests/integration/agent_factory/test_dry_run.py`
- `docs/agent_factory/DRY_RUN_RESULTS.md`
- handoff + reviews
### Forbidden Changes
Consumed primitives, data/heavy/db paths.
### Validation Commands
```bash
git status --short
python tools/verify.py --all
python -m pytest tests/integration/agent_factory -q
test -f docs/agent_factory/DRY_RUN_RESULTS.md
git ls-files runs
```
### Artifact Policy
Commit only: integration dry-run test + results doc. Explicit staging only.
### Done Criteria
- Integration dry run passes or records a truthful `PASS_WITH_WARNINGS`; results doc records the outcome with limitations and the explicit "not alpha evidence" framing; `verify.py --all` green.
### Handoff Requirements
Standard handoff.
### Review Requirements
YELLOW: fresh Claude review + verdict.
### Auto-Merge Eligibility
Eligible after review PASS/PASS_WITH_WARNINGS.

## AGENT-P24 — Workflow 2 DAG Integration and Parallel Plan

### Phase ID
`AGENT-P24`
### Phase Name
Workflow 2 DAG Integration and Parallel Plan
### Lane
YELLOW
### Dependencies
AGENT-P23
### DAG Scheduling
- `parallel_safe`: `false`; `must_run_alone`: `true`; `merge_group`: `closeout`
### Purpose
Document the Workflow 2 DAG integration and the parallel plan (waves, disjoint allowed_paths, serial merge).
### Scope
- `docs/agent_factory/WORKFLOW2_DAG.md`: the wave plan, disjointness guarantees, serial merge queue, coordinator-only `ACTIVE_CAMPAIGN.md`, and the `frontier-plan` / mock commands.
### Non-Goals
- No code; no scheduler edits.
### Expected Files / Directories
- `docs/agent_factory/WORKFLOW2_DAG.md`
- handoff + reviews
### Forbidden Changes
Consumed primitives, data/heavy/db paths; no scheduler/tooling edits.
### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
test -f docs/agent_factory/WORKFLOW2_DAG.md
git ls-files runs
```
### Artifact Policy
Commit only: Workflow 2 DAG integration doc. Explicit staging only.
### Done Criteria
- Doc records the exact waves, parallel-safe disjointness, serial merge, and coordinator-only pointer; matches `campaign.yaml` and the `frontier-plan` output.
### Handoff Requirements
Standard handoff.
### Review Requirements
YELLOW: fresh Claude review + verdict.
### Auto-Merge Eligibility
Eligible after review PASS/PASS_WITH_WARNINGS.

## AGENT-P25 — Acceptance Audit and Closeout

### Phase ID
`AGENT-P25`
### Phase Name
Acceptance Audit and Closeout
### Lane
YELLOW
### Dependencies
AGENT-P24
### DAG Scheduling
- `parallel_safe`: `false`; `must_run_alone`: `true`; `merge_group`: `closeout`
### Purpose
Run the acceptance audit + semantic done-check and write the closeout with a final verdict and Core-Alpha-Pilot readiness.
### Scope
- `campaigns/ALPHA_AGENT_FACTORY_MVP/CLOSEOUT.md` (final verdict ∈ {COMPLETE, COMPLETE_WITH_WARNINGS, BLOCKED}; per-gate status; warnings; `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` readiness) and `docs/agent_factory/ACCEPTANCE_AUDIT.md`.
### Non-Goals
- No new contracts; no autonomous agent; no alpha claim.
### Expected Files / Directories
- `campaigns/ALPHA_AGENT_FACTORY_MVP/CLOSEOUT.md`, `docs/agent_factory/ACCEPTANCE_AUDIT.md`
- handoff + reviews
### Forbidden Changes
Consumed primitives, data/heavy/db paths.
### Validation Commands
```bash
git status --short
python tools/verify.py --all
python tools/hooks/canary_runner.py
test -f campaigns/ALPHA_AGENT_FACTORY_MVP/CLOSEOUT.md
test -f docs/agent_factory/ACCEPTANCE_AUDIT.md
git ls-files runs
find data -type f ! -name README.md ! -name .gitkeep -print
find artifacts -type f -size +1M -print
```
### Artifact Policy
Commit only: acceptance audit + closeout doc. Explicit staging only.
### Done Criteria
- Acceptance audit covers every gate; semantic done-check passes or records a truthful BLOCKED; closeout records the final verdict + readiness; artifact audits empty (no data/heavy files); canaries pass.
### Handoff Requirements
Standard handoff with the final artifact audit results.
### Review Requirements
YELLOW: fresh Claude review + verdict; semantic done-check by Claude Opus.
### Auto-Merge Eligibility
Eligible after review PASS/PASS_WITH_WARNINGS through the serial merge queue.
