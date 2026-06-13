from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping

import pytest

from alpha_system.core.value_store import compute_value_content_hash, write_parquet_values
from alpha_system.governance.feature_lock_validation import FeatureLockValidationError
from alpha_system.governance.study_spec import generate_study_spec_id, validate_study_spec
from alpha_system.governance.surrogate_run import CALIBRATION_BLOCKED
from alpha_system.governance.validation import GovernanceValidationError
from tests._helpers.local_data import skip_unless_local_registry
from tools.discovery_rigor_floor.run_real_surrogate_calibration import (
    _aligned_factor_value_series,
    _declared_factor_ids,
    _declared_feature_family,
    _expected_sub_config_count,
    _factor_series_is_zero_variance,
    _load_study_spec,
    _select_label_locks,
    _staged_sub_config_is_constant_factor,
    run_real_surrogate_calibration,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
COMMITTED_STUDY_SPEC = (
    REPO_ROOT
    / "research/futures_substrate_scaleout_v1/rerun/study_specs/"
    "sspec_19cbe3c2c973ef68130b6224.json"
)
KILL_SHOT_RERUN_SPECS = {
    "sspec_f6cbd88caa0445f0f56d81fd": (
        "base_ohlcv_vwap",
        "base_ohlcv_anchored_vwap",
        "base_ohlcv_distance_to_vwap",
        "base_ohlcv_opening_range",
        "base_ohlcv_overnight_range",
        "base_ohlcv_session_minute",
    ),
    "sspec_1604b063f3a3401208ee0239": (
        "base_ohlcv_vwap",
        "base_ohlcv_anchored_vwap",
        "base_ohlcv_distance_to_vwap",
        "base_ohlcv_opening_range",
        "base_ohlcv_overnight_range",
        "base_ohlcv_session_minute",
    ),
    "sspec_dec89a327a9c50957adca780": (
        "base_ohlcv_trendiness",
        "base_ohlcv_atr",
        "liquidity_structure_range_contraction",
        "base_ohlcv_rolling_range",
        "base_ohlcv_returns",
    ),
    "sspec_840e8342564226f2c3257903": (
        "liquidity_structure_prior_high_distance",
        "liquidity_structure_prior_low_distance",
        "liquidity_structure_sweep_high_flag",
        "liquidity_structure_sweep_low_flag",
        "liquidity_structure_failed_high_breakout_flag",
        "liquidity_structure_failed_low_breakout_flag",
        "liquidity_structure_close_location_value",
        "liquidity_structure_wick_rejection_score",
        "liquidity_structure_range_contraction",
    ),
    "sspec_c237c6a8ce40c2585836fae0": (
        "liquidity_structure_prior_high_distance",
        "liquidity_structure_prior_low_distance",
        "liquidity_structure_sweep_high_flag",
        "liquidity_structure_sweep_low_flag",
        "liquidity_structure_failed_high_breakout_flag",
        "liquidity_structure_failed_low_breakout_flag",
        "liquidity_structure_close_location_value",
        "liquidity_structure_wick_rejection_score",
        "liquidity_structure_range_contraction",
    ),
    "sspec_533f665ec4ac063dbb664a54": (
        "bbo_tradability_mid",
        "bbo_tradability_spread_zscore",
        "bbo_tradability_spread",
        "bbo_tradability_spread_ticks",
        "bbo_tradability_top_book_depth",
        "bbo_tradability_top_book_imbalance",
        "bbo_tradability_missing_bbo_flag",
        "bbo_tradability_bad_quote_flag",
        "bbo_tradability_wide_spread_flag",
        "bbo_tradability_low_depth_flag",
        "bbo_tradability_microprice",
    ),
}


def test_real_surrogate_calibration_tool_resolves_locked_packs_via_resolver(
    tmp_path: Path,
) -> None:
    feature_version_id = "fver_" + "1" * 64
    label_version_id = "lver_" + "2" * 64
    spec_path = _study_spec_file(
        tmp_path,
        feature_version_id=feature_version_id,
        label_version_id=label_version_id,
    )
    feature_rows, label_rows = _value_rows(
        feature_version_id=feature_version_id,
        label_version_id=label_version_id,
    )
    feature_path = _write_jsonl(tmp_path / "feature-values.jsonl", feature_rows)
    label_path = _write_jsonl(tmp_path / "label-values.jsonl", label_rows)
    resolver = _FakeResolver(
        feature_record=_FeatureRecord(
            feature_version_id=feature_version_id,
            materialization_output_path=feature_path.as_posix(),
            value_content_hash=compute_value_content_hash(feature_rows),
        ),
        label_record=_LabelRecord(
            label_version_id=label_version_id,
            materialization_output_path=label_path.as_posix(),
            value_content_hash=compute_value_content_hash(label_rows),
        ),
    )
    namespace = tmp_path / "rigor_p05_surrogate_real_tool"
    namespace.mkdir()
    report_path = tmp_path / "report.md"
    base_seed = _base_seed_without_bootstrap_identity(label_rows)

    result = run_real_surrogate_calibration(
        study_spec_path=spec_path,
        alpha_data_root=tmp_path / "alpha_data",
        runs_per_config=1,
        base_seed=base_seed,
        namespace=namespace,
        report_out=report_path,
        resolver=resolver,
    )

    assert result["accepted"] is True
    assert result["run_count"] == 2
    assert result["gate_pass_count"] == 0
    assert result["statistic_pass_count"] == 0
    assert result["eligibility_clean_count"] == 0
    assert resolver.label_calls
    assert resolver.feature_calls
    rendered = report_path.read_text(encoding="utf-8")
    assert "Declared K per perturbation config: 1" in rendered
    assert "zero passes in K bounds false-pass rate at about 3/K at 95%" in rendered
    assert "Statistic pass count: 0" in rendered
    assert "Eligibility clean count: 0" in rendered
    assert "trade_date_block_shuffle" in rendered
    assert "trade_date_block_bootstrap" in rendered
    staged_labels = tuple(
        (namespace / "real_surrogate_inputs" / result["study_spec_id"]).glob(
            "**/labels.jsonl"
        )
    )
    assert len(staged_labels) == 1
    assert json.loads(staged_labels[0].read_text(encoding="utf-8").splitlines()[0])[
        "event_ts"
    ].startswith("2026-01-02")


def test_real_surrogate_calibration_rescores_existing_seed_outputs(
    tmp_path: Path,
) -> None:
    feature_version_id = "fver_" + "1" * 64
    label_version_id = "lver_" + "2" * 64
    spec_path = _study_spec_file(
        tmp_path,
        feature_version_id=feature_version_id,
        label_version_id=label_version_id,
    )
    feature_rows, label_rows = _value_rows(
        feature_version_id=feature_version_id,
        label_version_id=label_version_id,
    )
    feature_path = _write_jsonl(tmp_path / "feature-values.jsonl", feature_rows)
    label_path = _write_jsonl(tmp_path / "label-values.jsonl", label_rows)
    resolver = _FakeResolver(
        feature_record=_FeatureRecord(
            feature_version_id=feature_version_id,
            materialization_output_path=feature_path.as_posix(),
            value_content_hash=compute_value_content_hash(feature_rows),
        ),
        label_record=_LabelRecord(
            label_version_id=label_version_id,
            materialization_output_path=label_path.as_posix(),
            value_content_hash=compute_value_content_hash(label_rows),
        ),
    )
    namespace = tmp_path / "rigor_p05_surrogate_rescore"
    namespace.mkdir()
    base_seed = _base_seed_without_bootstrap_identity(label_rows)
    fresh = run_real_surrogate_calibration(
        study_spec_path=spec_path,
        alpha_data_root=tmp_path / "alpha_data",
        runs_per_config=1,
        base_seed=base_seed,
        namespace=namespace,
        report_out=tmp_path / "fresh.md",
        resolver=resolver,
    )

    rescored = run_real_surrogate_calibration(
        study_spec_path=spec_path,
        alpha_data_root=tmp_path / "alpha_data",
        runs_per_config=1,
        base_seed=base_seed,
        namespace=namespace,
        report_out=tmp_path / "rescored.md",
        rescore_existing=True,
    )

    for key in (
        "accepted",
        "run_count",
        "error_count",
        "gate_pass_count",
        "statistic_pass_count",
        "eligibility_clean_count",
        "threshold_verdict",
        "surrogate_study_spec_id",
    ):
        assert rescored[key] == fresh[key]


def test_real_surrogate_rescore_marks_missing_diagnostic_summary_error(
    tmp_path: Path,
) -> None:
    feature_version_id = "fver_" + "1" * 64
    label_version_id = "lver_" + "2" * 64
    spec_path = _study_spec_file(
        tmp_path,
        feature_version_id=feature_version_id,
        label_version_id=label_version_id,
    )
    feature_rows, label_rows = _value_rows(
        feature_version_id=feature_version_id,
        label_version_id=label_version_id,
    )
    feature_path = _write_jsonl(tmp_path / "feature-values.jsonl", feature_rows)
    label_path = _write_jsonl(tmp_path / "label-values.jsonl", label_rows)
    resolver = _FakeResolver(
        feature_record=_FeatureRecord(
            feature_version_id=feature_version_id,
            materialization_output_path=feature_path.as_posix(),
            value_content_hash=compute_value_content_hash(feature_rows),
        ),
        label_record=_LabelRecord(
            label_version_id=label_version_id,
            materialization_output_path=label_path.as_posix(),
            value_content_hash=compute_value_content_hash(label_rows),
        ),
    )
    namespace = tmp_path / "rigor_p05_surrogate_rescore_missing"
    namespace.mkdir()
    base_seed = _base_seed_without_bootstrap_identity(label_rows)
    run_real_surrogate_calibration(
        study_spec_path=spec_path,
        alpha_data_root=tmp_path / "alpha_data",
        runs_per_config=1,
        base_seed=base_seed,
        namespace=namespace,
        report_out=tmp_path / "fresh.md",
        resolver=resolver,
    )
    missing = namespace / f"seed_{base_seed}" / "study_outputs" / "diagnostic_summary.json"
    missing.unlink()

    rescored = run_real_surrogate_calibration(
        study_spec_path=spec_path,
        alpha_data_root=tmp_path / "alpha_data",
        runs_per_config=1,
        base_seed=base_seed,
        namespace=namespace,
        report_out=tmp_path / "rescored-missing.md",
        rescore_existing=True,
    )

    assert rescored["accepted"] is False
    assert rescored["error_count"] == 1
    assert rescored["threshold_verdict"] == CALIBRATION_BLOCKED


def test_real_surrogate_calibration_filters_locked_versions_from_parquet(
    tmp_path: Path,
) -> None:
    pytest.importorskip("polars")
    feature_version_id = "fver_" + "1" * 64
    other_feature_version_id = "fver_" + "3" * 64
    label_version_id = "lver_" + "2" * 64
    other_label_version_id = "lver_" + "4" * 64
    spec_path = _study_spec_file(
        tmp_path,
        feature_version_id=feature_version_id,
        label_version_id=label_version_id,
    )
    feature_rows, label_rows = _value_rows(
        feature_version_id=feature_version_id,
        label_version_id=label_version_id,
    )
    other_feature_rows, other_label_rows = _value_rows(
        feature_version_id=other_feature_version_id,
        label_version_id=other_label_version_id,
    )
    mixed_feature_rows = feature_rows + other_feature_rows
    mixed_label_rows = label_rows + other_label_rows
    feature_hash = compute_value_content_hash(mixed_feature_rows)
    label_hash = compute_value_content_hash(mixed_label_rows)
    feature_parquet = tmp_path / "feature-values.parquet"
    label_parquet = tmp_path / "label-values.parquet"
    write_parquet_values(
        mixed_feature_rows,
        feature_parquet,
        plan_dict={"kind": "feature"},
        content_hash=feature_hash,
        schema_version="test",
        value_count=len(mixed_feature_rows),
    )
    write_parquet_values(
        mixed_label_rows,
        label_parquet,
        plan_dict={"kind": "label"},
        content_hash=label_hash,
        schema_version="test",
        value_count=len(mixed_label_rows),
    )
    resolver = _FakeResolver(
        feature_record=_FeatureRecord(
            feature_version_id=feature_version_id,
            materialization_output_path=(tmp_path / "feature.jsonl").as_posix(),
            value_store_format="parquet",
            parquet_path=feature_parquet.as_posix(),
            value_content_hash=feature_hash,
        ),
        label_record=_LabelRecord(
            label_version_id=label_version_id,
            materialization_output_path=(tmp_path / "label.jsonl").as_posix(),
            value_store_format="parquet",
            parquet_path=label_parquet.as_posix(),
            value_content_hash=label_hash,
        ),
    )
    namespace = tmp_path / "rigor_p05_surrogate_parquet_filter"
    namespace.mkdir()

    result = run_real_surrogate_calibration(
        study_spec_path=spec_path,
        alpha_data_root=tmp_path / "alpha_data",
        runs_per_config=1,
        base_seed=_base_seed_without_bootstrap_identity(label_rows),
        namespace=namespace,
        report_out=tmp_path / "report.md",
        resolver=resolver,
    )

    assert result["accepted"] is True
    staged_factor = tuple(
        (namespace / "real_surrogate_inputs" / result["study_spec_id"]).glob(
            "**/factor-values.jsonl"
        )
    )
    staged_label = tuple(
        (namespace / "real_surrogate_inputs" / result["study_spec_id"]).glob(
            "**/labels.jsonl"
        )
    )
    assert len(staged_factor) == 1
    assert len(staged_label) == 1
    staged_factor_rows = _read_jsonl(staged_factor[0])
    staged_label_rows = _read_jsonl(staged_label[0])
    assert len(staged_factor_rows) == len(feature_rows)
    assert len(staged_label_rows) == len(label_rows)
    assert {row["factor_version"] for row in staged_factor_rows} == {feature_version_id}
    assert {
        row["path_metadata"]["label_version"] for row in staged_label_rows
    } == {label_version_id}
    rendered = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert f"{len(feature_rows)}/{len(mixed_feature_rows)}" in rendered
    assert f"{len(label_rows)}/{len(mixed_label_rows)}" in rendered


def test_real_surrogate_calibration_records_all_null_factor_exclusion(
    tmp_path: Path,
) -> None:
    numeric_feature_version_id = "fver_" + "1" * 64
    null_feature_version_id = "fver_" + "3" * 64
    label_version_id = "lver_" + "2" * 64
    spec_path = _study_spec_file(
        tmp_path,
        feature_version_id=numeric_feature_version_id,
        label_version_id=label_version_id,
        feature_locks=(
            _feature_lock(
                feature_id="fixture_all_null_signal",
                feature_family="fixture_signal_family",
                feature_version_id=null_feature_version_id,
            ),
            _feature_lock(
                feature_id="fixture_close_delta",
                feature_family="fixture_signal_family",
                feature_version_id=numeric_feature_version_id,
            ),
        ),
    )
    numeric_feature_rows, label_rows = _value_rows(
        feature_version_id=numeric_feature_version_id,
        label_version_id=label_version_id,
    )
    null_feature_rows = _all_null_feature_rows(
        feature_version_id=null_feature_version_id,
        label_version_id=label_version_id,
    )
    feature_rows = null_feature_rows + numeric_feature_rows
    feature_hash = compute_value_content_hash(feature_rows)
    label_hash = compute_value_content_hash(label_rows)
    feature_path = _write_jsonl(tmp_path / "feature-values.jsonl", feature_rows)
    label_path = _write_jsonl(tmp_path / "label-values.jsonl", label_rows)
    resolver = _FakeResolver(
        feature_record={
            null_feature_version_id: _FeatureRecord(
                feature_version_id=null_feature_version_id,
                materialization_output_path=feature_path.as_posix(),
                value_content_hash=feature_hash,
                feature_spec=_FeatureSpec(feature_id="fixture_all_null_signal"),
            ),
            numeric_feature_version_id: _FeatureRecord(
                feature_version_id=numeric_feature_version_id,
                materialization_output_path=feature_path.as_posix(),
                value_content_hash=feature_hash,
                feature_spec=_FeatureSpec(feature_id="fixture_close_delta"),
            ),
        },
        label_record=_LabelRecord(
            label_version_id=label_version_id,
            materialization_output_path=label_path.as_posix(),
            value_content_hash=label_hash,
        ),
    )
    namespace = tmp_path / "rigor_p05_surrogate_all_null_exclusion"
    namespace.mkdir()
    report_path = tmp_path / "report.md"

    result = run_real_surrogate_calibration(
        study_spec_path=spec_path,
        alpha_data_root=tmp_path / "alpha_data",
        runs_per_config=1,
        base_seed=_base_seed_without_bootstrap_identity(label_rows),
        namespace=namespace,
        report_out=report_path,
        resolver=resolver,
    )

    assert result["accepted"] is True
    assert result["declared_factor_count"] == 2
    assert result["surrogate_study_spec_count"] == 1
    assert result["run_count"] == 2
    assert result["excluded_factor_count"] == 1
    assert result["excluded_factors"] == [
        {
            "factor_id": "fixture_all_null_signal",
            "feature_version_id": null_feature_version_id,
            "reason": "all_null_values",
            "partition": "SYNTH_2026_full_year",
            "total_rows": len(null_feature_rows),
            "null_rows": len(null_feature_rows),
            "numeric_rows": 0,
        }
    ]
    rendered = report_path.read_text(encoding="utf-8")
    assert "## excluded_factors" in rendered
    assert "`fixture_all_null_signal`" in rendered
    assert "`all_null_values`" in rendered
    staged_factor_paths = tuple(
        (namespace / "real_surrogate_inputs" / result["study_spec_id"]).glob(
            "**/factor-values.jsonl"
        )
    )
    assert len(staged_factor_paths) == 1
    assert {
        row["factor_id"]
        for row in _read_jsonl(staged_factor_paths[0])
    } == {"fixture_close_delta"}

    rescored = run_real_surrogate_calibration(
        study_spec_path=spec_path,
        alpha_data_root=tmp_path / "alpha_data",
        runs_per_config=1,
        base_seed=_base_seed_without_bootstrap_identity(label_rows),
        namespace=namespace,
        report_out=tmp_path / "rescored.md",
        rescore_existing=True,
    )

    assert rescored["accepted"] is True
    assert rescored["run_count"] == result["run_count"]
    assert rescored["excluded_factors"] == result["excluded_factors"]


def test_real_surrogate_calibration_refuses_when_all_declared_factors_all_null(
    tmp_path: Path,
) -> None:
    feature_version_id = "fver_" + "1" * 64
    label_version_id = "lver_" + "2" * 64
    spec_path = _study_spec_file(
        tmp_path,
        feature_version_id=feature_version_id,
        label_version_id=label_version_id,
    )
    feature_rows = _all_null_feature_rows(
        feature_version_id=feature_version_id,
        label_version_id=label_version_id,
    )
    _, label_rows = _value_rows(
        feature_version_id=feature_version_id,
        label_version_id=label_version_id,
    )
    feature_path = _write_jsonl(tmp_path / "feature-values.jsonl", feature_rows)
    label_path = _write_jsonl(tmp_path / "label-values.jsonl", label_rows)
    namespace = tmp_path / "rigor_p05_surrogate_all_null_refusal"
    namespace.mkdir()

    with pytest.raises(GovernanceValidationError) as exc_info:
        run_real_surrogate_calibration(
            study_spec_path=spec_path,
            alpha_data_root=tmp_path / "alpha_data",
            runs_per_config=1,
            base_seed=1,
            namespace=namespace,
            report_out=tmp_path / "report.md",
            resolver=_FakeResolver(
                feature_record=_FeatureRecord(
                    feature_version_id=feature_version_id,
                    materialization_output_path=feature_path.as_posix(),
                    value_content_hash=compute_value_content_hash(feature_rows),
                ),
                label_record=_LabelRecord(
                    label_version_id=label_version_id,
                    materialization_output_path=label_path.as_posix(),
                    value_content_hash=compute_value_content_hash(label_rows),
                ),
            ),
        )

    assert exc_info.value.issues[0].code == "no_numeric_declared_factors_for_surrogate"


def test_real_surrogate_calibration_refuses_jsonl_hash_mismatch_with_sibling(
    tmp_path: Path,
) -> None:
    healthy_feature_version_id = "fver_" + "1" * 64
    corrupted_feature_version_id = "fver_" + "3" * 64
    label_version_id = "lver_" + "2" * 64
    spec_path = _study_spec_file(
        tmp_path,
        feature_version_id=healthy_feature_version_id,
        label_version_id=label_version_id,
        feature_locks=(
            _feature_lock(
                feature_id="fixture_close_delta",
                feature_family="fixture_signal_family",
                feature_version_id=healthy_feature_version_id,
            ),
            _feature_lock(
                feature_id="fixture_hash_corrupted_null_signal",
                feature_family="fixture_signal_family",
                feature_version_id=corrupted_feature_version_id,
            ),
        ),
    )
    healthy_feature_rows, label_rows = _value_rows(
        feature_version_id=healthy_feature_version_id,
        label_version_id=label_version_id,
    )
    corrupted_feature_rows = _all_null_feature_rows(
        feature_version_id=corrupted_feature_version_id,
        label_version_id=label_version_id,
    )
    healthy_feature_path = _write_jsonl(
        tmp_path / "healthy-feature-values.jsonl",
        healthy_feature_rows,
    )
    corrupted_feature_path = _write_jsonl(
        tmp_path / "corrupted-feature-values.jsonl",
        corrupted_feature_rows,
    )
    label_path = _write_jsonl(tmp_path / "label-values.jsonl", label_rows)
    namespace = tmp_path / "rigor_p05_surrogate_jsonl_hash_mismatch_with_sibling"
    namespace.mkdir()

    with pytest.raises(
        FeatureLockValidationError,
        match="feature value content hash mismatch",
    ):
        run_real_surrogate_calibration(
            study_spec_path=spec_path,
            alpha_data_root=tmp_path / "alpha_data",
            runs_per_config=1,
            base_seed=_base_seed_without_bootstrap_identity(label_rows),
            namespace=namespace,
            report_out=tmp_path / "report.md",
            resolver=_FakeResolver(
                feature_record={
                    healthy_feature_version_id: _FeatureRecord(
                        feature_version_id=healthy_feature_version_id,
                        materialization_output_path=healthy_feature_path.as_posix(),
                        value_content_hash=compute_value_content_hash(
                            healthy_feature_rows
                        ),
                        feature_spec=_FeatureSpec(feature_id="fixture_close_delta"),
                    ),
                    corrupted_feature_version_id: _FeatureRecord(
                        feature_version_id=corrupted_feature_version_id,
                        materialization_output_path=corrupted_feature_path.as_posix(),
                        value_content_hash=compute_value_content_hash(
                            healthy_feature_rows
                        ),
                        feature_spec=_FeatureSpec(
                            feature_id="fixture_hash_corrupted_null_signal"
                        ),
                    ),
                },
                label_record=_LabelRecord(
                    label_version_id=label_version_id,
                    materialization_output_path=label_path.as_posix(),
                    value_content_hash=compute_value_content_hash(label_rows),
                ),
            ),
        )


def test_real_surrogate_calibration_includes_partial_null_factor(
    tmp_path: Path,
) -> None:
    feature_version_id = "fver_" + "1" * 64
    label_version_id = "lver_" + "2" * 64
    spec_path = _study_spec_file(
        tmp_path,
        feature_version_id=feature_version_id,
        label_version_id=label_version_id,
    )
    numeric_feature_rows, label_rows = _value_rows(
        feature_version_id=feature_version_id,
        label_version_id=label_version_id,
    )
    partial_null_indexes = {0, 1, 3}
    partial_null_feature_rows = [
        {**row, "value": None} if index in partial_null_indexes else row
        for index, row in enumerate(numeric_feature_rows)
    ]
    feature_path = _write_jsonl(
        tmp_path / "partial-null-feature-values.jsonl",
        partial_null_feature_rows,
    )
    label_path = _write_jsonl(tmp_path / "label-values.jsonl", label_rows)
    namespace = tmp_path / "rigor_p05_surrogate_partial_null_inclusion"
    namespace.mkdir()
    report_path = tmp_path / "report.md"

    result = run_real_surrogate_calibration(
        study_spec_path=spec_path,
        alpha_data_root=tmp_path / "alpha_data",
        runs_per_config=1,
        base_seed=_base_seed_without_bootstrap_identity(label_rows),
        namespace=namespace,
        report_out=report_path,
        resolver=_FakeResolver(
            feature_record=_FeatureRecord(
                feature_version_id=feature_version_id,
                materialization_output_path=feature_path.as_posix(),
                value_content_hash=compute_value_content_hash(partial_null_feature_rows),
            ),
            label_record=_LabelRecord(
                label_version_id=label_version_id,
                materialization_output_path=label_path.as_posix(),
                value_content_hash=compute_value_content_hash(label_rows),
            ),
        ),
    )

    assert result["accepted"] is True
    assert result["surrogate_study_spec_count"] == 1
    assert result["run_count"] == 2
    assert result["excluded_factor_count"] == 0
    assert result["excluded_factors"] == []
    staged_factor_paths = tuple(
        (namespace / "real_surrogate_inputs" / result["study_spec_id"]).glob(
            "**/factor-values.jsonl"
        )
    )
    assert len(staged_factor_paths) == 1
    staged_rows = _read_jsonl(staged_factor_paths[0])
    assert sum(row["value"] is None for row in staged_rows) == 3
    assert sum(row["normalized_value"] is not None for row in staged_rows) == 3
    rendered = report_path.read_text(encoding="utf-8")
    assert "Excluded all-null/constant factor partitions: 0" in rendered
    assert "## excluded_factors\n\n- None." in rendered


def test_aligned_factor_value_series_drops_unpaired_rows() -> None:
    """The aligned IC series keeps only non-null factor/label pairs."""

    factor_rows = [
        {
            "factor_id": "f",
            "factor_version": "fv",
            "data_version": "dv",
            "instrument_id": "SYNTH",
            "event_ts": f"2026-01-02T14:3{index}:00Z",
            "session_id": "SYNTH:2026-01-02:surrogate",
            "value": float(index),
            "normalized_value": float(index),
        }
        for index in range(4)
    ]
    label_rows = [
        {
            "label_id": "forward_return_5m",
            "data_version": "dv",
            "instrument_id": "SYNTH",
            "event_ts": f"2026-01-02T14:3{index}:00Z",
            "horizon": 300,
            # only rows 1 and 2 have a numeric label
            "value": None if index in (0, 3) else 0.01 * index,
            "path_metadata": {
                "session_id": "SYNTH:2026-01-02:surrogate",
                "label_version": "lv",
            },
        }
        for index in range(4)
    ]
    series = _aligned_factor_value_series(factor_rows, label_rows, horizon_seconds=300)
    assert series == [1.0, 2.0]
    # mismatched horizon yields no aligned pairs
    assert _aligned_factor_value_series(factor_rows, label_rows, horizon_seconds=60) == []


def test_factor_series_is_zero_variance_distinguishes_constant_from_varying() -> None:
    assert _factor_series_is_zero_variance([]) is True
    assert _factor_series_is_zero_variance([0.0]) is True
    assert _factor_series_is_zero_variance([0.0, 0.0, 0.0]) is True
    assert _factor_series_is_zero_variance([0.0, 1.0]) is False
    assert _factor_series_is_zero_variance([1.5, 1.5, 1.5, 2.0]) is False


def test_staged_constant_factor_check_is_factor_only_safety_invariant(
    tmp_path: Path,
) -> None:
    """A varying factor against a CONSTANT label is NOT a constant-factor case."""

    feature_version_id = "fver_" + "1" * 64
    label_version_id = "lver_" + "2" * 64
    numeric_feature_rows, _ = _value_rows(
        feature_version_id=feature_version_id,
        label_version_id=label_version_id,
    )
    _, base_label_rows = _value_rows(
        feature_version_id=feature_version_id,
        label_version_id=label_version_id,
    )
    constant_label_rows = [{**row, "value": 0.25} for row in base_label_rows]
    factor_path = _write_jsonl(
        tmp_path / "factor-values.jsonl",
        _staged_factor_rows(numeric_feature_rows),
    )
    labels_path = _write_jsonl(
        tmp_path / "labels.jsonl",
        _converted_label_rows(constant_label_rows),
    )
    # FACTOR varies even though the LABEL is constant -> must NOT be excluded.
    assert (
        _staged_sub_config_is_constant_factor(
            factor_path,
            labels_path,
            horizon_seconds=300,
        )
        is False
    )
    # A genuinely constant factor against the same labels IS excluded.
    constant_factor_path = _write_jsonl(
        tmp_path / "constant-factor-values.jsonl",
        _staged_factor_rows(
            _constant_feature_rows(
                feature_version_id=feature_version_id,
                label_version_id=label_version_id,
            )
        ),
    )
    assert (
        _staged_sub_config_is_constant_factor(
            constant_factor_path,
            labels_path,
            horizon_seconds=300,
        )
        is True
    )


def test_real_surrogate_calibration_records_constant_factor_exclusion(
    tmp_path: Path,
) -> None:
    constant_feature_version_id = "fver_" + "3" * 64
    numeric_feature_version_id = "fver_" + "1" * 64
    label_version_id = "lver_" + "2" * 64
    spec_path = _study_spec_file(
        tmp_path,
        feature_version_id=numeric_feature_version_id,
        label_version_id=label_version_id,
        feature_locks=(
            _feature_lock(
                feature_id="fixture_constant_flag",
                feature_family="fixture_signal_family",
                feature_version_id=constant_feature_version_id,
            ),
            _feature_lock(
                feature_id="fixture_close_delta",
                feature_family="fixture_signal_family",
                feature_version_id=numeric_feature_version_id,
            ),
        ),
    )
    numeric_feature_rows, label_rows = _value_rows(
        feature_version_id=numeric_feature_version_id,
        label_version_id=label_version_id,
    )
    constant_feature_rows = _constant_feature_rows(
        feature_version_id=constant_feature_version_id,
        label_version_id=label_version_id,
    )
    feature_rows = constant_feature_rows + numeric_feature_rows
    feature_hash = compute_value_content_hash(feature_rows)
    label_hash = compute_value_content_hash(label_rows)
    feature_path = _write_jsonl(tmp_path / "feature-values.jsonl", feature_rows)
    label_path = _write_jsonl(tmp_path / "label-values.jsonl", label_rows)
    resolver = _FakeResolver(
        feature_record={
            constant_feature_version_id: _FeatureRecord(
                feature_version_id=constant_feature_version_id,
                materialization_output_path=feature_path.as_posix(),
                value_content_hash=feature_hash,
                feature_spec=_FeatureSpec(feature_id="fixture_constant_flag"),
            ),
            numeric_feature_version_id: _FeatureRecord(
                feature_version_id=numeric_feature_version_id,
                materialization_output_path=feature_path.as_posix(),
                value_content_hash=feature_hash,
                feature_spec=_FeatureSpec(feature_id="fixture_close_delta"),
            ),
        },
        label_record=_LabelRecord(
            label_version_id=label_version_id,
            materialization_output_path=label_path.as_posix(),
            value_content_hash=label_hash,
        ),
    )
    namespace = tmp_path / "rigor_p05_surrogate_constant_exclusion"
    namespace.mkdir()
    report_path = tmp_path / "report.md"

    result = run_real_surrogate_calibration(
        study_spec_path=spec_path,
        alpha_data_root=tmp_path / "alpha_data",
        runs_per_config=1,
        base_seed=_base_seed_without_bootstrap_identity(label_rows),
        namespace=namespace,
        report_out=report_path,
        resolver=resolver,
    )

    assert result["accepted"] is True
    assert result["declared_factor_count"] == 2
    # only the numeric sub-config is staged/scored
    assert result["surrogate_study_spec_count"] == 1
    assert result["run_count"] == 2
    assert result["error_count"] == 0
    assert result["excluded_factor_count"] == 1
    assert result["excluded_factors"] == [
        {
            "factor_id": "fixture_constant_flag",
            "feature_version_id": constant_feature_version_id,
            "reason": "constant_factor_zero_variance",
            "partition": "SYNTH_2026_full_year",
            "total_rows": len(constant_feature_rows),
            "null_rows": 0,
            "numeric_rows": len(constant_feature_rows),
        }
    ]
    rendered = report_path.read_text(encoding="utf-8")
    assert "## excluded_factors" in rendered
    assert "`fixture_constant_flag`" in rendered
    assert "`constant_factor_zero_variance`" in rendered
    assert "Excluded all-null/constant factor partitions: 1" in rendered
    # the constant sub-config's staged jsonl is removed; only the numeric one stays
    staged_factor_paths = tuple(
        (namespace / "real_surrogate_inputs" / result["study_spec_id"]).glob(
            "**/factor-values.jsonl"
        )
    )
    assert len(staged_factor_paths) == 1
    assert {
        row["factor_id"] for row in _read_jsonl(staged_factor_paths[0])
    } == {"fixture_close_delta"}


def test_real_surrogate_calibration_keeps_two_distinct_value_factor(
    tmp_path: Path,
) -> None:
    """A factor with two distinct aligned values stays staged and scored."""

    feature_version_id = "fver_" + "1" * 64
    label_version_id = "lver_" + "2" * 64
    spec_path = _study_spec_file(
        tmp_path,
        feature_version_id=feature_version_id,
        label_version_id=label_version_id,
    )
    _, label_rows = _value_rows(
        feature_version_id=feature_version_id,
        label_version_id=label_version_id,
    )
    two_distinct_rows = _two_distinct_feature_rows(
        feature_version_id=feature_version_id,
        label_version_id=label_version_id,
    )
    feature_path = _write_jsonl(tmp_path / "feature-values.jsonl", two_distinct_rows)
    label_path = _write_jsonl(tmp_path / "label-values.jsonl", label_rows)
    namespace = tmp_path / "rigor_p05_surrogate_two_distinct"
    namespace.mkdir()

    result = run_real_surrogate_calibration(
        study_spec_path=spec_path,
        alpha_data_root=tmp_path / "alpha_data",
        runs_per_config=1,
        base_seed=_base_seed_without_bootstrap_identity(label_rows),
        namespace=namespace,
        report_out=tmp_path / "report.md",
        resolver=_FakeResolver(
            feature_record=_FeatureRecord(
                feature_version_id=feature_version_id,
                materialization_output_path=feature_path.as_posix(),
                value_content_hash=compute_value_content_hash(two_distinct_rows),
            ),
            label_record=_LabelRecord(
                label_version_id=label_version_id,
                materialization_output_path=label_path.as_posix(),
                value_content_hash=compute_value_content_hash(label_rows),
            ),
        ),
    )

    # A two-distinct-value factor is NOT a constant exclusion: it is staged and
    # scored (zero errors). The pass/block verdict on tiny synthetic data is not
    # the contract under test here.
    assert result["surrogate_study_spec_count"] == 1
    assert result["excluded_factor_count"] == 0
    assert result["error_count"] == 0
    assert result["run_count"] == 2
    staged_factor_paths = tuple(
        (namespace / "real_surrogate_inputs" / result["study_spec_id"]).glob(
            "**/factor-values.jsonl"
        )
    )
    assert len(staged_factor_paths) == 1


def test_real_surrogate_calibration_excludes_aligned_constant_factor(
    tmp_path: Path,
) -> None:
    """A factor that is constant only after the non-null label join is excluded."""

    aligned_feature_version_id = "fver_" + "3" * 64
    numeric_feature_version_id = "fver_" + "1" * 64
    label_version_id = "lver_" + "2" * 64
    spec_path = _study_spec_file(
        tmp_path,
        feature_version_id=numeric_feature_version_id,
        label_version_id=label_version_id,
        feature_locks=(
            _feature_lock(
                feature_id="fixture_aligned_constant_flag",
                feature_family="fixture_signal_family",
                feature_version_id=aligned_feature_version_id,
            ),
            _feature_lock(
                feature_id="fixture_close_delta",
                feature_family="fixture_signal_family",
                feature_version_id=numeric_feature_version_id,
            ),
        ),
    )
    aligned_feature_rows, aligned_label_rows = _aligned_constant_feature_rows(
        feature_version_id=aligned_feature_version_id,
        label_version_id=label_version_id,
    )
    numeric_feature_rows, _ = _value_rows(
        feature_version_id=numeric_feature_version_id,
        label_version_id=label_version_id,
    )
    feature_rows = aligned_feature_rows + numeric_feature_rows
    feature_hash = compute_value_content_hash(feature_rows)
    label_hash = compute_value_content_hash(aligned_label_rows)
    feature_path = _write_jsonl(tmp_path / "feature-values.jsonl", feature_rows)
    label_path = _write_jsonl(tmp_path / "label-values.jsonl", aligned_label_rows)
    resolver = _FakeResolver(
        feature_record={
            aligned_feature_version_id: _FeatureRecord(
                feature_version_id=aligned_feature_version_id,
                materialization_output_path=feature_path.as_posix(),
                value_content_hash=feature_hash,
                feature_spec=_FeatureSpec(feature_id="fixture_aligned_constant_flag"),
            ),
            numeric_feature_version_id: _FeatureRecord(
                feature_version_id=numeric_feature_version_id,
                materialization_output_path=feature_path.as_posix(),
                value_content_hash=feature_hash,
                feature_spec=_FeatureSpec(feature_id="fixture_close_delta"),
            ),
        },
        label_record=_LabelRecord(
            label_version_id=label_version_id,
            materialization_output_path=label_path.as_posix(),
            value_content_hash=label_hash,
        ),
    )
    namespace = tmp_path / "rigor_p05_surrogate_aligned_constant"
    namespace.mkdir()

    # raw factor has two distinct values, so the all-null path does not fire.
    assert len({row["value"] for row in aligned_feature_rows}) == 2

    result = run_real_surrogate_calibration(
        study_spec_path=spec_path,
        alpha_data_root=tmp_path / "alpha_data",
        runs_per_config=1,
        base_seed=_base_seed_without_bootstrap_identity(aligned_label_rows),
        namespace=namespace,
        report_out=tmp_path / "report.md",
        resolver=resolver,
    )

    assert result["accepted"] is True
    assert result["error_count"] == 0
    assert result["excluded_factor_count"] == 1
    assert result["excluded_factors"][0]["factor_id"] == "fixture_aligned_constant_flag"
    assert (
        result["excluded_factors"][0]["reason"] == "constant_factor_zero_variance"
    )
    # the aligned-constant factor has two raw numeric values, so numeric_rows>1
    assert result["excluded_factors"][0]["numeric_rows"] == len(aligned_feature_rows)


def test_real_surrogate_calibration_constant_label_stays_error_not_excluded(
    tmp_path: Path,
) -> None:
    """Non-finite IC from a constant LABEL must stay an error, never excluded."""

    feature_version_id = "fver_" + "1" * 64
    label_version_id = "lver_" + "2" * 64
    spec_path = _study_spec_file(
        tmp_path,
        feature_version_id=feature_version_id,
        label_version_id=label_version_id,
    )
    numeric_feature_rows, label_rows = _value_rows(
        feature_version_id=feature_version_id,
        label_version_id=label_version_id,
    )
    constant_label_rows = [{**row, "value": 0.25} for row in label_rows]
    feature_path = _write_jsonl(tmp_path / "feature-values.jsonl", numeric_feature_rows)
    label_path = _write_jsonl(tmp_path / "label-values.jsonl", constant_label_rows)
    namespace = tmp_path / "rigor_p05_surrogate_constant_label"
    namespace.mkdir()

    result = run_real_surrogate_calibration(
        study_spec_path=spec_path,
        alpha_data_root=tmp_path / "alpha_data",
        runs_per_config=1,
        base_seed=_base_seed_without_bootstrap_identity(constant_label_rows),
        namespace=namespace,
        report_out=tmp_path / "report.md",
        resolver=_FakeResolver(
            feature_record=_FeatureRecord(
                feature_version_id=feature_version_id,
                materialization_output_path=feature_path.as_posix(),
                value_content_hash=compute_value_content_hash(numeric_feature_rows),
            ),
            label_record=_LabelRecord(
                label_version_id=label_version_id,
                materialization_output_path=label_path.as_posix(),
                value_content_hash=compute_value_content_hash(constant_label_rows),
            ),
        ),
    )

    # The factor varies -> it is staged (not excluded); the constant label makes
    # the IC non-finite -> the run is an ERROR and calibration is blocked.
    assert result["excluded_factor_count"] == 0
    assert result["error_count"] >= 1
    assert result["accepted"] is False
    assert result["threshold_verdict"] == CALIBRATION_BLOCKED


def test_real_surrogate_rescore_reclassifies_constant_preserving_seed_numbering(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Rescore drops a constant sub-config's seeds while higher specs keep theirs.

    Emulates a pre-fix run: the staging-time constant check is disabled so the
    constant sub-config (lower spec_index) DOES receive a spec_index and seed
    dirs, exactly like the live bbo namespace. The fix-era rescore must then
    reclassify only that sub-config error->excluded while the higher-spec_index
    numeric sub-config still resolves its original seed dirs.
    """

    import tools.discovery_rigor_floor.run_real_surrogate_calibration as tool

    constant_feature_version_id = "fver_" + "3" * 64
    numeric_feature_version_id = "fver_" + "1" * 64
    label_version_id = "lver_" + "2" * 64
    # constant sub-config sorts BEFORE the numeric one in staging order, so the
    # numeric sub-config sits at a higher spec_index and its seed dir must still
    # resolve after the constant sub-config's seeds are reclassified.
    spec_path = _study_spec_file(
        tmp_path,
        feature_version_id=numeric_feature_version_id,
        label_version_id=label_version_id,
        feature_locks=(
            _feature_lock(
                feature_id="aaa_constant_flag",
                feature_family="fixture_signal_family",
                feature_version_id=constant_feature_version_id,
            ),
            _feature_lock(
                feature_id="zzz_close_delta",
                feature_family="fixture_signal_family",
                feature_version_id=numeric_feature_version_id,
            ),
        ),
    )
    numeric_feature_rows, label_rows = _value_rows(
        feature_version_id=numeric_feature_version_id,
        label_version_id=label_version_id,
    )
    constant_feature_rows = _constant_feature_rows(
        feature_version_id=constant_feature_version_id,
        label_version_id=label_version_id,
    )
    feature_rows = constant_feature_rows + numeric_feature_rows
    feature_hash = compute_value_content_hash(feature_rows)
    label_hash = compute_value_content_hash(label_rows)
    feature_path = _write_jsonl(tmp_path / "feature-values.jsonl", feature_rows)
    label_path = _write_jsonl(tmp_path / "label-values.jsonl", label_rows)

    resolver = _FakeResolver(
        feature_record={
            constant_feature_version_id: _FeatureRecord(
                feature_version_id=constant_feature_version_id,
                materialization_output_path=feature_path.as_posix(),
                value_content_hash=feature_hash,
                feature_spec=_FeatureSpec(feature_id="aaa_constant_flag"),
            ),
            numeric_feature_version_id: _FeatureRecord(
                feature_version_id=numeric_feature_version_id,
                materialization_output_path=feature_path.as_posix(),
                value_content_hash=feature_hash,
                feature_spec=_FeatureSpec(feature_id="zzz_close_delta"),
            ),
        },
        label_record=_LabelRecord(
            label_version_id=label_version_id,
            materialization_output_path=label_path.as_posix(),
            value_content_hash=label_hash,
        ),
    )

    namespace = tmp_path / "rigor_p05_surrogate_rescore_constant"
    namespace.mkdir()
    base_seed = _base_seed_without_bootstrap_identity(label_rows)

    # Stage like the pre-fix code: constant sub-config is NOT excluded, so both
    # sub-configs receive spec_index slots (0 = constant, 1 = numeric) and seeds.
    monkeypatch.setattr(tool, "_staged_sub_config_is_constant_factor", lambda *a, **k: False)
    legacy = run_real_surrogate_calibration(
        study_spec_path=spec_path,
        alpha_data_root=tmp_path / "alpha_data",
        runs_per_config=1,
        base_seed=base_seed,
        namespace=namespace,
        report_out=tmp_path / "legacy.md",
        resolver=resolver,
    )
    # Pre-fix: the constant sub-config produced a DetectionStatisticError seed.
    assert legacy["surrogate_study_spec_count"] == 2
    assert legacy["excluded_factor_count"] == 0
    assert legacy["error_count"] >= 1
    assert legacy["threshold_verdict"] == CALIBRATION_BLOCKED
    # capture the numeric sub-config's (spec_index 1) seed dir to prove it is
    # preserved (not renumbered) by the rescore.
    seed_block_size = 2  # surrogate_spec_count(2) * runs_per_config(1)
    numeric_seed_dirs = [
        namespace / f"seed_{base_seed + config_index * seed_block_size + 1}"
        for config_index in range(2)
    ]
    for seed_dir in numeric_seed_dirs:
        assert (seed_dir / "study_outputs" / "diagnostic_summary.json").is_file()

    # Fix-era rescore reclassifies the constant sub-config and keeps the numeric.
    monkeypatch.undo()
    rescored = run_real_surrogate_calibration(
        study_spec_path=spec_path,
        alpha_data_root=tmp_path / "alpha_data",
        runs_per_config=1,
        base_seed=base_seed,
        namespace=namespace,
        report_out=tmp_path / "rescored.md",
        rescore_existing=True,
    )

    # The constant sub-config (spec_index 0) is reclassified to a recorded
    # exclusion; the numeric sub-config (spec_index 1) keeps its seed dir and is
    # rescored cleanly -> zero errors, accepted.
    assert rescored["excluded_factor_count"] == 1
    assert rescored["excluded_factors"][0]["factor_id"] == "aaa_constant_flag"
    assert (
        rescored["excluded_factors"][0]["reason"] == "constant_factor_zero_variance"
    )
    assert rescored["error_count"] == 0
    assert rescored["accepted"] is True
    assert rescored["statistic_pass_count"] == 0
    # exactly the numeric sub-config's seeds were rescored (2 perturbations x 1).
    assert rescored["run_count"] == 2
    # the numeric sub-config's original seed dirs are the ones that were read.
    for seed_dir in numeric_seed_dirs:
        assert (seed_dir / "study_outputs" / "diagnostic_summary.json").is_file()


def test_real_surrogate_calibration_refuses_value_hash_mismatch(
    tmp_path: Path,
) -> None:
    pytest.importorskip("polars")
    feature_version_id = "fver_" + "1" * 64
    label_version_id = "lver_" + "2" * 64
    spec_path = _study_spec_file(
        tmp_path,
        feature_version_id=feature_version_id,
        label_version_id=label_version_id,
    )
    feature_rows, label_rows = _value_rows(
        feature_version_id=feature_version_id,
        label_version_id=label_version_id,
    )
    feature_hash = compute_value_content_hash(feature_rows)
    label_hash = compute_value_content_hash(label_rows)
    feature_parquet = tmp_path / "feature-values.parquet"
    label_parquet = tmp_path / "label-values.parquet"
    write_parquet_values(
        feature_rows,
        feature_parquet,
        plan_dict={"kind": "feature"},
        content_hash=feature_hash,
        schema_version="test",
        value_count=len(feature_rows),
    )
    write_parquet_values(
        label_rows,
        label_parquet,
        plan_dict={"kind": "label"},
        content_hash=label_hash,
        schema_version="test",
        value_count=len(label_rows),
    )
    resolver = _FakeResolver(
        feature_record=_FeatureRecord(
            feature_version_id=feature_version_id,
            materialization_output_path=(tmp_path / "feature.jsonl").as_posix(),
            value_store_format="parquet",
            parquet_path=feature_parquet.as_posix(),
            value_content_hash="sha256:" + "0" * 64,
        ),
        label_record=_LabelRecord(
            label_version_id=label_version_id,
            materialization_output_path=(tmp_path / "label.jsonl").as_posix(),
            value_store_format="parquet",
            parquet_path=label_parquet.as_posix(),
            value_content_hash=label_hash,
        ),
    )
    namespace = tmp_path / "rigor_p05_surrogate_hash_mismatch"
    namespace.mkdir()

    with pytest.raises(ValueError, match="feature value content hash mismatch"):
        run_real_surrogate_calibration(
            study_spec_path=spec_path,
            alpha_data_root=tmp_path / "alpha_data",
            runs_per_config=1,
            base_seed=_base_seed_without_bootstrap_identity(label_rows),
            namespace=namespace,
            report_out=tmp_path / "report.md",
            resolver=resolver,
        )


def test_real_surrogate_calibration_refuses_ambiguous_declared_factor_family(
    tmp_path: Path,
) -> None:
    feature_version_id = "fver_" + "1" * 64
    second_feature_version_id = "fver_" + "3" * 64
    label_version_id = "lver_" + "2" * 64
    spec_path = _study_spec_file(
        tmp_path,
        feature_version_id=feature_version_id,
        label_version_id=label_version_id,
        feature_locks=(
            _feature_lock(
                feature_id="fixture_close_delta",
                feature_family="fixture_signal_family",
                feature_version_id=feature_version_id,
            ),
            _feature_lock(
                feature_id="fixture_second_signal",
                feature_family="fixture_second_family",
                feature_version_id=second_feature_version_id,
            ),
        ),
    )
    namespace = tmp_path / "rigor_p05_surrogate_ambiguous"
    namespace.mkdir()

    with pytest.raises(GovernanceValidationError) as exc_info:
        run_real_surrogate_calibration(
            study_spec_path=spec_path,
            alpha_data_root=tmp_path / "alpha_data",
            runs_per_config=1,
            base_seed=1,
            namespace=namespace,
            report_out=tmp_path / "report.md",
            resolver=_FakeResolver(
                feature_record=_FeatureRecord(
                    feature_version_id=feature_version_id,
                    materialization_output_path=(tmp_path / "feature.jsonl").as_posix(),
                    value_content_hash="sha256:" + "1" * 64,
                ),
                label_record=_LabelRecord(
                    label_version_id=label_version_id,
                    materialization_output_path=(tmp_path / "label.jsonl").as_posix(),
                    value_content_hash="sha256:" + "2" * 64,
                ),
            ),
        )

    assert exc_info.value.issues[0].code == "declared_factor_family_ambiguous"


def test_real_surrogate_declared_factor_resolution_for_six_rerun_specs() -> None:
    data_root = Path(os.environ.get("ALPHA_DATA_ROOT", "~/alpha_data/alpha_system")).expanduser()
    skip_unless_local_registry(
        lambda: data_root / "registry/features.sqlite",
        reason=(
            "real local feature registry absent; committed rerun sspec resolution "
            "is exercised when private local registry state is present"
        ),
    )
    spec_root = REPO_ROOT / "research/futures_substrate_scaleout_v1/rerun/study_specs"
    for study_spec_id, expected_factor_ids in KILL_SHOT_RERUN_SPECS.items():
        study_spec = _load_study_spec(spec_root / f"{study_spec_id}.json")
        horizon_text, _, _ = (
            "5m",
            300,
            "forward_return_5m",
        )
        label_locks = _select_label_locks(study_spec.dataset_scope, horizon_text)
        declared_feature_family = _declared_feature_family(study_spec.dataset_scope)

        assert (
            _declared_factor_ids(
                study_spec.dataset_scope,
                declared_feature_family=declared_feature_family,
            )
            == expected_factor_ids
        )
        assert _expected_sub_config_count(
            study_spec.dataset_scope,
            label_locks=label_locks,
            declared_feature_family=declared_feature_family,
        ) == len(label_locks) * len(expected_factor_ids)


def test_real_local_label_registry_absence_is_loud_skip() -> None:
    data_root = Path(os.environ.get("ALPHA_DATA_ROOT", "~/alpha_data/alpha_system")).expanduser()
    skip_unless_local_registry(
        lambda: data_root / "registry/labels.sqlite",
        reason=(
            "real local label registry absent; synthetic resolver path covers CI "
            "and coordinator runs this against private local data"
        ),
    )


def _study_spec_file(
    tmp_path: Path,
    *,
    feature_version_id: str,
    label_version_id: str,
    feature_locks: tuple[dict[str, Any], ...] | None = None,
    label_locks: tuple[dict[str, Any], ...] | None = None,
) -> Path:
    payload = json.loads(COMMITTED_STUDY_SPEC.read_text(encoding="utf-8"))
    payload["dataset_scope"] = {
        "declared_primary_horizon": "5m",
        "family": "fixture_family",
        "feature_pack_locks": list(
            feature_locks
            or (
                _feature_lock(
                    feature_id="fixture_close_delta",
                    feature_family="fixture_signal_family",
                    feature_version_id=feature_version_id,
                ),
            )
        ),
        "label_pack_locks": list(
            label_locks
            or (
                _label_lock(label_version_id=label_version_id),
            )
        ),
    }
    payload["study_spec_id"] = generate_study_spec_id(payload)
    validate_study_spec(payload)
    path = tmp_path / "study_spec.json"
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return path


def _feature_lock(
    *,
    feature_id: str,
    feature_family: str,
    feature_version_id: str,
    partition: str = "SYNTH_2026_full_year",
) -> dict[str, Any]:
    return {
        "feature_id": feature_id,
        "feature_family": feature_family,
        "feature_version_id": feature_version_id,
        "feature_request_id": "freq_" + "5" * 64,
        "dataset_version_id": "dsv_fixture_2026",
        "partition": partition,
    }


def _label_lock(
    *,
    label_version_id: str,
    partition: str = "SYNTH_2026_fwd_ret_5m",
) -> dict[str, Any]:
    return {
        "label_id": "forward_return_5m",
        "label_spec_id": "lspec_" + "6" * 24,
        "label_version_id": label_version_id,
        "dataset_version_id": "dsv_fixture_2026",
        "partition": partition,
    }


@dataclass(frozen=True, slots=True)
class _FeatureSpec:
    feature_id: str = "fixture_close_delta"


@dataclass(frozen=True, slots=True)
class _FeatureRecord:
    feature_version_id: str
    materialization_output_path: str
    value_content_hash: str
    dataset_version_id: str = "dsv_fixture_2026"
    partition_id: str = "SYNTH_2026_full_year"
    value_store_format: str = "jsonl"
    parquet_path: str | None = None
    feature_spec: _FeatureSpec = _FeatureSpec()


@dataclass(frozen=True, slots=True)
class _LabelRecord:
    label_version_id: str
    materialization_output_path: str
    value_content_hash: str
    dataset_version_id: str = "dsv_fixture_2026"
    partition_id: str = "SYNTH_2026_fwd_ret_5m"
    value_store_format: str = "jsonl"
    parquet_path: str | None = None


class _FakeFeatureStore:
    def __init__(self, record: _FeatureRecord | Mapping[str, _FeatureRecord]) -> None:
        if isinstance(record, Mapping):
            self.records = dict(record)
        else:
            self.records = {record.feature_version_id: record}

    def resolve_registered_feature(self, feature_version_id: str) -> _FeatureRecord | None:
        if feature_version_id in self.records:
            record = self.records[feature_version_id]
            active_feature_version_id = record.feature_version_id
        elif len(self.records) == 1:
            record = next(iter(self.records.values()))
            active_feature_version_id = feature_version_id
        else:
            return None
        return _FeatureRecord(
            feature_version_id=active_feature_version_id,
            materialization_output_path=record.materialization_output_path,
            value_content_hash=record.value_content_hash,
            dataset_version_id=record.dataset_version_id,
            partition_id=record.partition_id,
            value_store_format=record.value_store_format,
            parquet_path=record.parquet_path,
            feature_spec=record.feature_spec,
        )


class _FakeLabelRegistry:
    def __init__(self, record: _LabelRecord) -> None:
        self.record = record

    def resolve_registered_label(self, label_version_id: str) -> _LabelRecord:
        return _LabelRecord(
            label_version_id=label_version_id,
            materialization_output_path=self.record.materialization_output_path,
            value_content_hash=self.record.value_content_hash,
            dataset_version_id=self.record.dataset_version_id,
            partition_id=self.record.partition_id,
            value_store_format=self.record.value_store_format,
            parquet_path=self.record.parquet_path,
        )


class _FakeResolver:
    def __init__(
        self,
        *,
        feature_record: _FeatureRecord | Mapping[str, _FeatureRecord],
        label_record: _LabelRecord,
    ) -> None:
        self.feature_store = _FakeFeatureStore(feature_record)
        self.label_registry = _FakeLabelRegistry(label_record)
        self.feature_calls: list[dict[str, Any]] = []
        self.label_calls: list[dict[str, Any]] = []

    def resolve_label_packs(
        self,
        label_pack_refs: tuple[str, ...],
        *,
        expected_dataset_version_id: str,
        expected_label_spec_ids: tuple[str, ...],
        partition_id: str,
    ) -> tuple[object, ...]:
        self.label_calls.append(
            {
                "refs": label_pack_refs,
                "dataset_version_id": expected_dataset_version_id,
                "label_spec_ids": expected_label_spec_ids,
                "partition_id": partition_id,
            }
        )
        return ()

    def resolve_feature_packs(
        self,
        feature_pack_refs: tuple[str, ...],
        *,
        expected_dataset_version_id: str,
        expected_feature_request_ids: tuple[str, ...],
        partition_id: str,
    ) -> tuple[object, ...]:
        self.feature_calls.append(
            {
                "refs": feature_pack_refs,
                "dataset_version_id": expected_dataset_version_id,
                "feature_request_ids": expected_feature_request_ids,
                "partition_id": partition_id,
            }
        )
        return ()


def _value_rows(
    *,
    feature_version_id: str,
    label_version_id: str,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    feature_rows: list[dict[str, object]] = []
    label_rows: list[dict[str, object]] = []
    values = [1.0, 2.0, -1.0, -2.0, 1.5, -1.5]
    for index, value in enumerate(values):
        event_ts = datetime(2026, 1, 2 + index // 2, 14, 31 + index % 2, tzinfo=UTC)
        horizon_end_ts = event_ts + timedelta(minutes=5)
        feature_rows.append(
            {
                "feature_version_id": feature_version_id,
                "entity_id": "SYNTH",
                "event_ts": _text(event_ts),
                "available_ts": _text(event_ts + timedelta(seconds=5)),
                "value": value,
                "quality_flags": ["synthetic"],
            }
        )
        label_rows.append(
            {
                "label_version_id": label_version_id,
                "label_spec_id": "lspec_" + "6" * 24,
                "entity_id": "SYNTH",
                "event_ts": _text(event_ts),
                "horizon_end_ts": _text(horizon_end_ts),
                "label_available_ts": _text(horizon_end_ts + timedelta(seconds=5)),
                "value": value / 100.0,
                "quality_flags": ["synthetic"],
            }
        )
    return feature_rows, label_rows


def _all_null_feature_rows(
    *,
    feature_version_id: str,
    label_version_id: str,
) -> list[dict[str, object]]:
    feature_rows, _ = _value_rows(
        feature_version_id=feature_version_id,
        label_version_id=label_version_id,
    )
    return [{**row, "value": None} for row in feature_rows]


def _constant_feature_rows(
    *,
    feature_version_id: str,
    label_version_id: str,
    constant: float = 0.0,
) -> list[dict[str, object]]:
    """Numeric feature rows that all share one value (zero variance everywhere)."""

    feature_rows, _ = _value_rows(
        feature_version_id=feature_version_id,
        label_version_id=label_version_id,
    )
    return [{**row, "value": constant} for row in feature_rows]


def _two_distinct_feature_rows(
    *,
    feature_version_id: str,
    label_version_id: str,
) -> list[dict[str, object]]:
    """Numeric feature rows with exactly two distinct values (kept in calibration)."""

    feature_rows, _ = _value_rows(
        feature_version_id=feature_version_id,
        label_version_id=label_version_id,
    )
    return [
        {**row, "value": 0.0 if index % 2 == 0 else 1.0}
        for index, row in enumerate(feature_rows)
    ]


def _aligned_constant_feature_rows(
    *,
    feature_version_id: str,
    label_version_id: str,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Feature rows with two raw values that collapse to one after the label join.

    The only row carrying the second value (1.0) is paired with a null label,
    so the non-null IC join drops it and the aligned factor series is constant
    even though the raw factor has two distinct values. Mirrors the two ES_2019
    bbo binary flags that are aligned-constant in the live namespace.
    """

    feature_rows, label_rows = _value_rows(
        feature_version_id=feature_version_id,
        label_version_id=label_version_id,
    )
    distinct_index = 0
    raw_feature_rows = [
        {**row, "value": 1.0 if index == distinct_index else 0.0}
        for index, row in enumerate(feature_rows)
    ]
    aligned_label_rows = [
        {**row, "value": None} if index == distinct_index else row
        for index, row in enumerate(label_rows)
    ]
    return raw_feature_rows, aligned_label_rows


def _staged_factor_rows(
    feature_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Convert resolver-style feature rows into the staged factor-jsonl shape.

    Matches ``_materialize_factor_jsonl`` output (data_version/session_id) so the
    staged constant-factor check joins to ``_converted_label_rows`` correctly.
    """

    staged: list[dict[str, object]] = []
    for row in feature_rows:
        event_ts = str(row["event_ts"])
        value = row.get("value")
        numeric_value = (
            value
            if isinstance(value, (int, float)) and not isinstance(value, bool)
            else None
        )
        staged.append(
            {
                "factor_id": "fixture_close_delta",
                "factor_version": str(row["feature_version_id"]),
                "instrument_id": row["entity_id"],
                "event_ts": event_ts,
                "available_ts": row["available_ts"],
                "session_id": f"{row['entity_id']}:{event_ts[:10]}:surrogate",
                "bar_index": 0,
                "value": value,
                "normalized_value": numeric_value,
                "quality_flags": [],
                "data_version": "data:v1",
                "compute_version": "real_surrogate_calibration_bridge_v1",
            }
        )
    return staged


def _base_seed_without_bootstrap_identity(label_rows: list[dict[str, object]]) -> int:
    from alpha_system.governance.surrogate_run import write_trade_date_block_bootstrap_copy

    tmp = Path(os.environ.get("PYTEST_TMPDIR", "/tmp")) / "surrogate_seed_probe_labels.jsonl"
    out = Path(os.environ.get("PYTEST_TMPDIR", "/tmp")) / "surrogate_seed_probe_out.jsonl"
    _write_jsonl(tmp, _converted_label_rows(label_rows))
    for bootstrap_seed in range(1, 200):
        try:
            write_trade_date_block_bootstrap_copy(tmp, out, seed=bootstrap_seed)
        except Exception:
            continue
        return bootstrap_seed - 1
    raise AssertionError("no non-identity bootstrap seed found")


def _converted_label_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    converted: list[dict[str, object]] = []
    for row in rows:
        converted.append(
            {
                "label_id": "forward_return_5m",
                "instrument_id": row["entity_id"],
                "event_ts": row["event_ts"],
                "horizon": 300,
                "label_type": "forward_return_5m",
                "value": row["value"],
                "path_metadata": {
                    "session_id": f"SYNTH:{str(row['event_ts'])[:10]}:surrogate",
                    "label_version": "labels:v1",
                    "horizon_end_ts": row["horizon_end_ts"],
                    "required_future_bars": 1,
                    "observed_future_bars": 1,
                },
                "data_version": "data:v1",
                "label_available_ts": row["label_available_ts"],
            }
        )
    return converted


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> Path:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    return path


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _text(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")
