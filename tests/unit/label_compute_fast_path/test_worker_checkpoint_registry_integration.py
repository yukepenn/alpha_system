from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import alpha_system.cli.scaleout as scaleout_cli
import alpha_system.features.scaleout.driver as scaleout_driver
from alpha_system.cli.main import main
from alpha_system.features.scaleout import (
    MaterializedUnitEvidence,
    ScaleoutTarget,
    build_scaleout_units,
    load_scaleout_config,
    run_scaleout,
)

FIXED_CONFIG = "configs/labels/scaleout/fixed_horizon.json"
EXTENDED_CONFIG = "configs/labels/scaleout/extended_horizon.json"
DATASET_ID_2024 = "dsv_databento_ohlcv_05404069799decb0"


def test_label_fast_path_dry_run_targets_horizon_group_without_writes(tmp_path: Path) -> None:
    config = load_scaleout_config(EXTENDED_CONFIG)

    summary = run_scaleout(
        config,
        rollout="full-window",
        target=ScaleoutTarget(
            label_groups=("extended",),
            horizon_groups=("extended",),
            symbols=("ES",),
            years=(2024,),
            dataset_version_ids=(DATASET_ID_2024,),
        ),
        workers=8,
    )

    assert summary.dry_run is True
    assert summary.engine == "v1"
    assert summary.accepted_unit_count == 3
    assert summary.planned_count == 3
    assert summary.worker_plan.effective_workers == 1
    assert sorted(record.unit.feature_names[0] for record in summary.records) == [
        "fwd_ret_120m",
        "fwd_ret_240m",
        "fwd_ret_60m",
    ]
    assert not any(tmp_path.iterdir())


def test_label_worker_env_and_cli_precedence() -> None:
    assert scaleout_cli._resolve_label_workers(None, env={}) == 1
    assert scaleout_cli._resolve_label_workers(None, env={"ALPHA_CPU_WORKERS": "2"}) == 2
    assert (
        scaleout_cli._resolve_label_workers(
            None,
            env={"ALPHA_LABEL_CPU_WORKERS": "4", "ALPHA_CPU_WORKERS": "2"},
        )
        == 4
    )
    assert (
        scaleout_cli._resolve_label_workers(
            3,
            env={"ALPHA_LABEL_CPU_WORKERS": "4", "ALPHA_CPU_WORKERS": "2"},
        )
        == 3
    )


def test_label_checkpoint_skip_and_force_semantics(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    config = load_scaleout_config(FIXED_CONFIG)
    calls: list[str] = []

    monkeypatch.setattr(
        scaleout_driver,
        "_require_persisted_acceptance_lock",
        lambda _unit, _dataset_registry_path: None,
    )
    monkeypatch.setattr(
        scaleout_driver,
        "_completed_record_has_registry_truth",
        lambda *_args, **_kwargs: True,
    )
    monkeypatch.setattr(scaleout_driver, "_registry_completed_unit", lambda *args, **kwargs: None)

    def fake_executor(
        _config: Any,
        unit: Any,
        alpha_root: Path,
        _registry: Path,
        _canonical: Path,
    ) -> MaterializedUnitEvidence:
        calls.append(unit.unit_id)
        parquet_path = alpha_root / "labels" / f"{unit.unit_id}.parquet"
        parquet_path.parent.mkdir(parents=True, exist_ok=True)
        parquet_path.write_text("synthetic label parquet placeholder\n", encoding="utf-8")
        return MaterializedUnitEvidence(
            parquet_path=parquet_path.as_posix(),
            content_hash="sha256:" + "6" * 64,
            row_count=11,
            label_version_ids=("lver_" + "6" * 64,),
        )

    kwargs = {
        "alpha_data_root": tmp_path / "alpha",
        "dataset_registry_path": tmp_path / "datasets.sqlite",
        "canonical_root": tmp_path / "canonical",
        "rollout": "full-window",
        "execute": True,
        "engine": "v1",
        "unit_executor": fake_executor,
        "target": ScaleoutTarget(label_ids=("fwd_ret_10m",), symbols=("NQ",), years=(2024,)),
    }

    first = run_scaleout(config, **kwargs)
    second = run_scaleout(config, **kwargs)
    forced = run_scaleout(config, **{**kwargs, "force_recompute": True})

    assert first.completed_count == 1
    assert second.skipped_count == 1
    assert "checkpoint + registry truth" in second.records[0].message
    assert forced.completed_count == 1
    assert calls == [first.records[0].unit.unit_id, first.records[0].unit.unit_id]


def test_label_worker_compute_registers_serially_in_unit_order(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    config = load_scaleout_config(FIXED_CONFIG)
    target = ScaleoutTarget(label_ids=("fwd_ret_1m",), years=(2024,))
    units = build_scaleout_units(config, target=target)
    writer_order: list[str] = []

    monkeypatch.setattr(
        scaleout_driver,
        "_require_persisted_acceptance_lock",
        lambda _unit, _dataset_registry_path: None,
    )
    monkeypatch.setattr(scaleout_driver, "_registry_completed_unit", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        scaleout_driver,
        "_compute_fast_label_stage_outputs_in_workers",
        lambda _config, stage_units, **_kwargs: {
            unit.unit_id: SimpleNamespace(unit_id=unit.unit_id)
            for unit in reversed(stage_units)
        },
    )

    def fake_register(
        _config: Any,
        unit: Any,
        *,
        alpha_data_root: Path,
        output: Any,
    ) -> MaterializedUnitEvidence:
        writer_order.append(unit.unit_id)
        parquet_path = alpha_data_root / "labels" / f"{unit.unit_id}.parquet"
        parquet_path.parent.mkdir(parents=True, exist_ok=True)
        parquet_path.write_text("synthetic label parquet placeholder\n", encoding="utf-8")
        return MaterializedUnitEvidence(
            parquet_path=parquet_path.as_posix(),
            content_hash="sha256:" + "7" * 64,
            row_count=13,
            label_version_ids=("lver_" + "7" * 64,),
        )

    monkeypatch.setattr(scaleout_driver, "_register_fast_label_worker_output", fake_register)

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
    assert summary.worker_plan.effective_workers > 1
    assert writer_order == [unit.unit_id for unit in units]
    assert [record.unit.unit_id for record in summary.records] == writer_order


def test_label_materialize_fast_path_cli_builds_targeting_request(
    monkeypatch: Any,
    capsys: Any,
) -> None:
    captured: dict[str, Any] = {}

    monkeypatch.setattr("alpha_system.features.scaleout.load_scaleout_config", lambda _path: object())

    def fake_run_scaleout(_config: object, **kwargs: Any) -> _Summary:
        captured.update(kwargs)
        return _Summary(target=kwargs["target"], execute=bool(kwargs["execute"]))

    monkeypatch.setattr("alpha_system.features.scaleout.run_scaleout", fake_run_scaleout)

    rc = main(
        [
            "label",
            "materialize",
            "--fast-path",
            "--label-group",
            "extended",
            "--horizon-group",
            "extended",
            "--symbols",
            "es,nq",
            "--years",
            "2024",
            "--dataset-version-ids",
            "dsv_one",
            "--workers",
            "3",
            "--force",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    target = captured["target"]
    assert rc == 0
    assert target.label_groups == ("extended",)
    assert target.horizon_groups == ("extended",)
    assert target.symbols == ("ES", "NQ")
    assert target.years == (2024,)
    assert target.dataset_version_ids == ("dsv_one",)
    assert captured["workers"] == 3
    assert captured["force_recompute"] is True
    assert captured["execute"] is False
    assert payload["command"] == "label materialize --fast-path"


class _Summary:
    def __init__(self, *, target: ScaleoutTarget, execute: bool) -> None:
        self.target = target
        self.execute = execute
        self.failed_count = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "campaign_id": "LABEL_COMPUTE_FAST_PATH_V1",
            "phase_id": "LCFP-P06",
            "family": "fixed_horizon",
            "engine": "v1",
            "target": self.target.to_dict(),
            "rollout": "bounded-then-full",
            "dry_run": not self.execute,
            "bounded_year": 2024,
            "accepted_unit_count": 0,
            "bounded_unit_count": 0,
            "worker_plan": {
                "requested_workers": 3,
                "effective_workers": 1,
                "threads_per_worker": 1,
                "available_cores": 1,
                "parallel_enabled": False,
                "reductions": [],
            },
            "force_recompute": True,
            "dry_run_estimate": None,
            "planned_count": 0,
            "completed_count": 0,
            "skipped_count": 0,
            "failed_count": 0,
            "records": [],
        }
