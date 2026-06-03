from __future__ import annotations

from alpha_system.core.enums import FactorInputDomain, FactorStatus
from alpha_system.factors.base import FACTOR_VALUE_SCHEMA_FIELDS
from alpha_system.l2.feature_specs import all_l2_feature_declarations
from alpha_system.l2.feature_validation import validate_l2_feature_declarations
from alpha_system.l2.features import compute_top_of_book_spread
from alpha_system.l2.fixtures import synthetic_l2_snapshot_rows


def test_l2_feature_declarations_are_factor_spec_compatible() -> None:
    declarations = all_l2_feature_declarations()

    validate_l2_feature_declarations(declarations)

    categories = {declaration.category for declaration in declarations}
    assert {
        "spread_from_top_of_book",
        "imbalance_by_level",
        "depth_by_side",
        "order_count_by_level",
        "microprice",
        "quote_update_intensity",
        "liquidity_regime_tags",
        "future_order_flow_placeholder",
    } <= categories

    for declaration in declarations:
        spec = declaration.factor_spec
        assert spec.status is FactorStatus.DRAFT
        assert spec.validation_artifact_path is None
        assert spec.availability_lag.total_seconds() == 0
        assert len(spec.config_hash) == 64
        assert spec.parameters["fixture_only"] is True
        assert spec.parameters["materialize_by_default"] is False
        assert all(field.domain is FactorInputDomain.L2 for field in spec.input_fields)


def test_l2_feature_values_use_factor_value_schema_order() -> None:
    value = compute_top_of_book_spread(synthetic_l2_snapshot_rows())

    assert tuple(value.to_dict()) == FACTOR_VALUE_SCHEMA_FIELDS
    assert value.factor_id == "l2_top_of_book_spread"
    assert value.factor_version == "v0.design-fixture"
    assert value.compute_version == "l2_feature_fixture_skeleton_v1"
