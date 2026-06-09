from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import alpha_system.features.scaleout.driver as scaleout_driver
from alpha_system.core.value_store import ValueStoreFormat, ValueStoreHandle
from alpha_system.features.contracts import FeatureSetSpec
from alpha_system.features.fast import build_fast_feature_pack
from alpha_system.features.scaleout import (
    MaterializedUnitEvidence,
    ScaleoutTarget,
    build_scaleout_units,
    load_scaleout_config,
    run_scaleout,
)
from tests.fixtures.feature_label.synthetic import EmptyRegistryReader


DATASET_ID_2024 = "dsv_databento_ohlcv_05404069799decb0"


def test_scaleout_defaults_to_v1_and_reference_fallback_is_selectable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load_scaleout_config()
    calls: list[tuple[str, str]] = []

    monkeypatch.setattr(
        scaleout_driver,
        "_require_persisted_acceptance_lock",
        lambda _unit, _dataset_registry_path: None,
    )
    monkeypatch.setattr(scaleout_driver, "_registry_completed_unit", lambda *args, **kwargs: None)

    def fake_v1(_config, unit, alpha_root: Path, _registry: Path, _canonical: Path):
        calls.append(("v1", unit.unit_id))
        parquet_path = alpha_root / "values" / f"{unit.unit_id}.parquet"
        parquet_path.parent.mkdir(parents=True, exist_ok=True)
        parquet_path.write_text("synthetic placeholder\n", encoding="utf-8")
        return MaterializedUnitEvidence(
            parquet_path=parquet_path.as_posix(),
            content_hash="sha256:" + "1" * 64,
            row_count=3,
            feature_version_ids=(),
        )

    def fake_reference(_config, unit, alpha_root: Path, _registry: Path, _canonical: Path):
        calls.append(("reference", unit.unit_id))
        parquet_path = alpha_root / "values" / f"{unit.unit_id}.parquet"
        parquet_path.parent.mkdir(parents=True, exist_ok=True)
        parquet_path.write_text("synthetic placeholder\n", encoding="utf-8")
        return MaterializedUnitEvidence(
            parquet_path=parquet_path.as_posix(),
            content_hash="sha256:" + "2" * 64,
            row_count=3,
            feature_version_ids=(),
        )

    monkeypatch.setattr(scaleout_driver, "materialize_v1_feature_unit", fake_v1)
    default_summary = run_scaleout(
        config,
        alpha_data_root=tmp_path / "alpha_v1",
        dataset_registry_path=tmp_path / "datasets.sqlite",
        canonical_root=tmp_path / "canonical",
        rollout="bounded-real",
        execute=True,
        target=ScaleoutTarget(feature_ids=("returns",), symbols=("ES",), years=(2024,)),
    )

    monkeypatch.setattr(scaleout_driver, "materialize_base_ohlcv_unit", fake_reference)
    fallback_summary = run_scaleout(
        config,
        alpha_data_root=tmp_path / "alpha_reference",
        dataset_registry_path=tmp_path / "datasets.sqlite",
        canonical_root=tmp_path / "canonical",
        rollout="bounded-real",
        execute=True,
        engine="reference",
        target=ScaleoutTarget(feature_ids=("returns",), symbols=("ES",), years=(2024,)),
    )

    assert default_summary.engine == "v1"
    assert fallback_summary.engine == "reference"
    assert calls == [
        ("v1", default_summary.records[0].unit.unit_id),
        ("reference", fallback_summary.records[0].unit.unit_id),
    ]


def test_v1_feature_identity_matches_reference_preview_for_targeted_unit() -> None:
    pytest.importorskip("polars")
    config = load_scaleout_config()
    unit = build_scaleout_units(
        config,
        target=ScaleoutTarget(
            feature_ids=("returns",),
            symbols=("ES",),
            years=(2024,),
            dataset_version_ids=(DATASET_ID_2024,),
        ),
    )[0]

    preview_ids = scaleout_driver._preview_feature_version_ids(config, unit)
    definitions = scaleout_driver._feature_definitions_for_unit(
        config,
        unit,
        EmptyRegistryReader(),
    )
    feature_set = FeatureSetSpec(
        feature_set_id=unit.feature_set_id,
        feature_set_version=unit.feature_set_version,
        features=tuple(scaleout_driver._definition_feature_spec(item) for item in definitions),
    )
    pack = build_fast_feature_pack(feature_set)

    assert tuple(declaration.feature_version_id for declaration in pack.declarations) == preview_ids
    assert tuple(feature.feature_id for feature in pack.feature_set.features) == (
        "base_ohlcv_returns",
    )


def test_v1_unit_registration_uses_pack_materializer_and_registry_roundtrip(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load_scaleout_config()
    unit = build_scaleout_units(
        config,
        target=ScaleoutTarget(feature_ids=("returns",), symbols=("ES",), years=(2024,)),
    )[0]
    calls: list[dict[str, object]] = []
    handle = ValueStoreHandle(
        format=ValueStoreFormat.PARQUET,
        jsonl_path=None,
        parquet_path=(tmp_path / "values.parquet").as_posix(),
        value_count=7,
        content_hash="sha256:" + "3" * 64,
        schema_version="alpha_system.features.fast.values.v1",
        dataset_version_id=unit.dataset_version_id,
        set_id=unit.feature_set_id,
        partition_id=unit.partition_id,
        min_event_ts="2024-01-01T00:00:00+00:00",
        max_event_ts="2024-01-01T00:01:00+00:00",
        min_available_ts="2024-01-01T00:00:01+00:00",
        max_available_ts="2024-01-01T00:01:01+00:00",
    )

    class FakeStore:
        registry = EmptyRegistryReader()

    class FakeMaterializer:
        def materialize_pack(self, *args, **kwargs):
            calls.append({"method": "materialize_pack", "kwargs": kwargs})
            return SimpleNamespace(record_count=7, value_store_handle=handle)

        def register_pack(self, result, pack, *, feature_requests, store, registry_metadata):
            calls.append(
                {
                    "method": "register_pack",
                    "store": store,
                    "feature_requests": feature_requests,
                    "registry_metadata": registry_metadata,
                }
            )
            return (SimpleNamespace(feature_version_id="fver_" + "a" * 64),)

    monkeypatch.setattr(
        scaleout_driver.FeatureStore,
        "from_alpha_data_root",
        lambda _root: FakeStore(),
    )
    monkeypatch.setattr(
        scaleout_driver,
        "_v1_context_and_frame",
        lambda *_args, **_kwargs: (object(), object()),
    )
    monkeypatch.setattr(
        scaleout_driver,
        "_verify_feature_registry_roundtrip",
        lambda *args, **kwargs: calls.append({"method": "roundtrip", "kwargs": kwargs}),
    )
    import alpha_system.features.fast as fast_module

    monkeypatch.setattr(fast_module, "PackMaterializer", FakeMaterializer)
    monkeypatch.setattr(
        fast_module,
        "build_fast_feature_pack",
        lambda feature_set: SimpleNamespace(feature_set=feature_set, declarations=()),
    )

    evidence = scaleout_driver.materialize_v1_feature_unit(
        config,
        unit,
        tmp_path,
        tmp_path / "datasets.sqlite",
        tmp_path / "canonical",
    )

    assert evidence.feature_version_ids == ("fver_" + "a" * 64,)
    assert [call["method"] for call in calls] == [
        "materialize_pack",
        "register_pack",
        "roundtrip",
    ]
    register_call = calls[1]
    assert register_call["store"].__class__ is FakeStore
    assert register_call["registry_metadata"]["producer_engine_id"] == (
        "alpha_system.features.fast.pack_materializer.v1"
    )


def test_v1_checkpoint_skip_requires_v1_registry_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load_scaleout_config()
    unit = build_scaleout_units(
        config,
        target=ScaleoutTarget(feature_ids=("returns",), symbols=("ES",), years=(2024,)),
    )[0]
    parquet_path = tmp_path / "values.parquet"
    parquet_path.write_text("synthetic placeholder\n", encoding="utf-8")
    completed = scaleout_driver.ScaleoutUnitRecord(
        unit=unit,
        status="completed",
        stage="bounded_real",
        parquet_path=parquet_path.as_posix(),
        content_hash="sha256:" + "4" * 64,
        row_count=1,
        feature_version_ids=("fver_" + "b" * 64,),
    )

    class FakeStore:
        def __init__(self, producer_engine_id: str) -> None:
            self._producer_engine_id = producer_engine_id

        def resolve_feature(self, _feature_version_id: str):
            return SimpleNamespace(
                parquet_path=parquet_path.as_posix(),
                producer_engine_id=self._producer_engine_id,
            )

    monkeypatch.setattr(
        scaleout_driver.FeatureStore,
        "from_alpha_data_root",
        lambda _root: FakeStore("alpha_system.features.reference.materializer.v1"),
    )
    assert (
        scaleout_driver._completed_record_has_registry_truth(
            completed,
            tmp_path,
            engine="v1",
        )
        is False
    )

    monkeypatch.setattr(
        scaleout_driver.FeatureStore,
        "from_alpha_data_root",
        lambda _root: FakeStore("alpha_system.features.fast.pack_materializer.v1"),
    )
    assert (
        scaleout_driver._completed_record_has_registry_truth(
            completed,
            tmp_path,
            engine="v1",
        )
        is True
    )
