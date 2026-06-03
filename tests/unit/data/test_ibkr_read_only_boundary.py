from __future__ import annotations

import logging

import pytest

from alpha_system.data.foundation.ibkr import (
    IBKRReadOnlyApiBoundary,
    READ_ONLY_IBKR_API_METHODS,
    ReadOnlyBoundaryViolation,
    build_read_only_ibkr_boundary,
)
from alpha_system.data.foundation.sources import (
    DataAccessMode,
    DataFoundationValidationError,
)


VALID_EXTERNAL_ENV = {
    "ALPHA_DATA_PULL_AUTHORIZED": "true",
    "ALPHA_ALLOW_EXTERNAL_IBKR": "true",
    "ALPHA_IBKR_READ_ONLY_MODE": "true",
}

FORBIDDEN_API_METHODS = (
    "place" + "Order",
    "req" + "Positions",
    "req" + "AccountUpdates",
    "req" + "AccountSummary",
    "req" + "OpenOrders",
    "req" + "Executions",
)


def test_read_only_boundary_exposes_only_historical_read_methods() -> None:
    boundary = build_read_only_ibkr_boundary()
    public_names = {name for name in dir(boundary) if not name.startswith("_")}

    assert boundary.profile.read_only_mode is True
    assert boundary.access_mode == DataAccessMode.dry_run()
    assert READ_ONLY_IBKR_API_METHODS == frozenset(
        {
            "cancelHistoricalData",
            "reqHeadTimeStamp",
            "reqHistoricalData",
            "reqHistoricalSchedule",
        }
    )
    assert "request_historical_data" in public_names
    assert "request_historical_schedule" in public_names
    assert "request_head_timestamp" in public_names
    assert "cancel_historical_data" in public_names

    for method_name in FORBIDDEN_API_METHODS:
        assert method_name not in public_names
        assert hasattr(boundary, method_name) is False


def test_order_account_and_position_methods_fail_closed_when_reached(
    caplog: pytest.LogCaptureFixture,
) -> None:
    boundary = build_read_only_ibkr_boundary()
    caplog.set_level(logging.ERROR, logger="alpha_system.data.foundation.ibkr")

    for method_name in FORBIDDEN_API_METHODS:
        with pytest.raises(ReadOnlyBoundaryViolation, match="refuses API method"):
            getattr(boundary, method_name)
        with pytest.raises(ReadOnlyBoundaryViolation, match="historical data surface"):
            boundary.call_read_only_api(method_name, env=VALID_EXTERNAL_ENV, ci=False)

    assert "read-only boundary refused API method" in caplog.text
    for method_name in FORBIDDEN_API_METHODS:
        assert method_name in caplog.text


def test_read_only_boundary_rejects_forbidden_method_registration() -> None:
    with pytest.raises(ReadOnlyBoundaryViolation):
        build_read_only_ibkr_boundary(
            read_only_methods={"place" + "Order": lambda: None},
        )


def test_read_only_boundary_rejects_unknown_ibkr_methods() -> None:
    boundary = build_read_only_ibkr_boundary()

    with pytest.raises(ReadOnlyBoundaryViolation, match="registered read-only surface"):
        boundary.call_read_only_api("reqMktData", env=VALID_EXTERNAL_ENV, ci=False)


def test_registered_historical_method_requires_external_enabled_mode() -> None:
    def historical_handler(request_id: int) -> tuple[str, int]:
        return ("historical", request_id)

    boundary = build_read_only_ibkr_boundary(
        read_only_methods={"reqHistoricalData": historical_handler},
    )

    with pytest.raises(ReadOnlyBoundaryViolation, match="forbids API calls"):
        boundary.request_historical_data(7, env=VALID_EXTERNAL_ENV, ci=False)

    external_boundary = build_read_only_ibkr_boundary(
        access_mode=DataAccessMode.smoke(),
        read_only_methods={"reqHistoricalData": historical_handler},
    )

    assert external_boundary.request_historical_data(
        7,
        env=VALID_EXTERNAL_ENV,
        ci=False,
    ) == ("historical", 7)


def test_external_mode_boundary_is_forbidden_in_ci() -> None:
    boundary = build_read_only_ibkr_boundary(
        access_mode=DataAccessMode.smoke(),
        read_only_methods={"reqHistoricalData": lambda: "called"},
    )

    with pytest.raises(DataFoundationValidationError, match="CI"):
        boundary.request_historical_data(env=VALID_EXTERNAL_ENV, ci=True)


def test_boundary_stores_no_generic_api_client_path() -> None:
    boundary = IBKRReadOnlyApiBoundary()

    assert hasattr(boundary, "api") is False
    assert hasattr(boundary, "adapter") is False
    assert hasattr(boundary, "client") is False
    assert boundary.read_only_methods == {}
