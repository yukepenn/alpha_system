# ACCEPTANCE — ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1

This file defines the acceptance criteria for the campaign and for each
acceptance gate. A phase is **done** only when its lane checks pass, its handoff
exists, its review artifacts exist (Yellow), the artifact policy holds, and the
semantic done-check passes. The campaign is **done** only when every gate's exit
requirement is met, the final semantic done-check passes, and `CLOSEOUT.md`
records a verdict in `{COMPLETE, COMPLETE_WITH_WARNINGS, BLOCKED}`.

## Campaign-Level Acceptance

1. **Campaign contract completeness** — `GOAL.md`, `PHASE_PLAN.md`,
   `campaign.yaml`, `ACCEPTANCE.md`, `RISK_REGISTER.md`, `RUNBOOK.md` present and
   mutually consistent. No campaign-local `ACTIVE_CAMPAIGN.md`. Root
   `ACTIVE_CAMPAIGN.md` selects this campaign.
2. **Reality / handoff ingestion** — the measured `SUBSTRATE_REALITY_REPORT` and
   the Core Pilot closeout / scaleout handoff are reconciled into a locked
   baseline; the inherited promotion boundary (4 `REJECT` / 6 `INCONCLUSIVE` /
   0 `WATCH` / 0 `CANDIDATE_RESEARCH`) and the exact gaps are recorded.
3. **DatasetVersion inventory + acceptance-lock persistence** — every Databento
   yearly version (OHLCV-1m, OHLCV-dense, BBO-1m; ES/NQ/RTY; 2018→2026) carries a
   persisted `ACCEPTED | ACCEPTED_WITH_WARNINGS | BLOCKED` verdict with a coverage
   report. Registered alone is not treated as accepted.
4. **No external provider calls / no re-pull unless corrupt** — no Databento/IBKR
   API call; no agent raw-provider read; data is consumed from disk via registry
   tools.
5. **Roll metadata + roll-splice guard** — an approximate CME quarterly roll
   calendar is computed and persisted (documented as approximate, not
   provider-exact); the roll-splice guard with `roll_policy_id` /
   `roll_guard_version` + cross-roll policy + `roll_window` split is active and
   demonstrated on a known roll week.
6. **Maintenance-crossing guard** — no forward/extended label silently crosses
   the exchange daily maintenance / trade-date break.
7. **Keystone identity preflight** — `dry-run preview == execute == registry
   record == lock == resolver` verified on a representative slice; required
   registry metadata fields present.
8. **Materialization budget + batch plan** — a bounded, chunked, restart-safe
   batch plan with budgets/checkpoints and a serial registry resource guard
   exists; dry-run identity preview is produced before any execute.
9. **FeaturePack materialization per family** — all eight families (base OHLCV;
   session/calendar/maintenance; VWAP/session-auction; regime/vol/compression;
   liquidity-sweep/PA; volume/activity; BBO tradability/top-book; cross-market
   alignment) materialized + registered over the full window with `available_ts`,
   keystone identity, Parquet values, content hash, registry metadata.
10. **LabelPack materialization per family** — diagnostic 1m/3m; primary
    5m/10m/15m/30m; extended 60m/120m/240m; session-close + maintenance-flat;
    cost-adjusted; path (MFE/MAE, target-before-stop, triple-barrier where
    feasible) materialized + registered with `label_available_ts`, guards
    applied, horizon coverage + N_eff/overlap metadata.
11. **Parquet value storage + registry metadata** — research-scale values are
    registry-resolved Parquet; JSONL is audit-tier only; SQLite is metadata only;
    registry records store the required value/lineage fields.
12. **No committed values / local DBs / roll-calendar data** — `git ls-files
    runs` empty; no parquet/arrow/feather/sqlite/db/dbn/zst or roll-calendar data
    staged or tracked.
13. **Feature resolver smoke** — every representative feature lock resolves to a
    real Parquet value; resolver fails closed on stale/unresolvable.
14. **Label resolver smoke** — every representative label lock resolves to a real
    Parquet value; resolver fails closed.
15. **Coverage matrices** — feature-family coverage, label-family coverage,
    symbol×horizon, session×horizon, roll-window coverage, and
    maintenance-crossing invalidation matrices exist (value-free).
16. **BBO quality matrix** — exists, treating BBO as a tradability proxy (no
    execution-truth claim); missingness surfaced.
17. **Cross-market alignment matrix** — exists, with per-instrument
    `available_ts` preserved (no cross-instrument forward-fill).
18. **Walk-forward / purge / embargo runtime wiring** — `walk_forward_splits` +
    `apply_purge_embargo` are wired into the diagnostics path (or a minimal
    callable path + precise handoff) with STRUCTURAL/MEDIUM/FAST hooks.
19. **N_eff reporting** — overlap-aware effective-sample reporting present with a
    rows-vs-effective-samples distinction; extended horizons do not overstate
    N_eff; metadata available to Validation Governance.
20. **Core Pilot StudySpec re-lock + re-run where resolvable** — accepted
    StudySpecs re-locked where newly resolvable (StudySpec resolver-smoke PASS);
    the 6 INCONCLUSIVE studies re-run via runtime tools over locked Parquet with
    N_eff/walk-forward context.
21. **Honest verdict refresh** — refreshed verdicts use only `REJECT |
    INCONCLUSIVE | WATCH | CANDIDATE_RESEARCH`; any `WATCH`/`CANDIDATE_RESEARCH`
    carries an independent reviewer verdict; no profitability/tradability claim;
    promotion stays evidence- and cost-gated.
22. **Downstream handoff to Validation Governance** — concrete requirement
    handoff with deferred statistical scope + N_eff/fold metadata.
23. **Downstream handoff to FactorLibrary / Multi-Horizon Mining** — concrete
    handoffs exposing the materialized substrate + coverage matrices as the
    consumable base.
24. **Workflow 2 DAG consistency** — phase ids/names/lanes/deps/DAG metadata
    match between `PHASE_PLAN.md` and `campaign.yaml`; materialization phases
    share `resource_class: materialization_registry` and are not `parallel_safe`;
    serial merge respected; phase branches never write `ACTIVE_CAMPAIGN.md`.
25. **Artifact audit + closeout** — artifact audit clean; acceptance audit +
    semantic done-check pass; `CLOSEOUT.md` records the verdict; coordinator
    updates `ACTIVE_CAMPAIGN.md`; `verify.py --all` + canaries pass.

## Gate-Level Acceptance

### Gate `bootstrap_and_contract` — FUTSUB-P00…P05
Bundle present + consistent; no campaign-local pointer; reality baseline +
inherited boundary locked; DatasetVersion acceptance-lock persisted with coverage
verdicts; roll metadata + roll-splice guard primitive landed (approximate,
documented); keystone-identity preflight verified; bounded chunked restart-safe
batch plan + serial registry resource guard pinned (dry-run only); artifact audit
clean; no external provider calls; no values committed.

### Gate `feature_materialization` — FUTSUB-P06…P13 (drivers) + FUTSUB-P14 (run)
All eight per-family scaleout materialization drivers built (FUTSUB-P06…P13) with
keystone identity, Parquet-first output, serial registry writes, and value-free
coverage summaries. The actual full-accepted-window VALUE materialization was
deferred from P06…P13 because the WF2 executor sandbox could not write
`ALPHA_DATA_ROOT` at the time; that is resolved post-FCFP (the #299 sandbox grant),
and the consolidated V1 materialization now runs in **FUTSUB-P14** on the V1 fast
engine with FCFP-P15 worker parallelism (bounded-real 2024 first, then full
window): all eight families materialized + registered with `available_ts`,
keystone identity, Parquet values, content hash, and `producer_engine_id`
provenance; BBO treated as tradability proxy; cross-market preserves per-instrument
`available_ts` (no forward-fill); single-engine V1 feature substrate; coverage
summaries value-free; no value/SQLite/heavy artifact committed; registry writes
serialized.

### Gate `feature_integration` — FUTSUB-P14…P15
FUTSUB-P14 materializes all 8 feature families on V1 (above), then integrates the
feature registry (consistent); feature resolver-smoke PASS (fail closed);
feature-family coverage + quality/missingness matrix value-free with explicit gaps.

### Gate `label_materialization` — FUTSUB-P16…P20
Diagnostic/primary/extended/session-close/maintenance-flat/cost-adjusted/path
LabelPacks materialized + registered with `label_available_ts`, roll-splice +
maintenance-crossing guards applied, horizon coverage + N_eff/overlap metadata;
cost-adjusted uses documented cost/fee/slippage with BBO as proxy; coverage
summaries value-free; no value/SQLite committed; registry writes serialized.

### Gate `label_integration` — FUTSUB-P21…P23
Roll-splice + maintenance-crossing guards audited + demonstrated on a known roll
week/maintenance break; roll-window coverage + maintenance-crossing invalidation
matrices produced; label registry integrated; label resolver-smoke PASS;
label-family + symbol×horizon + session×horizon coverage matrices + horizon
quality report value-free.

### Gate `wiring_and_matrices` — FUTSUB-P24…P26
Purged/embargoed walk-forward wired into the diagnostics path (or a minimal
callable path + precise handoff) with STRUCTURAL/MEDIUM/FAST hooks; N_eff /
overlap-aware sample reporting present with a rows-vs-effective-samples
distinction; BBO quality + cross-market alignment matrices value-free.

### Gate `rerun` — FUTSUB-P27…P29
Core Pilot StudySpecs re-locked where newly resolvable (StudySpec resolver-smoke
PASS); previously INCONCLUSIVE studies re-run via runtime tools over locked
Parquet with N_eff/walk-forward context; honest verdicts refreshed (allowed
states only, reviewer verdict for any `WATCH`/`CANDIDATE`); no new specs, no
tuning, no promotion, no profitability claim; no value data committed.

### Gate `handoff_and_closeout` — FUTSUB-P30…P33
Artifact audit clean (`runs/` empty, no heavy/value/DB/roll-calendar artifact
tracked); concrete handoffs to Validation Governance, FactorLibrary, and
Multi-Horizon Mining; acceptance audit + semantic done-check pass; `CLOSEOUT.md`
records the final verdict; coordinator updates `ACTIVE_CAMPAIGN.md`;
`verify.py --all` + canaries pass.

Allowed final verdicts: `COMPLETE`, `COMPLETE_WITH_WARNINGS`, `BLOCKED`.

## Prohibited Shortcuts (any one fails acceptance)

- raw provider data read by agents; external provider API call; re-pull without
  proven corruption
- materialization without a persisted DatasetVersion acceptance-lock
- direct SQLite registry writes outside official tools; hand-patched locks
- resolver fallback by fuzzy feature/label name instead of failing closed
- JSONL used as a research-scale value store
- labels crossing a roll splice or maintenance break silently
- approximate roll calendar overclaimed as provider-exact
- full roll execution engine / IBKR contract resolver / per-contract mapping /
  back-adjusted construction
- BBO top-book proxy claimed as execution truth (passive fill / queue / impact)
- cross-market forward-fill across instruments; broken per-instrument
  `available_ts`
- missing `available_ts` / `label_available_ts`
- coverage matrices omitted; resolver smoke skipped; N_eff omitted or misleading
- unbounded or non-restart-safe materialization
- a re-run that becomes new alpha ideation, a new AlphaSpec batch, or parameter
  tuning beyond original bounds
- multiple-testing / DSR/PBO/PSR correction engine implemented here instead of
  handed off
- FactorLibrary ingestion / Strategy Reference / AlphaBook / Research Runner
  scope creep
- paper/live/broker/order scope; L1/L2 ingestion; ML training; portfolio
  construction
- any profitability / tradability / production / capital-allocation claim
- local Parquet/SQLite/roll-calendar/heavy artifacts committed; `runs/**` staged
- a parallel-scheduled phase without disjoint `allowed_paths`; a phase branch
  writing `ACTIVE_CAMPAIGN.md`; a merge outside the serial merge queue

## Acceptance Evidence

The closeout phase (`FUTSUB-P33`) must cite, for every criterion above, the
artifact path(s) under `research/futures_substrate_scaleout_v1/**`,
`handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/**`, and
`reviews/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/**` that satisfy it, plus
the final `verify.py --all` and canary results, and the `git ls-files runs` /
heavy-glob audit confirming all values remained local-only.
