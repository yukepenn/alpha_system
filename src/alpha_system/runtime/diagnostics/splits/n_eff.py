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

ESTIMATOR_FORMULA = (
    "n_eff = floor(max(rows - purge_gap - embargo_gap, 0) / discount_factor), "
    "bounded to [0, rows]"
)
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

# Forward-overlapping outcome label families. A label whose value looks ``N``
# bars ahead (a forward/excursion/barrier horizon) makes consecutive bar-spaced
# observations overlap ~N-fold, so the raw row count badly overstates the
# independent sample (the ratified #474 law). Classification is by label *type*
# (intrinsic to the outcome) so the overlap discount can never be silently
# skipped just because an OPTIONAL horizon field was left unset: a
# forward-overlapping label MUST carry an overlap-discounted N_eff or fail loud.
# Match is by prefix family (e.g. ``forward_return_5m``, ``fwd_ret_30m``,
# ``cost_adjusted_forward_return``, ``mfe_by_horizon``, ``triple_barrier_*``).
_FORWARD_OVERLAPPING_OUTCOME_PREFIXES: tuple[str, ...] = (
    "forward_return",
    "fwd_ret",
    "cost_adjusted",
    "cost_adj",
    "mfe",
    "mae",
    "triple_barrier",
    "net_excursion",
)


class NEffSampleReportingError(ValueError):
    """Raised when N_eff reporting would be missing or misleading."""


def is_forward_overlapping_outcome(outcome_label_type: str | None) -> bool:
    """Return True when the outcome label spans a forward horizon (overlaps).

    A forward-overlapping outcome (forward/cost-adjusted return, mfe/mae
    excursion, triple-barrier, derived net_excursion) looks several bars ahead,
    so consecutive bar-spaced observations overlap and the raw row count
    overstates the independent sample. Such an outcome MUST be discounted via the
    overlap-aware estimator; a non-overlapping outcome (e.g. the binary
    contemporaneous ``target_before_stop`` with ``outcome_label_type`` None) is
    not discounted.
    """

    if outcome_label_type is None:
        return False
    text = str(outcome_label_type).strip().lower()
    if not text:
        return False
    return any(text.startswith(prefix) for prefix in _FORWARD_OVERLAPPING_OUTCOME_PREFIXES)


def forward_overlap_block_size(
    outcome_label_type: str | None,
    *,
    required_future_bars: int | None = None,
    horizon_seconds: float | None = None,
    cadence_seconds: float | None = None,
) -> int:
    """Derive the overlap block size (in bars) for an outcome label, fail-closed.

    For a NON forward-overlapping outcome this returns 1 (no overlap to
    discount). For a forward-overlapping outcome the block size is the forward
    horizon in bars, derived from (in order):

    1. ``required_future_bars`` when it is a positive integer; otherwise
    2. ``floor(horizon_seconds / cadence_seconds)`` when both are positive.

    If the outcome is forward-overlapping but neither path can derive the
    horizon, this RAISES ``NEffSampleReportingError`` -- it NEVER silently
    returns 1 (which would mean raw, un-discounted rows and resurrect the #474
    regression). A genuinely single-bar-ahead forward label (block size 1) is a
    legitimate no-overlap case and is returned as 1.
    """

    if not is_forward_overlapping_outcome(outcome_label_type):
        return 1
    if required_future_bars is not None:
        bars = int(required_future_bars)
        if bars >= 1:
            return bars
        raise NEffSampleReportingError(
            "forward-overlapping outcome "
            f"{outcome_label_type!r} has non-positive required_future_bars "
            f"({required_future_bars!r}); cannot derive overlap block size"
        )
    if horizon_seconds is not None and cadence_seconds is not None:
        horizon = float(horizon_seconds)
        cadence = float(cadence_seconds)
        if math.isfinite(horizon) and math.isfinite(cadence) and horizon > 0 and cadence > 0:
            return max(1, math.floor(horizon / cadence))
    raise NEffSampleReportingError(
        "forward-overlapping outcome "
        f"{outcome_label_type!r} cannot derive an overlap block size: set "
        "required_future_bars or supply horizon_seconds and cadence_seconds. "
        "Refusing to fall back to raw rows / discount_factor=1 (the #474 law)."
    )


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
    rows_after_purge_embargo: int | None = None
    purge_gap: int = 0
    embargo_gap: int = 0
    purge_embargo_removed_rows: int | None = None

    def __post_init__(self) -> None:
        rows = _non_negative_int(self.rows, "rows")
        n_eff = _non_negative_int(self.n_eff, "n_eff")
        adjusted_value = rows if self.rows_after_purge_embargo is None else self.rows_after_purge_embargo
        adjusted_rows = _non_negative_int(
            adjusted_value,
            "rows_after_purge_embargo",
        )
        purge_gap = _non_negative_int(self.purge_gap, "purge_gap")
        embargo_gap = _non_negative_int(self.embargo_gap, "embargo_gap")
        removed_value = (
            rows - adjusted_rows
            if self.purge_embargo_removed_rows is None
            else self.purge_embargo_removed_rows
        )
        removed_rows = _non_negative_int(
            removed_value,
            "purge_embargo_removed_rows",
        )
        if n_eff > rows:
            raise NEffSampleReportingError("n_eff must never exceed rows")
        if adjusted_rows > rows:
            raise NEffSampleReportingError("rows_after_purge_embargo must never exceed rows")
        if removed_rows > rows:
            raise NEffSampleReportingError("purge/embargo removed rows must never exceed rows")
        object.__setattr__(self, "rows", rows)
        object.__setattr__(self, "n_eff", n_eff)
        object.__setattr__(self, "rows_after_purge_embargo", adjusted_rows)
        object.__setattr__(self, "purge_gap", purge_gap)
        object.__setattr__(self, "embargo_gap", embargo_gap)
        object.__setattr__(self, "purge_embargo_removed_rows", removed_rows)

    def to_dict(self) -> dict[str, object]:
        """Return a value-free rows-vs-effective-samples report block."""

        return {
            "rows": self.rows,
            "n_eff": self.n_eff,
            "rows_after_purge_embargo": self.rows_after_purge_embargo,
            "purge_gap": self.purge_gap,
            "embargo_gap": self.embargo_gap,
            "purge_embargo_removed_rows": self.purge_embargo_removed_rows,
            "rows_are_not_independent_samples": ROWS_NOT_INDEPENDENT_MARKER,
            "overlap_metadata": self.overlap_metadata.to_dict(),
            "estimator_formula": ESTIMATOR_FORMULA,
            "conservatism_direction": (
                "purge/embargo gaps are removed before the supplied overlap discount "
                "and n_eff is never reported above rows"
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
    *,
    purge_gap: int | None = None,
    embargo_gap: int | None = None,
) -> NEffEstimate:
    """Return a conservative overlap-aware effective sample count.

    Purge/embargo gaps are removed first, then the remaining rows are
    discounted by the explicit metadata discount factor. Non-empty adjusted
    samples retain at least one effective sample, while zero adjusted rows
    remain zero. The estimate is always bounded by the raw row count.
    """

    active_rows = _non_negative_int(rows, "rows")
    active_purge_gap = _gap_value(
        explicit=purge_gap,
        metadata=horizon_overlap_metadata,
        key="purge_gap",
    )
    active_embargo_gap = _gap_value(
        explicit=embargo_gap,
        metadata=horizon_overlap_metadata,
        key="embargo_gap",
    )
    removed_rows = min(active_rows, active_purge_gap + active_embargo_gap)
    adjusted_rows = active_rows - removed_rows
    metadata = coerce_horizon_overlap_metadata(horizon_overlap_metadata)
    if adjusted_rows == 0:
        n_eff = 0
    else:
        n_eff = max(1, math.floor(adjusted_rows / metadata.discount_factor))
    return NEffEstimate(
        rows=active_rows,
        n_eff=min(n_eff, active_rows),
        overlap_metadata=metadata,
        rows_after_purge_embargo=adjusted_rows,
        purge_gap=active_purge_gap,
        embargo_gap=active_embargo_gap,
        purge_embargo_removed_rows=removed_rows,
    )


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
        purge_gap = _optional_int(item.get("purge_gap"), "purge_gap")
        embargo_gap = _optional_int(item.get("embargo_gap"), "embargo_gap")
        record: dict[str, object] = {
            "split_id": split_id,
            "purge_gap": purge_gap,
            "embargo_gap": embargo_gap,
            "train": estimate_n_eff(
                train_rows,
                metadata,
                purge_gap=purge_gap,
                embargo_gap=embargo_gap,
            ).to_dict(),
            "validation": estimate_n_eff(
                validation_rows,
                metadata,
                purge_gap=purge_gap,
                embargo_gap=embargo_gap,
            ).to_dict(),
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


def _gap_value(
    *,
    explicit: int | None,
    metadata: HorizonOverlapMetadata | Mapping[str, Any] | None,
    key: str,
) -> int:
    if explicit is not None:
        return _non_negative_int(explicit, key)
    if isinstance(metadata, Mapping) and key in metadata:
        return _non_negative_int(metadata.get(key), key)
    return 0


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
    "forward_overlap_block_size",
    "is_forward_overlapping_outcome",
]
