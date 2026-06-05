from __future__ import annotations

from pathlib import Path

import pytest

from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.features.contracts import (
    FeatureContractError,
    FeatureFamily,
    FeatureInputSpec,
    FeatureSetSpec,
    FeatureSpec,
    FitPartitionPolicy,
    NormalizationSpec,
    TransformSpec,
    WindowCausality,
    WindowKind,
    WindowSpec,
)
from alpha_system.features.engine import (
    FeatureMaterializationError,
    build_feature_materialization_plan,
)
from alpha_system.features.engine.materialization import FEATURE_MATERIALIZATION_PURPOSE
from alpha_system.features.families.ohlcv import (
    OHLCVFeatureName,
    build_ohlcv_feature_definition,
)
from alpha_system.features.input_views import build_bbo_input_view, build_ohlcv_input_view
from alpha_system.features.request_gate import FeatureRequestGateError
from alpha_system.features.semantics import (
    is_real_trade_bar,
    is_synthetic_no_trade_bar,
    select_missing_or_abnormal_bbo_rows,
    select_real_trade_bars,
    select_valid_bbo_quotes,
)
from alpha_system.governance.feature_request import FeatureRequestApprovalStatus
from alpha_system.labels.engine import (
    LABEL_MATERIALIZATION_PURPOSE,
    LabelMaterializationError,
    build_label_materialization_plan,
)
from alpha_system.labels.families.fixed_horizon import (
    FixedHorizonLabelError,
    FixedHorizonLabelName,
    build_fixed_horizon_label_definition,
)
from alpha_system.labels.leakage_audit import audit_registered_label
from tests.fixtures.feature_label.synthetic import (
    DATASET_ID,
    EmptyRegistryReader,
    accepted_version,
    approved_feature_request,
    bbo_rows,
    canonical_partition_plan,
    clean_live_feature_references,
    dense_grid_rows,
    governed_label_spec,
    label_value_payload,
    locked_partition_governance_metadata,
    ohlcv_rows,
    registered_label_record,
)


def test_missing_or_unapproved_feature_request_blocks_feature_implementation() -> None:
    with pytest.raises(FeatureRequestGateError, match="FeatureRequest is required"):
        build_ohlcv_feature_definition(
            OHLCVFeatureName.RETURNS,
            None,
            EmptyRegistryReader(),
            dataset_version_ids=(DATASET_ID,),
        )

    with pytest.raises(FeatureRequestGateError, match="approval_status must be APPROVED"):
        build_ohlcv_feature_definition(
            OHLCVFeatureName.RETURNS,
            approved_feature_request(
                "pending_synthetic_returns",
                approval_status=FeatureRequestApprovalStatus.PENDING,
            ),
            EmptyRegistryReader(),
            dataset_version_ids=(DATASET_ID,),
        )


def test_missing_validated_feature_spec_or_available_ts_rule_blocks_values(
    tmp_path: Path,
) -> None:
    accepted = accepted_version()
    definition = build_ohlcv_feature_definition(
        OHLCVFeatureName.RETURNS,
        approved_feature_request(),
        EmptyRegistryReader(),
        dataset_version_ids=(DATASET_ID,),
        reset_on_session=False,
    )
    uneligible_spec = _feature_spec(
        feature_id="base_ohlcv_uneligible_returns",
        feature_request_id=definition.spec.feature_request_id,
        implementation_eligible=False,
    )

    with pytest.raises(FeatureMaterializationError, match="not implementation eligible"):
        build_feature_materialization_plan(
            FeatureSetSpec(
                feature_set_id="feature_set_flf_p25_uneligible",
                feature_set_version="v1",
                features=(uneligible_spec,),
            ),
            accepted,
            partition_id="development_partition",
            alpha_data_root=tmp_path,
        )

    bad_available_rule = _feature_spec(
        feature_id="base_ohlcv_ingested_at_returns",
        feature_request_id=definition.spec.feature_request_id,
        implementation_eligible=True,
        request_gate_decision=definition.request_gate_decision,
        available_ts_derivation_rule="feature timestamp = ingested_at",
    )
    with pytest.raises(FeatureMaterializationError, match="available_ts"):
        build_feature_materialization_plan(
            FeatureSetSpec(
                feature_set_id="feature_set_flf_p25_bad_available_rule",
                feature_set_version="v1",
                features=(bad_available_rule,),
            ),
            accepted,
            partition_id="development_partition",
            alpha_data_root=tmp_path,
        )


def test_canonical_feature_inputs_missing_available_ts_fail_before_values() -> None:
    rows = list(ohlcv_rows())
    rows[0] = dict(rows[0])
    rows[0].pop("available_ts")

    with pytest.raises(DataFoundationValidationError, match="available_ts"):
        build_ohlcv_input_view(
            accepted_version(),
            rows,
            partition_id="development_partition",
            purpose="feature_input",
        )


def test_missing_governed_label_spec_blocks_label_values(tmp_path: Path) -> None:
    accepted = accepted_version()

    with pytest.raises(FixedHorizonLabelError, match="lspec_ binding"):
        build_fixed_horizon_label_definition(
            FixedHorizonLabelName.FWD_RET_1M,
            None,
            dataset_version_ids=(DATASET_ID,),
        )

    definition = build_fixed_horizon_label_definition(
        FixedHorizonLabelName.FWD_RET_1M,
        governed_label_spec(),
        dataset_version_ids=(DATASET_ID,),
    )
    plan = build_label_materialization_plan(
        (definition,),
        accepted,
        partition_id="development_partition",
        alpha_data_root=tmp_path,
        dry_run=True,
    )
    assert plan.dry_run is True


def test_label_available_ts_missing_or_too_early_blocks_audit(tmp_path: Path) -> None:
    record = registered_label_record(tmp_path)
    missing_payload = label_value_payload(record)
    missing_payload.pop("label_available_ts")

    missing_report = audit_registered_label(
        record,
        live_feature_references=clean_live_feature_references(),
        label_value_records=(missing_payload,),
    )

    assert missing_report.blocked is True
    assert any(
        finding.check == "label_available_ts_present"
        for finding in missing_report.blocking_findings
    )

    early_payload = label_value_payload(record)
    early_payload["label_available_ts"] = "2024-01-02T14:31:59+00:00"
    early_report = audit_registered_label(
        record,
        live_feature_references=clean_live_feature_references(),
        label_value_records=(early_payload,),
    )

    assert early_report.blocked is True
    assert any(
        finding.check == "label_available_ts_ordering"
        for finding in early_report.blocking_findings
    )


def test_label_as_feature_reference_blocks_label_materialization_plan(
    tmp_path: Path,
) -> None:
    definition = build_fixed_horizon_label_definition(
        FixedHorizonLabelName.FWD_RET_1M,
        governed_label_spec(),
        dataset_version_ids=(DATASET_ID,),
    )

    with pytest.raises(LabelMaterializationError, match="live feature"):
        build_label_materialization_plan(
            (definition,),
            accepted_version(),
            partition_id="development_partition",
            alpha_data_root=tmp_path,
            feature_references=(
                {
                    "feature_id": definition.label_id,
                    "available_at": "2024-01-02T14:32:59+00:00",
                },
            ),
        )


def test_centered_or_future_windows_cannot_enter_live_feature_specs() -> None:
    for kind, causality in (
        (WindowKind.CENTERED, WindowCausality.CENTERED),
        (WindowKind.FUTURE, WindowCausality.FUTURE),
    ):
        with pytest.raises(FeatureContractError, match="live FeatureSpec"):
            _feature_spec(
                feature_id=f"base_ohlcv_{kind.value}_returns",
                feature_request_id=approved_feature_request().feature_request_id,
                implementation_eligible=False,
                window=WindowSpec(
                    kind=kind,
                    length=3,
                    causality=causality,
                    offline_only=True,
                ),
            )


def test_raw_provider_readers_are_not_reachable_from_feature_label_code() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    source_roots = (
        repo_root / "src" / "alpha_system" / "features",
        repo_root / "src" / "alpha_system" / "labels",
    )
    forbidden_tokens = (
        ".dbn",
        ".zst",
        ".feather",
        "read_parquet",
        "pyarrow",
        "databento",
        "ib_insync",
    )
    hits: list[str] = []

    for source_root in source_roots:
        for path in source_root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for token in forbidden_tokens:
                if token in text:
                    hits.append(f"{path.relative_to(repo_root)}:{token}")

    assert hits == []


def test_missing_or_abnormal_bbo_is_flagged_not_forward_filled() -> None:
    rows = bbo_rows()
    bad_missing = dict(rows[0])
    bad_missing["quality_flags"] = []

    with pytest.raises(DataFoundationValidationError, match="missing_bbo"):
        build_bbo_input_view(
            accepted_version(),
            (bad_missing,),
            partition_id="development_partition",
            purpose="feature_input",
        )

    view = build_bbo_input_view(
        accepted_version(),
        rows,
        partition_id="development_partition",
        purpose="feature_input",
    )
    missing_row, valid_row, quarantined_row = view.rows

    assert select_valid_bbo_quotes(view.rows) == (valid_row,)
    assert select_missing_or_abnormal_bbo_rows(view.rows) == (missing_row, quarantined_row)
    assert missing_row.quality_flags == ("missing_bbo",)
    assert quarantined_row.quality_flags == ("bbo_quarantined",)


def test_synthetic_dense_grid_no_trade_rows_are_never_real_trade_bars() -> None:
    rows = dense_grid_rows()
    records = accepted_version().dense_grid_bars_from_mappings(
        rows,
        partition_id="development_partition",
        purpose="feature_input",
    )
    trade_row, no_trade_row = records

    assert is_real_trade_bar(trade_row) is True
    assert is_synthetic_no_trade_bar(no_trade_row) is True
    assert is_real_trade_bar(no_trade_row) is False
    assert select_real_trade_bars(records) == (trade_row,)

    malformed_no_trade = dict(rows[1])
    malformed_no_trade["quality_flags"] = []
    with pytest.raises(DataFoundationValidationError, match="no_trade"):
        accepted_version().dense_grid_bars_from_mappings(
            (malformed_no_trade,),
            partition_id="development_partition",
            purpose="feature_input",
        )


def test_locked_test_partition_requires_governance_contamination_metadata() -> None:
    accepted = accepted_version()
    partition_plan = canonical_partition_plan()

    with pytest.raises(DataFoundationValidationError, match="contamination metadata"):
        accepted.require_partition_access(
            partition_id="locked_test_candidate",
            purpose=FEATURE_MATERIALIZATION_PURPOSE,
            partition_plan=partition_plan,
        )

    assert accepted.require_partition_access(
        partition_id="locked_test_candidate",
        purpose=LABEL_MATERIALIZATION_PURPOSE,
        governance_metadata=locked_partition_governance_metadata(),
        partition_plan=partition_plan,
    )


def test_locked_test_fit_policy_requires_contamination_metadata() -> None:
    with pytest.raises(FeatureContractError, match="contamination metadata"):
        NormalizationSpec(
            normalization_id="identity",
            fit_partition_policy=FitPartitionPolicy.LOCKED_TEST,
        )


def _feature_spec(
    *,
    feature_id: str,
    feature_request_id: str,
    implementation_eligible: bool,
    request_gate_decision: object | None = None,
    available_ts_derivation_rule: str = "feature.available_ts = max(input.available_ts)",
    window: WindowSpec | None = None,
) -> FeatureSpec:
    kwargs = {
        "feature_id": feature_id,
        "family": FeatureFamily.BASE_OHLCV,
        "feature_request_id": feature_request_id,
        "inputs": FeatureInputSpec(
            input_views=("canonical_ohlcv",),
            fields=("close", "available_ts"),
            dataset_version_ids=(DATASET_ID,),
        ),
        "transform": TransformSpec(
            transform_id="pct_change",
            parameters={"operation": "pct_change", "window": 1},
        ),
        "window": window
        or WindowSpec(
            kind=WindowKind.ROLLING,
            length=1,
            causality=WindowCausality.CAUSAL,
            offline_only=False,
        ),
        "normalization": NormalizationSpec(normalization_id="identity"),
        "availability_assumptions": {
            "timing": "synthetic fixture inputs carry explicit available_ts"
        },
        "available_ts_derivation_rule": available_ts_derivation_rule,
        "live": True,
        "implementation_eligible": implementation_eligible,
    }
    if implementation_eligible:
        return FeatureSpec(**kwargs, request_gate_decision=request_gate_decision)
    return FeatureSpec(**kwargs)
