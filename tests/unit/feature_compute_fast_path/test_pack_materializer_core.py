from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from alpha_system.core.value_store import ValueStoreFormat
from alpha_system.features.contracts import FeatureSetSpec
from alpha_system.features.fast import (
    FAST_PRODUCER_ENGINE_ID,
    FAST_VALUE_SCHEMA_VERSION,
    FastFeatureDeclaration,
    FastFeaturePack,
    PackMaterializer,
    SymbolYearFrameRequest,
)
from alpha_system.features.families.ohlcv import (
    OHLCVFeatureName,
    build_ohlcv_feature_definition,
    compute_ohlcv_feature,
)
from alpha_system.features.input_views import build_ohlcv_input_view
from tests.fixtures.feature_label.synthetic import (
    EmptyRegistryReader,
    accepted_version,
    approved_feature_request,
)
from tests.unit.feature_compute_fast_path.parity_harness import (
    FeatureParityTolerance,
    assert_feature_records_match,
)

DATASET_ID = "dsv_fast_path_synthetic_v1"
PARTITION_ID = "development_partition"


def test_pack_materializer_matches_reference_returns_on_synthetic_fixture() -> None:
    pl = pytest.importorskip("polars")
    rows = _fixture_rows()
    accepted = accepted_version(DATASET_ID)
    request = approved_feature_request("fast_path_synthetic_returns")
    definition = build_ohlcv_feature_definition(
        OHLCVFeatureName.RETURNS,
        request,
        EmptyRegistryReader(),
        dataset_version_ids=(DATASET_ID,),
        reset_on_session=False,
    )
    reference_view = build_ohlcv_input_view(
        accepted,
        rows,
        partition_id=PARTITION_ID,
        purpose="feature_fast_path_parity",
    )
    reference_records = compute_ohlcv_feature(definition, reference_view)
    materializer = PackMaterializer()
    frame = materializer.frame_from_rows(rows)
    pack = _returns_pack(definition.spec, pl)

    fast_records = materializer.compute_values(frame, pack)

    assert definition.version.feature_version_id == pack.declarations[0].feature_version_id
    assert_feature_records_match(
        reference_records,
        fast_records,
        expected_feature_version_id=definition.version.feature_version_id,
        tolerance=FeatureParityTolerance(abs=1e-12, reason="float division parity"),
    )


def test_pack_materializer_persists_and_registers_through_feature_store(
    tmp_path: Path,
) -> None:
    pl = pytest.importorskip("polars")
    rows = _fixture_rows()
    accepted = accepted_version(DATASET_ID)
    request = approved_feature_request("fast_path_synthetic_registry_returns")
    definition = build_ohlcv_feature_definition(
        OHLCVFeatureName.RETURNS,
        request,
        EmptyRegistryReader(),
        dataset_version_ids=(DATASET_ID,),
        reset_on_session=False,
    )
    checked_request = definition.request_gate_decision.checked_feature_request or request
    materializer = PackMaterializer()
    pack = _returns_pack(definition.spec, pl)

    result = materializer.materialize_pack(
        pack,
        accepted,
        partition_id=PARTITION_ID,
        canonical_frame=materializer.frame_from_rows(rows),
        alpha_data_root=tmp_path,
        value_store_format=ValueStoreFormat.DUAL,
    )
    records = materializer.register_pack(
        result,
        pack,
        feature_requests={definition.spec.feature_id: checked_request},
    )

    assert result.value_store_handle is not None
    assert result.value_store_handle.format is ValueStoreFormat.DUAL
    assert result.value_store_handle.schema_version == FAST_VALUE_SCHEMA_VERSION
    assert Path(result.value_store_handle.jsonl_path or "").exists()
    assert Path(result.value_store_handle.parquet_path or "").exists()
    assert len(records) == 1
    record = records[0]
    assert record.feature_version_id == definition.version.feature_version_id
    assert record.value_store_format == "dual"
    assert record.value_schema_version == FAST_VALUE_SCHEMA_VERSION
    assert record.registry_metadata.to_dict()["producer_engine_id"] == FAST_PRODUCER_ENGINE_ID
    assert record.registry_metadata.to_dict()["value_schema_version"] == FAST_VALUE_SCHEMA_VERSION
    assert record.lineage.contract_provenance.to_dict()["producer_engine_id"] == (
        FAST_PRODUCER_ENGINE_ID
    )


def test_symbol_year_loader_caches_one_frame_per_request() -> None:
    pytest.importorskip("polars")
    rows = _fixture_rows()
    calls: list[dict[str, Any]] = []

    def loader(**kwargs: Any) -> tuple[dict[str, Any], ...]:
        calls.append(dict(kwargs))
        return tuple(rows)

    materializer = PackMaterializer(canonical_ohlcv_loader=loader)
    request = SymbolYearFrameRequest(
        canonical_root="/tmp/alpha_system_synthetic",
        dataset_version_id=DATASET_ID,
        symbol="es",
        year=2024,
    )

    first = materializer.load_symbol_year_ohlcv_frame(request)
    second = materializer.load_symbol_year_ohlcv_frame(request)

    assert first is second
    assert len(calls) == 1
    assert calls[0]["symbol"] == "ES"
    assert calls[0]["start_ts"] == "2024-01-01T00:00:00+00:00"
    assert calls[0]["end_ts"] == "2025-01-01T00:00:00+00:00"


def _returns_pack(feature_spec: Any, pl: Any) -> FastFeaturePack:
    close = pl.col("close").cast(pl.Float64)
    prior_close = close.shift(1)
    current_no_trade = pl.col("quality_flags").list.contains("no_trade").fill_null(False)
    prior_no_trade = current_no_trade.shift(1).fill_null(False)
    insufficient_window = prior_close.is_null()
    input_gap = current_no_trade | prior_no_trade
    empty_flags = pl.lit([], dtype=pl.List(pl.Utf8))
    insufficient_flags = pl.lit(
        ["insufficient_window", "primitive_gap"],
        dtype=pl.List(pl.Utf8),
    )
    input_gap_flags = pl.lit(
        ["input_gap", "no_trade", "primitive_gap"],
        dtype=pl.List(pl.Utf8),
    )
    value_expr = (
        pl.when(insufficient_window | input_gap | (prior_close == 0.0))
        .then(None)
        .otherwise(close / prior_close - 1.0)
    )
    flags_expr = (
        pl.when(insufficient_window)
        .then(insufficient_flags)
        .when(input_gap)
        .then(input_gap_flags)
        .when(prior_close == 0.0)
        .then(pl.lit(["primitive_gap", "zero_denominator"], dtype=pl.List(pl.Utf8)))
        .otherwise(empty_flags)
    )
    return FastFeaturePack(
        feature_set=FeatureSetSpec(
            feature_set_id="feature_set_fast_path_demo",
            feature_set_version="v1",
            features=(feature_spec,),
            description="Synthetic fast-path parity demonstrator.",
        ),
        declarations=(
            FastFeatureDeclaration(
                feature_spec=feature_spec,
                value_expr=value_expr,
                quality_flags_expr=flags_expr,
            ),
        ),
    )


def _fixture_rows() -> tuple[dict[str, Any], ...]:
    path = (
        Path(__file__).resolve().parents[2]
        / "fixtures"
        / "feature_compute_fast_path"
        / "canonical_ohlcv_rows.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["dataset_version_id"] == DATASET_ID
    return tuple(dict(row) for row in payload["rows"])
