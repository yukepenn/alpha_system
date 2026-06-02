# ADR-0001: Local-First Stack

## Status

Accepted for v1 design baseline.

## Context

`alpha_system` needs a research stack that can run locally, reproduce results,
and avoid infrastructure dependencies during v1. The campaign is focused on an
offline Alpha Research Platform foundation, not server operations.

## Decision

Use local Parquet for large datasets. Use SQLite as the local metadata and
registry source of truth, as design intent only in this phase. Use DuckDB for
local SQL over Parquet, Polars for lazy dataframe pipelines, NumPy for arrays,
and Numba for hot loops and Fast path acceleration only.

Reports are Markdown, CSV, and optional static HTML. No server is required.

The following are not required in v1 and must not become hard dependencies:
ClickHouse, QuestDB, DolphinDB, kdb+, ArcticDB, S3, cloud object storage, paid
databases, database servers, Dagster, Prefect, Ray, MLflow server, or web UI.

## Consequences

The v1 platform remains local-first, reviewable, and reproducible. Later
campaigns may reconsider server or cloud tools, but they are outside this
baseline.

This ADR does not implement packages, schemas, registries, data storage, or
runtime behavior.
