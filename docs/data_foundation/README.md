# Data Foundation Docs

This directory is the durable documentation root for the
`ALPHA_DATA_FOUNDATION_V1` campaign. It describes the read-only,
provenance-rich, quality-gated historical futures data foundation for
ES/NQ/RTY research at a high level.

This docs root is an entry point only. It does not add data-package source,
tests, configs, templates, connector code, IBKR pull behavior, paper trading,
live trading, order routing, account access, real-time feeds, or market
claims.

> **Post-closeout providers (current).** The data foundation now spans two
> providers with distinct roles. **Databento** is the primary deep-history
> research source (GLBX.MDP3 ES/NQ/RTY OHLCV-1m + BBO-1m, 2018–2026, registered
> as 27 local-only DatasetVersions) — see the `databento/` subdirectory and
> `handoffs/ALPHA_DATA_FOUNDATION_V1/ADF1_DATABENTO_ES_NQ_RTY_OHLCV_BBO_DEEP_HISTORY.md`. **IBKR** is the
> read-only broker-validation source (~2 years of available depth). The original
> campaign text below describes the IBKR bootstrap posture and remains as
> historical campaign documentation. All real data stays local-only under
> `ALPHA_DATA_ROOT`; nothing is committed.

## Campaign Contract Bundle

The campaign source of truth lives in `campaigns/ALPHA_DATA_FOUNDATION_V1/`:

- `GOAL.md`
- `PHASE_PLAN.md`
- `campaign.yaml`
- `ACCEPTANCE.md`
- `RISK_REGISTER.md`
- `RUNBOOK.md`

Use the repository-level `ACTIVE_CAMPAIGN.md` as the active-campaign pointer.
Do not create `campaigns/ALPHA_DATA_FOUNDATION_V1/ACTIVE_CAMPAIGN.md`.

## Data Foundation Overview

- `DATA_FOUNDATION_OVERVIEW.md` summarizes the read-only data truth layer,
  campaign hard rules, data-foundation object list, lifecycle state model, and
  IBKR read-only posture.
- `MINI_BATCH_PLAN.md` describes the ES/NQ/RTY mini main-batch plan, optional
  QA/diagnostic panels, the mini/micro separation guard, the concurrency limit,
  and the no-authorization posture.
- `PROVENANCE.md` documents the continuous-vs-dated futures provenance split,
  the mandatory continuous diagnostic labels, discovered-not-assumed dated
  availability, adjusted-vs-unadjusted explicitness, and the no-roll-logic
  boundary.
- `SESSIONS_AND_CALENDAR.md` documents the DATA-P12 `SessionTemplate` and
  `TradingCalendarRecord` contracts, explicit timezone handling, DST and
  early-close representation, holiday handling, and the no-official-calendar
  non-claims.
- `BID_ASK_PILOT.md` documents the optional bounded BID_ASK pilot plan, heavier
  pacing/storage posture, spread-proxy diagnostics scaffold, quality/coverage
  linkage, and non-goals.
- `SYNTHETIC_FIXTURE_TESTS.md` documents the DATA-P21 synthetic IBKR fixture
  tests, the no-external-call mechanism, composed fail-closed assertions, and
  artifact-policy posture.
- `SMOKE_PULL.md` documents the DATA-P22 authorized read-only IBKR smoke-pull
  entry point, runtime gates, never-in-CI rule, bounded scope, local-only
  outputs, and artifact audit.
- `BACKFILL_RUNBOOK.md` documents the DATA-P23 local backfill resume drill,
  authorization gates, local-only output locations, resume-token behavior,
  and artifact audit.
- `END_TO_END_DRY_RUN.md` documents the DATA-P24 synthetic end-to-end dry run,
  lifecycle-block assertions, acceptance-audit posture, and closeout verdict.
- `DATASET_CONSUMPTION.md` documents how later feature/label campaigns resolve
  and consume accepted local DatasetVersions while preserving no-lookahead,
  partition, and no-claims rules.

The overview references the campaign contract bundle instead of duplicating
field-level requirements, acceptance gates, risk controls, or operator
procedures.

## Hard Data Rules

- IBKR is a bootstrap historical-data source only.
- No broker, order, account, paper, live, or real-time signal scope exists in
  this docs root.
- clientId `101` and `102` are hard-blocked; the data namespace is `201-209`
  with default `201`.
- No provider pull may occur without a manifest, pacing guard, resume ledger,
  local-data-root policy, and the required authorization environment for
  external IBKR calls.
- Raw provider responses, canonical data, provider/account artifacts, local
  DBs, logs, caches, heavy artifacts, and `runs/**` remain local-only.
- Explicit staging is required. `git add .`, `git add -A`, and force push are
  forbidden.
- No alpha search, factor research, label research, strategy research, or
  alpha/profitability/tradability claim is introduced here.

## Object Families

The data-foundation objects are grouped by purpose:

- Access and safety: `DataSourceProfile`, `IBKRConnectionProfile`,
  `IBKRClientIdPolicy`, `DataAccessMode`, `LocalDataRootPolicy`.
- Requests and pulls: `HistoricalRequestSpec`,
  `HistoricalRequestManifest`, `HistoricalChunkRecord`,
  `RequestPacingPolicy`, `HistoricalPullLedger`, `ProviderErrorRecord`,
  `DataIngestionRunRecord`.
- Instruments and contracts: `InstrumentMasterRecord`,
  `FuturesContractRecord`, `ContractDetailsSnapshot`.
- Sessions, rolls, and series: `SessionTemplate`,
  `TradingCalendarRecord`, `RollPolicy`, `RollCalendarRecord`,
  `ContinuousFuturesSeriesRecord`, `DatedFuturesSeriesRecord`.
- Data layers and quality: `RawDataObject`, `ParsedBarRecord`,
  `CanonicalBarRecord`, `DataQualityReport`, `CoverageReport`,
  `DatasetVersion`, `TimestampSemanticsPolicy`.
- Batches and partitions: `SymbolBatchPlan`, `MicroBatchPolicy`,
  `BidAskPilotPlan`, `SpreadProxyMetric`, `DatasetPartitionPlan`.

Field-level contracts and acceptance criteria remain in `campaign.yaml` and
`ACCEPTANCE.md`.

`DATASET_VERSION.md` documents the DATA-P17 `DatasetVersion` contract, registry
adapter, reproducibility hash binding, lifecycle gate, and local-only registry
policy.

`DATASET_CONSUMPTION.md` documents DatasetVersion lookup, the first real local
DatasetVersion ID, canonical timestamp semantics, and downstream
feature/label consumption boundaries.

`PARTITION_PLAN.md` documents the DATA-P18 `DatasetPartitionPlan` contract,
canonical development / validation / locked-test candidate windows, optional
latest-shadow candidate, and locked-test contamination-metadata rules.

## Lifecycle Summary

Future data-foundation objects move through this controlled lifecycle:

```text
NOT_REQUESTED
REQUEST_PLANNED
REQUEST_AUTHORIZED
REQUEST_SUBMITTED
PARTIAL_RAW
RAW_COMPLETE
RAW_FAILED
PARSED
CANONICALIZED
QUALITY_CHECKED
VERSIONED
REJECTED
QUARANTINED
READY_FOR_RESEARCH
```

`READY_FOR_TRADING`, `LIVE_FEED_READY`, `BROKER_ENABLED`, `ALPHA_VALIDATED`,
and `PROFITABLE` are prohibited MVP states. They may be named only as future,
non-MVP concepts and must remain unreachable in this campaign.
