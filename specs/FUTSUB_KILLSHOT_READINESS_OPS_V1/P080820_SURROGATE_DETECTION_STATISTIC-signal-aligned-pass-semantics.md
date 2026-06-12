---
campaign_id: FUTSUB_KILLSHOT_READINESS_OPS_V1
phase_id: P080820_SURROGATE_DETECTION_STATISTIC
lane: yellow
status: in_progress
---

# P080820_SURROGATE_DETECTION_STATISTIC: surrogate pass = detection statistic, not eligibility

## Purpose

LIVE CALIBRATION FINDING (2026-06-12, regime family real-data run):
`run_surrogate_study` defines `passed = diagnostics produced zero warnings`
(`surrogate_run.py:1206-1207` `_diagnostics_status`, `:560-561`). On the real
regime pack, all 120 label-shuffled runs ran warning-free → 120/120 "passes"
→ `LEAKAGE_BLOCKED`. Diagnosis: NOT label leakage — the pass criterion
measures ELIGIBILITY (clean diagnostics), which sufficient substrate satisfies
regardless of label content. A criterion that nulls can satisfy structurally
cannot calibrate false-pass control; conversely families that always emit
warnings would hit zero-pass VACUOUSLY. Compass v4.4 §7.2's intent is signal:
the same diagnostic-layer statistic whose detection power the TRUE-alpha
canary (P040500) proves — `detection_threshold_abs_pearson_ic` in
`src/alpha_system/governance/canaries/true_alpha_detection.py` — must NOT be
cleared by dependence-preserving nulls. This phase aligns the two legs.

## Scope (in-bounds)

1. **Signal-aligned pass semantics** (surrogate_run.py — COMPOSE with the
   detection canary's statistic evaluation; reuse its IC computation/threshold
   code path, never fork a second IC truth): a surrogate run's
   `gate_outcome` gains `statistic_passed` = the run's diagnostic-layer
   |Pearson IC| (computed from the surrogate study outputs exactly as the
   detection canary evaluates its fixtures) clears the SAME declared
   detection threshold. `passed` (the field the calibration report counts)
   becomes `statistic_passed`; the old zero-warnings boolean is RETAINED as
   `eligibility_clean` (recorded, reported, but not the pass criterion).
   If the statistic cannot be computed from a run's outputs, that run is
   `ERROR` (fail-closed), never a silent non-pass.
2. **Report**: per-config counts for BOTH `statistic_pass_count` (drives
   `threshold_verdict`) and `eligibility_clean_count` (context); the bound
   statement unchanged; report stays value-free (counts/ids only).
3. **Re-scoring mode** for `tools/discovery_rigor_floor/run_real_surrogate_calibration.py`:
   `--rescore-existing` re-evaluates persisted per-seed outputs
   (`<namespace>/seed_*/study_outputs/diagnostic_summary.json` + whatever the
   statistic needs) WITHOUT re-running studies; refuses (fail-closed, per-seed
   ERROR) when required outputs are absent. Fresh-run mode unchanged.
4. **Diagnosis record**: value-free note
   `research/discovery_rigor_floor_v1/surrogate_fdr/REGIME_LEAKAGE_BLOCKED_DIAGNOSIS.md`
   recording the finding, root cause (eligibility-vacuity, file:line), why it
   is NOT leakage, and the corrected semantics (cite this spec + the
   detection canary threshold as the aligned statistic).
5. **Tests**: (a) a synthetic seed-output fixture where the statistic clears
   the threshold → `statistic_passed=True` even with clean diagnostics, and
   one below threshold → False with `eligibility_clean=True` (proves the two
   fields are independent); (b) report counts both fields and verdict follows
   statistic only; (c) re-scoring on a fixture namespace reproduces fresh-run
   results and refuses missing outputs; (d) regression: the P05 synthetic
   calibration path still works (its fixtures' semantics updated honestly —
   if its synthetic runs cannot compute the statistic they must become ERROR
   and its test fixture upgraded, not special-cased).

## Hard constraints

- ONE IC truth: reuse the detection canary's statistic evaluation; any
  refactor extracts a SHARED helper both consume (move, don't duplicate).
- No changes to perturbation writers, namespaces, gate-stack semantics
  outside the surrogate pass field, or detection canary thresholds.
- No src/alpha_system/{features,labels,runtime}/** edits; values stay in
  isolated namespaces; explicit staging; research-only language.

## Validation

```bash
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/governance -q
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/discovery_rigor_floor -q
python tools/hooks/canary_runner.py
python tools/verify.py --smoke
just ci-parity
```

## Done criteria

Surrogate pass = detection statistic (one shared IC truth with the canary);
eligibility retained as context; re-scoring mode works on persisted outputs;
regime diagnosis note committed; tests prove field independence + verdict
follows statistic; validation green incl. ci-parity; truthful handoff under
handoffs/FUTSUB_KILLSHOT_READINESS_OPS_V1/; fresh adversarial review
PASS/PASS_WITH_WARNINGS under reviews/FUTSUB_KILLSHOT_READINESS_OPS_V1/.
