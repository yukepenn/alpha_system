
# Active Campaign

## Active Campaign ID

`ALPHA_SYSTEM_V1`

## Repository

* **Repo name:** `alpha_system`
* **Repo path:** `~/projects/alpha_system`
* **Host environment:** Windows host
* **Primary runtime:** WSL2 Ubuntu
* **Required active worktree location:** WSL2 Linux filesystem
* **Forbidden active worktree locations:** `/mnt/c`, `/mnt/d`, `/mnt/e`, OneDrive, Windows-synced folders, network drives, temporary directories

## Project Profile

* **Primary profile:** `trading_research`
* **Secondary profile:** `research`
* **Project type:** clean-slate local-first Alpha Research Platform
* **Initial workflow:** 1-minute intraday session research
* **Future readiness:** multi-asset-ready and Level-2-ready
* **Campaign target:** local-first v0.1 foundation
* **Broker/live trading:** out of scope
* **Paper trading:** out of scope
* **Production trading claims:** out of scope
* **Alpha/tradability claims without evidence:** prohibited

## Current Phase Pointer

* **Current campaign:** `ALPHA_SYSTEM_V1`
* **Current phase:** `ASV1-P00`
* **Current phase name:** Repo and Harness Bootstrap Policy
* **Phase state:** `not_started`
* **Next action:** Ralph Workflow 2 `RUN_INIT`

Ralph must update this pointer as phases complete, block, or require repair.

## Workflow Mode

* **Harness:** Frontier Harness Generic v3.0
* **Workflow:** Workflow 2
* **Driver:** Ralph
* **Executor:** Codex
* **Reviewer:** Claude
* **State machine:** strict
* **Fresh context per phase:** required
* **Handoff per phase:** required
* **Semantic done-check:** required
* **STOP file support:** required
* **Auto PR / auto merge:** allowed where lane policy passes
* **Artifact discipline:** required
* **Explicit staging only:** required
* **`git add .`:** forbidden
* **`git add -A`:** forbidden

## Required State Machine

Every Workflow 2 run must use this state machine:

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

Ralph must not mark a phase done based only on passing tests.

## Lane Policy Summary

### GREEN

Green phases are low-risk, usually documentation-only or mechanical changes.

Green phases may auto execute, repair, create PRs, and merge when all applicable gates pass.

Required for Green:

* checks pass,
* handoff exists,
* artifact policy passes,
* no forbidden files are staged,
* review passes if review is requested or required by the phase.

Claude review is optional for Green unless the phase explicitly requires it.

### YELLOW

Yellow phases are material engineering or research-platform work.

Yellow phases may auto execute, repair, create PRs, and merge after all gates pass.

Required for Yellow:

* checks pass,
* handoff validates,
* fresh Claude review exists,
* review verdict is `PASS` or `PASS_WITH_WARNINGS`,
* artifact policy passes,
* no forbidden files are staged,
* semantic done-check passes,
* CI passes if configured.

Most `ALPHA_SYSTEM_V1` phases are expected to be Yellow.

### RED

Red phases are production, destructive, live, external, or costly operations.

Red is pre-authorized automatic when scoped; it is not banned. Red requires all scoped authorization variables:

* `PROJECT_OP_AUTHORIZED`
* `PROJECT_OP_SCOPE`
* `PROJECT_OP_EXPIRES`

This campaign should not require Red phases because broker/live trading, destructive production operations, and costly external infrastructure are out of scope.

If a Red operation appears unexpectedly, Ralph must stop or block unless:

* the scoped authorization variables are present,
* the scope matches the campaign contract,
* the operation does not violate the campaign’s non-goals.

## Model Routing Summary

### ChatGPT Pro GPT-5.5 Thinking

Used for:

* strategy,
* roadmap,
* post-run reasoning,
* campaign design,
* final strategic review.

### Claude Opus 4.8 xhigh

Used for:

* phase specs,
* architecture specs,
* semantic reviews,
* done-checks,
* hard debugging,
* campaign decomposition.

### Claude Sonnet 4.6

Used for:

* source maps,
* verifier support,
* audits,
* mechanical inspections,
* static review support.

### Codex GPT-5.5 high

Used for:

* primary execution,
* implementation,
* tests,
* repairs,
* refactors,
* artifact generation.

### Codex GPT-5.4-mini medium

Used for:

* lightweight subagents,
* mechanical exploration,
* local source mapping.

## Active Campaign Files

Generated in Prompt 1:

* Goal: `campaigns/ALPHA_SYSTEM_V1/GOAL.md`
* Acceptance criteria: `campaigns/ALPHA_SYSTEM_V1/ACCEPTANCE.md`
* Active campaign pointer: `ACTIVE_CAMPAIGN.md`

To be generated in later prompts before full Workflow 2 execution:

* Phase plan: `campaigns/ALPHA_SYSTEM_V1/PHASE_PLAN.md`
* Machine control: `campaigns/ALPHA_SYSTEM_V1/campaign.yaml`
* Risk register: `campaigns/ALPHA_SYSTEM_V1/RISK_REGISTER.md`
* Runbook: `campaigns/ALPHA_SYSTEM_V1/RUNBOOK.md`

Ralph must not assume missing campaign files are complete. Missing later-prompt files are expected only during Prompt 1 contract generation and must be created before autonomous campaign execution proceeds beyond bootstrap planning.

## Acceptance Gate Summary

The campaign is accepted only when all major gates pass:

1. Harness/repo foundation.
2. Architecture and workspace foundation.
3. Data contracts.
4. Data validation, calendar, session, timezone, and quality handling.
5. SQLite metadata registry.
6. Reproducibility and artifact manifest utilities.
7. Factor registry and lifecycle.
8. Factor compute SDK and materialization controls.
9. Label store and label alignment.
10. Factor diagnostics.
11. Factor cards and promotion evidence.
12. Signal store and StrategySpec.
13. Reference 1-minute backtest truth.
14. Cost, spread, slippage, and conservative fill models.
15. Position management.
16. Portfolio and sizing layer.
17. Fast path parity.
18. Bounded grid engine.
19. Management grid and survivor workflow.
20. Experiment registry hardening.
21. ML/factor-combination MVP.
22. Multi-symbol/universe readiness.
23. L2 readiness schemas and feature skeleton.
24. Review bundle/source map/reporting framework.
25. Researcher and AI Agent onboarding docs.
26. End-to-end local v0.1 validation.
27. Campaign closeout and semantic done-check.

Passing tests alone is not sufficient. Semantic review, no-lookahead verification, reproducibility checks, and artifact-policy compliance are required.

## Non-Negotiable Project Rules

* Data is not factor.
* Factor is not signal.
* Signal is not strategy.
* Strategy is not portfolio.
* Portfolio is not execution.
* Backtest is not live trading.
* Reference backtest is canonical truth.
* Fast path is acceleration only.
* Draft factor values are not long-term materialized by default.
* Only validated/reviewed factors may be materialized into long-term factor store.
* Candidate promotion requires review.
* Every result must be reproducible through git commit, code hash, config hash, data version, factor version, label version, engine version, and run manifest.
* No raw data commits.
* No heavy artifact commits.
* No local SQLite DB commits.
* No hidden failed runs.
* No test weakening or gaming.
* No uncontrolled strategy explosion.
* No execution-truth ambiguity.
* No broker/live trading.
* No paper trading.
* No alpha/tradability claims without evidence and review context.
* No same-bar optimistic execution by default.
* No fast path usage without parity.
* No L2 replay or live L2 execution scope in this campaign.

## Local-First Stack Summary

`ALPHA_SYSTEM_V1` uses the following finalized v1 stack:

* **Large data:** local Parquet
* **Metadata/registry:** SQLite
* **SQL over local files:** DuckDB
* **Dataframe pipelines:** Polars
* **Compute arrays:** NumPy
* **Fast path:** Numba
* **Reports:** Markdown, CSV, optional static HTML
* **Experiment tracking:** local SQLite plus artifact folders
* **Grid execution:** local multiprocessing first
* **Orchestration:** Frontier Harness / Ralph

The campaign must not require:

* S3,
* cloud object storage,
* paid databases,
* database servers,
* ClickHouse,
* QuestDB,
* ArcticDB,
* DolphinDB,
* kdb+,
* Ray,
* MLflow server,
* Dagster,
* Prefect,
* web UI,
* broker APIs,
* live market data subscriptions.

## Artifact Policy Summary

### Never Commit

* raw data,
* canonical data,
* materialized factor values except tiny fixtures,
* materialized label values except tiny fixtures,
* caches,
* local SQLite DBs,
* full grid raw outputs,
* full trade logs,
* large Parquet files,
* large databases,
* logs,
* temporary files,
* generated heavy artifacts,
* generated review bundles,
* local ML model binaries,
* benchmark logs.

### May Commit When Curated and Small

* source code,
* configs,
* schemas,
* docs,
* specs,
* handoffs,
* reviews,
* small fixtures,
* small validation summaries,
* curated report summaries,
* source maps,
* small run manifests,
* top config examples if small.

## Stop and Resume Notes

Ralph must respect the active run STOP file:

```text
runs/<run_id>/STOP
```

If STOP indicates a requested stop:

* do not start a new phase,
* do not create a PR,
* do not merge,
* do not run destructive cleanup,
* update `state.json`,
* update `progress.txt`,
* update `RUN_SUMMARY.md`.

To resume:

1. Inspect `runs/<run_id>/state.json`.
2. Inspect `runs/<run_id>/progress.txt`.
3. Inspect the latest phase handoff.
4. Inspect the latest review and verdict.
5. Confirm STOP reason is resolved.
6. Confirm worktree path is valid WSL2 path.
7. Confirm artifact policy is clean.
8. Resume from the recorded Workflow 2 state.

Do not resume by blindly rerunning from the beginning unless the run is intentionally abandoned and a new run is created.

## Required Run Artifacts

Every Workflow 2 run must create or maintain:

```text
runs/<run_id>/RUN_GOAL.md
runs/<run_id>/PHASE_PLAN.md
runs/<run_id>/prd.json
runs/<run_id>/progress.txt
runs/<run_id>/state.json
runs/<run_id>/events.jsonl
runs/<run_id>/costs.jsonl
runs/<run_id>/STOP
runs/<run_id>/RUN_SUMMARY.md
runs/<run_id>/phases/<phase_id>/spec.md
runs/<run_id>/phases/<phase_id>/executor_prompt.md
runs/<run_id>/phases/<phase_id>/executor_notes.md
runs/<run_id>/phases/<phase_id>/handoff.md
runs/<run_id>/phases/<phase_id>/review.md
runs/<run_id>/phases/<phase_id>/verdict.json
runs/<run_id>/phases/<phase_id>/checks.json
runs/<run_id>/phases/<phase_id>/repair_attempts/
```

## Current Scope Boundary

Broker integration, paper trading, live trading, order routing, external trading account connectivity, and production trading operations are out of scope for `ALPHA_SYSTEM_V1`.

This campaign builds a local-first Alpha Research Platform foundation for research, validation, reproducibility, evidence generation, review bundles, and AI Agent workflows only.

No part of this campaign may claim that any factor, signal, strategy, model, or configuration is profitable, tradable, robust, production-ready, market-beating, or suitable for live deployment without later evidence and explicit review in a separate authorized campaign.
