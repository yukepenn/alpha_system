# DIFFERENTIATED_KILLSHOT_V1 — Goal

## Mission

The first kill-shot (FUTSUB) rejected all six crowded single-factor price-action / BBO mechanisms
at near-zero IC — **0 survivors**. This kill-shot tests a **differentiated** thesis: that a set of
**zero-feed, exchange-calendar-deterministic** mechanisms — day-of-week, OPEX / quad-witch pinning,
month-end / quarter-end flow, roll-week flow, open/close auction proximity — may carry intraday
behavior the efficient price-action substrate did not. It runs them as **pooled (ES/NQ/RTY)
conditional studies on the EXISTING rigor path (Track A)**, plus at least one **context≠trigger
SetupSpec EXPLORATORY probe** over materialized path labels using the just-completed
strategy-shaped lane (**Track B**). The whole surface is pre-registered under an FDR active-subset
restatement **before any metric**, and every readout is surrogate-FDR zero-pass gated,
variant-ledgered, and N_eff/power-qualified.

## What this is (and is NOT)

- **IS:** a conclusive, evidence-gated verdict on differentiated zero-feed mechanisms, reusing the
  existing StudySpec → surrogate-FDR → factor-diagnostics path (Track A) and the SSRL
  SetupSpec/conditional_probe engine (Track B), all FDR-bounded and EXPLORATORY-quarantined.
- **IS NOT:** a strategy backtester, FactorLibrary/AlphaBook, a PA grammar pack, paper/live/broker,
  or new paid data. No new dependency. No second PnL truth.

## Honest framing (no over-promise)

This does **not** claim these mechanisms carry alpha. It makes the *whole differentiated-mechanism
class* testable under the same rigor that produced a trustworthy negative before. **Success is
CONCLUSIVE, not positive:** 0 clean survivors with no remaining substrate excuse is a *successful*
kill-shot. The macro-surprise cards (`fomc_drift`, `cpi_surprise_reversion`) are **DEFERRED**
(`needs_paid_data`) until a feed is onboarded; a zero-feed "scheduled-time" stub would be a
different, weaker mechanism and is out of scope.

## Hard invariants (the boundaries that keep this safe)

1. **FDR before metric** — the active-subset restatement (DK-P00) + the surrogate-FDR zero-pass
   gate (DK-P02) both precede any real-data metric (DK-P03+). The restatement is a value-free
   pre-registration note (NOT a `BudgetAmendmentRecord` — that object is strictly-increasing and
   cannot encode a downward re-scope).
2. **EXPLORATORY ≠ promotion evidence** — Track B output can never be promotion evidence; the
   trusted/promotion path refuses EXPLORATORY artifacts (enforced + canary).
3. **No research→reference-sim bridge** — `research/` imports zero `backtest/management/fast_path/
   value_store`; outcomes come only from materialized path labels, and values are loaded by
   `tools/`/`runtime/` and **injected** into the pure research probe. No second PnL truth.
4. **Additive only** — the single-factor path is byte-unchanged; the new calendar flags and the
   declared-conditioning-factor admission are strictly additive and preserve every gate
   (parity, no-lookahead, roll/maintenance fail-closed, surrogate zero-pass).
5. **Bounded** — pre-registered VariantLedger/family_budget; instrument-pooled; no grid, no horizon
   sweep, no per-instrument split without a (strictly-increasing) amendment.
6. **C1/C2/C3** — Track B context vs trigger are genuinely distinct *signals*; SSRL first-light is a
   `DATA_GAP` not real evidence; the de-stack is a restatement not fresh corroboration.

## Why now (not build-by-inertia)

SSRL completed (5/5) and its gates were adversarially verified (Track B = GO_WITH_CONDITIONS); the
no-second-PnL-truth rail was hardened (PR #439). The user issued an explicit **full A+B execution
mandate**. This is the Compass Stage D(a) differentiated-mechanism kill-shot on the single research
production line — not a reflexive factory build on a 0-survivor board.

## Definition of Campaign Done

All 5 pre-registered Track A mechanisms accounted for — the **4 gated** scored on real data
(opex, month_end, day_of_week, open_close; post FDR-restatement + surrogate zero-pass) with a
`primary_state + reason_code`, and **roll_week carried as `INCONCLUSIVE`/`DATA_GAP`** (degenerate/all-null
`in_roll_window_flag`, excluded from real-metric inspection per DK-P02); one context≠trigger Track B EXPLORATORY probe run over path labels
(real evidence or honest `DATA_GAP`), never promoted; a campaign verdict aggregates them under the
survivor gate (0 survivors documented as conclusive, or any survivor surfaced with a reviewer
verdict — never auto-promoted); all invariants hold; `RUN_SUMMARY` written; research-only language
throughout.
