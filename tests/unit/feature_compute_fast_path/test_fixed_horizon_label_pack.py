from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import pytest

from alpha_system.core.value_store import ValueStoreFormat
from alpha_system.features.input_views import (
    CanonicalInputViews,
    build_bbo_input_view,
    build_ohlcv_input_view,
)
from alpha_system.labels.fast import (
    FAST_LABEL_PRODUCER_ENGINE_ID,
    FAST_LABEL_VALUE_SCHEMA_VERSION,
    FIXED_HORIZON_LABEL_IDS,
    FastLabelMaterializer,
    LabelPanelFrameRequest,
    build_fixed_horizon_label_pack,
    fixed_horizon_pack_coverage,
)
from alpha_system.labels.families.fixed_horizon import (
    FixedHorizonLabelDefinition,
    FixedHorizonLabelName,
    build_fixed_horizon_label_definition,
    compute_fixed_horizon_labels,
    supported_fixed_horizon_labels,
)
from alpha_system.labels.version import LabelValueRecord
from tests.fixtures.feature_compute_fast_path.fixed_horizon_label import (
    BBO_MISSING_SOURCE_INDEX,
    BBO_QUARANTINED_TERMINAL_INDEX,
    DATASET_ID,
    MAINTENANCE_TERMINAL_INDEX,
    PARTITION_ID,
    ROLL_SOURCE_INDEX,
    ROW_COUNT,
    fixed_horizon_bbo_rows,
    fixed_horizon_ohlcv_rows,
    governed_fixed_horizon_label_specs,
)
from tests.fixtures.feature_label.synthetic import accepted_version
from tests.unit.feature_compute_fast_path.parity_harness import (
    assert_label_records_match,
)


def test_fixed_horizon_label_pack_matches_reference_on_synthetic_fixture() -> None:
    pytest.importorskip("polars")
    accepted = accepted_version(DATASET_ID)
    definitions = _fixed_horizon_definitions()
    reference_views = CanonicalInputViews(
        ohlcv=build_ohlcv_input_view(
            accepted,
            fixed_horizon_ohlcv_rows(),
            partition_id=PARTITION_ID,
            purpose="feature_fast_path_fixed_horizon_label_reference",
        ),
        bbo=build_bbo_input_view(
            accepted,
            fixed_horizon_bbo_rows(),
            partition_id=PARTITION_ID,
            purpose="feature_fast_path_fixed_horizon_label_reference",
        ),
    )
    reference_records = compute_fixed_horizon_labels(definitions, reference_views)
    materializer = FastLabelMaterializer()
    pack = build_fixed_horizon_label_pack(definitions)

    computation = materializer.compute_values_with_metadata(
        materializer.frame_from_rows(
            ohlcv_rows=fixed_horizon_ohlcv_rows(),
            bbo_rows=fixed_horizon_bbo_rows(),
        ),
        pack,
    )
    fast_records = _records_by_label_version(computation.records)

    assert tuple(label.value for label in supported_fixed_horizon_labels()) == (
        FIXED_HORIZON_LABEL_IDS
    )
    assert tuple(declaration.label_version_id for declaration in pack.declarations) == tuple(
        definition.label_version_id for definition in definitions
    )
    _assert_fixture_guard_coverage(reference_records)
    for definition in definitions:
        assert_label_records_match(
            reference_records[definition.name],
            fast_records[definition.label_version_id],
            expected_label_version_id=definition.label_version_id,
        )

    metadata_by_label = {
        item.label_version_id: item for item in computation.metadata.labels
    }
    assert computation.metadata.shared_panel_rows_by_basis == {
        "close": ROW_COUNT,
        "mid": ROW_COUNT,
    }
    assert "is_real_trade_bar" in computation.metadata.prepared_guard_columns
    assert "is_valid_bbo_quote" in computation.metadata.prepared_guard_columns
    for definition in definitions:
        label_metadata = metadata_by_label[definition.label_version_id]
        assert label_metadata.n_eff == len(reference_records[definition.name])
        assert label_metadata.n_eff == ROW_COUNT - definition.horizon_minutes
        assert label_metadata.horizon_overlap_event_count > 0
        assert label_metadata.null_value_count == sum(
            1 for record in reference_records[definition.name] if record.value is None
        )

    coverage = fixed_horizon_pack_coverage()
    assert coverage.close_horizons_minutes == (1, 3, 5, 10, 15, 30)
    assert coverage.mid_horizons_minutes == (1, 3, 5, 10, 30)
    assert "longer" in coverage.governance_gap_note


def test_fixed_horizon_label_pack_materializes_and_registers_serially(
    tmp_path: Path,
) -> None:
    pytest.importorskip("polars")
    accepted = accepted_version(DATASET_ID)
    definitions = _fixed_horizon_definitions()
    materializer = FastLabelMaterializer()
    pack = build_fixed_horizon_label_pack(definitions)
    frame = materializer.frame_from_rows(
        ohlcv_rows=fixed_horizon_ohlcv_rows(),
        bbo_rows=fixed_horizon_bbo_rows(),
    )

    result = materializer.materialize_pack(
        pack,
        accepted,
        partition_id=PARTITION_ID,
        price_frame=frame,
        alpha_data_root=tmp_path,
        value_store_format=ValueStoreFormat.DUAL,
    )
    records = materializer.register_pack(result, pack)

    assert result.value_store_handle is not None
    assert result.value_store_handle.format is ValueStoreFormat.DUAL
    assert result.value_store_handle.schema_version == FAST_LABEL_VALUE_SCHEMA_VERSION
    assert Path(result.value_store_handle.jsonl_path or "").exists()
    assert Path(result.value_store_handle.parquet_path or "").exists()
    assert len(records) == len(definitions)
    assert {record.label_version_id for record in records} == {
        definition.label_version_id for definition in definitions
    }
    assert {
        record.registry_metadata.to_dict()["producer_engine_id"] for record in records
    } == {FAST_LABEL_PRODUCER_ENGINE_ID}
    assert {record.value_schema_version for record in records} == {
        FAST_LABEL_VALUE_SCHEMA_VERSION
    }
    assert {
        record.registry_metadata.to_dict()["value_schema_version"] for record in records
    } == {FAST_LABEL_VALUE_SCHEMA_VERSION}
    assert {
        record.lineage.contract_provenance.to_dict()["value_schema_version"]
        for record in records
    } == {FAST_LABEL_VALUE_SCHEMA_VERSION}

    payloads = [
        json.loads(line)
        for line in Path(result.value_store_handle.jsonl_path or "")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert {payload["record_type"] for payload in payloads} == {
        "fast_label_materialization_plan",
        "fast_label_value",
    }
    assert {payload["producer_engine_id"] for payload in payloads} == {
        FAST_LABEL_PRODUCER_ENGINE_ID
    }
    assert payloads[0]["fast_label_metadata"]["pack_id"] == "fixed_horizon"


def test_fixed_horizon_label_panel_loader_caches_ohlcv_and_bbo_once() -> None:
    pytest.importorskip("polars")
    ohlcv_calls: list[dict[str, Any]] = []
    bbo_calls: list[dict[str, Any]] = []

    def ohlcv_loader(**kwargs: Any) -> tuple[dict[str, Any], ...]:
        ohlcv_calls.append(dict(kwargs))
        return fixed_horizon_ohlcv_rows()

    def bbo_loader(**kwargs: Any) -> tuple[dict[str, Any], ...]:
        bbo_calls.append(dict(kwargs))
        return fixed_horizon_bbo_rows()

    materializer = FastLabelMaterializer(
        canonical_ohlcv_loader=ohlcv_loader,
        canonical_bbo_loader=bbo_loader,
    )
    request = LabelPanelFrameRequest(
        canonical_root="/tmp/alpha_system_synthetic",
        dataset_version_id=DATASET_ID,
        symbol="es",
        year=2024,
    )

    first = materializer.load_symbol_year_price_frame(request)
    second = materializer.load_symbol_year_price_frame(request)

    assert first is second
    assert len(ohlcv_calls) == 1
    assert len(bbo_calls) == 1
    assert ohlcv_calls[0]["symbol"] == "ES"
    assert bbo_calls[0]["symbol"] == "ES"
    assert ohlcv_calls[0]["start_ts"] == "2024-01-01T00:00:00+00:00"
    assert bbo_calls[0]["end_ts"] == "2025-01-01T00:00:00+00:00"


def _fixed_horizon_definitions() -> tuple[FixedHorizonLabelDefinition, ...]:
    specs = governed_fixed_horizon_label_specs()
    return tuple(
        build_fixed_horizon_label_definition(
            label_name,
            specs[label_name],
            dataset_version_ids=(DATASET_ID,),
        )
        for label_name in supported_fixed_horizon_labels()
    )


def _records_by_label_version(
    records: tuple[LabelValueRecord, ...],
) -> dict[str, tuple[LabelValueRecord, ...]]:
    grouped: dict[str, list[LabelValueRecord]] = defaultdict(list)
    for record in records:
        grouped[record.label_version_id].append(record)
    return {label_version_id: tuple(values) for label_version_id, values in grouped.items()}


def _assert_fixture_guard_coverage(
    reference_records: dict[FixedHorizonLabelName, tuple[LabelValueRecord, ...]],
) -> None:
    assert ROLL_SOURCE_INDEX < ROW_COUNT
    assert MAINTENANCE_TERMINAL_INDEX < ROW_COUNT
    assert BBO_MISSING_SOURCE_INDEX < ROW_COUNT
    assert BBO_QUARANTINED_TERMINAL_INDEX < ROW_COUNT

    trade_records = tuple(
        record
        for label_name, records in reference_records.items()
        if not label_name.value.startswith("mid_")
        for record in records
    )
    mid_records = tuple(
        record
        for label_name, records in reference_records.items()
        if label_name.value.startswith("mid_")
        for record in records
    )

    assert any(
        {"source_not_trade", "roll_splice_boundary", "no_trade"}.issubset(
            record.quality_flags
        )
        for record in trade_records
    )
    assert any(
        {"horizon_not_trade", "maintenance_crossing", "no_trade"}.issubset(
            record.quality_flags
        )
        for record in trade_records
    )
    assert any(
        {"bbo_gap", "source_bbo_gap", "missing_bbo"}.issubset(record.quality_flags)
        for record in mid_records
    )
    assert any(
        {"bbo_gap", "horizon_bbo_gap", "bbo_quarantined"}.issubset(
            record.quality_flags
        )
        for record in mid_records
    )
