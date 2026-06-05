# Operations

## Bootstrap A New Project

From the template repository:

```bash
python tools/bootstrap_frontier.py --target <repo> --profile <profile> --project-name <name> --force
```

In the generated repository:

```bash
git init
git config core.hooksPath .githooks
python -m compileall tools tests
python -m pytest
just frontier-doctor
just verify-canaries
FRONTIER_MOCK_PROVIDERS=1 FRONTIER_MAX_PHASES=1 just frontier-run-mock G005_WORKFLOW2_TOY
python tools/verify.py --artifacts
just frontier-acceptance
```

## Upgrade An Existing Project

From the template repository:

```bash
python tools/upgrade_frontier.py --target <repo> --profile <profile> --project-name <name> --dry-run
python tools/upgrade_frontier.py --target <repo> --profile <profile> --project-name <name> --dry-run --plan-json upgrade-plan.json --report-md upgrade-report.md
python tools/upgrade_frontier.py --target <repo> --profile <profile> --project-name <name> --apply
```

The upgrade tool preserves project files by default, including campaigns, `ACTIVE_CAMPAIGN.md`, `PROJECT_STATUS.md`, `PROGRESS.md`, and `frontier.yaml`. Use `--force-project-files` only after reviewing conflicts.

## Overnight Run

```bash
just frontier-overnight <campaign>
just frontier-heartbeat <run_id>
just frontier-tail <run_id>
just frontier-summary <run_id>
```

In the morning, inspect `runs/<run_id>/RUN_SUMMARY.md`, `events.jsonl`, `heartbeat.json`, every phase `verdict.json`, `done_check.json`, `ci_status.json`, and `merge_gate.json`.

## Scheduling Modes (Sequential vs DAG Wave)

`frontier.yaml` `workflow2.scheduler` (overridable per campaign under
`workflow2.scheduler`) selects how Ralph chooses work:

- `mode: sequential` (default): historical list-order, one phase at a time.
- `mode: dag_wave`: phases are selected by their dependency-ready set. Preview a
  campaign's waves with `just frontier-plan <campaign>` (read-only; no run, no
  provider/git calls).

```bash
just frontier-plan <campaign>            # dependency graph, ready waves, conflicts
just frontier-run-parallel <campaign> 3  # build a conflict-free wave concurrently
```

`frontier-run-parallel` (or `--parallel` / `parallel_execution: true` with
`max_parallel_phases > 1`) builds a parallel-safe, conflict-free wave concurrently
in isolated Frontier worktrees, then **merges serially through a merge queue** —
`main` advances one PR at a time, each re-checked against the current base. Only
phases that declare `parallel_safe: true` with disjoint `allowed_paths` (and are
not `must_run_alone`/RED, and touch no global file like `ACTIVE_CAMPAIGN.md`)
share a wave; everything else runs alone. In a parallel wave the coordinator owns
`ACTIVE_CAMPAIGN.md`, so phase branches never race on it; the projected pointer is
written to `runs/<run_id>/ACTIVE_CAMPAIGN.projected.md` and the tracked pointer is
refreshed by the next sequential phase / closeout. A `dag_wave` run that finds no
dependency-ready phase while phases remain pending stops with `SCHEDULE_DEADLOCK`.

## Crash Recovery

```bash
just frontier-resume [<campaign>]   # auto-resume the active campaign's latest run
just frontier-next <campaign> <n>   # resume N phases
just frontier-resume-run <run_id>   # resume a specific run directory
```

Resume reuses durable phase artifacts. A run interrupted after spec generation resumes from `SPEC_READY`; after execution it resumes from validation/review; after review it resumes from done-check and downstream gates. Runs stopped at `PUSH_BLOCKED`, `REMOTE_BRANCH_BLOCKED`, `PR_CREATE_BLOCKED`, `CI_BLOCKED`, or `MERGE_GATE_BLOCKED` retry from the failed GitHub gate without rerunning Claude spec generation, Codex execution, or creating a new commit when `commit_sha.txt` is present.

`frontier-resume` with no campaign id reads `ACTIVE_CAMPAIGN.md` and resumes the
latest non-completed run for that campaign. `frontier-resume`/`frontier-next`
resolve the latest non-completed local run; they do not start a new run, so use
`frontier-run` for a fresh campaign run. These commands default to real PR
creation, automerge enabled, merge dry-run disabled, and `FRONTIER_DISABLE_AUTOMERGE`
unset.

## Auth For Real Operations

```bash
gh auth status
claude -p "ping"
printf 'ping\n' | codex exec --sandbox workspace-write -
```

Real PR creation follows `frontier.yaml` (`git.auto_create_pr` and `workflow2.auto_pr`) and can be forced off with `FRONTIER_CREATE_PR=0`. Before `gh pr create`, Workflow 2 pushes the exact phase branch with a non-force `git push -u origin HEAD:refs/heads/<branch>` command, verifies the branch exists remotely, and verifies remote/local commit SHAs match. Push/auth failures stop as `PUSH_BLOCKED`; missing branches or SHA mismatches stop as `REMOTE_BRANCH_BLOCKED`; `gh pr create` failures stop as `PR_CREATE_BLOCKED`.

PR bodies are written to `runs/<run_id>/phases/<phase_id>/pr_body.md` and passed to `gh pr create` with `--body-file`. The gate also writes `push_branch.json`, `push_branch.md`, `remote_branch.json`, `pr_create.json`, and `pr_create.md`.

Real auto-merge for green/yellow requires lane `auto_merge: true`, CI success, passing verdicts, artifact policy success, branch protection validation, and authenticated `gh`. Red lane additionally requires `FRONTIER_RED_AUTHORIZED=1` and matching scope.

Emergency kill:

```bash
FRONTIER_DISABLE_AUTOMERGE=1
FRONTIER_MERGE_DRY_RUN=1
```

No live trading, paper trading, broker operation, production deployment, or destructive cleanup is provided by this generic harness.
