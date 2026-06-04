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
`DATA-P00` and `DATA-P01` are complete; the `DATA-P02` executor snapshot adds
validated `DataSourceProfile` and `LocalDataRootPolicy` records; and the
`DATA-P03` executor snapshot adds `IBKRConnectionProfile`,
`IBKRClientIdPolicy`, and a diagnostic-only connection-doctor scaffold. The
`ibkr_read_only_boundary` gate has the `DATA-P04` executor scope complete:
read-only IBKR API boundary, order-method kill switch, and `DataAccessMode`
gate. The `futures_contract_master` gate has progressed through `DATA-P06`:
`DATA-P05` adds `InstrumentMasterRecord`, six to-be-verified futures
contract-economics anchors, and exact `tick_value = tick_size * point_value`
validation; `DATA-P06` adds `ContractDetailsSnapshot`,
`FuturesContractRecord`, and the no-live-call contract-discovery scaffold. The
`request_and_storage` is in progress through `DATA-P08`: `DATA-P07` adds
`HistoricalRequestSpec`, `HistoricalRequestManifest`, deterministic
`manifest_hash` validation, the no-manifest-no-pull guard, the synthetic sample
manifest under `templates/data/`, and
`docs/data_foundation/REQUEST_SPEC_AND_MANIFEST.md`. `DATA-P08` is complete and
adds `RequestPacingPolicy`, `HistoricalChunkRecord`, `HistoricalPullLedger`,
`ProviderErrorRecord`, conservative to-be-verified pacing config, and
`docs/data_foundation/PACING_AND_RESUME.md`. The next phase is `DATA-P09` - Raw
Local Data Lake Layout. Ralph still owns formal validation, independent review,
verdict parsing, semantic done-check, PR, CI, and merge gates.

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

`DATA-P03` adds fail-closed IBKR historical connection configuration under
`src/alpha_system/data/foundation/ibkr.py`. clientId `101` and `102` are
hard-blocked, the data namespace is `201-209` with default `201`, worker IDs are
`ES=201`, `NQ=202`, `RTY=203`, and the connection doctor records scaffold
reachability status without opening a socket or calling IBKR. It also adds:

- `docs/data_foundation/IBKR_CONNECTION_PROFILE.md`
- `docs/data_foundation/CLIENT_ID_POLICY.md`

`DATA-P04` adds the read-only IBKR API boundary under
`src/alpha_system/data/foundation/ibkr.py` and the `DataAccessMode` gate under
`src/alpha_system/data/foundation/sources.py`. The boundary stores only
registered historical read-only callables, exposes no generic IBKR client path,
and hard-refuses order, account, position, broker, paper, live, and trading
methods. It also adds:

- `docs/data_foundation/READ_ONLY_BOUNDARY.md`

`DATA-P05` adds the futures instrument master under
`src/alpha_system/data/foundation/instruments.py`, with the ES/NQ/RTY and
MES/MNQ/M2K contract-economics anchors in
`configs/data/futures_instrument_master.json`. The anchors are recorded as
to-be-verified economic anchors, not production-certified values, and are
validated with exact `Decimal` equality for tick value, tick size, and point
value. It also adds:

- `docs/data_foundation/INSTRUMENT_MASTER.md`

`DATA-P06` adds dated futures contract identity and contract-details provenance
under `src/alpha_system/data/foundation/instruments.py`. It defines
`FuturesContractRecord`, immutable content-addressed `ContractDetailsSnapshot`
records, and a pure contract-discovery scaffold that logs includeExpired
availability as discovered, not assumed. It also adds:

- `docs/data_foundation/CONTRACT_DISCOVERY.md`

`DATA-P07` adds historical request planning under
`src/alpha_system/data/foundation/requests.py`. It defines
`HistoricalRequestSpec`, `HistoricalRequestManifest`, deterministic
`manifest_hash` computation, and a lifecycle guard that blocks provider-pull
preflight without a valid manifest. It also adds the synthetic-only manifest
template `templates/data/synthetic_historical_request_manifest.json` and:

- `docs/data_foundation/REQUEST_SPEC_AND_MANIFEST.md`

`DATA-P08` adds pacing, chunk lifecycle, retry/error, and resume-ledger records
under `src/alpha_system/data/foundation/requests.py`. It defines
`RequestPacingPolicy`, `HistoricalChunkRecord`, `HistoricalPullLedger`,
`ProviderErrorRecord`, duplicate-request detection, `resume_token` resume
state, no-silent-gaps reconciliation, and immutable content-addressed
`raw_object_ref` validation. It also adds:

- `configs/data/request_pacing_policy_to_be_verified.json`
- `docs/data_foundation/PACING_AND_RESUME.md`

The prior `ALPHA_SYSTEM_V1`, `ASV1_RELEASE_HYGIENE`, and
`ALPHA_RESEARCH_GOVERNANCE_MVP` baselines are treated as complete. This campaign
builds on that local-first research harness by adding a read-only, provenance-rich
historical futures data foundation.

Safety boundaries are unchanged: IBKR remains read-only historical only;
clientId `101` and `102` remain fail-closed, the data namespace remains
`201-209`; no provider pull proceeds without manifest, pacing guard, and
resume ledger; no broker, order, account, paper, live, or real-time scope is
introduced; real data is local-only via `ALPHA_DATA_ROOT`; no raw or heavy
artifact commits, no local DB commits, explicit staging only, and no alpha,
profitability, tradability, or production-readiness claims.

## Data Foundation Docs

The data-foundation docs root currently includes:

- `docs/data_foundation/README.md`
- `docs/data_foundation/DATA_FOUNDATION_OVERVIEW.md`
- `docs/data_foundation/NAMING.md`
- `docs/data_foundation/DATA_SOURCE_PROFILE.md`
- `docs/data_foundation/LOCAL_DATA_ROOT_POLICY.md`
- `docs/data_foundation/IBKR_CONNECTION_PROFILE.md`
- `docs/data_foundation/CLIENT_ID_POLICY.md`
- `docs/data_foundation/READ_ONLY_BOUNDARY.md`
- `docs/data_foundation/INSTRUMENT_MASTER.md`
- `docs/data_foundation/CONTRACT_DISCOVERY.md`
- `docs/data_foundation/REQUEST_SPEC_AND_MANIFEST.md`
- `docs/data_foundation/PACING_AND_RESUME.md`

These docs describe the read-only data truth layer, campaign hard rules,
data-foundation object list, lifecycle state model, prohibited MVP states, IBKR
read-only posture, canonical object names, ID prefixes, module names,
file-naming conventions, directory layout, `DataSourceProfile`,
`LocalDataRootPolicy`, `IBKRConnectionProfile`, `IBKRClientIdPolicy`,
`IBKRReadOnlyApiBoundary`, `DataAccessMode`, `InstrumentMasterRecord`,
contract-economics anchors, `FuturesContractRecord`,
`ContractDetailsSnapshot`, contract-discovery availability logging, and the
`HistoricalRequestSpec` / `HistoricalRequestManifest` planning records,
`manifest_hash`, the no-manifest-no-pull block, `RequestPacingPolicy`,
`HistoricalChunkRecord`, `HistoricalPullLedger`, `ProviderErrorRecord`,
duplicate-request detection, retry/backoff classification, `resume_token`, the
no-silent-gaps and no-raw-overwrite guards, and the `ALPHA_DATA_ROOT` local-only
data-root pointer. Field-level acceptance rules, risks, and operator procedures
remain in the campaign contract bundle.

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
