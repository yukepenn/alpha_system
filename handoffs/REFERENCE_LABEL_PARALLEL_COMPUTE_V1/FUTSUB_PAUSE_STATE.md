# FUTSUB Pause-State Record

Campaign: `REFERENCE_LABEL_PARALLEL_COMPUTE_V1`
Paused campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
Paused run id: `2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
Paused phase: `FUTSUB-P19`

## Summary

The FUTSUB run is deliberately stopped while `FUTSUB-P19` is mid
full-window `cost_adjusted` materialization. RLPC phases must treat the FUTSUB
run directory, the P19 worktree, label registry rows, checkpoints, and
materialized values as preserved local-only data. This campaign must not resume,
repair, clean, delete, stage, or rewrite them before RLPC-P04 and the
coordinator-owned resume.

## Read-Only Sources Inspected

- `runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/STOP`
- `runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/state.json`
- `runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/progress.txt`
- `runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/events.jsonl`
- `runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/phases/FUTSUB-P19/worktree_plan.json`
- Local checkpoint metadata under
  `$ALPHA_DATA_ROOT/materialization/futures_substrate_scaleout_v1/checkpoints/labels/cost_adjusted/`
- Local materialized-value manifest paths under
  `$ALPHA_DATA_ROOT/labels/materialized/futures_substrate_scaleout_v1/cost_adjusted/`
- Local registry path existence at `$ALPHA_DATA_ROOT/registry/labels.sqlite`
- P19 worktree directory existence at the path recorded in `worktree_plan.json`

No file under `runs/` was modified. No registry SQLite file or Parquet value
file was opened or written.

## STOP File

The STOP file is present. It records this rationale:

> STOP requested by coordinator 2026-06-11T01:45Z: pausing FUTSUB-P19 mid-materialization (checkpoint-safe) to run REFERENCE_LABEL_PARALLEL_COMPUTE_V1 (unit-parallel reference label compute per STRUCTURAL_BACKLOG §6). P19 resumes on workers=8 after that campaign merges. ~134/216 full-window cells checkpointed.

This is the coordinator-recorded pause statement for the run.

## Run State

`state.json` records:

- `campaign_id`: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- `current_phase_id`: `FUTSUB-P19`
- `current_stage`: `execute`
- `attempts.FUTSUB-P19`: `2`
- `broker_or_trading_operations_performed`: `false`
- `deployment_performed`: `false`

`progress.txt` records `FUTSUB-P19` as selected in wave 18 on
2026-06-10T19:44:01Z after coordinator reintegration surgery. The same file
also records that P19 resumed on the reference engine from existing completed
checkpoint units after the LCFP campaign.

`events.jsonl` records the current P19 worktree plan and resume events for the
branch `auto/alpha_futures_research_substrate_scaleout_v1/futsub-p19-cost-adjusted-labelpack-scaleout`.

## Checkpoint And Value Metadata Observed

The STOP file says approximately 134 of 216 full-window `cost_adjusted` cells
were checkpointed at the coordinator pause time. Read-only inspection of the
current checkpoint ledger does not independently reproduce that exact estimate:

- `completed_units.jsonl` currently has 665 total ledger rows.
- Ledger rows by `stage` / `status`:
  - `bounded_real` / `completed`: 48
  - `bounded_real` / `failed`: 54
  - `full_window` / `completed`: 394
  - `full_window` / `failed`: 161
  - `registry_resume` / `completed`: 8
- `full_window` / `completed` currently contains 334 unique unit IDs and 207
  unique partition IDs.
- Production `cost_adjusted` materialized-value manifest paths currently count
  574 `values.parquet.manifest.json` files under the inspected materialized
  values directory.

These raw ledger counts are not a clean replacement for the STOP file's
`~134/216` pause estimate because the ledger includes bounded-real entries,
failed entries, retries/resume history, and duplicate or superseded unit rows.
The discrepancy is recorded here rather than normalized.

## Preservation Boundary

Do not touch the following before RLPC-P04 and the coordinator-owned FUTSUB
resume:

- The paused FUTSUB run directory, including `STOP`, `state.json`,
  `progress.txt`, `events.jsonl`, phase artifacts, and any run-local handoff,
  review, verdict, or repair files.
- The P19 worktree recorded by `worktree_plan.json`.
- The `cost_adjusted` checkpoint ledger and per-unit checkpoint metadata.
- The production labels registry and any registry backup or journal files.
- Materialized label values and value manifests.
- Any raw/canonical data, provider responses, caches, logs, or local databases.

RLPC-P04 may amend FUTSUB contract files and write the coordinator resume
handoff. The actual STOP removal, state reset, and FUTSUB resume are
coordinator-owned after this campaign completes.
