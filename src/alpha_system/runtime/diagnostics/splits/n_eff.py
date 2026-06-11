"""Overlap-aware effective-sample-size reporting helpers.

The estimator in this module is a deterministic reporting input. It discounts
raw observation rows by caller-supplied horizon-overlap metadata and makes no
statistical-validity claim.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

JsonScalar = None | bool | int | float | str

ESTIMATOR_FORMULA = "n_eff = floor(rows / discount_factor), bounded to [0, rows]"
ROWS_NOT_INDEPENDENT_MARKER = True

_HORIZON_KEYS: tuple[tuple[str, str], ...] = (
    ("horizon_bars", "bars"),
    ("label_horizon_bars", "bars"),
    ("horizon_minutes", "minutes"),
    ("label_horizon_minutes", "minutes"),
    ("horizon_seconds", "seconds"),
    ("label_horizon_seconds", "seconds"),
)
_CADENCE_KEYS: tuple[tuple[str, str], ...] = (
    ("sampling_cadence_bars", "bars"),
    ("cadence_bars", "bars"),
    ("sampling_interval_bars", "bars"),
    ("sampling_cadence_minutes", "minutes"),
    ("cadence_minutes", "minutes"),
    ("sampling_interval_minutes", "minutes"),
    ("sampling_cadence_seconds", "seconds"),
    ("cadence_seconds", "seconds"),
    ("sampling_interval_seconds", "seconds"),
)
_FACTOR_KEYS = (
    "discount_factor",
    "overlap_factor",
    "effective_overlap_factor",
    "horizon_overlap_factor",
    "overlap_discount_factor",
)
_TIME_UNIT_SECONDS = {"seconds": 1.0, "minutes": 60.0}


class NEffSampleReportingError(ValueError):
    """Raised when N_eff reporting would be missing or misleading."""


@dataclass(frozen=True, slots=True)
class HorizonOverlapMetadata:
    """Explicit label-horizon overlap metadata supplied by the caller."""

    horizon: float
    horizon_unit: str
    sampling_cadence: float
    sampling_cadence_unit: str
    discount_factor: float
    metadata_source: str = "caller_supplied"

    def __post_init__(self) -> None:
        horizon = _positive_float(self.horizon, "horizon")
        cadence = _positive_float(self.sampling_cadence, "sampling_cadence")
        discount_factor = _positive_float(self.discount_factor, "discount_factor")
        horizon_unit = _unit(self.horizon_unit, "horizon_unit")
        cadence_unit = _unit(self.sampling_cadence_unit, "sampling_cadence_unit")
        source = _optional_text(self.metadata_source, "metadata_source") or "caller_supplied"
        implied_factor = _implied_discount_factor(
            horizon=horizon,
            horizon_unit=horizon_unit,
            cadence=cadence,
            cadence_unit=cadence_unit,
        )
        if discount_factor < 1.0:
            raise NEffSampleReportingError("discount_factor must be at least 1")
        if discount_factor + 1e-12 < implied_factor:
            raise NEffSampleReportingError(
                "discount_factor understates the horizon/cadence overlap "
                f"({discount_factor:g} < {implied_factor:g})"
            )

        object.__setattr__(self, "horizon", horizon)
        object.__setattr__(self, "horizon_unit", horizon_unit)
        object.__setattr__(self, "sampling_cadence", cadence)
        object.__setattr__(self, "sampling_cadence_unit", cadence_unit)
        object.__setattr__(self, "discount_factor", discount_factor)
        object.__setattr__(self, "metadata_source", source)

    @property
    def implied_discount_factor(self) -> float:
        """Return the minimum discount implied by horizon and cadence."""

        return _implied_discount_factor(
            horizon=self.horizon,
            horizon_unit=self.horizon_unit,
            cadence=self.sampling_cadence,
            cadence_unit=self.sampling_cadence_unit,
        )

    @property
    def overlap_fraction(self) -> float:
        """Return the overlap fraction implied by the reported discount factor."""

        return 0.0 if self.discount_factor <= 1.0 else 1.0 - (1.0 / self.discount_factor)

    def to_dict(self) -> dict[str, JsonScalar]:
        """Return deterministic scalar metadata used by the N_eff estimator."""

        return {
            "horizon": self.horizon,
            "horizon_unit": self.horizon_unit,
            "sampling_cadence": self.sampling_cadence,
            "sampling_cadence_unit": self.sampling_cadence_unit,
            "discount_factor": self.discount_factor,
            "implied_discount_factor": self.implied_discount_factor,
            "overlap_fraction": self.overlap_fraction,
            "metadata_source": self.metadata_source,
        }


@dataclass(frozen=True, slots=True)
class NEffEstimate:
    """Rows and overlap-aware effective-sample-size estimate."""

    rows: int
    n_eff: int
    overlap_metadata: HorizonOverlapMetadata

    def __post_init__(self) -> None:
        rows = _non_negative_int(self.rows, "rows")
        n_eff = _non_negative_int(self.n_eff, "n_eff")
        if n_eff > rows:
            raise NEffSampleReportingError("n_eff must never exceed rows")
        object.__setattr__(self, "rows", rows)
        object.__setattr__(self, "n_eff", n_eff)

    def to_dict(self) -> dict[str, object]:
        """Return a value-free rows-vs-effective-samples report block."""

        return {
            "rows": self.rows,
            "n_eff": self.n_eff,
            "rows_are_not_independent_samples": ROWS_NOT_INDEPENDENT_MARKER,
            "overlap_metadata": self.overlap_metadata.to_dict(),
            "estimator_formula": ESTIMATOR_FORMULA,
            "conservatism_direction": (
                "raw rows are discounted by the supplied overlap factor and "
                "n_eff is never reported above rows"
            ),
            "statistical_validity_claim": False,
        }


@dataclass(frozen=True, slots=True)
class SessionDayAggregation:
    """Counts of caller-supplied session and trade-date grouping units."""

    session_field_names: tuple[str, ...]
    trade_date_field_names: tuple[str, ...]
    observation_count: int
    session_unit_count: int
    trade_date_unit_count: int
    session_trade_date_unit_count: int
    missing_session_count: int
    missing_trade_date_count: int

    def to_dict(self) -> dict[str, JsonScalar]:
        """Return scalar session/day aggregate counts."""

        return {
            "session_fields": ",".join(self.session_field_names),
            "trade_date_fields": ",".join(self.trade_date_field_names),
            "observation_count": self.observation_count,
            "session_unit_count": self.session_unit_count,
            "trade_date_unit_count": self.trade_date_unit_count,
            "session_trade_date_unit_count": self.session_trade_date_unit_count,
            "missing_session_count": self.missing_session_count,
            "missing_trade_date_count": self.missing_trade_date_count,
        }


def coerce_horizon_overlap_metadata(
    value: HorizonOverlapMetadata | Mapping[str, Any] | None,
) -> HorizonOverlapMetadata:
    """Coerce caller-supplied horizon overlap metadata or fail closed."""

    if isinstance(value, HorizonOverlapMetadata):
        return value
    if value is None:
        raise NEffSampleReportingError("horizon overlap metadata is required for N_eff")
    if not isinstance(value, Mapping):
        raise NEffSampleReportingError(
            "horizon overlap metadata must be HorizonOverlapMetadata or mapping"
        )

    horizon_value, horizon_unit = _extract_dimension(
        value,
        explicit_key="horizon",
        explicit_unit_key="horizon_unit",
        candidates=_HORIZON_KEYS,
        field="horizon",
    )
    cadence_value, cadence_unit = _extract_dimension(
        value,
        explicit_key="sampling_cadence",
        explicit_unit_key="sampling_cadence_unit",
        candidates=_CADENCE_KEYS,
        field="sampling_cadence",
    )
    factor = _extract_factor(value)
    source = _optional_text(value.get("metadata_source"), "metadata_source") or _optional_text(
        value.get("source"), "source"
    )
    return HorizonOverlapMetadata(
        horizon=horizon_value,
        horizon_unit=horizon_unit,
        sampling_cadence=cadence_value,
        sampling_cadence_unit=cadence_unit,
        discount_factor=factor,
        metadata_source=source or "caller_supplied",
    )


def estimate_n_eff(
    rows: int,
    horizon_overlap_metadata: HorizonOverlapMetadata | Mapping[str, Any] | None,
) -> NEffEstimate:
    """Return a conservative overlap-aware effective sample count.

    Rows are discounted by the explicit metadata discount factor. Non-empty
    overlapping samples retain at least one effective sample, while zero rows
    remain zero. The estimate is always bounded by the raw row count.
    """

    active_rows = _non_negative_int(rows, "rows")
    metadata = coerce_horizon_overlap_metadata(horizon_overlap_metadata)
    if active_rows == 0:
        n_eff = 0
    else:
        n_eff = max(1, math.floor(active_rows / metadata.discount_factor))
    return NEffEstimate(rows=active_rows, n_eff=min(n_eff, active_rows), overlap_metadata=metadata)


def build_session_day_aggregation(
    observations: Iterable[Mapping[str, Any]],
    *,
    session_field_names: Sequence[str] = ("session_label", "session", "session_segment"),
    trade_date_field_names: Sequence[str] = ("trade_date", "trade_date_id"),
) -> SessionDayAggregation:
    """Count caller-supplied session and trade-date grouping units."""

    session_fields = _field_names(session_field_names, "session_field_names")
    trade_date_fields = _field_names(trade_date_field_names, "trade_date_field_names")
    session_units: set[str] = set()
    trade_date_units: set[str] = set()
    session_trade_date_units: set[tuple[str, str]] = set()
    missing_session_count = 0
    missing_trade_date_count = 0
    observation_count = 0

    for row in observations:
        if not isinstance(row, Mapping):
            raise NEffSampleReportingError("session/day aggregation observations must be mappings")
        observation_count += 1
        session = _first_text(row, session_fields)
        trade_date = _first_text(row, trade_date_fields)
        if session is None:
            missing_session_count += 1
        else:
            session_units.add(session)
        if trade_date is None:
            missing_trade_date_count += 1
        else:
            trade_date_units.add(trade_date)
        if session is not None and trade_date is not None:
            session_trade_date_units.add((session, trade_date))

    return SessionDayAggregation(
        session_field_names=session_fields,
        trade_date_field_names=trade_date_fields,
        observation_count=observation_count,
        session_unit_count=len(session_units),
        trade_date_unit_count=len(trade_date_units),
        session_trade_date_unit_count=len(session_trade_date_units),
        missing_session_count=missing_session_count,
        missing_trade_date_count=missing_trade_date_count,
    )


def attach_n_eff_to_walk_forward_metadata(
    walk_forward_metadata: Mapping[str, Any] | Iterable[Mapping[str, Any]] | object,
    horizon_overlap_metadata: HorizonOverlapMetadata | Mapping[str, Any] | None,
) -> tuple[dict[str, object], ...]:
    """Attach train/validation N_eff counts to P24-shaped fold metadata."""

    metadata = coerce_horizon_overlap_metadata(horizon_overlap_metadata)
    payload = _walk_forward_payload(walk_forward_metadata)
    config = payload.get("config", {})
    folds = payload.get("folds", payload)
    if not isinstance(folds, Iterable) or isinstance(folds, str | bytes | bytearray | Mapping):
        raise NEffSampleReportingError("walk-forward metadata must contain fold mappings")

    half_life_protocol = None
    if isinstance(config, Mapping):
        protocol = config.get("half_life_protocol") or config.get("protocol")
        half_life_protocol = None if protocol in (None, "") else str(protocol)

    records: list[dict[str, object]] = []
    for item in folds:
        if not isinstance(item, Mapping):
            raise NEffSampleReportingError("walk-forward fold metadata entries must be mappings")
        split_id = _required_text(item.get("split_id"), "split_id")
        train_rows = _index_count(item.get("train_indices"), "train_indices")
        validation_rows = _index_count(item.get("validation_indices"), "validation_indices")
        record: dict[str, object] = {
            "split_id": split_id,
            "purge_gap": _optional_int(item.get("purge_gap"), "purge_gap"),
            "embargo_gap": _optional_int(item.get("embargo_gap"), "embargo_gap"),
            "train": estimate_n_eff(train_rows, metadata).to_dict(),
            "validation": estimate_n_eff(validation_rows, metadata).to_dict(),
        }
        if half_life_protocol is not None:
            record["half_life_protocol"] = half_life_protocol
        records.append(record)
    return tuple(records)


def build_n_eff_sample_report(
    *,
    rows: int,
    horizon_overlap_metadata: HorizonOverlapMetadata | Mapping[str, Any] | None,
    observations: Iterable[Mapping[str, Any]] = (),
    walk_forward_metadata: Mapping[str, Any] | Iterable[Mapping[str, Any]] | object | None = None,
    session_field_names: Sequence[str] = ("session_label", "session", "session_segment"),
    trade_date_field_names: Sequence[str] = ("trade_date", "trade_date_id"),
) -> dict[str, object]:
    """Build the value-free N_eff report block used by diagnostics surfaces."""

    observations_tuple = tuple(observations)
    estimate = estimate_n_eff(rows, horizon_overlap_metadata)
    block: dict[str, object] = estimate.to_dict()
    block["session_day_aggregation"] = build_session_day_aggregation(
        observations_tuple,
        session_field_names=session_field_names,
        trade_date_field_names=trade_date_field_names,
    ).to_dict()
    if walk_forward_metadata is not None:
        block["walk_forward_fold_n_eff"] = [
            dict(item)
            for item in attach_n_eff_to_walk_forward_metadata(
                walk_forward_metadata,
                estimate.overlap_metadata,
            )
        ]
    return block


def _walk_forward_payload(value: object) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        payload = to_dict()
        if isinstance(payload, Mapping):
            return payload
    if isinstance(value, Iterable) and not isinstance(value, str | bytes | bytearray):
        return {"folds": tuple(value)}
    raise NEffSampleReportingError("walk-forward metadata must be a mapping or fold iterable")


def _extract_dimension(
    value: Mapping[str, Any],
    *,
    explicit_key: str,
    explicit_unit_key: str,
    candidates: tuple[tuple[str, str], ...],
    field: str,
) -> tuple[float, str]:
    for key, unit in candidates:
        if key in value:
            return _positive_float(value.get(key), key), unit
    if explicit_key in value:
        unit = _unit(value.get(explicit_unit_key), explicit_unit_key)
        return _positive_float(value.get(explicit_key), explicit_key), unit
    raise NEffSampleReportingError(f"{field} is required in horizon overlap metadata")


def _extract_factor(value: Mapping[str, Any]) -> float:
    for key in _FACTOR_KEYS:
        if key in value:
            return _positive_float(value.get(key), key)
    raise NEffSampleReportingError("discount_factor is required in horizon overlap metadata")


def _implied_discount_factor(
    *,
    horizon: float,
    horizon_unit: str,
    cadence: float,
    cadence_unit: str,
) -> float:
    horizon_basis = _unit_basis(horizon, horizon_unit)
    cadence_basis = _unit_basis(cadence, cadence_unit)
    if horizon_basis[0] != cadence_basis[0]:
        raise NEffSampleReportingError(
            "horizon and sampling cadence units must both be time units or both be bars"
        )
    return max(1.0, horizon_basis[1] / cadence_basis[1])


def _unit_basis(value: float, unit: str) -> tuple[str, float]:
    if unit == "bars":
        return ("bars", value)
    if unit in _TIME_UNIT_SECONDS:
        return ("time", value * _TIME_UNIT_SECONDS[unit])
    raise NEffSampleReportingError(f"unsupported horizon overlap unit {unit!r}")


def _field_names(values: Sequence[str], field: str) -> tuple[str, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence) or not values:
        raise NEffSampleReportingError(f"{field} must be a non-empty sequence of field names")
    return tuple(_required_text(item, field) for item in values)


def _first_text(row: Mapping[str, Any], fields: Sequence[str]) -> str | None:
    for field in fields:
        value = row.get(field)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _index_count(value: object, field: str) -> int:
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return len(value)
    raise NEffSampleReportingError(f"{field} must be a sequence in P24 fold metadata")


def _positive_float(value: object, field: str) -> float:
    if isinstance(value, bool):
        raise NEffSampleReportingError(f"{field} must be a positive finite number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise NEffSampleReportingError(f"{field} must be a positive finite number") from exc
    if not math.isfinite(number) or number <= 0:
        raise NEffSampleReportingError(f"{field} must be a positive finite number")
    return number


def _non_negative_int(value: object, field: str) -> int:
    if isinstance(value, bool):
        raise NEffSampleReportingError(f"{field} must be a non-negative integer")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise NEffSampleReportingError(f"{field} must be a non-negative integer") from exc
    if number < 0:
        raise NEffSampleReportingError(f"{field} must be a non-negative integer")
    return number


def _optional_int(value: object, field: str) -> int | None:
    if value is None:
        return None
    return _non_negative_int(value, field)


def _unit(value: object, field: str) -> str:
    text = _required_text(value, field).lower()
    aliases = {
        "bar": "bars",
        "bars": "bars",
        "minute": "minutes",
        "minutes": "minutes",
        "min": "minutes",
        "m": "minutes",
        "second": "seconds",
        "seconds": "seconds",
        "sec": "seconds",
        "s": "seconds",
    }
    try:
        return aliases[text]
    except KeyError as exc:
        allowed = ", ".join(sorted(set(aliases.values())))
        raise NEffSampleReportingError(f"{field} must be one of: {allowed}") from exc


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise NEffSampleReportingError(f"{field} must be non-empty text")
    return value.strip()


def _optional_text(value: object, field: str) -> str | None:
    if value is None:
        return None
    return _required_text(value, field)


__all__ = [
    "ESTIMATOR_FORMULA",
    "ROWS_NOT_INDEPENDENT_MARKER",
    "HorizonOverlapMetadata",
    "NEffEstimate",
    "NEffSampleReportingError",
    "SessionDayAggregation",
    "attach_n_eff_to_walk_forward_metadata",
    "build_n_eff_sample_report",
    "build_session_day_aggregation",
    "coerce_horizon_overlap_metadata",
    "estimate_n_eff",
]
