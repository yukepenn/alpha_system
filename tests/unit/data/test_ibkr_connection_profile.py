from __future__ import annotations

import dataclasses
import socket
from datetime import UTC, datetime

import pytest

import alpha_system.data.foundation.ibkr as ibkr_module
from alpha_system.data.foundation.ibkr import (
    DEFAULT_IBKR_CLIENT_ID,
    DEFAULT_IBKR_CONNECTION_TIMEOUT,
    DEFAULT_IBKR_ENVIRONMENT,
    DEFAULT_IBKR_HOST,
    DEFAULT_IBKR_PORT,
    DEFAULT_IBKR_READ_ONLY_MODE,
    IBKRConnectionProfile,
    run_connection_doctor,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError


VALIDATED_AT = datetime(2026, 1, 1, tzinfo=UTC)


def _profile(**overrides: object) -> IBKRConnectionProfile:
    fields: dict[str, object] = {
        "host": DEFAULT_IBKR_HOST,
        "port": DEFAULT_IBKR_PORT,
        "client_id": DEFAULT_IBKR_CLIENT_ID,
        "read_only_mode": DEFAULT_IBKR_READ_ONLY_MODE,
        "environment": DEFAULT_IBKR_ENVIRONMENT,
        "connection_timeout": DEFAULT_IBKR_CONNECTION_TIMEOUT,
        "validated_at": VALIDATED_AT,
    }
    fields.update(overrides)
    return IBKRConnectionProfile(**fields)


def test_connection_profile_fields_are_the_campaign_required_fields() -> None:
    assert [field.name for field in dataclasses.fields(IBKRConnectionProfile)] == [
        "host",
        "port",
        "client_id",
        "read_only_mode",
        "environment",
        "connection_timeout",
        "doctor_status",
        "validated_at",
    ]


def test_connection_profile_defaults_are_read_only_historical() -> None:
    profile = IBKRConnectionProfile.ibkr_historical(validated_at=VALIDATED_AT)

    assert profile.host == "127.0.0.1"
    assert profile.port == 4002
    assert profile.client_id == 201
    assert profile.read_only_mode is True
    assert profile.environment == "local_wsl2"
    assert profile.connection_timeout == 10.0
    assert profile.validated_at == VALIDATED_AT
    assert profile.doctor_status["status"] == "not_run"
    assert profile.doctor_status["reachability"] == "not_probed_scaffold"
    assert profile.doctor_status["probe_performed"] is False
    assert profile.doctor_status["external_call_performed"] is False


def test_connection_profile_from_env_uses_defaults_when_unset() -> None:
    profile = IBKRConnectionProfile.from_env({}, validated_at=VALIDATED_AT)

    assert profile.host == "127.0.0.1"
    assert profile.port == 4002
    assert profile.client_id == 201
    assert profile.read_only_mode is True


def test_connection_profile_from_env_reads_allowed_overrides() -> None:
    profile = IBKRConnectionProfile.from_env(
        {
            "ALPHA_IBKR_HOST": "localhost",
            "ALPHA_IBKR_PORT": "4002",
            "ALPHA_IBKR_CLIENT_ID": "204",
            "ALPHA_IBKR_READ_ONLY_MODE": "true",
        },
        validated_at=VALIDATED_AT,
    )

    assert profile.host == "localhost"
    assert profile.port == 4002
    assert profile.client_id == 204
    assert profile.read_only_mode is True


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    [
        ("host", ""),
        ("host", "http://127.0.0.1"),
        ("host", "0.0.0.0"),
        ("port", 0),
        ("port", 70000),
        ("port", "4002"),
        ("client_id", 101),
        ("client_id", 102),
        ("client_id", 210),
        ("read_only_mode", False),
        ("read_only_mode", "true"),
        ("environment", "paper"),
        ("connection_timeout", 0),
        ("connection_timeout", "10"),
        ("validated_at", datetime(2026, 1, 1)),
        ("doctor_status", {"status": "ok"}),
        (
            "doctor_status",
            {
                "status": "ok",
                "reachability": "reachable",
                "probe_performed": True,
                "external_call_performed": False,
                "diagnostics": ("bad probe",),
            },
        ),
    ],
)
def test_connection_profile_rejects_invalid_fields(
    field_name: str,
    bad_value: object,
) -> None:
    with pytest.raises(DataFoundationValidationError):
        _profile(**{field_name: bad_value})


@pytest.mark.parametrize(
    ("env", "match"),
    [
        ({"ALPHA_IBKR_PORT": "not-an-int"}, "integer"),
        ({"ALPHA_IBKR_CLIENT_ID": "101"}, "hard-blocked"),
        ({"ALPHA_IBKR_CLIENT_ID": "210"}, "201-209"),
        ({"ALPHA_IBKR_READ_ONLY_MODE": "false"}, "read_only_mode"),
        ({"ALPHA_IBKR_READ_ONLY_MODE": "maybe"}, "boolean"),
    ],
)
def test_connection_profile_from_env_fails_closed_on_bad_values(
    env: dict[str, str],
    match: str,
) -> None:
    with pytest.raises(DataFoundationValidationError, match=match):
        IBKRConnectionProfile.from_env(env, validated_at=VALIDATED_AT)


def test_connection_doctor_reports_status_without_opening_socket(monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked_socket(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("connection doctor must not open a socket in DATA-P03")

    monkeypatch.setattr(socket, "create_connection", blocked_socket)
    monkeypatch.setattr(socket, "socket", blocked_socket)
    profile = _profile()

    doctored = run_connection_doctor(profile)

    assert doctored.host == profile.host
    assert doctored.port == profile.port
    assert doctored.client_id == profile.client_id
    assert doctored.doctor_status["status"] == "configuration_validated"
    assert doctored.doctor_status["reachability"] == "not_probed_scaffold"
    assert doctored.doctor_status["probe_performed"] is False
    assert doctored.doctor_status["external_call_performed"] is False
    assert doctored.doctor_status["retry_target"] is None
    assert doctored.doctor_status["host"] == "127.0.0.1"
    assert doctored.doctor_status["port"] == 4002


def test_connection_doctor_can_build_profile_from_env_without_retry_target() -> None:
    doctored = run_connection_doctor(
        env={
            "ALPHA_IBKR_HOST": "127.0.0.1",
            "ALPHA_IBKR_PORT": "4002",
            "ALPHA_IBKR_CLIENT_ID": "201",
            "ALPHA_IBKR_READ_ONLY_MODE": "true",
        }
    )

    assert doctored.doctor_status["status"] == "configuration_validated"
    assert doctored.doctor_status["retry_target"] is None


def test_connection_doctor_rejects_ambiguous_profile_and_env_inputs() -> None:
    with pytest.raises(DataFoundationValidationError, match="either profile or env"):
        run_connection_doctor(_profile(), env={})


def test_ibkr_module_exposes_no_broker_style_public_surface() -> None:
    prohibited_tokens = ("order", "account", "position", "paper", "live", "real_time")
    public_names = set(ibkr_module.__all__)
    public_methods = {
        name
        for object_ in (IBKRConnectionProfile, ibkr_module.IBKRClientIdPolicy)
        for name in dir(object_)
        if not name.startswith("_")
    }

    offenders = sorted(
        name
        for name in public_names | public_methods
        if any(token in name.lower() for token in prohibited_tokens)
    )

    assert offenders == []
    assert "socket" not in ibkr_module.__dict__
    assert "ib_insync" not in ibkr_module.__dict__
