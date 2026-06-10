# LCFP-P01 Reference Label Baseline Benchmark

This is a value-free, bounded compute-only timing summary. It records counts,
elapsed time, rows per second, and extrapolated runtime only. It contains no
label values, market prices, canonical rows, Parquet payloads, SQLite rows,
JSONL payloads, provider payloads, or registry dumps.

## Command

```bash
ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m tools.label_compute_fast_path.baseline_benchmark --format json
```

Outcome: exited `0`.

## Timing Contract

- Reference engine: `alpha_system.labels.families.*.compute_*_label`
- Timing mode: `compute_only`
- Scratch root used: none
- Production registry write occurred: `false`
- Full-window reference timing occurred: `false`
- The command did not instantiate `LabelRegistry`, did not call
  `materialize_labels`, and did not write value stores.
- Full-window numbers below are extrapolations from bounded measured rows/sec.

## Bounded Slice

- Symbol: `ES`
- Year: `2024`
- Window: `2024-06-01T00:00:00+00:00` to `2024-07-01T00:00:00+00:00`
- OHLCV DatasetVersion: `dsv_databento_ohlcv_05404069799decb0`
- BBO DatasetVersion: `dsv_databento_bbo_f9e1d70a04d9dae4`
- OHLCV rows loaded: `26304`
- BBO rows loaded: `26304`
- Analytic roll events in window: `1`
- One-minute OHLCV maintenance/session gaps counted in window: `48`

The bounded slice is a single roll-containing symbol-month. Roll presence is
counted from the analytic CME equity-index quarterly roll calendar; maintenance
gaps are counted from one-minute OHLCV timestamp gaps in the bounded slice.

## Results

| Family | Definitions | Elapsed sec | Rows processed | Records emitted | Rows/sec | Full-window row basis | Estimated full-window sec | Estimated full-window |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `fixed_base` | 6 | 4.505292 | 157824 | 148066 | 35030.81 | 79200000 | 2260.87 | 37.68 min |
| `fixed_extended` | 3 | 2.096966 | 78912 | 66544 | 37631.52 | 39600000 | 1052.31 | 17.54 min |
| `close_out` | 2 | 1.517126 | 52608 | 48258 | 34676.09 | 26400000 | 761.33 | 12.69 min |
| `cost_adjusted` | 18 | 5.508200 | 473472 | 473472 | 85957.67 | 237600000 | 2764.15 | 46.07 min |
| `path` | 28 | 66.302128 | 736512 | 734674 | 11108.42 | 369600000 | 33272.05 | 9.24 hr |

Notes:

- `fixed_base`: FUTSUB-P16 horizons `1m`, `3m`, `5m`, `10m`, `15m`, `30m`.
- `fixed_extended`: FUTSUB-P17 horizons `60m`, `120m`, `240m`.
- `close_out`: FUTSUB-P18 `session_close` and `maintenance_flat`.
- `cost_adjusted`: FUTSUB-P19 horizons `1m` through `240m` for the existing
  cost-adjusted and spread-adjusted reference labels.
- `path`: FUTSUB-P20 horizons `5m` through `240m` for `mfe`, `mae`,
  `target_before_stop`, and `triple_barrier`.

## Extrapolation Basis

- Accepted FUTSUB years: `2019` through `2026`; blocked `2018` is excluded.
- Symbols: `ES`, `NQ`, `RTY`.
- Per-unit row budget: `550000` rows.
- Fixed base basis: `3 symbols x 8 years x 6 horizons x 550000 =
  79200000` label-row evaluations.
- Extended basis: `3 symbols x 8 years x 3 horizons x 550000 = 39600000`
  label-row evaluations.
- Close-out basis: `3 symbols x 8 years x 2 symbolic horizons x 550000 =
  26400000` label-row evaluations.
- Cost-adjusted basis: `3 symbols x 8 years x 9 horizons x 2 existing
  cost/spread labels x 550000 = 237600000` label-row evaluations.
- Path basis: `3 symbols x 8 years x 7 horizons x 4 existing path metrics x
  550000 = 369600000` label-row evaluations.

## Interpretation

The path oracle is the slowest measured family on this bounded slice. That is an
implementation-cost observation only; it is not a label-quality, alpha,
profitability, tradability, execution, live, paper, broker, deployment, or
production-trading claim.

LCFP-P08 should benchmark the accepted producer path against these bounded
reference rows/sec baselines and should not time the reference engine on a full
accepted window.
