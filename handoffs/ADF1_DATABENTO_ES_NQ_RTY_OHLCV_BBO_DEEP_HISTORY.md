# ADF1 Databento ES/NQ/RTY OHLCV+BBO Deep History Handoff

Status: **PHASE B COMPLETE (live, cost-gated)** — full Databento GLBX.MDP3 ES/NQ/RTY
continuous deep-history pulled, canonicalized (sparse provider truth + derived dense
research grid), quality/coverage gated, and registered as accepted local-only
DatasetVersions. Research-ready for ALPHA_FEATURE_LABEL_FOUNDATION_V1. NOT
tradability/profitability/paper/live/broker ready.

All data (raw DBN/Zstd, canonical, metadata refs, registry, reports, logs) is local-only
under `ALPHA_DATA_ROOT`; nothing in this repo. The API key is environment-only and was
never written/logged/committed. **The operator must rotate the Databento API key** (it
transited the operator shell during setup).

## Dependency And Environment

- Databento SDK: `databento==0.79.0` installed to isolated `~/.alpha_databento_libs`
  (system Python is PEP668); run with `PYTHONPATH=src:$HOME/.alpha_databento_libs`.
- `ALPHA_DATA_ROOT=~/alpha_data/alpha_system` (outside the repo).
- Auth gate env (live only): `ALPHA_DATA_PULL_AUTHORIZED=1`,
  `ALPHA_ALLOW_EXTERNAL_DATABENTO=1`, `ALPHA_ALLOW_RAW_LOCAL_WRITE=1`; key via
  `set -a; . ~/.databento_env; set +a` (never echoed). CI must never run the live flow.

## Dataset Scope

- Dataset: `GLBX.MDP3`. Symbols: `ES.v.0`, `NQ.v.0`, `RTY.v.0`, `stype_in=continuous`
  (volume-based front-month; labelled `provider_continuous` / `front_month` /
  `unadjusted` / `not_roll_truth` — NOT a discovered roll calendar).
- Schemas: `ohlcv-1m`, `bbo-1m`, `definition`, `statistics`, `status`.
- Window: `2018-01-01T00:00:00Z` → `2026-06-01T00:00:00Z` (as_of 2026-06-01).
- Encoding/compression: DBN / Zstd (immutable raw source of truth).

## Cost (FREE get_cost quote; under budget)

- Total: **$44.31** (hard cap $110). Per schema: ohlcv-1m $31.93, bbo-1m $12.02,
  statistics $0.35, status $0.008, definition $0.005.
- Symbology resolved to **continuous** (not parent), matching the quote.

## Jobs (batch, dbn+zstd)

- ohlcv-1m `GLBX-20260604-MEBQNKUVT5`; bbo-1m `GLBX-20260604-UQ39TTC9PS`;
  definition `GLBX-20260604-LSNK9N4MT8`; statistics `GLBX-20260604-F4C5EET3RW`;
  status `GLBX-20260604-7TNJVHHLJK`.

## Raw + Canonical

- Raw: **13,142 DBN/Zstd files, 528,844,615 bytes (~529 MB)** under
  `$ALPHA_DATA_ROOT/databento/raw/...`. File manifest hash
  `a1c998f6c70bb5b1dc3e0bb5297fe454103052fef1b6b4d5d3c5915babccf282`.
- Canonical sparse provider truth: **8,687,688 OHLCV-1m bars + 8,687,688 BBO-1m records**
  (trade-based; a missing minute = no trade, not missing data).
- Derived **dense research grid** (one row per expected session minute): no-trade minutes
  emitted as synthetic previous-close rows (`has_trade=false`, `synthetic=true`,
  `fill_method=previous_close`, `volume=0`, `no_trade` flag); no-lookahead
  `available_ts = bar_end_ts + latency`. Consumers must filter `has_trade`/`synthetic`.
- Canonicalization was memory-chunked per calendar year (subprocess-isolated) to stay
  within RAM; raw was pulled once and is content-hashed (no re-pull on re-runs).

## DatasetVersions registered (local-only registry `$ALPHA_DATA_ROOT/registry/datasets.sqlite`)

27 Databento DatasetVersions = 9 years × {sparse OHLCV, dense research grid, BBO},
kept SEPARATE from the 2 existing IBKR DatasetVersions. Partitions: 2018-2022
`development_partition`, 2023-2024 `validation_partition`, 2025-2026
`locked_test_candidate` (locked test carries contamination metadata; do not consume
without governance). Per year (sparse OHLCV / BBO / dense):

- 2018 dev: `dsv_databento_ohlcv_321568572236ef4a` / `dsv_databento_bbo_514d0f3b3fc7d48a` / `dsv_databento_ohlcv_dense_2018_v1`
- 2019 dev: `dsv_databento_ohlcv_a483cc0cc282474b` / `dsv_databento_bbo_f91f510a8d6fa87b` / `dsv_databento_ohlcv_dense_2019_v1`
- 2020 dev: `dsv_databento_ohlcv_bac95e92f1bb1850` / `dsv_databento_bbo_af9511d169b0aead` / `dsv_databento_ohlcv_dense_2020_v1`
- 2021 dev: `dsv_databento_ohlcv_8aeb50fb409fc691` / `dsv_databento_bbo_d5cb08f949e7ff28` / `dsv_databento_ohlcv_dense_2021_v1`
- 2022 dev: `dsv_databento_ohlcv_dc7c86c813fe0dfe` / `dsv_databento_bbo_7b5595d5030462ab` / `dsv_databento_ohlcv_dense_2022_v1`
- 2023 val: `dsv_databento_ohlcv_ec144f9a02a64774` / `dsv_databento_bbo_8772e3b47aa5fb98` / `dsv_databento_ohlcv_dense_2023_v1`
- 2024 val: `dsv_databento_ohlcv_05404069799decb0` / `dsv_databento_bbo_f9e1d70a04d9dae4` / `dsv_databento_ohlcv_dense_2024_v1`
- 2025 locked: `dsv_databento_ohlcv_35ffead770498acd` / `dsv_databento_bbo_35d4417c086be53f` / `dsv_databento_ohlcv_dense_2025_v1`
- 2026 locked: `dsv_databento_ohlcv_a0342ee6a412622b` / `dsv_databento_bbo_22c49fbf57cceea6` / `dsv_databento_ohlcv_dense_2026_v1`

Metadata refs: `dsv_databento_metadata_9111425cc29aa187` (definition/statistics/status,
ES/NQ/RTY) under `$ALPHA_DATA_ROOT/databento/metadata/glbx_mdp3/...`.

## Quality / Coverage (per the hybrid policy)

- Every year: OHLCV coverage PASSING, dense coverage PASSING, BBO coverage PASSING,
  OHLCV/dense/BBO quality WARNING (non-blocking).
- Blocking is reserved for genuine provider data loss (missing raw files/chunks — none,
  download verified complete) and genuine corruption (negative/crossed/mismatched
  quotes, duplicates, non-monotonic timestamps). Market-condition findings are recorded
  as NON-BLOCKING metrics/quarantine (see Findings).

## Findings (data-quality notes for follow-up — NOT blockers)

1. **BBO crossed-quote quarantine rate spikes in 2024-2026** (~47.5k/48.3k/25.8k minutes,
   ~4.6%) vs ~0.1% in 2018-2023. Treated as missing-BBO (non-blocking metric) per policy.
   Worth investigating whether this is a real bbo-1m characteristic from 2024 contracts or
   a canonicalization edge; recorded as a BBO quality metric, not a blocker.
2. **Long contiguous no-trade runs** (e.g. RTY 2020-03-16 COVID overnight) exceed the
   240-min heuristic. Because raw is verified complete, these are genuine illiquidity:
   recorded as `long_no_trade_run` metrics and dense-filled as flagged synthetic rows.
3. **Abnormal BBO spreads** during volatility (e.g. COVID March 2020) exceed the 10-tick
   threshold; recorded in a non-blocking `abnormal_spread_summary` warning metric.
4. **Holiday calendar is only populated for 2024.** Full-closure holidays in other years
   appear as whole-missing sessions and are recorded as `suspected_non_trading_session`
   quarantine (≈4/year, non-blocking). Completing the CME equity-index holiday calendar
   for 2018-2026 would let these be classified precisely (future task).
5. Continuous `.v.0` is volume-based front-month, `not_roll_truth`; dated-contract roll
   truth is out of scope.

## Cross-Source Comparison (Databento vs IBKR)

`compare_sources` was run (diagnostic only; no merge, no DatasetVersion). IBKR canonical
bars are NOT persisted to disk (IBKR materialize registered from memory), so there is no
local IBKR canonical to align against → the report records **NO_OVERLAP** with the IBKR
DatasetVersion ids noted. A future cross-source check requires re-materializing IBKR
canonical to disk over the overlap window (~2024+). Report:
`$ALPHA_DATA_ROOT/reports/databento_ibkr_compare.json`.

## Engineering changes in this run (live-discovered, merged)

- `to_df(pretty_px=False)` → `to_df(price_type="fixed")` (databento 0.79 rename).
- Register reads canonical parquet via `ParquetFile(path).read()` (avoid hive
  partition-column injection of `schema`/`root`).
- Memory-bounded chunked canonicalization (was OOM at 23 GB on the full corpus).
- O(n^2) → linear fixes in coverage/quality (`_run_bounded_by_trades` via session
  min/max; per-session expected-minute membership; bisect-indexed BBO interval counts)
  — full-year register went from ~hour/timeout to ~4 min.
- New dense research-grid record + builder; coverage/quality classify no-trade vs
  provider-gap; BBO missing-quote as non-blocking metric; long-no-trade and abnormal
  spread as non-blocking metrics. Genuine-corruption and missing-raw-chunk gates intact.

## Operator resume / re-run commands (local only; load key in operator shell)

```bash
set -a; . ~/.databento_env; set +a
export ALPHA_DATA_ROOT=$HOME/alpha_data/alpha_system
export PYTHONPATH=src:$HOME/.alpha_databento_libs
export ALPHA_DATA_PULL_AUTHORIZED=1 ALPHA_ALLOW_EXTERNAL_DATABENTO=1 ALPHA_ALLOW_RAW_LOCAL_WRITE=1
```

Raw is already downloaded + hashed; re-runs are free/local. Canonicalize per year, build
dense grid per year, then register per year (development/validation/locked partitions).
See `docs/data_foundation/databento/INGESTION_RUNBOOK.md` for the full CLI flow. After
the supervised run, **rotate the Databento API key**.

## Explicit scope statements

- No API key committed/logged. No raw/canonical/metadata market data committed. No local
  registry/reports/logs committed. No `runs/**` committed.
- ES/NQ/RTY only (no micros). No Databento/IBKR merged DatasetVersion.
- No alpha search, no Feature/Label materialization, no broker/live/paper/order scope.
- Synthetic no-trade rows are flagged, non-executable, and not tradability evidence.
- Dataset is research-ready for Feature/Label Foundation; NOT profitability/tradability/
  live/paper/production ready.
