from __future__ import annotations

from alpha_system.experiments.model_specs import ModelSpec
from alpha_system.experiments.scoring import fit_linear_baseline


def test_ic_weighted_score_normalizes_weight_gross_exposure() -> None:
    spec = ModelSpec.from_mapping(
        {
            "model_id": "ic",
            "model_type": "ic_weighted_score",
            "parameters": {"ridge_l2": 0.0},
        }
    )
    fit = fit_linear_baseline(
        spec,
        [
            {"a": 1.0, "b": -1.0},
            {"a": 2.0, "b": -2.0},
            {"a": 3.0, "b": -3.0},
        ],
        [0.1, 0.2, 0.3],
        ("a", "b"),
    )

    assert round(sum(abs(weight) for weight in fit.weights.values()), 12) == 1.0
