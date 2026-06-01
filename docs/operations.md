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
FRONTIER_MOCK_PROVIDERS=1 FRONTIER_MAX_PHASES=1 just frontier-run-campaign G005_WORKFLOW2_TOY
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
just frontier-run-overnight <campaign>
just frontier-heartbeat <run_id>
just frontier-tail <run_id>
just frontier-summary <run_id>
```

In the morning, inspect `runs/<run_id>/RUN_SUMMARY.md`, `events.jsonl`, `heartbeat.json`, every phase `verdict.json`, `done_check.json`, `ci_status.json`, and `merge_gate.json`.

## Crash Recovery

```bash
just frontier-resume <run_id>
```

Resume reuses durable phase artifacts. A run interrupted after spec generation resumes from `SPEC_READY`; after execution it resumes from validation/review; after review it resumes from done-check and downstream gates. Runs stopped at `PUSH_BLOCKED`, `REMOTE_BRANCH_BLOCKED`, `PR_CREATE_BLOCKED`, `CI_BLOCKED`, or `MERGE_GATE_BLOCKED` retry from the failed GitHub gate without rerunning Claude spec generation, Codex execution, or creating a new commit when `commit_sha.txt` is present.

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
