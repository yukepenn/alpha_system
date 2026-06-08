# Producer Compute Fast Path V1 — base_ohlcv Proof

Evidence that a single-machine, local, columnar (Polars), batch/vectorized producer
compute path can replace the per-row Python **reference** engine for feature
materialization with reference parity and a ~500x speedup. Generated while the
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` full-window backfill was paused.

Reproduce: `research/futures_substrate_scaleout_v1/producer_fast_path/v1_proof_base_ohlcv.py`
(requires the local research env + `ALPHA_DATA_ROOT` with canonical ES 2024 ohlcv_1m
and the already-materialized reference base_ohlcv values).

## Benchmark (ES 2024, 346,858 rows)

| path | work | wall time |
| --- | --- | --- |
| reference engine | per-feature per-row Python | ~18 s/feature x 6 = ~108 s |
| **V1 (Polars)** | **load once + compute all 6 features** | **0.19 s** |

Speedup ~500-600x. The full accepted-window feature backfill (estimated ~10-14 h on
the reference engine) becomes seconds-to-minutes of compute on V1.

## Reference parity (V1 vs already-materialized reference values)

| feature | rows | value match (<=1e-9) | max abs diff | gap handling |
| --- | --- | --- | --- | --- |
| returns | 346,858 | exact | 0 | exact |
| log_returns | 346,858 | exact | 0 | exact |
| rolling_volatility | 346,858 | exact | 3.7e-17 | exact |
| rolling_range | 346,858 | exact | 0 | exact |
| range_position | 346,858 | exact | 0 | exact |
| volume_zscore | 346,858 | within 3.3e-8 | 3.3e-8 (median 5.3e-12) | exact |

5/6 features bit-exact. `volume_zscore` differs by a documented float tolerance
(rolling-std summation order on a few high-volume rows; median diff 5.3e-12). All 6
reproduce the `insufficient_window` gap rows exactly.

## Why base_ohlcv is the easy case (and what the full V1 campaign must still cover)

base_ohlcv uses `reset_on_session=False` and only trailing rolling/diff primitives,
so it maps to native Polars `shift`/`rolling_*` expressions directly. The full V1
producer must additionally cover:

- session-reset rolling (group rolling by session segment) for vwap/session, regime,
  volume, structure/liquidity;
- the cross-market aligned ES/NQ/RTY panel in Polars (per-instrument `available_ts`
  preserved, no cross-instrument forward-fill) + rolling correlation/lead-lag;
- BBO tradability/top-book features over the bbo_1m schema;
- multi-horizon fixed-horizon labels in one pass (1m..240m) with roll-splice and
  maintenance-crossing guards (P16-P20);
- engine/value-schema versioning to reconcile float-tolerance differences against the
  already-materialized reference values (re-materialize or version, never mix silently);
- registry-safe serial writes through the official keystone path, Parquet-first;
- a synthetic-fixture parity test suite (CI-runnable, no local-data dependency) and a
  benchmark gate.

These are tracked by ADR-0007 and the `FEATURE_COMPUTE_FAST_PATH_V1` campaign scope.
