# DIFFERENTIATED_KILLSHOT_V1 — Pre-Registration Brief

Status: **VALUE-FREE pre-registration. Not a campaign contract yet.** This brief
is the binding design record the eventual `DIFFERENTIATED_KILLSHOT_V1` campaign
bundle must satisfy. It contains no IC/return values and makes no
alpha/tradability/profitability claim. It supersedes nothing in the prep cards;
it constrains how they may be used.

It exists because the FUTSUB first kill-shot produced **0 clean survivors**
(Compass Stage C fired; Stage D 0-survivor branch is live). Per Stage D(a), the
next move is a **narrow, differentiated** kill-shot from mechanisms already in
scope (§7 of the Compass) — NOT broad mining, NOT FactorLibrary buildout.

---

## 0. Two binding refinements (the reason this brief exists)

These are HARD gates. A campaign bundle that does not encode both is
non-conformant and must not run.

### Refinement 1 — Track B is hard-gated on SSRL-P02/P03 success

`DIFFERENTIATED_KILLSHOT_V1` has two tracks (§3). **Track B (SetupSpec /
strategy-shaped probes) DOES NOT RUN** unless `STRATEGY_SHAPED_RESEARCH_LANE_V0`
has first PROVEN, on merged evidence:

1. a `SetupSpec` with **context ≠ trigger** compiles and runs an **EXPLORATORY**
   probe whose outcome comes from a **materialized path label**
   (SSRL-P02 acceptance), AND
2. the trusted/promotion path **refuses** an EXPLORATORY-stamped artifact
   (the quarantine canary is green), AND
3. `research/` imports **zero** `backtest`/`management`/`fast_path`
   (no-second-PnL-truth assertion holds in CI), AND
4. SSRL-P03 has run at least one context≠trigger idea end-to-end on a real
   slice, variant-ledgered + surrogate-FDR + power-qualified, EXPLORATORY,
   with no promotion.

If any of these is not MET at campaign-authoring time, **Track B is dropped**
(not deferred-inside-the-run, not stubbed — absent) and the kill-shot runs
Track A only. The gate is checked against `status_doctor` + merged-PR truth,
not against intent. Rationale: Track B's expressibility (separate trigger,
path-outcome target/stop/hold) is exactly the capability SSRL builds; running
it before SSRL proves the quarantine boundary would either (a) duplicate the
SSRL engine work, or (b) leak EXPLORATORY output toward promotion — the precise
failure SSRL's `ACCEPTANCE.md` is built to prevent.

Track A (zero-feed calendar mechanisms, §3) is **independent of SSRL** and may
run regardless — even in parallel with the SSRL tail — because it uses the
existing single-factor / conditional-flag path, not the SetupSpec engine.

### Gate verification result — Track B = GO_WITH_CONDITIONS (verified 2026-06-13, merged HEAD `0c841c3`)

`STRATEGY_SHAPED_RESEARCH_LANE_V0` completed (5/5 merged). Refinement-1's four
sub-conditions were adversarially re-verified against **merged main** (not
handoff prose) by a verify→refute→adjudicate pass: both hard gates PASS and are
mutation-tested load-bearing (neutering the probe distinctness check or the
EXPLORATORY stamp-scan makes the negative tests fail), nothing exploratory is
treated as promotion evidence (first-light is an honest `DATA_GAP`,
`promotion_eligible:false`), `research/` imports zero reference engines, and all
71 targeted tests + 28 canaries are green. **Track B is eligible.**

One precondition was found and **closed before this rail**: the no-second-PnL-truth
guard (`test_research_package_has_no_sim_bridge_imports`) used a line regex that
silently missed dotted submodules (`import alpha_system.backtest.fast_path`) and
every `value_store` form. Replaced with an AST import check (PR #439, merged
`0c841c3`); no offending import existed, the gap was latent.

Non-blocking authoring constraints the verification surfaced — these **bind the
campaign bundle** (value-free):

- **C1 — declared-distinctness, not signal-distinctness.** The context≠trigger
  gate enforces *declared* distinctness (`factor_id` + alias/duplicate/derived
  markers), not numeric signal-identity. Two distinct `factor_id`s wrapping the
  same upstream signal compile cleanly. Track B SetupSpecs MUST use genuinely
  distinct context vs trigger signals; the probe will not catch an
  aliased-same-signal collapse. Authoring + review responsibility, not a runtime
  guarantee.
- **C2 — first-light is NOT a real-data result.** SSRL-P03's first-light
  ES_2024 readout is an honest `DATA_GAP` (`n_eff:0`, no Parquet reader in the
  executor); the only end-to-end conditional proof is on a synthetic fixture. No
  phase, spec, or report may cite `first_light/EVIDENCE.json` as a real ES_2024
  conditional result. A Track B real-slice run begins from zero real-data
  evidence.
- **C3 — de-stack is a re-statement, not fresh corroboration.** The de-stack
  `ic=0.068 / n=6862` are carried SHIP_REFIT settler constants (self-labeled);
  only the MDE bound is freshly computed and `promotion_evidence:false`. Do not
  treat `de_stack/EVIDENCE.json` as new evidence for the +0.068 read.

### Refinement 2 — FDR budget must be AMENDED before any metric

The committed `FDR_BUDGET.md` pre-registered `family_budget = 6` for a 4-card
family that **counts two `needs_paid_data` cards** (`fomc_drift`,
`cpi_surprise_reversion`). Under the standing no-new-Databento / no-macro-feed
constraint, those two cards' *differentiating* conditioner (surprise = actual
vs consensus) is unavailable. **The kill-shot may not silently reuse a budget
sized for data we are not running.**

Before any real-data metric is inspected, a **`BudgetAmendmentRecord`**
(`governance/variant_ledger.py::create_budget_amendment_record`) must define
the ACTIVE ZERO-FEED SUBSET (§2). The amendment is the only sanctioned way to
re-scope; it is pre-declared, provenance-carrying, and must predate the
earliest recorded variant attempt (`_find_covering_amendment`). A budget that
counted deferred paid-data cards is not "reused down" informally — it is
restated by an amendment whose rationale names the exclusion.

---

## 1. What carries over (no rebuild — REUSE-MAP rule)

All accounting reuses existing objects (per `FDR_BUDGET.md` §"Machinery
reused"): `StudySpec.variant_budget`/`family_budget`, `VariantLedger`,
`evaluate_family_budget`, `BudgetAmendmentRecord`, `run_surrogate_study` /
`calibrate_surrogate_fdr` (zero-pass `ZERO_PASS_MET` / `LEAKAGE_BLOCKED`),
`pooled_hypothesis.py`. The kill-shot builds NO new ledger or FDR mechanism.
Per-study MDE/power memos use `research/power.py` (SHIP_REFIT-P03 hardened).
Outcomes for any path-shaped probe come ONLY from materialized path labels —
never from a research→reference-sim bridge.

---

## 2. The active zero-feed subset (what Refinement-2's amendment must declare)

Classification is taken from each card's `data_dependency.class` field
(value-free, already committed under `cards/`):

### ACTIVE — zero-feed, exchange-calendar-deterministic (eligible this round)

| Card | New FeatureRequest needed | Notes |
|---|---|---|
| `day_of_week_effect` | **none** (uses existing `session_calendar_roll_day_of_week`) | cheapest first-light; truly zero new feature work |
| `opex_pinning` | `is_opex_day_flag`, `is_quad_witch_day_flag` (calendar-derived) | strike/OI data explicitly OUT (paid) |
| `month_end_flow` | `is_month_end_session_flag`, `is_quarter_end_session_flag` (calendar-derived) | shares its flag with `month_end_rebalance_flow` (pick ONE — anti-duplication) |
| `roll_week_flow` | `in_roll_window_flag` (REUSE `labels/roll_guard.py` classification) | known-ahead definition only, never the offline countdown features |
| `open_close_auction_flow` | **none** (existing RTH-open/close clocks) | literal auction-imbalance feed is paid → OUT |

All new FeatureRequests extend `SESSION_CALENDAR_ROLL` with known-ahead
(`metadata.available_ts <= row.available_ts`) provenance. No external feed.

### DEFERRED — `needs_paid_data` (NOT in this round's budget)

| Card | Why deferred |
|---|---|
| `fomc_drift` | scheduled-time clock is free, but the card's differentiating conditioner (FOMC surprise magnitude / dot-plot delta) is `needs_paid_data`; a zero-feed "scheduled-time drift" stub is a *different, weaker* mechanism — if wanted, it is a NEW card + amendment, not this card run cheap |
| `cpi_surprise_reversion` | core conditioner (CPI actual−consensus surprise) is `needs_paid_data`; the zero-feed remainder is only release-*timing*, not surprise reversion |

Paid-feed onboarding (FRED or a macro calendar) remains behind the documented
onboarding SOP + `FRED_API_KEY` secret discipline; until then both stay OUT.

### The amendment (value-free spec the campaign must instantiate)

```text
BudgetAmendmentRecord:
  family_id:        family-differentiated-substrate-v1-event-calendar
  action:           RESTATE active subset to zero-feed mechanisms only
  excluded (paid):  fomc_drift, cpi_surprise_reversion   (needs_paid_data)
  active mechanisms: day_of_week_effect, opex_pinning, month_end_flow,
                     roll_week_flow, open_close_auction_flow
                     (month_end_rebalance_flow folded into month_end_flow)
  per-mechanism variant_budget: = that mechanism's horizon count (below)
  family_budget:    re-derived from the ACTIVE subset's effective hypothesis
                    count — NOT the inherited 6 (which counted fomc+cpi horizons)
  horizons:         per-card, pre-registered (§ below), from the
                    materialized band {5m,15m,30m,60m,120m,240m} + path labels;
                    each card pins its own small set, no horizon sweep
  sessions:         RTH primary; ETH research-in-scope, flagged separately;
                    hard maintenance/trade-date boundary preserved (intraday)
  instruments:      POOLED across ES/NQ/RTY as ONE Track-B-style pooled test
                    per mechanism (per-instrument split needs a further amendment)
  provenance:       predates earliest variant attempt; rationale = this brief
  surrogate-FDR:    zero-pass (ZERO_PASS_MET), declared K, dependence-preserving
                    (session/trade-date-block) nulls — gates evidence, not optional
```

Horizons stay inside the **already-materialized band**, which extends to
**240m (4h)** plus path labels (MFE/MAE/target-before-stop/triple-barrier) —
consistent with the user directive that edge is sought up to 4h, not imprisoned
at ≤30m. Arbitrary fixed-minute horizons outside the enum remain a code change
and are out of scope; arbitrary path-horizon is config-only and in scope.

---

## 3. Track structure

### Track A — zero-feed differentiated mechanisms (ALWAYS eligible)

The active subset above, each as a conditional-flag study on the existing
single-factor / conditional path. Pre-declared variant budget = horizon count
per card; pooled across the index trio. Output is `primary_state + reason_code`
only (REJECT / INCONCLUSIVE[+code] / WATCH / CANDIDATE_RESEARCH). No promotion.

### Track B — SetupSpec / strategy-shaped probes (GATED, see Refinement 1)

ONLY if SSRL-P02/P03 are proven. At least one context≠trigger SetupSpec
(e.g. range-contraction context + prior-high-sweep-then-reclaim trigger;
target = path-label target-before-stop; hold ≤ 120m), run as an EXPLORATORY,
variant-ledgered, surrogate-FDR + power-qualified probe on a real slice.
EXPLORATORY output can NEVER become promotion evidence; a trusted rerun via
the SSRL-P04 handoff scaffold is required for any promotion. No sim-bridge.

Both tracks: success = **conclusive, not positive.** Zero clean survivors with
no remaining substrate excuse is a successful kill-shot.

---

## 4. Where this sits in the pipeline (no new taxonomy artifact)

The single research production line is the Compass §1 layer model; this brief is
the **Stage D(a) differentiated-mechanism kill-shot** on it. Layer naming is held
exactly as Compass §1 / §10 and `docs/SYSTEM_MAP.md`:

- **PA_GRAMMAR_SUBSTRATE** (the SetupSpec/MechanismCard expression catalog SSRL
  introduces) is the *grammar/expression* layer — **separate from**
- **FactorLibrary**, which is reserved for **evidence-backed survivor memory**
  only (Compass Stage G; triggered by ≥1 WATCH/CANDIDATE survivor, never by
  rejected-idea memory alone).

A mechanism card or SetupSpec is NOT a FactorLibrary entry. It becomes one only
after surviving the verdict gate. Do not conflate the two.

---

## 5. Hard invariants (carried from the Compass + SSRL ACCEPTANCE)

- Surrogate-FDR zero-pass gates all evidence; nulls dependence-preserving.
- No-lookahead / `available_ts` discipline; roll/maintenance fail-closed.
- EXPLORATORY ≠ promotion evidence; trusted path refuses EXPLORATORY artifacts.
- No second PnL truth: `research/` does not import `backtest`/`management`/`fast_path`.
- No new dependency; no new paid data; explicit staging; `git ls-files runs` empty.
- Research-only language throughout: diagnostics and gates decide, not priors.
