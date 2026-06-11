from __future__ import annotations

import inspect
import json
import os
import sqlite3
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import alpha_system.features.scaleout.driver as scaleout_driver
from alpha_system.core.hashing import hash_config
from alpha_system.core.value_store import (
    ValueStoreFormat,
    ValueStoreHandle,
    compute_value_content_hash,
)
from alpha_system.data.foundation.datasets import (
    CoverageReport,
    DataQualityReport,
    DatasetVersion,
    ReportStatus,
    compute_quality_report_hash,
)
from alpha_system.features.consumption import AcceptedDatasetVersion
from alpha_system.features.scaleout import (
    ScaleoutTarget,
    ScaleoutUnit,
    build_scaleout_units,
    load_scaleout_config,
    run_scaleout,
)
from alpha_system.governance.serialization import canonical_serialize
from alpha_system.labels.engine import (
    LABEL_MATERIALIZATION_SCHEMA,
    LabelMaterializationResult,
    build_label_materialization_plan,
    _definition_contract,
)
from alpha_system.labels.registry import LabelRegistry
from alpha_system.labels.version import LabelValueRecord


FIXED_CONFIG = "configs/labels/scaleout/fixed_horizon.json"
COST_CONFIG = "configs/labels/scaleout/cost_adjusted.json"
FIXED_TARGET = ScaleoutTarget(
    label_groups=("diagnostic",),
    symbols=("ES", "NQ"),
    years=(2024,),
)
COST_TARGET = ScaleoutTarget(
    label_ids=("cost_adjusted_fwd_ret", "spread_adjusted_fwd_ret"),
    symbols=("ES",),
    years=(2024,),
)
GRID = ((FIXED_CONFIG, FIXED_TARGET), (COST_CONFIG, COST_TARGET))


def test_reference_workers_1_and_4_are_exactly_equivalent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_synthetic_reference_driver(monkeypatch)

    serial = _run_synthetic_grid(tmp_path / "serial", workers=1)
    parallel = _run_synthetic_grid(tmp_path / "parallel", workers=4)

    assert serial.summary == {
        "worker_counts": [1, 1],
        "completed": 13,
        "failed": 0,
        "skipped": 0,
        "label_units": 13,
    }
    assert parallel.summary == {
        "worker_counts": [4, 4],
        "completed": 13,
        "failed": 0,
        "skipped": 0,
        "label_units": 13,
    }
    assert canonical_serialize(serial.snapshot) == canonical_serialize(parallel.snapshot)


def test_reference_worker_failure_resumes_without_duplicate_completed_checkpoints(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failing_unit = build_scaleout_units(load_scaleout_config(COST_CONFIG), target=COST_TARGET)[-1]
    failures = {failing_unit.unit_id}
    _patch_synthetic_reference_driver(monkeypatch, failures=failures)

    interrupted_root = tmp_path / "worker_failure"
    first = _run_synthetic_grid(interrupted_root, workers=4)

    assert first.summary["failed"] == 1
    assert failing_unit.unit_id in _failed_unit_ids(interrupted_root)

    failures.clear()
    monkeypatch.delenv("RLPC_P02_FAIL_UNITS", raising=False)
    resumed = _run_synthetic_grid(interrupted_root, workers=4)
    clean = _run_synthetic_grid(tmp_path / "uninterrupted", workers=4)

    assert resumed.summary["failed"] == 0
    assert _completed_ledger_unit_ids(interrupted_root) == _registered_unit_ids(resumed)
    assert _completed_ledger_unit_ids(interrupted_root).count(failing_unit.unit_id) == 1
    assert _registered_unit_ids(resumed) == _registered_unit_ids(clean)
    assert canonical_serialize(resumed.snapshot) == canonical_serialize(clean.snapshot)


def test_reference_parent_abort_between_registrations_resumes_to_clean_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_synthetic_reference_driver(monkeypatch, abort_after_completed=3)

    interrupted_root = tmp_path / "parent_abort"
    with pytest.raises(RuntimeError, match="synthetic parent abort between registrations"):
        _run_synthetic_grid(interrupted_root, workers=4)

    completed_before_resume = _completed_ledger_unit_ids(interrupted_root)
    assert len(completed_before_resume) == 3

    resumed = _run_synthetic_grid(interrupted_root, workers=4)
    clean = _run_synthetic_grid(tmp_path / "uninterrupted", workers=4)

    assert resumed.summary["failed"] == 0
    assert _completed_ledger_unit_ids(interrupted_root) == _registered_unit_ids(resumed)
    assert len(_completed_ledger_unit_ids(interrupted_root)) == len(set(_registered_unit_ids(resumed)))
    assert canonical_serialize(resumed.snapshot) == canonical_serialize(clean.snapshot)


def test_reference_worker_entrypoint_does_not_open_label_registry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load_scaleout_config(FIXED_CONFIG)
    unit = build_scaleout_units(config, target=FIXED_TARGET)[0]
    registry_opens: list[str] = []
    real_connect = sqlite3.connect

    def audited_connect(database: object, *args: object, **kwargs: object) -> sqlite3.Connection:
        text = str(database)
        if "labels.sqlite" in text or "/registry/" in text:
            registry_opens.append(text)
        return real_connect(database, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", audited_connect)
    monkeypatch.setattr(
        scaleout_driver,
        "_compute_reference_label_unit_output",
        lambda *_args, **_kwargs: SimpleNamespace(unit_id=unit.unit_id),
    )

    output = scaleout_driver._reference_label_worker_compute_entrypoint(
        config,
        unit,
        tmp_path / "alpha",
        tmp_path / "datasets.sqlite",
        tmp_path / "canonical",
    )

    assert output.unit_id == unit.unit_id
    assert registry_opens == []


def test_reference_worker_registry_open_canary_detects_future_worker_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    blocked: list[str] = []

    def fail_on_label_registry(database: object, *_args: object, **_kwargs: object) -> Any:
        text = str(database)
        if "labels.sqlite" in text:
            blocked.append(text)
            raise AssertionError("worker attempted to open labels.sqlite")
        raise AssertionError(f"unexpected sqlite open during canary self-check: {text}")

    monkeypatch.setattr(sqlite3, "connect", fail_on_label_registry)

    with pytest.raises(AssertionError, match="labels.sqlite"):
        sqlite3.connect(tmp_path / "registry" / "labels.sqlite")

    assert blocked == [(tmp_path / "registry" / "labels.sqlite").as_posix()]


def test_reference_worker_entrypoint_has_no_registry_writer_symbols() -> None:
    source = inspect.getsource(scaleout_driver._reference_label_worker_compute_entrypoint)
    signature = inspect.signature(scaleout_driver._reference_label_worker_compute_entrypoint)

    assert tuple(signature.parameters) == (
        "config",
        "unit",
        "alpha_data_root",
        "dataset_registry_path",
        "canonical_root",
    )
    assert "LabelRegistry" not in source
    assert "register_materialized_label" not in source
    assert "_register_reference_label_worker_output" not in source
    assert "labels.sqlite" not in source


@pytest.mark.skip(
    reason=(
        "optional RLPC-P02 real-slice spot-check requires local real data, "
        "polars, and an explicitly isolated namespace; synthetic gate is authoritative in CI"
    )
)
def test_optional_real_slice_spot_check_requires_local_data_namespace() -> None:
    pass


class _RunResult(SimpleNamespace):
    summary: dict[str, Any]
    snapshot: dict[str, Any]
    alpha_root: Path


def _patch_synthetic_reference_driver(
    monkeypatch: pytest.MonkeyPatch,
    *,
    failures: set[str] | None = None,
    abort_after_completed: int | None = None,
) -> None:
    monkeypatch.setattr(scaleout_driver.os, "cpu_count", lambda: 16)
    monkeypatch.setattr(
        scaleout_driver,
        "_require_persisted_acceptance_lock",
        lambda _unit, _dataset_registry_path: None,
    )

    active_failures = failures if failures is not None else set()
    if active_failures:
        monkeypatch.setenv("RLPC_P02_FAIL_UNITS", ",".join(sorted(active_failures)))
    else:
        monkeypatch.delenv("RLPC_P02_FAIL_UNITS", raising=False)

    def serial_executor(
        config: Any,
        unit: ScaleoutUnit,
        alpha_root: Path,
        _registry: Path,
        _canonical: Path,
    ) -> Any:
        output = _synthetic_reference_worker_output(config, unit, alpha_root)
        return scaleout_driver._register_reference_label_worker_output(
            config,
            unit,
            alpha_data_root=alpha_root,
            output=output,
        )

    monkeypatch.setattr(scaleout_driver, "materialize_reference_label_unit", serial_executor)
    monkeypatch.setattr(
        scaleout_driver,
        "REFERENCE_LABEL_WORKER_ENTRYPOINT",
        _spawn_synthetic_reference_worker_entrypoint,
    )

    if abort_after_completed is not None:
        original_append = scaleout_driver._ScaleoutLedger.append
        completed = {"count": 0, "raised": False}

        def append_then_abort(self: Any, record: Any) -> None:
            original_append(self, record)
            if record.status != "completed" or completed["raised"]:
                return
            completed["count"] += 1
            if completed["count"] == abort_after_completed:
                completed["raised"] = True
                raise RuntimeError("synthetic parent abort between registrations")

        monkeypatch.setattr(scaleout_driver._ScaleoutLedger, "append", append_then_abort)


def _spawn_synthetic_reference_worker_entrypoint(
    config: Any,
    unit: ScaleoutUnit,
    alpha_data_root: Path,
    _dataset_registry_path: Path,
    _canonical_root: Path,
) -> Any:
    failing_units = {
        value.strip()
        for value in os.environ.get("RLPC_P02_FAIL_UNITS", "").split(",")
        if value.strip()
    }
    if unit.unit_id in failing_units:
        raise RuntimeError(f"synthetic worker failure for {unit.unit_id}")
    return _synthetic_reference_worker_output(config, unit, alpha_data_root)


def _run_synthetic_grid(root: Path, *, workers: int) -> _RunResult:
    alpha_root = root / "alpha_data"
    dataset_registry_path = root / "datasets.sqlite"
    canonical_root = root / "canonical"
    summaries = []
    for config_path, target in GRID:
        summary = run_scaleout(
            load_scaleout_config(config_path),
            alpha_data_root=alpha_root,
            dataset_registry_path=dataset_registry_path,
            canonical_root=canonical_root,
            rollout="bounded-real",
            execute=True,
            workers=workers,
            target=target,
        )
        summaries.append(summary)
    return _RunResult(
        summary={
            "worker_counts": [summary.worker_plan.requested_workers for summary in summaries],
            "completed": sum(summary.completed_count for summary in summaries),
            "failed": sum(summary.failed_count for summary in summaries),
            "skipped": sum(summary.skipped_count for summary in summaries),
            "label_units": sum(len(summary.records) for summary in summaries),
        },
        snapshot=_snapshot_run(alpha_root, summaries),
        alpha_root=alpha_root,
    )


def _synthetic_reference_worker_output(
    config: Any,
    unit: ScaleoutUnit,
    alpha_root: Path,
) -> Any:
    definitions = scaleout_driver._reference_label_definitions_for_unit(config, unit)
    label_version_ids = scaleout_driver._reference_label_version_ids(definitions)
    plan = build_label_materialization_plan(
        definitions,
        _accepted_version_for_unit(unit),
        partition_id=unit.partition_id,
        instrument_ids=(unit.symbol,),
        alpha_data_root=alpha_root,
        governance_metadata=scaleout_driver._label_scaleout_metadata(config, unit),
        output_namespace=config.value_namespace,
    )
    stable_plan_key = hash_config(
        {
            "unit_id": unit.unit_id,
            "partition_id": unit.partition_id,
            "label_version_ids": label_version_ids,
        }
    )
    object.__setattr__(plan, "idempotency_key", stable_plan_key)
    object.__setattr__(plan, "plan_id", f"lmat_{stable_plan_key}")

    records = tuple(_synthetic_label_records(unit, definitions))
    record_dicts = tuple(record.to_dict() for record in records)
    content_hash = compute_value_content_hash(record_dicts)
    parquet_path = alpha_root / config.value_namespace / unit.unit_id / "values.parquet"
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    parquet_path.write_text(
        "\n".join(canonical_serialize(record) for record in record_dicts) + "\n",
        encoding="utf-8",
    )
    handle = ValueStoreHandle(
        format=ValueStoreFormat.PARQUET,
        jsonl_path=None,
        parquet_path=parquet_path.as_posix(),
        value_count=len(records),
        content_hash=content_hash,
        schema_version=LABEL_MATERIALIZATION_SCHEMA,
        dataset_version_id=unit.dataset_version_id,
        set_id=plan.plan_id,
        partition_id=unit.partition_id,
        min_event_ts=min(record.event_ts for record in records).isoformat(),
        max_event_ts=max(record.event_ts for record in records).isoformat(),
        min_available_ts=min(record.label_available_ts for record in records).isoformat(),
        max_available_ts=max(record.label_available_ts for record in records).isoformat(),
    )
    result = LabelMaterializationResult(
        plan=plan,
        records=records,
        dry_run=False,
        wrote_output=True,
        output_path=parquet_path,
        value_store_handle=handle,
        planned_input_rows=4,
        planned_label_count=len(definitions),
        runtime_seconds=0.0,
    )
    manifest = scaleout_driver._reference_label_worker_manifest_from_result(
        alpha_data_root=alpha_root,
        config=config,
        unit=unit,
        result=result,
        label_version_ids=label_version_ids,
        value_schema_version=LABEL_MATERIALIZATION_SCHEMA,
    )
    return scaleout_driver._ReferenceLabelWorkerUnitOutput(
        materialization_result=result,
        label_definitions=definitions,
        registry_metadata=scaleout_driver._label_scaleout_metadata(config, unit),
        manifest=manifest,
    )


def _synthetic_label_records(
    unit: ScaleoutUnit,
    definitions: Iterable[Any],
) -> Iterable[LabelValueRecord]:
    base = datetime(unit.year, 1, 2, 14, 30, tzinfo=UTC)
    for definition_index, definition in enumerate(definitions):
        contract = _definition_contract(definition)
        label_version_id = definition.version.label_version_id
        for row_index in range(2):
            event_ts = base + timedelta(minutes=definition_index * 10 + row_index)
            horizon_end_ts = event_ts + timedelta(minutes=1)
            yield LabelValueRecord(
                label_version_id=label_version_id,
                entity_id=f"{unit.symbol}_synthetic_{row_index}",
                event_ts=event_ts,
                horizon_end_ts=horizon_end_ts,
                label_available_ts=horizon_end_ts + timedelta(seconds=definition_index + 1),
                value=f"{unit.family}:{unit.symbol}:{unit.year}:{unit.horizon}:{definition.label_id}:{row_index}",
                quality_flags=("synthetic_guard_passed", f"family:{unit.family}"),
                label_contract=contract,
            )


def _accepted_version_for_unit(unit: ScaleoutUnit) -> AcceptedDatasetVersion:
    quality = _quality_report(unit.dataset_version_id)
    dataset_version = DatasetVersion(
        dataset_version_id=unit.dataset_version_id,
        source="dsrc_synthetic_rlpc_p02",
        symbol_universe=(unit.symbol,),
        bar_size="1 min",
        what_to_show="TRADES",
        start_ts=datetime.fromisoformat(unit.window_start_ts).astimezone(UTC),
        end_ts=datetime.fromisoformat(unit.window_end_ts).astimezone(UTC),
        contract_universe=(unit.symbol,),
        roll_policy_id="roll_cme_index_futures_quarterly",
        manifest_hash="0" * 64,
        code_hash="1" * 64,
        config_hash="2" * 64,
        quality_report_hash=compute_quality_report_hash(quality),
        created_at=datetime.fromisoformat(unit.window_end_ts).astimezone(UTC),
    )
    return AcceptedDatasetVersion(
        registry_path="synthetic_rlpc_p02_registry.sqlite",
        dataset_version=dataset_version,
        lifecycle_state="VERSIONED",
        quality_report=quality,
        coverage_report=_coverage_report(unit.dataset_version_id),
    )


def _quality_report(dataset_version_id: str) -> DataQualityReport:
    return DataQualityReport(
        quality_report_id=f"qr_{dataset_version_id}",
        dataset_version_id=dataset_version_id,
        gap_summary=_passing_summary(),
        duplicate_summary=_passing_summary(),
        non_monotonic_summary=_passing_summary(),
        ohlc_errors=_passing_summary(),
        zero_negative_price_errors=_passing_summary(),
        zero_volume_anomalies=_passing_summary(),
        dst_anomalies=_passing_summary(),
        session_coverage=_passing_summary(),
        roll_discontinuities=_passing_summary(),
        provider_error_summary=_passing_summary(),
        bbo_missing_metric=_passing_summary(),
        abnormal_spread_summary=_passing_summary(),
        status=ReportStatus.PASSING,
    )


def _coverage_report(dataset_version_id: str) -> CoverageReport:
    return CoverageReport(
        coverage_report_id=f"cr_{dataset_version_id}",
        dataset_version_id=dataset_version_id,
        symbol_coverage=_coverage_summary(),
        contract_coverage=_coverage_summary(),
        session_coverage=_coverage_summary(),
        partition_coverage=_coverage_summary(),
        missing_intervals=(),
        incomplete_chunks=(),
    )


def _passing_summary() -> dict[str, object]:
    return {"count": 0, "status": ReportStatus.PASSING.value, "blocking": False}


def _coverage_summary() -> dict[str, object]:
    return {
        "status": ReportStatus.PASSING.value,
        "blocking": False,
        "expected_count": 1,
        "observed_count": 1,
        "missing_count": 0,
        "missing_interval_count": 0,
        "incomplete_chunk_count": 0,
    }


def _snapshot_run(alpha_root: Path, summaries: Iterable[Any]) -> dict[str, Any]:
    registry = LabelRegistry.from_alpha_data_root(alpha_root)
    summary_records = tuple(record for summary in summaries for record in summary.records)
    completed = tuple(record for record in summary_records if record.status in {"completed", "skipped"})
    label_version_ids = tuple(
        label_version_id
        for record in completed
        for label_version_id in record.label_version_ids
    )
    value_records = tuple(
        record
        for summary_record in completed
        for record in _read_synthetic_value_records(Path(summary_record.parquet_path or ""))
    )
    registry_rows = tuple(
        _normalize_root(record.to_dict(), alpha_root)
        for label_version_id in label_version_ids
        if (record := registry.resolve_label(label_version_id)) is not None
    )
    lineage_rows = tuple(
        lineage.to_dict()
        for label_version_id in label_version_ids
        if (lineage := registry.resolve_lineage(label_version_id)) is not None
    )
    unit_evidence = tuple(
        {
            "unit_id": record.unit.unit_id,
            "family": record.unit.family,
            "symbol": record.unit.symbol,
            "year": record.unit.year,
            "horizon": record.unit.horizon,
            "content_hash": record.content_hash,
            "row_count": record.row_count,
            "label_version_ids": list(record.label_version_ids),
        }
        for record in completed
    )
    guard_outcomes = tuple(
        {
            "label_version_id": record["label_version_id"],
            "entity_id": record["entity_id"],
            "quality_flags": record["quality_flags"],
            "label_available_ts": record["label_available_ts"],
        }
        for record in value_records
    )
    return {
        "value_records": _canonical_sorted(value_records),
        "unit_evidence": _canonical_sorted(unit_evidence),
        "registry_rows": _canonical_sorted(registry_rows),
        "lineage_rows": _canonical_sorted(lineage_rows),
        "guard_outcomes": _canonical_sorted(guard_outcomes),
    }


def _read_synthetic_value_records(path: Path) -> tuple[dict[str, Any], ...]:
    return tuple(
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def _normalize_root(value: Any, alpha_root: Path) -> Any:
    if isinstance(value, str):
        return value.replace(alpha_root.as_posix(), "<ALPHA_ROOT>")
    if isinstance(value, Mapping):
        return {
            str(key): (
                "<REGISTERED_AT>"
                if str(key) == "registered_at"
                else _normalize_root(item, alpha_root)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_normalize_root(item, alpha_root) for item in value]
    if isinstance(value, tuple):
        return [_normalize_root(item, alpha_root) for item in value]
    return value


def _canonical_sorted(items: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [dict(item) for item in sorted(items, key=canonical_serialize)]


def _completed_ledger_unit_ids(root: Path) -> list[str]:
    alpha_root = root / "alpha_data"
    records = []
    for config_path, _target in GRID:
        config = load_scaleout_config(config_path)
        manifest = alpha_root / config.completed_manifest
        if not manifest.exists():
            continue
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            if payload.get("status") == "completed":
                records.append(str(payload["unit_id"]))
    return sorted(records)


def _failed_unit_ids(root: Path) -> set[str]:
    alpha_root = root / "alpha_data"
    failed = set()
    for config_path, _target in GRID:
        config = load_scaleout_config(config_path)
        manifest = alpha_root / config.completed_manifest
        if not manifest.exists():
            continue
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            if payload.get("status") == "failed":
                failed.add(str(payload["unit_id"]))
    return failed


def _registered_unit_ids(result: _RunResult) -> list[str]:
    unit_ids: set[str] = set()
    for row in result.snapshot["registry_rows"]:
        metadata = row.get("registry_metadata", {})
        if isinstance(metadata, Mapping):
            unit_id = metadata.get("unit_id")
            if isinstance(unit_id, str):
                unit_ids.add(unit_id)
    return sorted(unit_ids)
