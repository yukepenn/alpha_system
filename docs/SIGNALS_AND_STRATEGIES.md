# Signals And Strategies

ASV1-P14 defines the first signal and StrategySpec layer for local research.
It converts reviewed factor values into strategy-intent signal records without
running a backtest or simulating execution.

## Signal Records

Signal records carry point-in-time provenance:

- instrument id
- `event_ts`
- `available_ts`
- session id
- bar index
- signal type
- direction
- optional score, confidence, and desired exposure
- strategy id and strategy version
- factor version dependencies
- quality flags

`available_ts` must be at or after `event_ts` and must not be earlier than the
latest `available_ts` of the input factor values used by the signal.

## StrategySpec

`StrategySpec` declares signal intent only:

- entry signal
- exit signal
- direction
- optional confidence score
- optional desired exposure
- required factor dependencies

Strategies may read only declared factor value records. Labels and raw ad hoc
columns are rejected as live strategy inputs.

## Local Stores

Signal stores write JSONL records and small manifests only to temp/local paths
outside the repository. They do not write committed signal datasets, DB files,
Parquet, Arrow, Feather, logs, raw data, canonical data, factor stores, or
label stores.

## Registry

Strategy versions use the existing `strategy_registry` and `strategy_versions`
tables. ASV1-P14 does not add registry migrations. Tests exercise registry
version writes only in temporary SQLite databases outside the repository.

## Scope Boundary

This layer does not implement fills, slippage, commission, position sizing,
order lifecycle, portfolio aggregation, management accounting, paper trading,
live trading, broker operations, or backtest execution.
