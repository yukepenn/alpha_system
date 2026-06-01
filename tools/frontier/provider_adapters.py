"""Provider adapters for Frontier Workflow 2.

Adapters isolate provider command construction from the conductor. Mock mode is
deterministic and never invokes external CLIs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tools.frontier.command_runner import CommandResult, CommandRunner
from tools.frontier.provider_config import ProviderRuntimeConfig, load_provider_config


ROOT = Path(__file__).resolve().parents[2]
CLAUDE_STDIN_INSTRUCTION = "Read the full task from stdin and complete it."


@dataclass(frozen=True)
class ProviderResponse:
    provider: str
    prompt: str
    stdout: str
    stderr: str
    return_code: int
    duration_ms: int
    command: list[str]
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.return_code == 0 and not self.timed_out

    @classmethod
    def from_result(cls, provider: str, prompt: str, result: CommandResult) -> "ProviderResponse":
        return cls(
            provider=provider,
            prompt=prompt,
            stdout=result.stdout,
            stderr=result.stderr,
            return_code=result.return_code,
            duration_ms=result.duration_ms,
            command=result.command,
            timed_out=result.timed_out,
        )


class ProviderAdapter:
    provider_name = "provider"

    def __init__(
        self,
        config: ProviderRuntimeConfig | None = None,
        runner: CommandRunner | None = None,
    ) -> None:
        self.config = config or load_provider_config(ROOT)
        self.runner = runner or CommandRunner(self.config.root)

    def run_prompt(self, prompt: str, *, artifact_prefix: str | None = None) -> ProviderResponse:
        raise NotImplementedError


class MockProviderAdapter(ProviderAdapter):
    provider_name = "mock"

    def run_prompt(self, prompt: str, *, artifact_prefix: str | None = None) -> ProviderResponse:
        del artifact_prefix
        return ProviderResponse(
            provider=self.provider_name,
            prompt=prompt,
            stdout="# Mock Provider Output\n\nFRONTIER_MOCK_PROVIDERS=1; no external CLI was called.\n",
            stderr="",
            return_code=0,
            duration_ms=0,
            command=["mock-provider"],
        )


class ClaudeProviderAdapter(ProviderAdapter):
    provider_name = "claude"

    def build_command(self, prompt: str | None = None) -> list[str]:
        del prompt
        command = [*self.config.claude_cmd, "-p", CLAUDE_STDIN_INSTRUCTION]
        if self.config.claude_output_format:
            command.extend(["--output-format", self.config.claude_output_format])
        return command

    def run_prompt(self, prompt: str, *, artifact_prefix: str | None = None) -> ProviderResponse:
        if self.config.mock_providers:
            return MockProviderAdapter(self.config, self.runner).run_prompt(prompt, artifact_prefix=artifact_prefix)
        result = self.runner.run(
            self.build_command(prompt),
            timeout_seconds=self.config.provider_timeout_seconds,
            artifact_prefix=artifact_prefix,
            stdin_text=prompt,
        )
        return ProviderResponse.from_result(self.provider_name, prompt, result)


class CodexProviderAdapter(ProviderAdapter):
    provider_name = "codex"

    def build_command(self, prompt: str | None = None) -> list[str]:
        del prompt
        return [
            *self.config.codex_cmd,
            "exec",
            "--sandbox",
            self.config.codex_sandbox,
            "-",
        ]

    def run_prompt(self, prompt: str, *, artifact_prefix: str | None = None) -> ProviderResponse:
        if self.config.mock_providers:
            return MockProviderAdapter(self.config, self.runner).run_prompt(prompt, artifact_prefix=artifact_prefix)
        result = self.runner.run(
            self.build_command(prompt),
            timeout_seconds=self.config.provider_timeout_seconds,
            artifact_prefix=artifact_prefix,
            stdin_text=prompt,
        )
        return ProviderResponse.from_result(self.provider_name, prompt, result)
