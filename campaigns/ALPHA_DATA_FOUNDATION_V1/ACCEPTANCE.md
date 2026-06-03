# ALPHA_DATA_FOUNDATION_V1 Acceptance Criteria

## Acceptance Philosophy

Acceptance for this campaign is **semantic, not mechanical**. Passing tests are necessary
but never sufficient. A phase or gate is accepted only when the data-foundation machinery
genuinely **fails closed**, the gates genuinely **block** missing prerequisites, gaps and
defects are genuinely **visible and durable**, the read-only IBKR boundary is genuinely
**enforced**, real-market data stays genuinely **local-only**, and no prohibited scope or
claim is present.

This campaign installs the read-only real-market-data truth layer that future AI alpha
research will stand on. It owns provenance and truth, not market results. IBKR is a
**bootstrap historical data source only** — never a broker, order, account, paper, or live
surface. Therefore acceptance explicitly rejects any outcome where a connector works but
the clientId guard is missing, where data is pulled without a manifest, where raw provider
data is overwritten, where gaps are silently swallowed, where continuous futures are
treated as dated-contract truth, where canonical timestamps are conflated, where raw or
heavy data is committed, or where any alpha/profitability/tradability/broker/paper/live
claim appears.

The final verdict for the campaign is one of `COMPLETE`, `COMPLETE_WITH_WARNINGS`, or
`BLOCKED`. A truthful `BLOCKED` is acceptable and strongly preferred over a false
`COMPLETE`.

## Campaign-Level Acceptance Criteria

The campaign is accepted only when all ten success criteria from `GOAL.md`
("Success Definition") hold, every phase carries a merged `PASS` or `PASS_WITH_WARNINGS`
verdict (or a truthful `BLOCKED` is recorded), and the artifact audit is clean:

1. The repo can **define and validate a read-only IBKR historical data profile**
   (`DataSourceProfile` + `IBKRConnectionProfile` with `read_only_mode` default true and a
   required connection doctor).
2. clientId `101` and `102` are **hard-blocked** and the data namespace `201–209` is
   enforced with default `201` (`IBKRClientIdPolicy`, fail-closed, not a warning).
3. The ES/NQ/RTY **mini batch** and the MES/MNQ/M2K **micro batch** are explicitly
   separated and never mixed.
4. Historical requests are **manifest-driven, chunked, paced, resumable, and auditable**
   (`HistoricalRequestSpec`, `HistoricalRequestManifest`, `RequestPacingPolicy`,
   `HistoricalPullLedger`, `ProviderErrorRecord`).
5. Raw provider data, parsed bars, canonical bars, and dataset versions are **separate
   layers** (`RawDataObject` → `ParsedBarRecord` → `CanonicalBarRecord` →
   `DatasetVersion`).
6. Futures **contract economics, sessions, rolls, and provenance** are first-class records
   (`InstrumentMasterRecord`, `SessionTemplate`/`TradingCalendarRecord`, `RollPolicy`/
   `RollCalendarRecord`, `ContinuousFuturesSeriesRecord`/`DatedFuturesSeriesRecord`).
7. Canonical bars preserve `event_ts`, `bar_start_ts`, `bar_end_ts`, `available_ts`, and
   `ingested_at` as distinct fields.
8. Data-quality and coverage reports **fail closed** on silent gaps or timestamp defects.
9. Real-data artifacts are **local-only** and never committed.
10. No alpha, profitability, tradability, broker, paper, or live claim is introduced
    anywhere.

All 25 phases (`DATA-P00` … `DATA-P24`) are complete with merged verdicts; `DATA-P22` and
`DATA-P23` are RED and require scoped external/data authorization, all others are YELLOW.
The data-lifecycle blocks defined in `campaign.yaml`
(`data_lifecycle_state_machine.blocks`) are genuinely enforced, and the prohibited MVP
states `READY_FOR_TRADING`, `LIVE_FEED_READY`, `BROKER_ENABLED`, `ALPHA_VALIDATED`, and
`PROFITABLE` are unreachable.

## Connection-Profile-Level Acceptance

* `DataSourceProfile` carries `allowed_modes`/`forbidden_modes`, `requires_authorization`,
  and implies neither broker readiness, execution permission, nor data completeness.
* `IBKRConnectionProfile` carries `host`, `port`, `client_id`, `read_only_mode`,
  `environment`, `connection_timeout`, `doctor_status`, and `validated_at`; default is
  `host 127.0.0.1`, `port 4002`, `clientId 201`, `read_only_mode = true`.
* A **connection doctor** is required and must detect/report Windows↔WSL2 host/port
  reachability failures rather than silently retrying into the wrong host.
* The profile implies no account access, no order access, and no live-feed readiness.

## Client-Id-Policy-Level Acceptance

* `IBKRClientIdPolicy` carries `forbidden_client_ids`, `allowed_range`,
  `default_client_id`, `worker_client_ids`, and `collision_policy`.
* clientId `101` and `102` are **forbidden and fail closed** — rejection is a hard
  validation error, not a warning.
* The default clientId is `201`; the allowed data namespace is `201–209`; worker
  assignment is `ES=201`, `NQ=202`, `RTY=203` when multiple connections are used.
* `collision_policy = fail_closed`; clientId uniqueness is enforced, not optional, and the
  connector explicitly logs and validates the clientId on every connection.

## IBKR-Read-Only-Boundary-Level Acceptance

* An **order-method kill switch** is present: order/account/trading methods are
  unreachable or hard-disabled from the data module.
* The data module **cannot place an order, query positions, or touch account-trading
  paths**, and does not import order/account/execution APIs.
* `read_only_mode = true` is the default, and external provider calls require explicit
  RED-lane authorization and never run in CI.
* A reachable order-API surface through the data module is a hard merge blocker.

## Request-Manifest-Level Acceptance

* **No provider pull may occur without a `HistoricalRequestManifest`**; a missing manifest
  blocks the pull.
* `HistoricalRequestSpec` and `HistoricalRequestManifest` carry all required fields
  (including `manifest_hash`, `chunk_policy`, `expected_coverage`, `pacing_policy_id`,
  `data_root`) and imply neither that data exists nor that pull is authorized.
* **Duplicate-chunk / duplicate-request detection** is present so identical requests are
  not silently re-issued.
* Mini (`ES`/`NQ`/`RTY`) and micro (`MES`/`MNQ`/`M2K`) batches are kept in **separate
  manifests/batches**; `max_concurrent_roots = 3`; batches are never mixed.

## Pacing/Resume-Level Acceptance

* A conservative, configurable **pacing guard** (`RequestPacingPolicy`) is required;
  naive request loops are forbidden, and BID_ASK counts heavier than TRADES.
* A **resume ledger** (`HistoricalPullLedger` with `resume_token`,
  `coverage_summary`, `chunk_records`) supports resuming from recorded state rather than
  re-pulling completed chunks.
* A **provider-error ledger** (`ProviderErrorRecord`) permanently logs IBKR errors and
  incomplete responses with retryability classification.
* **No silent gaps** — incomplete chunks are recorded explicitly; **no raw overwrite** —
  raw objects are immutable and content-addressed. A missing pacing guard blocks a pull.

## Instrument-Master-Level Acceptance

* `InstrumentMasterRecord` carries `root_symbol`/`ib_symbol`, `exchange`, `currency`,
  `asset_class`, `sec_type`, `point_value`, `tick_size`, `tick_value`, `multiplier`,
  `timezone`, `session_template_id`, `roll_policy_id`, `source`, and `source_retrieved_at`;
  `trading_class` and `con_id` are carried on the dated `FuturesContractRecord`.
* `tick_value = tick_size × point_value` where applicable, and is verified, not assumed.
* The ES/NQ/RTY and MES/MNQ/M2K economic anchors (per `GOAL.md`) are **verified against
  official sources and repo tests**; they remain economic anchors, not
  production-certified until verified.
* The record implies no selected current contract.

## Contract-Details-Level Acceptance

* `ContractDetailsSnapshot` carries `snapshot_id`, `contract_id`, `raw_details_ref`,
  `normalized_fields`, `retrieved_at`, `client_id`, `source`, and `hash`; snapshots are
  **immutable**.
* `FuturesContractRecord` carries `include_expired_support_status`; `includeExpired`
  availability is **discovered and logged, not assumed**, and no full historical
  availability is promised.
* The snapshot implies no CME economic truth unless reconciled with the instrument master.

## Session-Calendar-Level Acceptance

* `SessionTemplate` defines RTH/ETH windows and `maintenance_breaks` with an explicit
  `timezone`; `TradingCalendarRecord` carries concrete `open_ts`/`close_ts`, `breaks`,
  `is_holiday`, and `is_early_close`.
* Timezone is **explicit** on every session/calendar record (never implicit local).
* **DST transitions and early closes are handled** and visible, not assumed away; the
  calendar implies no exchange-official finality unless sourced.

## Roll-Calendar-Level Acceptance

* `RollPolicy` defines a **default roll policy** (`method`, `roll_trigger`,
  `adjustment_method`, `fallback_rule`, volume/open-interest usage) and implies no
  tradable execution roll.
* `RollCalendarRecord` carries **explicit roll dates** (`from_contract`, `to_contract`,
  `roll_date`, `evidence`, `validation_status`).
* **Adjusted vs unadjusted** series are explicit, and **provider-continuous vs
  derived/stitched** rolls are kept separate; no roll record implies best execution.

## Raw-Data-Level Acceptance

* `RawDataObject` is **immutable**, **content-addressed/versioned** (`content_hash`),
  **local-only**, **never committed**, and **manifest/request linked**
  (`request_id`, `chunk_id`).
* `LocalDataRootPolicy` enforces a local, ignored data root outside the repo (suggested
  `~/alpha_data/alpha_system` via `ALPHA_DATA_ROOT`); a missing local-data-root policy
  blocks raw writes.
* Raw objects imply no canonical truth.

## Canonical-Bar-Level Acceptance

* `CanonicalBarRecord` carries `event_ts`, `bar_start_ts`, `bar_end_ts`, `available_ts`,
  and `ingested_at` as **distinct** fields, plus `instrument_id`, `contract_id`,
  `series_id`, OHLCV, `source`, `source_request_id`, `data_version`, `quality_flags`, and
  `session_label`.
* `available_ts >= bar_end_ts` for every bar; missing `available_ts` blocks
  canonicalization.
* OHLC is valid (`low <= open/close <= high`, no zero/negative prices); **quality flags are
  explicit**; a **session label** is present.
* The record implies no alpha value or tradability.

## Timestamp-Semantics-Level Acceptance

* `TimestampSemanticsPolicy` defines `event_ts`, `bar_start_ts`, `bar_end_ts`,
  `available_ts`, and `ingested_at` and aligns with the V1 **no-lookahead** semantics.
* `available_ts` represents **when the completed bar would have been usable in
  research/backtest**, not merely when the historical API returned it.
* `ingested_at` is **separate** from `available_ts`; provider timestamps are not treated as
  research-ready without canonical validation. The `tests/no_lookahead` suite passes.

## Data-Quality-Level Acceptance

* `DataQualityReport` covers **gaps, duplicates, non-monotonic timestamps, OHLC errors,
  zero/negative prices, zero-volume anomalies, DST anomalies, session coverage, roll
  discontinuities, and provider errors**.
* Findings are **classified as warnings vs blockers**; the report carries an explicit
  `status`.
* The report **fails closed**: silent gaps or timestamp defects produce a blocking status,
  and silent gaps block versioning. The report implies no alpha readiness.

## Coverage-Report-Level Acceptance

* `CoverageReport` covers coverage **by symbol, contract, session, and partition**, plus
  `missing_intervals` and `incomplete_chunks`.
* **Silent gaps fail**: undocumented missing coverage produces a blocking result rather
  than passing quietly.
* The coverage report implies no quality pass unless linked to a `DataQualityReport`.

## Dataset-Version-Level Acceptance

* `DatasetVersion` requires a linked **quality report**, **coverage report**, and **source
  manifest** before it is considered ready.
* It carries `manifest_hash`, `code_hash`, `config_hash`, and `quality_report_hash` (plus
  source, universe, bar size, what_to_show, start/end, contract universe, roll policy).
* The dataset version is **reproducible** from those hashes and implies no research
  approval.

## Dataset-Partition-Level Acceptance

* `DatasetPartitionPlan` defines `development_partition` (2018-01-01 → 2022-12-31),
  `validation_partition` (2023-01-01 → 2024-12-31), `locked_test_candidate`
  (2025-01-01 → as_of_run), and an optional `latest_shadow_candidate`.
* **Data QA may inspect coverage across all partitions.**
* **Alpha research must not use `locked_test_candidate` without Governance metadata**, and
  any use of locked partitions must create contamination metadata; the plan carries
  explicit `contamination_metadata_rules` and implies no research approval.

## Local-Artifact-Policy-Level Acceptance

* Raw and canonical real market data, provider responses, and account info are
  **local-only** and never committed; campaign files may describe paths but never commit
  data.
* `git ls-files runs` returns empty; `find data -type f ! -name README.md ! -name
  .gitkeep` returns empty; `find metadata -type f ! -name README.md ! -name .gitkeep`
  returns empty.
* No `*.parquet`/`*.arrow`/`*.feather`/`*.sqlite`/`*.db`/`*.log` outside documented tiny
  synthetic `tests/fixtures/**`; `find artifacts -type f -size +1M` returns empty.
* Explicit staging only; no `git add .` / `git add -A`; no force push.

## Workflow 2 Integration Acceptance

* Run-local handoff/review/verdict artifacts remain under `runs/**` and are **never
  committed**.
* Commit-eligible handoffs live under `handoffs/ALPHA_DATA_FOUNDATION_V1/**` and
  commit-eligible reviews under `reviews/ALPHA_DATA_FOUNDATION_V1/**`.
* The Workflow 2 state order, STOP/resume semantics, and bounded-repair routing are
  honored; RED phases (`DATA-P22`, `DATA-P23`) are not auto-merged and require scoped
  authorization.

## Review-Level Acceptance

* Every **YELLOW** and **RED** phase has a fresh Claude Opus 4.8 xhigh review and a
  `verdict.json`.
* Merged phases have `PASS` or `PASS_WITH_WARNINGS` verdicts; `FAIL`/`BLOCKED`/`REWORK`
  block merge.
* Reviews verify phase-scope compliance, object completeness, fail-closed validation, the
  clientId `101`/`102` hard-block, the read-only boundary and order-method kill switch,
  manifest/pacing/resume presence, absence of silent gaps, continuous-not-as-dated truth,
  canonical timestamp distinctness, dataset-version reproducibility, artifact-policy
  compliance, and absence of prohibited scope and claims.

## Prohibited Acceptance Shortcuts

The campaign is **not** accepted if any of the following is true:

* the IBKR connector works but the clientId guard is missing;
* clientId `101` or `102` is accepted;
* an order-placement API is reachable through the data module;
* a provider pull occurs without a request manifest;
* raw provider data is overwritten;
* there is no resume ledger;
* there is no pacing guard;
* data gaps are silently ignored;
* continuous futures are treated as dated-contract truth;
* dated contracts beyond IBKR availability are claimed without evidence;
* canonical bars are missing `available_ts`;
* `event_ts` / `bar_end_ts` / `available_ts` are conflated;
* there is no contract master;
* `tick_size` / `multiplier` / `tick_value` are missing;
* RTH/ETH sessions are not represented;
* the roll policy is undocumented;
* a dataset version is not registered;
* raw or heavy data is committed;
* any alpha/profitability/tradability claim is introduced;
* a real-data pull is run in CI;
* any broker/live/paper scope is introduced.

## Required Final Validation Commands

```bash
cd ~/projects/alpha_system
git status --short
python tools/verify.py --smoke
python tools/verify.py --all
python -m pytest tests/unit/data -q
python -m pytest tests/integration/data -q
python -m pytest tests/no_lookahead -q

git ls-files runs
find data -type f ! -name README.md ! -name ".gitkeep" -print
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
```

## Required Semantic Done-Check

Beyond passing tests, the final done-check (Claude Opus) must affirm that:

* the gates genuinely **block missing prerequisites** (no manifest, no pacing guard, no
  local-data-root policy, no quality/coverage report, no dataset version);
* there are **no silent gaps** — coverage and quality reports fail closed;
* the clientId `101`/`102` **hard-block is real** and fail-closed, not a warning;
* the IBKR **read-only boundary is real** — order/account APIs are unreachable from the
  data module and the order-method kill switch holds;
* **continuous futures are not used as dated-contract truth**;
* the **canonical timestamps are correct** — `event_ts` / `bar_start_ts` / `bar_end_ts` /
  `available_ts` / `ingested_at` are distinct and `available_ts >= bar_end_ts`;
* **dataset versions are reproducible** from manifest/code/config/quality hashes;
* **no prohibited scope or claim** exists (broker/live/paper/order-routing, real-data pull
  in CI, alpha/profitability/tradability);
* the **artifact audit is clean** (no `runs/**`, raw, canonical, heavy, provider, account,
  or local-DB artifacts committed).

## Final Closeout Requirements

* `campaigns/ALPHA_DATA_FOUNDATION_V1/CLOSEOUT.md` exists and records the final verdict and
  any warnings.
* `ACTIVE_CAMPAIGN.md` reflects campaign completion and points at the next campaign or
  none.
* Durable lessons are added to `project-skill` when applicable.
* Next-campaign readiness is recorded (e.g. `ALPHA_FEATURE_LABEL_FOUNDATION_V1` and later
  campaigns may consume this truth layer only under their own authorized contracts and the
  governance + data-admissibility gates this campaign installs).

## Final Acceptance Verdicts

### `COMPLETE`
All campaign-level criteria met, all data-lifecycle gates genuinely block missing
prerequisites, the semantic done-check is clean, the artifact audit is clean, and no
prohibited scope or claims exist.

### `COMPLETE_WITH_WARNINGS`
All hard criteria met, but non-blocking warnings (e.g. documented deferrals, an
unexercised RED smoke-pull pending authorization, or minor limitations) are recorded in
`CLOSEOUT.md`.

### `BLOCKED`
A hard criterion cannot be met (e.g. a gate cannot be made to fail closed, the clientId
hard-block or read-only boundary cannot be guaranteed, or a required object cannot be
completed in scope). The blocker is recorded truthfully; fake completion is forbidden, and
a truthful `BLOCKED` is preferred over a false `COMPLETE`.
