from __future__ import annotations

import pytest

from alpha_system.experiments.model_specs import ModelSpec
from alpha_system.experiments.scoring import ScoringError, fit_linear_baseline


def test_future_model_types_are_design_only_placeholders() -> None:
    spec = ModelSpec.from_mapping({"model_id": "future", "model_type": "lightgbm"})

    assert spec.executable is False
    with pytest.raises(ScoringError, match="deferred"):
        fit_linear_baseline(spec, [{"momentum_3": 1.0}], [0.1], ("momentum_3",))
