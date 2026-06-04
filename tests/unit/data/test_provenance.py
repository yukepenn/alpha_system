from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from alpha_system.data.foundation.instruments import FuturesContractRecord
from alpha_system.data.foundation.series import (
    CONTINUOUS_FUTURES_REQUIRED_LABELS,
    DATED_FUTURES_AVAILABILITY_SOURCE,
    ContinuousFuturesSeriesRecord,
    DatedFuturesSeriesRecord,
    reject_mixed_series_provenance_labels,
    require_dated_contract_truth,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError

RETRIEVED_AT = datetime(2026, 6, 3, tzinfo=UTC)


def _contract(
    *,
    contract_id: str = "fcr_es_2025_03",
    root_symbol: str = "ES",
    contract_month: str = "H5",
    multiplier: Decimal = Decimal("50"),
    trading_class: str = "ES",
) -> FuturesContractRecord:
    return FuturesContractRecord(
        contract_id=contract_id,
        root_symbol=root_symbol,
        contract_month=contract_month,
        ib_symbol=root_symbol,
        trading_class=trading_class,
        con_id=123456789,
        last_trade_date_or_contract_month="202503",
        expiration=date(2025, 3, 21),
        multiplier=multiplier,
        exchange="CME",
        currency="USD",
        include_expired_support_status="supported",
    )


def _continuous_values(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "series_id": "cfsr_ibkr_es_continuous_v1",
        "root_symbol": "ES",
        "provider": "IBKR",
        "provenance_label": "provider_continuous",
        "orderable": False,
        "dated_truth": False,
        "roll_adjustment_note": (
            "Provider continuous diagnostic artifact; not a tradable roll "
            "and not dated truth."
        ),
        "source_retrieved_at": RETRIEVED_AT.isoformat(),
    }
    values.update(overrides)
    return values


def _availability_window(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "start": "2025-01-01",
        "end": "2025-03-21",
        "availability_source": "discovered_not_assumed",
        "availability_log_ref": "synthetic:contract-discovery-log/es-h5",
    }
    values.update(overrides)
    return values


def _dated_values(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "series_id": "dfsr_es_unadjusted_h5_v1",
        "root_symbol": "ES",
        "contract_universe": (_contract(),),
        "roll_policy_id": "roll_cme_index_futures_quarterly",
        "adjustment_method": "unadjusted",
        "availability_window": _availability_window(),
        "validation_status": "discovered",
    }
    values.update(overrides)
    return values


def test_series_records_validate_required_fields_and_are_immutable() -> None:
    continuous = ContinuousFuturesSeriesRecord.from_mapping(_continuous_values())
    dated = DatedFuturesSeriesRecord.from_mapping(_dated_values())

    assert continuous.series_id == "cfsr_ibkr_es_continuous_v1"
    assert continuous.provenance_labels == CONTINUOUS_FUTURES_REQUIRED_LABELS
    assert continuous.implies_dated_contract_truth is False
    assert continuous.implies_orderability is False
    assert continuous.implies_tradability is False

    assert dated.series_id == "dfsr_es_unadjusted_h5_v1"
    assert dated.provenance_label == "dated_contract"
    assert dated.availability_source == DATED_FUTURES_AVAILABILITY_SOURCE
    assert dated.implies_full_historical_availability is False
    assert dated.implies_best_execution_roll is False
    assert dated.implies_tradability is False

    with pytest.raises(FrozenInstanceError):
        continuous.orderable = True  # type: ignore[misc]
    with pytest.raises(TypeError):
        dated.availability_window["full_history"] = False  # type: ignore[index]

    missing_continuous = _continuous_values()
    missing_continuous.pop("series_id")
    with pytest.raises(DataFoundationValidationError, match="missing required fields"):
        ContinuousFuturesSeriesRecord.from_mapping(missing_continuous)

    missing_dated = _dated_values()
    missing_dated.pop("availability_window")
    with pytest.raises(DataFoundationValidationError, match="missing required fields"):
        DatedFuturesSeriesRecord.from_mapping(missing_dated)


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"provenance_label": "dated_contract"}, "provider_continuous"),
        ({"orderable": True}, "orderable must be false"),
        ({"dated_truth": True}, "dated_truth must be false"),
        ({"root_symbol": "YM"}, "futures instrument master"),
        (
            {"provenance_labels": {"provider_continuous", "non_orderable"}},
            "mandatory continuous set",
        ),
        ({"roll_adjustment_note": "Provider adjusted artifact."}, "disclaim"),
        ({"tradable": True}, "forbidden trading/order affordance"),
    ],
)
def test_continuous_series_fails_closed_on_truth_and_orderability(
    overrides: dict[str, object],
    match: str,
) -> None:
    with pytest.raises(DataFoundationValidationError, match=match):
        ContinuousFuturesSeriesRecord.from_mapping(_continuous_values(**overrides))


def test_continuous_series_cannot_be_used_as_dated_contract_truth() -> None:
    continuous = ContinuousFuturesSeriesRecord.from_mapping(_continuous_values())

    with pytest.raises(DataFoundationValidationError, match="cannot be used"):
        require_dated_contract_truth(continuous)

    dated = DatedFuturesSeriesRecord.from_mapping(_dated_values())
    assert require_dated_contract_truth(dated) is dated


def test_dated_series_enforces_adjusted_vs_unadjusted_explicitly() -> None:
    unadjusted = DatedFuturesSeriesRecord.from_mapping(
        _dated_values(adjustment_method="unadjusted")
    )
    back_adjusted = DatedFuturesSeriesRecord.from_mapping(
        _dated_values(
            series_id="dfsr_es_back_adjusted_h5_v1",
            adjustment_method="back_adjusted",
        )
    )

    assert unadjusted.adjusted_vs_unadjusted == "unadjusted"
    assert back_adjusted.adjusted_vs_unadjusted == "adjusted"

    with pytest.raises(DataFoundationValidationError, match="adjustment_method"):
        DatedFuturesSeriesRecord.from_mapping(
            _dated_values(adjustment_method="implicit")
        )


def test_dated_series_availability_is_discovered_not_assumed() -> None:
    record = DatedFuturesSeriesRecord.from_mapping(_dated_values())

    assert record.availability_window["availability_source"] == (
        DATED_FUTURES_AVAILABILITY_SOURCE
    )
    assert "full_history" not in record.to_mapping()["availability_window"]

    with pytest.raises(DataFoundationValidationError, match="discovered_not_assumed"):
        DatedFuturesSeriesRecord.from_mapping(
            _dated_values(
                availability_window=_availability_window(
                    availability_source="assumed_available",
                )
            )
        )

    with pytest.raises(DataFoundationValidationError, match="full-history"):
        DatedFuturesSeriesRecord.from_mapping(
            _dated_values(
                availability_window=_availability_window(full_history_claim=False)
            )
        )


def test_dated_contract_universe_must_be_non_empty_and_root_consistent() -> None:
    with pytest.raises(DataFoundationValidationError, match="must not be empty"):
        DatedFuturesSeriesRecord.from_mapping(_dated_values(contract_universe=()))

    with pytest.raises(DataFoundationValidationError, match="FuturesContractRecord"):
        DatedFuturesSeriesRecord.from_mapping(
            _dated_values(contract_universe=("fcr_es_2025_03",))
        )

    nq_contract = _contract(
        contract_id="fcr_nq_2025_03",
        root_symbol="NQ",
        contract_month="H5",
        multiplier=Decimal("20"),
        trading_class="NQ",
    )
    with pytest.raises(DataFoundationValidationError, match="roots must match"):
        DatedFuturesSeriesRecord.from_mapping(
            _dated_values(contract_universe=(nq_contract,))
        )


def test_provenance_separation_guard_rejects_mixed_labels() -> None:
    assert reject_mixed_series_provenance_labels(
        series_kind="provider_continuous",
        labels=CONTINUOUS_FUTURES_REQUIRED_LABELS,
    ) == CONTINUOUS_FUTURES_REQUIRED_LABELS

    with pytest.raises(DataFoundationValidationError, match="continuous-only labels"):
        reject_mixed_series_provenance_labels(
            series_kind="dated_contract",
            labels=("dated_contract", "provider_continuous"),
        )

    with pytest.raises(DataFoundationValidationError, match="continuous-only labels"):
        DatedFuturesSeriesRecord.from_mapping(
            _dated_values(provenance_labels=("dated_contract", "provider_continuous"))
        )
