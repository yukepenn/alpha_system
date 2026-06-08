from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from alpha_system.features.families.ohlcv import (
    OHLCVFeatureName,
    build_ohlcv_feature_definition,
    compute_ohlcv_feature,
)
from alpha_system.features.families.structure import (
    StructureFeatureName,
    build_structure_feature_definition,
    compute_structure_feature,
)
from alpha_system.features.input_views import OHLCVInputRow, OHLCVInputView
from alpha_system.features.scaleout import load_scaleout_config, run_scaleout
from alpha_system.governance.duplicate_exposure import (
    ExposureCheckResult,
    ExposureRegistryStatus,
)
from alpha_system.governance.feature_request import (
    FeatureRequest,
    FeatureRequestApprovalStatus,
    create_feature_request,
)

ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd0"
CONFIG_PATH = "configs/features/scaleout/volume_activity.json"
DATASET_VERSION_ID = "dsv_databento_ohlcv_05404069799decb0"

P11_OHLCV_PRIMITIVES = (
    OHLCVFeatureName.ROLLING_VOLUME,
    OHLCVFeatureName.VOLUME_ZSCORE,
    OHLCVFeatureName.SESSION_MINUTE,
    OHLCVFeatureName.ROLLING_RANGE,
    OHLCVFeatureName.RANGE_POSITION,
    OHLCVFeatureName.TRENDINESS,
)
P11_STRUCTURE_PRIMITIVES = (
    StructureFeatureName.CLOSE_LOCATION_VALUE,
    StructureFeatureName.WICK_REJECTION_SCORE,
)
P11_PRIMITIVE_COUNT = len(P11_OHLCV_PRIMITIVES) + len(P11_STRUCTURE_PRIMITIVES)


class EmptyRegistryReader:
    def read_factor_versions(self) -> list[dict[str, object]]:
        return []


def test_volume_activity_scaleout_preview_maps_existing_primitives() -> None:
    config = load_scaleout_config(CONFIG_PATH)

    summary = run_scaleout(config, rollout="bounded-real")

    assert config.family == "volume_activity"
    assert config.feature_names == (
        "participation",
        "time_of_day_relative_volume",
        "volume_regime",
        "activity_bursts",
        "effort_result_proxies",
    )
    assert summary.accepted_unit_count == 24
    assert summary.bounded_unit_count == 3
    assert summary.failed_count == 0
    assert {record.unit.symbol for record in summary.records} == {"ES", "NQ", "RTY"}
    version_sets = [set(record.feature_version_ids) for record in summary.records]
    assert len(set.union(*version_sets)) == P11_PRIMITIVE_COUNT * len(summary.records)
    for record in summary.records:
        assert len(record.feature_version_ids) == P11_PRIMITIVE_COUNT
        assert all(version_id.startswith("fver_") for version_id in record.feature_version_ids)


def test_volume_activity_primitives_preserve_current_available_ts() -> None:
    rows = _rows()
    view = OHLCVInputView(rows)
    ohlcv_definitions = tuple(
        build_ohlcv_feature_definition(
            name,
            _approved_request(f"ohlcv_{name.value}"),
            EmptyRegistryReader(),
            dataset_version_ids=(DATASET_VERSION_ID,),
            window_length=3 if name is not OHLCVFeatureName.SESSION_MINUTE else 1,
            input_scope={"symbol": "ES", "partition_id": "ES.2024.synthetic"},
        )
        for name in P11_OHLCV_PRIMITIVES
    )
    structure_definitions = tuple(
        build_structure_feature_definition(
            name,
            _approved_request(f"structure_{name.value}"),
            EmptyRegistryReader(),
            dataset_version_ids=(DATASET_VERSION_ID,),
            window_length=3,
            input_scope={"symbol": "ES", "partition_id": "ES.2024.synthetic"},
        )
        for name in P11_STRUCTURE_PRIMITIVES
    )

    ohlcv_records = {
        definition.name: compute_ohlcv_feature(definition, view)
        for definition in ohlcv_definitions
    }
    structure_records = {
        definition.name: compute_structure_feature(definition, view)
        for definition in structure_definitions
    }

    expected_available_ts = [row.available_ts for row in rows]
    for records in (*ohlcv_records.values(), *structure_records.values()):
        assert [record.available_ts for record in records] == expected_available_ts
        assert all(record.available_ts >= record.event_ts for record in records)
        assert all(record.feature_version_id.startswith("fver_") for record in records)

    assert ohlcv_records[OHLCVFeatureName.SESSION_MINUTE][2].value == 2
    assert ohlcv_records[OHLCVFeatureName.ROLLING_VOLUME][2].value == 550.0
    assert structure_records[StructureFeatureName.CLOSE_LOCATION_VALUE][3].value is not None
    assert structure_records[StructureFeatureName.WICK_REJECTION_SCORE][3].value is not None


def _rows() -> tuple[OHLCVInputRow, ...]:
    start = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
    bars = (
        (Decimal("100"), Decimal("101"), Decimal("99"), Decimal("100"), Decimal("100")),
        (Decimal("101"), Decimal("102"), Decimal("100"), Decimal("101"), Decimal("150")),
        (Decimal("101"), Decimal("104"), Decimal("100"), Decimal("103"), Decimal("300")),
        (Decimal("103"), Decimal("105"), Decimal("102"), Decimal("104"), Decimal("450")),
        (Decimal("104"), Decimal("106"), Decimal("103"), Decimal("105"), Decimal("250")),
    )
    return tuple(
        _row(
            start + timedelta(minutes=index),
            open_=open_,
            high=high,
            low=low,
            close=close,
            volume=volume,
        )
        for index, (open_, high, low, close, volume) in enumerate(bars)
    )


def _row(
    bar_start_ts: datetime,
    *,
    open_: Decimal,
    high: Decimal,
    low: Decimal,
    close: Decimal,
    volume: Decimal,
) -> OHLCVInputRow:
    return OHLCVInputRow(
        instrument_id="ES",
        contract_id="ESM4",
        series_id="ES.c.0",
        bar_start_ts=bar_start_ts,
        bar_end_ts=bar_start_ts + timedelta(minutes=1),
        event_ts=bar_start_ts + timedelta(minutes=1),
        available_ts=bar_start_ts + timedelta(minutes=1, seconds=1),
        ingested_at=bar_start_ts + timedelta(minutes=1, seconds=2),
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=volume,
        data_version=DATASET_VERSION_ID,
        quality_flags=(),
        session_label="RTH",
    )


def _approved_request(feature_name: str) -> FeatureRequest:
    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    return create_feature_request(
        alpha_spec_id=ALPHA_SPEC_ID,
        requested_inputs=[f"volume_activity_{feature_name}"],
        formula_sketch={
            "exposure_family": f"volume_activity_{feature_name}",
            "inputs": ["ohlcv_1m"],
            "operation": feature_name,
            "window": "causal_point_in_time_or_rolling",
        },
        availability_assumptions={
            "timing": "feature value is emitted at the current row available_ts",
            "forbidden": "no future label, final-session aggregate, or new volume primitive is used",
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": ["open", "high", "low", "close", "volume", "session_label", "available_ts"],
            "source": "tiny synthetic OHLCV fixture",
        },
        approval_status=FeatureRequestApprovalStatus.APPROVED,
    )
