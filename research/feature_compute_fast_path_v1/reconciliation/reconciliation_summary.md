# FCFP-P12 Reconciliation Summary

Value-free summary for engine provenance and reference-output reconciliation in
`FEATURE_COMPUTE_FAST_PATH_V1`.

This artifact contains only policy decisions, logical-series counts,
tolerances, and aggregate absolute-difference statistics from committed
synthetic parity evidence. It contains no per-row feature or label values, no
Parquet payloads, no SQLite rows, no provider data, and no raw/canonical data.

## Policy

- Existing valid reference-engine outputs remain the parity reference.
- Identical or within documented tolerance: keep the reference output, tag
  `producer_engine_id`, and do not overwrite.
- Beyond documented tolerance: block silent engine mixing. The only allowed
  branches are V1 bug fix, explicit `value_schema_version` bump, or
  re-materialization through the official keystone path in a governed phase.
- Producer provenance is registry metadata. It does not enter
  `feature_version_id` or `label_version_id`.

## Producer Engines

| Producer | Engine id | Value-schema version |
| --- | --- | --- |
| Feature reference engine | `alpha_system.features.reference.materializer.v1` | `alpha_system.features.materialization.v1` |
| Feature fast path V1 | `alpha_system.features.fast.pack_materializer.v1` | `alpha_system.features.fast.values.v1` |
| Label fast path V1 | `alpha_system.labels.fast.pack_materializer.v1` | `alpha_system.labels.fast.values.v1` |

## Feature Reconciliation Classification

The FUTSUB-already-materialized feature families are reconciled by preserving
the existing reference-produced outputs and recording explicit provenance. The
V1 packs remain candidate producers until the later official integration /
materialization path runs; P12 performs no full backfill and no overwrite.

| Family / scope | Logical series | Compared fixture rows | Tolerance | Max abs diff | Median abs diff | Beyond tolerance rows | Classification | Decision |
| --- | ---: | ---: | --- | ---: | ---: | ---: | --- | --- |
| `base_ohlcv` full-window already materialized | 6 | 192 | exact except `volume_zscore` abs `5e-8` | `3.9968028886505635e-15` | `1.9984014443252818e-15` | 0 | within tolerance | keep reference, tag provenance, no overwrite |
| `vwap_session_auction` full-window already materialized | 5 | 60 | abs/rel `1e-12` for VWAP reductions; opening/overnight ranges exact | `2.842170943040401e-14` | `7.105427357601002e-15` | 0 | within tolerance | keep reference, tag provenance, no overwrite |
| `regime_vol_compression` full-window already materialized | 3 | 36 | abs/rel `1e-12` for ATR/trendiness; range contraction exact | `0` | `0` | 0 | identical on fixture | keep reference, tag provenance, no overwrite |
| `liquidity_pa_structure` partial already materialized | 11 | 132 | abs/rel `1e-12` for OHLC ratio reductions; flags exact | `2.220446049250313e-16` | `0` | 0 | within tolerance | keep reference, tag provenance, no overwrite |
| `session_calendar_roll` 2024 scope | 10 | 80 | exact | `0` | `0` | 0 | identical on fixture | keep reference, tag provenance, no overwrite |
| `volume_activity` 2024 scope | 8 | 376 | abs/rel `1e-12` for finite reductions/ratios; rolling volume and session minute exact | `2.220446049250313e-16` | `0` | 0 | within tolerance | keep reference, tag provenance, no overwrite |
| `bbo_tradability` 2024 scope | 15 | 150 | abs/rel `1e-12` for spread z-score; other BBO fields exact | `0` | `0` | 0 | identical on fixture | keep reference, tag provenance, no overwrite |
| `cross_market` 2024 scope | 11 | 110 | abs/rel `1e-12` for rolling beta/correlation reductions; point features exact | `0` | `0` | 0 | identical on fixture | keep reference, tag provenance, no overwrite |

## Label Path Note

The governed fixed-horizon label fast path is not used here for a real
full-window backfill. Its existing synthetic parity evidence remains exact for
all 11 governed labels, with 283 aggregate fixture comparisons and no
V1-specific `label_version_id`. Fast label registry records carry producer and
schema provenance through label registry metadata and lineage.

## Result

No valid existing reference output is deleted, overwritten, or interleaved with
V1 values by this phase. Any future beyond-tolerance reconciliation result is a
blocker until handled by one of the explicit policy branches above.
