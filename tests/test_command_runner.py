from __future__ import annotations

import sys

import pytest

from tools.frontier.command_runner import CommandRunner


def test_command_runner_success_writes_artifacts(tmp_path) -> None:
    runner = CommandRunner(tmp_path, tmp_path / "artifacts")
    result = runner.run([sys.executable, "-c", "print('ok')"], artifact_prefix="success")

    assert result.return_code == 0
    assert result.stdout.strip() == "ok"
    assert result.duration_ms >= 0
    assert (tmp_path / "artifacts" / "success.stdout.txt").is_file()
    assert (tmp_path / "artifacts" / "success.stderr.txt").is_file()
    assert (tmp_path / "artifacts" / "success.result.json").is_file()


def test_command_runner_failure() -> None:
    result = CommandRunner().run([sys.executable, "-c", "import sys; sys.exit(7)"])

    assert result.return_code == 7
    assert not result.ok


def test_command_runner_timeout() -> None:
    result = CommandRunner().run(
        [sys.executable, "-c", "import time; time.sleep(2)"],
        timeout_seconds=0.1,
    )

    assert result.return_code == 124
    assert result.timed_out


def test_command_runner_blocks_destructive_command() -> None:
    with pytest.raises(ValueError):
        CommandRunner().run(["git", "reset", "--hard"])
