# Review: P121500_FUTSUB_P19_GUARD_COUNT_SURFACE (WF1)

- Reviewer: fresh adversarial Claude agent, 2026-06-11
- Verdict: **PASS_WITH_WARNINGS**

## Deterministic evidence
- READ-ONLY proven to the sqlite open mode (mode=ro URI; fails closed on
  missing registry; only write is the committed value-free .md).
- Truth-source fidelity: drives the real evaluate_roll_guard + the reference
  family's own private helpers in the reference branch order; provenance ids
  are imported constants.
- Counts reconcile EXACTLY against P19's committed coverage_summary: scanned
  134,264,936 = 2x(kept+missing_terminal); gap arithmetic closes with zero
  residual; implied drops 2,020,922 == claimed total.
- 46,721 cross-family equality independently RE-COMPUTED from the BBO
  substrate (grid-determined: dense 1m timelines near breaks/rolls) —
  corroboration, not copy-through.
- Determinism: reviewer re-ran the ES/2024 slice; byte-identical counts.
- Mutation hardness: flipped maintenance-crossing → 5/5 tests FAIL; weakened
  span boundary → 4/5 FAIL. Both restored.
- 3 files only; no src/** edits; smoke + canaries green.

## Warnings
- W1: latent safe-default divergence in the span short-circuit (vacuous with
  analytic calendars; add empty-calendar pin test later).
- W2: duplicate-BBO-key ordering nuance (empirically zero rows; counts
  unaffected).
- W4: private-API coupling (required for fidelity; oracle test catches drift).
