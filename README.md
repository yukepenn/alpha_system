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

`ALPHA_DATA_FOUNDATION_V1` is active. Within the `campaign_bootstrap` gate,
`DATA-P00` and `DATA-P01` are complete, and the `DATA-P02` executor snapshot
adds validated `DataSourceProfile` and `LocalDataRootPolicy` records. The active
phase is `DATA-P02` - Data Source Profiles and Local Data Root Policy. The next
phase is `DATA-P03` - IBKR Connection Profile and Client ID Guard. Ralph-owned
review, verdict parsing, semantic done-check, PR, CI, and merge gates remain
required before any phase PASS is recorded.

`DATA-P00` added the durable `docs/data_foundation/` root:

- `docs/data_foundation/README.md`
- `docs/data_foundation/DATA_FOUNDATION_OVERVIEW.md`

`DATA-P01` adds the data-foundation skeleton under `src/alpha_system/data/foundation/`
alongside the pre-existing `alpha_system.data` modules. It defines placeholder
names for data sources, local data-root policy, IBKR historical-data connection
metadata, request manifests and ledgers, raw/parsed/canonical bars, instruments,
sessions, rolls, series provenance, batches, dataset versions, quality, coverage,
and partitions.

`DATA-P02` adds fail-closed policy behavior for provider usage modes and the
local data root under `src/alpha_system/data/foundation/sources.py`, plus unit
tests under `tests/unit/data/` and these durable docs:

- `docs/data_foundation/DATA_SOURCE_PROFILE.md`
- `docs/data_foundation/LOCAL_DATA_ROOT_POLICY.md`

The prior `ALPHA_SYSTEM_V1`, `ASV1_RELEASE_HYGIENE`, and
`ALPHA_RESEARCH_GOVERNANCE_MVP` baselines are treated as complete. This campaign
builds on that local-first research harness by adding a read-only, provenance-rich
historical futures data foundation.

Safety boundaries are unchanged: IBKR remains read-only historical only; no
broker, order, account, paper, live, or real-time scope is introduced; real data
is local-only via `ALPHA_DATA_ROOT`; no raw or heavy artifact commits, no local
DB commits, explicit staging only, and no alpha, profitability, tradability, or
production-readiness claims.

## Data Foundation Docs

The data-foundation docs root currently includes:

- `docs/data_foundation/README.md`
- `docs/data_foundation/DATA_FOUNDATION_OVERVIEW.md`
- `docs/data_foundation/NAMING.md`
- `docs/data_foundation/DATA_SOURCE_PROFILE.md`
- `docs/data_foundation/LOCAL_DATA_ROOT_POLICY.md`

These docs describe the read-only data truth layer, campaign hard rules,
data-foundation object list, lifecycle state model, prohibited MVP states, IBKR
read-only posture, canonical object names, ID prefixes, module names,
file-naming conventions, directory layout, `DataSourceProfile`,
`LocalDataRootPolicy`, and the `ALPHA_DATA_ROOT` local-only data-root pointer.
Field-level acceptance rules, risks, and operator procedures remain in the
campaign contract bundle.

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
Permitted placeholders are limited to `.gitkeep` or `README.md` files where the
campaign policy allows them. Commit-eligible phase handoffs for this campaign
belong under `handoffs/ALPHA_DATA_FOUNDATION_V1/`.

## Documentation Map

Project-level orientation:

- `ACTIVE_CAMPAIGN.md`
- `PROJECT_STATUS.md`
- `AGENTS.md`
- `CLAUDE.md`

Data-foundation docs:

- `docs/data_foundation/README.md`
- `docs/data_foundation/DATA_FOUNDATION_OVERVIEW.md`
- `docs/data_foundation/NAMING.md`

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
- `docs/REPRODUCIBILITY_PRINCIPLES.md`
- `docs/CLI_COMMANDS_TARGET.md`

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
- `src/alpha_system/cli/`
- `src/alpha_system/data/`
- `src/alpha_system/governance/`
- `tests/unit/data/`
- `tools/governance/`
- `tests/unit/governance/`
- `tests/integration/governance/`
- `tests/no_lookahead/`

Local data and generated artifact roots are present for structure only:

- `data/raw/`
- `data/canonical/`
- `data/factors/`
- `data/labels/`
- `data/cache/`
- `metadata/`
- `artifacts/`

## Useful Commands

The DATA-P01 data-foundation skeleton imports through
`alpha_system.data.foundation`. The governance CLI command group remains
`alpha governance`; see `docs/governance/CLI.md` for arguments and gate behavior.
Local validation commands include:

```bash
python -c "import alpha_system.data"
python -m pytest tests/unit/data -q
python -c "import alpha_system.governance"
python -m pytest tests/unit/governance/test_canary_harness.py -q
python -m pytest tests/unit/governance/test_negative_controls.py -q
python -m pytest tests/integration/governance/test_end_to_end_dry_run.py -q
python -m pytest tests/unit/governance -q
python -m pytest tests/integration/governance -q
python -m pytest tests/no_lookahead/test_governance_canaries.py -q
python -m pytest tests/no_lookahead -q
python tools/governance/validate_objects.py --object AlphaSpec:tests/fixtures/governance/alpha_spec_valid.json
python tools/verify.py --smoke
python tools/verify.py --all
python tools/hooks/canary_runner.py
```
