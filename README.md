# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing an Alpha Research Platform under Frontier Harness Generic `0.3.0-rc1`.

The active campaign is `ALPHA_RESEARCH_GOVERNANCE_MVP`, defined in `campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/`. Current phase progress is tracked in `ACTIVE_CAMPAIGN.md`.

This repository is not a broker, paper-trading, live-trading, order-routing, or production execution system. It must not introduce alpha, profitability, tradability, or production-readiness claims.

## Current Repo Snapshot

`ALPHA_RESEARCH_GOVERNANCE_MVP` is underway. `ARGOV-P03` has completed its executor deliverables for Ralph validation and independent review: the `AlphaSpec` contract, deterministic `AlphaSpec` ID check, canonical round-trip helpers, the pure no-code gate for `REGISTERED -> IMPLEMENTATION_ALLOWED`, focused governance unit tests, concise contract documentation, and the governance template now exist. No phase PASS verdict is recorded here.

The active/just-completed phase is `ARGOV-P03 — AlphaSpec Contract and No-Code Gate` while the Ralph-owned validation, review, verdict, PR, CI, merge, and done-check gates run. The next planned phase is `ARGOV-P04 — HypothesisCard and Pre-registration Protocol`.

The prior `ALPHA_SYSTEM_V1` and `ASV1_RELEASE_HYGIENE` baselines are treated as complete. This governance campaign builds on that local-first research harness by adding the admissibility and evidence-governance protocol that future research must pass through before broader research campaigns begin.

Safety boundaries are unchanged: governance-only scope, no real data ingestion, no alpha search, no broker/live/paper work, no order routing, no production deployment behavior, no raw or heavy artifact commits, no local DB commits, explicit staging only, and no alpha, profitability, tradability, or production-readiness claims.

## Governance Docs

The governance docs root currently includes:

- `docs/governance/README.md`
- `docs/governance/GOVERNANCE_OVERVIEW.md`
- `docs/governance/NAMING.md`
- `docs/governance/PRIMITIVES.md`
- `docs/governance/ALPHA_SPEC.md`

These docs describe the admissibility protocol at a high level, define the canonical governance object names and prefixes, document the shared ID, serialization, hashing, and fail-closed validation primitives, and describe the `AlphaSpec` contract plus no-code gate. Additional governance object schemas, registry integration, CLI behavior, and report builders remain for later phases.

## Campaign Source Of Truth

The active campaign contract bundle lives under `campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/`:

- `GOAL.md`
- `PHASE_PLAN.md`
- `campaign.yaml`
- `ACCEPTANCE.md`
- `RISK_REGISTER.md`
- `RUNBOOK.md`

`ACTIVE_CAMPAIGN.md` is the repository-level active-campaign pointer. Do not create a campaign-local active-campaign pointer for this campaign.

## Repository Location

Canonical repo path:

```text
~/projects/alpha_system
```

The active repo and any active worktree must live on the WSL2 Linux filesystem. Do not run active work from `/mnt/c`, `/mnt/d`, `/mnt/e`, OneDrive, Dropbox, Google Drive, Windows-synced folders, network drives, or temporary directories.

## Workflow 2 Boundary

Frontier Workflow 2 uses Ralph as the strict autonomous driver. Codex executes generated phase specs and writes executor output and commit-eligible handoffs. Ralph owns formal validation, independent review, verdict parsing, repair orchestration, semantic done-checks, PR creation, CI, and merge gates.

Required safety defaults:

- STOP files halt the Workflow 2 loop at the configured checkpoints.
- Failed runs and rejected ideas must remain visible to the governance process.
- Yellow phases require fresh independent review before merge eligibility.
- No phase may weaken or game tests.

## Git Discipline

Use explicit staging only. Stage curated paths one by one.

Forbidden:

```bash
git add .
git add -A
git push --force
```

Before any commit, inspect:

```bash
git status --short
git diff --cached --name-only
```

The staged set must contain only commit-eligible paths for the active phase and must not include forbidden data, cache, log, DB, or heavy artifact paths.

## Artifact Policy

Never commit raw data, canonical generated data, materialized factor values, materialized label values, local SQLite or DB files, heavy artifacts, generated reports, logs, caches, local model artifacts, credential material, or local environment files.

Permitted placeholders are limited to `.gitkeep` or `README.md` files where the campaign policy allows them. Commit-eligible phase handoffs for this campaign belong under `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/`.

## Documentation Map

Project-level orientation:

- `ACTIVE_CAMPAIGN.md`
- `PROJECT_STATUS.md`
- `AGENTS.md`
- `CLAUDE.md`

Architecture and workflow docs:

- `docs/PLAN.md`
- `docs/ARCHITECTURE.md`
- `docs/ONBOARDING.md`
- `docs/RESEARCHER_GUIDE.md`
- `docs/AI_AGENT_GUIDE.md`
- `docs/CLI_REFERENCE.md`
- `docs/EXAMPLE_WORKFLOWS.md`
- `docs/TROUBLESHOOTING.md`
- `docs/RESEARCH_INTERPRETATION_POLICY.md`
- `docs/LOCAL_FIRST_STACK.md`
- `docs/RESEARCH_WORKFLOW.md`
- `docs/DOMAIN_BOUNDARIES.md`
- `docs/NO_LOOKAHEAD_POLICY.md`
- `docs/BACKTEST_TIERS.md`
- `docs/ARTIFACT_POLICY.md`
- `docs/REPRODUCIBILITY_PRINCIPLES.md`
- `docs/CLI_COMMANDS_TARGET.md`

Governance docs:

- `docs/governance/README.md`
- `docs/governance/GOVERNANCE_OVERVIEW.md`
- `docs/governance/NAMING.md`
- `docs/governance/PRIMITIVES.md`
- `docs/governance/ALPHA_SPEC.md`

## Directory Layout

Commit-eligible policy and campaign files live under:

- `campaigns/`
- `specs/`
- `handoffs/`
- `reviews/`
- `docs/`
- `decisions/`
- `evals/`
- `configs/`
- `templates/`
- `src/alpha_system/governance/`
- `tests/unit/governance/`

Local data and generated artifact roots are present for structure only:

- `data/raw/`
- `data/canonical/`
- `data/factors/`
- `data/labels/`
- `data/cache/`
- `metadata/`
- `artifacts/`

## Useful Commands

No new CLI commands are added by `ARGOV-P03`. Durable governance modules now include `alpha_system.governance.ids`, `alpha_system.governance.serialization`, `alpha_system.governance.validation`, and `alpha_system.governance.alpha_spec`. The AlphaSpec template is `templates/governance/alpha_spec.template.yaml`. Local validation commands include:

```bash
python -c "import alpha_system.governance"
python -m pytest tests/unit/governance -q
python tools/verify.py --smoke
python tools/verify.py --all
python tools/hooks/canary_runner.py
```
