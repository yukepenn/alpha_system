# RLPC-P00 Handoff

Campaign: `REFERENCE_LABEL_PARALLEL_COMPUTE_V1`
Phase: `RLPC-P00` - Campaign Bootstrap + FUTSUB Pause-State Record
Lane: GREEN

## Phase Summary

Confirmed the six-file campaign bundle is present, `campaign.yaml` parses, and
the phase list is the expected serial chain `RLPC-P00` through `RLPC-P04` with
P00 GREEN and P01-P04 YELLOW. Confirmed `ACTIVE_CAMPAIGN.md` points at
`REFERENCE_LABEL_PARALLEL_COMPUTE_V1` and did not edit it.

Created the value-free evidence skeleton under
`research/reference_label_parallel_compute_v1/`. Recorded the paused FUTSUB-P19
state in `FUTSUB_PAUSE_STATE.md` from read-only inspection of the adjacent
preserved FUTSUB run directory and local metadata paths. Updated the root
README snapshot for the current campaign and safety boundaries.

One bundle consistency fix was made: `README.md` was added to the RLPC-P00
`allowed_paths` in `campaign.yaml` because the generated phase spec requires a
root README snapshot update and lists `README.md` as commit-eligible.

No source, tool, test, registry, data, value, or `runs/` file was edited.

## Created / Modified Paths

Intended commit-eligible changed paths:

- `README.md`
- `campaigns/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/campaign.yaml`
- `research/reference_label_parallel_compute_v1/README.md`
- `research/reference_label_parallel_compute_v1/.gitkeep`
- `handoffs/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/FUTSUB_PAUSE_STATE.md`
- `handoffs/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/RLPC-P00.md`

No staging commands were run by the executor.

## Git / Artifact Evidence

`git status --short` was not run because the executor prompt explicitly
forbids `git status`. This is an instruction conflict with the generated spec
validation list; the safety override was followed and this exception is
recorded here.

Because no `git add`, `git commit`, `git push`, `git status`, or `git diff`
command was run, the executor did not create or inspect a staged set. The
executor performed no staging, so no `runs/` path was staged by the executor.

`git ls-files runs` was run and produced no output.

The prompt-named run artifact directory for this phase,
`runs/2026-06-11T015152Z_REFERENCE_LABEL_PARALLEL_COMPUTE_V1/phases/RLPC-P00`,
was not present in this worktree when checked read-only. No run-local handoff,
review, or verdict file was created.

## Validation Results

- `git status --short` - NOT RUN. Reason: explicit executor prompt override
  forbids `git status`.
- `test -f ACTIVE_CAMPAIGN.md` - PASS.
- `grep -q "REFERENCE_LABEL_PARALLEL_COMPUTE_V1" ACTIVE_CAMPAIGN.md` - PASS.
- `test -f campaigns/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/GOAL.md` - PASS.
- `test -f campaigns/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/campaign.yaml` - PASS.
- `test -f campaigns/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/PHASE_PLAN.md` - PASS.
- `test -f campaigns/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/ACCEPTANCE.md` - PASS.
- `test -f campaigns/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/RISK_REGISTER.md` -
  PASS.
- `test -f campaigns/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/RUNBOOK.md` - PASS.
- `test -f handoffs/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/FUTSUB_PAUSE_STATE.md`
  - PASS.
- `test -f research/reference_label_parallel_compute_v1/README.md` - PASS.
- `python -c "import yaml; yaml.safe_load(open('campaigns/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/campaign.yaml'))"`
  - PASS.
- Additional bundle consistency check over parsed YAML phase IDs, lanes, and
  dependencies - PASS (`phase_chain_ok`).
- `python tools/verify.py --smoke` - PASS.
- `git ls-files runs` - PASS; output was empty.

## FUTSUB Pause-State Notes

Read-only inspection confirmed:

- STOP file present for
  `2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`.
- STOP text records coordinator pause at `2026-06-11T01:45Z`, mid
  `FUTSUB-P19` materialization, to run this RLPC campaign, with
  `~134/216 full-window cells checkpointed`.
- `state.json` records `current_phase_id` as `FUTSUB-P19` and
  `current_stage` as `execute`.
- P19 worktree plan records the FUTSUB-P19 worktree path, and that directory
  exists.
- The production `cost_adjusted` checkpoint ledger path exists.
- The production labels registry path exists.
- The production `cost_adjusted` materialized-value manifest directory exists.

Observed discrepancy: the current checkpoint ledger does not independently
reproduce the STOP file's `~134/216` estimate. The ledger currently contains
665 total rows, including bounded-real, failed, full-window, registry-resume,
retry, and duplicate/superseded history. Parsed counts include
394 `full_window` / `completed` rows, 334 unique completed full-window unit IDs,
and 207 unique completed full-window partition IDs. This discrepancy is
recorded in `FUTSUB_PAUSE_STATE.md`; no ledger, registry, value, run, or
worktree state was modified.

## Scope Notes

`ACTIVE_CAMPAIGN.md` was verified only and left unmodified. No review artifacts,
`review.md`, `verdict.json`, PR, merge, PASS marking, broker operation, paper
trading, live trading, deployment, registry mutation, value write, or
destructive cleanup was performed.
