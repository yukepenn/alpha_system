from __future__ import annotations

from pathlib import Path

import pytest

from alpha_system.factors.registry import (
    FactorRegistryError,
    get_factor_version,
    register_factor_spec,
)
from alpha_system.factors.spec import FactorSpec, compute_factor_config_hash


def _payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "factor_id": "synthetic_registry_factor",
        "name": "Synthetic Registry Factor",
        "version": "v1",
        "owner": "research_governance",
        "description": "Synthetic factor spec used for temp registry validation.",
        "input_fields": [
            {"name": "close_price", "domain": "bar", "source_field": "close"}
        ],
        "parameters": {"window_bars": 3, "data_version": "data:synthetic:v1"},
        "frequency": "1m",
        "warmup_bars": 3,
        "session_reset": True,
        "availability_lag": 60,
        "factor_type": "continuous",
        "evaluation_type": "point_in_time",
        "code_hash": "a" * 64,
        "config_hash": "0" * 64,
        "status": "draft",
        "created_at": "2026-01-02T14:30:00Z",
        "validation_artifact_path": None,
    }
    payload.update(overrides)
    payload["config_hash"] = compute_factor_config_hash(payload)
    return payload


def test_factor_versions_are_unique_in_temp_registry(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    spec = FactorSpec.from_mapping(_payload())

    register_factor_spec(registry_path, spec)

    with pytest.raises(FactorRegistryError, match="already exists"):
        register_factor_spec(registry_path, spec)


def test_deprecated_factor_versions_remain_queryable(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    deprecated = FactorSpec.from_mapping(
        _payload(status="deprecated", code_hash="b" * 64)
    )

    register_factor_spec(registry_path, deprecated)
    record = get_factor_version(registry_path, deprecated.factor_id, deprecated.version)

    assert record is not None
    assert record["factor_id"] == deprecated.factor_id
    assert record["factor_version"] == deprecated.version
    assert record["decision_status"] == "deprecated"
