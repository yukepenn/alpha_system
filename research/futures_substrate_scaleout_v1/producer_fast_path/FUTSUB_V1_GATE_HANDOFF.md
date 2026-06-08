# FUTSUB Pause + V1 Gate Handoff

`FEATURE_COMPUTE_FAST_PATH_V1_REQUIRED_BEFORE_FULL_BACKFILL`

`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` full accepted-window feature backfill
is **paused** by coordinator decision: the producer must run on a vectorized fast path
(ADR-0007), not the per-row reference engine, before large-scale materialization resumes.
This is not a data problem and not an alpha failure; it is a producer-architecture upgrade
proven correct and ~500x faster (see `V1_PROOF.md`).

## State at pause (preserve; do not wipe)

- Driver execute-path fixed and merged (PRs #276-#279): exposure-family scoping,
  unit+feature idempotency, two O(n^2) fixes (session roll-proximity, causal
  reset-on-session window), cross_market canonical market-id. All 8 families validated on
  bounded-real 2024 (0 failures).
- Reference-engine materialization completed before pause (full window 2019-2026):
  - base_ohlcv 144/144, vwap 144/144, regime 120/120 (full window)
  - liquidity 127/216 (partial)
  - session/volume/bbo/cross_market: 2024 only
  - TOTAL 663 feature_registry_records, **0 orphaned** (every parquet_path exists).
- Registries backed up local-only: `features.sqlite.bak_pausev0_<ts>`,
  `datasets.sqlite.bak_pausev0_<ts>`, `labels.sqlite.bak_pausev0_<ts>`.
- Dataset acceptance locks persisted for 2019-2026 (2018 ohlcv_1m/bbo_1m version-level
  BLOCKED -> 2018 excluded; documented coverage gap). Per-symbol 2018 not pursued (not cheap).
- Materializer fully stopped; no scaleout process running; disk ~944 G free.

These reference-engine outputs are **valid** and are retained as parity-reference samples.
They are reconciled to V1 per the ADR-0007 versioning rule once V1 lands.

## What is proven (V1)

base_ohlcv Polars pack: 0.19 s for all 6 features over 346,858 rows vs ~108 s on the
reference engine; reference parity (5/6 bit-exact, volume_zscore within 3.3e-8 documented
float tolerance; gap handling exact). See `V1_PROOF.md` + `v1_proof_base_ohlcv.py`.

## What V1 still requires (the campaign)

Per ADR-0007 acceptance: targeted/incremental materialization; pack-level batching for all
families; cross-market aligned-panel-in-Polars; multi-horizon label batching (P16-P20);
session-reset rolling; BBO features; reference-parity gate (synthetic-fixture, CI-runnable);
benchmark gate; registry-safe serial Parquet-first writes; engine/value-schema versioning.

## Recommended next campaign

`FEATURE_COMPUTE_FAST_PATH_V1` — single-machine, local, columnar, batch/vectorized,
incremental, reference-parity-gated, registry-safe producer compute engine. Boundaries:
no Ray/GPU/cluster, no feature-compiler platform, no alpha mining, no
FactorLibrary/AlphaBook/Strategy Reference, no paper/live/broker, no
profitability/tradability claims. Substrate/infra engineering only.

Suggested phase shape: V1 engine + Polars pack contract; per-family pack implementations
with parity tests (base/vwap/session/regime/structure-liquidity/volume/bbo); cross-market
panel; targeted/incremental CLI + dry-run estimates; label multi-horizon pack; benchmark
gate; engine/value versioning + reconciliation of existing reference outputs.

## Resume policy for FUTSUB

After V1 passes parity + benchmark gates:
1. Amend FUTSUB so P06-P13 (features) and P16-P20 (labels) materialize via V1; P14/P22
   resolver smoke validates V1-produced values; P30/P33 closeout records
   `producer_fast_path_v1_status`.
2. Resume full accepted-window materialization on V1 (idempotent: completed valid units
   skip; reconcile reference-vs-V1 per ADR-0007 versioning).
3. Continue P14/P15 -> labels -> P21-P29 (Core Pilot re-lock + rerun the 6 INCONCLUSIVE
   studies) -> P30 audit -> P31/P32 handoffs -> P33 closeout.

Do not resume the slow reference-engine full backfill. Do not call a family materialized
until `execute_status` and `registry_status` are true on V1 output.
