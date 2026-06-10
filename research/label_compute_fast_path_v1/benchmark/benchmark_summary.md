# LCFP-P08 Benchmark + Readiness Summary

- Campaign: `LABEL_COMPUTE_FAST_PATH_V1`
- Phase: `LCFP-P08`
- Status: `COMPLETE`
- Generated at: `2026-06-10T18:06:17.286274+00:00`
- Value policy: value-free summary only; no label values, market prices, Parquet payloads, SQLite content, or row-level records are included.
- Reference timing: bounded P01 reference runner only; no full-window reference timing occurred.
- Benchmark scratch root name: `lcfp_p08_benchmark_20260610T175622Z` (local-only under `ALPHA_DATA_ROOT`).

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
| `fixed_base` | 6 | 4.548437 | 34698.51 | 35030.81 | 148066 |
| `fixed_extended` | 3 | 2.060003 | 38306.73 | 37631.52 | 66544 |
| `close_out` | 2 | 1.522330 | 34557.55 | 34676.09 | 48258 |
| `cost_adjusted` | 18 | 5.556072 | 85217.03 | 85957.67 | 473472 |
| `path` | 28 | 66.687756 | 11044.19 | 11108.42 | 734674 |

## Worker Sweep

Component timings are disclosed per cell; `Speedup` = fast compute rows/sec / reference rerun rows/sec (same rows).

| Family | Requested | Effective | Threads/Worker | Compute (s) | Registration (s) | Parity (s) | Total (s) | Rows/sec | Files | Registry Delta | Speedup | Full-Window Estimate (s) | Resolver | Parity | Peak RSS KiB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: |
| `fixed_base` | 1 | 1 | 16 | 9.313584 | 0.155948 | 5.486638 | 14.956170 | 16945.57 | 6 | 6 | 0.49 | 4673.79 | `PASS 6/6` | `PASS` | 499040 |
| `fixed_base` | 2 | 2 | 8 | 6.072213 | 2.259495 | 5.531481 | 13.863189 | 25991.18 | 6 | 6 | 0.75 | 3047.19 | `PASS 6/6` | `PASS` | 499040 |
| `fixed_base` | 4 | 4 | 4 | 5.137065 | 2.292070 | 5.549877 | 12.979012 | 30722.60 | 6 | 6 | 0.89 | 2577.91 | `PASS 6/6` | `PASS` | 499040 |
| `fixed_base` | 8 | 6 | 2 | 4.581856 | 2.317807 | 5.577064 | 12.476728 | 34445.43 | 6 | 6 | 0.99 | 2299.29 | `PASS 6/6` | `PASS` | 499040 |
- `fixed_base` requested `8` worker reduction: requested workers 8 reduced to runnable unit count 6
| `fixed_extended` | 1 | 1 | 16 | 5.668808 | 0.073825 | 2.536329 | 8.278963 | 13920.39 | 3 | 3 | 0.36 | 2844.75 | `PASS 3/3` | `PASS` | 538184 |
| `fixed_extended` | 2 | 2 | 8 | 4.784913 | 1.067057 | 2.626553 | 8.478523 | 16491.84 | 3 | 3 | 0.43 | 2401.19 | `PASS 3/3` | `PASS` | 538184 |
| `fixed_extended` | 4 | 3 | 5 | 3.916984 | 1.069512 | 2.611740 | 7.598236 | 20146.11 | 3 | 3 | 0.53 | 1965.64 | `PASS 3/3` | `PASS` | 538184 |
- `fixed_extended` requested `4` worker reduction: requested workers 4 reduced to runnable unit count 3
| `fixed_extended` | 8 | 3 | 5 | 3.855160 | 1.055743 | 2.624305 | 7.535207 | 20469.19 | 3 | 3 | 0.53 | 1934.61 | `PASS 3/3` | `PASS` | 538184 |
- `fixed_extended` requested `8` worker reduction: requested workers 8 reduced to runnable unit count 3
| `close_out` | 1 | 1 | 16 | 4.737305 | 0.058231 | 1.783835 | 6.579371 | 11105.05 | 2 | 2 | 0.32 | 2377.30 | `PASS 2/2` | `PASS` | 546312 |
| `close_out` | 2 | 2 | 8 | 3.820880 | 0.775808 | 1.872618 | 6.469307 | 13768.55 | 2 | 2 | 0.40 | 1917.41 | `PASS 2/2` | `PASS` | 546312 |
| `close_out` | 4 | 2 | 8 | 3.830130 | 0.762494 | 1.873165 | 6.465789 | 13735.30 | 2 | 2 | 0.40 | 1922.05 | `PASS 2/2` | `PASS` | 546312 |
- `close_out` requested `4` worker reduction: requested workers 4 reduced to runnable unit count 2
| `close_out` | 8 | 2 | 8 | 3.858029 | 0.772667 | 1.845145 | 6.475840 | 13635.98 | 2 | 2 | 0.39 | 1936.05 | `PASS 2/2` | `PASS` | 546312 |
- `close_out` requested `8` worker reduction: requested workers 8 reduced to runnable unit count 2
| `cost_adjusted` | 1 | 1 | 16 | 16.650728 | 0.526589 | 7.268562 | 24.445879 | 28435.51 | 9 | 18 | 0.33 | 8355.75 | `PASS 18/18` | `PASS` | 750680 |
| `cost_adjusted` | 2 | 2 | 8 | 10.402385 | 7.195109 | 8.049853 | 25.647346 | 45515.72 | 9 | 18 | 0.53 | 5220.17 | `PASS 18/18` | `PASS` | 750680 |
| `cost_adjusted` | 4 | 4 | 4 | 8.088166 | 7.735971 | 8.002920 | 23.827057 | 58538.86 | 9 | 18 | 0.69 | 4058.84 | `PASS 18/18` | `PASS` | 750680 |
| `cost_adjusted` | 8 | 8 | 2 | 7.660997 | 7.281164 | 8.051287 | 22.993448 | 61802.93 | 9 | 18 | 0.73 | 3844.48 | `PASS 18/18` | `PASS` | 750680 |
| `path` | 1 | 1 | 16 | 21.246594 | 0.898763 | 74.769203 | 96.914560 | 34664.94 | 7 | 28 | 3.14 | 10662.07 | `PASS 28/28` | `PASS` | 768416 |
| `path` | 2 | 2 | 8 | 13.007088 | 10.613701 | 75.604729 | 99.225517 | 56623.90 | 7 | 28 | 5.13 | 6527.28 | `PASS 28/28` | `PASS` | 793312 |
| `path` | 4 | 4 | 4 | 8.312253 | 10.632811 | 75.734510 | 94.679574 | 88605.58 | 7 | 28 | 8.02 | 4171.29 | `PASS 28/28` | `PASS` | 793312 |
| `path` | 8 | 7 | 2 | 6.539652 | 10.606383 | 75.840834 | 92.986869 | 112622.51 | 7 | 28 | 10.20 | 3281.76 | `PASS 28/28` | `PASS` | 793312 |
- `path` requested `8` worker reduction: requested workers 8 reduced to runnable unit count 7

## Production Engine + Worker Policy

Per-family selection per the amended LCFP-P08 criterion: `fast` where measured materially faster (best passing fast_compute speedup > 1.0x), `reference` where the reference engine remains faster (honest component timings in the rationale). Both engines are parity-gated, so correctness is engine-independent.

| Family | Selected Engine | Workers | Measured Speedup | Rationale |
| --- | --- | ---: | ---: | --- |
| `fixed_base` | `reference` | n/a | 0.99 | best passing fast cell measured 0.99x (<= 1.00x) at requested_workers=8; component timings: fast_compute=4.581856s, registration=2.317807s, parity=5.577064s; the reference engine remains faster and stays selected (both engines are parity-gated, so correctness is engine-independent) |
| `fixed_extended` | `reference` | n/a | 0.53 | best passing fast cell measured 0.53x (<= 1.00x) at requested_workers=8; component timings: fast_compute=3.855160s, registration=1.055743s, parity=2.624305s; the reference engine remains faster and stays selected (both engines are parity-gated, so correctness is engine-independent) |
| `close_out` | `reference` | n/a | 0.40 | best passing fast cell measured 0.40x (<= 1.00x) at requested_workers=2; component timings: fast_compute=3.820880s, registration=0.775808s, parity=1.872618s; the reference engine remains faster and stays selected (both engines are parity-gated, so correctness is engine-independent) |
| `cost_adjusted` | `reference` | n/a | 0.73 | best passing fast cell measured 0.73x (<= 1.00x) at requested_workers=8; component timings: fast_compute=7.660997s, registration=7.281164s, parity=8.051287s; the reference engine remains faster and stays selected (both engines are parity-gated, so correctness is engine-independent) |
| `path` | `fast` | 8 | 10.20 | fast compute measured 10.20x the same-process reference rerun at requested_workers=8 (effective 7); materially faster than 1.00x, so the parity-gated fast engine is selected |

## Production Worker Policy

- Status: `SELECTED`
- Selected requested workers: `8`
- Effective workers observed at selection: `8`
- Thread controls: `POLARS_MAX_THREADS=2`, `OMP_NUM_THREADS=2`, `RAYON_NUM_THREADS=2`, `NUMBA_NUM_THREADS=2`
- Rationale: Selected by highest aggregate bounded-slice rows/sec among worker counts that passed resolver smoke and parity. The policy is not released for downstream reruns while status is blocked.

## Interpretation

Speedup is a measured engineering throughput claim only. This summary does not make any alpha, profitability, tradability, broker, paper, live, or deployment claim.
