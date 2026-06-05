"""Session, calendar, roll, and expiration feature definitions."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from alpha_system.features.contracts import (
    FeatureFamily,
    FeatureInputSpec,
    FeatureSetSpec,
    FeatureSpec,
    FeatureValueRecord,
    FeatureVersion,
    NormalizationSpec,
    TransformSpec,
    WindowCausality,
    WindowKind,
    WindowSpec,
)
from alpha_system.features.input_views import (
    CanonicalInputViews,
    OHLCVInputRow,
    OHLCVInputView,
)
from alpha_system.features.request_gate import (
    FeatureRequestGateDecision,
    require_feature_request_implementation_allowed,
)
from alpha_system.features.semantics import is_real_trade_bar
from alpha_system.governance.duplicate_exposure import RegistryReader
from alpha_system.governance.feature_request import FeatureRequest


class SessionFeatureError(ValueError):
    """Raised when the session/calendar/roll family fails closed."""


class SessionFeatureName(StrEnum):
    """Supported Session / Calendar / Roll feature names for FLF-P10."""

    SESSION_ID = "session_id"
    MINUTES_FROM_RTH_OPEN = "minutes_from_rth_open"
    MINUTES_TO_RTH_CLOSE = "minutes_to_rth_close"
    RTH_SEGMENT_FLAG = "rth_segment_flag"
    ETH_SEGMENT_FLAG = "eth_segment_flag"
    DAY_OF_WEEK = "day_of_week"
    ROLL_PROXIMITY_MINUTES = "roll_proximity_minutes"
    EXPIRATION_PROXIMITY_MINUTES = "expiration_proximity_minutes"
    MARKET_STATUS = "market_status"
    HALT_FLAG = "halt_flag"


SESSION_FEATURE_FAMILY = FeatureFamily.SESSION_CALENDAR_ROLL


@dataclass(frozen=True, slots=True)
class SessionCalendarEntry:
    """Runtime schedule and contract metadata for one trading session."""

    session_id: str
    rth_open_ts: datetime
    rth_close_ts: datetime
    session_start_ts: datetime | None = None
    session_end_ts: datetime | None = None
    roll_ts: datetime | None = None
    expiration_ts: datetime | None = None
    market_status: str | None = None
    halt: bool | None = None

    def __post_init__(self) -> None:
        session_id = _require_text(self.session_id, "SessionCalendarEntry.session_id")
        rth_open_ts = _require_aware_datetime(self.rth_open_ts, "rth_open_ts")
        rth_close_ts = _require_aware_datetime(self.rth_close_ts, "rth_close_ts")
        if rth_close_ts <= rth_open_ts:
            raise SessionFeatureError("rth_close_ts must be after rth_open_ts")
        session_start_ts = (
            _require_aware_datetime(self.session_start_ts, "session_start_ts")
            if self.session_start_ts is not None
            else rth_open_ts
        )
        session_end_ts = (
            _require_aware_datetime(self.session_end_ts, "session_end_ts")
            if self.session_end_ts is not None
            else rth_close_ts
        )
        if session_start_ts > rth_open_ts:
            raise SessionFeatureError("session_start_ts must be at or before rth_open_ts")
        if session_end_ts < rth_close_ts:
            raise SessionFeatureError("session_end_ts must be at or after rth_close_ts")
        if session_end_ts <= session_start_ts:
            raise SessionFeatureError("session_end_ts must be after session_start_ts")
        roll_ts = (
            _require_aware_datetime(self.roll_ts, "roll_ts")
            if self.roll_ts is not None
            else None
        )
        expiration_ts = (
            _require_aware_datetime(self.expiration_ts, "expiration_ts")
            if self.expiration_ts is not None
            else None
        )
        market_status = _optional_text(self.market_status, "market_status")
        if self.halt is not None and type(self.halt) is not bool:
            raise SessionFeatureError("halt must be a bool when supplied")

        object.__setattr__(self, "session_id", session_id)
        object.__setattr__(self, "rth_open_ts", rth_open_ts)
        object.__setattr__(self, "rth_close_ts", rth_close_ts)
        object.__setattr__(self, "session_start_ts", session_start_ts)
        object.__setattr__(self, "session_end_ts", session_end_ts)
        object.__setattr__(self, "roll_ts", roll_ts)
        object.__setattr__(self, "expiration_ts", expiration_ts)
        object.__setattr__(self, "market_status", market_status)

    def contains(self, timestamp: datetime) -> bool:
        """Return whether the timestamp belongs to this session schedule entry."""

        value = _require_aware_datetime(timestamp, "timestamp")
        assert self.session_start_ts is not None
        assert self.session_end_ts is not None
        return self.session_start_ts <= value <= self.session_end_ts


@dataclass(frozen=True, slots=True)
class SessionCalendarMetadata:
    """In-memory session schedule and contract-definition metadata."""

    entries: Sequence[SessionCalendarEntry]

    def __post_init__(self) -> None:
        entries = tuple(_coerce_calendar_entry(entry) for entry in self.entries)
        if not entries:
            raise SessionFeatureError("SessionCalendarMetadata.entries must not be empty")
        duplicate_ids = _duplicates(entry.session_id for entry in entries)
        if duplicate_ids:
            raise SessionFeatureError(
                f"SessionCalendarMetadata duplicate session_id values: {', '.join(duplicate_ids)}"
            )
        object.__setattr__(
            self,
            "entries",
            tuple(sorted(entries, key=lambda entry: entry.session_start_ts or entry.rth_open_ts)),
        )

    @classmethod
    def from_mappings(
        cls,
        entries: Iterable[SessionCalendarEntry | Mapping[str, object]],
    ) -> SessionCalendarMetadata:
        """Build runtime metadata from deterministic in-memory mappings."""

        return cls(tuple(_coerce_calendar_entry(entry) for entry in entries))

    def entry_for_row(self, row: OHLCVInputRow) -> SessionCalendarEntry | None:
        """Return the schedule entry containing the row timestamp, if available."""

        for entry in self.entries:
            if entry.contains(row.bar_start_ts):
                return entry
        return None


@dataclass(frozen=True, slots=True)
class SessionFeatureDefinition:
    """Approved, versioned Session / Calendar / Roll feature definition."""

    name: SessionFeatureName
    spec: FeatureSpec
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
    row: OHLCVInputRow
    value: float | int | str | None
    quality_flags: tuple[str, ...] = ()


_SESSION_FIELDS_BY_FEATURE: dict[SessionFeatureName, tuple[str, ...]] = {
    SessionFeatureName.SESSION_ID: ("bar_start_ts", "bar_end_ts", "session_label"),
    SessionFeatureName.MINUTES_FROM_RTH_OPEN: (
        "bar_start_ts",
        "bar_end_ts",
        "session_label",
    ),
    SessionFeatureName.MINUTES_TO_RTH_CLOSE: (
        "bar_start_ts",
        "bar_end_ts",
        "session_label",
    ),
    SessionFeatureName.RTH_SEGMENT_FLAG: ("session_label",),
    SessionFeatureName.ETH_SEGMENT_FLAG: ("session_label",),
    SessionFeatureName.DAY_OF_WEEK: ("bar_start_ts",),
    SessionFeatureName.ROLL_PROXIMITY_MINUTES: ("bar_start_ts", "contract_id"),
    SessionFeatureName.EXPIRATION_PROXIMITY_MINUTES: ("bar_start_ts", "contract_id"),
    SessionFeatureName.MARKET_STATUS: ("bar_start_ts", "contract_id", "session_label"),
    SessionFeatureName.HALT_FLAG: ("bar_start_ts", "contract_id", "session_label"),
}


def supported_session_features() -> tuple[SessionFeatureName, ...]:
    """Return the complete FLF-P10 Session / Calendar / Roll feature list."""

    return tuple(SessionFeatureName)


def build_session_feature_definition(
    name: SessionFeatureName | str,
    feature_request: FeatureRequest | Mapping[str, Any] | None,
    registry_reader: RegistryReader | object | None,
    *,
    dataset_version_ids: Sequence[str] = (),
    calendar_id: str = "session_calendar_metadata",
    roll_policy_id: str = "contract_roll_metadata",
    definition_source_id: str = "contract_definition_metadata",
    status_source_id: str = "session_status_metadata",
    window: WindowSpec | None = None,
) -> SessionFeatureDefinition:
    """Build one approved Session / Calendar / Roll feature definition.

    The FLF-P05 request gate is the only admission path. Missing, invalid,
    unapproved, duplicate-blocked, or registry-unchecked requests fail closed.
    """

    feature_name = _coerce_feature_name(name)
    calendar_id = _require_text(calendar_id, "calendar_id")
    roll_policy_id = _require_text(roll_policy_id, "roll_policy_id")
    definition_source_id = _require_text(definition_source_id, "definition_source_id")
    status_source_id = _require_text(status_source_id, "status_source_id")

    gate_decision = require_feature_request_implementation_allowed(
        feature_request,
        registry_reader,
    )
    spec = _feature_spec(
        feature_name,
        gate_decision,
        dataset_version_ids=dataset_version_ids,
        calendar_id=calendar_id,
        roll_policy_id=roll_policy_id,
        definition_source_id=definition_source_id,
        status_source_id=status_source_id,
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


def build_session_feature_set_spec(
    definitions: Iterable[SessionFeatureDefinition],
    *,
    feature_set_id: str = "session_calendar_roll_family",
    feature_set_version: str = "v1",
) -> FeatureSetSpec:
    """Return an FLF-P06 grouping object for session-family definitions."""

    checked = tuple(_require_definition(definition) for definition in definitions)
    if not checked:
        raise SessionFeatureError("at least one SessionFeatureDefinition is required")
    return FeatureSetSpec(
        feature_set_id=feature_set_id,
        feature_set_version=feature_set_version,
        features=tuple(definition.spec for definition in checked),
        description="FLF-P10 Session / Calendar / Roll feature family",
        metadata={
            "family": SESSION_FEATURE_FAMILY.value,
            "campaign": "ALPHA_FEATURE_LABEL_FOUNDATION_V1",
            "phase": "FLF-P10",
            "materialization": "in_memory_records_only",
        },
    )


def compute_session_feature(
    definition: SessionFeatureDefinition,
    input_view: OHLCVInputView | CanonicalInputViews,
    calendar_metadata: SessionCalendarMetadata
    | Mapping[str, object]
    | Sequence[SessionCalendarEntry | Mapping[str, object]]
    | None = None,
) -> tuple[FeatureValueRecord, ...]:
    """Compute one session/calendar/roll feature as in-memory records only."""

    definition = _require_definition(definition)
    rows = _validated_rows(_coerce_ohlcv_view(input_view).rows)
    metadata = _coerce_calendar_metadata(calendar_metadata)
    return _records_from_points(
        definition,
        tuple(_feature_point(definition, row, metadata) for row in rows),
    )


def compute_session_features(
    definitions: Iterable[SessionFeatureDefinition],
    input_view: OHLCVInputView | CanonicalInputViews,
    calendar_metadata: SessionCalendarMetadata
    | Mapping[str, object]
    | Sequence[SessionCalendarEntry | Mapping[str, object]]
    | None = None,
) -> dict[SessionFeatureName, tuple[FeatureValueRecord, ...]]:
    """Compute approved session definitions against one canonical OHLCV view."""

    metadata = _coerce_calendar_metadata(calendar_metadata)
    return {
        definition.name: compute_session_feature(definition, input_view, metadata)
        for definition in definitions
    }


def _feature_spec(
    name: SessionFeatureName,
    gate_decision: FeatureRequestGateDecision,
    *,
    dataset_version_ids: Sequence[str],
    calendar_id: str,
    roll_policy_id: str,
    definition_source_id: str,
    status_source_id: str,
    window: WindowSpec | None,
) -> FeatureSpec:
    if gate_decision.feature_request_id is None:
        raise SessionFeatureError("approved FeatureRequestGateDecision must expose freq_ id")
    feature_window = window or WindowSpec(
        kind=WindowKind.POINT_IN_TIME,
        length=1,
        causality=WindowCausality.CAUSAL,
        offline_only=False,
    )
    return FeatureSpec(
        feature_id=f"session_calendar_roll_{name.value}",
        family=SESSION_FEATURE_FAMILY,
        feature_request_id=gate_decision.feature_request_id,
        inputs=FeatureInputSpec(
            input_views=("canonical_ohlcv",),
            fields=_input_fields(name),
            dataset_version_ids=tuple(dataset_version_ids),
            input_metadata={
                "consumption_surface": "alpha_system.features.input_views.OHLCVInputView",
                "calendar_metadata": calendar_id,
                "roll_policy_metadata": roll_policy_id,
                "definition_metadata": definition_source_id,
                "status_metadata": status_source_id,
                "unavailable_policy": "emit_none_with_quality_flag",
                "trade_semantics": "FLF-P04 no_trade rows remain flagged and are not trade bars",
            },
        ),
        transform=TransformSpec(
            transform_id=_transform_id(name),
            parameters={
                "feature_name": name.value,
                "calendar_id": calendar_id,
                "roll_policy_id": roll_policy_id,
                "definition_source_id": definition_source_id,
                "status_source_id": status_source_id,
                "unit": "minutes" if _is_proximity_feature(name) else "point_in_time",
                "unavailable_policy": "emit_none_with_quality_flag",
            },
        ),
        window=feature_window,
        normalization=NormalizationSpec(normalization_id="identity"),
        availability_assumptions={
            "input": "canonical OHLCV rows are accepted-DatasetVersion input-view rows",
            "schedule": "session, roll, expiration, and status context is deterministic metadata",
            "causality": "outputs do not inspect later trade or quote rows",
        },
        available_ts_derivation_rule=(
            "feature.available_ts = current input row available_ts; schedule and "
            "contract-definition metadata are treated as pre-known context and never "
            "derived from ingested_at, event_ts, or future trade/quote rows"
        ),
        live=True,
        implementation_eligible=True,
        contract_metadata={
            "campaign": "ALPHA_FEATURE_LABEL_FOUNDATION_V1",
            "phase": "FLF-P10",
            "materialization": "in_memory_records_only",
            "claims": "session_calendar_roll_substrate_only_no_alpha_or_tradability_claim",
        },
        request_gate_decision=gate_decision,
    )


def _transform_id(name: SessionFeatureName) -> str:
    return {
        SessionFeatureName.SESSION_ID: "session_id",
        SessionFeatureName.MINUTES_FROM_RTH_OPEN: "minutes_from_rth_open",
        SessionFeatureName.MINUTES_TO_RTH_CLOSE: "minutes_to_rth_close",
        SessionFeatureName.RTH_SEGMENT_FLAG: "rth_segment_flag",
        SessionFeatureName.ETH_SEGMENT_FLAG: "eth_segment_flag",
        SessionFeatureName.DAY_OF_WEEK: "day_of_week",
        SessionFeatureName.ROLL_PROXIMITY_MINUTES: "roll_proximity_minutes",
        SessionFeatureName.EXPIRATION_PROXIMITY_MINUTES: "expiration_proximity_minutes",
        SessionFeatureName.MARKET_STATUS: "market_status",
        SessionFeatureName.HALT_FLAG: "halt_flag",
    }[name]


def _input_fields(name: SessionFeatureName) -> tuple[str, ...]:
    base = (
        "available_ts",
        "event_ts",
        "series_id",
        "contract_id",
        "quality_flags",
    )
    return tuple(dict.fromkeys((*base, *_SESSION_FIELDS_BY_FEATURE[name])))


def _coerce_ohlcv_view(input_view: OHLCVInputView | CanonicalInputViews) -> OHLCVInputView:
    if isinstance(input_view, CanonicalInputViews):
        return input_view.ohlcv
    if isinstance(input_view, OHLCVInputView):
        return input_view
    raise SessionFeatureError("Session features require an OHLCVInputView")


def _validated_rows(rows: Sequence[OHLCVInputRow]) -> tuple[OHLCVInputRow, ...]:
    ordered = tuple(rows)
    for row in ordered:
        if not isinstance(row, OHLCVInputRow):
            raise SessionFeatureError("Session feature inputs must be OHLCVInputRow objects")
        _require_aware_datetime(row.available_ts, "OHLCVInputRow.available_ts")
        _require_aware_datetime(row.event_ts, "OHLCVInputRow.event_ts")
        _require_aware_datetime(row.bar_start_ts, "OHLCVInputRow.bar_start_ts")
        _require_aware_datetime(row.bar_end_ts, "OHLCVInputRow.bar_end_ts")
    return tuple(sorted(ordered, key=lambda row: row.available_ts))


def _require_definition(definition: SessionFeatureDefinition) -> SessionFeatureDefinition:
    if not isinstance(definition, SessionFeatureDefinition):
        raise SessionFeatureError("compute requires a SessionFeatureDefinition")
    if definition.spec.family is not SESSION_FEATURE_FAMILY:
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
    row: OHLCVInputRow,
    metadata: SessionCalendarMetadata | None,
) -> _FeaturePoint:
    name = definition.name
    entry = metadata.entry_for_row(row) if metadata is not None else None
    flags = set(_row_quality_flags(row))
    if name is SessionFeatureName.SESSION_ID:
        if entry is not None:
            return _FeaturePoint(row=row, value=entry.session_id, quality_flags=tuple(flags))
        flags.add("session_boundary_inferred")
        return _FeaturePoint(row=row, value=_fallback_session_id(row), quality_flags=tuple(flags))
    if name is SessionFeatureName.RTH_SEGMENT_FLAG:
        return _FeaturePoint(
            row=row,
            value=1 if row.session_label.upper() == "RTH" else 0,
            quality_flags=tuple(flags),
        )
    if name is SessionFeatureName.ETH_SEGMENT_FLAG:
        return _FeaturePoint(
            row=row,
            value=1 if row.session_label.upper() == "ETH" else 0,
            quality_flags=tuple(flags),
        )
    if name is SessionFeatureName.DAY_OF_WEEK:
        return _FeaturePoint(row=row, value=row.bar_start_ts.weekday(), quality_flags=tuple(flags))
    if entry is None:
        return _unavailable_point(row, _missing_entry_reason(name), flags)
    if name is SessionFeatureName.MINUTES_FROM_RTH_OPEN:
        return _FeaturePoint(
            row=row,
            value=_minutes_between(entry.rth_open_ts, row.bar_start_ts),
            quality_flags=tuple(flags),
        )
    if name is SessionFeatureName.MINUTES_TO_RTH_CLOSE:
        return _FeaturePoint(
            row=row,
            value=_minutes_between(row.bar_start_ts, entry.rth_close_ts),
            quality_flags=tuple(flags),
        )
    if name is SessionFeatureName.ROLL_PROXIMITY_MINUTES:
        if entry.roll_ts is None:
            return _unavailable_point(row, "roll_metadata_unavailable", flags)
        return _FeaturePoint(
            row=row,
            value=_minutes_between(row.bar_start_ts, entry.roll_ts),
            quality_flags=tuple(flags),
        )
    if name is SessionFeatureName.EXPIRATION_PROXIMITY_MINUTES:
        if entry.expiration_ts is None:
            return _unavailable_point(row, "expiration_metadata_unavailable", flags)
        return _FeaturePoint(
            row=row,
            value=_minutes_between(row.bar_start_ts, entry.expiration_ts),
            quality_flags=tuple(flags),
        )
    if name is SessionFeatureName.MARKET_STATUS:
        if entry.market_status is None:
            return _unavailable_point(row, "status_unavailable", flags)
        if entry.market_status.lower() not in {"open", "normal"}:
            flags.add("market_status_non_open")
        return _FeaturePoint(row=row, value=entry.market_status, quality_flags=tuple(flags))
    if name is SessionFeatureName.HALT_FLAG:
        if entry.halt is None:
            return _unavailable_point(row, "halt_unavailable", flags)
        if entry.halt:
            flags.add("halted")
        return _FeaturePoint(row=row, value=1 if entry.halt else 0, quality_flags=tuple(flags))
    raise SessionFeatureError(f"unsupported Session feature: {definition.name}")


def _unavailable_point(
    row: OHLCVInputRow,
    reason: str,
    flags: set[str],
) -> _FeaturePoint:
    flags.add(reason)
    flags.add("session_context_unavailable")
    return _FeaturePoint(row=row, value=None, quality_flags=tuple(flags))


def _missing_entry_reason(name: SessionFeatureName) -> str:
    if name in {
        SessionFeatureName.MINUTES_FROM_RTH_OPEN,
        SessionFeatureName.MINUTES_TO_RTH_CLOSE,
    }:
        return "rth_schedule_unavailable"
    if name is SessionFeatureName.ROLL_PROXIMITY_MINUTES:
        return "roll_metadata_unavailable"
    if name is SessionFeatureName.EXPIRATION_PROXIMITY_MINUTES:
        return "expiration_metadata_unavailable"
    if name is SessionFeatureName.MARKET_STATUS:
        return "status_unavailable"
    if name is SessionFeatureName.HALT_FLAG:
        return "halt_unavailable"
    return "session_context_unavailable"


def _row_quality_flags(row: OHLCVInputRow) -> tuple[str, ...]:
    flags = set(_quality_flags(row.quality_flags))
    if not is_real_trade_bar(row):
        flags.add("no_trade")
    return tuple(sorted(flags))


def _fallback_session_id(row: OHLCVInputRow) -> str:
    return f"{row.series_id}:{row.session_label.upper()}:{row.bar_start_ts.date().isoformat()}"


def _minutes_between(start: datetime, end: datetime) -> int:
    return int((end - start).total_seconds() // 60)


def _is_proximity_feature(name: SessionFeatureName) -> bool:
    return name in {
        SessionFeatureName.MINUTES_FROM_RTH_OPEN,
        SessionFeatureName.MINUTES_TO_RTH_CLOSE,
        SessionFeatureName.ROLL_PROXIMITY_MINUTES,
        SessionFeatureName.EXPIRATION_PROXIMITY_MINUTES,
    }


def _coerce_calendar_metadata(
    value: SessionCalendarMetadata
    | Mapping[str, object]
    | Sequence[SessionCalendarEntry | Mapping[str, object]]
    | None,
) -> SessionCalendarMetadata | None:
    if value is None:
        return None
    if isinstance(value, SessionCalendarMetadata):
        return value
    if isinstance(value, Mapping):
        entries = value.get("entries")
        if entries is None:
            raise SessionFeatureError("calendar metadata mapping requires entries")
        if isinstance(entries, str) or not isinstance(entries, Sequence):
            raise SessionFeatureError("calendar metadata entries must be a sequence")
        return SessionCalendarMetadata.from_mappings(entries)
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise SessionFeatureError("calendar metadata must be SessionCalendarMetadata or entries")
    return SessionCalendarMetadata.from_mappings(value)


def _coerce_calendar_entry(
    value: SessionCalendarEntry | Mapping[str, object],
) -> SessionCalendarEntry:
    if isinstance(value, SessionCalendarEntry):
        return value
    if not isinstance(value, Mapping):
        raise SessionFeatureError("calendar metadata entries must be mappings")
    return SessionCalendarEntry(
        session_id=_mapping_text(value, "session_id"),
        rth_open_ts=_mapping_datetime(value, "rth_open_ts"),
        rth_close_ts=_mapping_datetime(value, "rth_close_ts"),
        session_start_ts=_mapping_optional_datetime(value, "session_start_ts"),
        session_end_ts=_mapping_optional_datetime(value, "session_end_ts"),
        roll_ts=_mapping_optional_datetime(value, "roll_ts"),
        expiration_ts=_mapping_optional_datetime(value, "expiration_ts"),
        market_status=_mapping_optional_text(value, "market_status"),
        halt=_mapping_optional_bool(value, "halt"),
    )


def _mapping_text(value: Mapping[str, object], field_name: str) -> str:
    if field_name not in value:
        raise SessionFeatureError(f"calendar metadata requires {field_name}")
    return _require_text(value[field_name], field_name)


def _mapping_optional_text(value: Mapping[str, object], field_name: str) -> str | None:
    if field_name not in value or value[field_name] is None:
        return None
    return _require_text(value[field_name], field_name)


def _mapping_datetime(value: Mapping[str, object], field_name: str) -> datetime:
    if field_name not in value:
        raise SessionFeatureError(f"calendar metadata requires {field_name}")
    return _coerce_datetime(value[field_name], field_name)


def _mapping_optional_datetime(value: Mapping[str, object], field_name: str) -> datetime | None:
    if field_name not in value or value[field_name] is None:
        return None
    return _coerce_datetime(value[field_name], field_name)


def _mapping_optional_bool(value: Mapping[str, object], field_name: str) -> bool | None:
    if field_name not in value or value[field_name] is None:
        return None
    if type(value[field_name]) is not bool:
        raise SessionFeatureError(f"{field_name} must be a bool")
    return bool(value[field_name])


def _coerce_datetime(value: object, field_name: str) -> datetime:
    if isinstance(value, datetime):
        return _require_aware_datetime(value, field_name)
    if isinstance(value, str):
        try:
            return _require_aware_datetime(datetime.fromisoformat(value), field_name)
        except ValueError as exc:
            raise SessionFeatureError(f"{field_name} must be an ISO datetime") from exc
    raise SessionFeatureError(f"{field_name} must be a timezone-aware datetime")


def _coerce_feature_name(name: SessionFeatureName | str) -> SessionFeatureName:
    try:
        return SessionFeatureName(name)
    except ValueError as exc:
        raise SessionFeatureError(f"unsupported Session / Calendar / Roll feature: {name}") from exc


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise SessionFeatureError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise SessionFeatureError(f"{field_name} must be non-empty")
    return normalized


def _optional_text(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_text(value, field_name)


def _require_aware_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise SessionFeatureError(f"{field_name} must be a timezone-aware datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise SessionFeatureError(f"{field_name} must be timezone-aware")
    return value


def _quality_flags(flags: Sequence[str]) -> tuple[str, ...]:
    if isinstance(flags, str) or not isinstance(flags, Sequence):
        raise SessionFeatureError("quality_flags must be a sequence of strings")
    normalized: list[str] = []
    for flag in flags:
        if not isinstance(flag, str) or not flag.strip():
            raise SessionFeatureError("quality_flags must contain non-empty strings")
        token = flag.strip().lower()
        if token not in normalized:
            normalized.append(token)
    return tuple(normalized)


def _duplicates(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    return tuple(duplicates)


__all__ = [
    "SESSION_FEATURE_FAMILY",
    "SessionCalendarEntry",
    "SessionCalendarMetadata",
    "SessionFeatureDefinition",
    "SessionFeatureError",
    "SessionFeatureName",
    "build_session_feature_definition",
    "build_session_feature_definitions",
    "build_session_feature_set_spec",
    "compute_session_feature",
    "compute_session_features",
    "supported_session_features",
]
