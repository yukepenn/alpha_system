# FDR / Multiple-Testing Budget — Priority-2 & Priority-3 Appendix (DIFFERENTIATED_SUBSTRATE_V1)

Status: VALUE-FREE pre-registration APPENDIX. This file EXTENDS `FDR_BUDGET.md`
(it does NOT rewrite it) to cover the priority-2 FLOW/CALENDAR SEASONALITY
mechanisms and the priority-3 GOVERNED OVERNIGHT family. It contains no
IC/return/Sharpe values and makes no alpha/tradability/profitability claim.
Diagnostics and gates decide promotion, never these priors.

The original `FDR_BUDGET.md` pre-registered the priority-1 EVENT-CALENDAR family
(family-level effective hypothesis count = **6 pooled tests**, family_id
`family-differentiated-substrate-v1-event-calendar`). That budget is unchanged by
this appendix. This appendix adds two NEW families and applies the same
already-existing machinery (REUSE-MAP rule).

## Machinery reused (no new mechanism built)

Identical to `FDR_BUDGET.md`: `StudySpec.variant_budget` / `family_budget`;
`VariantLedger` / `evaluate_family_budget` / `validate_variant_and_family_budget`
(family rollup keys on `(study_spec_id, variant_id)` via `_family_exposure_key`,
so near-duplicate variants count separately); `BudgetAmendmentRecord` /
`create_budget_amendment_record` (the only sanctioned, pre-declared,
strictly-increasing budget growth path, must predate the earliest recorded
variant attempt); surrogate-FDR calibration (`run_surrogate_study`,
`calibrate_surrogate_fdr`, `SurrogateCalibrationReport`, `ZERO_PASS_MET` /
`LEAKAGE_BLOCKED`, `SURROGATE_FALSE_PASS_BOUND_STATEMENT` "zero passes in K bounds
false-pass rate at about 3/K at 95%", surrogate trials carry `surrogate_flag` and
are excluded from production counts); `pooled_hypothesis.py` for the Track-B
pooled minimum. No new ledger, no new FDR object.

## The de-duplication rule restated (the 6=4 lesson)

The FUTSUB kill-shot's "6 studies" were really ~4 mechanisms (two near-duplicate
pairs), which understated the hypothesis count. This appendix counts at the
VARIANT/FAMILY level and applies one extra de-duplication constraint specific to
this round:

> The priority-2 card `month_end_rebalance_flow` and the priority-1
> event-calendar card `month_end_flow` condition on the SAME known-ahead
> month-end-session calendar flag (the latter adds a close-proximity
> interaction). They are NOT counted as two independent hypotheses. They are
> pre-registered as ONE pooled month-end hypothesis and SHARE one
> `FeatureRequest` implementation for the month-end flag. The priority-1 budget
> already counted the month-end pooled test (1) inside its family of 6; this
> appendix does NOT re-count it. `month_end_rebalance_flow` is the
> close-proximity SPECIFICATION of that one pooled hypothesis, not a fifth
> event-calendar card and not a new seasonality hypothesis.

## Family 2 — Flow / Calendar Seasonality

`family_id`: `family-differentiated-substrate-v1-flow-seasonality`.

### Counted dimensions

| Dimension | Pre-registered set | Count |
|---|---|---|
| Mechanisms (cards) | day_of_week_effect, roll_week_flow, open_close_auction_flow (month_end_rebalance_flow is the close-proximity spec of the priority-1 month-end pooled test — NOT counted here; see de-dup rule) | 3 counted |
| Variants per mechanism | 1 primary conditioning specification each (NO near-duplicate sibling variants this round) | 1 |
| Horizons | day_of_week_effect {30m}; roll_week_flow {30m}; open_close_auction_flow {5m,30m} | 1,1,2 |
| Instruments | POOLED across the index-futures family (ES/NQ/RTY and related) as ONE pooled test per Track-B, NOT one test per instrument | pooled = 1 |

Effective distinct hypotheses (variant x horizon, instrument-pooled):

- day_of_week_effect: 1 variant x 1 horizon = 1
- roll_week_flow: 1 variant x 1 horizon = 1
- open_close_auction_flow: 1 variant x 2 horizons = 2

Flow/seasonality family-level effective hypothesis count = 1 + 1 + 2 = **4
pooled tests**.

### Budgets to set on the StudySpecs (Family 2)

- Per-mechanism `variant_budget`: pre-register equal to that mechanism's horizon
  count (1, 1, 2). A second sibling variant of any mechanism requires a
  `BudgetAmendmentRecord`.
- Family-wide `family_budget`: **4**. Authoring a fourth NEW seasonality
  mechanism, splitting open_close_auction_flow's open and close windows into two
  hypotheses, or splitting any pooled test into per-instrument tests would breach
  the family budget and requires a pre-declared, strictly-increasing
  `BudgetAmendmentRecord`.

## Family 3 — Governed Overnight

`family_id`: `family-differentiated-substrate-v1-overnight`.

No overnight mechanism cards are authored yet (see
`overnight/OVERNIGHT_FAMILY_DESIGN_NOTE.md`); this pre-registers the budget the
family will be held to so the two overnight windows cannot become a hidden
multiple-testing surface later.

### Counted dimensions

| Dimension | Pre-registered set | Count |
|---|---|---|
| Label windows (the distinct outcome definitions) | close_to_open, close_to_close | 2 |
| Variants per window | 1 baseline conditioning specification each (no near-duplicate siblings) | 1 |
| Horizons | the window IS the horizon (next-open / next-close); not separately multiplied | 1 each |
| Instruments | POOLED across the index-futures family per Track-B | pooled = 1 |

Overnight family-level effective hypothesis count = 1 (close_to_open) + 1
(close_to_close) = **2 pooled tests**.

### Budgets to set on the StudySpecs (Family 3)

- Per-window `variant_budget`: **1** each. A reversion/continuation sibling, an
  ETH-leg-only variant, or a macro-overnight conditioning split requires a
  `BudgetAmendmentRecord`.
- Family-wide `family_budget`: **2**. Any third overnight outcome window or any
  per-instrument expansion requires a pre-declared, strictly-increasing
  `BudgetAmendmentRecord`.
- Overnight studies are RED-lane at paper/live (gap-risk approval gate); the FDR
  budget here governs the OFFLINE research hypotheses only. The Red gate is an
  additional, independent gate, not a substitute for the FDR budget.

## Headline numbers (extended budget rollup)

| Family | family_id | Effective pooled tests |
|---|---|---|
| Event-calendar (priority 1, unchanged, in `FDR_BUDGET.md`) | family-differentiated-substrate-v1-event-calendar | 6 |
| Flow / calendar seasonality (priority 2, this appendix) | family-differentiated-substrate-v1-flow-seasonality | 4 |
| Governed overnight (priority 3, this appendix) | family-differentiated-substrate-v1-overnight | 2 |
| **Differentiated-substrate total (all priorities)** | (three pre-registered families) | **12** |

The new pre-registered surface added by THIS appendix is **6 pooled tests** (4
seasonality + 2 overnight). The campaign-wide pre-registered surface is **12
pooled tests** across **3 families**. `month_end_rebalance_flow` adds ZERO to the
count (it is the close-proximity spec of the already-counted priority-1 month-end
pooled test).

## Hard budget rules (this appendix)

1. Each family budget (4 for seasonality, 2 for overnight) is a hard cap; growth
   only via a pre-declared, strictly-increasing `BudgetAmendmentRecord` that
   predates the earliest variant attempt. No silent growth.
2. No near-duplicate sibling variants this round (the explicit 6=4 fix), and the
   month-end de-duplication rule above is binding: do not double-count the
   month-end hypothesis across families.
3. Instrument pooling is the default for every family; per-instrument expansion
   needs an amendment.
4. Surrogate-FDR zero-pass calibration gates evidence for all three families; it
   is not optional and is not replaced by the overnight Red gate.
5. Overnight paper/live use is additionally Red-gated (gap-risk approval); the
   FDR budget governs offline hypotheses only.
6. No paid-data dependency is assumed: any paid overnight microstructure / macro
   feed is `deferred_pending_user_approval`. The BBO namespace is untouched.
7. Everything here is value-free pre-registration; diagnostics and gates decide
   promotion, never these priors.
