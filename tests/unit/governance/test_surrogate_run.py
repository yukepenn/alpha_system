from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from alpha_system.cli.main import main
from alpha_system.governance.detection_statistic import (
    TRUE_ALPHA_DETECTION_THRESHOLD_ABS_PEARSON_IC,
)
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
    study_config_for_surrogate_scope,
    validate_surrogate_study_run,
    _run_study_deterministic,
    write_label_shuffled_copy,
    write_trade_date_block_bootstrap_copy,
    write_trade_date_block_shuffled_copy,
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


def test_trade_date_block_shuffle_preserves_skeleton_and_within_day_order(
    tmp_path: Path,
) -> None:
    rows = _multi_day_label_rows((2, 2, 2))
    labels_path = _write_jsonl(tmp_path / "labels.jsonl", rows)
    output_path = tmp_path / "namespace" / "labels" / "block-shuffle.jsonl"

    summary = write_trade_date_block_shuffled_copy(labels_path, output_path, seed=11)

    shuffled = _read_jsonl(output_path)
    assert summary["timestamp_field"] == "event_ts"
    assert summary["moved_count"] == len(rows)
    assert _without_values(shuffled) == _without_values(rows)
    original_by_date = _values_by_date(rows)
    shuffled_by_date = _values_by_date(shuffled)
    assert set(shuffled_by_date) == set(original_by_date)
    for trade_date, values in shuffled_by_date.items():
        assert values in original_by_date.values()
        assert values != original_by_date[trade_date]


def test_trade_date_block_shuffle_counts_unmatched_lengths(tmp_path: Path) -> None:
    rows = _multi_day_label_rows((2, 2, 1))
    labels_path = _write_jsonl(tmp_path / "labels.jsonl", rows)
    output_path = tmp_path / "namespace" / "labels" / "block-shuffle.jsonl"

    summary = write_trade_date_block_shuffled_copy(labels_path, output_path, seed=12)

    shuffled = _read_jsonl(output_path)
    assert summary["unmatched_block_count"] == 1
    assert summary["unmatched_record_count"] == 1
    assert _values_by_date(shuffled)["2026-01-04"] == _values_by_date(rows)["2026-01-04"]


def test_trade_date_block_shuffle_fails_closed_without_event_ts(tmp_path: Path) -> None:
    rows = _multi_day_label_rows((2, 2))
    rows[0].pop("event_ts")
    labels_path = _write_jsonl(tmp_path / "labels.jsonl", rows)

    with pytest.raises(GovernanceValidationError) as exc_info:
        write_trade_date_block_shuffled_copy(
            labels_path,
            tmp_path / "out.jsonl",
            seed=13,
        )

    assert exc_info.value.issues[0].code == "missing_label_block_timestamp"


def test_trade_date_block_bootstrap_resamples_blocks_with_replacement(
    tmp_path: Path,
) -> None:
    rows = _multi_day_label_rows((2, 2, 2))
    labels_path = _write_jsonl(tmp_path / "labels.jsonl", rows)
    output_path = tmp_path / "namespace" / "labels" / "block-bootstrap.jsonl"
    seed = _seed_for_bootstrap_duplicate(labels_path, output_path)

    first = write_trade_date_block_bootstrap_copy(labels_path, output_path, seed=seed)
    first_rows = _read_jsonl(output_path)
    second_path = tmp_path / "namespace" / "labels" / "block-bootstrap-repeat.jsonl"
    second = write_trade_date_block_bootstrap_copy(labels_path, second_path, seed=seed)

    assert first["duplicate_source_block_count"] > 0
    assert first["moved_count"] > 0
    assert first == second
    assert first_rows == _read_jsonl(second_path)
    assert _without_values(first_rows) == _without_values(rows)
    original_blocks = set(_values_by_date(rows).values())
    assert set(_values_by_date(first_rows).values()).issubset(original_blocks)


def test_trade_date_block_bootstrap_rejects_identity_arrangement(tmp_path: Path) -> None:
    labels_path = _write_jsonl(tmp_path / "labels.jsonl", _multi_day_label_rows((1, 1)))
    output_path = tmp_path / "namespace" / "labels" / "block-bootstrap.jsonl"
    identity_seed = _seed_for_bootstrap_identity(labels_path, output_path)

    with pytest.raises(GovernanceValidationError) as exc_info:
        write_trade_date_block_bootstrap_copy(labels_path, output_path, seed=identity_seed)

    assert exc_info.value.issues[0].code == "identity_trade_date_block_bootstrap"


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
    assert result.run.gate_outcome["statistic_passed"] is False
    assert result.run.gate_outcome["eligibility_clean"] is False
    assert (
        result.run.gate_outcome["detection_threshold_abs_pearson_ic"]
        == TRUE_ALPHA_DETECTION_THRESHOLD_ABS_PEARSON_IC
    )
    power = result.run.gate_outcome["detection_power"]
    assert power["stacked"]["n_eff"] >= 0
    assert "Could have detected IC down to" in power["stacked"]["statement"]
    assert power["statistical_validity_claim"] is False
    assert result.run.gate_outcome["evidence_transition"] == "DIAGNOSTICS_RUN->EVIDENCE_READY"
    for path in result.paths.to_dict().values():
        assert Path(str(path)).is_relative_to(namespace)
    trial_ledger = json.loads(
        Path(result.paths.trial_ledger_path).read_text(encoding="utf-8")
    )
    assert trial_ledger["records"][0]["surrogate_flag"] is True
    assert Path(result.paths.variant_ledger_path).read_text(encoding="utf-8") == ""
    assert not Path(result.paths.shuffled_labels_path).exists()


def test_surrogate_fast_path_matches_reference_diagnostic_summary_hashes_for_10_seeds(
    tmp_path: Path,
) -> None:
    namespace = tmp_path / "rigor_p05_surrogate_fast_path_parity"
    namespace.mkdir()
    spec = _study_spec(tmp_path, min_total=1)
    scope = spec.dataset_scope["surrogate_fdr"]
    labels_path = Path(str(scope["labels_path"]))
    seed_hashes: dict[int, tuple[str, str]] = {}

    for seed in range(700, 710):
        run_root = namespace / f"seed_{seed}"
        shuffled_path = run_root / "labels" / "label_shuffle.jsonl"
        study_dir = run_root / "study_outputs"
        write_label_shuffled_copy(labels_path, shuffled_path, seed=seed)
        reference_config = study_config_for_surrogate_scope(
            spec,
            scope=scope,
            seed=seed,
            shuffled_labels_path=shuffled_path,
            output_dir=study_dir,
        )
        reference_result = _run_study_deterministic(reference_config, seed=seed)
        reference_summary_path = Path(reference_result.output_paths.summary_path)
        reference_hash = hashlib.sha256(reference_summary_path.read_bytes()).hexdigest()
        shuffled_path.unlink()

        fast_result = run_surrogate_study(spec, seed=seed, namespace=namespace)
        fast_summary_path = Path(fast_result.paths.study_output_dir) / "diagnostic_summary.json"
        fast_hash = hashlib.sha256(fast_summary_path.read_bytes()).hexdigest()

        assert fast_hash == reference_hash
        assert not shuffled_path.exists()
        seed_hashes[seed] = (reference_hash, fast_hash)

    assert len(seed_hashes) == 10


def test_surrogate_calibration_fast_path_writes_no_per_seed_label_copies(
    tmp_path: Path,
) -> None:
    namespace = tmp_path / "rigor_p05_surrogate_no_label_copies"
    namespace.mkdir()
    spec = _study_spec(tmp_path, min_total=10)

    report = calibrate_surrogate_fdr(
        (spec,),
        run_budget=3,
        base_seed=800,
        namespace=namespace,
    )

    assert report.run_count == 3
    assert tuple(namespace.glob("seed_*/labels/*.jsonl")) == ()
    assert len(tuple(namespace.glob("seed_*/study_outputs/diagnostic_summary.json"))) == 3


@pytest.mark.parametrize(
    "perturbation_type",
    (
        SurrogatePerturbationType.TRADE_DATE_BLOCK_SHUFFLE,
        SurrogatePerturbationType.TRADE_DATE_BLOCK_BOOTSTRAP,
    ),
)
def test_surrogate_runner_threads_block_perturbation_types(
    tmp_path: Path,
    perturbation_type: SurrogatePerturbationType,
) -> None:
    namespace = tmp_path / f"rigor_p05_surrogate_{perturbation_type.value}"
    namespace.mkdir()
    spec = _study_spec(tmp_path, min_total=10, multi_day=True)

    result = run_surrogate_study(
        spec,
        seed=61,
        namespace=namespace,
        perturbation_type=perturbation_type,
    )

    assert result.run.perturbation_type is perturbation_type
    assert result.run.gate_outcome["status"] == SurrogateGateStatus.BLOCKED.value
    assert result.run.gate_outcome["passed"] is False
    assert Path(result.paths.shuffled_labels_path).name == f"{perturbation_type.value}.jsonl"
    assert not Path(result.paths.shuffled_labels_path).exists()


def test_surrogate_pass_uses_statistic_not_clean_diagnostics(tmp_path: Path) -> None:
    passing_namespace = tmp_path / "rigor_p05_surrogate_statistic_pass"
    blocked_namespace = tmp_path / "rigor_p05_surrogate_statistic_block"
    passing_namespace.mkdir()
    blocked_namespace.mkdir()
    spec = _study_spec(tmp_path, min_total=1)

    passing = run_surrogate_study(spec, seed=200, namespace=passing_namespace)
    blocked = run_surrogate_study(spec, seed=20, namespace=blocked_namespace)

    assert passing.run.gate_outcome["diagnostics_status"] == "PASS"
    assert passing.run.gate_outcome["eligibility_clean"] is True
    assert passing.run.gate_outcome["statistic_passed"] is True
    assert passing.run.gate_outcome["passed"] is True
    assert passing.run.gate_outcome["status"] == SurrogateGateStatus.PASSED.value
    assert blocked.run.gate_outcome["diagnostics_status"] == "PASS"
    assert blocked.run.gate_outcome["eligibility_clean"] is True
    assert blocked.run.gate_outcome["statistic_passed"] is False
    assert blocked.run.gate_outcome["passed"] is False
    assert blocked.run.gate_outcome["status"] == SurrogateGateStatus.BLOCKED.value


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
    assert report.statistic_pass_count == 0
    assert report.eligibility_clean_count == 0
    rendered = render_value_free_calibration_report(report)
    assert "Run count: 2" in rendered
    assert "Statistic pass count: 0" in rendered
    assert "Eligibility clean count: 0" in rendered
    assert "0.03" not in rendered


def test_calibration_records_per_perturbation_type_counts(tmp_path: Path) -> None:
    namespace = tmp_path / "rigor_p05_surrogate_block_counts"
    namespace.mkdir()
    spec = _study_spec(tmp_path, min_total=10, multi_day=True)

    report = calibrate_surrogate_fdr(
        (spec,),
        run_budget=2,
        base_seed=500,
        namespace=namespace,
        perturbation_type=SurrogatePerturbationType.TRADE_DATE_BLOCK_SHUFFLE,
    )

    counts = report.perturbation_type_counts[
        SurrogatePerturbationType.TRADE_DATE_BLOCK_SHUFFLE.value
    ]
    assert counts["run_count"] == 2
    assert counts["error_count"] == 0
    assert counts["statistic_pass_count"] == 0
    assert counts["eligibility_clean_count"] == 0
    assert report.per_run[0]["perturbation_type"] == "trade_date_block_shuffle"


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
    assert report.statistic_pass_count == 1
    assert report.eligibility_clean_count == 1
    assert report.accepted is False


def test_calibration_verdict_follows_statistic_not_eligibility(
    tmp_path: Path,
) -> None:
    namespace = tmp_path / "rigor_p05_surrogate_statistic_over_eligibility"
    namespace.mkdir()
    spec = _study_spec(tmp_path, min_total=10)

    report = calibrate_surrogate_fdr(
        (spec,),
        run_budget=1,
        base_seed=200,
        namespace=namespace,
    )

    assert report.threshold_verdict == LEAKAGE_BLOCKED
    assert report.statistic_pass_count == 1
    assert report.eligibility_clean_count == 0
    assert report.per_run[0]["statistic_passed"] is True
    assert report.per_run[0]["eligibility_clean"] is False


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
    assert report.statistic_pass_count == 0
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
    assert payload["statistic_pass_count"] == 0
    assert report_path.read_text(encoding="utf-8").count("Statistic pass rate") == 1


def test_surrogate_calibrate_cli_accepts_block_perturbation_flag(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    namespace = tmp_path / "rigor_p05_surrogate_cli_block"
    namespace.mkdir()
    spec = _study_spec(tmp_path, min_total=10, multi_day=True)
    spec_path = _write_json(tmp_path / "study-spec.json", spec.to_dict())

    code = main(
        [
            "governance",
            "surrogate-calibrate",
            "--study-spec",
            str(spec_path),
            "--runs",
            "1",
            "--base-seed",
            "600",
            "--namespace",
            str(namespace),
            "--perturbation",
            "trade_date_block_shuffle",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert code == 0
    assert payload["per_run"][0]["perturbation_type"] == "trade_date_block_shuffle"
    assert payload["perturbation_type_counts"]["trade_date_block_shuffle"]["run_count"] == 1


def _study_spec(tmp_path: Path, *, min_total: int, multi_day: bool = False):
    factor_path = _write_jsonl(
        tmp_path / f"factor-values-{min_total}.jsonl",
        _factor_rows(multi_day=multi_day),
    )
    label_path = _write_jsonl(
        tmp_path / f"labels-{min_total}.jsonl",
        _multi_day_label_rows((2, 2, 2)) if multi_day else _label_rows(),
    )
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


def _factor_rows(*, multi_day: bool = False) -> list[dict[str, object]]:
    if not multi_day:
        return _single_day_factor_rows()
    return _multi_day_factor_rows()


def _single_day_factor_rows() -> list[dict[str, object]]:
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


def _multi_day_factor_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, value in enumerate([1.0, 2.0, -1.0, -2.0, 1.5, -1.5]):
        event_ts = _event_ts(index % 2, day_offset=index // 2)
        rows.append(
            {
                "factor_id": "fixture_close_delta",
                "factor_version": "v1",
                "instrument_id": "SYNTH",
                "event_ts": _text(event_ts),
                "available_ts": _text(event_ts + timedelta(seconds=5)),
                "session_id": f"XNYS:{event_ts.date().isoformat()}:regular",
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


def _multi_day_label_rows(day_lengths: tuple[int, ...]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    value = 1
    for day_offset, day_length in enumerate(day_lengths):
        for index in range(day_length):
            event_ts = _event_ts(index, day_offset=day_offset)
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
                        "session_id": f"XNYS:{event_ts.date().isoformat()}:regular",
                        "label_version": "labels:v1",
                        "horizon_end_ts": _text(horizon_end),
                        "required_future_bars": 1,
                        "observed_future_bars": 1,
                    },
                    "data_version": "data:v1",
                    "label_available_ts": _text(event_ts + timedelta(seconds=65)),
                }
            )
            value += 1
    return rows


def _event_ts(index: int, *, day_offset: int = 0) -> datetime:
    return datetime(2026, 1, 2 + day_offset, 14, 31 + index, tzinfo=UTC)


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


def _without_values(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [{key: value for key, value in row.items() if key != "value"} for row in rows]


def _values_by_date(rows: list[dict[str, object]]) -> dict[str, tuple[object, ...]]:
    values: dict[str, list[object]] = {}
    for row in rows:
        trade_date = str(row["event_ts"])[:10]
        values.setdefault(trade_date, []).append(row["value"])
    return {trade_date: tuple(items) for trade_date, items in values.items()}


def _seed_for_bootstrap_duplicate(labels_path: Path, output_path: Path) -> int:
    for seed in range(200):
        try:
            summary = write_trade_date_block_bootstrap_copy(labels_path, output_path, seed=seed)
        except GovernanceValidationError:
            continue
        if int(summary["duplicate_source_block_count"]) > 0:
            return seed
    raise AssertionError("no duplicate bootstrap seed found")


def _seed_for_bootstrap_identity(labels_path: Path, output_path: Path) -> int:
    for seed in range(200):
        try:
            write_trade_date_block_bootstrap_copy(labels_path, output_path, seed=seed)
        except GovernanceValidationError as exc:
            if exc.issues[0].code == "identity_trade_date_block_bootstrap":
                return seed
    raise AssertionError("no identity bootstrap seed found")
