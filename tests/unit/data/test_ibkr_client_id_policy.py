from __future__ import annotations

import pytest

from alpha_system.data.foundation.ibkr import (
    ALLOWED_IBKR_CLIENT_ID_RANGE,
    DEFAULT_IBKR_CLIENT_ID,
    DEFAULT_IBKR_WORKER_CLIENT_IDS,
    FORBIDDEN_IBKR_CLIENT_IDS,
    IBKR_CLIENT_ID_COLLISION_POLICY,
    IBKRClientIdPolicy,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError


def test_client_id_policy_defaults_match_campaign_namespace() -> None:
    policy = IBKRClientIdPolicy.default()

    assert policy.forbidden_client_ids == FORBIDDEN_IBKR_CLIENT_IDS
    assert policy.forbidden_client_ids == frozenset({101, 102})
    assert policy.allowed_range == ALLOWED_IBKR_CLIENT_ID_RANGE
    assert policy.allowed_range == (201, 209)
    assert policy.default_client_id == DEFAULT_IBKR_CLIENT_ID
    assert policy.default_client_id == 201
    assert dict(policy.worker_client_ids) == dict(DEFAULT_IBKR_WORKER_CLIENT_IDS)
    assert policy.collision_policy == IBKR_CLIENT_ID_COLLISION_POLICY
    assert policy.collision_policy == "fail_closed"


@pytest.mark.parametrize("client_id", [101, 102])
def test_client_id_101_and_102_are_hard_blocked(client_id: int) -> None:
    policy = IBKRClientIdPolicy.default()

    with pytest.raises(DataFoundationValidationError, match="hard-blocked"):
        policy.validate_client_id(client_id)

    with pytest.raises(DataFoundationValidationError, match="hard-blocked"):
        IBKRClientIdPolicy(default_client_id=client_id)


@pytest.mark.parametrize("client_id", [0, 100, 103, 200, 210, 999])
def test_client_ids_outside_201_209_fail_closed(client_id: int) -> None:
    policy = IBKRClientIdPolicy.default()

    with pytest.raises(DataFoundationValidationError, match="201-209"):
        policy.validate_client_id(client_id)


@pytest.mark.parametrize("client_id", list(range(201, 210)))
def test_client_ids_inside_201_209_validate(client_id: int) -> None:
    assert IBKRClientIdPolicy.default().validate_client_id(client_id) == client_id


def test_worker_client_id_lookup_uses_es_nq_rty_assignments() -> None:
    policy = IBKRClientIdPolicy.default()

    assert policy.client_id_for_worker("ES") == 201
    assert policy.client_id_for_worker("nq") == 202
    assert policy.client_id_for_worker("RTY") == 203


def test_unknown_worker_fails_closed() -> None:
    policy = IBKRClientIdPolicy.default()

    with pytest.raises(DataFoundationValidationError, match="no configured"):
        policy.client_id_for_worker("YM")


def test_worker_assignment_collision_fails_closed() -> None:
    policy = IBKRClientIdPolicy.default()

    with pytest.raises(DataFoundationValidationError, match="collision"):
        policy.validate_worker_assignments({"ES": 201, "NQ": 201, "RTY": 203})


def test_requested_client_id_collision_fails_closed() -> None:
    policy = IBKRClientIdPolicy.default()

    with pytest.raises(DataFoundationValidationError, match="already in use"):
        policy.check_collision(202, active_client_ids=[201, 202, 203])

    assert policy.check_collision(204, active_client_ids=[201, 202, 203]) == 204


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    [
        ("forbidden_client_ids", {102}),
        ("allowed_range", (201, 210)),
        ("default_client_id", 202),
        ("worker_client_ids", {"ES": 201, "NQ": 202, "YM": 204}),
        ("collision_policy", "warn"),
    ],
)
def test_policy_rejects_weakened_or_noncanonical_fields(
    field_name: str,
    bad_value: object,
) -> None:
    with pytest.raises(DataFoundationValidationError):
        IBKRClientIdPolicy(**{field_name: bad_value})
