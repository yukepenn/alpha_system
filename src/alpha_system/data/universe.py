"""Universe configuration, active membership, and deterministic hashing."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from alpha_system.core.enums import AssetClass
from alpha_system.core.hashing import hash_config
from alpha_system.core.instrument_master import (
    InstrumentMasterCatalog,
    InstrumentMasterError,
    InstrumentMasterRecord,
)
from alpha_system.core.instruments import normalize_instrument_id


FUTURE_CONSTRAINT_MODE = "contract_only"
MISSING_DATA_FLAG = "missing_data"
UNAVAILABLE_DATA_FLAG = "unavailable_at_decision"
MISALIGNED_TIMESTAMP_FLAG = "misaligned_timestamp"
INACTIVE_UNIVERSE_MEMBER_FLAG = "inactive_universe_member"


class UniverseSpecError(ValueError):
    """Raised when a universe config is incomplete or unsafe."""


@dataclass(frozen=True, slots=True, kw_only=True)
class UniverseMember:
    """One point-in-time universe member keyed by stable ``instrument_id``."""

    instrument_id: str
    symbol: str
    asset_class: AssetClass
    exchange: str
    currency: str
    timezone: str
    start_date: date
    end_date: date | None
    data_version: str
    inclusion_rules: tuple[str, ...] = ()
    exclusion_rules: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "instrument_id", normalize_instrument_id(self.instrument_id))
        object.__setattr__(self, "symbol", _text(self.symbol, "symbol"))
        object.__setattr__(self, "asset_class", _asset_class(self.asset_class))
        object.__setattr__(self, "exchange", _text(self.exchange, "exchange"))
        object.__setattr__(self, "currency", _text(self.currency, "currency").upper())
        timezone = _text(self.timezone, "timezone")
        _validate_timezone(timezone)
        object.__setattr__(self, "timezone", timezone)
        start_date = _date_value(self.start_date, "start_date")
        end_date = _optional_date(self.end_date, "end_date")
        if end_date is not None and end_date < start_date:
            raise UniverseSpecError("member end_date must be on or after start_date")
        object.__setattr__(self, "start_date", start_date)
        object.__setattr__(self, "end_date", end_date)
        object.__setattr__(self, "data_version", _text(self.data_version, "data_version"))
        object.__setattr__(
            self,
            "inclusion_rules",
            _string_tuple(self.inclusion_rules, "member.inclusion_rules"),
        )
        object.__setattr__(
            self,
            "exclusion_rules",
            _string_tuple(self.exclusion_rules, "member.exclusion_rules"),
        )
        object.__setattr__(self, "metadata", dict(self.metadata or {}))

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, Any],
        *,
        default_data_version: str,
        instrument_master: InstrumentMasterCatalog | None = None,
    ) -> "UniverseMember":
        if not isinstance(payload, Mapping):
            raise UniverseSpecError("universe member must be a mapping")
        master_record = _resolve_master_record(payload, instrument_master)
        merged = _member_payload_with_master_defaults(payload, master_record)
        return cls(
            instrument_id=merged["instrument_id"],
            symbol=merged["symbol"],
            asset_class=merged["asset_class"],
            exchange=merged["exchange"],
            currency=merged["currency"],
            timezone=merged["timezone"],
            start_date=merged.get("start_date", "1900-01-01"),
            end_date=merged.get("end_date"),
            data_version=merged.get("data_version", default_data_version),
            inclusion_rules=tuple(merged.get("inclusion_rules", ())),
            exclusion_rules=tuple(merged.get("exclusion_rules", ())),
            metadata=_mapping(merged.get("metadata", {}), "member.metadata"),
        )

    def active_on(self, active_date: date | str) -> bool:
        query_date = _date_value(active_date, "active_date")
        return self.start_date <= query_date and (
            self.end_date is None or query_date <= self.end_date
        )

    def active_at(self, timestamp: datetime) -> bool:
        _require_aware(timestamp, "timestamp")
        local_date = timestamp.astimezone(ZoneInfo(self.timezone)).date()
        return self.active_on(local_date)

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


@dataclass(frozen=True, slots=True, kw_only=True)
class FutureUniverseConstraint:
    """Representation-only future sector/asset exposure constraint."""

    constraint_id: str
    constraint_type: str
    mode: str = FUTURE_CONSTRAINT_MODE
    enabled: bool = False
    parameters: Mapping[str, Any] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "constraint_id", _text(self.constraint_id, "constraint_id"))
        object.__setattr__(self, "constraint_type", _text(self.constraint_type, "constraint_type"))
        object.__setattr__(self, "mode", _text(self.mode, "mode"))
        if self.mode != FUTURE_CONSTRAINT_MODE:
            raise UniverseSpecError("future universe constraints are contract_only in this phase")
        object.__setattr__(self, "enabled", _bool(self.enabled, "enabled"))
        if self.enabled:
            raise UniverseSpecError("future universe constraints are representation only in this phase")
        object.__setattr__(self, "parameters", dict(self.parameters or {}))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any], *, constraint_type: str) -> "FutureUniverseConstraint":
        if not isinstance(payload, Mapping):
            raise UniverseSpecError(f"{constraint_type} constraint must be a mapping")
        reserved = {"constraint_id", "name", "constraint_type", "mode", "enabled", "parameters"}
        parameters = dict(_mapping(payload.get("parameters", {}), f"{constraint_type}.parameters"))
        for key, value in payload.items():
            if key not in reserved:
                parameters[str(key)] = value
        return cls(
            constraint_id=str(payload.get("constraint_id", payload.get("name", constraint_type))),
            constraint_type=constraint_type,
            mode=str(payload.get("mode", FUTURE_CONSTRAINT_MODE)),
            enabled=payload.get("enabled", False),
            parameters=parameters,
        )

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


@dataclass(frozen=True, slots=True, kw_only=True)
class UniverseSpec:
    """Validated multi-symbol universe configuration."""

    universe_id: str
    name: str
    data_version: str
    members: tuple[UniverseMember, ...]
    inclusion_rules: tuple[str, ...] = ()
    exclusion_rules: tuple[str, ...] = ()
    future_sector_constraints: tuple[FutureUniverseConstraint, ...] = ()
    future_asset_constraints: tuple[FutureUniverseConstraint, ...] = ()
    metadata: Mapping[str, Any] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "universe_id", _text(self.universe_id, "universe_id"))
        object.__setattr__(self, "name", _text(self.name, "name"))
        object.__setattr__(self, "data_version", _text(self.data_version, "data_version"))
        members = tuple(_member(member, default_data_version=self.data_version) for member in self.members)
        if not members:
            raise UniverseSpecError("universe requires at least one member")
        seen: set[str] = set()
        for member in members:
            if member.instrument_id in seen:
                raise UniverseSpecError(f"duplicate universe instrument_id: {member.instrument_id}")
            seen.add(member.instrument_id)
        object.__setattr__(self, "members", tuple(sorted(members, key=lambda item: item.instrument_id)))
        object.__setattr__(self, "inclusion_rules", _string_tuple(self.inclusion_rules, "inclusion_rules"))
        object.__setattr__(self, "exclusion_rules", _string_tuple(self.exclusion_rules, "exclusion_rules"))
        object.__setattr__(
            self,
            "future_sector_constraints",
            tuple(
                _future_constraint(item, constraint_type="sector")
                for item in self.future_sector_constraints
            ),
        )
        object.__setattr__(
            self,
            "future_asset_constraints",
            tuple(
                _future_constraint(item, constraint_type="asset")
                for item in self.future_asset_constraints
            ),
        )
        object.__setattr__(self, "metadata", dict(self.metadata or {}))

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, Any],
        *,
        instrument_master: InstrumentMasterCatalog | Iterable[Mapping[str, Any]] | None = None,
    ) -> "UniverseSpec":
        if not isinstance(payload, Mapping):
            raise UniverseSpecError("universe config root must be a mapping")
        active_payload = payload.get("universe", payload)
        if not isinstance(active_payload, Mapping):
            raise UniverseSpecError("universe config root must be a mapping")
        data_version = _text(active_payload.get("data_version"), "data_version")
        catalog = _catalog(instrument_master)
        raw_members = active_payload.get("instruments", active_payload.get("members"))
        if not isinstance(raw_members, Sequence) or isinstance(raw_members, str | bytes):
            raise UniverseSpecError("universe config requires an instruments list")
        members = tuple(
            UniverseMember.from_mapping(
                member,
                default_data_version=data_version,
                instrument_master=catalog,
            )
            for member in raw_members
        )
        return cls(
            universe_id=active_payload.get("universe_id", active_payload.get("id")),
            name=active_payload.get("name", active_payload.get("universe_id", "")),
            data_version=data_version,
            members=members,
            inclusion_rules=tuple(active_payload.get("inclusion_rules", ())),
            exclusion_rules=tuple(active_payload.get("exclusion_rules", ())),
            future_sector_constraints=tuple(
                FutureUniverseConstraint.from_mapping(item, constraint_type="sector")
                for item in active_payload.get("future_sector_constraints", ())
            ),
            future_asset_constraints=tuple(
                FutureUniverseConstraint.from_mapping(item, constraint_type="asset")
                for item in active_payload.get("future_asset_constraints", ())
            ),
            metadata=_mapping(active_payload.get("metadata", {}), "metadata"),
        )

    def active_members(self, active_date: date | str) -> tuple[UniverseMember, ...]:
        return tuple(member for member in self.members if member.active_on(active_date))

    def active_members_at(self, timestamp: datetime) -> tuple[UniverseMember, ...]:
        return tuple(member for member in self.members if member.active_at(timestamp))

    def active_instrument_ids(self, active_date: date | str) -> tuple[str, ...]:
        return tuple(member.instrument_id for member in self.active_members(active_date))

    def member_by_instrument_id(self) -> dict[str, UniverseMember]:
        return {member.instrument_id: member for member in self.members}

    def get_member(self, instrument_id: str) -> UniverseMember:
        normalized = normalize_instrument_id(instrument_id)
        try:
            return self.member_by_instrument_id()[normalized]
        except KeyError as exc:
            raise UniverseSpecError(f"instrument_id {normalized!r} is not in universe") from exc

    def resolve_symbol(
        self,
        symbol: str,
        *,
        active_date: date | str | None = None,
        exchange: str | None = None,
        currency: str | None = None,
    ) -> str:
        normalized = _text(symbol, "symbol")
        candidates = [member for member in self.members if member.symbol == normalized]
        if active_date is not None:
            candidates = [member for member in candidates if member.active_on(active_date)]
        if exchange is not None:
            candidates = [member for member in candidates if member.exchange == exchange]
        if currency is not None:
            candidates = [member for member in candidates if member.currency == currency.upper()]
        if not candidates:
            raise UniverseSpecError(f"symbol {normalized!r} did not resolve inside universe")
        if len(candidates) > 1:
            ids = ", ".join(member.instrument_id for member in candidates)
            raise UniverseSpecError(f"symbol {normalized!r} is ambiguous inside universe: {ids}")
        return candidates[0].instrument_id

    def hash_input(self) -> dict[str, Any]:
        """Return deterministic universe/config hash input."""
        return {
            "schema": "universe_spec_v1",
            "universe_id": self.universe_id,
            "name": self.name,
            "data_version": self.data_version,
            "members": [member.to_dict() for member in self.members],
            "inclusion_rules": list(self.inclusion_rules),
            "exclusion_rules": list(self.exclusion_rules),
            "future_sector_constraints": [item.to_dict() for item in self.future_sector_constraints],
            "future_asset_constraints": [item.to_dict() for item in self.future_asset_constraints],
            "metadata": _json_ready(self.metadata),
        }

    def config_hash(self) -> str:
        return hash_config(self.hash_input())

    def to_dict(self) -> dict[str, Any]:
        return self.hash_input()


def load_universe_config(
    path: str | Path,
    *,
    instrument_master: InstrumentMasterCatalog | Iterable[Mapping[str, Any]] | None = None,
) -> UniverseSpec:
    """Load a JSON universe config."""
    config_path = Path(path).expanduser().resolve(strict=False)
    if config_path.suffix.lower() != ".json":
        raise UniverseSpecError(f"universe config must be JSON: {config_path}")
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    return UniverseSpec.from_mapping(payload, instrument_master=instrument_master)


def universe_hash_input(universe: UniverseSpec | Mapping[str, Any]) -> dict[str, Any]:
    active = universe if isinstance(universe, UniverseSpec) else UniverseSpec.from_mapping(universe)
    return active.hash_input()


def universe_config_hash(universe: UniverseSpec | Mapping[str, Any]) -> str:
    return hash_config(universe_hash_input(universe))


def _resolve_master_record(
    payload: Mapping[str, Any],
    instrument_master: InstrumentMasterCatalog | None,
) -> InstrumentMasterRecord | None:
    if instrument_master is None:
        if "instrument_id" not in payload:
            raise UniverseSpecError("symbol-only universe members require an instrument master")
        return None
    if "instrument_id" in payload:
        try:
            return instrument_master.get(str(payload["instrument_id"]))
        except InstrumentMasterError as exc:
            raise UniverseSpecError(str(exc)) from exc
    symbol = payload.get("symbol")
    if symbol is None:
        raise UniverseSpecError("universe member requires instrument_id or symbol")
    try:
        instrument_id = instrument_master.resolve_symbol(
            str(symbol),
            active_date=payload.get("start_date"),
            exchange=payload.get("exchange"),
            currency=payload.get("currency"),
        )
        return instrument_master.get(instrument_id)
    except InstrumentMasterError as exc:
        raise UniverseSpecError(str(exc)) from exc


def _member_payload_with_master_defaults(
    payload: Mapping[str, Any],
    master_record: InstrumentMasterRecord | None,
) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    base_metadata: dict[str, Any] = {}
    if master_record is not None:
        merged.update(master_record.to_dict())
        base_metadata = {
            "tick_size": merged.get("tick_size"),
            "lot_size": merged.get("lot_size"),
            "multiplier": merged.get("multiplier"),
            "corporate_action_policy": merged.get("corporate_action_policy"),
            "instrument_master_metadata": dict(master_record.metadata),
        }
        merged["metadata"] = base_metadata
    payload_metadata = dict(_mapping(payload.get("metadata", {}), "member.metadata")) if "metadata" in payload else {}
    merged.update(dict(payload))
    if master_record is not None or payload_metadata:
        merged["metadata"] = {**base_metadata, **payload_metadata}
    required = (
        "instrument_id",
        "symbol",
        "asset_class",
        "exchange",
        "currency",
        "timezone",
    )
    missing = tuple(field for field in required if field not in merged)
    if missing:
        raise UniverseSpecError(f"universe member missing required fields: {', '.join(missing)}")
    return merged


def _catalog(
    value: InstrumentMasterCatalog | Iterable[Mapping[str, Any]] | None,
) -> InstrumentMasterCatalog | None:
    if value is None:
        return None
    if isinstance(value, InstrumentMasterCatalog):
        return value
    return InstrumentMasterCatalog.from_mappings(value)


def _member(value: UniverseMember | Mapping[str, Any], *, default_data_version: str) -> UniverseMember:
    if isinstance(value, UniverseMember):
        return value
    return UniverseMember.from_mapping(value, default_data_version=default_data_version)


def _future_constraint(
    value: FutureUniverseConstraint | Mapping[str, Any],
    *,
    constraint_type: str,
) -> FutureUniverseConstraint:
    if isinstance(value, FutureUniverseConstraint):
        return value
    return FutureUniverseConstraint.from_mapping(value, constraint_type=constraint_type)


def _mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise UniverseSpecError(f"{field_name} must be a mapping")
    return value


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise UniverseSpecError(f"{field_name} must be a non-empty string")
    return value.strip()


def _bool(value: Any, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().lower() in {"true", "false"}:
        return value.strip().lower() == "true"
    raise UniverseSpecError(f"{field_name} must be boolean")


def _asset_class(value: Any) -> AssetClass:
    if isinstance(value, AssetClass):
        return value
    try:
        return AssetClass(str(value))
    except ValueError as exc:
        raise UniverseSpecError(f"unsupported asset_class: {value}") from exc


def _date_value(value: date | str, field_name: str) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise UniverseSpecError(f"{field_name} must be an ISO date") from exc
    raise UniverseSpecError(f"{field_name} must be a date or ISO date string")


def _optional_date(value: date | str | None, field_name: str) -> date | None:
    if value in (None, ""):
        return None
    return _date_value(value, field_name)


def _string_tuple(value: Iterable[Any], field_name: str) -> tuple[str, ...]:
    if isinstance(value, str):
        values = (value,)
    else:
        try:
            values = tuple(str(item).strip() for item in value)
        except TypeError as exc:
            raise UniverseSpecError(f"{field_name} must be a string sequence") from exc
    if any(not item for item in values):
        raise UniverseSpecError(f"{field_name} contains an empty value")
    return values


def _validate_timezone(value: str) -> None:
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise UniverseSpecError(f"timezone is not recognized: {value}") from exc


def _require_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise UniverseSpecError(f"{field_name} must be timezone-aware")


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, AssetClass):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    return value
