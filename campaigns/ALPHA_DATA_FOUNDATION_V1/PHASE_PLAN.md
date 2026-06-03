# ALPHA_DATA_FOUNDATION_V1 Phase Plan

## Purpose

This phase plan is the human-readable, phase-by-phase contract for the
`ALPHA_DATA_FOUNDATION_V1` campaign. It decomposes the read-only real-market-data truth
layer for AI alpha research into 25 Workflow 2 phases (`DATA-P00` … `DATA-P24`). Most
phases are in the **YELLOW** lane; the two authorized external-pull phases (`DATA-P22`,
`DATA-P23`) are **RED**.

This file is authoritative for human reading. `campaign.yaml` is authoritative for machine
execution. Phase IDs, names, lanes, dependencies, checks, allowed/forbidden paths, and
artifact policy in this file must match `campaign.yaml` exactly. If they diverge, Ralph
must STOP and the contract must be repaired before execution continues.

This campaign builds the data-foundation layer **on top of** the completed
`ALPHA_SYSTEM_V1`, `ASV1_RELEASE_HYGIENE`, and `ALPHA_RESEARCH_GOVERNANCE_MVP` baselines.
It admits real historical futures data only as controlled, versioned, provenance-labeled,
read-only research data. It does not search for alpha, research factors or labels, run
strategies, or touch broker, order, account, paper, or live trading. IBKR is a bootstrap
historical data source only. See `GOAL.md` for strategic framing and `ACCEPTANCE.md` for
done criteria.

## Campaign Invariants

The following invariants hold across every phase and must never be violated:

1. **IBKR is read-only historical data only** — never broker, order, account, paper, or
   live. The data module must not be able to place an order, query positions, or touch
   account-trading paths.
2. **clientId `101`/`102` fail closed.** These are reserved for paper/live separation and
   are a hard-block, not a warning. The data namespace is `201–209`, default `201`
   (`ES=201`, `NQ=202`, `RTY=203`); collisions fail closed.
3. **No provider pull without a manifest, pacing guard, and resume ledger.** A missing
   manifest blocks any provider pull; a missing pacing guard blocks a pull; a missing
   local-data-root policy blocks raw writes.
4. **No silent gaps.** Coverage and quality reports fail closed on gaps, timestamp
   defects, session/roll defects, or incomplete chunks.
5. **Continuous futures are never dated-contract truth.** Provider-continuous (`CONTFUT`)
   history is labeled `provider_continuous`, `non_orderable`, `not_dated_contract_truth`,
   and `research_diagnostics_only`. Continuous, dated, stitched, adjusted, and unadjusted
   series stay explicitly separate.
6. **Canonical bars carry `available_ts`** and never conflate `event_ts`, `bar_start_ts`,
   `bar_end_ts`, `available_ts`, and `ingested_at`. A missing `available_ts` blocks
   canonicalization.
7. **No real-data pull runs in CI.** External IBKR calls require RED-lane authorization
   plus data-pull authorization env and never execute in CI.
8. **Explicit staging only.** `git add .` and `git add -A` are forbidden; no force push.
9. **No raw/canonical/provider/account/heavy/db artifacts committed.** Real market data,
   provider responses, account info, parquet/feather/arrow, local DBs, logs, caches, and
   `runs/**` are local-only.
10. **No alpha/factor/label/strategy scope.** No alpha search, feature/label research,
    strategy optimization, portfolio allocation, ML/DL, or L2 replay is introduced.
11. **No broker/order/account/paper/live scope** is introduced in any lane.
12. **No unsupported claims.** No alpha/profitability/tradability/production-readiness
    claims anywhere; no "data fully pulled" or "quality accepted" claim except when
    describing future acceptance criteria.

## Global Phase Rules

### Workflow Rules

* Each phase runs as a fresh Workflow 2 iteration under the strict state machine:
  `RUN_INIT → CAMPAIGN_LOAD → PHASE_SELECT → SPEC_GENERATE → SPEC_VALIDATE → WORKTREE_CREATE → CODEX_EXECUTE → CHECKS_RUN → HANDOFF_VALIDATE → CLAUDE_REVIEW → VERDICT_PARSE → PR_CREATE → CI_WAIT → MERGE_GATE → MERGE → DONE_CHECK → NEXT_PHASE → CAMPAIGN_DONE_CHECK → RUN_SUMMARY`.
* Ralph owns state transitions, STOP checks, validation orchestration, review routing,
  verdict parsing, PR/CI/merge gates, bounded repair routing, done-checks, and run
  summaries.
* Codex executes the generated spec, makes only scoped in-spec repairs, runs only
  authorized checks for the phase, and writes truthful handoffs.
* Claude Opus 4.8 xhigh is the fresh semantic reviewer for every YELLOW and RED phase.
  Claude Sonnet 4.6 supports source-map, verifier, and mechanical audit work.

### Repo Path Rules

* The active repo and all Workflow 2 worktrees must run under `~/projects/alpha_system`
  on the WSL2 Linux filesystem.
* `/mnt/c`, `/mnt/d`, `/mnt/e`, OneDrive, Dropbox, Google Drive, Windows-synced folders,
  network drives, and temp directories are forbidden active worktree locations.

### Git Rules

* Explicit staging only. `git add .` and `git add -A` are forbidden.
* No force push.
* A commit-eligible handoff is required per phase under
  `handoffs/ALPHA_DATA_FOUNDATION_V1/<PHASE_ID>.md`.
* Before any merge-gate evaluation, the staged set must contain no `runs/` path and no
  forbidden data/provider/account/DB/cache/log/heavy-artifact path. `git ls-files runs`
  must return empty.

### Artifact Rules

* Commit-eligible: source code, configs, schemas, docs, tests, tiny synthetic fixtures
  (`tests/fixtures/**`), templates, handoffs, reviews, curated summaries, and sample
  manifests built from fake/synthetic data only.
* Never commit: `data/raw/**`, `data/canonical/**`, `data/factors/**`, `data/labels/**`,
  `data/cache/**`, `metadata/*.sqlite`/`*.db`/`*.db-journal`/`*.wal`,
  `*.parquet`/`*.arrow`/`*.feather` (outside documented tiny fixtures), `*.pkl`/`*.npy`,
  logs, caches, provider responses, account info, IBKR logs, credentials, `runs/**`, and
  generated heavy artifacts.
* Raw and canonical real market data are local-only. The suggested data root is outside
  the repo (e.g. `~/alpha_data/alpha_system`) or configured via `ALPHA_DATA_ROOT`.
* `runs/**` is local-only runtime state. Run-local `handoff.md`, `review.md`,
  `verdict.json`, `checks.json`, and `repair_attempts/` are never staged or committed;
  commit-eligible handoffs live under `handoffs/ALPHA_DATA_FOUNDATION_V1/**` and review
  artifacts under `reviews/ALPHA_DATA_FOUNDATION_V1/**`.

### Domain Boundary Rules

* The data package (`src/alpha_system/data/**`) is **read-only**. It pulls and curates
  historical data; it must never place orders, query positions, or import order/account
  trading APIs. An order-method kill switch enforces this at the boundary.
* The data module reads and writes only the local data root via `ALPHA_DATA_ROOT`. It does
  not write into the repository tree for real data and does not sync to cloud paths.
* External IBKR calls are gated by `DataAccessMode` and require RED-lane authorization
  plus `ALPHA_DATA_PULL_AUTHORIZED` and `ALPHA_ALLOW_EXTERNAL_IBKR`. No external call runs
  in CI.
* The dataset-version registry persists data-foundation objects through the existing local
  persistence layer without committing the database.

### Non-Negotiable Scope Rules

This campaign must not introduce: real alpha search, factor research, label research,
strategy optimization, portfolio allocation, an Agent Factory, a Feature/Label Foundation,
Futures Core Alpha, an AlphaBook, ML/DL, L1 live quotes, L2 depth, MBO, order-book replay,
tick data, an execution simulator, broker connectivity, order placement, account trading,
position polling, paper trading, live trading, a real-time signal loop, a production
execution adapter, or any alpha/profitability/tradability/production-readiness claim.

### Review Rules

* Every YELLOW and RED phase requires fresh Claude Opus review with a `verdict.json`.
* Merge requires a `PASS` or `PASS_WITH_WARNINGS` verdict. `REWORK`, `BLOCKED`, and `FAIL`
  block merge.
* Review must verify phase-scope compliance, data-foundation object completeness,
  fail-closed validation, clientId `101`/`102` hard-block, read-only boundary and
  order-method kill switch, manifest + pacing guard + resume ledger, no silent gaps,
  continuous-not-dated-truth provenance, canonical `available_ts` and distinct timestamp
  fields, dataset version + quality + coverage where required, artifact policy, absence of
  broker/live/paper/order/account scope, absence of alpha/profitability/tradability claims,
  no test weakening, handoff completeness, and semantic done criteria.

### Repair Rules

* Bounded repair loop with `max_repair_attempts = 3`, tracked under
  `runs/<run_id>/phases/<phase_id>/repair_attempts/`.
* Codex repairs only valid in-scope review findings. Contradictory scope, repeated
  failures, missing authorization, or impossible validation route to a truthful `BLOCKED`
  handoff. Fake completion is forbidden.
* RED phases have `automatic_repair = false`; repair routing for RED requires re-armed
  authorization and human awareness.

### Validation Rules

* Run the narrowest meaningful test first, then broaden when shared behavior changes.
* Record any skipped check with its exact command, failure, and reason in the handoff.
* Default validation commands: `python tools/verify.py --smoke`, targeted
  `python -m pytest tests/unit/data -q`, plus phase-specific checks and the artifact
  audit (`git ls-files runs`, `find data`/`find metadata`/`find artifacts` audits where
  the phase requires them).

## Phase Table Summary

| Phase ID  | Phase Name                                            |   Lane | Dependencies                                                          | Review | Auto PR | Auto Merge |
| --------- | ----------------------------------------------------- | -----: | -------------------------------------------------------------------- | -----: | ------: | ---------: |
| DATA-P00  | Data Foundation Campaign Bootstrap                    | YELLOW | none                                                                 |    yes |     yes |        yes |
| DATA-P01  | Data Package Skeleton and Naming                      | YELLOW | DATA-P00                                                             |    yes |     yes |        yes |
| DATA-P02  | Data Source Profiles and Local Data Root Policy       | YELLOW | DATA-P01                                                             |    yes |     yes |        yes |
| DATA-P03  | IBKR Connection Profile and Client ID Guard           | YELLOW | DATA-P02                                                             |    yes |     yes |        yes |
| DATA-P04  | Read-Only API Boundary and Order-Method Kill Switch   | YELLOW | DATA-P03                                                             |    yes |     yes |        yes |
| DATA-P05  | Futures Instrument Master and Contract Economics      | YELLOW | DATA-P02                                                             |    yes |     yes |        yes |
| DATA-P06  | Contract Details Snapshot and Contract Discovery      | YELLOW | DATA-P03, DATA-P05                                                   |    yes |     yes |        yes |
| DATA-P07  | Historical Request Spec and Manifest                  | YELLOW | DATA-P03, DATA-P06                                                   |    yes |     yes |        yes |
| DATA-P08  | Pacing, Chunking, Retry, and Resume Ledger            | YELLOW | DATA-P07                                                             |    yes |     yes |        yes |
| DATA-P09  | Raw Local Data Lake Layout                            | YELLOW | DATA-P02, DATA-P08                                                   |    yes |     yes |        yes |
| DATA-P10  | ES/NQ/RTY Main Batch Pull Plan                        | YELLOW | DATA-P07, DATA-P08                                                   |    yes |     yes |        yes |
| DATA-P11  | Continuous Futures vs Dated Futures Provenance        | YELLOW | DATA-P06, DATA-P10                                                   |    yes |     yes |        yes |
| DATA-P12  | Session Templates and Trading Calendar                | YELLOW | DATA-P05                                                             |    yes |     yes |        yes |
| DATA-P13  | Roll Policy and Roll Calendar                         | YELLOW | DATA-P05, DATA-P06, DATA-P12                                         |    yes |     yes |        yes |
| DATA-P14  | Parser and Parsed Bar Records                         | YELLOW | DATA-P09                                                             |    yes |     yes |        yes |
| DATA-P15  | Canonical 1m Bar Contract                             | YELLOW | DATA-P12, DATA-P14                                                   |    yes |     yes |        yes |
| DATA-P16  | Data Quality Checks and Coverage Reports              | YELLOW | DATA-P15                                                             |    yes |     yes |        yes |
| DATA-P17  | Dataset Version Registry Integration                  | YELLOW | DATA-P16                                                             |    yes |     yes |        yes |
| DATA-P18  | Dataset Partition Plan and Locked-Test Metadata       | YELLOW | DATA-P17                                                             |    yes |     yes |        yes |
| DATA-P19  | Micro Batch Policy for MES/MNQ/M2K                    | YELLOW | DATA-P05, DATA-P10                                                   |    yes |     yes |        yes |
| DATA-P20  | Optional BID_ASK / Spread Proxy Pilot Plan            | YELLOW | DATA-P08, DATA-P16                                                   |    yes |     yes |        yes |
| DATA-P21  | Synthetic IBKR Fixture Tests                          | YELLOW | DATA-P03, DATA-P05, DATA-P06, DATA-P07, DATA-P08, DATA-P09, DATA-P14, DATA-P15, DATA-P16, DATA-P17 | yes | yes | yes |
| DATA-P22  | Small Authorized IBKR Smoke Pull                      |    RED | DATA-P21                                                             |    yes |     yes |     **no** |
| DATA-P23  | Local Backfill Runbook and Resume Drill               |    RED | DATA-P22                                                             |    yes |     yes |     **no** |
| DATA-P24  | End-to-End Data Foundation Dry Run and Closeout       | YELLOW | DATA-P23                                                             |    yes |     yes |        yes |

Auto Merge is `yes` for every YELLOW phase after a passing review and clean gates. Auto
Merge is **no** for the RED phases (`DATA-P22`, `DATA-P23`): they auto-PR when authorized
but never auto-merge.

## Acceptance Gate Summary

Every phase belongs to exactly one acceptance gate. Gates have no gaps and no overlaps.

| Gate | Phases | Exit Requirement |
| ---- | ------ | ---------------- |
| `campaign_bootstrap` | DATA-P00 … DATA-P02 | Campaign control files present, no campaign-local `ACTIVE_CAMPAIGN.md`, data package imports, `DataSourceProfile` and `LocalDataRootPolicy` present, handoffs/reviews present, artifact audit clean, no forbidden scope or claims |
| `ibkr_read_only_boundary` | DATA-P03 … DATA-P04 | IBKR connection profile present; clientId `101`/`102` hard-blocked; default `201` and namespace `201–209` enforced; connection-doctor scaffold present; read-only boundary and order-method kill switch present; order API not reachable through the data module |
| `futures_contract_master` | DATA-P05 … DATA-P06 | Instrument master present; contract economics anchors encoded and verified (`tick_value = tick_size × point_value` where applicable); contract-details snapshot and contract discovery present; include-expired availability logged not assumed |
| `request_and_storage` | DATA-P07 … DATA-P10 | Request spec + manifest present; no provider pull without manifest; pacing guard, chunking/retry/resume ledger, provider-error ledger, and duplicate-request detection present; raw data lake immutable / no overwrite; mini and micro batches separate; sample manifests synthetic only |
| `provenance_sessions_rolls` | DATA-P11 … DATA-P13 | Continuous-vs-dated provenance separate; continuous not treated as dated truth; dated-truth availability logged; session templates, trading calendar, DST/early-close handling, roll policy, and roll calendar present; adjusted-vs-unadjusted explicit |
| `canonicalization_quality_versioning` | DATA-P14 … DATA-P18 | Parsed bars and canonical bar contract present; canonical bars carry `available_ts`; `event_ts`/`bar_end_ts`/`available_ts` not conflated; timestamp-semantics policy present; quality and coverage reports present with silent gaps failing closed; dataset-version registry requires quality + coverage + manifest; partition plan and locked-test metadata rules present |
| `secondary_data_tracks` | DATA-P19 … DATA-P20 | Micro-batch policy present and separate from the mini batch; BID_ASK pilot marked optional and bounded with heavier pacing/storage acknowledged |
| `validation_and_authorized_smoke` | DATA-P21 … DATA-P23 | Synthetic IBKR fixture tests present; connector/planner/parser/quality tested on synthetic fixtures; RED phases require explicit authorization, never run in CI, commit no data artifacts; smoke pull local-only; backfill runbook + resume drill present; resume-after-interruption demonstrated locally |
| `closeout` | DATA-P24 | End-to-end dry run passes or truthful `BLOCKED`; acceptance audit passes; semantic done-check passes; closeout doc present with final verdict (`COMPLETE`, `COMPLETE_WITH_WARNINGS`, or `BLOCKED`); next-campaign readiness recorded |

---

# Detailed Phase Specs

---

## DATA-P00 — Data Foundation Campaign Bootstrap

### Phase ID
`DATA-P00`

### Phase Name
Data Foundation Campaign Bootstrap

### Lane
YELLOW

### Dependencies
None.

### Purpose
Create the implementation entry point for the data-foundation campaign: the data-foundation
docs root and overview, and the commit-eligible handoff, while confirming the campaign
contract bundle is present and consistent. This phase makes the repository ready to execute
the remaining data phases.

### Scope
* Confirm and reference the campaign contract bundle under `campaigns/ALPHA_DATA_FOUNDATION_V1/`.
* Create `docs/data_foundation/README.md` and `docs/data_foundation/DATA_FOUNDATION_OVERVIEW.md`
  describing the read-only data truth layer, the hard rules, the object list, the data
  lifecycle state model, and the IBKR read-only posture at a high level.
* Create the commit-eligible handoff `handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P00.md`.
* Ensure `ACTIVE_CAMPAIGN.md` points to this campaign.

### Non-Goals
* Do not create data package source under `src/alpha_system/data/**`.
* Do not add tests, configs, templates, or any IBKR code.
* Do not create a campaign-local `ACTIVE_CAMPAIGN.md`.

### Expected Files / Directories
* `docs/data_foundation/README.md`
* `docs/data_foundation/DATA_FOUNDATION_OVERVIEW.md`
* `handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P00.md`

### Forbidden Changes
* No `src/alpha_system/data/ibkr/**`.
* No `tests/**`.
* No `runs/**` staged or committed; no raw/canonical data, heavy artifacts, or local DBs.
* No broker/live/paper/order-routing scope.
* No alpha/profitability/tradability claims.

### Validation Commands
```bash
git status --short
test -f ACTIVE_CAMPAIGN.md
test -f campaigns/ALPHA_DATA_FOUNDATION_V1/GOAL.md
test -f campaigns/ALPHA_DATA_FOUNDATION_V1/PHASE_PLAN.md
test -f campaigns/ALPHA_DATA_FOUNDATION_V1/campaign.yaml
test -f campaigns/ALPHA_DATA_FOUNDATION_V1/ACCEPTANCE.md
test -f campaigns/ALPHA_DATA_FOUNDATION_V1/RISK_REGISTER.md
test -f campaigns/ALPHA_DATA_FOUNDATION_V1/RUNBOOK.md
test '!' -f campaigns/ALPHA_DATA_FOUNDATION_V1/ACTIVE_CAMPAIGN.md
test -f handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P00.md
grep -q "ALPHA_DATA_FOUNDATION_V1" ACTIVE_CAMPAIGN.md
python tools/verify.py --smoke
git ls-files runs
```

### Artifact Policy
Commit only campaign files, data-foundation overview docs, and the commit-eligible handoff.
Never commit `runs/**`, raw data, canonical data, heavy artifacts, or local DB files.
Explicit staging only.

### Done Criteria
* Data-foundation docs root exists with an overview of the data truth layer and lifecycle.
* `ACTIVE_CAMPAIGN.md` points to `ALPHA_DATA_FOUNDATION_V1`.
* No campaign-local `ACTIVE_CAMPAIGN.md` exists.
* Commit-eligible handoff exists and records validation results.
* No data source, tests, or forbidden scope introduced.

### Handoff Requirements
`handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P00.md` must summarize created docs, exact staged
files, validation results, artifact-policy confirmation, explicit-staging confirmation, and
statements that no source/tests/forbidden scope/claims were added.

### Review Requirements
Claude Opus review required. Must verify contract-bundle consistency, no campaign-local
pointer, no source/test scope creep, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph only when checks pass, handoff validates, verdict is
`PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden paths are staged, no STOP
file, CI passes if configured, and the semantic done-check passes.

---

## DATA-P01 — Data Package Skeleton and Naming

### Phase ID
`DATA-P01`

### Phase Name
Data Package Skeleton and Naming

### Lane
YELLOW

### Dependencies
`DATA-P00`.

### Purpose
Establish the importable `alpha_system.data` package skeleton, the test root, the
configs/templates roots, and the canonical naming conventions for all data-foundation
objects, IDs, files, and directories.

### Scope
* Create `src/alpha_system/data/__init__.py` and stub module placeholders for the object
  families (sources, IBKR connection, requests, ledgers, raw/parsed/canonical bars,
  instruments/contracts, sessions/calendar, rolls, dataset versions, quality/coverage,
  partitions, access modes).
* Create `tests/unit/data/` with a package-import smoke test.
* Create `configs/data/` and `templates/data/` roots with documented placeholders.
* Create `docs/data_foundation/NAMING.md` defining canonical object names, ID prefixes,
  file naming, and directory layout.

### Non-Goals
* Do not implement object validation logic yet.
* Do not integrate with the registry/persistence layer; do not add IBKR connection code.

### Expected Files / Directories
* `src/alpha_system/data/**` (skeleton modules)
* `tests/unit/data/test_package_skeleton.py`
* `configs/data/`, `templates/data/` (with `.gitkeep`/`README.md`)
* `docs/data_foundation/NAMING.md`

### Forbidden Changes
* No `src/alpha_system/execution/broker/**`, `live/**`, or `paper/**`.
* No `data/raw/**` or `data/canonical/**` writes; no `metadata/*.sqlite`; no `artifacts/**`;
  no `*.parquet`.

### Validation Commands
```bash
git status --short
python -c "import alpha_system.data"
python tools/verify.py --smoke
python -m pytest tests/unit/data -q
test -f docs/data_foundation/NAMING.md
git ls-files runs
```

### Artifact Policy
Commit only the data package skeleton, tests, docs, and tiny synthetic fixtures. Never
commit `runs/**`, raw data, canonical data, heavy artifacts, or local DB files. Explicit
staging only.

### Done Criteria
* `alpha_system.data` imports cleanly.
* Package skeleton and test root exist with a passing import smoke test.
* Canonical naming documented.
* No object logic, registry integration, or forbidden scope introduced.

### Handoff Requirements
Summarize the skeleton, naming conventions, exact staged files, and validation results.

### Review Requirements
Claude Opus review must verify clean package boundaries, naming clarity, and no scope creep.

### Auto-Merge Eligibility
Standard YELLOW gates (see DATA-P00).

---

## DATA-P02 — Data Source Profiles and Local Data Root Policy

### Phase ID
`DATA-P02`

### Phase Name
Data Source Profiles and Local Data Root Policy

### Lane
YELLOW

### Dependencies
`DATA-P01`.

### Purpose
Define the `DataSourceProfile` (provider description and allowed/forbidden usage modes) and
the `LocalDataRootPolicy` that pins data to a local, ignored, outside-repo root via
`ALPHA_DATA_ROOT` and prevents accidental commits and unsafe data locations.

### Scope
* Implement `DataSourceProfile` with required fields (`source_id`, `provider_name`,
  `provider_type`, `allowed_modes`, `forbidden_modes`, `requires_authorization`,
  `market_data_permissions_note`, `created_at`), and validate fail-closed.
* Implement `LocalDataRootPolicy` with required fields (`data_root`, `must_be_local`,
  `must_be_ignored`, `forbidden_repo_paths`, `allowed_subdirs`, `max_file_policy`), reading
  `ALPHA_DATA_ROOT`, and rejecting forbidden repo paths and synced/cloud locations.
* Create `docs/data_foundation/DATA_SOURCE_PROFILE.md` and
  `docs/data_foundation/LOCAL_DATA_ROOT_POLICY.md`.

### Non-Goals
* Do not imply broker readiness, execution permission, or data completeness.
* Do not connect to IBKR or write any real data.

### Expected Files / Directories
* `src/alpha_system/data/**` (`DataSourceProfile`, `LocalDataRootPolicy`)
* `tests/unit/data/**`, `tests/fixtures/data/**`
* `configs/data/**`
* `docs/data_foundation/DATA_SOURCE_PROFILE.md`, `docs/data_foundation/LOCAL_DATA_ROOT_POLICY.md`

### Forbidden Changes
* No `src/alpha_system/execution/broker/**` or `live/**`; no real data writes; no
  `metadata/*.sqlite`; no `artifacts/**`; no `*.parquet`.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/data -q
test -f docs/data_foundation/DATA_SOURCE_PROFILE.md
test -f docs/data_foundation/LOCAL_DATA_ROOT_POLICY.md
git ls-files runs
```

### Artifact Policy
Commit only `DataSourceProfile` code, `LocalDataRootPolicy` code, tests, docs, and tiny
synthetic fixtures. Never commit `runs/**`, raw data, canonical data, heavy artifacts, or
local DB files. Explicit staging only.

### Done Criteria
* `DataSourceProfile` and `LocalDataRootPolicy` exist with required fields and validate
  fail-closed.
* The data-root policy pins data to an ignored, local, outside-repo root and rejects
  forbidden repo and synced paths.
* No broker readiness or completeness implied.

### Handoff Requirements
Document the source profile, the data-root policy, the `ALPHA_DATA_ROOT` semantics, and
validation results.

### Review Requirements
Claude Opus review must confirm fail-closed validation and that the data-root policy blocks
unsafe/committable locations.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## DATA-P03 — IBKR Connection Profile and Client ID Guard

### Phase ID
`DATA-P03`

### Phase Name
IBKR Connection Profile and Client ID Guard

### Lane
YELLOW

### Dependencies
`DATA-P02`.

### Purpose
Define the `IBKRConnectionProfile` and `IBKRClientIdPolicy` and enforce the clientId safety
policy: clientId `101`/`102` fail closed, the data namespace is `201–209` (default `201`),
and a connection-doctor scaffold reports host/port reachability for Windows/WSL2.

### Scope
* Implement `IBKRConnectionProfile` with required fields (`host`, `port`, `client_id`,
  `read_only_mode`, `environment`, `connection_timeout`, `doctor_status`, `validated_at`),
  defaulting to `127.0.0.1:4002`, `client_id 201`, `read_only_mode = true`.
* Implement `IBKRClientIdPolicy` with required fields (`forbidden_client_ids`,
  `allowed_range`, `default_client_id`, `worker_client_ids`, `collision_policy`) enforcing
  fail-closed rejection of `101`/`102`, the `201–209` range, default `201`, and worker IDs
  (`ES=201`, `NQ=202`, `RTY=203`) with collision fail-closed.
* Implement a connection-doctor scaffold (no live call required) that validates and reports
  host/port reachability and clientId rather than silently retrying.
* Create `docs/data_foundation/IBKR_CONNECTION_PROFILE.md` and
  `docs/data_foundation/CLIENT_ID_POLICY.md`.

### Non-Goals
* Do not imply account access, order access, or live-feed readiness.
* Do not perform an external IBKR call (RED-only, later).

### Expected Files / Directories
* `src/alpha_system/data/**` (`IBKRConnectionProfile`, `IBKRClientIdPolicy`, connection-doctor scaffold)
* `tests/unit/data/**`, `tests/fixtures/data/**`
* `configs/data/**`
* `docs/data_foundation/IBKR_CONNECTION_PROFILE.md`, `docs/data_foundation/CLIENT_ID_POLICY.md`

### Forbidden Changes
* No `src/alpha_system/execution/broker/**` or `live/**`; no order/account API surface; no
  real data writes; no `metadata/*.sqlite`; no `artifacts/**`; no `*.parquet`.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/data -q
test -f docs/data_foundation/IBKR_CONNECTION_PROFILE.md
test -f docs/data_foundation/CLIENT_ID_POLICY.md
git ls-files runs
```

### Artifact Policy
Commit only `IBKRConnectionProfile` code, `IBKRClientIdPolicy` code, connection-doctor
scaffold, tests, docs, and tiny synthetic fixtures. Never commit `runs/**`, raw data,
canonical data, heavy artifacts, or local DB files. Explicit staging only.

### Done Criteria
* `IBKRConnectionProfile` and `IBKRClientIdPolicy` exist and validate fail-closed.
* clientId `101`/`102` are hard-blocked; default is `201`; the `201–209` namespace and
  worker IDs are enforced; collisions fail closed.
* The connection-doctor scaffold reports reachability without silent retry.
* No account/order/live readiness implied.

### Handoff Requirements
Document the connection profile defaults, the clientId guard behavior, the connection-doctor
scaffold, and validation results.

### Review Requirements
Claude Opus review must confirm `101`/`102` are hard-blocked (not warnings), the namespace
is enforced, and no order/account surface is reachable.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## DATA-P04 — Read-Only API Boundary and Order-Method Kill Switch

### Phase ID
`DATA-P04`

### Phase Name
Read-Only API Boundary and Order-Method Kill Switch

### Lane
YELLOW

### Dependencies
`DATA-P03`.

### Purpose
Establish the read-only IBKR API boundary and an order-method kill switch so the data module
can only use the historical/read-only surface and can never place an order, query positions,
or touch account-trading paths. Defines `DataAccessMode` as the mode gate.

### Scope
* Implement the read-only boundary that exposes only historical/read-only API calls and a
  kill switch that blocks or refuses any order/account method.
* Implement `DataAccessMode` with required fields (`mode`, `requires_env`,
  `allows_external_api`, `allows_raw_write`, `allows_canonical_write`, `ci_allowed`) gating
  dry-run, synthetic, smoke, and authorized-pull modes; CI is never allowed external calls.
* Create `docs/data_foundation/READ_ONLY_BOUNDARY.md`.
* Add read-only boundary tests asserting that order/account methods are unreachable.

### Non-Goals
* Do not implement any order/account method; do not perform external calls here.
* Do not imply tradability or execution permission.

### Expected Files / Directories
* `src/alpha_system/data/**` (read-only boundary, order-method kill switch, `DataAccessMode`)
* `tests/unit/data/**`, `tests/fixtures/data/**`
* `docs/data_foundation/READ_ONLY_BOUNDARY.md`

### Forbidden Changes
* No `src/alpha_system/execution/broker/**`, `live/**`, `paper/**`, or `order_router*`; no
  real data writes; no `metadata/*.sqlite`; no `artifacts/**`; no `*.parquet`.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/data -q
test -f docs/data_foundation/READ_ONLY_BOUNDARY.md
git ls-files runs
```

### Artifact Policy
Commit only read-only boundary code, the order-method kill switch, tests, docs, and tiny
synthetic fixtures. Never commit `runs/**`, raw data, canonical data, heavy artifacts, or
local DB files. Explicit staging only.

### Done Criteria
* The read-only boundary exposes only historical/read-only calls.
* The order-method kill switch makes order/account methods unreachable through the data
  module, with tests proving it.
* `DataAccessMode` gates modes and forbids external calls in CI.

### Handoff Requirements
Document the boundary, the kill switch, the access-mode gate, the unreachable-order proof,
and validation results.

### Review Requirements
Claude Opus review must confirm the order API is not reachable through the data module and
the kill switch genuinely blocks order/account methods.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## DATA-P05 — Futures Instrument Master and Contract Economics

### Phase ID
`DATA-P05`

### Phase Name
Futures Instrument Master and Contract Economics

### Lane
YELLOW

### Dependencies
`DATA-P02`.

### Purpose
Define the `InstrumentMasterRecord` root-level futures definitions and verified contract
economics for ES/NQ/RTY and MES/MNQ/M2K, with `tick_value = tick_size × point_value` where
applicable.

### Scope
* Implement `InstrumentMasterRecord` with required fields (`root_symbol`, `ib_symbol`,
  `exchange`, `currency`, `asset_class`, `sec_type`, `point_value`, `tick_size`,
  `tick_value`, `multiplier`, `timezone`, `session_template_id`, `roll_policy_id`, `source`,
  `source_retrieved_at`), and validate fail-closed.
* Encode the contract economics anchors (ES, NQ, RTY, MES, MNQ, M2K) and verify
  `tick_value = tick_size × point_value` where applicable; treat anchors as to-be-verified,
  not production-certified.
* Create `docs/data_foundation/INSTRUMENT_MASTER.md`.

### Non-Goals
* Do not imply that a current contract is selected.
* Do not imply tradability or execution sizing certification.

### Expected Files / Directories
* `src/alpha_system/data/**` (`InstrumentMasterRecord`, contract economics)
* `tests/unit/data/**`, `tests/fixtures/data/**`
* `configs/data/**`
* `docs/data_foundation/INSTRUMENT_MASTER.md`

### Forbidden Changes
* No `src/alpha_system/execution/broker/**` or `live/**`; no real data writes; no
  `metadata/*.sqlite`; no `artifacts/**`; no `*.parquet`.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/data -q
test -f docs/data_foundation/INSTRUMENT_MASTER.md
git ls-files runs
```

### Artifact Policy
Commit only `InstrumentMasterRecord` code, contract economics, tests, docs, and tiny
synthetic fixtures. Never commit `runs/**`, raw data, canonical data, heavy artifacts, or
local DB files. Explicit staging only.

### Done Criteria
* `InstrumentMasterRecord` exists with required fields and validates fail-closed.
* Contract economics anchors for ES/NQ/RTY/MES/MNQ/M2K are encoded and verified
  (`tick_value = tick_size × point_value` where applicable).
* No current-contract selection or tradability implied.

### Handoff Requirements
Document the instrument master, the verified economics anchors, the verification method, and
validation results.

### Review Requirements
Claude Opus review must confirm the economics relationship holds and anchors are marked
to-be-verified rather than certified.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## DATA-P06 — Contract Details Snapshot and Contract Discovery

### Phase ID
`DATA-P06`

### Phase Name
Contract Details Snapshot and Contract Discovery

### Lane
YELLOW

### Dependencies
`DATA-P03`, `DATA-P05`.

### Purpose
Define the `ContractDetailsSnapshot` (immutable snapshot of an IBKR contract-details
response) and `FuturesContractRecord` (dated-contract identity), plus a contract-discovery
scaffold that logs include-expired availability rather than assuming full history.

### Scope
* Implement `ContractDetailsSnapshot` with required fields (`snapshot_id`, `contract_id`,
  `raw_details_ref`, `normalized_fields`, `retrieved_at`, `client_id`, `source`, `hash`).
* Implement `FuturesContractRecord` with required fields (`contract_id`, `root_symbol`,
  `contract_month`, `ib_symbol`, `trading_class`, `con_id`,
  `last_trade_date_or_contract_month`, `expiration`, `multiplier`, `exchange`, `currency`,
  `include_expired_support_status`).
* Implement a contract-discovery scaffold (no live call) that records availability and
  logs `include_expired` support as discovered, not assumed.
* Create `docs/data_foundation/CONTRACT_DISCOVERY.md`.

### Non-Goals
* Do not claim full historical availability or CME economic finality unless reconciled.
* Do not perform an external IBKR call here (RED-only, later).

### Expected Files / Directories
* `src/alpha_system/data/**` (`ContractDetailsSnapshot`, `FuturesContractRecord`, discovery scaffold)
* `tests/unit/data/**`, `tests/fixtures/data/**`
* `docs/data_foundation/CONTRACT_DISCOVERY.md`

### Forbidden Changes
* No `src/alpha_system/execution/broker/**` or `live/**`; no real data/provider responses
  committed; no `metadata/*.sqlite`; no `artifacts/**`; no `*.parquet`.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/data -q
test -f docs/data_foundation/CONTRACT_DISCOVERY.md
git ls-files runs
```

### Artifact Policy
Commit only `ContractDetailsSnapshot` code, `FuturesContractRecord` code, the contract
discovery scaffold, tests, docs, and tiny synthetic fixtures. Never commit `runs/**`, raw
data, canonical data, provider responses, heavy artifacts, or local DB files. Explicit
staging only.

### Done Criteria
* `ContractDetailsSnapshot` and `FuturesContractRecord` exist with required fields and
  validate fail-closed.
* The discovery scaffold logs include-expired availability as discovered, not assumed.
* No full-history or CME-finality claim.

### Handoff Requirements
Document the snapshot, the dated-contract record, the availability-logging behavior, and
validation results.

### Review Requirements
Claude Opus review must confirm availability is logged not assumed and no provider response
is committed.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## DATA-P07 — Historical Request Spec and Manifest

### Phase ID
`DATA-P07`

### Phase Name
Historical Request Spec and Manifest

### Lane
YELLOW

### Dependencies
`DATA-P03`, `DATA-P06`.

### Purpose
Define the `HistoricalRequestSpec` (declarative request before any IBKR historical call) and
the `HistoricalRequestManifest` (full planned set of chunks and contracts), enforcing that no
provider pull may proceed without a validated manifest.

### Scope
* Implement `HistoricalRequestSpec` with required fields (`request_spec_id`, `source_id`,
  `symbol_root`, `contract_ref`, `sec_type`, `exchange`, `currency`, `bar_size`,
  `what_to_show`, `use_rth`, `duration`, `end_datetime_policy`, `start_ts`, `end_ts`,
  `chunk_policy`, `client_id`).
* Implement `HistoricalRequestManifest` with required fields (`manifest_id`, `batch_id`,
  `request_specs`, `chunk_count`, `expected_coverage`, `pacing_policy_id`, `data_root`,
  `created_by`, `created_at`, `manifest_hash`), and a manifest hash.
* Encode the lifecycle block: `NOT_REQUESTED → REQUEST_PLANNED` requires a request spec; a
  missing manifest blocks any provider pull.
* Provide a sample synthetic manifest built from fake data only.
* Create `docs/data_foundation/REQUEST_SPEC_AND_MANIFEST.md` and a manifest template under
  `templates/data/**`.

### Non-Goals
* Do not imply that data exists or that the request has been executed.
* Do not imply pull authorization from a manifest.

### Expected Files / Directories
* `src/alpha_system/data/**` (`HistoricalRequestSpec`, `HistoricalRequestManifest`)
* `tests/unit/data/**`, `tests/fixtures/data/**`
* `configs/data/**`, `templates/data/**` (sample synthetic manifest)
* `docs/data_foundation/REQUEST_SPEC_AND_MANIFEST.md`

### Forbidden Changes
* No `src/alpha_system/execution/broker/**` or `live/**`; no real data writes; no
  `metadata/*.sqlite`; no `artifacts/**`; no `*.parquet`.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/data -q
test -f docs/data_foundation/REQUEST_SPEC_AND_MANIFEST.md
git ls-files runs
```

### Artifact Policy
Commit only `HistoricalRequestSpec` code, `HistoricalRequestManifest` code, a sample
synthetic manifest, tests, docs, and tiny synthetic fixtures. Never commit `runs/**`, raw
data, canonical data, heavy artifacts, or local DB files. Explicit staging only.

### Done Criteria
* `HistoricalRequestSpec` and `HistoricalRequestManifest` exist with required fields and a
  manifest hash, and validate fail-closed.
* No provider pull is permitted without a validated manifest.
* The sample manifest uses synthetic data only and does not imply authorization.

### Handoff Requirements
Document the request spec, the manifest contract and hash, the no-manifest-no-pull block, and
validation results.

### Review Requirements
Claude Opus review must confirm the manifest is mandatory before any pull and the sample
manifest is synthetic.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## DATA-P08 — Pacing, Chunking, Retry, and Resume Ledger

### Phase ID
`DATA-P08`

### Phase Name
Pacing, Chunking, Retry, and Resume Ledger

### Lane
YELLOW

### Dependencies
`DATA-P07`.

### Purpose
Define conservative `RequestPacingPolicy`, per-chunk `HistoricalChunkRecord`, the
`HistoricalPullLedger` (audit and resume), and `ProviderErrorRecord`, so pulls are paced,
chunked, retried with backoff, resumable, and auditable with no silent gaps and no raw
overwrite.

### Scope
* Implement `RequestPacingPolicy` with required fields (`pacing_policy_id`,
  `min_seconds_between_identical_requests`, `max_requests_per_window`, `window_seconds`,
  `bid_ask_counts_double`, `backoff_policy`, `source`); naive loops forbidden, values
  configurable and to-be-verified.
* Implement `HistoricalChunkRecord` (`chunk_id`, `request_spec_id`, `symbol_root`,
  `contract_ref`, `start_ts`, `end_ts`, `status`, `attempt_count`, `provider_request_id`,
  `raw_object_ref`, `row_count`, `error_ref`, `retrieved_at`).
* Implement `HistoricalPullLedger` (`pull_id`, `manifest_id`, `chunk_records`, `started_at`,
  `finished_at`, `status`, `resume_token`, `coverage_summary`, `error_summary`) with a
  resume token and duplicate-request detection.
* Implement `ProviderErrorRecord` (`error_id`, `provider`, `request_id`, `chunk_id`,
  `error_code`, `error_message`, `retryable`, `attempt`, `timestamp`, `resolution`).
* Enforce: no silent gaps, no raw overwrite, retry with backoff, request-id tracking.
* Create `docs/data_foundation/PACING_AND_RESUME.md`.

### Non-Goals
* Do not perform any external IBKR call (RED-only, later).
* Do not imply that a dataset version is ready or that quality passed.

### Expected Files / Directories
* `src/alpha_system/data/**` (`RequestPacingPolicy`, `HistoricalChunkRecord`, `HistoricalPullLedger`, `ProviderErrorRecord`)
* `tests/unit/data/**`, `tests/fixtures/data/**`
* `configs/data/**`
* `docs/data_foundation/PACING_AND_RESUME.md`

### Forbidden Changes
* No `src/alpha_system/execution/broker/**` or `live/**`; no real data writes; no
  `metadata/*.sqlite`; no `artifacts/**`; no `*.parquet`.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/data -q
test -f docs/data_foundation/PACING_AND_RESUME.md
git ls-files runs
```

### Artifact Policy
Commit only `RequestPacingPolicy` code, `HistoricalChunkRecord` code, `HistoricalPullLedger`
code, `ProviderErrorRecord` code, tests, docs, and tiny synthetic fixtures. Never commit
`runs/**`, raw data, canonical data, heavy artifacts, or local DB files. Explicit staging
only.

### Done Criteria
* Pacing policy, chunk record, pull ledger (with resume token), and provider-error record
  exist and validate fail-closed.
* Duplicate-request detection, retry-with-backoff, no-silent-gaps, and no-raw-overwrite are
  enforced.
* Pacing values are configurable and marked to-be-verified.

### Handoff Requirements
Document the pacing/chunk/retry/resume design, the error ledger, the no-gap/no-overwrite
guarantees, and validation results.

### Review Requirements
Claude Opus review must confirm pacing is conservative/configurable, resume works, and gaps
fail closed.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## DATA-P09 — Raw Local Data Lake Layout

### Phase ID
`DATA-P09`

### Phase Name
Raw Local Data Lake Layout

### Lane
YELLOW

### Dependencies
`DATA-P02`, `DATA-P08`.

### Purpose
Define the `RawDataObject` (immutable, content-addressed local provider response) and the raw
local data-lake layout policy, keeping raw data local-only, immutable, manifest-linked, and
never overwritten or committed.

### Scope
* Implement `RawDataObject` with required fields (`raw_object_id`, `source`, `request_id`,
  `chunk_id`, `path`, `content_hash`, `schema_hint`, `retrieved_at`, `row_count`).
* Define the raw data-lake layout under `ALPHA_DATA_ROOT` (content-addressed or versioned,
  request-manifest linked, immutable, no overwrite), with the repo tree carrying only
  README/.gitkeep placeholders.
* Create `docs/data_foundation/RAW_DATA_LAKE.md`.
* Verify (via the `find data` audit) that no raw data file is committed.

### Non-Goals
* Do not imply canonical truth from raw objects.
* Do not perform an external pull or write real provider responses into the repo.

### Expected Files / Directories
* `src/alpha_system/data/**` (`RawDataObject`, raw data lake layout policy)
* `tests/unit/data/**`, `tests/fixtures/data/**`
* `configs/data/**`
* `docs/data_foundation/RAW_DATA_LAKE.md`

### Forbidden Changes
* No `src/alpha_system/execution/broker/**` or `live/**`; no `data/raw/**` or
  `data/canonical/**` commits; no provider responses; no `metadata/*.sqlite`; no
  `artifacts/**`; no `*.parquet`.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/data -q
test -f docs/data_foundation/RAW_DATA_LAKE.md
find data -type f '!' -name README.md '!' -name .gitkeep -print
git ls-files runs
```

### Artifact Policy
Commit only `RawDataObject` code, the raw data lake layout policy, tests, docs, and tiny
synthetic fixtures. Never commit `runs/**`, raw data, canonical data, provider responses,
heavy artifacts, or local DB files. Explicit staging only.

### Done Criteria
* `RawDataObject` exists with required fields including `content_hash`, and validates
  fail-closed.
* The raw lake layout is local-only, immutable, manifest-linked, and no-overwrite.
* The `find data` audit shows only README/.gitkeep in the repo tree.

### Handoff Requirements
Document the raw object, the lake layout, the immutability/no-overwrite guarantees, the
`find data` audit, and validation results.

### Review Requirements
Claude Opus review must confirm raw data is local-only/immutable and no data is committed.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## DATA-P10 — ES/NQ/RTY Main Batch Pull Plan

### Phase ID
`DATA-P10`

### Phase Name
ES/NQ/RTY Main Batch Pull Plan

### Lane
YELLOW

### Dependencies
`DATA-P07`, `DATA-P08`.

### Purpose
Define the `SymbolBatchPlan` and the ES/NQ/RTY mini main-batch pull plan over the modern
common panel (`2018-01-01 → present`, `1 min`, `TRADES`), with concurrency limits and a
hard separation from the micro batch.

### Scope
* Implement `SymbolBatchPlan` with required fields (`plan_id`, `mini_main`,
  `micro_secondary`, `max_concurrent_roots`, `do_not_mix_mini_and_micro_batches`),
  `max_concurrent_roots = 3`.
* Encode the mini main-batch plan for ES/NQ/RTY over the primary common panel and the
  clearly-labeled optional secondary panels (ES/NQ long, RTY transition QA, contract-truth),
  referencing the manifest and pacing policy.
* Provide a sample synthetic manifest for the mini batch (fake data only).
* Create `docs/data_foundation/MINI_BATCH_PLAN.md`.

### Non-Goals
* Do not mix mini and micro batches.
* Do not imply pull authorization or that data is pulled.

### Expected Files / Directories
* `src/alpha_system/data/**` (`SymbolBatchPlan`, mini batch pull plan)
* `tests/unit/data/**`, `tests/fixtures/data/**`
* `configs/data/**`
* `docs/data_foundation/MINI_BATCH_PLAN.md`

### Forbidden Changes
* No `src/alpha_system/execution/broker/**` or `live/**`; no real data writes; no
  `metadata/*.sqlite`; no `artifacts/**`; no `*.parquet`.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/data -q
test -f docs/data_foundation/MINI_BATCH_PLAN.md
git ls-files runs
```

### Artifact Policy
Commit only `SymbolBatchPlan` code, the mini batch pull plan, a sample synthetic manifest,
tests, docs, and tiny synthetic fixtures. Never commit `runs/**`, raw data, canonical data,
heavy artifacts, or local DB files. Explicit staging only.

### Done Criteria
* `SymbolBatchPlan` exists with required fields and `max_concurrent_roots = 3`, validating
  fail-closed.
* The ES/NQ/RTY mini batch plan and optional secondary panels are defined and separated from
  the micro batch.
* The sample manifest is synthetic; no pull authorization implied.

### Handoff Requirements
Document the batch plan, the panel windows, mini/micro separation, and validation results.

### Review Requirements
Claude Opus review must confirm mini/micro separation, the concurrency limit, and synthetic
sample manifests.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## DATA-P11 — Continuous Futures vs Dated Futures Provenance

### Phase ID
`DATA-P11`

### Phase Name
Continuous Futures vs Dated Futures Provenance

### Lane
YELLOW

### Dependencies
`DATA-P06`, `DATA-P10`.

### Purpose
Define the `ContinuousFuturesSeriesRecord` and `DatedFuturesSeriesRecord` and keep
provider-continuous (`CONTFUT`), dated-contract (`FUT`), stitched, adjusted, and unadjusted
series explicitly separate, ensuring continuous history is never treated as dated-contract
truth.

### Scope
* Implement `ContinuousFuturesSeriesRecord` with required fields (`series_id`, `root_symbol`,
  `provider`, `provenance_label`, `orderable`, `dated_truth`, `roll_adjustment_note`,
  `source_retrieved_at`), labeled `provider_continuous`, `non_orderable`,
  `not_dated_contract_truth`, `research_diagnostics_only`.
* Implement `DatedFuturesSeriesRecord` with required fields (`series_id`, `root_symbol`,
  `contract_universe`, `roll_policy_id`, `adjustment_method`, `availability_window`,
  `validation_status`), with availability logged not assumed and adjusted-vs-unadjusted
  explicit.
* Create `docs/data_foundation/PROVENANCE.md`.

### Non-Goals
* Do not treat continuous history as dated-contract truth or tradable roll.
* Do not claim full historical availability.

### Expected Files / Directories
* `src/alpha_system/data/**` (`ContinuousFuturesSeriesRecord`, `DatedFuturesSeriesRecord`, provenance separation)
* `tests/unit/data/**`, `tests/fixtures/data/**`
* `docs/data_foundation/PROVENANCE.md`

### Forbidden Changes
* No `src/alpha_system/execution/broker/**` or `live/**`; no real data writes; no
  `metadata/*.sqlite`; no `artifacts/**`; no `*.parquet`.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/data -q
test -f docs/data_foundation/PROVENANCE.md
git ls-files runs
```

### Artifact Policy
Commit only `ContinuousFuturesSeriesRecord` code, `DatedFuturesSeriesRecord` code, the
provenance separation, tests, docs, and tiny synthetic fixtures. Never commit `runs/**`, raw
data, canonical data, heavy artifacts, or local DB files. Explicit staging only.

### Done Criteria
* Both series records exist with required fields and validate fail-closed.
* Continuous, dated, stitched, adjusted, and unadjusted series are explicitly separate.
* Continuous is labeled non-orderable / not-dated-truth; dated availability is logged;
  adjusted-vs-unadjusted is explicit.

### Handoff Requirements
Document the provenance separation, the continuous/dated labels, the availability-logging,
and validation results.

### Review Requirements
Claude Opus review must confirm continuous futures are never treated as dated-contract truth.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## DATA-P12 — Session Templates and Trading Calendar

### Phase ID
`DATA-P12`

### Phase Name
Session Templates and Trading Calendar

### Lane
YELLOW

### Dependencies
`DATA-P05`.

### Purpose
Define the `SessionTemplate` (RTH/ETH/maintenance-break definitions) and the
`TradingCalendarRecord` (concrete session dates, holidays, early closes), including DST and
early-close handling.

### Scope
* Implement `SessionTemplate` with required fields (`template_id`, `timezone`, `rth_start`,
  `rth_end`, `eth_start`, `eth_end`, `maintenance_breaks`, `source`).
* Implement `TradingCalendarRecord` with required fields (`calendar_id`, `instrument_root`,
  `date`, `session_type`, `open_ts`, `close_ts`, `breaks`, `is_holiday`, `is_early_close`,
  `source`), with DST and early-close handling.
* Create `docs/data_foundation/SESSIONS_AND_CALENDAR.md`.

### Non-Goals
* Do not imply holiday completeness or exchange-official finality unless sourced.

### Expected Files / Directories
* `src/alpha_system/data/**` (`SessionTemplate`, `TradingCalendarRecord`)
* `tests/unit/data/**`, `tests/fixtures/data/**`
* `configs/data/**`
* `docs/data_foundation/SESSIONS_AND_CALENDAR.md`

### Forbidden Changes
* No `src/alpha_system/execution/broker/**` or `live/**`; no real data writes; no
  `metadata/*.sqlite`; no `artifacts/**`; no `*.parquet`.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/data -q
test -f docs/data_foundation/SESSIONS_AND_CALENDAR.md
git ls-files runs
```

### Artifact Policy
Commit only `SessionTemplate` code, `TradingCalendarRecord` code, tests, docs, and tiny
synthetic fixtures. Never commit `runs/**`, raw data, canonical data, heavy artifacts, or
local DB files. Explicit staging only.

### Done Criteria
* `SessionTemplate` and `TradingCalendarRecord` exist with required fields and validate
  fail-closed.
* DST and early-close handling is present.
* No completeness/finality claim beyond sourced data.

### Handoff Requirements
Document the session templates, the calendar, DST/early-close handling, and validation
results.

### Review Requirements
Claude Opus review must confirm DST/early-close handling and that completeness is not implied.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## DATA-P13 — Roll Policy and Roll Calendar

### Phase ID
`DATA-P13`

### Phase Name
Roll Policy and Roll Calendar

### Lane
YELLOW

### Dependencies
`DATA-P05`, `DATA-P06`, `DATA-P12`.

### Purpose
Define the `RollPolicy` (how a canonical continuous series is selected or stitched) and the
`RollCalendarRecord` (specific roll dates and contract transitions), keeping adjusted vs
unadjusted explicit and not implying tradable/best-execution rolls.

### Scope
* Implement `RollPolicy` with required fields (`roll_policy_id`, `method`, `roll_trigger`,
  `adjustment_method`, `fallback_rule`, `uses_volume`, `uses_open_interest`, `source`).
* Implement `RollCalendarRecord` with required fields (`roll_calendar_id`, `root_symbol`,
  `from_contract`, `to_contract`, `roll_date`, `method`, `evidence`, `validation_status`).
* Create `docs/data_foundation/ROLL_POLICY.md`.

### Non-Goals
* Do not imply tradable execution roll or best execution roll.

### Expected Files / Directories
* `src/alpha_system/data/**` (`RollPolicy`, `RollCalendarRecord`)
* `tests/unit/data/**`, `tests/fixtures/data/**`
* `configs/data/**`
* `docs/data_foundation/ROLL_POLICY.md`

### Forbidden Changes
* No `src/alpha_system/execution/broker/**` or `live/**`; no real data writes; no
  `metadata/*.sqlite`; no `artifacts/**`; no `*.parquet`.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/data -q
test -f docs/data_foundation/ROLL_POLICY.md
git ls-files runs
```

### Artifact Policy
Commit only `RollPolicy` code, `RollCalendarRecord` code, tests, docs, and tiny synthetic
fixtures. Never commit `runs/**`, raw data, canonical data, heavy artifacts, or local DB
files. Explicit staging only.

### Done Criteria
* `RollPolicy` and `RollCalendarRecord` exist with required fields and validate fail-closed.
* Adjusted vs unadjusted is explicit; roll evidence and validation status are recorded.
* No tradable/best-execution roll implied.

### Handoff Requirements
Document the roll policy, the roll calendar, the adjusted/unadjusted distinction, and
validation results.

### Review Requirements
Claude Opus review must confirm adjusted-vs-unadjusted is explicit and no tradable roll is
implied.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## DATA-P14 — Parser and Parsed Bar Records

### Phase ID
`DATA-P14`

### Phase Name
Parser and Parsed Bar Records

### Lane
YELLOW

### Dependencies
`DATA-P09`.

### Purpose
Define the `ParsedBarRecord` (provider-shaped parsed bar with metadata) and a parser that
turns raw provider responses into bronze-layer parsed bars, still provider-shaped and not yet
canonical.

### Scope
* Implement `ParsedBarRecord` with required fields (`source`, `symbol`, `contract_ref`,
  `provider_ts`, `open`, `high`, `low`, `close`, `volume`, `wap_if_available`,
  `bar_count_if_available`, `request_id`, `raw_object_id`).
* Implement a parser that reads `RawDataObject` refs and produces `ParsedBarRecord`s, with
  provider metadata preserved.
* Create `docs/data_foundation/PARSED_BARS.md`.

### Non-Goals
* Do not apply canonical timestamp semantics here.
* Do not ingest real data or commit provider responses.

### Expected Files / Directories
* `src/alpha_system/data/**` (`ParsedBarRecord`, parser)
* `tests/unit/data/**`, `tests/fixtures/data/**`
* `docs/data_foundation/PARSED_BARS.md`

### Forbidden Changes
* No `src/alpha_system/execution/broker/**` or `live/**`; no real data/provider responses
  committed; no `metadata/*.sqlite`; no `artifacts/**`; no `*.parquet`.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/data -q
test -f docs/data_foundation/PARSED_BARS.md
git ls-files runs
```

### Artifact Policy
Commit only `ParsedBarRecord` code, parser code, tests, docs, and tiny synthetic fixtures.
Never commit `runs/**`, raw data, canonical data, provider responses, heavy artifacts, or
local DB files. Explicit staging only.

### Done Criteria
* `ParsedBarRecord` exists with required fields and validates fail-closed.
* The parser produces provider-shaped bars from raw object refs.
* No canonical timestamp semantics implied; no provider response committed.

### Handoff Requirements
Document the parser, the parsed-bar record, the provider-shaped boundary, and validation
results.

### Review Requirements
Claude Opus review must confirm parsed bars remain provider-shaped (not canonical) and no raw
data is committed.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## DATA-P15 — Canonical 1m Bar Contract

### Phase ID
`DATA-P15`

### Phase Name
Canonical 1m Bar Contract

### Lane
YELLOW

### Dependencies
`DATA-P12`, `DATA-P14`.

### Purpose
Define the `CanonicalBarRecord` (research-ready silver-layer 1-minute bar) and the
`TimestampSemanticsPolicy`, ensuring canonical bars carry `available_ts` and never conflate
`event_ts`, `bar_start_ts`, `bar_end_ts`, `available_ts`, and `ingested_at`, aligned with V1
no-lookahead semantics.

### Scope
* Implement `CanonicalBarRecord` with required fields (`instrument_id`, `contract_id`,
  `series_id`, `bar_start_ts`, `bar_end_ts`, `event_ts`, `available_ts`, `ingested_at`,
  `open`, `high`, `low`, `close`, `volume`, `source`, `source_request_id`, `data_version`,
  `quality_flags`, `session_label`).
* Implement `TimestampSemanticsPolicy` with required fields (`policy_id`,
  `event_ts_definition`, `bar_start_ts_definition`, `bar_end_ts_definition`,
  `available_ts_definition`, `ingested_at_definition`, `lookahead_rules`).
* Enforce: a missing `available_ts` blocks canonicalization; timestamp fields are distinct;
  `available_ts` is when the completed bar would be usable in research, not when the API
  returned it.
* Add no-lookahead tests under `tests/no_lookahead/**`.
* Create `docs/data_foundation/CANONICAL_BARS.md`.

### Non-Goals
* Do not imply alpha value or tradability.
* Do not treat provider timestamps as research-ready.

### Expected Files / Directories
* `src/alpha_system/data/**` (`CanonicalBarRecord`, `TimestampSemanticsPolicy`)
* `tests/unit/data/**`, `tests/no_lookahead/**`, `tests/fixtures/data/**`
* `docs/data_foundation/CANONICAL_BARS.md`

### Forbidden Changes
* No `src/alpha_system/execution/broker/**` or `live/**`; no real data writes; no
  `metadata/*.sqlite`; no `artifacts/**`; no `*.parquet`.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/data -q
python -m pytest tests/no_lookahead -q
test -f docs/data_foundation/CANONICAL_BARS.md
git ls-files runs
```

### Artifact Policy
Commit only `CanonicalBarRecord` code, `TimestampSemanticsPolicy` code, tests, docs, and tiny
synthetic fixtures. Never commit `runs/**`, raw data, canonical data, heavy artifacts, or
local DB files. Explicit staging only.

### Done Criteria
* `CanonicalBarRecord` and `TimestampSemanticsPolicy` exist with required fields and validate
  fail-closed.
* Canonical bars carry `available_ts`; the five timestamp fields are distinct and not
  conflated; a missing `available_ts` blocks canonicalization.
* No-lookahead tests pass; no alpha/tradability implied.

### Handoff Requirements
Document the canonical bar contract, the timestamp semantics, the `available_ts` enforcement,
the no-lookahead tests, and validation results.

### Review Requirements
Claude Opus review must confirm `available_ts` is mandatory and timestamp fields are never
conflated.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## DATA-P16 — Data Quality Checks and Coverage Reports

### Phase ID
`DATA-P16`

### Phase Name
Data Quality Checks and Coverage Reports

### Lane
YELLOW

### Dependencies
`DATA-P15`.

### Purpose
Define the `DataQualityReport` (fail-closed quality audit) and the `CoverageReport` (coverage
by symbol, contract, session, partition), so silent gaps and timestamp/session/roll defects
fail closed rather than passing silently.

### Scope
* Implement `DataQualityReport` with required fields (`quality_report_id`,
  `dataset_version_id`, `gap_summary`, `duplicate_summary`, `non_monotonic_summary`,
  `ohlc_errors`, `zero_negative_price_errors`, `zero_volume_anomalies`, `dst_anomalies`,
  `session_coverage`, `roll_discontinuities`, `provider_error_summary`, `status`).
* Implement `CoverageReport` with required fields (`coverage_report_id`,
  `dataset_version_id`, `symbol_coverage`, `contract_coverage`, `session_coverage`,
  `partition_coverage`, `missing_intervals`, `incomplete_chunks`).
* Enforce silent gaps fail closed; coverage does not imply quality unless linked to a quality
  report.
* Optionally emit a curated synthetic report summary (no raw data).
* Create `docs/data_foundation/DATA_QUALITY.md` and `docs/data_foundation/COVERAGE_REPORT.md`.

### Non-Goals
* Do not imply alpha readiness or that quality is accepted.

### Expected Files / Directories
* `src/alpha_system/data/**` (`DataQualityReport`, `CoverageReport`)
* `tests/unit/data/**`, `tests/fixtures/data/**`
* `docs/data_foundation/DATA_QUALITY.md`, `docs/data_foundation/COVERAGE_REPORT.md`

### Forbidden Changes
* No `src/alpha_system/execution/broker/**` or `live/**`; no real data writes; no full
  reports with raw data; no `metadata/*.sqlite`; no `artifacts/**`; no `*.parquet`.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/data -q
test -f docs/data_foundation/DATA_QUALITY.md
test -f docs/data_foundation/COVERAGE_REPORT.md
git ls-files runs
```

### Artifact Policy
Commit only `DataQualityReport` code, `CoverageReport` code, tests, docs, tiny synthetic
fixtures, and a curated synthetic report summary. Never commit `runs/**`, raw data, canonical
data, full reports with raw data, heavy artifacts, or local DB files. Explicit staging only.

### Done Criteria
* `DataQualityReport` and `CoverageReport` exist with required fields and validate
  fail-closed.
* Silent gaps fail closed; coverage does not imply quality unless linked to a quality report.
* Any committed summary is synthetic; no alpha readiness implied.

### Handoff Requirements
Document the quality and coverage reports, the fail-closed-on-gaps behavior, the synthetic
summary, and validation results.

### Review Requirements
Claude Opus review must confirm silent gaps fail closed and no raw-data report is committed.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## DATA-P17 — Dataset Version Registry Integration

### Phase ID
`DATA-P17`

### Phase Name
Dataset Version Registry Integration

### Lane
YELLOW

### Dependencies
`DATA-P16`.

### Purpose
Define the `DatasetVersion` and integrate it with the existing local registry/persistence
layer so reproducible canonical datasets persist and resolve by ID, linking manifest, code,
config, and quality hashes — without committing the database.

### Scope
* Implement `DatasetVersion` with required fields (`dataset_version_id`, `source`,
  `symbol_universe`, `bar_size`, `what_to_show`, `start_ts`, `end_ts`, `contract_universe`,
  `roll_policy_id`, `manifest_hash`, `code_hash`, `config_hash`, `quality_report_hash`,
  `created_at`).
* Integrate with the existing local persistence layer (and any migration), persisting and
  resolving dataset versions by ID.
* Enforce the lifecycle block: a dataset version requires quality, coverage, and manifest
  before `VERSIONED`/`READY_FOR_RESEARCH`.
* Add integration tests under `tests/integration/data/` using a temp DB (never committed).
* Create `docs/data_foundation/DATASET_VERSION.md`.

### Non-Goals
* Do not commit `metadata/*.sqlite` or any DB file.
* Do not ingest real data or imply research approval.

### Expected Files / Directories
* `src/alpha_system/data/**` (`DatasetVersion` registry code, migration if needed)
* `tests/unit/data/**`, `tests/integration/data/**`, `tests/fixtures/data/**`
* `docs/data_foundation/DATASET_VERSION.md`

### Forbidden Changes
* No `src/alpha_system/execution/broker/**` or `live/**`; no DB commits
  (`metadata/*.sqlite`, `metadata/*.db`); no real data; no `artifacts/**`; no `*.parquet`.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/data -q
python -m pytest tests/integration/data -q
test -f docs/data_foundation/DATASET_VERSION.md
find metadata -type f '!' -name README.md '!' -name .gitkeep -print
git ls-files runs
```

### Artifact Policy
Commit only `DatasetVersion` registry code, migrations, tests, docs, and tiny synthetic
fixtures. Never commit `runs/**`, `metadata/*.sqlite`, raw data, canonical data, heavy
artifacts, or local DB files. Explicit staging only.

### Done Criteria
* `DatasetVersion` exists with required hashes and persists/resolves via the existing
  registry layer using a temp DB in tests.
* A dataset version requires quality, coverage, and manifest hashes.
* No DB file is staged or committed (`find metadata` returns only README/.gitkeep);
  integration tests pass.

### Handoff Requirements
Document the dataset version, the registry integration, the temp-DB test approach, the
`find metadata` audit, and validation results.

### Review Requirements
Claude Opus review must confirm persistence works, hashes are mandatory, and no DB is
committed.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## DATA-P18 — Dataset Partition Plan and Locked-Test Metadata

### Phase ID
`DATA-P18`

### Phase Name
Dataset Partition Plan and Locked-Test Metadata

### Lane
YELLOW

### Dependencies
`DATA-P17`.

### Purpose
Define the `DatasetPartitionPlan` (development / validation / locked-test candidate / latest
shadow) and the locked-test contamination-metadata rules, without performing any alpha
research and without permitting locked-partition use without Governance metadata.

### Scope
* Implement `DatasetPartitionPlan` with required fields (`plan_id`, `development_partition`,
  `validation_partition`, `locked_test_candidate`, `latest_shadow_candidate`,
  `contamination_metadata_rules`), encoding development `2018-01-01 → 2022-12-31`, validation
  `2023-01-01 → 2024-12-31`, locked-test candidate `2025-01-01 → as_of_run`.
* Encode the rules: data QA may inspect coverage across partitions; alpha research must not
  use the locked-test candidate without Governance metadata; any locked-partition use must
  create contamination metadata later.
* Create `docs/data_foundation/PARTITION_PLAN.md`.

### Non-Goals
* Do not perform alpha research or imply research approval.
* Do not permit any locked-partition use without Governance metadata.

### Expected Files / Directories
* `src/alpha_system/data/**` (`DatasetPartitionPlan`, locked-test metadata rules)
* `tests/unit/data/**`, `tests/fixtures/data/**`
* `configs/data/**`
* `docs/data_foundation/PARTITION_PLAN.md`

### Forbidden Changes
* No `src/alpha_system/execution/broker/**` or `live/**`; no real data writes; no
  `metadata/*.sqlite`; no `artifacts/**`; no `*.parquet`.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/data -q
test -f docs/data_foundation/PARTITION_PLAN.md
git ls-files runs
```

### Artifact Policy
Commit only `DatasetPartitionPlan` code, locked-test metadata rules, tests, docs, and tiny
synthetic fixtures. Never commit `runs/**`, raw data, canonical data, heavy artifacts, or
local DB files. Explicit staging only.

### Done Criteria
* `DatasetPartitionPlan` exists with required fields and validates fail-closed.
* Development/validation/locked-test/latest-shadow partitions and contamination-metadata
  rules are encoded.
* No research approval implied; locked-partition use requires Governance metadata.

### Handoff Requirements
Document the partition plan, the contamination-metadata rules, the locked-test policy, and
validation results.

### Review Requirements
Claude Opus review must confirm the partition plan and locked-test contamination-metadata
rules without enabling alpha research.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## DATA-P19 — Micro Batch Policy for MES/MNQ/M2K

### Phase ID
`DATA-P19`

### Phase Name
Micro Batch Policy for MES/MNQ/M2K

### Lane
YELLOW

### Dependencies
`DATA-P05`, `DATA-P10`.

### Purpose
Define the `MicroBatchPolicy` as a separate secondary path for MES/MNQ/M2K (`2020-01-01` or
earliest clean), never mixed with the mini batch, with mini/micro parity-check targets.

### Scope
* Implement `MicroBatchPolicy` with required fields (`batch_id`, `symbols`, `start_date`,
  `separate_batch`, `parity_check_targets`), `symbols = MES, MNQ, M2K`,
  `separate_batch = true`.
* Encode the micro batch as a separate secondary path with parity checks against the mini
  batch; never a primary alpha source in V1.
* Create `docs/data_foundation/MICRO_BATCH.md`.

### Non-Goals
* Do not mix mini and micro batches.
* Do not imply micros are a primary alpha source.

### Expected Files / Directories
* `src/alpha_system/data/**` (`MicroBatchPolicy`, micro batch plan)
* `tests/unit/data/**`, `tests/fixtures/data/**`
* `configs/data/**`
* `docs/data_foundation/MICRO_BATCH.md`

### Forbidden Changes
* No `src/alpha_system/execution/broker/**` or `live/**`; no real data writes; no
  `metadata/*.sqlite`; no `artifacts/**`; no `*.parquet`.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/data -q
test -f docs/data_foundation/MICRO_BATCH.md
git ls-files runs
```

### Artifact Policy
Commit only `MicroBatchPolicy` code, the micro batch plan, tests, docs, and tiny synthetic
fixtures. Never commit `runs/**`, raw data, canonical data, heavy artifacts, or local DB
files. Explicit staging only.

### Done Criteria
* `MicroBatchPolicy` exists with required fields and validates fail-closed.
* The micro batch is separate from the mini batch with parity-check targets.
* Micros are not implied as a primary alpha source.

### Handoff Requirements
Document the micro batch policy, the separation, the parity-check targets, and validation
results.

### Review Requirements
Claude Opus review must confirm micro/mini separation and that micros are secondary.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## DATA-P20 — Optional BID_ASK / Spread Proxy Pilot Plan

### Phase ID
`DATA-P20`

### Phase Name
Optional BID_ASK / Spread Proxy Pilot Plan

### Lane
YELLOW

### Dependencies
`DATA-P08`, `DATA-P16`.

### Purpose
Define an optional, bounded BID_ASK / spread-proxy pilot plan and a spread-proxy scaffold,
acknowledging that BID_ASK requests carry heavier pacing and storage cost and are not part of
the primary panel.

### Scope
* Define the BID_ASK pilot as optional and bounded, with heavier pacing (BID_ASK counts
  double) and storage explicitly acknowledged and referencing the pacing policy.
* Implement a spread-proxy scaffold that derives spread-proxy metrics where BID_ASK data is
  available, marked pilot-only.
* Create `docs/data_foundation/BID_ASK_PILOT.md`.

### Non-Goals
* Do not make BID_ASK part of the primary panel.
* Do not imply tradable spread/cost truth.

### Expected Files / Directories
* `src/alpha_system/data/**` (BID_ASK pilot plan, spread proxy scaffold)
* `tests/unit/data/**`, `tests/fixtures/data/**`
* `configs/data/**`
* `docs/data_foundation/BID_ASK_PILOT.md`

### Forbidden Changes
* No `src/alpha_system/execution/broker/**` or `live/**`; no real data writes; no
  `metadata/*.sqlite`; no `artifacts/**`; no `*.parquet`.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/data -q
test -f docs/data_foundation/BID_ASK_PILOT.md
git ls-files runs
```

### Artifact Policy
Commit only the BID_ASK pilot plan, the spread proxy scaffold, tests, docs, and tiny
synthetic fixtures. Never commit `runs/**`, raw data, canonical data, heavy artifacts, or
local DB files. Explicit staging only.

### Done Criteria
* The BID_ASK pilot is marked optional and bounded.
* Heavier pacing and storage cost are acknowledged (BID_ASK counts double).
* The spread-proxy scaffold is pilot-only; no tradable cost truth implied.

### Handoff Requirements
Document the pilot plan, the heavier-pacing acknowledgement, the spread-proxy scaffold, and
validation results.

### Review Requirements
Claude Opus review must confirm the pilot is optional/bounded and the heavier pacing/storage
is acknowledged.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## DATA-P21 — Synthetic IBKR Fixture Tests

### Phase ID
`DATA-P21`

### Phase Name
Synthetic IBKR Fixture Tests

### Lane
YELLOW

### Dependencies
`DATA-P03`, `DATA-P05`, `DATA-P06`, `DATA-P07`, `DATA-P08`, `DATA-P09`, `DATA-P14`,
`DATA-P15`, `DATA-P16`, `DATA-P17`.

### Purpose
Exercise the connector, planner, parser, and quality path end to end against synthetic IBKR
fixtures (synthetic provider responses), proving the pipeline works without any external call
and without committing real provider data.

### Scope
* Add synthetic IBKR fixture tests and synthetic provider-response fixtures under
  `tests/fixtures/data/**`.
* Drive the connector/planner/parser/canonical/quality path on synthetic fixtures via unit
  and integration tests, with no external IBKR call.
* Verify (via `find . -name "*.parquet"`) that no parquet exists outside `tests/fixtures/`.
* Create `docs/data_foundation/SYNTHETIC_FIXTURE_TESTS.md`.

### Non-Goals
* Do not perform an external IBKR call (RED-only, later).
* Do not commit real provider responses; do not imply data is pulled.

### Expected Files / Directories
* `src/alpha_system/data/**` (any test hooks)
* `tests/unit/data/**`, `tests/integration/data/**`, `tests/fixtures/data/**`
* `docs/data_foundation/SYNTHETIC_FIXTURE_TESTS.md`

### Forbidden Changes
* No `src/alpha_system/execution/broker/**` or `live/**`; no real data; no real provider
  responses; no `metadata/*.sqlite`; no `artifacts/**`; no `*.parquet` outside
  `tests/fixtures`.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python tools/verify.py --all
python -m pytest tests/unit/data -q
python -m pytest tests/integration/data -q
test -f docs/data_foundation/SYNTHETIC_FIXTURE_TESTS.md
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
git ls-files runs
```

### Artifact Policy
Commit only synthetic IBKR fixture tests, synthetic provider-response fixtures, tests, docs,
and tiny synthetic fixtures. Never commit `runs/**`, raw data, canonical data, real provider
responses, heavy artifacts, or local DB files. Explicit staging only.

### Done Criteria
* Synthetic IBKR fixture tests exist; connector/planner/parser/quality are tested on
  synthetic fixtures.
* No external call occurs; the parquet audit shows none outside `tests/fixtures`.
* No real provider response committed; no data-pulled claim.

### Handoff Requirements
Document the synthetic fixtures, the pipeline coverage, the parquet audit, and validation
results.

### Review Requirements
Claude Opus review must confirm the pipeline is exercised on synthetic data with no external
call and no real data committed.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## DATA-P22 — Small Authorized IBKR Smoke Pull

### Phase ID
`DATA-P22`

### Phase Name
Small Authorized IBKR Smoke Pull

### Lane
RED

### Dependencies
`DATA-P21`.

### Purpose
Perform a small, explicitly authorized, read-only IBKR historical smoke pull to validate the
connector, manifest, pacing, and resume path against the real provider — local-only, never in
CI, never auto-merged, and committing no data artifacts. RED here means external /
provider-facing, **never** trading.

### Scope
* Implement a small smoke-pull entry point that, only when authorization is armed, performs a
  tiny read-only historical pull through the read-only boundary, writing raw outputs to the
  local data root.
* Require all of `PROJECT_OP_AUTHORIZED`, `PROJECT_OP_SCOPE`, `PROJECT_OP_EXPIRES`,
  `ALPHA_DATA_PULL_AUTHORIZED`, and `ALPHA_ALLOW_EXTERNAL_IBKR` before any external call; the
  pull is forbidden in CI (`ci_allowed: false`).
* Produce a curated synthetic-or-redacted summary only (no raw data, no provider responses,
  no account info).
* Create `docs/data_foundation/SMOKE_PULL.md`.

### Non-Goals
* Do not place orders, query positions, or touch account/paper/live paths.
* Do not commit any raw data, provider responses, or account info.
* Do not run in CI; do not auto-merge.

### Expected Files / Directories
* `src/alpha_system/data/**` (smoke pull code)
* `tests/unit/data/**`, `tests/fixtures/data/**`
* `docs/data_foundation/SMOKE_PULL.md`

### Forbidden Changes
* No `src/alpha_system/execution/broker/**`, `live/**`, `paper/**`, or `order_router*`; no
  `data/raw/**` or `data/canonical/**` commits; no `metadata/*.sqlite`; no `artifacts/**`; no
  `*.parquet`.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/data -q
test -f docs/data_foundation/SMOKE_PULL.md
git ls-files runs
git status --short
find data -type f '!' -name README.md '!' -name .gitkeep -print
```

### Artifact Policy
Commit only smoke-pull code, the smoke-pull runbook doc, a curated synthetic-or-redacted
summary only, tests, and docs. Never commit `runs/**`, raw data, canonical data, provider
responses, account info, heavy artifacts, or local DB files. Pull outputs are local-only.
Explicit staging only.

### Done Criteria
* The smoke pull runs only with full RED-lane and data-pull authorization armed, and never in
  CI.
* A tiny read-only historical pull validates connector/manifest/pacing/resume locally.
* No data artifact, provider response, or account info is committed; the `find data` audit is
  clean in the repo tree; the phase is not auto-merged.

### Handoff Requirements
Document the authorization gates, the smoke-pull scope, the local-only outputs, the artifact
audit, and validation results, plus an explicit statement that no order/account path was
touched.

### Review Requirements
Claude Opus review (RED) must confirm explicit external authorization was required, the pull
is read-only, no order/account surface is reachable, no data is committed, and CI never runs
the pull.

### Auto-Merge Eligibility
RED phase: auto PR when authorized, but **no auto merge**. Merge requires scoped
authorization present, data-pull authorization present, checks pass, handoff valid, Claude
review complete with `PASS`/`PASS_WITH_WARNINGS`, artifact policy pass, no data artifacts
committed, no forbidden paths, no STOP file, CI pass if configured, and human authorization.

---

## DATA-P23 — Local Backfill Runbook and Resume Drill

### Phase ID
`DATA-P23`

### Phase Name
Local Backfill Runbook and Resume Drill

### Lane
RED

### Dependencies
`DATA-P22`.

### Purpose
Provide a local backfill runbook and a resume drill that demonstrates resume-after-interruption
against the authorized local pull path — local-only, never in CI, never auto-merged, and
committing no data artifacts. RED here means external / provider-facing, **never** trading.

### Scope
* Implement a resume-drill entry point that, only when authorization is armed, interrupts and
  resumes a local backfill using the resume ledger and token, demonstrating no silent gaps and
  no raw overwrite.
* Require all of `PROJECT_OP_AUTHORIZED`, `PROJECT_OP_SCOPE`, `PROJECT_OP_EXPIRES`,
  `ALPHA_DATA_PULL_AUTHORIZED`, and `ALPHA_ALLOW_EXTERNAL_IBKR`; forbidden in CI.
* Produce a curated synthetic-or-redacted summary only (no raw data).
* Create `docs/data_foundation/BACKFILL_RUNBOOK.md`.

### Non-Goals
* Do not place orders, query positions, or touch account/paper/live paths.
* Do not commit any raw data, provider responses, or account info.
* Do not run in CI; do not auto-merge.

### Expected Files / Directories
* `src/alpha_system/data/**` (resume drill code)
* `tests/unit/data/**`, `tests/fixtures/data/**`
* `docs/data_foundation/BACKFILL_RUNBOOK.md`

### Forbidden Changes
* No `src/alpha_system/execution/broker/**`, `live/**`, `paper/**`, or `order_router*`; no
  `data/raw/**` or `data/canonical/**` commits; no `metadata/*.sqlite`; no `artifacts/**`; no
  `*.parquet`.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/data -q
test -f docs/data_foundation/BACKFILL_RUNBOOK.md
find data -type f '!' -name README.md '!' -name .gitkeep -print
git ls-files runs
```

### Artifact Policy
Commit only the backfill runbook doc, resume drill code, a curated synthetic-or-redacted
summary only, tests, and docs. Never commit `runs/**`, raw data, canonical data, provider
responses, account info, heavy artifacts, or local DB files. Pull outputs are local-only.
Explicit staging only.

### Done Criteria
* The resume drill runs only with full RED-lane and data-pull authorization armed, and never
  in CI.
* Resume-after-interruption is demonstrated locally with no silent gaps and no raw overwrite.
* No data artifact, provider response, or account info is committed; the `find data` audit is
  clean in the repo tree; the phase is not auto-merged.

### Handoff Requirements
Document the runbook, the resume drill, the authorization gates, the local-only outputs, the
artifact audit, and validation results, plus an explicit statement that no order/account path
was touched.

### Review Requirements
Claude Opus review (RED) must confirm explicit external authorization was required, resume
works with no silent gaps, the pull is read-only, no order/account surface is reachable, no
data is committed, and CI never runs the drill.

### Auto-Merge Eligibility
RED phase: auto PR when authorized, but **no auto merge**. Same RED merge requirements as
DATA-P22.

---

## DATA-P24 — End-to-End Data Foundation Dry Run and Closeout

### Phase ID
`DATA-P24`

### Phase Name
End-to-End Data Foundation Dry Run and Closeout

### Lane
YELLOW

### Dependencies
`DATA-P23`.

### Purpose
Run the complete data-foundation path over synthetic fixtures end to end (source → connection
→ request/manifest → pacing/chunk/resume → raw → parsed → canonical → quality/coverage →
dataset version → partitions), run the acceptance audit against `ACCEPTANCE.md`, and close out
the campaign with a final semantic done-check and closeout document.

### Scope
* Implement a synthetic end-to-end dry run (script/test) walking data through the lifecycle
  using fixtures, the registry, and the quality/coverage gates, with no external call.
* Assert the lifecycle blocks fire at each missing-prerequisite point (no manifest, no pacing,
  missing `available_ts`, silent gaps) and that no prohibited MVP state is reachable.
* Run the acceptance audit covering all gates and prohibited shortcuts.
* Produce `campaigns/ALPHA_DATA_FOUNDATION_V1/CLOSEOUT.md` and
  `docs/data_foundation/END_TO_END_DRY_RUN.md` with a curated synthetic summary; record
  next-campaign readiness.
* Confirm artifact policy: no raw/canonical data, heavy artifacts, local DBs, or `runs/**`
  committed.

### Non-Goals
* Do not use real data or perform an external call; do not claim any alpha/profitability/
  tradability/production result.
* Do not begin any next campaign.

### Expected Files / Directories
* `src/alpha_system/data/**` (end-to-end dry-run code)
* `tests/unit/data/**`, `tests/integration/data/**`, `tests/fixtures/data/**`
* `campaigns/ALPHA_DATA_FOUNDATION_V1/CLOSEOUT.md`
* `docs/data_foundation/END_TO_END_DRY_RUN.md`

### Forbidden Changes
* No `src/alpha_system/execution/broker/**` or `live/**`; no `data/raw/**` or
  `data/canonical/**` commits; no `metadata/*.sqlite`; no `artifacts/**/raw_outputs/**`; no
  `*.parquet`; no full generated bundles.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python tools/verify.py --all
python -m pytest tests/unit/data -q
python -m pytest tests/integration/data -q
test -f campaigns/ALPHA_DATA_FOUNDATION_V1/CLOSEOUT.md
test -f docs/data_foundation/END_TO_END_DRY_RUN.md
find data -type f '!' -name README.md '!' -name .gitkeep -print
find metadata -type f '!' -name README.md '!' -name .gitkeep -print
find artifacts -type f -size +1M -print
git ls-files runs
```

### Artifact Policy
Commit only end-to-end dry-run code, the closeout doc, tests, docs, tiny synthetic fixtures,
and a curated synthetic dry-run summary. Never commit `runs/**`, raw data, canonical data,
heavy artifacts, local DB files, or full generated bundles. Explicit staging only.

### Done Criteria
* The synthetic end-to-end data-foundation path passes; lifecycle blocks fire at each missing
  prerequisite; prohibited MVP states are unreachable.
* The acceptance audit passes (or records a truthful `BLOCKED`).
* The final semantic done-check passes; `CLOSEOUT.md` exists with a final verdict
  (`COMPLETE`, `COMPLETE_WITH_WARNINGS`, or `BLOCKED`) and next-campaign readiness.
* The artifact audit (`find data`, `find metadata`, `find artifacts`, `git ls-files runs`) is
  clean.

### Handoff Requirements
Summarize the end-to-end path, the lifecycle-block assertions, the acceptance-audit results,
the final verdict, the next-campaign readiness, and the artifact audit.

### Review Requirements
Claude Opus review must perform the final semantic done-check across the whole campaign, not
just per-phase tests, and confirm the dry run exercises every lifecycle block on synthetic
data.

### Auto-Merge Eligibility
Standard YELLOW gates; final verdict recorded in `CLOSEOUT.md`.

---

## Campaign-Wide Done Criteria

The campaign is done when:

* All 25 phases (`DATA-P00` … `DATA-P24`) are complete with `PASS`/`PASS_WITH_WARNINGS`
  verdicts.
* All acceptance gates in `ACCEPTANCE.md` pass.
* The repo can define and validate a read-only IBKR historical data profile; clientId
  `101`/`102` are hard-blocked and the `201–209` namespace (default `201`) is enforced.
* ES/NQ/RTY mini batch and MES/MNQ/M2K micro batch are explicitly separated; historical
  requests are manifest-driven, chunked, paced, resumable, and auditable.
* Raw provider data, parsed bars, canonical bars, and dataset versions are separate layers;
  contract economics, sessions, rolls, and provenance are first-class records.
* Canonical bars preserve `event_ts`/`bar_start_ts`/`bar_end_ts`/`available_ts`/`ingested_at`;
  data-quality and coverage reports fail closed on silent gaps or timestamp defects.
* The RED smoke pull and resume drill ran only under explicit external authorization, never in
  CI, never auto-merged, and committed no data artifacts.
* The synthetic end-to-end dry run passes with lifecycle blocks firing; the final semantic
  done-check passes and `CLOSEOUT.md` records the final verdict and next-campaign readiness.
* No raw/canonical/provider/account data, heavy artifacts, local DBs, caches, logs, or
  `runs/**` are committed.
* No broker/live/paper/order/account scope, no alpha/factor/label/strategy scope, and no
  alpha/profitability/tradability/production-readiness claims exist.

## Scope Boundary Reminders

Aggressive about provenance, quality, and reproducibility; conservative about market claims
and trading scope. This campaign installs the read-only data-admissibility foundation only. It
does not search for alpha, research factors or labels, connect to brokers, place orders, or
claim profitability or tradability. Future campaigns
(`ALPHA_FEATURE_LABEL_FOUNDATION_V1`, `ALPHA_AGENT_FACTORY_MVP`,
`ALPHA_FUTURES_CORE_ALPHA_V1`, `ALPHA_PORTFOLIO_ALPHA_BOOK_V1`,
`ALPHA_VALIDATION_GOVERNANCE_V1`) consume this truth layer but are not started here, and each
remains constrained by the governance gates and the data-admissibility rules this campaign
installs. Future alpha research must not use the locked-test partition without Governance
metadata, and any future locked-partition use must create contamination metadata.

## Forbidden Path Reminders

* Never commit: `data/raw/**`, `data/canonical/**`, `data/factors/**`, `data/labels/**`,
  `data/cache/**`, `metadata/*.sqlite`/`*.sqlite3`/`*.db`/`*.db-journal`/`*.wal`,
  `*.parquet`/`*.arrow`/`*.feather` (outside documented tiny fixtures),
  `*.pkl`/`*.pickle`/`*.joblib`/`*.onnx`/`*.npy`/`*.npz`, logs, caches, `runs/**`,
  `artifacts/**/raw_outputs/**`, `artifacts/**/full_trade_logs/**`, provider responses,
  account info, IBKR logs, credentials, and generated heavy artifacts.
* Never introduce: `src/alpha_system/execution/broker/**`,
  `src/alpha_system/execution/live/**`, `src/alpha_system/execution/paper/**`,
  `src/alpha_system/execution/order_router*`, `src/alpha_system/broker/**`,
  `src/alpha_system/live/**`, or any order/account API surface through the data module.
* Never use `git add .` or `git add -A`; never force push.

## External / RED Lane Rules

* RED in this campaign means external, provider-facing, local-heavy operations (`DATA-P22`,
  `DATA-P23`). RED **never** means trading, order placement, account access, paper, or live.
* RED phases require all scope env (`PROJECT_OP_AUTHORIZED`, `PROJECT_OP_SCOPE`,
  `PROJECT_OP_EXPIRES`) plus data-pull env (`ALPHA_DATA_PULL_AUTHORIZED`,
  `ALPHA_ALLOW_EXTERNAL_IBKR`) to be present, scope-matched, and unexpired before any external
  IBKR call.
* RED phases never run in CI, never auto-merge (auto PR only when authorized and human-gated),
  and never commit raw data, canonical data, provider responses, or account info. All pull
  outputs are local-only.
* RED has `automatic_repair = false`; an external pull attempted without authorization is a
  STOP-and-escalate condition.

## Review and Merge Rules

* Every YELLOW and RED phase requires fresh Claude Opus review with a `verdict.json`.
* YELLOW merge requires `PASS`/`PASS_WITH_WARNINGS`, passing checks, valid handoff, clean
  artifact policy, no forbidden paths, no STOP file, CI pass if configured, and a passing
  semantic done-check.
* RED merge additionally requires scoped authorization present, data-pull authorization
  present, no data artifacts committed, and human authorization; RED never auto-merges.
* `REWORK` routes to the bounded repair loop (max 3 attempts); `BLOCKED`/`FAIL` stop the phase
  with a truthful blocked handoff. Fake completion is forbidden.
