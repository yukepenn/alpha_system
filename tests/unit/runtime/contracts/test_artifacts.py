from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from alpha_system.runtime.contracts.artifacts import (
    CURATED_SUMMARY_COMMIT_SIZE_LIMIT_BYTES,
    RuntimeArtifactContractError,
    RuntimeArtifactEntry,
    RuntimeArtifactManifest,
)


def test_runtime_artifact_manifest_defaults_local_only_and_hashable() -> None:
    manifest = RuntimeArtifactManifest(
        run_id="run_rt_p05_fixture",
        entries=[
            {
                "artifact_id": "diagnostics_summary",
                "kind": "diagnostic_summary",
                "location": "summaries/diagnostics.json",
                "content_hash": "a" * 64,
                "size_bytes": 1200,
            }
        ],
    )

    entry = manifest.entries[0]
    assert entry.local_only is True
    assert entry.commit_allowed is False
    assert hash(manifest)
    assert manifest.to_dict()["value_free"] is True
    with pytest.raises(FrozenInstanceError):
        entry.size_bytes = 0  # type: ignore[misc]


@pytest.mark.parametrize(
    ("kind", "location"),
    [
        ("parquet", "runtime/diagnostics.parquet"),
        ("feature_values", "summaries/features.json"),
        ("diagnostic_summary", "runtime/labels.arrow"),
        ("value_table", "summaries/value_table.json"),
    ],
)
def test_heavy_or_value_bearing_artifact_cannot_be_commit_allowed(
    kind: str,
    location: str,
) -> None:
    with pytest.raises(RuntimeArtifactContractError):
        RuntimeArtifactEntry(
            artifact_id="heavy_output",
            kind=kind,
            location=location,
            content_hash="b" * 64,
            size_bytes=128,
            commit_allowed=True,
        )


@pytest.mark.parametrize(
    "location",
    [
        "runs/run_rt_p05_fixture/diagnostics.json",
        "data/raw/provider.json",
        "data/cache/runtime-summary.json",
        "metadata/runtime.sqlite",
        "artifacts/runtime-summary.json",
    ],
)
def test_non_local_artifact_cannot_point_under_never_commit_location(location: str) -> None:
    with pytest.raises(RuntimeArtifactContractError):
        RuntimeArtifactEntry(
            artifact_id="forbidden_location",
            kind="summary",
            location=location,
            content_hash="c" * 64,
            size_bytes=128,
            local_only=False,
        )


def test_only_tiny_curated_row_free_summaries_can_be_commit_allowed() -> None:
    allowed = RuntimeArtifactEntry(
        artifact_id="curated_summary",
        kind="summary",
        location="summaries/runtime-summary.json",
        content_hash="d" * 64,
        size_bytes=CURATED_SUMMARY_COMMIT_SIZE_LIMIT_BYTES,
        commit_allowed=True,
    )

    assert allowed.commit_allowed is True

    with pytest.raises(RuntimeArtifactContractError):
        RuntimeArtifactEntry(
            artifact_id="large_summary",
            kind="summary",
            location="summaries/runtime-summary-large.json",
            content_hash="e" * 64,
            size_bytes=CURATED_SUMMARY_COMMIT_SIZE_LIMIT_BYTES + 1,
            commit_allowed=True,
        )

    with pytest.raises(RuntimeArtifactContractError):
        RuntimeArtifactEntry(
            artifact_id="unsupported_kind",
            kind="raw_report",
            location="summaries/raw-report.json",
            content_hash="f" * 64,
            size_bytes=128,
            commit_allowed=True,
        )


def test_artifact_manifest_rejects_inline_value_fields() -> None:
    with pytest.raises(RuntimeArtifactContractError):
        RuntimeArtifactManifest(
            run_id="run_rt_p05_fixture",
            entries=[
                {
                    "artifact_id": "bad_entry",
                    "kind": "summary",
                    "location": "summaries/bad.json",
                    "content_hash": "0" * 64,
                    "size_bytes": 12,
                    "rows": [{"not": "allowed"}],
                }
            ],
        )
