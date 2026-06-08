from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from alpha_system.core.value_store import ValueStoreFormat
from alpha_system.features.contracts import FeatureSetSpec, FeatureValueRecord
from alpha_system.features.engine import (
    FeatureMaterializationInputs,
    build_feature_materialization_plan,
    materialize_features,
)
from alpha_system.features.fast import (
    FAST_PRODUCER_ENGINE_ID,
    FAST_VALUE_SCHEMA_VERSION,
    ReconciliationClassification,
    ReconciliationDecision,
    ReconciliationTolerance,
    classify_feature_value_records,
    reconciliation_decision_text,
)
from alpha_system.features.fast.materializer import (
    FastFeatureDeclaration,
    FastFeaturePack,
    PackMaterializer,
)
from alpha_system.features.registry import REFERENCE_FEATURE_PRODUCER_ENGINE_ID
from alpha_system.features.store import FeatureStore
from tests.unit.features.test_feature_engine import (
    _accepted_version,
    _bar_rows,
    _returns_definition,
)

DATASET_ID = "dsv_synthetic_engine_provenance_v1"
PARTITION_ID = "development_partition"


def test_feature_store_records_reference_and_fast_provenance_without_changing_identity(
    tmp_path: Path,
) -> None:
    pytest.importorskip("polars")
    accepted = _accepted_version(DATASET_ID)
    definition = _returns_definition(DATASET_ID)
    feature_set = FeatureSetSpec(
        feature_set_id="feature_set_engine_provenance_fixture",
        feature_set_version="v1",
        features=(definition.spec,),
    )
    checked_request = definition.request_gate_decision.checked_feature_request
    assert checked_request is not None

    reference_root = tmp_path / "reference"
    reference_plan = build_feature_materialization_plan(
        feature_set,
        accepted,
        partition_id=PARTITION_ID,
        alpha_data_root=reference_root,
    )
    reference_result = materialize_features(
        reference_plan,
        FeatureMaterializationInputs(
            accepted_version=accepted,
            bar_rows=_bar_rows(DATASET_ID),
        ),
        (definition,),
        value_store_format=ValueStoreFormat.DUAL,
    )
    reference_record = FeatureStore.from_alpha_data_root(
        reference_root
    ).register_materialized_feature(
        reference_result,
        feature_spec=definition.spec,
        feature_version=definition.version,
        feature_request=checked_request,
    )

    fast_root = tmp_path / "fast"
    materializer = PackMaterializer()
    pack = _returns_pack(definition.spec, pytest.importorskip("polars"))
    fast_result = materializer.materialize_pack(
        pack,
        accepted,
        partition_id=PARTITION_ID,
        canonical_frame=materializer.frame_from_rows(_bar_rows(DATASET_ID)),
        alpha_data_root=fast_root,
        value_store_format=ValueStoreFormat.DUAL,
    )
    fast_record = materializer.register_pack(
        fast_result,
        pack,
        feature_requests={definition.spec.feature_id: checked_request},
        store=FeatureStore.from_alpha_data_root(fast_root),
    )[0]

    assert reference_record.feature_version_id == fast_record.feature_version_id
    assert reference_record.feature_version_id == definition.version.feature_version_id
    assert reference_record.producer_engine_id == REFERENCE_FEATURE_PRODUCER_ENGINE_ID
    assert fast_record.producer_engine_id == FAST_PRODUCER_ENGINE_ID
    assert fast_record.value_schema_version == FAST_VALUE_SCHEMA_VERSION
    assert fast_record.registry_metadata.to_dict()["producer_engine_id"] == (
        FAST_PRODUCER_ENGINE_ID
    )

    with sqlite3.connect(fast_root / "registry" / "features.sqlite") as connection:
        producer_engine_id, value_schema_version = connection.execute(
            """
            SELECT producer_engine_id, value_schema_version
            FROM feature_registry_records
            WHERE feature_version_id = ?
            """,
            (fast_record.feature_version_id,),
        ).fetchone()
    assert producer_engine_id == FAST_PRODUCER_ENGINE_ID
    assert value_schema_version == FAST_VALUE_SCHEMA_VERSION


def test_existing_reference_record_refuses_fast_overwrite_without_version_boundary(
    tmp_path: Path,
) -> None:
    pytest.importorskip("polars")
    accepted = _accepted_version(DATASET_ID)
    definition = _returns_definition(DATASET_ID)
    feature_set = FeatureSetSpec(
        feature_set_id="feature_set_no_mix_fixture",
        feature_set_version="v1",
        features=(definition.spec,),
    )
    checked_request = definition.request_gate_decision.checked_feature_request
    assert checked_request is not None
    reference_root = tmp_path / "reference"
    reference_plan = build_feature_materialization_plan(
        feature_set,
        accepted,
        partition_id=PARTITION_ID,
        alpha_data_root=reference_root,
    )
    reference_result = materialize_features(
        reference_plan,
        FeatureMaterializationInputs(
            accepted_version=accepted,
            bar_rows=_bar_rows(DATASET_ID),
        ),
        (definition,),
        value_store_format=ValueStoreFormat.DUAL,
    )
    reference_store = FeatureStore.from_alpha_data_root(reference_root)
    reference_store.register_materialized_feature(
        reference_result,
        feature_spec=definition.spec,
        feature_version=definition.version,
        feature_request=checked_request,
    )

    materializer = PackMaterializer()
    pack = _returns_pack(definition.spec, pytest.importorskip("polars"))
    fast_result = materializer.materialize_pack(
        pack,
        accepted,
        partition_id=PARTITION_ID,
        canonical_frame=materializer.frame_from_rows(_bar_rows(DATASET_ID)),
        alpha_data_root=tmp_path / "fast_values",
        value_store_format=ValueStoreFormat.DUAL,
    )

    with pytest.raises(ValueError, match="mismatched lineage"):
        materializer.register_pack(
            fast_result,
            pack,
            feature_requests={definition.spec.feature_id: checked_request},
            store=reference_store,
        )

    preserved = reference_store.resolve_feature(definition.version.feature_version_id)
    assert preserved is not None
    assert preserved.producer_engine_id == REFERENCE_FEATURE_PRODUCER_ENGINE_ID


def test_reconciliation_within_tolerance_keeps_reference_and_tags_provenance() -> None:
    result = classify_feature_value_records(
        family_id="vwap_session_auction",
        logical_series_id="vwap",
        reference_records=(_record(1.0),),
        candidate_records=(_record(1.0 + 5e-13),),
        tolerance=ReconciliationTolerance(
            abs=1e-12,
            rel=1e-12,
            reason="VWAP cumulative floating-point reductions",
        ),
    )

    assert result.classification is ReconciliationClassification.WITHIN_TOLERANCE
    assert result.decision is ReconciliationDecision.KEEP_REFERENCE_TAG_PROVENANCE
    assert result.within_tolerance_count == 1
    assert result.beyond_tolerance_count == 0
    assert set(result.producer_engines) == {
        REFERENCE_FEATURE_PRODUCER_ENGINE_ID,
        FAST_PRODUCER_ENGINE_ID,
    }
    assert reconciliation_decision_text(result) == (
        "keep existing valid reference output, tag provenance, do not overwrite"
    )


def test_reconciliation_beyond_tolerance_blocks_silent_engine_mixing() -> None:
    result = classify_feature_value_records(
        family_id="vwap_session_auction",
        logical_series_id="vwap",
        reference_records=(_record(1.0),),
        candidate_records=(_record(1.01),),
        tolerance=ReconciliationTolerance(
            abs=1e-12,
            rel=1e-12,
            reason="VWAP cumulative floating-point reductions",
        ),
    )

    assert result.classification is ReconciliationClassification.BEYOND_TOLERANCE
    assert result.decision is ReconciliationDecision.BLOCK_SILENT_MIXING
    assert result.beyond_tolerance_count == 1
    assert "block silent mixing" in reconciliation_decision_text(result)


def _returns_pack(feature_spec: Any, pl: Any) -> FastFeaturePack:
    close = pl.col("close").cast(pl.Float64)
    prior_close = close.shift(1)
    value_expr = (
        pl.when(prior_close.is_null() | (prior_close == 0.0))
        .then(None)
        .otherwise(close / prior_close - 1.0)
    )
    flags_expr = (
        pl.when(prior_close.is_null())
        .then(pl.lit(["insufficient_window", "primitive_gap"], dtype=pl.List(pl.Utf8)))
        .otherwise(pl.lit([], dtype=pl.List(pl.Utf8)))
    )
    return FastFeaturePack(
        feature_set=FeatureSetSpec(
            feature_set_id="feature_set_engine_provenance_fixture",
            feature_set_version="v1",
            features=(feature_spec,),
        ),
        declarations=(
            FastFeatureDeclaration(
                feature_spec=feature_spec,
                value_expr=value_expr,
                quality_flags_expr=flags_expr,
            ),
        ),
    )


def _record(value: float) -> FeatureValueRecord:
    event_ts = datetime(2024, 1, 2, 14, 31, tzinfo=UTC)
    return FeatureValueRecord(
        feature_version_id="fver_" + "0" * 64,
        entity_id="ES_CONTINUOUS",
        event_ts=event_ts,
        available_ts=event_ts,
        value=value,
        quality_flags=(),
    )
