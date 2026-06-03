from __future__ import annotations

import dataclasses

import pytest

from alpha_system.data.foundation.sources import (
    DataAccessMode,
    DataFoundationValidationError,
)


VALID_EXTERNAL_ENV = {
    "ALPHA_DATA_PULL_AUTHORIZED": "true",
    "ALPHA_ALLOW_EXTERNAL_IBKR": "true",
    "ALPHA_IBKR_READ_ONLY_MODE": "true",
    "ALPHA_ALLOW_RAW_LOCAL_WRITE": "true",
}


def test_data_access_mode_fields_are_the_campaign_required_fields() -> None:
    assert [field.name for field in dataclasses.fields(DataAccessMode)] == [
        "mode",
        "requires_env",
        "allows_external_api",
        "allows_raw_write",
        "allows_canonical_write",
        "ci_allowed",
    ]


def test_local_data_access_modes_allow_no_external_api_and_are_ci_safe() -> None:
    dry_run = DataAccessMode.dry_run()
    synthetic = DataAccessMode.synthetic()

    assert dry_run.mode == "dry_run"
    assert dry_run.requires_env == ()
    assert dry_run.allows_external_api is False
    assert dry_run.allows_raw_write is False
    assert dry_run.allows_canonical_write is False
    assert dry_run.ci_allowed is True

    assert synthetic.mode == "synthetic"
    assert synthetic.requires_env == ()
    assert synthetic.allows_external_api is False
    assert synthetic.allows_raw_write is False
    assert synthetic.allows_canonical_write is True
    assert synthetic.ci_allowed is True

    assert dry_run.validate_runtime_env({"CI": "true"}) is dry_run
    assert synthetic.validate_runtime_env({"CI": "true"}) is synthetic


def test_external_data_access_modes_require_authorization_env_and_are_not_ci_safe() -> None:
    smoke = DataAccessMode.smoke()
    authorized_pull = DataAccessMode.authorized_pull()

    assert smoke.mode == "smoke"
    assert smoke.requires_env == (
        "ALPHA_DATA_PULL_AUTHORIZED",
        "ALPHA_ALLOW_EXTERNAL_IBKR",
        "ALPHA_IBKR_READ_ONLY_MODE",
    )
    assert smoke.allows_external_api is True
    assert smoke.allows_raw_write is False
    assert smoke.allows_canonical_write is False
    assert smoke.ci_allowed is False

    assert authorized_pull.mode == "authorized_pull"
    assert authorized_pull.requires_env == (
        "ALPHA_DATA_PULL_AUTHORIZED",
        "ALPHA_ALLOW_EXTERNAL_IBKR",
        "ALPHA_IBKR_READ_ONLY_MODE",
        "ALPHA_ALLOW_RAW_LOCAL_WRITE",
    )
    assert authorized_pull.allows_external_api is True
    assert authorized_pull.allows_raw_write is True
    assert authorized_pull.allows_canonical_write is False
    assert authorized_pull.ci_allowed is False

    assert smoke.validate_runtime_env(VALID_EXTERNAL_ENV, ci=False) is smoke
    assert authorized_pull.validate_runtime_env(VALID_EXTERNAL_ENV, ci=False) is authorized_pull


@pytest.mark.parametrize("mode", ["smoke", "authorized_pull"])
def test_external_data_access_modes_are_forbidden_in_ci(mode: str) -> None:
    with pytest.raises(DataFoundationValidationError, match="CI"):
        DataAccessMode.for_mode(mode).validate_runtime_env(VALID_EXTERNAL_ENV, ci=True)


def test_external_data_access_mode_fails_closed_on_malformed_ci_env() -> None:
    env = {**VALID_EXTERNAL_ENV, "CI": "definitely"}

    with pytest.raises(DataFoundationValidationError, match="CI"):
        DataAccessMode.smoke().validate_runtime_env(env)


@pytest.mark.parametrize(
    "env",
    [
        {},
        {"ALPHA_DATA_PULL_AUTHORIZED": "true"},
        {
            "ALPHA_DATA_PULL_AUTHORIZED": "true",
            "ALPHA_ALLOW_EXTERNAL_IBKR": "true",
            "ALPHA_IBKR_READ_ONLY_MODE": "false",
        },
    ],
)
def test_external_data_access_modes_fail_closed_without_required_env(
    env: dict[str, str],
) -> None:
    with pytest.raises(DataFoundationValidationError):
        DataAccessMode.smoke().validate_runtime_env(env, ci=False)


def test_data_access_mode_rejects_unknown_mode() -> None:
    with pytest.raises(DataFoundationValidationError, match="mode must be one of"):
        DataAccessMode.for_mode("paper")


@pytest.mark.parametrize(
    "overrides",
    [
        {"allows_external_api": True},
        {"ci_allowed": False},
        {"requires_env": ("ALPHA_DATA_PULL_AUTHORIZED",)},
        {"allows_raw_write": True},
    ],
)
def test_data_access_mode_rejects_tampered_contract_fields(
    overrides: dict[str, object],
) -> None:
    fields: dict[str, object] = {
        "mode": "dry_run",
        "requires_env": (),
        "allows_external_api": False,
        "allows_raw_write": False,
        "allows_canonical_write": False,
        "ci_allowed": True,
    }
    fields.update(overrides)

    with pytest.raises(DataFoundationValidationError, match="campaign access-mode contract"):
        DataAccessMode(**fields)
