from __future__ import annotations

import pytest

from alpha_system.runtime.artifact_policy import (
    CURATED_SUMMARY_COMMIT_SIZE_LIMIT_BYTES,
    RuntimeArtifactDescriptor,
    RuntimeArtifactDisposition,
    RuntimeArtifactPolicyError,
    classify_runtime_artifact,
    runtime_artifact_commit_allowed,
    runtime_artifact_manifest_flags,
    validate_commit_allowed,
)


@pytest.mark.parametrize(
    ("kind", "location", "forbidden_class"),
    [
        ("parquet", "runtime/diagnostics.parquet", "value_bearing"),
        ("feature_values", "summaries/features.json", "value_bearing"),
        ("summary", "runtime/labels.arrow", "heavy_artifact"),
        ("provider_response", "summaries/provider.json", "forbidden_output"),
        ("summary", "metadata/runtime.sqlite", "metadata_path"),
        ("summary", "logs/runtime.log", "logs_path"),
        ("summary", "$ALPHA_DATA_ROOT/runtime/cache/summary.json", "alpha_data_root_path"),
    ],
)
def test_heavy_value_provider_db_log_and_cache_outputs_are_local_only(
    kind: str,
    location: str,
    forbidden_class: str,
) -> None:
    decision = classify_runtime_artifact(
        {
            "kind": kind,
            "location": location,
            "size_bytes": 128,
            "curated": True,
            "row_free": True,
        }
    )

    assert decision.disposition is RuntimeArtifactDisposition.LOCAL_ONLY
    assert decision.commit_allowed is False
    assert decision.local_only is True
    assert forbidden_class in decision.forbidden_classes


def test_only_small_curated_row_free_summaries_are_commit_allowed() -> None:
    descriptor = RuntimeArtifactDescriptor(
        kind="summary",
        location="summaries/runtime-summary.json",
        size_bytes=CURATED_SUMMARY_COMMIT_SIZE_LIMIT_BYTES,
        curated=True,
        row_free=True,
    )

    decision = classify_runtime_artifact(descriptor)

    assert decision.disposition is RuntimeArtifactDisposition.COMMIT_ALLOWED
    assert decision.commit_allowed is True
    assert decision.local_only is False
    assert runtime_artifact_commit_allowed(descriptor) is True
    assert runtime_artifact_manifest_flags(descriptor) == {
        "commit_allowed": True,
        "local_only": False,
    }
    validate_commit_allowed(descriptor)


@pytest.mark.parametrize(
    "descriptor",
    [
        RuntimeArtifactDescriptor(
            kind="summary",
            location="summaries/not-curated.json",
            size_bytes=128,
            curated=False,
            row_free=True,
        ),
        RuntimeArtifactDescriptor(
            kind="summary",
            location="summaries/row-bearing.json",
            size_bytes=128,
            curated=True,
            row_count=1,
        ),
        RuntimeArtifactDescriptor(
            kind="summary",
            location="summaries/large.json",
            size_bytes=CURATED_SUMMARY_COMMIT_SIZE_LIMIT_BYTES + 1,
            curated=True,
            row_free=True,
        ),
        RuntimeArtifactDescriptor(
            kind="raw_report",
            location="summaries/raw-report.json",
            size_bytes=128,
            curated=True,
            row_free=True,
        ),
    ],
)
def test_non_curated_row_bearing_large_or_non_summary_outputs_are_local_only(
    descriptor: RuntimeArtifactDescriptor,
) -> None:
    decision = classify_runtime_artifact(descriptor)

    assert decision.commit_allowed is False
    assert decision.local_only is True
    with pytest.raises(RuntimeArtifactPolicyError):
        validate_commit_allowed(descriptor)


def test_runs_path_is_never_commit_eligible_even_for_curated_row_free_summary() -> None:
    decision = classify_runtime_artifact(
        RuntimeArtifactDescriptor(
            kind="summary",
            location="runs/run_rt_p19/summary.json",
            size_bytes=128,
            curated=True,
            row_free=True,
        )
    )

    assert decision.commit_allowed is False
    assert "runs_path" in decision.forbidden_classes


def test_descriptor_mapping_can_use_row_count_zero_as_row_free_marker() -> None:
    decision = classify_runtime_artifact(
        {
            "kind": "diagnostic_summary",
            "path": "summaries/diagnostics.json",
            "bytes": 256,
            "summary_curated": True,
            "row_count": 0,
        }
    )

    assert decision.commit_allowed is True
