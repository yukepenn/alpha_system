from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from tools.hooks import canary_runner, pre_push


GIT_CONTEXT_KEYS = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_COMMON_DIR",
    "GIT_PREFIX",
    "GIT_OBJECT_DIRECTORY",
)


def _run_git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        env=canary_runner._scrub_git_env(),
        text=True,
        capture_output=True,
        check=True,
    )


def _linked_worktree_gitdir(main_repo: Path, linked_tree: Path) -> Path:
    """Create linked-worktree gitdir metadata without running `git worktree`."""
    _run_git(main_repo, "init")
    worktree_gitdir = main_repo / ".git" / "worktrees" / "linked"
    worktree_gitdir.mkdir(parents=True)
    linked_tree.mkdir()
    linked_gitfile = linked_tree / ".git"
    linked_gitfile.write_text(f"gitdir: {worktree_gitdir}\n", encoding="utf-8")
    (worktree_gitdir / "commondir").write_text("../..\n", encoding="utf-8")
    (worktree_gitdir / "gitdir").write_text(f"{linked_gitfile}\n", encoding="utf-8")
    (worktree_gitdir / "HEAD").write_text(
        (main_repo / ".git" / "HEAD").read_text(),
        encoding="utf-8",
    )
    return worktree_gitdir


def test_git_env_scrub_removes_all_git_context_and_keeps_path() -> None:
    dirty_env = {"PATH": "/usr/bin", "HOME": "/tmp/home", "GIT_TRACE": "1"}
    dirty_env.update({key: f"leaked-{key}" for key in GIT_CONTEXT_KEYS})

    assert canary_runner._scrub_git_env(dirty_env) == {
        "PATH": "/usr/bin",
        "HOME": "/tmp/home",
    }
    assert pre_push._scrub_git_env(dirty_env) == {"PATH": "/usr/bin", "HOME": "/tmp/home"}


def test_canary_runner_git_init_ignores_leaked_linked_worktree_gitdir(
    tmp_path: Path,
    monkeypatch,
) -> None:
    main_repo = tmp_path / "main"
    linked_tree = tmp_path / "linked"
    main_repo.mkdir()
    worktree_gitdir = _linked_worktree_gitdir(main_repo, linked_tree)

    monkeypatch.setenv("GIT_DIR", str(worktree_gitdir))
    canary = canary_runner.Canary(
        "gitdir_scrub_regression",
        [
            sys.executable,
            "-c",
            (
                "import os; "
                "from pathlib import Path; "
                "assert not [key for key in os.environ if key.startswith('GIT_')]; "
                "raise SystemExit(0 if (Path.cwd() / '.git' / 'config').is_file() else 1)"
            ),
        ],
        {},
        expect_block=False,
    )

    passed, detail = canary_runner.run_canary(canary)

    assert passed, detail
    core_bare = _run_git(main_repo, "config", "--get", "--bool", "core.bare")
    assert core_bare.stdout.strip() == "false"


def test_pre_push_check_subprocesses_receive_scrubbed_git_env(monkeypatch) -> None:
    for key in (*GIT_CONTEXT_KEYS, "GIT_TRACE"):
        monkeypatch.setenv(key, f"leaked-{key}")
    monkeypatch.delenv("FRONTIER_STRICT_PRE_PUSH", raising=False)

    class TtyStdin:
        def isatty(self) -> bool:
            return True

    calls: list[dict[str, object]] = []

    def fake_run(command: list[str], **kwargs: object) -> SimpleNamespace:
        calls.append({"command": command, **kwargs})
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(pre_push.sys, "stdin", TtyStdin())
    monkeypatch.setattr(pre_push.subprocess, "run", fake_run)

    assert pre_push.main() == 0
    assert [call["command"] for call in calls] == [
        [sys.executable, "tools/verify.py", "--smoke"],
        [sys.executable, "tools/hooks/canary_runner.py"],
    ]
    for call in calls:
        env = call["env"]
        assert isinstance(env, dict)
        assert env["PATH"] == os.environ["PATH"]
        assert not [key for key in env if key.startswith("GIT_")]
