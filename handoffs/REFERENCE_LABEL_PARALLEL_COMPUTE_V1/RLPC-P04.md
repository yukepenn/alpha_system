# RLPC-P04 Handoff

Campaign: `REFERENCE_LABEL_PARALLEL_COMPUTE_V1`  
Phase: `RLPC-P04` - FUTSUB Amendment + Resume Handoff + Backlog Closeout  
Lane: YELLOW

## Summary

Executed the `NOT_RELEASED` branch. The committed benchmark summary at
`research/reference_label_parallel_compute_v1/benchmark/benchmark_summary.md`
records `Release decision: NOT_RELEASED`: requested workers=8 measured 2.14x
on the 9-unit bounded real `cost_adjusted` ES/2024 grid, below the 3.0x release
gate. The same summary records the serial registration ceiling diagnosis,
determinism PASS at every worker count, and production registry row delta 0.

FUTSUB operative policy was left unchanged. `FUTSUB-P19` remains on
`--engine reference` with default workers=1. The parallel reference path remains
an explicit opt-in but is not adopted as FUTSUB or production policy.

## Scope Executed

- Updated `docs/STRUCTURAL_BACKLOG.md` section 6 to close option 1 as
  delivered engineering / `NOT_RELEASED` policy, and to leave option 2 as the
  standing backlog escalation with the measured registration-ceiling timings.
- Wrote
  `handoffs/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/FUTSUB_RESUME_ON_PARALLEL_REFERENCE.md`
  with coordinator-owned FUTSUB-P19 resume steps on the unchanged serial
  reference policy.
- Updated `README.md` with the RLPC 5/5 closeout snapshot, the NOT_RELEASED
  outcome, and the FUTSUB resume handoff.
- Added a concise project-skill lesson for the validated NOT_RELEASED closeout
  and registration-ceiling finding.

## FUTSUB Annotation Decision

Skipped the optional FUTSUB campaign annotation. The spec allowed a provenance
annotation but required zero operative policy drift; the existing FUTSUB
campaign files contain many engine-policy bullets, and the NOT_RELEASED branch
is most safely represented by leaving those contract files byte-untouched and
recording the decision in the backlog, README snapshot, and resume handoff.

## Files For Ralph To Stage

The executor staged no files and ran no staging commands. Ralph should stage
only these commit-eligible paths:

- `docs/STRUCTURAL_BACKLOG.md`
- `handoffs/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/FUTSUB_RESUME_ON_PARALLEL_REFERENCE.md`
- `handoffs/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/RLPC-P04.md`
- `.claude/skills/project-skill/lessons.md`
- `README.md`

Do not stage anything under `runs/`, `$ALPHA_DATA_ROOT`, `src/`, `tests/`, data
directories, registry paths, logs, caches, or heavy artifact paths.

## Validation Results

- `git status --short` - NOT RUN because the executor prompt explicitly forbids
  `git status`.
- `python -c "import yaml; yaml.safe_load(open('campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/campaign.yaml'))"` -
  PASS, exit code 0, no output.
- `test -f handoffs/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/FUTSUB_RESUME_ON_PARALLEL_REFERENCE.md` -
  PASS, exit code 0, no output.
- `grep -q "NOT_RELEASED" research/reference_label_parallel_compute_v1/benchmark/benchmark_summary.md` -
  PASS, exit code 0, no output.
- `grep -q "NOT_RELEASED" handoffs/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/FUTSUB_RESUME_ON_PARALLEL_REFERENCE.md` -
  PASS, exit code 0, no output.
- `git diff --name-only -- src/ tests/` - NOT RUN because the executor prompt
  explicitly forbids `git diff`.
- `git diff --name-only -- src/alpha_system/labels/engine.py src/alpha_system/labels/families src/alpha_system/labels/roll_guard.py src/alpha_system/labels/version.py` -
  NOT RUN because the executor prompt explicitly forbids `git diff`.
- `python tools/verify.py --smoke` - PASS, exit code 0, no output.
- `python tools/hooks/canary_runner.py` - PASS, exit code 0. Output ended with
  `All Frontier canaries passed.`
- `git ls-files runs` - PASS, exit code 0, output empty.

Additional note: the local path
`runs/2026-06-11T015152Z_REFERENCE_LABEL_PARALLEL_COMPUTE_V1/phases/RLPC-P04/spec.md`
was absent, so the generated spec in the executor prompt was treated as the
phase contract.

## Preservation And Boundaries

The paused FUTSUB run directory, registry, label values, checkpoints, and P19
worktree were not modified. This phase did not resume FUTSUB, edit
`ACTIVE_CAMPAIGN.md`, remove STOP, clear `RUN.lock`, create a PR, merge, call
Claude, run a reviewer, create `review.md`, create `verdict.json`, mark the
phase PASS, perform broker/paper/live/order operations, or deploy anything.

No `src/**` or `tests/**` changes were made intentionally, and no reference
oracle file was edited.
