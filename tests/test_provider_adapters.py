from __future__ import annotations

from tools.frontier.provider_adapters import ClaudeProviderAdapter, CodexProviderAdapter, MockProviderAdapter
from tools.frontier.provider_config import load_provider_config


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

    assert command == ["claude", "-p", "prompt"]


def test_codex_command_uses_workspace_write_sandbox(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("FRONTIER_MOCK_PROVIDERS", raising=False)
    monkeypatch.setenv("FRONTIER_CODEX_CMD", "codex")
    monkeypatch.setenv("FRONTIER_CODEX_SANDBOX", "workspace-write")
    config = load_provider_config(tmp_path)

    command = CodexProviderAdapter(config).build_command("prompt")

    assert command == ["codex", "exec", "--sandbox", "workspace-write", "prompt"]
    assert "--full-auto" not in command
