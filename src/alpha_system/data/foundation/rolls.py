"""Roll policy and roll calendar records for derived dated-contract rolls.

DATA-P13 owns local-only roll policy and calendar contracts. This module does
not stitch data, adjust prices, pull provider data, or describe execution
quality. Provider-continuous series remain separate from derived dated-contract
rolls.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from math import isfinite
from pathlib import Path
from types import MappingProxyType

from alpha_system.data.foundation.instruments import (
    FuturesContractRecord,
    load_futures_instrument_master_by_root,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError

REQUIRED_ROLL_POLICY_FIELDS: tuple[str, ...] = (
    "roll_policy_id",
    "method",
    "roll_trigger",
    "adjustment_method",
    "fallback_rule",
    "uses_volume",
    "uses_open_interest",
    "source",
)

REQUIRED_ROLL_CALENDAR_FIELDS: tuple[str, ...] = (
    "roll_calendar_id",
    "root_symbol",
    "from_contract",
    "to_contract",
    "roll_date",
    "method",
    "evidence",
    "validation_status",
)

KNOWN_ROLL_ROOTS: frozenset[str] = frozenset({"ES", "NQ", "RTY", "MES", "MNQ", "M2K"})

ROLL_METHODS: frozenset[str] = frozenset(
    {
        "calendar_days_before_expiration",
        "open_interest_crossover",
        "volume_crossover",
        "volume_open_interest_hybrid",
    }
)

ROLL_TRIGGERS: frozenset[str] = frozenset(
    {
        "calendar",
        "open_interest",
        "volume",
        "volume_open_interest_hybrid",
    }
)

ROLL_ADJUSTMENT_METHOD_NONE = "none"
ROLL_ADJUSTMENT_METHODS: frozenset[str] = frozenset(
    {
        ROLL_ADJUSTMENT_METHOD_NONE,
        "back_adjusted",
        "ratio_adjusted",
    }
)

ROLL_FALLBACK_RULES: frozenset[str] = frozenset(
    {
        "calendar_fallback_unvalidated",
        "manual_review_required",
        "no_roll_without_evidence",
    }
)

ROLL_VALIDATION_STATUSES: frozenset[str] = frozenset(
    {
        "discovered",
        "reconciled",
        "unvalidated",
    }
)

DERIVED_STITCHED_ROLL_PROVENANCE_LABEL = "derived_stitched_dated_contract_roll"
CME_EQUITY_INDEX_QUARTERLY_ROLL_POLICY_ID = "roll_cme_index_futures_quarterly"
CME_EQUITY_INDEX_QUARTERLY_ROLL_POLICY_SOURCE = (
    "dsrc_analytic_cme_index_quarterly_roll_approx_v1"
)
CME_EQUITY_INDEX_QUARTERLY_CYCLE_MONTHS: tuple[int, ...] = (3, 6, 9, 12)
CME_EQUITY_INDEX_QUARTERLY_ROLL_OFFSET_DAYS = 8
CME_EQUITY_INDEX_QUARTERLY_VALIDATION_STATUS = "unvalidated"
CME_EQUITY_INDEX_QUARTERLY_METHOD = "calendar_days_before_expiration"
CME_EQUITY_INDEX_QUARTERLY_ROLL_TRIGGER = "calendar"
CME_EQUITY_INDEX_QUARTERLY_EXPIRATION_RULE = "third_friday"

_ROLL_METHOD_TRIGGER_REQUIREMENTS: Mapping[str, str] = MappingProxyType(
    {
        "calendar_days_before_expiration": "calendar",
        "open_interest_crossover": "open_interest",
        "volume_crossover": "volume",
        "volume_open_interest_hybrid": "volume_open_interest_hybrid",
    }
)

_ROLL_TRIGGER_DATA_REQUIREMENTS: Mapping[str, tuple[bool, bool]] = MappingProxyType(
    {
        "calendar": (False, False),
        "open_interest": (False, True),
        "volume": (True, False),
        "volume_open_interest_hybrid": (True, True),
    }
)

_FORBIDDEN_ROLL_AFFORDANCE_FIELDS: frozenset[str] = frozenset(
    {
        "account",
        "best_execution",
        "best_execution_roll",
        "broker",
        "can_route_order",
        "can_trade",
        "execution",
        "execution_quality",
        "fill",
        "fills",
        "live",
        "order",
        "order_router",
        "order_timing",
        "orderable",
        "paper",
        "position",
        "positions",
        "slippage",
        "tradable",
        "tradeable",
    }
)

_FORBIDDEN_ROLL_VALUE_MARKERS: frozenset[str] = frozenset(
    {
        "best_execution",
        "broker",
        "can_route_order",
        "can_trade",
        "execution_optimal",
        "fill_quality",
        "live_trading",
        "order_timing",
        "orderable",
        "paper_trading",
        "slippage",
        "tradable",
        "tradeable",
    }
)

_PROVIDER_CONTINUOUS_MARKERS: frozenset[str] = frozenset(
    {
        "contfut",
        "continuous_as_dated_truth",
        "dated_truth",
        "provider_continuous",
    }
)

_SOURCE_FINALITY_MARKERS: frozenset[str] = frozenset(
    {
        "authoritative",
        "certified",
        "cme_final",
        "exchange_final",
        "final",
        "official",
        "official_final",
        "production",
    }
)


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        msg = f"{field_name} must be a non-empty string"
        raise DataFoundationValidationError(msg)
    normalized = value.strip()
    if not normalized:
        msg = f"{field_name} must be a non-empty string"
        raise DataFoundationValidationError(msg)
    return normalized


def _normalize_id(value: object, field_name: str) -> str:
    token = _require_text(value, field_name)
    if not token.replace("_", "").replace("-", "").isalnum():
        msg = f"{field_name} must be an alphanumeric identifier"
        raise DataFoundationValidationError(msg)
    return token


def _normalize_label(value: object, field_name: str) -> str:
    token = _require_text(value, field_name).lower().replace("-", "_").replace(" ", "_")
    if not token.replace("_", "").isalnum():
        msg = f"{field_name} contains invalid label token {value!r}"
        raise DataFoundationValidationError(msg)
    return token


def _normalize_free_text(value: str) -> str:
    return value.lower().replace("-", "_").replace(" ", "_")


def _require_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        msg = f"{field_name} must be a boolean"
        raise DataFoundationValidationError(msg)
    return value


def _parse_date(value: object, field_name: str) -> date:
    if isinstance(value, datetime):
        msg = f"{field_name} must be a calendar date, not a datetime"
        raise DataFoundationValidationError(msg)
    if isinstance(value, date):
        return value
    raw = _require_text(value, field_name)
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        msg = f"{field_name} must be an ISO-8601 date"
        raise DataFoundationValidationError(msg) from exc


def _normalize_root_symbol(value: object) -> str:
    root_symbol = _require_text(value, "root_symbol").upper()
    if root_symbol not in KNOWN_ROLL_ROOTS:
        allowed = ", ".join(sorted(KNOWN_ROLL_ROOTS))
        msg = f"root_symbol must be one of the supported mini/micro roots: {allowed}"
        raise DataFoundationValidationError(msg)
    if root_symbol not in load_futures_instrument_master_by_root():
        msg = f"root_symbol {root_symbol!r} is not in the futures instrument master"
        raise DataFoundationValidationError(msg)
    return root_symbol


def _normalize_roll_method(value: object) -> str:
    method = _normalize_label(value, "method")
    if method not in ROLL_METHODS:
        allowed = ", ".join(sorted(ROLL_METHODS))
        msg = f"method must be one of {allowed}"
        raise DataFoundationValidationError(msg)
    return method


def _normalize_roll_trigger(value: object) -> str:
    roll_trigger = _normalize_label(value, "roll_trigger")
    if roll_trigger not in ROLL_TRIGGERS:
        allowed = ", ".join(sorted(ROLL_TRIGGERS))
        msg = f"roll_trigger must be one of {allowed}"
        raise DataFoundationValidationError(msg)
    return roll_trigger


def _normalize_adjustment_method(value: object) -> str:
    adjustment_method = _normalize_label(value, "adjustment_method")
    if adjustment_method not in ROLL_ADJUSTMENT_METHODS:
        allowed = ", ".join(sorted(ROLL_ADJUSTMENT_METHODS))
        msg = f"adjustment_method must be one of {allowed}"
        raise DataFoundationValidationError(msg)
    return adjustment_method


def _normalize_fallback_rule(value: object) -> str:
    fallback_rule = _normalize_label(value, "fallback_rule")
    if fallback_rule not in ROLL_FALLBACK_RULES:
        allowed = ", ".join(sorted(ROLL_FALLBACK_RULES))
        msg = f"fallback_rule must be one of {allowed}"
        raise DataFoundationValidationError(msg)
    return fallback_rule


def _normalize_validation_status(value: object) -> str:
    validation_status = _normalize_label(value, "validation_status")
    if validation_status not in ROLL_VALIDATION_STATUSES:
        allowed = ", ".join(sorted(ROLL_VALIDATION_STATUSES))
        msg = f"validation_status must be one of {allowed}"
        raise DataFoundationValidationError(msg)
    return validation_status


def _require_policy_source(value: object) -> str:
    source = _require_text(value, "source")
    if not source.startswith("dsrc_"):
        msg = "source must be a DataSourceProfile-style source identifier with dsrc_ prefix"
        raise DataFoundationValidationError(msg)

    token = _normalize_free_text(source)
    if any(marker in token for marker in _PROVIDER_CONTINUOUS_MARKERS):
        msg = "source must not label a roll policy as provider-continuous or CONTFUT"
        raise DataFoundationValidationError(msg)
    if any(marker in token for marker in _SOURCE_FINALITY_MARKERS) and "reconciled" not in token:
        msg = "source must not claim exchange/CME finality unless reconciled"
        raise DataFoundationValidationError(msg)
    return source


def _contains_marker(value: object, markers: frozenset[str]) -> bool:
    if isinstance(value, Mapping):
        return any(
            _contains_marker(key, markers) or _contains_marker(nested_value, markers)
            for key, nested_value in value.items()
        )
    if isinstance(value, str):
        token = _normalize_free_text(value)
        return any(marker in token for marker in markers)
    if isinstance(value, Iterable):
        return any(_contains_marker(item, markers) for item in value)
    return False


def _reject_forbidden_mapping_fields(
    values: Mapping[str, object],
    record_name: str,
) -> None:
    forbidden = sorted(
        _normalize_label(key, f"{record_name} field")
        for key in values
        if _normalize_label(key, f"{record_name} field")
        in _FORBIDDEN_ROLL_AFFORDANCE_FIELDS
    )
    if forbidden:
        msg = f"{record_name} includes forbidden trading/order affordance fields: "
        raise DataFoundationValidationError(msg + ", ".join(forbidden))


def _reject_provider_continuous_markers(value: object, field_name: str) -> None:
    if _contains_marker(value, _PROVIDER_CONTINUOUS_MARKERS):
        msg = f"{field_name} must not label derived rolls as provider-continuous or CONTFUT"
        raise DataFoundationValidationError(msg)


def _reject_execution_quality_markers(value: object, field_name: str) -> None:
    if _contains_marker(value, _FORBIDDEN_ROLL_VALUE_MARKERS):
        msg = f"{field_name} must not imply execution quality, orderability, or tradability"
        raise DataFoundationValidationError(msg)


def _freeze_evidence_value(value: object, field_name: str) -> object:
    _reject_provider_continuous_markers(value, field_name)
    _reject_execution_quality_markers(value, field_name)
    if isinstance(value, Mapping):
        if not value:
            msg = f"{field_name} must not be an empty mapping"
            raise DataFoundationValidationError(msg)
        _reject_forbidden_mapping_fields(value, field_name)
        return MappingProxyType(
            {
                _require_text(key, f"{field_name} key"): _freeze_evidence_value(
                    nested_value,
                    f"{field_name}.{key}",
                )
                for key, nested_value in sorted(value.items(), key=lambda item: str(item[0]))
            }
        )
    if isinstance(value, list | tuple):
        return tuple(
            _freeze_evidence_value(item, f"{field_name}[]") for item in value
        )
    if isinstance(value, float):
        if not isfinite(value):
            msg = f"{field_name} must contain only finite JSON-stable numbers"
            raise DataFoundationValidationError(msg)
        return value
    if value is None or isinstance(value, bool | int | str):
        return value
    msg = f"{field_name} contains unsupported evidence value {type(value).__name__}"
    raise DataFoundationValidationError(msg)


def _normalize_evidence(value: object) -> Mapping[str, object]:
    if isinstance(value, str) or not isinstance(value, Mapping):
        msg = "evidence must be a non-empty mapping"
        raise DataFoundationValidationError(msg)
    return _freeze_evidence_value(value, "evidence")  # type: ignore[return-value]


def _coerce_contract_record(value: object, field_name: str) -> FuturesContractRecord:
    _reject_provider_continuous_markers(value, field_name)
    _reject_execution_quality_markers(value, field_name)
    if isinstance(value, FuturesContractRecord):
        return value
    if isinstance(value, Mapping):
        _reject_forbidden_mapping_fields(value, field_name)
        return FuturesContractRecord.from_mapping(value)
    msg = f"{field_name} must be a FuturesContractRecord or mapping"
    raise DataFoundationValidationError(msg)


def _coerce_roll_policy(value: object) -> RollPolicy:
    if isinstance(value, RollPolicy):
        return value
    if isinstance(value, Mapping):
        return RollPolicy.from_mapping(value)
    msg = "roll policy consistency requires a RollPolicy record or mapping"
    raise DataFoundationValidationError(msg)


def _validate_policy_trigger_usage(
    *,
    method: str,
    roll_trigger: str,
    uses_volume: bool,
    uses_open_interest: bool,
) -> None:
    required_trigger = _ROLL_METHOD_TRIGGER_REQUIREMENTS[method]
    if roll_trigger != required_trigger:
        msg = f"method {method!r} requires roll_trigger {required_trigger!r}"
        raise DataFoundationValidationError(msg)

    required_uses_volume, required_uses_open_interest = _ROLL_TRIGGER_DATA_REQUIREMENTS[
        roll_trigger
    ]
    if uses_volume != required_uses_volume:
        msg = f"roll_trigger {roll_trigger!r} requires uses_volume={required_uses_volume}"
        raise DataFoundationValidationError(msg)
    if uses_open_interest != required_uses_open_interest:
        msg = (
            f"roll_trigger {roll_trigger!r} requires "
            f"uses_open_interest={required_uses_open_interest}"
        )
        raise DataFoundationValidationError(msg)


@dataclass(frozen=True, slots=True)
class RollPolicy:
    """Validated policy for derived/stitched dated-contract roll selection.

    The policy records method, trigger, adjustment, fallback, and provenance.
    It is not a provider-continuous record and carries no execution-quality or
    orderability meaning.
    """

    roll_policy_id: str
    method: str
    roll_trigger: str
    adjustment_method: str
    fallback_rule: str
    uses_volume: bool
    uses_open_interest: bool
    source: str

    def __post_init__(self) -> None:
        roll_policy_id = _normalize_id(self.roll_policy_id, "roll_policy_id")
        method = _normalize_roll_method(self.method)
        roll_trigger = _normalize_roll_trigger(self.roll_trigger)
        adjustment_method = _normalize_adjustment_method(self.adjustment_method)
        fallback_rule = _normalize_fallback_rule(self.fallback_rule)
        uses_volume = _require_bool(self.uses_volume, "uses_volume")
        uses_open_interest = _require_bool(self.uses_open_interest, "uses_open_interest")
        source = _require_policy_source(self.source)

        _validate_policy_trigger_usage(
            method=method,
            roll_trigger=roll_trigger,
            uses_volume=uses_volume,
            uses_open_interest=uses_open_interest,
        )

        object.__setattr__(self, "roll_policy_id", roll_policy_id)
        object.__setattr__(self, "method", method)
        object.__setattr__(self, "roll_trigger", roll_trigger)
        object.__setattr__(self, "adjustment_method", adjustment_method)
        object.__setattr__(self, "fallback_rule", fallback_rule)
        object.__setattr__(self, "uses_volume", uses_volume)
        object.__setattr__(self, "uses_open_interest", uses_open_interest)
        object.__setattr__(self, "source", source)

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> RollPolicy:
        """Build a roll policy from persisted values and fail closed."""

        _reject_forbidden_mapping_fields(values, "RollPolicy")
        _reject_provider_continuous_markers(values, "RollPolicy")
        _reject_execution_quality_markers(values, "RollPolicy")
        missing = tuple(field for field in REQUIRED_ROLL_POLICY_FIELDS if field not in values)
        if missing:
            msg = "RollPolicy missing required fields: "
            raise DataFoundationValidationError(msg + ", ".join(missing))

        return cls(
            roll_policy_id=_require_text(values["roll_policy_id"], "roll_policy_id"),
            method=_require_text(values["method"], "method"),
            roll_trigger=_require_text(values["roll_trigger"], "roll_trigger"),
            adjustment_method=_require_text(
                values["adjustment_method"],
                "adjustment_method",
            ),
            fallback_rule=_require_text(values["fallback_rule"], "fallback_rule"),
            uses_volume=_require_bool(values["uses_volume"], "uses_volume"),
            uses_open_interest=_require_bool(
                values["uses_open_interest"],
                "uses_open_interest",
            ),
            source=_require_text(values["source"], "source"),
        )

    @property
    def adjusted_vs_unadjusted(self) -> str:
        """Return whether this policy leaves prices unadjusted or adjusted."""

        if self.adjustment_method == ROLL_ADJUSTMENT_METHOD_NONE:
            return "unadjusted"
        return "adjusted"

    @property
    def describes_provider_continuous(self) -> bool:
        """Return false: roll policies are for derived dated-contract rolls."""

        return False

    @property
    def implies_best_execution_roll(self) -> bool:
        """Return false: execution quality is outside roll policy scope."""

        return False

    @property
    def implies_tradability(self) -> bool:
        """Return false: a roll policy is not trading authorization."""

        return False

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable mapping for audits and docs generation."""

        return MappingProxyType(
            {
                "roll_policy_id": self.roll_policy_id,
                "method": self.method,
                "roll_trigger": self.roll_trigger,
                "adjustment_method": self.adjustment_method,
                "adjusted_vs_unadjusted": self.adjusted_vs_unadjusted,
                "fallback_rule": self.fallback_rule,
                "uses_volume": self.uses_volume,
                "uses_open_interest": self.uses_open_interest,
                "source": self.source,
            }
        )


@dataclass(frozen=True, slots=True)
class RollCalendarRecord:
    """Concrete roll-date transition between two dated futures contracts.

    The record binds an explicit roll date to two distinct
    ``FuturesContractRecord`` identities. It describes derived/stitched
    dated-contract roll metadata only.
    """

    roll_calendar_id: str
    root_symbol: str
    from_contract: FuturesContractRecord
    to_contract: FuturesContractRecord
    roll_date: date
    method: str
    evidence: Mapping[str, object]
    validation_status: str

    def __post_init__(self) -> None:
        roll_calendar_id = _normalize_id(self.roll_calendar_id, "roll_calendar_id")
        root_symbol = _normalize_root_symbol(self.root_symbol)
        from_contract = _coerce_contract_record(self.from_contract, "from_contract")
        to_contract = _coerce_contract_record(self.to_contract, "to_contract")
        roll_date = _parse_date(self.roll_date, "roll_date")
        method = _normalize_roll_method(self.method)
        evidence = _normalize_evidence(self.evidence)
        validation_status = _normalize_validation_status(self.validation_status)

        if from_contract.root_symbol != root_symbol or to_contract.root_symbol != root_symbol:
            msg = "from_contract and to_contract roots must match root_symbol"
            raise DataFoundationValidationError(msg)
        if from_contract.contract_id == to_contract.contract_id:
            msg = "from_contract and to_contract must be distinct dated-contract identities"
            raise DataFoundationValidationError(msg)
        if (
            from_contract.con_id is not None
            and to_contract.con_id is not None
            and from_contract.con_id == to_contract.con_id
        ):
            msg = "from_contract and to_contract must have distinct discovered con_id values"
            raise DataFoundationValidationError(msg)

        object.__setattr__(self, "roll_calendar_id", roll_calendar_id)
        object.__setattr__(self, "root_symbol", root_symbol)
        object.__setattr__(self, "from_contract", from_contract)
        object.__setattr__(self, "to_contract", to_contract)
        object.__setattr__(self, "roll_date", roll_date)
        object.__setattr__(self, "method", method)
        object.__setattr__(self, "evidence", evidence)
        object.__setattr__(self, "validation_status", validation_status)

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> RollCalendarRecord:
        """Build a roll calendar record and fail closed on required metadata."""

        _reject_forbidden_mapping_fields(values, "RollCalendarRecord")
        _reject_provider_continuous_markers(values, "RollCalendarRecord")
        _reject_execution_quality_markers(values, "RollCalendarRecord")
        missing = tuple(field for field in REQUIRED_ROLL_CALENDAR_FIELDS if field not in values)
        if missing:
            msg = "RollCalendarRecord missing required fields: "
            raise DataFoundationValidationError(msg + ", ".join(missing))

        return cls(
            roll_calendar_id=_require_text(
                values["roll_calendar_id"],
                "roll_calendar_id",
            ),
            root_symbol=_require_text(values["root_symbol"], "root_symbol"),
            from_contract=_coerce_contract_record(
                values["from_contract"],
                "from_contract",
            ),
            to_contract=_coerce_contract_record(values["to_contract"], "to_contract"),
            roll_date=_parse_date(values["roll_date"], "roll_date"),
            method=_require_text(values["method"], "method"),
            evidence=_normalize_evidence(values["evidence"]),
            validation_status=_require_text(
                values["validation_status"],
                "validation_status",
            ),
        )

    @property
    def from_contract_id(self) -> str:
        """Return the source dated-contract identity."""

        return self.from_contract.contract_id

    @property
    def to_contract_id(self) -> str:
        """Return the destination dated-contract identity."""

        return self.to_contract.contract_id

    @property
    def provenance_label(self) -> str:
        """Return the derived dated-contract roll provenance label."""

        return DERIVED_STITCHED_ROLL_PROVENANCE_LABEL

    @property
    def describes_provider_continuous(self) -> bool:
        """Return false: this is not a provider-continuous or CONTFUT record."""

        return False

    @property
    def implies_provider_continuous_dated_truth(self) -> bool:
        """Return false: provider-continuous history is never dated-contract truth."""

        return False

    @property
    def implies_best_execution_roll(self) -> bool:
        """Return false: roll execution quality is outside this record."""

        return False

    @property
    def implies_tradability(self) -> bool:
        """Return false: a roll calendar is not trading authorization."""

        return False

    def validate_against_policy(
        self,
        policy: RollPolicy | Mapping[str, object],
    ) -> RollCalendarRecord:
        """Return this record if its method matches a concrete ``RollPolicy``."""

        roll_policy = _coerce_roll_policy(policy)
        if self.method != roll_policy.method:
            msg = "RollCalendarRecord method must match RollPolicy.method"
            raise DataFoundationValidationError(msg)
        return self

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable mapping for audits and handoffs."""

        return MappingProxyType(
            {
                "roll_calendar_id": self.roll_calendar_id,
                "root_symbol": self.root_symbol,
                "from_contract": self.from_contract.to_mapping(),
                "to_contract": self.to_contract.to_mapping(),
                "roll_date": self.roll_date.isoformat(),
                "method": self.method,
                "evidence": self.evidence,
                "validation_status": self.validation_status,
                "provenance_label": self.provenance_label,
            }
        )


def build_cme_equity_index_quarterly_roll_policy() -> RollPolicy:
    """Return the stable analytic CME equity-index quarterly roll policy."""

    return RollPolicy(
        roll_policy_id=CME_EQUITY_INDEX_QUARTERLY_ROLL_POLICY_ID,
        method=CME_EQUITY_INDEX_QUARTERLY_METHOD,
        roll_trigger=CME_EQUITY_INDEX_QUARTERLY_ROLL_TRIGGER,
        adjustment_method=ROLL_ADJUSTMENT_METHOD_NONE,
        fallback_rule="calendar_fallback_unvalidated",
        uses_volume=False,
        uses_open_interest=False,
        source=CME_EQUITY_INDEX_QUARTERLY_ROLL_POLICY_SOURCE,
    )


def third_friday(year: int, month: int) -> date:
    """Return the third Friday for a concrete calendar month."""

    _validate_year_month(year, month)
    first_day = date(year, month, 1)
    days_to_friday = (4 - first_day.weekday()) % 7
    return first_day + timedelta(days=days_to_friday + 14)


def cme_equity_index_quarterly_roll_date(
    *,
    year: int,
    month: int,
    roll_offset_days: int = CME_EQUITY_INDEX_QUARTERLY_ROLL_OFFSET_DAYS,
) -> date:
    """Return the approximate calendar roll date for one quarterly expiry."""

    if roll_offset_days < 0:
        msg = "roll_offset_days must be non-negative"
        raise DataFoundationValidationError(msg)
    if month not in CME_EQUITY_INDEX_QUARTERLY_CYCLE_MONTHS:
        allowed = ", ".join(
            str(cycle_month) for cycle_month in CME_EQUITY_INDEX_QUARTERLY_CYCLE_MONTHS
        )
        msg = f"month must be one of the quarterly cycle months: {allowed}"
        raise DataFoundationValidationError(msg)
    return third_friday(year, month) - timedelta(days=roll_offset_days)


def build_cme_equity_index_quarterly_contract(
    *,
    root_symbol: str,
    year: int,
    month: int,
) -> FuturesContractRecord:
    """Build a synthetic dated-contract identity for analytic roll metadata."""

    _validate_year_month(year, month)
    root = _normalize_root_symbol(root_symbol)
    master = load_futures_instrument_master_by_root()[root]
    expiration = third_friday(year, month)
    contract_month = f"{year:04d}-{month:02d}"
    contract_token = f"{year:04d}{month:02d}"
    return FuturesContractRecord(
        contract_id=f"contract_cme_analytic_{root.lower()}_{contract_token}",
        root_symbol=root,
        contract_month=contract_month,
        ib_symbol=master.ib_symbol,
        trading_class=master.ib_symbol,
        con_id=None,
        last_trade_date_or_contract_month=expiration.isoformat(),
        expiration=expiration,
        multiplier=master.multiplier,
        exchange=master.exchange,
        currency=master.currency,
        include_expired_support_status="not_checked",
    )


def build_analytic_cme_equity_index_quarterly_roll_calendar(
    *,
    root_symbols: Iterable[str] = ("ES", "NQ", "RTY"),
    start_year: int = 2018,
    end_year: int = 2026,
    roll_offset_days: int = CME_EQUITY_INDEX_QUARTERLY_ROLL_OFFSET_DAYS,
) -> tuple[RollCalendarRecord, ...]:
    """Build approximate ES/NQ/RTY quarterly roll records for a year range.

    The dates use the documented analytic heuristic only: quarterly cycle month,
    third-Friday expiration, and a calendar-day offset. The result is explicitly
    unvalidated and is not provider-exact splice truth.
    """

    if end_year < start_year:
        msg = "end_year must be greater than or equal to start_year"
        raise DataFoundationValidationError(msg)

    records: list[RollCalendarRecord] = []
    for raw_root in root_symbols:
        root = _normalize_root_symbol(raw_root)
        for year in range(start_year, end_year + 1):
            for month in CME_EQUITY_INDEX_QUARTERLY_CYCLE_MONTHS:
                next_year, next_month = _next_quarterly_cycle_month(year, month)
                roll_date = cme_equity_index_quarterly_roll_date(
                    year=year,
                    month=month,
                    roll_offset_days=roll_offset_days,
                )
                from_contract = build_cme_equity_index_quarterly_contract(
                    root_symbol=root,
                    year=year,
                    month=month,
                )
                to_contract = build_cme_equity_index_quarterly_contract(
                    root_symbol=root,
                    year=next_year,
                    month=next_month,
                )
                records.append(
                    RollCalendarRecord(
                        roll_calendar_id=(
                            "rollcal_cme_index_quarterly_"
                            f"{root.lower()}_{year:04d}{month:02d}_to_"
                            f"{next_year:04d}{next_month:02d}_approx_v1"
                        ),
                        root_symbol=root,
                        from_contract=from_contract,
                        to_contract=to_contract,
                        roll_date=roll_date,
                        method=CME_EQUITY_INDEX_QUARTERLY_METHOD,
                        evidence={
                            "source": "analytic_cme_equity_index_quarterly_heuristic",
                            "approximate": True,
                            "provider_exact_splice": False,
                            "reconciled_to_provider": False,
                            "cycle_months": CME_EQUITY_INDEX_QUARTERLY_CYCLE_MONTHS,
                            "expiration_rule": CME_EQUITY_INDEX_QUARTERLY_EXPIRATION_RULE,
                            "roll_offset_days_before_expiration": roll_offset_days,
                            "provenance": DERIVED_STITCHED_ROLL_PROVENANCE_LABEL,
                        },
                        validation_status=CME_EQUITY_INDEX_QUARTERLY_VALIDATION_STATUS,
                    )
                )

    return tuple(
        sorted(records, key=lambda record: (record.root_symbol, record.roll_date))
    )


def persist_roll_calendar_records_jsonl(
    records: Iterable[RollCalendarRecord | Mapping[str, object]],
    path: str | Path,
) -> Path:
    """Persist roll records as JSONL for local-only audit or registry loaders."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    normalized_records = tuple(
        record
        if isinstance(record, RollCalendarRecord)
        else RollCalendarRecord.from_mapping(record)
        for record in records
    )
    with output_path.open("w", encoding="utf-8") as handle:
        for record in normalized_records:
            payload = _json_stable_roll_value(record.to_mapping())
            encoded = json.dumps(
                payload,
                allow_nan=False,
                ensure_ascii=True,
                separators=(",", ":"),
                sort_keys=True,
            )
            handle.write(encoded + "\n")
    return output_path


def require_roll_calendar_matches_policy(
    calendar: RollCalendarRecord | Mapping[str, object],
    policy: RollPolicy | Mapping[str, object],
) -> RollCalendarRecord:
    """Return a roll calendar record only when it matches the policy method."""

    roll_calendar = (
        calendar
        if isinstance(calendar, RollCalendarRecord)
        else RollCalendarRecord.from_mapping(calendar)
    )
    return roll_calendar.validate_against_policy(policy)


def _validate_year_month(year: int, month: int) -> None:
    if isinstance(year, bool) or isinstance(month, bool):
        msg = "year and month must be integers"
        raise DataFoundationValidationError(msg)
    if not isinstance(year, int) or not isinstance(month, int):
        msg = "year and month must be integers"
        raise DataFoundationValidationError(msg)
    try:
        date(year, month, 1)
    except ValueError as exc:
        msg = "year and month must form a valid calendar month"
        raise DataFoundationValidationError(msg) from exc


def _next_quarterly_cycle_month(year: int, month: int) -> tuple[int, int]:
    if month not in CME_EQUITY_INDEX_QUARTERLY_CYCLE_MONTHS:
        allowed = ", ".join(
            str(cycle_month) for cycle_month in CME_EQUITY_INDEX_QUARTERLY_CYCLE_MONTHS
        )
        msg = f"month must be one of the quarterly cycle months: {allowed}"
        raise DataFoundationValidationError(msg)
    index = CME_EQUITY_INDEX_QUARTERLY_CYCLE_MONTHS.index(month)
    next_index = (index + 1) % len(CME_EQUITY_INDEX_QUARTERLY_CYCLE_MONTHS)
    next_year = year + 1 if next_index == 0 else year
    return next_year, CME_EQUITY_INDEX_QUARTERLY_CYCLE_MONTHS[next_index]


def _json_stable_roll_value(value: object) -> object:
    if isinstance(value, Mapping):
        return {
            str(key): _json_stable_roll_value(nested_value)
            for key, nested_value in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, tuple | list):
        return [_json_stable_roll_value(item) for item in value]
    if isinstance(value, date):
        return value.isoformat()
    if value is None or isinstance(value, bool | int | float | str):
        return value
    msg = f"roll calendar value {value!r} is not JSON-stable"
    raise DataFoundationValidationError(msg)


__all__ = [
    "CME_EQUITY_INDEX_QUARTERLY_CYCLE_MONTHS",
    "CME_EQUITY_INDEX_QUARTERLY_EXPIRATION_RULE",
    "CME_EQUITY_INDEX_QUARTERLY_METHOD",
    "CME_EQUITY_INDEX_QUARTERLY_ROLL_OFFSET_DAYS",
    "CME_EQUITY_INDEX_QUARTERLY_ROLL_POLICY_ID",
    "CME_EQUITY_INDEX_QUARTERLY_ROLL_POLICY_SOURCE",
    "CME_EQUITY_INDEX_QUARTERLY_ROLL_TRIGGER",
    "CME_EQUITY_INDEX_QUARTERLY_VALIDATION_STATUS",
    "DERIVED_STITCHED_ROLL_PROVENANCE_LABEL",
    "KNOWN_ROLL_ROOTS",
    "REQUIRED_ROLL_CALENDAR_FIELDS",
    "REQUIRED_ROLL_POLICY_FIELDS",
    "ROLL_ADJUSTMENT_METHOD_NONE",
    "ROLL_ADJUSTMENT_METHODS",
    "ROLL_FALLBACK_RULES",
    "ROLL_METHODS",
    "ROLL_TRIGGERS",
    "ROLL_VALIDATION_STATUSES",
    "RollCalendarRecord",
    "RollPolicy",
    "build_analytic_cme_equity_index_quarterly_roll_calendar",
    "build_cme_equity_index_quarterly_contract",
    "build_cme_equity_index_quarterly_roll_policy",
    "cme_equity_index_quarterly_roll_date",
    "persist_roll_calendar_records_jsonl",
    "require_roll_calendar_matches_policy",
    "third_friday",
]
