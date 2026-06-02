from __future__ import annotations

from alpha_system.core.enums import FactorInputDomain, FactorStatus, LabelType
from alpha_system.factors.contracts import (
    DRAFT_FACTOR_LONG_TERM_MATERIALIZATION_DEFAULT,
)


def test_factor_lifecycle_values_are_exact() -> None:
    assert [status.value for status in FactorStatus] == [
        "draft",
        "candidate",
        "validated",
        "approved",
        "deprecated",
    ]


def test_label_type_values_are_complete() -> None:
    assert [label_type.value for label_type in LabelType] == [
        "forward_return_1m",
        "forward_return_3m",
        "forward_return_5m",
        "forward_return_10m",
        "forward_return_30m",
        "mfe_by_horizon",
        "mae_by_horizon",
        "target_before_stop",
        "stop_before_target",
        "future_realized_volatility",
        "future_spread_liquidity",
    ]


def test_factor_inputs_do_not_include_labels() -> None:
    assert "label" not in {domain.value for domain in FactorInputDomain}


def test_draft_factor_materialization_is_not_enabled_by_default() -> None:
    assert DRAFT_FACTOR_LONG_TERM_MATERIALIZATION_DEFAULT is False
