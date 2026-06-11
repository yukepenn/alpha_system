# RLPC-P03 Reference Label Parallel Benchmark Summary

Value-free benchmark summary. It contains no label values, market prices,
canonical rows, Parquet payloads, SQLite content, provider responses,
logs, or run artifacts.

- Campaign: `REFERENCE_LABEL_PARALLEL_COMPUTE_V1`
- Phase: `RLPC-P03`
- Generated at: `2026-06-11T03:50:46.600080+00:00`
- Driver entrypoint: `alpha_system.features.scaleout.driver.run_scaleout`
- Benchmark namespace: `$ALPHA_DATA_ROOT/rlpc_p03_benchmark_<UTCSTAMP>/workers_N`
- Local namespace name: `rlpc_p03_benchmark_20260611T032628Z`
- Production registry row delta: `0`
- Rollout timed: `bounded-real` only; full-window timing occurred: `false`
- Thread cap env per cell: `POLARS_MAX_THREADS=2 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 NUMEXPR_MAX_THREADS=2`

## Slice Definition

- Config: `configs/labels/scaleout/cost_adjusted.json`
- Family: `cost_adjusted`
- Symbols: `ES`
- Years: `2024`
- Horizons: `1m, 3m, 5m, 10m, 15m, 30m, 60m, 120m, 240m`
- Label ids: `cost_adjusted_fwd_ret, spread_adjusted_fwd_ret`
- Runnable units: `9`
- Unit ids: `mbu_241290fd96424d08c7ee773b, mbu_4f8f521212eedfd0804d73a5, mbu_69c6ee8585dd5dc0476f779d, mbu_b70c477529b368187ee4a57d, mbu_ecb023cde3ef706eab250e67, mbu_fd84ba6176164534fa2e14a5, mbu_ab9e7f433e7ce9f42ea7e5e0, mbu_683bf98b5b2027c72bbd8540, mbu_bb2fb852c02a243ad3773d4d`
- OHLCV DatasetVersions: `dsv_databento_ohlcv_05404069799decb0`
- BBO DatasetVersions: `dsv_databento_bbo_f9e1d70a04d9dae4`
- Canonical OHLCV rows inspected: `346858`
- Analytic CME roll events in selected year(s): `4`
- Roll event dates: `2024-03-07, 2024-06-13, 2024-09-12, 2024-12-12`
- Raw contract/id transitions observed in canonical rows: `0`
- Session/maintenance gaps observed: `471`
- Max timestamp gap minutes: `4381`
- Slice widened from initial ES/2024: `false`

Roll self-validation uses the configured analytic CME equity-index quarterly
roll calendar because these canonical front-continuous rows keep stable
contract_id/instrument_id identifiers; timestamp gaps are measured directly
from canonical OHLCV rows.

## Worker Sweep

| Requested | Effective | Driver Plan Threads/Worker | Elapsed (s) | Units/s | Speedup vs 1 | Worker Compute (s) | Serial Registration (s) | Overhead (s) | Peak RSS MiB | Registry Delta | Completed | Label Versions | Rows | Determinism |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 16 | 530.998623 | 0.0169 | 1.00 | 526.587762 | 3.515340 | 0.895521 | 3496.10 | 18 | 9 | 18 | 6243444 | PASS |
| 2 | 2 | 8 | 389.293969 | 0.0231 | 1.36 | 303.147023 | 86.077229 | 0.069717 | 3682.13 | 18 | 9 | 18 | 6243444 | PASS |
| 4 | 4 | 4 | 289.894526 | 0.0310 | 1.83 | 203.654499 | 86.172520 | 0.067508 | 3690.77 | 18 | 9 | 18 | 6243444 | PASS |
| 8 | 8 | 2 | 247.888112 | 0.0363 | 2.14 | 157.706309 | 90.097791 | 0.084013 | 3690.77 | 18 | 9 | 18 | 6243444 | PASS |

## Determinism Spot-Check

| Requested | Record Count Match | label_version_id Match | Content Hash Match | Row Count Match | Compared Records |
| ---: | --- | --- | --- | --- | ---: |
| 1 | yes | yes | yes | yes | 9 |
| 2 | yes | yes | yes | yes | 9 |
| 4 | yes | yes | yes | yes | 9 |
| 8 | yes | yes | yes | yes | 9 |

## Release Gate

Release decision: NOT_RELEASED

Diagnosis: serial registration ceiling: workers=8 speedup was 2.14x, below the 3.0x gate; backlog section 6 option 2 remains the recorded escalation.

Speedup is wall-clock units/sec at requested workers=N divided by
wall-clock units/sec for requested workers=1 on the same bounded unit grid.
