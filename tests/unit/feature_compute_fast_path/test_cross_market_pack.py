from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pytest

from alpha_system.core.value_store import ValueStoreFormat
from alpha_system.features.contracts import FeatureSetSpec, FeatureValueRecord
from alpha_system.features.fast import (
    CROSS_MARKET_FEATURE_IDS,
    FAST_PRODUCER_ENGINE_ID,
    FAST_VALUE_SCHEMA_VERSION,
    PackMaterializer,
    PackMaterializerError,
    build_cross_market_pack,
    build_fast_feature_pack,
)
from alpha_system.features.families.cross_market import (
    CrossMarketFeatureDefinition,
    CrossMarketFeatureName,
    align_cross_market_rows,
    build_cross_market_feature_definition,
    compute_cross_market_feature,
)
from alpha_system.governance.duplicate_exposure import (
    ExposureCheckResult,
    ExposureRegistryStatus,
)
from alpha_system.governance.feature_request import (
    FeatureRequest,
    FeatureRequestApprovalStatus,
    create_feature_request,
)
from tests.fixtures.feature_compute_fast_path.cross_market import (
    DATASET_ID,
    PARTITION_ID,
    WINDOW_LENGTH,
    cross_market_combined_rows,
    cross_market_input_bundle,
    delayed_nq_available_ts,
    missing_rty_event_ts,
    no_trade_event_ts,
    session_reset_event_ts,
)
from tests.fixtures.feature_label.synthetic import EmptyRegistryReader, accepted_version
from tests.unit.feature_compute_fast_path.parity_harness import (
    FeatureParityTolerance,
    assert_feature_records_match,
)

ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd0"
PACK_FEATURES = tuple(CrossMarketFeatureName)
ROLLING_FLOAT_TOLERANCE = FeatureParityTolerance(
    abs=1e-12,
    rel=1e-12,
    reason=(
        "Rolling covariance, variance, residual, and correlation use equivalent "
        "floating-point reductions; Polars and the Python reference can differ "
        "by binary summation order."
    ),
)


def test_cross_market_pack_matches_reference_on_strict_intersection_fixture() -> None:
    pytest.importorskip("polars")
    bundle = cross_market_input_bundle()
    definitions, feature_set = _cross_market_pack_contracts("strict_intersection")
    reference_records = {
        definition.name: compute_cross_market_feature(definition, bundle)
        for definition in definitions
    }
    materializer = PackMaterializer()
    pack = build_fast_feature_pack(feature_set)

    fast_records = _records_by_feature_version(
        materializer.compute_values(
            materializer.frame_from_rows(cross_market_combined_rows()),
            pack,
        )
    )

    assert (
        tuple(feature.feature_id for feature in pack.feature_set.features)
        == CROSS_MARKET_FEATURE_IDS
    )
    assert tuple(declaration.feature_version_id for declaration in pack.declarations) == tuple(
        definition.feature_version_id for definition in definitions
    )
    _assert_fixture_coverage(reference_records)
    for definition in definitions:
        tolerance = (
            ROLLING_FLOAT_TOLERANCE
            if definition.name
            in {
                CrossMarketFeatureName.NQ_ES_ROLLING_BETA_RESIDUAL,
                CrossMarketFeatureName.RTY_ES_ROLLING_BETA_RESIDUAL,
                CrossMarketFeatureName.NQ_ES_ROLLING_CORRELATION,
                CrossMarketFeatureName.RTY_ES_ROLLING_CORRELATION,
            }
            else FeatureParityTolerance()
        )
        assert_feature_records_match(
            reference_records[definition.name],
            fast_records[definition.feature_version_id],
            expected_feature_version_id=definition.feature_version_id,
            tolerance=tolerance,
        )
        assert missing_rty_event_ts() not in {
            record.event_ts for record in fast_records[definition.feature_version_id]
        }


def test_cross_market_pack_matches_reference_on_asof_fixture() -> None:
    pytest.importorskip("polars")
    bundle = cross_market_input_bundle()
    definitions, feature_set = _cross_market_pack_contracts("asof")
    materializer = PackMaterializer()
    pack = build_fast_feature_pack(feature_set)

    fast_records = _records_by_feature_version(
        materializer.compute_values(
            materializer.frame_from_rows(cross_market_combined_rows()),
            pack,
        )
    )

    for definition in definitions:
        tolerance = (
            ROLLING_FLOAT_TOLERANCE
            if definition.name
            in {
                CrossMarketFeatureName.NQ_ES_ROLLING_BETA_RESIDUAL,
                CrossMarketFeatureName.RTY_ES_ROLLING_BETA_RESIDUAL,
                CrossMarketFeatureName.NQ_ES_ROLLING_CORRELATION,
                CrossMarketFeatureName.RTY_ES_ROLLING_CORRELATION,
            }
            else FeatureParityTolerance()
        )
        assert_feature_records_match(
            compute_cross_market_feature(definition, bundle),
            fast_records[definition.feature_version_id],
            expected_feature_version_id=definition.feature_version_id,
            tolerance=tolerance,
        )


def test_cross_market_pack_rejects_asof_for_scaleout_substrate_metadata() -> None:
    _definitions, feature_set = _cross_market_pack_contracts("asof")
    substrate_feature_set = FeatureSetSpec(
        feature_set_id="feature_set_futures_scaleout_cross_market_alignment",
        feature_set_version=feature_set.feature_set_version,
        features=feature_set.features,
        description=feature_set.description,
        metadata={
            "campaign_id": "ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1",
            "family": "cross_market_alignment",
        },
    )

    with pytest.raises(PackMaterializerError, match="strict_intersection"):
        build_cross_market_pack(substrate_feature_set)


def test_cross_market_pack_materialization_records_fast_provenance(tmp_path: Path) -> None:
    pytest.importorskip("polars")
    accepted = accepted_version(DATASET_ID)
    definitions, feature_set = _cross_market_pack_contracts("strict_intersection")
    materializer = PackMaterializer()
    pack = build_fast_feature_pack(feature_set)

    result = materializer.materialize_pack(
        pack,
        accepted,
        partition_id=PARTITION_ID,
        canonical_frame=materializer.frame_from_rows(cross_market_combined_rows()),
        alpha_data_root=tmp_path,
        value_store_format=ValueStoreFormat.DUAL,
    )

    assert result.value_store_handle is not None
    assert result.value_store_handle.schema_version == FAST_VALUE_SCHEMA_VERSION
    assert Path(result.value_store_handle.jsonl_path or "").exists()
    assert Path(result.value_store_handle.parquet_path or "").exists()
    assert result.value_store_handle.format is ValueStoreFormat.DUAL
    assert {record.feature_version_id for record in result.records} == {
        definition.feature_version_id for definition in definitions
    }
    payloads = [
        json.loads(line)
        for line in Path(result.value_store_handle.jsonl_path or "").read_text(
            encoding="utf-8"
        ).splitlines()
    ]
    assert {payload["record_type"] for payload in payloads} == {
        "fast_feature_materialization_plan",
        "fast_feature_value",
    }
    assert {payload["producer_engine_id"] for payload in payloads} == {
        FAST_PRODUCER_ENGINE_ID
    }
    assert {payload["value_schema_version"] for payload in payloads} == {
        FAST_VALUE_SCHEMA_VERSION
    }


def _cross_market_pack_contracts(
    alignment_policy: str,
) -> tuple[tuple[CrossMarketFeatureDefinition, ...], FeatureSetSpec]:
    registry_reader = EmptyRegistryReader()
    definitions = tuple(
        build_cross_market_feature_definition(
            feature_name,
            _approved_request(feature_name),
            registry_reader,
            dataset_version_ids=(DATASET_ID,),
            window_length=WINDOW_LENGTH,
            horizon=1,
            reset_on_session=True,
            ddof=0,
            alignment_policy=alignment_policy,
        )
        for feature_name in PACK_FEATURES
    )
    feature_set = FeatureSetSpec(
        feature_set_id="feature_set_fast_path_cross_market_v1",
        feature_set_version="v1",
        features=tuple(definition.spec.feature_spec for definition in definitions),
        description="V1 Cross-Market fast pack parity fixture.",
        metadata={"campaign": "FEATURE_COMPUTE_FAST_PATH_V1", "phase": "FCFP-P09"},
    )
    return definitions, feature_set


def _assert_fixture_coverage(
    records: dict[CrossMarketFeatureName, tuple[FeatureValueRecord, ...]],
) -> None:
    snapshots = align_cross_market_rows(
        cross_market_input_bundle(),
        reset_on_session=True,
        alignment_policy="strict_intersection",
    )
    assert missing_rty_event_ts() not in {snapshot.event_ts for snapshot in snapshots}

    spread = records[CrossMarketFeatureName.NQ_MINUS_ES_RETURN_SPREAD]
    delayed_record = _record_at(spread, delayed_nq_available_ts())
    assert delayed_record.value is not None
    assert delayed_record.quality_flags == (
        "bbo_gap",
        "missing_bbo",
        "nq_bbo_gap",
    )

    no_trade_record = _event_record(spread, no_trade_event_ts())
    assert no_trade_record.value is None
    assert "input_gap" in no_trade_record.quality_flags
    assert "no_trade" in no_trade_record.quality_flags
    assert "es_return_gap" in no_trade_record.quality_flags

    synchronized = records[CrossMarketFeatureName.SYNCHRONIZED_RETURNS]
    reset_record = _event_record(synchronized, session_reset_event_ts())
    assert reset_record.value is None
    assert "session_reset" in reset_record.quality_flags

    beta = records[CrossMarketFeatureName.NQ_ES_ROLLING_BETA_RESIDUAL]
    correlation = records[CrossMarketFeatureName.NQ_ES_ROLLING_CORRELATION]
    assert any("insufficient_window" in record.quality_flags for record in beta)
    assert any("input_gap" in record.quality_flags for record in beta)
    assert any("zero_benchmark_variance" in record.quality_flags for record in beta)
    assert any("zero_target_variance" in record.quality_flags for record in correlation)


def _record_at(
    records: tuple[FeatureValueRecord, ...],
    available_ts: object,
) -> FeatureValueRecord:
    for record in records:
        if record.available_ts == available_ts:
            return record
    raise AssertionError(f"missing record at {available_ts!r}")


def _event_record(
    records: tuple[FeatureValueRecord, ...],
    event_ts: object,
) -> FeatureValueRecord:
    for record in records:
        if record.event_ts == event_ts:
            return record
    raise AssertionError(f"missing record event {event_ts!r}")


def _records_by_feature_version(
    records: tuple[FeatureValueRecord, ...],
) -> dict[str, tuple[FeatureValueRecord, ...]]:
    grouped: dict[str, list[FeatureValueRecord]] = defaultdict(list)
    for record in records:
        grouped[record.feature_version_id].append(record)
    return {feature_version_id: tuple(values) for feature_version_id, values in grouped.items()}


def _approved_request(feature: CrossMarketFeatureName) -> FeatureRequest:
    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    return create_feature_request(
        alpha_spec_id=ALPHA_SPEC_ID,
        requested_inputs=[f"cross_market_{feature.value}"],
        formula_sketch={
            "exposure_family": f"cross_market_{feature.value}",
            "inputs": ["canonical_ohlcv"],
            "markets": ["ES", "NQ", "RTY"],
            "operation": feature.value,
            "alignment_policy": "strict_intersection",
        },
        availability_assumptions={
            "timing": "output waits for all same-event contributing instrument rows",
            "forbidden": "no cross-instrument forward-fill or missing-instrument imputation",
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": ["close", "event_ts", "available_ts", "quality_flags"],
            "source": "tiny synthetic ES/NQ/RTY fixture",
        },
        approval_status=FeatureRequestApprovalStatus.APPROVED,
    )
