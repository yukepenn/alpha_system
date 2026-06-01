from __future__ import annotations

from tools.frontier.command_runner import CommandResult
from tools.frontier.provider_adapters import ClaudeProviderAdapter, CodexProviderAdapter, MockProviderAdapter
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
    config = load_provider_config(tmp_path)

    command = CodexProviderAdapter(config).build_command("prompt")

    assert command == ["codex", "exec", "--sandbox", "workspace-write", "-"]
    assert "--full-auto" not in command


def test_codex_prompt_uses_stdin_for_large_prompts(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("FRONTIER_MOCK_PROVIDERS", raising=False)
    monkeypatch.setenv("FRONTIER_CODEX_CMD", "codex")
    monkeypatch.setenv("FRONTIER_CODEX_SANDBOX", "workspace-write")
    config = load_provider_config(tmp_path)
    runner = RecordingRunner()
    prompt = "execute\n" + ("x" * 200_000)

    response = CodexProviderAdapter(config, runner).run_prompt(prompt)

    assert response.ok
    command, kwargs = runner.calls[0]
    assert command == ["codex", "exec", "--sandbox", "workspace-write", "-"]
    assert kwargs["stdin_text"] == prompt
    assert prompt not in command
    assert sum(len(part) for part in command) < 1000
