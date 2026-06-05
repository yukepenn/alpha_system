# Workflow

## Workflow 1

Human-gated phase loop:

```text
strategy -> spec -> human approval -> Codex execution -> handoff -> Claude review -> human merge or repair
```

## Workflow 2

Provider-wired campaign loop:

```text
campaign -> phase selection -> Claude spec -> Codex execution -> validation -> Claude review -> Codex repair loop -> semantic done-check -> local commit -> push phase branch -> verify remote branch SHA -> PR -> CI wait -> merge gate -> lane auto-merge -> next phase -> campaign done-check -> RUN_SUMMARY
```

Boundary:

- Codex executes the generated spec and may write executor output and handoff notes.
- Codex must not call Claude, run review, create `review.md` or `verdict.json`, create a PR, merge,
  or mark a phase PASS.
- The Ralph driver owns validation, Claude review, verdict parsing, repair orchestration, semantic
  done-check, PR creation, CI, and merge gating.

Supported commands:

Omit `<campaign>` to use the `ACTIVE_CAMPAIGN.md` pointer.

```bash
just frontier-run [<campaign>]                  # start/continue (LIVE: real PR + auto-merge)
just frontier-resume [<campaign>]               # auto-resume the latest run of the active campaign
just frontier-next [<campaign>] [<phase_count>] # step forward N phases (default 1)
just frontier-run-parallel [<campaign>] [<n>]   # DAG-wave parallel build, serial merge
just frontier-plan [<campaign>]                 # read-only DAG wave plan
just frontier-run-mock [<campaign>]             # safe mock run
just frontier-next-mock [<campaign>] [<n>]
just frontier-run-parallel-mock [<campaign>] [<n>]
just frontier-ledger [<campaign>]               # ledger-only scaffold
just frontier-resume-run <run_id>               # resume a specific run directory
just frontier-resume-stage <campaign> <run_dir> <phase> [<from_stage>]
just frontier-tail <run_id>
just frontier-summary <run_id>
just frontier-stop <run_id>
just frontier-heartbeat <run_id>
just frontier-acceptance
```

## Scheduling modes (DAG wave)

`frontier.yaml` `workflow2.scheduler` (overridable per campaign) selects how Ralph
picks work:

- `mode: sequential` (default) — historical list-order, one phase at a time.
- `mode: dag_wave` — phases are chosen by their dependency-ready set; with
  `parallel_execution: true` and `max_parallel_phases > 1` (or `--parallel` /
  `frontier-run-parallel`), a conflict-free, parallel-safe wave **builds
  concurrently** in isolated worktrees and **merges serially** through a merge
  queue. Use `frontier-plan` to preview the waves first.

A phase joins a parallel wave only when it declares `parallel_safe: true` with
disjoint `allowed_paths`, is not `must_run_alone` or RED (unless RED scope is
armed), and does not declare a global file (e.g. `ACTIVE_CAMPAIGN.md`). In a
parallel wave the coordinator owns `ACTIVE_CAMPAIGN.md`; phase branches never
write it. Merge stays serial regardless of build concurrency.

## Modes

- Mock mode sets `FRONTIER_MOCK_PROVIDERS=1`; it writes deterministic artifacts and never calls Claude or Codex CLIs.
- Provider-wired local mode uses `claude -p` and `codex exec --sandbox workspace-write -` with full prompts on stdin.
- `frontier-next` resumes the latest active local run for the campaign and runs N phases (default 1). `frontier-run` and `frontier-resume` default to real PR creation, automerge enabled, merge dry-run disabled, and `FRONTIER_DISABLE_AUTOMERGE` unset. `frontier-resume` with no campaign resolves the active campaign from `ACTIVE_CAMPAIGN.md`.
- Worktree mode uses `FRONTIER_WORKTREE_MODE=1` or `--worktree-mode` to create `auto/<campaign>/<phase>-<slug>` branches in Frontier-owned worktrees.
- GitHub PR/CI mode uses `gh` for PR creation, CI polling, branch protection inspection, and merge.
- Real PR creation first pushes the phase branch with a non-force refspec, verifies the remote branch exists with `git ls-remote`, and checks the remote SHA matches the local commit.
- Real auto-merge is enabled only by `frontier.yaml` lane policy plus passing CI, verdicts, artifact policy, branch protection, and authenticated `gh`.

## Stop Conditions

- `STOP` file before a phase, provider call, done-check, PR, CI, or merge action.
- `BLOCKED` verdict or done-check.
- Repair attempts exhausted.
- Phase branch push failed (`PUSH_BLOCKED`).
- Remote branch missing or SHA mismatch (`REMOTE_BRANCH_BLOCKED`).
- PR creation failed after branch verification (`PR_CREATE_BLOCKED`).
- CI failure or timeout when CI is required.
- Branch protection missing or mismatched for real merge.
- Merge gate block.
- Run, phase, or estimated-cost budget stop.

`just frontier-stop <run_id>` writes `runs/<run_id>/STOP`. Resume with `just frontier-resume <run_id>` after removing or resolving the STOP condition.
