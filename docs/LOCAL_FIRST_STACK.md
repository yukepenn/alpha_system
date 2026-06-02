# Local-First Stack

## Decision

The v1 stack is local-first and file-backed. It avoids cloud object storage,
paid databases, database servers, and server-first orchestration.

## Required V1 Components

| Component | Role |
| --- | --- |
| Local Parquet | Large local datasets and generated local tables. |
| SQLite | Local metadata and registry source of truth, as design intent. |
| DuckDB | Local SQL over Parquet and analytical joins. |
| Polars | Lazy dataframe pipelines for data and factor workflows. |
| NumPy | Array operations and deterministic numerical paths. |
| Numba | Hot loops and accelerated fast path only. |
| Markdown | Human-readable reports and handoffs. |
| CSV | Simple tabular summaries and exports. |
| Static HTML | Optional local report rendering with no server. |

## Explicit V1 Exclusions

The following are not required in v1 and must not become hard dependencies:

- ClickHouse
- QuestDB
- DolphinDB
- kdb+
- ArcticDB
- S3
- cloud object storage
- paid database services
- database servers
- Dagster
- Prefect
- Ray
- MLflow server
- web UI

These exclusions protect local reproducibility, reviewability, and low
operating complexity.

## Local-Only Storage Rules

Raw data, canonical data, factor values, label values, caches, local SQLite
files, generated reports, logs, and run state are local-only artifacts. They are
not committed. Large files such as Parquet, Arrow, Feather, DB files, logs, and
model binaries remain out of git unless a later spec explicitly authorizes a
tiny synthetic fixture exception.

## Acceleration Boundary

Numba is acceleration only. It may support a Fast path after the Reference
engine exists and parity is proven on fixtures. It does not define semantics,
fill truth, accounting truth, or PnL truth.

## No Server Requirement

The v1 researcher should be able to run the platform locally without an object
store, hosted database, database daemon, workflow server, ML tracking server,
or web application.
