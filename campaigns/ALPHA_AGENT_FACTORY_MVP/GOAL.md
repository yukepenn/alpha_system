# ALPHA_AGENT_FACTORY_MVP Campaign Goal

## Campaign Identity

**ALPHA_AGENT_FACTORY_MVP — The Controlled AI Alpha Research Team Layer over Governance + Feature/Label + Research Runtime**

* **Campaign ID:** `ALPHA_AGENT_FACTORY_MVP`
* **Campaign name:** Agent Factory MVP: The Controlled AI Alpha Research Team Layer over Governance + Feature/Label + Research Runtime
* **Campaign path:** `campaigns/ALPHA_AGENT_FACTORY_MVP`
* **Repo name:** `alpha_system`
* **Repo path:** `~/projects/alpha_system`
* **Host environment:** Windows host
* **Primary runtime:** WSL2 Ubuntu
* **Required active filesystem location:** WSL2 Linux filesystem under `~/projects/alpha_system`
* **Forbidden active worktree locations:** `/mnt/c`, `/mnt/d`, `/mnt/e`, OneDrive, Dropbox, Google Drive, Windows-synced folders, network drives, temporary directories
* **Project profile:** `trading_research` / `research` / `agent_factory`
* **Campaign execution mode:** Frontier Harness Generic v3.0 Workflow 2 with the DAG wave scheduler
* **Campaign driver:** Ralph strict autonomous loop
* **Scheduler mode:** `dag_wave` (parallel build, serial merge queue)
* **Primary executor:** Codex GPT-5.5 high
* **Primary semantic reviewer:** Claude Opus 4.8 xhigh
* **Verifier / source-map / audit support:** Claude Sonnet 4.6
* **Strategic campaign reasoning:** ChatGPT Pro GPT-5.5 Thinking
* **Phase count:** 26 phases (`AGENT-P00` … `AGENT-P25`)

This campaign is **contract generation and agent-contract construction only**. It defines and
(where local-only and authorized) implements the **role contracts, permission matrix, tool
contracts, research queue, separation-of-duties enforcement, agent/decision/handoff records,
rejected-idea memory, prompt assets, a runtime tool integration bridge, and a bounded non-alpha
dry-run harness** that a controlled AI Alpha Research Team will be governed by. It does **not**
instantiate any autonomous agent, does **not** start a continuous research runner, does **not**
conduct alpha search, does **not** promote any factor, does **not** validate any strategy, does
**not** materialize or commit feature/label/runtime/agent values, does **not** call Databento or
IBKR, and does **not** pull or commit raw, canonical, feature, or label data.

One sentence captures the posture:

```text
The Agent Factory defines constrained workers, not autonomous traders;
agent dry-run success is not alpha, an agent-drafted AlphaSpec is not implementation approval,
a runtime diagnostic PASS is not factor promotion, an EvidenceDraft is not a candidate,
a ReferenceCandidateHandoff is not Reference validation, and validated research is not
paper/live approval.
```

The critical framing is stated explicitly and must hold everywhere in this campaign:

```text
Agent Factory is NOT Core Alpha Pilot.
Agent Factory is NOT the Agent Research Runner (continuous autonomous loop).
Agent Factory is NOT a Factor Library.
Agent Factory is NOT Strategy Reference Validation.
Agent Factory is NOT a Portfolio AlphaBook.
Agent Factory is NOT paper, live, or broker execution.
Agent Factory does NOT validate alpha.
It creates controlled agent roles, permissions, tool contracts, and dry-run protocols.
```

## Mission

Build the **controlled AI Alpha Research Team contract layer** — the role definitions, permission
boundaries, tool contracts, research queue, separation of duties, memory, and dry-run protocols
that let future AI Alpha Researchers operate **inside durable tool contracts and Workflow 2
gates** rather than writing ad hoc scripts that bypass the runtime, governance, or registry.

The Feature/Label Foundation built the research substrate. The Research Runtime built the
executable research loop. Seed packs and the real-data runtime smoke proved the real-data loop.
What is still missing is the **governed team of constrained workers** that drives that loop: who
may propose a hypothesis, who may draft an `AlphaSpec`, who may reject it, who may audit data
contracts, who may request diagnostics through the runtime, who may audit for lookahead, who may
issue a statistical verdict, and who may record memory — each with explicit permissions, strict
separation of duties, structured outputs, and fail-closed boundaries.

This campaign supplies exactly that missing **agent-contract layer**, by **driving existing
primitives, never duplicating them**:

* **Research Runtime** — agents call the runtime through its agent-facing structured outputs
  `alpha_system.runtime.tool_results.RuntimeToolResult` / `RuntimeRunSummary` and the
  `alpha_system.cli.runtime` surface (`plan`, `validate-inputs`, `run-diagnostics`,
  `run-label-diagnostics`, `run-signal-probe`, `run-cost-stress`, `build-evidence-draft`,
  `build-reference-handoff`, `summarize`, `inspect`, `replay-summary`). The runtime package is
  **consumed, never edited**.
* **Governance** — `alpha_system.governance.alpha_spec` (AlphaSpec), `governance.study_spec`
  (StudySpec), `governance.evidence_bundle` (EvidenceBundle), `governance.reviewer_verdict`
  (ReviewerVerdict), `governance.promotion_gate` / `governance.promotion`, `governance.rejected_idea`
  (RejectedIdeaRecord / ResearchGraveyardLedger), `governance.trial_ledger`,
  `governance.feature_request`, `governance.label_spec`, `governance.label_leakage_guard`,
  `governance.duplicate_exposure`, and `governance.study_input_pack`.
* **Registry / substrate** — `alpha_system.data.foundation.version_registry.resolve_dataset_version`
  with admissible states `{VERSIONED, READY_FOR_RESEARCH}` and canonical records
  (`CanonicalBarRecord` / `CanonicalBBORecord` / `DenseGridBarRecord`), plus the FeatureStore /
  LabelStore registries and the seed-pack operator `alpha_system.cli.seed_pack`
  (`alpha feature materialize` / `alpha label materialize --execute`).

The **new** package is `src/alpha_system/agent_factory/` (contracts and orchestration only). It
contains role contracts (`roles/`), the permission matrix (`permissions/`), tool contracts
(`tools/`), the research queue (`queue/`), separation-of-duties enforcement (`separation/`), agent
records (`records/`), rejected-idea/research memory (`memory/`), a runtime integration bridge
(`runtime_bridge.py`), and a bounded dry-run harness (`dry_run/`). Durable docs live under
`docs/agent_factory/`; reusable role-prompt and tool templates live under `templates/agent_factory/`.
These are described here as **planned** deliverables this campaign will build; they do not exist yet.

## Why This Campaign Exists

The strategic ordering of the program is precise and deliberate:

```text
ALPHA_SYSTEM_V1                made the system able to run.
ASV1_RELEASE_HYGIENE           made the V1 release baseline clean and reviewable.
ALPHA_RESEARCH_GOVERNANCE_MVP  decided what research results are allowed to be believed.
ALPHA_DATA_FOUNDATION_V1       let real market truth enter — controlled, versioned, read-only.
ALPHA_FEATURE_LABEL_FOUNDATION_V1  turned accepted DatasetVersions into a governed research substrate.
ALPHA_RESEARCH_RUNTIME_MVP     made an approved AlphaSpec + StudySpec runnable into diagnostics and evidence.
POST_RUNTIME_..._SEED_PACKS_V1 proved the real-data loop with governed seed packs + a real-data smoke.
ALPHA_AGENT_FACTORY_MVP        defines the controlled AI research team that drives that loop.
```

`alpha_system` is becoming an **AI Alpha Research Factory**, not a backtester and not a strategy
repository. The long-term north star — used here only for framing, never as a claim — is to
maximize robust out-of-sample, cost-adjusted, capacity-aware, low-correlation intraday Sharpe,
subject to drawdown, turnover, liquidity, execution, and reproducibility constraints. In that
factory:

* AI generates research throughput.
* `alpha_system` owns evidence and truth (runtime + governance + registries).
* Ralph / Workflow 2 owns process, state, gates, STOP/resume, and merge discipline.
* Claude reviews semantics and runs done-checks.
* Codex implements scoped phase specs.
* The human owns direction and risk/capital/live judgment.

Governance, a versioned data foundation, a no-lookahead-safe Feature/Label substrate, and an
executable Research Runtime all now exist. What is still missing is the **controlled team of
constrained AI workers** that can run that loop repeatedly and safely with **reduced human
interaction** — agents that operate *inside* the runtime and governance gates rather than around
them.

### Why Agent Factory must happen before Core Alpha Pilot

`ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` will run *real* studies that produce candidates a human will
judge. If the AI research team is wired up only during that pilot, the team's roles, permissions,
separation of duties, tool contracts, and memory would be improvised under pressure — exactly the
conditions that produce an **overfit machine**: agents that mine variants, self-review, self-promote,
hide failures, and manufacture convincing but false evidence. Agent Factory installs the
team's constraints **first**, on seed packs and synthetic fixtures, with no alpha at stake, so that
when the Core Alpha Pilot runs, the researchers are already constrained workers driving a governed
runtime — not an unbounded search.

### What the prior campaigns gave us — and what they intentionally did not

The prior campaigns gave us: a governance admissibility/evidence protocol; a versioned, read-only
data truth layer; a no-lookahead-safe, deduplicated, cost-aware Feature/Label substrate; an
executable, fail-closed Research Runtime with agent-facing structured outputs; governed seed
FeaturePack/LabelPack; and a real-data runtime smoke that PASSES (`real_dataset_version_smoke_ran:
true`). They intentionally did **not** give us a team: there is no agent role model, no permission
matrix, no agent-facing tool registry, no research queue, no separation-of-duties enforcement, no
agent decision/handoff/memory records, and no dry-run protocol that exercises role routing and
rejection memory. This campaign supplies exactly that — and **only** that.

### How it reduces human interaction without weakening gates

The Agent Factory does not remove a single gate. Instead it makes each gate **machine-addressable**:
agents act only through tool contracts whose outputs are structured and value-free; every role has
an explicit permission entry; separation of duties is enforced in code (generator cannot approve,
implementer cannot review, diagnostics runner cannot promote, reviewer is not the implementer,
librarian cannot write a registry without a reviewer verdict). The human's interaction shrinks to
direction and risk/capital/live judgment because the routine work — drafting specs, auditing data
contracts, requesting runtime diagnostics, auditing lookahead, issuing statistical verdicts,
recording rejection memory — happens inside durable, reviewable contracts under Workflow 2.

### How it prevents the AI from becoming an overfit machine

```text
self-review            (the drafter approving its own AlphaSpec)
self-promotion         (an implementer or runner promoting its own result)
variant mining         (unbounded grids / unlimited research budget)
duplicate churn        (re-generating already-rejected ideas)
dry-run-as-evidence    (treating a seed-pack dry-run as alpha)
runtime bypass         (computing diagnostics directly instead of via the runtime tools)
spec bypass            (running diagnostics without an AlphaSpec/StudySpec)
silent failure         (hiding failed or rejected ideas)
capital creep          (an agent making a risk/capital/live decision)
```

Each is a known way an AI research team manufactures false evidence or oversteps. The permission
matrix, separation-of-duties enforcement, structured tool outputs, research-budget/variant limits,
rejected-idea memory, and preflight gates make those failure modes **unreachable by construction**.

### How it uses the Runtime rather than bypassing it

Agents never re-implement diagnostics, cost models, overfit controls, or no-lookahead audits. The
Diagnostics Runner role invokes the Research Runtime through the `RuntimeToolResult` /
`RuntimeRunSummary` contracts (and the `alpha runtime` CLI); the No-Lookahead Auditor consumes
`alpha_system.runtime.audit.no_lookahead` and `governance.label_leakage_guard`; the Data Contract
Auditor resolves inputs through `resolve_dataset_version`. A single `runtime_bridge.py` is the only
place that adapts runtime outputs into agent tool results, and it **imports** the runtime — it never
edits it.

## Baseline from Completed Campaigns

The following campaigns are treated as **complete** and form this campaign's baseline:

* `ALPHA_SYSTEM_V1` — local-first research harness foundation.
* `ASV1_RELEASE_HYGIENE` — clean, reviewable V1 release baseline.
* `ALPHA_RESEARCH_GOVERNANCE_MVP` (COMPLETE_WITH_WARNINGS) — the admissibility/evidence protocol:
  `AlphaSpec`, `StudySpec`, `LabelSpec`, `FeatureRequest`, `EvidenceBundle`, `ReviewerVerdict`,
  the promotion gate and lifecycle, `RejectedIdeaRecord` / `ResearchGraveyardLedger`, the
  `trial_ledger`, the `label_leakage_guard`, the `duplicate_exposure` guard, and the
  `study_input_pack`, plus the hard rules *no-code-before-spec*, *no-candidate-without-evidence*,
  and *no-promotion-without-ledger*. This governance layer is **consumed, not duplicated**.
* `ALPHA_DATA_FOUNDATION_V1` (PASS_WITH_WARNINGS) — the read-only, provenance-rich, quality-gated
  data truth layer; the DatasetVersion registry; canonical records; partitions; and the sanctioned
  consumption API `resolve_dataset_version` (admissible states `{VERSIONED, READY_FOR_RESEARCH}`).
* `PRE_FEATURE_REPO_CONSOLIDATION_V1` — pre-Feature/Label repo consolidation and reconciliation.
* `WF2_PARALLEL_DAG_SCHEDULER_MVP` — the opt-in DAG wave scheduler (parallel build, serial merge)
  this campaign runs under.
* `ALPHA_FEATURE_LABEL_FOUNDATION_V1` (32/32, `COMPLETE_WITH_WARNINGS`) — the versioned,
  no-lookahead-safe, deduplicated, cost-aware FeatureStore/LabelStore research substrate.
* `ALPHA_RESEARCH_RUNTIME_MVP` (27/27, `COMPLETE_WITH_WARNINGS`) — the local-first executable
  research loop (`alpha_system.runtime`): input resolver, run/plan/record/manifest contracts,
  factor/label/split/cross-market/cost diagnostics, signal probe, bounded grid, no-lookahead audit,
  decision states + `RejectionReasonRecord`, `EvidenceDraft`, `ReferenceCandidateHandoff`, the
  `alpha runtime` CLI, and the agent-facing `RuntimeToolResult` / `RuntimeRunSummary` structured
  outputs that this campaign's agents drive.
* `POST_RUNTIME_FEATURE_LABEL_STORAGE_AND_SEED_PACKS_V1` — the storage policy (ADR-0006), the
  governed seed-pack operator (`alpha_system.cli.seed_pack`, `alpha feature|label materialize
  --execute`), the materialized + registered real Databento ES/NQ/RTY **2024** seed packs (6
  `BASE_OHLCV` features `returns` / `log_returns` / `rolling_volatility` / `rolling_range` /
  `volume_zscore` / `range_position`; labels `fwd_ret_5m` / `fwd_ret_10m` / `fwd_ret_30m`), and the
  **PASSING real-data runtime smoke** (`real_dataset_version_smoke_ran: true`).

**Dependency warnings:** if any baseline item is found not-on-`main` at run time, treat it as a
dependency warning and proceed only against the on-`main` state; the campaign contract itself is
still valid and may still be generated. The data corpus, seed-pack values, and the local registries
(`features.sqlite` / `labels.sqlite` / `datasets.sqlite` under `ALPHA_DATA_ROOT`) are **local-only**;
their absence in a clean checkout is expected and is not a contract blocker, because this campaign's
contracts drive accepted DatasetVersions and registered packs through their APIs rather than
committing the data.

## Data / Feature / Runtime Readiness Posture

The **accepted current usable seed path** that the Agent Factory dry-run may exercise is:

```text
accepted DatasetVersion (resolve_dataset_version)
  -> seed FeaturePack / LabelPack (registered, local-only)
  -> Research Runtime real smoke PASS
  -> agent-facing RuntimeToolResult / RuntimeRunSummary
```

This proves the real-data loop is closed end-to-end. It does **not** prove alpha, tradability,
profitability, a strategy, a portfolio, or paper/live readiness. Three known follow-ups constrain
the Agent Factory and are encoded as **preflight gates and future-blockers**, not as work this
campaign performs:

1. **`FEATURE_LABEL_PARQUET_SINK_V1`** (ADR-0006): feature/label values are today the JSONL
   audit/small tier; the research-scale tier is local Parquet. Per ADR-0006 this *"should land
   before any large-scale, value-consuming Agent Factory study."* Agent Factory MVP may use seed
   packs and synthetic fixtures for dry-run and may design tool contracts, but must **not** perform
   broad research requiring large feature/label scans until this lands or a human explicitly
   approves.
2. **`SESSION_LABEL_GUARD_FIX_V1`** (named follow-up, not yet a campaign dir): session-context
   features (`rth_flag` / `eth_flag` / `session_minute`) were deferred because the runtime leakage
   guard `_reject_label_as_live_feature` in `runtime/input_resolver.py` false-positives on the
   canonical point-in-time field `session_label`. This is a narrow guard over-match, not real
   leakage. Agent Factory must **not** rely on session-context features until this is fixed or
   explicitly marked available.
3. **Dataset registry report rehydration** (`docs/STRUCTURAL_BACKLOG.md`): `datasets.sqlite`
   persists quality/coverage report **hashes**, not full report objects. Agent Factory must not
   bypass accepted-DatasetVersion policy; it uses registry/runtime tools and respects this gap.

## Data / Agent Boundary Contract

* Agents consume **accepted DatasetVersions only**, never raw provider files. The sanctioned API is
  `alpha_system.data.foundation.version_registry.resolve_dataset_version(registry_path, id)`.
* A DatasetVersion is **admissible** only in state `{VERSIONED, READY_FOR_RESEARCH}`.
* It is **forbidden** for any `agent_factory` code to read `.dbn`, `.zst`, parquet, arrow, feather,
  or provider files directly, or to call Databento or IBKR. Databento is the primary deep-history
  research source; IBKR is broker-source recent-validation only; the two are never merged.
* Agents reach diagnostics **only** through the runtime tool surface; they never re-implement
  diagnostics, cost, overfit, or no-lookahead logic, and never bypass the runtime input resolver.
* No agent writes the FeatureStore / LabelStore / DatasetVersion registries directly; writes happen
  only through sanctioned tool APIs and only after the required reviewer verdict + PromotionGate.
* Raw, canonical, feature, label, runtime, and agent values are **local-only** and never committed.

## What This Campaign Builds

Across 26 Workflow 2 phases (`AGENT-P00` … `AGENT-P25`) the campaign defines and (where local-only
and authorized) implements the new `src/alpha_system/agent_factory/` contract package and its docs:

* **Bootstrap, entry contract, and core contracts** (`AGENT-P00` … `AGENT-P06`): the campaign
  control surface and `docs/agent_factory/` docs root; the Agent Factory **entry contract + preflight
  gates** (`agent_factory.entry_contract`) that check seed-pack existence, runtime real-smoke PASS,
  `FEATURE_LABEL_PARQUET_SINK_V1` status, and `SESSION_LABEL_GUARD_FIX_V1` status; the package / docs /
  template skeleton and naming; the **AgentRole contract model** + registry; the **permission matrix**
  (`ToolPermission` / `DataPermission` / `WritePermission` / `ReviewPermission` / `PromotionPermission`
  / `HumanApprovalRequired` / `RedLaneRequired`); the **tool contract registry** with structured,
  value-free outputs; and the **research queue** + work-item contracts.
* **Agent role contracts** (`AGENT-P07` … `AGENT-P15`, parallel): the ten MVP role contracts —
  Research Director, Hypothesis Scout, AlphaSpec Critic, Data Contract Auditor, Feature Engineer,
  Label Engineer, No-Lookahead Auditor, Diagnostics Runner, Statistical Reviewer, and Librarian —
  each defining purpose, readable inputs, callable tools, producible outputs, allowed and forbidden
  decisions, the required handoff format, reviewer-independence rules, and expected
  failure/rejection modes, each registering via the role registry in disjoint files.
* **Enforcement, records, and memory** (`AGENT-P16` … `AGENT-P18`): separation-of-duties / no-self-
  review enforcement and the role/permission wiring; the agent run / decision / handoff /
  tool-invocation / audit / prompt-version / role-version / permission-version records; and the
  rejected-idea + research memory (consuming `governance.rejected_idea` / `ResearchGraveyardLedger`)
  with duplicate-idea avoidance and prior-rejection surfacing.
* **Assets and runtime bridge** (`AGENT-P19` … `AGENT-P21`, parallel): the durable, indexed agent
  prompt / skill templates; the Agent Factory operator guide and Core-Alpha-Pilot readiness doc; and
  the runtime tool integration bridge that adapts `RuntimeToolResult` / `RuntimeRunSummary` into
  structured agent tool results (importing the runtime, never editing it).
* **Dry-run and closeout** (`AGENT-P22` … `AGENT-P25`): the bounded **non-alpha dry-run harness**
  (synthetic fixtures: Research Director scopes a tiny task → Hypothesis Scout drafts AlphaSpec
  drafts → AlphaSpec Critic rejects most → Data Contract Auditor checks seed availability →
  Feature/Label Engineer reference a bounded approved input → Diagnostics Runner invokes the runtime
  → No-Lookahead Auditor reviews → Statistical Reviewer issues REJECT/WATCH/INCONCLUSIVE → Librarian
  records rejection memory; **no promotion**); the seed-pack/synthetic integration dry run; the
  Workflow 2 DAG integration and parallel plan; and the acceptance audit, semantic done-check, and
  closeout with a final verdict and `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` next-campaign readiness.

## What This Campaign Does Not Build

This campaign must not implement or require any of the following:

* no autonomous agent instantiation and no continuous/unattended research runner (that is
  `ALPHA_AGENT_RESEARCH_RUNNER_V1`);
* no broad alpha discovery, factor search, hypothesis enumeration over all data, or candidate
  selection;
* no factor promotion, FactorLibrary, or promotion of any survivor into a candidate or strategy;
* no Core Alpha Pilot, Strategy Reference Validation beyond a dry-run handoff, Portfolio AlphaBook,
  strategy wrappers, or strategy/backtest/portfolio optimization as an agent product;
* no large-scale, value-consuming study before `FEATURE_LABEL_PARQUET_SINK_V1`; no session-context
  features before `SESSION_LABEL_GUARD_FIX_V1`;
* no re-implementation or destructive edit of any existing `runtime.*`, `governance.*`, `research.*`,
  `experiments.*`, `backtest.*`, `features.*`, `labels.*`, or `data.foundation.*` primitive — these
  are **consumed**, and they sit in every phase's `forbidden_paths`;
* no order placement, account trading, position polling, broker execution, or order routing; no
  paper trading, live trading, real-time signal generation, or production execution adapter;
* no external Databento or IBKR provider call; no raw provider data access from `agent_factory` code;
* no L2 depth / MBO / event-stream / tick ingestion; no ML/DL training beyond authorized scope; no
  distributed compute, Ray cluster, or ML experiment platform;
* no committed raw/canonical/feature/label/runtime/agent values, provider responses, heavy artifacts
  (parquet/arrow/feather/dbn/zst), local registries/DBs, logs, caches, or `runs/**`;
* no profitability, tradability, alpha-validity, strategy-readiness, paper-readiness,
  live-readiness, broker-readiness, or production-readiness claim.

## Agent Roster (Contracts Only)

The MVP roster is defined as **contracts**, not running agents. Each role's full contract
(inputs, tools, outputs, allowed/forbidden decisions, handoff format, reviewer independence, and
failure modes) is specified in `PHASE_PLAN.md` and `docs/agent_factory/roles/`.

| Role | One-line purpose | May decide | May not decide |
| --- | --- | --- | --- |
| Research Director | Scope a bounded task; assign roles; set budgets | task scope/budget within queue policy | promote; review verdicts; alpha search |
| Hypothesis Scout | Draft 3–5 `AlphaSpec` drafts | draft content | approve its own spec; implement; run diagnostics |
| AlphaSpec Critic | Critique / reject / request revision | reject or request revision | implement; promote; draft the spec it reviews |
| Data Contract Auditor | Verify seed DatasetVersion/FeaturePack/LabelPack availability | inputs available or blocked | raw access; registry writes; bypass accepted-DatasetVersion |
| Feature Engineer | Reference approved seed features or draft a bounded `FeatureRequest` | bounded reference/request | self-review; broad materialization; value commits |
| Label Engineer | Reference approved seed labels or draft a bounded `LabelSpec` | bounded reference/spec | self-review; broad materialization; label-as-feature |
| No-Lookahead Auditor | Audit runtime outputs for availability/leakage/same-bar/locked-test | lookahead PASS/BLOCKED | promote; weaken the guard |
| Diagnostics Runner | Invoke the Research Runtime for a bound `StudySpec` | request diagnostics within budget | promote; alter specs; bypass runtime |
| Statistical Reviewer | Issue PASS/REJECT/WATCH/INCONCLUSIVE on runtime evidence | the review verdict | implement; review its own work |
| Librarian | Record decisions/rejections + proposed memory after a verdict | propose memory records | promote without PromotionGate; write a registry without a verdict |

Optional later roles (explicitly **not** MVP): Strategy Wrapper Agent, Portfolio Agent, ML
Meta-Label Agent, Execution Cost Reviewer, Live/Paper Operator, Red-Team Reviewer.

## Core Hard Rules

```text
no AlphaSpec      -> no implementation
no FeatureRequest -> no feature
no LabelSpec      -> no label
no StudySpec      -> no diagnostics
no EvidenceBundle -> no candidate
no TrialLedger    -> no promotion
no reviewer verdict -> no factor library entry

idea generator cannot approve itself
implementation agent cannot review itself
diagnostics runner cannot promote
reviewer cannot be implementer
portfolio optimizer cannot ignore the statistical reviewer (future)
human owns risk/capital/live judgment
```

No agent may: read raw Databento/IBKR provider files; call external providers; write
raw/canonical/feature/label values into the repo; modify FeatureStore/LabelStore/DatasetVersion
registries directly; bypass the runtime input resolver or tool surface; bypass `StudySpec`;
self-review; self-promote; claim alpha/profitability/tradability; create paper/live/broker/order
code; or touch capital allocation.

## Agent Lifecycle Summary

The agent-research lifecycle the contracts must enforce is:

```text
RESEARCH_TASK_QUEUED -> DIRECTOR_SCOPED -> HYPOTHESIS_DRAFTED -> ALPHASPEC_DRAFTED
  -> ALPHASPEC_CRITIQUED (-> ALPHASPEC_REVISION_REQUESTED / ALPHASPEC_REJECTED)
  -> DATA_CONTRACT_AUDITED (-> INPUTS_BLOCKED)
  -> IMPLEMENTATION_SCOPED -> DIAGNOSTICS_REQUESTED -> DIAGNOSTICS_COMPLETE
  -> NO_LOOKAHEAD_AUDITED
  -> STATISTICAL_REVIEW_{PASS|WATCH|REJECT|INCONCLUSIVE}
  -> EVIDENCE_DRAFT_RECORDED -> REFERENCE_HANDOFF_RECORDED
  -> LIBRARIAN_MEMORY_RECORDED
  Terminal at any stage: REJECTED | INCONCLUSIVE | BLOCKED
```

`REFERENCE_HANDOFF_RECORDED` is the most advanced forward state any dry-run survivor may reach;
promotion belongs to a reviewer verdict + PromotionGate under a later, separately-authorized
campaign.

**Prohibited MVP states (must never be reachable by any transition the contracts define):**

```text
ALPHA_VALIDATED  FACTOR_PROMOTED  STRATEGY_READY  PORTFOLIO_READY  CANDIDATE_PROMOTED
LIVE_READY  PAPER_READY  PROFITABLE  TRADABLE  PRODUCTION_READY  AUTONOMOUS_RESEARCH_RUNNING
```

## Relationship to ALPHA_FUTURES_CORE_ALPHA_PILOT_V1

`ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` — the future core alpha pilot — will run *real* studies through
the runtime, driven by these controlled agent contracts, under its own explicitly authorized
campaign. The program roadmap is:

```text
Data Foundation -> Feature/Label Foundation -> Research Runtime -> Seed Packs / Real Smoke
  -> Agent Factory (this) -> Core Alpha Pilot -> Validation Governance -> Factor Library
  -> Strategy Reference Validation -> Portfolio AlphaBook -> Agent Research Runner
  -> Monitoring/Decay -> ML Meta-Labeling -> L1 Eventstream -> L2/Execution -> Paper -> Live Canary
```

This campaign is the link that turns the executable runtime into a **governed team that can drive
it** — so the Core Alpha Pilot can run with multiple controlled AI researchers on point-in-time-safe,
cost-aware, deduplicated, leakage-audited inputs, never as unbounded alpha search and never with the
locked-test partition unless governance contamination metadata exists. Any survivor an Agent Factory
dry-run produces stops at a `ReferenceCandidateHandoff` or an `EvidenceDraft`; turning that into a
validated candidate or a strategy is the explicit, separately-authorized job of later campaigns.

## Success Definition

`ALPHA_AGENT_FACTORY_MVP` succeeds when:

1. The new `src/alpha_system/agent_factory/` package exists as **contracts only** — no autonomous
   agent is instantiated and no continuous research runner is created.
2. The entry contract encodes the four preflight gates (seed FeaturePack/LabelPack exists, runtime
   real smoke PASS, `FEATURE_LABEL_PARQUET_SINK_V1` status, `SESSION_LABEL_GUARD_FIX_V1` status) and
   fails closed on missing prerequisites.
3. An AgentRole contract model + registry, a fail-closed permission matrix
   (`ToolPermission`/`DataPermission`/`WritePermission`/`ReviewPermission`/`PromotionPermission`/
   `HumanApprovalRequired`/`RedLaneRequired`), a structured tool contract registry, and the research
   queue / work-item contracts all exist.
4. All ten MVP role contracts exist additively in disjoint files, each with explicit
   inputs/tools/outputs/decisions/forbidden-actions/handoff/reviewer-independence, each registering
   via the role registry without editing shared files.
5. Separation of duties is enforced in code: generator cannot approve, implementer cannot review,
   diagnostics runner cannot promote, reviewer is not the implementer, librarian cannot write a
   registry without a reviewer verdict.
6. Agent records (run/decision/handoff/tool-invocation/audit/prompt-version/role-version/
   permission-version) and rejected-idea/research memory exist, consume the governance graveyard,
   avoid duplicate ideas, and surface prior rejection reasons.
7. All agent-facing tool contracts produce **structured, value-free outputs** (status, role,
   request_id, alpha_spec_id, study_spec_id, dataset_version_id, feature/label pack refs,
   runtime_run_id, diagnostics_summary, cost_summary, rejection_reasons, blocking_findings,
   next_required_gate, artifacts, limitations) and never embed raw or heavy data.
8. The runtime bridge drives `RuntimeToolResult` / `RuntimeRunSummary` (and the `alpha runtime` CLI)
   and resolves inputs via `resolve_dataset_version`; no `agent_factory` code reads raw provider
   files or calls an external provider; no consumed primitive is edited.
9. The bounded **non-alpha dry-run** (synthetic fixtures, and seed packs when local) proves role
   routing, tool contracts, permissions, handoffs, and rejection memory, and records a truthful
   `PASS_WITH_WARNINGS`; it does **not** prove alpha.
10. Large-scale value-consuming studies are blocked until `FEATURE_LABEL_PARQUET_SINK_V1`;
    session-context features are blocked until `SESSION_LABEL_GUARD_FIX_V1`; seed-pack dry-run is
    never treated as research evidence.
11. No raw/canonical/feature/label/runtime/agent values or local DBs are committed; `git ls-files
    runs` is empty; explicit staging is used throughout.
12. DAG metadata is correct: parallel-safe phases have disjoint `allowed_paths`, no phase branch
    writes `ACTIVE_CAMPAIGN.md` in parallel mode, and merge proceeds serially.
13. No alpha/profitability/tradability/strategy/paper/live/broker/production claim is introduced
    anywhere, no prohibited MVP state is reachable, and the closeout records a final verdict ∈
    {`COMPLETE`, `COMPLETE_WITH_WARNINGS`, `BLOCKED`} with `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`
    next-campaign readiness.

### Out-of-scope claims

This campaign must not claim that any alpha is validated, that any feature, label, signal, or idea
is predictive, that any agent dry-run found alpha, that any survivor is a strategy candidate, that
any strategy is profitable, tradable, robust, production-ready, paper-ready, live-ready, or
broker-ready, that any factor is promoted, or that a good dry-run implies tradability. It produces a
controlled AI research team **contract layer** only.

---

*This document is a campaign contract describing strategic intent and boundaries. It is not an
implementation, instantiates no autonomous agent, and makes no alpha, tradability, profitability,
production, or live claim.*
