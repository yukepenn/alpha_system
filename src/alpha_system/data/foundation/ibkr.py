"""Fail-closed IBKR historical connection profile records.

DATA-P03 defines configuration records and a diagnostic-only connection doctor for the
read-only historical IBKR bootstrap source. This module performs no network access, opens
no sockets, imports no IBKR client library, and reads no credentials at import time.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from ipaddress import ip_address
from types import MappingProxyType

from alpha_system.data.foundation.sources import (
    DataAccessMode,
    DataFoundationValidationError,
)

DEFAULT_IBKR_HOST = "127.0.0.1"
DEFAULT_IBKR_PORT = 4002
DEFAULT_IBKR_CLIENT_ID = 201
DEFAULT_IBKR_READ_ONLY_MODE = True
DEFAULT_IBKR_ENVIRONMENT = "local_wsl2"
DEFAULT_IBKR_CONNECTION_TIMEOUT = 10.0

FORBIDDEN_IBKR_CLIENT_IDS = frozenset({101, 102})
ALLOWED_IBKR_CLIENT_ID_RANGE = (201, 209)
DEFAULT_IBKR_WORKER_CLIENT_IDS: Mapping[str, int] = MappingProxyType(
    {"ES": 201, "NQ": 202, "RTY": 203}
)
IBKR_CLIENT_ID_COLLISION_POLICY = "fail_closed"
ALLOWED_IBKR_ENVIRONMENTS = frozenset({"local_wsl2", "local_linux", "ci_scaffold"})
READ_ONLY_IBKR_API_METHODS: frozenset[str] = frozenset(
    {
        "cancelHistoricalData",
        "reqHeadTimeStamp",
        "reqHistoricalData",
        "reqHistoricalSchedule",
    }
)

_LOGGER = logging.getLogger(__name__)

_FORBIDDEN_API_METHOD_TERMS: frozenset[str] = frozenset(
    {
        "account",
        "accounts",
        "broker",
        "execution",
        "executions",
        "fill",
        "fills",
        "globalcancel",
        "live",
        "openorder",
        "openorders",
        "order",
        "orders",
        "portfolio",
        "position",
        "positions",
        "paper",
        "trade",
        "trades",
        "trading",
    }
)

_FORBIDDEN_API_METHOD_SUBSTRINGS: tuple[str, ...] = (
    "account",
    "broker",
    "execution",
    "globalcancel",
    "openorder",
    "order",
    "portfolio",
    "position",
    "paper",
    "trade",
    "trading",
)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        msg = f"{field_name} must be a non-empty string"
        raise DataFoundationValidationError(msg)
    normalized = value.strip()
    if not normalized:
        msg = f"{field_name} must be a non-empty string"
        raise DataFoundationValidationError(msg)
    return normalized


def _require_aware_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        msg = f"{field_name} must be a timezone-aware datetime"
        raise DataFoundationValidationError(msg)
    if value.tzinfo is None or value.utcoffset() is None:
        msg = f"{field_name} must be timezone-aware"
        raise DataFoundationValidationError(msg)
    return value


def _require_client_id(value: object, field_name: str = "client_id") -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"{field_name} must be an integer clientId"
        raise DataFoundationValidationError(msg)
    return value


def _normalize_client_id_set(value: object, field_name: str) -> frozenset[int]:
    if isinstance(value, str) or not isinstance(value, Iterable):
        msg = f"{field_name} must be a non-empty iterable of integer clientIds"
        raise DataFoundationValidationError(msg)
    normalized = frozenset(_require_client_id(item, field_name) for item in value)
    if not normalized:
        msg = f"{field_name} must not be empty"
        raise DataFoundationValidationError(msg)
    return normalized


def _normalize_allowed_range(value: object) -> tuple[int, int]:
    if isinstance(value, range):
        if value.step != 1 or len(value) == 0:
            msg = "allowed_range must be a non-empty contiguous clientId range"
            raise DataFoundationValidationError(msg)
        start = value.start
        end = value.stop - 1
    elif isinstance(value, str) or not isinstance(value, Iterable):
        msg = "allowed_range must be a two-item inclusive clientId range"
        raise DataFoundationValidationError(msg)
    else:
        items = tuple(value)
        if len(items) != 2:
            msg = "allowed_range must contain exactly start and end clientIds"
            raise DataFoundationValidationError(msg)
        start = _require_client_id(items[0], "allowed_range.start")
        end = _require_client_id(items[1], "allowed_range.end")

    if isinstance(start, bool) or isinstance(end, bool) or not isinstance(start, int):
        msg = "allowed_range must contain integer clientIds"
        raise DataFoundationValidationError(msg)
    if not isinstance(end, int):
        msg = "allowed_range must contain integer clientIds"
        raise DataFoundationValidationError(msg)
    if start > end:
        msg = "allowed_range start must be less than or equal to end"
        raise DataFoundationValidationError(msg)
    return (start, end)


def _normalize_worker_client_ids(value: object) -> Mapping[str, int]:
    if not isinstance(value, Mapping):
        msg = "worker_client_ids must be a mapping of worker symbol to clientId"
        raise DataFoundationValidationError(msg)
    if not value:
        msg = "worker_client_ids must not be empty"
        raise DataFoundationValidationError(msg)

    normalized: dict[str, int] = {}
    for worker, client_id in value.items():
        worker_name = _require_text(worker, "worker_client_ids.worker").upper()
        if not worker_name.replace("_", "").isalnum():
            msg = f"worker_client_ids worker {worker!r} must be an alphanumeric symbol"
            raise DataFoundationValidationError(msg)
        if worker_name in normalized:
            msg = f"worker_client_ids contains duplicate worker {worker_name!r}"
            raise DataFoundationValidationError(msg)
        normalized[worker_name] = _require_client_id(
            client_id,
            f"worker_client_ids[{worker_name}]",
        )
    return MappingProxyType(normalized)


def _normalize_collision_policy(value: object) -> str:
    token = _require_text(value, "collision_policy").lower().replace("-", "_")
    if token != IBKR_CLIENT_ID_COLLISION_POLICY:
        msg = "collision_policy must be fail_closed"
        raise DataFoundationValidationError(msg)
    return token


def _validate_client_id_against(
    client_id: int,
    *,
    forbidden_client_ids: frozenset[int],
    allowed_range: tuple[int, int],
) -> int:
    if client_id in forbidden_client_ids:
        msg = (
            f"client_id {client_id} is forbidden and hard-blocked; "
            "101 and 102 are reserved outside the data-client namespace"
        )
        raise DataFoundationValidationError(msg)

    allowed_start, allowed_end = allowed_range
    if not allowed_start <= client_id <= allowed_end:
        msg = (
            f"client_id {client_id} must be in the data-client namespace "
            f"{allowed_start}-{allowed_end}"
        )
        raise DataFoundationValidationError(msg)
    return client_id


def _validate_worker_assignment_collisions(
    worker_client_ids: Mapping[str, int],
    *,
    forbidden_client_ids: frozenset[int],
    allowed_range: tuple[int, int],
) -> None:
    assigned: dict[int, str] = {}
    for worker, client_id in worker_client_ids.items():
        _validate_client_id_against(
            client_id,
            forbidden_client_ids=forbidden_client_ids,
            allowed_range=allowed_range,
        )
        existing_worker = assigned.get(client_id)
        if existing_worker is not None:
            msg = (
                f"worker clientId collision: {existing_worker} and {worker} "
                f"both request client_id {client_id}; collision_policy fail_closed"
            )
            raise DataFoundationValidationError(msg)
        assigned[client_id] = worker


@dataclass(frozen=True, slots=True)
class IBKRClientIdPolicy:
    """Validated data-client ID namespace policy for historical IBKR pulls."""

    forbidden_client_ids: frozenset[int] = FORBIDDEN_IBKR_CLIENT_IDS
    allowed_range: tuple[int, int] = ALLOWED_IBKR_CLIENT_ID_RANGE
    default_client_id: int = DEFAULT_IBKR_CLIENT_ID
    worker_client_ids: Mapping[str, int] = field(
        default_factory=lambda: MappingProxyType(dict(DEFAULT_IBKR_WORKER_CLIENT_IDS))
    )
    collision_policy: str = IBKR_CLIENT_ID_COLLISION_POLICY

    def __post_init__(self) -> None:
        forbidden_client_ids = _normalize_client_id_set(
            self.forbidden_client_ids,
            "forbidden_client_ids",
        )
        allowed_range = _normalize_allowed_range(self.allowed_range)
        default_client_id = _require_client_id(self.default_client_id, "default_client_id")
        worker_client_ids = _normalize_worker_client_ids(self.worker_client_ids)
        collision_policy = _normalize_collision_policy(self.collision_policy)

        _validate_client_id_against(
            default_client_id,
            forbidden_client_ids=forbidden_client_ids,
            allowed_range=allowed_range,
        )
        _validate_worker_assignment_collisions(
            worker_client_ids,
            forbidden_client_ids=forbidden_client_ids,
            allowed_range=allowed_range,
        )

        if forbidden_client_ids != FORBIDDEN_IBKR_CLIENT_IDS:
            msg = "forbidden_client_ids must be exactly {101, 102}"
            raise DataFoundationValidationError(msg)
        if allowed_range != ALLOWED_IBKR_CLIENT_ID_RANGE:
            msg = "allowed_range must be exactly the inclusive namespace 201-209"
            raise DataFoundationValidationError(msg)
        if default_client_id != DEFAULT_IBKR_CLIENT_ID:
            msg = "default_client_id must be 201"
            raise DataFoundationValidationError(msg)
        if dict(worker_client_ids) != dict(DEFAULT_IBKR_WORKER_CLIENT_IDS):
            msg = "worker_client_ids must be exactly ES=201, NQ=202, RTY=203"
            raise DataFoundationValidationError(msg)

        object.__setattr__(self, "forbidden_client_ids", forbidden_client_ids)
        object.__setattr__(self, "allowed_range", allowed_range)
        object.__setattr__(self, "default_client_id", default_client_id)
        object.__setattr__(self, "worker_client_ids", worker_client_ids)
        object.__setattr__(self, "collision_policy", collision_policy)

    @classmethod
    def default(cls) -> "IBKRClientIdPolicy":
        """Build the campaign's canonical fail-closed clientId policy."""

        return cls()

    def validate_client_id(self, client_id: object) -> int:
        """Return a validated data-client ID or raise fail-closed."""

        normalized = _require_client_id(client_id)
        return _validate_client_id_against(
            normalized,
            forbidden_client_ids=self.forbidden_client_ids,
            allowed_range=self.allowed_range,
        )

    def client_id_for_worker(self, worker: object) -> int:
        """Return the assigned data-client ID for a configured worker symbol."""

        worker_name = _require_text(worker, "worker").upper()
        client_id = self.worker_client_ids.get(worker_name)
        if client_id is None:
            msg = f"worker {worker_name!r} has no configured data-client ID"
            raise DataFoundationValidationError(msg)
        return self.validate_client_id(client_id)

    def validate_worker_assignments(
        self,
        worker_client_ids: Mapping[str, int] | None = None,
    ) -> Mapping[str, int]:
        """Validate worker assignment uniqueness under the fail-closed policy."""

        assignments = self.worker_client_ids if worker_client_ids is None else worker_client_ids
        normalized = _normalize_worker_client_ids(assignments)
        _validate_worker_assignment_collisions(
            normalized,
            forbidden_client_ids=self.forbidden_client_ids,
            allowed_range=self.allowed_range,
        )
        return normalized

    def check_collision(
        self, requested_client_id: object, active_client_ids: Iterable[object]
    ) -> int:
        """Validate that a requested clientId is not already active."""

        requested = self.validate_client_id(requested_client_id)
        if isinstance(active_client_ids, str) or not isinstance(active_client_ids, Iterable):
            msg = "active_client_ids must be an iterable of data-client IDs"
            raise DataFoundationValidationError(msg)

        active = {self.validate_client_id(client_id) for client_id in active_client_ids}
        if requested in active:
            msg = f"client_id {requested} is already in use; collision_policy fail_closed"
            raise DataFoundationValidationError(msg)
        return requested


def _normalize_host(value: object) -> str:
    host = _require_text(value, "host")
    if any(character.isspace() for character in host):
        msg = "host must not contain whitespace"
        raise DataFoundationValidationError(msg)
    if "://" in host or "/" in host or "\\" in host:
        msg = "host must be a host name or IP address, not a URL or path"
        raise DataFoundationValidationError(msg)
    if len(host) > 253:
        msg = "host must be no longer than 253 characters"
        raise DataFoundationValidationError(msg)

    try:
        address = ip_address(host)
    except ValueError:
        labels = host.split(".")
        if any(not label for label in labels):
            msg = "host must not contain empty DNS labels"
            raise DataFoundationValidationError(msg)
        for label in labels:
            if len(label) > 63:
                msg = "host DNS labels must be no longer than 63 characters"
                raise DataFoundationValidationError(msg)
            if label.startswith("-") or label.endswith("-"):
                msg = "host DNS labels must not start or end with '-'"
                raise DataFoundationValidationError(msg)
            if not label.replace("-", "").isalnum():
                msg = "host DNS labels must contain only letters, digits, and '-'"
                raise DataFoundationValidationError(msg)
        return host.lower()

    if address.is_unspecified or address.is_multicast:
        msg = f"host {host!r} is not a valid connection target"
        raise DataFoundationValidationError(msg)
    return str(address)


def _normalize_port(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        msg = "port must be an integer TCP port"
        raise DataFoundationValidationError(msg)
    if not 1 <= value <= 65535:
        msg = "port must be between 1 and 65535"
        raise DataFoundationValidationError(msg)
    return value


def _normalize_read_only_mode(value: object) -> bool:
    if not isinstance(value, bool):
        msg = "read_only_mode must be a boolean"
        raise DataFoundationValidationError(msg)
    if value is not True:
        msg = "read_only_mode must be true for the IBKR historical data profile"
        raise DataFoundationValidationError(msg)
    return value


def _normalize_environment(value: object) -> str:
    environment = _require_text(value, "environment").lower().replace("-", "_")
    if environment not in ALLOWED_IBKR_ENVIRONMENTS:
        allowed = ", ".join(sorted(ALLOWED_IBKR_ENVIRONMENTS))
        msg = f"environment must be one of: {allowed}"
        raise DataFoundationValidationError(msg)
    return environment


def _normalize_connection_timeout(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        msg = "connection_timeout must be a positive number of seconds"
        raise DataFoundationValidationError(msg)
    timeout = float(value)
    if timeout <= 0:
        msg = "connection_timeout must be positive"
        raise DataFoundationValidationError(msg)
    return timeout


def _default_doctor_status() -> Mapping[str, object]:
    return MappingProxyType(
        {
            "status": "not_run",
            "reachability": "not_probed_scaffold",
            "probe_performed": False,
            "external_call_performed": False,
            "diagnostics": ("Connection doctor has not been run.",),
        }
    )


def _normalize_doctor_status(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        msg = "doctor_status must be a diagnostic mapping"
        raise DataFoundationValidationError(msg)

    status = _require_text(value.get("status"), "doctor_status.status")
    reachability = _require_text(value.get("reachability"), "doctor_status.reachability")
    probe_performed = value.get("probe_performed")
    external_call_performed = value.get("external_call_performed")
    if probe_performed is not False:
        msg = "doctor_status.probe_performed must remain false in DATA-P03"
        raise DataFoundationValidationError(msg)
    if external_call_performed is not False:
        msg = "doctor_status.external_call_performed must remain false in DATA-P03"
        raise DataFoundationValidationError(msg)

    diagnostics = value.get("diagnostics")
    if isinstance(diagnostics, str) or not isinstance(diagnostics, Iterable):
        msg = "doctor_status.diagnostics must be a non-empty iterable of strings"
        raise DataFoundationValidationError(msg)
    normalized_diagnostics = tuple(
        _require_text(diagnostic, "doctor_status.diagnostics") for diagnostic in diagnostics
    )
    if not normalized_diagnostics:
        msg = "doctor_status.diagnostics must not be empty"
        raise DataFoundationValidationError(msg)

    normalized = dict(value)
    normalized["status"] = status
    normalized["reachability"] = reachability
    normalized["probe_performed"] = False
    normalized["external_call_performed"] = False
    normalized["diagnostics"] = normalized_diagnostics
    return MappingProxyType(normalized)


def _parse_env_int(value: object, field_name: str) -> int:
    if not isinstance(value, str):
        msg = f"{field_name} must be supplied as a string environment value"
        raise DataFoundationValidationError(msg)
    stripped = value.strip()
    if not stripped:
        msg = f"{field_name} must not be empty when set"
        raise DataFoundationValidationError(msg)
    try:
        return int(stripped)
    except ValueError as exc:
        msg = f"{field_name} must be an integer"
        raise DataFoundationValidationError(msg) from exc


def _parse_env_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, str):
        msg = f"{field_name} must be supplied as a string environment value"
        raise DataFoundationValidationError(msg)
    token = value.strip().lower()
    if token in {"1", "true", "yes", "on"}:
        return True
    if token in {"0", "false", "no", "off"}:
        return False
    msg = f"{field_name} must be a boolean string"
    raise DataFoundationValidationError(msg)


@dataclass(frozen=True, slots=True)
class IBKRConnectionProfile:
    """Validated read-only historical IBKR connection settings."""

    host: str = DEFAULT_IBKR_HOST
    port: int = DEFAULT_IBKR_PORT
    client_id: int = DEFAULT_IBKR_CLIENT_ID
    read_only_mode: bool = DEFAULT_IBKR_READ_ONLY_MODE
    environment: str = DEFAULT_IBKR_ENVIRONMENT
    connection_timeout: float = DEFAULT_IBKR_CONNECTION_TIMEOUT
    doctor_status: Mapping[str, object] = field(default_factory=_default_doctor_status)
    validated_at: datetime = field(default_factory=_now_utc)

    def __post_init__(self) -> None:
        host = _normalize_host(self.host)
        port = _normalize_port(self.port)
        client_id = IBKRClientIdPolicy.default().validate_client_id(self.client_id)
        read_only_mode = _normalize_read_only_mode(self.read_only_mode)
        environment = _normalize_environment(self.environment)
        connection_timeout = _normalize_connection_timeout(self.connection_timeout)
        doctor_status = _normalize_doctor_status(self.doctor_status)
        validated_at = _require_aware_datetime(self.validated_at, "validated_at")

        object.__setattr__(self, "host", host)
        object.__setattr__(self, "port", port)
        object.__setattr__(self, "client_id", client_id)
        object.__setattr__(self, "read_only_mode", read_only_mode)
        object.__setattr__(self, "environment", environment)
        object.__setattr__(self, "connection_timeout", connection_timeout)
        object.__setattr__(self, "doctor_status", doctor_status)
        object.__setattr__(self, "validated_at", validated_at)

    @classmethod
    def ibkr_historical(cls, *, validated_at: datetime | None = None) -> "IBKRConnectionProfile":
        """Build the campaign's default read-only historical connection profile."""

        return cls(validated_at=validated_at or _now_utc())

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
        *,
        environment: str = DEFAULT_IBKR_ENVIRONMENT,
        connection_timeout: float = DEFAULT_IBKR_CONNECTION_TIMEOUT,
        validated_at: datetime | None = None,
    ) -> "IBKRConnectionProfile":
        """Read ALPHA_IBKR_* settings and build a fail-closed connection profile."""

        source = os.environ if env is None else env
        host = source.get("ALPHA_IBKR_HOST", DEFAULT_IBKR_HOST)
        port = (
            DEFAULT_IBKR_PORT
            if "ALPHA_IBKR_PORT" not in source
            else _parse_env_int(source["ALPHA_IBKR_PORT"], "ALPHA_IBKR_PORT")
        )
        client_id = (
            DEFAULT_IBKR_CLIENT_ID
            if "ALPHA_IBKR_CLIENT_ID" not in source
            else _parse_env_int(source["ALPHA_IBKR_CLIENT_ID"], "ALPHA_IBKR_CLIENT_ID")
        )
        read_only_mode = (
            DEFAULT_IBKR_READ_ONLY_MODE
            if "ALPHA_IBKR_READ_ONLY_MODE" not in source
            else _parse_env_bool(
                source["ALPHA_IBKR_READ_ONLY_MODE"],
                "ALPHA_IBKR_READ_ONLY_MODE",
            )
        )
        return cls(
            host=host,
            port=port,
            client_id=client_id,
            read_only_mode=read_only_mode,
            environment=environment,
            connection_timeout=connection_timeout,
            validated_at=validated_at or _now_utc(),
        )


def _doctor_status_for(profile: IBKRConnectionProfile) -> Mapping[str, object]:
    return MappingProxyType(
        {
            "status": "configuration_validated",
            "reachability": "not_probed_scaffold",
            "host": profile.host,
            "port": profile.port,
            "client_id": profile.client_id,
            "retry_target": None,
            "probe_performed": False,
            "external_call_performed": False,
            "diagnostics": (
                "DATA-P03 validates configuration only; no socket or IBKR API call was opened.",
                "No alternate host fallback or silent retry target was attempted.",
            ),
        }
    )


def run_connection_doctor(
    profile: IBKRConnectionProfile | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> IBKRConnectionProfile:
    """Validate the profile and record diagnostic reachability posture without probing."""

    if profile is not None and env is not None:
        msg = "pass either profile or env to run_connection_doctor, not both"
        raise DataFoundationValidationError(msg)
    candidate = IBKRConnectionProfile.from_env(env) if profile is None else profile
    if not isinstance(candidate, IBKRConnectionProfile):
        msg = "run_connection_doctor requires an IBKRConnectionProfile"
        raise DataFoundationValidationError(msg)

    IBKRClientIdPolicy.default().validate_client_id(candidate.client_id)
    return replace(
        candidate,
        doctor_status=_doctor_status_for(candidate),
        validated_at=_now_utc(),
    )


class ReadOnlyBoundaryViolation(DataFoundationValidationError, AttributeError):
    """Raised when the IBKR data boundary refuses a non-historical API method."""


def _api_method_token(value: object) -> str:
    raw = _require_text(value, "method_name")
    normalized: list[str] = []
    previous = ""
    for character in raw:
        if character in {"-", ".", " "}:
            normalized.append("_")
        elif character == "_":
            normalized.append(character)
        elif character.isupper():
            if previous and (previous.islower() or previous.isdigit()):
                normalized.append("_")
            normalized.append(character.lower())
        else:
            normalized.append(character.lower())
        previous = character

    token = "".join(normalized).strip("_")
    while "__" in token:
        token = token.replace("__", "_")
    if not token.replace("_", "").isalnum():
        msg = f"method_name contains invalid API method token {raw!r}"
        raise DataFoundationValidationError(msg)
    return token


def _api_method_is_forbidden(method_name: object) -> bool:
    token = _api_method_token(method_name)
    parts = frozenset(token.split("_"))
    compact = token.replace("_", "")
    return bool(
        parts & _FORBIDDEN_API_METHOD_TERMS
        or any(term in compact for term in _FORBIDDEN_API_METHOD_SUBSTRINGS)
    )


def _refuse_api_method(method_name: object, reason: str) -> None:
    method = _require_text(method_name, "method_name")
    _LOGGER.error(
        "IBKR data read-only boundary refused API method %s",
        method,
        extra={"ibkr_api_method": method, "reason": reason},
    )
    msg = (
        f"IBKR data read-only boundary refuses API method {method!r}: {reason}. "
        "Only registered historical read-only methods are allowed."
    )
    raise ReadOnlyBoundaryViolation(msg)


def _validate_read_only_api_method(method_name: object) -> str:
    method = _require_text(method_name, "method_name")
    if _api_method_is_forbidden(method):
        _refuse_api_method(method, "method is outside the historical data surface")
    if method not in READ_ONLY_IBKR_API_METHODS:
        _refuse_api_method(method, "method is not in the registered read-only surface")
    return method


def _normalize_read_only_methods(
    value: object,
) -> Mapping[str, Callable[..., object]]:
    if not isinstance(value, Mapping):
        msg = "read_only_methods must be a mapping of read-only API method names to callables"
        raise DataFoundationValidationError(msg)

    normalized: dict[str, Callable[..., object]] = {}
    for method_name, handler in value.items():
        method = _validate_read_only_api_method(method_name)
        if not callable(handler):
            msg = f"read_only_methods[{method!r}] must be callable"
            raise DataFoundationValidationError(msg)
        normalized[method] = handler
    return MappingProxyType(normalized)


@dataclass(frozen=True, slots=True)
class IBKRReadOnlyApiBoundary:
    """Single historical-data seam for IBKR access from the data module."""

    profile: IBKRConnectionProfile = field(default_factory=IBKRConnectionProfile.ibkr_historical)
    access_mode: DataAccessMode = field(default_factory=DataAccessMode.dry_run)
    read_only_methods: Mapping[str, Callable[..., object]] = field(
        default_factory=lambda: MappingProxyType({}),
        repr=False,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.profile, IBKRConnectionProfile):
            msg = "IBKRReadOnlyApiBoundary requires an IBKRConnectionProfile"
            raise DataFoundationValidationError(msg)
        if self.profile.read_only_mode is not True:
            msg = "IBKRReadOnlyApiBoundary requires read_only_mode=true"
            raise DataFoundationValidationError(msg)
        if not isinstance(self.access_mode, DataAccessMode):
            msg = "IBKRReadOnlyApiBoundary requires a DataAccessMode"
            raise DataFoundationValidationError(msg)

        methods = _normalize_read_only_methods(self.read_only_methods)
        object.__setattr__(self, "read_only_methods", methods)

    def __getattr__(self, name: str) -> object:
        if name.startswith("__"):
            raise AttributeError(name)
        self.refuse_api_method(name)

    def assert_read_only_method(self, method_name: object) -> str:
        """Return a validated historical read-only API method or fail closed."""

        return _validate_read_only_api_method(method_name)

    def refuse_api_method(self, method_name: object) -> None:
        """Log and refuse any method outside the historical read-only surface."""

        reason = (
            "method is not exposed by the data module; broker, account, "
            "position, and trading surfaces are refused"
        )
        _refuse_api_method(method_name, reason)

    def call_read_only_api(
        self,
        method_name: object,
        *args: object,
        env: Mapping[str, str] | None = None,
        ci: bool | None = None,
        **kwargs: object,
    ) -> object:
        """Call a registered historical read-only method after mode-gate validation."""

        method = self.assert_read_only_method(method_name)
        self.access_mode.validate_runtime_env(env, ci=ci)
        if not self.access_mode.allows_external_api:
            _refuse_api_method(
                method, f"DataAccessMode {self.access_mode.mode!r} forbids API calls"
            )

        handler = self.read_only_methods.get(method)
        if handler is None:
            msg = f"no read-only API handler registered for {method!r}"
            raise DataFoundationValidationError(msg)
        return handler(*args, **kwargs)

    def request_historical_data(
        self,
        *args: object,
        env: Mapping[str, str] | None = None,
        ci: bool | None = None,
        **kwargs: object,
    ) -> object:
        """Call the registered historical-data request method."""

        return self.call_read_only_api("reqHistoricalData", *args, env=env, ci=ci, **kwargs)

    def cancel_historical_data(
        self,
        *args: object,
        env: Mapping[str, str] | None = None,
        ci: bool | None = None,
        **kwargs: object,
    ) -> object:
        """Call the registered historical-data cancellation method."""

        return self.call_read_only_api("cancelHistoricalData", *args, env=env, ci=ci, **kwargs)

    def request_head_timestamp(
        self,
        *args: object,
        env: Mapping[str, str] | None = None,
        ci: bool | None = None,
        **kwargs: object,
    ) -> object:
        """Call the registered historical head-timestamp request method."""

        return self.call_read_only_api("reqHeadTimeStamp", *args, env=env, ci=ci, **kwargs)

    def request_historical_schedule(
        self,
        *args: object,
        env: Mapping[str, str] | None = None,
        ci: bool | None = None,
        **kwargs: object,
    ) -> object:
        """Call the registered historical schedule request method."""

        return self.call_read_only_api(
            "reqHistoricalSchedule",
            *args,
            env=env,
            ci=ci,
            **kwargs,
        )


def build_read_only_ibkr_boundary(
    *,
    profile: IBKRConnectionProfile | None = None,
    access_mode: DataAccessMode | None = None,
    read_only_methods: Mapping[str, Callable[..., object]] | None = None,
) -> IBKRReadOnlyApiBoundary:
    """Build the default fail-closed IBKR historical-data boundary."""

    return IBKRReadOnlyApiBoundary(
        profile=profile or IBKRConnectionProfile.ibkr_historical(),
        access_mode=access_mode or DataAccessMode.dry_run(),
        read_only_methods=read_only_methods or MappingProxyType({}),
    )


__all__ = [
    "ALLOWED_IBKR_CLIENT_ID_RANGE",
    "DEFAULT_IBKR_CLIENT_ID",
    "DEFAULT_IBKR_CONNECTION_TIMEOUT",
    "DEFAULT_IBKR_ENVIRONMENT",
    "DEFAULT_IBKR_HOST",
    "DEFAULT_IBKR_PORT",
    "DEFAULT_IBKR_READ_ONLY_MODE",
    "DEFAULT_IBKR_WORKER_CLIENT_IDS",
    "FORBIDDEN_IBKR_CLIENT_IDS",
    "IBKR_CLIENT_ID_COLLISION_POLICY",
    "IBKRClientIdPolicy",
    "IBKRConnectionProfile",
    "IBKRReadOnlyApiBoundary",
    "READ_ONLY_IBKR_API_METHODS",
    "ReadOnlyBoundaryViolation",
    "build_read_only_ibkr_boundary",
    "run_connection_doctor",
]
