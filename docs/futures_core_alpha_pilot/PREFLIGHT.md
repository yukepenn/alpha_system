# Futures Core Alpha Pilot Preflight

`FUTCORE-P01` records the pre-pilot entry gates for
`ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`. The authoritative value-free evidence table
is:

- `research/futures_core_alpha_pilot_v1/preflight/preflight_report.md`

This companion page is the durable operator-facing pointer. It does not copy
market data, value rows, Parquet files, SQLite files, provider responses, or
run-local artifacts into the repository.

## Recorded Gate Outcome

The report records `PASS` rows for:

- consumed primitive imports: `governance`, `runtime`, `agent_factory`;
- `FEATURE_LABEL_PARQUET_SINK_V1`;
- `SESSION_LABEL_GUARD_FIX_V1`;
- Research Runtime real-data smoke status by reference;
- accepted DatasetVersion resolution by `resolve_dataset_version`;
- registry-resolved Parquet FeaturePack / LabelPack references;
- Agent Factory preflight and separation-of-duties wiring.

Phase verdict, review, staging, commit, PR, CI, merge, and done-check remain
Ralph-owned. This page is not a review verdict.

## Safety Boundary

The preflight is evidence-only. It does not authorize broker, live, paper,
order, account, deployment, production, strategy, portfolio, profitability,
tradability, or capital-allocation behavior. Later pilot phases must continue
to consume inputs through registry and runtime tools, keep `runs/**` local-only,
and avoid committing raw/canonical data, feature values, label values, Parquet,
SQLite, provider responses, logs, caches, secrets, or credentials.
