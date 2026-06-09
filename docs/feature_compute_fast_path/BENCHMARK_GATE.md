# Benchmark Gate

`FCFP-P13` adds the bounded benchmark gate for
`FEATURE_COMPUTE_FAST_PATH_V1`. The gate measures the governed V1 fast packs
against the reference feature and label engines on one real, roll-containing
month, confirms real-data parity on the same slice, and writes only a
value-free summary.

## Scope

The benchmark is a local operator step. It does not resume the full accepted
window, does not write feature or label values, and does not change reference
or V1 pack semantics. The reference engine remains the correctness oracle.

Default measurement window:

- Symbols: `ES,NQ,RTY`
- Primary single-symbol packs: `ES`
- Window: `2024-12-01T00:00:00+00:00` through
  `2025-01-01T00:00:00+00:00`
- OHLCV DatasetVersion: `dsv_databento_ohlcv_05404069799decb0`
- Dense OHLCV DatasetVersion: `dsv_databento_ohlcv_dense_2024_v1`
- BBO DatasetVersion: `dsv_databento_bbo_f9e1d70a04d9dae4`

The slice self-validation fails closed unless it observes at least one
configured quarterly roll event and at least one session gap. Operators may
override the month, symbols, primary symbol, and DatasetVersion ids from the
CLI when a different bounded roll month is required.

## Run

Run from the repository root with the research environment active and
`ALPHA_DATA_ROOT` exported.

Before the benchmark, back up the local feature registry:

```bash
TS=$(date -u +%Y%m%dT%H%M%SZ)
cp "$ALPHA_DATA_ROOT/registry/features.sqlite" "$ALPHA_DATA_ROOT/registry/features.sqlite.bak_fcfp_$TS"
```

Run the default bounded benchmark:

```bash
python tools/feature_compute_fast_path/benchmark_gate.py
```

Useful overrides:

```bash
python tools/feature_compute_fast_path/benchmark_gate.py \
  --year 2024 \
  --month 12 \
  --symbols ES,NQ,RTY \
  --primary-symbol ES \
  --alpha-data-root "$ALPHA_DATA_ROOT"
```

If `ALPHA_DATA_ROOT` or the canonical root is genuinely absent, the entrypoint
writes a blocked, value-free summary instead of fabricating timings.

## Summary

The committed summary is:

```text
research/feature_compute_fast_path_v1/benchmark/benchmark_summary.md
```

It reports counts and timing fields only:

- `elapsed`
- `rows_per_sec`
- `canonical_reads_per_symbol_year`
- `output_features_or_labels_per_read`
- `full_accepted_window_runtime_estimate`
- `speedup_vs_reference`
- slice row count, window, symbols, extrapolation basis, reference read count,
  V1 read count, and parity confirmation

The summary must not include per-row feature values, label values, market
prices, Parquet output, SQLite output, or profitability/tradability claims.
Benchmark output values, local registry backups, and any run-local artifacts
remain local-only under `ALPHA_DATA_ROOT` or `runs/**`.
