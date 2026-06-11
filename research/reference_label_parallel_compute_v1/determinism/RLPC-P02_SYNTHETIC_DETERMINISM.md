# RLPC-P02 Synthetic Determinism Evidence

This value-free note records the committed synthetic correctness gate for
`REFERENCE_LABEL_PARALLEL_COMPUTE_V1/RLPC-P02`.

- Scope: fixed-horizon plus cost-adjusted-shaped label units.
- Synthetic grid size: 13 label units.
- Worker counts compared: 1 and 4.
- Exact equality dimensions: value-record snapshots, label version ids, content
  hashes, normalized registry rows, lineage rows, guard quality flags, and
  `label_available_ts`.
- Interruption coverage: worker failure retry and parent abort between serial
  registrations.
- Single-writer coverage: worker entrypoint registry-open audit plus canary
  detection for `labels.sqlite` opens.
- Real-slice spot-check: not run in this phase execution; the committed CI test
  skips unless local real data, optional dependencies, and an isolated namespace
  are explicitly provided.

No label values, Parquet, SQLite, raw/canonical data, logs, or run artifacts are
stored in this report.
