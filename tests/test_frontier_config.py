from __future__ import annotations

from tools.frontier.config import validate_config
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
        "artifacts": {"allow_commit": [], "forbid_commit": []},
    }


def test_valid_generated_shape_passes() -> None:
    assert validate_config(base_config()) == []


def test_missing_lanes_fails() -> None:
    config = base_config()
    config["lanes"].pop("red")
    errors = validate_config(config)

    assert any("missing required lanes" in error for error in errors)


def test_env_overrides_provider_config(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("FRONTIER_MOCK_PROVIDERS", "1")
    monkeypatch.setenv("FRONTIER_PROVIDER_TIMEOUT_SECONDS", "9")
    monkeypatch.setenv("FRONTIER_CODEX_SANDBOX", "read-only")
    config = load_provider_config(tmp_path)

    assert config.mock_providers is True
    assert config.provider_timeout_seconds == 9
    assert config.codex_sandbox == "read-only"
