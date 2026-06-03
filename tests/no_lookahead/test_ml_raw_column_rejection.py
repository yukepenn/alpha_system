from __future__ import annotations

import pytest

from alpha_system.experiments.feature_sets import FeatureSetError, FeatureSetSpec, LabelSpec


def test_ml_feature_set_rejects_raw_columns() -> None:
    with pytest.raises(FeatureSetError, match="raw ad hoc"):
        FeatureSetSpec.from_mapping(
            {
                "feature_set_id": "raw",
                "data_version": "data:v1",
                "factor_versions": {"momentum_3": "factor:v1"},
                "features": [
                    {
                        "factor_id": "momentum_3",
                        "factor_version": "factor:v1",
                        "raw_column": "close",
                    }
                ],
            },
            label_spec=LabelSpec(label_id="forward_return_1", label_version="label:v1"),
        )


def test_ml_feature_set_rejects_raw_sources() -> None:
    with pytest.raises(FeatureSetError, match="versioned factor"):
        FeatureSetSpec.from_mapping(
            {
                "feature_set_id": "raw",
                "data_version": "data:v1",
                "factor_versions": {"momentum_3": "factor:v1"},
                "features": [
                    {
                        "factor_id": "momentum_3",
                        "factor_version": "factor:v1",
                        "source": "raw",
                    }
                ],
            },
            label_spec=LabelSpec(label_id="forward_return_1", label_version="label:v1"),
        )
