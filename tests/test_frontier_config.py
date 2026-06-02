from __future__ import annotations

from pathlib import Path

from tools.frontier.config import load_config, validate_config
from tools.frontier.provider_config import load_provider_config


def base_config() -> dict:
    return {
        "schema_version": "frontier-harness-v3",
        "lanes": {
            "green": {"required_checks": [], "require_claude_review": False, "auto_pr": True, "auto_merge": True, "max_micro_loops": 1, "max_repair_attempts": 1, "max_phase_minutes": 1, "merge_policy": {"allow_pass_with_warnings": True}},
            "yellow": {"required_checks": [], "require_claude_review": True, "auto_pr": True, "auto_merge": True, "max_micro_loops": 1, "max_repair_attempts": 1, "max_phase_minutes": 1, "merge_policy": {"allow_pass_with_warnings": True}},
            "red": {"required_checks": [], "require_claude_review": True, "auto_pr": False, "auto_merge": False, "max_micro_loops": 1, "max_repair_attempts": 1, "max_phase_minutes": 1, "merge_policy": {"allow_pass_with_warnings": False}},
        },
        "workflow2": {
            "enabled": True,
            "max_phases": 1,
            "max_micro_loops_default": 1,
            "max_repair_attempts_default": 1,
            "max_run_minutes": 1,
            "max_phase_minutes": 1,
            "max_estimated_usd": 0.0,
            "semantic_done_check_required": True,
            "worktree_mode": False,
            "worktree_mode_recommended": True,
            "auto_pr": True,
            "auto_merge": True,
        },
        "github": {
            "ci_timeout_seconds": 1,
            "ci_poll_seconds": 1,
            "required_checks": [],
            "require_ci": True,
            "require_branch_protection": True,
            "allow_unprotected_green_merge": False,
            "allow_unprotected_dry_run": True,
            "merge_method": "squash",
        },
        "git": {
            "explicit_add_only": True,
            "forbid_git_add_dot": True,
            "forbid_git_add_A": True,
            "forbid_force_push": True,
        },
        "artifacts": {
            "allow_commit": [],
            "forbid_commit": [],
            "placeholder_exceptions": ["**/.gitkeep", "**/README.md"],
            "placeholder_dirs": ["data/raw/**", "data/cache/**"],
        },
    }


def test_valid_generated_shape_passes() -> None:
    assert validate_config(base_config()) == []


def test_missing_lanes_fails() -> None:
    config = base_config()
    config["lanes"].pop("red")
    errors = validate_config(config)

    assert any("missing required lanes" in error for error in errors)


def test_artifact_placeholder_policy_shape_is_validated() -> None:
    config = base_config()
    config["artifacts"]["placeholder_exceptions"] = "**/.gitkeep"

    errors = validate_config(config)

    assert "artifacts.placeholder_exceptions must be a list." in errors


def test_generated_frontier_yaml_artifact_policy_includes_bootstrap_paths() -> None:
    config = load_config(Path("frontier.yaml"))
    artifacts = config["artifacts"]
    allow_commit = artifacts["allow_commit"]
    forbid_commit = artifacts["forbid_commit"]

    for required in [
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
        "artifacts/**/README.md",
        "artifacts/**/.gitkeep",
    ]:
        assert required in allow_commit

    assert "runs/**" in forbid_commit
    assert ".frontier/upgrade_reports/**" in forbid_commit
    assert "runs/**" not in allow_commit


def test_env_overrides_provider_config(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("FRONTIER_MOCK_PROVIDERS", "1")
    monkeypatch.setenv("FRONTIER_PROVIDER_TIMEOUT_SECONDS", "9")
    monkeypatch.setenv("FRONTIER_CODEX_SANDBOX", "read-only")
    config = load_provider_config(tmp_path)

    assert config.mock_providers is True
    assert config.provider_timeout_seconds == 9
    assert config.codex_sandbox == "read-only"
