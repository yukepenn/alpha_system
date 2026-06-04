from __future__ import annotations

from datetime import UTC, datetime

import pytest

from alpha_system.data.foundation.sources import (
    DATABENTO_EXTERNAL_ACCESS_ENV,
    DATABENTO_FORBIDDEN_MODES,
    READ_ONLY_HISTORICAL_MODES,
    DataFoundationValidationError,
    DataSourceProfile,
    require_databento_external_access,
)

CREATED_AT = datetime(2026, 6, 1, tzinfo=UTC)

VALID_DATABENTO_ENV = {
    "ALPHA_DATA_PULL_AUTHORIZED": "true",
    "ALPHA_ALLOW_EXTERNAL_DATABENTO": "true",
}


def test_databento_profile_is_read_only_historical_and_forbids_trading_modes() -> None:
    profile = DataSourceProfile.databento_historical(created_at=CREATED_AT)

    assert profile.source_id == "dsrc_databento_historical"
    assert profile.provider_name == "Databento"
    assert profile.provider_type == "historical_data_provider"
    assert profile.allowed_modes == READ_ONLY_HISTORICAL_MODES
    assert profile.forbidden_modes == DATABENTO_FORBIDDEN_MODES
    assert profile.allowed_modes.isdisjoint(profile.forbidden_modes)
    assert profile.requires_authorization is True

    for mode in ("orders", "account", "paper_trading", "live_trading", "broker"):
        assert profile.forbids_mode(mode)
        assert not profile.allows_mode(mode)


@pytest.mark.parametrize(
    "env",
    [
        {},
        {"ALPHA_DATA_PULL_AUTHORIZED": "true"},
        {"ALPHA_ALLOW_EXTERNAL_DATABENTO": "true"},
        {
            "ALPHA_DATA_PULL_AUTHORIZED": "true",
            "ALPHA_ALLOW_EXTERNAL_DATABENTO": "false",
        },
    ],
)
def test_databento_external_access_fails_closed_without_required_env(
    env: dict[str, str],
) -> None:
    with pytest.raises(DataFoundationValidationError):
        require_databento_external_access(env, ci=False)


def test_databento_external_access_refuses_ci() -> None:
    with pytest.raises(DataFoundationValidationError, match="CI"):
        require_databento_external_access(VALID_DATABENTO_ENV, ci=True)

    with pytest.raises(DataFoundationValidationError, match="CI"):
        require_databento_external_access({**VALID_DATABENTO_ENV, "CI": "true"})


def test_databento_external_access_passes_with_gates_and_does_not_require_api_key() -> None:
    env = dict(VALID_DATABENTO_ENV)

    authorization = require_databento_external_access(env, ci=False)

    assert "DATABENTO_API_KEY" not in env
    assert authorization.requires_env == (
        "ALPHA_DATA_PULL_AUTHORIZED",
        DATABENTO_EXTERNAL_ACCESS_ENV,
    )
    assert authorization.allows_external_api is True
    assert authorization.allows_raw_write is False
    assert authorization.ci_allowed is False


def test_databento_external_access_requires_raw_write_gate_when_requested() -> None:
    with pytest.raises(DataFoundationValidationError, match="ALPHA_ALLOW_RAW_LOCAL_WRITE"):
        require_databento_external_access(VALID_DATABENTO_ENV, ci=False, require_raw_write=True)

    authorization = require_databento_external_access(
        {**VALID_DATABENTO_ENV, "ALPHA_ALLOW_RAW_LOCAL_WRITE": "true"},
        ci=False,
        require_raw_write=True,
    )

    assert authorization.requires_env == (
        "ALPHA_DATA_PULL_AUTHORIZED",
        "ALPHA_ALLOW_EXTERNAL_DATABENTO",
        "ALPHA_ALLOW_RAW_LOCAL_WRITE",
    )
    assert authorization.allows_raw_write is True
