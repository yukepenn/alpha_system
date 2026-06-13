"""Local-only retention for Frontier Workflow 2 run directories."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.frontier.runtime_paths import persistent_tmp_root

DEFAULT_KEEP_LAST = 25
DEFAULT_MAX_AGE_DAYS = 30
DEFAULT_BACKUP_KEEP_LAST = 10
COMPLETED_STATUS = "COMPLETED"


@dataclass(frozen=True)
class RunsRetentionPolicy:
    keep_last: int = DEFAULT_KEEP_LAST
    max_age_days: int = DEFAULT_MAX_AGE_DAYS
    backup_keep_last: int = DEFAULT_BACKUP_KEEP_LAST

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "RunsRetentionPolicy":
        source = os.environ if env is None else env
        return cls(
            keep_last=_positive_int(source.get("FRONTIER_RUNS_RETENTION_KEEP_LAST"), DEFAULT_KEEP_LAST),
            max_age_days=_positive_int(source.get("FRONTIER_RUNS_RETENTION_MAX_AGE_DAYS"), DEFAULT_MAX_AGE_DAYS),
            backup_keep_last=_positive_int(source.get("FRONTIER_RUNS_BACKUP_KEEP_LAST"), DEFAULT_BACKUP_KEEP_LAST),
        )


def _positive_int(raw: str | None, default: int) -> int:
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError as error:
        raise ValueError(f"Retention value must be an integer, got {raw!r}.") from error
    if value < 1:
        raise ValueError("Retention values must be at least 1.")
    return value


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _run_mtime(run_dir: Path) -> float:
    state = run_dir / "state.json"
    try:
        return state.stat().st_mtime
    except OSError:
        try:
            return run_dir.stat().st_mtime
        except OSError:
            return 0.0


def _age_days(mtime: float, *, now: datetime) -> float:
    return max(0.0, (now.timestamp() - mtime) / 86_400)


def _safe_backup_name(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "_.-" else "-" for ch in name).strip(".-") or "run"


def _backup_batches(backup_root: Path) -> list[Path]:
    if not backup_root.exists():
        return []
    return sorted((path for path in backup_root.iterdir() if path.is_dir()), key=lambda p: p.name, reverse=True)


def plan_runs_retention(
    *,
    repo_root: Path = ROOT,
    active_run_dir: Path | None = None,
    policy: RunsRetentionPolicy | None = None,
    now: datetime | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Plan which completed, non-active runs should be rotated to backup.

    Only run directories with a readable ``state.json`` are considered. Active
    runs, any run with an unresolved STOP marker, and non-completed runs are
    protected. Completed runs are eligible when they exceed either the count
    budget (older than ``keep_last`` completed runs) or the age budget.
    """

    policy = policy or RunsRetentionPolicy.from_env(env)
    now = now or datetime.now(UTC)
    runs_root = repo_root / "runs"
    backup_root = persistent_tmp_root(repo_root=repo_root, env=env, create=False) / "runs_backups"
    active = active_run_dir.resolve(strict=False) if active_run_dir else None
    records: list[dict[str, Any]] = []
    protected: list[dict[str, Any]] = []
    rotated: list[dict[str, Any]] = []

    if runs_root.exists():
        for run_dir in sorted(path for path in runs_root.iterdir() if path.is_dir()):
            state_path = run_dir / "state.json"
            state = _read_json(state_path)
            if not state:
                protected.append({"run_id": run_dir.name, "path": str(run_dir), "reason": "missing_state_json"})
                continue
            status = str(state.get("status") or "")
            stop_exists = (run_dir / "STOP").exists()
            unresolved_stop = stop_exists and status != COMPLETED_STATUS
            if active is not None and run_dir.resolve(strict=False) == active:
                protected.append({"run_id": run_dir.name, "path": str(run_dir), "reason": "active_run"})
                continue
            if unresolved_stop:
                protected.append({"run_id": run_dir.name, "path": str(run_dir), "reason": "unresolved_stop"})
                continue
            if status != COMPLETED_STATUS:
                protected.append({"run_id": run_dir.name, "path": str(run_dir), "reason": "not_completed"})
                continue
            mtime = _run_mtime(run_dir)
            records.append(
                {
                    "run_id": run_dir.name,
                    "path": str(run_dir),
                    "mtime": mtime,
                    "age_days": round(_age_days(mtime, now=now), 3),
                    "status": status,
                    "completed_stop_marker": stop_exists,
                }
            )

    completed_desc = sorted(records, key=lambda item: (float(item["mtime"]), str(item["run_id"])), reverse=True)
    kept_ids = {str(item["run_id"]) for item in completed_desc[: policy.keep_last]}
    batch_name = now.strftime("%Y%m%dT%H%M%SZ")
    for item in completed_desc:
        run_id = str(item["run_id"])
        reasons: list[str] = []
        if run_id not in kept_ids:
            reasons.append(f"count_over_keep_last_{policy.keep_last}")
        if float(item["age_days"]) > policy.max_age_days:
            reasons.append(f"age_over_{policy.max_age_days}_days")
        if not reasons:
            protected.append({"run_id": run_id, "path": str(item["path"]), "reason": "within_retention_budget"})
            continue
        rotated.append(
            {
                "run_id": run_id,
                "from": str(item["path"]),
                "to": str(backup_root / batch_name / _safe_backup_name(run_id)),
                "reasons": reasons,
                "age_days": item["age_days"],
                "completed_stop_marker": item["completed_stop_marker"],
            }
        )

    backups = _backup_batches(backup_root)
    keep_existing_backups = max(policy.backup_keep_last - (1 if rotated else 0), 0)
    pruned_backups = [
        {"path": str(path), "reason": f"backup_batches_over_keep_last_{policy.backup_keep_last}"}
        for path in backups[keep_existing_backups:]
    ]
    return {
        "schema_version": "frontier-runs-retention-v1",
        "runs_root": str(runs_root),
        "backup_root": str(backup_root),
        "policy": asdict(policy),
        "protected": protected,
        "rotated": rotated,
        "pruned_backups": pruned_backups,
    }


def apply_runs_retention(
    *,
    repo_root: Path = ROOT,
    active_run_dir: Path | None = None,
    policy: RunsRetentionPolicy | None = None,
    dry_run: bool = True,
    now: datetime | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    report = plan_runs_retention(
        repo_root=repo_root,
        active_run_dir=active_run_dir,
        policy=policy,
        now=now,
        env=env,
    )
    report["dry_run"] = dry_run
    if dry_run:
        return report
    for action in report["rotated"]:
        source = Path(str(action["from"]))
        target = Path(str(action["to"]))
        if not source.exists():
            action["skipped"] = "missing_source"
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            suffix = datetime.now(UTC).strftime("%H%M%S")
            target = target.with_name(f"{target.name}-{suffix}")
            action["to"] = str(target)
        shutil.move(str(source), str(target))
        action["moved"] = True
    for action in report["pruned_backups"]:
        path = Path(str(action["path"]))
        if path.exists():
            shutil.rmtree(path)
            action["removed"] = True
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rotate local-only Frontier runs to persistent backup storage.")
    parser.add_argument("--apply", action="store_true", help="Move eligible completed runs into backup storage.")
    parser.add_argument("--active-run", type=Path, help="Run directory that must be protected.")
    parser.add_argument("--keep-last", type=int, default=None)
    parser.add_argument("--max-age-days", type=int, default=None)
    parser.add_argument("--backup-keep-last", type=int, default=None)
    args = parser.parse_args(argv)
    base_policy = RunsRetentionPolicy.from_env()
    policy = RunsRetentionPolicy(
        keep_last=args.keep_last or base_policy.keep_last,
        max_age_days=args.max_age_days or base_policy.max_age_days,
        backup_keep_last=args.backup_keep_last or base_policy.backup_keep_last,
    )
    report = apply_runs_retention(active_run_dir=args.active_run, policy=policy, dry_run=not args.apply)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
