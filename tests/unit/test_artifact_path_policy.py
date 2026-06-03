from __future__ import annotations

from alpha_system.experiments.artifact_manifest import classify_artifact_path


def test_commit_eligible_doc_path_is_commit_safe() -> None:
    policy = classify_artifact_path("docs/EXPERIMENT_REGISTRY.md")

    assert policy.commit_safe is True
    assert policy.commit_eligible is True
    assert policy.local_only is False
    assert policy.forbidden is False


def test_local_artifact_path_is_not_commit_safe_and_warns() -> None:
    policy = classify_artifact_path("artifacts/run-1/summary.json")

    assert policy.local_only is True
    assert policy.commit_eligible is False
    assert policy.commit_safe is False
    assert "artifact path is not commit-safe" in policy.warnings


def test_forbidden_paths_are_detected() -> None:
    windows_policy = classify_artifact_path("/mnt/c/Users/me/output.sqlite")
    traversal_policy = classify_artifact_path("../metadata/registry.sqlite3")

    assert windows_policy.forbidden is True
    assert traversal_policy.forbidden is True
