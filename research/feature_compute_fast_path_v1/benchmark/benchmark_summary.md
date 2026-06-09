# FCFP-P13 Benchmark Summary

- Campaign: `FEATURE_COMPUTE_FAST_PATH_V1`
- Phase: `FCFP-P13`
- Status: `COMPLETE`
- Generated at: `2026-06-09T04:28:48.416136+00:00`
- Value policy: value-free summary only; no feature, label, price, Parquet, SQLite, or row-level values are included.

## Window

- Window: `2024-12` (`2024-12-01T00:00:00+00:00` to `2025-01-01T00:00:00+00:00`)
- Symbols: `ES, NQ, RTY`
- Primary single-symbol packs: `ES`
- OHLCV DatasetVersion: `dsv_databento_ohlcv_05404069799decb0`
- Dense OHLCV DatasetVersion: `dsv_databento_ohlcv_dense_2024_v1`
- BBO DatasetVersion: `dsv_databento_bbo_f9e1d70a04d9dae4`
- Slice row count across loaded inputs: `168794`
- Contract-roll events in configured roll calendar: `1`
- Raw contract/id transitions observed in canonical rows: `0`
- Session gaps observed: `1304`
- Note: Contract roll self-validation uses the configured quarterly CME roll calendar because the canonical continuous front rows keep stable contract_id / instrument_id identifiers.

## Results

| Pack | Slice Rows | Outputs | Reference Elapsed (s) | V1 Elapsed (s) | V1 Rows/s | Reference Reads | V1 Reads | Reads/Symbol-Year | Outputs/Read | Speedup | Full-Window Estimate | Parity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| base_ohlcv | 28727 | 6 | 3.216224 | 0.971325 | 29575.07 | 6 | 1 | 1.00 | 6.00 | 3.31 | 99.433829 | PASS |
| session_calendar_roll | 28727 | 10 | 2.664208 | 1.827210 | 15721.78 | 10 | 1 | 1.00 | 10.00 | 1.46 | 187.050199 | PASS |
| vwap_session_auction | 28727 | 5 | 1.040662 | 0.893272 | 32159.30 | 5 | 1 | 1.00 | 5.00 | 1.17 | 91.443603 | PASS |
| regime_vol_compression | 28727 | 3 | 1.593168 | 0.587573 | 48890.93 | 3 | 1 | 1.00 | 3.00 | 2.71 | 60.149436 | PASS |
| liquidity_pa_structure | 28727 | 11 | 4.658662 | 1.718925 | 16712.19 | 11 | 1 | 1.00 | 11.00 | 2.71 | 175.965082 | PASS |
| volume_activity | 28727 | 8 | 3.611354 | 1.280916 | 22426.92 | 8 | 1 | 1.00 | 8.00 | 2.82 | 131.126456 | PASS |
| bbo_tradability | 28727 | 15 | 4.247365 | 2.833102 | 10139.77 | 15 | 1 | 1.00 | 15.00 | 1.50 | 290.022620 | PASS |
| cross_market | 84397 | 11 | 15.787355 | 3.174105 | 26589.23 | 33 | 3 | 1.00 | 3.67 | 4.97 | 326.737114 | PASS |
| fixed_horizon_labels | 57454 | 7 | 2.126707 | 1.340289 | 42866.87 | 11 | 2 | 2.00 | 3.50 | 1.59 | 137.204420 | PASS |

## Extrapolation Basis

- `base_ohlcv`: base_ohlcv: 28727 bounded ohlcv rows measured; 2940762 accepted-window ohlcv rows extrapolated
- `session_calendar_roll`: session_calendar_roll: 28727 bounded ohlcv rows measured; 2940762 accepted-window ohlcv rows extrapolated
- `vwap_session_auction`: vwap_session_auction: 28727 bounded ohlcv rows measured; 2940762 accepted-window ohlcv rows extrapolated
- `regime_vol_compression`: regime_vol_compression: 28727 bounded ohlcv rows measured; 2940762 accepted-window ohlcv rows extrapolated
- `liquidity_pa_structure`: liquidity_pa_structure: 28727 bounded ohlcv rows measured; 2940762 accepted-window ohlcv rows extrapolated
- `volume_activity`: volume_activity: 28727 bounded ohlcv rows measured; 2940762 accepted-window ohlcv rows extrapolated
- `bbo_tradability`: bbo_tradability: 28727 bounded bbo rows measured; 2940762 accepted-window bbo rows extrapolated
- `cross_market`: cross_market: 84397 bounded ES,NQ,RTY OHLCV rows measured; 8687688 accepted-window ES,NQ,RTY OHLCV rows extrapolated
- `fixed_horizon_labels`: fixed_horizon_labels: 57454 bounded ES OHLCV+BBO rows measured; 5881524 accepted-window ES OHLCV+BBO rows extrapolated

## Parity Confirmation

- `base_ohlcv`: `PASS` on value, available_ts, gap/quality flags, and feature_version_id identity (rolling volatility variance reduction may differ by binary summation order; volume_zscore rolling variance may differ by binary summation order).
- `session_calendar_roll`: `PASS` on value, available_ts, gap/quality flags, and feature_version_id identity (exact parity).
- `vwap_session_auction`: `PASS` on value, available_ts, gap/quality flags, and feature_version_id identity (VWAP cumulative floating point reduction; anchored VWAP cumulative floating point reduction; distance to VWAP cumulative floating point reduction).
- `regime_vol_compression`: `PASS` on value, available_ts, gap/quality flags, and feature_version_id identity (ATR rolling mean reduction; trendiness floating point reduction; range-contraction floating point reduction).
- `liquidity_pa_structure`: `PASS` on value, available_ts, gap/quality flags, and feature_version_id identity (structure distance floating point reduction; opening-range distance floating point reduction; structure ratio floating point reduction; range-contraction floating point reduction).
- `volume_activity`: `PASS` on value, available_ts, gap/quality flags, and feature_version_id identity (volume_zscore rolling variance may differ by binary summation order; trendiness floating point reduction; structure ratio floating point reduction).
- `bbo_tradability`: `PASS` on value, available_ts, gap/quality flags, and feature_version_id identity (spread z-score rolling variance may differ by binary summation order).
- `cross_market`: `PASS` on value, available_ts, gap/quality flags, and feature_version_id identity (cross-market rolling covariance reduction; cross-market rolling correlation reduction).
- `fixed_horizon_labels`: `PASS` on value, label_available_ts, gap/quality flags, and label_version_id identity (exact parity).

## Required Report Fields

- `elapsed`: V1 elapsed seconds per pack; reference elapsed seconds is also reported.
- `rows_per_sec`: V1 bounded-slice input rows per second.
- `canonical_reads_per_symbol_year`: V1 canonical reads per symbol-year unit.
- `output_features_or_labels_per_read`: governed outputs divided by V1 canonical reads.
- `full_accepted_window_runtime_estimate`: extrapolated seconds from slice rows/sec.
- `speedup_vs_reference`: reference elapsed seconds divided by V1 elapsed seconds.
