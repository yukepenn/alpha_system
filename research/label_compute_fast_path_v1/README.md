# Label Compute Fast Path Evidence

This directory is the commit-eligible evidence root for
`LABEL_COMPUTE_FAST_PATH_V1`.

Only value-free summaries may be committed here. Acceptable evidence includes
inventory notes, bounded baseline summaries, parity counts and tolerances,
no-lookahead and guard summaries, benchmark/readiness summaries, integration
summaries, file counts, registry deltas, elapsed time, rows per second, and
coordinator-facing closeout notes.

Do not commit per-row label values, feature values, raw or canonical data,
Parquet, Arrow, Feather, SQLite, DB files, DB journals, WAL files, DBN/Zstd
provider payloads, logs, caches, full-history JSONL payloads, or local run
artifacts. Those remain under `runs/**` or `ALPHA_DATA_ROOT` as local-only
state.

Phase-owned subdirectories are created only by the phase that owns them.
LCFP-P01 owns:

- `inventory/inventory.md`: value-free inventory of the reference label engine,
  existing fast-label surface, FUTSUB label needs, guard and availability
  contracts, overlap metadata, registry schema, and parity harness.
- `baseline/baseline_benchmark_summary.md`: value-free bounded reference-engine
  timing summary for later comparison.

Later phases own `parity/`, `benchmark/`, `integration/`, and `closeout/`
evidence as their scopes authorize them.
