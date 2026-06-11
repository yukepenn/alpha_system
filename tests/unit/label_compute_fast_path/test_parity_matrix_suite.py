from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal

import pytest

from alpha_system.data.foundation.rolls import (
    build_analytic_cme_equity_index_quarterly_roll_calendar,
)
from alpha_system.features.input_views import (
    CanonicalInputViews,
    build_bbo_input_view,
    build_ohlcv_input_view,
)
from alpha_system.labels.fast import (
    COST_ADJUSTED_LABEL_IDS,
    FIXED_HORIZON_LABEL_IDS,
    PATH_LABEL_IDS,
    SESSION_MAINTENANCE_LABEL_IDS,
    FastLabelMaterializer,
    TerminalGuardDisposition,
    TerminalKind,
    TerminalRequest,
    build_cost_adjusted_label_pack,
    build_fixed_horizon_label_pack,
    build_path_label_pack,
    build_session_maintenance_label_pack,
    build_shared_label_panel,
    resolve_terminal_indices,
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
    OVERLAP_METADATA_VERSION,
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
from alpha_system.labels.roll_guard import RollCrossPolicy, RollGuardAction, evaluate_roll_guard
from alpha_system.labels.version import LabelValueRecord
from tests.fixtures.feature_compute_fast_path.fixed_horizon_label import (
    BBO_MISSING_SOURCE_INDEX,
    BBO_QUARANTINED_TERMINAL_INDEX,
    DATASET_ID as FIXED_DATASET_ID,
    MAINTENANCE_SOURCE_INDEX,
    MAINTENANCE_TERMINAL_INDEX,
    NO_TRADE_TERMINAL_INDEX,
    PARTITION_ID as FIXED_PARTITION_ID,
    ROLL_SOURCE_INDEX,
    ROW_COUNT,
    fixed_horizon_bbo_rows,
    fixed_horizon_ohlcv_rows,
    governed_fixed_horizon_label_specs,
)
from tests.fixtures.feature_label.synthetic import accepted_version
from tests.fixtures.label_compute_fast_path.path_labels import (
    DATASET_ID as PATH_DATASET_ID,
    MAINTENANCE_SOURCE_TS as PATH_MAINTENANCE_SOURCE_TS,
    PARTITION_ID as PATH_PARTITION_ID,
    ROLL_SOURCE_TS as PATH_ROLL_SOURCE_TS,
    SAME_BAR_SOURCE_TS,
    SESSION_GAP_SOURCE_TS as PATH_SESSION_GAP_SOURCE_TS,
    TIMEOUT_SOURCE_TS,
    maintenance_crossing_ohlcv_rows,
    path_kernel_ohlcv_rows,
    path_label_specs,
    roll_crossing_ohlcv_rows,
    session_gap_ohlcv_rows,
)
from tests.fixtures.label_compute_fast_path.session_cost_labels import (
    COST_MISSING_SOURCE_TS,
    COST_NORMAL_SOURCE_TS,
    COST_TERMINAL_GAP_SOURCE_TS,
    DATASET_ID as SESSION_COST_DATASET_ID,
    MAINTENANCE_NORMAL_SOURCE_TS,
    PARTITION_ID as SESSION_COST_PARTITION_ID,
    ROLL_SOURCE_TS as SESSION_ROLL_SOURCE_TS,
    SESSION_GAP_SOURCE_TS,
    SESSION_NORMAL_SOURCE_TS,
    cost_adjusted_bbo_rows,
    cost_adjusted_label_specs,
    cost_adjusted_ohlcv_rows,
    session_maintenance_label_specs,
    session_maintenance_ohlcv_rows,
)
from tests.unit.feature_compute_fast_path.parity_harness import (
    LabelParityStats,
    LabelParityTolerance,
    assert_and_summarize_label_records_match,
)

COMMON_PARITY_DIMENSIONS = frozenset(
    {
        "label_value",
        "label_available_ts_exact",
        "horizon_end_ts_exact",
        "label_spec_id_exact",
        "label_version_id_exact",
        "quality_flags_exact",
    }
)
REQUIRED_DIMENSIONS_BY_FAMILY = {
    "fixed_horizon": COMMON_PARITY_DIMENSIONS
    | {
        "roll_crossing_guard_exact",
        "maintenance_crossing_guard_exact",
        "gap_missingness_flags_exact",
        "horizon_overlap_metadata_preserved",
    },
    "session_maintenance": COMMON_PARITY_DIMENSIONS
    | {
        "roll_crossing_guard_exact",
        "maintenance_crossing_guard_exact",
        "session_gap_exact",
        "gap_missingness_flags_exact",
    },
    "cost_adjusted": COMMON_PARITY_DIMENSIONS
    | {
        "maintenance_crossing_guard_exact",
        "bbo_missingness_exact",
        "gap_missingness_flags_exact",
        "cost_profile_consistency",
    },
    "path": COMMON_PARITY_DIMENSIONS
    | {
        "roll_crossing_guard_exact",
        "maintenance_crossing_guard_exact",
        "same_bar_barrier_policy_exact",
        "session_gap_exact",
        "barrier_never_touched_exact",
        "gap_missingness_flags_exact",
    },
}


@dataclass(frozen=True, slots=True)
class MatrixCase:
    family: str
    label_id: str
    stats: LabelParityStats
    dimensions: frozenset[str]


def test_campaign_level_parity_matrix_covers_every_fast_label_family_and_dimension() -> None:
    pytest.importorskip("polars")

    cases = (
        *_fixed_horizon_cases(),
        *_session_maintenance_cases(),
        *_cost_adjusted_cases(),
        *_path_cases(),
    )

    labels_by_family: dict[str, set[str]] = defaultdict(set)
    dimensions_by_family: dict[str, set[str]] = defaultdict(set)
    for case in cases:
        labels_by_family[case.family].add(case.label_id)
        dimensions_by_family[case.family].update(case.dimensions)
        assert case.stats.record_count > 0
        assert case.stats.compared_value_count == case.stats.record_count
        if case.stats.tolerance.abs == 0.0 and case.stats.tolerance.rel == 0.0:
            assert case.stats.max_abs_diff == 0.0
            assert case.stats.median_abs_diff == 0.0
        else:
            assert case.stats.max_abs_diff <= case.stats.tolerance.abs

    assert labels_by_family == {
        "fixed_horizon": set(FIXED_HORIZON_LABEL_IDS),
        "session_maintenance": set(SESSION_MAINTENANCE_LABEL_IDS),
        "cost_adjusted": set(COST_ADJUSTED_LABEL_IDS),
        "path": set(PATH_LABEL_IDS),
    }
    for family, required_dimensions in REQUIRED_DIMENSIONS_BY_FAMILY.items():
        assert required_dimensions.issubset(dimensions_by_family[family])


def test_required_guard_and_missingness_cases_are_exercised_by_the_matrix() -> None:
    pytest.importorskip("polars")

    fixed_definitions = _fixed_horizon_definitions()
    fixed_reference = _fixed_horizon_reference_records(fixed_definitions)
    fixed_fast = _fixed_horizon_fast_records(fixed_definitions)
    fixed_trade_records = tuple(
        record
        for definition in fixed_definitions
        if not definition.name.value.startswith("mid_")
        for record in fixed_fast[definition.label_version_id]
    )
    fixed_mid_records = tuple(
        record
        for definition in fixed_definitions
        if definition.name.value.startswith("mid_")
        for record in fixed_fast[definition.label_version_id]
    )
    _assert_fixed_fixture_indices_are_present()
    assert any(
        {"source_not_trade", "roll_splice_boundary", "no_trade"}.issubset(
            record.quality_flags
        )
        for record in fixed_trade_records
    )
    assert any(
        {"horizon_not_trade", "maintenance_crossing", "no_trade"}.issubset(
            record.quality_flags
        )
        for record in fixed_trade_records
    ) or any(
        {"horizon_not_trade", "no_trade"}.issubset(record.quality_flags)
        for record in fixed_trade_records
    )
    assert any(
        {"bbo_gap", "source_bbo_gap", "missing_bbo"}.issubset(record.quality_flags)
        for record in fixed_mid_records
    )
    assert any(
        {"bbo_gap", "horizon_bbo_gap", "bbo_quarantined"}.issubset(record.quality_flags)
        for record in fixed_mid_records
    )
    assert all(fixed_reference[definition.name] for definition in fixed_definitions)

    session_definitions = _session_maintenance_definitions()
    session_reference = _session_maintenance_reference_records(session_definitions)
    session_fast = _session_maintenance_fast_records(session_definitions)
    for definition in session_definitions:
        assert_and_summarize_label_records_match(
            session_reference[definition.name],
            session_fast[definition.label_version_id],
            expected_label_version_id=definition.label_version_id,
        )
    session_records = session_fast[_definition_by_name(
        session_definitions,
        FixedHorizonLabelName.SESSION_CLOSE,
    ).label_version_id]
    maintenance_records = session_fast[_definition_by_name(
        session_definitions,
        FixedHorizonLabelName.MAINTENANCE_FLAT,
    ).label_version_id]
    assert _has_event(session_records, SESSION_NORMAL_SOURCE_TS)
    assert not _has_event(session_records, SESSION_GAP_SOURCE_TS)
    assert not _has_event(session_records, SESSION_ROLL_SOURCE_TS)
    assert _has_event(maintenance_records, MAINTENANCE_NORMAL_SOURCE_TS)
    assert not _has_event(maintenance_records, SESSION_ROLL_SOURCE_TS)

    cost_definitions = _cost_adjusted_definitions()
    cost_reference = _cost_adjusted_reference_records(cost_definitions)
    cost_fast = _cost_adjusted_fast_records(cost_definitions)
    spread_definition = _cost_definition_by_name(
        cost_definitions,
        CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET,
    )
    spread_records = cost_fast[spread_definition.label_version_id]
    assert _record_by_event(spread_records, COST_NORMAL_SOURCE_TS).value is not None
    assert _record_by_event(spread_records, COST_TERMINAL_GAP_SOURCE_TS).quality_flags == (
        "label_gap",
        "terminal_bbo_gap",
        "bbo_gap",
        "missing_bbo",
    )
    assert _record_by_event(spread_records, COST_MISSING_SOURCE_TS).quality_flags == (
        "label_gap",
        "missing_terminal_bbo",
    )
    for definition in cost_definitions:
        assert_and_summarize_label_records_match(
            cost_reference[definition.name],
            cost_fast[definition.label_version_id],
            expected_label_version_id=definition.label_version_id,
            tolerance=_FLOAT_PANEL_TOLERANCE,
        )

    path_definitions = _path_definitions()
    path_reference = _path_reference_records(path_definitions)
    path_fast = _path_fast_records(path_definitions)
    target_before_stop = path_fast[_path_definition_by_name(
        path_definitions,
        PathLabelName.TARGET_BEFORE_STOP,
    ).label_version_id]
    triple_barrier = path_fast[_path_definition_by_name(
        path_definitions,
        PathLabelName.TRIPLE_BARRIER,
    ).label_version_id]
    assert _record_by_event(target_before_stop, SAME_BAR_SOURCE_TS).value is None
    assert _record_by_event(target_before_stop, SAME_BAR_SOURCE_TS).quality_flags == (
        "ambiguous_same_bar_barrier",
    )
    assert _record_by_event(triple_barrier, TIMEOUT_SOURCE_TS).value == 0
    assert _record_by_event(triple_barrier, TIMEOUT_SOURCE_TS).quality_flags == (
        "horizon_no_barrier",
    )
    for definition in path_definitions:
        assert_and_summarize_label_records_match(
            path_reference[definition.name],
            path_fast[definition.label_version_id],
            expected_label_version_id=definition.label_version_id,
            tolerance=_FLOAT_PANEL_TOLERANCE,
        )
    assert _path_session_gap_records() == ()
    _assert_path_crossing_row_drops(roll_crossing_ohlcv_rows(), PATH_ROLL_SOURCE_TS, "roll")
    _assert_path_crossing_row_drops(
        maintenance_crossing_ohlcv_rows(),
        PATH_MAINTENANCE_SOURCE_TS,
        "maintenance_crossing",
    )


@pytest.mark.parametrize(
    ("same_bar_policy", "target_before_stop", "triple_barrier"),
    (
        ("ambiguous", None, None),
        ("target_first", True, 1),
        ("stop_first", False, -1),
    ),
)
def test_same_bar_barrier_policy_variants_match_reference_exactly(
    same_bar_policy: str,
    target_before_stop: bool | None,
    triple_barrier: int | None,
) -> None:
    pytest.importorskip("polars")

    definitions = _path_definitions(same_bar_policy=same_bar_policy)
    reference_records = _path_reference_records(definitions)
    fast_records = _path_fast_records(definitions)
    for definition in definitions:
        assert_and_summarize_label_records_match(
            reference_records[definition.name],
            fast_records[definition.label_version_id],
            expected_label_version_id=definition.label_version_id,
            tolerance=_FLOAT_PANEL_TOLERANCE,
        )

    fast_tbs = _record_by_event(
        fast_records[_path_definition_by_name(
            definitions,
            PathLabelName.TARGET_BEFORE_STOP,
        ).label_version_id],
        SAME_BAR_SOURCE_TS,
    )
    fast_triple = _record_by_event(
        fast_records[_path_definition_by_name(
            definitions,
            PathLabelName.TRIPLE_BARRIER,
        ).label_version_id],
        SAME_BAR_SOURCE_TS,
    )
    assert fast_tbs.value is target_before_stop
    assert fast_triple.value == triple_barrier


@pytest.mark.parametrize("policy", tuple(RollCrossPolicy))
def test_roll_policy_terminal_dispositions_match_reference_guard(policy: RollCrossPolicy) -> None:
    calendar = build_analytic_cme_equity_index_quarterly_roll_calendar(
        root_symbols=("ES",),
        start_year=2024,
        end_year=2024,
    )
    roll_record = next(record for record in calendar if record.root_symbol == "ES")
    source_ts = datetime.combine(
        roll_record.roll_date - timedelta(days=1),
        time(23, 45),
        tzinfo=UTC,
    )
    terminal_ts = source_ts + timedelta(minutes=240)
    truncate_ts = datetime.combine(roll_record.roll_date, time.min, tzinfo=UTC)
    rows = (
        _policy_row(source_ts, close=Decimal("100")),
        _policy_row(truncate_ts, close=Decimal("100.5")),
        _policy_row(terminal_ts, close=Decimal("101")),
    )
    panel = build_shared_label_panel(
        symbol="ES",
        year=source_ts.year,
        ohlcv_rows=rows,
        roll_calendar=calendar,
        root_symbol="ES",
    )
    model = resolve_terminal_indices(
        panel,
        TerminalRequest(
            kind=TerminalKind.FIXED_HORIZON,
            horizon_minutes=240,
            roll_policy=policy,
        ),
    )
    resolution = model.resolutions[0]
    verdict = evaluate_roll_guard(
        entry_ts=source_ts,
        label_horizon_ts=terminal_ts,
        calendar=calendar,
        policy=policy,
        root_symbol="ES",
    )

    assert verdict.requested_policy is policy
    assert resolution.roll_policy is policy
    assert resolution.reason == verdict.reason
    if verdict.action is RollGuardAction.DROP:
        assert resolution.disposition is TerminalGuardDisposition.DROP
        assert resolution.terminal_index is None
    elif verdict.action is RollGuardAction.TRUNCATE:
        assert resolution.disposition is TerminalGuardDisposition.TRUNCATE
        assert resolution.effective_terminal_ts == truncate_ts
        assert resolution.terminal_index is not None
        assert panel.row_at(resolution.terminal_index).event_ts == truncate_ts
    elif verdict.action is RollGuardAction.FLAG:
        assert resolution.disposition is TerminalGuardDisposition.FLAG
        assert resolution.terminal_index is not None
        assert panel.row_at(resolution.terminal_index).event_ts == terminal_ts
        assert "roll_splice_flag" in resolution.quality_flags
    elif verdict.action is RollGuardAction.INVALID:
        assert resolution.disposition is TerminalGuardDisposition.INVALID
        assert resolution.terminal_index is None
    else:
        raise AssertionError(f"unexpected roll guard action: {verdict.action}")


_FLOAT_PANEL_TOLERANCE = LabelParityTolerance(
    abs=1e-12,
    rel=1e-12,
    reason="Decimal reference arithmetic is compared to float shared-panel arithmetic",
)


def _fixed_horizon_cases() -> tuple[MatrixCase, ...]:
    definitions = _fixed_horizon_definitions()
    reference_records = _fixed_horizon_reference_records(definitions)
    fast_records, computation = _fixed_horizon_fast_records_with_metadata(definitions)
    _assert_fixed_overlap_metadata(computation.metadata.labels, reference_records, definitions)
    return tuple(
        MatrixCase(
            family="fixed_horizon",
            label_id=definition.name.value,
            stats=assert_and_summarize_label_records_match(
                reference_records[definition.name],
                fast_records[definition.label_version_id],
                expected_label_version_id=definition.label_version_id,
            ),
            dimensions=REQUIRED_DIMENSIONS_BY_FAMILY["fixed_horizon"],
        )
        for definition in definitions
    )


def _session_maintenance_cases() -> tuple[MatrixCase, ...]:
    definitions = _session_maintenance_definitions()
    reference_records = _session_maintenance_reference_records(definitions)
    fast_records = _session_maintenance_fast_records(definitions)
    return tuple(
        MatrixCase(
            family="session_maintenance",
            label_id=definition.name.value,
            stats=assert_and_summarize_label_records_match(
                reference_records[definition.name],
                fast_records[definition.label_version_id],
                expected_label_version_id=definition.label_version_id,
            ),
            dimensions=REQUIRED_DIMENSIONS_BY_FAMILY["session_maintenance"],
        )
        for definition in definitions
    )


def _cost_adjusted_cases() -> tuple[MatrixCase, ...]:
    definitions = _cost_adjusted_definitions()
    reference_records = _cost_adjusted_reference_records(definitions)
    fast_records = _cost_adjusted_fast_records(definitions)
    return tuple(
        MatrixCase(
            family="cost_adjusted",
            label_id=definition.name.value,
            stats=assert_and_summarize_label_records_match(
                reference_records[definition.name],
                fast_records[definition.label_version_id],
                expected_label_version_id=definition.label_version_id,
                tolerance=_FLOAT_PANEL_TOLERANCE,
            ),
            dimensions=REQUIRED_DIMENSIONS_BY_FAMILY["cost_adjusted"],
        )
        for definition in definitions
    )


def _path_cases() -> tuple[MatrixCase, ...]:
    definitions = _path_definitions()
    reference_records = _path_reference_records(definitions)
    fast_records = _path_fast_records(definitions)
    return tuple(
        MatrixCase(
            family="path",
            label_id=definition.name.value,
            stats=assert_and_summarize_label_records_match(
                reference_records[definition.name],
                fast_records[definition.label_version_id],
                expected_label_version_id=definition.label_version_id,
                tolerance=_FLOAT_PANEL_TOLERANCE,
            ),
            dimensions=REQUIRED_DIMENSIONS_BY_FAMILY["path"],
        )
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


def _fixed_horizon_reference_records(
    definitions: tuple[FixedHorizonLabelDefinition, ...],
) -> dict[FixedHorizonLabelName, tuple[LabelValueRecord, ...]]:
    accepted = accepted_version(FIXED_DATASET_ID)
    views = CanonicalInputViews(
        ohlcv=build_ohlcv_input_view(
            accepted,
            fixed_horizon_ohlcv_rows(),
            partition_id=FIXED_PARTITION_ID,
            purpose="lcfp_p07_fixed_horizon_reference",
        ),
        bbo=build_bbo_input_view(
            accepted,
            fixed_horizon_bbo_rows(),
            partition_id=FIXED_PARTITION_ID,
            purpose="lcfp_p07_fixed_horizon_reference",
        ),
    )
    return compute_fixed_horizon_labels(definitions, views)


def _fixed_horizon_fast_records(
    definitions: tuple[FixedHorizonLabelDefinition, ...],
) -> dict[str, tuple[LabelValueRecord, ...]]:
    return _fixed_horizon_fast_records_with_metadata(definitions)[0]


def _fixed_horizon_fast_records_with_metadata(
    definitions: tuple[FixedHorizonLabelDefinition, ...],
):
    materializer = FastLabelMaterializer()
    computation = materializer.compute_values_with_metadata(
        materializer.frame_from_rows(
            ohlcv_rows=fixed_horizon_ohlcv_rows(),
            bbo_rows=fixed_horizon_bbo_rows(),
        ),
        build_fixed_horizon_label_pack(definitions),
    )
    return _records_by_label_version(computation.records), computation


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


def _session_maintenance_reference_records(
    definitions: tuple[FixedHorizonLabelDefinition, ...],
) -> dict[FixedHorizonLabelName, tuple[LabelValueRecord, ...]]:
    accepted = accepted_version(SESSION_COST_DATASET_ID)
    return compute_fixed_horizon_labels(
        definitions,
        build_ohlcv_input_view(
            accepted,
            session_maintenance_ohlcv_rows(),
            partition_id=SESSION_COST_PARTITION_ID,
            purpose="lcfp_p07_session_maintenance_reference",
        ),
    )


def _session_maintenance_fast_records(
    definitions: tuple[FixedHorizonLabelDefinition, ...],
) -> dict[str, tuple[LabelValueRecord, ...]]:
    materializer = FastLabelMaterializer()
    computation = materializer.compute_values_with_metadata(
        materializer.frame_from_rows(
            ohlcv_rows=session_maintenance_ohlcv_rows(),
            bbo_rows=(),
        ),
        build_session_maintenance_label_pack(definitions),
    )
    return _records_by_label_version(computation.records)


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


def _cost_adjusted_reference_records(
    definitions: tuple[CostAdjustedLabelDefinition, ...],
) -> dict[CostAdjustedLabelName, tuple[LabelValueRecord, ...]]:
    accepted = accepted_version(SESSION_COST_DATASET_ID)
    ohlcv_view = build_ohlcv_input_view(
        accepted,
        cost_adjusted_ohlcv_rows(),
        partition_id=SESSION_COST_PARTITION_ID,
        purpose="lcfp_p07_cost_adjusted_reference",
    )
    bbo_view = build_bbo_input_view(
        accepted,
        cost_adjusted_bbo_rows(),
        partition_id=SESSION_COST_PARTITION_ID,
        purpose="lcfp_p07_cost_adjusted_reference",
    )
    return compute_cost_adjusted_labels(definitions, bbo_view, trade_rows=ohlcv_view.rows)


def _cost_adjusted_fast_records(
    definitions: tuple[CostAdjustedLabelDefinition, ...],
) -> dict[str, tuple[LabelValueRecord, ...]]:
    materializer = FastLabelMaterializer()
    computation = materializer.compute_values_with_metadata(
        materializer.frame_from_rows(
            ohlcv_rows=cost_adjusted_ohlcv_rows(),
            bbo_rows=cost_adjusted_bbo_rows(),
        ),
        build_cost_adjusted_label_pack(definitions),
    )
    return _records_by_label_version(computation.records)


def _path_definitions(
    *,
    horizon_steps: int = 3,
    same_bar_policy: str = "ambiguous",
) -> tuple[PathLabelDefinition, ...]:
    specs = path_label_specs(horizon_steps=horizon_steps, same_bar_policy=same_bar_policy)
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


def _path_reference_records(
    definitions: tuple[PathLabelDefinition, ...],
) -> dict[PathLabelName, tuple[LabelValueRecord, ...]]:
    accepted = accepted_version(PATH_DATASET_ID)
    return compute_path_labels(
        definitions,
        build_ohlcv_input_view(
            accepted,
            path_kernel_ohlcv_rows(),
            partition_id=PATH_PARTITION_ID,
            purpose="lcfp_p07_path_reference",
        ),
    )


def _path_fast_records(
    definitions: tuple[PathLabelDefinition, ...],
) -> dict[str, tuple[LabelValueRecord, ...]]:
    materializer = FastLabelMaterializer()
    computation = materializer.compute_values_with_metadata(
        materializer.frame_from_rows(
            ohlcv_rows=path_kernel_ohlcv_rows(),
            bbo_rows=(),
        ),
        build_path_label_pack(definitions),
    )
    return _records_by_label_version(computation.records)


def _path_session_gap_records() -> tuple[LabelValueRecord, ...]:
    definition = _path_definitions()[0]
    accepted = accepted_version(PATH_DATASET_ID)
    reference_records = compute_path_labels(
        (definition,),
        build_ohlcv_input_view(
            accepted,
            session_gap_ohlcv_rows(),
            partition_id=PATH_PARTITION_ID,
            purpose="lcfp_p07_path_session_gap_reference",
        ),
    )[definition.name]
    assert reference_records == ()
    materializer = FastLabelMaterializer()
    return materializer.compute_values_with_metadata(
        materializer.frame_from_rows(
            ohlcv_rows=session_gap_ohlcv_rows(),
            bbo_rows=(),
        ),
        build_path_label_pack((definition,)),
    ).records


def _assert_path_crossing_row_drops(
    ohlcv_rows: tuple[dict[str, object], ...],
    source_ts: datetime,
    reason_token: str,
) -> None:
    definition = _path_definitions(horizon_steps=240)[0]
    panel = build_shared_label_panel(
        symbol="ES",
        year=source_ts.year,
        ohlcv_rows=ohlcv_rows,
        root_symbol="ES",
    )
    terminal_model = resolve_terminal_indices(
        panel,
        TerminalRequest(
            kind=TerminalKind.FIXED_HORIZON,
            horizon_minutes=definition.horizon_steps,
        ),
    )
    source_resolution = terminal_model.resolutions[0]
    assert source_resolution.disposition is TerminalGuardDisposition.DROP
    assert reason_token in source_resolution.reason

    materializer = FastLabelMaterializer()
    computation = materializer.compute_values_with_metadata(
        materializer.frame_from_rows(ohlcv_rows=ohlcv_rows, bbo_rows=()),
        build_path_label_pack((definition,)),
    )
    assert computation.records == ()


def _assert_fixed_overlap_metadata(
    metadata_labels,
    reference_records: dict[FixedHorizonLabelName, tuple[LabelValueRecord, ...]],
    definitions: tuple[FixedHorizonLabelDefinition, ...],
) -> None:
    metadata_by_label = {item.label_version_id: item for item in metadata_labels}
    for definition in definitions:
        label_metadata = metadata_by_label[definition.label_version_id]
        overlap = label_metadata.horizon_overlap_metadata
        assert label_metadata.n_eff == len(reference_records[definition.name])
        assert label_metadata.horizon_overlap_event_count > 0
        assert label_metadata.null_value_count == sum(
            1 for record in reference_records[definition.name] if record.value is None
        )
        assert overlap["metadata_version"] == OVERLAP_METADATA_VERSION
        assert overlap["label_id"] == definition.label_id
        assert overlap["horizon_minutes"] == definition.horizon_minutes
        assert overlap["raw_row_count"] == len(reference_records[definition.name])
        assert overlap["effective_sample_count"] <= len(reference_records[definition.name])


def _assert_fixed_fixture_indices_are_present() -> None:
    assert ROLL_SOURCE_INDEX < ROW_COUNT
    assert NO_TRADE_TERMINAL_INDEX < ROW_COUNT
    assert MAINTENANCE_SOURCE_INDEX < ROW_COUNT
    assert MAINTENANCE_TERMINAL_INDEX < ROW_COUNT
    assert BBO_MISSING_SOURCE_INDEX < ROW_COUNT
    assert BBO_QUARANTINED_TERMINAL_INDEX < ROW_COUNT


def _records_by_label_version(
    records: tuple[LabelValueRecord, ...],
) -> dict[str, tuple[LabelValueRecord, ...]]:
    grouped: dict[str, list[LabelValueRecord]] = defaultdict(list)
    for record in records:
        grouped[record.label_version_id].append(record)
    return {label_version_id: tuple(values) for label_version_id, values in grouped.items()}


def _definition_by_name(
    definitions: tuple[FixedHorizonLabelDefinition, ...],
    label_name: FixedHorizonLabelName,
) -> FixedHorizonLabelDefinition:
    matches = tuple(definition for definition in definitions if definition.name is label_name)
    assert len(matches) == 1
    return matches[0]


def _cost_definition_by_name(
    definitions: tuple[CostAdjustedLabelDefinition, ...],
    label_name: CostAdjustedLabelName,
) -> CostAdjustedLabelDefinition:
    matches = tuple(definition for definition in definitions if definition.name is label_name)
    assert len(matches) == 1
    return matches[0]


def _path_definition_by_name(
    definitions: tuple[PathLabelDefinition, ...],
    label_name: PathLabelName,
) -> PathLabelDefinition:
    matches = tuple(definition for definition in definitions if definition.name is label_name)
    assert len(matches) == 1
    return matches[0]


def _has_event(records: tuple[LabelValueRecord, ...], event_ts: datetime) -> bool:
    return any(record.event_ts == event_ts for record in records)


def _record_by_event(
    records: tuple[LabelValueRecord, ...],
    event_ts: datetime,
) -> LabelValueRecord:
    matches = tuple(record for record in records if record.event_ts == event_ts)
    assert len(matches) == 1
    return matches[0]


def _policy_row(event_ts: datetime, *, close: Decimal) -> dict[str, object]:
    return {
        "instrument_id": "ES",
        "contract_id": "ESH4",
        "series_id": "ES_POLICY",
        "bar_start_ts": (event_ts - timedelta(minutes=1)).isoformat(),
        "bar_end_ts": event_ts.isoformat(),
        "event_ts": event_ts.isoformat(),
        "available_ts": (event_ts + timedelta(seconds=1)).isoformat(),
        "ingested_at": (event_ts + timedelta(seconds=2)).isoformat(),
        "open": str(close),
        "high": str(close + Decimal("0.25")),
        "low": str(close - Decimal("0.25")),
        "close": str(close),
        "volume": "10",
        "source": "dsrc_synthetic_fixture",
        "source_request_id": "synthetic_lcfp_p07_roll_policy",
        "data_version": "dsv_lcfp_p07_roll_policy",
        "quality_flags": [],
        "session_label": "RTH",
    }
