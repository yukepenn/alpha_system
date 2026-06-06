# ALPHA_RESEARCH_RUNTIME_MVP Campaign Goal

## Campaign Identity

**ALPHA_RESEARCH_RUNTIME_MVP — The Executable Research Loop Layer over the Feature/Label Substrate**

* **Campaign ID:** `ALPHA_RESEARCH_RUNTIME_MVP`
* **Campaign name:** Research Runtime MVP: Executable Research Loop Layer over the Feature/Label Substrate
* **Campaign path:** `campaigns/ALPHA_RESEARCH_RUNTIME_MVP`
* **Repo name:** `alpha_system`
* **Repo path:** `~/projects/alpha_system`
* **Host environment:** Windows host
* **Primary runtime:** WSL2 Ubuntu
* **Required active filesystem location:** WSL2 Linux filesystem under `~/projects/alpha_system`
* **Forbidden active worktree locations:** `/mnt/c`, `/mnt/d`, `/mnt/e`, OneDrive, Dropbox, Google Drive, Windows-synced folders, network drives, temporary directories
* **Project profile:** `trading_research` / `research` / `research_runtime`
* **Campaign execution mode:** Frontier Harness Generic v3.0 Workflow 2 with the DAG wave scheduler
* **Campaign driver:** Ralph strict autonomous loop
* **Scheduler mode:** `dag_wave` (parallel build, serial merge queue)
* **Primary executor:** Codex GPT-5.5 high
* **Primary semantic reviewer:** Claude Opus 4.8 xhigh
* **Verifier / source-map / audit support:** Claude Sonnet 4.6
* **Strategic campaign reasoning:** ChatGPT Pro GPT-5.5 Thinking
* **Phase count:** 27 phases (`RT-P00` … `RT-P26`)

This campaign is **contract generation and runtime-orchestration construction only**. It defines,
designs, and (where local-only and authorized) implements the **research runtime** that turns an
approved `AlphaSpec` + `StudySpec` into reproducible diagnostics, cost stress, bounded probes, an
`EvidenceDraft`, rejection reasons, and a `ReferenceCandidateHandoff`. It does **not** conduct
alpha search, does **not** promote any factor, does **not** validate any strategy, does **not**
materialize or commit feature/label/runtime values, does **not** call Databento or IBKR, and does
**not** pull or commit raw, canonical, feature, or label data.

One sentence captures the posture:

```text
A diagnostic PASS is not alpha validation; a signal probe is not a strategy candidate;
a bounded grid is not promotion; an EvidenceDraft is not a candidate;
a ReferenceCandidateHandoff is not Reference validation; the fast path is not Reference truth.
```

The critical framing is stated explicitly and must hold everywhere in this campaign:

```text
Research Runtime is NOT the Agent Factory.
Research Runtime is NOT alpha search.
Research Runtime is NOT a FactorLibrary.
Research Runtime is NOT Strategy Reference Validation.
Research Runtime is NOT a Portfolio AlphaBook.
Research Runtime is NOT paper, live, or broker execution.
A diagnostic PASS is not alpha validation.
A signal probe is not a strategy candidate.
A bounded grid is not promotion.
An EvidenceDraft is not a candidate.
A ReferenceCandidateHandoff is not Reference validation.
The fast path is not Reference truth.
```

## Mission

Build the **local, deterministic research runtime** — the executable loop layer that makes an
approved `AlphaSpec` + `StudySpec` *runnable* against the registered, point-in-time-safe
FeatureStore/LabelStore substrate, by **orchestrating existing primitives** rather than
re-implementing them.

This campaign is the **executable research loop layer**. It is the bridge from a
`research-ready FeatureStore / LabelStore substrate` to an `EvidenceDraft` plus a
`ReferenceCandidateHandoff` — or to an honest `REJECTED`, `INCONCLUSIVE`, or `BLOCKED` outcome.
It is not just diagnostics, and it is not just a set of CLI tools: it is the governed,
reproducible, fail-closed runtime that future AI Alpha Researchers in the Agent Factory drive
through structured tool calls.

The full research loop the runtime executes is:

```text
resolve accepted DatasetVersion + Feature/Label packs
  -> Tier 0 feature/factor diagnostics
  -> label diagnostics
  -> simple signal probe
  -> cost stress
  -> bounded variant budget
  -> EvidenceDraft
  -> ReferenceCandidateHandoff
OR -> REJECTED / INCONCLUSIVE / BLOCKED
```

The runtime achieves this by **orchestrating existing primitives, never duplicating them**:

* **Diagnostic math** — `alpha_system.research.ic`, `research.buckets`, `research.regimes`,
  `research.correlation`, `research.feature_label_diagnostics`.
* **Cost and slippage** — `alpha_system.backtest.costs`, `backtest.slippage`.
* **Variant budget / overfit / splits** — `alpha_system.experiments.limits`,
  `experiments.overfit_controls`, `experiments.splits`, `experiments.survivors`.
* **Governance and evidence** — `alpha_system.governance.study_input_pack` (StudyInputPack),
  `governance.evidence_bundle` (EvidenceBundle), `governance.alpha_spec`, `governance.study_spec`,
  `governance.feature_request`, `governance.label_spec`, `governance.duplicate_exposure`,
  `governance.label_leakage_guard`, `governance.trial_ledger`.
* **Data and substrate** — `alpha_system.data.foundation.version_registry.resolve_dataset_version`
  with `CanonicalBarRecord` / `CanonicalBBORecord` / `DenseGridBarRecord`, plus
  `alpha_system.features.consumption/store/registry` and `labels.store/registry`.

The **new** package is `src/alpha_system/runtime/` (orchestration only). The CLI surface is a
**target** `alpha runtime ...` command group added additively to `src/alpha_system/cli/`. Both are
described here as **planned** deliverables this campaign will build; they do not exist yet.

## Why This Campaign Exists

The strategic ordering of the program is precise and deliberate:

```text
ALPHA_SYSTEM_V1                made the system able to run.
ASV1_RELEASE_HYGIENE           made the V1 release baseline clean and reviewable.
ALPHA_RESEARCH_GOVERNANCE_MVP  decided what research results are allowed to be believed.
ALPHA_DATA_FOUNDATION_V1       let real market truth enter — controlled, versioned, read-only.
ALPHA_FEATURE_LABEL_FOUNDATION_V1  turned accepted DatasetVersions into a governed research substrate.
ALPHA_RESEARCH_RUNTIME_MVP     makes an approved AlphaSpec + StudySpec runnable into diagnostics and evidence.
```

`alpha_system` is becoming an **AI Alpha Research Factory**, not a backtester and not a strategy
repository. The long-term north star is an AI-driven, evidence-gated, cost-aware intraday alpha
factory that continuously discovers, validates, combines, monitors, deweights, and retires alphas
under strict point-in-time and reproducibility rules. The long-term objective — used here only for
framing, never as a claim — is to maximize robust out-of-sample, cost-adjusted, capacity-aware,
low-correlation intraday Sharpe, subject to drawdown, turnover, liquidity, execution, and
reproducibility constraints. In that factory:

* AI generates research throughput.
* `alpha_system` owns evidence and truth.
* Ralph / Workflow 2 owns process and gates.
* Claude reviews semantics and runs done-checks.
* Codex implements scoped phase specs.
* The human owns direction and risk/capital judgment.

Governance exists, a versioned data foundation exists, and a governed, no-lookahead-safe
Feature/Label substrate now exists. What is still missing is the *executable layer* that turns
those static assets into a **running, reproducible, fail-closed research loop** — one that any
future agent can drive without re-implementing diagnostic math, cost models, or overfit controls,
and without ever bypassing governance or availability discipline.

This campaign exists to **prevent** the failure modes that destroy an automated research loop:

```text
diagnostic-as-validation        (treating a PASS as proof of alpha)
probe-as-strategy               (treating a signal probe as a strategy candidate)
unbounded grid sprawl           (variant-mining until something looks good)
locked-test contamination       (selecting on the locked test without metadata)
zero-cost optimism              (using a zero-cost result as a promotion basis)
silent failure                  (hiding failed or inconclusive runs)
fast-path-as-truth              (treating the fast runtime path as Reference truth)
primitive duplication           (re-coding research/experiments/governance/backtest math)
raw-data runtime hacking        (runtime code reading provider files directly)
heavy-artifact leakage          (committing feature/label/runtime values or local DBs)
```

Each is a known way that an AI research loop manufactures convincing but false evidence, or leaks
state it should never touch. The Research Runtime installs the orchestration, the decision states,
the cost discipline, the variant budget, and the no-lookahead audit that make those failure modes
**unreachable by construction**.

### Do Not Let Research Runtime Become Alpha Search

This boundary is load-bearing and must hold in every phase: **Research Runtime is the runtime that
*executes one approved study at a time*; it is not the search that *decides what to study*.** It
takes an already-approved `AlphaSpec` + `StudySpec`, runs a bounded, budgeted, cost-stressed,
no-lookahead-audited study, and emits descriptive evidence — never a candidate, never a promotion,
never a tradability claim. Broad alpha discovery, factor mining, hypothesis generation, and
candidate promotion belong to the future Agent Factory and Core Alpha campaigns under their own
authorized contracts. If a phase begins to enumerate hypotheses, expand grids without a
`VariantBudget`, or promote a survivor, it has crossed out of this campaign's scope and must stop.

## Baseline from Completed Campaigns

The following campaigns are treated as **complete** and form this campaign's baseline:

* `ALPHA_SYSTEM_V1` — local-first research harness foundation.
* `ASV1_RELEASE_HYGIENE` — clean, reviewable V1 release baseline with validation gates.
* `ALPHA_RESEARCH_GOVERNANCE_MVP` (COMPLETE_WITH_WARNINGS) — the admissibility/evidence protocol:
  `AlphaSpec`, `FeatureRequest`, `LabelSpec`, `StudySpec`, the `StudyInputPack`, the
  `EvidenceBundle`, the duplicate-exposure guard, the `label_leakage_guard`, and the `trial_ledger`,
  plus the hard rules *no-code-before-spec*, *no-candidate-without-evidence*, and
  *no-promotion-without-ledger*. This governance layer is **fully built** and must be **consumed,
  not duplicated**.
* `ALPHA_DATA_FOUNDATION_V1` (PASS_WITH_WARNINGS) — the read-only, provenance-rich, quality-gated
  data truth layer; the DatasetVersion registry; canonical records (`CanonicalBarRecord`,
  `CanonicalBBORecord`, `DenseGridBarRecord`); partitions; and the sanctioned consumption API
  `resolve_dataset_version`.
* `PRE_FEATURE_REPO_CONSOLIDATION_V1` — pre-Feature/Label repo consolidation and reconciliation.
* `WF2_PARALLEL_DAG_SCHEDULER_MVP` — the opt-in DAG wave scheduler (parallel build, serial merge)
  this campaign runs under.
* `ALPHA_FEATURE_LABEL_FOUNDATION_V1` (32/32, `COMPLETE_WITH_WARNINGS`) — the versioned,
  no-lookahead-safe, deduplicated, cost-aware, BBO-aware research substrate: the governed
  FeatureStore/LabelStore over accepted DatasetVersions, feature/label families, materialization
  engines, registries, quality/coverage reports, leakage/availability audits, and the StudySpec
  Input Pack integration. Its registered, point-in-time-safe FeatureStore/LabelStore substrate is
  **the input this campaign's runtime consumes**.

**Dependency warnings:** if any baseline item is found not-on-`main` at run time, treat it as a
dependency warning and proceed only against the on-`main` state — but the campaign contract itself
is still valid and may still be generated. The data corpus and the materialized Feature/Label
values are **local-only**; their absence in a clean checkout is expected and is not a contract
blocker, because this campaign consumes accepted DatasetVersions and registered Feature/Label packs
through their APIs rather than committing the data.

That baseline deliberately did **not** provide an executable research runtime: there is no package
that resolves an `AlphaSpec` + `StudySpec` into a runnable, budgeted, cost-stressed,
no-lookahead-audited study; no runtime contracts (`RuntimeRequest`, `RuntimePlan`,
`StudyRunSpec`/`StudyRunRecord`, manifests); no runtime diagnostics/probe/cost/grid/audit
orchestration; no `EvidenceDraft` builder feeding the governance `EvidenceBundle`; no
`ReferenceCandidateHandoff`; no agent-facing tool-result contracts; and no `alpha runtime` CLI.
This campaign supplies exactly that missing executable layer.

## Data / Feature / Label Posture

* The runtime consumes **accepted DatasetVersions only**, never raw provider files. The sanctioned
  consumption API is
  `alpha_system.data.foundation.version_registry.resolve_dataset_version(registry_path, id)`,
  returning DatasetVersion metadata. Canonical records are built via `CanonicalBarRecord`,
  `CanonicalBBORecord`, and `DenseGridBarRecord`.
* A DatasetVersion is **admissible** when its lifecycle state is in
  `{VERSIONED, READY_FOR_RESEARCH}` with non-blocking quality and coverage.
* It is **forbidden** for any runtime code to read `.dbn`, `.zst`, parquet, arrow, feather, or
  provider files directly. Canonical records and registered Feature/Label packs only.
* **No external Databento or IBKR provider call** occurs in this campaign; the data is already
  local. **Databento is the primary deep-history research source**; **IBKR is a broker-source,
  recent-validation-only DatasetVersion path** and is never a primary alpha source and never an
  execution venue. Databento and IBKR DatasetVersions are **never merged**.
* **Availability discipline:** feature inputs carry `available_ts`; label inputs carry
  `label_available_ts`. **No label is ever exposed as a runtime feature.** Forward-looking horizons
  are legal only for labels, never for live features; no centered/future window may feed a live
  feature input.
* **Feature/Label packs** are consumed through `alpha_system.features.consumption/store/registry`
  and `labels.store/registry`; the runtime never re-materializes or edits them.
* **Partitions:** development `2018-01-01 .. 2022-12-31`; validation `2023-01-01 .. 2024-12-31`;
  locked_test_candidate `2025-01-01 .. as_of_run`; an optional rolling latest_shadow_candidate.
  Use of the locked-test (or latest-shadow) partition requires governance contamination metadata,
  and selection on the locked test is forbidden.
* Raw, canonical, feature, label, and runtime values are **local-only** and never committed; the
  data root is outside the repo (configured via `ALPHA_DATA_ROOT`), and the registry path is
  local-only at `$ALPHA_DATA_ROOT/registry/datasets.sqlite`.

## What This Campaign Builds

Across 27 Workflow 2 phases (`RT-P00` … `RT-P26`) the campaign defines, designs, and (where
local-only and authorized) implements the new `src/alpha_system/runtime/` orchestration package
and the planned `alpha runtime` CLI:

* **Campaign bootstrap and entry contract** (`RT-P00` … `RT-P02`): the campaign control surface and
  `docs/research_runtime/` docs root; the single sanctioned runtime entry contract
  (`alpha_system.runtime.entry_contract`) that consumes `resolve_dataset_version`, the
  `StudyInputPack`, and the registered FeatureStore/LabelStore and defines
  `INPUTS_RESOLVED` / `INPUTS_BLOCKED` / `INPUTS_INCONCLUSIVE`; and the importable runtime package
  skeleton plus naming conventions.
* **Runtime contracts** (`RT-P03` … `RT-P06`): the `RuntimeInputPack` resolver (accepted
  DatasetVersion + feature/label packs, with `available_ts` / `label_available_ts` discipline); the
  `RuntimeRequest` / `RuntimePlan` / `StudyRunSpec` contracts that describe and validate a bounded
  job before it runs; the durable `StudyRunRecord`, reproducibility `StudyRunManifest`, and
  `RuntimeArtifactManifest`; and the shared diagnostics report contracts
  (`DiagnosticsRunSpec` / `DiagnosticsRunRecord` and the descriptive, non-promotional report shape).
* **Diagnostics runtime** (`RT-P07` … `RT-P11`, parallel): the Factor Diagnostics runtime
  (orchestrating `research.ic`/`research.buckets`), Label Diagnostics runtime, Session / Regime /
  RTH / ETH split diagnostics (orchestrating `research.regimes`), Cross-Market ES/NQ/RTY
  diagnostics (orchestrating `research.correlation`), and `CostModelVersion` + the cost-stress
  runtime (orchestrating `backtest.costs`/`backtest.slippage`) producing a `CostSensitivityReport`
  across base / stress_1 / stress_2 / double_cost profiles.
* **Runtime integration** (`RT-P12` … `RT-P19`): the simple Signal Probe runtime
  (`SignalProbeSpec` / `SignalProbeReport`, no same-bar optimistic fill); the bounded-grid /
  `VariantBudget` guard (orchestrating `experiments.limits`/`experiments.overfit_controls`); the
  `NoLookaheadRuntimeAudit`; `RejectionReasonRecord` plus the runtime decision states; the
  `EvidenceDraft` builder feeding `governance.evidence_bundle`; the `ReferenceCandidateHandoff`
  builder; the planned `alpha runtime` CLI / tool surface; and the `RuntimeCachePolicy` plus the
  local-only runtime artifact policy.
* **Tests, tools, and docs** (`RT-P20` … `RT-P23`): tiny synthetic runtime fixtures and the
  fail-closed test suite; a small real local-only DatasetVersion runtime smoke; the agent-facing
  `RuntimeToolResult` / `RuntimeRunSummary` structured-output contracts (no autonomous agent
  created); and the `RuntimeReportCard` renderer plus report/markdown templates.
* **Workflow and closeout** (`RT-P24` … `RT-P26`): the Workflow 2 DAG integration and parallel
  plan; the end-to-end runtime dry run on synthetic fixtures; and the acceptance audit, semantic
  done-check, and closeout with a final verdict and Agent Factory next-campaign readiness.

The planned `alpha runtime` CLI subcommands are: `plan`, `validate-inputs`, `run-diagnostics`,
`run-label-diagnostics`, `run-signal-probe`, `run-cost-stress`, `build-evidence-draft`,
`build-reference-handoff`, `summarize`, `inspect`, and `replay-summary` — all local-only and
CI-safe, registered additively in the existing CLI shell.

## What This Campaign Does Not Build

This campaign must not implement or require any of the following:

* no broad alpha discovery, factor search, hypothesis generation, or candidate selection;
* no factor promotion, FactorLibrary, or promotion of any survivor into a candidate or strategy;
* no Strategy Reference Validation, Portfolio AlphaBook, strategy wrappers as research products, or
  strategy/backtest/portfolio optimization as a runtime product;
* no Agent Factory, no autonomous agents, no Futures Core Alpha work beyond preparing tool
  contracts that a future Agent Factory will consume;
* no re-implementation or destructive edit of any existing `research.*`, `experiments.*`,
  `governance.*`, `backtest.*`, `features.*`, `labels.*`, or `data.foundation.*` primitive — these
  are **consumed**, and they sit in every phase's `forbidden_paths`;
* no order placement, account trading, position polling, broker execution, or order routing;
* no paper trading, live trading, real-time signal generation, or production execution adapter;
* no external Databento or IBKR provider call; no raw provider data access from runtime code;
* no L2 depth, MBO, event-stream ingestion, or tick-data ingestion;
* no ML/DL training beyond authorized scope; no distributed compute, Ray cluster, or ML experiment
  platform;
* no committed raw/canonical/feature/label/runtime values, provider responses, heavy artifacts
  (parquet/arrow/feather/dbn/zst), local registries/DBs, logs, caches, or `runs/**`;
* no profitability, tradability, alpha-validity, strategy-readiness, paper-readiness,
  live-readiness, broker-readiness, or production-readiness claim.

## Runtime Tier Model

The runtime is organized into a strict ladder of tiers. Each tier answers a narrower, more
expensive question than the one before it, and **no tier ever upgrades the meaning of the tier
below it**. A higher tier is reachable only when the lower tiers complete cleanly; any tier may end
in `REJECTED`, `INCONCLUSIVE`, or `BLOCKED`, recorded with a `RejectionReasonRecord`.

### Tier 0 — Feature / Factor / Label Diagnostics

* **What it answers:** Is this feature/factor/label well-formed, well-covered, point-in-time safe,
  and does it exhibit any descriptive relationship (IC/RankIC, bucket monotonicity, decay,
  distribution, horizon coverage, class balance, MFE/MAE, session/regime/cross-market structure)?
* **Allowed:** orchestrating `research.ic`, `research.buckets`, `research.regimes`,
  `research.correlation`, and `research.feature_label_diagnostics`; descriptive, non-promotional
  reports with explicit limitations; session/RTH/ETH/regime/cross-market splits; cost-aware
  diagnostics.
* **Forbidden:** any signal probe; any promotion language; any new IC/bucket/regime math; any claim
  that a relationship is predictive, robust, or tradable.
* **Main outcome:** `DIAGNOSTICS_COMPLETE` (with a `FactorDiagnosticsReport` /
  `LabelDiagnosticsReport` / split / cross-market report), or `DIAGNOSTICS_FAILED`, or a terminal
  `REJECTED` / `INCONCLUSIVE`. **A PASS at Tier 0 is not alpha validation.**

### Tier 1 — Simple Signal / Bounded Study Probe

* **What it answers:** Does a diagnostic relationship survive a *simple* long/short/flat probe
  under cost, turnover, and parameter-neighborhood stability — within a bounded `VariantBudget`?
* **Allowed:** a `SignalProbeSpec` / `SignalProbeReport` with threshold probes, trade count,
  turnover, a cost-aware expectancy proxy, a drawdown proxy, and stability checks; a bounded grid
  guarded by `experiments.limits` / `experiments.overfit_controls`; mandatory cost stress including
  a `double_cost` profile; no same-bar optimistic fill.
* **Forbidden:** final strategy validation; management/position-sizing grids; portfolio claims;
  unbounded grids; selection on the locked test; any promotion.
* **Main outcome:** `SIGNAL_PROBE_COMPLETE` and `COST_STRESS_COMPLETE` for a survivor, or a
  terminal `REJECTED` / `INCONCLUSIVE`. **A probe survivor is not a strategy candidate, and a
  bounded grid is not promotion.**

### Tier 2 — Reference Candidate Handoff

* **What it answers:** For a survivor that cleared Tiers 0–1 cleanly, what is the conservative,
  fully-documented package a *future* Reference validation step would need?
* **Allowed:** a `ReferenceCandidateHandoff` that bundles the reports, the `StudyRunManifest`,
  dataset/feature/label/code/config versions, the cost profile, explicit limitations, a
  `strategy_not_validated` flag, and `reference_requirements` (next required gate
  `REFERENCE_VALIDATION_REQUIRED`).
* **Forbidden:** running Reference validation itself; executing a Reference backtest; any
  tradability or promotion claim; treating the fast path as Reference truth.
* **Main outcome:** `REFERENCE_HANDOFF_READY` (handoff only), or a terminal `REJECTED` /
  `INCONCLUSIVE` / `BLOCKED`. **A handoff is not Reference validation; the fast path is not
  Reference truth.** `REFERENCE_HANDOFF_READY` is the most advanced state any survivor may reach.

### Tier 3 — Evidence Draft

* **What it answers:** What descriptive evidence bundle — diagnostics, cost summaries, limitations,
  and rejection/handoff state — feeds the existing governance `EvidenceBundle` as an *evidence
  input*?
* **Allowed:** an `EvidenceDraft` builder that assembles tier outputs into a structure consumable by
  `alpha_system.governance.evidence_bundle`; explicit limitations and non-promotional framing.
* **Forbidden:** creating a candidate; re-implementing the `EvidenceBundle`; any promotion or
  tradability claim.
* **Main outcome:** `EVIDENCE_DRAFT_READY`, or a terminal `REJECTED` / `INCONCLUSIVE` / `BLOCKED`.
  **An EvidenceDraft is not a candidate.**

Tier 3 (the `EvidenceDraft`) and Tier 2 (the `ReferenceCandidateHandoff`) are the two terminal
*forward* products of a clean run; both are descriptive inputs to later, separately-authorized
gates, never promotions in themselves.

## Data / Feature / Label Entry Contract

The single sanctioned runtime entry path is established in `RT-P01` (`entry_contract`), built out by
the `RT-P03` `RuntimeInputPack` resolver, and consumed by every later phase:

```text
AlphaSpec (aspec_) + StudySpec  required        -> no spec, no runtime run
StudyInputPack (governance)     consumed         -> binds freq_/lspec_/aspec_ + dataset_scope
resolve_dataset_version(registry_path, id)       -> DatasetVersion (metadata, accepted-only)
CanonicalBarRecord / CanonicalBBORecord / DenseGridBarRecord  -> canonical records only
features.consumption/store/registry              -> feature packs (carry available_ts)
labels.store/registry                            -> label packs (carry label_available_ts)
locked-partition use                             -> requires governance contamination metadata
```

* **No `AlphaSpec` / `StudySpec`, no run.** A diagnostics or probe run is never executed without an
  `AlphaSpec` and `StudySpec` reference.
* **No accepted DatasetVersion, no execution.** Inputs are produced only by resolving an admissible
  DatasetVersion (`{VERSIONED, READY_FOR_RESEARCH}`); raw provider access is forbidden; no external
  provider calls occur.
* **Availability discipline at resolution time.** Feature inputs carry `available_ts`; label inputs
  carry `label_available_ts`; no label-as-feature; no centered/future window as a live feature.
* **Databento and IBKR DatasetVersions are never merged.**
* **Locked-test partition use requires governance contamination metadata**, recorded through the
  governance gate; selection on the locked test is forbidden.
* The registry and all data/value artifacts remain **local-only and uncommitted**.

The entry contract produces one of three pre-execution outcomes — `INPUTS_RESOLVED`,
`INPUTS_BLOCKED`, or `INPUTS_INCONCLUSIVE` — before any diagnostics run.

## Research Runtime Object Model Summary

The runtime objects below are the contract the Workflow 2 phases implement. They are grouped by
role; their names are normative and must match the names used in `PHASE_PLAN.md` and `campaign.yaml`.

* **Request / plan / inputs:** `RuntimeRequest`, `RuntimePlan`, `RuntimeInputPack`,
  `FeatureLabelPackResolver`, `StudyInputPack` (consumed from governance).
* **Study lifecycle records:** `StudyRunSpec`, `StudyRunRecord`, `StudyRunManifest`,
  `RuntimeArtifactManifest`.
* **Diagnostics:** `DiagnosticsRunSpec`, `DiagnosticsRunRecord`, `FactorDiagnosticsReport`,
  `LabelDiagnosticsReport`, `RegimeSplitSpec` / `RegimeSplitReport`, `SessionSplitReport`,
  `CrossMarketDiagnosticsReport`, `DiagnosticsQualityGate`.
* **Probe / bounded study:** `SignalProbeSpec`, `SignalProbeReport`, `BoundedGridSpec`,
  `BoundedGridRunRecord`, `VariantBudget`.
* **Cost:** `CostModelVersion`, `CostStressSpec`, `CostSensitivityReport`.
* **Integrity / decisions:** `NoLookaheadRuntimeAudit`, `RejectionReasonRecord`,
  `RuntimeStopCondition`.
* **Forward products:** `EvidenceDraft`, `ReferenceCandidateHandoff`.
* **Tooling / agent-facing / policy:** `RuntimeToolResult`, `RuntimeRunSummary`, `RuntimeReportCard`,
  `RuntimeCachePolicy`, `RuntimeConcurrencyPolicy`.

Every report-bearing object is **descriptive and non-promotional**, carries explicit limitations,
and embeds **no raw or heavy data**; agent-facing tool results in particular carry only summaries,
version ids, statuses, rejection reasons, artifact references, and the next required gate.

## Research State Machine Summary

The research-run lifecycle the runtime objects must enforce is:

```text
RUNTIME_REQUESTED
  -> INPUTS_RESOLVED
  -> PLAN_VALIDATED
  -> DIAGNOSTICS_READY
  -> DIAGNOSTICS_RUNNING
  -> DIAGNOSTICS_COMPLETE        (/ DIAGNOSTICS_FAILED)
  -> SIGNAL_PROBE_READY
  -> SIGNAL_PROBE_COMPLETE
  -> COST_STRESS_COMPLETE
  -> EVIDENCE_DRAFT_READY
  -> REFERENCE_HANDOFF_READY
  Terminal at any stage: REJECTED | INCONCLUSIVE | BLOCKED
```

This is the contract the Workflow 2 phases implement; Ralph's own Workflow 2 state machine
(`RUN_INIT … RUN_SUMMARY`) is a separate, outer loop and does not execute this research lifecycle.
Failed and inconclusive runs **stay visible**: a terminal `REJECTED` / `INCONCLUSIVE` / `BLOCKED`
always carries a `RejectionReasonRecord` (e.g. `data_unavailable`, `leakage_risk`,
`weak_diagnostics`, `cost_fragile`, `low_sample`, `variant_budget_exceeded`, `duplicate_exposure`,
`blocked_by_policy`, `inconclusive`). `REFERENCE_HANDOFF_READY` is the most advanced state any
survivor may reach.

**Prohibited MVP states (must never be reachable by any transition implemented in this campaign):**

```text
ALPHA_VALIDATED
FACTOR_PROMOTED
STRATEGY_READY
PORTFOLIO_READY
LIVE_READY
PAPER_READY
PROFITABLE
TRADABLE
PRODUCTION_READY
```

These are named only as future, non-MVP concepts. No runtime run may reach them in this campaign.

## Relationship to ALPHA_AGENT_FACTORY_MVP

`ALPHA_RESEARCH_RUNTIME_MVP` is the **runtime that `ALPHA_AGENT_FACTORY_MVP` will drive.** The
future Agent Factory's AI Alpha Researchers do not re-implement diagnostics, cost models, overfit
controls, or no-lookahead audits — they call this runtime through structured tool contracts. The
agent-facing `RuntimeToolResult` / `RuntimeRunSummary` contracts delivered in this campaign
(`RT-P22`) are **new additive structured-output contracts** that prepare those tool surfaces
**without creating any autonomous agent**: they carry status, run id, version ids, a diagnostics
summary, a cost summary, rejection reasons, artifact references, and the next required gate — and
never embed raw or heavy data. The Agent Factory's research throughput is only as trustworthy as
this runtime's spec-gating, availability discipline, cost stress, variant budget, and fail-closed
decision states — which is why this campaign installs them first, and why the runtime, not the
agent, owns truth and evidence.

## Relationship to ALPHA_FUTURES_CORE_ALPHA_PILOT_V1

`ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` — the future core alpha pilot — will run *real* studies through
this runtime under its own explicitly authorized campaign contract, constrained by the governance
gates and data-admissibility rules already installed. The program roadmap is:

```text
Data Foundation -> Feature/Label Foundation -> Research Runtime -> Agent Factory -> Core Alpha -> Strategy/Portfolio
```

This campaign is the third link in that chain: it turns the registered, no-lookahead-safe
Feature/Label substrate into a **runnable, reproducible, fail-closed research loop** so the Agent
Factory and the core alpha pilot can execute approved studies on point-in-time-safe, cost-aware,
deduplicated, leakage-audited inputs — never on raw provider data, never as unbounded alpha search,
and never with the locked-test partition unless governance contamination metadata exists. Any
survivor this runtime produces stops at a `ReferenceCandidateHandoff` or an `EvidenceDraft`;
turning that into a validated candidate or a strategy is the explicit, separately-authorized job of
later campaigns.

## Success Definition

`ALPHA_RESEARCH_RUNTIME_MVP` succeeds when:

1. The runtime consumes only accepted DatasetVersions via `resolve_dataset_version` plus registered
   Feature/Label packs, and never reads raw provider files or makes any external provider call.
2. No runtime study runs without an approved `AlphaSpec` + `StudySpec`; the entry contract resolves
   to `INPUTS_RESOLVED` / `INPUTS_BLOCKED` / `INPUTS_INCONCLUSIVE` before any diagnostics run.
3. Runtime contracts exist — `RuntimeRequest`, `RuntimePlan`, `StudyRunSpec`, `StudyRunRecord`,
   `StudyRunManifest`, `RuntimeArtifactManifest`, and the diagnostics report contracts — with a
   reproducibility manifest binding dataset/feature/label/code/config versions.
4. Factor, label, session/regime/RTH/ETH split, cross-market, and cost-stress diagnostics runtimes
   are implemented additively in disjoint directories, **orchestrating** existing `research.*` and
   `backtest.costs/slippage` primitives, descriptive and non-promotional, with a `double_cost`
   profile present and slippage labeled a proxy.
5. The simple signal probe enforces no same-bar optimistic fill and mandatory cost stress; the
   bounded-grid / `VariantBudget` guard rejects unbounded grids and forbids selection on the locked
   test, consuming `experiments.limits` / `experiments.overfit_controls`.
6. The `NoLookaheadRuntimeAudit` fails closed on `available_ts` / `label_available_ts`, same-bar
   fills, label-as-feature, centered/future live windows, and locked-test contamination.
7. `RejectionReasonRecord` and the runtime decision states keep failed and inconclusive runs
   visible (`REJECTED` / `INCONCLUSIVE` / `BLOCKED`, never hidden).
8. The `EvidenceDraft` builder feeds `governance.evidence_bundle` as an evidence input (not a
   candidate); the `ReferenceCandidateHandoff` is a handoff only (not Reference validation), marked
   `strategy_not_validated` with `next_required_gate = REFERENCE_VALIDATION_REQUIRED`.
9. The planned `alpha runtime` CLI is local-only and CI-safe, registered additively; the
   `RuntimeCachePolicy` and runtime artifact policy mark heavy outputs local-only.
10. Tiny synthetic documented fixtures plus a fail-closed test suite exercise every prohibited
    shortcut; a small real local-only DatasetVersion smoke and the end-to-end dry run pass or record
    a truthful `PASS_WITH_WARNINGS`; agent-facing tool results carry no raw or heavy data.
11. No raw/canonical/feature/label/runtime values, provider responses, heavy artifacts, or local
    DBs are committed; `git ls-files runs` is empty; explicit staging is used throughout.
12. DAG metadata is correct: parallel-safe phases have disjoint `allowed_paths`, no phase branch
    writes `ACTIVE_CAMPAIGN.md` in parallel mode, and merge proceeds serially.
13. No alpha, profitability, tradability, strategy, paper, live, broker, or production-readiness
    claim is introduced anywhere, and no prohibited MVP runtime state is reachable; the closeout
    records a final verdict ∈ {`COMPLETE`, `COMPLETE_WITH_WARNINGS`, `BLOCKED`} and Agent Factory
    next-campaign readiness.

### Out-of-scope claims

This campaign must not claim that any alpha is validated, that any feature, label, or signal is
predictive, that any probe survivor is a strategy candidate, that any strategy is profitable,
tradable, robust, production-ready, paper-ready, live-ready, or broker-ready, that any factor is
promoted, or that a good diagnostic implies tradability. It produces an executable research runtime
that emits descriptive evidence drafts and reference candidate handoffs only.

---

*This document is a campaign contract describing strategic intent and boundaries. It is not an
implementation, and it makes no alpha, tradability, profitability, production, or live claim.*
