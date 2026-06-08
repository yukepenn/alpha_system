"""Tests for the secret_scan high-confidence content scan."""

from __future__ import annotations

from pathlib import Path

from tools.hooks import secret_scan

ROOT = Path(__file__).resolve().parents[2]


def _write(tmp_path: Path, name: str, body: str) -> str:
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return str(p)


def test_private_key_content_blocked_even_with_innocuous_name(tmp_path) -> None:
    path = _write(tmp_path, "config_loader.py",
                  "-----BEGIN OPENSSH PRIVATE KEY-----\nabc\n-----END OPENSSH PRIVATE KEY-----\n")
    assert secret_scan.has_secret_content(path) is True
    assert secret_scan.main([path]) == 1


def test_aws_and_github_and_slack_tokens_blocked(tmp_path) -> None:
    for body in ('k="AKIAIOSFODNN7EXAMPLE"\n', "t='xoxb-1234567890-abcdef'\n",
                 "p='ghp_" + "a" * 36 + "'\n"):
        path = _write(tmp_path, "f.py", body)
        assert secret_scan.main([path]) == 1


def test_normal_source_not_blocked(tmp_path) -> None:
    path = _write(tmp_path, "ok.py", "def f():\n    return 'returns and pnl are fine words'\n")
    assert secret_scan.has_secret_content(path) is False
    assert secret_scan.main([path]) == 0


def test_binary_and_missing_files_fail_open(tmp_path) -> None:
    # Skipped suffixes and nonexistent paths never raise and never match.
    assert secret_scan.has_secret_content(str(tmp_path / "nope.parquet")) is False
    assert secret_scan.has_secret_content(str(tmp_path / "missing.py")) is False


def test_repo_tree_is_clean_under_content_scan() -> None:
    # Regression guard: the live tree must contain no high-confidence secret material.
    import subprocess

    files = subprocess.run(
        ["git", "ls-files", "*.py", "*.md", "*.yaml", "*.yml", "*.toml", "*.json", "*.sh"],
        cwd=ROOT, text=True, capture_output=True, check=False,
    ).stdout.split()
    offenders = [f for f in files if secret_scan.has_secret_content(str(ROOT / f))]
    assert offenders == [], f"secret material in tracked files: {offenders}"
