from __future__ import annotations

from alpha_system.experiments.model_specs import ModelSpec, registered_model_types


def test_model_spec_registration_contains_mvp_baselines() -> None:
    registry = registered_model_types()

    assert registry["linear_baseline"].implemented is True
    assert registry["ridge_baseline"].implemented is True
    assert registry["ic_weighted_score"].implemented is True


def test_model_spec_validates_registered_model_type() -> None:
    spec = ModelSpec.from_mapping(
        {
            "model_id": "baseline",
            "model_type": "ridge_baseline",
            "parameters": {"ridge_l2": 0.5},
        }
    )

    assert spec.executable is True
    assert spec.ridge_l2 == 0.5
