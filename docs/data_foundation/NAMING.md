# Data Foundation Naming Contract

`DATA-P01` fixes the canonical names and path conventions for the
`ALPHA_DATA_FOUNDATION_V1` data-foundation layer. Later DATA phases may add object
schemas, validation behavior, persistence, and provider integrations, but they must
preserve these object names, ID prefixes, module names, and directory roots unless
this contract is explicitly updated.

This document is a naming contract only. It does not define validation behavior,
registry behavior, provider connectivity, data completeness, alpha validity,
profitability, tradability, paper readiness, live readiness, broker readiness, or
production readiness.

## Package Layout

The existing data package remains:

```text
src/alpha_system/data/
```

`DATA-P01` adds an additive namespace under that existing package:

```text
src/alpha_system/data/foundation/
```

The new namespace avoids collisions with pre-existing sibling modules such as
`bar_schema.py`, `calendar.py`, `contracts.py`, `paths.py`, `quality.py`,
`sessions.py`, `storage.py`, `universe.py`, `validation.py`, and `versions.py`.
Importing `alpha_system.data` and `alpha_system.data.foundation` must not perform
network access, filesystem writes, credential reads, registry writes, data
ingestion, broker calls, order routing, validation, or report generation.

## Canonical Objects And ID Prefixes

Object names must match `campaigns/ALPHA_DATA_FOUNDATION_V1/campaign.yaml` under
`data_foundation_objects` and the DATA-P01 phase spec. Canonical IDs use the form
`<prefix>_<token>`. Later phases own token format, ID generation, and validation
behavior. This phase fixes only the object names and prefixes.

| Object name | ID prefix | Canonical module |
| --- | --- | --- |
| `DataSourceProfile` | `dsrc` | `alpha_system.data.foundation.sources` |
| `LocalDataRootPolicy` | `ldrp` | `alpha_system.data.foundation.sources` |
| `DataAccessMode` | `dam` | `alpha_system.data.foundation.sources` |
| `IBKRConnectionProfile` | `icp` | `alpha_system.data.foundation.ibkr` |
| `IBKRClientIdPolicy` | `icidp` | `alpha_system.data.foundation.ibkr` |
| `HistoricalRequestSpec` | `hrs` | `alpha_system.data.foundation.requests` |
| `HistoricalRequestManifest` | `hrm` | `alpha_system.data.foundation.requests` |
| `HistoricalChunkRecord` | `hcr` | `alpha_system.data.foundation.requests` |
| `HistoricalPullLedger` | `hpl` | `alpha_system.data.foundation.requests` |
| `ProviderErrorRecord` | `perr` | `alpha_system.data.foundation.requests` |
| `RequestPacingPolicy` | `rpp` | `alpha_system.data.foundation.requests` |
| `DataIngestionRunRecord` | `dirr` | `alpha_system.data.foundation.requests` |
| `RawDataObject` | `raw` | `alpha_system.data.foundation.bars` |
| `ParsedBarRecord` | `pbar` | `alpha_system.data.foundation.bars` |
| `CanonicalBarRecord` | `cbar` | `alpha_system.data.foundation.bars` |
| `TimestampSemanticsPolicy` | `tsp` | `alpha_system.data.foundation.bars` |
| `InstrumentMasterRecord` | `imr` | `alpha_system.data.foundation.instruments` |
| `FuturesContractRecord` | `fcr` | `alpha_system.data.foundation.instruments` |
| `ContractDetailsSnapshot` | `cds` | `alpha_system.data.foundation.instruments` |
| `SessionTemplate` | `stpl` | `alpha_system.data.foundation.sessions` |
| `TradingCalendarRecord` | `tcal` | `alpha_system.data.foundation.sessions` |
| `RollPolicy` | `rpol` | `alpha_system.data.foundation.rolls` |
| `RollCalendarRecord` | `rcal` | `alpha_system.data.foundation.rolls` |
| `ContinuousFuturesSeriesRecord` | `cfsr` | `alpha_system.data.foundation.series` |
| `DatedFuturesSeriesRecord` | `dfsr` | `alpha_system.data.foundation.series` |
| `SymbolBatchPlan` | `sbp` | `alpha_system.data.foundation.batches` |
| `MicroBatchPolicy` | `mbp` | `alpha_system.data.foundation.batches` |
| `DatasetVersion` | `dver` | `alpha_system.data.foundation.datasets` |
| `DataQualityReport` | `dqr` | `alpha_system.data.foundation.datasets` |
| `CoverageReport` | `covr` | `alpha_system.data.foundation.datasets` |
| `DatasetPartitionPlan` | `dpp` | `alpha_system.data.foundation.datasets` |

Prefixes are lower snake-free tokens suitable for `<prefix>_<token>` IDs. They must
not be reused for a different object family without updating this contract.

## Python Module Names

Python modules in `alpha_system.data.foundation` use lower snake_case names:

- `sources.py`
- `ibkr.py`
- `requests.py`
- `bars.py`
- `instruments.py`
- `sessions.py`
- `rolls.py`
- `series.py`
- `batches.py`
- `datasets.py`

Object classes use the exact PascalCase names in the canonical object table.
`run_connection_doctor` is a DATA-P04 placeholder only and must not make an IBKR
connection until the authorized later phase implements that behavior.

## File Naming

Data-foundation documentation uses clear uppercase topic names when it defines a
durable contract, for example:

```text
docs/data_foundation/NAMING.md
```

Data configuration and template files added in later phases should use lower
snake_case names. Structured configuration files should use `.yaml` unless a later
spec authorizes another format. Provider responses, raw data, canonical data,
Parquet, Arrow, Feather, local DBs, caches, logs, and generated report bundles are
not commit-eligible under this naming contract.

## Directory Roots

Commit-eligible data-foundation code, tests, docs, config placeholders, and
template placeholders live under:

```text
src/alpha_system/data/foundation/
tests/unit/data/
docs/data_foundation/
configs/data/
templates/data/
handoffs/ALPHA_DATA_FOUNDATION_V1/
reviews/ALPHA_DATA_FOUNDATION_V1/
```

The local data root is configured by `ALPHA_DATA_ROOT`. No real local path is
committed in this phase. Data under `ALPHA_DATA_ROOT` is local-only and must remain
outside git unless a later spec explicitly authorizes a tiny synthetic fixture.

Workflow 2 run artifacts are local-only. Nothing under `runs/` is
commit-eligible, including run-local handoffs, reviews, verdicts, checks, repair
attempts, state files, ledgers, summaries, or STOP files.

No data-foundation naming convention may imply alpha validity, profitability,
tradability, paper readiness, live readiness, broker readiness, account access,
order access, execution permission, capital allocation, data completeness, or
production readiness.
