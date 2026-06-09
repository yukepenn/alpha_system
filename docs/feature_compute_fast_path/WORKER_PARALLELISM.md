# V1 Worker Parallelism

`FCFP-P15` adds CPU worker parallelism to the V1 scaleout producer path without
parallelizing the feature registry.

## Contract

- `--workers N` controls V1 compute workers for `alpha scaleout feature-pack`.
- `ALPHA_CPU_WORKERS` is the fallback when `--workers` is omitted.
- Default `workers=1` keeps the serial producer path.
- Worker processes load canonical inputs, compute V1 values, write local
  Parquet values, and write deterministic worker manifests.
- The parent process is the only registry writer. It consumes worker outputs in
  deterministic unit order and registers through `FeatureStore` /
  `PackMaterializer.register_pack`.
- Workers never write SQLite registry rows and never create feature identity.
  `feature_version_id` still comes from the governed `FeatureSpec`.

## Unit Rules

Standard feature families parallelize over independent
`family x symbol x year/DatasetVersion` units. `cross_market_alignment`
is special: one unit spans the full ES/NQ/RTY aligned panel for a year so the
panel is never split across workers. The canonical loader still reads each
configured instrument and the fast pack preserves per-instrument
`available_ts`; no cross-instrument forward fill is introduced.

## Oversubscription

The driver computes an effective worker plan from requested workers, runnable
unit count, and available CPU cores. It pins per-worker native thread pools via
`POLARS_MAX_THREADS`, `OMP_NUM_THREADS`, and `RAYON_NUM_THREADS` so
`workers x threads_per_worker` does not exceed available cores. Any reduction is
recorded in the run summary and emitted by the CLI log hook.

## Determinism

Fast feature and label value-store writes canonicalize record order before
content hashing:

```text
feature_version_id/entity_id/event_ts/available_ts
label_version_id/entity_id/event_ts/label_available_ts
```

Worker manifests include the unit key, content hash, row count,
`producer_engine_id`, `value_schema_version`, feature ids, and canonical record
order. The benchmark compares content hashes across requested worker counts.

## Benchmark

The value-free worker benchmark runner is:

```bash
python tools/feature_compute_fast_path/worker_benchmark.py
```

It measures requested workers `1,2,4,8` over isolated local-only data roots under
`ALPHA_DATA_ROOT`, compares V1 worker hashes against the reference engine for the
bounded units, checks registry truth after serial registration, and writes:

```text
research/feature_compute_fast_path_v1/workers/worker_benchmark_summary.md
```

The summary includes elapsed time, rows/sec, canonical reads, peak memory,
registry queue wait, resolver-smoke result, parity result, deterministic-hash
status, worker reductions, and the fastest stable requested worker count. It
contains no values, Parquet payloads, SQLite content, provider data, or
row-level data.
