from __future__ import annotations

import pytest

from alpha_system.experiments.feature_sets import FeatureSetError, FeatureSetSpec, LabelSpec


def test_feature_set_schema_normalizes_factor_features() -> None:
    spec = FeatureSetSpec.from_mapping(
        {
            "feature_set_id": "fixture",
            "data_version": "data:v1",
            "factor_versions": {"momentum_3": "factor:v1"},
            "features": [{"factor_id": "momentum_3"}],
            "instruments": ["SYNTH"],
        },
        label_spec=LabelSpec(label_id="forward_return_1", label_version="label:v1"),
    )

    assert spec.feature_ids == ("momentum_3",)
    assert spec.features[0].factor_version == "factor:v1"
    assert spec.to_dict()["instruments"] == ["SYNTH"]


def test_feature_set_rejects_feature_version_mismatch() -> None:
    with pytest.raises(FeatureSetError, match="does not match"):
        FeatureSetSpec.from_mapping(
            {
                "feature_set_id": "fixture",
                "data_version": "data:v1",
                "factor_versions": {"momentum_3": "factor:v1"},
                "features": [{"factor_id": "momentum_3", "factor_version": "factor:v2"}],
            },
            label_spec=LabelSpec(label_id="forward_return_1", label_version="label:v1"),
        )
