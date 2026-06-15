# BROAD_MINING_DRIVER_V0 — multi-partition pooled run + unattended mining loop

Status: BUILT (integration; lands the single highest-leverage build of
`decisions/BROAD_MINING_READINESS_V1/ROADMAP.md` §3 — closes #5 driver + #2 OOS
pooling). Date: 2026-06-15. Lane: Yellow (research/engineering integration).
Research-only. No PnL/value truth. The machine NEVER auto-promotes.

## 0. What this integrates (no recreation)

This is pure INTEGRATION: every component already existed on main and was merely
unconnected. The new module `src/alpha_system/research_lane/mining_driver.py`
wires them together; it recreates none of them.

| Reused (unchanged) | file:symbol | role in the driver |
|---|---|---|
| per-partition probe | `research_lane/fast_probe.py:fast_probe` | run once per declared partition SliceSpec |
| typed readout | `research_lane/fast_readout.py:FastReadout` | harvest the component metric from typed fields (no string-spelunk) |
| OOS aggregator (was ORPHANED) | `governance/pooled_hypothesis.py:aggregate_pooled_metric` | pool present partitions into the cross-partition OOS statistic |
| pooled pre-registration | `governance/pooled_hypothesis.py:{PooledHypothesisRegistry,generate_pooled_hypothesis_id,validate_pooled_hypothesis_record}` | pre-register the pooled hypothesis (registry append optional, opt-in by path) |
| verdict routing + family-FDR | `research_lane/memory_router.py:route_verdict_to_memory` | route the POOLED verdict through the Stage-B family-FDR gate → shelf/requeue/graveyard |
| append-only ledgers | `agent_factory/memory/store.py:{persist_route,read_ledger,resolve_research_memory_dir,ensure_family_fdr_ledger_path}` | per-idea + pooled provenance; the loop's idempotent resume record |

New surface:
- `research_lane/mining_driver.py:run_multi_partition_pool` — Part A orchestrator.
- `research_lane/mining_driver.py:mine_ideas` — Part B unattended loop.
- `cli/idea.py:run_idea_mine` + the `alpha idea mine` subcommand — the CLI driver.

## 1. Part A — multi-partition pooled run (the OOS rung)

`run_multi_partition_pool(idea_payload, idea_draft, mechanism_card, setup_spec,
partition_slice_ids, ...)`:

1. Runs `fast_probe` once per declared partition SliceSpec (`_probe_partitions`).
   When no resolver is supplied it passes `resolver=None` through to `fast_probe`
   so the probe builds a resolver rooted at EACH slice's resolved data root.
2. Harvests each partition's component metric from the **typed** `FastReadout`
   (`_partition_outcome_from_readout`): the setup-lane net-excursion
   `continuous_lift_summary.mean_lift` as the point estimate and the single
   canonical `FastReadout.n_eff` accessor — no recursive key search.
3. Pools the present partitions via `aggregate_pooled_metric` (`_pool_components`):
   for ≥2 present partitions this is a genuine cross-partition OOS pool over a
   pre-registered `PooledHypothesisRecord`; for exactly 1 present partition it
   reports a degenerate single-component `PooledMetricResult` (the pooled contract
   needs ≥2 members — a 1-partition "pool" is NOT OOS) and `pooled_hypothesis_id`
   is `None`.
4. Routes the POOLED verdict through `route_verdict_to_memory` with the family-FDR
   ledger wired, so multiplicity + the reviewer shelf gate apply to the pooled
   result exactly as for a single-idea setup signal.
5. Records the per-partition + pooled outcome to the research-memory ledgers (when
   `persist`).

## 2. Partition-coverage honesty guard (ROADMAP §4 silent-danger guard)

Only `ES_2020_120m` is materialized today; the other label partitions are BLOCKED
(ROADMAP #4). The driver therefore enforces:

- A declared partition whose data/descriptor is absent is **NOT silently skipped**:
  `fast_probe` returns an honest DATA_GAP, or an undeclared slice id yields a
  fail-closed DATA_GAP `PartitionOutcome` (`_missing_partition_outcome`) — never a
  dropped row.
- The pooled result **ALWAYS** carries explicit `PartitionCoverage`
  (declared / present / missing slice ids, `present_count`,
  `is_multi_partition_oos`). A pooled verdict states its coverage so a 1-partition
  "OOS" can never masquerade as multi-year evidence.
- When **zero** partitions resolve, the run **fails closed** with a DATA_GAP pooled
  verdict, no pooled metric, and no route — the run never fabricates a pooled
  statistic from absent data.

This is the same false-signal failure mode as
`law-overlap-aware-ic-power-n-eff`, one layer up: an un-coverage-stated pool would
let a single materialized year look like multi-year OOS evidence.

## 3. Part B — unattended mining loop (the driver)

`mine_ideas(idea_paths, partition_policy=..., ...)` and the `alpha idea mine` CLI:

1. Take a SET of idea files (explicit paths and/or a `--directory` of
   `*.idea.yaml`/`*.idea.json`) + an optional `--partition` policy.
2. For each idea: load + validate → run the Part-A pooled run → record the verdict
   → next idea, WITHOUT a human per idea. One idea's failure is recorded as an
   `error` result and does not abort the batch.
3. Resumable/idempotent: an idea whose AlphaSpec id already appears in any route
   ledger is skipped (`already_recorded_alpha_spec_ids`) — the append-only ledgers
   ARE the progress record; no new progress file.
4. Emits a run summary (`MiningLoopSummary`): counts per route (shelf / requeue /
   graveyard / data-gap) and per status (mined / skipped / error), plus each
   idea's partition coverage.
5. NEVER auto-promotes: the independent reviewer shelf + capital gate are
   unchanged.

## 4. Deferred follow-ups (explicitly out of scope for V0)

- **Concurrency / parallel researchers.** The loop is single-threaded. Multi-writer
  concurrency-safety on the shared append-only ledgers (route ledgers + the
  family-FDR accumulator) is the explicit follow-up before parallel mining.
- **Idea generation / breadth (ROADMAP #3).** No enumerator; ideas are still
  hand-authored YAMLs. This must land AFTER the sound-gate plumbing (this build),
  else breadth = more false positives.
- **Materialization (ROADMAP #4).** The 27 BLOCKED label acceptance locks are
  unchanged; only `ES_2020_120m` is materialized, so real multi-year pooling waits
  on materialization. The driver is correct for N partitions and degrades honestly
  (coverage-stated) to the 1 materialized partition today.
- **Surrogate adequacy (ROADMAP #1).** Surrogate budgets stay per-idea; bumping
  64→~1000 is a separate idea-contract change.
- **Pooled StudySpec contract.** Per-partition pooled member refs are minted
  deterministically (`_partition_member_ref`, a StudySpec-kind id) to satisfy the
  `aggregate_pooled_metric` fixed-membership contract, because the ideas carry no
  per-partition StudySpec today. A real per-partition StudySpec pre-registration is
  a follow-up.

## 5. Tests + validation

`tests/unit/research_lane/test_mining_driver.py`: multi-partition pooling
correctness (2–3 synthetic partition readouts → expected `aggregate_pooled_metric`
mean + summed n_eff); partition-coverage reporting; missing-partition and
undeclared-partition fail-closed DATA_GAP; all-missing → fail-closed DATA_GAP with
no pooled metric/route; pooled verdict routes through the family-FDR gate
(shelf when resolution-adequate + cleared, requeue when not); the loop skips
already-recorded ideas (idempotent) and records errors without aborting.
N-partition pooling is tested on synthetic readouts (no unmaterialized data
required). The real `ES_2020_120m` partition is exercised as a degenerate
1-partition pool to prove the end-to-end path on real materialized data, carrying
explicit coverage=1.
