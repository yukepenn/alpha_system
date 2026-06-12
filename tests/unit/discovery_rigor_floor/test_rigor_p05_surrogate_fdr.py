from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from alpha_system.data.fixture_policy import repository_root_from_module
from alpha_system.governance.study_spec import generate_study_spec_id, validate_study_spec
from alpha_system.governance.surrogate_run import (
    CALIBRATION_BLOCKED,
    LEAKAGE_BLOCKED,
    ZERO_PASS_MET,
    calibrate_surrogate_fdr,
    require_isolated_namespace,
    run_surrogate_study,
)
from alpha_system.governance.validation import GovernanceValidationError

FIXTURE_PATH = Path("tests/fixtures/governance/study_spec_valid.json")


def test_production_namespace_canary_blocks_surrogate_targeting() -> None:
    production_namespace = repository_root_from_module() / "registry"

    with pytest.raises(GovernanceValidationError) as exc_info:
        require_isolated_namespace(production_namespace)

    assert any(
        issue.code == "production_namespace_forbidden" for issue in exc_info.value.issues
    )


def test_surrogate_flag_canary_marks_trial_records(tmp_path: Path) -> None:
    namespace = tmp_path / "rigor_p05_surrogate_flag"
    namespace.mkdir()
    result = run_surrogate_study(_study_spec(tmp_path, min_total=10), seed=11, namespace=namespace)

    trial_ledger = json.loads(
        Path(result.paths.trial_ledger_path).read_text(encoding="utf-8")
    )

    assert trial_ledger["records"][0]["surrogate_flag"] is True


def test_zero_pass_threshold_canary_blocks_any_shuffled_pass(tmp_path: Path) -> None:
    namespace = tmp_path / "rigor_p05_threshold"
    namespace.mkdir()
    report = calibrate_surrogate_fdr(
        (_study_spec(tmp_path, min_total=1),),
        run_budget=1,
        base_seed=20,
        namespace=namespace,
    )

    assert report.threshold_verdict == LEAKAGE_BLOCKED
    assert report.gate_pass_count == 1


def test_error_masking_canary_blocks_zero_pass_success(tmp_path: Path) -> None:
    namespace = tmp_path / "rigor_p05_error_masking"
    namespace.mkdir()
    spec = _study_spec(tmp_path, min_total=10)
    payload = spec.to_dict()
    scope = dict(payload["dataset_scope"]["surrogate_fdr"])
    scope["factor_values_path"] = (tmp_path / "missing-factor-values.jsonl").as_posix()
    payload["dataset_scope"] = {**payload["dataset_scope"], "surrogate_fdr": scope}
    payload["study_spec_id"] = generate_study_spec_id(payload)
    broken_spec = validate_study_spec(payload)

    report = calibrate_surrogate_fdr(
        (broken_spec,),
        run_budget=1,
        base_seed=30,
        namespace=namespace,
    )

    assert report.error_count == 1
    assert report.gate_pass_count == 0
    assert report.threshold_verdict == CALIBRATION_BLOCKED


def test_seed_determinism_canary_repeats_gate_outcome(tmp_path: Path) -> None:
    namespace = tmp_path / "rigor_p05_seed_determinism"
    namespace.mkdir()
    spec = _study_spec(tmp_path, min_total=10)

    first = run_surrogate_study(spec, seed=40, namespace=namespace)
    second = run_surrogate_study(spec, seed=40, namespace=namespace)

    assert first.run.gate_outcome == second.run.gate_outcome
    assert first.run.surrogate_id == second.run.surrogate_id


def test_synthetic_calibration_canary_is_zero_pass_in_ci(tmp_path: Path) -> None:
    namespace = tmp_path / "rigor_p05_synthetic_ci"
    namespace.mkdir()
    report = calibrate_surrogate_fdr(
        (_study_spec(tmp_path, min_total=10),),
        run_budget=2,
        base_seed=50,
        namespace=namespace,
    )

    assert report.threshold_verdict == ZERO_PASS_MET
    assert report.run_count == 2
    assert report.error_count == 0
    assert report.gate_pass_count == 0


def _study_spec(tmp_path: Path, *, min_total: int):
    factor_path = _write_jsonl(tmp_path / f"factor-values-{min_total}.jsonl", _factor_rows())
    label_path = _write_jsonl(tmp_path / f"labels-{min_total}.jsonl", _label_rows())
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    payload["dataset_scope"] = {
        **payload["dataset_scope"],
        "surrogate_fdr": {
            "factor_id": "fixture_close_delta",
            "factor_version": "v1",
            "label_id": "forward_return_1m",
            "label_version": "labels:v1",
            "data_version": "data:v1",
            "factor_values_path": factor_path.as_posix(),
            "labels_path": label_path.as_posix(),
            "horizon_seconds": 60,
            "sample_size_thresholds": {"min_total": min_total},
            "diagnostic_types": ["directional"],
            "bucket_count": 2,
        },
    }
    payload["study_spec_id"] = generate_study_spec_id(payload)
    return validate_study_spec(payload)


def _factor_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, value in enumerate([1.0, 2.0, -1.0, -2.0]):
        event_ts = _event_ts(index)
        rows.append(
            {
                "factor_id": "fixture_close_delta",
                "factor_version": "v1",
                "instrument_id": "SYNTH",
                "event_ts": _text(event_ts),
                "available_ts": _text(event_ts + timedelta(seconds=5)),
                "session_id": "XNYS:2026-01-02:regular",
                "bar_index": index,
                "value": value,
                "normalized_value": value,
                "quality_flags": ["synthetic"],
                "data_version": "data:v1",
                "compute_version": "test",
            }
        )
    return rows


def _label_rows() -> list[dict[str, object]]:
    values = [0.03, 0.02, -0.01, -0.02]
    rows: list[dict[str, object]] = []
    for index, value in enumerate(values):
        event_ts = _event_ts(index)
        horizon_end = event_ts + timedelta(seconds=60)
        rows.append(
            {
                "label_id": "forward_return_1m",
                "instrument_id": "SYNTH",
                "event_ts": _text(event_ts),
                "horizon": 60,
                "label_type": "forward_return_1m",
                "value": value,
                "path_metadata": {
                    "session_id": "XNYS:2026-01-02:regular",
                    "label_version": "labels:v1",
                    "horizon_end_ts": _text(horizon_end),
                    "required_future_bars": 1,
                    "observed_future_bars": 1,
                },
                "data_version": "data:v1",
                "label_available_ts": _text(event_ts + timedelta(seconds=65)),
            }
        )
    return rows


def _event_ts(index: int) -> datetime:
    return datetime(2026, 1, 2, 14, 31 + index, tzinfo=UTC)


def _text(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> Path:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    return path
