from __future__ import annotations

import pytest

from alpha_system.experiments.feature_sets import FeatureSetError, FeatureSetSpec, LabelSpec


def test_label_id_cannot_be_feature() -> None:
    with pytest.raises(FeatureSetError, match="label ids"):
        FeatureSetSpec.from_mapping(
            {
                "feature_set_id": "leak",
                "data_version": "data:v1",
                "factor_versions": {"forward_return_1": "factor:v1"},
                "features": [{"factor_id": "forward_return_1", "factor_version": "factor:v1"}],
            },
            label_spec=LabelSpec(label_id="forward_return_1", label_version="label:v1"),
        )


def test_label_source_cannot_be_feature() -> None:
    with pytest.raises(FeatureSetError, match="labels cannot"):
        FeatureSetSpec.from_mapping(
            {
                "feature_set_id": "leak",
                "data_version": "data:v1",
                "factor_versions": {"momentum_3": "factor:v1"},
                "features": [
                    {
                        "factor_id": "momentum_3",
                        "factor_version": "factor:v1",
                        "source": "label",
                    }
                ],
            },
            label_spec=LabelSpec(label_id="forward_return_1", label_version="label:v1"),
        )
