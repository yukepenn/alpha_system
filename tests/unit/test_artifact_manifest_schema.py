from __future__ import annotations

from pathlib import Path

import pytest

from alpha_system.core.registry import connect_registry, init_registry
from alpha_system.experiments.artifact_manifest import (
    ArtifactManifestEntry,
    ArtifactManifestError,
    insert_artifact_manifest,
    read_artifact_manifest,
)


def test_artifact_manifest_entry_schema_and_registry_mapping(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    init_registry(registry_path)
    entry = ArtifactManifestEntry(
        artifact_id="artifact-1",
        run_id="run-1",
        artifact_type="summary",
        relative_path="docs/EXPERIMENT_REGISTRY.md",
        content_hash="hash",
        size_bytes=12,
        created_at="2026-06-02T01:20:07Z",
    )

    with connect_registry(registry_path) as connection:
        insert_artifact_manifest(connection, entry, run_table="study_runs")
        rows = read_artifact_manifest(connection, run_id="run-1")

    assert rows[0]["artifact_id"] == "artifact-1"
    assert rows[0]["artifact_path"] == "docs/EXPERIMENT_REGISTRY.md"
    assert rows[0]["metadata"]["artifact_type"] == "summary"
    assert rows[0]["metadata"]["size_bytes"] == 12
    assert rows[0]["metadata"]["commit_eligible"] is True


def test_artifact_manifest_requires_relative_path() -> None:
    with pytest.raises(ArtifactManifestError, match="relative"):
        ArtifactManifestEntry(
            artifact_id="artifact-1",
            run_id="run-1",
            artifact_type="summary",
            relative_path="/tmp/output.json",
        )
