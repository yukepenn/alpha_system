from __future__ import annotations

from alpha_system.experiments.model_specs import ModelSpec
from alpha_system.experiments.scoring import fit_linear_baseline


def test_linear_model_spec_baseline_is_deterministic() -> None:
    spec = ModelSpec.from_mapping(
        {
            "model_id": "linear",
            "model_type": "ridge_baseline",
            "parameters": {"ridge_l2": 0.1},
        }
    )
    rows = [
        {"momentum_3": 0.1, "reversal_2": -0.2},
        {"momentum_3": 0.2, "reversal_2": -0.1},
        {"momentum_3": -0.1, "reversal_2": 0.2},
    ]
    labels = [0.01, 0.02, -0.01]

    first = fit_linear_baseline(spec, rows, labels, ("momentum_3", "reversal_2"))
    second = fit_linear_baseline(spec, rows, labels, ("momentum_3", "reversal_2"))

    assert first.weights == second.weights
    assert first.intercept == second.intercept
    assert first.training_row_count == 3
