# PHASE_PLAN — ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1

34 phases (`FUTSUB-P00` … `FUTSUB-P33`) over a `dag_wave` scheduler with
`parallel_execution: true`, `max_parallel_phases: 3`, and a **serial merge
queue**. Phase ids, names, lanes, dependencies, and DAG metadata are the source
of truth in `campaign.yaml`; this file mirrors them and adds the human-readable
contract per phase. Any disagreement between the two files is a STOP condition.

## Materialization Serialization Note

`alpha feature materialize` and `alpha label materialize` **materialize AND
register inline**, writing the shared local SQLite registries
(`registry/features.sqlite`, `registry/labels.sqlite`). To avoid concurrent
SQLite registry corruption, every phase that writes the registry shares
`resource_class: materialization_registry` and is **not** `parallel_safe`. The
scheduler therefore serializes them. This keeps the campaign DAG-aware (mode
`dag_wave`) without forcing unsafe parallel registry writes; a future
deferred-registry-write design could re-enable path-disjoint parallel waves.
**No phase is `parallel_safe` in this campaign** — the entire campaign runs as a
serial DAG with a serial merge queue.

## Scheduler Wave Map

```text
Sequential : FUTSUB-P00 -> P01 -> P02 -> P03 -> P04 -> P05            (bootstrap / contract)
Serialized : FUTSUB-P06 P07 P08 P09 P10 P11 P12 P13                   (FeaturePack scaleout DRIVERS; shared registry resource_class)
Sequential : FUTSUB-P14 -> P15                                        (V1 feature MATERIALIZATION [all 8 families, workers] + integration + coverage)
Serialized : FUTSUB-P16 P17 P18 P19 P20                              (LabelPacks; shared registry resource_class)
Sequential : FUTSUB-P21 -> P22 -> P23                                 (label guard audit + integration + coverage)
Sequential : FUTSUB-P24 -> P25 -> P26                                 (walk-forward wiring + N_eff + matrices)
Sequential : FUTSUB-P27 -> P28 -> P29                                 (Core Pilot re-lock + re-run + verdict refresh)
Sequential : FUTSUB-P30 -> P31 -> P32 -> P33                          (artifact audit + handoffs + closeout)
```

Merge is always one PR at a time. Bootstrap / contract / integration / audit /
wiring / rerun / closeout phases are `must_run_alone`.

## Phase Summary Table

| Phase | Name | Lane | Deps | parallel_safe | must_run_alone | resource_class | merge_group | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `FUTSUB-P00` | Campaign Bootstrap and Active Pointer | GREEN | — | false | true | — | bootstrap | bootstrap_and_contract |
| `FUTSUB-P01` | Reality Report Lock and Core Pilot Handoff Ingestion | YELLOW | P00 | false | true | — | foundation | bootstrap_and_contract |
| `FUTSUB-P02` | DatasetVersion Inventory and Acceptance-Lock Contract | YELLOW | P01 | false | true | materialization_registry | foundation | bootstrap_and_contract |
| `FUTSUB-P03` | Continuous Series / Roll Metadata / Roll-Splice Guard Contract | YELLOW | P02 | false | true | — | foundation | bootstrap_and_contract |
| `FUTSUB-P04` | Value Store / Registry / Keystone Identity Preflight | YELLOW | P03 | false | true | — | foundation | bootstrap_and_contract |
| `FUTSUB-P05` | Materialization Budget, Batch Plan, and Resource Guard | YELLOW | P04 | false | true | — | foundation | bootstrap_and_contract |
| `FUTSUB-P06` | Scaleout Materialization Driver + Base OHLCV FeaturePack Scaleout | YELLOW | P05 | false | false | materialization_registry | feature_materialization | feature_materialization |
| `FUTSUB-P07` | Session / Calendar / Maintenance FeaturePack Scaleout | YELLOW | P05 | false | false | materialization_registry | feature_materialization | feature_materialization |
| `FUTSUB-P08` | VWAP / Session Auction FeaturePack Scaleout | YELLOW | P05 | false | false | materialization_registry | feature_materialization | feature_materialization |
| `FUTSUB-P09` | Regime / Volatility / Compression FeaturePack Scaleout | YELLOW | P05 | false | false | materialization_registry | feature_materialization | feature_materialization |
| `FUTSUB-P10` | Liquidity Sweep / PA Structure FeaturePack Scaleout | YELLOW | P05 | false | false | materialization_registry | feature_materialization | feature_materialization |
| `FUTSUB-P11` | Volume / Activity FeaturePack Scaleout | YELLOW | P05 | false | false | materialization_registry | feature_materialization | feature_materialization |
| `FUTSUB-P12` | BBO Tradability / Top-Book FeaturePack Scaleout | YELLOW | P05 | false | false | materialization_registry | feature_materialization | feature_materialization |
| `FUTSUB-P13` | Cross-Market Alignment FeaturePack Scaleout | YELLOW | P05, P06 | false | false | materialization_registry | feature_materialization | feature_materialization |
| `FUTSUB-P14` | FeaturePack Registry Integration, Coverage Audit, and Resolver Smoke | YELLOW | P06–P13 | false | true | materialization_registry | feature_integration | feature_integration |
| `FUTSUB-P15` | Feature Coverage Matrix and Quality Report | YELLOW | P14 | false | true | — | feature_integration | feature_integration |
| `FUTSUB-P16` | Fixed-Horizon LabelPack Scaleout: 1m/3m/5m/10m/15m/30m | YELLOW | P15 | false | false | materialization_registry | label_materialization | label_materialization |
| `FUTSUB-P17` | Extended Intraday LabelPack Scaleout: 60m/120m/240m | YELLOW | P15 | false | false | materialization_registry | label_materialization | label_materialization |
| `FUTSUB-P18` | Session-Close and Maintenance-Flat LabelPack Scaleout | YELLOW | P15 | false | false | materialization_registry | label_materialization | label_materialization |
| `FUTSUB-P19` | Cost-Adjusted LabelPack Scaleout | YELLOW | P15, P16 | false | false | materialization_registry | label_materialization | label_materialization |
| `FUTSUB-P20` | Path LabelPack Scaleout: MFE/MAE/Target-Before-Stop/Triple-Barrier | YELLOW | P15 | false | false | materialization_registry | label_materialization | label_materialization |
| `FUTSUB-P21` | Roll-Splice and Maintenance-Crossing Label Guard Audit | YELLOW | P16–P20 | false | true | — | label_integration | label_integration |
| `FUTSUB-P22` | LabelPack Registry Integration, Coverage Audit, and Resolver Smoke | YELLOW | P21 | false | true | materialization_registry | label_integration | label_integration |
| `FUTSUB-P23` | Label Coverage Matrix and Horizon Quality Report | YELLOW | P22 | false | true | — | label_integration | label_integration |
| `FUTSUB-P24` | Purged / Embargo Walk-Forward Runtime Wiring | YELLOW | P23 | false | true | — | wiring | wiring_and_matrices |
| `FUTSUB-P25` | N_eff / Overlap-Aware Sample Reporting | YELLOW | P24 | false | true | — | wiring | wiring_and_matrices |
| `FUTSUB-P26` | BBO Quality and Cross-Market Alignment Matrices | YELLOW | P23 | false | true | — | wiring | wiring_and_matrices |
| `FUTSUB-P27` | Re-lock Core Pilot StudySpecs Against Full Substrate | YELLOW | P15, P23, P25 | false | true | — | rerun | rerun |
| `FUTSUB-P28` | Re-run Previously INCONCLUSIVE Core Pilot Studies | YELLOW | P27 | false | true | — | rerun | rerun |
| `FUTSUB-P29` | Honest Verdict Refresh and Scaleout Evidence Summary | YELLOW | P28 | false | true | — | rerun | rerun |
| `FUTSUB-P30` | Artifact Audit and Local-Only Value Verification | YELLOW | P29 | false | true | — | closeout | handoff_and_closeout |
| `FUTSUB-P31` | Validation Governance Handoff | YELLOW | P30 | false | true | — | closeout | handoff_and_closeout |
| `FUTSUB-P32` | FactorLibrary / Multi-Horizon Mining Handoff | YELLOW | P31 | false | true | — | closeout | handoff_and_closeout |
| `FUTSUB-P33` | Acceptance Audit and Closeout | YELLOW | P32 | false | true | — | closeout | handoff_and_closeout |

## Common Per-Phase Contract Defaults

- **Executor**: Codex GPT-5.5 high. **Reviewer**: Claude Opus 4.8 xhigh.
  **Verifier**: Claude Sonnet 4.6.
- **Forbidden changes (all phases)**: `execution/`, `broker/`, `live/`,
  `signals/`, `strategies/`, `portfolio/`, `management/`, `l2/`, `backtest/`,
  `agent_factory/`; raw/canonical data; heavy artifacts (parquet/arrow/feather/
  dbn/zst); local SQLite registries and roll-calendar data; paper/live/broker/
  order; IBKR contract resolver; full roll execution engine; L1/L2; ML;
  FactorLibrary ingestion; Strategy Reference; AlphaBook; new alpha ideation /
  AlphaSpec batch; parameter tuning beyond original bounds.
- **Artifact policy (all phases)**: explicit staging only; never `git add .` /
  `-A`; never commit `runs/**`, values, SQLite registries, roll-calendar data,
  heavy artifacts, or provider responses; only value-free summaries / code /
  tests / docs / handoffs / reviews are commit-eligible.
- **Review (all Yellow phases)**: fresh Claude Opus review required.
  **Auto-merge**: Green auto-merges after checks; Yellow auto-merges after a
  passing review; merge is serial.

## Per-Phase Contracts

### FUTSUB-P00 — Campaign Bootstrap and Active Pointer
- **Lane**: GREEN · **Deps**: none · **parallel_safe**: false · **must_run_alone**: true
- **Purpose**: Land the 6-file bundle, root active pointer, and doc/evidence scaffolding so Workflow 2 can plan.
- **Scope**: confirm bundle consistency; create docs index + value-free evidence skeleton; update root `ACTIVE_CAMPAIGN.md` (coordinator-owned).
- **Non-goals**: any acceptance-lock, materialization, guard, or diagnostics; any value/DB writes.
- **Expected files**: `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/**`, `docs/futures_substrate_scaleout/README.md`+`OVERVIEW.md`, `research/futures_substrate_scaleout_v1/README.md`+`.gitkeep`, `handoffs/…/FUTSUB-P00.md`, `reviews/…/FUTSUB-P00/**`, `ACTIVE_CAMPAIGN.md`, `runs/**`.
- **Validation**: bundle `test -f` checks; `test '!' -f …/ACTIVE_CAMPAIGN.md`; YAML parse; `grep -q` campaign id in pointer; `python tools/verify.py --smoke`; `git ls-files runs`.
- **Done**: bundle present + consistent; root pointer selects this campaign; no campaign-local pointer; YAML parses; smoke passes; `runs/` untracked.
- **Handoff**: `handoffs/…/FUTSUB-P00.md` · **Review**: optional (Green).

### FUTSUB-P01 — Reality Report Lock and Core Pilot Handoff Ingestion
- **Lane**: YELLOW · **Deps**: P00 · **must_run_alone**: true
- **Purpose**: Lock the measured substrate reality + Core Pilot closeout handoff as the factual baseline.
- **Scope**: reconcile `docs/SUBSTRATE_REALITY_REPORT.md` + closeout/scaleout handoff into one locked baseline; record the inherited boundary (4 REJECT / 6 INCONCLUSIVE / 0 WATCH / 0 CANDIDATE) and the exact gaps; confirm consumed primitives import.
- **Non-goals**: editing primitives; materializing values; diagnostics.
- **Expected files**: `docs/futures_substrate_scaleout/REALITY_LOCK.md`, `research/futures_substrate_scaleout_v1/preflight/**`, handoff/review, `runs/**`.
- **Validation**: import `runtime/features/labels/experiments.splits/data.foundation.rolls`; smoke; baseline files exist; `git ls-files runs`.
- **Done**: baseline + inherited boundary + gap list recorded; primitives import; smoke passes; no primitive edited.

### FUTSUB-P02 — DatasetVersion Inventory and Acceptance-Lock Contract
- **Lane**: YELLOW · **Deps**: P01 · **must_run_alone**: true · **resource_class**: materialization_registry
- **Purpose**: Inventory registered DatasetVersions and add a persisted acceptance-lock with coverage verdicts (closes registered≠accepted).
- **Scope**: inventory OHLCV-1m / OHLCV-dense / BBO-1m (ES/NQ/RTY, 2018→2026) via registry tools; **compute real coverage evidence from on-disk canonical data** through sanctioned readers only (`data.foundation.canonical_loader` + per-version canonical `manifest.json` `row_count`) — extend `_coverage_evidence_from_registry_metadata` in `datasets.py` to populate all five evidence dimensions (`row_count_sanity`, `gap_coverage`, `required_field_presence`, `missingness_quality_flags`, `roll_metadata` from P03's roll calendar; `continuous_provenance` already resolves from registry metadata) instead of leaving them unavailable; persist honest `ACCEPTED` / `ACCEPTED_WITH_WARNINGS` (2026 partial year) / `BLOCKED` (genuine gaps only) + coverage report per version via `alpha data accept-datasets` (no re-pull unless corrupt); commit only the value-free summary.
- **Non-goals**: re-pull; external calls; materializing features/labels; tradability claims; fabricating coverage evidence or silently accepting without computed evidence.
- **Expected files**: `src/alpha_system/data/foundation/datasets.py`, `src/alpha_system/cli/registry.py`/`data.py`, `configs/data/dataset_acceptance/**`, `research/…/dataset_acceptance/**`, `docs/…/DATASET_ACCEPTANCE.md`, tests, handoff/review.
- **Validation**: smoke; `pytest test_dataset_acceptance.py`; summary/doc exist; `git ls-files runs` + heavy globs empty.
- **Done**: every yearly version carries a persisted accept/block/warn + coverage verdict **computed from real on-disk canonical evidence** (local registry); a clean full-history corpus yields mostly `ACCEPTED` (2026 `ACCEPTED_WITH_WARNINGS`), not a uniform `BLOCKED` grid; summary value-free; no re-pull; no value/SQLite committed.

### FUTSUB-P03 — Continuous Series / Roll Metadata / Roll-Splice Guard Contract
- **Lane**: YELLOW · **Deps**: P02 · **must_run_alone**: true
- **Purpose**: Compute approximate CME quarterly roll boundaries + add a roll-splice guard primitive (leakage guard, not execution tooling).
- **Scope**: compute the analytic roll calendar + persist `RollCalendarRecord`s (local-only) via `data/foundation/rolls.py`; add a roll-splice guard helper with `roll_policy_id` + `roll_guard_version` + drop/truncate/flag/invalid policy + `roll_window` split; document boundaries as approximate; tests on a known roll week.
- **Non-goals**: full live roll engine; IBKR/per-contract mapping; back-adjusted construction; execution.
- **Expected files**: `src/alpha_system/data/foundation/rolls.py`, `src/alpha_system/labels/roll_guard.py`, `configs/data/roll_calendar/**`, `research/…/roll_guard/**`, `docs/…/ROLL_GUARD.md`, tests, handoff/review.
- **Validation**: smoke; `pytest test_roll_guard.py`; docs/contract exist; heavy globs empty.
- **Done**: roll calendar computed (approximate, documented); guard with policy id/version + cross-roll policy + `roll_window` split; tests pass; no calendar data committed.

### FUTSUB-P04 — Value Store / Registry / Keystone Identity Preflight
- **Lane**: YELLOW · **Deps**: P03 · **must_run_alone**: true
- **Purpose**: Confirm/extend value-store + registry metadata so keystone identity + resolver-smoke hold at scale.
- **Scope**: verify `dry-run preview == execute == registry record == lock == resolver` on a representative slice; add any missing registry metadata fields (`value_store_format`/`parquet_path`/`value_content_hash`/`value_schema_version`/`dataset_version_id`/version ids); record the preflight.
- **Non-goals**: full accepted-window materialization; editing runtime diagnostics; alpha work.
- **Expected files**: `src/alpha_system/core/value_store.py`, `src/alpha_system/features/engine/materialization.py`, `research/…/preflight/**`, `docs/…/KEYSTONE_IDENTITY.md`, tests, handoff/review.
- **Validation**: smoke; `pytest test_keystone_identity.py`; preflight report exists; heavy globs empty.
- **Done**: keystone identity verified on a slice; required metadata present; preflight value-free; no full materialization yet.

### FUTSUB-P05 — Materialization Budget, Batch Plan, and Resource Guard
- **Lane**: YELLOW · **Deps**: P04 · **must_run_alone**: true
- **Purpose**: Pin the bounded, chunked, restart-safe materialization plan + serial registry resource guard before any full accepted-window write.
- **Scope**: define per-family / per-symbol / per-year batch units with row/file budgets + checkpoints; define the `materialization_registry` serial resource guard + restart-safe recovery; produce the dry-run identity preview (no execute).
- **Non-goals**: executing materialization; editing runtime diagnostics; alpha work.
- **Expected files**: `configs/features/scaleout/**`, `configs/labels/scaleout/**`, `research/…/materialization/**`, `docs/…/MATERIALIZATION_PLAN.md`, handoff/review.
- **Validation**: smoke; batch plan + plan doc exist; heavy globs empty.
- **Done**: bounded chunked restart-safe batch plan + serial registry resource guard; dry-run only; no execute; no values committed.

### FUTSUB-P06 — Scaleout Materialization Driver + Base OHLCV FeaturePack Scaleout
- **Lane**: YELLOW · **Deps**: P05 · **resource_class**: materialization_registry
- **Purpose**: Build the reusable multi-family scaleout materialization driver (the substrate tool for P06–P13 features and P16–P20 labels) and use it to materialize the base OHLCV FeaturePack over the full accepted materialization window for ES/NQ/RTY. The real blocker is missing scaleout **orchestration**, not missing market data: `alpha feature materialize` is a seed/smoke `seed_pack.v1` operator and nothing iterates the family × symbol × accepted-year grid.
- **Scope**: BUILD a generic scaleout driver (module + CLI) that iterates the family × symbol × accepted-year grid and per unit REUSES the existing family engines (`features/families/*`) + sanctioned `canonical_loader`/BBO loaders + the official keystone registry write path (`FeatureStore.register_materialized_feature`, as in `seed_pack.run_seed_feature_pack`) — never hand-write registry records, never weaken resolver semantics, never bypass acceptance. Window = ACCEPTED + ACCEPTED_WITH_WARNINGS DatasetVersions (BLOCKED 2018 excluded, see `2018_BLOCKED_DIAGNOSIS.md`). **Parquet-first** (JSONL audit/smoke only; no full-history JSONL). **Checkpoint/restart** by family/symbol/dataset_version_id-year/feature_set (completed units skipped). **Serial** keystone registry writes. Use it to materialize base OHLCV **bounded-real first** (one recent accepted year, e.g. 2024, ES/NQ/RTY) then expand to the full accepted window. Commit only value-free driver code + CLI + tests + coverage summary + config.
- **Non-goals**: new features beyond the base family; diagnostics; alpha work; new AlphaSpecs; full-history JSONL payloads; per-symbol acceptance.
- **Expected files**: `src/alpha_system/features/scaleout/**`, `src/alpha_system/cli/scaleout.py`/`cli/feature.py`, `src/alpha_system/features/families/ohlcv/**`, `configs/features/scaleout/**`, `research/…/feature_packs/base_ohlcv/**`, `research/…/scaleout_driver/**`, `docs/futures_substrate_scaleout/SCALEOUT_DRIVER.md`, tests, handoff/review.
- **Validation**: smoke; `git ls-files runs` + heavy globs empty.
- **Done**: scaleout driver built (generic, Parquet-first, checkpointed, serial registry) + base OHLCV materialized/registered over the full accepted window with `available_ts`/keystone identity/Parquet/content hash/registry metadata, bounded-real validated before full expansion; coverage summary value-free; no value/SQLite/heavy artifact committed.

### FUTSUB-P07 — Session / Calendar / Maintenance FeaturePack Scaleout
- **Lane**: YELLOW · **Deps**: P05 · **resource_class**: materialization_registry
- **Purpose**: Materialize the full accepted-window session/calendar/maintenance FeaturePack (RTH/ETH flags, session-minute, maintenance-window flags, holiday/half-day, minutes-to-close/maintenance where available).
- **Scope**: materialize + register over the full accepted materialization window; enforce point-in-time SESSION_METADATA / role-aware guard; enforce identity/Parquet/hash/metadata; commit value-free summary + config.
- **Non-goals**: new session features; diagnostics; alpha work.
- **Expected files**: `src/alpha_system/features/families/session/**`, `configs/features/scaleout/session_calendar_maintenance.json`, `research/…/feature_packs/session_calendar_maintenance/**`, test, handoff/review.
- **Done**: as base feature done-criteria; point-in-time session guard respected.

### FUTSUB-P08 — VWAP / Session Auction FeaturePack Scaleout
- **Lane**: YELLOW · **Deps**: P05 · **resource_class**: materialization_registry
- **Purpose**: Materialize VWAP / session-auction features (running VWAP, anchored/ETH VWAP, distance-to-VWAP, opening/overnight range, RTH-open context).
- **Scope**: distinguish running vs final VWAP (no final-session aggregate used intraday); identity/Parquet/hash/metadata; value-free summary + config.
- **Non-goals**: new features beyond family; diagnostics; alpha work.
- **Expected files**: `src/alpha_system/features/families/ohlcv/**`+`session/**`, `configs/features/scaleout/vwap_session_auction.json`, `research/…/feature_packs/vwap_session_auction/**`, test, handoff/review.
- **Done**: as base feature done-criteria; running-vs-final VWAP distinguished.

### FUTSUB-P09 — Regime / Volatility / Compression FeaturePack Scaleout
- **Lane**: YELLOW · **Deps**: P05 · **resource_class**: materialization_registry
- **Purpose**: Materialize regime features (trendiness, ATR/vol-regime buckets, range compression/expansion, momentum/reversion state) to unblock the pilot regime study (P18).
- **Scope**: materialize + register full accepted-window; identity/Parquet/hash/metadata; value-free summary + config.
- **Non-goals**: new regime features; diagnostics; alpha work.
- **Expected files**: `src/alpha_system/features/families/structure/**`+`ohlcv/**`, `configs/features/scaleout/regime_volatility_compression.json`, `research/…/feature_packs/regime_volatility_compression/**`, test, handoff/review.
- **Done**: as base feature done-criteria.

### FUTSUB-P10 — Liquidity Sweep / PA Structure FeaturePack Scaleout
- **Lane**: YELLOW · **Deps**: P05 · **resource_class**: materialization_registry
- **Purpose**: Materialize liquidity-sweep / PA-structure features (prior-high/low sweep, close-back-inside, wick rejection, displacement, compression breakout, failed breakout) to unblock the pilot liquidity/PA study (P19).
- **Scope**: objective PA primitives only; identity/Parquet/hash/metadata; value-free summary + config.
- **Non-goals**: subjective/discretionary PA; new features; diagnostics; alpha work.
- **Expected files**: `src/alpha_system/features/families/structure/**`, `configs/features/scaleout/liquidity_sweep_pa_structure.json`, `research/…/feature_packs/liquidity_sweep_pa_structure/**`, test, handoff/review.
- **Done**: as base feature done-criteria; objective primitives only.

### FUTSUB-P11 — Volume / Activity FeaturePack Scaleout
- **Lane**: YELLOW · **Deps**: P05 · **resource_class**: materialization_registry
- **Purpose**: Materialize volume/activity features (participation, time-of-day relative volume, volume regime, activity bursts, effort/result proxies) using existing primitives only.
- **Scope**: existing primitives only (no volume zoo); identity/Parquet/hash/metadata; value-free summary + config.
- **Non-goals**: new volume feature zoo; diagnostics; alpha work.
- **Expected files**: `src/alpha_system/features/families/ohlcv/**`+`structure/**`, `configs/features/scaleout/volume_activity.json`, `research/…/feature_packs/volume_activity/**`, test, handoff/review.
- **Done**: as base feature done-criteria; existing primitives only.

### FUTSUB-P12 — BBO Tradability / Top-Book FeaturePack Scaleout
- **Lane**: YELLOW · **Deps**: P05 · **resource_class**: materialization_registry
- **Purpose**: Materialize BBO top-book features from existing BBO DatasetVersions (mid, spread, spread_ticks, spread_zscore, top-book depth/imbalance, missing_bbo/bad_quote/wide_spread/low_depth flags, microprice-ish proxy) to close the pilot P20 data gap.
- **Scope**: treat BBO-1m as a **time-sampled + forward-filled tradability proxy** (no execution-truth/passive-fill/queue/impact claims); identity/Parquet/hash/metadata; value-free summary + config.
- **Non-goals**: passive-fill/queue/impact/execution claims; new BBO features; diagnostics; alpha work.
- **Expected files**: `src/alpha_system/features/families/bbo/**`, `configs/features/scaleout/bbo_tradability_top_book.json`, `research/…/feature_packs/bbo_tradability_top_book/**`, test, handoff/review.
- **Done**: BBO top-book family materialized + registered full accepted-window as a tradability proxy (no execution-truth claim) with identity/Parquet/hash/metadata; coverage summary value-free; no value/SQLite committed.

### FUTSUB-P13 — Cross-Market Alignment FeaturePack Scaleout
- **Lane**: YELLOW · **Deps**: P05, P06 · **resource_class**: materialization_registry
- **Purpose**: Materialize cross-market alignment features (ES/NQ/RTY aligned returns, beta residual, basket residual, relative-strength rank, catch-up/rotation, divergence/agreement, lead-lag) preserving per-instrument `available_ts`.
- **Scope**: strict per-instrument `available_ts` (**no cross-instrument forward-fill**); identity/Parquet/hash/metadata; value-free summary + config.
- **Non-goals**: cross-instrument forward-fill; new features; diagnostics; alpha work.
- **Expected files**: `src/alpha_system/features/families/cross_market/**`, `configs/features/scaleout/cross_market_alignment.json`, `research/…/feature_packs/cross_market_alignment/**`, test, handoff/review.
- **Done**: cross-market family materialized + registered full accepted-window with per-instrument `available_ts` preserved (no forward-fill across instruments) + identity/Parquet/hash/metadata; coverage summary value-free; no value/SQLite committed.

### FUTSUB-P14 — FeaturePack Registry Integration, Coverage Audit, and Resolver Smoke
- **Lane**: YELLOW · **Deps**: P06–P13 · **must_run_alone**: true · **resource_class**: materialization_registry
- **Purpose**: Integrate all FeaturePack registrations, audit registry consistency, and prove a **feature resolver-smoke** (every feature lock resolves to a real Parquet value).
- **Scope**: audit identity/hash/metadata across all 8 families; run resolver-smoke (fail closed on stale/unresolvable); commit value-free integration + resolver-smoke report.
- **Non-goals**: materializing new values; diagnostics; alpha work.
- **Expected files**: `research/…/feature_packs/**` (incl. `feature_resolver_smoke.md`), `docs/…/FEATURE_INTEGRATION.md`, test, handoff/review.
- **Done**: 8 families integrated; registry consistent; feature resolver-smoke PASS (fail-closed verified); report value-free; no value/SQLite committed.

### FUTSUB-P15 — Feature Coverage Matrix and Quality Report
- **Lane**: YELLOW · **Deps**: P14 · **must_run_alone**: true
- **Purpose**: Produce the feature-family coverage matrix (family × symbol × year) + quality/missingness report as gating inputs.
- **Scope**: value-free coverage + missingness summaries; flag families/instruments/years that do not resolve; record gaps.
- **Non-goals**: diagnostics; alpha work; value commits.
- **Expected files**: `research/…/matrices/feature_family_coverage.md`, `docs/…/FEATURE_COVERAGE.md`, handoff/review.
- **Done**: coverage matrix + quality report value-free; gaps explicit/machine-reviewable; no values committed.

### FUTSUB-P16 — Fixed-Horizon LabelPack Scaleout: 1m/3m/5m/10m/15m/30m
- **Lane**: YELLOW · **Deps**: P15 · **resource_class**: materialization_registry
- **Purpose**: Materialize fixed-horizon LabelPacks (diagnostic 1m/3m + primary 5m/10m/15m/30m) with `label_available_ts` and roll/maintenance guards applied at materialization.
- **Scope**: apply roll-splice + maintenance-crossing guards; enforce `label_available_ts`, horizon coverage, N_eff/overlap metadata; value-free summary + config.
- **Non-goals**: new label families; diagnostics; alpha work; silent cross-roll/maintenance windows.
- **Expected files**: `src/alpha_system/labels/families/fixed_horizon/**`, `configs/labels/scaleout/fixed_horizon.json`, `research/…/label_packs/fixed_horizon/**`, test, handoff/review.
- **Done**: LabelPack materialized + registered full accepted-window with `label_available_ts`, guards applied, horizon coverage + N_eff/overlap metadata; coverage summary value-free; no value/SQLite/heavy artifact committed.

### FUTSUB-P17 — Extended Intraday LabelPack Scaleout: 60m/120m/240m
- **Lane**: YELLOW · **Deps**: P15 · **resource_class**: materialization_registry
- **Purpose**: Materialize extended-horizon LabelPacks (60m/120m/240m) with stronger roll/maintenance guards and overlap-aware N_eff metadata.
- **Scope**: guards (no silent crossing); `label_available_ts`, horizon coverage, overlap-aware N_eff (extended horizons must not overstate N_eff); value-free summary + config.
- **Non-goals**: new families; diagnostics; alpha work; silent crossing; N_eff inflation.
- **Expected files**: `src/alpha_system/labels/families/fixed_horizon/**`, `configs/labels/scaleout/extended_horizon.json`, `research/…/label_packs/extended_horizon/**`, test, handoff/review.
- **Done**: as fixed-horizon label done-criteria; extended-horizon N_eff not overstated.

### FUTSUB-P18 — Session-Close and Maintenance-Flat LabelPack Scaleout
- **Lane**: YELLOW · **Deps**: P15 · **resource_class**: materialization_registry
- **Purpose**: Materialize to-session-close and to-maintenance-flat LabelPacks with close-out semantics that never silently cross a maintenance break.
- **Scope**: explicit close-out semantics; `label_available_ts`, maintenance-crossing guard, horizon coverage; value-free summary + config.
- **Non-goals**: new families; diagnostics; alpha work; positions crossing the maintenance/trade-date break.
- **Expected files**: `src/alpha_system/labels/families/fixed_horizon/**`+`event/**`, `configs/labels/scaleout/session_close_maintenance_flat.json`, `research/…/label_packs/session_close_maintenance_flat/**`, test, handoff/review.
- **Done**: as fixed-horizon label done-criteria; maintenance-crossing guard enforced.

### FUTSUB-P19 — Cost-Adjusted LabelPack Scaleout
- **Lane**: YELLOW · **Deps**: P15, P16 · **resource_class**: materialization_registry
- **Purpose**: Materialize cost-adjusted LabelPacks (mid-to-mid, spread crossing, fee-adjusted where a cost model exists, slippage-stress adjusted where supported).
- **Scope**: use existing cost model + BBO spreads as a **proxy** (not execution truth); `label_available_ts`, roll/maintenance guards, horizon coverage; document cost/fee/slippage assumptions + versions; value-free summary + config.
- **Non-goals**: new cost model; execution-truth claims; stale fee/slippage assumptions; diagnostics; alpha work.
- **Expected files**: `src/alpha_system/labels/families/cost_adjusted/**`, `configs/labels/scaleout/cost_adjusted.json`, `research/…/label_packs/cost_adjusted/**`, test, handoff/review.
- **Done**: cost-adjusted LabelPack materialized + registered with documented cost/fee/slippage versions, BBO-as-proxy, `label_available_ts` + guards + horizon coverage; coverage summary value-free; no value/SQLite committed.

### FUTSUB-P20 — Path LabelPack Scaleout: MFE/MAE/Target-Before-Stop/Triple-Barrier
- **Lane**: YELLOW · **Deps**: P15 · **resource_class**: materialization_registry
- **Purpose**: Materialize path LabelPacks (MFE, MAE, target-before-stop, triple-barrier where feasible) with roll/maintenance guards.
- **Scope**: materialize where feasible; flag where compute is too expensive/unstable + record the bound; `label_available_ts`, guards, horizon coverage; value-free summary + config.
- **Non-goals**: new families; diagnostics; alpha work; silent crossing.
- **Expected files**: `src/alpha_system/labels/families/path/**`, `configs/labels/scaleout/path.json`, `research/…/label_packs/path/**`, test, handoff/review.
- **Done**: as fixed-horizon label done-criteria; expensive/unstable cases flagged with the bound recorded.

### FUTSUB-P21 — Roll-Splice and Maintenance-Crossing Label Guard Audit
- **Lane**: YELLOW · **Deps**: P16–P20 · **must_run_alone**: true
- **Purpose**: Audit that every materialized LabelPack correctly applies the roll-splice + maintenance-crossing guards, demonstrated on a known roll week + maintenance break.
- **Scope**: verify no forward label silently books a roll jump or crosses a maintenance break; produce roll-window coverage + maintenance-crossing invalidation matrices; record the cross-roll policy applied.
- **Non-goals**: materializing new values; alpha work; full roll execution engine.
- **Expected files**: `research/…/matrices/**` (roll_window_coverage, maintenance_crossing_invalidation), `research/…/roll_guard/**`, `docs/…/ROLL_GUARD_AUDIT.md`, test, handoff/review.
- **Validation**: smoke; `canary_runner`; matrices exist; `git ls-files runs`.
- **Done**: guards verified across all LabelPacks + demonstrated; matrices value-free; canaries pass; no values committed.

### FUTSUB-P22 — LabelPack Registry Integration, Coverage Audit, and Resolver Smoke
- **Lane**: YELLOW · **Deps**: P21 · **must_run_alone**: true · **resource_class**: materialization_registry
- **Purpose**: Integrate all LabelPack registrations, audit consistency, and prove a **label resolver-smoke** (every label lock resolves to a real Parquet value).
- **Scope**: audit `label_available_ts`/hash/metadata across all horizon/label families; run resolver-smoke (fail closed); commit value-free report.
- **Non-goals**: materializing new values; diagnostics; alpha work.
- **Expected files**: `research/…/label_packs/**` (incl. `label_resolver_smoke.md`), `docs/…/LABEL_INTEGRATION.md`, test, handoff/review.
- **Done**: LabelPacks integrated; registry consistent; label resolver-smoke PASS (fail-closed verified); report value-free; no value/SQLite committed.

### FUTSUB-P23 — Label Coverage Matrix and Horizon Quality Report
- **Lane**: YELLOW · **Deps**: P22 · **must_run_alone**: true
- **Purpose**: Produce label-family coverage matrix (label family × symbol × horizon × year) + symbol×horizon + session×horizon coverage + horizon quality report with overlap/N_eff context.
- **Scope**: value-free coverage + quality summaries; record horizon overlap + N_eff context; flag non-resolving horizons/instruments.
- **Non-goals**: diagnostics; alpha work; value commits.
- **Expected files**: `research/…/matrices/**` (label_family_coverage, symbol_horizon_coverage, session_horizon_coverage), `docs/…/LABEL_COVERAGE.md`, handoff/review.
- **Done**: coverage matrices + horizon quality report value-free with overlap/N_eff context; gaps explicit; no values committed.

### FUTSUB-P24 — Purged / Embargo Walk-Forward Runtime Wiring
- **Lane**: YELLOW · **Deps**: P23 · **must_run_alone**: true
- **Purpose**: Wire `walk_forward_splits` / `apply_purge_embargo` into the StudySpec → runtime diagnostics path with family half-life protocols.
- **Scope**: plumb `walk_forward_splits` + `apply_purge_embargo` (`purge_gap`/`embargo_gap`) into the diagnostics evaluation path; add STRUCTURAL/MEDIUM/FAST hooks; produce a wiring smoke report; if a full refactor is required, ship a minimal callable path + precise handoff to Validation Governance.
- **Non-goals**: full multiple-testing correction; DSR/PBO/PSR; locked-test contamination ledger; portfolio-level walk-forward; alpha work.
- **Expected files**: `src/alpha_system/runtime/diagnostics/splits/**`+`factor/**`+`contracts.py`, `research/…/wiring/**`, `docs/…/WALK_FORWARD_WIRING.md`, test, handoff/review.
- **Validation**: smoke; `pytest test_walk_forward_wiring.py`; wiring smoke report exists.
- **Done**: purge/embargo walk-forward wired (or minimal callable path + handoff) with STRUCTURAL/MEDIUM/FAST hooks; wiring smoke PASS; no values committed.

### FUTSUB-P25 — N_eff / Overlap-Aware Sample Reporting
- **Lane**: YELLOW · **Deps**: P24 · **must_run_alone**: true
- **Purpose**: Add overlap-aware effective-sample-size (N_eff) reporting so overlapping intraday/extended labels are not counted as independent samples.
- **Scope**: N_eff / overlap-aware sample-count reporting with a rows-vs-effective-samples distinction + horizon overlap metadata + session/day aggregation hooks; produce an N_eff sample report; make N_eff + fold metadata available to Validation Governance.
- **Non-goals**: full multiple-testing engine; alpha work.
- **Expected files**: `src/alpha_system/runtime/diagnostics/splits/**`+`label/**`, `research/…/wiring/**`, `docs/…/N_EFF.md`, test, handoff/review.
- **Validation**: smoke; `pytest test_n_eff_reporting.py`; N_eff report exists.
- **Done**: N_eff reporting present with rows-vs-effective-samples distinction + overlap + session/day hooks; report value-free; metadata available to Validation Governance; no values committed.

### FUTSUB-P26 — BBO Quality and Cross-Market Alignment Matrices
- **Lane**: YELLOW · **Deps**: P23 · **must_run_alone**: true
- **Purpose**: Produce the BBO quality matrix + cross-market alignment matrix as gating inputs (BBO as proxy; per-instrument availability preserved).
- **Scope**: BBO quality matrix (symbol × year × session × spread bucket × missingness × bad-quote × depth × wide-spread regime); cross-market alignment matrix (lead-lag/residual states) with per-instrument `available_ts` preserved; value-free summaries.
- **Non-goals**: execution-truth/passive-fill claims; cross-instrument forward-fill; alpha work; value commits.
- **Expected files**: `research/…/matrices/**` (bbo_quality, cross_market_alignment), `docs/…/BBO_AND_CROSS_MARKET_MATRICES.md`, handoff/review.
- **Done**: BBO quality (proxy) + cross-market alignment (availability preserved) matrices value-free; no values committed.

### FUTSUB-P27 — Re-lock Core Pilot StudySpecs Against Full Substrate
- **Lane**: YELLOW · **Deps**: P15, P23, P25 · **must_run_alone**: true
- **Purpose**: Re-lock Core Pilot accepted StudySpecs against the new full substrate, proving every lock resolves to a real Parquet value.
- **Scope**: re-lock StudySpecs (feature + label locks) where newly resolvable; run StudySpec resolver-smoke (fail closed); record which previously INCONCLUSIVE studies are now resolvable (regime, liquidity/PA, BBO, enriched cross-market, enriched VWAP/session); commit value-free re-lock report.
- **Non-goals**: new AlphaSpec batch; parameter tuning; promotion; alpha ideation; value commits.
- **Expected files**: `research/…/rerun/studyspec_relock.md`, `docs/…/CORE_PILOT_RELOCK.md`, test, handoff/review.
- **Done**: StudySpecs re-locked where newly resolvable; StudySpec resolver-smoke PASS; resolvable-study list value-free; no new specs; no value/SQLite committed.

### FUTSUB-P28 — Re-run Previously INCONCLUSIVE Core Pilot Studies
- **Lane**: YELLOW · **Deps**: P27 · **must_run_alone**: true
- **Purpose**: Re-run the 6 INCONCLUSIVE studies against real materialized inputs via the runtime tool surface, with N_eff + walk-forward in the path.
- **Scope**: re-run regime, liquidity/PA, BBO, enriched cross-market, enriched VWAP/session via runtime tools over locked Parquet; produce value-free DiagnosticsReports with N_eff/overlap + walk-forward context; no value data committed; no promotion here.
- **Non-goals**: new AlphaSpec batch; tuning beyond original bounds; profitability/tradability claims; FactorLibrary promotion; value commits.
- **Expected files**: `research/…/rerun/rerun_diagnostics_summary.md`, `docs/…/CORE_PILOT_RERUN.md`, handoff/review.
- **Done**: studies re-run via runtime tools over locked Parquet with N_eff/walk-forward context; value-free DiagnosticsReports; no new specs; no promotion; no value/SQLite committed.

### FUTSUB-P29 — Honest Verdict Refresh and Scaleout Evidence Summary
- **Lane**: YELLOW · **Deps**: P28 · **must_run_alone**: true
- **Purpose**: Re-issue honest `REJECT | INCONCLUSIVE | WATCH | CANDIDATE_RESEARCH` verdicts for the re-run studies + summarize scaleout evidence, with reviewer verdicts for any WATCH/CANDIDATE.
- **Scope**: refreshed verdicts (allowed states only); independent reviewer verdict required for any WATCH/CANDIDATE_RESEARCH; summarize updated boundary vs inherited 4 REJECT / 6 INCONCLUSIVE / 0 WATCH / 0 CANDIDATE; no profitability/tradability claims; promotion evidence/cost-gated.
- **Non-goals**: new alpha; tuning; Strategy Reference validation; FactorLibrary promotion; value commits.
- **Expected files**: `research/…/rerun/verdict_refresh.md`, `docs/…/VERDICT_REFRESH.md`, handoff/review.
- **Done**: refreshed verdicts use only allowed states with reviewer verdicts for any WATCH/CANDIDATE; updated boundary recorded; no profitability claim; no promotion; no values committed.

### FUTSUB-P30 — Artifact Audit and Local-Only Value Verification
- **Lane**: YELLOW · **Deps**: P29 · **must_run_alone**: true
- **Purpose**: Verify all materialized values, registries, and roll-calendar data remain local-only and only value-free summaries are committed.
- **Scope**: artifact audit (`git ls-files runs` empty; no parquet/arrow/feather/sqlite/db/dbn/zst tracked); confirm registries + roll-calendar data stay under `ALPHA_DATA_ROOT` / local-only; record the audit report.
- **Non-goals**: materializing values; alpha work.
- **Expected files**: `research/…/closeout/artifact_audit.md`, `docs/…/ARTIFACT_AUDIT.md`, handoff/review.
- **Validation**: `verify.py --all`; `canary_runner`; heavy-glob `git ls-files` empty.
- **Done**: artifact audit clean; `runs/` empty; no heavy/value/DB artifact tracked; registries + roll-calendar local-only; `verify.py --all` + canaries pass (or env-only failures documented).

### FUTSUB-P31 — Validation Governance Handoff
- **Lane**: YELLOW · **Deps**: P30 · **must_run_alone**: true
- **Purpose**: Produce the concrete requirement handoff to `ALPHA_VALIDATION_GOVERNANCE_V1`, carrying N_eff/fold metadata + the deferred statistical scope.
- **Scope**: specify multiple-testing / false-discovery correction, locked-test policy, contamination ledger, negative controls, promotion eligibility, DSR/PBO/PSR (or alternatives), + N_eff/fold metadata; reference coverage matrices + walk-forward wiring as inputs.
- **Non-goals**: implementing the governance engine; alpha work; value commits.
- **Expected files**: `handoffs/…/VALIDATION_GOVERNANCE_HANDOFF.md`, `research/…/closeout/**`, `docs/…/HANDOFF_VALIDATION_GOVERNANCE.md`, handoff/review.
- **Done**: concrete handoff with deferred statistical scope + N_eff/fold metadata + references; value-free; no values committed.

### FUTSUB-P32 — FactorLibrary / Multi-Horizon Mining Handoff
- **Lane**: YELLOW · **Deps**: P31 · **must_run_alone**: true
- **Purpose**: Produce the concrete handoffs to `ALPHA_FACTOR_LIBRARY_V1` and `ALPHA_FUTURES_MULTI_HORIZON_ALPHA_MINING_V1`, exposing the materialized substrate + coverage matrices as the consumable base.
- **Scope**: specify FactorCard / EvidenceBundle ingestion requirements + the substrate metadata survivors depend on; specify the materialized substrate + matrices as the consumable mining base; no mining started.
- **Non-goals**: FactorLibrary ingestion implementation; AlphaBook; mining; alpha work; value commits.
- **Expected files**: `handoffs/…/FACTOR_LIBRARY_HANDOFF.md`, `handoffs/…/MULTI_HORIZON_MINING_HANDOFF.md`, `research/…/closeout/**`, `docs/…/HANDOFF_FACTOR_LIBRARY_AND_MINING.md`, handoff/review.
- **Done**: concrete FactorLibrary + Multi-Horizon Mining handoffs exposing the substrate + matrices; value-free; no mining started; no values committed.

### FUTSUB-P33 — Acceptance Audit and Closeout
- **Lane**: YELLOW · **Deps**: P32 · **must_run_alone**: true
- **Purpose**: Run the acceptance audit + semantic done-check, write `CLOSEOUT.md` with a final verdict, and update the coordinator `ACTIVE_CAMPAIGN.md`.
- **Scope**: verify every acceptance gate's exit requirement with cited evidence; write `CLOSEOUT.md` (`{COMPLETE, COMPLETE_WITH_WARNINGS, BLOCKED}`); update the root pointer (coordinator-owned); run final `verify.py --all` + canaries.
- **Non-goals**: new materialization; alpha work; promotion claims.
- **Expected files**: `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/CLOSEOUT.md`, `research/…/closeout/**`, `docs/…/CLOSEOUT.md`, `ACTIVE_CAMPAIGN.md`, handoff/review.
- **Validation**: `verify.py --all`; `canary_runner`; `CLOSEOUT.md` exists; `grep -q` campaign id in pointer; heavy-glob empty.
- **Done**: acceptance audit + semantic done-check pass; `CLOSEOUT.md` records the verdict; coordinator updates `ACTIVE_CAMPAIGN.md`; `verify.py --all` + canaries pass (or env-only failures documented); no values committed.
