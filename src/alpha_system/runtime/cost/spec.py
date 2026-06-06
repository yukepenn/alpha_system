"""Cost-stress specification and configuration parsing."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from alpha_system.runtime.cost.model_version import CostModelVersion

DEFAULT_PROFILE_ORDER = ("base", "stress_1", "stress_2", "double_cost")
DEFAULT_SESSION_PENALTY_CONFIG_ID = "runtime_cost_stress_default_v1"
ZERO = Decimal("0")


class CostStressSpecError(ValueError):
    """Raised when cost stress would omit a required fail-closed invariant."""


@dataclass(frozen=True, slots=True)
class CostStressProfile:
    """One ordered cost-stress profile with explicit multipliers."""

    name: str
    cost_multiplier: Decimal
    slippage_multiplier: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _required_text(self.name, field="profile.name"))
        object.__setattr__(
            self,
            "cost_multiplier",
            _positive_decimal(self.cost_multiplier, field=f"{self.name}.cost_multiplier"),
        )
        object.__setattr__(
            self,
            "slippage_multiplier",
            _positive_decimal(
                self.slippage_multiplier,
                field=f"{self.name}.slippage_multiplier",
            ),
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> CostStressProfile:
        """Build a profile from a JSON-compatible config mapping."""

        _reject_extra_keys(
            value,
            allowed={"name", "cost_multiplier", "slippage_multiplier"},
            field="profile",
        )
        return cls(
            name=value.get("name"),
            cost_multiplier=_decimal(value.get("cost_multiplier"), field="cost_multiplier"),
            slippage_multiplier=_decimal(
                value.get("slippage_multiplier"),
                field="slippage_multiplier",
            ),
        )

    def to_dict(self) -> dict[str, str]:
        """Return a stable profile payload."""

        return {
            "name": self.name,
            "cost_multiplier": _decimal_text(self.cost_multiplier),
            "slippage_multiplier": _decimal_text(self.slippage_multiplier),
        }


@dataclass(frozen=True, slots=True)
class SessionCostPenalty:
    """Configured session multiplier applied after primitive cost/slippage results."""

    session_label: str
    cost_multiplier: Decimal
    slippage_multiplier: Decimal

    def __post_init__(self) -> None:
        label = _required_text(self.session_label, field="session_label").upper()
        object.__setattr__(self, "session_label", label)
        object.__setattr__(
            self,
            "cost_multiplier",
            _positive_decimal(self.cost_multiplier, field=f"{label}.cost_multiplier"),
        )
        object.__setattr__(
            self,
            "slippage_multiplier",
            _positive_decimal(
                self.slippage_multiplier,
                field=f"{label}.slippage_multiplier",
            ),
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> SessionCostPenalty:
        """Build a session penalty from a JSON-compatible config mapping."""

        _reject_extra_keys(
            value,
            allowed={"session_label", "cost_multiplier", "slippage_multiplier"},
            field="session_penalty",
        )
        return cls(
            session_label=value.get("session_label"),
            cost_multiplier=_decimal(value.get("cost_multiplier"), field="cost_multiplier"),
            slippage_multiplier=_decimal(
                value.get("slippage_multiplier"),
                field="slippage_multiplier",
            ),
        )

    def to_dict(self) -> dict[str, str]:
        """Return a stable session-penalty payload."""

        return {
            "session_label": self.session_label,
            "cost_multiplier": _decimal_text(self.cost_multiplier),
            "slippage_multiplier": _decimal_text(self.slippage_multiplier),
        }


@dataclass(frozen=True, slots=True)
class CostStressSpec:
    """Bounded cost-stress run spec tied to a CostModelVersion."""

    cost_model_version: CostModelVersion
    profiles: tuple[CostStressProfile, ...] = ()
    session_penalty_config_id: str = DEFAULT_SESSION_PENALTY_CONFIG_ID
    session_penalties: tuple[SessionCostPenalty, ...] = ()
    requires_double_cost: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.cost_model_version, CostModelVersion):
            raise CostStressSpecError("cost_model_version must be a CostModelVersion")
        if self.requires_double_cost is not True:
            raise CostStressSpecError("requires_double_cost must be true")

        profiles = self.profiles or default_cost_stress_profiles()
        penalties = self.session_penalties or default_session_penalties()
        object.__setattr__(self, "profiles", tuple(_coerce_profile(item) for item in profiles))
        object.__setattr__(
            self,
            "session_penalty_config_id",
            _required_text(
                self.session_penalty_config_id,
                field="session_penalty_config_id",
            ),
        )
        object.__setattr__(
            self,
            "session_penalties",
            tuple(_coerce_session_penalty(item) for item in penalties),
        )
        _validate_profiles(self.profiles)
        _validate_session_penalties(self.session_penalties)

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, Any],
        *,
        cost_model_version: CostModelVersion,
    ) -> CostStressSpec:
        """Build a spec from config data and an already-recorded cost version."""

        _reject_extra_keys(
            value,
            allowed={
                "config_id",
                "description",
                "profiles",
                "session_penalties",
                "requires_double_cost",
            },
            field="cost_stress_config",
        )
        profiles = tuple(
            CostStressProfile.from_mapping(item)
            for item in _mapping_sequence(value.get("profiles"), field="profiles")
        )
        penalties = tuple(
            SessionCostPenalty.from_mapping(item)
            for item in _mapping_sequence(
                value.get("session_penalties"),
                field="session_penalties",
            )
        )
        return cls(
            cost_model_version=cost_model_version,
            profiles=profiles,
            session_penalty_config_id=str(
                value.get("config_id", DEFAULT_SESSION_PENALTY_CONFIG_ID)
            ),
            session_penalties=penalties,
            requires_double_cost=bool(value.get("requires_double_cost", True)),
        )

    @property
    def profile_names(self) -> tuple[str, ...]:
        """Return the ordered profile names."""

        return tuple(profile.name for profile in self.profiles)

    @property
    def profile_by_name(self) -> dict[str, CostStressProfile]:
        """Return profiles keyed by name."""

        return {profile.name: profile for profile in self.profiles}

    def penalty_for(self, session_label: str) -> SessionCostPenalty:
        """Return the configured penalty for a session label."""

        label = _required_text(session_label, field="session_label").upper()
        penalties = {penalty.session_label: penalty for penalty in self.session_penalties}
        if label in penalties:
            return penalties[label]
        if label in {"ETH", "ILLIQUID"} and label in penalties:
            return penalties[label]
        if "ETH" in penalties:
            return penalties["ETH"]
        return penalties["RTH"]

    def to_dict(self) -> dict[str, object]:
        """Return a stable cost-stress spec payload."""

        return {
            "cost_model_version_id": self.cost_model_version.cost_model_version_id,
            "profiles": [profile.to_dict() for profile in self.profiles],
            "session_penalty_config_id": self.session_penalty_config_id,
            "session_penalties": [penalty.to_dict() for penalty in self.session_penalties],
            "requires_double_cost": self.requires_double_cost,
            "slippage_is_proxy": self.cost_model_version.slippage_is_proxy,
        }


def default_cost_stress_profiles() -> tuple[CostStressProfile, ...]:
    """Return the required ordered base/stress/double-cost profile set."""

    return (
        CostStressProfile("base", Decimal("1.0"), Decimal("1.0")),
        CostStressProfile("stress_1", Decimal("1.25"), Decimal("1.25")),
        CostStressProfile("stress_2", Decimal("1.5"), Decimal("1.5")),
        CostStressProfile("double_cost", Decimal("2.0"), Decimal("2.0")),
    )


def default_session_penalties() -> tuple[SessionCostPenalty, ...]:
    """Return the conservative sample session-penalty defaults."""

    return (
        SessionCostPenalty("RTH", Decimal("1.0"), Decimal("1.0")),
        SessionCostPenalty("ETH", Decimal("1.5"), Decimal("1.5")),
        SessionCostPenalty("ILLIQUID", Decimal("2.0"), Decimal("2.0")),
    )


def load_cost_stress_config(path: str | Path) -> dict[str, Any]:
    """Load JSON cost-stress config data."""

    active_path = Path(path)
    with active_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise CostStressSpecError("cost stress config must contain a mapping")
    return payload


def _validate_profiles(profiles: tuple[CostStressProfile, ...]) -> None:
    names = tuple(profile.name for profile in profiles)
    if "double_cost" not in names:
        raise CostStressSpecError("double_cost profile is required")
    if names != DEFAULT_PROFILE_ORDER:
        raise CostStressSpecError(
            "profiles must be ordered exactly as base, stress_1, stress_2, double_cost"
        )
    for previous, current in zip(profiles, profiles[1:]):
        if current.cost_multiplier < previous.cost_multiplier:
            raise CostStressSpecError("profile cost multipliers must be nondecreasing")
        if current.slippage_multiplier < previous.slippage_multiplier:
            raise CostStressSpecError("profile slippage multipliers must be nondecreasing")
    double_cost = profiles[-1]
    if double_cost.cost_multiplier < Decimal("2.0"):
        raise CostStressSpecError("double_cost cost multiplier must be at least 2.0")
    if double_cost.slippage_multiplier < Decimal("2.0"):
        raise CostStressSpecError("double_cost slippage multiplier must be at least 2.0")


def _validate_session_penalties(penalties: tuple[SessionCostPenalty, ...]) -> None:
    labels = tuple(penalty.session_label for penalty in penalties)
    if len(set(labels)) != len(labels):
        raise CostStressSpecError("session penalties must not contain duplicate labels")
    by_label = {penalty.session_label: penalty for penalty in penalties}
    if "RTH" not in by_label or "ETH" not in by_label:
        raise CostStressSpecError("session penalties must include RTH and ETH")
    if by_label["ETH"].cost_multiplier < by_label["RTH"].cost_multiplier:
        raise CostStressSpecError("ETH cost penalty must be at least RTH")
    if by_label["ETH"].slippage_multiplier < by_label["RTH"].slippage_multiplier:
        raise CostStressSpecError("ETH slippage penalty must be at least RTH")
    if "ILLIQUID" in by_label:
        if by_label["ILLIQUID"].cost_multiplier < by_label["RTH"].cost_multiplier:
            raise CostStressSpecError("ILLIQUID cost penalty must be at least RTH")
        if by_label["ILLIQUID"].slippage_multiplier < by_label["RTH"].slippage_multiplier:
            raise CostStressSpecError("ILLIQUID slippage penalty must be at least RTH")


def _coerce_profile(value: CostStressProfile | Mapping[str, Any]) -> CostStressProfile:
    if isinstance(value, CostStressProfile):
        return value
    if not isinstance(value, Mapping):
        raise CostStressSpecError("profile must be CostStressProfile or mapping")
    return CostStressProfile.from_mapping(value)


def _coerce_session_penalty(
    value: SessionCostPenalty | Mapping[str, Any],
) -> SessionCostPenalty:
    if isinstance(value, SessionCostPenalty):
        return value
    if not isinstance(value, Mapping):
        raise CostStressSpecError("session penalty must be SessionCostPenalty or mapping")
    return SessionCostPenalty.from_mapping(value)


def _mapping_sequence(value: Any, *, field: str) -> tuple[Mapping[str, Any], ...]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise CostStressSpecError(f"{field} must be a sequence of mappings")
    if not value:
        raise CostStressSpecError(f"{field} must not be empty")
    if not all(isinstance(item, Mapping) for item in value):
        raise CostStressSpecError(f"{field} must contain only mappings")
    return tuple(value)


def _reject_extra_keys(value: Mapping[str, Any], *, allowed: set[str], field: str) -> None:
    extra = set(value) - allowed
    if extra:
        raise CostStressSpecError(
            f"{field} contains unsupported fields: {', '.join(sorted(extra))}"
        )


def _required_text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CostStressSpecError(f"{field} is required")
    return value.strip()


def _decimal(value: object, *, field: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise CostStressSpecError(f"{field} must be numeric")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise CostStressSpecError(f"{field} must be numeric") from exc


def _positive_decimal(value: object, *, field: str) -> Decimal:
    active = _decimal(value, field=field)
    if active <= ZERO:
        raise CostStressSpecError(f"{field} must be positive")
    return active


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")


__all__ = [
    "DEFAULT_PROFILE_ORDER",
    "CostStressProfile",
    "CostStressSpec",
    "CostStressSpecError",
    "SessionCostPenalty",
    "default_cost_stress_profiles",
    "default_session_penalties",
    "load_cost_stress_config",
]
