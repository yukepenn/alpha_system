# G005 Phase Plan

The toy campaign has exactly three deterministic phases.

1. `P01_CREATE_TOY_DOC_A`
   - Create `docs/toy_workflow2/phase_a.md`.
   - Write run phase artifacts: `spec.md`, `handoff.md`, `review.md`, and `verdict.json`.

2. `P02_CREATE_TOY_DOC_B`
   - Create `docs/toy_workflow2/phase_b.md`.
   - Write run phase artifacts: `spec.md`, `handoff.md`, `review.md`, and `verdict.json`.

3. `P03_CREATE_TOY_SUMMARY`
   - Create `docs/toy_workflow2/summary.md`.
   - Write run phase artifacts: `spec.md`, `handoff.md`, `review.md`, and `verdict.json`.

The driver must check for `STOP` before starting each next phase and stop safely when it exists.
