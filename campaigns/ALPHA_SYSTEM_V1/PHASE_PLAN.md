# ALPHA_SYSTEM_V1 Phase Plan

## Purpose

This file defines the machine-executable Workflow 2 phase plan for the clean-slate repository:

```text
~/projects/alpha_system
```

The campaign builds a local-first, 1-minute-session-first Alpha Research Platform foundation for human researchers and AI Agents.

This is not merely a backtester campaign. It must progressively build the foundations for:

* data contracts,
* canonical 1-minute research data,
* calendars and sessions,
* factor registry and versioning,
* factor compute and diagnostics,
* label store and alignment,
* signal and strategy specifications,
* reference backtest truth,
* cost/slippage/conservative execution,
* management and portfolio layers,
* fast-path parity,
* bounded grids,
* ML/factor-combination experiments,
* multi-symbol readiness,
* Level-2 readiness,
* review bundles,
* reproducibility,
* artifact discipline,
* human researcher workflow,
* AI Agent workflow.

The plan is designed for **Frontier Harness Generic v3.0**, using the strict **Ralph-driven Workflow 2 autonomous loop**.

Ralph must execute this campaign phase by phase. Each phase must produce a spec, execute in an isolated worktree or branch, run checks, produce handoff artifacts, receive review when required, pass merge gates, and update run state before the next phase starts.

---

## Global Phase Rules

These rules apply to every phase, even when repeated in phase-specific language.

### Workflow Rules

Every phase must run under Frontier Harness Generic v3.0 Workflow 2 using the required state machine:

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

Every phase must create or update its run artifacts under:

```text
runs/<run_id>/phases/<phase_id>/
```

Required per-phase artifacts:

```text
spec.md
executor_prompt.md
executor_notes.md
handoff.md
review.md
verdict.json
checks.json
repair_attempts/
```

For Green phases, `review.md` and `verdict.json` may record that review was skipped only if the phase permits skipping review and Ralph records the reason.

### Repo Path Rules

The active repository and active worktree must live on the WSL2 Linux filesystem.

Required repo path:

```text
~/projects/alpha_system
```

Forbidden active worktree locations:

```text
/mnt/c
/mnt/d
/mnt/e
OneDrive
Windows-synced folders
network drives
temporary directories
```

A path violation is a stop condition.

### Git Rules

Every phase must use explicit staging only.

Forbidden commands:

```bash
git add .
git add -A
```

Every phase must stage curated files explicitly. No phase may force push unless a later campaign explicitly authorizes it; this campaign does not require force push.

### Artifact Rules

Never commit:

* raw data,
* canonical generated data,
* materialized factor values except tiny deterministic fixtures,
* materialized label values except tiny deterministic fixtures,
* caches,
* local SQLite databases,
* generated `.db` files,
* full grid outputs,
* full trade logs,
* large Parquet files,
* large CSVs,
* logs,
* temporary files,
* generated local-only heavy artifacts,
* generated review bundles,
* local ML model binaries,
* benchmark logs.

May commit when curated and small:

* source code,
* configs,
* schemas,
* small deterministic fixtures,
* docs,
* specs,
* handoffs,
* reviews,
* small validation summaries,
* curated report summaries,
* source maps,
* small run manifests,
* top config examples if small.

### Domain Boundary Rules

Every phase must preserve the following separations:

1. Data is not factor.
2. Factor is not signal.
3. Signal is not strategy.
4. Strategy is not portfolio.
5. Portfolio is not execution.
6. Backtest is not live trading.
7. Fast research simulation is not execution truth.
8. Draft factor values are not automatically long-term stored.
9. Only validated/reviewed factors may be materialized into the long-term factor store.
10. Every result must be reproducible through git commit, code hash, config hash, data version, factor version, label version, engine version, and run manifest.

### Non-Negotiable Scope Rules

Every phase must explicitly avoid:

* broker integration,
* paper trading,
* live trading,
* order routing,
* production execution adapters,
* alpha/profitability/tradability claims without evidence and review context,
* candidate promotion without review,
* uncontrolled strategy explosion,
* execution-truth ambiguity,
* lookahead,
* hidden failed runs,
* test weakening or gaming,
* raw data commits,
* heavy artifact commits,
* local DB commits,
* unbounded grids,
* silent fast/reference divergence,
* L2 replay scope creep.

### Review Rules

* Green phases: Claude review optional unless required by the phase.
* Yellow phases: fresh Claude Opus 4.8 xhigh review required.
* Red phases: require scoped authorization and review. This campaign should not need Red phases.

Allowed review verdicts:

* `PASS`
* `PASS_WITH_WARNINGS`
* `REWORK`
* `BLOCKED`

Merge may proceed only for `PASS` or `PASS_WITH_WARNINGS`, and only when all phase gates pass.

### Repair Rules

If checks or review fail:

* Ralph must route to bounded repair loop.
* Repair attempts must be recorded under `repair_attempts/`.
* The phase must not be marked done until repaired and reviewed if required.
* If repair attempts are exhausted, the phase must be marked `BLOCKED`.
* A blocked phase must have a blocked handoff and must not be falsely marked complete.

### Validation Rules

Passing tests alone is insufficient.

Each phase done-check must verify:

* scope compliance,
* artifact policy,
* no-lookahead policy where relevant,
* domain boundary integrity,
* no unsupported claims,
* no hidden failed runs,
* no test weakening,
* review and handoff completeness.

---

## Phase Table Summary

| Phase ID | Phase Name                                             |   Lane | Dependencies       | Review Required | Auto PR | Auto Merge |
| -------- | ------------------------------------------------------ | -----: | ------------------ | --------------: | ------: | ---------: |
| ASV1-P00 | Repo and Harness Bootstrap Policy                      | YELLOW | none               |             yes |     yes |        yes |
| ASV1-P01 | Frontier Harness Baseline Files                        | YELLOW | ASV1-P00           |             yes |     yes |        yes |
| ASV1-P02 | Architecture Baseline and Local-First PLAN.md          | YELLOW | ASV1-P01           |             yes |     yes |        yes |
| ASV1-P03 | Python Workspace and Package Skeleton                  | YELLOW | ASV1-P02           |             yes |     yes |        yes |
| ASV1-P04 | Core Contracts and Schema Primitives                   | YELLOW | ASV1-P03           |             yes |     yes |        yes |
| ASV1-P05 | SQLite Metadata Registry MVP                           | YELLOW | ASV1-P04           |             yes |     yes |        yes |
| ASV1-P06 | Canonical 1-Minute Data Layer                          | YELLOW | ASV1-P04, ASV1-P05 |             yes |     yes |        yes |
| ASV1-P07 | Calendar, Session, and Data Quality Layer              | YELLOW | ASV1-P06           |             yes |     yes |        yes |
| ASV1-P08 | Data Validation CLI and Local Fixture Policy           | YELLOW | ASV1-P06, ASV1-P07 |             yes |     yes |        yes |
| ASV1-P09 | FactorSpec, Factor Registry, and Lifecycle             | YELLOW | ASV1-P05, ASV1-P08 |             yes |     yes |        yes |
| ASV1-P10 | Label Store MVP                                        | YELLOW | ASV1-P05, ASV1-P08 |             yes |     yes |        yes |
| ASV1-P11 | Factor Compute SDK MVP                                 | YELLOW | ASV1-P09, ASV1-P10 |             yes |     yes |        yes |
| ASV1-P12 | Intraday Factor Diagnostics Engine                     | YELLOW | ASV1-P11           |             yes |     yes |        yes |
| ASV1-P13 | Factor Card and Report Generation                      | YELLOW | ASV1-P12           |             yes |     yes |        yes |
| ASV1-P14 | Signal Store and StrategySpec Layer                    | YELLOW | ASV1-P11, ASV1-P13 |             yes |     yes |        yes |
| ASV1-P15 | Reference 1-Minute Backtest Truth                      | YELLOW | ASV1-P14           |             yes |     yes |        yes |
| ASV1-P16 | Cost, Slippage, and Conservative Execution Semantics   | YELLOW | ASV1-P15           |             yes |     yes |        yes |
| ASV1-P17 | Position Management Module                             | YELLOW | ASV1-P16           |             yes |     yes |        yes |
| ASV1-P18 | Portfolio Target and Sizing Layer                      | YELLOW | ASV1-P17           |             yes |     yes |        yes |
| ASV1-P19 | Fast Path and Reference Parity                         | YELLOW | ASV1-P18           |             yes |     yes |        yes |
| ASV1-P20 | Strategy Grid Engine MVP                               | YELLOW | ASV1-P19           |             yes |     yes |        yes |
| ASV1-P21 | Management Grid Engine                                 | YELLOW | ASV1-P20           |             yes |     yes |        yes |
| ASV1-P22 | Experiment Registry Hardening                          | YELLOW | ASV1-P21           |             yes |     yes |        yes |
| ASV1-P23 | ML and Factor Combination MVP                          | YELLOW | ASV1-P22           |             yes |     yes |        yes |
| ASV1-P24 | Multi-Symbol Universe Support                          | YELLOW | ASV1-P23           |             yes |     yes |        yes |
| ASV1-P25 | L2 Readiness Schema and Design                         | YELLOW | ASV1-P24           |             yes |     yes |        yes |
| ASV1-P26 | L2-Derived Feature Pipeline Skeleton                   | YELLOW | ASV1-P25           |             yes |     yes |        yes |
| ASV1-P27 | Review Bundles, Source Maps, and Audit Reports         | YELLOW | ASV1-P26           |             yes |     yes |        yes |
| ASV1-P28 | Researcher and AI Agent Onboarding                     |  GREEN | ASV1-P27           |        optional |     yes |        yes |
| ASV1-P29 | End-to-End Local v0.1 Validation and Campaign Closeout | YELLOW | ASV1-P28           |             yes |     yes |        yes |

---

## Acceptance Gate Summary

The campaign progresses through the following gates.

| Gate                                  | Phases               | Exit Requirement                                                                                                       |
| ------------------------------------- | -------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Harness and repo foundation           | ASV1-P00 to ASV1-P01 | Repo is Workflow 2 compatible, WSL2 path policy exists, artifact policy is enforceable, explicit staging policy exists |
| Architecture and workspace foundation | ASV1-P02 to ASV1-P03 | Local-first architecture is documented and importable Python package/test harness exists                               |
| Contracts and registry foundation     | ASV1-P04 to ASV1-P05 | Domain contracts and SQLite registry MVP exist and are tested                                                          |
| Data/calendar foundation              | ASV1-P06 to ASV1-P08 | Canonical 1-minute bars, sessions, validation CLI, and fixture policy exist                                            |
| Factor/label foundation               | ASV1-P09 to ASV1-P11 | Factor registry, label store, and factor compute SDK exist with no-lookahead controls                                  |
| Diagnostics and factor evidence       | ASV1-P12 to ASV1-P13 | Factor diagnostics and factor cards exist without tradability claims                                                   |
| Signal/strategy/reference truth       | ASV1-P14 to ASV1-P16 | StrategySpec, signal store, reference engine, and conservative cost/fill semantics exist                               |
| Management and portfolio              | ASV1-P17 to ASV1-P18 | Management and portfolio layers exist without collapsing into strategy or execution                                    |
| Fast path and grids                   | ASV1-P19 to ASV1-P21 | Fast path is parity-gated and bounded grids exist                                                                      |
| Registry/ML/multi-symbol              | ASV1-P22 to ASV1-P24 | Experiment registry is hardened, ML MVP uses versioned factors, universe support exists                                |
| L2 readiness                          | ASV1-P25 to ASV1-P26 | L2 schemas and feature skeleton exist as design/fixture-only scope                                                     |
| Reporting and agent workflow          | ASV1-P27 to ASV1-P28 | Review bundles, source maps, audit reports, and onboarding docs exist                                                  |
| Release validation and closeout       | ASV1-P29             | End-to-end fixture validation passes and semantic closeout is complete or truthfully blocked                           |

---

# Detailed Phase Specs

---

## ASV1-P00 — Repo and Harness Bootstrap Policy

### Phase ID

`ASV1-P00`

### Phase Name

Repo and Harness Bootstrap Policy

### Lane

YELLOW

### Dependencies

None.

### Purpose

Create the initial repository policy foundation for `alpha_system` and make the clean-slate repo safe for Frontier Harness Generic v3.0 Workflow 2 execution.

This phase establishes repo identity, WSL2 path policy, local-only artifact policy, explicit staging policy, campaign directory layout, and the first project status baseline.

### Scope

Create or update:

* `README.md`
* `PROJECT_STATUS.md`
* `.gitignore`
* `.gitattributes` if needed for text normalization
* `.editorconfig` if desired by repo convention
* `campaigns/ALPHA_SYSTEM_V1/GOAL.md`
* `campaigns/ALPHA_SYSTEM_V1/ACCEPTANCE.md`
* `campaigns/ALPHA_SYSTEM_V1/PHASE_PLAN.md`
* `campaigns/ALPHA_SYSTEM_V1/campaign.yaml`
* `campaigns/ALPHA_SYSTEM_V1/RISK_REGISTER.md`
* `campaigns/ALPHA_SYSTEM_V1/RUNBOOK.md`
* `ACTIVE_CAMPAIGN.md`
* top-level placeholder directories:

  * `specs/`
  * `handoffs/`
  * `reviews/`
  * `runs/`
  * `evals/`
  * `docs/`
  * `decisions/`
  * `configs/`
  * `data/raw/`
  * `data/canonical/`
  * `data/factors/`
  * `data/labels/`
  * `data/cache/`
  * `metadata/`
  * `artifacts/`

Allowed placeholders:

* `.gitkeep` or `README.md` files in empty local-only directories when required to preserve structure.

The phase must document:

* repo path `~/projects/alpha_system`,
* WSL2 Linux filesystem requirement,
* `/mnt/c`, OneDrive, Windows-synced folders, network drives, and temp dirs as forbidden active worktree locations,
* no `git add .`,
* no `git add -A`,
* no raw data commits,
* no heavy artifact commits,
* no local SQLite DB commits,
* no broker/live trading,
* no alpha/tradability claims without evidence,
* no hidden failed runs,
* no test weakening or gaming.

### Non-Goals

* Do not create Python package source.
* Do not add domain contracts.
* Do not implement data ingestion.
* Do not implement factor computation.
* Do not implement registry migrations.
* Do not implement backtesting.
* Do not create real raw/canonical/factor/label data.
* Do not create SQLite DB files.
* Do not add broker, paper trading, live trading, or production execution files.

### Expected Files / Directories

Expected new or updated files:

* `README.md`
* `PROJECT_STATUS.md`
* `.gitignore`
* `ACTIVE_CAMPAIGN.md`
* `campaigns/ALPHA_SYSTEM_V1/GOAL.md`
* `campaigns/ALPHA_SYSTEM_V1/ACCEPTANCE.md`
* `campaigns/ALPHA_SYSTEM_V1/PHASE_PLAN.md`
* `campaigns/ALPHA_SYSTEM_V1/campaign.yaml`
* `campaigns/ALPHA_SYSTEM_V1/RISK_REGISTER.md`
* `campaigns/ALPHA_SYSTEM_V1/RUNBOOK.md`

Expected directories:

* `campaigns/ALPHA_SYSTEM_V1/`
* `specs/`
* `handoffs/`
* `reviews/`
* `runs/`
* `evals/`
* `docs/`
* `decisions/`
* `configs/`
* `data/raw/`
* `data/canonical/`
* `data/factors/`
* `data/labels/`
* `data/cache/`
* `metadata/`
* `artifacts/`

### Forbidden Changes

* No source implementation.
* No raw data committed.
* No canonical data committed.
* No materialized factor values committed.
* No materialized label values committed.
* No heavy artifacts committed.
* No local SQLite DB committed.
* No broker/live trading scope.
* No alpha/profitability/tradability claims.
* No uncontrolled scope expansion.
* No hidden failed runs.
* No test weakening or gaming.
* No `git add .`.
* No `git add -A`.

### Validation Commands

Ralph must run and record:

```bash
git status --short
test -f README.md
test -f PROJECT_STATUS.md
test -f .gitignore
test -f ACTIVE_CAMPAIGN.md
test -f campaigns/ALPHA_SYSTEM_V1/GOAL.md
test -f campaigns/ALPHA_SYSTEM_V1/ACCEPTANCE.md
test -f campaigns/ALPHA_SYSTEM_V1/PHASE_PLAN.md
test -f campaigns/ALPHA_SYSTEM_V1/campaign.yaml
test -f campaigns/ALPHA_SYSTEM_V1/RISK_REGISTER.md
test -f campaigns/ALPHA_SYSTEM_V1/RUNBOOK.md
test -d specs
test -d handoffs
test -d reviews
test -d runs
test -d evals
test -d docs
test -d decisions
test -d configs
test -d data/raw
test -d data/canonical
test -d data/factors
test -d data/labels
test -d data/cache
test -d metadata
test -d artifacts
git check-ignore -v data/raw/example.parquet || true
git check-ignore -v data/canonical/example.parquet || true
git check-ignore -v data/factors/example.parquet || true
git check-ignore -v data/labels/example.parquet || true
git check-ignore -v metadata/alpha_system.sqlite || true
git check-ignore -v artifacts/example_large_output.csv || true
```

If hooks or artifact policy scripts are not yet available, record that they are deferred to ASV1-P01.

### Artifact Policy

Commit only policy files, campaign files, docs, and placeholder `.gitkeep` or `README.md` files if needed.

Do not commit:

* raw data,
* generated canonical data,
* materialized factor or label data,
* local DB files,
* logs,
* caches,
* generated heavy artifacts,
* full report bundles.

Stage explicit files only. Never use `git add .` or `git add -A`.

### Done Criteria

* Initial repo structure exists.
* Campaign directory exists.
* `ACTIVE_CAMPAIGN.md` points to `ALPHA_SYSTEM_V1`.
* `.gitignore` protects local-only folders and generated artifacts.
* WSL2 path policy is documented.
* Explicit staging policy is documented.
* No forbidden files are staged or committed.
* Handoff exists and records validation results.
* Claude review passes.

### Handoff Requirements

Create:

```text
handoffs/ASV1-P00.md
runs/<run_id>/phases/ASV1-P00/handoff.md
```

Handoff must include:

* summary of created repo foundation,
* directory tree summary,
* files changed,
* validation commands and results,
* artifact policy confirmation,
* explicit staging confirmation,
* statement that no raw data/heavy artifacts/local DBs were committed,
* statement that broker/live trading is out of scope,
* known limitations,
* review focus.

### Review Requirements

Claude Opus 4.8 xhigh review required.

Review must verify:

* Workflow 2 compatibility,
* WSL2 path policy,
* artifact policy,
* explicit staging policy,
* no forbidden files,
* no broker/live scope,
* no unsupported claims.

### Auto-Merge Eligibility

Auto PR and auto merge allowed if:

* validation commands pass,
* handoff validates,
* review verdict is `PASS` or `PASS_WITH_WARNINGS`,
* artifact policy passes,
* no forbidden files are staged,
* semantic done-check passes.

---

## ASV1-P01 — Frontier Harness Baseline Files

### Phase ID

`ASV1-P01`

### Phase Name

Frontier Harness Baseline Files

### Lane

YELLOW

### Dependencies

* `ASV1-P00`

### Purpose

Add the baseline Frontier Harness / Ralph / Codex / Claude control files and policies needed for Workflow 2 operation.

This phase turns the repo from a policy skeleton into a harness-ready repository with agent instructions, lane policy, hooks or hook documentation, and run-artifact conventions.

### Scope

Create or update:

* `AGENTS.md`
* `CLAUDE.md`
* `frontier.yaml`
* `.codex/`
* `.claude/`
* `.githooks/`
* `.github/workflows/` if lightweight CI scaffolding is included
* `tools/frontier/`
* `tools/hooks/`
* `scripts/ralph/`
* `docs/HARNESS_WORKFLOW_2.md`
* `docs/GIT_AND_ARTIFACT_DISCIPLINE.md`
* `docs/STOP_AND_RESUME.md`

The phase must define:

* Workflow 2 state machine,
* Ralph responsibilities,
* Codex executor responsibilities,
* Claude review responsibilities,
* Claude Sonnet verifier/source-map responsibilities,
* ChatGPT strategic reasoning role,
* Green/Yellow/Red lane policy,
* Red scoped authorization environment variables:

  * `PROJECT_OP_AUTHORIZED`
  * `PROJECT_OP_SCOPE`
  * `PROJECT_OP_EXPIRES`
* STOP file semantics,
* run artifact paths,
* handoff paths,
* review paths,
* checks/result paths,
* repair attempt paths,
* explicit staging only,
* forbidden `git add .` and `git add -A`,
* artifact-policy checks or placeholders.

### Non-Goals

* Do not implement research platform source modules.
* Do not implement data/factor/backtest logic.
* Do not run real campaign phases beyond harness baseline.
* Do not add cloud services.
* Do not add broker/live integrations.
* Do not create generated research artifacts.
* Do not create local SQLite DB files.

### Expected Files / Directories

Expected files:

* `AGENTS.md`
* `CLAUDE.md`
* `frontier.yaml`
* `docs/HARNESS_WORKFLOW_2.md`
* `docs/GIT_AND_ARTIFACT_DISCIPLINE.md`
* `docs/STOP_AND_RESUME.md`

Expected directories or placeholders:

* `.codex/`
* `.claude/`
* `.githooks/`
* `.github/workflows/` if included
* `tools/frontier/`
* `tools/hooks/`
* `scripts/ralph/`

### Forbidden Changes

* No source implementation.
* No raw data committed.
* No heavy artifacts committed.
* No local SQLite DB committed.
* No broker/live trading scope.
* No paper trading scope.
* No alpha/tradability claims.
* No uncontrolled scope expansion.
* No hidden failed runs.
* No test weakening or gaming.
* No `git add .`.
* No `git add -A`.

### Validation Commands

```bash
git status --short
test -f AGENTS.md
test -f CLAUDE.md
test -f frontier.yaml
test -f docs/HARNESS_WORKFLOW_2.md
test -f docs/GIT_AND_ARTIFACT_DISCIPLINE.md
test -f docs/STOP_AND_RESUME.md
test -d .codex
test -d .claude
test -d .githooks
test -d tools/frontier
test -d tools/hooks
test -d scripts/ralph
grep -R "RUN_INIT" AGENTS.md CLAUDE.md frontier.yaml docs/HARNESS_WORKFLOW_2.md
grep -R "PROJECT_OP_AUTHORIZED" AGENTS.md CLAUDE.md frontier.yaml docs/HARNESS_WORKFLOW_2.md
```

Ralph must also verify that references to forbidden staging commands are written only as forbidden examples, not as instructions to execute:

```bash
grep -R "git add ." AGENTS.md CLAUDE.md docs/GIT_AND_ARTIFACT_DISCIPLINE.md || true
grep -R "git add -A" AGENTS.md CLAUDE.md docs/GIT_AND_ARTIFACT_DISCIPLINE.md || true
```

If hooks are executable, run their dry-run mode or unit checks. If hooks are documentation-only in this phase, record that enforcement implementation is deferred.

### Artifact Policy

Commit only harness files, policy docs, hook scripts, CI scaffolding if lightweight, and small placeholders.

Do not commit:

* generated logs,
* local run outputs,
* caches,
* DB files,
* raw data,
* generated artifacts.

Stage explicit files only.

### Done Criteria

* Agent instruction files exist.
* `frontier.yaml` exists and documents Workflow 2 expectations.
* STOP/resume behavior is documented.
* Red scoped authorization is documented.
* Artifact and staging discipline are documented.
* Hook strategy exists or hook implementation is present.
* No forbidden files are staged or committed.
* Handoff exists.
* Claude review passes.

### Handoff Requirements

Create:

```text
handoffs/ASV1-P01.md
runs/<run_id>/phases/ASV1-P01/handoff.md
```

Handoff must include:

* files created/updated,
* lane policy summary,
* hook/artifact enforcement summary,
* Workflow 2 run artifact summary,
* validation command results,
* remaining enforcement gaps,
* artifact policy confirmation,
* no broker/live confirmation.

### Review Requirements

Claude Opus 4.8 xhigh review required.

Review must verify:

* Workflow 2 state machine completeness,
* model routing clarity,
* lane policy correctness,
* Red authorization semantics,
* artifact and staging discipline,
* no live/broker scope,
* no generated artifacts.

### Auto-Merge Eligibility

Auto PR and auto merge allowed if:

* checks pass,
* handoff validates,
* review verdict is `PASS` or `PASS_WITH_WARNINGS`,
* artifact policy passes,
* no forbidden files are staged,
* semantic done-check passes.

---

## ASV1-P02 — Architecture Baseline and Local-First PLAN.md

### Phase ID

`ASV1-P02`

### Phase Name

Architecture Baseline and Local-First PLAN.md

### Lane

YELLOW

### Dependencies

* `ASV1-P01`

### Purpose

Create the architecture and planning baseline for the `alpha_system` platform.

This phase documents the system as a local-first Alpha Research Platform, not merely a backtester, and locks down the local-first v1 stack and domain boundaries before implementation begins.

### Scope

Create or update:

* `docs/PLAN.md`
* `docs/ARCHITECTURE.md`
* `docs/LOCAL_FIRST_STACK.md`
* `docs/RESEARCH_WORKFLOW.md`
* `docs/DOMAIN_BOUNDARIES.md`
* `docs/NO_LOOKAHEAD_POLICY.md`
* `docs/BACKTEST_TIERS.md`
* `docs/ARTIFACT_POLICY.md`
* `docs/REPRODUCIBILITY_PRINCIPLES.md`
* `docs/CLI_COMMANDS_TARGET.md`
* `decisions/0001-local-first-stack.md`
* `decisions/0002-reference-backtest-truth.md`
* `decisions/0003-domain-boundary-separation.md`
* `decisions/0004-no-broker-live-in-v1.md`
* `decisions/0005-l2-readiness-design-only.md`

Docs must cover:

* local Parquet storage,
* SQLite registry,
* DuckDB and Polars,
* NumPy and Numba,
* Markdown/CSV/static HTML reports,
* no cloud DB,
* no paid DB,
* no server-first architecture,
* no ClickHouse/QuestDB/DolphinDB/kdb+/S3/Dagster/Ray/MLflow-server dependency in v1,
* data/factor/label/signal/strategy/portfolio/execution separation,
* no-lookahead invariants,
* reference backtest truth,
* fast path acceleration only,
* grid discipline,
* ML/factor-combination design,
* L2 readiness design scope,
* artifact discipline,
* human researcher and AI Agent workflow.

### Non-Goals

* No source code implementation.
* No CLI implementation.
* No schema implementation beyond documentation.
* No generated datasets.
* No registry migration.
* No backtest engine.
* No factor computation.
* No alpha/tradability claims.
* No broker/live trading.

### Expected Files / Directories

Expected files:

* `docs/PLAN.md`
* `docs/ARCHITECTURE.md`
* `docs/LOCAL_FIRST_STACK.md`
* `docs/RESEARCH_WORKFLOW.md`
* `docs/DOMAIN_BOUNDARIES.md`
* `docs/NO_LOOKAHEAD_POLICY.md`
* `docs/BACKTEST_TIERS.md`
* `docs/ARTIFACT_POLICY.md`
* `docs/REPRODUCIBILITY_PRINCIPLES.md`
* `docs/CLI_COMMANDS_TARGET.md`
* five decision records under `decisions/`

### Forbidden Changes

* No source implementation.
* No raw data committed.
* No heavy artifacts committed.
* No local SQLite DB committed.
* No broker/live trading scope.
* No paper trading scope.
* No alpha/tradability claims.
* No uncontrolled strategy explosion.
* No execution-truth ambiguity.
* No hidden failed runs.
* No test weakening or gaming.
* No `git add .`.
* No `git add -A`.

### Validation Commands

```bash
git status --short
test -f docs/PLAN.md
test -f docs/ARCHITECTURE.md
test -f docs/LOCAL_FIRST_STACK.md
test -f docs/RESEARCH_WORKFLOW.md
test -f docs/DOMAIN_BOUNDARIES.md
test -f docs/NO_LOOKAHEAD_POLICY.md
test -f docs/BACKTEST_TIERS.md
test -f docs/ARTIFACT_POLICY.md
test -f docs/REPRODUCIBILITY_PRINCIPLES.md
test -f docs/CLI_COMMANDS_TARGET.md
test -f decisions/0001-local-first-stack.md
test -f decisions/0002-reference-backtest-truth.md
test -f decisions/0003-domain-boundary-separation.md
test -f decisions/0004-no-broker-live-in-v1.md
test -f decisions/0005-l2-readiness-design-only.md
grep -R "Data is not factor" docs decisions
grep -R "Reference" docs/BACKTEST_TIERS.md decisions/0002-reference-backtest-truth.md
grep -R "Fast path" docs/BACKTEST_TIERS.md docs/ARCHITECTURE.md
grep -R "No broker" docs decisions README.md || true
```

If markdown lint is available, run it and record results. If unavailable, record that it is unavailable.

### Artifact Policy

Commit docs and decision records only.

Do not commit generated data, generated reports, DB files, caches, logs, or heavy artifacts.

Stage explicit files only.

### Done Criteria

* Architecture baseline exists.
* Local-first stack is explicitly finalized.
* Backtest tiers are documented.
* Reference truth is documented.
* Fast path is documented as acceleration only.
* No-lookahead policy is documented.
* Domain boundaries are documented.
* Artifact policy is documented.
* No unsupported claims are present.
* Handoff exists.
* Claude review passes.

### Handoff Requirements

Create:

```text
handoffs/ASV1-P02.md
runs/<run_id>/phases/ASV1-P02/handoff.md
```

Handoff must include:

* list of docs/decision records created,
* summary of architecture decisions,
* local-first stack summary,
* backtest-tier summary,
* validation command results,
* no source implementation confirmation,
* artifact policy confirmation,
* known limitations,
* review focus.

### Review Requirements

Claude Opus 4.8 xhigh review required.

Review must verify:

* architecture is an Alpha Research Platform, not merely a backtester,
* domain separations are correct,
* local-first stack decisions match campaign contract,
* no-lookahead and artifact policies are explicit,
* no broker/live scope,
* no overclaims.

### Auto-Merge Eligibility

Auto PR and auto merge allowed if:

* validation passes,
* handoff validates,
* review verdict is `PASS` or `PASS_WITH_WARNINGS`,
* artifact policy passes,
* no forbidden files are staged,
* semantic done-check passes.

---

## ASV1-P03 — Python Workspace and Package Skeleton

### Phase ID

`ASV1-P03`

### Phase Name

Python Workspace and Package Skeleton

### Lane

YELLOW

### Dependencies

* `ASV1-P02`

### Purpose

Create the Python package foundation, development tooling, CLI shell, module skeleton, and test layout without implementing domain logic beyond importable stubs and CLI help.

### Scope

Create or update:

* `pyproject.toml`
* `src/alpha_system/__init__.py`
* `src/alpha_system/__main__.py`
* `src/alpha_system/core/`
* `src/alpha_system/data/`
* `src/alpha_system/factors/`
* `src/alpha_system/labels/`
* `src/alpha_system/research/`
* `src/alpha_system/signals/`
* `src/alpha_system/strategies/`
* `src/alpha_system/management/`
* `src/alpha_system/portfolio/`
* `src/alpha_system/backtest/`
* `src/alpha_system/execution/`
* `src/alpha_system/l2/`
* `src/alpha_system/experiments/`
* `src/alpha_system/reports/`
* `src/alpha_system/cli/`
* `tests/unit/`
* `tests/integration/`
* `tests/no_lookahead/`
* `tests/parity/`
* `tests/performance/`
* `tests/fixtures/`

Create minimal CLI entry point:

```bash
alpha --help
python -m alpha_system --help
python -m alpha_system.cli --help
```

Dependencies must align with the finalized stack:

* Python,
* NumPy,
* Numba,
* Polars,
* DuckDB,
* pytest,
* standard-library SQLite or lightweight wrapper,
* optional Ruff/Mypy if configured.

### Non-Goals

* No domain contract implementation beyond placeholders.
* No registry migrations.
* No data ingestion.
* No factor computation.
* No label generation.
* No backtest engine.
* No ML implementation.
* No L2 processing.
* No broker/live trading.

### Expected Files / Directories

Expected files:

* `pyproject.toml`
* package `__init__.py` files,
* CLI skeleton modules,
* baseline tests proving package import and CLI help.

Expected test files:

* `tests/unit/test_imports.py`
* `tests/unit/test_cli_help.py`
* `tests/unit/test_no_local_data_required.py`

### Forbidden Changes

* No raw data committed.
* No canonical data committed.
* No heavy artifacts committed.
* No local SQLite DB committed.
* No broker/live trading scope.
* No alpha/tradability claims.
* No domain logic scope creep.
* No uncontrolled scope expansion.
* No hidden failed runs.
* No test weakening or gaming.
* No `git add .`.
* No `git add -A`.

### Validation Commands

```bash
python -m pip install -e ".[dev]"
python -m pytest tests/unit
python -m alpha_system --help
python -m alpha_system.cli --help
python -c "import alpha_system; print(alpha_system.__name__)"
git status --short
```

If configured:

```bash
python -m ruff check .
python -m mypy src
```

If `alpha` console script is configured:

```bash
alpha --help
```

### Artifact Policy

Commit source skeleton, tests, configs, and docs only.

Do not commit:

* virtual environments,
* `.pytest_cache`,
* coverage output,
* logs,
* generated artifacts,
* DBs,
* data.

Stage explicit files only.

### Done Criteria

* Package installs editable.
* Package imports.
* CLI help works.
* Test suite for skeleton passes.
* Directory skeleton matches architecture.
* Dependencies do not introduce cloud/database server/broker requirements.
* No domain logic is prematurely implemented.
* Handoff exists.
* Claude review passes.

### Handoff Requirements

Create:

```text
handoffs/ASV1-P03.md
runs/<run_id>/phases/ASV1-P03/handoff.md
```

Handoff must include:

* package layout summary,
* dependency rationale,
* CLI smoke result,
* test results,
* files changed,
* no domain implementation confirmation,
* artifact policy confirmation,
* no broker/live confirmation,
* known limitations.

### Review Requirements

Claude Opus 4.8 xhigh review required.

Review must verify:

* architecture alignment,
* dependency discipline,
* CLI skeleton correctness,
* test adequacy,
* no domain scope creep,
* no local artifacts,
* no broker/live scope.

### Auto-Merge Eligibility

Auto PR and auto merge allowed if:

* checks pass,
* handoff validates,
* review verdict is `PASS` or `PASS_WITH_WARNINGS`,
* artifact policy passes,
* no forbidden files are staged,
* semantic done-check passes.

---

## ASV1-P04 — Core Contracts and Schema Primitives

### Phase ID

`ASV1-P04`

### Phase Name

Core Contracts and Schema Primitives

### Lane

YELLOW

### Dependencies

* `ASV1-P03`

### Purpose

Define core domain contracts and schema primitives that anchor the rest of the platform.

This phase must explicitly represent the required domain fields and boundaries for instruments, calendars, sessions, bars, quote/trade readiness, future L2, factors, factor values, labels, signals, strategies, management, portfolio, and experiment metadata.

### Scope

Create or update:

* `src/alpha_system/core/contracts.py`
* `src/alpha_system/core/schema.py`
* `src/alpha_system/core/time.py`
* `src/alpha_system/core/enums.py`
* `src/alpha_system/data/contracts.py`
* `src/alpha_system/factors/contracts.py`
* `src/alpha_system/labels/contracts.py`
* `src/alpha_system/signals/contracts.py`
* `src/alpha_system/strategies/contracts.py`
* `src/alpha_system/management/contracts.py`
* `src/alpha_system/portfolio/contracts.py`
* `src/alpha_system/experiments/contracts.py`
* `src/alpha_system/l2/contracts.py`
* `docs/CONTRACTS.md`
* tests for required schema fields and boundary rules.

Required contracts:

#### Instrument Master

Fields:

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

#### Trading Calendar / Session

Fields:

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

#### 1-Minute Bar

Fields:

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

No-lookahead primitives:

* `available_ts` required.
* `bar_start_ts < bar_end_ts`.
* Completed bar usable only after `bar_end_ts` plus configured latency.
* Signal based on bar `t` cannot execute inside bar `t` by default.

#### Quote/Trade Readiness

Represent readiness for:

* quote data,
* trade prints,
* bid/ask spread,
* future executable labels,
* future cost modeling.

#### Future L2 Contracts

Design-only fields for:

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

#### FactorSpec

Fields:

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

Lifecycle states:

* `draft`
* `candidate`
* `validated`
* `approved`
* `deprecated`

#### Factor Value Schema

Fields:

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

#### Label Schema

Standard labels:

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

Fields:

* `label_id`
* `instrument_id`
* `event_ts`
* `horizon`
* `label_type`
* `value`
* `path_metadata`
* `data_version`
* `label_available_ts`

#### StrategySpec

Strategies produce:

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

#### ManagementSpec

Support fields for:

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

#### PortfolioSpec

Support fields for:

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

### Non-Goals

* No persistence implementation.
* No registry migrations.
* No full validation engine beyond schema-level validation.
* No factor computation.
* No label generation.
* No strategy execution.
* No backtest engine.
* No L2 replay.
* No broker/live trading.

### Expected Files / Directories

Expected files:

* contract modules under `src/alpha_system/**/contracts.py`
* `docs/CONTRACTS.md`

Expected tests:

* `tests/unit/test_contract_fields.py`
* `tests/unit/test_contract_enums.py`
* `tests/no_lookahead/test_contract_timestamps.py`
* `tests/unit/test_strategy_boundary_contracts.py`
* `tests/unit/test_management_portfolio_contracts.py`
* `tests/unit/test_l2_design_contracts.py`

### Forbidden Changes

* No raw data committed.
* No heavy artifacts committed.
* No local SQLite DB committed.
* No broker/live trading scope.
* No alpha/tradability claims.
* No persistence or compute scope creep.
* No uncontrolled scope expansion.
* No hidden failed runs.
* No test weakening or gaming.
* No `git add .`.
* No `git add -A`.
* Do not remove or weaken `available_ts`.
* Do not collapse StrategySpec into management, portfolio, or execution.

### Validation Commands

```bash
python -m pytest tests/unit tests/no_lookahead
python -m alpha_system --help
git status --short
```

If configured:

```bash
python -m ruff check .
python -m mypy src
```

Required test coverage:

* instrument required fields,
* calendar/session required fields,
* 1-minute bar required fields,
* timestamp/availability fields,
* FactorSpec required fields and lifecycle values,
* factor value required fields,
* label schema required fields and label types,
* StrategySpec allowed and forbidden responsibilities,
* ManagementSpec required support fields,
* PortfolioSpec required support fields,
* L2 design fields.

### Artifact Policy

Commit source contracts, docs, tests, and tiny configs if needed.

Do not commit data, generated artifacts, Parquet outputs, DBs, logs, or caches.

Stage explicit files only.

### Done Criteria

* All required contracts are represented.
* Required fields are tested.
* Timestamp/no-lookahead fields are tested.
* Domain boundaries are represented in tests and docs.
* Strategy responsibility restrictions are tested.
* L2 readiness is design-only.
* No live/broker scope exists.
* Handoff exists.
* Claude review passes.

### Handoff Requirements

Create:

```text
handoffs/ASV1-P04.md
runs/<run_id>/phases/ASV1-P04/handoff.md
```

Handoff must include:

* contract coverage table,
* file mapping by domain,
* tests run and results,
* unresolved schema decisions,
* no implementation scope creep confirmation,
* artifact policy confirmation,
* no broker/live confirmation,
* review focus.

### Review Requirements

Claude Opus 4.8 xhigh review required.

Review must verify:

* field completeness,
* no-lookahead readiness,
* boundary separation,
* strategy forbidden responsibility coverage,
* L2 design-only scope,
* no unsupported claims,
* artifact policy compliance.

### Auto-Merge Eligibility

Auto PR and auto merge allowed if:

* tests pass,
* handoff validates,
* review verdict is `PASS` or `PASS_WITH_WARNINGS`,
* artifact policy passes,
* no forbidden files are staged,
* semantic done-check passes.

## ASV1-P05 — SQLite Metadata Registry MVP

### Phase ID

`ASV1-P05`

### Phase Name

SQLite Metadata Registry MVP

### Lane

YELLOW

### Dependencies

* `ASV1-P04`

### Purpose

Implement the local SQLite metadata registry MVP, including migrations, initialization, required tables, registry status CLI, hashing support, and tests using temporary databases only.

The registry is the local source of truth for reproducibility metadata, dataset versions, factor versions, label versions, strategy versions, experiment records, artifact manifests, and promotion decisions.

This phase must establish the metadata spine for the entire Alpha Research Platform without introducing an external database server, cloud dependency, or committed local database file.

### Scope

Create or update:

* `src/alpha_system/core/registry.py`
* `src/alpha_system/core/migrations.py`
* `src/alpha_system/core/hashing.py`
* `src/alpha_system/core/git_info.py`
* `src/alpha_system/core/run_ids.py`
* `src/alpha_system/experiments/registry.py`
* `src/alpha_system/cli/registry.py`
* migration files under `src/alpha_system/core/migrations/` or equivalent repo-approved migration directory
* `docs/METADATA_REGISTRY.md`
* `configs/registry/default.yaml`
* tests for registry initialization, migration idempotence, required tables, required columns, hashing, git metadata capture, and registry CLI help.

The SQLite registry MVP must include the following tables:

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

Every experiment-style run table, or shared run-record structure if implemented through a common table pattern, must support:

* run id,
* timestamp,
* git commit,
* dirty tree indicator where available,
* code hash,
* config hash,
* data version,
* factor versions,
* label versions,
* engine version,
* parameters,
* artifact paths,
* decision status,
* warnings or status message field where appropriate.

The MVP may represent factor/label/version lists as JSON text columns initially if the schema documents the format and tests validate round-trip behavior. Later phases may harden normalized relationships if needed.

CLI command introduced:

```bash
alpha registry status
```

Command purpose:

* report registry location,
* report migration status,
* report required table status,
* report schema version,
* report whether the active database path is local-only,
* surface missing or invalid registry state.

Command inputs:

* optional `--registry-path`,
* optional `--config`,
* optional `--json` if simple JSON output is implemented.

Command outputs:

* console summary,
* optional JSON summary,
* nonzero exit or explicit error message for invalid registry state, depending on CLI conventions chosen in ASV1-P03.

Artifacts:

* no committed registry database,
* temporary SQLite files only in test temp directories,
* no generated production database in `metadata/`.

Validation checks:

* migrations are idempotent,
* required tables exist,
* required columns exist,
* registry status command works,
* no `.sqlite` or `.db` files are staged,
* config/code hash utilities are deterministic.

### Non-Goals

* No real experiment execution.
* No factor computation.
* No label generation.
* No data ingestion.
* No generated production registry.
* No external database server support.
* No PostgreSQL, MySQL, ClickHouse, QuestDB, ArcticDB, DolphinDB, or kdb+ dependency.
* No MLflow server integration.
* No candidate promotion workflow beyond schema representation.
* No broker/live trading.
* No alpha/tradability claims.

### Expected Files / Directories

Expected source files:

* `src/alpha_system/core/registry.py`
* `src/alpha_system/core/migrations.py`
* `src/alpha_system/core/hashing.py`
* `src/alpha_system/core/git_info.py`
* `src/alpha_system/core/run_ids.py`
* `src/alpha_system/experiments/registry.py`
* `src/alpha_system/cli/registry.py`

Expected migration files:

* `src/alpha_system/core/migrations/0001_initial_registry.sql` or equivalent structured migration file
* optional migration loader metadata if needed

Expected docs/configs:

* `docs/METADATA_REGISTRY.md`
* `configs/registry/default.yaml`

Expected tests:

* `tests/unit/test_hashing.py`
* `tests/unit/test_git_info.py`
* `tests/unit/test_run_ids.py`
* `tests/integration/test_registry_init_tempdb.py`
* `tests/integration/test_registry_migrations_idempotent.py`
* `tests/integration/test_registry_required_tables.py`
* `tests/integration/test_registry_required_columns.py`
* `tests/integration/test_registry_status_cli.py`
* `tests/integration/test_no_committed_sqlite.py`

### Forbidden Changes

* No `metadata/alpha_system.sqlite` committed.
* No `.sqlite`, `.sqlite3`, `.db`, `.db-journal`, or WAL files committed.
* No raw data committed.
* No canonical generated data committed.
* No factor values committed.
* No label values committed.
* No heavy artifacts committed.
* No cache/log/temp files committed.
* No broker/live trading scope.
* No paper trading scope.
* No alpha/profitability/tradability claims.
* No external database dependency.
* No cloud database dependency.
* No uncontrolled scope expansion.
* No hidden failed runs.
* No test weakening or gaming.
* No `git add .`.
* No `git add -A`.

### Validation Commands

Ralph must run and record:

```bash
python -m pytest tests/unit tests/integration
python -m alpha_system.cli registry status --help
git status --short
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
find . -type f \( -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.db" -o -name "*.db-journal" -o -name "*.wal" \) -print
```

If the console script is available:

```bash
alpha registry status --help
```

If lint/type tools are configured:

```bash
python -m ruff check .
python -m mypy src
```

Required validation coverage:

* registry initializes in a temporary directory,
* migrations are idempotent,
* all required tables exist,
* all required reproducibility columns exist,
* status CLI help works,
* registry status can inspect a temp DB,
* hashing is deterministic,
* git metadata capture handles unavailable git state gracefully,
* no committed SQLite database is present.

### Artifact Policy

Commit only:

* source files,
* migration files,
* docs,
* config examples,
* tests,
* tiny fixtures if required for migration tests.

Do not commit:

* SQLite DB files,
* SQLite journal/WAL files,
* generated registry artifacts,
* raw data,
* canonical data,
* heavy artifacts,
* logs,
* caches,
* temp files.

Stage explicit files only. Never use `git add .` or `git add -A`.

### Done Criteria

* SQLite registry can initialize in a temporary directory.
* Required tables exist.
* Required columns for reproducibility metadata are represented.
* Migrations are idempotent.
* `alpha registry status` help works.
* Registry status can inspect a temp database in tests.
* Hashing utilities are deterministic.
* Git metadata utility is safe and tested.
* No local database file is committed.
* No external DB dependency is introduced.
* Handoff exists and records validation results.
* Claude review passes.

### Handoff Requirements

Create:

```text
handoffs/ASV1-P05.md
runs/<run_id>/phases/ASV1-P05/handoff.md
```

Handoff must include:

* migration summary,
* table/column coverage matrix,
* registry CLI behavior,
* hashing/git metadata behavior,
* tests run and results,
* exact files changed,
* confirmation that no SQLite DB file was committed,
* confirmation that no raw/heavy artifacts were committed,
* confirmation that no broker/live scope was introduced,
* known limitations,
* review focus.

### Review Requirements

Claude Opus 4.8 xhigh review required.

Review must verify:

* registry schema completeness,
* migration discipline,
* reproducibility field coverage,
* temp DB usage,
* no committed DB files,
* no external DB/server dependency,
* no broker/live scope,
* no unsupported claims,
* tests are meaningful and not weakened.

### Auto-Merge Eligibility

Auto PR and auto merge allowed if:

* all validation commands pass or non-applicable commands are explicitly documented,
* handoff validates,
* Claude verdict is `PASS` or `PASS_WITH_WARNINGS`,
* no SQLite/DB files are staged,
* no raw/heavy artifacts are staged,
* artifact policy passes,
* semantic done-check passes.

---

## ASV1-P06 — Canonical 1-Minute Data Layer

### Phase ID

`ASV1-P06`

### Phase Name

Canonical 1-Minute Data Layer

### Lane

YELLOW

### Dependencies

* `ASV1-P04`
* `ASV1-P05`

### Purpose

Implement the canonical 1-minute bar data layer foundations using local Parquet, DuckDB, and Polars, with explicit point-in-time fields and no-lookahead validation primitives.

This phase establishes the local data representation that later factor, label, diagnostics, strategy, and backtest phases rely on.

### Scope

Create or update:

* `src/alpha_system/data/bar_schema.py`
* `src/alpha_system/data/paths.py`
* `src/alpha_system/data/storage.py`
* `src/alpha_system/data/query.py`
* `src/alpha_system/data/build_bars.py`
* `src/alpha_system/data/validation.py`
* `src/alpha_system/data/versions.py`
* `docs/DATA_LAYER.md`
* `configs/data/example_1min.yaml`
* tiny deterministic fixtures under `tests/fixtures/data/`

Canonical 1-minute bar schema must enforce:

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

Validation primitives must check:

* required fields,
* timestamp ordering,
* `bar_start_ts < bar_end_ts`,
* `available_ts >= bar_end_ts` plus configured latency where latency is configured,
* OHLC sanity,
* nonnegative volume,
* nonnegative trade count when present,
* bid/ask sanity when present,
* spread consistency when bid/ask present,
* duplicate bar keys,
* data version presence,
* source version presence,
* instrument/session key presence.

DuckDB and Polars support must be fixture-level and local-only:

* DuckDB: local SQL query over a tiny fixture Parquet/CSV converted fixture or in-memory table.
* Polars: lazy transformation smoke test over tiny deterministic fixture.
* No real or large dataset is introduced.

The data path utilities must preserve local-only directory semantics and must not encourage committing generated data under `data/`.

### Non-Goals

* No vendor data integration.
* No cloud ingestion.
* No large real dataset.
* No quote/trade full processing.
* No factor computation.
* No label generation.
* No strategy simulation.
* No backtest engine.
* No final data CLI behavior; CLI is completed in ASV1-P08.
* No broker/live trading.
* No alpha/tradability claims.

### Expected Files / Directories

Expected source files:

* `src/alpha_system/data/bar_schema.py`
* `src/alpha_system/data/paths.py`
* `src/alpha_system/data/storage.py`
* `src/alpha_system/data/query.py`
* `src/alpha_system/data/build_bars.py`
* `src/alpha_system/data/validation.py`
* `src/alpha_system/data/versions.py`

Expected docs/configs:

* `docs/DATA_LAYER.md`
* `configs/data/example_1min.yaml`

Expected fixtures:

* small deterministic fixture under `tests/fixtures/data/`
* fixture must be tiny, deterministic, and explicitly documented as correctness-only fixture

Expected tests:

* `tests/unit/test_bar_schema.py`
* `tests/unit/test_data_paths.py`
* `tests/unit/test_data_versions.py`
* `tests/unit/test_bar_validation_required_fields.py`
* `tests/unit/test_bar_validation_ohlc.py`
* `tests/unit/test_bar_validation_spread.py`
* `tests/unit/test_bar_validation_duplicates.py`
* `tests/no_lookahead/test_bar_available_ts.py`
* `tests/integration/test_duckdb_query_fixture.py`
* `tests/integration/test_polars_lazy_fixture.py`
* `tests/integration/test_no_generated_data_committed.py`

### Forbidden Changes

* No real raw data committed.
* No generated canonical data committed outside tiny fixtures.
* No materialized factor values committed.
* No materialized label values committed.
* No heavy artifacts committed.
* No local SQLite DB committed.
* No broker/live trading scope.
* No paper trading scope.
* No alpha/tradability claims.
* No same-bar execution semantics in the data layer.
* No cloud storage dependency.
* No vendor dependency.
* No uncontrolled scope expansion.
* No hidden failed runs.
* No test weakening or gaming.
* No `git add .`.
* No `git add -A`.

### Validation Commands

Ralph must run and record:

```bash
python -m pytest tests/unit tests/integration tests/no_lookahead
git status --short
find data -type f ! -name README.md ! -name ".gitkeep" -print
find . -path "./tests/fixtures/*" -prune -o -type f \( -name "*.parquet" -o -name "*.csv" -o -name "*.jsonl" \) -print
```

If lint/type tools are configured:

```bash
python -m ruff check .
python -m mypy src
```

Required validation coverage:

* all required 1-minute bar fields,
* timestamp ordering,
* `available_ts` latency,
* duplicate detection,
* OHLC sanity,
* negative volume rejection,
* bid/ask/spread consistency,
* data/source version checks,
* DuckDB fixture query,
* Polars lazy transformation fixture,
* no committed generated data outside allowed fixtures.

### Artifact Policy

Commit only:

* source files,
* docs,
* configs,
* tests,
* tiny deterministic fixtures under `tests/fixtures/data/`.

Do not commit:

* local raw data,
* generated canonical data under `data/canonical/`,
* generated Parquet outputs outside test fixtures,
* DB files,
* generated reports,
* logs,
* caches,
* heavy artifacts.

Stage explicit files only. Never use `git add .` or `git add -A`.

### Done Criteria

* Canonical 1-minute schema is enforceable.
* Point-in-time fields are validated.
* Data version/source version fields are represented.
* DuckDB and Polars fixture smoke tests pass.
* Data paths respect local-only artifact policy.
* Tests prove no-lookahead field presence and ordering.
* No data outputs are committed outside tiny fixtures.
* Handoff exists and records validation results.
* Claude review passes.

### Handoff Requirements

Create:

```text
handoffs/ASV1-P06.md
runs/<run_id>/phases/ASV1-P06/handoff.md
```

Handoff must include:

* data schema summary,
* DuckDB/Polars fixture summary,
* validation checks implemented,
* tests run and results,
* fixture file list and size statement,
* confirmation that no raw/canonical data was committed outside fixtures,
* confirmation that no local DB/heavy artifacts were committed,
* confirmation that no broker/live scope was introduced,
* known limitations,
* review focus.

### Review Requirements

Claude Opus 4.8 xhigh review required.

Review must verify:

* 1-minute bar schema completeness,
* no-lookahead timestamp semantics,
* local-first storage discipline,
* fixture-only data scope,
* DuckDB/Polars usage without server dependency,
* artifact policy,
* no vendor/cloud dependency,
* no broker/live scope,
* no unsupported claims.

### Auto-Merge Eligibility

Auto PR and auto merge allowed if:

* tests pass,
* handoff validates,
* Claude verdict is `PASS` or `PASS_WITH_WARNINGS`,
* no generated data outputs are staged outside allowed fixtures,
* no DB/heavy artifacts are staged,
* artifact policy passes,
* semantic done-check passes.

---

## ASV1-P07 — Calendar, Session, and Data Quality Layer

### Phase ID

`ASV1-P07`

### Phase Name

Calendar, Session, and Data Quality Layer

### Lane

YELLOW

### Dependencies

* `ASV1-P06`

### Purpose

Implement trading calendar, session assignment, timezone handling, half-day handling, session reset support, and data quality diagnostics for 1-minute-session-first intraday research.

This phase ensures that all later factor, label, strategy, and backtest logic has a consistent session model.

### Scope

Create or update:

* `src/alpha_system/data/calendar.py`
* `src/alpha_system/data/sessions.py`
* `src/alpha_system/data/quality.py`
* `src/alpha_system/data/sessionize.py`
* `configs/data/calendars/`
* `docs/CALENDAR_AND_SESSIONS.md`
* tests for calendars, sessions, timezones, half-days, holidays, bar indexing, and data quality flags.

Session contract must use:

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

Tests must cover:

* timezone conversion,
* exchange-local session definition,
* session assignment,
* `bar_index` reset at session boundary,
* half-day close,
* holiday no-session behavior,
* missing bars quality flag,
* duplicate bars quality flag,
* out-of-session bar quality flag,
* invalid timestamp quality flag where appropriate,
* session reset behavior for future factor use,
* `available_ts` remains after `bar_end_ts`.

The calendar examples should be minimal and deterministic. They do not need to represent a full exchange-grade holiday database.

### Non-Goals

* No full exchange-grade holiday database.
* No live calendar API.
* No paid calendar dependency.
* No data vendor dependency.
* No strategy/backtest logic.
* No factor computation.
* No label generation.
* No real market dataset ingestion.
* No broker/live trading.
* No alpha/tradability claims.

### Expected Files / Directories

Expected source files:

* `src/alpha_system/data/calendar.py`
* `src/alpha_system/data/sessions.py`
* `src/alpha_system/data/quality.py`
* `src/alpha_system/data/sessionize.py`

Expected docs/configs:

* `docs/CALENDAR_AND_SESSIONS.md`
* `configs/data/calendars/example_equity_calendar.yaml` or equivalent

Expected tests:

* `tests/unit/test_calendar_contract.py`
* `tests/unit/test_session_assignment.py`
* `tests/unit/test_timezone_handling.py`
* `tests/unit/test_half_day_sessions.py`
* `tests/unit/test_holiday_sessions.py`
* `tests/unit/test_bar_index_session_reset.py`
* `tests/unit/test_data_quality_missing_bars.py`
* `tests/unit/test_data_quality_duplicate_bars.py`
* `tests/unit/test_data_quality_out_of_session.py`
* `tests/no_lookahead/test_session_available_ts.py`

### Forbidden Changes

* No raw data committed.
* No generated canonical data committed.
* No materialized factor/label values committed.
* No heavy artifacts committed.
* No local SQLite DB committed.
* No broker/live trading scope.
* No paper trading scope.
* No alpha/tradability claims.
* No UTC-only assumption when exchange timezone is required.
* No treating half-days as full sessions.
* No strategy/backtest scope creep.
* No full vendor calendar dump.
* No uncontrolled scope expansion.
* No hidden failed runs.
* No test weakening or gaming.
* No `git add .`.
* No `git add -A`.

### Validation Commands

Ralph must run and record:

```bash
python -m pytest tests/unit tests/integration tests/no_lookahead
git status --short
find data -type f ! -name README.md ! -name ".gitkeep" -print
```

If lint/type tools are configured:

```bash
python -m ruff check .
python -m mypy src
```

Required validation coverage:

* timezone conversion,
* session assignment,
* DST-sensitive behavior where fixture design supports it,
* half-day fixture,
* holiday fixture,
* `bar_index` reset,
* missing bar quality flag,
* duplicate bar quality flag,
* out-of-session bar quality flag,
* `available_ts` ordering after sessionization.

### Artifact Policy

Commit only:

* source files,
* docs,
* configs,
* tests,
* tiny deterministic fixtures if needed.

Do not commit:

* vendor calendar dumps,
* generated bar datasets,
* local reports,
* local DBs,
* logs,
* caches,
* raw/canonical data.

Stage explicit files only. Never use `git add .` or `git add -A`.

### Done Criteria

* Session assignment works on deterministic fixtures.
* Timezone tests pass.
* Half-day and holiday tests pass.
* `bar_index` session reset is tested.
* Quality flags are represented and tested.
* Docs explain session-first assumptions and limitations.
* No-lookahead policy remains intact.
* No generated data or vendor dumps are committed.
* Handoff exists and records validation results.
* Claude review passes.

### Handoff Requirements

Create:

```text
handoffs/ASV1-P07.md
runs/<run_id>/phases/ASV1-P07/handoff.md
```

Handoff must include:

* calendar/session implementation summary,
* quality flag summary,
* test results,
* known limitations of example calendars,
* artifact policy confirmation,
* confirmation that no vendor calendar dump or generated data was committed,
* confirmation that no broker/live scope was introduced,
* review focus.

### Review Requirements

Claude Opus 4.8 xhigh review required.

Review must verify:

* timezone/session semantics,
* half-day behavior,
* holiday behavior,
* quality flag behavior,
* `bar_index` reset,
* no-lookahead preservation,
* artifact policy,
* no live/broker scope,
* no unsupported claims.

### Auto-Merge Eligibility

Auto PR and auto merge allowed if:

* tests pass,
* handoff validates,
* Claude verdict is `PASS` or `PASS_WITH_WARNINGS`,
* no generated data/vendor dumps are staged,
* no DB/heavy artifacts are staged,
* artifact policy passes,
* semantic done-check passes.

---

## ASV1-P08 — Data Validation CLI and Local Fixture Policy

### Phase ID

`ASV1-P08`

### Phase Name

Data Validation CLI and Local Fixture Policy

### Lane

YELLOW

### Dependencies

* `ASV1-P06`
* `ASV1-P07`

### Purpose

Implement data CLI commands and the local fixture policy required for deterministic platform testing without committing real datasets.

This phase introduces user-facing data commands while preserving local-only artifact discipline.

### Scope

Create or update:

* `src/alpha_system/cli/data.py`
* `src/alpha_system/data/fixture_policy.py`
* `src/alpha_system/data/cli_validation.py` if needed
* `docs/DATA_VALIDATION_CLI.md`
* `docs/FIXTURE_POLICY.md`
* `configs/data/validation_example.yaml`
* `configs/data/build_bars_example.yaml`
* tests for CLI help, validation workflow, build-bars workflow, local fixture policy, and artifact policy.

CLI commands introduced:

```bash
alpha data validate
alpha data build-bars
```

#### `alpha data validate`

Purpose:

* validate local input or canonical datasets against schema and no-lookahead timestamp requirements.

Inputs:

* config path,
* dataset path,
* schema id,
* optional calendar id,
* optional registry path,
* optional output summary path.

Outputs:

* console summary,
* small validation summary,
* quality flag counts,
* optional registry entry in temp/local DB.

Artifacts:

* small Markdown/CSV/JSON summaries only if configured,
* no committed large validation outputs.

Validation checks:

* required fields,
* timestamp ordering,
* numeric constraints,
* duplicate bars,
* null handling,
* data version presence,
* source version presence,
* `available_ts >= bar_end_ts + latency`,
* session assignment when calendar provided,
* out-of-session records,
* quality flag consistency.

#### `alpha data build-bars`

Purpose:

* convert allowed local source fixture/input into canonical 1-minute bars.

Inputs:

* local source path,
* instrument config,
* calendar config,
* output path under local-only data directory,
* data version,
* optional registry path,
* optional validation config.

Outputs:

* local canonical Parquet bars,
* small manifest,
* validation summary.

Artifacts:

* generated Parquet output is local-only,
* tiny fixture Parquet may be committed only under `tests/fixtures/` if explicitly curated.

Validation checks:

* schema,
* session assignment,
* bar indexing,
* OHLC sanity,
* spread sanity,
* quality flags,
* artifact output path policy.

### Non-Goals

* No data vendor connector.
* No cloud ingestion.
* No large real dataset.
* No quote/trade full processing.
* No factor computation.
* No label generation.
* No strategy simulation.
* No backtest.
* No broker/live trading.
* No alpha/tradability claims.

### Expected Files / Directories

Expected source files:

* `src/alpha_system/cli/data.py`
* `src/alpha_system/data/fixture_policy.py`
* optional `src/alpha_system/data/cli_validation.py`

Expected docs/configs:

* `docs/DATA_VALIDATION_CLI.md`
* `docs/FIXTURE_POLICY.md`
* `configs/data/validation_example.yaml`
* `configs/data/build_bars_example.yaml`

Expected tests:

* `tests/unit/test_data_cli_help.py`
* `tests/unit/test_fixture_policy.py`
* `tests/integration/test_data_validate_command.py`
* `tests/integration/test_build_bars_fixture_command.py`
* `tests/integration/test_data_cli_registry_tempdb.py`
* `tests/integration/test_data_artifact_policy.py`
* `tests/no_lookahead/test_data_cli_available_ts.py`

### Forbidden Changes

* No raw data committed.
* No generated canonical data committed outside tiny fixtures.
* No materialized factor/label values committed.
* No heavy artifacts committed.
* No local SQLite DB committed.
* No broker/live trading scope.
* No paper trading scope.
* No alpha/tradability claims.
* No vendor/cloud dependency.
* No same-bar execution semantics.
* No generated validation outputs committed unless tiny curated summaries are explicitly scoped.
* No uncontrolled scope expansion.
* No hidden failed runs.
* No test weakening or gaming.
* No `git add .`.
* No `git add -A`.

### Validation Commands

Ralph must run and record:

```bash
python -m pytest tests/unit tests/integration tests/no_lookahead
python -m alpha_system.cli data validate --help
python -m alpha_system.cli data build-bars --help
git status --short
find data -type f ! -name README.md ! -name ".gitkeep" -print
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
```

If console script is available:

```bash
alpha data validate --help
alpha data build-bars --help
```

Required validation coverage:

* CLI help,
* validation command with tiny fixture,
* build-bars command with tiny fixture,
* local fixture policy,
* artifact policy for outputs,
* no-lookahead timestamp checks,
* optional temp registry integration,
* no generated data under `data/` committed.

### Artifact Policy

Commit only:

* source files,
* docs,
* configs,
* tests,
* tiny deterministic fixtures.

Do not commit:

* local raw data,
* generated canonical data,
* full validation outputs,
* local DB files,
* logs,
* caches,
* temporary outputs.

Stage explicit files only. Never use `git add .` or `git add -A`.

### Done Criteria

* `alpha data validate` exists.
* `alpha data build-bars` exists.
* Commands expose help.
* Commands work on deterministic tiny fixtures.
* Commands enforce local-only output policy.
* Artifact policy rejects generated local outputs in committed paths.
* Docs explain fixture policy.
* No generated data is committed under `data/`.
* Handoff exists and records validation results.
* Claude review passes.

### Handoff Requirements

Create:

```text
handoffs/ASV1-P08.md
runs/<run_id>/phases/ASV1-P08/handoff.md
```

Handoff must include:

* data command summary,
* input/output/artifact behavior,
* fixture policy summary,
* tests run and results,
* confirmation that no generated data was committed,
* confirmation that no local DB/heavy artifacts were committed,
* confirmation that no broker/live scope was introduced,
* known limitations,
* review focus.

### Review Requirements

Claude Opus 4.8 xhigh review required.

Review must verify:

* CLI semantics,
* no-lookahead validation,
* fixture policy,
* local-first constraints,
* artifact policy,
* optional registry behavior,
* no vendor/cloud dependency,
* no broker/live scope.

### Auto-Merge Eligibility

Auto PR and auto merge allowed if:

* tests pass,
* CLI help works,
* handoff validates,
* Claude verdict is `PASS` or `PASS_WITH_WARNINGS`,
* no data outputs or DBs are staged,
* artifact policy passes,
* semantic done-check passes.

---

## ASV1-P09 — FactorSpec, Factor Registry, and Lifecycle

### Phase ID

`ASV1-P09`

### Phase Name

FactorSpec, Factor Registry, and Lifecycle

### Lane

YELLOW

### Dependencies

* `ASV1-P05`
* `ASV1-P08`

### Purpose

Implement FactorSpec, factor registry behavior, versioning, lifecycle constraints, and factor validation CLI.

This phase prevents draft factors from being treated as validated or approved and prevents unreviewed materialization into long-term factor stores.

### Scope

Create or update:

* `src/alpha_system/factors/spec.py`
* `src/alpha_system/factors/registry.py`
* `src/alpha_system/factors/lifecycle.py`
* `src/alpha_system/factors/validation.py`
* `src/alpha_system/factors/dependency_spec.py`
* `src/alpha_system/cli/factor.py`
* `docs/FACTOR_REGISTRY.md`
* `configs/factors/examples/`
* tests for factor specs, lifecycle, registry, hashing, dependencies, review-gated promotion, and CLI help.

CLI command introduced:

```bash
alpha factor validate
```

Command purpose:

* validate FactorSpec structure, declared dependencies, lifecycle status, code/config hashes, warmup, session reset, availability lag, artifact policy, and registry eligibility.

Inputs:

* factor spec config,
* optional registry path,
* optional code path,
* optional validation artifact path,
* optional output summary path.

Outputs:

* console summary,
* small validation summary,
* optional draft/candidate registry entry in temp/local DB.

Artifacts:

* small validation summary only,
* no computed factor values.

Validation checks:

* required FactorSpec fields,
* lifecycle transition legality,
* no raw ad hoc columns outside declared dependencies,
* missing dependency rejection,
* invalid availability lag rejection,
* invalid warmup rejection,
* invalid session reset value rejection,
* no unreviewed approval,
* candidate requires validation artifact path,
* approved requires promotion decision.

FactorSpec required fields:

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

Lifecycle states:

* `draft`
* `candidate`
* `validated`
* `approved`
* `deprecated`

Rules:

* draft may be experimented with but not permanently materialized by default,
* candidate requires validation artifact path,
* validated requires diagnostics artifact and review status,
* approved requires explicit promotion decision,
* deprecated remains queryable for reproducibility.

### Non-Goals

* No factor computation engine.
* No factor materialization.
* No factor diagnostics.
* No label generation.
* No signals or strategies.
* No candidate approval.
* No alpha/tradability claims.
* No broker/live trading.

### Expected Files / Directories

Expected source files:

* `src/alpha_system/factors/spec.py`
* `src/alpha_system/factors/registry.py`
* `src/alpha_system/factors/lifecycle.py`
* `src/alpha_system/factors/validation.py`
* `src/alpha_system/factors/dependency_spec.py`
* `src/alpha_system/cli/factor.py`

Expected docs/configs:

* `docs/FACTOR_REGISTRY.md`
* `configs/factors/examples/`

Expected tests:

* `tests/unit/test_factor_spec_fields.py`
* `tests/unit/test_factor_lifecycle.py`
* `tests/unit/test_factor_lifecycle_transitions.py`
* `tests/unit/test_factor_dependency_validation.py`
* `tests/unit/test_factor_hashes.py`
* `tests/unit/test_factor_promotion_requires_review.py`
* `tests/integration/test_factor_registry_tempdb.py`
* `tests/integration/test_factor_validate_cli.py`
* `tests/integration/test_factor_no_output_artifacts.py`

### Forbidden Changes

* No computed factor values committed.
* No materialized factor store committed.
* No generated factor Parquet committed.
* No raw data committed.
* No canonical generated data committed.
* No heavy artifacts committed.
* No local SQLite DB committed.
* No label-as-factor input path.
* No unreviewed approval path.
* No candidate promotion without review.
* No broker/live trading scope.
* No paper trading scope.
* No alpha/tradability claims.
* No uncontrolled scope expansion.
* No hidden failed runs.
* No test weakening or gaming.
* No `git add .`.
* No `git add -A`.

### Validation Commands

Ralph must run and record:

```bash
python -m pytest tests/unit tests/integration
python -m alpha_system.cli factor validate --help
git status --short
find data/factors -type f ! -name README.md ! -name ".gitkeep" -print
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
```

If console script is available:

```bash
alpha factor validate --help
```

Required validation coverage:

* required FactorSpec fields,
* lifecycle states,
* lifecycle transitions,
* version uniqueness in temp registry,
* code/config hash recording,
* invalid dependencies,
* raw ad hoc dependency rejection,
* draft materialization prevention rule representation,
* promotion requires review,
* deprecated factors remain reproducible,
* CLI help,
* no generated factor outputs.

### Artifact Policy

Commit only:

* source files,
* docs,
* configs,
* tests,
* tiny examples.

Do not commit:

* computed factor values,
* generated factor Parquet,
* local factor stores,
* local registry DBs,
* raw data,
* generated artifacts,
* logs,
* caches.

Stage explicit files only. Never use `git add .` or `git add -A`.

### Done Criteria

* FactorSpec exists and enforces required fields.
* Factor lifecycle rules exist and are tested.
* Factor dependencies can be validated.
* Factor versions can be registered in temp SQLite.
* `alpha factor validate` help works.
* Unreviewed approval is rejected.
* Draft materialization is blocked by policy.
* No computed factor outputs are committed.
* Handoff exists and records validation results.
* Claude review passes.

### Handoff Requirements

Create:

```text
handoffs/ASV1-P09.md
runs/<run_id>/phases/ASV1-P09/handoff.md
```

Handoff must include:

* FactorSpec field mapping,
* lifecycle rules,
* registry behavior,
* CLI behavior,
* tests run and results,
* artifact policy confirmation,
* confirmation that no factor output was committed,
* confirmation that no local DB/heavy artifacts were committed,
* confirmation that no broker/live scope was introduced,
* known limitations,
* review focus.

### Review Requirements

Claude Opus 4.8 xhigh review required.

Review must verify:

* lifecycle discipline,
* required field coverage,
* registry integration,
* promotion constraints,
* dependency validation,
* no label leakage,
* no alpha/tradability overclaims,
* no factor output artifacts,
* no broker/live scope,
* no test weakening.

### Auto-Merge Eligibility

Auto PR and auto merge allowed if:

* tests pass,
* CLI help works,
* handoff validates,
* Claude verdict is `PASS` or `PASS_WITH_WARNINGS`,
* no factor outputs or DBs are staged,
* artifact policy passes,
* semantic done-check passes.

---

## ASV1-P10 — Label Store MVP

### Phase ID

`ASV1-P10`

### Phase Name

Label Store MVP

### Lane

YELLOW

### Dependencies

* `ASV1-P05`
* `ASV1-P08`

### Purpose

Implement label specifications, label generation foundations, label versioning, and alignment checks for forward returns, path-dependent labels, volatility labels, and future liquidity/spread labels.

Labels must remain separate from factors, signals, strategies, and live decision inputs. Labels are future-looking research targets used for diagnostics and ML training, not live features.

### Scope

Create or update:

* `src/alpha_system/labels/spec.py`
* `src/alpha_system/labels/store.py`
* `src/alpha_system/labels/generation.py`
* `src/alpha_system/labels/alignment.py`
* `src/alpha_system/labels/validation.py`
* `src/alpha_system/labels/path_metrics.py`
* `docs/LABEL_STORE.md`
* `configs/labels/examples/`
* tests for label schema, generation, path metrics, alignment, no-lookahead, session boundaries, half-days, registry integration, and factor/strategy leakage prevention.

Standard labels:

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

Label fields:

* `label_id`
* `instrument_id`
* `event_ts`
* `horizon`
* `label_type`
* `value`
* `path_metadata`
* `data_version`
* `label_available_ts`

No-lookahead rules:

* `label_available_ts` must be after the future horizon is known.
* Forward-return labels are not available until the future close or future price required by the label exists.
* MFE/MAE labels are not available until the full path horizon exists.
* Target-before-stop and stop-before-target labels are not available until the path outcome is known or horizon expires.
* Labels must not be available to live factor computation.
* Labels must not be available to live strategy inputs.
* Label alignment must respect instrument, session, event timestamp, horizon, data version, and label version.

Registry behavior:

* label versions must be recordable in temporary SQLite tests,
* label generation runs must carry data version and label spec hash where applicable,
* generated label stores are local-only.

### Non-Goals

* No ML training.
* No factor diagnostics.
* No strategy execution.
* No large label store materialization.
* No label CLI unless a later phase explicitly adds it.
* No generated label artifacts committed.
* No alpha/tradability claims.
* No broker/live trading.

### Expected Files / Directories

Expected source files:

* `src/alpha_system/labels/spec.py`
* `src/alpha_system/labels/store.py`
* `src/alpha_system/labels/generation.py`
* `src/alpha_system/labels/alignment.py`
* `src/alpha_system/labels/validation.py`
* `src/alpha_system/labels/path_metrics.py`

Expected docs/configs:

* `docs/LABEL_STORE.md`
* `configs/labels/examples/`

Expected tests:

* `tests/unit/test_label_spec_fields.py`
* `tests/unit/test_forward_return_labels.py`
* `tests/unit/test_mfe_mae_labels.py`
* `tests/unit/test_stop_target_ordering_labels.py`
* `tests/unit/test_future_volatility_labels.py`
* `tests/unit/test_future_spread_liquidity_labels.py`
* `tests/no_lookahead/test_label_available_ts.py`
* `tests/no_lookahead/test_labels_not_factor_inputs.py`
* `tests/no_lookahead/test_labels_not_strategy_inputs.py`
* `tests/unit/test_label_session_boundaries.py`
* `tests/unit/test_label_half_day_behavior.py`
* `tests/integration/test_label_registry_tempdb.py`
* `tests/integration/test_label_no_output_artifacts.py`

### Forbidden Changes

* No generated label store committed.
* No label Parquet committed outside tiny fixtures.
* No raw data committed.
* No canonical generated data committed.
* No materialized factor values committed.
* No heavy artifacts committed.
* No local SQLite DB committed.
* No label leakage into factors.
* No label leakage into strategies.
* No broker/live trading scope.
* No paper trading scope.
* No alpha/tradability claims.
* No treating label values as live features.
* No ignoring session close for forward horizons.
* No uncontrolled scope expansion.
* No hidden failed runs.
* No test weakening or gaming.
* No `git add .`.
* No `git add -A`.

### Validation Commands

Ralph must run and record:

```bash
python -m pytest tests/unit tests/integration tests/no_lookahead
git status --short
find data/labels -type f ! -name README.md ! -name ".gitkeep" -print
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
```

If lint/type tools are configured:

```bash
python -m ruff check .
python -m mypy src
```

Required validation coverage:

* label required fields,
* standard label coverage,
* forward-return horizon alignment,
* MFE/MAE path metadata,
* target-before-stop ordering,
* stop-before-target ordering,
* realized volatility labels,
* future spread/liquidity labels,
* `label_available_ts` after horizon,
* session boundary behavior,
* half-day behavior,
* label version registry,
* labels rejected as factor inputs,
* labels rejected as strategy inputs,
* no generated label outputs committed.

### Artifact Policy

Commit only:

* source files,
* docs,
* configs,
* tests,
* tiny deterministic fixtures if explicitly needed.

Do not commit:

* generated label stores,
* local label Parquet,
* local DB files,
* raw/canonical data,
* logs,
* caches,
* heavy artifacts.

Stage explicit files only. Never use `git add .` or `git add -A`.

### Done Criteria

* Label schema exists.
* Standard labels are represented.
* Label generation works on deterministic fixtures.
* Label alignment checks exist.
* `label_available_ts` no-lookahead tests pass.
* Labels cannot be used as factor inputs.
* Labels cannot be used as strategy live inputs.
* Label versions can be registered in temp SQLite.
* No generated label outputs are committed.
* Handoff exists and records validation results.
* Claude review passes.

### Handoff Requirements

Create:

```text
handoffs/ASV1-P10.md
runs/<run_id>/phases/ASV1-P10/handoff.md
```

Handoff must include:

* label type coverage,
* label field mapping,
* alignment rules,
* no-lookahead test results,
* registry integration summary,
* artifact policy confirmation,
* confirmation that no generated label outputs were committed,
* confirmation that no local DB/heavy artifacts were committed,
* confirmation that no broker/live scope was introduced,
* known limitations,
* review focus.

### Review Requirements

Claude Opus 4.8 xhigh review required.

Review must verify:

* label/factor separation,
* label/strategy separation,
* `label_available_ts` semantics,
* session/horizon alignment,
* path-dependent label correctness,
* standard label coverage,
* artifact policy,
* no overclaims,
* no broker/live scope,
* no test weakening.

### Auto-Merge Eligibility

Auto PR and auto merge allowed if:

* tests pass,
* handoff validates,
* Claude verdict is `PASS` or `PASS_WITH_WARNINGS`,
* no label outputs or DBs are staged,
* artifact policy passes,
* semantic done-check passes.

## ASV1-P11 — Factor Compute SDK MVP

### Phase ID

`ASV1-P11`

### Phase Name

Factor Compute SDK MVP

### Lane

YELLOW

### Dependencies

* `ASV1-P09`
* `ASV1-P10`

### Purpose

Create the Factor Compute SDK MVP for deterministic factor calculation on canonical 1-minute bars while enforcing declared dependencies, warmup behavior, session reset behavior, availability lag, quality flags, lifecycle rules, and materialization restrictions.

This phase moves the platform from factor specification into controlled factor computation. It must preserve the core rule that factors are not labels, signals, strategies, portfolios, or execution. It must also enforce that draft factor values are not permanently materialized into the long-term factor store by default.

### Scope

Create or update:

* `src/alpha_system/factors/base.py`
* `src/alpha_system/factors/compute.py`
* `src/alpha_system/factors/dependencies.py`
* `src/alpha_system/factors/materialize.py`
* `src/alpha_system/factors/normalization.py`
* `src/alpha_system/factors/quality.py`
* `src/alpha_system/factors/io.py`
* `src/alpha_system/cli/factor.py`
* factor library directory placeholders:

  * `factors/price_action/`
  * `factors/momentum/`
  * `factors/reversal/`
  * `factors/volatility/`
  * `factors/liquidity/`
  * `factors/order_flow/`
  * `factors/microstructure/`
  * `factors/researcher_sandbox/`
* `docs/FACTOR_COMPUTE.md`
* `configs/factors/examples/`
* tests for compute behavior, dependency behavior, materialization policy, no-lookahead timing, quality flags, and CLI help.

CLI command introduced or expanded:

```bash
alpha factor materialize
```

Command purpose:

* compute and optionally persist validated factor values to a local-only factor store.

Command inputs:

* factor spec path,
* canonical data path or dataset version,
* data version,
* instrument or universe selector,
* date/session range,
* output policy,
* optional registry path,
* optional output directory,
* optional run manifest output path.

Command outputs:

* factor value dataset under local-only factor store when materialization is allowed,
* small manifest,
* optional registry entry in temp/local SQLite DB,
* console summary.

Artifacts:

* computed factor values are local-only,
* generated factor Parquet is not committed,
* small summaries/manifests may be committed only when explicitly curated and tiny,
* generated outputs under `data/factors/` remain local-only.

Validation checks:

* factor lifecycle permits materialization,
* draft materialization is blocked by default,
* factor dependencies are declared and available,
* labels are rejected as factor inputs,
* no raw ad hoc columns outside declared dependencies,
* warmup behavior is correct,
* session reset behavior is correct,
* availability lag is applied,
* `available_ts` is propagated correctly,
* data version is recorded,
* compute version is recorded,
* code hash and config hash are recorded,
* quality flags are represented.

Factor value schema must include:

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

Factor compute SDK must support at least one tiny deterministic example factor for testing. The example factor must be explicitly documented as a correctness fixture, not as a useful alpha factor.

### Non-Goals

* No large factor library.
* No factor diagnostics engine beyond compute correctness.
* No factor card/report generation.
* No signal generation.
* No strategy logic.
* No label generation.
* No ML model training.
* No alpha/profitability/tradability claims.
* No broker/live trading.
* No permanent draft factor materialization by default.
* No production factor store claim.

### Expected Files / Directories

Expected source files:

* `src/alpha_system/factors/base.py`
* `src/alpha_system/factors/compute.py`
* `src/alpha_system/factors/dependencies.py`
* `src/alpha_system/factors/materialize.py`
* `src/alpha_system/factors/normalization.py`
* `src/alpha_system/factors/quality.py`
* `src/alpha_system/factors/io.py`
* `src/alpha_system/cli/factor.py`

Expected factor library directories:

* `factors/price_action/`
* `factors/momentum/`
* `factors/reversal/`
* `factors/volatility/`
* `factors/liquidity/`
* `factors/order_flow/`
* `factors/microstructure/`
* `factors/researcher_sandbox/`

Expected docs/configs:

* `docs/FACTOR_COMPUTE.md`
* example factor specs under `configs/factors/examples/`

Expected tests:

* `tests/unit/test_factor_compute_deterministic.py`
* `tests/unit/test_factor_dependencies.py`
* `tests/unit/test_factor_dependency_missing_input.py`
* `tests/unit/test_factor_warmup_behavior.py`
* `tests/unit/test_factor_session_reset.py`
* `tests/unit/test_factor_quality_flags.py`
* `tests/unit/test_factor_normalization.py`
* `tests/no_lookahead/test_factor_availability_lag.py`
* `tests/no_lookahead/test_factor_available_ts_propagation.py`
* `tests/no_lookahead/test_label_as_factor_input_rejected.py`
* `tests/integration/test_factor_materialize_tempdir.py`
* `tests/integration/test_draft_materialization_blocked.py`
* `tests/integration/test_factor_materialize_registry_tempdb.py`
* `tests/unit/test_factor_value_schema.py`
* `tests/integration/test_factor_materialize_cli_help.py`
* `tests/integration/test_factor_no_output_artifacts.py`

### Forbidden Changes

* No generated factor store committed.
* No generated factor Parquet committed outside tiny explicit fixtures.
* No generated outputs under `data/factors/` committed.
* No raw data committed.
* No canonical generated data committed.
* No materialized label values committed.
* No heavy artifacts committed.
* No local SQLite DB committed.
* No label leakage into factor inputs.
* No raw ad hoc input columns outside declared dependencies.
* No permanent draft factor materialization by default.
* No unreviewed approval path.
* No strategy/signal/backtest scope creep.
* No broker/live trading scope.
* No paper trading scope.
* No alpha/profitability/tradability claims.
* No uncontrolled scope expansion.
* No hidden failed runs.
* No test weakening or gaming.
* No `git add .`.
* No `git add -A`.

### Validation Commands

Ralph must run and record:

```bash
python -m pytest tests/unit tests/integration tests/no_lookahead
python -m alpha_system.cli factor materialize --help
git status --short
find data/factors -type f ! -name README.md ! -name ".gitkeep" -print
find data/labels -type f ! -name README.md ! -name ".gitkeep" -print
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
```

If console script is available:

```bash
alpha factor materialize --help
```

If lint/type tools are configured:

```bash
python -m ruff check .
python -m mypy src
```

Required validation coverage:

* deterministic factor output on tiny fixtures,
* dependency validation,
* missing dependency rejection,
* warmup null/quality behavior,
* session reset behavior,
* availability lag,
* `available_ts` propagation,
* label-as-input rejection,
* draft materialization rejection,
* validated/candidate materialization to temp directory where allowed by policy,
* factor value schema fields,
* temp registry integration,
* no generated factor outputs committed.

### Artifact Policy

Commit only:

* source files,
* docs,
* configs,
* tests,
* tiny deterministic fixtures if explicitly needed,
* placeholder `.gitkeep` files for factor library directories if needed.

Do not commit:

* generated factor stores,
* local Parquet factor values,
* local manifests from real runs,
* registry DB files,
* raw data,
* canonical data,
* label values,
* generated heavy artifacts,
* logs,
* caches,
* temp files.

Stage explicit files only. Never use `git add .` or `git add -A`.

### Done Criteria

* Factor Compute SDK exists.
* `alpha factor materialize` help works.
* Factor value schema is respected.
* Dependency validation works.
* Labels are rejected as factor inputs.
* Warmup, session reset, availability lag, and quality flag tests pass.
* Draft factors cannot be materialized by default.
* Allowed materialization writes only to temp/local-only paths in tests.
* Temp registry integration works.
* No generated factor outputs are committed.
* Handoff exists and records validation results.
* Claude review passes.

### Handoff Requirements

Create:

```text
handoffs/ASV1-P11.md
runs/<run_id>/phases/ASV1-P11/handoff.md
```

Handoff must include:

* Factor Compute SDK summary,
* factor value schema coverage,
* dependency validation summary,
* materialization policy summary,
* lifecycle enforcement summary,
* no-lookahead timing summary,
* example factor scope and fixture-only disclaimer,
* tests run and results,
* CLI help result,
* artifact policy confirmation,
* confirmation that no factor outputs were committed,
* confirmation that no local DB/heavy artifacts were committed,
* confirmation that no broker/live scope was introduced,
* known limitations,
* review focus.

### Review Requirements

Claude Opus 4.8 xhigh review required.

Review must verify:

* factor lifecycle enforcement,
* no-lookahead semantics,
* `available_ts` propagation,
* dependency validation,
* label-input rejection,
* materialization path policy,
* no draft permanent materialization,
* no strategy/signal/backtest scope creep,
* no alpha/tradability overclaims,
* no broker/live scope,
* no generated factor artifacts,
* no test weakening.

### Auto-Merge Eligibility

Auto PR and auto merge allowed if:

* all tests pass,
* CLI help works,
* handoff validates,
* Claude verdict is `PASS` or `PASS_WITH_WARNINGS`,
* no factor outputs or DBs are staged,
* no raw/heavy artifacts are staged,
* artifact policy passes,
* semantic done-check passes.

---

## ASV1-P12 — Intraday Factor Diagnostics Engine

### Phase ID

`ASV1-P12`

### Phase Name

Intraday Factor Diagnostics Engine

### Lane

YELLOW

### Dependencies

* `ASV1-P11`

### Purpose

Implement the intraday factor diagnostics engine for evaluating factor behavior without running full trade simulation and without making tradability claims.

This phase creates the Tier 0 factor research engine. It must support directional, nonlinear, event, regime, execution-filter, and management-related diagnostics using versioned factor values and versioned labels while preserving no-lookahead alignment.

### Scope

Create or update:

* `src/alpha_system/research/diagnostics.py`
* `src/alpha_system/research/ic.py`
* `src/alpha_system/research/buckets.py`
* `src/alpha_system/research/events.py`
* `src/alpha_system/research/regimes.py`
* `src/alpha_system/research/execution_filters.py`
* `src/alpha_system/research/management_features.py`
* `src/alpha_system/research/study_config.py`
* `src/alpha_system/research/study_outputs.py`
* `src/alpha_system/cli/study.py`
* `docs/FACTOR_DIAGNOSTICS.md`
* `configs/studies/examples/`
* tests for deterministic diagnostic calculations, no-lookahead label alignment, artifact policy, registry integration, and CLI help.

CLI command introduced:

```bash
alpha study run
```

Command purpose:

* run factor diagnostics against versioned factor values and versioned labels.

Command inputs:

* study config,
* factor version,
* label version,
* data version,
* date/session range,
* optional universe/instrument selector,
* output directory,
* optional registry path,
* optional run manifest output path.

Command outputs:

* local study artifacts,
* diagnostic summary,
* optional factor validation run or study run registry entry,
* warnings,
* run manifest.

Artifacts:

* summaries may be committed only when tiny and curated,
* raw full outputs are local-only,
* generated outputs under `artifacts/factor_studies/` are local-only unless explicitly curated summaries.

Validation checks:

* sample size thresholds,
* factor version presence,
* label version presence,
* data version presence,
* horizon alignment,
* factor/label instrument alignment,
* factor/label session alignment,
* label availability,
* no-lookahead,
* artifact manifest,
* registry run record.

Required diagnostics:

#### Directional Continuous Factors

* Pearson IC,
* Rank IC,
* IC by horizon,
* IC decay,
* IC by day/week/month,
* ICIR,
* bucket monotonicity.

#### Nonlinear Bucket Factors

* bucket forward returns,
* tail expectancy,
* U-shape profile,
* extreme bucket hit rate,
* MFE/MAE by bucket.

#### Event Trigger Factors

* event study,
* conditional forward returns,
* sample size,
* false breakout rate,
* target-before-stop probability,
* post-event MFE/MAE.

#### Regime Filters

* with-filter vs without-filter uplift,
* coverage,
* false rejection rate,
* conditional strategy improvement.

#### Execution Filters

* spread sensitivity,
* liquidity sensitivity,
* slippage sensitivity,
* volume participation,
* adverse selection proxy.

#### Management Features

* target-before-stop,
* time-to-target,
* time-to-stop,
* breakeven usefulness,
* trailing stop usefulness.

Diagnostics must emit warnings for:

* insufficient sample size,
* missing label coverage,
* unstable horizon coverage,
* high missing factor rate,
* invalid version references,
* possible alignment gaps,
* unsupported diagnostic type.

Diagnostics must not emit:

* “tradable,”
* “profitable,”
* “production-ready,”
* “approved,”
* “robust alpha,”
* or any equivalent unsupported claim.

### Non-Goals

* No strategy backtest.
* No full trade simulation.
* No reference execution engine changes.
* No candidate approval.
* No promotion to approved.
* No factor card/report template beyond minimal diagnostic summary; full reporting is ASV1-P13.
* No ML model training.
* No full review bundle.
* No broker/live trading.
* No alpha/tradability claims.

### Expected Files / Directories

Expected source files:

* `src/alpha_system/research/diagnostics.py`
* `src/alpha_system/research/ic.py`
* `src/alpha_system/research/buckets.py`
* `src/alpha_system/research/events.py`
* `src/alpha_system/research/regimes.py`
* `src/alpha_system/research/execution_filters.py`
* `src/alpha_system/research/management_features.py`
* `src/alpha_system/research/study_config.py`
* `src/alpha_system/research/study_outputs.py`
* `src/alpha_system/cli/study.py`

Expected docs/configs:

* `docs/FACTOR_DIAGNOSTICS.md`
* study configs under `configs/studies/examples/`

Expected tests:

* `tests/unit/test_pearson_ic.py`
* `tests/unit/test_rank_ic.py`
* `tests/unit/test_ic_decay.py`
* `tests/unit/test_ic_by_calendar_period.py`
* `tests/unit/test_icir.py`
* `tests/unit/test_bucket_monotonicity.py`
* `tests/unit/test_bucket_tail_expectancy.py`
* `tests/unit/test_bucket_u_shape_profile.py`
* `tests/unit/test_event_study_counts.py`
* `tests/unit/test_false_breakout_rate.py`
* `tests/unit/test_event_target_before_stop.py`
* `tests/unit/test_regime_filter_uplift.py`
* `tests/unit/test_regime_filter_coverage.py`
* `tests/unit/test_execution_filter_sensitivity.py`
* `tests/unit/test_management_feature_metrics.py`
* `tests/no_lookahead/test_diagnostics_label_availability.py`
* `tests/no_lookahead/test_diagnostics_factor_label_alignment.py`
* `tests/integration/test_study_run_tempdir.py`
* `tests/integration/test_study_registry_tempdb.py`
* `tests/integration/test_study_cli_help.py`
* `tests/unit/test_study_no_tradability_claims.py`
* `tests/unit/test_study_artifact_policy.py`

### Forbidden Changes

* No full study outputs committed.
* No generated factor study directory committed unless tiny curated fixture is explicitly scoped.
* No raw data committed.
* No canonical generated data committed.
* No generated factor stores committed.
* No generated label stores committed.
* No heavy artifacts committed.
* No local SQLite DB committed.
* No broker/live trading scope.
* No paper trading scope.
* No alpha/profitability/tradability claims.
* No diagnostics-as-PnL-truth claims.
* No candidate promotion.
* No strategy/backtest scope creep.
* No uncontrolled scope expansion.
* No hidden failed runs.
* No test weakening or gaming.
* No `git add .`.
* No `git add -A`.

### Validation Commands

Ralph must run and record:

```bash
python -m pytest tests/unit tests/integration tests/no_lookahead
python -m alpha_system.cli study run --help
git status --short
find artifacts/factor_studies -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
```

If console script is available:

```bash
alpha study run --help
```

If lint/type tools are configured:

```bash
python -m ruff check .
python -m mypy src
```

Required validation coverage:

* Pearson IC correctness,
* Rank IC correctness,
* IC by horizon,
* IC decay,
* IC by day/week/month,
* ICIR,
* bucket monotonicity,
* tail expectancy,
* U-shape profile,
* event study sample counts,
* false breakout rate,
* target-before-stop probability,
* post-event MFE/MAE,
* regime filter uplift and coverage,
* spread/liquidity/slippage sensitivity,
* management path metrics,
* no-lookahead label availability,
* factor/label version alignment,
* temp registry run recording,
* CLI help,
* no tradability claim language.

### Artifact Policy

Commit only:

* source files,
* docs,
* configs,
* tests,
* tiny expected-output fixtures if explicitly needed.

Do not commit:

* full diagnostics outputs,
* large CSVs,
* generated plots except tiny curated fixtures,
* local study artifact directories,
* local DB files,
* raw/canonical data,
* generated factor/label stores,
* logs,
* caches,
* temp files.

Stage explicit files only. Never use `git add .` or `git add -A`.

### Done Criteria

* Diagnostics engine computes required metrics on deterministic fixtures.
* `alpha study run` help works.
* Diagnostics include sample sizes and warnings.
* Diagnostics validate factor/label/data versions.
* Diagnostics enforce label availability and alignment.
* Diagnostics do not emit tradability or profitability claims.
* Study run registry integration works in temp DB tests.
* No full study outputs are committed.
* Handoff exists and records validation results.
* Claude review passes.

### Handoff Requirements

Create:

```text
handoffs/ASV1-P12.md
runs/<run_id>/phases/ASV1-P12/handoff.md
```

Handoff must include:

* diagnostic coverage table,
* CLI behavior summary,
* factor/label alignment summary,
* no-lookahead validation summary,
* sample-size warning behavior,
* registry integration summary,
* tests run and results,
* artifact output policy,
* statistical limitations,
* no tradability claim confirmation,
* confirmation that no full study outputs were committed,
* confirmation that no broker/live scope was introduced,
* known limitations,
* review focus.

### Review Requirements

Claude Opus 4.8 xhigh review required.

Review must verify:

* diagnostic completeness,
* no-lookahead factor/label alignment,
* sample-size and warning discipline,
* no overclaiming,
* no PnL truth confusion,
* registry integration,
* artifact policy,
* no broker/live scope,
* no test weakening.

### Auto-Merge Eligibility

Auto PR and auto merge allowed if:

* tests pass,
* CLI help works,
* handoff validates,
* Claude verdict is `PASS` or `PASS_WITH_WARNINGS`,
* no full study outputs or DBs are staged,
* no raw/heavy artifacts are staged,
* artifact policy passes,
* semantic done-check passes.

---

## ASV1-P13 — Factor Card and Report Generation

### Phase ID

`ASV1-P13`

### Phase Name

Factor Card and Report Generation

### Lane

YELLOW

### Dependencies

* `ASV1-P12`

### Purpose

Implement factor card and study report generation that summarizes diagnostics, stability, correlations, clusters, warnings, and promotion recommendations without unsupported alpha/profitability/tradability claims.

This phase turns diagnostics into reviewable evidence artifacts while preserving the rule that evidence artifacts are not automatic candidate approvals.

### Scope

Create or update:

* `src/alpha_system/reports/factor_card.py`
* `src/alpha_system/reports/study_report.py`
* `src/alpha_system/reports/report_models.py`
* `src/alpha_system/reports/prohibited_claims.py`
* `src/alpha_system/reports/templates/`
* `docs/FACTOR_CARDS.md`
* `docs/REPORT_LANGUAGE_POLICY.md`
* `configs/reports/factor_card.yaml`
* tests for report sections, metadata, warnings, recommendation vocabulary, prohibited language, and fixture output.

Reports must include:

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
* data version,
* factor version,
* label version,
* code/config hash references where available,
* run manifest path,
* no-lookahead validation status,
* review status,
* diagnostic summary,
* limitations section.

Allowed promotion recommendations:

* `reject`
* `needs_more_data`
* `candidate_for_strategy_test`
* `candidate_for_review`
* `do_not_promote`

The report generator must not allow unsupported claim language, including:

* profitable,
* tradable,
* production-ready,
* guaranteed alpha,
* market-beating,
* robust without evidence,
* approved without review,
* live-ready,
* deployable,
* production candidate.

The generator must either reject prohibited language or flag it as a blocking report validation error in tests.

### Non-Goals

* No candidate approval workflow beyond evidence artifact creation.
* No promotion to approved.
* No strategy backtest.
* No ML report bundle.
* No full review bundle/source map; that is ASV1-P27.
* No live trading.
* No broker integration.
* No web server.
* No large report bundle commit.
* No alpha/tradability claims.

### Expected Files / Directories

Expected source files:

* `src/alpha_system/reports/factor_card.py`
* `src/alpha_system/reports/study_report.py`
* `src/alpha_system/reports/report_models.py`
* `src/alpha_system/reports/prohibited_claims.py`
* templates under `src/alpha_system/reports/templates/`

Expected docs/configs:

* `docs/FACTOR_CARDS.md`
* `docs/REPORT_LANGUAGE_POLICY.md`
* `configs/reports/factor_card.yaml`

Expected tests:

* `tests/unit/test_factor_card_sections.py`
* `tests/unit/test_factor_card_metadata.py`
* `tests/unit/test_factor_card_stability_sections.py`
* `tests/unit/test_factor_card_warnings.py`
* `tests/unit/test_factor_card_recommendations.py`
* `tests/unit/test_factor_card_review_status.py`
* `tests/unit/test_report_prohibited_claims.py`
* `tests/unit/test_report_language_policy.py`
* `tests/integration/test_factor_card_fixture_output.py`
* `tests/integration/test_study_report_fixture_output.py`
* `tests/unit/test_report_artifact_policy.py`

### Forbidden Changes

* No full report bundles committed.
* No generated heavy artifacts committed.
* No local report directories committed except tiny explicit fixtures.
* No raw data committed.
* No canonical generated data committed.
* No local SQLite DB committed.
* No broker/live trading scope.
* No paper trading scope.
* No alpha/profitability/tradability claims.
* No automatic candidate approval.
* No unreviewed promotion.
* No strategy/backtest scope creep.
* No uncontrolled scope expansion.
* No hidden failed runs.
* No test weakening or gaming.
* No `git add .`.
* No `git add -A`.

### Validation Commands

Ralph must run and record:

```bash
python -m pytest tests/unit tests/integration
git status --short
find artifacts -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true
```

If lint/type tools are configured:

```bash
python -m ruff check .
python -m mypy src
```

Required validation coverage:

* report contains required metadata,
* report includes all stability sections,
* report includes correlation and factor cluster fields,
* report includes only allowed promotion recommendation vocabulary,
* report includes sample size and warnings,
* report includes no-lookahead validation status,
* report includes review status,
* prohibited claim language is blocked,
* insufficient sample size warnings appear,
* report references manifest and versions,
* generated output fixture remains tiny.

### Artifact Policy

Commit only:

* source files,
* templates,
* docs,
* configs,
* tests,
* tiny expected report fixtures if explicitly needed.

Do not commit:

* full generated report bundles,
* large HTML,
* large plots,
* generated artifact directories,
* local DBs,
* raw/canonical data,
* logs,
* caches.

Stage explicit files only. Never use `git add .` or `git add -A`.

### Done Criteria

* Factor card generator exists.
* Study report generator exists.
* Required report sections are represented.
* Prohibited language tests pass.
* Promotion recommendations are limited and evidence-oriented.
* Reports do not auto-approve candidates.
* Reports preserve no-lookahead and version metadata.
* No full report bundle is committed.
* Handoff exists and records validation results.
* Claude review passes.

### Handoff Requirements

Create:

```text
handoffs/ASV1-P13.md
runs/<run_id>/phases/ASV1-P13/handoff.md
```

Handoff must include:

* report section coverage,
* prohibited claim test results,
* recommendation vocabulary,
* template summary,
* fixture output path and size if any,
* artifact policy confirmation,
* no overclaim confirmation,
* confirmation that no full report bundle was committed,
* confirmation that no broker/live scope was introduced,
* known limitations,
* review focus.

### Review Requirements

Claude Opus 4.8 xhigh review required.

Review must verify:

* report evidence language,
* prohibited claim enforcement,
* promotion discipline,
* metadata completeness,
* stability section coverage,
* no auto-approval,
* no large report artifacts,
* no broker/live scope,
* no test weakening.

### Auto-Merge Eligibility

Auto PR and auto merge allowed if:

* tests pass,
* handoff validates,
* Claude verdict is `PASS` or `PASS_WITH_WARNINGS`,
* no full report bundles are staged,
* no DB/heavy artifacts are staged,
* artifact policy passes,
* semantic done-check passes.

---

## ASV1-P14 — Signal Store and StrategySpec Layer

### Phase ID

`ASV1-P14`

### Phase Name

Signal Store and StrategySpec Layer

### Lane

YELLOW

### Dependencies

* `ASV1-P11`
* `ASV1-P13`

### Purpose

Implement signal store and StrategySpec foundations while preserving strict separation between factors, signals, strategies, management, portfolio, and execution.

This phase defines how reviewed factor information can become strategy-intent signals without introducing fills, slippage, position sizing, portfolio allocation, or live trading responsibilities into strategy code.

### Scope

Create or update:

* `src/alpha_system/signals/spec.py`
* `src/alpha_system/signals/store.py`
* `src/alpha_system/signals/validation.py`
* `src/alpha_system/signals/io.py`
* `src/alpha_system/strategies/spec.py`
* `src/alpha_system/strategies/templates.py`
* `src/alpha_system/strategies/validation.py`
* `strategies/templates/`
* `strategies/researcher_sandbox/`
* `docs/SIGNALS_AND_STRATEGIES.md`
* `docs/STRATEGY_BOUNDARIES.md`
* `configs/strategies/examples/`
* tests for signal schema, strategy dependencies, forbidden responsibilities, label leakage, timestamps, deterministic template behavior, registry integration, and artifact policy.

StrategySpec must produce:

* entry signal,
* exit signal,
* direction,
* optional confidence score,
* optional desired exposure,
* required factor dependencies.

StrategySpec must not directly handle:

* account equity,
* position sizing,
* fills,
* order lifecycle,
* slippage,
* commission,
* partial take-profit accounting,
* portfolio aggregation.

Signal records must include enough timing metadata to support no-lookahead validation:

* instrument id,
* `event_ts`,
* `available_ts`,
* session id,
* bar index,
* signal type,
* direction,
* optional score/confidence,
* strategy id/version,
* factor version dependencies,
* quality flags.

Rules:

* signal timestamps must respect factor `available_ts`,
* strategies may read only declared factor dependencies,
* labels are rejected as live strategy inputs,
* raw ad hoc data columns outside declared dependencies are rejected,
* strategy versioning must be registry-backed in temporary DB tests.

### Non-Goals

* No reference backtest execution.
* No position management implementation.
* No portfolio sizing.
* No cost/slippage/fill logic.
* No order lifecycle.
* No broker orders.
* No generated signal store commitment.
* No profitability/tradability claims.
* No paper/live trading.

### Expected Files / Directories

Expected source files:

* `src/alpha_system/signals/spec.py`
* `src/alpha_system/signals/store.py`
* `src/alpha_system/signals/validation.py`
* `src/alpha_system/signals/io.py`
* `src/alpha_system/strategies/spec.py`
* `src/alpha_system/strategies/templates.py`
* `src/alpha_system/strategies/validation.py`

Expected directories:

* `strategies/templates/`
* `strategies/researcher_sandbox/`

Expected docs/configs:

* `docs/SIGNALS_AND_STRATEGIES.md`
* `docs/STRATEGY_BOUNDARIES.md`
* `configs/strategies/examples/`

Expected tests:

* `tests/unit/test_signal_schema.py`
* `tests/unit/test_signal_available_ts_fields.py`
* `tests/unit/test_strategy_spec_fields.py`
* `tests/unit/test_strategy_factor_dependencies.py`
* `tests/unit/test_strategy_forbidden_responsibilities.py`
* `tests/no_lookahead/test_strategy_no_label_inputs.py`
* `tests/no_lookahead/test_strategy_no_raw_adhoc_inputs.py`
* `tests/no_lookahead/test_signal_available_ts.py`
* `tests/unit/test_template_strategy_deterministic.py`
* `tests/integration/test_strategy_registry_tempdb.py`
* `tests/integration/test_signal_store_tempdir.py`
* `tests/unit/test_signal_artifact_policy.py`

### Forbidden Changes

* No generated signal store committed.
* No signal datasets committed outside tiny fixtures.
* No raw data committed.
* No canonical generated data committed.
* No materialized factor/label stores committed.
* No heavy artifacts committed.
* No local SQLite DB committed.
* No fills/slippage/commission/account equity in StrategySpec.
* No position sizing in StrategySpec.
* No partial take-profit accounting in StrategySpec.
* No portfolio aggregation in StrategySpec.
* No label values as live strategy inputs.
* No broker/live trading scope.
* No paper trading scope.
* No alpha/profitability/tradability claims.
* No uncontrolled strategy explosion.
* No uncontrolled scope expansion.
* No hidden failed runs.
* No test weakening or gaming.
* No `git add .`.
* No `git add -A`.

### Validation Commands

Ralph must run and record:

```bash
python -m pytest tests/unit tests/integration tests/no_lookahead
git status --short
find data -path "*signals*" -type f -print || true
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
```

If lint/type tools are configured:

```bash
python -m ruff check .
python -m mypy src
```

Required validation coverage:

* signal schema fields,
* signal timing fields,
* strategy required fields,
* strategy dependency declarations,
* forbidden responsibilities absent,
* labels rejected as live inputs,
* raw ad hoc inputs rejected,
* `available_ts` respected,
* deterministic template output,
* strategy versions registered in temp DB,
* signal store writes only to temp/local-only path in tests,
* no generated signal outputs committed.

### Artifact Policy

Commit only:

* source files,
* docs,
* configs,
* strategy templates,
* tests,
* tiny deterministic fixtures if needed.

Do not commit:

* generated signal datasets,
* local signal stores,
* local DBs,
* raw data,
* generated heavy artifacts,
* logs,
* caches.

Stage explicit files only. Never use `git add .` or `git add -A`.

### Done Criteria

* Signal store exists.
* StrategySpec exists.
* Strategy/factor/signal boundaries are tested.
* Strategy forbidden responsibilities are tested.
* Label leakage is rejected.
* Raw ad hoc strategy inputs are rejected.
* Signal timing respects `available_ts`.
* Strategy versions can be registered in temp SQLite.
* No generated signal outputs are committed.
* Handoff exists and records validation results.
* Claude review passes.

### Handoff Requirements

Create:

```text
handoffs/ASV1-P14.md
runs/<run_id>/phases/ASV1-P14/handoff.md
```

Handoff must include:

* signal/strategy summary,
* StrategySpec responsibility boundary summary,
* dependency validation summary,
* no-lookahead timing summary,
* label/raw-input rejection summary,
* tests run and results,
* registry integration summary,
* artifact policy confirmation,
* confirmation that no generated signal store was committed,
* confirmation that no broker/live scope was introduced,
* known limitations,
* review focus.

### Review Requirements

Claude Opus 4.8 xhigh review required.

Review must verify:

* domain boundary enforcement,
* StrategySpec responsibility restrictions,
* no label leakage,
* no raw ad hoc strategy inputs,
* no execution logic in strategy,
* no portfolio/management logic in strategy,
* artifact policy,
* no overclaims,
* no broker/live scope,
* no test weakening.

### Auto-Merge Eligibility

Auto PR and auto merge allowed if:

* tests pass,
* handoff validates,
* Claude verdict is `PASS` or `PASS_WITH_WARNINGS`,
* no signal datasets or DBs are staged,
* no raw/heavy artifacts are staged,
* artifact policy passes,
* semantic done-check passes.

---

## ASV1-P15 — Reference 1-Minute Backtest Truth

### Phase ID

`ASV1-P15`

### Phase Name

Reference 1-Minute Backtest Truth

### Lane

YELLOW

### Dependencies

* `ASV1-P14`

### Purpose

Implement the conservative Python reference 1-minute bar execution truth engine for v1 bar-level strategy research.

This engine is the single canonical PnL truth for 1-minute bar-level strategies in this campaign. It must preserve point-in-time correctness and conservative next-bar execution semantics.

### Scope

Create or update:

* `src/alpha_system/backtest/reference.py`
* `src/alpha_system/backtest/orders.py`
* `src/alpha_system/backtest/fills.py`
* `src/alpha_system/backtest/accounting.py`
* `src/alpha_system/backtest/trades.py`
* `src/alpha_system/backtest/equity.py`
* `src/alpha_system/backtest/results.py`
* `src/alpha_system/backtest/engine_config.py`
* `src/alpha_system/cli/backtest.py`
* `docs/REFERENCE_BACKTEST.md`
* `docs/BACKTEST_TRUTH_POLICY.md`
* `configs/execution/reference_1min.yaml`
* tests for conservative next-bar execution, accounting, trade journal, equity curve, no-lookahead behavior, same-bar ambiguity, registry integration, and CLI help.

CLI command introduced:

```bash
alpha backtest run
```

Command purpose:

* run canonical reference 1-minute bar strategy backtest.

Command inputs:

* strategy version/spec,
* management spec placeholder or baseline,
* portfolio spec placeholder or baseline,
* data version,
* factor versions,
* execution config,
* date/session range,
* optional registry path,
* optional output directory,
* optional run manifest path.

Command outputs:

* local trade/equity artifacts,
* summary report,
* registry entry,
* run manifest.

Artifacts:

* full trade/equity logs are local-only unless tiny fixtures,
* summary may be committed only if curated and tiny,
* generated outputs under `artifacts/execution_validations/` or equivalent are local-only.

Validation checks:

* strategy dependency availability,
* factor version references,
* data version reference,
* next-bar execution,
* no same-bar signal execution,
* data latency,
* cost hook presence,
* no-lookahead,
* run manifest,
* registry entry.

Reference rules:

* completed 1-minute bar can only be used after `bar_end_ts` plus configured latency,
* signals based on bar `t` cannot execute inside bar `t` by default,
* default execution uses next-bar conservative execution,
* same-bar stop/target ambiguity is handled conservatively,
* EOD exit is supported where configured,
* trade journal records required accounting fields,
* equity curve is deterministic,
* reference engine is truth,
* fast path may not define separate PnL truth.

This phase may include simple baseline management/portfolio placeholders only as needed to run the reference engine. Full management and portfolio modules are handled in later phases.

### Non-Goals

* No fast path.
* No NumPy/Numba acceleration.
* No full management module beyond baseline placeholders required for reference tests.
* No full portfolio module beyond baseline placeholders required for reference tests.
* No advanced event-driven finalist engine.
* No L2 replay.
* No broker/paper/live trading.
* No production order lifecycle.
* No alpha/profitability/tradability claims.
* No performance marketing reports.

### Expected Files / Directories

Expected source files:

* `src/alpha_system/backtest/reference.py`
* `src/alpha_system/backtest/orders.py`
* `src/alpha_system/backtest/fills.py`
* `src/alpha_system/backtest/accounting.py`
* `src/alpha_system/backtest/trades.py`
* `src/alpha_system/backtest/equity.py`
* `src/alpha_system/backtest/results.py`
* `src/alpha_system/backtest/engine_config.py`
* `src/alpha_system/cli/backtest.py`

Expected docs/configs:

* `docs/REFERENCE_BACKTEST.md`
* `docs/BACKTEST_TRUTH_POLICY.md`
* `configs/execution/reference_1min.yaml`

Expected tests:

* `tests/unit/test_reference_next_bar_entry.py`
* `tests/unit/test_reference_next_bar_exit.py`
* `tests/no_lookahead/test_no_same_bar_signal_execution.py`
* `tests/unit/test_same_bar_stop_target_conservative.py`
* `tests/unit/test_reference_accounting.py`
* `tests/unit/test_trade_journal_schema.py`
* `tests/unit/test_equity_curve_schema.py`
* `tests/unit/test_eod_flat_behavior.py`
* `tests/no_lookahead/test_backtest_data_latency.py`
* `tests/no_lookahead/test_backtest_signal_availability.py`
* `tests/integration/test_reference_backtest_fixture.py`
* `tests/integration/test_backtest_registry_tempdb.py`
* `tests/integration/test_backtest_cli_help.py`
* `tests/unit/test_backtest_artifact_policy.py`

### Forbidden Changes

* No full trade logs committed.
* No generated equity curves committed except tiny explicit fixtures.
* No generated execution artifact directories committed.
* No raw data committed.
* No canonical generated data committed.
* No generated factor/label/signal stores committed.
* No heavy artifacts committed.
* No local SQLite DB committed.
* No fast path or second PnL truth.
* No same-bar optimistic fills by default.
* No broker/live trading scope.
* No paper trading scope.
* No alpha/profitability/tradability claims.
* No strategy promotion or candidate approval.
* No uncontrolled scope expansion.
* No hidden failed runs.
* No test weakening or gaming.
* No `git add .`.
* No `git add -A`.

### Validation Commands

Ralph must run and record:

```bash
python -m pytest tests/unit tests/integration tests/no_lookahead
python -m alpha_system.cli backtest run --help
git status --short
find artifacts/execution_validations -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
```

If console script is available:

```bash
alpha backtest run --help
```

If lint/type tools are configured:

```bash
python -m ruff check .
python -m mypy src
```

Required validation coverage:

* next-bar entry,
* next-bar exit,
* no same-bar signal execution,
* same-bar stop/target conservative order,
* accounting correctness,
* trade journal schema,
* equity curve schema,
* EOD flat behavior when configured,
* data latency enforcement,
* signal availability enforcement,
* temp registry run recording,
* CLI help,
* no generated backtest outputs committed.

### Artifact Policy

Commit only:

* source files,
* docs,
* configs,
* tests,
* tiny deterministic fixtures.

Do not commit:

* full trade logs,
* full equity curves,
* generated execution artifacts,
* local DB files,
* raw/canonical data,
* generated factor/label/signal stores,
* logs,
* caches,
* heavy artifacts.

Stage explicit files only. Never use `git add .` or `git add -A`.

### Done Criteria

* Reference engine runs on deterministic tiny fixture.
* Conservative execution semantics are tested.
* No-lookahead signal/data availability tests pass.
* Same-bar stop/target ambiguity is conservative.
* Trade and equity outputs are structurally defined.
* `alpha backtest run` help works.
* Registry integration works in temp tests.
* Docs identify reference engine as canonical truth.
* No generated backtest outputs are committed.
* Handoff exists and records validation results.
* Claude review passes.

### Handoff Requirements

Create:

```text
handoffs/ASV1-P15.md
runs/<run_id>/phases/ASV1-P15/handoff.md
```

Handoff must include:

* reference engine behavior summary,
* reference truth policy summary,
* no-lookahead test summary,
* conservative fill semantics,
* same-bar ambiguity handling,
* trade/equity schema summary,
* registry integration summary,
* tests run and results,
* known limitations,
* artifact policy confirmation,
* confirmation that no trade/equity outputs were committed,
* confirmation that no broker/live scope was introduced,
* review focus.

### Review Requirements

Claude Opus 4.8 xhigh review required.

Review must verify:

* execution truth semantics,
* no-lookahead behavior,
* next-bar execution default,
* same-bar ambiguity handling,
* no conflicting PnL truth,
* no fast path truth creep,
* no live/broker scope,
* no unsupported claims,
* artifact policy compliance,
* no test weakening.

### Auto-Merge Eligibility

Auto PR and auto merge allowed if:

* tests pass,
* CLI help works,
* handoff validates,
* Claude verdict is `PASS` or `PASS_WITH_WARNINGS`,
* no backtest outputs or DBs are staged,
* no raw/heavy artifacts are staged,
* artifact policy passes,
* semantic done-check passes.

---

## ASV1-P16 — Cost, Slippage, and Conservative Execution Semantics

### Phase ID

`ASV1-P16`

### Phase Name

Cost, Slippage, and Conservative Execution Semantics

### Lane

YELLOW

### Dependencies

* `ASV1-P15`

### Purpose

Implement cost, spread, slippage, liquidity, participation, adverse-selection proxy, and conservative fill model support for the reference backtest engine.

This phase hardens the execution assumptions of the reference engine while preserving the rule that this is still research simulation, not live trading or broker execution.

### Scope

Create or update:

* `src/alpha_system/backtest/costs.py`
* `src/alpha_system/backtest/slippage.py`
* `src/alpha_system/backtest/liquidity.py`
* `src/alpha_system/backtest/fill_models.py`
* `src/alpha_system/backtest/execution_config.py`
* `src/alpha_system/backtest/conservative_semantics.py`
* `docs/COST_AND_SLIPPAGE.md`
* `docs/CONSERVATIVE_EXECUTION_SEMANTICS.md`
* `configs/execution/cost_models/`
* tests for commissions, spread cost, slippage, volume participation caps, liquidity rejection, adverse-selection proxy hooks, conservative fill prices, and reference engine integration.

Cost/slippage support:

* fixed commission,
* per-share/per-contract commission,
* bps cost,
* half-spread/full-spread assumptions,
* configurable slippage bps,
* spread-sensitive slippage,
* volume participation cap,
* liquidity rejection/penalty,
* adverse-selection proxy hook,
* deterministic fixture behavior.

Conservative execution semantics must cover:

* next-bar default execution,
* no same-bar signal execution by default,
* conservative same-bar stop/target ordering,
* spread-aware fills when bid/ask are available,
* explicit behavior when bid/ask are missing,
* explicit zero-cost fixture configuration only,
* default non-test configs must be conservative.

Reference integration:

* reference backtest must use configured cost model,
* non-test defaults must not silently be zero-cost,
* zero-cost may exist only as explicit fixture/test config,
* spread fields must be used when present,
* slippage assumptions must appear in run/config metadata.

### Non-Goals

* No broker-specific commission schedule.
* No live execution adapter.
* No paper trading adapter.
* No market-impact model beyond simple local research approximation.
* No L2 passive fill simulation.
* No production execution claims.
* No alpha/profitability/tradability claims.
* No replacement of reference engine truth.
* No fast path implementation.

### Expected Files / Directories

Expected source files:

* `src/alpha_system/backtest/costs.py`
* `src/alpha_system/backtest/slippage.py`
* `src/alpha_system/backtest/liquidity.py`
* `src/alpha_system/backtest/fill_models.py`
* `src/alpha_system/backtest/execution_config.py`
* `src/alpha_system/backtest/conservative_semantics.py`

Expected docs/configs:

* `docs/COST_AND_SLIPPAGE.md`
* `docs/CONSERVATIVE_EXECUTION_SEMANTICS.md`
* config examples under `configs/execution/cost_models/`

Expected tests:

* `tests/unit/test_fixed_commission.py`
* `tests/unit/test_per_unit_commission.py`
* `tests/unit/test_bps_cost.py`
* `tests/unit/test_half_full_spread_cost.py`
* `tests/unit/test_slippage_bps.py`
* `tests/unit/test_spread_sensitive_slippage.py`
* `tests/unit/test_volume_participation_cap.py`
* `tests/unit/test_liquidity_rejection.py`
* `tests/unit/test_adverse_selection_proxy_hook.py`
* `tests/unit/test_conservative_fill_price.py`
* `tests/unit/test_missing_bid_ask_behavior.py`
* `tests/unit/test_zero_cost_only_explicit_fixture.py`
* `tests/integration/test_reference_backtest_cost_model.py`
* `tests/integration/test_reference_backtest_slippage_model.py`
* `tests/no_lookahead/test_cost_model_no_same_bar_optimism.py`
* `tests/unit/test_execution_artifact_policy.py`

### Forbidden Changes

* No execution validation artifacts committed.
* No full trade logs committed.
* No generated equity curves committed.
* No raw data committed.
* No canonical generated data committed.
* No materialized factor/label/signal stores committed.
* No heavy artifacts committed.
* No local SQLite DB committed.
* No broker/live trading scope.
* No paper trading scope.
* No broker-specific adapters.
* No silent zero-cost default for non-test configs.
* No optimistic same-bar execution default.
* No L2 passive fill simulation.
* No alpha/profitability/tradability claims.
* No execution-quality production claims.
* No uncontrolled scope expansion.
* No hidden failed runs.
* No test weakening or gaming.
* No `git add .`.
* No `git add -A`.

### Validation Commands

Ralph must run and record:

```bash
python -m pytest tests/unit tests/integration tests/no_lookahead
git status --short
find artifacts/execution_validations -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
```

If lint/type tools are configured:

```bash
python -m ruff check .
python -m mypy src
```

Required validation coverage:

* fixed commission,
* per-unit commission,
* bps cost,
* half/full spread,
* slippage bps,
* spread-sensitive cost,
* volume participation cap,
* liquidity rejection,
* adverse-selection proxy hook,
* deterministic conservative fill price,
* missing bid/ask behavior,
* explicit zero-cost fixture configuration,
* reference engine cost integration,
* reference engine slippage integration,
* no same-bar optimism.

### Artifact Policy

Commit only:

* source files,
* docs,
* configs,
* tests,
* tiny deterministic fixtures if required.

Do not commit:

* generated execution outputs,
* trade logs,
* equity logs,
* execution validation artifact directories,
* local DBs,
* raw/canonical data,
* generated factor/label/signal stores,
* logs,
* caches,
* heavy artifacts.

Stage explicit files only. Never use `git add .` or `git add -A`.

### Done Criteria

* Cost/slippage modules integrate with the reference engine.
* Nonzero cost behavior is tested.
* Conservative defaults are documented.
* Spread fields are used when present.
* Missing bid/ask behavior is explicit and tested.
* Zero-cost is allowed only through explicit fixture/test configs.
* Conservative execution semantics are documented.
* No live/broker execution scope is introduced.
* No generated execution outputs are committed.
* Handoff exists and records validation results.
* Claude review passes.

### Handoff Requirements

Create:

```text
handoffs/ASV1-P16.md
runs/<run_id>/phases/ASV1-P16/handoff.md
```

Handoff must include:

* cost model summary,
* slippage model summary,
* conservative execution semantics summary,
* default assumptions,
* zero-cost fixture policy,
* reference integration summary,
* tests run and results,
* limitations,
* artifact policy confirmation,
* confirmation that no execution artifacts were committed,
* confirmation that no broker/live scope was introduced,
* review focus.

### Review Requirements

Claude Opus 4.8 xhigh review required.

Review must verify:

* conservative execution assumptions,
* spread/slippage integration,
* zero-cost restrictions,
* reference engine integration,
* no same-bar optimism,
* no broker/live scope,
* no production execution claims,
* no overclaims,
* artifact policy compliance,
* no test weakening.

### Auto-Merge Eligibility

Auto PR and auto merge allowed if:

* tests pass,
* handoff validates,
* Claude verdict is `PASS` or `PASS_WITH_WARNINGS`,
* no execution artifacts or DBs are staged,
* no raw/heavy artifacts are staged,
* artifact policy passes,
* semantic done-check passes.

## ASV1-P17 — Position Management Module

### Phase ID

`ASV1-P17`

### Phase Name

Position Management Module

### Lane

YELLOW

### Dependencies

* `ASV1-P16`

### Purpose

Implement position management specifications and deterministic management behavior for stops, targets, partial exits, trailing logic, time exits, EOD exits, cooldowns, trade-count limits, and holding limits as inputs to the reference backtest engine.

This phase must keep management separate from StrategySpec, PortfolioSpec, and execution truth. Strategies may produce intent, but position management controls how an open position is managed after entry under the reference backtest engine.

### Scope

Create or update:

* `src/alpha_system/management/spec.py`
* `src/alpha_system/management/stops.py`
* `src/alpha_system/management/targets.py`
* `src/alpha_system/management/partials.py`
* `src/alpha_system/management/trailing.py`
* `src/alpha_system/management/rules.py`
* `src/alpha_system/management/state.py`
* `src/alpha_system/management/validation.py`
* `src/alpha_system/management/integration.py`
* `src/alpha_system/cli/management.py`
* `docs/POSITION_MANAGEMENT.md`
* `docs/MANAGEMENT_OVERFIT_POLICY.md`
* `configs/management/examples/`
* tests for management specs, deterministic rule behavior, accounting integration, conservative path handling, and CLI help.

ManagementSpec must support:

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

Management rules must preserve:

* conservative same-bar stop/target handling,
* deterministic partial exit accounting,
* explicit rule ordering,
* reproducible trade journal effects,
* no hidden state across sessions unless explicitly configured,
* no strategy-level accounting,
* no portfolio-level allocation,
* no broker order lifecycle.

CLI command expanded:

```bash
alpha management grid
```

In this phase, the command may expose help and validate management-grid config structure. Full survivor-based bounded management-grid execution is implemented in ASV1-P21.

Command purpose in this phase:

* expose management grid command help,
* validate management config files,
* validate management parameter ranges,
* reject unbounded management-grid definitions,
* document that actual survivor-based execution is deferred to ASV1-P21.

Command inputs:

* management config path,
* optional strategy/grid reference placeholder,
* optional validation-only flag,
* optional registry path for validation metadata if already available.

Command outputs:

* console validation summary,
* optional tiny validation summary,
* no management study outputs in this phase.

### Non-Goals

* No full management grid execution yet.
* No survivor workflow yet.
* No candidate approval.
* No automatic promotion.
* No portfolio allocation logic beyond management references.
* No ML.
* No live order lifecycle.
* No broker integration.
* No paper trading.
* No production execution semantics.
* No alpha/profitability/tradability claims.

### Expected Files / Directories

Expected source files:

* `src/alpha_system/management/spec.py`
* `src/alpha_system/management/stops.py`
* `src/alpha_system/management/targets.py`
* `src/alpha_system/management/partials.py`
* `src/alpha_system/management/trailing.py`
* `src/alpha_system/management/rules.py`
* `src/alpha_system/management/state.py`
* `src/alpha_system/management/validation.py`
* `src/alpha_system/management/integration.py`
* `src/alpha_system/cli/management.py`

Expected docs/configs:

* `docs/POSITION_MANAGEMENT.md`
* `docs/MANAGEMENT_OVERFIT_POLICY.md`
* config examples under `configs/management/examples/`

Expected tests:

* `tests/unit/test_management_spec_fields.py`
* `tests/unit/test_fixed_stop.py`
* `tests/unit/test_atr_stop.py`
* `tests/unit/test_volatility_stop.py`
* `tests/unit/test_target_r_multiple.py`
* `tests/unit/test_laddered_partials.py`
* `tests/unit/test_breakeven_stop.py`
* `tests/unit/test_trailing_stop.py`
* `tests/unit/test_time_exit.py`
* `tests/unit/test_eod_exit.py`
* `tests/unit/test_cooldown.py`
* `tests/unit/test_max_trades_per_day.py`
* `tests/unit/test_scale_in_scale_out_contracts.py`
* `tests/unit/test_max_holding_bars.py`
* `tests/unit/test_management_risk_per_trade.py`
* `tests/unit/test_management_max_position_percent.py`
* `tests/unit/test_same_bar_management_conservative.py`
* `tests/unit/test_management_rule_ordering.py`
* `tests/integration/test_management_reference_integration.py`
* `tests/integration/test_management_cli_help.py`
* `tests/unit/test_management_artifact_policy.py`

### Forbidden Changes

* No management study outputs committed.
* No management grid raw outputs committed.
* No full trade logs committed.
* No generated equity curves committed.
* No raw data committed.
* No canonical generated data committed.
* No materialized factor/label/signal stores committed.
* No heavy artifacts committed.
* No local SQLite DB committed.
* No management rules hidden inside StrategySpec.
* No account equity ownership inside StrategySpec.
* No portfolio allocation hidden inside management rules.
* No optimistic same-bar target-before-stop assumption.
* No invisible partial exit accounting.
* No broker/live trading scope.
* No paper trading scope.
* No production execution claims.
* No alpha/profitability/tradability claims.
* No automatic candidate approval.
* No uncontrolled management search.
* No uncontrolled scope expansion.
* No hidden failed runs.
* No test weakening or gaming.
* No `git add .`.
* No `git add -A`.

### Validation Commands

Ralph must run and record:

```bash
python -m pytest tests/unit tests/integration tests/no_lookahead
python -m alpha_system.cli management grid --help
git status --short
find artifacts/management_studies -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true
find artifacts/execution_validations -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
```

If console script is available:

```bash
alpha management grid --help
```

If lint/type tools are configured:

```bash
python -m ruff check .
python -m mypy src
```

Required validation coverage:

* ManagementSpec required fields,
* fixed stop,
* ATR stop,
* volatility stop,
* target R multiple,
* laddered partial take-profit accounting,
* breakeven stop update,
* trailing stop update,
* time exit,
* EOD exit,
* cooldown,
* max trades per day,
* scale-in/scale-out contract representation,
* max holding bars,
* risk per trade field behavior,
* max position percent field behavior,
* conservative same-bar handling,
* deterministic rule ordering,
* integration with reference backtest fixture,
* management CLI help,
* no generated management outputs committed.

### Artifact Policy

Commit only:

* source files,
* docs,
* configs,
* tests,
* tiny deterministic fixtures if required.

Do not commit:

* management-grid outputs,
* management study artifacts,
* full trade logs,
* generated equity curves,
* generated execution outputs,
* local DB files,
* raw/canonical data,
* generated factor/label/signal stores,
* logs,
* caches,
* heavy artifacts.

Stage explicit files only. Never use `git add .` or `git add -A`.

### Done Criteria

* ManagementSpec supports required features.
* Management rules are deterministic.
* Management logic integrates with reference engine fixtures.
* Conservative same-bar ambiguity behavior is tested.
* Partial exits are accounted for deterministically.
* Rule ordering is explicit and tested.
* `alpha management grid --help` works.
* Management grid execution remains deferred to ASV1-P21.
* Docs explain management overfit risk.
* No generated management outputs are committed.
* Handoff exists and records validation results.
* Claude review passes.

### Handoff Requirements

Create:

```text
handoffs/ASV1-P17.md
runs/<run_id>/phases/ASV1-P17/handoff.md
```

Handoff must include:

* management feature coverage table,
* ManagementSpec field coverage,
* rule-ordering summary,
* partial-exit accounting summary,
* conservative ambiguity summary,
* reference integration summary,
* CLI help result,
* tests run and results,
* artifact policy confirmation,
* confirmation that no management outputs were committed,
* confirmation that no local DB/heavy artifacts were committed,
* confirmation that no broker/live scope was introduced,
* known limitations,
* review focus.

### Review Requirements

Claude Opus 4.8 xhigh review required.

Review must verify:

* management/accounting behavior,
* conservative ambiguity handling,
* partial exit handling,
* deterministic rule ordering,
* separation from StrategySpec,
* separation from PortfolioSpec,
* no live/broker order lifecycle,
* no overfit claims,
* no generated artifacts,
* artifact policy compliance,
* no test weakening.

### Auto-Merge Eligibility

Auto PR and auto merge allowed if:

* tests pass,
* CLI help works,
* handoff validates,
* Claude verdict is `PASS` or `PASS_WITH_WARNINGS`,
* no management outputs or DBs are staged,
* no raw/heavy artifacts are staged,
* artifact policy passes,
* semantic done-check passes.

---

## ASV1-P18 — Portfolio Target and Sizing Layer

### Phase ID

`ASV1-P18`

### Phase Name

Portfolio Target and Sizing Layer

### Lane

YELLOW

### Dependencies

* `ASV1-P17`

### Purpose

Implement portfolio target, sizing, capital allocation, risk limit, and signal-to-target conversion foundations while keeping strategy, management, and execution responsibilities separate.

This phase establishes portfolio-level abstractions needed for future multi-symbol research and risk-controlled backtests without introducing broker account sync or live portfolio management.

### Scope

Create or update:

* `src/alpha_system/portfolio/spec.py`
* `src/alpha_system/portfolio/sizing.py`
* `src/alpha_system/portfolio/risk.py`
* `src/alpha_system/portfolio/targets.py`
* `src/alpha_system/portfolio/allocation.py`
* `src/alpha_system/portfolio/validation.py`
* `src/alpha_system/portfolio/integration.py`
* `docs/PORTFOLIO_LAYER.md`
* `docs/PORTFOLIO_BOUNDARIES.md`
* `configs/portfolio/examples/`
* tests for sizing, risk limits, exposure constraints, multi-symbol readiness, signal-to-target conversion, and reference integration.

PortfolioSpec must support:

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

Portfolio layer must preserve:

* StrategySpec produces signals/intent only,
* ManagementSpec manages position exits and adjustments,
* Backtest engine owns fills/accounting,
* PortfolioSpec owns target sizing and exposure constraints,
* no broker account state,
* no live order state,
* no live execution.

Portfolio target outputs must be deterministic and structurally validated.

### Non-Goals

* No optimization solver requirement.
* No production multi-asset optimizer.
* No broker account sync.
* No live portfolio.
* No paper trading.
* No execution routing.
* No order lifecycle.
* No factor/signal generation.
* No alpha/profitability/tradability claims.
* No real multi-symbol dataset requirement.

### Expected Files / Directories

Expected source files:

* `src/alpha_system/portfolio/spec.py`
* `src/alpha_system/portfolio/sizing.py`
* `src/alpha_system/portfolio/risk.py`
* `src/alpha_system/portfolio/targets.py`
* `src/alpha_system/portfolio/allocation.py`
* `src/alpha_system/portfolio/validation.py`
* `src/alpha_system/portfolio/integration.py`

Expected docs/configs:

* `docs/PORTFOLIO_LAYER.md`
* `docs/PORTFOLIO_BOUNDARIES.md`
* config examples under `configs/portfolio/examples/`

Expected tests:

* `tests/unit/test_portfolio_spec_fields.py`
* `tests/unit/test_fixed_risk_sizing.py`
* `tests/unit/test_max_position_percent.py`
* `tests/unit/test_max_gross_exposure.py`
* `tests/unit/test_max_net_exposure.py`
* `tests/unit/test_multi_symbol_limits.py`
* `tests/unit/test_signal_to_target_conversion.py`
* `tests/unit/test_insufficient_capital.py`
* `tests/unit/test_portfolio_target_schema.py`
* `tests/unit/test_future_sector_asset_constraints.py`
* `tests/unit/test_future_correlation_aware_allocation_contract.py`
* `tests/unit/test_portfolio_boundary_no_fills.py`
* `tests/integration/test_portfolio_reference_integration.py`
* `tests/unit/test_portfolio_artifact_policy.py`

### Forbidden Changes

* No portfolio run outputs committed.
* No generated portfolio artifacts committed.
* No raw data committed.
* No canonical generated data committed.
* No materialized factor/label/signal stores committed.
* No full trade logs committed.
* No heavy artifacts committed.
* No local SQLite DB committed.
* No fills/slippage/commission ownership in portfolio layer.
* No alpha logic in portfolio layer.
* No management exit logic hidden in portfolio layer.
* No broker/live trading scope.
* No paper trading scope.
* No broker account sync.
* No single-symbol-only hardcoding in core contracts.
* No alpha/profitability/tradability claims.
* No production portfolio claims.
* No uncontrolled scope expansion.
* No hidden failed runs.
* No test weakening or gaming.
* No `git add .`.
* No `git add -A`.

### Validation Commands

Ralph must run and record:

```bash
python -m pytest tests/unit tests/integration
git status --short
find artifacts -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
```

If lint/type tools are configured:

```bash
python -m ruff check .
python -m mypy src
```

Required validation coverage:

* PortfolioSpec required fields,
* fixed risk sizing,
* max position percent,
* gross exposure limits,
* net exposure limits,
* multi-symbol limit representation,
* signal-to-target conversion,
* insufficient capital behavior,
* portfolio target output schema,
* future sector/asset constraints,
* future correlation-aware allocation contract,
* portfolio layer does not own fills/slippage/commission,
* reference engine integration.

### Artifact Policy

Commit only:

* source files,
* docs,
* configs,
* tests,
* tiny deterministic fixtures if required.

Do not commit:

* portfolio run outputs,
* generated portfolio artifacts,
* full trade logs,
* generated equity outputs,
* local DBs,
* raw/canonical data,
* generated factor/label/signal stores,
* logs,
* caches,
* heavy artifacts.

Stage explicit files only. Never use `git add .` or `git add -A`.

### Done Criteria

* PortfolioSpec exists.
* Sizing and risk constraints work on fixtures.
* Signal-to-target conversion is represented and tested.
* Multi-symbol readiness is represented.
* Strategy remains separate from portfolio.
* Management remains separate from portfolio.
* Execution remains separate from portfolio.
* No broker account sync or live portfolio state exists.
* No generated portfolio outputs are committed.
* Handoff exists and records validation results.
* Claude review passes.

### Handoff Requirements

Create:

```text
handoffs/ASV1-P18.md
runs/<run_id>/phases/ASV1-P18/handoff.md
```

Handoff must include:

* portfolio feature summary,
* PortfolioSpec field coverage,
* sizing/risk behavior summary,
* multi-symbol readiness summary,
* boundary separation summary,
* reference integration summary,
* tests run and results,
* artifact policy confirmation,
* confirmation that no portfolio outputs were committed,
* confirmation that no broker/live scope was introduced,
* known limitations,
* review focus.

### Review Requirements

Claude Opus 4.8 xhigh review required.

Review must verify:

* domain separation,
* risk semantics,
* signal-to-target behavior,
* multi-symbol readiness,
* no broker account sync,
* no fills/slippage/commission ownership,
* no overclaims,
* artifact policy compliance,
* no test weakening.

### Auto-Merge Eligibility

Auto PR and auto merge allowed if:

* tests pass,
* handoff validates,
* Claude verdict is `PASS` or `PASS_WITH_WARNINGS`,
* no portfolio outputs or DBs are staged,
* no raw/heavy artifacts are staged,
* artifact policy passes,
* semantic done-check passes.

---

## ASV1-P19 — Fast Path and Reference Parity

### Phase ID

`ASV1-P19`

### Phase Name

Fast Path and Reference Parity

### Lane

YELLOW

### Dependencies

* `ASV1-P18`

### Purpose

Implement NumPy/Numba fast path scaffolding for accelerated simulation and require deterministic parity against the reference engine before any grid engine may use it.

Fast path is acceleration only. It must never define separate PnL truth. The reference 1-minute bar engine remains canonical truth.

### Scope

Create or update:

* `src/alpha_system/backtest/fast_path.py`
* `src/alpha_system/backtest/fast_arrays.py`
* `src/alpha_system/backtest/parity.py`
* `src/alpha_system/backtest/parity_cases.py`
* `src/alpha_system/backtest/fixtures.py`
* `docs/FAST_PATH_PARITY.md`
* `docs/FAST_PATH_LIMITATIONS.md`
* `tests/parity/`
* bounded performance smoke tests under `tests/performance/`.

Rules:

* Reference engine is truth.
* Fast path is acceleration only.
* Fast path cannot define separate accounting semantics.
* Fast path cannot weaken reference semantics.
* Grid engine may use fast path only after parity passes for the selected feature set.
* Unsupported fast path features must fail closed or route to reference.
* Reference behavior must not be modified merely to match fast path output.

Parity fixtures must cover:

* no-trade case,
* simple long trade,
* simple short trade if short side is supported by contracts,
* costs,
* slippage,
* fixed stop,
* target,
* same-bar ambiguity,
* partial exits,
* EOD exit,
* cooldown,
* max holding bars,
* deterministic trade journal summary,
* deterministic equity curve summary.

Fast path may support a scoped subset initially, but unsupported features must be explicit, tested, and blocked from fast-path grid use.

### Non-Goals

* No full optimization campaign.
* No Rust.
* No GPU.
* No replacement of reference engine.
* No grid engine implementation.
* No management grid implementation.
* No benchmark artifact commit.
* No alpha/profitability/tradability claims.
* No live/paper/broker integration.

### Expected Files / Directories

Expected source files:

* `src/alpha_system/backtest/fast_path.py`
* `src/alpha_system/backtest/fast_arrays.py`
* `src/alpha_system/backtest/parity.py`
* `src/alpha_system/backtest/parity_cases.py`
* `src/alpha_system/backtest/fixtures.py`

Expected docs:

* `docs/FAST_PATH_PARITY.md`
* `docs/FAST_PATH_LIMITATIONS.md`

Expected tests:

* `tests/parity/test_no_trade_parity.py`
* `tests/parity/test_simple_long_parity.py`
* `tests/parity/test_simple_short_parity.py`
* `tests/parity/test_costs_parity.py`
* `tests/parity/test_slippage_parity.py`
* `tests/parity/test_stop_target_parity.py`
* `tests/parity/test_same_bar_ambiguity_parity.py`
* `tests/parity/test_partial_exit_parity.py`
* `tests/parity/test_eod_exit_parity.py`
* `tests/parity/test_cooldown_parity.py`
* `tests/parity/test_max_holding_parity.py`
* `tests/parity/test_equity_curve_parity.py`
* `tests/parity/test_trade_summary_parity.py`
* `tests/parity/test_unsupported_fast_feature_fail_closed.py`
* `tests/performance/test_fast_path_smoke.py`
* `tests/unit/test_fast_path_artifact_policy.py`

### Forbidden Changes

* No benchmark logs committed.
* No large arrays committed.
* No generated fast-path artifacts committed.
* No raw data committed.
* No canonical generated data committed.
* No materialized factor/label/signal stores committed.
* No full trade/equity logs committed.
* No heavy artifacts committed.
* No local SQLite DB committed.
* No changing reference engine behavior only to match fast path.
* No using fast path as truth.
* No grid use of fast path without parity certification.
* No broker/live trading scope.
* No paper trading scope.
* No alpha/profitability/tradability claims.
* No uncontrolled scope expansion.
* No hidden failed runs.
* No test weakening or gaming.
* No `git add .`.
* No `git add -A`.

### Validation Commands

Ralph must run and record:

```bash
python -m pytest tests/unit tests/integration tests/parity
python -m pytest tests/performance || true
git status --short
find artifacts -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
```

If lint/type tools are configured:

```bash
python -m ruff check .
python -m mypy src
```

Required validation coverage:

* no-trade parity,
* simple long parity,
* simple short parity if supported,
* costs parity,
* slippage parity,
* stop/target parity,
* same-bar ambiguity parity,
* partial exit parity,
* EOD exit parity,
* cooldown parity,
* max holding bars parity,
* equity curve parity,
* trade summary parity,
* unsupported fast feature fail-closed or reference fallback behavior,
* bounded performance smoke,
* no generated benchmark artifacts committed.

### Artifact Policy

Commit only:

* source files,
* docs,
* tests,
* tiny deterministic fixtures if required.

Do not commit:

* benchmark logs,
* generated arrays,
* local grid results,
* fast-path outputs,
* local DBs,
* raw/canonical data,
* generated factor/label/signal stores,
* logs,
* caches,
* heavy artifacts.

Stage explicit files only. Never use `git add .` or `git add -A`.

### Done Criteria

* Fast path exists.
* Parity checker exists.
* Fast path is not treated as truth.
* Reference engine remains canonical truth.
* Parity tests pass for scoped features.
* Unsupported features fail closed or route to reference.
* Docs explain fast path usage restrictions.
* No benchmark artifacts are committed.
* Handoff exists and records validation results.
* Claude review passes.

### Handoff Requirements

Create:

```text
handoffs/ASV1-P19.md
runs/<run_id>/phases/ASV1-P19/handoff.md
```

Handoff must include:

* fast path scope,
* parity matrix,
* unsupported feature matrix,
* tests run and results,
* performance smoke result if run,
* confirmation that reference truth is unchanged,
* artifact policy confirmation,
* confirmation that no benchmark artifacts were committed,
* confirmation that no broker/live scope was introduced,
* known limitations,
* review focus.

### Review Requirements

Claude Opus 4.8 xhigh review required.

Claude Sonnet mechanical parity audit may be used.

Review must verify:

* reference truth is unchanged,
* parity coverage is adequate for scoped features,
* fast path is acceleration only,
* no separate PnL truth,
* fail-closed behavior,
* no fast-path grid use without parity,
* artifact policy,
* no overclaims,
* no broker/live scope,
* no test weakening.

### Auto-Merge Eligibility

Auto PR and auto merge allowed if:

* parity tests pass,
* required unit/integration tests pass,
* handoff validates,
* Claude verdict is `PASS` or `PASS_WITH_WARNINGS`,
* no benchmark artifacts or DBs are staged,
* no raw/heavy artifacts are staged,
* artifact policy passes,
* semantic done-check passes.

---

## ASV1-P20 — Strategy Grid Engine MVP

### Phase ID

`ASV1-P20`

### Phase Name

Strategy Grid Engine MVP

### Lane

YELLOW

### Dependencies

* `ASV1-P19`

### Purpose

Implement bounded local grid execution for factor parameters, strategy signals, execution costs, risk sizing, and position management parameters with controls against combinatorial explosion.

This phase creates the grid experiment foundation for systematic research while preserving the rule that grid results are evidence artifacts, not tradability claims or candidate approvals.

### Scope

Create or update:

* `src/alpha_system/experiments/grid.py`
* `src/alpha_system/experiments/runner.py`
* `src/alpha_system/experiments/limits.py`
* `src/alpha_system/experiments/leaderboard.py`
* `src/alpha_system/experiments/grid_outputs.py`
* `src/alpha_system/experiments/grid_config.py`
* `src/alpha_system/experiments/grid_manifest.py`
* `src/alpha_system/cli/grid.py`
* `docs/GRID_ENGINE.md`
* `docs/GRID_OVERFIT_POLICY.md`
* `configs/grids/examples/`
* tests for grid expansion, limits, deterministic ordering, output schemas, manifest generation, registry integration, artifact policy, and fast path parity gates.

CLI command introduced:

```bash
alpha grid run
```

Command purpose:

* run bounded local strategy/factor/execution/risk grid experiments.

Command inputs:

* grid config,
* strategy spec,
* management spec,
* portfolio spec,
* data version,
* factor versions,
* label versions where needed,
* execution config,
* engine selection,
* optional registry path,
* optional output directory.

Command outputs:

* local grid artifacts,
* summary files,
* registry entry,
* run manifest.

Artifacts:

* full grid raw outputs are local-only,
* curated summaries may be committed only if tiny and explicitly scoped,
* generated output under `artifacts/strategy_grids/` is local-only by default.

Validation checks:

* max combinations,
* required data/factor/label versions,
* strategy version presence,
* management config validation,
* portfolio config validation,
* cost config validation,
* parity gate for fast path,
* output schema validation,
* manifest required fields,
* registry entry.

Grid types:

* factor parameter grid,
* strategy signal grid,
* execution cost grid,
* risk sizing grid,
* position management grid.

Grid discipline:

1. Factor diagnostics first.
2. Simple signal grid.
3. Simple management baseline.
4. Survivor strategy management grid.
5. Finalist execution validation.

Grid output schemas:

* `leaderboard.csv`
* `grid_summary.md`
* `monthly_breakdown.csv`
* `cost_sensitivity.csv`
* `top_configs.yaml`
* `rejected_configs.csv`
* `run_manifest.json`

Grid engine must record rejected configurations and reasons.

### Non-Goals

* No distributed Ray execution.
* No cloud execution.
* No hyperparameter sweep service.
* No unlimited grids.
* No management survivor workflow yet; full survivor workflow is ASV1-P21.
* No candidate approval.
* No production/tradability claims.
* No broker/live trading.
* No paper trading.

### Expected Files / Directories

Expected source files:

* `src/alpha_system/experiments/grid.py`
* `src/alpha_system/experiments/runner.py`
* `src/alpha_system/experiments/limits.py`
* `src/alpha_system/experiments/leaderboard.py`
* `src/alpha_system/experiments/grid_outputs.py`
* `src/alpha_system/experiments/grid_config.py`
* `src/alpha_system/experiments/grid_manifest.py`
* `src/alpha_system/cli/grid.py`

Expected docs/configs:

* `docs/GRID_ENGINE.md`
* `docs/GRID_OVERFIT_POLICY.md`
* example configs under `configs/grids/examples/`

Expected tests:

* `tests/unit/test_grid_expansion_count.py`
* `tests/unit/test_grid_max_combination_rejection.py`
* `tests/unit/test_grid_deterministic_ordering.py`
* `tests/unit/test_grid_rejected_configs.py`
* `tests/unit/test_grid_rejected_reasons.py`
* `tests/unit/test_grid_leaderboard_schema.py`
* `tests/unit/test_grid_output_schemas.py`
* `tests/unit/test_grid_manifest_fields.py`
* `tests/unit/test_grid_requires_versions.py`
* `tests/integration/test_grid_registry_tempdb.py`
* `tests/integration/test_grid_fast_path_parity_gate.py`
* `tests/integration/test_grid_reference_fallback.py`
* `tests/integration/test_grid_cli_help.py`
* `tests/unit/test_grid_artifact_policy.py`
* `tests/unit/test_grid_no_tradability_claims.py`

### Forbidden Changes

* No full grid outputs committed.
* No temporary multiprocessing outputs committed.
* No generated `artifacts/strategy_grids/` outputs committed.
* No raw data committed.
* No canonical generated data committed.
* No materialized factor/label/signal stores committed.
* No full trade logs committed.
* No heavy artifacts committed.
* No local SQLite DB committed.
* No unbounded Cartesian products.
* No fast path without parity gate.
* No hidden rejected configs.
* No hidden failed runs.
* No automatic candidate approval.
* No broker/live trading scope.
* No paper trading scope.
* No alpha/profitability/tradability claims.
* No uncontrolled scope expansion.
* No test weakening or gaming.
* No `git add .`.
* No `git add -A`.

### Validation Commands

Ralph must run and record:

```bash
python -m pytest tests/unit tests/integration tests/parity
python -m alpha_system.cli grid run --help
git status --short
find artifacts/strategy_grids -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
```

If console script is available:

```bash
alpha grid run --help
```

If lint/type tools are configured:

```bash
python -m ruff check .
python -m mypy src
```

Required validation coverage:

* grid expansion count,
* max-combination rejection,
* deterministic ordering,
* rejected config output,
* rejected reason recording,
* leaderboard schema,
* required output schemas,
* manifest fields,
* required version references,
* registry recording,
* fast path parity gate,
* reference fallback,
* artifact path policy,
* no tradability claim language.

### Artifact Policy

Commit only:

* source files,
* docs,
* configs,
* tests,
* tiny fixture outputs if explicitly required.

Do not commit:

* full grid outputs,
* local grid artifact directories,
* temporary multiprocessing outputs,
* local DBs,
* raw/canonical data,
* generated factor/label/signal stores,
* full trade logs,
* logs,
* caches,
* heavy artifacts.

Stage explicit files only. Never use `git add .` or `git add -A`.

### Done Criteria

* `alpha grid run` help works.
* Bounded fixture grids run in tests.
* Max-combination/explosion controls are enforced.
* Required output schemas exist.
* Rejected configs and reasons are visible.
* Registry records grid runs in temp DB.
* Fast path requires parity.
* Reference fallback works for unsupported fast-path features.
* No full grid outputs are committed.
* Handoff exists and records validation results.
* Claude review passes.

### Handoff Requirements

Create:

```text
handoffs/ASV1-P20.md
runs/<run_id>/phases/ASV1-P20/handoff.md
```

Handoff must include:

* grid type coverage,
* grid discipline summary,
* explosion control summary,
* output schema summary,
* rejected config behavior,
* fast path gate behavior,
* registry integration summary,
* tests run and results,
* artifact output policy,
* confirmation that no full grid outputs were committed,
* confirmation that no broker/live scope was introduced,
* known limitations,
* review focus.

### Review Requirements

Claude Opus 4.8 xhigh review required.

Review must verify:

* bounded search discipline,
* grid discipline order,
* parity gate,
* rejected config visibility,
* reproducibility metadata,
* registry integration,
* no overfit/tradability claims,
* artifact policy,
* no broker/live scope,
* no test weakening.

### Auto-Merge Eligibility

Auto PR and auto merge allowed if:

* tests pass,
* CLI help works,
* handoff validates,
* Claude verdict is `PASS` or `PASS_WITH_WARNINGS`,
* no grid outputs or DBs are staged,
* no raw/heavy artifacts are staged,
* artifact policy passes,
* semantic done-check passes.

---

## ASV1-P21 — Management Grid Engine

### Phase ID

`ASV1-P21`

### Phase Name

Management Grid Engine

### Lane

YELLOW

### Dependencies

* `ASV1-P20`

### Purpose

Implement survivor-based management grid workflow that applies position management exploration only after factor diagnostics and simple strategy grids produce eligible candidates.

This phase completes bounded execution for:

```bash
alpha management grid
```

Management-grid results must remain review evidence, not approvals or tradability claims.

### Scope

Create or update:

* `src/alpha_system/experiments/management_grid.py`
* `src/alpha_system/experiments/survivors.py`
* `src/alpha_system/experiments/candidate_policy.py`
* `src/alpha_system/experiments/overfit_controls.py`
* `src/alpha_system/experiments/management_outputs.py`
* `src/alpha_system/cli/management.py`
* `docs/MANAGEMENT_GRID_WORKFLOW.md`
* `docs/SURVIVOR_POLICY.md`
* `configs/management/grid_examples/`
* tests for survivor gating, bounded management grids, output schemas, rejection reasons, overfit controls, registry integration, and CLI execution.

Workflow discipline:

1. Factor diagnostics first.
2. Simple signal grid.
3. Simple management baseline.
4. Survivor-only management grid.
5. Finalist execution validation.

Survivor records must include:

* candidate id,
* source run id,
* factor versions,
* label versions where applicable,
* strategy version,
* baseline management config,
* baseline portfolio config,
* source grid config hash,
* reason for survivor eligibility,
* warnings,
* review status,
* allowed management grid scope.

Management-grid outputs must include:

* baseline comparison,
* leaderboard,
* rejected configs,
* rejected reasons,
* monthly breakdown,
* cost sensitivity,
* run manifest,
* warnings,
* survivor eligibility summary.

Rules:

* management grid cannot run on arbitrary unvalidated ideas without explicit fail or warning,
* unbounded stop/target/partial combinations must be rejected,
* no automatic candidate approval,
* no promotion decision is made by grid engine,
* all results are review-only evidence.

### Non-Goals

* No automatic candidate approval.
* No promotion to approved.
* No live execution validation.
* No unlimited management search.
* No ML ensembling.
* No finalist event-driven engine.
* No broker/live trading.
* No paper trading.
* No tradability claims.

### Expected Files / Directories

Expected source files:

* `src/alpha_system/experiments/management_grid.py`
* `src/alpha_system/experiments/survivors.py`
* `src/alpha_system/experiments/candidate_policy.py`
* `src/alpha_system/experiments/overfit_controls.py`
* `src/alpha_system/experiments/management_outputs.py`
* `src/alpha_system/cli/management.py`

Expected docs/configs:

* `docs/MANAGEMENT_GRID_WORKFLOW.md`
* `docs/SURVIVOR_POLICY.md`
* config examples under `configs/management/grid_examples/`

Expected tests:

* `tests/unit/test_survivor_eligibility_gate.py`
* `tests/unit/test_survivor_record_schema.py`
* `tests/unit/test_management_grid_max_combinations.py`
* `tests/unit/test_management_grid_rejected_reasons.py`
* `tests/unit/test_management_grid_baseline_comparison.py`
* `tests/unit/test_management_grid_cost_sensitivity.py`
* `tests/unit/test_management_grid_monthly_breakdown.py`
* `tests/unit/test_management_grid_warnings.py`
* `tests/integration/test_management_grid_registry_tempdb.py`
* `tests/unit/test_management_grid_no_auto_approval.py`
* `tests/unit/test_management_grid_requires_review_status.py`
* `tests/integration/test_management_grid_cli_execution.py`
* `tests/unit/test_management_grid_artifact_policy.py`
* `tests/unit/test_management_grid_no_tradability_claims.py`

### Forbidden Changes

* No management grid outputs committed.
* No generated `artifacts/management_studies/` outputs committed.
* No full trade logs committed.
* No generated equity curves committed.
* No raw data committed.
* No canonical generated data committed.
* No materialized factor/label/signal stores committed.
* No heavy artifacts committed.
* No local SQLite DB committed.
* No management grid on arbitrary unvalidated ideas without explicit fail/warning.
* No unbounded stop/target/partial combinations.
* No automatic approval.
* No promotion decision by grid engine.
* No broker/live trading scope.
* No paper trading scope.
* No alpha/profitability/tradability claims.
* No uncontrolled scope expansion.
* No hidden failed runs.
* No hidden rejected configs.
* No test weakening or gaming.
* No `git add .`.
* No `git add -A`.

### Validation Commands

Ralph must run and record:

```bash
python -m pytest tests/unit tests/integration
python -m alpha_system.cli management grid --help
git status --short
find artifacts/management_studies -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
```

If console script is available:

```bash
alpha management grid --help
```

If lint/type tools are configured:

```bash
python -m ruff check .
python -m mypy src
```

Required validation coverage:

* survivor eligibility gate,
* survivor record schema,
* max-combination gate,
* rejected reason recording,
* baseline comparison,
* cost sensitivity,
* monthly breakdown,
* warnings,
* registry recording,
* no approval without promotion decision,
* review status requirement,
* artifact path policy,
* CLI behavior,
* no tradability claim language.

### Artifact Policy

Commit only:

* source files,
* docs,
* configs,
* tests,
* tiny fixture summaries if explicitly required.

Do not commit:

* full management grid outputs,
* generated management studies,
* local DBs,
* full trade logs,
* generated equity curves,
* raw/canonical data,
* generated factor/label/signal stores,
* logs,
* caches,
* heavy artifacts.

Stage explicit files only. Never use `git add .` or `git add -A`.

### Done Criteria

* `alpha management grid` supports bounded execution.
* Survivor gating is enforced.
* Survivor records include required fields.
* Outputs include required summaries.
* Rejected configurations and reasons are visible.
* No automatic approval occurs.
* Management overfit controls are documented and tested.
* Registry records management grid runs in temp DB.
* No full management grid outputs are committed.
* Handoff exists and records validation results.
* Claude review passes.

### Handoff Requirements

Create:

```text
handoffs/ASV1-P21.md
runs/<run_id>/phases/ASV1-P21/handoff.md
```

Handoff must include:

* survivor workflow summary,
* survivor record schema summary,
* gate behavior,
* grid output summary,
* rejected config behavior,
* overfit controls,
* registry integration summary,
* tests run and results,
* artifact policy confirmation,
* no auto-approval confirmation,
* confirmation that no management grid outputs were committed,
* confirmation that no broker/live scope was introduced,
* known limitations,
* review focus.

### Review Requirements

Claude Opus 4.8 xhigh review required.

Review must verify:

* survivor discipline,
* overfit controls,
* bounded search,
* rejected config visibility,
* no automatic approval,
* no promotion decision by grid,
* no overclaims,
* registry integration,
* artifact policy,
* no broker/live scope,
* no test weakening.

### Auto-Merge Eligibility

Auto PR and auto merge allowed if:

* tests pass,
* CLI help works,
* handoff validates,
* Claude verdict is `PASS` or `PASS_WITH_WARNINGS`,
* no management outputs or DBs are staged,
* no raw/heavy artifacts are staged,
* artifact policy passes,
* semantic done-check passes.

---

## ASV1-P22 — Experiment Registry Hardening

### Phase ID

`ASV1-P22`

### Phase Name

Experiment Registry Hardening

### Lane

YELLOW

### Dependencies

* `ASV1-P21`

### Purpose

Harden experiment registry integration across study, factor validation, label generation, strategy runs, backtest runs, grid runs, management grid runs, and future ML runs.

This phase ensures complete reproducibility metadata, artifact manifests, failed-run visibility, promotion decision traceability, registry audit support, and no hidden failed runs.

### Scope

Create or update:

* `src/alpha_system/experiments/run_records.py`
* `src/alpha_system/experiments/artifact_manifest.py`
* `src/alpha_system/experiments/reproducibility.py`
* `src/alpha_system/experiments/promotion.py`
* `src/alpha_system/experiments/audit.py`
* `src/alpha_system/experiments/failure_records.py`
* `src/alpha_system/experiments/version_refs.py`
* `docs/EXPERIMENT_REGISTRY.md`
* `docs/REPRODUCIBILITY_AUDIT.md`
* tests for registry records, failed runs, artifact manifests, promotion decisions, reproducibility audit, version references, and no committed DB files.

All required tables must be exercised:

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
* dirty tree indicator where available,
* code hash,
* config hash,
* data version,
* factor versions,
* label versions,
* engine version,
* parameters,
* artifact paths,
* decision status,
* warnings,
* failed-step visibility.

Artifact manifests must support:

* artifact id,
* run id,
* artifact type,
* relative path,
* hash,
* size if available,
* created timestamp,
* local-only status,
* commit-eligible status,
* warning if artifact path is not commit-safe.

Promotion decisions must require:

* candidate id,
* source run id,
* review status,
* reviewer identity or review artifact,
* decision status,
* rationale,
* artifact references,
* timestamp.

Registry audit must detect:

* missing code hash,
* missing config hash,
* missing git commit,
* missing data version,
* missing factor version,
* missing label version where required,
* missing artifact references,
* forbidden artifact paths,
* promotion decision without review,
* hidden failed run patterns where observable.

### Non-Goals

* No new research engine.
* No external experiment tracker.
* No MLflow server.
* No candidate approval without review.
* No generated production DB.
* No cloud registry.
* No broker/live trading.
* No alpha/tradability claims.

### Expected Files / Directories

Expected source files:

* `src/alpha_system/experiments/run_records.py`
* `src/alpha_system/experiments/artifact_manifest.py`
* `src/alpha_system/experiments/reproducibility.py`
* `src/alpha_system/experiments/promotion.py`
* `src/alpha_system/experiments/audit.py`
* `src/alpha_system/experiments/failure_records.py`
* `src/alpha_system/experiments/version_refs.py`

Expected docs:

* `docs/EXPERIMENT_REGISTRY.md`
* `docs/REPRODUCIBILITY_AUDIT.md`

Expected tests:

* `tests/unit/test_run_record_required_fields.py`
* `tests/unit/test_failed_run_recording.py`
* `tests/unit/test_failure_records_visible.py`
* `tests/unit/test_artifact_manifest_schema.py`
* `tests/unit/test_artifact_manifest_hash_size.py`
* `tests/unit/test_artifact_path_policy.py`
* `tests/unit/test_promotion_requires_review.py`
* `tests/unit/test_promotion_decision_schema.py`
* `tests/unit/test_version_refs.py`
* `tests/integration/test_registry_audit_missing_hashes.py`
* `tests/integration/test_registry_audit_missing_versions.py`
* `tests/integration/test_registry_audit_forbidden_artifacts.py`
* `tests/integration/test_registry_all_tables_exercised.py`
* `tests/integration/test_duplicate_run_behavior.py`
* `tests/integration/test_no_committed_sqlite.py`

### Forbidden Changes

* No local SQLite DB committed.
* No generated registry DB committed.
* No raw data committed.
* No canonical generated data committed.
* No materialized factor/label/signal stores committed.
* No grid/management/backtest outputs committed.
* No heavy artifacts committed.
* No artifact paths outside approved local directories without warnings.
* No hidden failed runs.
* No promotion without review status.
* No broker/live trading scope.
* No paper trading scope.
* No alpha/profitability/tradability claims.
* No uncontrolled scope expansion.
* No test weakening or gaming.
* No `git add .`.
* No `git add -A`.

### Validation Commands

Ralph must run and record:

```bash
python -m pytest tests/unit tests/integration
git status --short
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
find artifacts -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true
```

If lint/type tools are configured:

```bash
python -m ruff check .
python -m mypy src
```

Required validation coverage:

* run record required fields,
* failed run recording,
* failed run visibility,
* artifact manifest schema,
* artifact hash/size behavior,
* artifact path policy,
* promotion decision requires review,
* promotion decision schema,
* version reference behavior,
* registry audit detects missing hashes,
* registry audit detects missing data/factor/label versions,
* registry audit detects forbidden artifact paths,
* all required tables exercised,
* duplicate behavior deterministic,
* no committed SQLite DB.

### Artifact Policy

Commit only:

* source files,
* docs,
* tests,
* tiny fixtures if explicitly required.

Do not commit:

* local SQLite DBs,
* full manifests from local experiments,
* generated artifacts,
* raw/canonical data,
* materialized factor/label/signal stores,
* logs,
* caches,
* temp files,
* heavy artifacts.

Stage explicit files only. Never use `git add .` or `git add -A`.

### Done Criteria

* Registry audit exists.
* All run categories can record reproducibility metadata.
* Failed runs can be recorded and surfaced.
* Artifact manifests can be recorded and audited.
* Promotion decisions require review.
* Version references are structurally validated.
* Artifact path policy is tested.
* No DB file is committed.
* No generated artifacts are committed.
* Handoff exists and records validation results.
* Claude review passes.

### Handoff Requirements

Create:

```text
handoffs/ASV1-P22.md
runs/<run_id>/phases/ASV1-P22/handoff.md
```

Handoff must include:

* registry hardening summary,
* table coverage matrix,
* run record field coverage,
* artifact manifest summary,
* failed-run visibility summary,
* promotion decision traceability summary,
* reproducibility audit summary,
* tests run and results,
* artifact policy confirmation,
* confirmation that no local DB was committed,
* confirmation that no generated artifacts were committed,
* confirmation that no broker/live scope was introduced,
* known limitations,
* review focus.

### Review Requirements

Claude Opus 4.8 xhigh review required.

Review must verify:

* reproducibility completeness,
* failed-run visibility,
* artifact manifest correctness,
* promotion decision traceability,
* version reference handling,
* artifact path policy,
* no DB commits,
* no hidden failure patterns,
* no overclaims,
* no broker/live scope,
* no test weakening.

### Auto-Merge Eligibility

Auto PR and auto merge allowed if:

* tests pass,
* handoff validates,
* Claude verdict is `PASS` or `PASS_WITH_WARNINGS`,
* no DBs or generated artifacts are staged,
* no raw/heavy artifacts are staged,
* artifact policy passes,
* semantic done-check passes.

---

## ASV1-P23 — ML and Factor Combination MVP

### Phase ID

`ASV1-P23`

### Phase Name

ML and Factor Combination MVP

### Lane

YELLOW

### Dependencies

* `ASV1-P22`

### Purpose

Implement an ML/factor-combination MVP that consumes only versioned factor store inputs, supports model specs, train/validation split discipline, walk-forward readiness, purge/embargo readiness, score outputs, score-to-portfolio conversion contracts, and ML experiment registry recording.

This phase creates an ML research scaffold without production ML, live inference, model deployment, or tradability claims.

### Scope

Create or update:

* `src/alpha_system/experiments/ml.py`
* `src/alpha_system/experiments/feature_sets.py`
* `src/alpha_system/experiments/splits.py`
* `src/alpha_system/experiments/model_specs.py`
* `src/alpha_system/experiments/scoring.py`
* `src/alpha_system/experiments/ml_outputs.py`
* `src/alpha_system/experiments/ml_registry.py`
* `src/alpha_system/cli/ml.py`
* `docs/ML_LAYER.md`
* `docs/ML_LEAKAGE_POLICY.md`
* `configs/ml/examples/`
* tests for feature set validation, label alignment, split discipline, model specs, scoring schema, registry integration, leakage prevention, artifact policy, and CLI help.

CLI command introduced:

```bash
alpha ml run
```

Command purpose:

* run local MVP ML/factor-combination experiments.

Command inputs:

* `FeatureSetSpec`,
* `LabelSpec`,
* `ModelSpec`,
* split config,
* factor versions,
* label version,
* data version,
* optional universe/instrument selector,
* optional registry path,
* optional output directory.

Command outputs:

* local ML artifacts,
* score summary,
* registry entry,
* run manifest.

Artifacts:

* model artifacts are local-only unless tiny explicit fixtures,
* prediction/score outputs are local-only unless tiny explicit fixtures,
* summaries may be committed only if curated and small.

Validation checks:

* feature sets reference factor versions only,
* no raw ad hoc feature columns,
* labels are not included in features,
* train/validation split is valid,
* walk-forward split is valid,
* purge/embargo config is represented and tested,
* label availability is respected,
* run manifest exists,
* registry entry exists.

ML contracts:

* `FeatureSetSpec`,
* `LabelSpec`,
* `ModelSpec`,
* train/validation split,
* walk-forward split,
* purge/embargo,
* score output schema,
* score-to-portfolio conversion,
* ML experiment registry.

Support design for:

* linear model,
* ridge/lasso,
* LightGBM/XGBoost later,
* random forest later,
* meta-labeling,
* ensemble,
* regime-conditioned model,
* IC-weighted factor score,
* orthogonalized factor score.

MVP may implement a deterministic simple linear/ridge-style baseline or config-validation scaffold using approved lightweight dependencies only. It must not require LightGBM, XGBoost, Ray, MLflow server, GPUs, cloud, or model-serving infrastructure.

### Non-Goals

* No production ML.
* No GPU.
* No required LightGBM/XGBoost dependency.
* No required random forest dependency unless already lightweight and approved.
* No model deployment.
* No live inference.
* No MLflow server.
* No model registry server.
* No raw ad hoc feature experiments.
* No broker/live trading.
* No paper trading.
* No alpha/profitability/tradability claims.

### Expected Files / Directories

Expected source files:

* `src/alpha_system/experiments/ml.py`
* `src/alpha_system/experiments/feature_sets.py`
* `src/alpha_system/experiments/splits.py`
* `src/alpha_system/experiments/model_specs.py`
* `src/alpha_system/experiments/scoring.py`
* `src/alpha_system/experiments/ml_outputs.py`
* `src/alpha_system/experiments/ml_registry.py`
* `src/alpha_system/cli/ml.py`

Expected docs/configs:

* `docs/ML_LAYER.md`
* `docs/ML_LEAKAGE_POLICY.md`
* config examples under `configs/ml/examples/`

Expected tests:

* `tests/unit/test_feature_set_requires_factor_versions.py`
* `tests/unit/test_feature_set_schema.py`
* `tests/no_lookahead/test_ml_raw_column_rejection.py`
* `tests/no_lookahead/test_ml_label_leakage_rejection.py`
* `tests/no_lookahead/test_ml_label_availability.py`
* `tests/unit/test_train_validation_split.py`
* `tests/unit/test_walk_forward_split.py`
* `tests/unit/test_purge_embargo_gap.py`
* `tests/unit/test_model_spec_registration.py`
* `tests/unit/test_linear_model_spec.py`
* `tests/unit/test_future_model_type_placeholders.py`
* `tests/integration/test_ml_run_registry_tempdb.py`
* `tests/unit/test_ml_score_output_schema.py`
* `tests/unit/test_score_to_portfolio_contract.py`
* `tests/unit/test_ml_artifact_policy.py`
* `tests/unit/test_ml_no_tradability_claims.py`
* `tests/integration/test_ml_cli_help.py`

### Forbidden Changes

* No trained model binaries committed.
* No generated prediction datasets committed.
* No generated score outputs committed except tiny explicit fixtures.
* No local ML experiment directories committed.
* No raw data committed.
* No canonical generated data committed.
* No materialized factor/label/signal stores committed.
* No heavy artifacts committed.
* No local SQLite DB committed.
* No raw ad hoc feature columns.
* No labels as features.
* No future validation labels used in training.
* No MLflow server requirement.
* No Ray requirement.
* No cloud dependency.
* No model deployment.
* No live inference.
* No broker/live trading scope.
* No paper trading scope.
* No alpha/profitability/tradability claims.
* No uncontrolled scope expansion.
* No hidden failed runs.
* No test weakening or gaming.
* No `git add .`.
* No `git add -A`.

### Validation Commands

Ralph must run and record:

```bash
python -m pytest tests/unit tests/integration tests/no_lookahead
python -m alpha_system.cli ml run --help
git status --short
find artifacts/ml_experiments -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
find . -type f \( -name "*.pkl" -o -name "*.joblib" -o -name "*.pickle" -o -name "*.onnx" \) -print
```

If console script is available:

```bash
alpha ml run --help
```

If lint/type tools are configured:

```bash
python -m ruff check .
python -m mypy src
```

Required validation coverage:

* FeatureSetSpec requires factor versions,
* raw columns rejected,
* labels rejected as features,
* label availability respected,
* train/validation split,
* walk-forward split,
* purge/embargo gap,
* model spec registration,
* linear model spec or MVP model spec behavior,
* future model type placeholders are design-only,
* ML run registry,
* score output schema,
* score-to-portfolio conversion contract,
* artifact policy,
* no tradability claim language,
* CLI help.

### Artifact Policy

Commit only:

* source files,
* docs,
* configs,
* tests,
* tiny deterministic fixtures if explicitly required.

Do not commit:

* trained model binaries,
* large predictions,
* score datasets,
* ML experiment directories,
* local DBs,
* raw/canonical data,
* generated factor/label/signal stores,
* logs,
* caches,
* heavy artifacts.

Stage explicit files only. Never use `git add .` or `git add -A`.

### Done Criteria

* `alpha ml run` help works.
* Feature inputs are versioned factors only.
* Raw ad hoc columns are rejected.
* Label leakage is rejected.
* Label availability is respected.
* Split contracts exist and are tested.
* Walk-forward and purge/embargo readiness exist and are tested.
* ML run registry integration works in temp DB.
* Score output schema exists.
* Score-to-portfolio conversion contract exists.
* No model artifacts are committed.
* Docs explain ML limitations and no-claim policy.
* Handoff exists and records validation results.
* Claude review passes.

### Handoff Requirements

Create:

```text
handoffs/ASV1-P23.md
runs/<run_id>/phases/ASV1-P23/handoff.md
```

Handoff must include:

* ML contract summary,
* FeatureSetSpec summary,
* leakage controls,
* split behavior,
* model spec behavior,
* score output schema,
* registry integration summary,
* tests run and results,
* deferred model types,
* artifact policy confirmation,
* confirmation that no model/prediction artifacts were committed,
* confirmation that no broker/live scope was introduced,
* known limitations,
* review focus.

### Review Requirements

Claude Opus 4.8 xhigh review required.

Review must verify:

* feature-store discipline,
* no label leakage,
* no raw feature columns,
* split discipline,
* purge/embargo readiness,
* model artifact policy,
* no ML server dependency,
* no live inference/deployment scope,
* no overclaims,
* no broker/live scope,
* no test weakening.

### Auto-Merge Eligibility

Auto PR and auto merge allowed if:

* tests pass,
* CLI help works,
* handoff validates,
* Claude verdict is `PASS` or `PASS_WITH_WARNINGS`,
* no model artifacts, prediction outputs, or DBs are staged,
* no raw/heavy artifacts are staged,
* artifact policy passes,
* semantic done-check passes.

## ASV1-P24 — Multi-Symbol Universe Support

### Phase ID

`ASV1-P24`

### Phase Name

Multi-Symbol Universe Support

### Lane

YELLOW

### Dependencies

* `ASV1-P23`

### Purpose

Implement universe configuration and multi-symbol readiness for data, factors, labels, signals, portfolio constraints, and experiment runners while preserving the 1-minute-session-first architecture.

This phase prepares `alpha_system` for future multi-asset research without requiring real multi-symbol datasets, live universe updates, broker account state, or production portfolio optimization.

### Scope

Create or update:

* `src/alpha_system/data/universe.py`
* `src/alpha_system/core/instruments.py`
* `src/alpha_system/core/instrument_master.py`
* `src/alpha_system/experiments/universe_runner.py`
* `src/alpha_system/portfolio/universe_constraints.py`
* `configs/universes/examples/`
* `docs/UNIVERSES_AND_MULTI_ASSET.md`
* `docs/INSTRUMENT_MASTER.md`
* tests for universe selection, instrument metadata, multi-symbol session alignment, per-symbol data quality, portfolio constraints, registry metadata, and local artifact policy.

Universe configs must support:

* instrument ids,
* symbols,
* asset classes,
* exchanges,
* currencies,
* timezones,
* active date ranges,
* data versions,
* inclusion rules,
* exclusion rules,
* future sector constraints,
* future asset constraints.

Instrument master must preserve:

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

Multi-symbol readiness must include:

* independent session calendars per instrument,
* timezone-aware session alignment,
* active-date filtering,
* missing-data flags per instrument,
* universe/config hash recording,
* portfolio max gross exposure across symbols,
* portfolio max net exposure across symbols,
* future sector/asset exposure representation,
* future correlation-aware allocation contract,
* deterministic tiny multi-symbol fixture support.

This phase must explicitly avoid assuming that all instruments share the same timezone, session calendar, currency, or multiplier.

### Non-Goals

* No full cross-asset analytics.
* No FX conversion engine beyond metadata readiness.
* No live universe updates.
* No broker universe sync.
* No cloud data source.
* No production multi-asset optimizer.
* No real multi-symbol market dataset.
* No live trading.
* No paper trading.
* No alpha/profitability/tradability claims.
* No L2 data processing.

### Expected Files / Directories

Expected source files:

* `src/alpha_system/data/universe.py`
* `src/alpha_system/core/instruments.py`
* `src/alpha_system/core/instrument_master.py`
* `src/alpha_system/experiments/universe_runner.py`
* `src/alpha_system/portfolio/universe_constraints.py`

Expected docs/configs:

* `docs/UNIVERSES_AND_MULTI_ASSET.md`
* `docs/INSTRUMENT_MASTER.md`
* example universe configs under `configs/universes/examples/`

Expected tests:

* `tests/unit/test_universe_config_validation.py`
* `tests/unit/test_instrument_metadata_required_fields.py`
* `tests/unit/test_instrument_master_active_dates.py`
* `tests/unit/test_universe_active_date_filtering.py`
* `tests/unit/test_multi_symbol_session_alignment.py`
* `tests/unit/test_multi_symbol_timezone_handling.py`
* `tests/unit/test_per_symbol_missing_data_flags.py`
* `tests/unit/test_multi_symbol_portfolio_limits.py`
* `tests/unit/test_future_sector_asset_constraints.py`
* `tests/unit/test_future_correlation_aware_allocation_contract.py`
* `tests/integration/test_universe_registry_hash.py`
* `tests/integration/test_universe_runner_fixture.py`
* `tests/unit/test_universe_artifact_policy.py`

### Forbidden Changes

* No real multi-symbol datasets committed.
* No raw data committed.
* No canonical generated data committed.
* No generated universe outputs committed.
* No materialized factor/label/signal stores committed.
* No full trade logs committed.
* No heavy artifacts committed.
* No local SQLite DB committed.
* No assumption that all instruments share one timezone.
* No assumption that all instruments share one calendar.
* No ignoring currency, multiplier, tick size, or lot size metadata.
* No broker universe sync.
* No live trading scope.
* No paper trading scope.
* No alpha/profitability/tradability claims.
* No production multi-asset portfolio claims.
* No uncontrolled scope expansion.
* No hidden failed runs.
* No test weakening or gaming.
* No `git add .`.
* No `git add -A`.

### Validation Commands

Ralph must run and record:

```bash
python -m pytest tests/unit tests/integration tests/no_lookahead
git status --short
find data -type f ! -name README.md ! -name ".gitkeep" -print
find artifacts -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
```

If lint/type tools are configured:

```bash
python -m ruff check .
python -m mypy src
```

Required validation coverage:

* universe config validation,
* instrument master required fields,
* active date filtering,
* multi-symbol session alignment,
* multi-symbol timezone handling,
* per-symbol missing data flags,
* multi-symbol gross/net constraints,
* future sector/asset constraint representation,
* future correlation-aware allocation contract,
* universe/config hash registry recording,
* deterministic tiny universe runner fixture,
* no real multi-symbol data committed.

### Artifact Policy

Commit only:

* source files,
* docs,
* configs,
* tests,
* tiny deterministic fixtures if explicitly required.

Do not commit:

* real multi-symbol datasets,
* generated universe outputs,
* local DBs,
* generated artifacts,
* raw/canonical data,
* generated factor/label/signal stores,
* logs,
* caches,
* heavy artifacts.

Stage explicit files only. Never use `git add .` or `git add -A`.

### Done Criteria

* UniverseSpec or equivalent exists.
* Instrument master support exists.
* Instrument metadata supports multi-asset readiness.
* Multi-symbol fixture tests pass.
* Portfolio and experiment layers can represent universe inputs.
* Timezone/session differences are represented and tested.
* Universe/config hash can be recorded in temp registry tests.
* Docs explain multi-asset readiness and limitations.
* No real multi-symbol datasets are committed.
* Handoff exists and records validation results.
* Claude review passes.

### Handoff Requirements

Create:

```text
handoffs/ASV1-P24.md
runs/<run_id>/phases/ASV1-P24/handoff.md
```

Handoff must include:

* universe support summary,
* instrument master field coverage,
* multi-symbol session/timezone summary,
* portfolio constraint summary,
* registry hash behavior,
* tests run and results,
* artifact policy confirmation,
* confirmation that no real multi-symbol data was committed,
* confirmation that no broker/live scope was introduced,
* known limitations,
* review focus.

### Review Requirements

Claude Opus 4.8 xhigh review required.

Review must verify:

* multi-asset readiness,
* instrument metadata completeness,
* no single-symbol hardcoding in core contracts,
* timezone/currency/multiplier discipline,
* artifact policy,
* no broker/live scope,
* no overclaims,
* no test weakening.

### Auto-Merge Eligibility

Auto PR and auto merge allowed if:

* tests pass,
* handoff validates,
* Claude verdict is `PASS` or `PASS_WITH_WARNINGS`,
* no real data or generated artifacts are staged,
* no DB/heavy artifacts are staged,
* artifact policy passes,
* semantic done-check passes.

---

## ASV1-P25 — L2 Readiness Schema and Design

### Phase ID

`ASV1-P25`

### Phase Name

L2 Readiness Schema and Design

### Lane

YELLOW

### Dependencies

* `ASV1-P24`

### Purpose

Create design-only future Level-2 readiness schemas and documentation for L2 snapshots, event/delta tables, book levels, timing fields, quality flags, and future execution-sensitive research.

This phase must keep Level-2 work as schema/design readiness only. It must not implement full L2 replay, passive fill simulation, queue-position modeling, live market data ingestion, or broker execution.

### Scope

Create or update:

* `src/alpha_system/l2/schemas.py`
* `src/alpha_system/l2/design.py`
* `src/alpha_system/l2/timestamps.py`
* `src/alpha_system/l2/validation.py`
* `docs/L2_READINESS.md`
* `docs/FUTURE_L2_REPLAY.md`
* `docs/L2_SCOPE_BOUNDARIES.md`
* `configs/data/l2_examples/`
* tests for required L2 schema fields, timestamp semantics, enum validation, quality flags, and design-only scope.

L2 snapshot schema must include:

* instrument id,
* session id,
* `event_ts`,
* `receive_ts`,
* `available_ts`,
* book level,
* side,
* price,
* size,
* order count if available,
* data version,
* quality flags.

L2 event/delta schema must include:

* instrument id,
* session id,
* `event_ts`,
* `receive_ts`,
* `available_ts`,
* sequence id if available,
* action/update type,
* book level if applicable,
* side,
* price,
* size,
* order count if available,
* data version,
* quality flags.

Design docs must discuss:

* future book reconstruction,
* future queue position needs,
* future latency models,
* future passive fills,
* snapshot/delta consistency,
* event ordering,
* receive timestamp vs event timestamp vs available timestamp,
* no-lookahead for L2-derived features,
* why L2 replay is out of scope in this campaign,
* why live market data and broker execution are out of scope.

Timestamp semantics must distinguish:

* `event_ts`: exchange/source event timestamp if available,
* `receive_ts`: local or feed receive timestamp if available,
* `available_ts`: earliest time research system may use the information,
* session assignment timestamp behavior,
* ordering and tie-breaking expectations.

### Non-Goals

* No L2 replay engine.
* No L3 order reconstruction.
* No passive fill simulation.
* No queue-position model.
* No live market data feed.
* No broker/live execution.
* No paper trading.
* No real L2 dataset.
* No executable L2 strategy validation.
* No production execution claims.
* No alpha/profitability/tradability claims.

### Expected Files / Directories

Expected source files:

* `src/alpha_system/l2/schemas.py`
* `src/alpha_system/l2/design.py`
* `src/alpha_system/l2/timestamps.py`
* `src/alpha_system/l2/validation.py`

Expected docs/configs:

* `docs/L2_READINESS.md`
* `docs/FUTURE_L2_REPLAY.md`
* `docs/L2_SCOPE_BOUNDARIES.md`
* synthetic config examples under `configs/data/l2_examples/`

Expected tests:

* `tests/unit/test_l2_snapshot_required_fields.py`
* `tests/unit/test_l2_delta_required_fields.py`
* `tests/no_lookahead/test_l2_timestamp_ordering.py`
* `tests/unit/test_l2_available_ts_required.py`
* `tests/unit/test_l2_receive_ts_semantics.py`
* `tests/unit/test_l2_side_enum.py`
* `tests/unit/test_l2_update_action_enum.py`
* `tests/unit/test_l2_book_level_validation.py`
* `tests/unit/test_l2_data_version_required.py`
* `tests/unit/test_l2_quality_flags_required.py`
* `tests/unit/test_l2_snapshot_delta_consistency_contract.py`
* `tests/unit/test_l2_design_only_scope.py`
* `tests/unit/test_l2_artifact_policy.py`

### Forbidden Changes

* No L2 data committed.
* No real order book data committed.
* No replay engine implementation.
* No L3 order reconstruction.
* No passive fill simulation.
* No queue-position model implementation.
* No live market data connection.
* No broker/live trading scope.
* No paper trading scope.
* No executable L2 strategy validation claims.
* No heavy artifacts committed.
* No local SQLite DB committed.
* No alpha/profitability/tradability claims.
* No production execution claims.
* No uncontrolled scope expansion.
* No hidden failed runs.
* No test weakening or gaming.
* No `git add .`.
* No `git add -A`.

### Validation Commands

Ralph must run and record:

```bash
python -m pytest tests/unit tests/no_lookahead
git status --short
find data -path "*l2*" -type f -print || true
find artifacts -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
```

If lint/type tools are configured:

```bash
python -m ruff check .
python -m mypy src
```

Required validation coverage:

* snapshot required fields,
* delta/event required fields,
* event/receive/available timestamp ordering,
* available timestamp presence,
* receive timestamp semantics,
* side enum,
* update action enum,
* book level validation,
* data version requirement,
* quality flag requirement,
* snapshot/delta consistency contract,
* design-only scope.

### Artifact Policy

Commit only:

* source schema/design files,
* docs,
* configs,
* tests,
* tiny synthetic examples if required.

Do not commit:

* real L2 data,
* order book datasets,
* replay outputs,
* local DBs,
* generated artifacts,
* logs,
* caches,
* heavy artifacts.

Stage explicit files only. Never use `git add .` or `git add -A`.

### Done Criteria

* L2 readiness schemas exist.
* L2 timestamp semantics are explicit.
* Snapshot and event/delta schema fields are tested.
* Docs explicitly state design-only scope.
* Future replay constraints are documented.
* No replay/live/broker scope exists.
* No real L2 data is committed.
* Handoff exists and records validation results.
* Claude review passes.

### Handoff Requirements

Create:

```text
handoffs/ASV1-P25.md
runs/<run_id>/phases/ASV1-P25/handoff.md
```

Handoff must include:

* L2 schema coverage,
* timestamp semantics summary,
* snapshot/delta contract summary,
* design-only confirmation,
* tests run and results,
* deferred future work,
* artifact policy confirmation,
* confirmation that no L2 data was committed,
* confirmation that no replay/live/broker scope was introduced,
* known limitations,
* review focus.

### Review Requirements

Claude Opus 4.8 xhigh review required.

Review must verify:

* L2 schema completeness,
* event/receive/available timestamp semantics,
* scope control,
* no replay implementation,
* no passive-fill/queue-position implementation,
* no live data feed,
* no broker/live scope,
* artifact policy,
* no execution claims,
* no test weakening.

### Auto-Merge Eligibility

Auto PR and auto merge allowed if:

* tests pass,
* handoff validates,
* Claude verdict is `PASS` or `PASS_WITH_WARNINGS`,
* no L2 data or replay artifacts are staged,
* no DB/heavy artifacts are staged,
* artifact policy passes,
* semantic done-check passes.

---

## ASV1-P26 — L2-Derived Feature Pipeline Skeleton

### Phase ID

`ASV1-P26`

### Phase Name

L2-Derived Feature Pipeline Skeleton

### Lane

YELLOW

### Dependencies

* `ASV1-P25`

### Purpose

Create a fixture-only skeleton for future L2-derived feature computation while avoiding full L2 replay, passive fill modeling, live ingestion, broker execution, or execution simulation.

This phase prepares the platform for future microstructure features but keeps outputs synthetic, test-only, and design-scope.

### Scope

Create or update:

* `src/alpha_system/l2/features.py`
* `src/alpha_system/l2/feature_specs.py`
* `src/alpha_system/l2/quality.py`
* `src/alpha_system/l2/fixtures.py`
* `src/alpha_system/l2/feature_validation.py`
* `docs/L2_DERIVED_FEATURES.md`
* `docs/L2_FEATURE_SCOPE_POLICY.md`
* `configs/factors/microstructure/l2_feature_examples.yaml`
* tests for fixture-level L2-derived feature schema, no-lookahead timing, quality flags, missing levels, and design-only scope.

Future feature categories may include:

* spread from top of book,
* imbalance by level,
* depth by side,
* order count by level,
* microprice,
* quote update intensity,
* liquidity regime tags,
* event-rate features,
* future order-flow features.

Skeleton must enforce:

* synthetic fixture-only tests,
* `available_ts` propagation,
* quality flag propagation,
* missing level handling,
* no-lookahead timing,
* no label leakage,
* no factor store materialization by default,
* design-only scope.

Feature outputs must be compatible with the broader FactorSpec/Factor Value Schema architecture, but this phase must not create a real L2 factor store or compute production-ready L2 factors.

### Non-Goals

* No production L2 processing.
* No large L2 data.
* No real L2 data ingestion.
* No L2 replay engine.
* No passive fill model.
* No queue-position model.
* No live market data connection.
* No materialized L2 factor store by default.
* No executable L2 strategy validation.
* No broker/live trading.
* No paper trading.
* No alpha/profitability/tradability claims.

### Expected Files / Directories

Expected source files:

* `src/alpha_system/l2/features.py`
* `src/alpha_system/l2/feature_specs.py`
* `src/alpha_system/l2/quality.py`
* `src/alpha_system/l2/fixtures.py`
* `src/alpha_system/l2/feature_validation.py`

Expected docs/configs:

* `docs/L2_DERIVED_FEATURES.md`
* `docs/L2_FEATURE_SCOPE_POLICY.md`
* `configs/factors/microstructure/l2_feature_examples.yaml`

Expected tests:

* `tests/unit/test_l2_feature_spec_schema.py`
* `tests/unit/test_l2_top_of_book_spread.py`
* `tests/unit/test_l2_depth_imbalance.py`
* `tests/unit/test_l2_microprice.py`
* `tests/unit/test_l2_event_rate_feature_contract.py`
* `tests/no_lookahead/test_l2_feature_available_ts.py`
* `tests/no_lookahead/test_l2_feature_no_label_leakage.py`
* `tests/unit/test_l2_quality_flag_propagation.py`
* `tests/unit/test_l2_missing_level_handling.py`
* `tests/unit/test_l2_feature_design_only_scope.py`
* `tests/unit/test_l2_feature_no_materialization_by_default.py`
* `tests/unit/test_l2_feature_artifact_policy.py`

### Forbidden Changes

* No real L2 data committed.
* No generated L2 feature store committed.
* No materialized L2 factor values committed.
* No L2 replay execution.
* No passive fill simulation.
* No queue-position model.
* No live market data feed.
* No heavy artifacts committed.
* No local SQLite DB committed.
* No broker/live trading scope.
* No paper trading scope.
* No alpha/profitability/tradability claims.
* No executable L2 validation claims.
* No production microstructure feature claims.
* No uncontrolled scope expansion.
* No hidden failed runs.
* No test weakening or gaming.
* No `git add .`.
* No `git add -A`.

### Validation Commands

Ralph must run and record:

```bash
python -m pytest tests/unit tests/no_lookahead
git status --short
find data -path "*l2*" -type f -print || true
find data/factors -type f ! -name README.md ! -name ".gitkeep" -print
find artifacts -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
```

If lint/type tools are configured:

```bash
python -m ruff check .
python -m mypy src
```

Required validation coverage:

* L2 feature spec schema,
* top-of-book spread fixture,
* depth imbalance fixture,
* microprice fixture if implemented,
* event-rate feature contract,
* available timestamp propagation,
* no label leakage,
* quality flag propagation,
* missing level handling,
* no materialization by default,
* design-only scope,
* no generated L2 data or feature store committed.

### Artifact Policy

Commit only:

* source files,
* docs,
* configs,
* tests,
* tiny synthetic fixtures if explicitly needed.

Do not commit:

* real L2 datasets,
* generated feature stores,
* materialized L2 factors,
* replay outputs,
* local DBs,
* logs,
* caches,
* heavy artifacts.

Stage explicit files only. Never use `git add .` or `git add -A`.

### Done Criteria

* L2-derived feature skeleton exists.
* L2 feature specs are represented.
* Synthetic fixture tests pass.
* `available_ts` propagation is tested.
* Quality flag propagation is tested.
* Missing level handling is tested.
* No L2 feature materialization occurs by default.
* Docs clearly mark future-readiness scope.
* No L2 replay/live/broker scope is added.
* No real L2 data is committed.
* Handoff exists and records validation results.
* Claude review passes.

### Handoff Requirements

Create:

```text
handoffs/ASV1-P26.md
runs/<run_id>/phases/ASV1-P26/handoff.md
```

Handoff must include:

* feature skeleton summary,
* L2 feature spec summary,
* synthetic fixture behavior,
* no-lookahead timing summary,
* quality flag behavior,
* materialization policy,
* tests run and results,
* design-only limitations,
* artifact policy confirmation,
* confirmation that no real L2 data or L2 feature store was committed,
* confirmation that no replay/live/broker scope was introduced,
* known limitations,
* review focus.

### Review Requirements

Claude Opus 4.8 xhigh review required.

Review must verify:

* scope control,
* `available_ts` semantics,
* quality flag behavior,
* no label leakage,
* no materialization by default,
* no replay/passive-fill/queue-position scope,
* artifact policy,
* no execution claims,
* no broker/live scope,
* no overclaims,
* no test weakening.

### Auto-Merge Eligibility

Auto PR and auto merge allowed if:

* tests pass,
* handoff validates,
* Claude verdict is `PASS` or `PASS_WITH_WARNINGS`,
* no L2 data, feature stores, or DBs are staged,
* no raw/heavy artifacts are staged,
* artifact policy passes,
* semantic done-check passes.

---

## ASV1-P27 — Review Bundles, Source Maps, and Audit Reports

### Phase ID

`ASV1-P27`

### Phase Name

Review Bundles, Source Maps, and Audit Reports

### Lane

YELLOW

### Dependencies

* `ASV1-P26`

### Purpose

Implement review bundle, source map, and audit report generation so human researchers and AI Agents can inspect evidence, source dependencies, run manifests, registry entries, artifacts, warnings, failures, and risks.

This phase creates the review artifact layer needed for disciplined human/agent research governance. Review bundles must make evidence more inspectable; they must not approve candidates or claim tradability.

### Scope

Create or update:

* `src/alpha_system/reports/review_bundle.py`
* `src/alpha_system/reports/source_map.py`
* `src/alpha_system/reports/audit_report.py`
* `src/alpha_system/reports/release_report.py`
* `src/alpha_system/reports/bundle_validation.py`
* `src/alpha_system/reports/claim_checks.py`
* `src/alpha_system/cli/report.py`
* `docs/REVIEW_BUNDLES.md`
* `docs/SOURCE_MAPS.md`
* `docs/AUDIT_REPORTS.md`
* `configs/reports/review_bundle.yaml`
* tests for bundle contents, source maps, artifact policy, missing artifact visibility, failed-run visibility, prohibited claim language, registry integration, and CLI help.

CLI command introduced:

```bash
alpha report build
```

Command purpose:

* build local Markdown/CSV/static HTML report bundle for study, strategy grid, ML run, management study, execution validation, or release validation.

Command inputs:

* run id,
* registry path,
* artifact manifest,
* report config,
* optional output directory,
* optional source root.

Command outputs:

* local review bundle directory,
* small summary,
* source map,
* audit report,
* validation warnings.

Artifacts:

* full bundle is local-only,
* curated summary may be committed only if explicitly allowed and tiny,
* generated bundle directories under `artifacts/review_bundles/` are local-only by default.

Validation checks:

* run manifest exists,
* source map exists,
* required versions are present,
* config hashes are present,
* code hashes are present,
* artifact manifest is present,
* missing artifacts are surfaced,
* failed runs are surfaced,
* prohibited claims are absent,
* local-only outputs are not committed.

Review bundles must include:

* run manifest,
* source map,
* config hashes,
* code hashes,
* data/factor/label versions,
* engine version,
* registry records,
* diagnostics summary,
* backtest summary when applicable,
* cost sensitivity when applicable,
* monthly breakdown when applicable,
* rejected configs when applicable,
* warnings,
* failed-step visibility,
* promotion decision status,
* no-lookahead validation status,
* artifact manifest,
* known limitations,
* review status.

Source maps must include:

* relevant source files,
* relevant config files,
* relevant test files where discoverable,
* run manifest path,
* registry record reference,
* artifact references.

### Non-Goals

* No web server.
* No external dashboard.
* No approval automation.
* No full bundle commit.
* No candidate promotion.
* No production release claim.
* No alpha/profitability/tradability claim.
* No broker/live trading.
* No paper trading.

### Expected Files / Directories

Expected source files:

* `src/alpha_system/reports/review_bundle.py`
* `src/alpha_system/reports/source_map.py`
* `src/alpha_system/reports/audit_report.py`
* `src/alpha_system/reports/release_report.py`
* `src/alpha_system/reports/bundle_validation.py`
* `src/alpha_system/reports/claim_checks.py`
* `src/alpha_system/cli/report.py`

Expected docs/configs:

* `docs/REVIEW_BUNDLES.md`
* `docs/SOURCE_MAPS.md`
* `docs/AUDIT_REPORTS.md`
* `configs/reports/review_bundle.yaml`

Expected tests:

* `tests/unit/test_source_map_contents.py`
* `tests/unit/test_source_map_includes_configs.py`
* `tests/unit/test_review_bundle_required_files.py`
* `tests/unit/test_review_bundle_required_versions.py`
* `tests/unit/test_review_bundle_missing_artifact_warning.py`
* `tests/unit/test_review_bundle_failed_run_visibility.py`
* `tests/unit/test_review_bundle_rejected_configs_visibility.py`
* `tests/unit/test_review_bundle_promotion_status.py`
* `tests/unit/test_review_bundle_prohibited_claims.py`
* `tests/unit/test_review_bundle_summary_schema.py`
* `tests/unit/test_review_bundle_artifact_policy.py`
* `tests/integration/test_report_build_cli_help.py`
* `tests/integration/test_review_bundle_fixture.py`
* `tests/integration/test_review_bundle_registry_tempdb.py`

### Forbidden Changes

* No full review bundles committed.
* No generated `artifacts/review_bundles/` outputs committed.
* No generated heavy artifacts committed.
* No raw data committed.
* No canonical generated data committed.
* No materialized factor/label/signal stores committed.
* No full grid/trade/model outputs committed.
* No local SQLite DB committed.
* No hidden missing artifacts.
* No hidden failed runs.
* No hidden rejected configs.
* No automatic candidate approval.
* No alpha/profitability/tradability claims.
* No production-ready claims.
* No broker/live trading scope.
* No paper trading scope.
* No web server requirement.
* No uncontrolled scope expansion.
* No test weakening or gaming.
* No `git add .`.
* No `git add -A`.

### Validation Commands

Ralph must run and record:

```bash
python -m pytest tests/unit tests/integration
python -m alpha_system.cli report build --help
git status --short
find artifacts/review_bundles -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
```

If console script is available:

```bash
alpha report build --help
```

If lint/type tools are configured:

```bash
python -m ruff check .
python -m mypy src
```

Required validation coverage:

* source map includes relevant source files,
* source map includes relevant config files,
* review bundle includes required manifest files,
* review bundle includes required versions,
* missing artifact warning,
* failed run visibility,
* rejected config visibility,
* promotion decision status,
* prohibited claim rejection,
* small summary output schema,
* artifact path policy,
* registry temp DB integration,
* CLI help.

### Artifact Policy

Commit only:

* source files,
* docs,
* configs,
* tests,
* tiny fixture report outputs if explicitly required.

Do not commit:

* full review bundles,
* generated bundle directories,
* large artifacts,
* local DBs,
* raw/canonical data,
* generated factor/label/signal stores,
* full grid/trade/model outputs,
* logs,
* caches,
* heavy artifacts.

Stage explicit files only. Never use `git add .` or `git add -A`.

### Done Criteria

* `alpha report build` help works.
* Review bundle builder exists.
* Source map builder exists.
* Audit report builder exists.
* Required metadata is included.
* Failed runs are visible.
* Missing artifacts are visible.
* Rejected configs are visible where applicable.
* Prohibited claim language is blocked.
* Docs explain review bundle use by humans and agents.
* No full review bundle is committed.
* Handoff exists and records validation results.
* Claude review passes.

### Handoff Requirements

Create:

```text
handoffs/ASV1-P27.md
runs/<run_id>/phases/ASV1-P27/handoff.md
```

Handoff must include:

* review bundle coverage,
* source map summary,
* audit report summary,
* missing/failed artifact visibility summary,
* prohibited claim behavior,
* registry integration summary,
* tests run and results,
* artifact policy confirmation,
* confirmation that no full review bundle was committed,
* confirmation that no broker/live scope was introduced,
* known limitations,
* review focus.

### Review Requirements

Claude Opus 4.8 xhigh review required.

Claude Sonnet source-map audit may be used.

Review must verify:

* bundle completeness,
* source map usefulness,
* missing/failed artifact visibility,
* rejected config visibility,
* prohibited language enforcement,
* no approval/tradability claims,
* registry integration,
* artifact policy,
* no broker/live scope,
* no test weakening.

### Auto-Merge Eligibility

Auto PR and auto merge allowed if:

* tests pass,
* CLI help works,
* handoff validates,
* Claude verdict is `PASS` or `PASS_WITH_WARNINGS`,
* no full bundles or DBs are staged,
* no raw/heavy artifacts are staged,
* artifact policy passes,
* semantic done-check passes.

---

## ASV1-P28 — Researcher and AI Agent Onboarding

### Phase ID

`ASV1-P28`

### Phase Name

Researcher and AI Agent Onboarding

### Lane

GREEN

### Dependencies

* `ASV1-P27`

### Purpose

Create practical onboarding documentation for human researchers and AI Agents operating `alpha_system` under Frontier Harness Generic v3.0 Workflow 2 without violating artifact, no-lookahead, review, or no-claims policy.

This phase makes the platform usable and governable by future humans and autonomous agents.

### Scope

Create or update:

* `docs/ONBOARDING.md`
* `docs/RESEARCHER_GUIDE.md`
* `docs/AI_AGENT_GUIDE.md`
* `docs/CLI_REFERENCE.md`
* `docs/EXAMPLE_WORKFLOWS.md`
* `docs/TROUBLESHOOTING.md`
* `docs/RESEARCH_INTERPRETATION_POLICY.md`
* `AGENTS.md`
* `CLAUDE.md`
* `README.md`
* optional index updates in existing docs.

Docs must cover:

* WSL2 setup expectations,
* repo path policy,
* local-first stack,
* Workflow 2 operation,
* Ralph/Codex/Claude role boundaries,
* CLI command overview:

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
* artifact policy,
* no-lookahead policy,
* factor lifecycle,
* label/factor separation,
* strategy vs management vs portfolio boundaries,
* reference truth,
* fast path parity,
* grid discipline,
* ML leakage policy,
* registry inspection,
* review bundle generation,
* report interpretation without overclaiming,
* handoff creation,
* avoiding raw/heavy commits,
* no `git add .`,
* no `git add -A`,
* broker/live trading out of scope,
* how to escalate blocked states,
* how to avoid treating fixtures as alpha evidence.

### Non-Goals

* No new platform features.
* No source behavior changes except documentation references if unavoidable.
* No test weakening.
* No generated artifacts.
* No raw data.
* No local DB.
* No broker/live trading.
* No paper trading.
* No alpha/profitability/tradability claims.

### Expected Files / Directories

Expected docs:

* `docs/ONBOARDING.md`
* `docs/RESEARCHER_GUIDE.md`
* `docs/AI_AGENT_GUIDE.md`
* `docs/CLI_REFERENCE.md`
* `docs/EXAMPLE_WORKFLOWS.md`
* `docs/TROUBLESHOOTING.md`
* `docs/RESEARCH_INTERPRETATION_POLICY.md`

Expected updates:

* `AGENTS.md`
* `CLAUDE.md`
* `README.md`

Optional docs index updates:

* `docs/PLAN.md`
* `docs/ARCHITECTURE.md`

### Forbidden Changes

* No source implementation changes unless strictly documentation-link related and justified.
* No test weakening.
* No generated outputs.
* No raw data committed.
* No canonical data committed.
* No factor/label/signal stores committed.
* No full grid/trade/model/report outputs committed.
* No heavy artifacts committed.
* No local SQLite DB committed.
* No broker/live trading instructions.
* No paper trading instructions.
* No alpha/profitability/tradability claims.
* No fixture results presented as market evidence.
* No uncontrolled scope expansion.
* No hidden failed runs.
* No `git add .`.
* No `git add -A`.

### Validation Commands

Ralph must run and record:

```bash
test -f docs/ONBOARDING.md
test -f docs/RESEARCHER_GUIDE.md
test -f docs/AI_AGENT_GUIDE.md
test -f docs/CLI_REFERENCE.md
test -f docs/EXAMPLE_WORKFLOWS.md
test -f docs/TROUBLESHOOTING.md
test -f docs/RESEARCH_INTERPRETATION_POLICY.md
grep -R "broker/live trading" docs AGENTS.md CLAUDE.md README.md || true
grep -R "git add ." docs AGENTS.md CLAUDE.md README.md || true
grep -R "git add -A" docs AGENTS.md CLAUDE.md README.md || true
git status --short
find data -type f ! -name README.md ! -name ".gitkeep" -print
find artifacts -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
```

If markdown lint is available, run it and record results:

```bash
markdownlint docs README.md AGENTS.md CLAUDE.md || true
```

Ralph must inspect any `grep` hits for `git add .` and `git add -A` and confirm they are forbidden examples, not instructions to execute.

### Artifact Policy

Commit docs only, plus necessary updates to `AGENTS.md`, `CLAUDE.md`, and `README.md`.

Do not commit:

* generated outputs,
* data,
* DBs,
* logs,
* caches,
* artifacts,
* source behavior changes,
* test weakening.

Stage explicit files only. Never use `git add .` or `git add -A`.

### Done Criteria

* Researcher guide exists.
* AI Agent guide exists.
* CLI reference exists.
* Example workflows explain safe local-first research.
* Troubleshooting guide exists.
* Research interpretation policy exists.
* Docs repeat no raw/heavy artifact policy.
* Docs repeat no alpha/tradability claims.
* Docs repeat broker/live trading out of scope.
* Docs explain fixture results are correctness tests, not market evidence.
* Handoff exists and records validation results.
* Review is optional but must be recorded if skipped.

### Handoff Requirements

Create:

```text
handoffs/ASV1-P28.md
runs/<run_id>/phases/ASV1-P28/handoff.md
```

Handoff must include:

* docs changed,
* coverage checklist,
* validation results,
* confirmation no source behavior changes occurred unless explicitly justified,
* confirmation no data/artifact/DB files were committed,
* artifact policy confirmation,
* no broker/live confirmation,
* no overclaim confirmation,
* review skipped reason or review summary,
* known limitations.

### Review Requirements

Claude review optional because this is Green.

If skipped, Ralph must record:

* review not required by phase lane,
* docs-only nature,
* checks passed,
* artifact policy passed.

Ralph may request Claude Sonnet mechanical doc review if documentation consistency is uncertain.

### Auto-Merge Eligibility

Auto PR and auto merge allowed if:

* validation passes,
* handoff validates,
* artifact policy passes,
* no source/data/artifact changes outside docs are present unless justified,
* review passes if requested,
* semantic done-check passes.

---

## ASV1-P29 — End-to-End Local v0.1 Validation and Campaign Closeout

### Phase ID

`ASV1-P29`

### Phase Name

End-to-End Local v0.1 Validation and Campaign Closeout

### Lane

YELLOW

### Dependencies

* `ASV1-P28`

### Purpose

Run end-to-end local validation of the v0.1 platform on deterministic tiny fixtures and perform campaign-level semantic closeout.

This phase determines whether `ALPHA_SYSTEM_V1` is:

* `COMPLETE`,
* `COMPLETE_WITH_WARNINGS`,
* or `BLOCKED`.

The final decision must be evidence-based and must not rely on tests alone.

### Scope

Create or update:

* `evals/v0_1/`
* `docs/V0_1_VALIDATION.md`
* `docs/V0_1_RELEASE_NOTES.md`
* `docs/KNOWN_LIMITATIONS.md`
* `docs/NEXT_CAMPAIGN_CANDIDATES.md`
* `campaigns/ALPHA_SYSTEM_V1/CLOSEOUT.md`
* `tests/integration/test_end_to_end_v0_1.py`
* final validation configs under:

  * `configs/data/`
  * `configs/factors/`
  * `configs/labels/`
  * `configs/studies/`
  * `configs/strategies/`
  * `configs/grids/`
  * `configs/ml/`
  * `configs/management/`
  * `configs/portfolio/`
  * `configs/execution/`
* final handoff under `handoffs/`
* final review under `reviews/`
* final run summary under `runs/<run_id>/RUN_SUMMARY.md`

End-to-end fixture workflow must exercise:

1. data validation,
2. canonical 1-minute fixture bars,
3. calendar/session assignment,
4. factor validation,
5. label generation/alignment,
6. factor compute,
7. factor diagnostics,
8. factor card/report generation,
9. signal/strategy generation,
10. reference backtest,
11. cost/slippage,
12. management rules,
13. portfolio sizing,
14. fast path parity,
15. bounded grid,
16. management grid,
17. experiment registry,
18. ML MVP,
19. multi-symbol fixture if feasible,
20. L2 schema/feature fixture if feasible,
21. review bundle generation,
22. registry status.

Semantic closeout must verify:

* all phases completed or blocked honestly,
* acceptance criteria satisfied or blocked,
* no conflicting PnL truth,
* reference engine remains truth,
* fast path parity is proven for scoped features,
* no raw data committed,
* no heavy artifacts committed,
* no SQLite DB committed,
* no known unresolved lookahead issue,
* no hidden failed runs,
* no test weakening/gaming,
* no broker/live trading scope,
* no paper trading scope,
* no unsupported alpha/profitability/tradability claims,
* candidate promotion requires review,
* L2 work remains readiness/design only,
* docs/onboarding are complete.

Final closeout docs must include:

* final acceptance result,
* acceptance gate results,
* warnings,
* unresolved limitations,
* deferred future work,
* next campaign candidates,
* artifact audit result,
* no-lookahead status,
* fast parity status,
* registry status,
* explicit broker/live out-of-scope statement,
* explicit no alpha/tradability claim statement.

### Non-Goals

* No real dataset validation.
* No large historical backtest.
* No performance benchmark as acceptance proof.
* No live trading.
* No paper trading.
* No broker integration.
* No production release claim.
* No alpha/profitability/tradability claim.
* No large release artifacts committed.
* No source feature expansion unless required to fix a validation blocker through repair loop.
* No broad redesign.

### Expected Files / Directories

Expected files:

* `docs/V0_1_VALIDATION.md`
* `docs/V0_1_RELEASE_NOTES.md`
* `docs/KNOWN_LIMITATIONS.md`
* `docs/NEXT_CAMPAIGN_CANDIDATES.md`
* `campaigns/ALPHA_SYSTEM_V1/CLOSEOUT.md`
* `tests/integration/test_end_to_end_v0_1.py`
* final handoff file under `handoffs/`
* final review file under `reviews/`

Expected final run artifacts:

* `runs/<run_id>/RUN_SUMMARY.md`
* `runs/<run_id>/phases/ASV1-P29/handoff.md`
* `runs/<run_id>/phases/ASV1-P29/review.md`
* `runs/<run_id>/phases/ASV1-P29/verdict.json`
* `runs/<run_id>/phases/ASV1-P29/checks.json`

Expected small curated validation outputs if allowed:

* `evals/v0_1/VALIDATION_SUMMARY.md`
* `evals/v0_1/VALIDATION_MATRIX.csv`
* `evals/v0_1/ARTIFACT_AUDIT_SUMMARY.md`

These files must be small, curated, and must not include raw data, trade logs, factor values, label values, full grid outputs, or local DB contents.

### Forbidden Changes

* No release SQLite DB committed.
* No generated factor values committed.
* No generated label values committed.
* No generated signal stores committed.
* No full grid outputs committed.
* No management grid outputs committed.
* No full trade logs committed.
* No full equity curves committed.
* No full review bundle committed.
* No raw data committed.
* No canonical generated data committed outside fixtures.
* No heavy artifacts committed.
* No weakening tests to pass validation.
* No hiding failed steps.
* No broker/live trading scope.
* No paper trading scope.
* No alpha/profitability/tradability claims.
* No treating fixture results as market evidence.
* No uncontrolled scope expansion.
* No `git add .`.
* No `git add -A`.

### Validation Commands

Ralph must run and record:

```bash
python -m pytest
python -m alpha_system.cli registry status --help
python -m alpha_system.cli data validate --help
python -m alpha_system.cli data build-bars --help
python -m alpha_system.cli factor validate --help
python -m alpha_system.cli factor materialize --help
python -m alpha_system.cli study run --help
python -m alpha_system.cli backtest run --help
python -m alpha_system.cli grid run --help
python -m alpha_system.cli management grid --help
python -m alpha_system.cli ml run --help
python -m alpha_system.cli report build --help
git status --short
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
find data -type f ! -name README.md ! -name ".gitkeep" ! -path "*/tests/fixtures/*" -print
git ls-files | grep -E '(^data/.*\.(parquet|csv|jsonl|db|sqlite)$|^metadata/.*\.(sqlite|db)$|^artifacts/)' || true
test -f ACTIVE_CAMPAIGN.md
test -f campaigns/ALPHA_SYSTEM_V1/GOAL.md
test -f campaigns/ALPHA_SYSTEM_V1/PHASE_PLAN.md
test -f campaigns/ALPHA_SYSTEM_V1/campaign.yaml
test -f campaigns/ALPHA_SYSTEM_V1/ACCEPTANCE.md
test -f campaigns/ALPHA_SYSTEM_V1/RISK_REGISTER.md
test -f campaigns/ALPHA_SYSTEM_V1/RUNBOOK.md
test -f docs/V0_1_VALIDATION.md
test -f docs/V0_1_RELEASE_NOTES.md
test -f docs/KNOWN_LIMITATIONS.md
test -f docs/NEXT_CAMPAIGN_CANDIDATES.md
test -f campaigns/ALPHA_SYSTEM_V1/CLOSEOUT.md
test -f tests/integration/test_end_to_end_v0_1.py
```

If console script is available, also run:

```bash
alpha registry status --help
alpha data validate --help
alpha data build-bars --help
alpha factor validate --help
alpha factor materialize --help
alpha study run --help
alpha backtest run --help
alpha grid run --help
alpha management grid --help
alpha ml run --help
alpha report build --help
```

If lint/type tools are configured:

```bash
python -m ruff check .
python -m mypy src
```

Required validation coverage:

* full integration smoke,
* end-to-end v0.1 fixture test,
* aggregate no-lookahead tests,
* artifact policy tests,
* reproducibility tests,
* registry tests,
* CLI smoke tests,
* parity tests,
* report prohibited-claim tests,
* fixture-only validation summary,
* artifact audit,
* no committed local DB,
* no committed raw/heavy outputs.

### Artifact Policy

Commit only:

* validation docs,
* release notes,
* known limitations,
* next-campaign candidates,
* closeout docs,
* integration tests,
* tiny fixture configs,
* small curated validation summaries if below repository artifact-size policy.

Do not commit:

* release SQLite DB,
* generated factor values,
* generated label values,
* generated signal stores,
* full grid outputs,
* management grid outputs,
* full trade logs,
* full equity curves,
* generated review bundle directory,
* logs,
* cache,
* raw datasets,
* canonical datasets,
* large Parquet files,
* local model artifacts,
* heavy artifacts.

Stage explicit files only. Never use `git add .` or `git add -A`.

### Done Criteria

* Full test suite passes or blockers are truthfully recorded.
* End-to-end fixture validation passes or blocker is truthfully recorded.
* CLI smoke checks pass.
* No-lookahead tests pass.
* Fast/reference parity tests pass for scoped features.
* Artifact policy audit passes.
* Registry status works on temp/local test DB.
* Validation summary states fixture validation is correctness validation, not market evidence.
* Closeout docs exist.
* Known limitations exist.
* Next-campaign candidates exist.
* Final semantic done-check completed.
* Final recommendation is one of:

  * `COMPLETE`
  * `COMPLETE_WITH_WARNINGS`
  * `BLOCKED`
* No raw/heavy/local artifacts are committed.
* No broker/live/paper scope is introduced.
* No alpha/profitability/tradability claims are made.
* Handoff exists and records validation results.
* Claude review passes for `COMPLETE` or `COMPLETE_WITH_WARNINGS`, or records block reason for `BLOCKED`.

### Handoff Requirements

Create:

```text
handoffs/ASV1-P29.md
runs/<run_id>/phases/ASV1-P29/handoff.md
```

Handoff must include:

* end-to-end workflow summary,
* command/test results,
* validation artifact locations,
* failed-step visibility,
* acceptance gate results,
* artifact policy audit,
* no raw/heavy/local artifact confirmation,
* no-lookahead status,
* fast parity status,
* registry status,
* known limitations,
* next-campaign candidates,
* final semantic done-check result,
* final recommendation:

  * `COMPLETE`
  * `COMPLETE_WITH_WARNINGS`
  * `BLOCKED`
* explicit statement that broker/live/paper trading remains out of scope,
* explicit statement that no alpha/profitability/tradability claims are made.

### Review Requirements

Claude Opus 4.8 xhigh final review required.

Review must verify:

* semantic v0.1 readiness,
* acceptance criteria,
* no-lookahead compliance,
* artifact policy,
* reference truth,
* fast parity,
* registry/reproducibility,
* review-bundle/source-map readiness,
* documentation/onboarding completeness,
* no broker/live/paper scope,
* no unsupported claims,
* no hidden failed runs,
* no test weakening,
* blocked state honesty if applicable.

ChatGPT Pro GPT-5.5 Thinking may perform final strategic review after run completion.

### Auto-Merge Eligibility

Auto PR and auto merge allowed if:

* full validation passes,
* handoff validates,
* final review verdict is `PASS` or `PASS_WITH_WARNINGS`,
* artifact audit is clean,
* no heavy/local artifacts are staged,
* no raw/generated data is staged,
* semantic done-check passes,
* final verdict is `COMPLETE` or `COMPLETE_WITH_WARNINGS`.

If final verdict is `BLOCKED`, merge may occur only for truthful closeout documentation if no unsafe partial changes are included and Ralph policy permits blocked closeout documentation.

---

## Phase Gate Summary

### Gate 1 — Harness and Repo Foundation

Phases:

* ASV1-P00
* ASV1-P01

Exit requirement:

* repo foundation exists,
* Workflow 2 harness policy exists,
* WSL2 path policy is documented,
* artifact policy is enforceable,
* explicit staging policy exists,
* no raw/heavy/local artifacts are committed.

### Gate 2 — Architecture and Workspace Foundation

Phases:

* ASV1-P02
* ASV1-P03

Exit requirement:

* local-first architecture is documented,
* target platform is defined as an Alpha Research Platform, not merely a backtester,
* Python package skeleton exists,
* CLI skeleton exists,
* base tests pass,
* no domain logic scope creep occurs.

### Gate 3 — Contracts and Registry Foundation

Phases:

* ASV1-P04
* ASV1-P05

Exit requirement:

* required domain contracts exist,
* required schema fields are represented and tested,
* SQLite registry MVP exists,
* required tables exist,
* reproducibility metadata fields are represented,
* no local DB is committed.

### Gate 4 — Data and Calendar Foundation

Phases:

* ASV1-P06
* ASV1-P07
* ASV1-P08

Exit requirement:

* canonical 1-minute data layer exists,
* session and calendar model exists,
* data quality flags exist,
* data validation CLI exists,
* fixture policy exists,
* no real/generative data is committed.

### Gate 5 — Factor and Label Foundation

Phases:

* ASV1-P09
* ASV1-P10
* ASV1-P11

Exit requirement:

* FactorSpec, lifecycle, and registry behavior exist,
* label store exists,
* factor compute SDK exists,
* label leakage is blocked,
* draft factor materialization is blocked by default,
* no generated factor/label outputs are committed.

### Gate 6 — Diagnostics and Evidence

Phases:

* ASV1-P12
* ASV1-P13

Exit requirement:

* intraday factor diagnostics engine exists,
* factor cards and reports exist,
* sample size and warning behavior exist,
* prohibited claim language is blocked,
* diagnostics are not treated as tradability proof.

### Gate 7 — Signal, Strategy, and Reference Truth

Phases:

* ASV1-P14
* ASV1-P15
* ASV1-P16

Exit requirement:

* signal store exists,
* StrategySpec exists,
* reference 1-minute backtest truth exists,
* conservative cost/slippage/fill semantics exist,
* strategy does not own portfolio, management, fills, or accounting,
* no conflicting PnL truth exists.

### Gate 8 — Management, Portfolio, and Fast Parity

Phases:

* ASV1-P17
* ASV1-P18
* ASV1-P19

Exit requirement:

* position management layer exists,
* portfolio target/sizing layer exists,
* fast path exists only as acceleration,
* reference/fast parity is tested,
* unsupported fast-path features fail closed or route to reference.

### Gate 9 — Grid, Registry, and ML Research Foundation

Phases:

* ASV1-P20
* ASV1-P21
* ASV1-P22
* ASV1-P23

Exit requirement:

* bounded strategy grid exists,
* survivor-based management grid exists,
* experiment registry is hardened,
* failed runs are visible,
* ML/factor-combination MVP consumes versioned factor inputs only,
* no raw ad hoc ML features are allowed,
* no candidate approval is automatic.

### Gate 10 — Multi-Symbol and L2 Readiness

Phases:

* ASV1-P24
* ASV1-P25
* ASV1-P26

Exit requirement:

* multi-symbol universe support exists,
* instrument master supports future multi-asset research,
* L2 schemas exist,
* L2-derived feature skeleton exists,
* L2 work remains design/fixture-only,
* no real L2 data, replay, passive fill, or live feed scope is introduced.

### Gate 11 — Review, Onboarding, and Closeout

Phases:

* ASV1-P27
* ASV1-P28
* ASV1-P29

Exit requirement:

* review bundles and source maps exist,
* onboarding docs exist,
* end-to-end local v0.1 validation is complete or truthfully blocked,
* final semantic done-check is complete,
* final verdict is `COMPLETE`, `COMPLETE_WITH_WARNINGS`, or `BLOCKED`.

---

## Campaign-Wide Done Criteria

The campaign may be marked `COMPLETE` or `COMPLETE_WITH_WARNINGS` only when all of the following are true:

1. All phases ASV1-P00 through ASV1-P29 are complete, or any exception is truthfully documented as non-blocking.
2. Every Yellow phase has a fresh Claude Opus review.
3. Every merged reviewed phase has verdict `PASS` or `PASS_WITH_WARNINGS`.
4. Every phase has a handoff.
5. Every phase has checks recorded.
6. Every required CLI command exposes help:

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
7. The full test suite passes, or any failure is truthfully recorded as a blocker.
8. End-to-end v0.1 fixture validation passes, or final verdict is `BLOCKED`.
9. Artifact audit confirms no raw data, generated data, local DBs, heavy artifacts, full trade logs, full grid outputs, generated review bundles, or model binaries are committed.
10. No `git add .` or `git add -A` is used for campaign staging.
11. No test weakening or gaming is detected.
12. No hidden failed runs are detected.
13. No candidate promotion can occur without review.
14. No factor draft can be permanently materialized by default.
15. Labels cannot leak into live factor inputs or live strategy inputs.
16. No unresolved known lookahead issue remains.
17. Reference 1-minute engine remains the canonical bar-level PnL truth.
18. Fast path remains acceleration only and is parity-gated.
19. Grid and management-grid searches are bounded.
20. ML uses versioned factor inputs only.
21. Multi-symbol support does not assume one global timezone/session.
22. L2 work remains schema/skeleton/design-only.
23. No broker, paper trading, live trading, or order routing is introduced.
24. No alpha/profitability/tradability/production-readiness claims are made.
25. Final closeout docs exist:

* `docs/V0_1_VALIDATION.md`
* `docs/V0_1_RELEASE_NOTES.md`
* `docs/KNOWN_LIMITATIONS.md`
* `docs/NEXT_CAMPAIGN_CANDIDATES.md`
* `campaigns/ALPHA_SYSTEM_V1/CLOSEOUT.md`

26. Final run summary exists.
27. Final semantic done-check is complete.
28. Final verdict is explicit:

* `COMPLETE`
* `COMPLETE_WITH_WARNINGS`
* `BLOCKED`

A truthful `BLOCKED` verdict is acceptable. A false `COMPLETE` verdict is not acceptable.

---

## Final Notes on Scope Boundaries

`ALPHA_SYSTEM_V1` is a local-first research-platform foundation campaign.

It must end with:

* no broker integration,
* no paper trading,
* no live trading,
* no order routing,
* no production execution adapter,
* no cloud database dependency,
* no paid database dependency,
* no server-first architecture,
* no required ClickHouse/QuestDB/DolphinDB/kdb+/S3/Dagster/Ray/MLflow-server dependency,
* no real raw market data committed,
* no large generated artifacts committed,
* no unsupported alpha/profitability/tradability claims.

The campaign may produce:

* source code,
* contracts,
* configs,
* schemas,
* tiny deterministic fixtures,
* tests,
* docs,
* phase specs,
* handoffs,
* reviews,
* run manifests if small,
* curated validation summaries,
* review-bundle/source-map tooling,
* release closeout docs.

The campaign must preserve the core architectural separations:

1. Data is not factor.
2. Factor is not signal.
3. Signal is not strategy.
4. Strategy is not portfolio.
5. Portfolio is not execution.
6. Backtest is not live trading.
7. Fast research simulation is not execution truth.
8. Draft factor values are not automatically long-term stored.
9. Only validated/reviewed factors may be materialized into long-term factor store.
10. Every result must be reproducible through git commit, code hash, config hash, data version, factor version, label version, engine version, and run manifest.

Future campaigns may extend `alpha_system` with:

* richer data ingestion,
* larger market datasets,
* deeper factor libraries,
* more sophisticated ML,
* event-driven finalist validation,
* Level-2 replay research,
* distributed compute,
* external experiment-tracking integrations,
* web UI,
* paper trading,
* live trading.

Those future extensions require separate campaign contracts, separate scope authorization, and separate acceptance gates. They are not part of `ALPHA_SYSTEM_V1`.
