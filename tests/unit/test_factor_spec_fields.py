from __future__ import annotations

import json
from pathlib import Path

import pytest

from alpha_system.factors.spec import (
    REQUIRED_FACTOR_SPEC_FIELDS,
    FactorSpec,
    FactorSpecError,
    compute_factor_config_hash,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
VALID_DRAFT = REPO_ROOT / "configs" / "factors" / "examples" / "valid_draft_factor.json"


def _base_spec(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "factor_id": "synthetic_contract_factor",
        "name": "Synthetic Contract Factor",
        "version": "v1",
        "owner": "research_governance",
        "description": "Synthetic factor spec used for field validation.",
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
        "code_hash": "d" * 64,
        "config_hash": "0" * 64,
        "status": "draft",
        "created_at": "2026-01-02T14:30:00Z",
        "validation_artifact_path": None,
    }
    payload.update(overrides)
    payload["config_hash"] = compute_factor_config_hash(payload)
    return payload


def test_example_factor_spec_contains_all_required_fields() -> None:
    payload = json.loads(VALID_DRAFT.read_text(encoding="utf-8"))
    assert tuple(payload) == REQUIRED_FACTOR_SPEC_FIELDS

    spec = FactorSpec.from_mapping(payload)

    assert spec.factor_id == "synthetic_momentum_ratio"
    assert spec.warmup_bars == 3
    assert spec.session_reset is True
    assert spec.availability_lag.total_seconds() == 60
    assert spec.validation_artifact_path is None


@pytest.mark.parametrize("field", REQUIRED_FACTOR_SPEC_FIELDS)
def test_missing_required_factor_spec_field_is_rejected(field: str) -> None:
    payload = _base_spec()
    payload.pop(field)

    with pytest.raises(FactorSpecError, match="missing required"):
        FactorSpec.from_mapping(payload)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("warmup_bars", -1, "warmup_bars"),
        ("availability_lag", -0.5, "availability_lag"),
        ("session_reset", "true", "session_reset"),
        ("code_hash", "not-a-hash", "code_hash"),
        ("factor_id", "Bad-ID", "factor_id"),
    ),
)
def test_invalid_factor_spec_fields_are_rejected(
    field: str,
    value: object,
    message: str,
) -> None:
    payload = _base_spec(**{field: value})

    with pytest.raises(FactorSpecError, match=message):
        FactorSpec.from_mapping(payload)


def test_candidate_requires_validation_artifact_path() -> None:
    payload = _base_spec(status="candidate", validation_artifact_path=None)

    with pytest.raises(FactorSpecError, match="validation_artifact_path"):
        FactorSpec.from_mapping(payload)


def test_validation_artifact_path_rejects_forbidden_factor_output_suffix() -> None:
    payload = _base_spec(
        status="candidate",
        validation_artifact_path="data/factors/generated_factor.parquet",
    )

    with pytest.raises(FactorSpecError, match="validation_artifact_path"):
        FactorSpec.from_mapping(payload)
