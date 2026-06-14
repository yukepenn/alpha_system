# IVL-P06 Dogfood Fixtures

These value-free fixtures express the existing DK Track B
`context_not_equal_trigger` idea as front-door `idea.yaml` documents with
embedded slice metadata.

- `track_b_es2024_120m.idea.yaml` is the burned single-class slice. Check-3
  (`path_label_two_class`) must return `DATA_GAP` before any probe is invoked.
- `track_b_es2020_120m.idea.yaml` is the barrier-resolving two-class slice from
  the coverage matrix (`row_count=313156`, `overlap_rows=310547`). In a fully
  resolving local environment Check-3 passes; if local pack resolution is absent
  or partition metadata cannot resolve, the accepted outcome is an honest
  `DATA_GAP` with no fabricated values.

The files contain ids, relative paths, class-count metadata, and governance
context only. They do not contain row values, parquet data, sqlite databases, or
promotion artifacts.
