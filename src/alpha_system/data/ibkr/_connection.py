"""Shared read-only IBKR connector gates."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from alpha_system.data.foundation.ibkr import IBKRClientIdPolicy, IBKRConnectionProfile
from alpha_system.data.foundation.sources import DataAccessMode, DataFoundationValidationError


def connection_doctor_blocked_message(
    profile: IBKRConnectionProfile,
    failure_reason: str | None,
    *,
    connector_name: str = "smoke",
) -> str:
    """Return the operator-facing connection-doctor block message."""

    reason = failure_reason or "unreachable"
    return (
        f"IBKR read-only {connector_name} connector blocked: connection doctor "
        "could not reach "
        f"{profile.host}:{profile.port} ({reason}). Set ALPHA_IBKR_HOST to a "
        "Windows-reachable address or enable WSL2 mirrored networking; host/port are "
        "NOT changed automatically."
    )


def require_env_present(
    env: Mapping[str, str],
    name: str,
    *,
    purpose: str = "for authorized smoke-pull local outputs",
) -> str:
    """Return a required environment value or fail closed."""

    value = env.get(name)
    if value is None or not value.strip():
        msg = f"{name} is required {purpose}"
        raise DataFoundationValidationError(msg)
    return value


def gate_read_only_ibkr_access(
    env: Mapping[str, str],
    *,
    reachability_probe: Callable[[IBKRConnectionProfile], object],
) -> tuple[IBKRConnectionProfile, DataAccessMode, object]:
    """Validate read-only IBKR pull authorization before probing host/port."""

    profile = IBKRConnectionProfile.from_env(env)
    IBKRClientIdPolicy.default().validate_client_id(profile.client_id)
    access_mode = DataAccessMode.authorized_pull()
    access_mode.validate_runtime_env(env, ci=None)
    doctor = reachability_probe(profile)
    return profile, access_mode, doctor
