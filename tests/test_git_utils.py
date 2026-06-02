from __future__ import annotations

from pathlib import Path

import pytest

from tools.frontier.artifact_policy import curate_commit_paths
from tools.frontier.git_utils import (
    commit_phase_changes,
    git,
    prepare_phase_branch,
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
BOOTSTRAP_CONFIG = {
    "artifacts": {
        "allow_commit": [
            ".gitignore",
            "README.md",
            "PROJECT_STATUS.md",
            "frontier.yaml",
            "ACTIVE_CAMPAIGN.md",
            ".codex/**",
            ".claude/**",
            ".githooks/**",
            ".github/**",
            "tools/**",
            "scripts/**",
            "campaigns/**",
            "specs/**",
            "handoffs/**",
            "reviews/**",
            "decisions/**",
            "docs/**",
            "evals/**",
            "src/**",
            "tests/**",
            "configs/**",
            "data/**/README.md",
            "data/**/.gitkeep",
            "metadata/README.md",
            "metadata/.gitkeep",
            "artifacts/README.md",
            "artifacts/.gitkeep",
            "artifacts/**/README.md",
            "artifacts/**/.gitkeep",
        ],
        "forbid_commit": ["runs/**", ".frontier/upgrade_reports/**", "**/.env", "**/*.db", "**/*.parquet"],
        "placeholder_exceptions": ["**/.gitkeep", "**/README.md"],
        "placeholder_dirs": ["data/raw/**", "metadata/**", "artifacts/**"],
    }
}


def init_repo(root: Path) -> str:
    assert git(root, "init", "-b", "main").returncode == 0
    assert git(root, "config", "user.email", "frontier@example.invalid").returncode == 0
    assert git(root, "config", "user.name", "Frontier Test").returncode == 0
    (root / "README.md").write_text("# Base\n", encoding="utf-8")
    assert git(root, "add", "--", "README.md").returncode == 0
    assert git(root, "commit", "-m", "test: base").returncode == 0
    return git(root, "rev-parse", "HEAD").stdout.strip()


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
    assert result.commands == []
    assert result.commit_sha is None
    assert ["git", "add", "."] not in result.commands


def test_commit_refuses_pre_staged_run_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "tools.frontier.git_utils.status_porcelain",
        lambda root: "?? docs/a.md\nA  runs/run1/phases/P00/handoff.md\n",
    )
    monkeypatch.setattr(
        "tools.frontier.git_utils.checkout_or_create_branch",
        lambda root, branch, dry_run=False: [["git", "checkout", "-B", branch]],
    )
    monkeypatch.setattr(
        "tools.frontier.git_utils.stage_paths",
        lambda root, paths, dry_run=False: [["git", "add", "--", path] for path in paths],
    )
    monkeypatch.setattr(
        "tools.frontier.git_utils.staged_files",
        lambda root: ["docs/a.md", "runs/run1/phases/P00/handoff.md"],
    )
    monkeypatch.setattr("tools.frontier.git_utils.diff_stat", lambda root: "")
    monkeypatch.setattr(
        "tools.frontier.git_utils.commit_staged",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("commit must not run")),
    )

    result = commit_phase_changes(
        root=tmp_path,
        campaign_id="C1",
        phase_id="P1",
        summary="summary",
        branch="auto/c1/p1",
        config=CONFIG,
        dry_run=False,
        push=False,
    )

    assert "runs/run1/phases/P00/handoff.md" in result.blocked_files
    assert result.commit_sha is None


def test_prepare_phase_branch_resets_local_retry_branch_without_advancing_main(tmp_path: Path) -> None:
    base_sha = init_repo(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "old.md").write_text("old\n", encoding="utf-8")
    assert git(tmp_path, "checkout", "-B", "auto/c1/p00", "main").returncode == 0
    assert git(tmp_path, "add", "--", "docs/old.md").returncode == 0
    assert git(tmp_path, "commit", "-m", "test: old phase").returncode == 0
    assert git(tmp_path, "checkout", "main").returncode == 0

    result = prepare_phase_branch(tmp_path, "auto/c1/p00", base_ref="main", dry_run=False)

    assert result.branch == "auto/c1/p00"
    assert result.base_sha == base_sha
    assert git(tmp_path, "rev-parse", "main").stdout.strip() == base_sha
    assert git(tmp_path, "rev-parse", "HEAD").stdout.strip() == base_sha


def test_prepare_phase_branch_uses_unique_retry_when_remote_tracking_ref_exists(tmp_path: Path) -> None:
    base_sha = init_repo(tmp_path)
    assert git(tmp_path, "update-ref", "refs/remotes/origin/auto/c1/p00", base_sha).returncode == 0

    result = prepare_phase_branch(tmp_path, "auto/c1/p00", base_ref="main", dry_run=False)

    assert result.branch == "auto/c1/p00-retry-2"
    assert result.requested_branch == "auto/c1/p00"
    assert result.used_unique_branch is True
    assert result.remote_tracking_ref == "refs/remotes/origin/auto/c1/p00"


def test_commit_phase_changes_commits_uncommitted_bootstrap_files(tmp_path: Path) -> None:
    base_sha = init_repo(tmp_path)
    prepare_phase_branch(tmp_path, "auto/c1/p00-bootstrap", base_ref="main", dry_run=False)
    for relative_path, body in {
        ".gitignore": "__pycache__/\n",
        "PROJECT_STATUS.md": "# Status\n",
        "frontier.yaml": "schema_version: test\n",
        "ACTIVE_CAMPAIGN.md": "Campaign: C1\n",
        "data/raw/README.md": "# Raw Data\n",
        "metadata/README.md": "# Metadata\n",
        "artifacts/README.md": "# Artifacts\n",
        "artifacts/.gitkeep": "",
        "artifacts/reports/README.md": "# Reports\n",
    }.items():
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")

    result = commit_phase_changes(
        root=tmp_path,
        campaign_id="C1",
        phase_id="P00",
        summary="bootstrap repo policy",
        branch="auto/c1/p00-bootstrap",
        config=BOOTSTRAP_CONFIG,
        dry_run=False,
        push=False,
        base_sha=base_sha,
    )

    assert result.commit_sha
    assert result.source == "uncommitted_changes"
    assert "PROJECT_STATUS.md" in result.changed_files
    assert "data/raw/README.md" in result.staged_files
    assert result.blocked_files == []
    assert git(tmp_path, "rev-parse", "main").stdout.strip() == base_sha


def test_commit_phase_changes_adopts_existing_head_commit(tmp_path: Path) -> None:
    base_sha = init_repo(tmp_path)
    prepare_phase_branch(tmp_path, "auto/c1/p00", base_ref="main", dry_run=False)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# A\n", encoding="utf-8")
    assert git(tmp_path, "add", "--", "docs/a.md").returncode == 0
    assert git(tmp_path, "commit", "-m", "C1/P00: executor commit").returncode == 0
    head_sha = git(tmp_path, "rev-parse", "HEAD").stdout.strip()

    result = commit_phase_changes(
        root=tmp_path,
        campaign_id="C1",
        phase_id="P00",
        summary="summary",
        branch="auto/c1/p00",
        config=CONFIG,
        dry_run=False,
        push=False,
        base_sha=base_sha,
    )

    assert result.commit_sha == head_sha
    assert result.source == "existing_head_commit"
    assert result.changed_files == ["docs/a.md"]
    assert result.diff_files == ["docs/a.md"]
    assert result.staged_files == ["docs/a.md"]
    assert result.blocked_files == []


def test_commit_phase_changes_blocks_clean_head_equal_to_base(tmp_path: Path) -> None:
    base_sha = init_repo(tmp_path)
    prepare_phase_branch(tmp_path, "auto/c1/p00", base_ref="main", dry_run=False)

    result = commit_phase_changes(
        root=tmp_path,
        campaign_id="C1",
        phase_id="P00",
        summary="summary",
        branch="auto/c1/p00",
        config=CONFIG,
        dry_run=False,
        push=False,
        base_sha=base_sha,
    )

    assert result.commit_sha is None
    assert result.changed_files == []
    assert result.source == "no_phase_commit"


def test_commit_phase_changes_rejects_forbidden_existing_head_diff(tmp_path: Path) -> None:
    base_sha = init_repo(tmp_path)
    prepare_phase_branch(tmp_path, "auto/c1/p00", base_ref="main", dry_run=False)
    (tmp_path / "runs" / "run1").mkdir(parents=True)
    (tmp_path / "runs" / "run1" / "state.json").write_text("{}\n", encoding="utf-8")
    assert git(tmp_path, "add", "--", "runs/run1/state.json").returncode == 0
    assert git(tmp_path, "commit", "-m", "C1/P00: bad run artifact").returncode == 0

    result = commit_phase_changes(
        root=tmp_path,
        campaign_id="C1",
        phase_id="P00",
        summary="summary",
        branch="auto/c1/p00",
        config=BOOTSTRAP_CONFIG,
        dry_run=False,
        push=False,
        base_sha=base_sha,
    )

    assert result.commit_sha is None
    assert result.source == "existing_head_commit"
    assert "runs/run1/state.json" in result.diff_files
    assert "runs/run1/state.json" in result.blocked_files


def test_commit_phase_changes_rejects_upgrade_report_existing_head_diff(tmp_path: Path) -> None:
    base_sha = init_repo(tmp_path)
    prepare_phase_branch(tmp_path, "auto/c1/p00", base_ref="main", dry_run=False)
    (tmp_path / ".frontier" / "upgrade_reports").mkdir(parents=True)
    (tmp_path / ".frontier" / "upgrade_reports" / "report.json").write_text("{}\n", encoding="utf-8")
    assert git(tmp_path, "add", "--", ".frontier/upgrade_reports/report.json").returncode == 0
    assert git(tmp_path, "commit", "-m", "C1/P00: bad upgrade report").returncode == 0

    result = commit_phase_changes(
        root=tmp_path,
        campaign_id="C1",
        phase_id="P00",
        summary="summary",
        branch="auto/c1/p00",
        config=BOOTSTRAP_CONFIG,
        dry_run=False,
        push=False,
        base_sha=base_sha,
    )

    assert result.commit_sha is None
    assert ".frontier/upgrade_reports/report.json" in result.blocked_files


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
        "artifacts/README.md",
        "artifacts/.gitkeep",
        "artifacts/reports/README.md",
        "data/raw/SPY.parquet",
        "data/cache/cache.sqlite",
        "artifacts/report.pkl",
        "artifacts/model.pkl",
        "artifacts/model.joblib",
        "artifacts/output.parquet",
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
            "artifacts/README.md",
            "artifacts/.gitkeep",
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
            "**/*.joblib",
        ],
    )

    assert allowed == [
        "artifacts/.gitkeep",
        "artifacts/README.md",
        "artifacts/reports/README.md",
        "data/cache/README.md",
        "data/labels/README.md",
        "data/raw/README.md",
        "metadata/README.md",
    ]
    assert "data/raw/SPY.parquet" in blocked
    assert "data/cache/cache.sqlite" in blocked
    assert "artifacts/report.pkl" in blocked
    assert "artifacts/model.pkl" in blocked
    assert "artifacts/model.joblib" in blocked
    assert "artifacts/output.parquet" in blocked
    assert "metadata/registry.sqlite" in blocked
    assert ".frontier/upgrade_reports/report.json" in blocked
    assert ".env" in blocked
    assert "secrets.json" in blocked
    assert "runs/run1/state.json" in blocked
    assert "runs/local.log" in blocked
    assert "logs/frontier.log" in blocked
    assert "notes/README.md" in blocked
