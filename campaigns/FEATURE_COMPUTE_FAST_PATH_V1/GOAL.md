# GOAL — FEATURE_COMPUTE_FAST_PATH_V1

## One sentence

Build a single-machine, local, columnar (Polars), batch/vectorized, incremental,
reference-parity-gated, registry-safe **producer compute fast path** for feature/label
materialization so large-scale backfill stops depending on the per-row Python reference
engine — which remains the correctness oracle.

## Why

ADR-0001 intended Polars/NumPy for hot loops; it was realized for I/O, value storage
(ADR-0006), and the backtest fast path, but **never for feature/label value computation**.
The feature engine computes every value per-row in Python (~20–50 µs/row, single-threaded),
which made the `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` full-window backfill a ~10–14 h
job. A measured Polars proof (`research/futures_substrate_scaleout_v1/producer_fast_path/V1_PROOF.md`)
computed all 6 base_ohlcv features for ES 2024 (346,858 rows) in **0.19 s vs ~108 s** on the
reference engine (~500×) with **reference parity** (5/6 bit-exact; volume_zscore within a
documented 3.3e-8 float tolerance; gap handling exact). ADR-0007 makes this the architecture
direction. FUTSUB is paused until V1 lands.

## What this campaign delivers

1. A Polars **PackMaterializer** engine core (load a symbol-year canonical frame once, compute
   a family's whole governed feature pack vectorized) + a synthetic-fixture, CI-runnable
   **reference-parity harness**.
2. Per-family Polars packs with parity tests: base_ohlcv, session/calendar, vwap/session-auction,
   regime/vol/compression, liquidity/PA-structure, volume/activity, bbo tradability/top-book,
   and the cross_market aligned ES/NQ/RTY panel.
3. A multi-horizon fixed-horizon **label pack** (1m..240m in one pass, roll-splice +
   maintenance-crossing guards applied once, `label_available_ts` preserved) — readiness for
   FUTSUB P16–P20.
4. **Targeted / incremental** materialization CLI (family / feature / feature-group / label /
   symbols / years / dataset-version-ids; dry-run estimates; execute-selected-only;
   skip-completed) so adding one feature never recomputes all families.
5. **Engine / value-schema versioning** + reconciliation of the existing reference-engine
   outputs (no silent engine mixing).
6. A **benchmark gate** (elapsed, rows/sec, reads/symbol-year, full-window estimate, speedup).
7. **Integration**: V1 as the default producer path in the scaleout driver (reference engine as
   selectable oracle/fallback) + resolver-smoke on V1 output.

## Done = capability, not cosmetics

Materialization is "done" only when `code_status`, `producer_fast_path_v1_status`,
`execute_status`, `registry_status`, and `artifact_status` all hold. "Fast" is only claimed
when the benchmark proves it; "materialized" only when execute + registry are true.

## Hard boundaries (out of scope)

NOT Ray/GPU/cluster, NOT a feature-compiler/DSL platform, NOT alpha ideation/new AlphaSpecs,
NOT new features/labels beyond existing governed families, NOT parameter search, NOT
FactorLibrary/AlphaBook/Strategy Reference, NOT paper/live/broker/order, NO profitability or
tradability claims. The reference engine is never deleted or weakened; resolver exact-id
semantics and serial registry writes are never weakened; no raw/canonical/value/SQLite/heavy
artifact is committed.
