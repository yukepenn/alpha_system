"""Frontier configuration loading and validation."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from tools.frontier.provider_config import ProviderConfigError, load_provider_config, load_yaml_file


ROOT = Path(__file__).resolve().parents[2]
REQUIRED_LANES = {"green", "yellow", "red"}
REQUIRED_LANE_KEYS = {
    "required_checks",
    "require_claude_review",
    "auto_pr",
    "auto_merge",
    "max_micro_loops",
    "max_repair_attempts",
    "max_phase_minutes",
    "merge_policy",
}
REQUIRED_WORKFLOW2_KEYS = {
    "enabled",
    "max_phases",
    "max_micro_loops_default",
    "max_repair_attempts_default",
    "max_run_minutes",
    "max_phase_minutes",
    "max_estimated_usd",
    "semantic_done_check_required",
    "worktree_mode",
    "worktree_mode_recommended",
    "auto_pr",
    "auto_merge",
}
REQUIRED_GITHUB_KEYS = {
    "ci_timeout_seconds",
    "ci_poll_seconds",
    "required_checks",
    "require_ci",
    "require_branch_protection",
    "allow_unprotected_green_merge",
    "allow_unprotected_dry_run",
    "merge_method",
}


class FrontierConfigError(ValueError):
    """Raised when frontier.yaml is invalid."""


def load_config(path: Path | None = None) -> dict[str, Any]:
    return load_yaml_file(path or (ROOT / "frontier.yaml"))


def _require_mapping(data: dict[str, Any], key: str, errors: list[str]) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        errors.append(f"{key} must be a mapping.")
        return {}
    return value


def _validate_lanes(data: dict[str, Any], errors: list[str]) -> None:
    lanes = _require_mapping(data, "lanes", errors)
    missing = sorted(REQUIRED_LANES - set(lanes))
    if missing:
        errors.append("lanes is missing required lanes: " + ", ".join(missing))
    for lane_name in sorted(REQUIRED_LANES & set(lanes)):
        lane = lanes.get(lane_name)
        if not isinstance(lane, dict):
            errors.append(f"lanes.{lane_name} must be a mapping.")
            continue
        missing_keys = sorted(REQUIRED_LANE_KEYS - set(lane))
        if missing_keys:
            errors.append(f"lanes.{lane_name} is missing: " + ", ".join(missing_keys))
        if not isinstance(lane.get("required_checks", []), list):
            errors.append(f"lanes.{lane_name}.required_checks must be a list.")
        if not isinstance(lane.get("merge_policy", {}), dict):
            errors.append(f"lanes.{lane_name}.merge_policy must be a mapping.")
        for key in ("max_micro_loops", "max_repair_attempts", "max_phase_minutes"):
            value = lane.get(key)
            try:
                if int(value) < 1:
                    errors.append(f"lanes.{lane_name}.{key} must be at least 1.")
            except (TypeError, ValueError):
                errors.append(f"lanes.{lane_name}.{key} must be an integer.")


def _validate_workflow2(data: dict[str, Any], errors: list[str]) -> None:
    workflow2 = _require_mapping(data, "workflow2", errors)
    if workflow2 and not workflow2.get("enabled", False):
        errors.append("workflow2.enabled must be true for this harness runtime.")
    missing = sorted(REQUIRED_WORKFLOW2_KEYS - set(workflow2))
    if missing:
        errors.append("workflow2 is missing: " + ", ".join(missing))
    for key in (
        "max_phases",
        "max_micro_loops_default",
        "max_repair_attempts_default",
        "max_run_minutes",
        "max_phase_minutes",
    ):
        value = workflow2.get(key)
        if value is not None:
            try:
                if int(value) < 1:
                    errors.append(f"workflow2.{key} must be at least 1.")
            except (TypeError, ValueError):
                errors.append(f"workflow2.{key} must be an integer.")
    value = workflow2.get("max_estimated_usd")
    if value is not None:
        try:
            if float(value) < 0:
                errors.append("workflow2.max_estimated_usd must be non-negative.")
        except (TypeError, ValueError):
            errors.append("workflow2.max_estimated_usd must be numeric.")


def _validate_github(data: dict[str, Any], errors: list[str]) -> None:
    github = _require_mapping(data, "github", errors)
    missing = sorted(REQUIRED_GITHUB_KEYS - set(github))
    if missing:
        errors.append("github is missing: " + ", ".join(missing))
    if "required_checks" in github and not isinstance(github.get("required_checks"), list):
        errors.append("github.required_checks must be a list.")
    for key in ("ci_timeout_seconds", "ci_poll_seconds"):
        value = github.get(key)
        if value is not None:
            try:
                if int(value) < 1:
                    errors.append(f"github.{key} must be at least 1.")
            except (TypeError, ValueError):
                errors.append(f"github.{key} must be an integer.")
    if github.get("merge_method") not in {None, "squash", "merge", "rebase"}:
        errors.append("github.merge_method must be squash, merge, or rebase.")


def _validate_git(data: dict[str, Any], errors: list[str]) -> None:
    git_config = _require_mapping(data, "git", errors)
    for key in ("explicit_add_only", "forbid_git_add_dot", "forbid_git_add_A", "forbid_force_push"):
        if key not in git_config:
            errors.append(f"git.{key} is required.")


def _validate_artifacts(data: dict[str, Any], errors: list[str]) -> None:
    artifacts = _require_mapping(data, "artifacts", errors)
    for key in ("allow_commit", "forbid_commit"):
        if key not in artifacts:
            errors.append(f"artifacts.{key} is required.")
        elif not isinstance(artifacts[key], list):
            errors.append(f"artifacts.{key} must be a list.")


def _validate_provider_config(root: Path, errors: list[str]) -> None:
    try:
        config = load_provider_config(root)
    except ProviderConfigError as error:
        errors.append(str(error))
        return
    if not config.mock_providers:
        for label, command in (("Claude", config.claude_cmd), ("Codex", config.codex_cmd)):
            if command and shutil.which(command[0]) is None:
                errors.append(f"{label} command is not available on PATH: {command[0]}")


def validate_config(data: dict[str, Any], *, root: Path | None = None, check_commands: bool = False) -> list[str]:
    root = (root or ROOT).resolve()
    errors: list[str] = []
    if data.get("schema_version") != "frontier-harness-v3":
        errors.append("schema_version must be frontier-harness-v3.")
    _validate_lanes(data, errors)
    _validate_workflow2(data, errors)
    _validate_github(data, errors)
    _validate_git(data, errors)
    _validate_artifacts(data, errors)
    if check_commands:
        _validate_provider_config(root, errors)
    return errors


def assert_valid_config(data: dict[str, Any], *, root: Path | None = None, check_commands: bool = False) -> None:
    errors = validate_config(data, root=root, check_commands=check_commands)
    if errors:
        raise FrontierConfigError("; ".join(errors))
