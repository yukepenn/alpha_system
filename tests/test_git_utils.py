from __future__ import annotations

from pathlib import Path

import pytest

from tools.frontier.git_utils import commit_phase_changes, git, sanitize_component, stage_paths


CONFIG = {
    "artifacts": {
        "allow_commit": ["docs/**", "src/**", "tests/**"],
        "forbid_commit": ["**/.env", "**/*.pem", "runs/**"],
    }
}


def test_sanitize_component() -> None:
    assert sanitize_component("Build Thing!") == "build-thing"


def test_git_refuses_broad_add(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        git(tmp_path, "add", ".")
    with pytest.raises(ValueError):
        git(tmp_path, "add", "-A")


def test_stage_paths_never_uses_git_add_dot(tmp_path: Path, monkeypatch) -> None:
    commands: list[tuple[str, ...]] = []

    def fake_git(root: Path, *args: str):
        del root
        commands.append(args)

        class Result:
            returncode = 0
            stdout = ""
            stderr = ""

        return Result()

    monkeypatch.setattr("tools.frontier.git_utils.git", fake_git)
    stage_paths(tmp_path, ["docs/a.md"], dry_run=False)

    assert commands == [("add", "--", "docs/a.md")]


def test_commit_plan_excludes_forbidden_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("tools.frontier.git_utils.status_porcelain", lambda root: "?? docs/a.md\n?? runs/run1/state.json\n?? .env\n")
    monkeypatch.setattr("tools.frontier.git_utils.diff_stat", lambda root: " docs/a.md | 1 +\n")

    result = commit_phase_changes(
        root=tmp_path,
        campaign_id="C1",
        phase_id="P1",
        summary="summary",
        branch="auto/c1/p1",
        config=CONFIG,
        dry_run=True,
        push=True,
    )

    assert result.staged_files == ["docs/a.md"]
    assert "runs/run1/state.json" in result.blocked_files
    assert ".env" in result.blocked_files
    assert ["git", "add", "--", "docs/a.md"] in result.commands
    assert ["git", "add", "."] not in result.commands
