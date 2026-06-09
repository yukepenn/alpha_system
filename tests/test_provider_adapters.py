from __future__ import annotations

from tools.frontier.command_runner import CommandResult
from tools.frontier.provider_adapters import (
    PROVIDER_BLOCKED,
    WAITING_CLAUDE_LIMIT,
    WAITING_CODEX_LIMIT,
    WAITING_PROVIDER_LIMIT,
    ClaudeProviderAdapter,
    CodexProviderAdapter,
    MockProviderAdapter,
    classify_provider_nonzero,
)
from tools.frontier.provider_config import load_provider_config


class RecordingRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], dict]] = []

    def run(self, command, **kwargs):
        self.calls.append((list(command), kwargs))
        return CommandResult(
            command=list(command),
            return_code=0,
            stdout="ok",
            stderr="",
            duration_ms=1,
        )


def test_mock_provider_never_calls_external_cli(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("FRONTIER_MOCK_PROVIDERS", "1")
    config = load_provider_config(tmp_path)

    response = MockProviderAdapter(config).run_prompt("hello")

    assert response.ok
    assert response.command == ["mock-provider"]
    assert "no external CLI" in response.stdout


def test_claude_command_uses_print_mode(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("FRONTIER_MOCK_PROVIDERS", raising=False)
    monkeypatch.setenv("FRONTIER_CLAUDE_CMD", "claude")
    config = load_provider_config(tmp_path)

    command = ClaudeProviderAdapter(config).build_command("prompt")

    assert command[:2] == ["claude", "-p"]
    assert command[2] != "prompt"


def test_claude_prompt_uses_stdin_for_large_prompts(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("FRONTIER_MOCK_PROVIDERS", raising=False)
    monkeypatch.setenv("FRONTIER_CLAUDE_CMD", "claude")
    config = load_provider_config(tmp_path)
    runner = RecordingRunner()
    prompt = "review\n" + ("x" * 200_000)

    response = ClaudeProviderAdapter(config, runner).run_prompt(prompt)

    assert response.ok
    command, kwargs = runner.calls[0]
    assert kwargs["stdin_text"] == prompt
    assert prompt not in command
    assert sum(len(part) for part in command) < 1000


def test_codex_command_uses_workspace_write_sandbox(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("FRONTIER_MOCK_PROVIDERS", raising=False)
    monkeypatch.setenv("FRONTIER_CODEX_CMD", "codex")
    monkeypatch.setenv("FRONTIER_CODEX_SANDBOX", "workspace-write")
    data_root = tmp_path / "alpha_data" / "alpha_system"
    monkeypatch.setenv("ALPHA_DATA_ROOT", str(data_root))
    config = load_provider_config(tmp_path)

    command = CodexProviderAdapter(config).build_command("prompt")

    resolved = str(data_root.resolve())
    assert command == [
        "codex", "exec",
        "-c", "service_tier=priority",
        "-c", "shell_environment_policy.inherit=all",
        "-c", f'shell_environment_policy.set.ALPHA_DATA_ROOT="{resolved}"',
        "-c", f'sandbox_workspace_write.writable_roots=["{resolved}"]',
        "--sandbox", "workspace-write", "-",
    ]
    assert "--full-auto" not in command


def test_codex_grants_data_root_sandbox_access_and_env(tmp_path, monkeypatch) -> None:
    # The data root lives outside the git worktree; without the writable-roots
    # grant + env injection, the workspace-write sandbox blocks it and
    # data-dependent phases report "ALPHA_DATA_ROOT is not set" / read-only FS.
    monkeypatch.delenv("FRONTIER_MOCK_PROVIDERS", raising=False)
    monkeypatch.setenv("FRONTIER_CODEX_CMD", "codex")
    monkeypatch.setenv("FRONTIER_CODEX_SANDBOX", "workspace-write")
    data_root = tmp_path / "alpha_data" / "alpha_system"
    monkeypatch.setenv("ALPHA_DATA_ROOT", str(data_root))
    config = load_provider_config(tmp_path)
    resolved = str(data_root.resolve())

    assert config.codex_data_root == data_root.resolve()
    assert resolved in config.codex_sandbox_writable_roots

    # The env var is force-injected into the driver process too, so even a
    # launcher that forgot to export it leaves the tree consistent.
    monkeypatch.delenv("ALPHA_DATA_ROOT", raising=False)
    command = CodexProviderAdapter(config).build_command("prompt")
    assert f'shell_environment_policy.set.ALPHA_DATA_ROOT="{resolved}"' in command
    assert f'sandbox_workspace_write.writable_roots=["{resolved}"]' in command


def test_codex_data_root_defaults_when_env_unset(tmp_path, monkeypatch) -> None:
    # With neither ALPHA_DATA_ROOT nor providers.codex.data_root set, the grant
    # still resolves to the repo default (~/alpha_data/alpha_system) so the
    # sandbox access is robust to a forgotten export.
    monkeypatch.delenv("FRONTIER_MOCK_PROVIDERS", raising=False)
    monkeypatch.delenv("ALPHA_DATA_ROOT", raising=False)
    monkeypatch.setenv("FRONTIER_CODEX_SANDBOX", "workspace-write")
    config = load_provider_config(tmp_path)

    from pathlib import Path

    assert config.codex_data_root == (Path("~/alpha_data/alpha_system").expanduser().resolve())
    assert config.codex_sandbox_writable_roots == (str(config.codex_data_root),)


def test_codex_readonly_sandbox_omits_writable_roots(tmp_path, monkeypatch) -> None:
    # writable_roots only applies to workspace-write; read-only must not emit it.
    monkeypatch.delenv("FRONTIER_MOCK_PROVIDERS", raising=False)
    monkeypatch.setenv("FRONTIER_CODEX_CMD", "codex")
    monkeypatch.setenv("FRONTIER_CODEX_SANDBOX", "read-only")
    monkeypatch.setenv("ALPHA_DATA_ROOT", str(tmp_path / "data"))
    config = load_provider_config(tmp_path)

    command = CodexProviderAdapter(config).build_command("prompt")
    assert not any("writable_roots" in part for part in command)
    assert command[-3:] == ["--sandbox", "read-only", "-"]


def test_codex_prompt_uses_stdin_for_large_prompts(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("FRONTIER_MOCK_PROVIDERS", raising=False)
    monkeypatch.setenv("FRONTIER_CODEX_CMD", "codex")
    monkeypatch.setenv("FRONTIER_CODEX_SANDBOX", "workspace-write")
    monkeypatch.setenv("ALPHA_DATA_ROOT", str(tmp_path / "alpha_data" / "alpha_system"))
    config = load_provider_config(tmp_path)
    runner = RecordingRunner()
    prompt = "execute\n" + ("x" * 200_000)

    response = CodexProviderAdapter(config, runner).run_prompt(prompt)

    assert response.ok
    command, kwargs = runner.calls[0]
    assert command[:2] == ["codex", "exec"]
    assert command[-3:] == ["--sandbox", "workspace-write", "-"]
    assert kwargs["stdin_text"] == prompt
    assert prompt not in command
    assert sum(len(part) for part in command) < 1000


def test_provider_usage_limits_classify_as_waiting_limit_statuses() -> None:
    samples = [
        "usage limit reached",
        "rate limit exceeded",
        "quota exceeded",
        "5-hour limit resets at 12:00",
        "too many requests 429 retry after 60",
        "Claude Code usage limit reached",
        "Codex limit reached",
    ]

    for sample in samples:
        assert classify_provider_nonzero("provider", "", sample, 1) == WAITING_PROVIDER_LIMIT
        assert classify_provider_nonzero("claude", "", sample, 1) == WAITING_CLAUDE_LIMIT
        assert classify_provider_nonzero("codex", "", sample, 1) == WAITING_CODEX_LIMIT


def test_generic_provider_nonzero_remains_blocked() -> None:
    assert classify_provider_nonzero("codex", "", "syntax error", 1) == PROVIDER_BLOCKED
    assert classify_provider_nonzero("claude", "", "connection reset by peer", 1) == PROVIDER_BLOCKED
