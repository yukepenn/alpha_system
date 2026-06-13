# FDR / Multiple-Testing Budget — DIFFERENTIATED_SUBSTRATE_V1

Status: VALUE-FREE pre-registration. This note fixes, BEFORE any data work, how
many mechanisms x variants x horizons x instruments will be tested so that
authoring mechanism cards does not become a hidden multiple-testing surface. It
contains no IC/return values and makes no alpha/tradability/profitability claim.

## Why this exists (the near-duplicate lesson)

The FUTSUB first kill-shot's "6 studies" were really ~4 distinct mechanisms
(regime, liquidity_pa x2, bbo_tradability, vwap_session x2 — two pairs were
near-duplicate variants). Counting studies instead of distinct mechanisms
understated the effective number of hypotheses and inflated the multiple-testing
surface. This budget counts at the VARIANT and FAMILY level using the existing
ledger machinery, not at the loose "study" level, so the same pathology cannot
recur silently.

## Machinery reused (no new mechanism built — REUSE-MAP rule)

All accounting uses objects that already exist; this campaign builds NO new
ledger or FDR mechanism:

- `StudySpec.variant_budget` (required int) and `StudySpec.family_budget`
  (optional int) — `src/alpha_system/governance/study_spec.py`.
- `VariantLedger`, `VariantLedgerRecord`, `evaluate_family_budget(...)`,
  `FamilyBudgetCheck`, `validate_variant_and_family_budget(...)` —
  `src/alpha_system/governance/variant_ledger.py`. Family rollup keys on
  `(study_spec_id, variant_id)` (`_family_exposure_key`), so two near-duplicate
  variants count as two, not one.
- `BudgetAmendmentRecord` + `create_budget_amendment_record(...)` — the ONLY
  sanctioned way to raise a budget: pre-declared, provenance-carrying, strictly
  increasing, and (per `_find_covering_amendment`) must predate the earliest
  recorded variant attempt. No silent budget growth.
- Surrogate-FDR calibration: `run_surrogate_study(...)`,
  `calibrate_surrogate_fdr(...)`, `SurrogateCalibrationReport`,
  zero-pass threshold (`ZERO_PASS_MET` / `LEAKAGE_BLOCKED`), false-pass bound
  "zero passes in K bounds false-pass rate at about 3/K at 95%"
  (`SURROGATE_FALSE_PASS_BOUND_STATEMENT`) —
  `src/alpha_system/governance/surrogate_run.py`. Surrogate trials carry
  `surrogate_flag=true` and are excluded from production variant/family counts.
- Pooled-hypothesis accounting: `src/alpha_system/governance/pooled_hypothesis.py`
  (supports the Compass Track-B pooled minimum).

## Pre-registered family and budget structure

- `family_id`: `family-differentiated-substrate-v1-event-calendar`.
  (Aligns with the existing `family-<scope>` convention, e.g.
  `family-rigor-p05-surrogate-fdr`.) All event-calendar variants below share this
  one family so the `family_budget` caps the WHOLE event-calendar effort, not each
  study independently.

### Counted dimensions (the budget arithmetic)

| Dimension | Pre-registered set | Count |
|---|---|---|
| Mechanisms (cards) | fomc_drift, cpi_surprise_reversion, opex_pinning, month_end_flow | 4 |
| Variants per mechanism | 1 primary conditioning specification each (NO near-duplicate sibling variants this round — the explicit fix for the 6=4 pathology) | 1 |
| Horizons | per card: fomc_drift {5m,30m}, cpi_surprise_reversion {5m,30m}, opex_pinning {30m}, month_end_flow {30m} | 2,2,1,1 |
| Instruments | POOLED across index futures (ES/NQ/RTY family) as ONE pooled test per Track-B, NOT one test per instrument | pooled = 1 |

Effective distinct hypotheses (variant x horizon, instrument-pooled):

- fomc_drift: 1 variant x 2 horizons = 2
- cpi_surprise_reversion: 1 variant x 2 horizons = 2
- opex_pinning: 1 variant x 1 horizon = 1
- month_end_flow: 1 variant x 1 horizon = 1

Family-level effective hypothesis count = 2 + 2 + 1 + 1 = **6 pooled tests**.

### Budgets to set on the StudySpecs

- Per-mechanism `variant_budget`: pre-register equal to that mechanism's
  horizon count (2, 2, 1, 1). A second sibling variant of any mechanism may NOT
  be added without a `BudgetAmendmentRecord`.
- Family-wide `family_budget`: **6** (the family-level effective hypothesis
  count above). Authoring a fifth mechanism card, or splitting any pooled test
  into per-instrument tests, would breach the family budget and require a
  pre-declared, strictly-increasing `BudgetAmendmentRecord` with rationale — it
  cannot happen silently.

### Instrument pooling is mandatory, not optional

Per the Compass Track-B pooled minimum and the low per-event occurrence counts
(roughly 8 FOMC, 12 CPI, 12 OPEX + 4 quad-witch, 12 month-end + 4 quarter-end
windows per year), each mechanism is N_eff-limited. The pre-registered design
pools across the index-futures family as a SINGLE test rather than multiplying
the surface by instrument. Converting any mechanism to per-instrument tests
multiplies the hypothesis count and requires a family-budget amendment.

## Surrogate-FDR calibration requirement (pre-registered)

Before any real-data event-calendar study is treated as evidence, the shared
detection statistic must be calibrated on label-shuffled / trade-date-block
surrogates over these StudySpecs using `calibrate_surrogate_fdr(...)`, with the
declared threshold that ZERO shuffled runs may clear the statistic
(`ZERO_PASS_MET`). Any shuffled pass is `LEAKAGE_BLOCKED` and must be diagnosed
before proceeding. With a K-seed budget the false-pass rate is bounded at about
`3/K` at 95% confidence; the seed budget K will be pre-registered on the
StudySpec/runbook (mirroring the existing RIGOR-P05 surrogate calibration), not
chosen after seeing results.

## Hard budget rules

1. The family budget (6) is a hard cap; growth only via a pre-declared,
   strictly-increasing `BudgetAmendmentRecord` that predates the earliest variant
   attempt.
2. No near-duplicate sibling variants this round (the explicit 6=4 fix).
3. Instrument pooling is the default; per-instrument expansion needs an amendment.
4. Authoring additional mechanism cards consumes pre-registered budget; a 5th card
   requires an amendment before it is counted as a study.
5. Surrogate-FDR zero-pass calibration gates evidence; it is not optional.
6. Everything here is value-free pre-registration; diagnostics and gates decide
   promotion, never these priors.
