from __future__ import annotations

from collections import defaultdict

import pytest

from alpha_system.features.input_views import (
    CanonicalInputViews,
    build_bbo_input_view,
    build_ohlcv_input_view,
)
from alpha_system.labels.fast import (
    FastLabelMaterializer,
    FastLabelPack,
    build_cost_adjusted_label_pack,
    build_fixed_horizon_label_pack,
    build_path_label_pack,
    build_session_maintenance_label_pack,
)
from alpha_system.labels.families.cost_adjusted import (
    CostAdjustedLabelDefinition,
    CostAdjustedLabelName,
    build_cost_adjusted_label_definition,
    compute_cost_adjusted_labels,
)
from alpha_system.labels.families.fixed_horizon import (
    FixedHorizonLabelDefinition,
    FixedHorizonLabelName,
    build_fixed_horizon_label_definition,
    compute_fixed_horizon_labels,
    supported_fixed_horizon_labels,
)
from alpha_system.labels.families.path import (
    PathLabelDefinition,
    PathLabelName,
    build_path_label_definition,
    compute_path_labels,
)
from alpha_system.labels.version import LabelContractError, LabelContractSpec, LabelValueRecord
from tests.fixtures.feature_compute_fast_path.fixed_horizon_label import (
    DATASET_ID as FIXED_DATASET_ID,
    PARTITION_ID as FIXED_PARTITION_ID,
    fixed_horizon_bbo_rows,
    fixed_horizon_ohlcv_rows,
    governed_fixed_horizon_label_specs,
)
from tests.fixtures.feature_label.synthetic import accepted_version
from tests.fixtures.label_compute_fast_path.path_labels import (
    DATASET_ID as PATH_DATASET_ID,
    PARTITION_ID as PATH_PARTITION_ID,
    path_kernel_ohlcv_rows,
    path_label_specs,
)
from tests.fixtures.label_compute_fast_path.session_cost_labels import (
    DATASET_ID as SESSION_COST_DATASET_ID,
    PARTITION_ID as SESSION_COST_PARTITION_ID,
    cost_adjusted_bbo_rows,
    cost_adjusted_label_specs,
    cost_adjusted_ohlcv_rows,
    session_maintenance_label_specs,
    session_maintenance_ohlcv_rows,
)


def test_fast_label_available_ts_never_precedes_reference_derivation() -> None:
    pytest.importorskip("polars")

    for record_sets in (
        _fixed_horizon_record_sets(),
        _session_maintenance_record_sets(),
        _cost_adjusted_record_sets(),
        _path_record_sets(),
    ):
        for reference_records, fast_records in record_sets:
            reference_by_key = {_record_key(record): record for record in reference_records}
            fast_by_key = {_record_key(record): record for record in fast_records}
            assert fast_by_key.keys() == reference_by_key.keys()
            for key, fast in fast_by_key.items():
                reference = reference_by_key[key]
                assert fast.label_available_ts == reference.label_available_ts
                assert fast.label_available_ts >= reference.label_available_ts
                assert fast.label_available_ts >= fast.horizon_end_ts
                assert fast.label_available_ts > fast.event_ts


def test_fast_label_packs_use_label_only_canonical_input_contracts() -> None:
    definitions_and_packs = (
        (_fixed_horizon_definitions(), build_fixed_horizon_label_pack),
        (_session_maintenance_definitions(), build_session_maintenance_label_pack),
        (_cost_adjusted_definitions(), build_cost_adjusted_label_pack),
        (_path_definitions(), build_path_label_pack),
    )

    for definitions, pack_builder in definitions_and_packs:
        pack = pack_builder(definitions)
        assert isinstance(pack, FastLabelPack)
        assert pack.label_version_ids == tuple(
            definition.label_version_id for definition in definitions
        )
        for definition in definitions:
            contract = _contract(definition)
            assert contract.availability_policy.future_data_legal_only_for_labels
            assert set(contract.inputs.input_views).issubset(
                {"canonical_ohlcv", "canonical_bbo", "dense_grid_ohlcv"}
            )
            assert all("label" not in field.lower() for field in contract.inputs.fields)
            if contract.path.window is not None:
                assert contract.path.window.offline_only is True

            clean = contract.validate_live_feature_references(
                {
                    "features": [
                        {
                            "feature_id": "base_ohlcv_close",
                            "available_at": "2020-01-01T00:00:00+00:00",
                        }
                    ]
                }
            )
            assert clean.is_clean is True
            with pytest.raises(LabelContractError, match="live feature"):
                contract.validate_live_feature_references(
                    {
                        "features": [
                            {
                                "feature_id": contract.label_id,
                                "available_at": "2099-01-01T00:00:00+00:00",
                            }
                        ]
                    }
                )


def _fixed_horizon_record_sets() -> tuple[tuple[LabelValueRecord, ...], ...]:
    definitions = _fixed_horizon_definitions()
    accepted = accepted_version(FIXED_DATASET_ID)
    views = CanonicalInputViews(
        ohlcv=build_ohlcv_input_view(
            accepted,
            fixed_horizon_ohlcv_rows(),
            partition_id=FIXED_PARTITION_ID,
            purpose="lcfp_p07_no_lookahead_fixed_reference",
        ),
        bbo=build_bbo_input_view(
            accepted,
            fixed_horizon_bbo_rows(),
            partition_id=FIXED_PARTITION_ID,
            purpose="lcfp_p07_no_lookahead_fixed_reference",
        ),
    )
    reference = compute_fixed_horizon_labels(definitions, views)
    materializer = FastLabelMaterializer()
    fast = _records_by_label_version(
        materializer.compute_values_with_metadata(
            materializer.frame_from_rows(
                ohlcv_rows=fixed_horizon_ohlcv_rows(),
                bbo_rows=fixed_horizon_bbo_rows(),
            ),
            build_fixed_horizon_label_pack(definitions),
        ).records
    )
    return tuple(
        (reference[definition.name], fast[definition.label_version_id])
        for definition in definitions
    )


def _session_maintenance_record_sets() -> tuple[tuple[LabelValueRecord, ...], ...]:
    definitions = _session_maintenance_definitions()
    accepted = accepted_version(SESSION_COST_DATASET_ID)
    reference = compute_fixed_horizon_labels(
        definitions,
        build_ohlcv_input_view(
            accepted,
            session_maintenance_ohlcv_rows(),
            partition_id=SESSION_COST_PARTITION_ID,
            purpose="lcfp_p07_no_lookahead_session_reference",
        ),
    )
    materializer = FastLabelMaterializer()
    fast = _records_by_label_version(
        materializer.compute_values_with_metadata(
            materializer.frame_from_rows(
                ohlcv_rows=session_maintenance_ohlcv_rows(),
                bbo_rows=(),
            ),
            build_session_maintenance_label_pack(definitions),
        ).records
    )
    return tuple(
        (reference[definition.name], fast[definition.label_version_id])
        for definition in definitions
    )


def _cost_adjusted_record_sets() -> tuple[tuple[LabelValueRecord, ...], ...]:
    definitions = _cost_adjusted_definitions()
    accepted = accepted_version(SESSION_COST_DATASET_ID)
    ohlcv_view = build_ohlcv_input_view(
        accepted,
        cost_adjusted_ohlcv_rows(),
        partition_id=SESSION_COST_PARTITION_ID,
        purpose="lcfp_p07_no_lookahead_cost_reference",
    )
    bbo_view = build_bbo_input_view(
        accepted,
        cost_adjusted_bbo_rows(),
        partition_id=SESSION_COST_PARTITION_ID,
        purpose="lcfp_p07_no_lookahead_cost_reference",
    )
    reference = compute_cost_adjusted_labels(definitions, bbo_view, trade_rows=ohlcv_view.rows)
    materializer = FastLabelMaterializer()
    fast = _records_by_label_version(
        materializer.compute_values_with_metadata(
            materializer.frame_from_rows(
                ohlcv_rows=cost_adjusted_ohlcv_rows(),
                bbo_rows=cost_adjusted_bbo_rows(),
            ),
            build_cost_adjusted_label_pack(definitions),
        ).records
    )
    return tuple(
        (reference[definition.name], fast[definition.label_version_id])
        for definition in definitions
    )


def _path_record_sets() -> tuple[tuple[LabelValueRecord, ...], ...]:
    definitions = _path_definitions()
    accepted = accepted_version(PATH_DATASET_ID)
    reference = compute_path_labels(
        definitions,
        build_ohlcv_input_view(
            accepted,
            path_kernel_ohlcv_rows(),
            partition_id=PATH_PARTITION_ID,
            purpose="lcfp_p07_no_lookahead_path_reference",
        ),
    )
    materializer = FastLabelMaterializer()
    fast = _records_by_label_version(
        materializer.compute_values_with_metadata(
            materializer.frame_from_rows(ohlcv_rows=path_kernel_ohlcv_rows(), bbo_rows=()),
            build_path_label_pack(definitions),
        ).records
    )
    return tuple(
        (reference[definition.name], fast[definition.label_version_id])
        for definition in definitions
    )


def _fixed_horizon_definitions() -> tuple[FixedHorizonLabelDefinition, ...]:
    specs = governed_fixed_horizon_label_specs()
    return tuple(
        build_fixed_horizon_label_definition(
            label_name,
            specs[label_name],
            dataset_version_ids=(FIXED_DATASET_ID,),
        )
        for label_name in supported_fixed_horizon_labels()
        if label_name
        not in {
            FixedHorizonLabelName.SESSION_CLOSE,
            FixedHorizonLabelName.MAINTENANCE_FLAT,
        }
    )


def _session_maintenance_definitions() -> tuple[FixedHorizonLabelDefinition, ...]:
    specs = session_maintenance_label_specs()
    return tuple(
        build_fixed_horizon_label_definition(
            label_name,
            specs[label_name],
            dataset_version_ids=(SESSION_COST_DATASET_ID,),
        )
        for label_name in (
            FixedHorizonLabelName.SESSION_CLOSE,
            FixedHorizonLabelName.MAINTENANCE_FLAT,
        )
    )


def _cost_adjusted_definitions() -> tuple[CostAdjustedLabelDefinition, ...]:
    specs = cost_adjusted_label_specs()
    return tuple(
        build_cost_adjusted_label_definition(
            label_name,
            specs[label_name],
            dataset_version_ids=(SESSION_COST_DATASET_ID,),
        )
        for label_name in (
            CostAdjustedLabelName.COST_ADJUSTED_FWD_RET,
            CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET,
        )
    )


def _path_definitions() -> tuple[PathLabelDefinition, ...]:
    specs = path_label_specs()
    return tuple(
        build_path_label_definition(
            label_name,
            specs[label_name],
            dataset_version_ids=(PATH_DATASET_ID,),
        )
        for label_name in (
            PathLabelName.MFE,
            PathLabelName.MAE,
            PathLabelName.TARGET_BEFORE_STOP,
            PathLabelName.TRIPLE_BARRIER,
        )
    )


def _records_by_label_version(
    records: tuple[LabelValueRecord, ...],
) -> dict[str, tuple[LabelValueRecord, ...]]:
    grouped: dict[str, list[LabelValueRecord]] = defaultdict(list)
    for record in records:
        grouped[record.label_version_id].append(record)
    return {label_version_id: tuple(values) for label_version_id, values in grouped.items()}


def _contract(
    definition: FixedHorizonLabelDefinition | CostAdjustedLabelDefinition | PathLabelDefinition,
) -> LabelContractSpec:
    if isinstance(definition, CostAdjustedLabelDefinition):
        return definition.spec.label_contract
    return definition.contract


def _record_key(record: LabelValueRecord) -> tuple[str, str, object]:
    return (record.label_version_id, record.entity_id, record.event_ts)
