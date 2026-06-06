from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from alpha_system.runtime.contracts.manifest import (
    FeaturePackVersionRef,
    LabelPackVersionRef,
    StudyRunManifest,
    StudyRunManifestContractError,
)


def test_study_run_manifest_is_immutable_hashable_and_deterministic() -> None:
    manifest = _manifest()
    same_manifest = _manifest()

    assert manifest.manifest_hash == same_manifest.manifest_hash
    assert manifest.manifest_id == same_manifest.manifest_id
    assert hash(manifest)
    assert manifest.to_dict()["value_free"] is True
    with pytest.raises(FrozenInstanceError):
        manifest.config_hash = "changed"  # type: ignore[misc]


def test_manifest_hash_uses_reproducibility_references_not_run_path() -> None:
    manifest = _manifest(run_id="run_rt_p05_a")
    same_references_different_run = _manifest(run_id="run_rt_p05_b")

    assert manifest.run_id != same_references_different_run.run_id
    assert manifest.manifest_hash == same_references_different_run.manifest_hash


def test_manifest_hash_rejects_runs_path_references() -> None:
    with pytest.raises(StudyRunManifestContractError):
        _manifest(dataset_lineage_ref="runs/run_rt_p05_fixture/lineage.json")


@pytest.mark.parametrize(
    "overrides",
    [
        {"dataset_version_id": ""},
        {"dataset_version_hash": ""},
        {"dataset_lineage_ref": ""},
        {"code_version": ""},
        {"code_content_hash": ""},
        {"config_version": ""},
        {"config_hash": ""},
        {"feature_pack_versions": []},
        {"label_pack_versions": []},
    ],
)
def test_manifest_missing_version_lineage_is_invalid(overrides: dict[str, object]) -> None:
    with pytest.raises(StudyRunManifestContractError):
        _manifest(**overrides)


def test_manifest_requires_availability_metadata_references() -> None:
    with pytest.raises(StudyRunManifestContractError):
        FeaturePackVersionRef(
            pack_id="feature_pack_v1",
            content_hash="1" * 64,
            lineage_ref="feature_lineage_v1",
            available_ts_ref="timestamp_column",
        )

    with pytest.raises(StudyRunManifestContractError):
        LabelPackVersionRef(
            pack_id="label_pack_v1",
            content_hash="2" * 64,
            lineage_ref="label_lineage_v1",
            label_available_ts_ref="timestamp_column",
        )


def test_manifest_rejects_inline_raw_or_heavy_value_fields() -> None:
    with pytest.raises(StudyRunManifestContractError):
        _manifest(
            feature_pack_versions=[
                {
                    "pack_id": "feature_pack_v1",
                    "content_hash": "1" * 64,
                    "lineage_ref": "feature_lineage_v1",
                    "available_ts_ref": "features.available_ts",
                    "values": [1, 2, 3],
                }
            ]
        )

    payload = _manifest().to_dict()
    assert "values" not in str(payload)
    assert "rows" not in str(payload)


def test_cost_model_version_slot_is_optional_but_pairwise_when_present() -> None:
    assert _manifest(cost_model_version=None, cost_model_hash=None).cost_model_version is None

    with pytest.raises(StudyRunManifestContractError):
        _manifest(cost_model_version="cost_model_v1", cost_model_hash=None)

    with pytest.raises(StudyRunManifestContractError):
        _manifest(cost_model_version=None, cost_model_hash="3" * 64)


def _manifest(**overrides: object) -> StudyRunManifest:
    values: dict[str, object] = {
        "run_id": "run_rt_p05_fixture",
        "dataset_version_id": "dsv_synthetic_runtime_fixture_v1",
        "dataset_version_hash": "0" * 64,
        "dataset_lineage_ref": "dataset_lineage_fixture_v1",
        "dataset_admissibility_state": "VERSIONED",
        "feature_pack_versions": [
            {
                "pack_id": "feature_pack_v1",
                "content_hash": "1" * 64,
                "lineage_ref": "feature_lineage_v1",
                "available_ts_ref": "features.available_ts",
            }
        ],
        "label_pack_versions": [
            {
                "pack_id": "label_pack_v1",
                "content_hash": "2" * 64,
                "lineage_ref": "label_lineage_v1",
                "label_available_ts_ref": "labels.label_available_ts",
            }
        ],
        "code_version": "git:abcdef1234567890",
        "code_content_hash": "3" * 64,
        "config_version": "config_runtime_fixture_v1",
        "config_hash": "4" * 64,
    }
    values.update(overrides)
    return StudyRunManifest(**values)  # type: ignore[arg-type]
