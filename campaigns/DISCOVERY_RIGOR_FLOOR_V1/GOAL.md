# DISCOVERY_RIGOR_FLOOR_V1 — Goal

## Why (Compass test: removes THE blocker before the kill-shot)

Compass v4.3 Stage B: before CORE_PILOT_RERUN (FUTSUB-P28) produces any
metric, the discovery pipeline must be able to prove its verdicts are
trustworthy — otherwise a survivor could be a false discovery and a rejection
could be untrusted. The FUTSUB run is boundary-gated (STOP before P28) until
this campaign closes. Every later stage (survivor gate, Mining V2, the one
bounded-ML pipeline) inherits this floor; the surrogate-FDR calibration is
the ML pipeline's HARD precondition.

## REUSE MAP grounding (2026-06-11 inspection — enhance, don't rebuild)

EXISTS (smallest upgrade only): TrialLedger + RejectedIdeaLedger
(platform-cumulative; add fail-closed presence/writability gates), variant
counting (embedded in TrialLedgerAccounting; promote to first-class),
contamination FLAGS on trials (gate them), canary catalog/harness (3 of 4
executable; finish RANDOM_TARGET), promotion lifecycle states (add
reason_code). GENUINELY ABSENT (build): VerdictReasonCode enum,
VariantLedger w/ family budgets, SealedHoldoutWindow + HoldoutAccessLog,
PlantedFakeAlphaStudyCanary (end-to-end), SurrogateStudyRun (label-shuffled
full-pipeline FDR calibration), RequeuedVerdictRecord (evidence accrual).
EXPLICITLY DEFERRED by REUSE-MAP ruling: computed duplicate-exposure
registry (Mining V2 upgrade), fast lanes, FactorLibrary.

## What done means

A synthetic study driven through the full path hits every gate fail-closed
(entry budget hook → trial ledger → holdout access log → 4/4 negative
controls + planted-fake-alpha → reason_coded verdict → promotion gate), each
gate has a bypass canary that fails when neutered, surrogate calibration
measures the pipeline's false-pass floor with a declared zero-pass threshold,
the 6 Core Pilot INCONCLUSIVE verdicts carry additive reason_code annotations
(originals byte-identical), and the coordinator holds an executable
kill-shot resume handoff with a Track-B pre-registration template.

## What this campaign is NOT

Not the kill-shot itself (FUTSUB-P28 runs after), not alpha ideation, not a
rewrite of any historical evidence, not duplicate-exposure computation, not
ML, not paper/live/broker. No alpha/profitability/tradability claim.
