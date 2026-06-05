# Ralph Scripts

Run the built-in smoke campaign:

```bash
scripts/ralph/ralph.sh --campaign-id G005_WORKFLOW2_TOY
```

Consolidated just recipes (omit `<campaign>` to use the `ACTIVE_CAMPAIGN.md` pointer):

```bash
just frontier-run [<campaign>]            # start/continue a run (LIVE: real PR + auto-merge)
just frontier-resume [<campaign>]         # auto-resume the latest run of the active campaign
just frontier-next [<campaign>] [<n>]     # step a run forward by N phases (default 1)
just frontier-run-parallel [<campaign>] [<n>]  # DAG-wave parallel build, serial merge
just frontier-plan [<campaign>]           # read-only DAG wave plan (no run)

just frontier-run-mock [<campaign>]       # safe mock run (no providers/network/merge)
just frontier-next-mock [<campaign>] [<n>]
just frontier-run-parallel-mock [<campaign>] [<n>]
just frontier-run-workflow2-toy           # deterministic local toy campaign

just frontier-ledger [<campaign>]         # ledger-only scaffold (no execution)
just frontier-resume-run <run_id>         # resume a specific run directory
just frontier-resume-stage <campaign> <run_dir> <phase> [<from_stage>]  # surgical stage resume
just frontier-stop <run_id> / -tail / -summary / -heartbeat
```

`frontier-run` starts (or continues) campaign-loop mode. `frontier-next` (or
`FRONTIER_MAX_PHASES=1`) advances one phase for smoke/debug. `frontier-resume`
with no argument resolves the active campaign from `ACTIVE_CAMPAIGN.md` and
resumes its latest non-completed run.

## Scheduling modes

Workflow 2 selects phases two ways, set in `frontier.yaml` (and overridable per
campaign under `workflow2.scheduler`):

- `mode: sequential` (default) — the historical list-order, one-phase-at-a-time
  loop. Unchanged behaviour.
- `mode: dag_wave` — phases are chosen by their dependency-ready set. When
  `parallel_execution: true` and `max_parallel_phases > 1` (or the
  `--parallel` CLI flag / `frontier-run-parallel`), a conflict-free, parallel-safe
  wave **builds concurrently** in isolated Frontier worktrees and then **merges
  serially** through a merge queue.

A phase is only eligible for a parallel wave when it declares `parallel_safe: true`
with disjoint `allowed_paths`, is not `must_run_alone`, is not RED (unless RED
scope is armed), and does not touch global/coordinator files such as
`ACTIVE_CAMPAIGN.md`. In a parallel wave the **coordinator owns
`ACTIVE_CAMPAIGN.md`** — phase branches never write it, so they cannot conflict.
Merge stays serial even when builds run in parallel: `main` is updated one PR at
a time, each re-evaluated against the current base.

The local Ralph driver is provider-wired. Green/yellow auto-merge can run for
real when `frontier.yaml`, CI, verdicts, artifact policy, branch protection, and
`gh` auth all pass. Red lane requires `PROJECT_OP_AUTHORIZED=1`,
`PROJECT_OP_SCOPE`, `PROJECT_OP_EXPIRES`, and matching scope. The `*-mock`
recipes never touch providers, the network, or merge.
