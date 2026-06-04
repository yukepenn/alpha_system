# Data Foundation Docs

This directory is the durable documentation root for the
`ALPHA_DATA_FOUNDATION_V1` campaign. It describes the read-only,
provenance-rich, quality-gated historical futures data foundation for
ES/NQ/RTY research at a high level.

This docs root is an entry point only. It does not add data-package source,
tests, configs, templates, connector code, IBKR pull behavior, paper trading,
live trading, order routing, account access, real-time feeds, or market
claims.

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
  `DatasetPartitionPlan`.

Field-level contracts and acceptance criteria remain in `campaign.yaml` and
`ACCEPTANCE.md`.

`DATASET_VERSION.md` documents the DATA-P17 `DatasetVersion` contract, registry
adapter, reproducibility hash binding, lifecycle gate, and local-only registry
policy.

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
