"""Session, calendar, and roll feature definitions and calculations."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, time
from enum import StrEnum
from types import MappingProxyType
from typing import Any

from alpha_system.data.foundation.grid import DenseGridBarRecord
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.features.contracts import (
    FeatureFamily,
    FeatureInputSpec,
    FeatureSpec,
    FeatureValueRecord,
    FeatureVersion,
    NormalizationSpec,
    TransformSpec,
    WindowCausality,
    WindowKind,
    WindowSpec,
)
from alpha_system.features.input_views import CanonicalInputViews, OHLCVInputRow, OHLCVInputView
from alpha_system.features.request_gate import (
    FeatureRequestGateDecision,
    require_feature_request_implementation_allowed,
)
from alpha_system.features.semantics import (
    TradeBarRow,
    is_real_trade_bar,
    is_synthetic_no_trade_bar,
)
from alpha_system.governance.duplicate_exposure import RegistryReader
from alpha_system.governance.feature_request import FeatureRequest


class SessionFeatureError(ValueError):
    """Raised when Session / Calendar / Roll feature computation fails closed."""


class SessionFeatureName(StrEnum):
    """Supported Session / Calendar / Roll feature names for FLF-P10."""

    SESSION_ID = "session_id"
    MINUTES_FROM_RTH_OPEN = "minutes_from_rth_open"
    MINUTES_TO_RTH_CLOSE = "minutes_to_rth_close"
    RTH_SEGMENT_FLAG = "rth_segment_flag"
    ETH_SEGMENT_FLAG = "eth_segment_flag"
    DAY_OF_WEEK = "day_of_week"
    BARS_TO_ROLL = "bars_to_roll"
    MINUTES_TO_ROLL = "minutes_to_roll"
    MINUTES_TO_EXPIRATION = "minutes_to_expiration"
    HALT_STATUS_FLAG = "halt_status_flag"


@dataclass(frozen=True, slots=True)
class SessionCalendarRollMetadata:
    """Optional accepted-DatasetVersion metadata for expiration and status features."""

    expiration_ts_by_contract_id: Mapping[str, datetime] = field(default_factory=dict)
    status_by_row_key: Mapping[str, str] = field(default_factory=dict)
    status_by_available_ts: Mapping[datetime, str] = field(default_factory=dict)
    expiration_available_ts_by_contract_id: Mapping[str, datetime] = field(default_factory=dict)
    status_available_ts_by_row_key: Mapping[str, datetime] = field(default_factory=dict)
    status_available_ts_by_available_ts: Mapping[datetime, datetime] = field(default_factory=dict)

    def __post_init__(self) -> None:
        expiration = {
            _require_text(contract_id, "expiration_ts_by_contract_id key"): _require_aware_datetime(
                expiration_ts,
                "expiration_ts_by_contract_id value",
            )
            for contract_id, expiration_ts in self.expiration_ts_by_contract_id.items()
        }
        row_status = {
            _require_text(row_key, "status_by_row_key key"): _normalize_status(status)
            for row_key, status in self.status_by_row_key.items()
        }
        available_status = {
            _require_aware_datetime(available_ts, "status_by_available_ts key"): _normalize_status(
                status
            )
            for available_ts, status in self.status_by_available_ts.items()
        }
        expiration_available = {
            _require_text(
                contract_id,
                "expiration_available_ts_by_contract_id key",
            ): _require_aware_datetime(
                available_ts,
                "expiration_available_ts_by_contract_id value",
            )
            for contract_id, available_ts in self.expiration_available_ts_by_contract_id.items()
        }
        row_status_available = {
            _require_text(
                row_key_value,
                "status_available_ts_by_row_key key",
            ): _require_aware_datetime(
                available_ts,
                "status_available_ts_by_row_key value",
            )
            for row_key_value, available_ts in self.status_available_ts_by_row_key.items()
        }
        available_status_available = {
            _require_aware_datetime(
                status_available_ts,
                "status_available_ts_by_available_ts key",
            ): _require_aware_datetime(
                metadata_available_ts,
                "status_available_ts_by_available_ts value",
            )
            for status_available_ts, metadata_available_ts in (
                self.status_available_ts_by_available_ts.items()
            )
        }
        object.__setattr__(self, "expiration_ts_by_contract_id", MappingProxyType(expiration))
        object.__setattr__(self, "status_by_row_key", MappingProxyType(row_status))
        object.__setattr__(self, "status_by_available_ts", MappingProxyType(available_status))
        object.__setattr__(
            self,
            "expiration_available_ts_by_contract_id",
            MappingProxyType(expiration_available),
        )
        object.__setattr__(
            self,
            "status_available_ts_by_row_key",
            MappingProxyType(row_status_available),
        )
        object.__setattr__(
            self,
            "status_available_ts_by_available_ts",
            MappingProxyType(available_status_available),
        )

    def expiration_for(self, row: TradeBarRow) -> datetime | None:
        """Return the expiration timestamp for ``row.contract_id`` if supplied."""

        expiration_ts = self.expiration_ts_by_contract_id.get(row.contract_id)
        if expiration_ts is not None:
            _require_metadata_known_as_of(
                self.expiration_available_ts_by_contract_id.get(row.contract_id),
                row,
                "expiration metadata",
            )
        return expiration_ts

    def status_for(self, row: TradeBarRow) -> str | None:
        """Return canonical status metadata for one row if supplied."""

        key = row_key(row)
        if key in self.status_by_row_key:
            _require_metadata_known_as_of(
                self.status_available_ts_by_row_key.get(key),
                row,
                "status metadata",
            )
            return self.status_by_row_key[key]
        if row.available_ts in self.status_by_available_ts:
            _require_metadata_known_as_of(
                self.status_available_ts_by_available_ts.get(row.available_ts),
                row,
                "status metadata",
            )
            return self.status_by_available_ts[row.available_ts]
        return None


@dataclass(frozen=True, slots=True)
class SessionFeatureSpec:
    """Session family view over a governed FLF-P06 ``FeatureSpec``."""

    feature_spec: FeatureSpec
    feature_name: SessionFeatureName

    def __post_init__(self) -> None:
        if not isinstance(self.feature_spec, FeatureSpec):
            raise SessionFeatureError("SessionFeatureSpec.feature_spec must be a FeatureSpec")
        feature_name = _coerce_feature_name(self.feature_name)
        if self.feature_spec.family is not FeatureFamily.SESSION_CALENDAR_ROLL:
            raise SessionFeatureError(
                "SessionFeatureSpec requires FeatureFamily.SESSION_CALENDAR_ROLL"
            )
        object.__setattr__(self, "feature_name", feature_name)

    @property
    def feature_id(self) -> str:
        """Return the stable feature id from the underlying contract."""

        return self.feature_spec.feature_id

    @property
    def family(self) -> FeatureFamily:
        """Return the shared FLF-P06 feature family enum."""

        return self.feature_spec.family

    @property
    def feature_request_id(self) -> str:
        """Return the governed ``freq_`` request id."""

        return self.feature_spec.feature_request_id

    @property
    def inputs(self) -> FeatureInputSpec:
        """Return the underlying input contract."""

        return self.feature_spec.inputs

    @property
    def transform(self) -> TransformSpec:
        """Return the underlying transform contract."""

        return self.feature_spec.transform

    @property
    def window(self) -> WindowSpec:
        """Return the underlying window contract."""

        return self.feature_spec.window

    @property
    def normalization(self) -> NormalizationSpec:
        """Return the underlying normalization contract."""

        return self.feature_spec.normalization

    @property
    def live(self) -> bool:
        """Return whether the underlying contract is live-compatible."""

        return self.feature_spec.live

    @property
    def implementation_eligible(self) -> bool:
        """Return whether the approved request gate admitted implementation."""

        return self.feature_spec.implementation_eligible

    def derive_feature_version(self) -> FeatureVersion:
        """Derive the deterministic version from the underlying contract."""

        return self.feature_spec.derive_feature_version()

    def to_contract_dict(self) -> dict[str, object]:
        """Return the canonical underlying feature contract payload."""

        return self.feature_spec.to_contract_dict()


@dataclass(frozen=True, slots=True)
class SessionPositionFeatureSpec(SessionFeatureSpec):
    """Session identifier, RTH/ETH flag, and RTH clock feature contract."""


@dataclass(frozen=True, slots=True)
class CalendarFeatureSpec(SessionFeatureSpec):
    """Calendar-position feature contract."""


@dataclass(frozen=True, slots=True)
class RollFeatureSpec(SessionFeatureSpec):
    """Contract-roll proximity feature contract."""


@dataclass(frozen=True, slots=True)
class ExpirationFeatureSpec(SessionFeatureSpec):
    """Expiration-proximity feature contract with absent-metadata flags."""


@dataclass(frozen=True, slots=True)
class StatusFeatureSpec(SessionFeatureSpec):
    """Status and halt flag feature contract with absent-metadata flags."""


@dataclass(frozen=True, slots=True)
class SessionFeatureDefinition:
    """Approved, versioned Session / Calendar / Roll feature definition."""

    name: SessionFeatureName
    spec: SessionFeatureSpec
    version: FeatureVersion
    request_gate_decision: FeatureRequestGateDecision

    @property
    def feature_id(self) -> str:
        """Return the stable feature id from the bound contract."""

        return self.spec.feature_id

    @property
    def feature_version_id(self) -> str:
        """Return the deterministic feature-version id."""

        return self.version.feature_version_id


@dataclass(frozen=True, slots=True)
class _FeaturePoint:
    row: TradeBarRow
    value: int | float | str | None
    quality_flags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class _RollProximity:
    bars_to_roll: int | None
    minutes_to_roll: int | None


_SESSION_POSITION_FEATURES = frozenset(
    {
        SessionFeatureName.SESSION_ID,
        SessionFeatureName.MINUTES_FROM_RTH_OPEN,
        SessionFeatureName.MINUTES_TO_RTH_CLOSE,
        SessionFeatureName.RTH_SEGMENT_FLAG,
        SessionFeatureName.ETH_SEGMENT_FLAG,
    }
)
_CALENDAR_FEATURES = frozenset({SessionFeatureName.DAY_OF_WEEK})
_ROLL_FEATURES = frozenset(
    {
        SessionFeatureName.BARS_TO_ROLL,
        SessionFeatureName.MINUTES_TO_ROLL,
    }
)
_EXPIRATION_FEATURES = frozenset({SessionFeatureName.MINUTES_TO_EXPIRATION})
_STATUS_FEATURES = frozenset({SessionFeatureName.HALT_STATUS_FLAG})
_HALT_STATUS_TOKENS = frozenset(
    {
        "halt",
        "halted",
        "paused",
        "suspended",
        "trading_halt",
        "trading_halted",
    }
)
_INPUT_FIELDS_BY_FEATURE: dict[SessionFeatureName, tuple[str, ...]] = {
    SessionFeatureName.SESSION_ID: ("series_id", "session_label", "bar_start_ts"),
    SessionFeatureName.MINUTES_FROM_RTH_OPEN: ("session_label", "bar_start_ts"),
    SessionFeatureName.MINUTES_TO_RTH_CLOSE: ("session_label", "bar_start_ts"),
    SessionFeatureName.RTH_SEGMENT_FLAG: ("session_label",),
    SessionFeatureName.ETH_SEGMENT_FLAG: ("session_label",),
    SessionFeatureName.DAY_OF_WEEK: ("bar_start_ts",),
    SessionFeatureName.BARS_TO_ROLL: ("contract_id", "series_id", "bar_start_ts"),
    SessionFeatureName.MINUTES_TO_ROLL: ("contract_id", "series_id", "bar_start_ts"),
    SessionFeatureName.MINUTES_TO_EXPIRATION: ("contract_id", "bar_start_ts"),
    SessionFeatureName.HALT_STATUS_FLAG: ("available_ts",),
}


def supported_session_features() -> tuple[SessionFeatureName, ...]:
    """Return the complete FLF-P10 Session / Calendar / Roll feature list."""

    return tuple(SessionFeatureName)


def row_key(row: TradeBarRow) -> str:
    """Return a deterministic key for optional row-level metadata."""

    return f"{row.series_id}|{row.contract_id}|{row.available_ts.isoformat()}"


def build_session_feature_definition(
    name: SessionFeatureName | str,
    feature_request: FeatureRequest | Mapping[str, Any] | None,
    registry_reader: RegistryReader | object | None,
    *,
    dataset_version_ids: Sequence[str] = (),
    rth_open_time: str = "14:30",
    rth_close_time: str = "21:00",
    input_view_name: str = "canonical_ohlcv",
    input_scope: Mapping[str, Any] | None = None,
    window: WindowSpec | None = None,
) -> SessionFeatureDefinition:
    """Build one approved Session / Calendar / Roll feature definition.

    The FLF-P05 request gate is the only admission path. Missing, invalid,
    unapproved, duplicate-blocked, or registry-unchecked requests fail closed.
    """

    feature_name = _coerce_feature_name(name)
    open_time = _parse_clock_time(rth_open_time, "rth_open_time")
    close_time = _parse_clock_time(rth_close_time, "rth_close_time")
    input_view = _input_view_name(input_view_name)
    if close_time <= open_time:
        raise SessionFeatureError("rth_close_time must be after rth_open_time")

    gate_decision = require_feature_request_implementation_allowed(
        feature_request,
        registry_reader,
    )
    spec = _feature_spec(
        feature_name,
        gate_decision,
        dataset_version_ids=dataset_version_ids,
        rth_open_time=open_time,
        rth_close_time=close_time,
        input_view_name=input_view,
        input_scope=input_scope,
        window=window,
    )
    return SessionFeatureDefinition(
        name=feature_name,
        spec=spec,
        version=spec.derive_feature_version(),
        request_gate_decision=gate_decision,
    )


def build_session_feature_definitions(
    feature_requests: Mapping[SessionFeatureName | str, FeatureRequest | Mapping[str, Any]],
    registry_reader: RegistryReader | object | None,
    **parameters: Any,
) -> tuple[SessionFeatureDefinition, ...]:
    """Build multiple approved Session / Calendar / Roll feature definitions."""

    return tuple(
        build_session_feature_definition(name, request, registry_reader, **parameters)
        for name, request in feature_requests.items()
    )


def compute_session_feature(
    definition: SessionFeatureDefinition,
    input_view: OHLCVInputView | CanonicalInputViews | Iterable[TradeBarRow],
    metadata: SessionCalendarRollMetadata | Mapping[str, object] | None = None,
) -> tuple[FeatureValueRecord, ...]:
    """Compute one Session / Calendar / Roll feature as in-memory value records.

    Values are returned only to the caller. This function does not materialize,
    persist, register, read provider data, or write feature values.
    """

    definition = _require_definition(definition)
    rows = _validated_rows(_coerce_rows(input_view))
    metadata = _coerce_metadata(metadata)
    roll_proximity = _roll_proximity_by_row(rows)
    return _records_from_points(
        definition,
        tuple(_feature_point(definition, row, metadata, roll_proximity) for row in rows),
    )


def compute_session_features(
    definitions: Iterable[SessionFeatureDefinition],
    input_view: OHLCVInputView | CanonicalInputViews | Iterable[TradeBarRow],
    metadata: SessionCalendarRollMetadata | Mapping[str, object] | None = None,
) -> dict[SessionFeatureName, tuple[FeatureValueRecord, ...]]:
    """Compute approved Session definitions against canonical OHLCV rows."""

    return {
        definition.name: compute_session_feature(definition, input_view, metadata)
        for definition in definitions
    }


def _feature_spec(
    name: SessionFeatureName,
    gate_decision: FeatureRequestGateDecision,
    *,
    dataset_version_ids: Sequence[str],
    rth_open_time: time,
    rth_close_time: time,
    input_view_name: str,
    input_scope: Mapping[str, Any] | None,
    window: WindowSpec | None,
) -> SessionFeatureSpec:
    if gate_decision.feature_request_id is None:
        raise SessionFeatureError("approved FeatureRequestGateDecision must expose freq_ id")
    feature_window = window or WindowSpec(
        kind=WindowKind.POINT_IN_TIME,
        length=1,
        causality=WindowCausality.CAUSAL,
        offline_only=False,
    )
    parameters = {
        "feature_name": name.value,
        "rth_open_time_utc": _clock_time_text(rth_open_time),
        "rth_close_time_utc": _clock_time_text(rth_close_time),
        "roll_transition_source": "contract_id_or_series_id_transition",
        "metadata_absence_policy": "flag_absent_never_fabricate",
    }
    feature_spec = FeatureSpec(
        feature_id=f"session_calendar_roll_{name.value}",
        family=FeatureFamily.SESSION_CALENDAR_ROLL,
        feature_request_id=gate_decision.feature_request_id,
        inputs=FeatureInputSpec(
            input_views=(input_view_name,),
            fields=_input_fields(name),
            dataset_version_ids=tuple(dataset_version_ids),
            input_metadata=_input_metadata(
                {
                "consumption_surface": (
                    "alpha_system.features.input_views.OHLCVInputView; FUTSUB-P07 may "
                    "bind dense_grid_ohlcv so FLF-P01 DenseGridBarRecord objects are "
                    "reconstructed through the materialization engine"
                ),
                "optional_metadata": [
                    "expiration_ts_by_contract_id",
                    "status_by_row_key",
                    "status_by_available_ts",
                    "expiration_available_ts_by_contract_id",
                    "status_available_ts_by_row_key",
                    "status_available_ts_by_available_ts",
                ],
                "trade_semantics": (
                    "FLF-P04 synthetic no-trade rows retain session/calendar position "
                    "but are flagged as position-only rows, not trade bars"
                ),
                "session_metadata_role": "SESSION_METADATA_POINT_IN_TIME",
                },
                input_scope=input_scope,
            ),
        ),
        transform=TransformSpec(
            transform_id=_transform_id(name),
            parameters=parameters,
        ),
        window=feature_window,
        normalization=NormalizationSpec(normalization_id="identity"),
        availability_assumptions={
            "input": "canonical OHLCV rows are accepted-DatasetVersion input-view rows",
            "causality": "outputs use the current row availability timestamp",
            "calendar_metadata": (
                "RTH clock times, contract roll transitions, expiration, and status "
                "metadata are treated as calendar/definition/status metadata"
            ),
            "session_metadata_role_guard": (
                "optional metadata carrying explicit metadata availability must be "
                "known at or before the row available_ts"
            ),
            "absence": "missing expiration or status metadata yields None with absent flags",
        },
        available_ts_derivation_rule=(
            "feature.available_ts = current input row available_ts; feature values do "
            "not use event_ts or ingested_at as availability substitutes"
        ),
        live=True,
        implementation_eligible=True,
        contract_metadata={
            "campaign": "ALPHA_FEATURE_LABEL_FOUNDATION_V1",
            "phase": "FLF-P10",
            "materialization": "in_memory_records_only",
            "claims": "session_calendar_roll_substrate_only_no_alpha_or_tradability_claim",
            "session_metadata_role": "SESSION_METADATA_POINT_IN_TIME",
        },
        request_gate_decision=gate_decision,
    )
    return _wrap_feature_spec(name, feature_spec)


def _wrap_feature_spec(name: SessionFeatureName, feature_spec: FeatureSpec) -> SessionFeatureSpec:
    if name in _SESSION_POSITION_FEATURES:
        return SessionPositionFeatureSpec(feature_spec=feature_spec, feature_name=name)
    if name in _CALENDAR_FEATURES:
        return CalendarFeatureSpec(feature_spec=feature_spec, feature_name=name)
    if name in _ROLL_FEATURES:
        return RollFeatureSpec(feature_spec=feature_spec, feature_name=name)
    if name in _EXPIRATION_FEATURES:
        return ExpirationFeatureSpec(feature_spec=feature_spec, feature_name=name)
    if name in _STATUS_FEATURES:
        return StatusFeatureSpec(feature_spec=feature_spec, feature_name=name)
    return SessionFeatureSpec(feature_spec=feature_spec, feature_name=name)


def _transform_id(name: SessionFeatureName) -> str:
    return {
        SessionFeatureName.SESSION_ID: "session_id",
        SessionFeatureName.MINUTES_FROM_RTH_OPEN: "minutes_from_rth_open",
        SessionFeatureName.MINUTES_TO_RTH_CLOSE: "minutes_to_rth_close",
        SessionFeatureName.RTH_SEGMENT_FLAG: "rth_segment_flag",
        SessionFeatureName.ETH_SEGMENT_FLAG: "eth_segment_flag",
        SessionFeatureName.DAY_OF_WEEK: "day_of_week",
        SessionFeatureName.BARS_TO_ROLL: "bars_to_roll",
        SessionFeatureName.MINUTES_TO_ROLL: "minutes_to_roll",
        SessionFeatureName.MINUTES_TO_EXPIRATION: "minutes_to_expiration",
        SessionFeatureName.HALT_STATUS_FLAG: "halt_status_flag",
    }[name]


def _input_fields(name: SessionFeatureName) -> tuple[str, ...]:
    base = (
        "instrument_id",
        "contract_id",
        "series_id",
        "bar_start_ts",
        "bar_end_ts",
        "event_ts",
        "available_ts",
        "session_label",
        "quality_flags",
    )
    return tuple(dict.fromkeys((*base, *_INPUT_FIELDS_BY_FEATURE[name])))


def _coerce_rows(
    input_view: OHLCVInputView | CanonicalInputViews | Iterable[TradeBarRow],
) -> tuple[TradeBarRow, ...]:
    if isinstance(input_view, CanonicalInputViews):
        return tuple(input_view.ohlcv.rows)
    if isinstance(input_view, OHLCVInputView):
        return tuple(input_view.rows)
    if isinstance(input_view, Iterable) and not isinstance(input_view, str):
        return tuple(input_view)
    raise SessionFeatureError(
        "Session features require an OHLCVInputView, CanonicalInputViews, or trade rows"
    )


def _coerce_metadata(
    metadata: SessionCalendarRollMetadata | Mapping[str, object] | None,
) -> SessionCalendarRollMetadata:
    if metadata is None:
        return SessionCalendarRollMetadata()
    if isinstance(metadata, SessionCalendarRollMetadata):
        return metadata
    if isinstance(metadata, Mapping):
        return SessionCalendarRollMetadata(
            expiration_ts_by_contract_id=_mapping_value(
                metadata,
                "expiration_ts_by_contract_id",
            ),
            status_by_row_key=_mapping_value(metadata, "status_by_row_key"),
            status_by_available_ts=_mapping_value(metadata, "status_by_available_ts"),
            expiration_available_ts_by_contract_id=_mapping_value(
                metadata,
                "expiration_available_ts_by_contract_id",
            ),
            status_available_ts_by_row_key=_mapping_value(
                metadata,
                "status_available_ts_by_row_key",
            ),
            status_available_ts_by_available_ts=_mapping_value(
                metadata,
                "status_available_ts_by_available_ts",
            ),
        )
    raise SessionFeatureError("metadata must be SessionCalendarRollMetadata or a mapping")


def _mapping_value(values: Mapping[str, object], key: str) -> Mapping[Any, Any]:
    value = values.get(key, {})
    if not isinstance(value, Mapping):
        raise SessionFeatureError(f"metadata.{key} must be a mapping")
    return value


def _validated_rows(rows: Sequence[TradeBarRow]) -> tuple[TradeBarRow, ...]:
    ordered = tuple(rows)
    for row in ordered:
        _validate_trade_row(row)
    return tuple(sorted(ordered, key=lambda row: row.available_ts))


def _validate_trade_row(row: TradeBarRow) -> None:
    if not isinstance(row, OHLCVInputRow | DenseGridBarRecord):
        raise SessionFeatureError("Session feature inputs must be OHLCV or DenseGrid rows")
    _require_aware_datetime(row.available_ts, "trade_row.available_ts")
    _require_aware_datetime(row.event_ts, "trade_row.event_ts")
    _require_aware_datetime(row.bar_start_ts, "trade_row.bar_start_ts")
    _require_aware_datetime(row.bar_end_ts, "trade_row.bar_end_ts")
    if row.available_ts < row.bar_end_ts:
        raise SessionFeatureError("trade_row.available_ts must be >= bar_end_ts")
    _require_text(row.instrument_id, "trade_row.instrument_id")
    _require_text(row.contract_id, "trade_row.contract_id")
    _require_text(row.series_id, "trade_row.series_id")
    _require_text(row.session_label, "trade_row.session_label")
    _quality_flags(row.quality_flags)
    try:
        is_real_trade_bar(row)
        is_synthetic_no_trade_bar(row)
    except DataFoundationValidationError as exc:
        raise SessionFeatureError(str(exc)) from exc


def _require_definition(definition: SessionFeatureDefinition) -> SessionFeatureDefinition:
    if not isinstance(definition, SessionFeatureDefinition):
        raise SessionFeatureError("compute requires a SessionFeatureDefinition")
    if definition.spec.family is not FeatureFamily.SESSION_CALENDAR_ROLL:
        raise SessionFeatureError("definition must belong to FeatureFamily.SESSION_CALENDAR_ROLL")
    if not definition.spec.implementation_eligible:
        raise SessionFeatureError("definition is not implementation eligible")
    if not definition.request_gate_decision.implementation_allowed:
        raise SessionFeatureError("FeatureRequest gate did not admit implementation")
    if definition.version != definition.spec.derive_feature_version():
        raise SessionFeatureError("definition FeatureVersion does not match FeatureSpec")
    if not definition.spec.window.is_live_compatible:
        raise SessionFeatureError("Session live features require causal windows")
    return definition


def _records_from_points(
    definition: SessionFeatureDefinition,
    points: Sequence[_FeaturePoint],
) -> tuple[FeatureValueRecord, ...]:
    return tuple(
        FeatureValueRecord(
            feature_version_id=definition.feature_version_id,
            entity_id=point.row.series_id,
            event_ts=point.row.event_ts,
            available_ts=point.row.available_ts,
            value=point.value,
            quality_flags=_quality_flags(point.quality_flags),
        )
        for point in points
    )


def _feature_point(
    definition: SessionFeatureDefinition,
    row: TradeBarRow,
    metadata: SessionCalendarRollMetadata,
    roll_proximity: Mapping[int, _RollProximity],
) -> _FeaturePoint:
    name = definition.name
    if name is SessionFeatureName.SESSION_ID:
        value = f"{row.series_id}:{row.bar_start_ts.date().isoformat()}:{_session_label(row)}"
        return _point(row, value)
    if name is SessionFeatureName.MINUTES_FROM_RTH_OPEN:
        return _rth_minutes_point(row, definition, from_open=True)
    if name is SessionFeatureName.MINUTES_TO_RTH_CLOSE:
        return _rth_minutes_point(row, definition, from_open=False)
    if name is SessionFeatureName.RTH_SEGMENT_FLAG:
        return _point(row, 1 if _session_label(row) == "RTH" else 0)
    if name is SessionFeatureName.ETH_SEGMENT_FLAG:
        return _point(row, 1 if _session_label(row) == "ETH" else 0)
    if name is SessionFeatureName.DAY_OF_WEEK:
        return _point(row, row.bar_start_ts.weekday())
    if name is SessionFeatureName.BARS_TO_ROLL:
        proximity = roll_proximity[id(row)]
        return _roll_point(row, proximity.bars_to_roll)
    if name is SessionFeatureName.MINUTES_TO_ROLL:
        proximity = roll_proximity[id(row)]
        return _roll_point(row, proximity.minutes_to_roll)
    if name is SessionFeatureName.MINUTES_TO_EXPIRATION:
        return _expiration_point(row, metadata)
    if name is SessionFeatureName.HALT_STATUS_FLAG:
        return _halt_status_point(row, metadata)
    raise SessionFeatureError(f"unsupported Session feature: {definition.name}")


def _point(
    row: TradeBarRow,
    value: int | float | str | None,
    quality_flags: Sequence[str] = (),
) -> _FeaturePoint:
    return _FeaturePoint(
        row=row,
        value=value,
        quality_flags=_row_semantic_flags(row, quality_flags),
    )


def _rth_minutes_point(
    row: TradeBarRow,
    definition: SessionFeatureDefinition,
    *,
    from_open: bool,
) -> _FeaturePoint:
    if _session_label(row) != "RTH":
        return _point(row, None, ("outside_rth",))
    rth_open = _time_parameter(definition, "rth_open_time_utc")
    rth_close = _time_parameter(definition, "rth_close_time_utc")
    session_date = row.bar_start_ts.date()
    open_dt = _combine_session_time(session_date, rth_open, row.bar_start_ts)
    close_dt = _combine_session_time(session_date, rth_close, row.bar_start_ts)
    if from_open:
        minutes = _minutes_between(open_dt, row.bar_start_ts)
        return _non_negative_point(row, minutes, "before_rth_open")
    minutes = _minutes_between(row.bar_start_ts, close_dt)
    return _non_negative_point(row, minutes, "after_rth_close")


def _expiration_point(
    row: TradeBarRow,
    metadata: SessionCalendarRollMetadata,
) -> _FeaturePoint:
    expiration_ts = metadata.expiration_for(row)
    if expiration_ts is None:
        return _point(row, None, ("expiration_metadata_absent",))
    minutes = _minutes_between(row.bar_start_ts, expiration_ts)
    return _non_negative_point(row, minutes, "expiration_elapsed")


def _halt_status_point(
    row: TradeBarRow,
    metadata: SessionCalendarRollMetadata,
) -> _FeaturePoint:
    status = metadata.status_for(row)
    if status is None:
        return _point(row, None, ("status_metadata_absent",))
    quality_flags = (f"status_{status}",)
    return _point(row, 1 if status in _HALT_STATUS_TOKENS else 0, quality_flags)


def _roll_point(row: TradeBarRow, value: int | None) -> _FeaturePoint:
    if value is None:
        return _point(row, None, ("roll_transition_absent",))
    return _point(row, value)


def _non_negative_point(row: TradeBarRow, value: int, negative_flag: str) -> _FeaturePoint:
    if value < 0:
        return _point(row, None, (negative_flag,))
    return _point(row, value)


def _roll_proximity_by_row(rows: Sequence[TradeBarRow]) -> Mapping[int, _RollProximity]:
    by_instrument: dict[str, list[TradeBarRow]] = {}
    for row in rows:
        by_instrument.setdefault(row.instrument_id, []).append(row)

    proximity: dict[int, _RollProximity] = {}
    for instrument_rows in by_instrument.values():
        chronological = sorted(
            instrument_rows,
            key=lambda row: (row.bar_start_ts, row.available_ts),
        )
        for index, row in enumerate(chronological):
            target = _next_roll_transition(chronological, index)
            if target is None:
                proximity[id(row)] = _RollProximity(None, None)
                continue
            bars_to_roll = target - index
            minutes_to_roll = _minutes_between(row.bar_start_ts, chronological[target].bar_start_ts)
            proximity[id(row)] = _RollProximity(bars_to_roll, minutes_to_roll)
    return MappingProxyType(proximity)


def _next_roll_transition(rows: Sequence[TradeBarRow], index: int) -> int | None:
    current = rows[index]
    current_key = (current.contract_id, current.series_id)
    for candidate_index in range(index + 1, len(rows)):
        candidate = rows[candidate_index]
        if (candidate.contract_id, candidate.series_id) != current_key:
            return candidate_index
    return None


def _row_semantic_flags(row: TradeBarRow, extra_flags: Sequence[str] = ()) -> tuple[str, ...]:
    flags = set(_quality_flags(row.quality_flags))
    try:
        if is_synthetic_no_trade_bar(row):
            flags.add("synthetic_no_trade_position_only")
        elif not is_real_trade_bar(row) and "no_trade" in flags:
            flags.add("no_trade_position_only")
    except DataFoundationValidationError as exc:
        raise SessionFeatureError(str(exc)) from exc
    flags.update(_quality_flags(extra_flags))
    return tuple(sorted(flags))


def _session_label(row: TradeBarRow) -> str:
    return _require_text(row.session_label, "trade_row.session_label").upper()


def _time_parameter(definition: SessionFeatureDefinition, name: str) -> time:
    value = definition.spec.transform.parameters.to_dict().get(name)
    if not isinstance(value, str):
        raise SessionFeatureError(f"{name} parameter must be HH:MM text")
    return _parse_clock_time(value, name)


def _parse_clock_time(value: str, field_name: str) -> time:
    text = _require_text(value, field_name)
    parts = text.split(":")
    if len(parts) != 2:
        raise SessionFeatureError(f"{field_name} must use HH:MM format")
    try:
        hour = int(parts[0], 10)
        minute = int(parts[1], 10)
    except ValueError as exc:
        raise SessionFeatureError(f"{field_name} must use HH:MM format") from exc
    try:
        return time(hour=hour, minute=minute)
    except ValueError as exc:
        raise SessionFeatureError(f"{field_name} must use a valid clock time") from exc


def _clock_time_text(value: time) -> str:
    return f"{value.hour:02d}:{value.minute:02d}"


def _combine_session_time(session_date: date, session_time: time, reference: datetime) -> datetime:
    return datetime.combine(session_date, session_time, tzinfo=reference.tzinfo)


def _minutes_between(start: datetime, end: datetime) -> int:
    return math.floor((end - start).total_seconds() / 60)


def _coerce_feature_name(name: SessionFeatureName | str) -> SessionFeatureName:
    try:
        return name if isinstance(name, SessionFeatureName) else SessionFeatureName(str(name))
    except ValueError as exc:
        raise SessionFeatureError(f"unsupported Session feature: {name}") from exc


def _input_metadata(
    metadata: Mapping[str, Any],
    *,
    input_scope: Mapping[str, Any] | None,
) -> dict[str, object]:
    payload: dict[str, object] = dict(metadata)
    if input_scope:
        payload["input_scope"] = {str(key): value for key, value in input_scope.items()}
    return payload


def _input_view_name(value: str) -> str:
    text = _require_text(value, "input_view_name")
    if text not in {"canonical_ohlcv", "dense_grid_ohlcv"}:
        raise SessionFeatureError(
            "input_view_name must be canonical_ohlcv or dense_grid_ohlcv"
        )
    return text


def _require_metadata_known_as_of(
    metadata_available_ts: datetime | None,
    row: TradeBarRow,
    metadata_role: str,
) -> None:
    if metadata_available_ts is None:
        return
    available_ts = _require_aware_datetime(
        metadata_available_ts,
        f"{metadata_role}.available_ts",
    )
    row_available_ts = _require_aware_datetime(row.available_ts, "trade_row.available_ts")
    if available_ts > row_available_ts:
        raise SessionFeatureError(
            f"{metadata_role} available_ts must be <= trade_row.available_ts"
        )


def _normalize_status(value: object) -> str:
    text = _require_text(value, "status").lower().replace("-", "_").replace(" ", "_")
    if not text.replace("_", "").isalnum():
        raise SessionFeatureError("status metadata must be an alphanumeric label")
    return text


def _quality_flags(value: Sequence[str]) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, Iterable):
        raise SessionFeatureError("quality_flags must be an explicit collection of strings")
    flags: set[str] = set()
    for flag in value:
        flags.add(_require_text(flag, "quality_flags").lower())
    return tuple(sorted(flags))


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise SessionFeatureError(f"{field_name} must be a non-empty string")
    text = value.strip()
    if not text:
        raise SessionFeatureError(f"{field_name} must be a non-empty string")
    return text


def _require_aware_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise SessionFeatureError(f"{field_name} must be a timezone-aware datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise SessionFeatureError(f"{field_name} must be timezone-aware")
    return value


__all__ = [
    "CalendarFeatureSpec",
    "ExpirationFeatureSpec",
    "RollFeatureSpec",
    "SessionCalendarRollMetadata",
    "SessionFeatureDefinition",
    "SessionFeatureError",
    "SessionFeatureName",
    "SessionFeatureSpec",
    "SessionPositionFeatureSpec",
    "StatusFeatureSpec",
    "build_session_feature_definition",
    "build_session_feature_definitions",
    "compute_session_feature",
    "compute_session_features",
    "row_key",
    "supported_session_features",
]
