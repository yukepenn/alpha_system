from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal

import pytest

from alpha_system.data.foundation.instruments import FuturesContractRecord
from alpha_system.data.foundation.rolls import (
    DERIVED_STITCHED_ROLL_PROVENANCE_LABEL,
    REQUIRED_ROLL_CALENDAR_FIELDS,
    REQUIRED_ROLL_POLICY_FIELDS,
    ROLL_ADJUSTMENT_METHODS,
    ROLL_VALIDATION_STATUSES,
    RollCalendarRecord,
    RollPolicy,
    require_roll_calendar_matches_policy,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError


def _contract(
    *,
    contract_id: str = "fcr_es_2025_03",
    contract_month: str = "H5",
    con_id: int | None = 123456789,
    expiration: date = date(2025, 3, 21),
) -> FuturesContractRecord:
    return FuturesContractRecord(
        contract_id=contract_id,
        root_symbol="ES",
        contract_month=contract_month,
        ib_symbol="ES",
        trading_class="ES",
        con_id=con_id,
        last_trade_date_or_contract_month=expiration.strftime("%Y%m%d"),
        expiration=expiration,
        multiplier=Decimal("50"),
        exchange="CME",
        currency="USD",
        include_expired_support_status="supported",
    )


def _policy_values(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "roll_policy_id": "roll_es_calendar_unadjusted_v1",
        "method": "calendar_days_before_expiration",
        "roll_trigger": "calendar",
        "adjustment_method": "none",
        "fallback_rule": "no_roll_without_evidence",
        "uses_volume": False,
        "uses_open_interest": False,
        "source": "dsrc_synthetic_roll_policy_to_be_verified",
    }
    values.update(overrides)
    return values


def _evidence(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "basis": "synthetic calendar trigger",
        "source_ref": "synthetic:roll-calendar/es-h5-to-m5",
        "notes": ("hand-authored fixture", "not exchange final"),
    }
    values.update(overrides)
    return values


def _calendar_values(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "roll_calendar_id": "rollcal_es_h5_to_m5_synthetic",
        "root_symbol": "ES",
        "from_contract": _contract(),
        "to_contract": _contract(
            contract_id="fcr_es_2025_06",
            contract_month="M5",
            con_id=123456790,
            expiration=date(2025, 6, 20),
        ),
        "roll_date": "2025-03-14",
        "method": "calendar_days_before_expiration",
        "evidence": _evidence(),
        "validation_status": "unvalidated",
    }
    values.update(overrides)
    return values


def test_roll_policy_exposes_required_fields_and_is_immutable() -> None:
    policy = RollPolicy.from_mapping(_policy_values())
    mapping = policy.to_mapping()

    for field_name in REQUIRED_ROLL_POLICY_FIELDS:
        assert field_name in mapping

    assert policy.roll_policy_id == "roll_es_calendar_unadjusted_v1"
    assert policy.method == "calendar_days_before_expiration"
    assert policy.adjustment_method == "none"
    assert policy.adjusted_vs_unadjusted == "unadjusted"
    assert policy.uses_volume is False
    assert policy.uses_open_interest is False
    assert policy.describes_provider_continuous is False
    assert policy.implies_best_execution_roll is False
    assert policy.implies_tradability is False

    with pytest.raises(FrozenInstanceError):
        policy.method = "volume_crossover"  # type: ignore[misc]


def test_roll_policy_enforces_adjusted_vs_unadjusted_explicitly() -> None:
    unadjusted = RollPolicy.from_mapping(_policy_values(adjustment_method="none"))
    back_adjusted = RollPolicy.from_mapping(
        _policy_values(
            roll_policy_id="roll_es_calendar_back_adjusted_v1",
            adjustment_method="back_adjusted",
        )
    )
    ratio_adjusted = RollPolicy.from_mapping(
        _policy_values(
            roll_policy_id="roll_es_calendar_ratio_adjusted_v1",
            adjustment_method="ratio_adjusted",
        )
    )

    assert ROLL_ADJUSTMENT_METHODS == {"none", "back_adjusted", "ratio_adjusted"}
    assert unadjusted.adjusted_vs_unadjusted == "unadjusted"
    assert back_adjusted.adjusted_vs_unadjusted == "adjusted"
    assert ratio_adjusted.adjusted_vs_unadjusted == "adjusted"

    with pytest.raises(DataFoundationValidationError, match="adjustment_method"):
        RollPolicy.from_mapping(_policy_values(adjustment_method="implicit_adjustment"))


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"roll_trigger": "volume"}, "requires roll_trigger"),
        ({"uses_volume": True}, "uses_volume=False"),
        ({"uses_open_interest": True}, "uses_open_interest=False"),
        ({"method": "freeform_roll"}, "method must be one of"),
        ({"fallback_rule": "guess_roll_date"}, "fallback_rule"),
        ({"source": "dsrc_cme_official_final_roll_policy"}, "exchange/CME finality"),
        ({"source": "dsrc_provider_continuous_roll_policy"}, "provider-continuous"),
        ({"best_execution_roll": True}, "forbidden trading/order affordance"),
    ],
)
def test_roll_policy_fails_closed_on_ambiguous_or_forbidden_fields(
    overrides: dict[str, object],
    match: str,
) -> None:
    with pytest.raises(DataFoundationValidationError, match=match):
        RollPolicy.from_mapping(_policy_values(**overrides))


def test_roll_policy_missing_required_fields_fail_closed() -> None:
    for field_name in REQUIRED_ROLL_POLICY_FIELDS:
        values = _policy_values()
        values.pop(field_name)
        with pytest.raises(DataFoundationValidationError, match="missing required fields"):
            RollPolicy.from_mapping(values)


def test_roll_calendar_exposes_required_fields_and_matches_policy() -> None:
    policy = RollPolicy.from_mapping(_policy_values())
    calendar = RollCalendarRecord.from_mapping(_calendar_values())
    mapping = calendar.to_mapping()

    for field_name in REQUIRED_ROLL_CALENDAR_FIELDS:
        assert field_name in mapping

    assert calendar.roll_calendar_id == "rollcal_es_h5_to_m5_synthetic"
    assert calendar.root_symbol == "ES"
    assert calendar.from_contract_id == "fcr_es_2025_03"
    assert calendar.to_contract_id == "fcr_es_2025_06"
    assert calendar.roll_date == date(2025, 3, 14)
    assert calendar.method == policy.method
    assert calendar.validation_status in ROLL_VALIDATION_STATUSES
    assert calendar.provenance_label == DERIVED_STITCHED_ROLL_PROVENANCE_LABEL
    assert calendar.describes_provider_continuous is False
    assert calendar.implies_provider_continuous_dated_truth is False
    assert calendar.implies_best_execution_roll is False
    assert calendar.implies_tradability is False
    assert require_roll_calendar_matches_policy(calendar, policy) is calendar


def test_roll_calendar_missing_method_evidence_or_status_fails_closed() -> None:
    for field_name in ("method", "evidence", "validation_status"):
        values = _calendar_values()
        values.pop(field_name)
        with pytest.raises(DataFoundationValidationError, match="missing required fields"):
            RollCalendarRecord.from_mapping(values)

    with pytest.raises(DataFoundationValidationError, match="evidence"):
        RollCalendarRecord.from_mapping(_calendar_values(evidence={}))
    with pytest.raises(DataFoundationValidationError, match="validation_status"):
        RollCalendarRecord.from_mapping(_calendar_values(validation_status="execution_ready"))


def test_roll_calendar_requires_distinct_dated_contract_identities() -> None:
    from_contract = _contract()

    with pytest.raises(DataFoundationValidationError, match="distinct dated-contract"):
        RollCalendarRecord.from_mapping(
            _calendar_values(from_contract=from_contract, to_contract=from_contract)
        )

    with pytest.raises(DataFoundationValidationError, match="distinct discovered con_id"):
        RollCalendarRecord.from_mapping(
            _calendar_values(
                to_contract=_contract(
                    contract_id="fcr_es_same_conid",
                    contract_month="M5",
                    expiration=date(2025, 6, 20),
                )
            )
        )


def test_roll_calendar_requires_valid_known_root_and_contract_root_consistency() -> None:
    with pytest.raises(DataFoundationValidationError, match="supported mini/micro roots"):
        RollCalendarRecord.from_mapping(_calendar_values(root_symbol="YM"))

    with pytest.raises(DataFoundationValidationError, match="roots must match"):
        RollCalendarRecord.from_mapping(_calendar_values(root_symbol="NQ"))


def test_roll_calendar_rejects_provider_continuous_and_execution_quality_markers() -> None:
    for overrides in (
        {"provenance_label": "provider_continuous"},
        {"from_contract": {"sec_type": "CONTFUT"}},
        {"evidence": _evidence(basis="best_execution calendar")},
        {"tradable": True},
    ):
        with pytest.raises(DataFoundationValidationError):
            RollCalendarRecord.from_mapping(_calendar_values(**overrides))

    calendar = RollCalendarRecord.from_mapping(_calendar_values())
    forbidden_fields = {
        "best_execution_roll",
        "execution_quality",
        "orderable",
        "tradable",
        "tradeable",
    }
    assert forbidden_fields.isdisjoint(calendar.to_mapping())


def test_roll_calendar_policy_method_mismatch_fails_closed() -> None:
    calendar = RollCalendarRecord.from_mapping(_calendar_values())
    volume_policy = RollPolicy.from_mapping(
        _policy_values(
            roll_policy_id="roll_es_volume_v1",
            method="volume_crossover",
            roll_trigger="volume",
            fallback_rule="calendar_fallback_unvalidated",
            uses_volume=True,
        )
    )

    with pytest.raises(DataFoundationValidationError, match="method must match"):
        require_roll_calendar_matches_policy(calendar, volume_policy)
