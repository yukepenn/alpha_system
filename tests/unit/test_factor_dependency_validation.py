from __future__ import annotations

import json
from pathlib import Path

import pytest

from alpha_system.factors.dependency_spec import (
    FactorDependencyError,
    normalize_input_fields,
    validate_declared_dependencies,
)
from alpha_system.factors.spec import FactorSpec, FactorSpecError


REPO_ROOT = Path(__file__).resolve().parents[2]
INVALID_LABEL = (
    REPO_ROOT / "configs" / "factors" / "examples" / "invalid_label_input_factor.json"
)


def test_declared_dependencies_accept_only_declared_used_fields() -> None:
    fields = normalize_input_fields(
        [{"name": "close_price", "domain": "bar", "source_field": "close"}]
    )

    validate_declared_dependencies(fields, used_fields=("close_price", "close"))

    with pytest.raises(FactorDependencyError, match="undeclared"):
        validate_declared_dependencies(fields, used_fields=("close", "raw_close"))


def test_label_domain_is_rejected_as_factor_input() -> None:
    with pytest.raises(FactorDependencyError, match="label fields"):
        normalize_input_fields(
            [
                {
                    "name": "future_return_label",
                    "domain": "label",
                    "source_field": "forward_return_1m",
                }
            ]
        )


def test_label_like_source_field_is_rejected() -> None:
    with pytest.raises(FactorDependencyError, match="label field"):
        normalize_input_fields(
            [
                {
                    "name": "future_return_input",
                    "domain": "bar",
                    "source_field": "forward_return_1m",
                }
            ]
        )


def test_raw_ad_hoc_input_domain_is_rejected() -> None:
    with pytest.raises(FactorDependencyError, match="unsupported"):
        normalize_input_fields(
            [{"name": "raw_close", "domain": "raw", "source_field": "close"}]
        )


def test_invalid_example_rejects_label_leakage() -> None:
    payload = json.loads(INVALID_LABEL.read_text(encoding="utf-8"))

    with pytest.raises(FactorSpecError, match="label"):
        FactorSpec.from_mapping(payload)
