from __future__ import annotations

from pathlib import Path

import pytest

from alpha_system.runtime.cache_policy import (
    RuntimeCacheLineage,
    RuntimeCacheLookupState,
    RuntimeCachePolicy,
    RuntimeCachePolicyError,
    RuntimeCacheStorageKind,
)


def test_cache_key_is_deterministic_for_same_lineage_and_scope() -> None:
    policy = RuntimeCachePolicy()
    lineage = _lineage()

    first = policy.derive_cache_key(lineage=lineage, summary_kind="summary")
    second = policy.derive_cache_key(lineage=lineage, summary_kind="summary")

    assert first == second
    assert first.key.startswith("rcache_")
    assert first.lineage_hash == lineage.lineage_hash


@pytest.mark.parametrize(
    "overrides",
    [
        {"dataset_version_hash": "9" * 64},
        {
            "feature_pack_versions": [
                {"name": "feature_pack", "version": "feature_pack_v2", "content_hash": "1" * 64}
            ]
        },
        {
            "label_pack_versions": [
                {"name": "label_pack", "version": "label_pack_v2", "content_hash": "2" * 64}
            ]
        },
        {"code_content_hash": "8" * 64},
        {"config_hash": "7" * 64},
        {"run_scope": {"partition": "locked_test"}},
    ],
)
def test_cache_key_changes_when_any_lineage_component_changes(
    overrides: dict[str, object],
) -> None:
    policy = RuntimeCachePolicy()
    original = policy.derive_cache_key(lineage=_lineage(), summary_kind="summary")
    changed = policy.derive_cache_key(
        lineage=_lineage(**overrides),
        summary_kind="summary",
    )

    assert changed.key != original.key
    assert changed.lineage_hash != original.lineage_hash


def test_lookup_classifies_hit_miss_and_stale_without_reading_cache_contents() -> None:
    policy = RuntimeCachePolicy()
    lineage = _lineage()
    metadata = policy.metadata_for(lineage=lineage, summary_kind="summary")

    hit = policy.lookup(lineage=lineage, summary_kind="summary", existing_metadata=metadata)
    miss = policy.lookup(lineage=lineage, summary_kind="summary", existing_metadata=None)
    stale = policy.lookup(
        lineage=_lineage(config_version="runtime_config_v2"),
        summary_kind="summary",
        existing_metadata=metadata,
    )

    assert hit.state is RuntimeCacheLookupState.HIT
    assert hit.hit is True
    assert miss.state is RuntimeCacheLookupState.MISS
    assert miss.miss is True
    assert stale.state is RuntimeCacheLookupState.STALE
    assert stale.stale is True
    assert "lineage_changed" in stale.reasons


def test_cache_root_resolves_under_alpha_data_root_outside_repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = tmp_path / "repo"
    alpha_data_root = tmp_path / "alpha_data_root"
    monkeypatch.setenv("ALPHA_DATA_ROOT", str(alpha_data_root))

    root = RuntimeCachePolicy().resolve_storage_root(repo_root=repo_root)

    assert root.storage_kind is RuntimeCacheStorageKind.ALPHA_DATA_ROOT
    assert root.local_only is True
    assert root.commit_allowed is False
    assert root.path == alpha_data_root / "runtime" / "cache" / "derived_summaries"
    assert not _is_relative_to(root.path, repo_root)


def test_cache_root_rejects_in_repo_alpha_data_root(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    in_repo_root = repo_root / "data" / "cache"

    with pytest.raises(RuntimeCachePolicyError):
        RuntimeCachePolicy().resolve_storage_root(
            alpha_data_root=in_repo_root,
            repo_root=repo_root,
        )


def test_run_artifact_cache_root_is_explicit_local_only(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    run_root = repo_root / "runs" / "run_rt_p19"

    root = RuntimeCachePolicy().resolve_storage_root(run_root=run_root, repo_root=repo_root)

    assert root.storage_kind is RuntimeCacheStorageKind.RUN_ARTIFACTS
    assert root.local_only is True
    assert root.commit_allowed is False
    assert "runs" in root.path.parts


def test_cache_policy_rejects_value_bearing_summary_kinds() -> None:
    with pytest.raises(RuntimeCachePolicyError):
        RuntimeCachePolicy().derive_cache_key(
            lineage=_lineage(),
            summary_kind="feature_values",
        )


def _lineage(**overrides: object) -> RuntimeCacheLineage:
    values: dict[str, object] = {
        "dataset_version_id": "dsv_synthetic_runtime_fixture_v1",
        "dataset_version_hash": "0" * 64,
        "feature_pack_versions": [
            {"name": "feature_pack", "version": "feature_pack_v1", "content_hash": "1" * 64}
        ],
        "label_pack_versions": [
            {"name": "label_pack", "version": "label_pack_v1", "content_hash": "2" * 64}
        ],
        "code_version": "git:abcdef1234567890",
        "code_content_hash": "3" * 64,
        "config_version": "runtime_config_v1",
        "config_hash": "4" * 64,
        "run_scope": {"partition": "train", "session": "rth"},
    }
    values.update(overrides)
    return RuntimeCacheLineage(**values)  # type: ignore[arg-type]


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
