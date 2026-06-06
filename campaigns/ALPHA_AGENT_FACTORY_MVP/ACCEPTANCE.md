# ALPHA_AGENT_FACTORY_MVP Acceptance Criteria

## Acceptance philosophy

Acceptance for this campaign is **semantic, not mechanical**. Passing tests are necessary but
never sufficient. A phase or gate is accepted only when the Agent Factory contract layer genuinely
**fails closed** on a missing prerequisite, the boundaries genuinely **hold** (contracts only — no
autonomous agent and no continuous research runner; accepted-DatasetVersion only; no raw-provider
access; no external provider calls), the contracts genuinely **drive the existing
runtime/governance/registry primitives instead of duplicating or editing them**, separation of
duties genuinely **holds** in code (generator cannot approve, implementer cannot review,
diagnostics runner cannot promote, reviewer is not the implementer, librarian cannot write a
registry without a reviewer verdict), every agent-facing tool output is genuinely **structured and
value-free**, the preflight gates are genuinely **real** (seed packs, runtime real smoke, the two
future blockers), failed and rejected ideas stay genuinely **visible**, and no prohibited scope,
prohibited MVP state, or alpha/tradability claim is present.

This campaign builds the **controlled AI Alpha Research Team contract layer** between the
executable Research Runtime (`ALPHA_RESEARCH_RUNTIME_MVP`, 27/27 `COMPLETE_WITH_WARNINGS`) plus its
governed seed packs (`POST_RUNTIME_FEATURE_LABEL_STORAGE_AND_SEED_PACKS_V1`) and the future Core
Alpha Pilot. It defines, as **contracts only**, the agent role model, the fail-closed permission
matrix, the agent-facing tool contracts, the research queue, separation-of-duties enforcement,
agent/decision/handoff/tool-invocation/audit/version records, rejected-idea and research memory, a
single runtime tool integration bridge, and a bounded non-alpha dry-run harness — by **driving
existing primitives, never re-implementing or editing them**. It owns the *governed team that
drives the runtime*, not alpha results. It instantiates **no autonomous agent**, starts **no
continuous research runner**, conducts **no alpha search**, promotes **no factor**, validates **no
strategy**, materializes or commits **no** feature/label/runtime/agent values, calls **neither**
Databento nor IBKR, and makes **no** alpha/tradability/profitability claim.

The framing that acceptance enforces, in its own terms: **Agent Factory is not the Core Alpha
Pilot, not the Agent Research Runner (continuous autonomous loop), not a FactorLibrary, not
Strategy Reference Validation, not a Portfolio AlphaBook, and not paper/live/broker.** An agent
dry-run success is not alpha; an agent-drafted `AlphaSpec` is not implementation approval; a
runtime diagnostic PASS is not factor promotion; an `EvidenceDraft` is not a candidate; a
`ReferenceCandidateHandoff` is not Reference validation; and validated research is not paper/live
approval. Acceptance therefore explicitly rejects any outcome where `agent_factory` code reads raw
provider files or calls an external provider, where the accepted-DatasetVersion boundary is
bypassed, where the runtime input resolver or tool surface is bypassed, where a diagnostics request
is routed without a bound `AlphaSpec` and `StudySpec`, where an agent role exists without a
permission-matrix entry, where a generator approves its own spec or an implementer reviews its own
work or a diagnostics runner promotes or a reviewer is the implementer, where a librarian writes a
registry without a reviewer verdict, where any agent-facing tool result is unstructured or embeds
raw or heavy data, where a registry is written directly outside sanctioned tool APIs, where a
locked-test partition is used without governance contamination metadata, where a large-scale
value-consuming study is attempted before `FEATURE_LABEL_PARQUET_SINK_V1`, where a session-context
feature is used before `SESSION_LABEL_GUARD_FIX_V1`, where a seed-pack or synthetic dry-run is
treated as alpha evidence, where an `EvidenceDraft` is treated as a candidate, where a
`ReferenceCandidateHandoff` is treated as Reference validation, where the Agent Factory tries to
start the Core Alpha Pilot, where a failed or rejected idea is hidden, where an audit log is
omitted, where the contracts duplicate an existing primitive, where an autonomous agent is
instantiated or a continuous research runner is created, where parallel DAG metadata is unsound,
where a phase branch writes `ACTIVE_CAMPAIGN.md`, where merge escapes the serial merge queue, or
where any alpha/profitability/tradability/strategy/backtest/portfolio/paper/live/broker claim or
scope appears.

This campaign runs under **Workflow 2 with the DAG wave scheduler**: dependency-ready phase
selection, concurrent build of conflict-free parallel-safe waves in isolated worktrees, and a
**serial merge queue** that merges one PR at a time. Ralph owns the strict driver loop, STOP
checks, validation orchestration, review routing, verdict parsing, bounded repair, PR/CI/merge
gates, and run summaries. Codex owns scoped execution of the generated spec and truthful handoffs.
Claude Opus 4.8 xhigh is the fresh semantic reviewer for every YELLOW phase. ChatGPT owns strategic
framing and post-run reasoning. The IN-PRODUCT agent roster defined here is **contracts only** and
is distinct from this build-time model routing; no roster agent is instantiated.

The final verdict for the campaign is one of `COMPLETE`, `COMPLETE_WITH_WARNINGS`, or `BLOCKED`.
A truthful `BLOCKED` is acceptable and strongly preferred over a false `COMPLETE`.

## Campaign-level acceptance criteria

The campaign is accepted only when all of the following hold, every phase carries a merged `PASS`
or `PASS_WITH_WARNINGS` verdict (or a truthful `BLOCKED` is recorded), and the artifact audit is
clean:

1. The new `src/alpha_system/agent_factory/` package exists as **contracts only** — role contracts
   (`roles/`), the permission matrix (`permissions/`), tool contracts (`tools/`), the research
   queue (`queue/`), separation-of-duties enforcement (`separation/`), agent records (`records/`),
   rejected-idea / research memory (`memory/`), the runtime bridge (`runtime_bridge.py`), the
   bounded dry-run harness (`dry_run/`), and the entry contract (`entry_contract.py`). **No
   autonomous agent is instantiated and no continuous research runner is created.**
2. The Agent Factory entry contract (`alpha_system.agent_factory.entry_contract`) encodes the four
   preflight gates — a real seed `FeaturePack`/`LabelPack` exists; the runtime real smoke PASSED
   (`real_dataset_version_smoke_ran: true`); `FEATURE_LABEL_PARQUET_SINK_V1` status;
   `SESSION_LABEL_GUARD_FIX_V1` status — and **fails closed** on missing prerequisites, returning a
   structured `PREFLIGHT_PASS` / `PREFLIGHT_WARN` / `PREFLIGHT_BLOCKED` result and degrading to a
   truthful warning (not a hard crash) when the local registries under `ALPHA_DATA_ROOT` are absent
   (clean checkout / CI).
3. An `AgentRole` contract model + a discovery-based role registry, a fail-closed permission matrix
   (`ToolPermission` / `DataPermission` / `WritePermission` / `ReviewPermission` /
   `PromotionPermission` / `HumanApprovalRequired` / `RedLaneRequired`), a structured agent-facing
   tool contract registry, and the research queue / work-item contracts all exist; the permission
   model is **default-deny**.
4. All ten MVP role contracts — Research Director, Hypothesis Scout, AlphaSpec Critic, Data Contract
   Auditor, Feature Engineer, Label Engineer, No-Lookahead Auditor, Diagnostics Runner, Statistical
   Reviewer, Librarian — exist **additively in disjoint files**, each with explicit
   inputs/tools/outputs/allowed-decisions/forbidden-actions/handoff-format/reviewer-independence,
   and each **registers via the role registry without editing shared files**.
5. Separation of duties is **enforced in code** and fails closed: generator cannot approve its own
   `AlphaSpec`, implementer cannot review its own work, diagnostics runner cannot promote, reviewer
   is not the implementer, and the librarian cannot write a registry without a reviewer verdict.
6. Agent records (`AgentRunRecord` / `AgentDecisionRecord` / `AgentHandoff` /
   `ToolInvocationRecord` / `AgentAuditLog` / `AgentPromptVersion` / `AgentRoleVersion` /
   `AgentPermissionVersion`) and rejected-idea / research memory
   (`RejectedIdeaMemoryRecord` / `ResearchMemoryRecord`) exist, **consume** the governance graveyard
   (`alpha_system.governance.rejected_idea` `RejectedIdeaRecord` / `ResearchGraveyardLedger`), avoid
   duplicate ideas, and surface prior rejection reasons.
7. All agent-facing tool contracts produce **structured, value-free outputs** carrying the fields
   `status`, `role`, `request_id`, `alpha_spec_id`, `study_spec_id`, `dataset_version_id`,
   `feature_pack_refs`, `label_pack_refs`, `runtime_run_id`, `diagnostics_summary`, `cost_summary`,
   `rejection_reasons`, `blocking_findings`, `next_required_gate`, `artifacts`, and `limitations`,
   and **never embed raw or heavy data**; the allowed-tool registry is required and direct registry
   writes are forbidden.
8. The runtime bridge (`alpha_system.agent_factory.runtime_bridge`) drives
   `alpha_system.runtime.tool_results.RuntimeToolResult` / `RuntimeRunSummary` and the
   `alpha_system.cli.runtime` surface, and resolves inputs via
   `alpha_system.data.foundation.version_registry.resolve_dataset_version` (admissible states
   `{VERSIONED, READY_FOR_RESEARCH}`); it **imports** the runtime and **never edits it**; no
   `agent_factory` code reads raw provider files or calls an external provider; no consumed
   primitive (`runtime.*`, `governance.*`, `research.*`, `experiments.*`, `backtest.*`, `features.*`,
   `labels.*`, `data.foundation.*`) is edited.
9. The bounded **non-alpha dry-run** (synthetic fixtures, and seed packs when local) proves role
   routing, tool contracts, permissions, handoffs, and rejection memory end-to-end (Director scopes
   → Scout drafts `AlphaSpec` drafts → Critic rejects/revises → Data Contract Auditor checks seed
   availability via `resolve_dataset_version` → Feature/Label Engineer reference a bounded approved
   input → Diagnostics Runner invokes the runtime via the bridge → No-Lookahead Auditor reviews →
   Statistical Reviewer issues REJECT/WATCH/INCONCLUSIVE → Librarian records rejection memory) and
   records a truthful `PASS_WITH_WARNINGS`; **it does not prove alpha and reaches no promotion**.
10. The agent lifecycle the contracts enforce stops at `REFERENCE_HANDOFF_RECORDED` as the most
    advanced forward state any dry-run survivor may reach, with terminal `REJECTED` / `INCONCLUSIVE`
    / `BLOCKED`; the prohibited MVP states (`ALPHA_VALIDATED`, `FACTOR_PROMOTED`, `STRATEGY_READY`,
    `PORTFOLIO_READY`, `CANDIDATE_PROMOTED`, `LIVE_READY`, `PAPER_READY`, `PROFITABLE`, `TRADABLE`,
    `PRODUCTION_READY`, `AUTONOMOUS_RESEARCH_RUNNING`) are **unreachable** by any defined transition.
11. Large-scale value-consuming studies are **blocked until `FEATURE_LABEL_PARQUET_SINK_V1`**;
    session-context features (`rth_flag` / `eth_flag` / `session_minute`) are **blocked until
    `SESSION_LABEL_GUARD_FIX_V1`**; the dataset registry report rehydration gap is respected (agents
    use registry/runtime tools and never bypass accepted-DatasetVersion policy); seed-pack dry-run
    is never treated as research evidence; and the Agent Factory does **not** start the Core Alpha
    Pilot (`ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` is a separate, separately-authorized campaign).
12. No raw/canonical/feature/label/runtime/agent values, provider responses, heavy artifacts
    (parquet/arrow/feather/dbn/zst), or local DBs (sqlite/db/wal) are committed; `git ls-files runs`
    is empty; explicit staging is used throughout (`git add .` / `git add -A` forbidden; no force
    push). DAG metadata is correct: parallel-safe phases have disjoint `allowed_paths` and no global
    files, no phase branch writes `ACTIVE_CAMPAIGN.md` in parallel mode, and merge proceeds
    serially.
13. No alpha/profitability/tradability/strategy/paper/live/broker/production claim is introduced
    anywhere, no prohibited scope (broad alpha search, factor promotion, continuous research runner,
    strategy/backtest/portfolio as an agent product) appears, the human owns risk/capital/live
    judgment, and the closeout records a final verdict ∈ {`COMPLETE`, `COMPLETE_WITH_WARNINGS`,
    `BLOCKED`} with `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` next-campaign readiness.

All 26 phases (`AGENT-P00` … `AGENT-P25`) are complete with merged verdicts. `AGENT-P00` is GREEN
(campaign-control / docs bootstrap; Claude review optional); all other phases are YELLOW and require
fresh Claude Opus 4.8 xhigh review and auto-merge through the serial merge queue. There are **no
RED-lane phases** and **no external provider calls** in this campaign: the contract layer is
local-only and consumes accepted DatasetVersions, registered seed packs, and runtime structured
outputs through their APIs.

## Acceptance gate coverage

Acceptance is organized into the six gates defined in `campaign.yaml`; every one of the 26 phases
belongs to exactly one gate (the campaign-contract validation snippet below enforces this):

| Gate (`campaign.yaml` key) | Phases | Exit requirement (summary) |
| --- | --- | --- |
| `bootstrap_and_entry` | `AGENT-P00`, `AGENT-P01`, `AGENT-P02` | Campaign files present; no campaign-local pointer; `agent_factory` imports; entry contract encodes the four preflight gates; package/docs/template skeleton + naming present. |
| `core_contracts` | `AGENT-P03`, `AGENT-P04`, `AGENT-P05`, `AGENT-P06` | AgentRole model + registry, fail-closed permission matrix, structured tool contract registry, and research-queue/work-item contracts present; no agent instantiated. |
| `agent_roles` | `AGENT-P07`, `AGENT-P08`, `AGENT-P09`, `AGENT-P10`, `AGENT-P11`, `AGENT-P12`, `AGENT-P13`, `AGENT-P14`, `AGENT-P15` | All ten MVP role contracts additive in disjoint files, each registering via the registry; no role can self-review or self-promote. |
| `enforcement_and_records` | `AGENT-P16`, `AGENT-P17`, `AGENT-P18` | Separation-of-duties enforcement + wiring fail-closed; agent records present; rejected-idea/research memory present (consuming the governance graveyard). |
| `assets_and_bridge` | `AGENT-P19`, `AGENT-P20`, `AGENT-P21` | Indexed prompt/skill templates, operator guide + Core-Alpha-Pilot readiness, and the runtime tool bridge (consumes runtime, never edits it). |
| `dry_run_and_closeout` | `AGENT-P22`, `AGENT-P23`, `AGENT-P24`, `AGENT-P25` | Bounded non-alpha dry-run + seed-pack/synthetic integration dry run pass or record a truthful `PASS_WITH_WARNINGS`; Workflow 2 DAG integration documented; acceptance audit + done-check with a recorded final verdict and readiness. |

Each gate's `requires` block in `campaign.yaml` additionally carries the full cross-cutting checklist
(contracts-only, runtime-consumed-not-bypassed, accepted-DatasetVersion, no-raw/no-external, preflight
blockers, separation of duties, structured value-free outputs, visible failures, artifact audit,
disjoint parallel `allowed_paths`, serial merge). A gate is accepted only when every phase in it carries
a merged `PASS`/`PASS_WITH_WARNINGS` verdict (or a truthful `BLOCKED` is recorded) **and** that checklist holds.

## Entry-contract-and-preflight-level acceptance

* The entry contract (`alpha_system.agent_factory.entry_contract`, documented in
  `docs/agent_factory/PREFLIGHT_GATES.md`) defines the single sanctioned way to start an Agent
  Factory session and encodes the four preflight gates: seed `FeaturePack`/`LabelPack` exists;
  runtime real smoke PASSED (`real_dataset_version_smoke_ran`); `FEATURE_LABEL_PARQUET_SINK_V1`
  status; `SESSION_LABEL_GUARD_FIX_V1` status.
* The preflight **fails closed** on a missing prerequisite, returns a structured
  `PREFLIGHT_PASS` / `PREFLIGHT_WARN` / `PREFLIGHT_BLOCKED` result, and **degrades to a truthful
  warning** (not a hard crash) when the local registries are absent on a clean checkout / CI.
* The entry contract implies neither that any agent has run, nor that any diagnostic passed, nor
  that any alpha exists; it never opens onto raw provider data and never permits an external
  provider call.

## Role-contract-level acceptance

* The `AgentRole` contract model (`alpha_system.agent_factory.roles.contracts`) and discovery-based
  registry (`roles.registry`, documented in `docs/agent_factory/ROLES.md`) let each role declare
  purpose, readable inputs, callable tools, producible outputs, allowed decisions, forbidden
  decisions/actions, required handoff format, reviewer-independence rules, and expected
  failure/rejection modes.
* Each of the ten role modules registers **via the registry without editing `roles/__init__.py` or
  `roles/registry.py`**; the parallel role wave (`AGENT-P07`…`AGENT-P15`) writes only its own
  disjoint files (module, test, doc, prompt template).
* Each role's contract respects its forbidden actions: the Hypothesis Scout cannot approve its own
  `AlphaSpec`; the AlphaSpec Critic cannot draft the spec it reviews; the Diagnostics Runner cannot
  alter specs or bypass the runtime; the Statistical Reviewer cannot review its own implementation;
  the Librarian cannot promote without a `PromotionGate` or write a registry without a verdict.

## Permission-matrix-level acceptance

* The permission model (`alpha_system.agent_factory.permissions.model`) defines `ToolPermission`,
  `DataPermission`, `WritePermission`, `ReviewPermission`, `PromotionPermission`,
  `HumanApprovalRequired`, and `RedLaneRequired`, and the matrix (`permissions.matrix`, documented
  in `docs/agent_factory/PERMISSIONS.md`) is **default-deny / fail-closed**.
* **Every roster role has an explicit matrix entry**; a role without a permission entry is a hard
  blocker. Tests assert no-raw-data access, no-direct-registry-write, and the
  human-approval / red-lane flags.
* The matrix encodes that the human owns risk/capital/live judgment (`HumanApprovalRequired`
  respected); no permission grants raw provider access, an external provider call, or a direct
  registry write.

## Tool-contract-level acceptance

* The tool contract registry (`alpha_system.agent_factory.tools.contracts` / `tools.registry`,
  documented in `docs/agent_factory/TOOLS.md`) describes each candidate tool group (registry /
  feature_label / runtime / review / ledger_memory_promotion) with allowed callers, required
  inputs, output schema, forbidden side effects, local-only artifact policy, failure states,
  required reviewer, and MVP/target/future status; the registry is **default-deny**.
* The structured result type (`tools.results.AgentToolResult`) carries the value-free fields listed
  in campaign criterion 7 and **rejects raw or heavy payloads**; an agent-facing tool result that is
  unstructured or embeds raw/heavy data is a hard failure.
* Tools **drive** the existing runtime/governance/registry tools and never duplicate them; direct
  registry writes outside sanctioned tool APIs are forbidden.

## Data-access-level acceptance

* `agent_factory` code consumes **accepted DatasetVersions only**, via
  `alpha_system.data.foundation.version_registry.resolve_dataset_version`, admissible only in state
  `{VERSIONED, READY_FOR_RESEARCH}`, and the canonical record types `CanonicalBarRecord` /
  `CanonicalBBORecord` / `DenseGridBarRecord`.
* It is **forbidden** for any `agent_factory` code to read `.dbn` / `.zst` / parquet / arrow /
  feather / provider files directly or to call Databento or IBKR; Databento is the primary
  deep-history source, IBKR is broker-source recent-validation only, and the two are never merged.
* Locked-test partition use requires governance contamination metadata; the dataset registry report
  rehydration gap (`datasets.sqlite` persists report hashes, not full report objects) is respected;
  accepted-DatasetVersion policy is never bypassed.

## Runtime-integration-(bridge)-level acceptance

* The single runtime bridge (`alpha_system.agent_factory.runtime_bridge`, documented in
  `docs/agent_factory/RUNTIME_BRIDGE.md`) is the **only** module that imports the runtime tool
  surface; it adapts `RuntimeToolResult` / `RuntimeRunSummary` (and the `alpha runtime` CLI) into
  the value-free `AgentToolResult` shape and resolves inputs via `resolve_dataset_version`.
* The bridge **imports the runtime, never edits it** (`src/alpha_system/runtime/**` stays in
  `forbidden_paths`); it re-implements no diagnostics, cost, overfit, or no-lookahead logic; it
  embeds no raw or heavy data; and tests assert the runtime package is unmodified.
* No diagnostics request is routed without a bound `AlphaSpec` and `StudySpec`; the runtime input
  resolver and tool surface are never bypassed.

## Research-queue-level acceptance

* The research-queue contracts (`alpha_system.agent_factory.queue.models`, documented in
  `docs/agent_factory/RESEARCH_QUEUE.md`) define `ResearchQueue`, `ResearchTask`, `AgentAssignment`,
  `ResearchBudget`, `VariantBudget`, `ComputeBudget`, `ReviewRequirement`, `BlockerRecord`,
  `QueuePriorityPolicy`, and `FamilyBudgetPolicy`, scoping bounded agent work.
* A `ResearchTask` carries task status, allowed alpha family, allowed DatasetVersion / FeaturePack /
  LabelPack, allowed and blocked partitions, max variants, max runtime budget, required reviews,
  retry policy, rejection reason, and next action; budgets **bound** variants and runtime.
* The queue is **single-task-bounded** — it is **not** a continuous daily/weekly autonomous loop
  (that is `ALPHA_AGENT_RESEARCH_RUNNER_V1`).

## Separation-of-duties-level acceptance

* The enforcement module (`alpha_system.agent_factory.separation.enforcement`, documented in
  `docs/agent_factory/SEPARATION_OF_DUTIES.md`) enforces, fail-closed: generator≠approver,
  implementer≠reviewer, runner≠promoter, reviewer≠implementer, and librarian-needs-a-verdict.
* The wiring module (`separation.wiring`) is the **single** module that imports all ten roles and
  assembles the role registry + permission matrix; the role modules themselves are not edited.
* Enforcement tests prove each separation rule genuinely fails closed (a generator approving its own
  spec, an implementer reviewing its own work, a runner promoting, a reviewer-as-implementer, or a
  librarian writing a registry without a verdict are all rejected).

## Records-level acceptance

* The record contracts (`alpha_system.agent_factory.records.models`, documented in
  `docs/agent_factory/HANDOFFS.md`) define `AgentRunRecord`, `AgentDecisionRecord`, `AgentHandoff`,
  `ToolInvocationRecord`, `AgentAuditLog`, `AgentPromptVersion`, `AgentRoleVersion`, and
  `AgentPermissionVersion`.
* An `AgentHandoff` links decision → tool invocation → spec ids; the version records support
  prompt/role/permission versioning; the `AgentAuditLog` makes agent activity auditable.
* Records are **value-free contracts** — they carry summaries, statuses, ids, and refs, never raw or
  heavy data, and no registry is written from a record.

## Rejected-idea / memory-level acceptance

* The memory contracts (`alpha_system.agent_factory.memory.models`, documented in
  `docs/agent_factory/REJECTION_MEMORY.md`) define `RejectedIdeaMemoryRecord` and
  `ResearchMemoryRecord` and **consume** `governance.rejected_idea` `RejectedIdeaRecord` /
  `ResearchGraveyardLedger` (importing, not duplicating, the governance graveyard).
* Duplicate-idea avoidance works on synthetic fixtures and **prior rejection reasons are surfaced**;
  failed and rejected ideas remain visible — a hidden failed or rejected idea is a hard failure.
* This MVP introduces **no** full FactorLibrary or AlphaBook; memory proposes records only and never
  promotes or writes a registry directly.

## Dry-run-level acceptance

* The dry-run harness (`alpha_system.agent_factory.dry_run.harness`, documented in
  `docs/agent_factory/DRY_RUN.md`) routes roles → tools → runtime bridge → rejection memory on
  **synthetic fixtures**, exercising routing, permissions, handoffs, and rejection memory; **no
  promotion is reachable**.
* The integration dry run (`tests/integration/agent_factory/test_dry_run.py`, recorded in
  `docs/agent_factory/DRY_RUN_RESULTS.md`) **degrades to synthetic fixtures** when `ALPHA_DATA_ROOT`
  / seed registries are absent and records a truthful `PASS_WITH_WARNINGS` with explicit limitations.
* Every dry-run doc states explicitly that a seed-pack or synthetic dry-run is **not alpha
  evidence**, an `EvidenceDraft` is **not a candidate**, and a `ReferenceCandidateHandoff` is **not
  Reference validation**.

## DAG-scheduler-level acceptance

* `workflow2.scheduler.mode: dag_wave`, `parallel_execution: true`, `max_parallel_phases: 3`,
  `merge_queue: serial`, `update_active_campaign: coordinator_only`.
* A phase is parallel-safe **only** if it sets `parallel_safe: true`, declares **disjoint
  `allowed_paths`**, sets `must_run_alone: false`, declares no global/coordinator file, and is not
  RED. A phase that omits `parallel_safe: true` or `allowed_paths` **runs alone**.
* Parallel-safe phases are exactly the role-contract fan-out `AGENT-P07`…`AGENT-P15` (`agent_roles`
  merge group) and the assets + runtime-bridge fan-out `AGENT-P19`, `AGENT-P20`, `AGENT-P21`
  (`assets` merge group). Bootstrap and core contracts (`AGENT-P00`…`AGENT-P06`), enforcement /
  records / memory (`AGENT-P16`…`AGENT-P18`), and dry-run + closeout (`AGENT-P22`…`AGENT-P25`)
  **run alone**.
* The intended waves are: **W0** sequential `AGENT-P00`→…→`AGENT-P06`; **W1** parallel role
  contracts `AGENT-P07`, `AGENT-P08`, `AGENT-P09`, `AGENT-P10`, `AGENT-P11`, `AGENT-P12`,
  `AGENT-P13`, `AGENT-P14`, `AGENT-P15` (split into sub-waves of three at `max_parallel_phases: 3`);
  **W2** sequential `AGENT-P16`→`AGENT-P17`→`AGENT-P18`; **W3** parallel assets + bridge
  `AGENT-P19`, `AGENT-P20`, `AGENT-P21`; **W4** sequential `AGENT-P22`→`AGENT-P23`→`AGENT-P24`→
  `AGENT-P25`.
* Parallel-safe phases build concurrently in isolated worktrees but **merge serially** — one PR at a
  time. `ACTIVE_CAMPAIGN.md` is coordinator-owned and **never written by a phase branch** in
  parallel mode (no phase lists it in `allowed_paths`); parallel-safe phases omit `runs/**` from
  `allowed_paths`.
* `just frontier-plan ALPHA_AGENT_FACTORY_MVP` (read-only) and
  `just frontier-run-parallel-mock ALPHA_AGENT_FACTORY_MVP 3` are run before any live parallel run,
  and the planned waves match the intended shape.

## Artifact-policy-level acceptance

* Raw/canonical market data, feature/label values, runtime/agent values, provider responses, local
  registries/DBs, logs, caches, and heavy artifacts are **local-only** and never committed; campaign
  and docs files may describe paths but never commit data.
* `git ls-files runs` returns empty; run-local `handoff.md` / `review.md` / `verdict.json` /
  `checks.json` / `repair_attempts/` remain under `runs/**` and are never committed.
* No `*.parquet` / `*.arrow` / `*.feather` / `*.dbn` / `*.zst` / `*.sqlite` / `*.db` / `*.wal` /
  `*.log` outside documented tiny synthetic `tests/**/fixtures/**`; `find artifacts -type f -size
  +1M` returns empty.
* Commit-eligible handoffs live under `handoffs/ALPHA_AGENT_FACTORY_MVP/**` and commit-eligible
  reviews under `reviews/ALPHA_AGENT_FACTORY_MVP/**`. Explicit staging only; **no `git add .` /
  `git add -A`**; no force push. The consumed `runtime` / `governance` / `research` / `experiments`
  / `backtest` / `features` / `labels` / `data.foundation` packages are never edited.

## Review-level acceptance

* Every YELLOW phase has a **fresh Claude Opus 4.8 xhigh review** and a `verdict.json`; merged
  phases are `PASS` or `PASS_WITH_WARNINGS`. `FAIL` / `BLOCKED` / `REWORK` block merge. The GREEN
  bootstrap phase (`AGENT-P00`) may skip review.
* The reviewer is **independent**; the implementer cannot self-approve.
* Reviews verify: phase-scope compliance; that the contracts drive existing runtime/governance/
  registry primitives and do not duplicate or edit them; that **no autonomous agent is instantiated**
  and **no continuous research runner is created**; that every role has explicit
  `ToolPermission` / `DataPermission` / `WritePermission` / `ReviewPermission` / `PromotionPermission`
  entries; that separation of duties holds (generator cannot approve, implementer cannot review,
  diagnostics runner cannot promote, reviewer is not the implementer, librarian cannot write a
  registry without a verdict); that all agent-facing tool contracts produce **structured value-free
  outputs** and never embed raw/heavy data; that tools consume the runtime via
  `RuntimeToolResult` / `RuntimeRunSummary` and `resolve_dataset_version` with no raw-provider access
  and no external provider calls; that the four preflight gates are present and fail closed; that
  large-scale value-consuming studies are blocked until `FEATURE_LABEL_PARQUET_SINK_V1` and
  session-context features until `SESSION_LABEL_GUARD_FIX_V1`; that the dry-run uses synthetic
  fixtures or seed packs only and is not alpha evidence, an `EvidenceDraft` is not a candidate, and a
  `ReferenceCandidateHandoff` is not Reference validation; that failed and rejected ideas remain
  visible via `RejectedIdeaMemoryRecord` / `RejectionReasonRecord`; **DAG-metadata correctness**
  (parallel-safe phases have disjoint `allowed_paths` and no global files); serial merge queue
  respected and no phase branch writing `ACTIVE_CAMPAIGN.md`; artifact-policy compliance; no
  broker/live/paper/order-routing/account scope; no alpha/profitability/tradability claim and no
  strategy/backtest/portfolio/alpha-search/factor-promotion scope; no test weakening or gaming; and
  handoff completeness with semantic done criteria.

## Prohibited shortcuts

The campaign is **not** accepted if any of the following is true:

* `agent_factory` code reads raw Databento/IBKR provider files (`.dbn` / `.zst` / parquet / arrow /
  feather) directly;
* `agent_factory` code calls an external Databento or IBKR provider API;
* an agent input is produced by bypassing the runtime input resolver or tool surface;
* an agent role self-reviews (a generator approves its own `AlphaSpec`, an implementer reviews its
  own work, a diagnostics runner promotes, or a reviewer is the implementer);
* an agent self-promotes its own result;
* an agent writes a FeatureStore / LabelStore / DatasetVersion registry directly outside sanctioned
  tool APIs (the librarian writes a registry without a reviewer verdict + `PromotionGate`);
* a locked-test partition is used without governance contamination metadata;
* an unqualified alpha/tradability/profitability (or market-beating / production-ready / live-ready /
  broker-ready / strategy-ready) claim is introduced;
* the Agent Factory starts the Core Alpha Pilot (`ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`) instead of
  only preparing readiness;
* a seed-pack or synthetic dry-run is treated as alpha evidence;
* a large-scale value-consuming study is attempted before `FEATURE_LABEL_PARQUET_SINK_V1`;
* a session-context feature (`rth_flag` / `eth_flag` / `session_minute`) is used before
  `SESSION_LABEL_GUARD_FIX_V1`;
* a role prompt / role contract exists without a permission-matrix entry;
* a tool is documented but its outputs are unstructured or embed raw/heavy data;
* a failed or rejected idea is omitted (not recorded with a `RejectedIdeaMemoryRecord` /
  `RejectionReasonRecord`);
* an `AgentAuditLog` is omitted (no audit log of agent activity);
* raw/canonical/feature/label/runtime/agent values, heavy artifacts, provider responses, or local
  DBs are committed;
* an autonomous agent is instantiated;
* a continuous / unattended research runner is created;
* a parallel phase is marked safe without disjoint `allowed_paths`;
* a phase branch writes `ACTIVE_CAMPAIGN.md` in parallel mode;
* a merge occurs outside the serial merge queue.

## Required final validation commands

```bash
cd ~/projects/alpha_system

# Test + canary validation
python tools/verify.py --all
python tools/hooks/canary_runner.py

# YAML parse + phase-coverage validation of the campaign contract
python -c "import yaml; d=yaml.safe_load(open('campaigns/ALPHA_AGENT_FACTORY_MVP/campaign.yaml')); ids=[p['id'] for p in d['phases']]; assert ids==[f'AGENT-P{n:02d}' for n in range(26)], ids; gphases=[p for g in d['acceptance_gates'].values() for p in g['phases']]; assert sorted(gphases)==sorted(ids) and len(gphases)==len(ids), gphases; print('campaign.yaml OK:', len(ids), 'phases; every phase in exactly one gate')"

# Run-artifact audit (must be empty)
git status --short
git ls-files runs

# Data / metadata / heavy-artifact audits (must be empty outside tiny synthetic fixtures)
find data -type f ! -name README.md ! -name ".gitkeep" -print
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/*" -print
find . -name "*.arrow" -not -path "./tests/*" -print
find . -name "*.feather" -not -path "./tests/*" -print
find . -name "*.dbn" -not -path "./tests/*" -print
find . -name "*.zst" -not -path "./tests/*" -print

# DAG scheduler read-only plan + mock parallel run (no live merges)
just frontier-plan ALPHA_AGENT_FACTORY_MVP
just frontier-run-parallel-mock ALPHA_AGENT_FACTORY_MVP 3
```

## Required semantic done-check

Beyond passing tests, the final done-check (Claude Opus) must affirm that:

* the Agent Factory is **contracts only** — no autonomous agent is instantiated and no continuous
  research runner is created; the `agent_factory` package defines role/permission/tool/queue/
  separation/records/memory/dry-run contracts and a runtime bridge, nothing more;
* the contracts **drive existing primitives, not duplicate them** — `runtime.*`, `governance.*`,
  `research.*`, `experiments.*`, `backtest.*`, `features.*`, `labels.*`, and `data.foundation.*` are
  consumed by their real import paths and never edited;
* the entry contract **fails closed on a missing prerequisite** — the four preflight gates (seed
  pack, runtime real smoke PASS, `FEATURE_LABEL_PARQUET_SINK_V1` status, `SESSION_LABEL_GUARD_FIX_V1`
  status) genuinely gate the session and degrade to a truthful warning when local registries are
  absent;
* the **data boundary is real** — `agent_factory` code never reads raw provider files, makes no
  external Databento/IBKR call, and consumes only admissible DatasetVersions via
  `resolve_dataset_version`, with Databento and IBKR versions never merged and the registry
  rehydration gap respected;
* the **permission matrix is real and fail-closed** — every roster role has explicit
  `ToolPermission` / `DataPermission` / `WritePermission` / `ReviewPermission` / `PromotionPermission`
  entries under default-deny, and the human-approval / red-lane flags hold;
* **separation of duties is enforced in code** — generator≠approver, implementer≠reviewer,
  runner≠promoter, reviewer≠implementer, and librarian-needs-a-verdict all genuinely fail closed;
* **tool outputs are structured and value-free** — every `AgentToolResult` carries the required
  summary/version/status fields and rejects raw or heavy payloads, and the runtime bridge embeds no
  raw/heavy data;
* the **dry-run is not evidence** — a seed-pack or synthetic dry-run is not alpha, an `EvidenceDraft`
  is not a candidate, a `ReferenceCandidateHandoff` is not Reference validation, and no promotion is
  reachable;
* **failed and rejected ideas stay visible** — every rejection carries a `RejectedIdeaMemoryRecord`
  / `RejectionReasonRecord`, duplicate ideas are avoided, prior rejection reasons are surfaced, and
  the `AgentAuditLog` records agent activity;
* the **DAG metadata is sound** — parallel-safe phases (`AGENT-P07`…`AGENT-P15`, `AGENT-P19`…
  `AGENT-P21`) have disjoint `allowed_paths` and no global files, merge is serial, and no phase
  branch writes `ACTIVE_CAMPAIGN.md`;
* **no prohibited scope, state, or claim exists** — no broker/live/paper/order-routing/account, no
  external provider call, no broad alpha search, no factor promotion, no continuous research runner,
  no strategy/backtest/portfolio scope; the prohibited MVP states (`ALPHA_VALIDATED`,
  `FACTOR_PROMOTED`, `STRATEGY_READY`, `PORTFOLIO_READY`, `CANDIDATE_PROMOTED`, `LIVE_READY`,
  `PAPER_READY`, `PROFITABLE`, `TRADABLE`, `PRODUCTION_READY`, `AUTONOMOUS_RESEARCH_RUNNING`) are
  unreachable; and the Agent Factory does not start the Core Alpha Pilot;
* the **artifact audit is clean** (no `runs/**`, raw, canonical, feature/label value, runtime value,
  agent value, heavy, provider, or local-DB artifacts committed).

## Final closeout requirements

* `campaigns/ALPHA_AGENT_FACTORY_MVP/CLOSEOUT.md` exists and records the final verdict and any
  warnings (written by `AGENT-P25`); `docs/agent_factory/ACCEPTANCE_AUDIT.md` records the audit
  covering every acceptance gate.
* `ACTIVE_CAMPAIGN.md` reflects campaign completion and points at the next campaign or none —
  **updated by the coordinator, never by a phase branch**.
* The bounded non-alpha dry-run (`AGENT-P22`) and the seed-pack/synthetic integration dry run
  (`AGENT-P23`) are local-only, make **no external provider call**, commit only curated value-free
  summaries, and may record a truthful `PASS_WITH_WARNINGS` (with the exact operator command
  documented) when the local registry/seed packs are absent on the runner.
* Durable lessons are added to `project-skill` when applicable.
* Next-campaign readiness is recorded: the controlled AI research team contract layer is ready to be
  consumed by the future **Core Alpha Pilot** (`ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`), which may run
  *real* studies through the runtime, driven by these controlled agent contracts, only under its own
  explicitly authorized campaign and the governance + data-admissibility gates this campaign relies
  on. A dry-run success is not alpha; an agent-drafted `AlphaSpec` is not implementation approval; a
  diagnostic PASS is not factor promotion; an `EvidenceDraft` is not a candidate; a
  `ReferenceCandidateHandoff` is not Reference validation.

## Final acceptance verdicts

### `COMPLETE`
All 26 phases (`AGENT-P00` … `AGENT-P25`) carry merged `PASS` or `PASS_WITH_WARNINGS` verdicts
(`AGENT-P00` GREEN with review optional; all others YELLOW with a fresh Claude Opus 4.8 xhigh
review), all campaign-level criteria are met, the Agent Factory is genuinely contracts-only with no
autonomous agent and no continuous research runner, the entry contract fails closed on missing
prerequisites, the data boundary and runtime-consumption boundaries hold, the permission matrix and
separation of duties are enforced fail-closed, tool outputs are structured and value-free, the
dry-run proves the machinery without proving alpha, failed and rejected ideas remain visible, the
semantic done-check is clean, the artifact audit is clean, and no prohibited scope, prohibited MVP
state, or alpha/tradability claim exists.

### `COMPLETE_WITH_WARNINGS`
All hard criteria met, but non-blocking warnings (e.g. documented deferrals; an integration dry run
that recorded a truthful `PASS_WITH_WARNINGS` because the local seed packs / registries were absent
on the runner; the `FEATURE_LABEL_PARQUET_SINK_V1` and `SESSION_LABEL_GUARD_FIX_V1` future blockers
still open; or minor limitations) are recorded in `CLOSEOUT.md`.

### `BLOCKED`
A hard criterion cannot be met (e.g. the entry contract cannot be made to fail closed, the
data-access or runtime-consumption boundary cannot be guaranteed, the permission matrix or
separation of duties cannot be enforced, a tool result cannot be kept structured and value-free, the
contracts cannot be made to drive rather than duplicate a primitive, or a required contract cannot be
completed in scope). The blocker is recorded truthfully; fake completion is forbidden, and a
truthful `BLOCKED` is preferred over a false `COMPLETE`.

---

*This file is a campaign contract describing intent and boundaries for the Agent Factory MVP; it
instantiates no autonomous agent, starts no continuous research runner, and makes no alpha,
tradability, profitability, production, or live claim.*
