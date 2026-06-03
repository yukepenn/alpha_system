"""Declarative fixture-only L2-derived feature specs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from alpha_system.factors.spec import FactorSpec, compute_factor_config_hash
from alpha_system.l2.feature_validation import L2_FEATURE_DESIGN_SCOPE


L2_FEATURE_SPEC_VERSION = "l2_feature_skeleton_v1"
L2_FEATURE_CREATED_AT = "2026-06-03T00:00:00Z"
L2_FEATURE_OWNER = "research_governance"
L2_FEATURE_CODE_HASH = "26" * 32


@dataclass(frozen=True, slots=True)
class L2FeatureDeclaration:
    """One design-scope L2 feature declaration compatible with FactorSpec."""

    feature_id: str
    category: str
    factor_spec: FactorSpec
    design_scope: str = L2_FEATURE_DESIGN_SCOPE
    fixture_only: bool = True
    materialize_by_default: bool = False
    produces_factor_value_schema: bool = True
    implemented_for_fixture: bool = True
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize declaration metadata without registering the factor."""
        return {
            "feature_id": self.feature_id,
            "category": self.category,
            "design_scope": self.design_scope,
            "fixture_only": self.fixture_only,
            "materialize_by_default": self.materialize_by_default,
            "produces_factor_value_schema": self.produces_factor_value_schema,
            "implemented_for_fixture": self.implemented_for_fixture,
            "factor_spec": self.factor_spec.to_dict(),
            "notes": list(self.notes),
        }


def _input(name: str, source_field: str) -> dict[str, str]:
    return {"name": name, "domain": "l2", "source_field": source_field}


def _factor_payload(
    *,
    factor_id: str,
    name: str,
    description: str,
    input_fields: Sequence[Mapping[str, str]],
    parameters: Mapping[str, Any],
    factor_type: str = "continuous",
    evaluation_type: str = "point_in_time",
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "factor_id": factor_id,
        "name": name,
        "version": "v0.design-fixture",
        "owner": L2_FEATURE_OWNER,
        "description": description,
        "input_fields": [dict(field) for field in input_fields],
        "parameters": dict(parameters),
        "frequency": "1m",
        "warmup_bars": 0,
        "session_reset": True,
        "availability_lag": 0,
        "factor_type": factor_type,
        "evaluation_type": evaluation_type,
        "code_hash": L2_FEATURE_CODE_HASH,
        "config_hash": "0" * 64,
        "status": "draft",
        "created_at": L2_FEATURE_CREATED_AT,
        "validation_artifact_path": None,
    }
    payload["config_hash"] = compute_factor_config_hash(payload)
    return payload


def _declaration(
    *,
    feature_id: str,
    category: str,
    name: str,
    description: str,
    input_fields: Sequence[Mapping[str, str]],
    parameters: Mapping[str, Any],
    factor_type: str = "continuous",
    evaluation_type: str = "point_in_time",
    implemented_for_fixture: bool = True,
    notes: Sequence[str] = (),
) -> L2FeatureDeclaration:
    spec = FactorSpec.from_mapping(
        _factor_payload(
            factor_id=feature_id,
            name=name,
            description=description,
            input_fields=input_fields,
            parameters={
                "l2_feature_spec_version": L2_FEATURE_SPEC_VERSION,
                "design_scope": L2_FEATURE_DESIGN_SCOPE,
                "fixture_only": True,
                "materialize_by_default": False,
                **dict(parameters),
            },
            factor_type=factor_type,
            evaluation_type=evaluation_type,
        )
    )
    return L2FeatureDeclaration(
        feature_id=feature_id,
        category=category,
        factor_spec=spec,
        implemented_for_fixture=implemented_for_fixture,
        notes=tuple(notes),
    )


L2_FEATURE_DECLARATIONS: tuple[L2FeatureDeclaration, ...] = (
    _declaration(
        feature_id="l2_top_of_book_spread",
        category="spread_from_top_of_book",
        name="L2 Top Of Book Spread",
        description=(
            "Fixture-only top-of-book spread skeleton using synthetic L2 rows."
        ),
        input_fields=(
            _input("side", "side"),
            _input("book_level", "book_level"),
            _input("price", "price"),
        ),
        parameters={"book_level": 1, "formula": "ask_price - bid_price"},
    ),
    _declaration(
        feature_id="l2_top1_imbalance",
        category="imbalance_by_level",
        name="L2 Top-1 Size Imbalance",
        description="Fixture-only top-level bid/ask size imbalance skeleton.",
        input_fields=(
            _input("side", "side"),
            _input("book_level", "book_level"),
            _input("size", "size"),
        ),
        parameters={"depth_levels": 1, "formula": "(bid_size - ask_size) / total"},
    ),
    _declaration(
        feature_id="l2_top5_imbalance",
        category="imbalance_by_level",
        name="L2 Top-5 Size Imbalance",
        description="Fixture-only top-five displayed depth imbalance skeleton.",
        input_fields=(
            _input("side", "side"),
            _input("book_level", "book_level"),
            _input("size", "size"),
        ),
        parameters={"depth_levels": 5, "formula": "(bid_size - ask_size) / total"},
    ),
    _declaration(
        feature_id="l2_depth_by_side",
        category="depth_by_side",
        name="L2 Displayed Depth By Side",
        description="Fixture-only displayed depth aggregation by book side.",
        input_fields=(
            _input("side", "side"),
            _input("book_level", "book_level"),
            _input("size", "size"),
        ),
        parameters={"depth_levels": 5, "side_parameter": "bid_or_ask"},
    ),
    _declaration(
        feature_id="l2_order_count_by_level",
        category="order_count_by_level",
        name="L2 Order Count By Level",
        description="Fixture-only displayed order count by side and level.",
        input_fields=(
            _input("side", "side"),
            _input("book_level", "book_level"),
            _input("order_count", "order_count"),
        ),
        parameters={"book_level": 1, "side_parameter": "bid_or_ask"},
    ),
    _declaration(
        feature_id="l2_microprice",
        category="microprice",
        name="L2 Microprice",
        description="Fixture-only top-of-book microprice skeleton.",
        input_fields=(
            _input("side", "side"),
            _input("book_level", "book_level"),
            _input("price", "price"),
            _input("size", "size"),
        ),
        parameters={
            "book_level": 1,
            "formula": "(ask_price * bid_size + bid_price * ask_size) / total_size",
        },
    ),
    _declaration(
        feature_id="l2_quote_update_intensity",
        category="quote_update_intensity",
        name="L2 Quote Update Intensity",
        description=(
            "Fixture-only event-rate skeleton ordered by available_ts over "
            "synthetic L2 deltas."
        ),
        input_fields=(
            _input("event_ts", "event_ts"),
            _input("available_ts", "available_ts"),
            _input("sequence_id", "sequence_id"),
            _input("action", "action"),
        ),
        parameters={"window_seconds": 1.0, "ordering": "available_ts"},
        factor_type="event",
    ),
    _declaration(
        feature_id="l2_liquidity_regime_tag",
        category="liquidity_regime_tags",
        name="L2 Liquidity Regime Tag",
        description="Fixture-only categorical liquidity regime tag skeleton.",
        input_fields=(
            _input("side", "side"),
            _input("book_level", "book_level"),
            _input("price", "price"),
            _input("size", "size"),
            _input("order_count", "order_count"),
        ),
        parameters={"tags": ["tight_deep", "wide_or_shallow", "incomplete"]},
        factor_type="regime",
    ),
    _declaration(
        feature_id="l2_order_flow_imbalance_placeholder",
        category="future_order_flow_placeholder",
        name="L2 Order Flow Imbalance Placeholder",
        description=(
            "Placeholder declaration for future reviewed order-flow research; "
            "no production computation is implemented in ASV1-P26."
        ),
        input_fields=(
            _input("side", "side"),
            _input("book_level", "book_level"),
            _input("size", "size"),
            _input("action", "action"),
            _input("sequence_id", "sequence_id"),
        ),
        parameters={"placeholder_only": True},
        factor_type="event",
        implemented_for_fixture=False,
        notes=("Future work requires reviewed replay and sequencing assumptions.",),
    ),
)


def all_l2_feature_declarations() -> tuple[L2FeatureDeclaration, ...]:
    """Return all design-scope L2 feature declarations."""
    return L2_FEATURE_DECLARATIONS


def all_l2_factor_specs() -> tuple[FactorSpec, ...]:
    """Return draft FactorSpec-compatible declarations without registration."""
    return tuple(declaration.factor_spec for declaration in L2_FEATURE_DECLARATIONS)


def l2_feature_declaration(feature_id: str) -> L2FeatureDeclaration:
    """Return one L2 feature declaration by id."""
    for declaration in L2_FEATURE_DECLARATIONS:
        if declaration.feature_id == feature_id:
            return declaration
    msg = f"unknown L2 feature declaration {feature_id!r}"
    raise KeyError(msg)
