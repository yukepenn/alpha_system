# ALPHA_SYSTEM_V1 Campaign Goal

## Campaign Title

**ALPHA_SYSTEM_V1 — Local-First Alpha Research Platform Foundation**

## Active Repository

* **Repo name:** `alpha_system`
* **Repo path:** `~/projects/alpha_system`
* **Host environment:** Windows host
* **Primary runtime:** WSL2 Ubuntu
* **Required active filesystem location:** WSL2 Linux filesystem
* **Forbidden active worktree locations:** `/mnt/c`, `/mnt/d`, `/mnt/e`, OneDrive, Dropbox, Google Drive, Windows-synced folders, network drives, temporary directories, and any Windows-synced active development path

## Project Profile

* **Primary project profile:** `trading_research`
* **Secondary project profile:** `research`
* **Project type:** clean-slate alpha research platform
* **Initial research workflow:** 1-minute intraday, session-first research
* **Long-term readiness:** multi-asset-ready and Level-2-ready
* **Campaign target:** local-first v0.1 foundation
* **Campaign execution mode:** Frontier Harness Generic v3.0 Workflow 2
* **Campaign driver:** Ralph strict autonomous loop
* **Primary executor:** Codex GPT-5.5 high
* **Primary semantic reviewer:** Claude Opus 4.8 xhigh
* **Verifier / source-map / audit support:** Claude Sonnet 4.6
* **Strategic campaign reasoning:** ChatGPT Pro GPT-5.5 Thinking

## Why This Project Exists

`alpha_system` exists to provide a rigorous, reproducible, local-first research platform for developing and evaluating intraday alpha ideas without confusing research diagnostics, strategy simulation, portfolio construction, execution modeling, and live trading.

The platform must let human researchers and AI Agents:

1. Ingest and validate local market data.
2. Normalize data into canonical, point-in-time contracts.
3. Define factors through explicit versioned specifications.
4. Compute factors only from declared inputs.
5. Validate factor behavior before long-term materialization.
6. Keep labels separate from factors, signals, strategies, and portfolio decisions.
7. Run factor diagnostics without claiming tradability.
8. Promote candidates only through evidence and review.
9. Convert reviewed factor ideas into signals and strategy specifications.
10. Backtest strategies against one conservative reference execution truth.
11. Add acceleration only after deterministic parity with the reference engine.
12. Run bounded grids without uncontrolled combinatorial explosion.
13. Record every run with reproducibility metadata.
14. Produce reviewable evidence bundles for future human or agent inspection.
15. Preserve no-lookahead, artifact, and review discipline throughout the research lifecycle.

This campaign must build the foundation of an **Alpha Research Platform**, not merely a backtester.

A backtester alone answers, “What would this strategy have done under one simulator?”
An Alpha Research Platform must answer broader and stricter questions:

* What data version was used?
* What factor version was used?
* What label definition was used?
* Was information available at the decision time?
* Was the factor validated before materialization?
* Did the strategy depend only on declared factors?
* Were costs, spread, and fill assumptions explicit?
* Was fast simulation proven equivalent to reference truth?
* Were failed runs and rejected configurations visible?
* Was candidate promotion reviewed?
* Were artifacts reproducible and safe to inspect later?

## What the Platform Is

`alpha_system` is a local-first, config-driven, test-heavy, agent-friendly research platform with explicit domain boundaries.

It is intended to contain the following layers over the v0.1 foundation and future campaigns:

### Data Layer

The data layer owns data contracts, validation, canonical storage, calendars, sessions, instrument metadata, point-in-time timestamp semantics, quality flags, and query access over local datasets.

It must eventually support:

* instrument master contracts,
* trading calendar and session contracts,
* canonical 1-minute bar contracts,
* quote/trade readiness,
* future L2 snapshot and event/delta schemas,
* local Parquet data,
* DuckDB SQL over Parquet,
* Polars lazy transformations,
* data quality summaries,
* strict `available_ts` semantics.

### Metadata and Registry Layer

The metadata layer owns SQLite-backed local registry state for reproducibility and review.

It must eventually track:

* dataset versions,
* factor registry entries,
* factor versions,
* factor validation runs,
* label versions,
* study runs,
* strategy registry entries,
* strategy versions,
* grid runs,
* ML runs,
* backtest runs,
* artifact manifests,
* promotion decisions,
* review status,
* code hashes,
* config hashes,
* data/factor/label versions,
* engine versions.

SQLite is the local metadata source of truth for v1. No database server is required.

### Factor Layer

The factor layer owns factor specifications, factor lifecycle, factor dependency validation, deterministic computation, factor normalization, factor quality flags, and controlled materialization.

It must enforce:

* `FactorSpec` required fields,
* lifecycle states: `draft`, `candidate`, `validated`, `approved`, `deprecated`,
* no default long-term materialization for draft factor values,
* no label values as factor inputs,
* versioned factor registry records,
* code and config hashes,
* validation artifact links,
* review-gated promotion.

### Label Layer

The label layer owns future-looking labels used for diagnostics and model training. Labels are never live inputs to factors or strategies.

It must support:

* forward return labels,
* MFE and MAE labels,
* target-before-stop labels,
* stop-before-target labels,
* future realized volatility labels,
* future spread/liquidity labels,
* `label_available_ts`,
* session and horizon alignment,
* label versioning,
* leakage prevention.

### Research Diagnostics Layer

The diagnostics layer owns factor and candidate diagnostics that evaluate research behavior without claiming tradability.

It must include diagnostics for:

* directional continuous factors,
* nonlinear bucket factors,
* event trigger factors,
* regime filters,
* execution filters,
* management-related factor behavior.

Diagnostics must include sample sizes, warnings, and interpretation limits.

### Signal and Strategy Layer

The signal and strategy layer converts reviewed factor information into declared signals and strategy specifications.

Strategies may produce:

* entry signal,
* exit signal,
* direction,
* optional confidence score,
* optional desired exposure,
* required factor dependencies.

Strategies must not directly own:

* account equity,
* position sizing,
* fills,
* order lifecycle,
* slippage,
* commission,
* partial take-profit accounting,
* portfolio aggregation.

### Management Layer

The management layer owns position management rules such as stops, targets, partial exits, trailing logic, cooldowns, holding limits, and EOD exits.

It must support:

* fixed stop,
* ATR stop,
* volatility stop,
* target R multiple,
* laddered partial take profit,
* breakeven stop,
* trailing stop,
* time exit,
* EOD exit,
* max trades per day,
* cooldown,
* scale-in,
* scale-out,
* max holding bars,
* risk per trade,
* max position percent.

### Portfolio Layer

The portfolio layer owns signal-to-target conversion, sizing, capital allocation, and portfolio risk constraints.

It must support:

* portfolio target representation,
* position sizing,
* capital allocation,
* risk limits,
* multi-symbol constraints,
* max gross exposure,
* max net exposure,
* future sector/asset constraints,
* future correlation-aware allocation,
* signal-to-target conversion.

### Backtest Layer

The backtest layer owns reference strategy simulation and accounting.

For this campaign, the canonical execution truth is:

**Tier 1 reference 1-minute bar execution truth.**

It must be conservative, deterministic, and point-in-time correct.

It must enforce:

* completed bar data can only be used after `bar_end_ts` plus configured latency,
* signals based on bar `t` cannot execute inside bar `t` by default,
* default execution is next-bar conservative,
* same-bar stop/target ambiguity is conservative,
* costs, spread, and slippage are explicit,
* trade journal and equity outputs are reproducible,
* full trade logs remain local-only unless tiny fixtures.

### Fast Path Layer

The fast path layer owns NumPy/Numba acceleration.

It must never define separate PnL truth.

It may be used for grid scaling only after parity checks prove equivalence against the reference engine for the selected feature set.

Fast path must:

* be acceleration only,
* have deterministic parity fixtures,
* fail closed or route to reference for unsupported features,
* never force reference semantics to change to match fast behavior.

### Experiment Layer

The experiment layer owns bounded local grid execution, management grids, ML/factor-combination experiments, registry recording, reproducibility audits, and run manifests.

It must support:

* factor parameter grids,
* strategy signal grids,
* execution cost grids,
* risk sizing grids,
* position management grids,
* survivor-based management grids,
* ML MVP experiments from versioned factor inputs only,
* local multiprocessing first,
* no required Ray,
* no required MLflow server,
* no hidden failed runs,
* no unbounded search.

### Reporting and Review Layer

The reporting layer owns Markdown, CSV, and optional static HTML summaries suitable for review bundles.

It must support:

* factor cards,
* study reports,
* review bundles,
* source maps,
* release validation reports,
* artifact manifests,
* prohibited-claim checks,
* warnings and known limitations,
* missing artifact visibility,
* failed-step visibility.

### Agent Workflow Layer

The agent workflow layer owns campaign execution discipline, run artifacts, handoffs, reviews, state-machine compliance, STOP handling, semantic done-checks, and artifact policy.

It must support:

* Frontier Harness Generic v3.0 Workflow 2,
* Ralph-driven strict autonomous loop,
* fresh context per phase,
* Codex execution,
* Claude review,
* source-map audits,
* automatic PR and merge where lane policy passes,
* explicit staging only,
* no `git add .`,
* no `git add -A`,
* no raw/heavy artifact commits,
* no test weakening or gaming.

## What the Platform Is Not

`alpha_system` is not:

* a live trading system,
* a broker adapter,
* a paper trading system,
* an order router,
* a production execution platform,
* a performance-marketing tool,
* a claim engine for alpha, profitability, robustness, or tradability,
* a cloud-native data platform in this campaign,
* a paid database project,
* an industrial data-server benchmark,
* a mandatory ClickHouse, QuestDB, DolphinDB, kdb+, ArcticDB, Ray, Dagster, Prefect, or MLflow-server project,
* a web UI project in this campaign,
* an L2 replay engine in this campaign,
* an L3 order book reconstruction engine in this campaign,
* a passive queue-position execution simulator in this campaign,
* a replacement for future execution-quality validation on finalist strategies,
* a system where fast simulation creates a second PnL truth.

This campaign must end with no broker integration, no paper trading, no live trading, no production execution adapter, and no production trading claims.

## Non-Negotiable Architecture Principles

The campaign must enforce the following separations and invariants:

1. **Data is not factor.**
2. **Factor is not signal.**
3. **Signal is not strategy.**
4. **Strategy is not portfolio.**
5. **Portfolio is not execution.**
6. **Backtest is not live trading.**
7. **Fast research simulation is not execution truth.**
8. **Draft factor values are not automatically long-term stored.**
9. **Only validated/reviewed factors may be materialized into the long-term factor store.**
10. **Every result must be reproducible through git commit, code hash, config hash, data version, factor version, label version, engine version, and run manifest.**
11. **No alpha, profitability, robustness, or tradability claims without evidence and review context.**
12. **No candidate promotion without review.**
13. **No broker or live trading in this campaign.**
14. **No uncontrolled strategy explosion.**
15. **No execution-truth ambiguity.**
16. **No raw data committed.**
17. **No heavy artifacts committed.**
18. **No lookahead.**
19. **No hidden failed runs.**
20. **No test weakening or gaming.**

## Finalized Local-First V1 Stack

### Storage

* Local Parquet files for large datasets.
* No S3.
* No cloud object storage.
* No paid database.
* No kdb+.
* No DolphinDB.
* No ClickHouse dependency.
* No QuestDB dependency.
* No ArcticDB dependency.
* No database server required.

### Metadata and Registry

SQLite is the local metadata and registry source of truth for:

* dataset versions,
* factor registry entries,
* factor versions,
* label versions,
* strategy specs,
* model specs,
* experiment runs,
* factor validation runs,
* grid runs,
* ML runs,
* backtest runs,
* artifact paths,
* config hashes,
* code hashes,
* promotion status,
* review status.

### Query and Transformation

* DuckDB for local SQL over Parquet.
* Polars for lazy dataframe pipelines and fast transformations.

### Compute

* Python first.
* NumPy for arrays.
* Numba for hot loops and accelerated fast path.
* Rust is optional later and not required in this campaign.

### Reports

* Markdown.
* CSV.
* Static HTML optional.
* No server required.

### Experiment Tracking

* Local SQLite plus artifact folders.
* MLflow local mode may be considered later.
* MLflow server is not required in this campaign.

### Grid Execution

* Local multiprocessing first.
* Ray optional later.
* Ray is not required in this campaign.

### Orchestration

* Frontier Harness / Ralph owns campaign automation.
* No Dagster or Prefect server dependency in this campaign.

## Deferred Future Upgrades

The following may be considered in later campaigns but must not be required in `ALPHA_SYSTEM_V1`:

* ClickHouse,
* QuestDB,
* ArcticDB,
* DolphinDB,
* kdb+,
* Ray,
* MLflow server,
* Dagster,
* Prefect,
* L2 replay engine,
* L3 order book reconstruction,
* live or paper broker adapter,
* web UI,
* cloud object storage,
* production deployment.

## Frontier Harness Generic v3.0 Workflow 2 Assumptions

This campaign is written for **Frontier Harness Generic v3.0** and the strict **Ralph-driven Workflow 2 autonomous loop**.

The harness is assumed to be:

* WSL2-primary,
* repo-native,
* Ralph-driven,
* Codex-executed,
* Claude-reviewed,
* Git-memory based,
* campaign-contract based,
* fresh-context-per-phase,
* strict state-machine driven,
* STOP-file aware,
* automatic PR/merge capable where lane policy allows,
* run-summary producing,
* handoff and review artifact generating,
* semantic done-check aware,
* artifact-policy enforcing,
* explicit-staging only,
* resistant to raw data and heavy artifact commits,
* resistant to test weakening and gaming,
* resistant to false done claims based only on passing tests.

### Required Workflow 2 State Machine

Every run must use the following state machine:

1. `RUN_INIT`
2. `CAMPAIGN_LOAD`
3. `PHASE_SELECT`
4. `SPEC_GENERATE`
5. `SPEC_VALIDATE`
6. `WORKTREE_CREATE`
7. `CODEX_EXECUTE`
8. `CHECKS_RUN`
9. `HANDOFF_VALIDATE`
10. `CLAUDE_REVIEW`
11. `VERDICT_PARSE`
12. `PR_CREATE`
13. `CI_WAIT`
14. `MERGE_GATE`
15. `MERGE`
16. `DONE_CHECK`
17. `NEXT_PHASE`
18. `CAMPAIGN_DONE_CHECK`
19. `RUN_SUMMARY`

### Required Run Artifacts

Each Workflow 2 run must create or maintain:

* `runs/<run_id>/RUN_GOAL.md`
* `runs/<run_id>/PHASE_PLAN.md`
* `runs/<run_id>/prd.json`
* `runs/<run_id>/progress.txt`
* `runs/<run_id>/state.json`
* `runs/<run_id>/events.jsonl`
* `runs/<run_id>/costs.jsonl`
* `runs/<run_id>/STOP`
* `runs/<run_id>/RUN_SUMMARY.md`
* `runs/<run_id>/phases/<phase_id>/spec.md`
* `runs/<run_id>/phases/<phase_id>/executor_prompt.md`
* `runs/<run_id>/phases/<phase_id>/executor_notes.md`
* `runs/<run_id>/phases/<phase_id>/handoff.md`
* `runs/<run_id>/phases/<phase_id>/review.md`
* `runs/<run_id>/phases/<phase_id>/verdict.json`
* `runs/<run_id>/phases/<phase_id>/checks.json`
* `runs/<run_id>/phases/<phase_id>/repair_attempts/`

### Model Routing

#### ChatGPT Pro GPT-5.5 Thinking

Used for:

* campaign strategy,
* roadmap reasoning,
* post-run reasoning,
* campaign design,
* final strategic review.

#### Claude Opus 4.8 xhigh

Used for:

* phase specs,
* architecture specs,
* semantic reviews,
* done-checks,
* hard debugging,
* campaign decomposition.

#### Claude Sonnet 4.6

Used for:

* source maps,
* verifier support,
* audits,
* mechanical inspections,
* static review support.

#### Codex GPT-5.5 high

Used for:

* primary execution,
* implementation,
* tests,
* repairs,
* refactors,
* artifact generation.

#### Codex GPT-5.4-mini medium

Used for:

* lightweight subagents,
* mechanical exploration,
* local source mapping.

## Lane Policy

### GREEN

Green phases are low-risk phases such as documentation-only or mechanical updates.

Green phases may:

* execute automatically,
* repair automatically,
* create PRs automatically,
* merge automatically when gates pass.

Claude review is optional for Green unless a phase explicitly requires it.

Green still requires:

* checks,
* handoff,
* artifact policy compliance,
* no forbidden files,
* no raw/heavy/local artifact commits.

### YELLOW

Yellow phases are material engineering or research-platform phases.

Yellow phases may:

* execute automatically,
* repair automatically,
* create PRs automatically,
* merge automatically after lane gates pass.

Yellow requires:

* fresh Claude review,
* `PASS` or `PASS_WITH_WARNINGS` verdict,
* checks pass,
* CI pass if configured,
* handoff validation,
* artifact policy pass,
* semantic done-check pass,
* no forbidden files.

Most phases in this campaign are expected to be Yellow.

### RED

Red phases are production, destructive, live, external, costly, or otherwise high-risk operations.

Red is **pre-authorized automatic when scoped**, not banned, but it requires all of the following environment variables:

* `PROJECT_OP_AUTHORIZED`
* `PROJECT_OP_SCOPE`
* `PROJECT_OP_EXPIRES`

This campaign should not require Red phases because it explicitly excludes:

* broker integration,
* paper trading,
* live trading,
* destructive production operations,
* paid cloud infrastructure,
* external costly infrastructure.

If Red scope appears unexpectedly, Ralph must stop or block unless the scoped authorization variables are present and the campaign contract explicitly allows the operation.

## High-Level Phase Categories

The full campaign is expected to be decomposed into approximately 20 to 30 Workflow 2 phases. The phase plan is intentionally generated separately, but this goal file anchors the required categories.

### 1. Harness and Repository Foundation

Purpose:

* create repo bootstrap files,
* establish Frontier/Ralph policy,
* define artifact and git discipline,
* set up campaign control files,
* create local-only directory placeholders,
* document WSL2 path policy.

Expected focus:

* `AGENTS.md`,
* `CLAUDE.md`,
* `frontier.yaml`,
* `ACTIVE_CAMPAIGN.md`,
* `.gitignore`,
* `PROJECT_STATUS.md`,
* campaign directory,
* `specs/`,
* `handoffs/`,
* `reviews/`,
* `runs/`,
* `docs/`,
* `decisions/`,
* `configs/`.

### 2. Architecture and Workspace Foundation

Purpose:

* establish architecture documents,
* define local-first stack decisions,
* create Python package skeleton,
* create CLI skeleton,
* create test harness,
* ensure imports and CLI smoke checks work.

### 3. Core Contracts and Registry Foundation

Purpose:

* define domain contracts,
* implement contract tests,
* create SQLite registry foundation,
* create migrations,
* define reproducibility and hashing utilities.

Required contracts include:

* instrument master,
* trading calendar/session,
* canonical 1-minute bars,
* quote/trade readiness,
* future L2 schemas,
* FactorSpec,
* factor value schema,
* label schema,
* StrategySpec,
* ManagementSpec,
* PortfolioSpec,
* experiment registry records.

### 4. Data and Calendar Foundation

Purpose:

* implement canonical 1-minute schema,
* validate local datasets,
* support sessions and calendars,
* handle timezones,
* handle half-days,
* represent data quality flags,
* enforce `available_ts`.

### 5. Factor and Label Foundation

Purpose:

* implement FactorSpec,
* implement factor registry and lifecycle,
* implement label specs and alignment,
* implement factor compute SDK,
* enforce materialization controls.

### 6. Diagnostics and Reporting Foundation

Purpose:

* implement factor diagnostics,
* generate factor cards,
* produce study reports,
* represent promotion evidence,
* block prohibited claim language.

### 7. Signal, Strategy, and Reference Truth Foundation

Purpose:

* implement signal store,
* implement StrategySpec,
* implement reference 1-minute bar execution truth,
* integrate costs, spread, slippage, conservative fills,
* implement management and portfolio foundations.

### 8. Acceleration and Experiments

Purpose:

* implement fast path,
* prove reference parity,
* build bounded grid engine,
* build management grid and survivor workflow,
* harden experiment registry and reproducibility checks.

### 9. ML and Multi-Asset Readiness

Purpose:

* implement ML/factor-combination MVP,
* enforce versioned factor inputs,
* represent train/validation splits,
* represent walk-forward and purge/embargo readiness,
* add universe and multi-symbol support.

### 10. L2 Readiness and Agent Workflow

Purpose:

* create L2 readiness schemas,
* create L2-derived feature skeleton,
* keep L2 design-only in this campaign,
* build review bundles and source maps,
* document researcher and AI Agent workflows.

### 11. Release Validation and Closeout

Purpose:

* run deterministic local v0.1 validation,
* verify CLI smoke checks,
* verify no-lookahead tests,
* verify parity tests,
* verify artifact policy,
* perform semantic done-check,
* produce closeout docs and final recommendations.

## Target Repository Structure

The campaign should progressively build toward this repository structure:

```text
alpha_system/
  AGENTS.md
  CLAUDE.md
  frontier.yaml
  ACTIVE_CAMPAIGN.md
  README.md
  PROJECT_STATUS.md
  pyproject.toml

  campaigns/
    ALPHA_SYSTEM_V1/
      GOAL.md
      PHASE_PLAN.md
      campaign.yaml
      ACCEPTANCE.md
      RISK_REGISTER.md
      RUNBOOK.md

  specs/
  handoffs/
  reviews/
  runs/
  evals/
  docs/
  decisions/

  data/
    raw/
    canonical/
    factors/
    labels/
    cache/

  metadata/
    alpha_system.sqlite

  artifacts/
    factor_studies/
    strategy_grids/
    ml_experiments/
    management_studies/
    execution_validations/
    review_bundles/
    release_validation/

  configs/
    data/
    universes/
    factors/
    labels/
    studies/
    strategies/
    grids/
    ml/
    management/
    portfolio/
    execution/

  src/
    alpha_system/
      core/
      data/
      factors/
      labels/
      research/
      signals/
      strategies/
      management/
      portfolio/
      backtest/
      execution/
      l2/
      experiments/
      reports/
      cli/

  factors/
    price_action/
    momentum/
    reversal/
    volatility/
    liquidity/
    order_flow/
    microstructure/
    researcher_sandbox/

  strategies/
    templates/
    researcher_sandbox/

  tests/
    unit/
    integration/
    no_lookahead/
    parity/
    performance/
    fixtures/
```

## Local-Only Folders

The campaign must configure and preserve local-only behavior for:

* `data/raw/`
* `data/canonical/`
* `data/factors/`
* `data/labels/`
* `data/cache/`
* `metadata/*.sqlite`
* `metadata/*.db`
* large generated artifacts,
* caches,
* logs,
* temporary grid outputs,
* full trade logs,
* generated report bundles,
* large Parquet files,
* local ML model artifacts,
* local release-validation outputs.

These paths may contain placeholder `.gitkeep` or `README.md` files only when explicitly allowed by phase scope and artifact policy.

## Commit-Eligible Curated Files

The campaign may commit:

* source code,
* configs,
* schemas,
* small fixtures,
* docs,
* specs,
* handoffs,
* reviews,
* small validation summaries,
* curated report summaries,
* source maps,
* small run manifests,
* top config examples if small.

## Non-Goals for This Campaign

This campaign must not implement or require:

* broker integration,
* paper trading,
* live trading,
* order routing,
* external trading account connectivity,
* production execution adapters,
* cloud object storage,
* managed database services,
* mandatory ClickHouse,
* mandatory QuestDB,
* mandatory ArcticDB,
* mandatory DolphinDB,
* mandatory kdb+,
* mandatory Ray,
* mandatory MLflow server,
* Dagster server,
* Prefect server,
* web UI,
* production deployment,
* Kubernetes,
* paid infrastructure,
* real-time market data subscriptions,
* full L2 replay engine execution,
* L3 order book reconstruction,
* passive queue-position execution modeling beyond design readiness,
* alpha or tradability claims without evidence and review.

## Required Domain Contracts

The campaign must eventually define, implement, test, and document the following domain contracts.

### Instrument Master

Required fields:

* `instrument_id`
* `symbol`
* `asset_class`
* `exchange`
* `currency`
* `timezone`
* `tick_size`
* `lot_size`
* `multiplier`
* `start_date`
* `end_date`
* `corporate_action_policy`
* `metadata`

### Trading Calendar / Session Contract

Required fields:

* `calendar_id`
* `trading_date`
* `session_id`
* `open_ts`
* `close_ts`
* `is_holiday`
* `is_half_day`
* `session_type`
* `timezone`
* `quality_flags`

### 1-Minute Bar Contract

Required fields:

* `instrument_id`
* `session_id`
* `bar_index`
* `bar_start_ts`
* `bar_end_ts`
* `event_ts`
* `available_ts`
* `open`
* `high`
* `low`
* `close`
* `volume`
* `vwap`
* `trade_count`
* `bid`
* `ask`
* `spread`
* `source_version`
* `data_version`
* `quality_flags`

Required no-lookahead rules:

* A completed 1-minute bar can only be used after `bar_end_ts` plus configured data latency.
* Signals based on bar `t` cannot execute inside bar `t` unless explicitly modeled with event-level data.
* Default v1 execution uses next-bar conservative execution.
* Same-bar stop/target ambiguity must be handled conservatively.

### Quote/Trade Readiness Contracts

Contracts must prepare for:

* quote data,
* trade prints,
* bid/ask spread,
* future executable labels,
* future cost modeling.

### Future L2 Contracts

Design-only initially.

Required future schema coverage:

* L2 snapshot table,
* L2 event/delta table,
* book levels,
* side,
* price,
* size,
* order count if available,
* `event_ts`,
* `receive_ts`,
* `available_ts`,
* data version,
* quality flags.

### FactorSpec

Required fields:

* `factor_id`
* `name`
* `version`
* `owner`
* `description`
* `input_fields`
* `parameters`
* `frequency`
* `warmup_bars`
* `session_reset`
* `availability_lag`
* `factor_type`
* `evaluation_type`
* `code_hash`
* `config_hash`
* `status`
* `created_at`
* `validation_artifact_path`

Required lifecycle states:

* `draft`
* `candidate`
* `validated`
* `approved`
* `deprecated`

Draft factor values must not be permanently materialized by default.

### Factor Value Schema

Required fields:

* `factor_id`
* `factor_version`
* `instrument_id`
* `event_ts`
* `available_ts`
* `session_id`
* `bar_index`
* `value`
* `normalized_value`
* `quality_flags`
* `data_version`
* `compute_version`

### Label Schema

Required standard labels:

* forward return 1m,
* forward return 3m,
* forward return 5m,
* forward return 10m,
* forward return 30m,
* MFE by horizon,
* MAE by horizon,
* target-before-stop,
* stop-before-target,
* future realized volatility,
* future spread/liquidity labels.

Required fields:

* `label_id`
* `instrument_id`
* `event_ts`
* `horizon`
* `label_type`
* `value`
* `path_metadata`
* `data_version`
* `label_available_ts`

### StrategySpec

Strategies should produce:

* entry signal,
* exit signal,
* direction,
* optional confidence score,
* optional desired exposure,
* required factor dependencies.

Strategies must not directly handle:

* account equity,
* position sizing,
* fills,
* order lifecycle,
* slippage,
* commission,
* partial take-profit accounting,
* portfolio aggregation.

### ManagementSpec

Required support:

* fixed stop,
* ATR stop,
* volatility stop,
* target R multiple,
* laddered partial take profit,
* breakeven stop,
* trailing stop,
* time exit,
* EOD exit,
* max trades per day,
* cooldown,
* scale-in,
* scale-out,
* max holding bars,
* risk per trade,
* max position percent.

### PortfolioSpec

Required support:

* portfolio target,
* position sizing,
* capital allocation,
* risk limits,
* multi-symbol constraints,
* max gross exposure,
* max net exposure,
* sector/asset constraints for future,
* correlation-aware allocation for future,
* signal-to-target conversion.

### Experiment Registry

Required SQLite tables:

* `dataset_versions`
* `factor_registry`
* `factor_versions`
* `factor_validation_runs`
* `label_versions`
* `study_runs`
* `strategy_registry`
* `strategy_versions`
* `grid_runs`
* `ml_runs`
* `backtest_runs`
* `artifact_manifest`
* `promotion_decisions`

Every run record must support:

* run id,
* timestamp,
* git commit,
* code hash,
* config hash,
* data version,
* factor versions,
* label versions,
* engine version,
* parameters,
* artifact paths,
* decision status.

## Required Research Diagnostics

The campaign must eventually support diagnostics for the following categories.

### Directional Continuous Factors

* Pearson IC
* Rank IC
* IC by horizon
* IC decay
* IC by day/week/month
* ICIR
* bucket monotonicity

### Nonlinear Bucket Factors

* bucket forward returns
* tail expectancy
* U-shape profile
* extreme bucket hit rate
* MFE/MAE by bucket

### Event Trigger Factors

* event study
* conditional forward returns
* sample size
* false breakout rate
* target-before-stop probability
* post-event MFE/MAE

### Regime Filters

* with-filter vs without-filter uplift
* coverage
* false rejection rate
* conditional strategy improvement

### Execution Filters

* spread sensitivity
* liquidity sensitivity
* slippage sensitivity
* volume participation
* adverse selection proxy

### Management Features

* target-before-stop
* time-to-target
* time-to-stop
* breakeven usefulness
* trailing stop usefulness

### Factor Reports

All factor reports must eventually include:

* time-of-day stability,
* session segment stability,
* monthly stability,
* volatility regime stability,
* liquidity regime stability,
* correlation to existing factors,
* factor cluster id,
* promotion recommendation,
* sample size,
* warnings,
* data/factor/label versions,
* no-lookahead validation status,
* review status.

## Required Backtest Architecture

The campaign must define and progressively build a multi-tier backtest architecture.

### Tier 0 — Factor Research Engine

* No full trade simulation.
* Fast diagnostics only.
* Used for factor validation and factor cards.
* Must not emit tradability claims.

### Tier 1 — Reference 1-Minute Bar Execution Truth

* Conservative Python implementation.
* Clear accounting truth.
* Next-bar conservative fills by default.
* Spread/slippage model.
* Cost model.
* Stops/targets using conservative bar logic.
* Trade/equity reports.
* Used as canonical truth for 1-minute bar-level strategies.

### Tier 2 — Fast Path Parity

* NumPy/Numba accelerated path.
* Must match reference path on deterministic fixtures.
* Used for grid scaling only after parity.
* Not allowed to define separate PnL truth.

### Tier 3 — Event-Driven Execution Truth Engine

* Future finalist-level engine.
* Orders, fills, latency, partial fills, risk, accounting, trade journal.
* Design readiness may be documented, but implementation is not required for v0.1 unless explicitly authorized by a later campaign.

### Tier 4 — Future L2/L3 Replay Engine

* Future-only execution-sensitive research capability.
* Queue position, order book reconstruction, passive fills, latency model.
* Not part of execution in this campaign.
* L2 work in this campaign is design/schema/skeleton only.

### Backtest Truth Rules

* There must never be two conflicting PnL truths.
* Reference engine is truth for v1 bar-level research.
* Fast path is acceleration only.
* Fast path must pass parity against reference fixtures.
* Grid engine may use fast path only after parity.

## Required Grid, ML, and Management Design

### Grid Types

The platform must support:

* factor parameter grid,
* strategy signal grid,
* execution cost grid,
* risk sizing grid,
* position management grid.

### Grid Discipline

Grid workflows must follow:

1. Factor diagnostics first.
2. Simple signal grid.
3. Simple management baseline.
4. Survivor strategy management grid.
5. Finalist execution validation.

### Required Grid Outputs

Grid outputs must eventually include schemas for:

* `leaderboard.csv`
* `grid_summary.md`
* `monthly_breakdown.csv`
* `cost_sensitivity.csv`
* `top_configs.yaml`
* `rejected_configs.csv`
* `run_manifest.json`

Full grid raw outputs are local-only unless tiny curated fixtures are explicitly allowed.

### ML Layer

ML must consume factor versions from the factor store.

ML must not use raw ad hoc columns.

ML support design should include:

* linear model,
* ridge/lasso,
* LightGBM/XGBoost later,
* random forest later,
* meta-labeling,
* ensemble,
* regime-conditioned model,
* IC-weighted factor score,
* orthogonalized factor score.

Required ML contracts:

* `FeatureSetSpec`
* `LabelSpec`
* `ModelSpec`
* train/validation split,
* walk-forward split,
* purge/embargo readiness,
* score-to-portfolio conversion,
* ML experiment registry.

## Required CLI Commands

The campaign must eventually phase in these CLI commands:

* `alpha data validate`
* `alpha data build-bars`
* `alpha factor validate`
* `alpha factor materialize`
* `alpha study run`
* `alpha grid run`
* `alpha management grid`
* `alpha ml run`
* `alpha backtest run`
* `alpha report build`
* `alpha registry status`

For each command, the phase introducing it must specify:

* purpose,
* inputs,
* outputs,
* artifacts,
* validation checks,
* expected registry behavior when applicable,
* artifact policy restrictions.

## Required Testing Categories

The campaign must require targeted tests for:

* schema tests,
* no-lookahead tests,
* `available_ts` tests,
* label alignment tests,
* session reset tests,
* timezone tests,
* half-day tests,
* data quality tests,
* factor deterministic tests,
* factor dependency tests,
* factor registry tests,
* factor lifecycle tests,
* grid expansion tests,
* management accounting tests,
* cost model tests,
* reference simulator sanity tests,
* fast/reference parity tests,
* CLI smoke tests,
* artifact policy tests,
* reproducibility tests,
* source map tests,
* review bundle tests,
* experiment registry tests.

Tests must not be vague. Phase specs must identify exact test categories relevant to the phase.

## Artifact Policy

### Never Commit

The campaign must never commit:

* raw data,
* canonical data,
* materialized factor values except tiny fixtures,
* materialized label values except tiny fixtures,
* caches,
* full grid raw outputs,
* full trade logs for non-fixture runs,
* large Parquet files,
* large databases,
* local SQLite database files,
* logs,
* temporary files,
* generated local-only heavy artifacts,
* generated report bundles,
* local model binaries,
* benchmark logs,
* temporary multiprocessing outputs.

### May Commit When Curated and Small

The campaign may commit:

* configs,
* schemas,
* small fixtures,
* summaries,
* curated reports,
* source maps,
* handoff docs,
* validation summaries,
* top config samples if small,
* docs,
* phase specs,
* reviews,
* run manifests if small.

Every phase must include artifact policy and explicit staging requirements.

## Git and Staging Policy

The campaign must enforce:

* no `git add .`,
* no `git add -A`,
* explicit curated staging only,
* no force push unless explicitly authorized by a phase, which this campaign does not expect,
* no raw data staged,
* no heavy artifacts staged,
* no local DB staged,
* no caches/logs staged,
* no hidden failed runs,
* no test weakening or gaming.

## Success Definition

The campaign is successful when `alpha_system` has a local-first v0.1 foundation that:

1. Can be operated under Frontier Harness Generic v3.0 Workflow 2.
2. Has clear repo, git, artifact, review, and merge policies.
3. Defines and validates core data contracts.
4. Provides SQLite-backed metadata and experiment registry foundations.
5. Separates data, factors, labels, signals, strategies, management, portfolio, and execution.
6. Provides factor specs, factor registry, factor lifecycle, and controlled factor materialization.
7. Provides label specs and label alignment checks.
8. Provides factor compute and diagnostics workflows.
9. Produces factor cards and evidence artifacts without overclaiming tradability.
10. Provides StrategySpec and signal store abstractions.
11. Provides a conservative reference 1-minute bar execution truth.
12. Provides cost, spread, and slippage modeling.
13. Provides position management and portfolio sizing foundations.
14. Provides fast path acceleration only with deterministic parity against reference truth.
15. Provides bounded grid and management-grid execution.
16. Provides experiment registry hardening and reproducibility checks.
17. Provides ML/factor-combination MVP using versioned factor store inputs only.
18. Provides multi-symbol/universe support readiness.
19. Provides L2 data schema and feature readiness without live/L2 execution scope creep.
20. Provides review bundles, source maps, onboarding docs, and final v0.1 validation artifacts.
21. Passes semantic done-check beyond test results.
22. Commits no raw data, heavy artifacts, local databases, caches, logs, or temporary outputs.
23. Contains no broker/live trading scope.
24. Contains no unsupported alpha/profitability/tradability claims.

## Final Campaign Outcome

At completion, the repository should represent a serious local-first Alpha Research Platform foundation suitable for future campaigns that may add:

* richer data ingestion,
* additional factor libraries,
* larger datasets,
* more robust finalist event-driven validation,
* optional L2 replay research,
* optional external experiment-tracking integrations,
* optional distributed compute,
* optional web UI,
* optional paper/live trading in a separate explicitly authorized campaign.

This campaign ends with no live trading, no broker integration, no production trading claims, and no alpha/tradability claims beyond evidence-backed research artifacts and review context.
