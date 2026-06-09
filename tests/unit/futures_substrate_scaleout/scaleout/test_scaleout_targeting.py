from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

import alpha_system.features.scaleout.driver as scaleout_driver
from alpha_system.features.scaleout import (
    MaterializedUnitEvidence,
    ScaleoutTarget,
    build_scaleout_units,
    load_scaleout_config,
    run_scaleout,
)

DATASET_ID_2024 = "dsv_databento_ohlcv_05404069799decb0"


def test_targeted_feature_selection_narrows_grid_to_feature_symbol_year_dataset() -> None:
    config = load_scaleout_config()
    target = ScaleoutTarget(
        feature_ids=("returns",),
        symbols=("ES",),
        years=(2024,),
        dataset_version_ids=(DATASET_ID_2024,),
    )

    units = build_scaleout_units(config, target=target)
    default_units = build_scaleout_units(
        config,
        target=ScaleoutTarget(symbols=("ES",), years=(2024,)),
    )

    assert len(units) == 1
    assert len(default_units) == 1
    unit = units[0]
    assert unit.family == "base_ohlcv"
    assert unit.symbol == "ES"
    assert unit.year == 2024
    assert unit.dataset_version_id == DATASET_ID_2024
    assert unit.feature_names == ("returns",)
    assert default_units[0].feature_names == config.feature_names
    assert unit.unit_id != default_units[0].unit_id


def test_feature_group_selection_uses_configured_group_without_other_features() -> None:
    config = replace(
        load_scaleout_config(),
        feature_groups={"price_change": ("returns", "log_returns")},
    )

    units = build_scaleout_units(
        config,
        target=ScaleoutTarget(
            feature_groups=("price_change",),
            symbols=("NQ",),
            years=(2024,),
        ),
    )

    assert len(units) == 1
    assert units[0].feature_names == ("returns", "log_returns")
    assert units[0].symbol == "NQ"


def test_selecting_one_feature_does_not_expand_to_other_families() -> None:
    config = load_scaleout_config()

    selected = build_scaleout_units(
        config,
        target=ScaleoutTarget(feature_ids=("returns",), symbols=("ES",), years=(2024,)),
    )
    mismatched_family = build_scaleout_units(
        config,
        target=ScaleoutTarget(family="volume_activity", feature_ids=("returns",)),
    )

    assert len(selected) == 1
    assert {unit.family for unit in selected} == {"base_ohlcv"}
    assert selected[0].feature_names == ("returns",)
    assert mismatched_family == ()


def test_label_target_on_feature_pack_selects_no_feature_units() -> None:
    config = load_scaleout_config()

    summary = run_scaleout(
        config,
        rollout="full-window",
        target=ScaleoutTarget(label_ids=("fixed_horizon_return_1m",)),
    )

    assert summary.accepted_unit_count == 0
    assert summary.planned_count == 0
    assert summary.dry_run_estimate is not None
    assert summary.dry_run_estimate.selected_unit_count == 0


def test_dry_run_estimate_is_value_free_and_writes_nothing(tmp_path: Path) -> None:
    config = load_scaleout_config()
    alpha_data_root = tmp_path / "alpha_data"

    summary = run_scaleout(
        config,
        alpha_data_root=alpha_data_root,
        rollout="full-window",
        target=ScaleoutTarget(feature_ids=("returns",), symbols=("ES",), years=(2024,)),
    )

    assert summary.dry_run is True
    assert summary.accepted_unit_count == 1
    assert summary.planned_count == 1
    assert summary.dry_run_estimate is not None
    assert summary.dry_run_estimate.selected_unit_count == 1
    assert summary.dry_run_estimate.estimated_rows_per_unit == 550000
    assert summary.dry_run_estimate.estimated_total_rows == 550000
    assert summary.dry_run_estimate.estimated_total_seconds > 0
    assert not alpha_data_root.exists()
    payload = summary.to_dict()
    assert payload["dry_run_estimate"] is not None
    assert all(record["parquet_path"] is None for record in payload["records"])
    assert all(record["row_count"] == 0 for record in payload["records"])


def test_execute_runs_selected_units_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load_scaleout_config()
    calls: list[tuple[str, int, tuple[str, ...]]] = []

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
        calls.append((unit.symbol, unit.year, unit.feature_names))
        parquet_path = alpha_root / "fake_values" / f"{unit.unit_id}.parquet"
        parquet_path.parent.mkdir(parents=True, exist_ok=True)
        parquet_path.write_text("synthetic placeholder\n", encoding="utf-8")
        return MaterializedUnitEvidence(
            parquet_path=parquet_path.as_posix(),
            content_hash="sha256:" + "1" * 64,
            row_count=3,
            feature_version_ids=(),
        )

    summary = run_scaleout(
        config,
        alpha_data_root=tmp_path / "alpha_data",
        dataset_registry_path=tmp_path / "registry.sqlite",
        canonical_root=tmp_path / "canonical",
        rollout="full-window",
        execute=True,
        unit_executor=fake_executor,
        target=ScaleoutTarget(feature_ids=("returns",), symbols=("ES", "NQ"), years=(2024,)),
    )

    assert summary.completed_count == 2
    assert summary.failed_count == 0
    assert calls == [
        ("ES", 2024, ("returns",)),
        ("NQ", 2024, ("returns",)),
    ]
    assert {record.unit.symbol for record in summary.records} == {"ES", "NQ"}
    assert all(record.unit.feature_names == ("returns",) for record in summary.records)


def test_skip_completed_requires_checkpoint_and_registry_truth(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load_scaleout_config()
    calls: list[str] = []
    registry_records: dict[str, _FakeFeatureRecord] = {}

    class _FakeFeatureStore:
        def resolve_feature(self, feature_version_id: str) -> _FakeFeatureRecord | None:
            return registry_records.get(feature_version_id)

    monkeypatch.setattr(
        scaleout_driver,
        "_require_persisted_acceptance_lock",
        lambda _unit, _dataset_registry_path: None,
    )
    monkeypatch.setattr(
        scaleout_driver.FeatureStore,
        "from_alpha_data_root",
        lambda _root: _FakeFeatureStore(),
    )

    def fake_executor(
        _config,
        unit,
        alpha_root: Path,
        _registry: Path,
        _canonical: Path,
    ) -> MaterializedUnitEvidence:
        calls.append(unit.unit_id)
        parquet_path = alpha_root / "fake_values" / f"{unit.unit_id}.parquet"
        parquet_path.parent.mkdir(parents=True, exist_ok=True)
        parquet_path.write_text("synthetic placeholder\n", encoding="utf-8")
        feature_version_id = f"fver_{unit.unit_id.removeprefix('mbu_')}"
        content_hash = "sha256:" + "2" * 64
        registry_records[feature_version_id] = _FakeFeatureRecord(
            parquet_path=parquet_path.as_posix(),
            content_hash=content_hash,
            row_count=5,
        )
        return MaterializedUnitEvidence(
            parquet_path=parquet_path.as_posix(),
            content_hash=content_hash,
            row_count=5,
            feature_version_ids=(feature_version_id,),
        )

    kwargs = {
        "alpha_data_root": tmp_path / "alpha_data",
        "dataset_registry_path": tmp_path / "registry.sqlite",
        "canonical_root": tmp_path / "canonical",
        "rollout": "full-window",
        "execute": True,
        "unit_executor": fake_executor,
        "target": ScaleoutTarget(feature_ids=("returns",), symbols=("ES",), years=(2024,)),
    }
    first = run_scaleout(config, **kwargs)
    second = run_scaleout(config, **kwargs)

    assert first.completed_count == 1
    assert second.skipped_count == 1
    assert second.completed_count == 0
    assert calls == [first.records[0].unit.unit_id]
    assert second.records[0].message == "completed unit skipped from checkpoint + registry truth"


class _FakeFeatureRecord:
    def __init__(self, *, parquet_path: str, content_hash: str, row_count: int) -> None:
        self.parquet_path = parquet_path
        self.value_content_hash = content_hash
        self.value_record_count = row_count
        self.producer_engine_id = "alpha_system.features.fast.pack_materializer.v1"
