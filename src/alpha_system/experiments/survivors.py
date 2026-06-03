"""Survivor record schema and loading for management-grid entry."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


class SurvivorSchemaError(ValueError):
    """Raised when a survivor record is incomplete or malformed."""


SURVIVOR_REQUIRED_FIELDS: tuple[str, ...] = (
    "candidate_id",
    "source_run_id",
    "factor_versions",
    "label_versions",
    "strategy_version",
    "baseline_management_config",
    "baseline_portfolio_config",
    "source_grid_config_hash",
    "survivor_eligibility_reason",
    "warnings",
    "review_status",
    "allowed_management_grid_scope",
)

SURVIVOR_FIELD_ALIASES: Mapping[str, str] = {
    "candidate id": "candidate_id",
    "source run id": "source_run_id",
    "factor versions": "factor_versions",
    "label versions": "label_versions",
    "strategy version": "strategy_version",
    "baseline management config": "baseline_management_config",
    "baseline portfolio config": "baseline_portfolio_config",
    "source grid config hash": "source_grid_config_hash",
    "reason for survivor eligibility": "survivor_eligibility_reason",
    "reason_for_survivor_eligibility": "survivor_eligibility_reason",
    "review status": "review_status",
    "allowed management grid scope": "allowed_management_grid_scope",
}

VALID_REVIEW_STATUSES: tuple[str, ...] = (
    "PASS",
    "PASS_WITH_WARNINGS",
    "REVIEWED",
    "REVIEWED_WITH_WARNINGS",
    "ELIGIBLE_FOR_MANAGEMENT_GRID",
)


@dataclass(frozen=True, slots=True)
class SurvivorRecord:
    """One reviewed candidate allowed to request management-grid evaluation."""

    candidate_id: str
    source_run_id: str
    factor_versions: Mapping[str, str]
    label_versions: Mapping[str, str]
    strategy_version: str
    baseline_management_config: Mapping[str, Any]
    baseline_portfolio_config: Mapping[str, Any]
    source_grid_config_hash: str
    survivor_eligibility_reason: str
    warnings: tuple[str, ...]
    review_status: str
    allowed_management_grid_scope: Mapping[str, Any]

    @classmethod
    def required_fields(cls) -> tuple[str, ...]:
        """Return the canonical required survivor fields."""
        return SURVIVOR_REQUIRED_FIELDS

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "SurvivorRecord":
        """Build a survivor record from canonical or human-readable keys."""
        normalized = _normalize_keys(payload)
        missing = tuple(field for field in SURVIVOR_REQUIRED_FIELDS if field not in normalized)
        if missing:
            msg = f"survivor record missing required fields: {', '.join(missing)}"
            raise SurvivorSchemaError(msg)

        return cls(
            candidate_id=_text(normalized["candidate_id"], "candidate_id"),
            source_run_id=_text(normalized["source_run_id"], "source_run_id"),
            factor_versions=_version_map(normalized["factor_versions"], "factor_versions", allow_empty=False),
            label_versions=_version_map(normalized["label_versions"], "label_versions", allow_empty=True),
            strategy_version=_text(normalized["strategy_version"], "strategy_version"),
            baseline_management_config=_non_empty_mapping(
                normalized["baseline_management_config"],
                "baseline_management_config",
            ),
            baseline_portfolio_config=_non_empty_mapping(
                normalized["baseline_portfolio_config"],
                "baseline_portfolio_config",
            ),
            source_grid_config_hash=_text(normalized["source_grid_config_hash"], "source_grid_config_hash"),
            survivor_eligibility_reason=_text(
                normalized["survivor_eligibility_reason"],
                "survivor_eligibility_reason",
            ),
            warnings=_warning_tuple(normalized["warnings"]),
            review_status=_review_status(normalized["review_status"]),
            allowed_management_grid_scope=_scope(normalized["allowed_management_grid_scope"]),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-ready survivor payload."""
        payload = asdict(self)
        payload["factor_versions"] = dict(self.factor_versions)
        payload["label_versions"] = dict(self.label_versions)
        payload["baseline_management_config"] = dict(self.baseline_management_config)
        payload["baseline_portfolio_config"] = dict(self.baseline_portfolio_config)
        payload["warnings"] = list(self.warnings)
        payload["allowed_management_grid_scope"] = dict(self.allowed_management_grid_scope)
        return payload


def load_survivor_records(path: str | Path) -> tuple[SurvivorRecord, ...]:
    """Load a survivor set from a JSON file."""
    payload = json.loads(Path(path).expanduser().resolve(strict=False).read_text(encoding="utf-8"))
    return survivor_records_from_payload(payload)


def survivor_records_from_payload(payload: Any) -> tuple[SurvivorRecord, ...]:
    """Build survivor records from a list or ``{"survivors": [...]}`` payload."""
    records_payload = payload.get("survivors") if isinstance(payload, Mapping) else payload
    if not isinstance(records_payload, Sequence) or isinstance(records_payload, str | bytes):
        msg = "survivor set must be a list or an object with a survivors list"
        raise SurvivorSchemaError(msg)
    records = tuple(SurvivorRecord.from_mapping(_mapping(item, "survivor record")) for item in records_payload)
    if not records:
        raise SurvivorSchemaError("survivor set must contain at least one record")
    candidate_ids = [record.candidate_id for record in records]
    duplicates = sorted({candidate_id for candidate_id in candidate_ids if candidate_ids.count(candidate_id) > 1})
    if duplicates:
        msg = f"survivor set contains duplicate candidate_id values: {', '.join(duplicates)}"
        raise SurvivorSchemaError(msg)
    return records


def select_survivor(records: Sequence[SurvivorRecord], candidate_id: str | None = None) -> SurvivorRecord:
    """Select one survivor by id, or the only record when unambiguous."""
    if candidate_id is None:
        if len(records) != 1:
            raise SurvivorSchemaError("candidate_id is required when multiple survivor records are present")
        return records[0]
    for record in records:
        if record.candidate_id == candidate_id:
            return record
    raise SurvivorSchemaError(f"candidate_id {candidate_id!r} was not found in survivor records")


def _normalize_keys(payload: Mapping[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in payload.items():
        active_key = SURVIVOR_FIELD_ALIASES.get(str(key), str(key))
        normalized[active_key] = value
    return normalized


def _version_map(value: Any, field_name: str, *, allow_empty: bool) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise SurvivorSchemaError(f"{field_name} must be a mapping")
    if not value and not allow_empty:
        raise SurvivorSchemaError(f"{field_name} must contain at least one version")
    return {_text(key, f"{field_name} key"): _text(version, f"{field_name} value") for key, version in value.items()}


def _non_empty_mapping(value: Any, field_name: str) -> dict[str, Any]:
    active = dict(_mapping(value, field_name))
    if not active:
        raise SurvivorSchemaError(f"{field_name} must be a non-empty mapping")
    return active


def _scope(value: Any) -> dict[str, Any]:
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        value = {"management_parameters": list(value)}
    active = dict(_mapping(value, "allowed_management_grid_scope"))
    if not active:
        raise SurvivorSchemaError("allowed_management_grid_scope must be a non-empty mapping")
    return active


def _warning_tuple(value: Any) -> tuple[str, ...]:
    if value in (None, ""):
        return ()
    if isinstance(value, str):
        return (_text(value, "warnings"),)
    if not isinstance(value, Sequence):
        raise SurvivorSchemaError("warnings must be a string or list of strings")
    return tuple(_text(item, "warnings") for item in value)


def _review_status(value: Any) -> str:
    status = _text(value, "review_status").upper()
    if status not in VALID_REVIEW_STATUSES:
        msg = f"review_status must be one of: {', '.join(VALID_REVIEW_STATUSES)}"
        raise SurvivorSchemaError(msg)
    return status


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SurvivorSchemaError(f"{field_name} must be a non-empty string")
    return value.strip()


def _mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SurvivorSchemaError(f"{field_name} must be a mapping")
    return value
