from __future__ import annotations

from pathlib import Path

import alpha_system.features.scaleout.driver as scaleout_driver
import alpha_system.labels.registry as label_registry_module
from alpha_system.features.scaleout import (
    MaterializedUnitEvidence,
    ScaleoutTarget,
    load_scaleout_config,
    render_scaleout_summary_markdown,
    run_scaleout,
)

CONFIG_PATH = "configs/labels/scaleout/fixed_horizon.json"
DATASET_ID_2024 = "dsv_databento_ohlcv_05404069799decb0"


def test_fixed_horizon_label_scaleout_plans_fast_label_units() -> None:
    config = load_scaleout_config(CONFIG_PATH)

    summary = run_scaleout(config, rollout="full-window", engine="v1", workers=4)

    assert config.feature_names == ()
    assert config.label_names == (
        "fwd_ret_1m",
        "fwd_ret_3m",
        "fwd_ret_5m",
        "fwd_ret_10m",
        "fwd_ret_15m",
        "fwd_ret_30m",
    )
    assert summary.engine == "v1"
    assert summary.accepted_unit_count == 144
    assert summary.planned_count == 144
    assert summary.failed_count == 0
    assert summary.worker_plan.effective_workers == 1
    assert {record.unit.year for record in summary.records} == set(range(2019, 2027))
    assert all(record.status == "planned" for record in summary.records)
    assert all(record.label_version_ids for record in summary.records)
    assert all(not record.feature_version_ids for record in summary.records)
    assert all(
        record.unit.partition_id.endswith(record.unit.feature_names[0])
        for record in summary.records
    )
    assert (
        len({record.label_version_ids[0] for record in summary.records})
        == summary.accepted_unit_count
    )

    rendered = render_scaleout_summary_markdown(summary)
    assert "Engine: `v1`" in rendered
    assert "label_available_ts" in rendered
    assert "series_id+contract_id+event_ts" in rendered


def test_fixed_horizon_label_targeting_selects_one_horizon_symbol_year() -> None:
    config = load_scaleout_config(CONFIG_PATH)

    summary = run_scaleout(
        config,
        rollout="full-window",
        target=ScaleoutTarget(
            label_ids=("fwd_ret_5m",),
            symbols=("ES",),
            years=(2024,),
            dataset_version_ids=(DATASET_ID_2024,),
        ),
    )

    assert summary.accepted_unit_count == 1
    assert summary.planned_count == 1
    record = summary.records[0]
    assert record.unit.symbol == "ES"
    assert record.unit.year == 2024
    assert record.unit.dataset_version_id == DATASET_ID_2024
    assert record.unit.feature_names == ("fwd_ret_5m",)
    assert record.unit.partition_id == "ES_2024_fwd_ret_5m"
    assert len(record.label_version_ids) == 1
    assert record.label_version_ids[0].startswith("lver_")


def test_fixed_horizon_label_execute_is_serial_and_preserves_label_versions(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config = load_scaleout_config(CONFIG_PATH)
    calls: list[tuple[str, tuple[str, ...]]] = []

    monkeypatch.setattr(
        scaleout_driver,
        "_require_persisted_acceptance_lock",
        lambda _unit, _dataset_registry_path: None,
    )

    def fake_executor(
        _config,
        unit,
        alpha_root: Path,
        _registry: Path,
        _canonical: Path,
    ) -> MaterializedUnitEvidence:
        calls.append((unit.unit_id, unit.feature_names))
        parquet_path = alpha_root / "fake_label_values" / f"{unit.unit_id}.parquet"
        parquet_path.parent.mkdir(parents=True, exist_ok=True)
        parquet_path.write_text("synthetic label parquet placeholder\n", encoding="utf-8")
        return MaterializedUnitEvidence(
            parquet_path=parquet_path.as_posix(),
            content_hash="sha256:" + "7" * 64,
            row_count=13,
            label_version_ids=(f"lver_{unit.unit_id.removeprefix('mbu_'):0<64}"[:69],),
        )

    summary = run_scaleout(
        config,
        alpha_data_root=tmp_path / "alpha_data",
        dataset_registry_path=tmp_path / "registry.sqlite",
        canonical_root=tmp_path / "canonical",
        rollout="full-window",
        execute=True,
        unit_executor=fake_executor,
        target=ScaleoutTarget(label_ids=("fwd_ret_10m",), symbols=("NQ",), years=(2024,)),
        workers=4,
    )

    assert summary.engine == "v1"
    assert summary.worker_plan.effective_workers == 1
    assert summary.completed_count == 1
    assert summary.failed_count == 0
    assert calls == [(summary.records[0].unit.unit_id, ("fwd_ret_10m",))]
    assert summary.records[0].feature_version_ids == ()
    assert summary.records[0].label_version_ids


def test_fixed_horizon_label_resume_rejects_stale_label_version_checkpoint(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config = load_scaleout_config(CONFIG_PATH)
    calls: list[str] = []
    registry_records: dict[str, _FakeLabelRecord] = {}

    class _FakeLabelRegistry:
        def resolve_label(self, label_version_id: str) -> _FakeLabelRecord | None:
            return registry_records.get(label_version_id)

    monkeypatch.setattr(
        scaleout_driver,
        "_require_persisted_acceptance_lock",
        lambda _unit, _dataset_registry_path: None,
    )
    monkeypatch.setattr(
        label_registry_module.LabelRegistry,
        "from_alpha_data_root",
        staticmethod(lambda _root=None, **_kwargs: _FakeLabelRegistry()),
    )

    def fake_executor(
        _config,
        unit,
        alpha_root: Path,
        _registry: Path,
        _canonical: Path,
    ) -> MaterializedUnitEvidence:
        calls.append(unit.unit_id)
        parquet_path = alpha_root / "fake_label_values" / f"{unit.unit_id}.parquet"
        parquet_path.parent.mkdir(parents=True, exist_ok=True)
        parquet_path.write_text("synthetic label parquet placeholder\n", encoding="utf-8")
        stale_label_version_id = f"lver_{unit.unit_id.removeprefix('mbu_'):0<64}"[:69]
        registry_records[stale_label_version_id] = _FakeLabelRecord(
            dataset_version_id=unit.dataset_version_id,
            partition_id=unit.partition_id,
            parquet_path=parquet_path.as_posix(),
        )
        return MaterializedUnitEvidence(
            parquet_path=parquet_path.as_posix(),
            content_hash="sha256:" + "8" * 64,
            row_count=17,
            label_version_ids=(stale_label_version_id,),
        )

    kwargs = {
        "alpha_data_root": tmp_path / "alpha_data",
        "dataset_registry_path": tmp_path / "registry.sqlite",
        "canonical_root": tmp_path / "canonical",
        "rollout": "full-window",
        "execute": True,
        "unit_executor": fake_executor,
        "target": ScaleoutTarget(label_ids=("fwd_ret_10m",), symbols=("NQ",), years=(2024,)),
    }

    first = run_scaleout(config, **kwargs)
    second = run_scaleout(config, **kwargs)

    assert first.completed_count == 1
    assert second.completed_count == 1
    assert second.skipped_count == 0
    assert calls == [first.records[0].unit.unit_id, first.records[0].unit.unit_id]


class _FakeLabelRecord:
    def __init__(
        self,
        *,
        dataset_version_id: str,
        partition_id: str,
        parquet_path: str,
    ) -> None:
        self.dataset_version_id = dataset_version_id
        self.partition_id = partition_id
        self.value_store_format = "parquet"
        self.parquet_path = parquet_path
