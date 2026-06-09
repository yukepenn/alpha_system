from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

import alpha_system.features.scaleout.driver as scaleout_driver
from alpha_system.core.value_store import ValueStoreFormat, ValueStoreHandle
from alpha_system.features.contracts import (
    FeatureLineageRecord,
    FeatureSetSpec,
    FeatureValueRecord,
)
from alpha_system.features.engine import (
    FeatureMaterializationResult,
    build_feature_materialization_plan,
)
from alpha_system.features.fast import (
    FAST_PRODUCER_ENGINE_ID,
    FAST_VALUE_SCHEMA_VERSION,
    FastWorkerManifest,
    FastWorkerUnitOutput,
    build_fast_feature_pack,
)
from alpha_system.features.scaleout import (
    MaterializedUnitEvidence,
    ScaleoutTarget,
    build_scaleout_units,
    load_scaleout_config,
    run_scaleout,
)
from tests.fixtures.feature_label.synthetic import EmptyRegistryReader
from tests.unit.futures_substrate_scaleout.test_keystone_identity import _accepted_version


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


def test_v1_force_recompute_reuses_existing_specs_and_updates_only_stale_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load_scaleout_config()
    unit = build_scaleout_units(
        config,
        target=ScaleoutTarget(feature_ids=("returns",), symbols=("ES",), years=(2024,)),
    )[0]
    definition = scaleout_driver._feature_definitions_for_unit(
        config,
        unit,
        EmptyRegistryReader(),
    )[0]
    spec = scaleout_driver._definition_feature_spec(definition)
    version = spec.derive_feature_version()
    feature_set = FeatureSetSpec(
        feature_set_id=unit.feature_set_id,
        feature_set_version=unit.feature_set_version,
        features=(spec,),
    )
    plan = build_feature_materialization_plan(
        feature_set,
        _accepted_version(unit.dataset_version_id),
        partition_id="development_partition",
        alpha_data_root=tmp_path,
        governance_metadata={"producer_engine_id": FAST_PRODUCER_ENGINE_ID},
        output_namespace=config.value_namespace,
    )
    parquet_path = tmp_path / "values.parquet"
    parquet_path.write_text("synthetic parquet placeholder\n", encoding="utf-8")
    fresh_hash = "sha256:" + "5" * 64
    handle = ValueStoreHandle(
        format=ValueStoreFormat.PARQUET,
        jsonl_path=None,
        parquet_path=parquet_path.as_posix(),
        value_count=1,
        content_hash=fresh_hash,
        schema_version=FAST_VALUE_SCHEMA_VERSION,
        dataset_version_id=plan.dataset_version_id,
        set_id=unit.feature_set_id,
        partition_id=plan.partition_id,
        min_event_ts="2024-01-01T00:00:00+00:00",
        max_event_ts="2024-01-01T00:00:00+00:00",
        min_available_ts="2024-01-01T00:01:00+00:00",
        max_available_ts="2024-01-01T00:01:00+00:00",
    )
    result = FeatureMaterializationResult(
        plan=plan,
        records=(
            FeatureValueRecord(
                feature_version_id=version.feature_version_id,
                entity_id="ES",
                event_ts=datetime(2024, 1, 1, tzinfo=UTC),
                available_ts=datetime(2024, 1, 1, 0, 1, tzinfo=UTC),
                value=1.0,
            ),
        ),
        dry_run=False,
        wrote_output=True,
        output_path=parquet_path,
        value_store_handle=handle,
    )
    checked_request = definition.request_gate_decision.checked_feature_request
    assert checked_request is not None
    lineage = FeatureLineageRecord(
        feature_version=version,
        feature_spec=spec,
        feature_request_id=spec.feature_request_id,
        contract_provenance={
            "producer_engine_id": FAST_PRODUCER_ENGINE_ID,
            "value_schema_version": FAST_VALUE_SCHEMA_VERSION,
        },
    )
    output = FastWorkerUnitOutput(
        materialization_result=result,
        feature_set=feature_set,
        feature_request_payloads={spec.feature_id: checked_request.to_dict()},
        registry_metadata={"producer_engine_id": FAST_PRODUCER_ENGINE_ID},
        manifest=FastWorkerManifest(
            unit_key={"unit_id": unit.unit_id},
            parquet_path=parquet_path.as_posix(),
            content_hash=fresh_hash,
            row_count=1,
            feature_version_ids=(version.feature_version_id,),
            producer_engine_id=FAST_PRODUCER_ENGINE_ID,
            value_schema_version=FAST_VALUE_SCHEMA_VERSION,
            manifest_path=(tmp_path / "manifest.json").as_posix(),
        ),
    )

    monkeypatch.setattr(
        scaleout_driver,
        "_verify_feature_registry_roundtrip",
        lambda *args, **kwargs: None,
    )

    def run_with_existing_hash(existing_hash: str) -> tuple[MaterializedUnitEvidence, list[dict]]:
        register_calls: list[dict] = []
        existing = SimpleNamespace(
            feature_version_id=version.feature_version_id,
            feature_spec=spec,
            feature_version=version,
            lineage=lineage,
            feature_request_payload=checked_request.to_dict(),
            producer_engine_id=FAST_PRODUCER_ENGINE_ID,
            parquet_path=parquet_path.as_posix(),
            value_content_hash=existing_hash,
        )

        class FakeStore:
            registry = EmptyRegistryReader()

            def resolve_feature(self, feature_version_id: str):
                assert feature_version_id == version.feature_version_id
                return existing

            def register_materialized_feature(self, materialization_result, **kwargs):
                register_calls.append(
                    {"materialization_result": materialization_result, **kwargs}
                )
                return SimpleNamespace(
                    feature_version_id=version.feature_version_id,
                    feature_spec=spec,
                    feature_version=version,
                    lineage=lineage,
                    producer_engine_id=FAST_PRODUCER_ENGINE_ID,
                    parquet_path=parquet_path.as_posix(),
                    value_content_hash=fresh_hash,
                )

        monkeypatch.setattr(
            scaleout_driver.FeatureStore,
            "from_alpha_data_root",
            lambda _root: FakeStore(),
        )
        prepared = scaleout_driver._prepare_v1_worker_job(
            config,
            unit,
            alpha_data_root=tmp_path,
            force_recompute=True,
        )
        assert prepared.feature_set.features == (spec,)
        assert set(prepared.feature_request_payloads) == {spec.feature_id}
        force_output = FastWorkerUnitOutput(
            materialization_result=result,
            feature_set=prepared.feature_set,
            feature_request_payloads=prepared.feature_request_payloads,
            registry_metadata=prepared.registry_metadata,
            manifest=output.manifest,
        )
        evidence = scaleout_driver._register_v1_worker_output(
            config,
            unit,
            alpha_data_root=tmp_path,
            output=force_output,
        )
        return evidence, register_calls

    matching_evidence, matching_calls = run_with_existing_hash(fresh_hash)
    stale_evidence, stale_calls = run_with_existing_hash("sha256:" + "6" * 64)

    assert matching_evidence.feature_version_ids == (version.feature_version_id,)
    assert matching_calls == []
    assert stale_evidence.feature_version_ids == (version.feature_version_id,)
    assert len(stale_calls) == 1
    assert stale_calls[0]["feature_spec"] is spec
    assert stale_calls[0]["feature_version"] is version
    assert stale_calls[0]["feature_request"] == checked_request.to_dict()
    assert stale_calls[0]["materialization_result"].value_store_handle.content_hash == fresh_hash


def test_v1_force_recompute_prepare_reuses_existing_registry_specs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load_scaleout_config(
        "configs/features/scaleout/regime_volatility_compression.json"
    )
    unit = build_scaleout_units(
        config,
        target=ScaleoutTarget(symbols=("ES",), years=(2024,)),
    )[0]
    definitions = scaleout_driver._regime_volatility_compression_feature_definitions(
        config,
        unit,
        lambda: (),
    )
    parquet_path = tmp_path / "existing.parquet"
    parquet_path.write_text("synthetic parquet placeholder\n", encoding="utf-8")
    existing_by_id = {
        definition.feature_version_id: SimpleNamespace(
            feature_spec=scaleout_driver._definition_feature_spec(definition),
            feature_request_payload={
                "feature_request_id": scaleout_driver._definition_feature_spec(
                    definition
                ).feature_request_id,
            },
            producer_engine_id=FAST_PRODUCER_ENGINE_ID,
            parquet_path=parquet_path.as_posix(),
        )
        for definition in definitions
    }

    class FakeStore:
        registry = object()

        def resolve_feature(self, feature_version_id: str):
            return existing_by_id.get(feature_version_id)

    monkeypatch.setattr(
        scaleout_driver.FeatureStore,
        "from_alpha_data_root",
        lambda _root: FakeStore(),
    )

    prepared = scaleout_driver._prepare_v1_worker_job(
        config,
        unit,
        alpha_data_root=tmp_path,
        force_recompute=True,
    )

    assert tuple(prepared.feature_set.features) == tuple(
        record.feature_spec for record in existing_by_id.values()
    )
    assert set(prepared.feature_request_payloads) == {
        record.feature_spec.feature_id for record in existing_by_id.values()
    }


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
