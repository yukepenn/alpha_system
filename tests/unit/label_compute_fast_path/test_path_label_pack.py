from __future__ import annotations

from collections import defaultdict

import pytest

from alpha_system.features.input_views import build_ohlcv_input_view
from alpha_system.labels.fast import (
    PATH_LABEL_IDS,
    FastLabelMaterializer,
    TerminalGuardDisposition,
    TerminalKind,
    TerminalRequest,
    build_path_label_pack,
    build_shared_label_panel,
    path_label_pack_coverage,
    resolve_terminal_indices,
)
from alpha_system.labels.families.path import (
    PathLabelDefinition,
    PathLabelName,
    build_path_label_definition,
    compute_path_labels,
)
from alpha_system.labels.version import LabelValueRecord
from tests.fixtures.feature_label.synthetic import accepted_version
from tests.fixtures.label_compute_fast_path.path_labels import (
    DATASET_ID,
    MAINTENANCE_SOURCE_TS,
    PARTITION_ID,
    ROLL_SOURCE_TS,
    SAME_BAR_SOURCE_TS,
    SESSION_GAP_SOURCE_TS,
    STOP_FIRST_SOURCE_TS,
    TARGET_FIRST_SOURCE_TS,
    TIMEOUT_SOURCE_TS,
    maintenance_crossing_ohlcv_rows,
    path_kernel_ohlcv_rows,
    path_label_specs,
    roll_crossing_ohlcv_rows,
    session_gap_ohlcv_rows,
)
from tests.unit.feature_compute_fast_path.parity_harness import (
    LabelParityTolerance,
    assert_label_records_match,
)


def test_path_label_pack_matches_reference_for_kernelized_scan_cases() -> None:
    pytest.importorskip("polars")
    accepted = accepted_version(DATASET_ID)
    definitions = _definitions()
    ohlcv_rows = path_kernel_ohlcv_rows()
    reference_records = compute_path_labels(
        definitions,
        build_ohlcv_input_view(
            accepted,
            ohlcv_rows,
            partition_id=PARTITION_ID,
            purpose="lcfp_p05_path_reference",
        ),
    )

    materializer = FastLabelMaterializer()
    computation = materializer.compute_values_with_metadata(
        materializer.frame_from_rows(ohlcv_rows=ohlcv_rows, bbo_rows=()),
        build_path_label_pack(definitions),
    )
    fast_records = _records_by_label_version(computation.records)

    assert PATH_LABEL_IDS == ("mfe", "mae", "target_before_stop", "triple_barrier")
    coverage = path_label_pack_coverage()
    assert coverage.kernelized_label_ids == PATH_LABEL_IDS
    assert coverage.fallback_label_ids == PATH_LABEL_IDS
    tolerance = LabelParityTolerance(
        abs=1e-12,
        rel=1e-12,
        reason="Decimal reference path arithmetic is compared to float panel arithmetic",
    )
    for definition in definitions:
        assert_label_records_match(
            reference_records[definition.name],
            fast_records[definition.label_version_id],
            expected_label_version_id=definition.label_version_id,
            tolerance=tolerance,
        )

    tbs_records = reference_records[PathLabelName.TARGET_BEFORE_STOP]
    triple_records = reference_records[PathLabelName.TRIPLE_BARRIER]
    assert _record_by_event(tbs_records, TARGET_FIRST_SOURCE_TS).value is True
    assert _record_by_event(tbs_records, STOP_FIRST_SOURCE_TS).value is False
    assert _record_by_event(tbs_records, SAME_BAR_SOURCE_TS).value is None
    assert _record_by_event(tbs_records, SAME_BAR_SOURCE_TS).quality_flags == (
        "ambiguous_same_bar_barrier",
    )
    timeout = _record_by_event(triple_records, TIMEOUT_SOURCE_TS)
    assert timeout.value == 0
    assert timeout.quality_flags == ("horizon_no_barrier",)


@pytest.mark.parametrize(
    ("same_bar_policy", "target_before_stop", "triple_barrier"),
    (
        ("ambiguous", None, None),
        ("target_first", True, 1),
        ("stop_first", False, -1),
    ),
)
def test_same_bar_policy_matches_reference_exactly(
    same_bar_policy: str,
    target_before_stop: bool | None,
    triple_barrier: int | None,
) -> None:
    pytest.importorskip("polars")
    accepted = accepted_version(DATASET_ID)
    definitions = _definitions(same_bar_policy=same_bar_policy)
    ohlcv_rows = path_kernel_ohlcv_rows()
    reference_records = compute_path_labels(
        definitions,
        build_ohlcv_input_view(
            accepted,
            ohlcv_rows,
            partition_id=PARTITION_ID,
            purpose=f"lcfp_p05_path_same_bar_{same_bar_policy}",
        ),
    )

    materializer = FastLabelMaterializer()
    computation = materializer.compute_values_with_metadata(
        materializer.frame_from_rows(ohlcv_rows=ohlcv_rows, bbo_rows=()),
        build_path_label_pack(definitions),
    )
    fast_records = _records_by_label_version(computation.records)
    for definition in definitions:
        assert_label_records_match(
            reference_records[definition.name],
            fast_records[definition.label_version_id],
            expected_label_version_id=definition.label_version_id,
            tolerance=LabelParityTolerance(
                abs=1e-12,
                rel=1e-12,
                reason="Decimal reference path arithmetic is compared to float panel arithmetic",
            ),
        )

    fast_tbs = _record_by_event(
        fast_records[_definition(PathLabelName.TARGET_BEFORE_STOP, definitions).label_version_id],
        SAME_BAR_SOURCE_TS,
    )
    fast_triple = _record_by_event(
        fast_records[_definition(PathLabelName.TRIPLE_BARRIER, definitions).label_version_id],
        SAME_BAR_SOURCE_TS,
    )
    assert fast_tbs.value is target_before_stop
    assert fast_triple.value == triple_barrier


def test_session_gap_source_row_is_omitted_like_reference() -> None:
    pytest.importorskip("polars")
    accepted = accepted_version(DATASET_ID)
    definition = _definitions()[0]
    ohlcv_rows = session_gap_ohlcv_rows()
    reference_records = compute_path_labels(
        (definition,),
        build_ohlcv_input_view(
            accepted,
            ohlcv_rows,
            partition_id=PARTITION_ID,
            purpose="lcfp_p05_path_session_gap_reference",
        ),
    )[definition.name]

    materializer = FastLabelMaterializer()
    computation = materializer.compute_values_with_metadata(
        materializer.frame_from_rows(ohlcv_rows=ohlcv_rows, bbo_rows=()),
        build_path_label_pack((definition,)),
    )

    assert reference_records == ()
    assert computation.records == ()
    assert all(record.event_ts != SESSION_GAP_SOURCE_TS for record in computation.records)


@pytest.mark.parametrize(
    ("rows_factory", "source_ts", "reason_token"),
    (
        (roll_crossing_ohlcv_rows, ROLL_SOURCE_TS, "roll"),
        (maintenance_crossing_ohlcv_rows, MAINTENANCE_SOURCE_TS, "maintenance_crossing"),
    ),
)
def test_path_pack_uses_p02_terminal_guards_for_crossing_rows(
    rows_factory,
    source_ts,
    reason_token: str,
) -> None:
    pytest.importorskip("polars")
    ohlcv_rows = rows_factory()
    definition = _definitions(horizon_steps=240)[0]
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


def _definitions(
    *,
    horizon_steps: int = 3,
    same_bar_policy: str = "ambiguous",
) -> tuple[PathLabelDefinition, ...]:
    specs = path_label_specs(horizon_steps=horizon_steps, same_bar_policy=same_bar_policy)
    return tuple(
        build_path_label_definition(
            label_name,
            specs[label_name],
            dataset_version_ids=(DATASET_ID,),
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


def _record_by_event(
    records: tuple[LabelValueRecord, ...],
    event_ts,
) -> LabelValueRecord:
    matches = tuple(record for record in records if record.event_ts == event_ts)
    assert len(matches) == 1
    return matches[0]


def _definition(
    label_name: PathLabelName,
    definitions: tuple[PathLabelDefinition, ...],
) -> PathLabelDefinition:
    matches = tuple(definition for definition in definitions if definition.name is label_name)
    assert len(matches) == 1
    return matches[0]


@pytest.mark.parametrize(
    ("rows_factory", "expected_full_window_entries"),
    (
        # 7 rows around the maintenance break + timestamp gap, horizon 3:
        # the reference emits the 4 entries with full positional windows.
        ("maintenance_gap_recovery", 4),
        # 8 contiguous rows inside the ES analytic roll window, horizon 3:
        # the reference applies no roll guard and emits 5 entries.
        ("roll_window_recovery", 5),
    ),
)
def test_mfe_record_set_matches_reference_across_gaps_and_roll_windows(
    rows_factory: str,
    expected_full_window_entries: int,
) -> None:
    """Regression for LCFP-P08 finding 3 (1628 missing fast mfe records).

    The reference path family resolves horizons positionally over real trade
    bars with no roll or maintenance terminal guard; the fast kernel must emit
    exactly the same record set on panels containing maintenance breaks,
    timestamp gaps, and roll windows.
    """

    pytest.importorskip("polars")
    from tests.fixtures.label_compute_fast_path.path_labels import (
        maintenance_gap_recovery_ohlcv_rows,
        roll_window_recovery_ohlcv_rows,
    )

    ohlcv_rows = (
        maintenance_gap_recovery_ohlcv_rows()
        if rows_factory == "maintenance_gap_recovery"
        else roll_window_recovery_ohlcv_rows()
    )
    accepted = accepted_version(DATASET_ID)
    definitions = _definitions(horizon_steps=3)

    # Prove the fixture actually triggers the pre-repair drop mechanism: the
    # fixed-minute guarded terminal model (which the old kernel consumed)
    # drops at least one entry that the reference emits positionally.
    panel = build_shared_label_panel(
        symbol="ES",
        year=2024,
        ohlcv_rows=ohlcv_rows,
        root_symbol="ES",
    )
    guarded = resolve_terminal_indices(
        panel,
        TerminalRequest(kind=TerminalKind.FIXED_HORIZON, horizon_minutes=3),
    )
    assert any(
        resolution.disposition is TerminalGuardDisposition.DROP
        for resolution in guarded.resolutions
    ), "fixture no longer exercises the guarded-drop mechanism"

    reference_records = compute_path_labels(
        definitions,
        build_ohlcv_input_view(
            accepted,
            ohlcv_rows,
            partition_id=PARTITION_ID,
            purpose=f"lcfp_p08_repair_{rows_factory}_reference",
        ),
    )

    materializer = FastLabelMaterializer()
    computation = materializer.compute_values_with_metadata(
        materializer.frame_from_rows(ohlcv_rows=ohlcv_rows, bbo_rows=()),
        build_path_label_pack(definitions),
    )
    fast_records = _records_by_label_version(computation.records)

    mfe_definition = _definition(PathLabelName.MFE, definitions)
    mfe_reference = reference_records[PathLabelName.MFE]
    mfe_fast = fast_records.get(mfe_definition.label_version_id, ())

    # The mechanism requires the reference to emit records here at all.
    assert len(mfe_reference) == expected_full_window_entries
    reference_keys = {(record.entity_id, record.event_ts) for record in mfe_reference}
    fast_keys = {(record.entity_id, record.event_ts) for record in mfe_fast}
    assert fast_keys == reference_keys, (
        f"missing_fast_records={len(reference_keys - fast_keys)} "
        f"extra_fast_records={len(fast_keys - reference_keys)}"
    )
    tolerance = LabelParityTolerance(
        abs=1e-12,
        rel=1e-12,
        reason="Decimal reference path arithmetic is compared to float panel arithmetic",
    )
    for definition in definitions:
        assert_label_records_match(
            reference_records[definition.name],
            fast_records.get(definition.label_version_id, ()),
            expected_label_version_id=definition.label_version_id,
            tolerance=tolerance,
        )
