# GOAL — ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1

## Campaign Identity

- Campaign ID: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Campaign path: `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Repo: `alpha_system`
- Repo path: `~/projects/alpha_system`
- Workflow: `workflow2` (Ralph strict autonomous loop, `dag_wave` scheduler;
  materialization phases are serialized by a shared registry `resource_class`,
  merge is always serial)
- Project profile: `trading_research` / `research` / `research_substrate_scaleout`
- Lane policy: Green/Yellow only; **no Red scope** in this campaign
- Phase count: 34 phases (`FUTSUB-P00` … `FUTSUB-P33`)
- Phase prefix: `FUTSUB-`

## Mission

`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` is the **bridge from the smoke /
pilot-scale substrate to a full research substrate**. It takes the existing,
already-deep Databento ES/NQ/RTY OHLCV-1m + BBO-1m history and the existing
feature/label/runtime code, and turns the current "code and data both present,
but full-window values not materialized" state into a **full-window, BBO-aware,
roll-guarded, resolver-safe research substrate** that the next campaigns can
consume directly.

It is **substrate engineering, not new alpha ideation**. The AlphaSpecs and
StudySpecs already exist (from the Core Pilot) and are reusable. This campaign
does not design a new alpha factory, does not build a platform, and does not
hunt for alpha. It materializes, guards, wires, measures, and re-runs.

## North Star

Maximize robust out-of-sample, cost-adjusted, capacity-aware, low-correlation
intraday Sharpe, subject to drawdown, turnover, liquidity, execution, and
reproducibility constraints. In this campaign that north star is served only by
**building honest, leakage-guarded substrate and evidence**, never by a
tradability or profitability claim.

## Why This Campaign Exists Now

`ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` completed `COMPLETE_WITH_WARNINGS` (31/31
phases) and proved two things end-to-end:

1. The **real research loop** works:

   ```text
   Hypothesis -> AlphaSpec -> StudySpec -> Runtime diagnostics
     -> cost / session / regime / no-lookahead review
     -> TrialLedger / RejectedIdeaLedger
     -> REJECT | INCONCLUSIVE | WATCH | CANDIDATE_RESEARCH
   ```

2. The **keystone identity / resolver invariant** holds:

   ```text
   dry-run identity preview == execute materialization == registry record
     == StudySpec lock == runtime resolver
   ```

   Resolver-smoke passed for 10 StudySpecs, 45 feature locks, and 30 label locks,
   all resolving to real materialized Parquet values, with zero fabricated values.

The pilot's final promotion boundary was **4 `REJECT`, 6 `INCONCLUSIVE`, 0
`WATCH`, 0 `CANDIDATE_RESEARCH`** — no FactorLibrary-ingestible survivor and no
Strategy Reference candidate. **This is not an alpha failure; it is a substrate
coverage finding.** Three of five families (regime, liquidity/PA, BBO) and the
cross-market family could not be evaluated because the only lock-resolvable
substrate is a **single-week (2024-01-02 → 2024-01-09), ES-only,
OHLCV-family/session-only smoke pack** with 5m/10m/30m labels.

The `docs/SUBSTRATE_REALITY_REPORT.md` measurement confirms the binding
constraint is **not data acquisition and not platform code** — it is
**materialization at scale + two guards (roll-splice, maintenance-crossing) +
N_eff / walk-forward wiring + acceptance-lock persistence**. Continuing to build
new platform layers would be procrastination; this campaign removes the real
blocker so `ALPHA_VALIDATION_GOVERNANCE_V1`, `ALPHA_FACTOR_LIBRARY_V1`, and
`ALPHA_FUTURES_MULTI_HORIZON_ALPHA_MINING_V1` can move fast.

## What The Core Pilot Proved (consumed, not re-proven)

- The hypothesis → diagnostics → ledger → verdict loop runs and stays bounded.
- Keystone content-addressing + resolver-smoke is a hard system invariant.
- The runtime fails closed on stale/unresolvable locks; it never substitutes.
- Honest outcomes only; no fabricated quotes or values.

## What The Core Pilot Exposed (the gaps this campaign closes)

- Lock-resolvable substrate is single-week / ES-only / OHLCV+session-only.
- Materialized features are mostly base OHLCV + two session features.
- Materialized labels are only 5m/10m/30m over one week.
- `FUTCORE-P18` regime lacked trendiness / volatility / compression values.
- `FUTCORE-P19` liquidity/PA lacked sweep / failed-breakout / wick /
  displacement / compression primitives as values.
- `FUTCORE-P20` BBO lacked a locked/materialized BBO top-book FeaturePack.
- Cross-market diagnostics lacked full ES/NQ/RTY aligned values.

## What The SUBSTRATE_REALITY_REPORT Measured

- **29 DatasetVersions registered** (9 OHLCV-1m, 9 OHLCV dense research grid,
  9 BBO-1m, 2 IBKR validation); symbols ES/NQ/RTY; Databento history 2018-01 →
  2026-05; BBO history fully present.
- **Registered ≠ accepted/locked**: every row carries the same DATA-P17
  status_message; there is **no persisted per-version accept/reject + coverage
  verdict** — so DatasetVersion acceptance-lock is in scope.
- Continuous series are **unadjusted provider-continuous** (`ES.v.0`, `NQ.v.0`,
  `RTY.v.0`; `v` = volume-based front, `0` = front rank); roll splices are real
  price jumps; no roll calendar data is materialized; the CME quarterly roll is
  analytically approximable but **not provider-exact**.
- Feature family code exists for `ohlcv`, `bbo`, `session`, `cross_market`,
  `structure` (liquidity/PA); label family code exists for `fixed_horizon`,
  `cost_adjusted`, `path`, `event`. Most families have **no full-window values**.
- `experiments/splits.py` has `train_validation_split`, `walk_forward_splits`,
  `apply_purge_embargo` — but the **runtime diagnostics path does not call them**;
  N_eff / overlap-aware reporting is missing.

## What Prior Layers Already Provide (consumed, not rebuilt)

- **Data**: registered Databento ES/NQ/RTY OHLCV-1m, OHLCV dense grid, and
  BBO-1m DatasetVersions over 2018→2026 (local-only under `ALPHA_DATA_ROOT`).
- **Feature/Label**: registry-resolved Parquet value sink + reader
  (`core/value_store.py`), dual JSONL+Parquet materialization, content-addressed
  identity (`fver_…`, `lver_…`), `available_ts` / `label_available_ts`,
  fail-closed leakage + availability-ordering guards, and the
  `alpha feature|label materialize|plan|list` CLI surface.
- **Runtime** (`src/alpha_system/runtime`): `input_resolver`, `tool_results`,
  diagnostics (`factor`, `cross_market`, `label`, `splits`), `cost`, reports.
- **Roll contracts** (`src/alpha_system/data/foundation/rolls.py`): `RollPolicy`
  / `RollCalendarRecord` contracts (no calendar data written yet).
- **Validation primitives** (`src/alpha_system/experiments/splits.py`):
  walk-forward + purge/embargo splits (not yet wired into the runtime path).

## What This Campaign Builds

- **DatasetVersion acceptance-lock**: persisted accept/block/warn + coverage
  verdicts for the Databento yearly versions (OHLCV-1m, OHLCV-dense, BBO-1m;
  ES/NQ/RTY; 2018→2026). No re-pull — the data is on disk.
- **Roll-boundary metadata + roll-splice guard**: an analytically computed CME
  quarterly roll calendar (documented as approximate), persisted
  `RollCalendarRecord`s, a label-window exclusion/flag policy, a `roll_window`
  regime split, and `roll_guard_version` / `roll_policy_id`. Treated as a
  **leakage / contamination guard**, not execution tooling.
- **Maintenance-crossing guard**: no forward label silently crosses the exchange
  daily maintenance / trade-date break, as a label materialization invariant.
- **Full-window FeaturePacks** (8 families): base OHLCV; session/calendar/
  maintenance; VWAP/session-auction; regime/volatility/compression; liquidity
  sweep/PA structure; volume/activity; BBO tradability/top-book; cross-market
  alignment. Each with `available_ts`, keystone identity, Parquet values,
  registry metadata, content hash, and a resolver-smoke gate.
- **Full-window LabelPacks**: diagnostic 1m/3m; primary 5m/10m/15m/30m; extended
  60m/120m/240m; session-close + maintenance-flat; cost-adjusted; path
  (MFE/MAE, target-before-stop, triple-barrier where feasible). Each with
  `label_available_ts`, roll-splice + maintenance-crossing guards, horizon
  coverage and N_eff / overlap metadata.
- **N_eff / overlap-aware sample reporting** inputs and **purged/embargoed
  walk-forward runtime wiring** (connect the existing `splits.py` primitives to
  the StudySpec → diagnostics path; STRUCTURAL / MEDIUM / FAST protocol hooks).
- **Coverage and quality matrices**: symbol×horizon, session×horizon,
  feature-family coverage, label-family coverage, BBO quality, cross-market
  alignment, roll-window coverage, maintenance-crossing invalidation.
- **Core Pilot re-lock + re-run**: re-lock accepted StudySpecs where newly
  resolvable; re-run the 6 INCONCLUSIVE studies (regime, liquidity/PA, BBO,
  enriched cross-market, enriched VWAP/session) against real materialized inputs;
  re-issue honest `REJECT | INCONCLUSIVE | WATCH | CANDIDATE_RESEARCH` verdicts.
- **Downstream handoffs** to Validation Governance, FactorLibrary, and
  Multi-Horizon Alpha Mining.

## What This Campaign Does NOT Build

- NOT new alpha ideation; NOT a new broad AlphaSpec batch; NOT a feature zoo
  beyond the existing governed families.
- NOT Strategy Reference validation; NOT FactorLibrary V1 ingestion; NOT
  AlphaBook; NOT a Research Runner.
- NOT paper trading, live trading, broker/order/execution; NOT an IBKR contract
  resolver; NOT a per-contract live roll / back-adjusted continuous engine; NOT
  ESM/NQM/RTYM tradable mapping.
- NOT L1/L2/L3 event-stream ingestion; NOT ML/DL/RL; NOT portfolio construction.
- NOT a full multiple-testing / false-discovery correction engine, full
  DSR/PBO/PSR framework, locked-test contamination ledger, or portfolio-level
  walk-forward (those are `ALPHA_VALIDATION_GOVERNANCE_V1`; this campaign only
  produces the **inputs** — N_eff + fold metadata).
- NOT any proof of profitability, tradability, production, or capital allocation.
- NOT external provider calls; NOT raw provider reads by agents; NOT a re-pull
  unless corruption is proven.

## DatasetVersion / Feature / Label / Runtime Contract

- Universe in scope: **ES, NQ, RTY**. Deferred: MES/MNQ/M2K, rates, FX,
  commodities, vol products, options, equities, per-contract tradable mappings,
  L1/L2/L3 event-stream, IBKR execution.
- Required data: existing Databento OHLCV-1m, OHLCV dense grid, BBO-1m
  DatasetVersions; Definition/Statistics/Status metadata where available;
  canonical timestamps; `available_ts`; `exchange_trade_date`; `session_segment`;
  continuous provenance; roll / approximate roll-boundary metadata;
  quality/missingness flags.
- Inputs resolved only through registry tools and `resolve_dataset_version`; no
  raw provider reads by agents, no external provider calls, no hand-read paths.
- Research-scale values are registry-resolved **Parquet**; JSONL is audit / small
  / smoke tier only; SQLite is metadata / pointer / lineage / hash only.
- Every feature has `available_ts`; every label has `label_available_ts`.
- Diagnostics run only through the runtime tool surface.

## Roll-Splice Guard Contract

- Compute / persist the approximate CME equity-index quarterly roll boundaries
  using the repo's roll contracts (`data/foundation/rolls.py`); persist
  `RollCalendarRecord`s (local-only).
- Document that boundaries are **approximate** (provider-internal volume-based
  splice not recoverable from the continuous series alone).
- Add a roll-splice guard for fixed-horizon and extended labels; record
  `roll_guard_version` and `roll_policy_id`; add a `roll_window` split; apply a
  drop / truncate / flag / invalid policy. No forward label silently books a
  contract-to-contract jump as a return.
- Out of scope: full live roll execution engine; IBKR contract resolver;
  ESM/NQM/RTYM mapping; complete per-contract back-adjusted construction.

## BBO Proxy Contract

- BBO-1m exists locally; this is a **materialization / lock gap, not a data gap**.
- Materialize BBO top-book FeaturePacks from the existing BBO DatasetVersions.
- Treat BBO-1m as a **time-sampled + forward-filled tradability proxy**; do not
  claim passive fill, queue priority, true intra-minute impact, or execution
  truth. Cost stress treats BBO as a proxy.
- Produce a BBO quality matrix (symbol × year × session × spread bucket ×
  missingness × bad-quote × depth/top-book availability × wide-spread regime).

## Cross-Market Contract

- Preserve per-instrument `available_ts`; **no cross-instrument forward-fill**.
- Produce a cross-market alignment matrix (lead-lag / residual states).

## Walk-Forward / N_eff Contract

- Wire the existing `walk_forward_splits` / `apply_purge_embargo` primitives into
  the StudySpec → diagnostics path; if a full refactor is required, ship a
  minimal callable path plus a precise handoff.
- Required now: N_eff / overlap-aware sample reporting; rows-vs-effective-samples
  distinction; horizon overlap metadata; session/day aggregation hooks; family
  half-life protocol hooks (STRUCTURAL / MEDIUM / FAST).
- Deferred to Validation Governance: full multiple-testing correction;
  DSR/PBO/PSR; locked-test contamination ledger; portfolio-level walk-forward.

## Core Pilot Re-Run Contract

- Re-lock accepted StudySpecs where newly resolvable; re-run the 6 INCONCLUSIVE
  studies against real materialized inputs.
- Outcomes remain `REJECT | INCONCLUSIVE | WATCH | CANDIDATE_RESEARCH`.
- No profitability/tradability claims; no Strategy Reference validation; no
  FactorLibrary promotion. Promotion stays evidence- and cost-gated; no human
  prior decides edge.

## Allowed Outputs

- DatasetVersion acceptance-lock records / docs / configs (verdicts persisted in
  the local registry; value-free summaries committed).
- Roll-boundary metadata / configs / tests; roll-splice guard specs/tests/code.
- FeaturePack and LabelPack materialization configs and minimal family-code
  repairs needed to materialize at scale.
- Value-store / registry metadata schema additions if needed.
- Resolver-smoke reports; coverage matrices; BBO quality matrix; cross-market
  alignment matrix; N_eff / overlap-aware sample report; walk-forward wiring
  smoke reports.
- Core Pilot re-run reports for previously INCONCLUSIVE studies where resolvable.
- Handoffs to Validation Governance / FactorLibrary / Multi-Horizon Mining.
- **No real Parquet, no local SQLite, no raw/canonical data in git.**

## Forbidden Outputs

`VALIDATED_RESEARCH`, `LIVE_APPROVED`, `PAPER_APPROVED`, `PRODUCTION_READY`,
`CAPITAL_ALLOCATED`, `PROFITABLE`, `TRADABLE`, `STRATEGY_READY`,
`PORTFOLIO_READY`; new alpha ideas; new broad AlphaSpec batch; Strategy Reference
validation; FactorLibrary promotion; AlphaBook allocation; paper/live/broker/
order code; IBKR contract resolver; full roll execution engine; L1/L2 ingestion;
ML model training; any profitability / tradability / production / capital
claim.

## Aggressive But Bounded Posture

- **Aggressive**: materialize real research-scale Parquet values (not more smoke
  JSONL) across the full 2018→2026 / ES+NQ+RTY window for all eight feature
  families and the full label horizon set; add the roll guard and N_eff now; wire
  walk-forward now; re-run the pilot's INCONCLUSIVE studies; make coverage gaps
  explicit and machine-reviewable.
- **Bounded**: no new alpha ideation; no feature zoo; no multiple-testing engine;
  no FactorLibrary/AlphaBook/Strategy Reference; no IBKR/live/roll engine; no
  L1/L2; no ML; no paper/live/broker/order; no profitability claim; no unbounded
  materialization without budget / chunking / checkpointing.

## Success Criteria

The campaign succeeds when:

- full ES/NQ/RTY OHLCV+BBO DatasetVersions are accepted/locked or explicitly
  blocked with reasons (persisted coverage verdicts);
- full-window FeaturePacks and LabelPacks are materialized and registered with
  stable keystone identity;
- registry-resolved Parquet values pass resolver-smoke (feature, label, and
  representative + Core Pilot StudySpecs);
- the roll-splice guard prevents/flags labels crossing roll boundaries and is
  demonstrated on a known roll week; the maintenance-break guard prevents/flags
  extended horizons crossing the daily maintenance break;
- BBO top-book values are materialized as a tradability proxy (not execution
  truth); cross-market alignment values preserve per-instrument `available_ts`;
- N_eff / overlap-aware sample counts appear in diagnostics or are made available
  to Validation Governance; walk-forward / purge / embargo is wired or clearly
  handed off;
- all coverage matrices exist; the BBO quality and cross-market alignment
  matrices exist;
- the Core Pilot INCONCLUSIVE studies are re-run with honest verdicts;
- no alpha is promoted without evidence; no raw/canonical/value Parquet or local
  SQLite registry is committed; no paper/live/broker/profitability/tradability
  claim is made.

## Closeout Handoffs

`FUTSUB-P31` / `FUTSUB-P32` produce concrete, evidence-driven requirement
handoffs to:

- `ALPHA_VALIDATION_GOVERNANCE_V1` — multiple-testing / false-discovery
  correction, locked-test policy, contamination ledger, negative controls,
  promotion eligibility, DSR/PBO/PSR (or alternatives) for survivors, plus the
  N_eff and fold metadata produced here.
- `ALPHA_FACTOR_LIBRARY_V1` — FactorCard / EvidenceBundle ingestion path for any
  survivors and the substrate metadata they depend on.
- `ALPHA_FUTURES_MULTI_HORIZON_ALPHA_MINING_V1` — the coverage matrices and
  materialized substrate as the directly consumable mining base.

## Boundaries Summary

```text
Data ≠ Feature ≠ Factor ≠ Signal ≠ Strategy ≠ Portfolio ≠ Execution
Registered ≠ Accepted/Locked
Materialized value ≠ Validated alpha
Fast path ≠ Reference truth
Runtime diagnostics ≠ Strategy Reference validation
BBO top-book proxy ≠ execution truth
Approximate roll calendar ≠ provider-exact roll truth
Validated research ≠ paper/live approval
Candidate ≠ capital allocation
Agent ≠ autonomous trader ≠ self-reviewer ≠ self-promoter
```

This is the campaign **goal contract**. The executable per-phase contracts live
in `PHASE_PLAN.md` and `campaign.yaml`; acceptance in `ACCEPTANCE.md`; risks in
`RISK_REGISTER.md`; operations in `RUNBOOK.md`.
