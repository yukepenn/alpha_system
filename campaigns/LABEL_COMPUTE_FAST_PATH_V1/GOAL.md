# GOAL — LABEL_COMPUTE_FAST_PATH_V1

## One sentence

Build a single-machine, local, columnar (Polars/NumPy/Numba where correct), batch/vectorized,
incremental, **reference-parity-gated**, registry-safe **fast producer path for labels** —
the label analogue of the completed `FEATURE_COMPUTE_FAST_PATH_V1` — so the paused
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` full-window label backfill stops depending on
the per-row Python reference label engine, which remains the correctness oracle forever.

## Why

FUTSUB is stopped at FUTSUB-P19 (19/34, run `2026-06-07T235209Z`, STOP active) because
reference-engine label materialization is too slow at full-window scale: P19's cost-adjusted
labels reached ~60% before the deliberate stop (checkpointed and durable; nothing lost).
`FEATURE_COMPUTE_FAST_PATH_V1` (17/17, run `2026-06-08T160146Z`) already proved the pattern
for features with reference parity. Calibrate speedup expectations honestly: the ~500x figure
was the **pre-campaign compute-only proof** on base_ohlcv
(`research/futures_substrate_scaleout_v1/producer_fast_path/V1_PROOF.md`); FCFP's committed
**end-to-end** benchmark gate on the bounded slice measured **3.31x** for base_ohlcv and
**1.59x** for fixed-horizon labels
(`research/feature_compute_fast_path_v1/benchmark/benchmark_summary.md`). LCFP-P08
expectations are set against measured end-to-end numbers, not the compute-only proof. FCFP
also shipped a **partial** fast label
path: `src/alpha_system/labels/fast/{materializer.py, fixed_horizon.py}` (FCFP-P10:
`FastLabelMaterializer`, `FastLabelPack`, `build_fixed_horizon_label_pack`,
`LabelPanelFrameRequest`) covering the base fixed horizons only. **Disclosed defect:** that
FCFP-P10 pack is currently **broken against the extended governed enum** — FUTSUB-P14+
extended `FixedHorizonLabelName` (FWD_RET_60M/120M/240M, SESSION_CLOSE, MAINTENANCE_FLAT)
after FCFP-P10, and `_horizon_minutes` in `labels/fast/fixed_horizon.py` plus the fixture
`tests/fixtures/feature_compute_fast_path/fixed_horizon_label.py` crash with `ValueError` on
the non-minute tokens, so `tests/unit/feature_compute_fast_path/test_fixed_horizon_label_pack.py`
FAILS when polars is installed (CI is green only because polars is absent there). LCFP-P03
repairs the pack + fixture and corrects the module's stale `governance_gap_note`
(`labels/fast/fixed_horizon.py:96-101`); that test must be green from LCFP-P03 onward. This
campaign **extends that
existing module — it does not greenfield** — to the full governed label surface: fixed +
extended horizons, session-close / maintenance-flat, cost-adjusted, and path labels, plus
targeted/incremental/worker-parallel execution, a parity + no-lookahead + guard test suite,
and a benchmark/readiness gate.

## Policy supersession (explicit)

FUTSUB-P18/P19 phase specs list "a V1 fast label path" as a **non-goal** ("labels stay
reference-engine-only"). **This campaign deliberately supersedes that policy.** After LCFP
acceptance, the V1 fast label path becomes the sanctioned production label materialization
path, and FUTSUB P16–P20 will be amended to use it; the executable reintegration handoff is
LCFP-P09's deliverable. Until LCFP acceptance, the reference engine remains the only
production label path. The reference engine is never deleted or weakened in either case —
it is the parity oracle forever.

## What this campaign delivers

1. **FUTSUB pause handoff** (P00): the stop state recorded (P19 ~60% cost-adjusted labels,
   checkpointed; worktrees preserved), all valid values/registries preserved — no deletion.
2. **Inventory + baseline benchmark** (P01): the reference label path, the existing
   `labels/fast` coverage, the FUTSUB P16–P20 label configs, `roll_guard`, and the registry
   inventoried; the reference path benchmarked on a bounded slice (never the full window).
3. **Shared label panel / terminal / guard contract** (P02): one shared
   price/mid/high/low/BBO/cost/session/roll/maintenance panel; a terminal-index model;
   the `label_available_ts` + quality-metadata contract (`LabelAvailabilityPolicy` parity).
4. **Fast fixed + extended horizon labels** (P03): all of 1m/3m/5m/10m/15m/30m/60m/120m/240m
   batched in one pass per symbol-year where feasible, extending `labels/fast/fixed_horizon.py`
   — repairing first the stale FCFP-P10 pack/fixture vs the extended governed enum (and the
   stale `governance_gap_note`) so the existing fast-label test is green from P03 onward.
5. **Fast session/maintenance/cost labels** (P04): session-close, maintenance-flat,
   cost-adjusted (`COST_ADJUSTED_FWD_RET`, `SPREAD_ADJUSTED_FWD_RET`) reusing fixed-horizon
   terminals and the **existing** cost profiles (`backtest/costs.py`, consumed read-only);
   BBO spread stays a proxy only.
6. **Fast path labels** (P05): MFE / MAE / target-before-stop / triple-barrier with
   NumPy/Numba/Polars kernels where correct; `SameBarBarrierPolicy` ambiguity semantics must
   match the reference exactly (documented safe fallback where a kernel cannot be proven).
7. **Worker/checkpoint/registry/resolver integration** (P06): targeted incremental
   materialization (label_group / horizon_group / symbol / year / dataset_version_id;
   dry-run estimate; execute-selected; checkpoint/restart; force-recompute;
   skip-registry-valid), CPU workers over independent units with **strictly serial** registry
   writes, `--workers` / `ALPHA_LABEL_CPU_WORKERS` / `ALPHA_CPU_WORKERS`, resolver smoke.
8. **Parity / no-lookahead / guard test suite** (P07): fast == reference on the required
   parity set, including roll-crossing and maintenance-crossing cases, exact
   `label_available_ts` parity, and identity (`label_version_id`) parity.
9. **Benchmark + production readiness gate** (P08): workers 1/2/4/8 where safe; rows/sec,
   file counts, registry deltas, resolver smoke, parity confirmation on a bounded real slice;
   a selected production worker policy.
10. **FUTSUB reintegration handoff + closeout** (P09): exact executable instructions to amend
    the FUTSUB campaign files and reset/rerun P16–P20 on the fast path, with
    preserve-don't-delete state-cleanup rules for stale reference-label registry rows/values.

## Done = capability, not cosmetics

Label materialization is "done" only when `code_status`, `fast_label_path_v1_status`,
`execute_status`, `registry_status`, and `artifact_status` all hold. "Fast" is only claimed
when the benchmark proves it; "materialized" only when execute + registry are true. The fast
path becomes the production label path ONLY after the parity / no-lookahead / guard gates pass.

## Hard boundaries (out of scope / forbidden)

- **Never** trust fast labels without parity; **never** let unverified labels into the trusted
  registry; unexplained differences are blockers.
- **Never** weaken `roll_guard` (`RollCrossPolicy`, DROP default, ex-ante calendar; R-036/R-037),
  ignore the maintenance break, or silently cross rolls; the fast path must reproduce guard
  behavior EXACTLY (drop/truncate/flag/invalid).
- **No new identities**: `label_version_id` is content-addressed from `LabelContractSpec`;
  the fast path emits VALUES ONLY. No future-observed contract changes; labels are never
  consumed as features.
- **No second cost/PnL truth**: cost-adjusted labels consume the existing cost profiles
  (`backtest/costs.py`) read-only; editing cost/value/accounting math is forbidden.
- **No parallel SQLite writes** — registry writes are strictly serial via the official
  keystone path. **No full-history JSONL payloads** — Parquet-first; JSONL is
  sample/manifest/audit tier only.
- NOT alpha mining / new AlphaSpecs / parameter search; NOT Strategy Reference, FactorLibrary,
  or AlphaBook scope; NOT paper/live/broker/order anything; NOT Ray/GPU/cluster or a
  label-compiler/DSL platform; no new label families beyond the existing governed families.
- Research-only language throughout: no alpha, profitability, tradability, or production-trading
  claims. The reference engine is never deleted or weakened; no
  raw/canonical/value/SQLite/heavy artifact is committed.
