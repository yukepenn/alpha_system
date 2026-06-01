"""Safe subprocess runner for Frontier runtime tools.

The runner is intentionally small: no shell execution, bounded timeouts,
captured output, and optional artifact files for later review.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TIMEOUT_SECONDS = 600
TIMEOUT_RETURN_CODE = 124

DESTRUCTIVE_COMMAND_PREFIXES: tuple[tuple[str, ...], ...] = (
    ("git", "reset", "--hard"),
    ("git", "clean", "-fd"),
    ("git", "clean", "-fdx"),
    ("git", "push", "--force"),
    ("git", "push", "-f"),
    ("rm", "-rf"),
    ("rm", "-fr"),
)


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    return_code: int
    stdout: str
    stderr: str
    duration_ms: int
    timed_out: bool = False
    cwd: str | None = None
    stdout_path: str | None = None
    stderr_path: str | None = None
    result_path: str | None = None

    @property
    def returncode(self) -> int:
        """Compatibility alias for subprocess.CompletedProcess-style callers."""

        return self.return_code

    @property
    def ok(self) -> bool:
        return self.return_code == 0 and not self.timed_out


def _normalize_command(command: Sequence[str]) -> list[str]:
    if isinstance(command, (str, bytes)):
        raise TypeError("CommandRunner requires a sequence of arguments, not a shell string.")
    normalized = [str(part) for part in command]
    if not normalized:
        raise ValueError("CommandRunner requires a non-empty command.")
    return normalized


def _matches_prefix(command: Sequence[str], prefix: Sequence[str]) -> bool:
    return len(command) >= len(prefix) and tuple(command[: len(prefix)]) == tuple(prefix)


def assert_safe_command(command: Sequence[str]) -> None:
    normalized = _normalize_command(command)
    for prefix in DESTRUCTIVE_COMMAND_PREFIXES:
        if _matches_prefix(normalized, prefix):
            raise ValueError(f"Refusing destructive command: {' '.join(normalized)}")
    if len(normalized) >= 3 and normalized[:2] == ["git", "add"] and normalized[2] in {".", "-A"}:
        raise ValueError(f"Refusing broad git staging command: {' '.join(normalized)}")


def _safe_artifact_stem(value: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip(".-")
    return stem[:80] or "command"


class CommandRunner:
    """Run commands with captured output and optional artifact persistence."""

    def __init__(self, root: Path | None = None, artifact_dir: Path | None = None) -> None:
        self.root = (root or ROOT).resolve()
        self.artifact_dir = artifact_dir

    def _resolve_cwd(self, cwd: Path | str | None) -> Path:
        if cwd is None:
            return self.root
        candidate = Path(cwd)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        return candidate.resolve()

    def _artifact_paths(self, prefix: str) -> tuple[Path, Path, Path] | tuple[None, None, None]:
        if self.artifact_dir is None:
            return None, None, None
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        stem = _safe_artifact_stem(prefix)
        return (
            self.artifact_dir / f"{stem}.stdout.txt",
            self.artifact_dir / f"{stem}.stderr.txt",
            self.artifact_dir / f"{stem}.result.json",
        )

    def run(
        self,
        command: Sequence[str],
        *,
        cwd: Path | str | None = None,
        env: Mapping[str, str] | None = None,
        timeout_seconds: int | float | None = None,
        artifact_prefix: str | None = None,
    ) -> CommandResult:
        normalized = _normalize_command(command)
        assert_safe_command(normalized)
        resolved_cwd = self._resolve_cwd(cwd)
        merged_env = os.environ.copy()
        if env:
            merged_env.update({str(key): str(value) for key, value in env.items()})

        started = time.monotonic()
        stdout = ""
        stderr = ""
        return_code = 0
        timed_out = False
        timeout = timeout_seconds if timeout_seconds is not None else DEFAULT_TIMEOUT_SECONDS

        try:
            completed = subprocess.run(
                normalized,
                cwd=resolved_cwd,
                env=merged_env,
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
            stdout = completed.stdout
            stderr = completed.stderr
            return_code = completed.returncode
        except subprocess.TimeoutExpired as error:
            stdout = error.stdout or ""
            stderr = error.stderr or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", errors="replace")
            if isinstance(stderr, bytes):
                stderr = stderr.decode("utf-8", errors="replace")
            stderr = (stderr + "\n" if stderr else "") + f"Command timed out after {timeout} seconds."
            return_code = TIMEOUT_RETURN_CODE
            timed_out = True
        except FileNotFoundError as error:
            stdout = ""
            stderr = str(error)
            return_code = 127

        duration_ms = int((time.monotonic() - started) * 1000)
        result = CommandResult(
            command=normalized,
            return_code=return_code,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
            timed_out=timed_out,
            cwd=str(resolved_cwd),
        )

        if artifact_prefix:
            stdout_path, stderr_path, result_path = self._artifact_paths(artifact_prefix)
            if stdout_path and stderr_path and result_path:
                stdout_path.write_text(stdout, encoding="utf-8")
                stderr_path.write_text(stderr, encoding="utf-8")
                result_data = asdict(result)
                result_data["stdout_path"] = str(stdout_path)
                result_data["stderr_path"] = str(stderr_path)
                result_data["result_path"] = str(result_path)
                result_path.write_text(json.dumps(result_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                result = CommandResult(
                    **{
                        **asdict(result),
                        "stdout_path": str(stdout_path),
                        "stderr_path": str(stderr_path),
                        "result_path": str(result_path),
                    }
                )

        return result
