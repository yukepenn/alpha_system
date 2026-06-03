"""Run-manifest assembly for strategy grid reproducibility."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from alpha_system.core.git_info import capture_git_info
from alpha_system.core.hashing import hash_code_paths, hash_config


GRID_CODE_MODULES: tuple[str, ...] = (
    "grid.py",
    "limits.py",
    "leaderboard.py",
    "grid_outputs.py",
    "grid_config.py",
    "grid_manifest.py",
    "runner.py",
)


def build_grid_manifest(
    *,
    run_id: str,
    grid_id: str,
    engine_version: str,
    config_hash: str,
    config_payload: Mapping[str, Any],
    data_version: str,
    factor_versions: Mapping[str, str],
    label_versions: Mapping[str, str],
    parameters: Mapping[str, Any],
    artifact_paths: Mapping[str, str],
    decision_status: str,
    warnings: Sequence[str],
    failed_steps: Sequence[str],
    repo_root: str | Path | None = None,
    timestamp: datetime | None = None,
) -> dict[str, Any]:
    """Build a deterministic manifest payload with required reproducibility fields."""
    active_timestamp = timestamp or datetime.now(timezone.utc)
    if active_timestamp.tzinfo is None:
        active_timestamp = active_timestamp.replace(tzinfo=timezone.utc)
    active_timestamp = active_timestamp.astimezone(timezone.utc)
    root = Path(repo_root).resolve(strict=False) if repo_root is not None else Path.cwd()
    git_info = capture_git_info(root)
    code_hash = _grid_code_hash(root)
    payload: dict[str, Any] = {
        "run_id": run_id,
        "grid_id": grid_id,
        "timestamp": active_timestamp.isoformat().replace("+00:00", "Z"),
        "git_commit": git_info.commit,
        "git_dirty": git_info.dirty,
        "git_status_message": git_info.status_message,
        "code_hash": code_hash,
        "config_hash": config_hash,
        "config": dict(config_payload),
        "data_version": data_version,
        "factor_versions": dict(sorted(factor_versions.items())),
        "label_versions": dict(sorted(label_versions.items())),
        "engine_version": engine_version,
        "parameters": dict(parameters),
        "artifact_paths": dict(sorted(artifact_paths.items())),
        "decision_status": decision_status,
        "warnings": list(warnings),
        "failed_steps": list(failed_steps),
    }
    payload["manifest_hash"] = hash_config(
        {key: value for key, value in payload.items() if key != "manifest_hash"}
    )
    return payload


def _grid_code_hash(repo_root: Path) -> str:
    module_root = Path(__file__).resolve().parent
    paths = tuple(module_root / name for name in GRID_CODE_MODULES if (module_root / name).exists())
    if not paths:
        return hash_config({"module": __name__, "available": False})
    try:
        return hash_code_paths(paths, root=repo_root)
    except ValueError:
        return hash_code_paths(paths)
