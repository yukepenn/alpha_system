"""Provider and runtime configuration for Frontier Workflow 2."""

from __future__ import annotations

import os
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TIMEOUT_SECONDS = 1800


class ProviderConfigError(ValueError):
    """Raised when provider configuration is malformed."""


@dataclass(frozen=True)
class ProviderRuntimeConfig:
    root: Path
    mock_providers: bool
    provider_timeout_seconds: int
    claude_cmd: list[str]
    claude_output_format: str | None
    codex_cmd: list[str]
    codex_sandbox: str
    default_worktree_mode: bool
    worktree_root: Path | None
    lane_policies: dict[str, Any]
    raw: dict[str, Any]

    @property
    def provider_mode(self) -> str:
        return "mock" if self.mock_providers else "external"


def load_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        import yaml
    except ImportError as error:
        raise ProviderConfigError("PyYAML is required to read frontier.yaml.") from error
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise ProviderConfigError(f"Malformed YAML in {path}: {error}") from error
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ProviderConfigError(f"{path} must contain a YAML mapping.")
    return data


def _bool_from_env(name: str) -> bool | None:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return None
    return raw.lower() in {"1", "true", "yes", "on"}


def _positive_int(value: Any, source: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as error:
        raise ProviderConfigError(f"{source} must be a positive integer.") from error
    if parsed < 1:
        raise ProviderConfigError(f"{source} must be at least 1.")
    return parsed


def _command(value: Any, default: str) -> list[str]:
    if value is None or value == "":
        return [default]
    if isinstance(value, list) and all(isinstance(part, str) for part in value):
        if not value:
            raise ProviderConfigError("Provider command list cannot be empty.")
        return list(value)
    if isinstance(value, str):
        parsed = shlex.split(value)
        if not parsed:
            raise ProviderConfigError("Provider command cannot be empty.")
        return parsed
    raise ProviderConfigError("Provider command must be a string or list of strings.")


def _nested(mapping: Mapping[str, Any], *keys: str) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def _resolve_worktree_root(root: Path, raw: str | None) -> Path | None:
    if not raw:
        return None
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve()
    allowed_parent = root.resolve().parent
    if resolved != allowed_parent and allowed_parent not in resolved.parents:
        raise ProviderConfigError("FRONTIER_WORKTREE_ROOT must stay under the repository parent directory.")
    return resolved


def load_provider_config(root: Path | None = None, env: Mapping[str, str] | None = None) -> ProviderRuntimeConfig:
    root = (root or ROOT).resolve()
    if env is not None:
        old_env = os.environ.copy()
        os.environ.clear()
        os.environ.update(env)
    else:
        old_env = None
    try:
        raw = load_yaml_file(root / "frontier.yaml")
        providers = raw.get("providers") if isinstance(raw.get("providers"), dict) else {}
        workflow2 = raw.get("workflow2") if isinstance(raw.get("workflow2"), dict) else {}

        mock = _bool_from_env("FRONTIER_MOCK_PROVIDERS")
        if mock is None:
            mock = bool(_nested(providers, "mock", "enabled") or False)

        timeout_value = os.environ.get("FRONTIER_PROVIDER_TIMEOUT_SECONDS")
        if timeout_value is None:
            timeout_value = _nested(providers, "timeout_seconds") or DEFAULT_TIMEOUT_SECONDS
        timeout = _positive_int(timeout_value, "FRONTIER_PROVIDER_TIMEOUT_SECONDS")

        claude_cmd = _command(
            os.environ.get("FRONTIER_CLAUDE_CMD") or _nested(providers, "claude", "cmd"),
            "claude",
        )
        claude_output_format = _nested(providers, "claude", "output_format")
        if claude_output_format is not None and not isinstance(claude_output_format, str):
            raise ProviderConfigError("providers.claude.output_format must be a string when set.")

        codex_cmd = _command(
            os.environ.get("FRONTIER_CODEX_CMD") or _nested(providers, "codex", "cmd"),
            "codex",
        )
        codex_sandbox = os.environ.get("FRONTIER_CODEX_SANDBOX") or str(
            _nested(providers, "codex", "sandbox") or "workspace-write"
        )
        if codex_sandbox not in {"workspace-write", "read-only", "danger-full-access"}:
            raise ProviderConfigError("Codex sandbox must be workspace-write, read-only, or danger-full-access.")

        env_worktree = _bool_from_env("FRONTIER_WORKTREE_MODE")
        configured_worktree = workflow2.get("worktree_mode", workflow2.get("default_worktree_mode", False))
        default_worktree_mode = bool(configured_worktree) if env_worktree is None else env_worktree
        worktree_root = _resolve_worktree_root(root, os.environ.get("FRONTIER_WORKTREE_ROOT"))

        lanes = raw.get("lanes") if isinstance(raw.get("lanes"), dict) else {}
        return ProviderRuntimeConfig(
            root=root,
            mock_providers=mock,
            provider_timeout_seconds=timeout,
            claude_cmd=claude_cmd,
            claude_output_format=claude_output_format,
            codex_cmd=codex_cmd,
            codex_sandbox=codex_sandbox,
            default_worktree_mode=default_worktree_mode,
            worktree_root=worktree_root,
            lane_policies=dict(lanes),
            raw=raw,
        )
    finally:
        if old_env is not None:
            os.environ.clear()
            os.environ.update(old_env)
