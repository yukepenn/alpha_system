from __future__ import annotations

from pathlib import Path

import pytest

from tools.frontier.artifact_policy import curate_commit_paths
from tools.frontier.git_utils import (
    commit_phase_changes,
    git,
    push_phase_branch,
    sanitize_component,
    stage_paths,
    verify_remote_branch,
)


CONFIG = {
    "artifacts": {
        "allow_commit": ["docs/**", "src/**", "tests/**"],
        "forbid_commit": ["**/.env", "**/*.pem", "runs/**"],
    }
}
DATA_PLACEHOLDER_CONFIG = {
    "artifacts": {
        "allow_commit": ["data/**/README.md", "data/**/.gitkeep"],
        "forbid_commit": ["**/data/raw/**", "**/cache/**", "**/*.db", "**/*.parquet"],
        "placeholder_exceptions": ["**/.gitkeep", "**/README.md"],
        "placeholder_dirs": ["data/raw/**", "data/cache/**"],
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
    monkeypatch.setattr(
        "tools.frontier.git_utils.status_porcelain",
        lambda root: "?? docs/a.md\n?? runs/run1/state.json\n?? .env\n",
    )
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
    assert ["git", "push", "-u", "origin", "HEAD:refs/heads/auto/c1/p1"] in result.commands


def test_push_phase_branch_uses_safe_head_refspec(tmp_path: Path, monkeypatch) -> None:
    commands: list[tuple[str, ...]] = []

    def fake_git(root: Path, *args: str):
        del root
        commands.append(args)

        class Result:
            returncode = 0
            stdout = "ok\n"
            stderr = ""

        return Result()

    monkeypatch.setattr("tools.frontier.git_utils.git", fake_git)

    result = push_phase_branch(tmp_path, "auto/c1/p1-slug", dry_run=False)

    assert result.ok
    assert result.command == ["git", "push", "-u", "origin", "HEAD:refs/heads/auto/c1/p1-slug"]
    assert commands == [("push", "-u", "origin", "HEAD:refs/heads/auto/c1/p1-slug")]


def test_verify_remote_branch_matches_sha_with_slashes(tmp_path: Path, monkeypatch) -> None:
    branch = "auto/c1/p1-slug"
    sha = "a" * 40

    def fake_git(root: Path, *args: str):
        del root

        class Result:
            returncode = 0
            stdout = ""
            stderr = ""

        result = Result()
        if args == ("rev-parse", branch):
            result.stdout = sha + "\n"
        elif args == ("ls-remote", "--heads", "origin", f"refs/heads/{branch}"):
            result.stdout = f"{sha}\trefs/heads/{branch}\n"
        else:
            result.returncode = 1
            result.stderr = "unexpected command"
        return result

    monkeypatch.setattr("tools.frontier.git_utils.git", fake_git)

    result = verify_remote_branch(tmp_path, branch)

    assert result.exists
    assert result.matches
    assert result.remote_sha == sha
    assert result.local_sha == sha


def test_commit_plan_allows_configured_placeholders_before_forbidden_globs(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        "tools.frontier.git_utils.status_porcelain",
        lambda root: "?? data/raw/.gitkeep\n?? data/raw/README.md\n?? data/raw/input.csv\n?? data/cache/cache.db\n",
    )
    monkeypatch.setattr("tools.frontier.git_utils.diff_stat", lambda root: "")

    result = commit_phase_changes(
        root=tmp_path,
        campaign_id="C1",
        phase_id="P1",
        summary="summary",
        branch="auto/c1/p1",
        config=DATA_PLACEHOLDER_CONFIG,
        dry_run=True,
        push=False,
    )

    assert result.staged_files == ["data/raw/.gitkeep", "data/raw/README.md"]
    assert "data/raw/input.csv" in result.blocked_files
    assert "data/cache/cache.db" in result.blocked_files


def test_artifact_policy_allows_only_configured_local_placeholders() -> None:
    paths = [
        "data/raw/README.md",
        "data/cache/README.md",
        "data/labels/README.md",
        "metadata/README.md",
        "artifacts/reports/README.md",
        "data/raw/SPY.parquet",
        "data/cache/cache.sqlite",
        "artifacts/model.pkl",
        "metadata/registry.sqlite",
        ".frontier/upgrade_reports/report.json",
        ".env",
        "secrets.json",
        "runs/run1/state.json",
        "runs/local.log",
        "logs/frontier.log",
        "notes/README.md",
    ]

    allowed, blocked = curate_commit_paths(
        paths,
        allow_patterns=[
            "data/**/README.md",
            "data/**/.gitkeep",
            "metadata/README.md",
            "metadata/.gitkeep",
            "artifacts/**/README.md",
            "artifacts/**/.gitkeep",
        ],
        forbid_patterns=[
            "**/.env",
            "**/secrets.*",
            "**/data/raw/**",
            "**/data/cache/**",
            "**/cache/**",
            ".frontier/upgrade_reports/**",
            "runs/**",
            "logs/**",
            "metadata/**",
            "artifacts/**",
            "**/*.parquet",
            "**/*.sqlite",
            "**/*.pkl",
        ],
    )

    assert allowed == [
        "artifacts/reports/README.md",
        "data/cache/README.md",
        "data/labels/README.md",
        "data/raw/README.md",
        "metadata/README.md",
    ]
    assert "data/raw/SPY.parquet" in blocked
    assert "data/cache/cache.sqlite" in blocked
    assert "artifacts/model.pkl" in blocked
    assert "metadata/registry.sqlite" in blocked
    assert ".frontier/upgrade_reports/report.json" in blocked
    assert ".env" in blocked
    assert "secrets.json" in blocked
    assert "runs/run1/state.json" in blocked
    assert "runs/local.log" in blocked
    assert "logs/frontier.log" in blocked
    assert "notes/README.md" in blocked
