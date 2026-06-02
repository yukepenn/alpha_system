from __future__ import annotations

import subprocess
from pathlib import Path

from tools import verify
from tools.hooks import artifact_guard, forbidden_pattern_guard, pre_commit, secret_scan, test_tamper_guard


def test_secret_scan_blocks_secret_like_paths() -> None:
    assert secret_scan.is_forbidden(".env")
    assert secret_scan.is_forbidden("credentials/token.txt")
    assert not secret_scan.is_forbidden("tools/hooks/secret_scan.py")


def test_artifact_guard_allows_curated_summaries() -> None:
    assert artifact_guard.forbidden("data/raw/input.csv")
    assert artifact_guard.forbidden("models/model.onnx")
    assert not artifact_guard.forbidden("reviews/summary.json")


def test_artifact_guard_allows_explicit_placeholders() -> None:
    allowed = [
        "data/raw/.gitkeep",
        "data/raw/README.md",
        "data/cache/.gitkeep",
        "data/cache/README.md",
        "data/canonical/.gitkeep",
        "data/factors/README.md",
        "data/labels/README.md",
        "metadata/README.md",
        "artifacts/README.md",
        "artifacts/.gitkeep",
        "artifacts/reports/README.md",
    ]
    assert all(not artifact_guard.forbidden(path) for path in allowed)


def test_artifact_guard_blocks_real_raw_cache_and_model_artifacts() -> None:
    blocked = [
        ".frontier/upgrade_reports/report.json",
        "data/raw/input.csv",
        "data/raw/input.parquet",
        "data/raw/SPY.parquet",
        "data/cache/cache.db",
        "data/cache/cache.sqlite",
        "artifacts/raw/output.csv",
        "artifacts/model.pkl",
        "data/canonical/snapshot.parquet",
        "data/factors/factors.csv",
        "data/labels/labels.csv",
        "metadata/registry.sqlite",
        ".env",
        "secrets.json",
        "runs/run1/state.json",
        "state.sqlite",
        "state.db",
        "state.duckdb",
        "runs/local.log",
        "logs/frontier.log",
        "models/model.onnx",
        "models/model.pt",
        "models/model.pkl",
        "models/model.joblib",
    ]
    assert all(artifact_guard.forbidden(path) for path in blocked)


def test_artifact_verification_ignores_staged_deletions(monkeypatch) -> None:
    commands: list[list[str]] = []

    def fake_run(command, **kwargs):
        commands.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(verify.subprocess, "run", fake_run)

    assert verify.check_artifacts() == 0
    assert ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRTUXB"] in commands


def test_artifact_verification_blocks_staged_forbidden_artifacts(monkeypatch) -> None:
    def fake_run(command, **kwargs):
        stdout = ".frontier/upgrade_reports/report.json\n" if command[1] == "diff" else ""
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(verify.subprocess, "run", fake_run)

    assert verify.check_artifacts() == 1


def test_pre_commit_collects_only_staged_non_deletions(monkeypatch) -> None:
    commands: list[list[str]] = []

    def fake_run(command, **kwargs):
        commands.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="docs/a.md\n", stderr="")

    monkeypatch.setattr(pre_commit.subprocess, "run", fake_run)

    assert pre_commit.staged_files() == ["docs/a.md"]
    assert ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRTUXB"] in commands


def test_forbidden_pattern_guard_allows_policy_docs(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("docs").mkdir()
    path = Path("docs/policy.md")
    path.write_text("Do not use " + "git add" + " .\n", encoding="utf-8")

    assert forbidden_pattern_guard.main([str(path)]) == 0


def test_test_tamper_guard_blocks_skip(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("tests").mkdir()
    path = Path("tests/test_bad.py")
    path.write_text("import pytest\n\n@pytest.mark.skip(reason='bad')\ndef test_bad():\n    assert True\n", encoding="utf-8")

    assert test_tamper_guard.main([str(path)]) == 1
