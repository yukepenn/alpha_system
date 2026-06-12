# Regime Surrogate Calibration Diagnosis

Date: 2026-06-12

Scope: value-free diagnosis of the regime-family real-data surrogate calibration
finding. No feature, label, return, diagnostic, cost, alpha-validity,
profitability, tradability, or production-readiness claim is made here.

## Finding

The real regime-family surrogate calibration reported 120 warning-free
surrogate runs and therefore 120 old-style "passes". This was not evidence of
label leakage. It exposed that the old pass criterion measured diagnostic
eligibility rather than signal detection.

## Root Cause

Before `P080820_SURROGATE_DETECTION_STATISTIC`, the surrogate runner set the
calibration pass field from warning cleanliness:

- `src/alpha_system/governance/surrogate_run.py` pre-fix `run_surrogate_study`
  lines 1206-1207: `passed = diagnostics_status == "PASS"`.
- `src/alpha_system/governance/surrogate_run.py` pre-fix `_diagnostics_status`
  lines 560-561: warnings absent meant `"PASS"`.

A sufficient substrate can produce warning-free diagnostics after dependence-
preserving label perturbation, so warning cleanliness is structural
eligibility. A null can satisfy it regardless of whether the diagnostic layer
contains a signal.

## Why This Is Not Leakage

The result did not show that label content survived the null perturbations. It
showed that the calibration was counting `eligibility_clean` as if it were a
signal pass. Conversely, a family that always emitted warnings could have met a
zero-pass threshold vacuously under the old criterion.

## Corrected Semantics

`P080820_SURROGATE_DETECTION_STATISTIC` aligns surrogate pass semantics with the
TRUE-alpha detection canary statistic:

- Shared statistic: diagnostic-layer `directional.pearson_ic` absolute value.
- Shared threshold: the declared TRUE-alpha detection threshold
  `detection_threshold_abs_pearson_ic = 0.95`.
- `statistic_passed` is true only when the shared statistic clears that
  threshold.
- `passed` equals `statistic_passed`.
- `eligibility_clean` records warning-free diagnostics as context only.
- If the statistic cannot be computed from persisted study outputs, the seed is
  `ERROR`; it is never treated as a silent non-pass.

The corrected report threshold follows `statistic_pass_count`; it also records
`eligibility_clean_count` for interpretation context.
