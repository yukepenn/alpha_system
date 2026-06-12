---
campaign_id: DISCOVERY_RIGOR_FLOOR_V1
phase_id: P014500_WF2_RESUME_COMPLETENESS
lane: yellow
status: in_progress
---

# P014500_WF2_RESUME_COMPLETENESS: verdict fidelity at repair-exhaustion + mid-pipeline resume

## Purpose

Two proven WF2 harness gaps forced coordinator intervention tonight
(RIGOR-P02, run 2026-06-11T223643Z):

1. **Synthetic verdict shadows the real one.** When the repair budget
   exhausts, the driver writes `verdict.json` with
   `{"verdict": "BLOCKED", "source": "repair_exhausted", "findings": [],
   "raw_review_path": null}` even when the final attempt's FRESH REVIEW
   (written to `review.md`, with an embedded `frontier-review-verdict-v1`
   JSON block) is PASS_WITH_WARNINGS with zero required repairs. The real
   verdict was discoverable; the driver discarded it. Evidence:
   runs/2026-06-11T223643Z_DISCOVERY_RIGOR_FLOOR_V1/phases/RIGOR-P02/
   verdict.json.synthetic_blocked.bak vs review.md.
2. **Mid-pipeline phases are unschedulable after a stop.** Targeted resume
   `--from-stage done_check` maps the phase to status REVIEWED
   (PROVIDER_RESUME_STATUS_BY_STAGE, ralph_driver.py:134-141) and then calls
   `continue_provider_wired_run`, but wave scheduling
   (`ready_wave_phases`/`dag_scheduler.compute_waves`) selects only PENDING
   phases. A REVIEWED/EXECUTED/VALIDATED/SPEC_READY phase is therefore
   invisible: it blocks its dependents and the run ends in
   SCHEDULE_DEADLOCK (events 167/171/175 in the run above). Deterministic
   stages (ci/branch_protection/merge_gate/merge) have a working resume
   path; provider stages do not.

## Scope (in-bounds)

1. **Verdict fidelity** in the repair-exhaustion path: before writing the
   synthetic BLOCKED verdict, parse the LAST attempt's review output (the
   same parser used by the normal VERDICT_PARSE stage; review.md +
   embedded JSON block). If it parses to a passing verdict
   (PASS/PASS_WITH_WARNINGS) with no required repairs, use IT as the
   phase verdict (source: "repair_exhausted_final_review") and let the
   phase proceed through the normal gate order instead of stopping. If it
   parses to REWORK/BLOCKED or does not parse, keep today's exact behavior
   (synthetic BLOCKED, stop). Never invent a verdict; fidelity only.
2. **Mid-pipeline schedulability**: when a targeted `--from-stage` resume
   maps a phase to a provider-stage status (SPEC_READY/EXECUTED/VALIDATED/
   REVIEWED/REWORK), the driver must CONTINUE that phase's pipeline from
   that stage directly (reusing the existing per-stage execution functions
   and recorded artifacts — checkpointed stages are not regenerated)
   before falling back to wave scheduling. Equivalently: the wave builder
   may treat a phase whose status is a mid-pipeline provider status as the
   current in-flight phase to finish, never as invisible. Choose the
   implementation that reuses the most existing machinery; do NOT
   restructure the scheduler.
3. Tests (driver mock-mode, pattern of tests/unit/frontier/):
   a. repair-exhaustion with a passing final review → phase proceeds (no
      synthetic BLOCKED), event trail records the fidelity source;
   b. repair-exhaustion with failing/unparseable final review → today's
      BLOCKED stop unchanged;
   c. targeted resume from done_check on a REVIEWED phase with completed
      prior-stage artifacts → phase reaches the commit stage (mock) and
      dependents become schedulable — no SCHEDULE_DEADLOCK;
   d. SCHEDULE_DEADLOCK still fires when a phase is genuinely
      dependency-starved (no mid-pipeline phase exists).

## Hard constraints

- Surgical edits to tools/frontier/ralph_driver.py (+ resume.py if
  needed); NO reformatting; no state-name changes; no gate weakening; STOP
  semantics untouched; the public WORKFLOW2_STAGES order unchanged.
- Never auto-approve: fidelity means using the REVIEWER's parsed verdict,
  not synthesizing one.
- No src/alpha_system/** changes. Explicit staging only; no runs/**.
- Research-only language.

## Validation

```bash
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/frontier -q
python tools/verify.py --smoke
python tools/hooks/canary_runner.py
python tools/frontier/status_doctor.py
```

Exact counts in the handoff; note any skipped check with reason.

## Done criteria

- A passing final repair review is never shadowed by a synthetic BLOCKED;
  mid-pipeline phases resume to completion without coordinator surgery;
  genuine deadlocks still stop; tests prove both behaviors and their
  negatives; full validation green; truthful handoff; fresh adversarial
  review PASS or PASS_WITH_WARNINGS under reviews/DISCOVERY_RIGOR_FLOOR_V1/.
