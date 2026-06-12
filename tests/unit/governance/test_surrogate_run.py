from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from alpha_system.cli.main import main
from alpha_system.governance.serialization import deserialize
from alpha_system.governance.study_spec import (
    generate_study_spec_id,
    validate_study_spec,
)
from alpha_system.governance.surrogate_run import (
    CALIBRATION_BLOCKED,
    LEAKAGE_BLOCKED,
    ZERO_PASS_MET,
    SurrogateGateStatus,
    SurrogatePerturbationType,
    SurrogateStudyRun,
    calibrate_surrogate_fdr,
    create_surrogate_study_run,
    deterministic_created_at,
    render_value_free_calibration_report,
    run_surrogate_study,
    validate_surrogate_study_run,
    write_label_shuffled_copy,
)
from alpha_system.governance.validation import GovernanceValidationError

FIXTURE_PATH = Path("tests/fixtures/governance/study_spec_valid.json")


def test_surrogate_study_run_schema_round_trips_canonically() -> None:
    run = create_surrogate_study_run(
        original_study_spec_id="sspec_438ceffd40855205de5497f0",
        perturbation_type=SurrogatePerturbationType.LABEL_SHUFFLE,
        seed=17,
        trial_ids=("trial_0123456789abcdef01234567",),
        gate_outcome={
            "status": SurrogateGateStatus.BLOCKED.value,
            "passed": False,
            "reason_code": "UNDERPOWERED",
        },
        created_at="2000-01-01T00:00:17Z",
    )

    serialized = run.to_canonical_json()
    round_tripped = SurrogateStudyRun.from_canonical_json(serialized)

    assert round_tripped == run
    assert deserialize(serialized) == run.to_dict()
    assert tuple(run.to_dict()) == (
        "surrogate_id",
        "original_study_spec_id",
        "perturbation_type",
        "seed",
        "trial_ids",
        "gate_outcome",
        "created_at",
    )
    assert run.surrogate_id.startswith("surrun_")


def test_surrogate_study_run_rejects_free_text_perturbation() -> None:
    run = create_surrogate_study_run(
        original_study_spec_id="sspec_438ceffd40855205de5497f0",
        perturbation_type="label_shuffle",
        seed=19,
        trial_ids=("trial_0123456789abcdef01234567",),
        gate_outcome={"status": "BLOCKED", "passed": False},
        created_at="2000-01-01T00:00:19Z",
    ).to_dict()
    run["perturbation_type"] = "shuffle-ish"

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_surrogate_study_run(run)

    assert exc_info.value.issues[0].code == "invalid_surrogate_perturbation_type"


def test_label_shuffle_moves_values_without_changing_alignment_keys(tmp_path: Path) -> None:
    labels_path = _write_jsonl(tmp_path / "labels.jsonl", _label_rows())
    shuffled_path = tmp_path / "namespace" / "labels" / "shuffled.jsonl"

    summary = write_label_shuffled_copy(labels_path, shuffled_path, seed=5)

    original = _read_jsonl(labels_path)
    shuffled = _read_jsonl(shuffled_path)
    assert summary["moved_count"] > 0
    assert [row["event_ts"] for row in shuffled] == [row["event_ts"] for row in original]
    assert [row["value"] for row in shuffled] != [row["value"] for row in original]


def test_surrogate_runner_uses_isolated_namespace_and_real_gate_stack(
    tmp_path: Path,
) -> None:
    namespace = tmp_path / "rigor_p05_surrogate_runner"
    namespace.mkdir()
    spec = _study_spec(tmp_path, min_total=10)

    result = run_surrogate_study(spec, seed=23, namespace=namespace)

    assert result.run.perturbation_type is SurrogatePerturbationType.LABEL_SHUFFLE
    assert result.run.gate_outcome["status"] == SurrogateGateStatus.BLOCKED.value
    assert result.run.gate_outcome["passed"] is False
    assert result.run.gate_outcome["evidence_transition"] == "DIAGNOSTICS_RUN->EVIDENCE_READY"
    for path in result.paths.to_dict().values():
        assert Path(str(path)).is_relative_to(namespace)
    trial_ledger = json.loads(
        Path(result.paths.trial_ledger_path).read_text(encoding="utf-8")
    )
    assert trial_ledger["records"][0]["surrogate_flag"] is True
    assert Path(result.paths.variant_ledger_path).read_text(encoding="utf-8") == ""


def test_surrogate_runner_is_seed_deterministic(tmp_path: Path) -> None:
    namespace = tmp_path / "rigor_p05_surrogate_determinism"
    namespace.mkdir()
    spec = _study_spec(tmp_path, min_total=10)

    first = run_surrogate_study(spec, seed=29, namespace=namespace)
    second = run_surrogate_study(spec, seed=29, namespace=namespace)

    assert first.run.gate_outcome == second.run.gate_outcome
    assert first.run.surrogate_id == second.run.surrogate_id
    assert deterministic_created_at(29) == "2000-01-01T00:00:29Z"


def test_calibration_zero_pass_threshold_met_on_blocked_synthetic_runs(
    tmp_path: Path,
) -> None:
    namespace = tmp_path / "rigor_p05_surrogate_zero_pass"
    namespace.mkdir()
    spec = _study_spec(tmp_path, min_total=10)

    report = calibrate_surrogate_fdr(
        (spec,),
        run_budget=2,
        base_seed=100,
        namespace=namespace,
    )

    assert report.threshold_verdict == ZERO_PASS_MET
    assert report.run_count == 2
    assert report.error_count == 0
    assert report.gate_pass_count == 0
    rendered = render_value_free_calibration_report(report)
    assert "Run count: 2" in rendered
    assert "0.03" not in rendered


def test_calibration_reports_leakage_blocked_when_any_shuffled_run_passes(
    tmp_path: Path,
) -> None:
    namespace = tmp_path / "rigor_p05_surrogate_leakage"
    namespace.mkdir()
    spec = _study_spec(tmp_path, min_total=1)

    report = calibrate_surrogate_fdr(
        (spec,),
        run_budget=1,
        base_seed=200,
        namespace=namespace,
    )

    assert report.threshold_verdict == LEAKAGE_BLOCKED
    assert report.gate_pass_count == 1
    assert report.accepted is False


def test_calibration_errors_do_not_count_as_non_passes(tmp_path: Path) -> None:
    namespace = tmp_path / "rigor_p05_surrogate_errors"
    namespace.mkdir()
    spec = _study_spec(tmp_path, min_total=1)
    payload = spec.to_dict()
    scope = dict(payload["dataset_scope"]["surrogate_fdr"])
    scope["labels_path"] = (tmp_path / "missing-labels.jsonl").as_posix()
    payload["dataset_scope"] = {**payload["dataset_scope"], "surrogate_fdr": scope}
    payload["study_spec_id"] = generate_study_spec_id(payload)
    broken_spec = validate_study_spec(payload)

    report = calibrate_surrogate_fdr(
        (broken_spec,),
        run_budget=1,
        base_seed=300,
        namespace=namespace,
    )

    assert report.error_count == 1
    assert report.gate_pass_count == 0
    assert report.threshold_verdict == CALIBRATION_BLOCKED
    assert report.accepted is False


def test_surrogate_calibrate_cli_writes_value_free_report(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    namespace = tmp_path / "rigor_p05_surrogate_cli"
    namespace.mkdir()
    spec = _study_spec(tmp_path, min_total=10)
    spec_path = _write_json(tmp_path / "study-spec.json", spec.to_dict())
    report_path = tmp_path / "report.md"

    code = main(
        [
            "governance",
            "surrogate-calibrate",
            "--study-spec",
            str(spec_path),
            "--runs",
            "2",
            "--base-seed",
            "400",
            "--namespace",
            str(namespace),
            "--report-out",
            str(report_path),
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert code == 0
    assert payload["threshold_verdict"] == ZERO_PASS_MET
    assert payload["gate_pass_count"] == 0
    assert report_path.read_text(encoding="utf-8").count("Gate pass rate") == 1


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


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
    return path


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> Path:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    return path


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
