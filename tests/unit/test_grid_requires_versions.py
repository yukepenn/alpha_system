from __future__ import annotations

import pytest

from alpha_system.experiments.grid_config import GridConfigError, GridSpec


@pytest.mark.parametrize("field", ["strategy_version", "data_version", "factor_versions", "label_versions"])
def test_grid_spec_requires_version_references(field: str) -> None:
    payload = _payload()
    payload.pop(field)

    with pytest.raises(GridConfigError, match="missing required fields"):
        GridSpec.from_mapping(payload)


def _payload() -> dict[str, object]:
    return {
        "grid_id": "versions",
        "strategy_version": "strategy:v1",
        "data_version": "data:v1",
        "factor_versions": {"fixture_factor": "v1"},
        "label_versions": {"fixture_label": "v1"},
        "max_combinations": 1,
        "parameter_space": {
            "factor": {"lookback": [2]},
            "strategy": {"direction": ["long"]},
        },
    }
