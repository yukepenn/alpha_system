from __future__ import annotations

import pytest

from alpha_system.governance.study_spec import (
    StudyBudgetCheck,
    StudyBudgetStatus,
    check_variant_budget,
    evaluate_variant_budget,
)
from alpha_system.governance.validation import GovernanceValidationError


def test_variant_budget_reports_respected_budget() -> None:
    result = evaluate_variant_budget(variant_budget=4, observed_count=3)

    assert isinstance(result, StudyBudgetCheck)
    assert result.status is StudyBudgetStatus.RESPECTED
    assert result.respected is True
    assert result.overrun is False
    assert result.variants_remaining == 1
    assert result.overrun_by == 0
    assert result.to_dict() == {
        "variant_budget": 4,
        "observed_count": 3,
        "status": "RESPECTED",
        "respected": True,
        "overrun": False,
        "variants_remaining": 1,
        "overrun_by": 0,
    }


def test_variant_budget_reports_exact_cap_as_respected() -> None:
    result = evaluate_variant_budget(variant_budget=4, observed_count=4)

    assert result.status is StudyBudgetStatus.RESPECTED
    assert result.respected is True
    assert result.overrun is False
    assert result.variants_remaining == 0
    assert result.overrun_by == 0


def test_variant_budget_reports_overrun_metadata() -> None:
    result = evaluate_variant_budget(variant_budget=4, observed_count=7)

    assert result.status is StudyBudgetStatus.OVERRUN
    assert result.respected is False
    assert result.overrun is True
    assert result.variants_remaining == 0
    assert result.overrun_by == 3
    assert result.to_dict()["overrun"] is True
    assert result.to_dict()["status"] == "OVERRUN"


def test_check_variant_budget_alias_is_pure_accounting() -> None:
    assert check_variant_budget(variant_budget=2, observed_count=5) == evaluate_variant_budget(
        variant_budget=2,
        observed_count=5,
    )


@pytest.mark.parametrize(
    ("variant_budget", "observed_count", "field", "code"),
    [
        (0, 0, "variant_budget", "invalid_variant_budget"),
        (-1, 0, "variant_budget", "invalid_variant_budget"),
        (True, 0, "variant_budget", "invalid_variant_budget_type"),
        ("unbounded", 0, "variant_budget", "invalid_variant_budget_type"),
        (3, -1, "observed_count", "invalid_observed_count"),
        (3, False, "observed_count", "invalid_observed_count_type"),
        (3, 1.5, "observed_count", "invalid_observed_count_type"),
    ],
)
def test_variant_budget_accounting_rejects_invalid_inputs(
    variant_budget: object,
    observed_count: object,
    field: str,
    code: str,
) -> None:
    with pytest.raises(GovernanceValidationError) as exc_info:
        evaluate_variant_budget(variant_budget, observed_count)

    assert exc_info.value.issues[0].field == field
    assert exc_info.value.issues[0].code == code
