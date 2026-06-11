# FUTSUB Boundary State

Campaign: `DISCOVERY_RIGOR_FLOOR_V1`
Boundary source run:
`2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
Recorded by: `RIGOR-P00`

## Live Sources Read

- `/home/yuke_zhang/projects/alpha_system/runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/STOP`
- `/home/yuke_zhang/projects/alpha_system/runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/state.json`
- `/home/yuke_zhang/projects/alpha_system/runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/RUN_SUMMARY.md`
- `/home/yuke_zhang/projects/alpha_system/runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/progress.txt`
- `/home/yuke_zhang/projects/alpha_system/runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/events.jsonl`
- `/home/yuke_zhang/projects/alpha_system/runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/ACTIVE_CAMPAIGN.projected.md`

The prompt-relative path
`runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/` was not
present in this phase worktree. The readable live run directory was in the
coordinator repo at `/home/yuke_zhang/projects/alpha_system/runs/...`.

## Boundary State

The FUTSUB run is stopped at the P27/P28 boundary. `state.json` records:

- run status: `STOPPED`;
- `stop_requested`: `true`;
- total phases: `34`;
- pass-like completed phases: `28`;
- completed range: `FUTSUB-P00` through `FUTSUB-P27`;
- last completed phase: `FUTSUB-P27`, `PASS_WITH_WARNINGS`, PR `371`;
- blocked phase: `FUTSUB-P28`, status `BLOCKED`, current stage `spec`;
- pending phases: `FUTSUB-P29` through `FUTSUB-P33`.

`RUN_SUMMARY.md` agrees with the state file and reports `Passing phases: 28/34`
and `Pending phases: 5`.

The STOP file text, quoted verbatim, is:

```text
Workflow 2 provider-wired run stopped safely.
Reason: Wave 31 left 1 phase(s) not passing: FUTSUB-P28. Resume after the blocking conditions are resolved.
```

The STOP file does not itself contain the words "boundary gate" or
"before FUTSUB-P28". The live event/state sequence places the gate before
FUTSUB-P28 execution:

- `events.jsonl` records `WAVE_START` for `FUTSUB-P28` at
  `2026-06-11T21:51:48Z`;
- `events.jsonl` records `PHASE_STOPPED` for `FUTSUB-P28` at
  `2026-06-11T21:57:03Z` with reason `STOP file exists before execution.`;
- `events.jsonl` records `STOP_WRITTEN` at `2026-06-11T21:57:03Z` with reason
  `Wave 31 left 1 phase(s) not passing: FUTSUB-P28. Resume after the blocking conditions are resolved.`;
- `progress.txt` records that the coordinator was resuming for
  `P26 tail -> P27 -> boundary gate` before P28 was selected.

## Resume Ownership

FUTSUB resumes only after `DISCOVERY_RIGOR_FLOOR_V1` closes. Resume is
coordinator-owned and must follow the RIGOR-P07 handoff
`handoffs/DISCOVERY_RIGOR_FLOOR_V1/FUTSUB_KILL_SHOT_RESUME.md`, including
Track-B pre-registration before any Track-A metric, readiness verification,
surrogate/calibration requirements, and explicit clearing of the boundary STOP.

## Mutation Statement

This phase did not modify the FUTSUB run directory, registries, materialized
values, or worktrees. It only read the live run sources listed above and wrote
commit-eligible RIGOR-P00 documentation in the current phase worktree.
