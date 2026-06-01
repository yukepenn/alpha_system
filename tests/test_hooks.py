from __future__ import annotations

from pathlib import Path

from tools.hooks import artifact_guard, forbidden_pattern_guard, secret_scan, test_tamper_guard


def test_secret_scan_blocks_secret_like_paths() -> None:
    assert secret_scan.is_forbidden(".env")
    assert secret_scan.is_forbidden("credentials/token.txt")
    assert not secret_scan.is_forbidden("tools/hooks/secret_scan.py")


def test_artifact_guard_allows_curated_summaries() -> None:
    assert artifact_guard.forbidden("data/raw/input.csv")
    assert artifact_guard.forbidden("models/model.onnx")
    assert not artifact_guard.forbidden("reviews/summary.json")


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
