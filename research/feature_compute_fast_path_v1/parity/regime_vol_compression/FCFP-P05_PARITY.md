# FCFP-P05 Regime / Volatility / Compression Parity

This is a value-free synthetic-fixture parity summary. It contains only counts,
gap coverage, tolerances, and aggregate differences; it contains no per-row
feature values, real market data, Parquet output, or SQLite state.

Fixture:
`tests/fixtures/feature_compute_fast_path/regime_vol_compression.py`

Pack:
`src/alpha_system/features/fast/regime_vol_compression.py`

Reference oracles:

- `average_true_range` via the Base OHLCV family for `atr`
- `_trendiness_points` via the Base OHLCV family for `trendiness`
- `_range_contraction_points` via the Liquidity Structure family for
  `range_contraction`

## Coverage

- Rows: 12 synthetic OHLCV rows.
- Session segments: 2 contiguous segments (`RTH`, then `ETH`).
- Window length: 3.
- Reset-on-session warm-up: covered immediately after the session boundary.
- Input gap: one synthetic `no_trade` row.
- Feature-specific gap: flat-close windows trigger `zero_movement` for
  trendiness.
- Structure prior-window behavior: range contraction uses an exclusive prior
  window and includes a valid post-reset prior-window row.

## Tolerance

ATR and trendiness use absolute/relative tolerance `1e-12` because they are
floating-point reductions. Range contraction is exact on this fixture.

| Feature | Rows | Valid value pairs | Gap rows | Max abs diff | Median abs diff | Result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `base_ohlcv_atr` | 12 | 6 | 6 | 0 | 0 | within `1e-12` |
| `base_ohlcv_trendiness` | 12 | 4 | 8 | 0 | 0 | within `1e-12` |
| `liquidity_structure_range_contraction` | 12 | 4 | 8 | 0 | 0 | exact |

Additional parity confirmations:

- `available_ts` parity: exact for all three features.
- Gap-row parity: exact for `insufficient_window`, `input_gap`, `no_trade`,
  `zero_movement`, and structure/primitive gap flags.
- Session-reset grouping: exact reset and warm-up behavior at the `RTH` to
  `ETH` boundary.
- `feature_version_id` equality: exact for all three features; no V1-specific
  identities are minted.
