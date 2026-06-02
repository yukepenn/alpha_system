from __future__ import annotations

from pathlib import Path

from alpha_system.factors.registry import (
    record_factor_validation_run,
    record_promotion_decision,
)
from alpha_system.factors.spec import FactorSpec, compute_factor_config_hash
from alpha_system.factors.validation import validate_factor_spec_mapping


def _approved_spec_payload() -> dict[str, object]:
    payload: dict[str, object] = {
        "factor_id": "synthetic_reviewed_factor",
        "name": "Synthetic Reviewed Factor",
        "version": "v1",
        "owner": "research_governance",
        "description": "Synthetic factor spec used for promotion-gate validation.",
        "input_fields": [
            {"name": "close_price", "domain": "bar", "source_field": "close"}
        ],
        "parameters": {"window_bars": 4, "data_version": "data:synthetic:v1"},
        "frequency": "1m",
        "warmup_bars": 4,
        "session_reset": True,
        "availability_lag": 60,
        "factor_type": "continuous",
        "evaluation_type": "point_in_time",
        "code_hash": "a" * 64,
        "config_hash": "0" * 64,
        "status": "approved",
        "created_at": "2026-01-02T14:30:00Z",
        "validation_artifact_path": "local_only/factor_validation/reviewed.json",
    }
    payload["config_hash"] = compute_factor_config_hash(payload)
    return payload


def test_approved_factor_requires_reviewed_validation_and_promotion(
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    payload = _approved_spec_payload()

    summary = validate_factor_spec_mapping(payload, registry_path=registry_path)

    assert not summary.valid
    assert summary.issue_counts == {
        "validation_review_missing": 1,
        "promotion_review_missing": 1,
    }


def test_review_backed_promotion_allows_approved_status(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    payload = _approved_spec_payload()
    spec = FactorSpec.from_mapping(payload)

    record_factor_validation_run(
        registry_path,
        spec,
        run_id="factor-validation-reviewed-001",
        decision_status="accepted",
        reviewer="semantic-review",
    )
    record_promotion_decision(
        registry_path,
        spec,
        reviewer="semantic-review",
        rationale="Reviewed validation evidence is recorded for this synthetic spec.",
    )

    summary = validate_factor_spec_mapping(payload, registry_path=registry_path)

    assert summary.valid
    assert summary.issue_counts == {}
