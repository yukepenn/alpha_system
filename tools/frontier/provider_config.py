"""Provider and runtime configuration for Frontier Workflow 2."""

from __future__ import annotations

import os
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TIMEOUT_SECONDS = 21600


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
    codex_service_tier: str
    codex_shell_environment_inherit: str
    default_worktree_mode: bool
    worktree_root: Path | None
    lane_policies: dict[str, Any]
    raw: dict[str, Any]

    @property
    def provider_mode(self) -> str:
        return "mock" if self.mock_providers else "external"


# OpenAI service tiers accepted by the codex CLI `-c service_tier=<v>` override.
# "fast" is the friendly alias for the priority (expedited, higher-cost) tier.
_VALID_SERVICE_TIERS = {"auto", "default", "flex", "priority", "scale"}
_SERVICE_TIER_ALIASES = {"fast": "priority"}


def _resolve_service_tier(value: str) -> str:
    resolved = (value or "").strip().lower()
    resolved = _SERVICE_TIER_ALIASES.get(resolved, resolved)
    if resolved not in _VALID_SERVICE_TIERS:
        raise ProviderConfigError(
            "Codex service_tier must be one of "
            f"{sorted(_VALID_SERVICE_TIERS)} (or alias 'fast' -> 'priority'); got {value!r}."
        )
    return resolved


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
        codex_service_tier = _resolve_service_tier(
            os.environ.get("FRONTIER_CODEX_SERVICE_TIER")
            or str(_nested(providers, "codex", "service_tier") or "fast")
        )
        # Codex sandboxes the environment of model-executed commands; by default it
        # does NOT pass through custom env vars (e.g. ALPHA_DATA_ROOT) or the
        # caller's PATH (e.g. an activated venv). Data-dependent phases run their
        # runtime via those commands, so the executor must inherit the run
        # environment. Default to "all"; allow narrowing to codex's "core" if a
        # deployment wants the minimal set.
        codex_shell_environment_inherit = str(
            os.environ.get("FRONTIER_CODEX_SHELL_ENV_INHERIT")
            or _nested(providers, "codex", "shell_environment_inherit")
            or "all"
        ).strip().lower()
        if codex_shell_environment_inherit not in {"all", "core"}:
            raise ProviderConfigError(
                "Codex shell_environment_inherit must be 'all' or 'core'; "
                f"got {codex_shell_environment_inherit!r}."
            )

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
            codex_service_tier=codex_service_tier,
            codex_shell_environment_inherit=codex_shell_environment_inherit,
            default_worktree_mode=default_worktree_mode,
            worktree_root=worktree_root,
            lane_policies=dict(lanes),
            raw=raw,
        )
    finally:
        if old_env is not None:
            os.environ.clear()
            os.environ.update(old_env)
