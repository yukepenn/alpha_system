from __future__ import annotations

from datetime import UTC, datetime

import pytest

from alpha_system.data.foundation.sources import (
    DataFoundationValidationError,
    DataSourceProfile,
    IBKR_FORBIDDEN_MODES,
    READ_ONLY_HISTORICAL_MODES,
)


CREATED_AT = datetime(2026, 1, 1, tzinfo=UTC)


def _valid_profile(**overrides: object) -> DataSourceProfile:
    fields: dict[str, object] = {
        "source_id": "dsrc_test_vendor",
        "provider_name": "Synthetic Historical Vendor",
        "provider_type": "historical_data_provider",
        "allowed_modes": {"historical_data"},
        "forbidden_modes": {
            "account",
            "broker",
            "execution",
            "orders",
            "paper_trading",
            "live_trading",
            "real_time_market_data",
        },
        "requires_authorization": True,
        "market_data_permissions_note": "Synthetic note for permission limits.",
        "created_at": CREATED_AT,
    }
    fields.update(overrides)
    return DataSourceProfile(**fields)


def test_ibkr_profile_is_read_only_historical_and_forbids_trading_modes() -> None:
    profile = DataSourceProfile.ibkr_historical(created_at=CREATED_AT)

    assert profile.source_id == "dsrc_ibkr_historical"
    assert profile.provider_type == "historical_data_provider"
    assert profile.allowed_modes == READ_ONLY_HISTORICAL_MODES
    assert profile.forbidden_modes == IBKR_FORBIDDEN_MODES
    assert profile.allowed_modes.isdisjoint(profile.forbidden_modes)
    assert profile.requires_authorization is True

    for mode in ("orders", "account", "paper_trading", "live_trading", "real_time_market_data"):
        assert profile.forbids_mode(mode)
        assert not profile.allows_mode(mode)


def test_data_source_profile_rejects_missing_required_fields() -> None:
    with pytest.raises(TypeError):
        DataSourceProfile(source_id="dsrc_incomplete")  # type: ignore[call-arg]


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    [
        ("source_id", ""),
        ("provider_name", " "),
        ("provider_type", "broker"),
        ("allowed_modes", set()),
        ("forbidden_modes", ()),
        ("requires_authorization", "yes"),
        ("market_data_permissions_note", ""),
        ("created_at", datetime(2026, 1, 1)),
    ],
)
def test_data_source_profile_rejects_invalid_required_fields(
    field_name: str,
    bad_value: object,
) -> None:
    with pytest.raises(DataFoundationValidationError):
        _valid_profile(**{field_name: bad_value})


def test_data_source_profile_rejects_overlapping_mode_sets() -> None:
    with pytest.raises(DataFoundationValidationError, match="disjoint"):
        _valid_profile(
            allowed_modes={"historical_data"},
            forbidden_modes={"historical_data", "orders"},
        )


@pytest.mark.parametrize(
    "mode",
    [
        "broker",
        "execution_permission",
        "orders",
        "account_access",
        "paper_trading",
        "live_trading",
        "real_time_market_data",
        "data_completeness_claim",
    ],
)
def test_data_source_profile_rejects_allowed_modes_with_forbidden_implications(
    mode: str,
) -> None:
    with pytest.raises(DataFoundationValidationError):
        _valid_profile(allowed_modes={"historical_data", mode})


def test_ibkr_profile_does_not_imply_broker_execution_or_completeness() -> None:
    profile = DataSourceProfile.ibkr_historical(created_at=CREATED_AT)
    forbidden_tokens = {
        "broker",
        "execution",
        "orders",
        "account",
        "paper",
        "live",
        "real_time",
        "complete",
        "completeness",
    }

    for mode in profile.allowed_modes:
        assert not any(token in mode for token in forbidden_tokens)

    assert "broker_readiness" in profile.forbidden_modes
    assert "execution_permission" in profile.forbidden_modes
    assert "data_completeness_claim" in profile.forbidden_modes
