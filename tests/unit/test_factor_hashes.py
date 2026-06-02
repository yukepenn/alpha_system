from __future__ import annotations

from pathlib import Path

from alpha_system.factors.spec import compute_factor_config_hash
from alpha_system.factors.validation import (
    compute_factor_code_hash,
    validate_factor_spec_mapping,
)


def _spec_payload(code_hash: str) -> dict[str, object]:
    payload: dict[str, object] = {
        "factor_id": "synthetic_hash_factor",
        "name": "Synthetic Hash Factor",
        "version": "v1",
        "owner": "research_governance",
        "description": "Synthetic factor spec used for hash validation.",
        "input_fields": [
            {"name": "close_price", "domain": "bar", "source_field": "close"}
        ],
        "parameters": {"window_bars": 2, "data_version": "data:synthetic:v1"},
        "frequency": "1m",
        "warmup_bars": 2,
        "session_reset": True,
        "availability_lag": 60,
        "factor_type": "continuous",
        "evaluation_type": "point_in_time",
        "code_hash": code_hash,
        "config_hash": "0" * 64,
        "status": "draft",
        "created_at": "2026-01-02T14:30:00Z",
        "validation_artifact_path": None,
    }
    payload["config_hash"] = compute_factor_config_hash(payload)
    return payload


def test_factor_config_hash_is_deterministic_and_self_hash_excluded() -> None:
    payload = _spec_payload("e" * 64)
    same_payload = dict(payload)
    same_payload["config_hash"] = "f" * 64

    assert compute_factor_config_hash(payload) == compute_factor_config_hash(same_payload)

    changed = dict(payload)
    changed["parameters"] = {"window_bars": 3, "data_version": "data:synthetic:v1"}
    assert compute_factor_config_hash(payload) != compute_factor_config_hash(changed)


def test_code_hash_check_records_computed_hash(tmp_path: Path) -> None:
    code_path = tmp_path / "factor_code.py"
    code_path.write_text("def compute(row):\n    return row['close']\n", encoding="utf-8")
    code_hash = compute_factor_code_hash((code_path,))
    payload = _spec_payload(code_hash)

    summary = validate_factor_spec_mapping(payload, code_paths=(code_path,))

    assert summary.valid
    assert summary.computed_code_hash == code_hash
    assert summary.code_hash == code_hash


def test_code_hash_mismatch_is_reported(tmp_path: Path) -> None:
    code_path = tmp_path / "factor_code.py"
    code_path.write_text("def compute(row):\n    return row['close']\n", encoding="utf-8")
    payload = _spec_payload("1" * 64)

    summary = validate_factor_spec_mapping(payload, code_paths=(code_path,))

    assert not summary.valid
    assert summary.issue_counts == {"code_hash_mismatch": 1}
