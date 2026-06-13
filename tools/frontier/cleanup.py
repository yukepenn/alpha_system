"""Shared Frontier cleanup entry point for driver and operator recipes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.frontier.provider_config import load_provider_config
from tools.frontier.runs_retention import RunsRetentionPolicy, apply_runs_retention
from tools.frontier.worktree_manager import WorktreeManager


def run_frontier_cleanup(
    *,
    repo_root: Path = ROOT,
    worktree_root: Path | None = None,
    active_run_dir: Path | None = None,
    dry_run: bool = True,
    include_runs: bool = True,
    policy: RunsRetentionPolicy | None = None,
) -> dict[str, Any]:
    """Run safe Frontier-owned cleanup tasks.

    Worktree cleanup is limited to Frontier-owned worktrees. Run retention only
    rotates completed local-only run directories and writes backups outside the
    git worktree under ``$ALPHA_SYSTEM_ROOT/.tmp``.
    """

    manager = WorktreeManager(repo_root, worktree_root)
    report: dict[str, Any] = {
        "schema_version": "frontier-cleanup-v1",
        "dry_run": dry_run,
        "repo_root": str(repo_root),
        "worktrees": {"stale": manager.clean_stale(dry_run=dry_run)},
    }
    if include_runs:
        report["runs_retention"] = apply_runs_retention(
            repo_root=repo_root,
            active_run_dir=active_run_dir,
            policy=policy,
            dry_run=dry_run,
        )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Clean Frontier-owned local runtime leftovers.")
    parser.add_argument("--apply", action="store_true", help="Apply cleanup; default is dry-run.")
    parser.add_argument("--active-run", type=Path, help="Run directory protected from retention.")
    parser.add_argument("--skip-runs", action="store_true", help="Only clean stale Frontier worktrees.")
    parser.add_argument("--keep-last", type=int)
    parser.add_argument("--max-age-days", type=int)
    parser.add_argument("--backup-keep-last", type=int)
    args = parser.parse_args(argv)
    runtime = load_provider_config(ROOT)
    base_policy = RunsRetentionPolicy.from_env()
    policy = RunsRetentionPolicy(
        keep_last=args.keep_last or base_policy.keep_last,
        max_age_days=args.max_age_days or base_policy.max_age_days,
        backup_keep_last=args.backup_keep_last or base_policy.backup_keep_last,
    )
    report = run_frontier_cleanup(
        worktree_root=runtime.worktree_root,
        active_run_dir=args.active_run,
        dry_run=not args.apply,
        include_runs=not args.skip_runs,
        policy=policy,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
