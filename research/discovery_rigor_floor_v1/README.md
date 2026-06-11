# Discovery Rigor Floor Evidence

This directory holds commit-eligible, value-free evidence for
`DISCOVERY_RIGOR_FLOOR_V1`.

Allowed evidence includes gate inventories, reason-code and ledger coverage
tables, holdout and contamination summaries, canary pass/fail tables,
surrogate-FDR calibration statistics, requeue eligibility tables, readiness
checklists, and other aggregate records that contain no study values.

The following must never land here:

- study values, feature values, label values, price series, return series, or
  per-row diagnostics outputs;
- SQLite databases, journals, WAL files, manifests, caches, logs, notebooks,
  generated report bundles, or local scratch files;
- raw or canonical provider data, DBN/Zstd, Parquet, Arrow, Feather, model
  binaries, secrets, credentials, or other heavy artifacts;
- broker, live, paper, order-routing, deployment, or account-operation output.

Local-only runtime state belongs under `runs/**`. Local market data, registries,
and materialized values belong under `$ALPHA_DATA_ROOT`. Evidence committed here
must stay research-only and must not make alpha, profitability, tradability,
execution-quality, or production claims.
