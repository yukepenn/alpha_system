from __future__ import annotations

from pathlib import Path

from alpha_system.core.hashing import hash_file
from alpha_system.experiments.artifact_manifest import artifact_entry_from_file


def test_artifact_manifest_captures_hash_and_size(tmp_path: Path) -> None:
    artifact = tmp_path / "manifest.json"
    artifact.write_text('{"ok": true}\n', encoding="utf-8")

    entry = artifact_entry_from_file(
        run_id="run-1",
        artifact_type="summary",
        path=artifact,
        root=tmp_path,
        created_at="2026-06-02T01:20:07Z",
    )

    assert entry.relative_path == "manifest.json"
    assert entry.content_hash == hash_file(artifact)
    assert entry.size_bytes == artifact.stat().st_size
