"""Data source and local data-root policy records.

DATA-P02 owns fail-closed validation for provider usage boundaries and the local-only
data-root policy. This module performs no provider calls, network access, or filesystem
writes.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType


class DataFoundationValidationError(ValueError):
    """Raised when a data-foundation policy record fails validation."""


READ_ONLY_HISTORICAL_MODES: frozenset[str] = frozenset(
    {
        "historical_data",
        "read_only_historical",
    }
)

IBKR_FORBIDDEN_MODES: frozenset[str] = frozenset(
    {
        "account",
        "account_access",
        "broker",
        "broker_readiness",
        "data_completeness_claim",
        "execution",
        "execution_permission",
        "live",
        "live_trading",
        "order_routing",
        "orders",
        "paper",
        "paper_trading",
        "positions",
        "real_time",
        "real_time_market_data",
    }
)

DATABENTO_FORBIDDEN_MODES: frozenset[str] = frozenset(
    {
        "account",
        "account_access",
        "broker",
        "broker_readiness",
        "data_completeness_claim",
        "execution",
        "execution_permission",
        "live",
        "live_trading",
        "order_routing",
        "orders",
        "paper",
        "paper_trading",
        "positions",
        "real_time",
        "real_time_market_data",
    }
)

PROHIBITED_ALLOWED_MODE_PARTS: frozenset[str] = frozenset(
    {
        "account",
        "broker",
        "complete",
        "completeness",
        "execution",
        "guaranteed",
        "live",
        "order",
        "orders",
        "paper",
        "position",
        "positions",
        "realtime",
        "streaming",
    }
)

PROHIBITED_ALLOWED_MODE_PREFIXES: tuple[str, ...] = (
    "real_time",
    "order_",
    "account_",
    "broker_",
    "execution_",
    "paper_",
    "live_",
)

DEFAULT_ALPHA_DATA_ROOT = Path("~/alpha_data/alpha_system")


def resolve_alpha_data_root(
    explicit: str | os.PathLike[str] | None = None,
    env: Mapping[str, str] | None = None,
) -> Path:
    """Resolve the local ALPHA_DATA_ROOT path without touching the filesystem.

    This is the single source of truth for the data-root resolution order so the
    core registry path used by ``alpha idea run`` / ``alpha idea mine`` matches the
    tool defaults instead of fail-closing on an unset env var. Resolution order:

    1. an explicit override (caller-supplied path),
    2. the ``ALPHA_DATA_ROOT`` environment variable,
    3. the known-good local default :data:`DEFAULT_ALPHA_DATA_ROOT`
       (``~/alpha_data/alpha_system``).

    It performs NO I/O: it neither checks existence nor creates anything. Callers
    that need an environment precondition (a root that actually exists on disk)
    must check ``Path.is_dir()`` on the result themselves -- see
    ``alpha_system.research_lane.environment_preflight``.
    """

    source = os.environ if env is None else env
    raw: str | os.PathLike[str]
    if explicit is not None:
        raw = explicit
    else:
        env_value = source.get("ALPHA_DATA_ROOT")
        raw = env_value if env_value else DEFAULT_ALPHA_DATA_ROOT
    return Path(raw).expanduser()

DEFAULT_FORBIDDEN_REPO_PATHS: tuple[str, ...] = (
    "data/raw",
    "data/canonical",
    "data/factors",
    "data/labels",
    "data/cache",
    "metadata",
    "artifacts",
)

DEFAULT_ALLOWED_SUBDIRS: tuple[str, ...] = (
    "raw",
    "canonical",
    "manifests",
    "metadata",
    "quality",
    "coverage",
)

DEFAULT_MAX_FILE_POLICY: Mapping[str, object] = MappingProxyType(
    {
        "max_bytes_per_file": 1_073_741_824,
        "oversize_action": "fail_closed",
    }
)

_EXTERNAL_DATA_ACCESS_REQUIRED_ENV: tuple[str, ...] = (
    "ALPHA_DATA_PULL_AUTHORIZED",
    "ALPHA_ALLOW_EXTERNAL_IBKR",
    "ALPHA_IBKR_READ_ONLY_MODE",
)

_RAW_WRITE_REQUIRED_ENV = "ALPHA_ALLOW_RAW_LOCAL_WRITE"

DATABENTO_DATA_PULL_AUTHORIZED_ENV = "ALPHA_DATA_PULL_AUTHORIZED"
DATABENTO_EXTERNAL_ACCESS_ENV = "ALPHA_ALLOW_EXTERNAL_DATABENTO"
DATABENTO_EXTERNAL_ACCESS_REQUIRED_ENV: tuple[str, ...] = (
    DATABENTO_DATA_PULL_AUTHORIZED_ENV,
    DATABENTO_EXTERNAL_ACCESS_ENV,
)

_DATA_ACCESS_MODE_CONTRACT: Mapping[str, Mapping[str, object]] = MappingProxyType(
    {
        "dry_run": MappingProxyType(
            {
                "requires_env": (),
                "allows_external_api": False,
                "allows_raw_write": False,
                "allows_canonical_write": False,
                "ci_allowed": True,
            }
        ),
        "synthetic": MappingProxyType(
            {
                "requires_env": (),
                "allows_external_api": False,
                "allows_raw_write": False,
                "allows_canonical_write": True,
                "ci_allowed": True,
            }
        ),
        "smoke": MappingProxyType(
            {
                "requires_env": _EXTERNAL_DATA_ACCESS_REQUIRED_ENV,
                "allows_external_api": True,
                "allows_raw_write": False,
                "allows_canonical_write": False,
                "ci_allowed": False,
            }
        ),
        "authorized_pull": MappingProxyType(
            {
                "requires_env": _EXTERNAL_DATA_ACCESS_REQUIRED_ENV + (_RAW_WRITE_REQUIRED_ENV,),
                "allows_external_api": True,
                "allows_raw_write": True,
                "allows_canonical_write": False,
                "ci_allowed": False,
            }
        ),
    }
)

CLOUD_OR_SYNC_MARKERS: tuple[str, ...] = (
    "onedrive",
    "dropbox",
    "google drive",
    "googledrive",
    "windows-synced",
    "windows_synced",
    "windows synced",
)

FORBIDDEN_PREFIXES: tuple[str, ...] = (
    "/mnt",
    "/net",
    "/nfs",
    "/tmp",
    "/var/tmp",
    "/dev/shm",
)


def _repo_root() -> Path:
    for parent in Path(__file__).resolve(strict=False).parents:
        if (parent / "pyproject.toml").is_file() and (parent / "src").is_dir():
            return parent.resolve(strict=False)
    return Path.cwd().resolve(strict=False)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        msg = f"{field_name} must be a non-empty string"
        raise DataFoundationValidationError(msg)
    normalized = value.strip()
    if not normalized:
        msg = f"{field_name} must be a non-empty string"
        raise DataFoundationValidationError(msg)
    return normalized


def _normalize_mode_token(value: object, field_name: str) -> str:
    raw = _require_text(value, field_name)
    token = raw.lower().replace("-", "_").replace(" ", "_")
    if not token.replace("_", "").isalnum():
        msg = f"{field_name} contains invalid mode token {raw!r}"
        raise DataFoundationValidationError(msg)
    return token


def _normalize_modes(value: object, field_name: str) -> frozenset[str]:
    if isinstance(value, str) or not isinstance(value, Iterable):
        msg = f"{field_name} must be a non-empty iterable of mode strings"
        raise DataFoundationValidationError(msg)
    modes = frozenset(_normalize_mode_token(item, field_name) for item in value)
    if not modes:
        msg = f"{field_name} must not be empty"
        raise DataFoundationValidationError(msg)
    return modes


def _normalize_env_names(value: object, field_name: str) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, Iterable):
        msg = f"{field_name} must be an iterable of environment variable names"
        raise DataFoundationValidationError(msg)

    names: list[str] = []
    for item in value:
        name = _require_text(item, field_name).upper()
        if not name.replace("_", "").isalnum():
            msg = f"{field_name} contains invalid environment variable name {name!r}"
            raise DataFoundationValidationError(msg)
        names.append(name)
    return tuple(dict.fromkeys(names))


def _require_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        msg = f"{field_name} must be a boolean"
        raise DataFoundationValidationError(msg)
    return value


def _parse_env_bool_flag(value: object, field_name: str) -> bool:
    if not isinstance(value, str):
        msg = f"{field_name} must be a boolean string"
        raise DataFoundationValidationError(msg)
    token = value.strip().lower()
    if token in {"1", "true", "yes", "on"}:
        return True
    if token in {"0", "false", "no", "off", ""}:
        return False
    msg = f"{field_name} must be a boolean string"
    raise DataFoundationValidationError(msg)


def _env_flag_enabled(value: object, field_name: str) -> bool:
    if _parse_env_bool_flag(value, field_name):
        return True
    msg = f"{field_name} must be set to a true boolean string"
    raise DataFoundationValidationError(msg)


def _runtime_ci_enabled(env: Mapping[str, str]) -> bool:
    value = env.get("CI")
    if value is None:
        return False
    return _parse_env_bool_flag(value, "CI")


def _mode_implies_forbidden_capability(mode: str) -> bool:
    parts = frozenset(mode.split("_"))
    return bool(
        parts & PROHIBITED_ALLOWED_MODE_PARTS
        or any(mode.startswith(prefix) for prefix in PROHIBITED_ALLOWED_MODE_PREFIXES)
    )


def _require_aware_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        msg = f"{field_name} must be a timezone-aware datetime"
        raise DataFoundationValidationError(msg)
    if value.tzinfo is None or value.utcoffset() is None:
        msg = f"{field_name} must be timezone-aware"
        raise DataFoundationValidationError(msg)
    return value


@dataclass(frozen=True, slots=True)
class DatabentoExternalAccessAuthorization:
    """Validated Databento external-access gate separate from IBKR access modes."""

    requires_env: tuple[str, ...]
    allows_external_api: bool
    allows_raw_write: bool
    ci_allowed: bool

    def __post_init__(self) -> None:
        requires_env = _normalize_env_names(self.requires_env, "requires_env")
        allows_external_api = _require_bool(
            self.allows_external_api,
            "allows_external_api",
        )
        allows_raw_write = _require_bool(self.allows_raw_write, "allows_raw_write")
        ci_allowed = _require_bool(self.ci_allowed, "ci_allowed")

        expected = DATABENTO_EXTERNAL_ACCESS_REQUIRED_ENV
        if allows_raw_write:
            expected = expected + (_RAW_WRITE_REQUIRED_ENV,)
        if requires_env != expected:
            msg = "Databento external access authorization requires Databento env gates"
            raise DataFoundationValidationError(msg)
        if not allows_external_api:
            msg = "Databento external access authorization must allow external API access"
            raise DataFoundationValidationError(msg)
        if ci_allowed:
            msg = "Databento external access authorization cannot be CI-allowed"
            raise DataFoundationValidationError(msg)

        object.__setattr__(self, "requires_env", requires_env)
        object.__setattr__(self, "allows_external_api", allows_external_api)
        object.__setattr__(self, "allows_raw_write", allows_raw_write)
        object.__setattr__(self, "ci_allowed", ci_allowed)


def require_databento_external_access(
    env: Mapping[str, str] | None = None,
    *,
    ci: bool | None = None,
    require_raw_write: bool = False,
) -> DatabentoExternalAccessAuthorization:
    """Fail closed unless Databento external access is explicitly authorized."""

    source = os.environ if env is None else env
    ci_enabled = _runtime_ci_enabled(source) if ci is None else _require_bool(ci, "ci")
    if ci_enabled:
        msg = "Databento external access is not allowed in CI"
        raise DataFoundationValidationError(msg)

    required_env = DATABENTO_EXTERNAL_ACCESS_REQUIRED_ENV
    if require_raw_write:
        required_env = required_env + (_RAW_WRITE_REQUIRED_ENV,)
    for env_name in required_env:
        if env_name not in source:
            msg = f"Databento external access requires {env_name}"
            raise DataFoundationValidationError(msg)
        _env_flag_enabled(source[env_name], env_name)

    return DatabentoExternalAccessAuthorization(
        requires_env=required_env,
        allows_external_api=True,
        allows_raw_write=require_raw_write,
        ci_allowed=False,
    )


@dataclass(frozen=True, slots=True)
class DataSourceProfile:
    """Validated description of a provider's allowed and forbidden data usage modes."""

    source_id: str
    provider_name: str
    provider_type: str
    allowed_modes: frozenset[str]
    forbidden_modes: frozenset[str]
    requires_authorization: bool
    market_data_permissions_note: str
    created_at: datetime

    def __post_init__(self) -> None:
        source_id = _require_text(self.source_id, "source_id")
        provider_name = _require_text(self.provider_name, "provider_name")
        provider_type = _normalize_mode_token(self.provider_type, "provider_type")
        allowed_modes = _normalize_modes(self.allowed_modes, "allowed_modes")
        forbidden_modes = _normalize_modes(self.forbidden_modes, "forbidden_modes")
        market_data_permissions_note = _require_text(
            self.market_data_permissions_note,
            "market_data_permissions_note",
        )
        created_at = _require_aware_datetime(self.created_at, "created_at")

        if not source_id.startswith("dsrc_"):
            msg = "source_id must use the dsrc_ prefix"
            raise DataFoundationValidationError(msg)
        if not isinstance(self.requires_authorization, bool):
            msg = "requires_authorization must be a boolean"
            raise DataFoundationValidationError(msg)
        if allowed_modes & forbidden_modes:
            overlap = ", ".join(sorted(allowed_modes & forbidden_modes))
            msg = f"allowed_modes and forbidden_modes must be disjoint; overlap: {overlap}"
            raise DataFoundationValidationError(msg)
        if _mode_implies_forbidden_capability(provider_type):
            msg = f"provider_type {provider_type!r} implies a forbidden capability"
            raise DataFoundationValidationError(msg)
        implied = sorted(mode for mode in allowed_modes if _mode_implies_forbidden_capability(mode))
        if implied:
            msg = (
                "allowed_modes must not include broker, execution, order, account, "
                "paper, live, real-time, or completeness modes: "
            )
            msg += ", ".join(implied)
            raise DataFoundationValidationError(msg)

        object.__setattr__(self, "source_id", source_id)
        object.__setattr__(self, "provider_name", provider_name)
        object.__setattr__(self, "provider_type", provider_type)
        object.__setattr__(self, "allowed_modes", allowed_modes)
        object.__setattr__(self, "forbidden_modes", forbidden_modes)
        object.__setattr__(self, "market_data_permissions_note", market_data_permissions_note)
        object.__setattr__(self, "created_at", created_at)

    @classmethod
    def ibkr_historical(cls, *, created_at: datetime | None = None) -> DataSourceProfile:
        """Build the campaign's read-only historical IBKR data-source profile."""

        return cls(
            source_id="dsrc_ibkr_historical",
            provider_name="Interactive Brokers",
            provider_type="historical_data_provider",
            allowed_modes=READ_ONLY_HISTORICAL_MODES,
            forbidden_modes=IBKR_FORBIDDEN_MODES,
            requires_authorization=True,
            market_data_permissions_note=(
                "Market-data permissions and provider availability can limit historical "
                "data; this profile is not a coverage assertion."
            ),
            created_at=created_at or datetime.now(UTC),
        )

    @classmethod
    def databento_historical(
        cls,
        *,
        created_at: datetime | None = None,
    ) -> DataSourceProfile:
        """Build the read-only historical Databento data-source profile."""

        return cls(
            source_id="dsrc_databento_historical",
            provider_name="Databento",
            provider_type="historical_data_provider",
            allowed_modes=READ_ONLY_HISTORICAL_MODES,
            forbidden_modes=DATABENTO_FORBIDDEN_MODES,
            requires_authorization=True,
            market_data_permissions_note=(
                "Databento market-data entitlements, dataset availability, and provider "
                "coverage can limit historical data; this profile is not a coverage "
                "assertion."
            ),
            created_at=created_at or datetime.now(UTC),
        )

    def allows_mode(self, mode: str) -> bool:
        return _normalize_mode_token(mode, "mode") in self.allowed_modes

    def forbids_mode(self, mode: str) -> bool:
        return _normalize_mode_token(mode, "mode") in self.forbidden_modes


def _normalize_data_root(value: object) -> Path:
    if not isinstance(value, (str, os.PathLike)):
        msg = "data_root must be a string or path-like value"
        raise DataFoundationValidationError(msg)
    raw = os.fspath(value).strip()
    if not raw:
        msg = "data_root must be a non-empty path"
        raise DataFoundationValidationError(msg)
    if raw.startswith(("//", "\\\\")):
        msg = "data_root must not use a network path"
        raise DataFoundationValidationError(msg)
    return Path(raw).expanduser().resolve(strict=False)


def _normalize_repo_paths(value: object) -> tuple[Path, ...]:
    if isinstance(value, (str, os.PathLike)) or not isinstance(value, Iterable):
        msg = "forbidden_repo_paths must be a non-empty iterable of repo-relative paths"
        raise DataFoundationValidationError(msg)

    normalized: list[Path] = []
    for item in value:
        if not isinstance(item, (str, os.PathLike)):
            msg = "forbidden_repo_paths entries must be path-like"
            raise DataFoundationValidationError(msg)
        path = Path(os.fspath(item))
        if path.is_absolute() or not path.parts or any(part == ".." for part in path.parts):
            msg = "forbidden_repo_paths entries must be repo-relative and stay inside the repo"
            raise DataFoundationValidationError(msg)
        normalized.append(path)
    if not normalized:
        msg = "forbidden_repo_paths must not be empty"
        raise DataFoundationValidationError(msg)
    return tuple(normalized)


def _normalize_subdirs(value: object) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, Iterable):
        msg = "allowed_subdirs must be a non-empty iterable of relative subdirectory names"
        raise DataFoundationValidationError(msg)

    normalized: list[str] = []
    for item in value:
        name = _require_text(item, "allowed_subdirs")
        path = Path(name)
        if path.is_absolute() or len(path.parts) != 1 or name in {".", ".."}:
            msg = "allowed_subdirs entries must be simple relative directory names"
            raise DataFoundationValidationError(msg)
        normalized.append(name)
    if not normalized:
        msg = "allowed_subdirs must not be empty"
        raise DataFoundationValidationError(msg)
    return tuple(dict.fromkeys(normalized))


def _normalize_max_file_policy(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        msg = "max_file_policy must be a mapping"
        raise DataFoundationValidationError(msg)
    max_bytes = value.get("max_bytes_per_file")
    if not isinstance(max_bytes, int) or max_bytes <= 0:
        msg = "max_file_policy.max_bytes_per_file must be a positive integer"
        raise DataFoundationValidationError(msg)
    oversize_action = value.get("oversize_action")
    if oversize_action != "fail_closed":
        msg = "max_file_policy.oversize_action must be fail_closed"
        raise DataFoundationValidationError(msg)
    return MappingProxyType(dict(value))


def _path_starts_with(path: Path, prefix: str) -> bool:
    text = path.as_posix().lower()
    return text == prefix or text.startswith(prefix + "/")


def _is_forbidden_location(path: Path) -> bool:
    text = path.as_posix().lower()
    temp_root = Path(tempfile.gettempdir()).resolve(strict=False).as_posix().lower()
    return bool(
        any(_path_starts_with(path, prefix) for prefix in FORBIDDEN_PREFIXES)
        or (text == temp_root or text.startswith(temp_root + "/"))
        or any(marker in text for marker in CLOUD_OR_SYNC_MARKERS)
    )


@dataclass(frozen=True, slots=True)
class LocalDataRootPolicy:
    """Validated local-only root policy for real market-data artifacts."""

    data_root: Path
    must_be_local: bool
    must_be_ignored: bool
    forbidden_repo_paths: tuple[Path, ...]
    allowed_subdirs: tuple[str, ...]
    max_file_policy: Mapping[str, object]

    def __post_init__(self) -> None:
        data_root = _normalize_data_root(self.data_root)
        forbidden_repo_paths = _normalize_repo_paths(self.forbidden_repo_paths)
        allowed_subdirs = _normalize_subdirs(self.allowed_subdirs)
        max_file_policy = _normalize_max_file_policy(self.max_file_policy)
        repo_root = _repo_root()

        if self.must_be_local is not True:
            msg = "must_be_local must be true"
            raise DataFoundationValidationError(msg)
        if self.must_be_ignored is not True:
            msg = "must_be_ignored must be true"
            raise DataFoundationValidationError(msg)
        if _is_relative_to(data_root, repo_root):
            msg = f"data_root must be outside the repository tree: {data_root.as_posix()}"
            raise DataFoundationValidationError(msg)
        if _is_forbidden_location(data_root):
            msg = (
                "data_root is in a forbidden synced, network, mount, or temporary "
                f"location: {data_root.as_posix()}"
            )
            raise DataFoundationValidationError(msg)

        object.__setattr__(self, "data_root", data_root)
        object.__setattr__(self, "forbidden_repo_paths", forbidden_repo_paths)
        object.__setattr__(self, "allowed_subdirs", allowed_subdirs)
        object.__setattr__(self, "max_file_policy", max_file_policy)

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
        *,
        default_root: str | Path = DEFAULT_ALPHA_DATA_ROOT,
    ) -> LocalDataRootPolicy:
        """Read ``ALPHA_DATA_ROOT`` and build the default local data-root policy."""

        source = os.environ if env is None else env
        root = source.get("ALPHA_DATA_ROOT", os.fspath(default_root))
        return cls(
            data_root=root,
            must_be_local=True,
            must_be_ignored=True,
            forbidden_repo_paths=DEFAULT_FORBIDDEN_REPO_PATHS,
            allowed_subdirs=DEFAULT_ALLOWED_SUBDIRS,
            max_file_policy=DEFAULT_MAX_FILE_POLICY,
        )


def require_local_data_root_policy(policy: LocalDataRootPolicy | None) -> LocalDataRootPolicy:
    """Return a validated policy or fail closed before any raw-data write can proceed."""

    if not isinstance(policy, LocalDataRootPolicy):
        msg = "missing LocalDataRootPolicy blocks raw writes"
        raise DataFoundationValidationError(msg)
    return policy


@dataclass(frozen=True, slots=True)
class DataAccessMode:
    """Validated local/external data-access mode gate."""

    mode: str
    requires_env: tuple[str, ...]
    allows_external_api: bool
    allows_raw_write: bool
    allows_canonical_write: bool
    ci_allowed: bool

    def __post_init__(self) -> None:
        mode = _normalize_mode_token(self.mode, "mode")
        expected = _DATA_ACCESS_MODE_CONTRACT.get(mode)
        if expected is None:
            allowed = ", ".join(sorted(_DATA_ACCESS_MODE_CONTRACT))
            msg = f"DataAccessMode mode must be one of: {allowed}"
            raise DataFoundationValidationError(msg)

        requires_env = _normalize_env_names(self.requires_env, "requires_env")
        allows_external_api = _require_bool(
            self.allows_external_api,
            "allows_external_api",
        )
        allows_raw_write = _require_bool(self.allows_raw_write, "allows_raw_write")
        allows_canonical_write = _require_bool(
            self.allows_canonical_write,
            "allows_canonical_write",
        )
        ci_allowed = _require_bool(self.ci_allowed, "ci_allowed")

        expected_requires_env = tuple(expected["requires_env"])
        if (
            requires_env != expected_requires_env
            or allows_external_api != expected["allows_external_api"]
            or allows_raw_write != expected["allows_raw_write"]
            or allows_canonical_write != expected["allows_canonical_write"]
            or ci_allowed != expected["ci_allowed"]
        ):
            msg = f"DataAccessMode {mode!r} must match the campaign access-mode contract"
            raise DataFoundationValidationError(msg)

        if allows_external_api and ci_allowed:
            msg = "DataAccessMode cannot allow external API calls in CI"
            raise DataFoundationValidationError(msg)
        if allows_external_api and not set(_EXTERNAL_DATA_ACCESS_REQUIRED_ENV).issubset(
            requires_env
        ):
            msg = "external API modes require the data-pull and read-only IBKR env gates"
            raise DataFoundationValidationError(msg)
        if allows_raw_write and _RAW_WRITE_REQUIRED_ENV not in requires_env:
            msg = "raw-write modes require ALPHA_ALLOW_RAW_LOCAL_WRITE"
            raise DataFoundationValidationError(msg)

        object.__setattr__(self, "mode", mode)
        object.__setattr__(self, "requires_env", requires_env)
        object.__setattr__(self, "allows_external_api", allows_external_api)
        object.__setattr__(self, "allows_raw_write", allows_raw_write)
        object.__setattr__(self, "allows_canonical_write", allows_canonical_write)
        object.__setattr__(self, "ci_allowed", ci_allowed)

    @classmethod
    def for_mode(cls, mode: object) -> DataAccessMode:
        """Build a canonical mode record by mode name."""

        token = _normalize_mode_token(mode, "mode")
        expected = _DATA_ACCESS_MODE_CONTRACT.get(token)
        if expected is None:
            allowed = ", ".join(sorted(_DATA_ACCESS_MODE_CONTRACT))
            msg = f"DataAccessMode mode must be one of: {allowed}"
            raise DataFoundationValidationError(msg)
        return cls(
            mode=token,
            requires_env=tuple(expected["requires_env"]),
            allows_external_api=bool(expected["allows_external_api"]),
            allows_raw_write=bool(expected["allows_raw_write"]),
            allows_canonical_write=bool(expected["allows_canonical_write"]),
            ci_allowed=bool(expected["ci_allowed"]),
        )

    @classmethod
    def dry_run(cls) -> DataAccessMode:
        """Build the local dry-run mode."""

        return cls.for_mode("dry_run")

    @classmethod
    def synthetic(cls) -> DataAccessMode:
        """Build the local synthetic mode."""

        return cls.for_mode("synthetic")

    @classmethod
    def smoke(cls) -> DataAccessMode:
        """Build the external-read smoke mode; it is never CI-allowed."""

        return cls.for_mode("smoke")

    @classmethod
    def authorized_pull(cls) -> DataAccessMode:
        """Build the authorized external-pull mode; it is never CI-allowed."""

        return cls.for_mode("authorized_pull")

    def validate_runtime_env(
        self,
        env: Mapping[str, str] | None = None,
        *,
        ci: bool | None = None,
    ) -> DataAccessMode:
        """Validate runtime env gates before an external data access attempt."""

        source = os.environ if env is None else env
        ci_enabled = _runtime_ci_enabled(source) if ci is None else ci
        if ci_enabled and not self.ci_allowed:
            msg = f"DataAccessMode {self.mode!r} is not allowed to call external APIs in CI"
            raise DataFoundationValidationError(msg)

        for env_name in self.requires_env:
            if env_name not in source:
                msg = f"DataAccessMode {self.mode!r} requires {env_name}"
                raise DataFoundationValidationError(msg)
            _env_flag_enabled(source[env_name], env_name)
        return self


__all__ = [
    "DEFAULT_ALLOWED_SUBDIRS",
    "DEFAULT_ALPHA_DATA_ROOT",
    "DEFAULT_FORBIDDEN_REPO_PATHS",
    "DEFAULT_MAX_FILE_POLICY",
    "DATABENTO_DATA_PULL_AUTHORIZED_ENV",
    "DATABENTO_EXTERNAL_ACCESS_ENV",
    "DATABENTO_EXTERNAL_ACCESS_REQUIRED_ENV",
    "DATABENTO_FORBIDDEN_MODES",
    "DataAccessMode",
    "DatabentoExternalAccessAuthorization",
    "DataFoundationValidationError",
    "DataSourceProfile",
    "IBKR_FORBIDDEN_MODES",
    "LocalDataRootPolicy",
    "READ_ONLY_HISTORICAL_MODES",
    "require_databento_external_access",
    "require_local_data_root_policy",
]
