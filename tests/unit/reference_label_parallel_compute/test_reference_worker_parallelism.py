from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import alpha_system.features.scaleout.driver as scaleout_driver
from alpha_system.cli.scaleout import _resolve_label_workers
from alpha_system.features.scaleout import (
    MaterializedUnitEvidence,
    ScaleoutTarget,
    build_scaleout_units,
    load_scaleout_config,
    run_scaleout,
)


LABEL_CONFIG = "configs/labels/scaleout/fixed_horizon.json"


def test_reference_label_workers_register_serially_in_unit_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load_scaleout_config(LABEL_CONFIG)
    target = ScaleoutTarget(label_groups=("diagnostic",), symbols=("ES",), years=(2024,))
    units = build_scaleout_units(config, target=target)
    writer_order: list[str] = []

    _patch_runnable_units(monkeypatch)
    monkeypatch.setattr(
        scaleout_driver,
        "_compute_reference_label_stage_outputs_in_workers",
        lambda _config, stage_units, **_kwargs: {
            unit.unit_id: SimpleNamespace(unit_id=unit.unit_id)
            for unit in reversed(stage_units)
        },
    )

    def fake_register(_config, unit, *, alpha_data_root: Path, output):
        writer_order.append(unit.unit_id)
        return _label_evidence(alpha_data_root, unit.unit_id)

    monkeypatch.setattr(
        scaleout_driver,
        "_register_reference_label_worker_output",
        fake_register,
    )

    summary = run_scaleout(
        config,
        alpha_data_root=tmp_path / "alpha",
        dataset_registry_path=tmp_path / "datasets.sqlite",
        canonical_root=tmp_path / "canonical",
        rollout="bounded-real",
        execute=True,
        workers=8,
        target=target,
    )

    assert summary.failed_count == 0
    assert summary.completed_count == len(units)
    assert summary.worker_plan.requested_workers == 8
    assert summary.worker_plan.effective_workers == len(units)
    assert writer_order == [unit.unit_id for unit in units]
    assert [record.unit.unit_id for record in summary.records] == writer_order


def test_reference_label_worker_failure_keeps_siblings_registerable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load_scaleout_config(LABEL_CONFIG)
    target = ScaleoutTarget(label_groups=("diagnostic",), symbols=("ES",), years=(2024,))
    units = build_scaleout_units(config, target=target)
    failed_unit = units[1].unit_id
    registered: list[str] = []

    _patch_runnable_units(monkeypatch)
    monkeypatch.setattr(
        scaleout_driver,
        "_compute_reference_label_stage_outputs_in_workers",
        lambda _config, stage_units, **_kwargs: {
            unit.unit_id: (
                ValueError("synthetic reference worker failure")
                if unit.unit_id == failed_unit
                else SimpleNamespace(unit_id=unit.unit_id)
            )
            for unit in stage_units
        },
    )

    def fake_register(_config, unit, *, alpha_data_root: Path, output):
        registered.append(unit.unit_id)
        return _label_evidence(alpha_data_root, unit.unit_id)

    monkeypatch.setattr(
        scaleout_driver,
        "_register_reference_label_worker_output",
        fake_register,
    )

    summary = run_scaleout(
        config,
        alpha_data_root=tmp_path / "alpha",
        dataset_registry_path=tmp_path / "datasets.sqlite",
        canonical_root=tmp_path / "canonical",
        rollout="bounded-real",
        execute=True,
        workers=4,
        target=target,
    )

    assert summary.completed_count == len(units) - 1
    assert summary.failed_count == 1
    assert failed_unit not in registered
    assert {record.unit.unit_id for record in summary.records if record.status == "failed"} == {
        failed_unit
    }


def test_reference_label_worker_plan_caps_and_default_workers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(scaleout_driver.os, "cpu_count", lambda: 4)

    plan = scaleout_driver._resolve_worker_plan(
        8,
        unit_count=2,
        parallel_allowed=True,
    )

    assert _resolve_label_workers(None, env={}) == 1
    assert _resolve_label_workers(None, env={"ALPHA_LABEL_CPU_WORKERS": "3"}) == 3
    assert _resolve_label_workers(None, env={"ALPHA_CPU_WORKERS": "2"}) == 2
    assert _resolve_label_workers(5, env={"ALPHA_LABEL_CPU_WORKERS": "3"}) == 5
    assert plan.requested_workers == 8
    assert plan.effective_workers == 2
    assert "available cores 4" in plan.reductions[0]
    assert "runnable unit count 2" in plan.reductions[1]


def test_reference_label_checkpoint_appends_after_parent_registration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load_scaleout_config(LABEL_CONFIG)
    target = ScaleoutTarget(label_groups=("diagnostic",), symbols=("ES",), years=(2024,))
    registered: set[str] = set()
    events: list[tuple[str, str]] = []
    original_append = scaleout_driver._ScaleoutLedger.append

    _patch_runnable_units(monkeypatch)
    monkeypatch.setattr(
        scaleout_driver,
        "_compute_reference_label_stage_outputs_in_workers",
        lambda _config, stage_units, **_kwargs: {
            unit.unit_id: SimpleNamespace(unit_id=unit.unit_id) for unit in stage_units
        },
    )

    def fake_register(_config, unit, *, alpha_data_root: Path, output):
        registered.add(unit.unit_id)
        events.append(("registry", unit.unit_id))
        return _label_evidence(alpha_data_root, unit.unit_id)

    def append_after_registry(self, record):
        assert record.unit.unit_id in registered
        events.append(("ledger", record.unit.unit_id))
        return original_append(self, record)

    monkeypatch.setattr(
        scaleout_driver,
        "_register_reference_label_worker_output",
        fake_register,
    )
    monkeypatch.setattr(scaleout_driver._ScaleoutLedger, "append", append_after_registry)

    summary = run_scaleout(
        config,
        alpha_data_root=tmp_path / "alpha",
        dataset_registry_path=tmp_path / "datasets.sqlite",
        canonical_root=tmp_path / "canonical",
        rollout="bounded-real",
        execute=True,
        workers=4,
        target=target,
    )

    assert summary.failed_count == 0
    assert events == [
        event
        for unit in build_scaleout_units(config, target=target)
        for event in (("registry", unit.unit_id), ("ledger", unit.unit_id))
    ]


def test_reference_label_worker_entrypoint_does_not_register_in_worker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load_scaleout_config(LABEL_CONFIG)
    unit = build_scaleout_units(
        config,
        target=ScaleoutTarget(label_ids=("fwd_ret_1m",), symbols=("ES",), years=(2024,)),
    )[0]
    sentinel = SimpleNamespace(unit_id=unit.unit_id)

    monkeypatch.setattr(
        scaleout_driver,
        "_compute_reference_label_unit_output",
        lambda *_args, **_kwargs: sentinel,
    )
    monkeypatch.setattr(
        scaleout_driver,
        "_register_reference_label_worker_output",
        lambda *_args, **_kwargs: pytest.fail("worker must not register labels"),
    )

    output = scaleout_driver._reference_label_worker_compute_entrypoint(
        config,
        unit,
        tmp_path / "alpha",
        tmp_path / "datasets.sqlite",
        tmp_path / "canonical",
    )

    assert output is sentinel


def test_reference_label_worker_thread_caps_are_exported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in (
        "POLARS_MAX_THREADS",
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "NUMEXPR_MAX_THREADS",
    ):
        monkeypatch.delenv(name, raising=False)

    scaleout_driver._pin_reference_label_worker_threads()

    assert {name: scaleout_driver.os.environ[name] for name in (
        "POLARS_MAX_THREADS",
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "NUMEXPR_MAX_THREADS",
    )} == {
        "POLARS_MAX_THREADS": "2",
        "OMP_NUM_THREADS": "2",
        "OPENBLAS_NUM_THREADS": "2",
        "NUMEXPR_MAX_THREADS": "2",
    }


def _patch_runnable_units(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        scaleout_driver,
        "_require_persisted_acceptance_lock",
        lambda _unit, _dataset_registry_path: None,
    )
    monkeypatch.setattr(
        scaleout_driver,
        "_registry_completed_unit",
        lambda *args, **kwargs: None,
    )


def _label_evidence(alpha_data_root: Path, unit_id: str) -> MaterializedUnitEvidence:
    digest = unit_id.removeprefix("mbu_").ljust(64, "0")[:64]
    parquet_path = alpha_data_root / "labels" / f"{unit_id}.parquet"
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    parquet_path.write_text("synthetic placeholder\n", encoding="utf-8")
    return MaterializedUnitEvidence(
        parquet_path=parquet_path.as_posix(),
        content_hash="sha256:" + digest,
        row_count=5,
        label_version_ids=("lver_" + digest,),
    )
