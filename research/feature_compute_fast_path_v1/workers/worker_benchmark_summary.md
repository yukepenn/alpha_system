# FCFP-P15 Worker Benchmark Summary

- Campaign: `FEATURE_COMPUTE_FAST_PATH_V1`
- Phase: `FCFP-P15`
- Status: `COMPLETE`
- Generated at: `2026-06-09T09:48:16.250317+00:00`
- Value policy: value-free summary only; no feature values, label values, prices, Parquet payloads, SQLite content, or row-level data are included.
- Local-only benchmark root: `/home/yuke_zhang/alpha_data/alpha_system/fcfp_p15_worker_benchmark_20260609T094816Z`
- ALPHA_DATA_ROOT: `/home/yuke_zhang/alpha_data/alpha_system`
- Canonical root: `/home/yuke_zhang/alpha_data/alpha_system/databento/canonical/glbx_mdp3`

## Slice Self-Validation

- Contract-roll events: `1`
- Session gaps observed: `1304`
- Raw contract/id transitions observed: `0`

## Results

| Requested Workers | Effective Workers | Threads/Worker | Elapsed (s) | Rows/s | Canonical Reads | Peak Memory MB | Registry Queue Wait (s) | Resolver Smoke | Parity | Deterministic Hashes | Stable | Reductions |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 1 | 1 | 16 | 6.136716 | 13752.79 | 3 | 739.41 | 0.000000 | `PASS` | `PASS` | `yes` | `yes` | `none` |
| 2 | 2 | 8 | 5.099665 | 16549.52 | 3 | 739.41 | 0.554521 | `PASS` | `PASS` | `yes` | `yes` | `none` |
| 4 | 3 | 5 | 3.116745 | 27078.57 | 3 | 739.41 | 0.548911 | `PASS` | `PASS` | `yes` | `yes` | `requested workers 4 reduced to runnable unit count 3; scaleout worker reduction: requested workers 4 reduced to runnable unit count 3` |
| 8 | 3 | 5 | 3.126410 | 26994.86 | 3 | 739.41 | 0.545688 | `PASS` | `PASS` | `yes` | `yes` | `requested workers 8 reduced to runnable unit count 3; scaleout worker reduction: requested workers 8 reduced to runnable unit count 3` |

## Chosen Stable Worker Count

- Fastest stable requested worker count: `4`
- Effective workers used: `3`
- Determinism evidence: content hashes matched the worker-1 baseline for all completed units.
- Parity evidence: V1 worker content hashes matched the reference-engine bounded units.
- Registry evidence: every completed V1 unit resolved through registry truth after serial official registration.
