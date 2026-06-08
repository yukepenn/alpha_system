# Feature Compute Fast Path V1 Evidence

This directory is the commit-eligible evidence root for
`FEATURE_COMPUTE_FAST_PATH_V1`.

Only value-free summaries are commit-eligible here, including:

- parity reports with aggregate counts, tolerances, and summary diffs
- benchmark summaries with aggregate elapsed time, rows/sec, reads per
  symbol-year, speedup, and full-window estimates
- reconciliation summaries that describe engine/value-schema provenance without
  committing per-row feature or label values

Never commit raw or canonical market data, provider responses, materialized
feature values, materialized label values, Parquet/Arrow/Feather files, SQLite
registries or journals, logs, caches, model artifacts, or generated report
bundles. Local run state remains under `runs/**` and is not commit-eligible.

`FCFP-P00` anchors this directory. `FCFP-P02` adds the value-free
`parity/base_ohlcv/` report for the first governed V1 family pack.
