# ADR-0007: Producer Compute Fast Path (V1)

## Status

Accepted (architecture direction). Implementation is a scoped follow-up campaign
`FEATURE_COMPUTE_FAST_PATH_V1`; it gates resumption of large-scale feature/label
materialization in `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`.

## Context

[ADR-0001](0001-local-first-stack.md) sets the local-first stack with
"Polars/NumPy/Numba serve pipelines and hot loops." That intent was realized for
**data I/O** (canonical Parquet via pyarrow/Polars), **value storage**
([ADR-0006](0006-feature-label-value-storage.md): feature/label values as Parquet),
and a **scoped backtest-simulation fast path** (`fast_arrays.py`, ASV1-P19). It was
**never realized for feature/label value *computation*.**

The feature engine (`features/primitives/*`, `features/families/*`) computes every
feature on a pure-Python, per-row, object-building **reference** engine
(`grep -r numpy|pandas|polars src/alpha_system/features/` returns nothing). It is
correctness-first and is the right **oracle**, but it is single-threaded and
~20-50 us/row.

This surfaced concretely during the substrate scaleout full-window backfill: the
one-time backfill was on track for ~10-14 h. A measurement (`research/.../V1_PROOF.md`)
isolated the cost to the per-row compute itself (not I/O, not alignment, not re-reads):
caching/batching are marginal; only vectorizing the compute kernels helps. A Polars
prototype of base_ohlcv computed all 6 features in **0.19 s** vs **~108 s** on the
reference engine (~500x) with **reference parity** (5/6 bit-exact, volume_zscore within
a documented 3.3e-8 float tolerance, gap handling exact).

The consumer side (studies/backtests resolving registry Parquet via Polars/DuckDB) is
already fast and is out of scope here. The producer side is not.

## Decision

Adopt an explicit **three-path** producer/consumer compute model and require a
vectorized producer fast path for large-scale materialization:

1. **`reference_compute_path`** — the existing per-row Python engine. Slow, simple,
   trusted. Used only as the correctness oracle: tiny fixtures, bounded samples, and
   parity tests. Never the default production backfill path when V1 covers a family.

2. **`producer_fast_path_v1`** — single-machine, local, columnar (Polars), batch/
   vectorized, incremental, checkpointed, registry-safe materialization. Used for
   full accepted-window backfill, future feature/label additions, and future data
   append. Must pass a reference-parity gate per family/primitive before it is the
   production path for that family. NOT Ray/GPU/cluster, NOT a feature-compiler
   platform, NOT alpha mining.

3. **`consumer_query_path`** — StudySpec/Runtime/diagnostics/backtests resolve
   pre-materialized Parquet through the registry via Polars/DuckDB; never recompute
   canonical data during normal studies. (Already implemented.)

### V1 required capabilities (campaign acceptance)

- **Targeted, incremental materialization**: by family, feature_id/feature_group,
  label_id/label_group, symbols, years, dataset_version_ids; dry-run plan with
  row/unit/time estimates; execute selected units only; skip completed units by
  checkpoint and registry truth. Adding one feature must not recompute all families.
- **Pack-level batching**: load each symbol-year canonical once, compute all of a
  family's features together; reuse shared rolling primitives.
- **Cross-market alignment cache**: build the ES/NQ/RTY aligned panel once per
  year/grid/session policy; preserve per-instrument `available_ts`; no cross-instrument
  forward-fill; compute all cross-market features from it.
- **Multi-horizon label batching**: load price panel once, compute 1m..240m fixed-horizon
  labels in one pass; roll-splice and maintenance-crossing guards applied once;
  preserve `label_available_ts`.
- **Reference parity gate**: synthetic-fixture, CI-runnable tests proving V1 output
  equals reference (exact where expected, documented tolerance where float differences
  are expected) for values, `available_ts`, `label_available_ts`, guard behavior, and
  missingness/quality flags. Unexplained differences are blockers.
- **Benchmark gate**: bounded-real timing + rows/sec + canonical-reads-per-symbol-year +
  estimated full-window runtime + speedup vs reference.
- **Registry-safe + Parquet-first**: serial registry writes through the official
  keystone path; no manual SQLite; exact `feature_version_id`/`label_version_id`
  semantics preserved; full-window values are Parquet; JSONL is audit/sample only.
- **Engine/value-schema versioning**: where V1 output differs from already-materialized
  reference values beyond documented tolerance, either treat as a bug, version the
  producer engine / value schema explicitly, or re-materialize via the official path.
  Never mix engines silently in the same logical value series.

## Consequences

- Feature/label materialization phases are not "done" until `code_status`,
  `producer_fast_path_v1_status`, `execute_status`, `registry_status`, and
  `artifact_status` all hold.
- FUTSUB full-window backfill resumes only after V1 passes its parity + benchmark gates;
  the partial reference-engine outputs already produced (base_ohlcv/vwap/regime full
  window, liquidity partial, 2024 for the rest) are preserved and used as parity
  reference samples, then reconciled per the versioning rule.
- The reference engine remains and is never deleted; it is the oracle.
