# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing
an Alpha Research Platform under Frontier Harness Generic `0.3.0-rc1`.

The active campaign is `ALPHA_DATA_FOUNDATION_V1`, defined in
`campaigns/ALPHA_DATA_FOUNDATION_V1/`. Current campaign state is tracked in the
repository-level `ACTIVE_CAMPAIGN.md`.

This repository is not a broker, paper-trading, live-trading, order-routing, or
production execution system. It must not introduce alpha, profitability,
tradability, or production-readiness claims.

## Current Repo Snapshot

`ALPHA_DATA_FOUNDATION_V1` is active. `DATA-P00` - Data Foundation Campaign
Bootstrap - is complete at executor handoff, with Ralph-owned independent
review, verdict parsing, semantic done-check, PR, CI, and merge gates still
required before any phase PASS is recorded. The next phase is `DATA-P01` -
Data Package Skeleton and Naming.

This phase adds the durable `docs/data_foundation/` root:

- `docs/data_foundation/README.md`
- `docs/data_foundation/DATA_FOUNDATION_OVERVIEW.md`

`DATA-P00` adds documentation and the commit-eligible handoff only. It adds no
`src/alpha_system/data/**` source, no tests, no configs, no templates, no IBKR
connector code, and no provider pull behavior.

Safety boundaries are unchanged: IBKR is read-only historical only; no broker,
order, account, paper, live, or real-time signal scope exists; clientId `101`
and `102` are hard-blocked; the data-client namespace is `201-209`; real data
is local-only; raw/canonical/provider/account/heavy/DB artifacts and `runs/**`
must not be committed; explicit staging is required.

## Data Foundation Docs

The data-foundation docs root currently includes:

- `docs/data_foundation/README.md`
- `docs/data_foundation/DATA_FOUNDATION_OVERVIEW.md`

These docs describe the read-only data truth layer, campaign hard rules,
data-foundation object list, lifecycle state model, prohibited MVP states, and
IBKR read-only posture at a high level. Field-level contracts, acceptance
rules, risks, and operator procedures remain in the campaign contract bundle.

## Campaign Source Of Truth

The active campaign contract bundle lives under
`campaigns/ALPHA_DATA_FOUNDATION_V1/`:

- `GOAL.md`
- `PHASE_PLAN.md`
- `campaign.yaml`
- `ACCEPTANCE.md`
- `RISK_REGISTER.md`
- `RUNBOOK.md`

`ACTIVE_CAMPAIGN.md` is the repository-level active-campaign pointer. Do not
create `campaigns/ALPHA_DATA_FOUNDATION_V1/ACTIVE_CAMPAIGN.md`.

## Prior Baselines

`ALPHA_DATA_FOUNDATION_V1` builds on these completed baselines:

- `ALPHA_SYSTEM_V1`
- `ASV1_RELEASE_HYGIENE`
- `ALPHA_RESEARCH_GOVERNANCE_MVP`

The governance docs remain under `docs/governance/`; future research must still
honor the governance protocol before broader research campaigns expand scope.

## Repository Location

Canonical repo path:

```text
~/projects/alpha_system
```

The active repo and any active worktree must live on the WSL2 Linux
filesystem. Do not run active work from `/mnt/c`, `/mnt/d`, `/mnt/e`,
OneDrive, Dropbox, Google Drive, Windows-synced folders, network drives, or
temporary directories.

## Workflow 2 Boundary

Frontier Workflow 2 uses Ralph as the strict autonomous driver. Codex executes
generated phase specs and writes executor output and commit-eligible handoffs.
Ralph owns formal validation, independent review, verdict parsing, repair
orchestration, semantic done-checks, PR creation, CI, and merge gates.

Required safety defaults:

- STOP files halt the Workflow 2 loop at configured checkpoints.
- Yellow phases require fresh independent review before merge eligibility.
- No phase may weaken or game tests.
- Run-local Workflow 2 artifacts stay under `runs/**`.
- Commit-eligible data-foundation handoffs live under
  `handoffs/ALPHA_DATA_FOUNDATION_V1/**`.

## Git Discipline

Use explicit staging only. Stage curated paths one by one.

Forbidden:

```bash
git add .
git add -A
git push --force
```

Before any commit or merge-gate evaluation, inspect:

```bash
git status --short
git diff --cached --name-only
git ls-files runs
```

The staged set must contain only commit-eligible paths for the active phase and
must not include `runs/**`, raw data, canonical data, provider responses,
account artifacts, DB files, logs, caches, or heavy artifacts.

## Artifact Policy

Never commit raw data, canonical generated data, materialized factor values,
materialized label values, local SQLite or DB files, heavy artifacts, generated
reports, logs, caches, local model artifacts, credential material, provider
responses, account information, or local environment files.

Raw and canonical real market data remain local-only outside git. `runs/**` is
local-only runtime state and must not be staged or committed.

## Documentation Map

Project-level orientation:

- `ACTIVE_CAMPAIGN.md`
- `PROJECT_STATUS.md`
- `AGENTS.md`
- `CLAUDE.md`

Data-foundation docs:

- `docs/data_foundation/README.md`
- `docs/data_foundation/DATA_FOUNDATION_OVERVIEW.md`

Governance docs:

- `docs/governance/README.md`
- `docs/governance/GOVERNANCE_OVERVIEW.md`
- `docs/governance/WORKFLOW2_INTEGRATION.md`

Architecture and workflow docs:

- `docs/ONBOARDING.md`
- `docs/RESEARCHER_GUIDE.md`
- `docs/AI_AGENT_GUIDE.md`
- `docs/CLI_REFERENCE.md`
- `docs/EXAMPLE_WORKFLOWS.md`
- `docs/TROUBLESHOOTING.md`
- `docs/RESEARCH_INTERPRETATION_POLICY.md`
- `docs/ARTIFACT_POLICY.md`
- `docs/DOMAIN_BOUNDARIES.md`
- `docs/NO_LOOKAHEAD_POLICY.md`
- `docs/BACKTEST_TIERS.md`

## Useful Commands

Local validation commands include:

```bash
python tools/verify.py --smoke
python tools/verify.py --all
python tools/hooks/canary_runner.py
```
