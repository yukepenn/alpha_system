# FUTSUB Pause State

Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`

Run id: `2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`

Recorded by: `LABEL_COMPUTE_FAST_PATH_V1` / `LCFP-P00`

## Summary

FUTSUB is paused at `FUTSUB-P19` while
`LABEL_COMPUTE_FAST_PATH_V1` builds a reference-parity-gated fast label
producer path. This handoff records the pause state only. It does not delete,
edit, clean up, resume, repair, or mutate FUTSUB run state, worktrees, label
values, checkpoint files, or registry rows.

Reintegration and resume are coordinator actions after LCFP-P09. Phase branches
must not clear the FUTSUB STOP file, edit FUTSUB `state.json`, remove leftover
worktrees, delete existing label values, or rewrite registry rows.

## Locally Verified Facts

- Run directory visible:
  `test -d /home/yuke_zhang/projects/alpha_system/runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
  returned success.
- STOP file present:
  `test -f /home/yuke_zhang/projects/alpha_system/runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/STOP`
  returned success.
- `state.json` present and stale-running:
  `python -c "json.load(...)"` reported
  `status=RUNNING`, `current_phase_id=FUTSUB-P19`, `phase_count=34`,
  and `updated_at=2026-06-10T00:38:26Z`.
- Completed phase count is 19 of 34:
  the same `state.json` read reported phase status counts
  `PASS:1`, `PASS_WITH_WARNINGS:18`, `PENDING:14`, `SPEC_READY:1`.
- `FUTSUB-P19` is the current paused phase:
  the same `state.json` read reported `FUTSUB-P19` with status `SPEC_READY`
  and branch
  `auto/alpha_futures_research_substrate_scaleout_v1/futsub-p19-cost-adjusted-labelpack-scaleout`.
- P19 local cost-adjusted value artifacts are present and durable at the
  aggregate level:
  `find /home/yuke_zhang/alpha_data/alpha_system ... '*cost*adjust*'`
  found `labels/materialized/futures_substrate_scaleout_v1/cost_adjusted/`
  and
  `materialization/futures_substrate_scaleout_v1/checkpoints/labels/cost_adjusted/`.
- P19 local cost-adjusted materialized directory has paired aggregate outputs:
  a read-only file count reported `181` Parquet files and `181` JSON metadata
  files under
  `ALPHA_DATA_ROOT/labels/materialized/futures_substrate_scaleout_v1/cost_adjusted/`.
  No Parquet payloads or per-row label values were opened or copied.
- P19 local checkpoint directory is present:
  a read-only file count reported `181` unit checkpoint JSON files plus
  `completed_units.jsonl` under
  `ALPHA_DATA_ROOT/materialization/futures_substrate_scaleout_v1/checkpoints/labels/cost_adjusted/`.
- P19 value-free coverage summaries are present in the preserved P19 worktree:
  `find /home/yuke_zhang/projects/alpha_system-alpha_futures_research_substrate_scaleout_v1-futsub-p19/research/futures_substrate_scaleout_v1/label_packs/cost_adjusted`
  found `coverage_summary.md`, `coverage_counts.json`, and
  `aggregate_counts.md`.
- The local label registry file exists:
  `test -f "$ALPHA_DATA_ROOT/registry/labels.sqlite"` returned success.
  This was a presence check only; no registry rows or label values were dumped.
- `git worktree list` reported the following worktrees, which were preserved
  and not removed:

```text
/home/yuke_zhang/projects/alpha_system                                                          [main]
/home/yuke_zhang/projects/alpha_system-alpha_futures_research_substrate_scaleout_v1-futsub-p14  [auto/alpha_futures_research_substrate_scaleout_v1/futsub-p14-featurepack-registry-integration-coverage-audit-and-resolver-smoke]
/home/yuke_zhang/projects/alpha_system-alpha_futures_research_substrate_scaleout_v1-futsub-p19  [auto/alpha_futures_research_substrate_scaleout_v1/futsub-p19-cost-adjusted-labelpack-scaleout]
/home/yuke_zhang/projects/alpha_system-label_compute_fast_path_v1-lcfp-p00                      [auto/label_compute_fast_path_v1/lcfp-p00-campaign-bootstrap-futsub-pause-handoff]
```

The two preserved FUTSUB worktrees are:

- `/home/yuke_zhang/projects/alpha_system-alpha_futures_research_substrate_scaleout_v1-futsub-p14`
- `/home/yuke_zhang/projects/alpha_system-alpha_futures_research_substrate_scaleout_v1-futsub-p19`

## Contract-Stated Facts Not Fully Locally Verified

- The campaign contract states that P19 cost-adjusted labels are approximately
  60% materialized. Local checks verified durable partial cost-adjusted outputs
  and checkpoint files, but did not verify an authoritative planned denominator
  for the percentage without deeper value/registry inspection.
- The campaign contract states that nothing was lost. Local checks verified
  presence of run state, STOP, cost-adjusted output/checkpoint directories, and
  the label registry file. This phase did not perform a before/after content
  comparison of every value file or registry row.

## Preservation Rules

- Do not delete or edit the FUTSUB run directory, `STOP`, `state.json`,
  checkpoint ledgers, materialized label values, registry files, registry rows,
  or leftover worktrees from an LCFP phase branch.
- Do not copy per-row label values, Parquet payloads, SQLite rows, or provider
  payloads into git.
- Do not rerun or resume FUTSUB from this phase. Resume belongs to the
  coordinator after LCFP-P09 writes the reintegration handoff.
- Existing label values and registry rows are preserved as-is unless a later
  coordinator action supersedes them through the official preserve-don't-delete,
  superseded-and-verified process.
