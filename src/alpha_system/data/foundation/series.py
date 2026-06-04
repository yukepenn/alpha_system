"""Continuous and dated futures series provenance records.

DATA-P11 owns provenance-rich series behavior. DATA-P13 owns future roll
policy/calendar definitions and any roll or stitching computation.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType

from alpha_system.data.foundation.instruments import (
    FuturesContractRecord,
    load_futures_instrument_master_by_root,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError

REQUIRED_CONTINUOUS_FUTURES_SERIES_FIELDS: tuple[str, ...] = (
    "series_id",
    "root_symbol",
    "provider",
    "provenance_label",
    "orderable",
    "dated_truth",
    "roll_adjustment_note",
    "source_retrieved_at",
)

REQUIRED_DATED_FUTURES_SERIES_FIELDS: tuple[str, ...] = (
    "series_id",
    "root_symbol",
    "contract_universe",
    "roll_policy_id",
    "adjustment_method",
    "availability_window",
    "validation_status",
)

PROVIDER_CONTINUOUS_PROVENANCE_LABEL = "provider_continuous"
DATED_CONTRACT_PROVENANCE_LABEL = "dated_contract"
CANONICAL_STITCHED_PROVENANCE_LABEL = "canonical_stitched"
ROLL_ADJUSTED_PROVENANCE_LABEL = "roll_adjusted"
UNADJUSTED_PROVENANCE_LABEL = "unadjusted"

SERIES_PROVENANCE_KINDS: frozenset[str] = frozenset(
    {
        PROVIDER_CONTINUOUS_PROVENANCE_LABEL,
        DATED_CONTRACT_PROVENANCE_LABEL,
        CANONICAL_STITCHED_PROVENANCE_LABEL,
        ROLL_ADJUSTED_PROVENANCE_LABEL,
        UNADJUSTED_PROVENANCE_LABEL,
    }
)

CONTINUOUS_FUTURES_REQUIRED_LABELS: frozenset[str] = frozenset(
    {
        PROVIDER_CONTINUOUS_PROVENANCE_LABEL,
        "non_orderable",
        "not_dated_contract_truth",
        "research_diagnostics_only",
    }
)

DATED_FUTURES_ADJUSTMENT_METHODS: frozenset[str] = frozenset(
    {
        UNADJUSTED_PROVENANCE_LABEL,
        "back_adjusted",
        "ratio_adjusted",
    }
)

DATED_FUTURES_VALIDATION_STATUSES: frozenset[str] = frozenset(
    {
        "unvalidated",
        "discovered",
        "reconciled",
    }
)

DATED_FUTURES_AVAILABILITY_SOURCE = "discovered_not_assumed"

_AVAILABILITY_WINDOW_REQUIRED_FIELDS: tuple[str, ...] = (
    "start",
    "end",
    "availability_source",
)
_FORBIDDEN_FULL_HISTORY_MARKERS: frozenset[str] = frozenset(
    {
        "all_history",
        "assumed_full_history",
        "complete_history",
        "full_historical_availability",
        "full_history",
        "max_available_history",
    }
)
_FORBIDDEN_SERIES_AFFORDANCE_FIELDS: frozenset[str] = frozenset(
    {
        "account",
        "best_execution_roll",
        "broker",
        "can_route_order",
        "can_trade",
        "execution",
        "live",
        "order_router",
        "paper",
        "tradable",
        "tradeable",
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


def _require_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        msg = f"{field_name} must be a boolean"
        raise DataFoundationValidationError(msg)
    return value


def _require_aware_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        msg = f"{field_name} must be a timezone-aware datetime"
        raise DataFoundationValidationError(msg)
    if value.tzinfo is None or value.utcoffset() is None:
        msg = f"{field_name} must be timezone-aware"
        raise DataFoundationValidationError(msg)
    return value


def _parse_aware_datetime(value: object, field_name: str) -> datetime:
    if isinstance(value, datetime):
        return _require_aware_datetime(value, field_name)
    raw = _require_text(value, field_name)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        msg = f"{field_name} must be an ISO-8601 timezone-aware datetime"
        raise DataFoundationValidationError(msg) from exc
    return _require_aware_datetime(parsed, field_name)


def _normalize_root_symbol(value: object) -> str:
    root_symbol = _require_text(value, "root_symbol").upper()
    if not root_symbol.isalnum():
        msg = "root_symbol must be alphanumeric"
        raise DataFoundationValidationError(msg)
    masters = load_futures_instrument_master_by_root()
    if root_symbol not in masters:
        msg = f"root_symbol {root_symbol!r} is not in the futures instrument master"
        raise DataFoundationValidationError(msg)
    return root_symbol


def _normalize_label_set(value: object, field_name: str) -> frozenset[str]:
    if isinstance(value, str) or not isinstance(value, Iterable):
        msg = f"{field_name} must be a non-empty iterable of labels"
        raise DataFoundationValidationError(msg)
    labels = frozenset(_normalize_label(item, field_name) for item in value)
    if not labels:
        msg = f"{field_name} must not be empty"
        raise DataFoundationValidationError(msg)
    return labels


def _reject_forbidden_affordance_fields(
    values: Mapping[str, object],
    record_name: str,
) -> None:
    forbidden = sorted(
        _normalize_label(key, f"{record_name} field")
        for key in values
        if _normalize_label(key, f"{record_name} field")
        in _FORBIDDEN_SERIES_AFFORDANCE_FIELDS
    )
    if forbidden:
        msg = f"{record_name} includes forbidden trading/order affordance fields: "
        raise DataFoundationValidationError(msg + ", ".join(forbidden))


def _contains_forbidden_full_history_marker(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(
            _contains_forbidden_full_history_marker(key)
            or _contains_forbidden_full_history_marker(nested_value)
            for key, nested_value in value.items()
        )
    if isinstance(value, str):
        token = value.lower().replace("-", "_").replace(" ", "_")
        return any(marker in token for marker in _FORBIDDEN_FULL_HISTORY_MARKERS)
    if isinstance(value, Iterable):
        return any(_contains_forbidden_full_history_marker(item) for item in value)
    return False


def _freeze_availability_value(value: object, field_name: str) -> object:
    if _contains_forbidden_full_history_marker(value):
        msg = f"{field_name} must not carry a full-history availability marker"
        raise DataFoundationValidationError(msg)
    if isinstance(value, Mapping):
        if not value:
            msg = f"{field_name} must not be an empty mapping"
            raise DataFoundationValidationError(msg)
        return MappingProxyType(
            {
                _require_text(key, f"{field_name} key"): _freeze_availability_value(
                    nested_value,
                    f"{field_name}.{key}",
                )
                for key, nested_value in sorted(value.items(), key=lambda item: str(item[0]))
            }
        )
    if isinstance(value, str):
        return _require_text(value, field_name)
    if isinstance(value, tuple):
        return tuple(
            _freeze_availability_value(item, f"{field_name}[]") for item in value
        )
    if isinstance(value, list):
        return tuple(
            _freeze_availability_value(item, f"{field_name}[]") for item in value
        )
    if value is None or isinstance(value, bool | int | float):
        return value
    msg = f"{field_name} contains unsupported availability value {type(value).__name__}"
    raise DataFoundationValidationError(msg)


def _normalize_availability_window(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        msg = "availability_window must be a mapping"
        raise DataFoundationValidationError(msg)
    if _contains_forbidden_full_history_marker(value):
        msg = "availability_window must not carry a full-history availability marker"
        raise DataFoundationValidationError(msg)

    missing = tuple(
        field for field in _AVAILABILITY_WINDOW_REQUIRED_FIELDS if field not in value
    )
    if missing:
        msg = "availability_window missing required fields: " + ", ".join(missing)
        raise DataFoundationValidationError(msg)

    start = _require_text(value["start"], "availability_window.start")
    end = _require_text(value["end"], "availability_window.end")
    availability_source = _normalize_label(
        value["availability_source"],
        "availability_window.availability_source",
    )
    if availability_source != DATED_FUTURES_AVAILABILITY_SOURCE:
        msg = "availability_window.availability_source must be discovered_not_assumed"
        raise DataFoundationValidationError(msg)

    frozen = dict(
        _freeze_availability_value(value, "availability_window")
    )
    frozen["start"] = start
    frozen["end"] = end
    frozen["availability_source"] = availability_source
    return MappingProxyType(frozen)


def _coerce_contract_record(value: object) -> FuturesContractRecord:
    if isinstance(value, FuturesContractRecord):
        return value
    if isinstance(value, Mapping):
        return FuturesContractRecord.from_mapping(value)
    msg = "contract_universe entries must be FuturesContractRecord records or mappings"
    raise DataFoundationValidationError(msg)


def _normalize_contract_universe(
    value: object,
    *,
    root_symbol: str,
) -> tuple[FuturesContractRecord, ...]:
    if isinstance(value, str) or not isinstance(value, Iterable):
        msg = "contract_universe must be a non-empty iterable of dated contracts"
        raise DataFoundationValidationError(msg)

    records = tuple(_coerce_contract_record(item) for item in value)
    if not records:
        msg = "contract_universe must not be empty"
        raise DataFoundationValidationError(msg)

    mismatched_roots = sorted(
        {record.root_symbol for record in records if record.root_symbol != root_symbol}
    )
    if mismatched_roots:
        msg = (
            "contract_universe roots must match DatedFuturesSeriesRecord root_symbol; "
            "found "
            + ", ".join(mismatched_roots)
        )
        raise DataFoundationValidationError(msg)

    contract_ids = [record.contract_id for record in records]
    duplicate_contract_ids = sorted(
        {contract_id for contract_id in contract_ids if contract_ids.count(contract_id) > 1}
    )
    if duplicate_contract_ids:
        msg = "contract_universe contains duplicate contract_ids: "
        raise DataFoundationValidationError(msg + ", ".join(duplicate_contract_ids))

    return records


def _normalize_adjustment_method(value: object) -> str:
    adjustment_method = _normalize_label(value, "adjustment_method")
    if adjustment_method not in DATED_FUTURES_ADJUSTMENT_METHODS:
        allowed = ", ".join(sorted(DATED_FUTURES_ADJUSTMENT_METHODS))
        msg = f"adjustment_method must be one of {allowed}"
        raise DataFoundationValidationError(msg)
    return adjustment_method


def _normalize_validation_status(value: object) -> str:
    validation_status = _normalize_label(value, "validation_status")
    if validation_status not in DATED_FUTURES_VALIDATION_STATUSES:
        allowed = ", ".join(sorted(DATED_FUTURES_VALIDATION_STATUSES))
        msg = f"validation_status must be one of {allowed}"
        raise DataFoundationValidationError(msg)
    return validation_status


def reject_mixed_series_provenance_labels(
    *,
    series_kind: object,
    labels: Iterable[object],
) -> frozenset[str]:
    """Validate label separation between continuous and dated-series kinds."""

    normalized_kind = _normalize_label(series_kind, "series_kind")
    if normalized_kind not in SERIES_PROVENANCE_KINDS:
        allowed = ", ".join(sorted(SERIES_PROVENANCE_KINDS))
        msg = f"series_kind must be one of {allowed}"
        raise DataFoundationValidationError(msg)

    normalized_labels = _normalize_label_set(labels, "labels")
    continuous_overlap = normalized_labels & CONTINUOUS_FUTURES_REQUIRED_LABELS
    if normalized_kind == PROVIDER_CONTINUOUS_PROVENANCE_LABEL:
        if normalized_labels != CONTINUOUS_FUTURES_REQUIRED_LABELS:
            msg = "provider_continuous labels must equal the mandatory continuous set"
            raise DataFoundationValidationError(msg)
        return normalized_labels

    if continuous_overlap:
        msg = (
            f"{normalized_kind} series labels must not include continuous-only labels: "
            + ", ".join(sorted(continuous_overlap))
        )
        raise DataFoundationValidationError(msg)

    if normalized_kind not in normalized_labels:
        msg = f"{normalized_kind} series labels must include its own provenance label"
        raise DataFoundationValidationError(msg)

    return normalized_labels


@dataclass(frozen=True, slots=True)
class ContinuousFuturesSeriesRecord:
    """Fail-closed provider-continuous series provenance record.

    This record permanently labels provider-continuous history as diagnostic
    only. It never represents a dated contract, orderable contract, tradable
    roll, or best-execution roll.
    """

    series_id: str
    root_symbol: str
    provider: str
    provenance_label: str
    orderable: bool
    dated_truth: bool
    roll_adjustment_note: str
    source_retrieved_at: datetime
    provenance_labels: frozenset[str] = CONTINUOUS_FUTURES_REQUIRED_LABELS

    def __post_init__(self) -> None:
        series_id = _normalize_id(self.series_id, "series_id")
        root_symbol = _normalize_root_symbol(self.root_symbol)
        provider = _require_text(self.provider, "provider")
        provenance_label = _normalize_label(self.provenance_label, "provenance_label")
        if provenance_label != PROVIDER_CONTINUOUS_PROVENANCE_LABEL:
            msg = "provenance_label must be provider_continuous"
            raise DataFoundationValidationError(msg)

        labels = reject_mixed_series_provenance_labels(
            series_kind=PROVIDER_CONTINUOUS_PROVENANCE_LABEL,
            labels=self.provenance_labels,
        )
        if provenance_label not in labels:
            msg = "provenance_labels must include provider_continuous"
            raise DataFoundationValidationError(msg)

        orderable = _require_bool(self.orderable, "orderable")
        if orderable:
            msg = "ContinuousFuturesSeriesRecord orderable must be false"
            raise DataFoundationValidationError(msg)

        dated_truth = _require_bool(self.dated_truth, "dated_truth")
        if dated_truth:
            msg = "ContinuousFuturesSeriesRecord dated_truth must be false"
            raise DataFoundationValidationError(msg)

        roll_adjustment_note = _require_text(
            self.roll_adjustment_note,
            "roll_adjustment_note",
        )
        normalized_note = roll_adjustment_note.lower().replace("-", " ")
        if "provider" not in normalized_note and "diagnostic" not in normalized_note:
            msg = (
                "roll_adjustment_note must identify provider or diagnostic "
                "continuous-series provenance"
            )
            raise DataFoundationValidationError(msg)
        if (
            "tradable" not in normalized_note
            and "orderable" not in normalized_note
            and "dated truth" not in normalized_note
        ):
            msg = (
                "roll_adjustment_note must disclaim tradable, orderable, "
                "or dated-truth use"
            )
            raise DataFoundationValidationError(msg)
        if "not" not in normalized_note and "non" not in normalized_note:
            msg = "roll_adjustment_note must explicitly state the negative boundary"
            raise DataFoundationValidationError(msg)

        source_retrieved_at = _parse_aware_datetime(
            self.source_retrieved_at,
            "source_retrieved_at",
        )

        object.__setattr__(self, "series_id", series_id)
        object.__setattr__(self, "root_symbol", root_symbol)
        object.__setattr__(self, "provider", provider)
        object.__setattr__(self, "provenance_label", provenance_label)
        object.__setattr__(self, "orderable", orderable)
        object.__setattr__(self, "dated_truth", dated_truth)
        object.__setattr__(self, "roll_adjustment_note", roll_adjustment_note)
        object.__setattr__(self, "source_retrieved_at", source_retrieved_at)
        object.__setattr__(self, "provenance_labels", labels)

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> ContinuousFuturesSeriesRecord:
        """Build a continuous-series record from persisted values and fail closed."""

        _reject_forbidden_affordance_fields(values, "ContinuousFuturesSeriesRecord")
        missing = tuple(
            field
            for field in REQUIRED_CONTINUOUS_FUTURES_SERIES_FIELDS
            if field not in values
        )
        if missing:
            msg = "ContinuousFuturesSeriesRecord missing required fields: "
            raise DataFoundationValidationError(msg + ", ".join(missing))

        return cls(
            series_id=_require_text(values["series_id"], "series_id"),
            root_symbol=_require_text(values["root_symbol"], "root_symbol"),
            provider=_require_text(values["provider"], "provider"),
            provenance_label=_require_text(values["provenance_label"], "provenance_label"),
            orderable=_require_bool(values["orderable"], "orderable"),
            dated_truth=_require_bool(values["dated_truth"], "dated_truth"),
            roll_adjustment_note=_require_text(
                values["roll_adjustment_note"],
                "roll_adjustment_note",
            ),
            source_retrieved_at=_parse_aware_datetime(
                values["source_retrieved_at"],
                "source_retrieved_at",
            ),
            provenance_labels=(
                CONTINUOUS_FUTURES_REQUIRED_LABELS
                if "provenance_labels" not in values
                else _normalize_label_set(values["provenance_labels"], "provenance_labels")
            ),
        )

    @property
    def implies_dated_contract_truth(self) -> bool:
        """Return false: provider-continuous history is never dated truth."""

        return False

    @property
    def implies_orderability(self) -> bool:
        """Return false: provider-continuous series are not orderable."""

        return False

    @property
    def implies_tradability(self) -> bool:
        """Return false: provider-continuous diagnostics are not tradable."""

        return False

    def to_mapping(self) -> Mapping[str, object]:
        """Return JSON-stable provenance fields and mandatory labels."""

        return MappingProxyType(
            {
                "series_id": self.series_id,
                "root_symbol": self.root_symbol,
                "provider": self.provider,
                "provenance_label": self.provenance_label,
                "provenance_labels": tuple(sorted(self.provenance_labels)),
                "orderable": self.orderable,
                "dated_truth": self.dated_truth,
                "roll_adjustment_note": self.roll_adjustment_note,
                "source_retrieved_at": self.source_retrieved_at.isoformat(),
            }
        )


@dataclass(frozen=True, slots=True)
class DatedFuturesSeriesRecord:
    """Fail-closed dated-contract series provenance record.

    The record logs discovered availability and explicit adjustment state only.
    It references a future roll policy id but implements no roll calculation,
    stitching, provider pull, or best-execution assertion.
    """

    series_id: str
    root_symbol: str
    contract_universe: tuple[FuturesContractRecord, ...]
    roll_policy_id: str
    adjustment_method: str
    availability_window: Mapping[str, object]
    validation_status: str = "unvalidated"

    def __post_init__(self) -> None:
        series_id = _normalize_id(self.series_id, "series_id")
        root_symbol = _normalize_root_symbol(self.root_symbol)
        contract_universe = _normalize_contract_universe(
            self.contract_universe,
            root_symbol=root_symbol,
        )
        roll_policy_id = _normalize_id(self.roll_policy_id, "roll_policy_id")
        adjustment_method = _normalize_adjustment_method(self.adjustment_method)
        availability_window = _normalize_availability_window(self.availability_window)
        validation_status = _normalize_validation_status(self.validation_status)

        object.__setattr__(self, "series_id", series_id)
        object.__setattr__(self, "root_symbol", root_symbol)
        object.__setattr__(self, "contract_universe", contract_universe)
        object.__setattr__(self, "roll_policy_id", roll_policy_id)
        object.__setattr__(self, "adjustment_method", adjustment_method)
        object.__setattr__(self, "availability_window", availability_window)
        object.__setattr__(self, "validation_status", validation_status)

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> DatedFuturesSeriesRecord:
        """Build a dated-series record from persisted values and fail closed."""

        _reject_forbidden_affordance_fields(values, "DatedFuturesSeriesRecord")
        for label_field in ("provenance_label", "provenance_labels"):
            if label_field in values:
                labels = (
                    (values[label_field],)
                    if isinstance(values[label_field], str)
                    else values[label_field]
                )
                if not isinstance(labels, Iterable):
                    msg = f"{label_field} must be an iterable when supplied"
                    raise DataFoundationValidationError(msg)
                overlap = (
                    _normalize_label_set(labels, label_field)
                    & CONTINUOUS_FUTURES_REQUIRED_LABELS
                )
                if overlap:
                    msg = (
                        "DatedFuturesSeriesRecord must not carry continuous-only "
                        "labels: "
                        + ", ".join(sorted(overlap))
                    )
                    raise DataFoundationValidationError(msg)

        missing = tuple(
            field for field in REQUIRED_DATED_FUTURES_SERIES_FIELDS if field not in values
        )
        if missing:
            msg = "DatedFuturesSeriesRecord missing required fields: "
            raise DataFoundationValidationError(msg + ", ".join(missing))

        return cls(
            series_id=_require_text(values["series_id"], "series_id"),
            root_symbol=_require_text(values["root_symbol"], "root_symbol"),
            contract_universe=_normalize_contract_universe(
                values["contract_universe"],
                root_symbol=_normalize_root_symbol(values["root_symbol"]),
            ),
            roll_policy_id=_require_text(values["roll_policy_id"], "roll_policy_id"),
            adjustment_method=_require_text(
                values["adjustment_method"],
                "adjustment_method",
            ),
            availability_window=_normalize_availability_window(
                values["availability_window"],
            ),
            validation_status=_require_text(values["validation_status"], "validation_status"),
        )

    @property
    def provenance_label(self) -> str:
        """Return the dated-contract provenance family label."""

        return DATED_CONTRACT_PROVENANCE_LABEL

    @property
    def availability_source(self) -> str:
        """Return the required discovered-not-assumed availability source."""

        return str(self.availability_window["availability_source"])

    @property
    def adjusted_vs_unadjusted(self) -> str:
        """Return the explicit adjustment family for reporting."""

        if self.adjustment_method == UNADJUSTED_PROVENANCE_LABEL:
            return UNADJUSTED_PROVENANCE_LABEL
        return "adjusted"

    @property
    def implies_full_historical_availability(self) -> bool:
        """Return false: availability is logged and bounded, never assumed full."""

        return False

    @property
    def implies_best_execution_roll(self) -> bool:
        """Return false: roll execution quality is outside this record."""

        return False

    @property
    def implies_tradability(self) -> bool:
        """Return false: a dated provenance record is not trading authorization."""

        return False

    def to_mapping(self) -> Mapping[str, object]:
        """Return JSON-stable dated-series provenance fields."""

        return MappingProxyType(
            {
                "series_id": self.series_id,
                "root_symbol": self.root_symbol,
                "contract_universe": tuple(
                    record.to_mapping() for record in self.contract_universe
                ),
                "roll_policy_id": self.roll_policy_id,
                "adjustment_method": self.adjustment_method,
                "availability_window": self.availability_window,
                "validation_status": self.validation_status,
                "provenance_label": self.provenance_label,
            }
        )


def require_dated_contract_truth(series: object) -> DatedFuturesSeriesRecord:
    """Return a dated series or fail if a caller supplies continuous history."""

    if isinstance(series, ContinuousFuturesSeriesRecord):
        msg = "provider-continuous series cannot be used as dated-contract truth"
        raise DataFoundationValidationError(msg)
    if not isinstance(series, DatedFuturesSeriesRecord):
        msg = "dated-contract truth requires DatedFuturesSeriesRecord"
        raise DataFoundationValidationError(msg)
    return series


__all__ = [
    "CANONICAL_STITCHED_PROVENANCE_LABEL",
    "CONTINUOUS_FUTURES_REQUIRED_LABELS",
    "ContinuousFuturesSeriesRecord",
    "DATED_CONTRACT_PROVENANCE_LABEL",
    "DATED_FUTURES_ADJUSTMENT_METHODS",
    "DATED_FUTURES_AVAILABILITY_SOURCE",
    "DATED_FUTURES_VALIDATION_STATUSES",
    "DatedFuturesSeriesRecord",
    "PROVIDER_CONTINUOUS_PROVENANCE_LABEL",
    "REQUIRED_CONTINUOUS_FUTURES_SERIES_FIELDS",
    "REQUIRED_DATED_FUTURES_SERIES_FIELDS",
    "ROLL_ADJUSTED_PROVENANCE_LABEL",
    "SERIES_PROVENANCE_KINDS",
    "UNADJUSTED_PROVENANCE_LABEL",
    "reject_mixed_series_provenance_labels",
    "require_dated_contract_truth",
]
