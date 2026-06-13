# Cleanup And Provenance Hardening

`SHIP_REFIT-P04` adds non-gating Workflow 2 cleanup and provenance hardening.
It does not change diagnostics, detection, surrogate, value, or registry code.

## Post-Merge Cleanup

The driver post-merge path keeps branch cleanup driver-owned:

- Worktree mode uses `WorktreeManager.cleanup_after_merge` for the merged phase
  worktree and its guarded `auto/` branch cleanup.
- In-tree mode keeps remote `auto/` branch deletion inside
  `cleanup_phase_worktree_after_merge` and deletes the local `auto/` branch only
  when it is not the checked-out branch.
- Both modes record a `post_merge_cleanup.json` local audit artifact and run the
  shared cleanup path for stale Frontier worktrees plus `runs/` retention.

The on-demand operator command is:

```bash
just frontier-clean
```

The dry-run variant is:

```bash
just frontier-clean-dry-run
```

## Runs Retention

`tools/frontier/runs_retention.py` rotates only completed run directories with a
readable `state.json`. The active run, any non-completed run, and any run with
an unresolved `STOP` marker are protected. Completed runs with the terminal
completed `STOP` marker may be rotated because that marker is not an unresolved
halt.

Eligible completed runs are moved to persistent backup storage under
`$ALPHA_SYSTEM_ROOT/.tmp/runs_backups/`. Defaults keep the newest 25 completed
runs, rotate completed runs older than 30 days, and keep the newest 10 backup
batches. These can be adjusted with `FRONTIER_RUNS_RETENTION_KEEP_LAST`,
`FRONTIER_RUNS_RETENTION_MAX_AGE_DAYS`, and
`FRONTIER_RUNS_BACKUP_KEEP_LAST`.

## Provenance And Temp Paths

Done-check artifacts stay local-audit-owned as `done_check.md` and
`done_check.json`. A done-check warning can still promote the phase status to
`PASS_WITH_WARNINGS`, but it no longer rewrites reviewer-owned `verdict.json`.
Reviewer artifacts remain reviewer-owned.

Frontier temp scratch now resolves to `$ALPHA_SYSTEM_ROOT/.tmp`, outside the git
worktree. The canary runner passes that location through `TMPDIR`/`TEMP`/`TMP`
so nested stdlib temporary directories use the same persistent root.
