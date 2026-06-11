# LCFP-P08 Benchmark + Readiness Summary

- Campaign: `LABEL_COMPUTE_FAST_PATH_V1`
- Phase: `LCFP-P08`
- Status: `COMPLETE`
- Generated at: `2026-06-10T18:42:30.852688+00:00`
- Value policy: value-free summary only; no label values, market prices, Parquet payloads, SQLite content, or row-level records are included.
- Reference timing: bounded P01 reference runner only; no full-window reference timing occurred.
- Benchmark scratch root name: `lcfp_p08_benchmark_20260610T183231Z` (local-only under `ALPHA_DATA_ROOT`).

## Bounded Slice

- Symbol: `ES`
- Year: `2024`
- Window: `2024-06-01T00:00:00+00:00` to `2024-07-01T00:00:00+00:00`
- OHLCV DatasetVersion: `dsv_databento_ohlcv_05404069799decb0`
- BBO DatasetVersion: `dsv_databento_bbo_f9e1d70a04d9dae4`
- OHLCV rows loaded: `26304`
- BBO rows loaded: `26304`
- Contract-roll events asserted: `1`
- Session/maintenance gaps asserted: `48`

## Coverage

| Family | Required P01 Definitions | Production Definitions | Units | Status |
| --- | ---: | ---: | ---: | --- |
| `fixed_base` | 6 | 6 | 6 | `PASS` |
| `fixed_extended` | 3 | 3 | 3 | `PASS` |
| `close_out` | 2 | 2 | 2 | `PASS` |
| `cost_adjusted` | 18 | 18 | 9 | `PASS` |
| `path` | 28 | 28 | 7 | `PASS` |

## Timing Methodology

- The fast path's window is decomposed into three explicitly reported components: `fast_compute` (panel load + vectorized compute + the unit's Parquet value-store write), `registration` (serial keystone registry writes, including hydrating worker Parquet records), and `parity` (parity confirmation, which re-runs the full per-row reference engine per definition).
- `rows/sec` and `speedup` use `fast_compute` only, against the same-process reference rerun on the same rows and definitions (compute vs compute). Parity confirmation is a correctness gate and never enters the throughput numbers.
- The reference rows/sec denominator is the bounded rerun in this process (same machine, same slice); the committed P01 baseline rows/sec is shown alongside for context only.
- Asymmetry disclosed: the reference denominator times pure compute over pre-built input views, while `fast_compute` additionally includes the fast path's canonical panel load, input adaptation, and Parquet value-store write. The asymmetry biases against the fast path, never for it. Each (family, worker-count) cell starts with cold panel caches; panel-load amortization is measured within a cell only.

## Reference Baseline Rerun

| Family | Definitions | Elapsed (s) | Rows/sec | P01 Committed Rows/sec | Records Emitted |
| --- | ---: | ---: | ---: | ---: | ---: |
| `fixed_base` | 6 | 4.631140 | 34078.87 | 35030.81 | 148066 |
| `fixed_extended` | 3 | 2.159406 | 36543.39 | 37631.52 | 66544 |
| `close_out` | 2 | 1.555170 | 33827.82 | 34676.09 | 48258 |
| `cost_adjusted` | 18 | 5.615396 | 84316.77 | 85957.67 | 473472 |
| `path` | 28 | 66.974030 | 10996.98 | 11108.42 | 734674 |

## Worker Sweep

Component timings are disclosed per cell; `Speedup` = fast compute rows/sec / reference rerun rows/sec (same rows).

| Family | Requested | Effective | Threads/Worker | Compute (s) | Registration (s) | Parity (s) | Total (s) | Rows/sec | Files | Registry Delta | Speedup | Full-Window Estimate (s) | Resolver | Parity | Peak RSS KiB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: |
| `fixed_base` | 1 | 1 | 16 | 9.466860 | 0.163165 | 5.577982 | 15.208007 | 16671.21 | 6 | 6 | 0.49 | 4750.71 | `PASS 6/6` | `PASS` | 488440 |
| `fixed_base` | 2 | 2 | 8 | 6.021117 | 2.283412 | 5.720756 | 14.025285 | 26211.75 | 6 | 6 | 0.77 | 3021.55 | `PASS 6/6` | `PASS` | 488440 |
| `fixed_base` | 4 | 4 | 4 | 5.091750 | 2.371516 | 5.677561 | 13.140828 | 30996.02 | 6 | 6 | 0.91 | 2555.17 | `PASS 6/6` | `PASS` | 488440 |
| `fixed_base` | 8 | 6 | 2 | 4.477502 | 2.336307 | 5.699205 | 12.513014 | 35248.23 | 6 | 6 | 1.03 | 2246.92 | `PASS 6/6` | `PASS` | 488440 |
- `fixed_base` requested `8` worker reduction: requested workers 8 reduced to runnable unit count 6
| `fixed_extended` | 1 | 1 | 16 | 5.713801 | 0.078131 | 2.562654 | 8.354586 | 13810.77 | 3 | 3 | 0.38 | 2867.33 | `PASS 3/3` | `PASS` | 524324 |
| `fixed_extended` | 2 | 2 | 8 | 4.696040 | 1.074701 | 2.653934 | 8.424675 | 16803.95 | 3 | 3 | 0.46 | 2356.59 | `PASS 3/3` | `PASS` | 524324 |
| `fixed_extended` | 4 | 3 | 5 | 3.971311 | 1.086011 | 2.660625 | 7.717948 | 19870.51 | 3 | 3 | 0.54 | 1992.90 | `PASS 3/3` | `PASS` | 524324 |
- `fixed_extended` requested `4` worker reduction: requested workers 4 reduced to runnable unit count 3
| `fixed_extended` | 8 | 3 | 5 | 3.955603 | 1.086833 | 2.643607 | 7.686044 | 19949.42 | 3 | 3 | 0.55 | 1985.02 | `PASS 3/3` | `PASS` | 524324 |
- `fixed_extended` requested `8` worker reduction: requested workers 8 reduced to runnable unit count 3
| `close_out` | 1 | 1 | 16 | 4.802317 | 0.052938 | 1.841140 | 6.696396 | 10954.71 | 2 | 2 | 0.32 | 2409.92 | `PASS 2/2` | `PASS` | 533992 |
| `close_out` | 2 | 2 | 8 | 3.862011 | 0.777431 | 1.890850 | 6.530292 | 13621.92 | 2 | 2 | 0.40 | 1938.05 | `PASS 2/2` | `PASS` | 533992 |
| `close_out` | 4 | 2 | 8 | 3.879582 | 0.771924 | 1.987004 | 6.638510 | 13560.22 | 2 | 2 | 0.40 | 1946.87 | `PASS 2/2` | `PASS` | 533992 |
- `close_out` requested `4` worker reduction: requested workers 4 reduced to runnable unit count 2
| `close_out` | 8 | 2 | 8 | 3.966574 | 0.795211 | 1.955066 | 6.716852 | 13262.83 | 2 | 2 | 0.39 | 1990.53 | `PASS 2/2` | `PASS` | 533992 |
- `close_out` requested `8` worker reduction: requested workers 8 reduced to runnable unit count 2
| `cost_adjusted` | 1 | 1 | 16 | 16.791146 | 0.551826 | 7.360990 | 24.703961 | 28197.72 | 9 | 18 | 0.33 | 8426.21 | `PASS 18/18` | `PASS` | 776232 |
| `cost_adjusted` | 2 | 2 | 8 | 10.543742 | 7.241005 | 8.052468 | 25.837215 | 44905.50 | 9 | 18 | 0.53 | 5291.11 | `PASS 18/18` | `PASS` | 776232 |
| `cost_adjusted` | 4 | 4 | 4 | 8.204816 | 8.592217 | 8.118621 | 24.915654 | 57706.60 | 9 | 18 | 0.68 | 4117.38 | `PASS 18/18` | `PASS` | 776232 |
| `cost_adjusted` | 8 | 8 | 2 | 7.798899 | 7.342883 | 8.068522 | 23.210305 | 60710.10 | 9 | 18 | 0.72 | 3913.68 | `PASS 18/18` | `PASS` | 776232 |
| `path` | 1 | 1 | 16 | 21.358225 | 0.947317 | 74.974553 | 97.280096 | 34483.76 | 7 | 28 | 3.14 | 10718.09 | `PASS 28/28` | `PASS` | 792064 |
| `path` | 2 | 2 | 8 | 12.774319 | 10.696020 | 75.895013 | 99.365352 | 57655.68 | 7 | 28 | 5.24 | 6410.47 | `PASS 28/28` | `PASS` | 813896 |
| `path` | 4 | 4 | 4 | 8.340258 | 10.672132 | 76.129750 | 95.142141 | 88308.06 | 7 | 28 | 8.03 | 4185.35 | `PASS 28/28` | `PASS` | 813896 |
| `path` | 8 | 7 | 2 | 6.544099 | 10.643959 | 75.963613 | 93.151671 | 112545.98 | 7 | 28 | 10.23 | 3283.99 | `PASS 28/28` | `PASS` | 813896 |
- `path` requested `8` worker reduction: requested workers 8 reduced to runnable unit count 7

## Production Engine + Worker Policy

Per-family selection per the amended LCFP-P08 criterion: `fast` where measured materially faster (best passing fast_compute speedup > 1.0x), `reference` where the reference engine remains faster (honest component timings in the rationale). Both engines are parity-gated, so correctness is engine-independent.

| Family | Selected Engine | Workers | Measured Speedup | Rationale |
| --- | --- | ---: | ---: | --- |
| `fixed_base` | `fast` | 8 | 1.03 | fast compute measured 1.03x the same-process reference rerun at requested_workers=8 (effective 6); materially faster than 1.00x, so the parity-gated fast engine is selected |
| `fixed_extended` | `reference` | n/a | 0.55 | best passing fast cell measured 0.55x (<= 1.00x) at requested_workers=8; component timings: fast_compute=3.955603s, registration=1.086833s, parity=2.643607s; the reference engine remains faster and stays selected (both engines are parity-gated, so correctness is engine-independent) |
| `close_out` | `reference` | n/a | 0.40 | best passing fast cell measured 0.40x (<= 1.00x) at requested_workers=2; component timings: fast_compute=3.862011s, registration=0.777431s, parity=1.890850s; the reference engine remains faster and stays selected (both engines are parity-gated, so correctness is engine-independent) |
| `cost_adjusted` | `reference` | n/a | 0.72 | best passing fast cell measured 0.72x (<= 1.00x) at requested_workers=8; component timings: fast_compute=7.798899s, registration=7.342883s, parity=8.068522s; the reference engine remains faster and stays selected (both engines are parity-gated, so correctness is engine-independent) |
| `path` | `fast` | 8 | 10.23 | fast compute measured 10.23x the same-process reference rerun at requested_workers=8 (effective 7); materially faster than 1.00x, so the parity-gated fast engine is selected |

## Production Worker Policy

- Status: `SELECTED`
- Selected requested workers: `8`
- Effective workers observed at selection: `8`
- Thread controls: `POLARS_MAX_THREADS=2`, `OMP_NUM_THREADS=2`, `RAYON_NUM_THREADS=2`, `NUMBA_NUM_THREADS=2`
- Rationale: Selected by highest aggregate bounded-slice rows/sec among worker counts that passed resolver smoke and parity.

## Interpretation

Speedup is a measured engineering throughput claim only. This summary does not make any alpha, profitability, tradability, broker, paper, live, or deployment claim.
