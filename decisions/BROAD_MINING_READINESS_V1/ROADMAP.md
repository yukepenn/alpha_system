# BROAD_MINING_READINESS_V1 — the EV-ordered route to autonomous broad mining

Status: STRATEGIC ROADMAP (grounded bottleneck analysis; guides next builds)
Date: 2026-06-15
Lane: Yellow (architecture / route decision). Research-only. No PnL/value truth.
Consistent with `docs/OPERATING_COMPASS.md` §3.8 / §4 / §6 (this sequences the
readiness gaps; the compass holds the layer model + rail).

## 0. The one-sentence finding

**The deterministic gates are BUILT but NOT WIRED INTO THE RUNNER'S RAIL** — so
running broad mining today would manufacture a stream of single-year, 64-surrogate,
un-pooled, un-FDR-corrected "signals" that *look* promotable but that the project's
own independent reviewer has already ruled non-promotable. Sequence: put the sound
gates ON the runner BEFORE scaling breadth.

## 1. Bottleneck verdict (grounded; file:line in the research record)

| # | Area | Status | What exactly is missing |
|---|------|--------|--------------------------|
| 5 | **Autonomous driver** | ADDRESSED (BROAD_MINING_DRIVER_V0) | `alpha idea mine` (`research_lane/mining_driver.py:mine_ideas`) is an unattended, resumable, single-threaded loop that mines a SET of ideas through the sound gates without a human per idea (the append-only ledgers are the idempotent progress record). Concurrency / parallel researchers remain the explicit follow-up. |
| 2 | **Cross-year OOS aggregation** | ADDRESSED (BROAD_MINING_DRIVER_V0 + PARTITION_RESOLVER_V0; OOS-resolution gap CLOSED for the setup lane) | `research_lane/mining_driver.py:run_multi_partition_pool` fans ONE idea over its `(instrument, year, horizon)` partitions via `fast_probe`, harvests each partition's typed `FastReadout` component, and pools via the (previously ORPHANED) `pooled_hypothesis.aggregate_pooled_metric` into a cross-partition OOS statistic with explicit partition coverage. **PARTITION_RESOLVER_V0 closes the OOS-resolution gap:** `research_lane/partition_resolver.py:resolve_partition_slice` synthesizes a COMPLETE SliceSpec for any TARGET partition by resolving each declared factor role to that partition's REGISTERED materialized `feature_version_id`/`label_version_id` from the on-disk registries (keyed by `(feature_id, partition)` / `(label_id, partition)`, NOT by copying the declared slice's hashes; the runtime resolver matches packs BY version-id hash then asserts dsv+partition). `_probe_partitions` uses it as the fall-back whenever a target partition is not explicitly declared in the idea, so a setup idea declared on `ES_2020_120m` now fans across the materialized ES/NQ/RTY 2019-2026 120m grid → `present_count>=2` real OOS pool. `alpha idea mine --years … --instruments …` expands the target grid (+ `resolve_partition_setup` retargets the per-partition `path_label` content hash). Fails closed (typed `PartitionResolutionError` → honest DATA_GAP) when a factor/label is genuinely unmaterialized; never falls back to another partition's data. SETUP lane only (the poolable lane); main_effect partitions stay `present=False` by design (separate follow-up). |
| 1 | **Surrogate adequacy** | PARTIAL | `surrogate_run_count` default 1, hardcoded **64** in all 19–20 idea YAMLs (resolution-inadequate; the `family_fdr_budget` canary proves 64 can't resolve a corrected p). Loop is serial Python, full re-probe per surrogate → 64→1000 is ~16× single-threaded. |
| 4 | **Materialization** | DONE on disk; acceptance-lock bookkeeping is the only residual | Scaleout commands are turnkey (`alpha scaleout feature-pack`, `alpha label materialize --fast-path`, fan over `--symbols/--years` w/ resume) and the values are **already materialized**: ES/NQ/RTY 2019–2026 features (8 families) + labels (`cost_adjusted`/`path`/`fixed`/`extended`/`session`). The config `ACCEPTED:0 / BLOCKED:27` + `fail_closed_on_blocked_or_missing_lock` is **acceptance-lock bookkeeping (intent/gate), NOT absence of values on disk** — the exact "config BLOCKED:27 vs disk full of `values.parquet`" misread that `tools/frontier/data_inventory.py` (`alpha data inventory`) was built to reconcile. Disk truth = `alpha data inventory`; residual = an acceptance-lock unblock + re-lock pass, not a materialization run. Input OHLCV/BBO ACCEPTED 2020–2025. |
| 3 | **Idea generation / breadth** | GAP | All ~20 ideas hand-authored YAMLs; no enumerator (contexts × triggers × outcomes × instruments × years). `hypothesis_scout.alphaspec.draft` is a declared-but-unimplemented tool; agent_factory MVP explicitly excludes discovery/enumeration. |

## 2. Ranking (binding constraint first)

1. **#5 driver** — without a loop, "broad mining" is impossible by definition.
2. **#2 OOS pooling** — the reviewer made OOS replication a HARD promotion
   requirement; a single-partition runner cannot produce promotable evidence even
   at 10k ideas. (High overlap with #5 — the same driver fans out over partitions.)
3. **#1 surrogate adequacy** — credibility + the compute wall; bump 64→~1000 AND
   parallelize the serial loop or broad mining is intractable / non-credible.
4. **#4 materialization** — data supply for OOS years/instruments; unblock the 27
   label locks + run the (already turnkey) scaleout within the ~400G WSL budget.
5. **#3 idea generation** — multiplies breadth, LEAST binding now (≈20 ideas already
   exercise the whole loop). Must land AFTER sound-gate plumbing, else breadth =
   more false positives.

## 3. The single highest-leverage next build

**A multi-partition, unattended idea-mining driver** that, per idea:
fan out over its `(instrument, year, horizon)` partitions → run the existing
`fast_probe` per partition → pool via `pooled_hypothesis.aggregate_pooled_metric`
(OOS) → apply `family_fdr_correction` across the co-mined batch → record the verdict
to the existing research-memory ledgers → pull the next idea.

This single build closes #5 (the loop) AND #2 (OOS pooling) at once, and is the ONLY
thing that lets the existing sound-gated ideas produce **promotable** (multi-year,
FDR-corrected) evidence. It is INTEGRATION, not greenfield — `fast_probe`,
`aggregate_pooled_metric`, `family_fdr_correction`/`family_fdr_ledger`, and the
memory ledgers all already exist and are merely unconnected. Pair it with bumping
`surrogate_run_count` 64→~1000 and parallelizing the surrogate loop so runs are
credible and tractable.

Dependency: Stage B of `CROSS_IDEA_FDR_BUDGET_V1` (wiring family-FDR into the
single-idea run path) is the first rung; the multi-partition driver builds on it.

## 4. Silent-danger guard (why order matters)

If broad mining ran TODAY it would emit single-year, 64-surrogate, individually
-thresholded, un-pooled, un-FDR "signals" — high-confidence-looking output already
ruled non-promotable. The same false-signal failure mode as
[[law-overlap-aware-ic-power-n-eff]], one layer up. Therefore: NO breadth scaling
(#3) until the driver runs ideas through pooling + FDR + adequate surrogates. Any
mining run must `log()`/record its surrogate count + partition set so a 64-surrogate
single-year run can never be mistaken for evidence.

## 5. Genuine user/strategy forks (surface, don't auto-decide)

- **FDR α / method** (already flagged, `CROSS_IDEA_FDR_BUDGET_V1` §5): BH @ 0.10
  substrate default, overridable.
- **Surrogate budget**: ~1000 proposed (resolution-adequate for realistic batch
  sizes); confirm before it becomes the standing idea-contract default (it raises
  per-idea compute ~16×).
- **OOS window policy**: which years are discovery vs validation vs locked holdout,
  and which instruments — a pre-registration policy choice (compass §3.8).
- **Materialization scope**: unblocking the 27 label acceptance locks + which
  instrument/year grid to materialize is a compute-spend + data-acceptance decision
  (within the ~400G budget; not paid-data/live, so inside autonomy — but surface the
  scope before a multi-day run).
