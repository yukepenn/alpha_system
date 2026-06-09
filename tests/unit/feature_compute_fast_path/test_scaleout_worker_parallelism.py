from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

import alpha_system.features.scaleout.driver as scaleout_driver
from alpha_system.features.contracts import FeatureValueRecord
from alpha_system.features.scaleout import (
    MaterializedUnitEvidence,
    ScaleoutTarget,
    build_scaleout_units,
    load_scaleout_config,
    run_scaleout,
)
from alpha_system.cli.scaleout import _resolve_workers
from alpha_system.features.fast.materializer import _canonical_record_dicts


def test_scaleout_workers_default_env_and_cli_precedence() -> None:
    assert _resolve_workers(None, env={}) == 1
    assert _resolve_workers(None, env={"ALPHA_CPU_WORKERS": "4"}) == 4
    assert _resolve_workers(2, env={"ALPHA_CPU_WORKERS": "8"}) == 2

    with pytest.raises(scaleout_driver.ScaleoutError, match="ALPHA_CPU_WORKERS"):
        _resolve_workers(None, env={"ALPHA_CPU_WORKERS": "0"})
    with pytest.raises(scaleout_driver.ScaleoutError, match="--workers"):
        _resolve_workers(0, env={"ALPHA_CPU_WORKERS": "8"})


def test_worker_plan_caps_are_explicit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scaleout_driver.os, "cpu_count", lambda: 4)

    plan = scaleout_driver._resolve_worker_plan(
        8,
        unit_count=2,
        parallel_allowed=True,
    )

    assert plan.requested_workers == 8
    assert plan.effective_workers == 2
    assert plan.threads_per_worker == 2
    assert "available cores 4" in plan.reductions[0]
    assert "runnable unit count 2" in plan.reductions[1]


def test_v1_worker_compute_registers_serially_in_unit_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load_scaleout_config()
    units = build_scaleout_units(
        config,
        target=ScaleoutTarget(feature_ids=("returns",), years=(2024,)),
    )
    writer_order: list[str] = []

    monkeypatch.setattr(
        scaleout_driver,
        "_require_persisted_acceptance_lock",
        lambda _unit, _dataset_registry_path: None,
    )
    monkeypatch.setattr(scaleout_driver, "_registry_completed_unit", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        scaleout_driver,
        "_compute_v1_stage_outputs_in_workers",
        lambda _config, stage_units, **_kwargs: {
            unit.unit_id: SimpleNamespace(unit_id=unit.unit_id)
            for unit in reversed(stage_units)
        },
    )

    def fake_register(
        _config,
        unit,
        *,
        alpha_data_root: Path,
        output,
        rebuild_request_against_live_registry: bool = False,
    ):
        writer_order.append(unit.unit_id)
        parquet_path = alpha_data_root / "values" / f"{unit.unit_id}.parquet"
        parquet_path.parent.mkdir(parents=True, exist_ok=True)
        parquet_path.write_text("synthetic placeholder\n", encoding="utf-8")
        return MaterializedUnitEvidence(
            parquet_path=parquet_path.as_posix(),
            content_hash="sha256:" + unit.unit_id.removeprefix("mbu_").ljust(64, "0")[:64],
            row_count=5,
            feature_version_ids=("fver_" + unit.unit_id.removeprefix("mbu_").ljust(64, "0")[:64],),
        )

    monkeypatch.setattr(scaleout_driver, "_register_v1_worker_output", fake_register)

    summary = run_scaleout(
        config,
        alpha_data_root=tmp_path / "alpha",
        dataset_registry_path=tmp_path / "datasets.sqlite",
        canonical_root=tmp_path / "canonical",
        rollout="bounded-real",
        execute=True,
        workers=8,
        target=ScaleoutTarget(feature_ids=("returns",), years=(2024,)),
    )

    assert summary.failed_count == 0
    assert summary.completed_count == len(units)
    assert summary.worker_plan.requested_workers == 8
    assert writer_order == [unit.unit_id for unit in units]
    assert [record.unit.unit_id for record in summary.records] == writer_order


def test_v1_worker_failure_is_independently_retryable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load_scaleout_config()
    units = build_scaleout_units(
        config,
        target=ScaleoutTarget(feature_ids=("returns",), years=(2024,)),
    )
    failed_unit = units[1].unit_id
    registered: list[str] = []

    monkeypatch.setattr(
        scaleout_driver,
        "_require_persisted_acceptance_lock",
        lambda _unit, _dataset_registry_path: None,
    )
    monkeypatch.setattr(scaleout_driver, "_registry_completed_unit", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        scaleout_driver,
        "_compute_v1_stage_outputs_in_workers",
        lambda _config, stage_units, **_kwargs: {
            unit.unit_id: (
                ValueError("synthetic worker failure")
                if unit.unit_id == failed_unit
                else SimpleNamespace(unit_id=unit.unit_id)
            )
            for unit in stage_units
        },
    )

    def fake_register(
        _config,
        unit,
        *,
        alpha_data_root: Path,
        output,
        rebuild_request_against_live_registry: bool = False,
    ):
        registered.append(unit.unit_id)
        parquet_path = alpha_data_root / "values" / f"{unit.unit_id}.parquet"
        parquet_path.parent.mkdir(parents=True, exist_ok=True)
        parquet_path.write_text("synthetic placeholder\n", encoding="utf-8")
        return MaterializedUnitEvidence(
            parquet_path=parquet_path.as_posix(),
            content_hash="sha256:" + "1" * 64,
            row_count=5,
            feature_version_ids=("fver_" + "1" * 64,),
        )

    monkeypatch.setattr(scaleout_driver, "_register_v1_worker_output", fake_register)

    summary = run_scaleout(
        config,
        alpha_data_root=tmp_path / "alpha",
        dataset_registry_path=tmp_path / "datasets.sqlite",
        canonical_root=tmp_path / "canonical",
        rollout="bounded-real",
        execute=True,
        workers=4,
        target=ScaleoutTarget(feature_ids=("returns",), years=(2024,)),
    )

    assert summary.completed_count == len(units) - 1
    assert summary.failed_count == 1
    assert failed_unit not in registered
    assert {record.unit.unit_id for record in summary.records if record.status == "failed"} == {
        failed_unit
    }


def test_fast_feature_content_hash_order_is_canonical() -> None:
    first = FeatureValueRecord(
        feature_version_id="fver_" + "1" * 64,
        entity_id="ES",
        event_ts=datetime(2024, 1, 1, 0, 0, tzinfo=UTC),
        available_ts=datetime(2024, 1, 1, 0, 1, tzinfo=UTC),
        value=1.0,
    )
    second = FeatureValueRecord(
        feature_version_id="fver_" + "0" * 64,
        entity_id="ES",
        event_ts=datetime(2024, 1, 1, 0, 0, tzinfo=UTC),
        available_ts=datetime(2024, 1, 1, 0, 1, tzinfo=UTC),
        value=2.0,
    )

    assert _canonical_record_dicts((first, second)) == _canonical_record_dicts((second, first))
