# RESEARCH TRUTH RECONCILIATION

**Date:** 2026-06-15 · **Author:** Command Center Brain (coordinator) ·
**Mandate:** v3 Step 1 (truth reconciliation before any new mining) ·
**Method:** 4-lane repo archaeology crew, every claim cited to on-disk
artifacts / git history. This is a **descriptive evidence record**, research-only,
no profitability/tradability claim. Companion to `GROUND_TRUTH_AND_ROUTE.md`.

> One-line truth: **the simple factor / linear-IC hypothesis space on
> ES/NQ/RTY is a repeatedly-confirmed, well-powered NULL (0 survivors across 4
> campaigns).** The PnL backtest engine has **never** run on real data and has
> **never** produced a Sharpe. The setup / path-outcome lane is **built but
> barely exercised** (2 dogfood attempts, both single-class `DATA_GAP`).

---

## A. What has already been tested (campaign ledger)

| Campaign | Symbols | Years | Horizons | WF / purge / embargo | Diagnostic | Survivors | Verdict |
|---|---|---|---|---|---|---|---|
| **FUTCORE** `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` | ES/NQ/RTY | not pinned (pilot packs) | 5/10/15/30m (+1/3m diag) | **No** (WF deferred to validation-gov v1) | IC (Pearson+rank) + path + cost-stress | **0** | `COMPLETE_WITH_WARNINGS`; 4 REJECT (cross-market, missing NQ/RTY legs) + 6 INCONCLUSIVE (unresolved feature/label bindings) |
| **FUTSUB** `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` | ES/NQ/RTY | **2019–2026** (2018 BLOCKED, sparse) | 1/3/5/10/15/30/60/120/240m + session/maint | **Yes** — purge=embargo=10, **61–67 WF folds** | IC (Pearson+rank), bucket monotonicity | **0** | substrate engineering success; all 6 prior-INCONCLUSIVE → **REJECT** (near-zero IC, no monotonicity). Campaign status BLOCKED = **admin/review-provenance**, NOT science |
| **DK** `DIFFERENTIATED_KILLSHOT_V1` | ES/NQ/RTY pooled | 2024–26 calendar coverage | 5/30m (Track A), 120m (Track B) | surrogate-FDR ZERO_PASS **before** any real metric | Track A IC; Track B path-outcome (`target_before_stop`) | **0** | 4 REJECT (day_of_week, opex, month_end, open_close) + roll_week `DATA_GAP` + Track B `DATA_GAP` (single-class slice) |
| **IVL** `ALPHA_IDEA_TO_VERDICT_LOOP_V0` | ES | 2020 (60m seeds), 2020/2024 (120m dogfood) | 60m (main_effect), 120m (setup) | overlap-aware n_eff (PR #474), surrogate-FDR | main_effect IC; context≠trigger path | **0** | 5 graveyard (well-powered null) + 1 requeue (`distance_to_vwap`, underpowered/borderline) + 0 signal; 2 Track-B dogfood → `DATA_GAP` (single-class) |

Repo evidence anchors (representative, full cites in crew reports / git):
- FUTCORE: `research/futures_core_alpha_pilot_v1/promotion/PROMOTION_DECISIONS.md:12-14`,
  `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/CLOSEOUT.md:7-10,34`,
  `campaign.yaml:529-533` (WF deferred), `campaign.yaml:20-22` ("not a backtester… no profitability claim").
- FUTSUB: `research/futures_substrate_scaleout_v1/rerun/verdict_refresh.md:51-56` (REJECT 10 / WATCH 0 / CANDIDATE 0),
  `rerun_diagnostics_summary.md:74-85` (61–67 folds, purge=embargo=10, IC near-zero, monotonicity false),
  `dataset_acceptance/acceptance_summary.md:24,33` (2019–2026; 2018 BLOCKED), `CLOSEOUT.md:5,14-24` (BLOCKED = artifact provenance).
- DK: `research/differentiated_substrate_v1/CAMPAIGN_VERDICT.md:53-61,84-109`,
  `verdict_refresh.md:26-27,52-58,67-73`.
- IVL: `~/alpha_data/alpha_system/research_memory/{graveyard.jsonl (5), requeue.jsonl (1)}`,
  git `bfd0b10` (PR #474 overlap n_eff), `GROUND_TRUTH_AND_ROUTE.md`.

---

## B. Per-family classification (graveyard / requeue / follow-up)

**Factor / main_effect families — all GRAVEYARD (well-powered null), do NOT re-run:**
distance_to_vwap*, opening_range_position, prior_high_distance, prior_low_distance,
range_contraction, trendiness, cross_market lead-lag/beta-residual, regime
momentum/reversion, liquidity-sweep/failed-breakout PA *as a linear factor*,
BBO tradability *as a linear factor*, day_of_week, opex_pinning, month_end_flow,
open_close_auction_flow.

> \*`distance_to_vwap` is the single **REQUEUE** (IVL `requeue.jsonl`): IC = −0.0557
> with honest 60m overlap MDE ≈ 0.0266 — borderline but flagged underpowered/evidence-accrual,
> NOT a survivor. Not promotable; revisit only with more independent years, not a re-run of the same slice.

**Setup / path-outcome (context≠trigger) — DATA_GAP, follow-up REQUIRED (not null):**
DK Track B + 2 IVL dogfood ideas all hit **single-class `target_before_stop`**
(`horizon_no_barrier` — at the chosen 120m horizon/geometry the barrier was never
touched, so the path label had only one class → no test was possible). This is a
**geometry/horizon/data-shape gap, NOT a science null.** The lane has never had a
fair test.

**Roll-week flow — DATA_GAP** (`CALIBRATION_BLOCKED`); substrate gap, not a null.

---

## C. Clarifications (mandate-required)

1. **FUTSUB already ran multi-year (2019–2026) walk-forward IC (61–67 folds).**
   → Do NOT rebuild it. The previously-proposed "cross-year consistency
   aggregation" build is **CANCELLED** as a FUTSUB reinvention (REUSE-MAP). The
   simple-factor IC question is *answered: null*.

2. **A true Strategy-Reference PnL on real multi-year data has NEVER run.**
   The reference engine (`src/alpha_system/backtest/reference.py:52-69`) only ever
   ran on **synthetic fixtures** (`tests/fixtures/backtest_reference.py:1-2`
   "not market evidence… not from real market data"; experiments runner uses
   `synthetic_bars(4)` `experiments/runner.py:383`; CLI reads `read_csv_fixture_bars`).
   **No Sharpe is computed anywhere** — `BacktestSummary` (`results.py:38-67`) has
   gross/cost/net/equity but **no Sharpe field**; repo-wide `grep -i sharpe *.py` = empty.
   → Recorded GAP: real-data end-to-end PnL + a Sharpe calculator are unbuilt.

3. **PA/setup path-outcome diagnostics are BUILT and runnable, but barely tested.**
   SetupSpec (`governance/setup_spec.py:96-274`), path metrics
   (`labels/path_metrics.py:31-150`), event extraction (`research/events.py:77-112`),
   conditional probe (`research/conditional_probe.py:88-321`), and the fast_probe
   `CONTEXT_NOT_EQUAL_TRIGGER` lane (`research_lane/fast_probe.py:118-135,328-389`,
   incl. label-shuffle surrogate-FDR gate) all exist. → Recorded GAP: needs (a) a
   slice whose path label is genuinely **multi-class** at the chosen horizon/geometry,
   and (b) real authored PA SetupSpecs. This is the **least-explored lane**.

4. **TBBO is NOT canonicalized and OOMs on full-month in-memory decode.** →
   Recorded as **background cost-truth refinement**, NOT mainline (BBO already
   canonical + `bbo_tradability` materialized → proxy cost labels already use real
   BBO spread). See `tbbo-cost-calibration-asset` memory. Do not block discovery on it.

5. **Earlier "profitable / multi-year / walk-forward alpha" memory — reconciled.**
   The Captain was **RIGHT** that we ran genuine multi-year (2019–2026) walk-forward
   with purge+embargo (FUTSUB, 61–67 folds) — I previously under-stated this and
   own the error. The Captain's memory of *profitable* alpha is **not supported by
   any artifact**: every campaign recorded **0 survivors**, near-zero IC, and
   explicit no-profitability language; no Sharpe was ever computed. The likely
   source of the "profitable" memory is conflation of *engineering* success
   (substrate built, loop works) with *alpha* success (there was none), plus the
   pre-PR-#474 inflated-n_eff readouts that briefly looked like "signals" before the
   overlap fix correctly reclassified them to well-powered nulls.

6. **Any historical real multi-year NET PnL signal?** → **None found.** No real-data
   PnL run, no Sharpe, no survivor, in any campaign. Strongest negative evidence:
   FUTSUB `verdict_refresh.md:160-166` explicit non-claim; repo-wide no Sharpe.

---

## D. Route decision (feeds the Route Arbiter, §3 of mandate)

Given (a) simple factor/IC = exhaustively-confirmed null, (b) setup/path lane =
built-but-never-fairly-tested, (c) PnL engine never touched real data:

- **ROUTE C (more factor mining): LOW EV** — same null space, REUSE-MAP says don't.
- **ROUTE A (PA_SETUP_DIAGNOSTICS_V0): HIGHEST EV** — least-explored lane, code
  exists, matches the "any strategy shape" north star; the only blocker is a
  concrete, solvable data-shape gap (multi-class path slice).
- **ROUTE B (STRATEGY_REFERENCE_SMOKE on real data): HIGH EV, complementary** —
  closes a real never-done gap (de-risks the capital-truth engine), but has no
  reviewer-approved setup to test yet, so it is best sequenced *after* the setup
  lane produces a mechanism-justified candidate, OR run as a parallel engine-only
  de-risk on a pre-declared simple rule.

**Chosen mainline: ROUTE A — `PA_SETUP_DIAGNOSTICS_V0`.** First concrete unit:
diagnose the single-class `DATA_GAP` (why `target_before_stop` is one-class at the
tested horizons) and establish a slice/geometry that yields a genuine multi-class
path outcome — the precondition for any fair PA setup test. No mining until that
precondition is met and pre-registered.

**No HARD STOP triggered** (no paid data / universe / broker / live / capital /
non-regenerable delete / invariant weakening). Proceeding autonomously per mandate.
