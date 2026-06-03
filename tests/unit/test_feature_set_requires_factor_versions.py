from __future__ import annotations

import pytest

from alpha_system.experiments.feature_sets import FeatureSetError, FeatureSetSpec, LabelSpec


def test_feature_set_requires_factor_versions() -> None:
    payload = _feature_set_payload()
    payload.pop("factor_versions")

    with pytest.raises(FeatureSetError, match="factor_versions"):
        FeatureSetSpec.from_mapping(payload, label_spec=_label_spec())


def test_feature_set_rejects_empty_factor_versions() -> None:
    payload = _feature_set_payload()
    payload["factor_versions"] = {}

    with pytest.raises(FeatureSetError, match="factor_versions"):
        FeatureSetSpec.from_mapping(payload, label_spec=_label_spec())


def _label_spec() -> LabelSpec:
    return LabelSpec(label_id="forward_return_1", label_version="label:v1")


def _feature_set_payload() -> dict[str, object]:
    return {
        "feature_set_id": "fixture",
        "data_version": "data:v1",
        "factor_versions": {"momentum_3": "factor:v1"},
        "features": [{"factor_id": "momentum_3", "factor_version": "factor:v1"}],
    }
