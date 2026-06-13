"""Local runtime paths that must stay outside the git worktree."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ALPHA_SYSTEM_ROOT = Path("~/alpha_data/alpha_system")


def _expand_path(value: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(value))).resolve(strict=False)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def alpha_system_root(
    *,
    repo_root: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> Path:
    """Resolve the persistent local alpha_system root outside the repo.

    ``ALPHA_SYSTEM_ROOT`` is the preferred operator-facing name for harness
    scratch and post-mortem breadcrumbs. ``ALPHA_DATA_ROOT`` is accepted as the
    local default because existing Frontier runs already grant that root to the
    Codex sandbox and keep it outside the worktree.
    """

    root = (repo_root or ROOT).resolve()
    source = os.environ if env is None else env
    raw = (source.get("ALPHA_SYSTEM_ROOT") or source.get("ALPHA_DATA_ROOT") or str(DEFAULT_ALPHA_SYSTEM_ROOT)).strip()
    resolved = _expand_path(raw)
    if resolved == root or _is_relative_to(resolved, root):
        raise ValueError("ALPHA_SYSTEM_ROOT must resolve outside the git worktree.")
    return resolved


def persistent_tmp_root(
    *,
    repo_root: Path | None = None,
    env: Mapping[str, str] | None = None,
    create: bool = True,
) -> Path:
    """Return ``$ALPHA_SYSTEM_ROOT/.tmp`` and create it by default."""

    tmp = alpha_system_root(repo_root=repo_root, env=env) / ".tmp"
    repo = (repo_root or ROOT).resolve()
    resolved = tmp.resolve(strict=False)
    if resolved == repo or _is_relative_to(resolved, repo):
        raise ValueError("Persistent Frontier tmp root must stay outside the git worktree.")
    if create:
        resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def persistent_tmp_env(
    *,
    repo_root: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return an environment copy with stdlib temporary directories re-rooted."""

    merged = dict(os.environ if env is None else env)
    tmp = persistent_tmp_root(repo_root=repo_root, env=merged)
    for name in ("TMPDIR", "TEMP", "TMP"):
        merged[name] = str(tmp)
    return merged
