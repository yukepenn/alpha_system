# Canonical 1-Minute Data Layer

ASV1-P06 defines the local, canonical 1-minute bar representation used by later
offline research workflows. It is a schema, path, validation, and fixture layer
only. It does not ingest vendor data, build production datasets, compute
factors or labels, create signals, run strategies, or define backtest execution
semantics.

## Schema

Canonical bars must contain these fields in contract order:

```text
instrument_id
session_id
bar_index
bar_start_ts
bar_end_ts
event_ts
available_ts
open
high
low
close
volume
vwap
trade_count
bid
ask
spread
source_version
data_version
quality_flags
```

The schema is aligned to `alpha_system.data.contracts.OneMinuteBar`.
Normalized Python records use timezone-aware `datetime` values for timestamp
fields, `Decimal` values for price/size fields, `int` values for `bar_index`
and `trade_count`, strings for identifiers and versions, and
`tuple[str, ...]` for `quality_flags`.

## Point-In-Time Semantics

`bar_start_ts` and `bar_end_ts` describe the interval represented by the bar.
`event_ts` records when the bar event occurred. `available_ts` records when the
completed bar can be consumed by downstream research code. These are separate
fields with separate meanings.

Validation requires:

- `bar_start_ts < bar_end_ts`
- `event_ts` inside the bar interval by default
- `available_ts >= event_ts`
- `available_ts >= bar_end_ts + configured latency`

The data layer does not introduce same-bar execution behavior. Downstream
components must use availability timestamps rather than infer that a value is
usable before the completed bar and latency boundary.

## Validation

`alpha_system.data.validation` fails closed for:

- missing required fields
- missing instrument, session, bar index, `data_version`, or `source_version`
- invalid field types on normalized records
- invalid timestamp ordering
- OHLC range violations
- negative volume
- negative `trade_count`
- invalid bid/ask values
- spread mismatches when bid and ask are present
- duplicate instrument/session/bar-index keys
- duplicate instrument/session/bar-start timestamp keys

## Storage And Query Scope

`alpha_system.data.storage` provides fixture CSV loading and local Parquet
read/write helpers. Parquet operations require the local Polars dependency at
runtime and write only to caller-provided local paths, usually temp paths in
tests or local-only data directories in later phases.

`alpha_system.data.query` provides fixture-scoped DuckDB helpers over local CSV
or Parquet files and Polars lazy helpers over local CSV fixtures. DuckDB uses an
in-memory connection. No database server, object store, cloud path, vendor
client, or network service is used.

## Local Artifact Discipline

The repository keeps durable code, docs, configs, tests, and tiny synthetic
fixtures in git. Generated raw, canonical, factor, label, cache, report,
SQLite, DB, Parquet, Arrow, Feather, log, and model artifacts remain local-only
unless a later phase explicitly authorizes a tiny synthetic fixture exception.

The `data/` subdirectories keep their semantics:

- `data/raw`
- `data/canonical`
- `data/factors`
- `data/labels`
- `data/cache`

Files produced under those directories are local-only artifacts and are not
commit-eligible in this phase.

## Fixtures

`tests/fixtures/data/synthetic_1min_bars.csv` is a three-row synthetic,
deterministic, correctness-only fixture. It is not real raw market data and is
not evidence for any market behavior. Its purpose is to exercise schema,
validation, DuckDB, and Polars code paths on tiny local data.
