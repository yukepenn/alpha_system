# Alpha System Plan

## Purpose

`alpha_system` is a local-first Alpha Research Platform foundation. It is not
merely a backtester and it is not a live trading system. The v1 platform is
intended to support offline research over point-in-time data, reproducible
factor studies, deterministic reference backtests, bounded grid exploration,
reviewable reports, and local automation handoffs.

The plan for v1 is to establish clear research boundaries before
implementation begins. Later phases must conform to this baseline.

## V1 Design Principles

- Local-first by default. Large datasets live as local Parquet files.
- SQLite is the local metadata and registry source of truth, as design intent.
- DuckDB provides local SQL over Parquet.
- Polars provides lazy dataframe pipelines.
- NumPy handles array operations.
- Numba is reserved for hot loops and accelerated fast paths only.
- Reports are Markdown, CSV, and optional static HTML. No server is required.
- Every material result must be reproducible from a run manifest.
- The Reference 1-minute backtest engine is the single canonical PnL truth for
  v1.
- Fast research simulation is not execution truth.
- No broker, paper trading, live trading, order routing, or production
  execution is in v1 scope.

## Planned Research Flow

The target workflow moves from data quality to reviewed research evidence:

1. Validate raw or vendor-provided local inputs.
2. Build canonical 1-minute bars with point-in-time timestamps.
3. Validate factor definitions before materialization.
4. Run factor diagnostics before strategy or grid work.
5. Run bounded study grids only after diagnostics justify the question.
6. Run survivor management grids for constrained candidates.
7. Validate finalists with the Reference backtest truth model.
8. Build reports that separate evidence, limitations, and review state.
9. Record versions, hashes, run manifests, and failed runs.

The workflow does not imply that any factor, strategy, or model is alpha,
tradable, profitable, robust, or production-ready.

## V1 Exclusions

The following must not become hard dependencies in v1:

- ClickHouse
- QuestDB
- DolphinDB
- kdb+
- ArcticDB
- S3 or other cloud object storage
- paid databases
- database servers
- Dagster
- Prefect
- Ray
- MLflow server
- web UI

These tools may be reconsidered only in a later reviewed campaign.

## Implementation Boundary

This document is planning and architecture baseline only. It does not implement
source code, package metadata, schemas, migrations, registries, CLIs, data,
factor values, label values, engines, reports, tests, hooks, CI, broker
operations, paper trading, live trading, order routing, PR creation, or merge
actions.
