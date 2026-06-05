# Data Foundation Overview

`ALPHA_DATA_FOUNDATION_V1` establishes the read-only real-market-data truth
layer for `alpha_system`. The layer is for historical ES/NQ/RTY futures data
used by future research workflows. It owns provenance, timestamp semantics,
quality checks, coverage checks, dataset versioning, and local-only artifact
discipline.

This overview is descriptive only. It does not implement data-foundation
objects, lifecycle transitions, schemas, validation, data pulls, tests,
connector behavior, IBKR code, broker behavior, paper trading, live trading,
order routing, account access, deployment behavior, or market claims.

> **Post-closeout update.** This overview was authored for the IBKR bootstrap
> posture. Since closeout, **Databento** is the primary deep-history research
> source (GLBX.MDP3 ES/NQ/RTY OHLCV-1m + BBO-1m, 2018–2026, registered as
> local-only DatasetVersions), and **IBKR** is the read-only broker-validation
> source. See `docs/data_foundation/databento/` and
> `handoffs/ALPHA_DATA_FOUNDATION_V1/ADF1_DATABENTO_ES_NQ_RTY_OHLCV_BBO_DEEP_HISTORY.md`. The IBKR-centric
> description below remains as historical campaign documentation.

## Read-Only Truth Layer

The campaign admits real historical market data only after the data can be
requested, stored, parsed, canonicalized, checked, versioned, and traced back
through durable provenance records. Raw provider responses, parsed bars,
canonical bars, quality reports, coverage reports, and dataset versions are
separate concepts.

The truth layer is local-first and conservative:

- real data remains outside git;
- provider responses are local-only;
- canonical data is not committed;
- quality and coverage gates fail closed on silent gaps or timestamp defects;
- continuous, dated, stitched, adjusted, and unadjusted futures series remain
  explicitly separated;
- `event_ts`, `bar_start_ts`, `bar_end_ts`, `available_ts`, and `ingested_at`
  must not be conflated by future implementation phases.

## Campaign Hard Rules

The campaign contract bundle is the source of truth:

- `campaigns/ALPHA_DATA_FOUNDATION_V1/GOAL.md`
- `campaigns/ALPHA_DATA_FOUNDATION_V1/PHASE_PLAN.md`
- `campaigns/ALPHA_DATA_FOUNDATION_V1/campaign.yaml`
- `campaigns/ALPHA_DATA_FOUNDATION_V1/ACCEPTANCE.md`
- `campaigns/ALPHA_DATA_FOUNDATION_V1/RISK_REGISTER.md`
- `campaigns/ALPHA_DATA_FOUNDATION_V1/RUNBOOK.md`

The high-level rules are:

- IBKR is read-only historical data only.
- No order, account, broker execution, paper trading, live trading, or
  real-time signal surface may be introduced.
- clientId `101` and `102` are forbidden and must fail closed; the data client
  namespace is `201-209`, with default `201`.
- No provider pull may occur without a manifest, pacing guard, resume ledger,
  and local-data-root policy.
- External IBKR historical calls require the data-pull authorization
  environment and never run in CI.
- No silent gaps are accepted; incomplete chunks, provider errors, timestamp
  defects, session defects, and roll defects must be visible.
- Raw data, canonical data, provider responses, account artifacts, local DBs,
  logs, caches, heavy artifacts, and `runs/**` are local-only.
- Mini (`ES`, `NQ`, `RTY`) and micro (`MES`, `MNQ`, `M2K`) batches are kept
  separate.
- No alpha search, factor research, label research, strategy research,
  portfolio allocation, ML/DL, L2 replay, production execution, or
  alpha/profitability/tradability claim is introduced by this campaign.

## Data-Foundation Object List

The required object names are listed here for navigation. Field-level
requirements live in `campaign.yaml` and acceptance rules live in
`ACCEPTANCE.md`.

- `DataSourceProfile`
- `IBKRConnectionProfile`
- `IBKRClientIdPolicy`
- `HistoricalRequestSpec`
- `HistoricalRequestManifest`
- `HistoricalChunkRecord`
- `HistoricalPullLedger`
- `ProviderErrorRecord`
- `RawDataObject`
- `ParsedBarRecord`
- `CanonicalBarRecord`
- `InstrumentMasterRecord`
- `FuturesContractRecord`
- `ContractDetailsSnapshot`
- `SessionTemplate`
- `TradingCalendarRecord`
- `RollPolicy`
- `RollCalendarRecord`
- `DatasetVersion`
- `DataQualityReport`
- `CoverageReport`
- `DataIngestionRunRecord`
- `LocalDataRootPolicy`
- `DataAccessMode`
- `ContinuousFuturesSeriesRecord`
- `DatedFuturesSeriesRecord`
- `MicroBatchPolicy`
- `SymbolBatchPlan`
- `RequestPacingPolicy`
- `TimestampSemanticsPolicy`
- `DatasetPartitionPlan`

## Data Lifecycle State Model

The campaign lifecycle describes the future state model for data-foundation
objects. This overview does not implement the transitions.

```text
NOT_REQUESTED
  -> REQUEST_PLANNED
  -> REQUEST_AUTHORIZED
  -> REQUEST_SUBMITTED
  -> PARTIAL_RAW
  -> RAW_COMPLETE
  -> PARSED
  -> CANONICALIZED
  -> QUALITY_CHECKED
  -> VERSIONED
  -> READY_FOR_RESEARCH

Any state -> REJECTED
Any state -> QUARANTINED
REQUEST_SUBMITTED -> RAW_FAILED
```

Transition prerequisites are defined by `campaign.yaml`. At a high level:
request planning requires a `HistoricalRequestSpec`; authorization requires a
manifest, clientId validation, and local-data-root validation; submission of an
external IBKR request requires the data-pull authorization environment; raw
completion requires every chunk to be accounted for or explicitly recorded as
incomplete; canonicalization requires timestamp, session, and contract
normalization; versioning requires coverage, manifest, code, and config hashes;
research availability requires a dataset version, non-blocking quality status,
coverage status, and artifact-policy pass.

The prohibited MVP state names are:

- `READY_FOR_TRADING`
- `LIVE_FEED_READY`
- `BROKER_ENABLED`
- `ALPHA_VALIDATED`
- `PROFITABLE`

These names are future, non-MVP concepts only. They must not be reachable by
any transition implemented in this campaign.

## IBKR Read-Only Posture

IBKR is scoped only as a bootstrap historical-data source. The data foundation
must not expose order placement, account trading, position polling, paper
trading, live trading, broker execution, or a real-time signal loop.

The intended default profile is historical-data-only with `read_only_mode =
true`, a connection doctor before any pull, `host 127.0.0.1`, `port 4002`, and
clientId `201` unless an allowed data client ID in `201-209` is configured.
clientId `101` and `102` are hard-blocked rather than warned about.

Future phases may add code that enforces this posture. This overview only
records the campaign-level contract and points to the bundle for the exact
requirements.
