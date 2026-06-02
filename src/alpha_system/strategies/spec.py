"""StrategySpec contracts and registry-backed version helpers."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from alpha_system.core.git_info import capture_git_info
from alpha_system.core.hashing import canonical_json, hash_config
from alpha_system.core.registry import connect_registry, init_registry
from alpha_system.core.enums import Direction
from alpha_system.factors.dependency_spec import looks_like_label_field


class StrategySpecError(ValueError):
    """Raised when StrategySpec construction violates its contract."""


class StrategyRegistryError(ValueError):
    """Raised when strategy registry operations violate registry policy."""


FORBIDDEN_STRATEGY_RESPONSIBILITIES: tuple[str, ...] = (
    "account_equity",
    "equity",
    "capital",
    "cash_balance",
    "position_size",
    "position_sizing",
    "fills",
    "fill_model",
    "order_lifecycle",
    "order_router",
    "slippage",
    "commission",
    "partial_take_profit",
    "partial_take_profit_accounting",
    "portfolio",
    "portfolio_aggregation",
)

ALLOWED_STRATEGY_OUTPUT_FIELDS: tuple[str, ...] = (
    "entry_signal",
    "exit_signal",
    "direction",
    "confidence_score",
    "desired_exposure",
    "required_factor_dependencies",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class StrategyFactorDependency:
    """A declared factor version a strategy may read."""

    factor_id: str
    factor_version: str
    input_name: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "factor_id",
            _required_identifier(self.factor_id, "factor_id"),
        )
        object.__setattr__(
            self,
            "factor_version",
            _required_string(self.factor_version, "factor_version"),
        )
        object.__setattr__(
            self,
            "input_name",
            _required_identifier(self.input_name, "input_name"),
        )
        _reject_label_like(self.factor_id, "factor_id")
        _reject_label_like(self.input_name, "input_name")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "StrategyFactorDependency":
        """Build a declared factor dependency from a JSON-like mapping."""
        required = ("factor_id", "factor_version", "input_name")
        missing = tuple(field for field in required if field not in payload)
        if missing:
            msg = f"strategy factor dependency missing fields: {', '.join(missing)}"
            raise StrategySpecError(msg)
        return cls(
            factor_id=payload["factor_id"],
            factor_version=payload["factor_version"],
            input_name=payload["input_name"],
        )

    def to_dict(self) -> dict[str, str]:
        """Serialize to JSON-compatible values."""
        return {
            "factor_id": self.factor_id,
            "factor_version": self.factor_version,
            "input_name": self.input_name,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class StrategySpec:
    """Strategy intent contract that excludes management, portfolio, and execution."""

    strategy_id: str
    name: str
    version: str
    owner: str
    description: str
    entry_signal: str
    exit_signal: str
    direction: Direction
    required_factor_dependencies: tuple[StrategyFactorDependency, ...]
    parameters: Mapping[str, Any]
    metadata: Mapping[str, Any]
    confidence_score: float | Decimal | None = None
    desired_exposure: float | Decimal | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "strategy_id",
            _required_identifier(self.strategy_id, "strategy_id"),
        )
        object.__setattr__(self, "name", _required_string(self.name, "name"))
        object.__setattr__(self, "version", _required_string(self.version, "version"))
        object.__setattr__(self, "owner", _required_string(self.owner, "owner"))
        object.__setattr__(
            self,
            "description",
            _required_string(self.description, "description"),
        )
        object.__setattr__(
            self,
            "entry_signal",
            _strategy_expression(self.entry_signal, "entry_signal"),
        )
        object.__setattr__(
            self,
            "exit_signal",
            _strategy_expression(self.exit_signal, "exit_signal"),
        )
        object.__setattr__(self, "direction", _parse_direction(self.direction, "direction"))
        object.__setattr__(
            self,
            "required_factor_dependencies",
            _dependency_tuple(self.required_factor_dependencies),
        )
        object.__setattr__(self, "parameters", _checked_mapping(self.parameters, "parameters"))
        object.__setattr__(self, "metadata", _checked_mapping(self.metadata, "metadata"))
        object.__setattr__(
            self,
            "confidence_score",
            _optional_number(self.confidence_score, "confidence_score"),
        )
        object.__setattr__(
            self,
            "desired_exposure",
            _optional_number(self.desired_exposure, "desired_exposure"),
        )

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "StrategySpec":
        """Build a StrategySpec from a JSON-like mapping."""
        _reject_forbidden_payload(payload, "StrategySpec")
        required = (
            "strategy_id",
            "name",
            "version",
            "owner",
            "description",
            "entry_signal",
            "exit_signal",
            "direction",
            "required_factor_dependencies",
            "parameters",
            "metadata",
        )
        missing = tuple(field for field in required if field not in payload)
        if missing:
            msg = f"StrategySpec missing required fields: {', '.join(missing)}"
            raise StrategySpecError(msg)
        return cls(
            strategy_id=payload["strategy_id"],
            name=payload["name"],
            version=payload["version"],
            owner=payload["owner"],
            description=payload["description"],
            entry_signal=payload["entry_signal"],
            exit_signal=payload["exit_signal"],
            direction=payload["direction"],
            required_factor_dependencies=normalize_factor_dependencies(
                payload["required_factor_dependencies"]
            ),
            parameters=payload["parameters"],
            metadata=payload["metadata"],
            confidence_score=payload.get("confidence_score"),
            desired_exposure=payload.get("desired_exposure"),
        )

    @property
    def required_factor_ids(self) -> tuple[str, ...]:
        """Return declared factor identifiers in dependency order."""
        return tuple(dependency.factor_id for dependency in self.required_factor_dependencies)

    @property
    def factor_versions(self) -> Mapping[str, str]:
        """Return declared factor version dependencies."""
        return {
            dependency.factor_id: dependency.factor_version
            for dependency in self.required_factor_dependencies
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize to stable JSON-compatible values."""
        return {
            "strategy_id": self.strategy_id,
            "name": self.name,
            "version": self.version,
            "owner": self.owner,
            "description": self.description,
            "entry_signal": self.entry_signal,
            "exit_signal": self.exit_signal,
            "direction": self.direction.value,
            "required_factor_dependencies": [
                dependency.to_dict()
                for dependency in self.required_factor_dependencies
            ],
            "parameters": dict(self.parameters),
            "metadata": dict(self.metadata),
            "confidence_score": _number_to_json(self.confidence_score),
            "desired_exposure": _number_to_json(self.desired_exposure),
        }


@dataclass(frozen=True, slots=True)
class StrategyVersionRecord:
    strategy_id: str
    strategy_version: str
    created_at: str
    git_commit: str | None
    git_dirty: int | None
    code_hash: str
    config_hash: str
    data_version: str
    factor_versions: Mapping[str, str]
    parameters: Mapping[str, Any]
    artifact_paths: Mapping[str, Any]
    decision_status: str
    status_message: str


def normalize_factor_dependencies(value: Any) -> tuple[StrategyFactorDependency, ...]:
    """Normalize factor dependency declarations."""
    if not isinstance(value, Sequence) or isinstance(value, str | bytes):
        msg = "required_factor_dependencies must be a non-empty sequence"
        raise StrategySpecError(msg)
    dependencies = tuple(
        item
        if isinstance(item, StrategyFactorDependency)
        else StrategyFactorDependency.from_mapping(item)
        for item in value
    )
    return _dependency_tuple(dependencies)


def compute_strategy_config_hash(payload: Mapping[str, Any]) -> str:
    """Hash a strategy config while excluding a self-referential config_hash."""
    return hash_config(
        {
            str(key): value
            for key, value in payload.items()
            if str(key) != "config_hash"
        }
    )


def register_strategy_spec(
    registry_path: str | Path,
    spec: StrategySpec,
    *,
    data_version: str,
    decision_status: str = "draft",
    status_message: str = "strategy version registration",
    code_hash: str | None = None,
    config_hash: str | None = None,
    artifact_paths: Mapping[str, Any] | None = None,
    repo_root: str | Path | None = None,
) -> None:
    """Record a strategy identity and version in existing registry tables."""
    registry = _init_valid_temp_registry(registry_path, repo_root=repo_root)
    git_info = capture_git_info(Path.cwd())
    active_code_hash = code_hash or hash_config(
        {
            "module": "alpha_system.strategies",
            "strategy_id": spec.strategy_id,
            "strategy_version": spec.version,
        }
    )
    active_config_hash = config_hash or compute_strategy_config_hash(spec.to_dict())
    active_artifact_paths = dict(artifact_paths or {})
    with connect_registry(registry) as connection:
        if strategy_version_exists(connection, spec.strategy_id, spec.version):
            msg = f"strategy version already exists: {spec.strategy_id} {spec.version}"
            raise StrategyRegistryError(msg)
        now = _utc_now()
        connection.execute(
            """
            INSERT INTO strategy_registry (
                strategy_id,
                name,
                owner,
                description,
                status,
                created_at,
                updated_at,
                metadata_json,
                status_message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(strategy_id) DO UPDATE SET
                name = excluded.name,
                owner = excluded.owner,
                description = excluded.description,
                status = excluded.status,
                updated_at = excluded.updated_at,
                metadata_json = excluded.metadata_json,
                status_message = excluded.status_message
            """,
            (
                spec.strategy_id,
                spec.name,
                spec.owner,
                spec.description,
                decision_status,
                now,
                now,
                canonical_json(dict(spec.metadata)),
                status_message,
            ),
        )
        connection.execute(
            """
            INSERT INTO strategy_versions (
                strategy_id,
                strategy_version,
                created_at,
                git_commit,
                git_dirty,
                code_hash,
                config_hash,
                data_version,
                factor_versions_json,
                parameters_json,
                artifact_paths_json,
                decision_status,
                status_message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                spec.strategy_id,
                spec.version,
                now,
                git_info.commit,
                _git_dirty_value(git_info.dirty),
                active_code_hash,
                active_config_hash,
                data_version,
                canonical_json(spec.factor_versions),
                canonical_json(dict(spec.parameters)),
                canonical_json(active_artifact_paths),
                decision_status,
                status_message,
            ),
        )


def strategy_version_exists(
    connection: sqlite3.Connection,
    strategy_id: str,
    strategy_version: str,
) -> bool:
    """Return whether a strategy version already exists."""
    row = connection.execute(
        """
        SELECT 1
        FROM strategy_versions
        WHERE strategy_id = ? AND strategy_version = ?
        """,
        (strategy_id, strategy_version),
    ).fetchone()
    return row is not None


def get_strategy_version(
    registry_path: str | Path,
    strategy_id: str,
    strategy_version: str,
) -> StrategyVersionRecord | None:
    """Read a strategy version record from a temp/local registry database."""
    with connect_registry(registry_path, read_only=True) as connection:
        row = connection.execute(
            """
            SELECT
                strategy_id,
                strategy_version,
                created_at,
                git_commit,
                git_dirty,
                code_hash,
                config_hash,
                data_version,
                factor_versions_json,
                parameters_json,
                artifact_paths_json,
                decision_status,
                status_message
            FROM strategy_versions
            WHERE strategy_id = ? AND strategy_version = ?
            """,
            (strategy_id, strategy_version),
        ).fetchone()
    if row is None:
        return None
    return StrategyVersionRecord(
        strategy_id=str(row["strategy_id"]),
        strategy_version=str(row["strategy_version"]),
        created_at=str(row["created_at"]),
        git_commit=row["git_commit"],
        git_dirty=row["git_dirty"],
        code_hash=str(row["code_hash"]),
        config_hash=str(row["config_hash"]),
        data_version=str(row["data_version"]),
        factor_versions=_loads(row["factor_versions_json"]),
        parameters=_loads(row["parameters_json"]),
        artifact_paths=_loads(row["artifact_paths_json"]),
        decision_status=str(row["decision_status"]),
        status_message=str(row["status_message"]),
    )


def _dependency_tuple(
    value: Sequence[StrategyFactorDependency],
) -> tuple[StrategyFactorDependency, ...]:
    dependencies = tuple(value)
    if not dependencies:
        msg = "required_factor_dependencies must contain at least one dependency"
        raise StrategySpecError(msg)
    seen_ids: set[str] = set()
    seen_names: set[str] = set()
    for dependency in dependencies:
        if not isinstance(dependency, StrategyFactorDependency):
            msg = "required_factor_dependencies must contain StrategyFactorDependency values"
            raise StrategySpecError(msg)
        if dependency.factor_id in seen_ids:
            msg = f"duplicate strategy factor dependency {dependency.factor_id!r}"
            raise StrategySpecError(msg)
        if dependency.input_name in seen_names:
            msg = f"duplicate strategy input name {dependency.input_name!r}"
            raise StrategySpecError(msg)
        seen_ids.add(dependency.factor_id)
        seen_names.add(dependency.input_name)
    return dependencies


def _init_valid_temp_registry(
    registry_path: str | Path,
    *,
    repo_root: str | Path | None = None,
) -> Path:
    registry = Path(registry_path).expanduser().resolve(strict=False)
    repo = Path(repo_root or Path.cwd()).resolve(strict=False)
    if registry == repo or repo in registry.parents:
        msg = "strategy registry writes must use a temp/local path outside the repository"
        raise StrategyRegistryError(msg)
    status = init_registry(registry)
    if not status.valid:
        msg = f"registry is not valid: {status.status_message}"
        raise StrategyRegistryError(msg)
    return registry


def _checked_mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        msg = f"{field_name} must be a mapping"
        raise StrategySpecError(msg)
    payload = dict(value)
    _reject_forbidden_payload(payload, field_name)
    return payload


def _reject_forbidden_payload(value: Any, context: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = _normalize_key(key)
            if normalized in FORBIDDEN_STRATEGY_RESPONSIBILITIES:
                msg = (
                    f"{context} contains forbidden StrategySpec responsibility "
                    f"{key!r}"
                )
                raise StrategySpecError(msg)
            _reject_forbidden_payload(item, f"{context}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, str | bytes):
        for index, item in enumerate(value):
            _reject_forbidden_payload(item, f"{context}[{index}]")


def _strategy_expression(value: Any, field_name: str) -> str:
    text = _required_string(value, field_name)
    _reject_label_like(text, field_name)
    return text


def _reject_label_like(value: str, field_name: str) -> None:
    if looks_like_label_field(value):
        msg = f"{field_name} {value!r} looks like a label field"
        raise StrategySpecError(msg)


def _required_identifier(value: Any, field_name: str) -> str:
    text = _required_string(value, field_name)
    if not text.replace("_", "").replace("-", "").replace(".", "").isalnum():
        msg = f"{field_name} must contain only letters, numbers, dots, dashes, or underscores"
        raise StrategySpecError(msg)
    return text


def _required_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        msg = f"{field_name} must be a non-empty string"
        raise StrategySpecError(msg)
    return value.strip()


def _parse_direction(value: Any, field_name: str) -> Direction:
    if isinstance(value, Direction):
        return value
    if not isinstance(value, str) or not value.strip():
        msg = f"{field_name} must be a non-empty string"
        raise StrategySpecError(msg)
    try:
        return Direction(value.strip().lower())
    except ValueError as exc:
        allowed = ", ".join(item.value for item in Direction)
        msg = f"{field_name} must be one of: {allowed}"
        raise StrategySpecError(msg) from exc


def _optional_number(value: Any, field_name: str) -> float | Decimal | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float | Decimal):
        msg = f"{field_name} must be numeric when present"
        raise StrategySpecError(msg)
    if isinstance(value, int):
        return float(value)
    return value


def _number_to_json(value: float | Decimal | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _normalize_key(value: Any) -> str:
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def _loads(value: str) -> dict[str, Any]:
    payload = json.loads(value or "{}")
    if isinstance(payload, dict):
        return payload
    return {}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _git_dirty_value(value: bool | None) -> int | None:
    if value is None:
        return None
    return 1 if value else 0
