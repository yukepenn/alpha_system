"""Causal BBO tradability feature definitions and in-memory calculations."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from alpha_system.data.foundation.quotes import (
    BBO_QUARANTINE_QUALITY_FLAG,
    MISSING_BBO_QUALITY_FLAG,
)
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
from alpha_system.features.input_views import BBOInputRow, BBOInputView, CanonicalInputViews
from alpha_system.features.primitives import PrimitivePoint, PrimitiveResult, causal_zscore
from alpha_system.features.request_gate import (
    FeatureRequestGateDecision,
    require_feature_request_implementation_allowed,
)
from alpha_system.features.semantics import BBOQuoteSemantics, bbo_quote_semantics
from alpha_system.governance.duplicate_exposure import RegistryReader
from alpha_system.governance.feature_request import FeatureRequest


class BBOFeatureError(ValueError):
    """Raised when BBO tradability family computation fails closed."""


class BBOFeatureName(StrEnum):
    """Supported BBO tradability feature names for FLF-P09."""

    MID = "mid"
    SPREAD = "spread"
    SPREAD_TICKS = "spread_ticks"
    SPREAD_BPS = "spread_bps"
    SPREAD_ZSCORE = "spread_zscore"
    BID_SIZE = "bid_size"
    ASK_SIZE = "ask_size"
    TOP_BOOK_DEPTH = "top_book_depth"
    TOP_BOOK_IMBALANCE = "top_book_imbalance"
    MICROPRICE = "microprice"
    MICROPRICE_MINUS_MID = "microprice_minus_mid"
    MISSING_BBO_FLAG = "missing_bbo_flag"
    BAD_QUOTE_FLAG = "bad_quote_flag"
    WIDE_SPREAD_FLAG = "wide_spread_flag"
    LOW_DEPTH_FLAG = "low_depth_flag"


@dataclass(frozen=True, slots=True)
class BBOFeatureSpec:
    """BBO family view over a governed FLF-P06 ``FeatureSpec``."""

    feature_spec: FeatureSpec
    feature_name: BBOFeatureName

    def __post_init__(self) -> None:
        if not isinstance(self.feature_spec, FeatureSpec):
            raise BBOFeatureError("BBOFeatureSpec.feature_spec must be a FeatureSpec")
        feature_name = _coerce_feature_name(self.feature_name)
        if self.feature_spec.family is not FeatureFamily.BBO_TRADABILITY:
            raise BBOFeatureError("BBOFeatureSpec requires FeatureFamily.BBO_TRADABILITY")
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
class SpreadFeatureSpec(BBOFeatureSpec):
    """BBO spread and spread-normalization feature contract."""


@dataclass(frozen=True, slots=True)
class MicropriceFeatureSpec(BBOFeatureSpec):
    """BBO microprice feature contract requiring valid top-book sizes."""


@dataclass(frozen=True, slots=True)
class TopBookImbalanceFeatureSpec(BBOFeatureSpec):
    """BBO top-book depth and imbalance feature contract."""


@dataclass(frozen=True, slots=True)
class LiquidityQualityFeatureSpec(BBOFeatureSpec):
    """BBO quote-quality flag feature contract."""


@dataclass(frozen=True, slots=True)
class BBOFeatureDefinition:
    """Approved, versioned BBO tradability feature definition."""

    name: BBOFeatureName
    spec: BBOFeatureSpec
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
    row: BBOInputRow
    value: float | int | None
    quality_flags: tuple[str, ...] = ()


type _Numeric = int | float | Decimal

_NUMERIC_TYPES = (int, float, Decimal)
_SPREAD_FEATURES = frozenset(
    {
        BBOFeatureName.SPREAD,
        BBOFeatureName.SPREAD_TICKS,
        BBOFeatureName.SPREAD_BPS,
        BBOFeatureName.SPREAD_ZSCORE,
    }
)
_MICROPRICE_FEATURES = frozenset(
    {
        BBOFeatureName.MICROPRICE,
        BBOFeatureName.MICROPRICE_MINUS_MID,
    }
)
_TOP_BOOK_FEATURES = frozenset(
    {
        BBOFeatureName.BID_SIZE,
        BBOFeatureName.ASK_SIZE,
        BBOFeatureName.TOP_BOOK_DEPTH,
        BBOFeatureName.TOP_BOOK_IMBALANCE,
    }
)
_QUALITY_FEATURES = frozenset(
    {
        BBOFeatureName.MISSING_BBO_FLAG,
        BBOFeatureName.BAD_QUOTE_FLAG,
        BBOFeatureName.WIDE_SPREAD_FLAG,
        BBOFeatureName.LOW_DEPTH_FLAG,
    }
)
_BBO_FIELDS_BY_FEATURE: dict[BBOFeatureName, tuple[str, ...]] = {
    BBOFeatureName.MID: ("mid",),
    BBOFeatureName.SPREAD: ("spread",),
    BBOFeatureName.SPREAD_TICKS: ("spread_ticks",),
    BBOFeatureName.SPREAD_BPS: ("mid", "spread"),
    BBOFeatureName.SPREAD_ZSCORE: ("spread", "session_label"),
    BBOFeatureName.BID_SIZE: ("bid_size",),
    BBOFeatureName.ASK_SIZE: ("ask_size",),
    BBOFeatureName.TOP_BOOK_DEPTH: ("bid_size", "ask_size"),
    BBOFeatureName.TOP_BOOK_IMBALANCE: ("bid_size", "ask_size"),
    BBOFeatureName.MICROPRICE: ("bid", "ask", "bid_size", "ask_size", "microprice"),
    BBOFeatureName.MICROPRICE_MINUS_MID: (
        "bid",
        "ask",
        "bid_size",
        "ask_size",
        "mid",
        "microprice",
    ),
    BBOFeatureName.MISSING_BBO_FLAG: ("quality_flags",),
    BBOFeatureName.BAD_QUOTE_FLAG: ("quality_flags",),
    BBOFeatureName.WIDE_SPREAD_FLAG: ("mid", "spread", "quality_flags"),
    BBOFeatureName.LOW_DEPTH_FLAG: ("bid_size", "ask_size", "quality_flags"),
}


def supported_bbo_features() -> tuple[BBOFeatureName, ...]:
    """Return the complete FLF-P09 BBO tradability feature list."""

    return tuple(BBOFeatureName)


def build_bbo_feature_definition(
    name: BBOFeatureName | str,
    feature_request: FeatureRequest | Mapping[str, Any] | None,
    registry_reader: RegistryReader | object | None,
    *,
    dataset_version_ids: Sequence[str] = (),
    window_length: int = 3,
    wide_spread_bps_threshold: float = 25.0,
    low_depth_threshold: float = 1.0,
    reset_on_session: bool = True,
    ddof: int = 0,
    window: WindowSpec | None = None,
) -> BBOFeatureDefinition:
    """Build one approved BBO tradability feature definition.

    The FLF-P05 request gate is the only admission path. Missing, invalid,
    unapproved, duplicate-blocked, or registry-unchecked requests fail closed.
    """

    feature_name = _coerce_feature_name(name)
    window_length = _positive_int(window_length, "window_length")
    wide_spread_bps_threshold = _non_negative_float(
        wide_spread_bps_threshold,
        "wide_spread_bps_threshold",
    )
    low_depth_threshold = _non_negative_float(low_depth_threshold, "low_depth_threshold")
    if type(reset_on_session) is not bool:
        raise BBOFeatureError("reset_on_session must be a bool")
    ddof = _non_negative_int(ddof, "ddof")

    gate_decision = require_feature_request_implementation_allowed(
        feature_request,
        registry_reader,
    )
    spec = _feature_spec(
        feature_name,
        gate_decision,
        dataset_version_ids=dataset_version_ids,
        window_length=window_length,
        wide_spread_bps_threshold=wide_spread_bps_threshold,
        low_depth_threshold=low_depth_threshold,
        reset_on_session=reset_on_session,
        ddof=ddof,
        window=window,
    )
    return BBOFeatureDefinition(
        name=feature_name,
        spec=spec,
        version=spec.derive_feature_version(),
        request_gate_decision=gate_decision,
    )


def build_bbo_feature_definitions(
    feature_requests: Mapping[BBOFeatureName | str, FeatureRequest | Mapping[str, Any]],
    registry_reader: RegistryReader | object | None,
    **parameters: Any,
) -> tuple[BBOFeatureDefinition, ...]:
    """Build multiple approved BBO tradability feature definitions."""

    return tuple(
        build_bbo_feature_definition(name, request, registry_reader, **parameters)
        for name, request in feature_requests.items()
    )


def compute_bbo_feature(
    definition: BBOFeatureDefinition,
    input_view: BBOInputView | CanonicalInputViews,
) -> tuple[FeatureValueRecord, ...]:
    """Compute one BBO tradability feature as in-memory value records.

    Values are returned only to the caller. This function does not materialize,
    persist, register, or write feature values.
    """

    definition = _require_definition(definition)
    rows = _validated_rows(_coerce_bbo_view(input_view).rows)
    if definition.name is BBOFeatureName.SPREAD_ZSCORE:
        return _records_from_primitive_results(
            definition,
            rows,
            causal_zscore(
                _points_from_valid_bbo_rows(rows, "spread"),
                definition.spec.window,
                ddof=_int_parameter(definition, "ddof"),
                reset_on_session=_bool_parameter(definition, "reset_on_session"),
            ),
        )
    return _records_from_points(definition, _feature_points(definition, rows))


def compute_bbo_features(
    definitions: Iterable[BBOFeatureDefinition],
    input_view: BBOInputView | CanonicalInputViews,
) -> dict[BBOFeatureName, tuple[FeatureValueRecord, ...]]:
    """Compute approved BBO definitions against one canonical BBO view."""

    return {
        definition.name: compute_bbo_feature(definition, input_view)
        for definition in definitions
    }


def _feature_spec(
    name: BBOFeatureName,
    gate_decision: FeatureRequestGateDecision,
    *,
    dataset_version_ids: Sequence[str],
    window_length: int,
    wide_spread_bps_threshold: float,
    low_depth_threshold: float,
    reset_on_session: bool,
    ddof: int,
    window: WindowSpec | None,
) -> BBOFeatureSpec:
    if gate_decision.feature_request_id is None:
        raise BBOFeatureError("approved FeatureRequestGateDecision must expose freq_ id")
    feature_window = window or _default_window(name, window_length=window_length)
    parameters = _transform_parameters(
        name,
        window_length=window_length,
        wide_spread_bps_threshold=wide_spread_bps_threshold,
        low_depth_threshold=low_depth_threshold,
        reset_on_session=reset_on_session,
        ddof=ddof,
    )
    feature_spec = FeatureSpec(
        feature_id=f"bbo_tradability_{name.value}",
        family=FeatureFamily.BBO_TRADABILITY,
        feature_request_id=gate_decision.feature_request_id,
        inputs=FeatureInputSpec(
            input_views=("canonical_bbo",),
            fields=_input_fields(name),
            dataset_version_ids=tuple(dataset_version_ids),
            input_metadata={
                "consumption_surface": "alpha_system.features.input_views.BBOInputView",
                "bbo_quality_tokens": [
                    MISSING_BBO_QUALITY_FLAG,
                    BBO_QUARANTINE_QUALITY_FLAG,
                ],
                "quote_semantics": (
                    "FLF-P04 missing_bbo and bbo_quarantined rows are gaps for "
                    "quote-derived values"
                ),
            },
        ),
        transform=TransformSpec(
            transform_id=_transform_id(name),
            parameters=parameters,
        ),
        window=feature_window,
        normalization=NormalizationSpec(
            normalization_id=(
                "causal_zscore" if name is BBOFeatureName.SPREAD_ZSCORE else "identity"
            ),
            parameters={"reset_on_session": reset_on_session, "ddof": ddof}
            if name is BBOFeatureName.SPREAD_ZSCORE
            else {},
        ),
        availability_assumptions={
            "input": "canonical BBO rows are accepted-DatasetVersion input-view rows",
            "causality": "outputs use only source rows with available_ts <= output available_ts",
            "missingness": "missing_bbo and bbo_quarantined rows are never forward-filled",
        },
        available_ts_derivation_rule=(
            "feature.available_ts = current input row available_ts; trailing BBO state "
            "may use only source rows whose available_ts is <= current row available_ts"
        ),
        live=True,
        implementation_eligible=True,
        contract_metadata={
            "campaign": "ALPHA_FEATURE_LABEL_FOUNDATION_V1",
            "phase": "FLF-P09",
            "materialization": "in_memory_records_only",
            "claims": "quote_quality_substrate_only_no_alpha_or_tradability_claim",
        },
        request_gate_decision=gate_decision,
    )
    return _wrap_feature_spec(name, feature_spec)


def _wrap_feature_spec(name: BBOFeatureName, feature_spec: FeatureSpec) -> BBOFeatureSpec:
    if name in _SPREAD_FEATURES:
        return SpreadFeatureSpec(feature_spec=feature_spec, feature_name=name)
    if name in _MICROPRICE_FEATURES:
        return MicropriceFeatureSpec(feature_spec=feature_spec, feature_name=name)
    if name in _TOP_BOOK_FEATURES:
        return TopBookImbalanceFeatureSpec(feature_spec=feature_spec, feature_name=name)
    if name in _QUALITY_FEATURES:
        return LiquidityQualityFeatureSpec(feature_spec=feature_spec, feature_name=name)
    return BBOFeatureSpec(feature_spec=feature_spec, feature_name=name)


def _default_window(name: BBOFeatureName, *, window_length: int) -> WindowSpec:
    if name is BBOFeatureName.SPREAD_ZSCORE:
        return WindowSpec(
            kind=WindowKind.ROLLING,
            length=window_length,
            causality=WindowCausality.CAUSAL,
            offline_only=False,
        )
    return WindowSpec(
        kind=WindowKind.POINT_IN_TIME,
        length=1,
        causality=WindowCausality.CAUSAL,
        offline_only=False,
    )


def _transform_id(name: BBOFeatureName) -> str:
    return {
        BBOFeatureName.MID: "identity",
        BBOFeatureName.SPREAD: "identity",
        BBOFeatureName.SPREAD_TICKS: "identity",
        BBOFeatureName.SPREAD_BPS: "spread_bps",
        BBOFeatureName.SPREAD_ZSCORE: "identity",
        BBOFeatureName.BID_SIZE: "identity",
        BBOFeatureName.ASK_SIZE: "identity",
        BBOFeatureName.TOP_BOOK_DEPTH: "top_book_depth",
        BBOFeatureName.TOP_BOOK_IMBALANCE: "top_book_imbalance",
        BBOFeatureName.MICROPRICE: "microprice",
        BBOFeatureName.MICROPRICE_MINUS_MID: "microprice_minus_mid",
        BBOFeatureName.MISSING_BBO_FLAG: "missing_bbo_flag",
        BBOFeatureName.BAD_QUOTE_FLAG: "bad_quote_flag",
        BBOFeatureName.WIDE_SPREAD_FLAG: "wide_spread_flag",
        BBOFeatureName.LOW_DEPTH_FLAG: "low_depth_flag",
    }[name]


def _transform_parameters(
    name: BBOFeatureName,
    *,
    window_length: int,
    wide_spread_bps_threshold: float,
    low_depth_threshold: float,
    reset_on_session: bool,
    ddof: int,
) -> dict[str, object]:
    parameters: dict[str, object] = {
        "feature_name": name.value,
        "quality_tokens": [
            MISSING_BBO_QUALITY_FLAG,
            BBO_QUARANTINE_QUALITY_FLAG,
        ],
    }
    if name is BBOFeatureName.SPREAD_ZSCORE:
        parameters["window_length"] = window_length
        parameters["reset_on_session"] = reset_on_session
        parameters["ddof"] = ddof
    if name is BBOFeatureName.WIDE_SPREAD_FLAG:
        parameters["wide_spread_bps_threshold"] = wide_spread_bps_threshold
    if name is BBOFeatureName.LOW_DEPTH_FLAG:
        parameters["low_depth_threshold"] = low_depth_threshold
    return parameters


def _input_fields(name: BBOFeatureName) -> tuple[str, ...]:
    base = (
        "available_ts",
        "event_ts",
        "series_id",
        "quality_flags",
    )
    return tuple(dict.fromkeys((*base, *_BBO_FIELDS_BY_FEATURE[name])))


def _coerce_bbo_view(input_view: BBOInputView | CanonicalInputViews) -> BBOInputView:
    if isinstance(input_view, CanonicalInputViews):
        return input_view.bbo
    if isinstance(input_view, BBOInputView):
        return input_view
    raise BBOFeatureError("BBO tradability features require a BBOInputView")


def _validated_rows(rows: Sequence[BBOInputRow]) -> tuple[BBOInputRow, ...]:
    ordered = tuple(rows)
    for row in ordered:
        if not isinstance(row, BBOInputRow):
            raise BBOFeatureError("BBO feature inputs must be BBOInputRow objects")
        _require_aware_datetime(row.available_ts, "BBOInputRow.available_ts")
        _require_aware_datetime(row.event_ts, "BBOInputRow.event_ts")
        _require_aware_datetime(row.bar_start_ts, "BBOInputRow.bar_start_ts")
        _require_aware_datetime(row.bar_end_ts, "BBOInputRow.bar_end_ts")
        for field in ("bid", "ask", "bid_size", "ask_size", "mid", "spread"):
            _to_float(getattr(row, field), f"BBOInputRow.{field}")
        if row.spread_ticks is not None:
            _to_float(row.spread_ticks, "BBOInputRow.spread_ticks")
        if row.microprice is not None:
            _to_float(row.microprice, "BBOInputRow.microprice")
    return tuple(sorted(ordered, key=lambda row: row.available_ts))


def _require_definition(definition: BBOFeatureDefinition) -> BBOFeatureDefinition:
    if not isinstance(definition, BBOFeatureDefinition):
        raise BBOFeatureError("compute requires a BBOFeatureDefinition")
    if definition.spec.family is not FeatureFamily.BBO_TRADABILITY:
        raise BBOFeatureError("definition must belong to FeatureFamily.BBO_TRADABILITY")
    if not definition.spec.implementation_eligible:
        raise BBOFeatureError("definition is not implementation eligible")
    if not definition.request_gate_decision.implementation_allowed:
        raise BBOFeatureError("FeatureRequest gate did not admit implementation")
    if definition.version != definition.spec.derive_feature_version():
        raise BBOFeatureError("definition FeatureVersion does not match FeatureSpec")
    if not definition.spec.window.is_live_compatible:
        raise BBOFeatureError("BBO live features require causal windows")
    return definition


def _records_from_primitive_results(
    definition: BBOFeatureDefinition,
    rows: Sequence[BBOInputRow],
    results: Sequence[PrimitiveResult],
) -> tuple[FeatureValueRecord, ...]:
    if len(rows) != len(results):
        raise BBOFeatureError("primitive output length must match BBO row length")
    return tuple(
        _feature_value_record(
            definition,
            row,
            value=result.value,
            quality_flags=result.quality_flags,
        )
        for row, result in zip(rows, results, strict=True)
    )


def _records_from_points(
    definition: BBOFeatureDefinition,
    points: Sequence[_FeaturePoint],
) -> tuple[FeatureValueRecord, ...]:
    return tuple(
        _feature_value_record(
            definition,
            point.row,
            value=point.value,
            quality_flags=point.quality_flags,
        )
        for point in points
    )


def _feature_value_record(
    definition: BBOFeatureDefinition,
    row: BBOInputRow,
    *,
    value: float | int | None,
    quality_flags: Sequence[str] = (),
) -> FeatureValueRecord:
    return FeatureValueRecord(
        feature_version_id=definition.feature_version_id,
        entity_id=row.series_id,
        event_ts=row.event_ts,
        available_ts=row.available_ts,
        value=value,
        quality_flags=_quality_flags(quality_flags),
    )


def _feature_points(
    definition: BBOFeatureDefinition,
    rows: Sequence[BBOInputRow],
) -> tuple[_FeaturePoint, ...]:
    return tuple(_feature_point(definition, row) for row in rows)


def _feature_point(definition: BBOFeatureDefinition, row: BBOInputRow) -> _FeaturePoint:
    name = definition.name
    if name is BBOFeatureName.MISSING_BBO_FLAG:
        return _quality_flag_point(row, MISSING_BBO_QUALITY_FLAG)
    if name is BBOFeatureName.BAD_QUOTE_FLAG:
        return _bad_quote_flag_point(row)
    if name is BBOFeatureName.WIDE_SPREAD_FLAG:
        return _wide_spread_flag_point(row, _float_parameter(definition, "wide_spread_bps_threshold"))
    if name is BBOFeatureName.LOW_DEPTH_FLAG:
        return _low_depth_flag_point(row, _float_parameter(definition, "low_depth_threshold"))
    if not _is_valid_quote(row):
        return _gap_feature_point(row)
    if name is BBOFeatureName.MID:
        return _FeaturePoint(row=row, value=_to_float(row.mid, "mid"))
    if name is BBOFeatureName.SPREAD:
        return _FeaturePoint(row=row, value=_to_float(row.spread, "spread"))
    if name is BBOFeatureName.SPREAD_TICKS:
        if row.spread_ticks is None:
            return _gap_feature_point(row, "missing_spread_ticks")
        return _FeaturePoint(row=row, value=_to_float(row.spread_ticks, "spread_ticks"))
    if name is BBOFeatureName.SPREAD_BPS:
        return _spread_bps_point(row)
    if name is BBOFeatureName.BID_SIZE:
        return _FeaturePoint(row=row, value=_to_float(row.bid_size, "bid_size"))
    if name is BBOFeatureName.ASK_SIZE:
        return _FeaturePoint(row=row, value=_to_float(row.ask_size, "ask_size"))
    if name is BBOFeatureName.TOP_BOOK_DEPTH:
        return _FeaturePoint(row=row, value=_top_book_depth(row))
    if name is BBOFeatureName.TOP_BOOK_IMBALANCE:
        return _top_book_imbalance_point(row)
    if name is BBOFeatureName.MICROPRICE:
        return _microprice_point(row)
    if name is BBOFeatureName.MICROPRICE_MINUS_MID:
        return _microprice_minus_mid_point(row)
    raise BBOFeatureError(f"unsupported BBO feature: {definition.name}")


def _points_from_valid_bbo_rows(
    rows: Sequence[BBOInputRow],
    field: str,
) -> tuple[PrimitivePoint, ...]:
    field_name = _require_field_name(field)
    points: list[PrimitivePoint] = []
    for row in rows:
        if not _is_valid_quote(row):
            points.append(
                PrimitivePoint(
                    available_ts=row.available_ts,
                    event_ts=row.event_ts,
                    value=None,
                    session_label=row.session_label,
                    quality_flags=_bbo_gap_flags(row),
                )
            )
            continue
        points.append(
            PrimitivePoint(
                available_ts=row.available_ts,
                event_ts=row.event_ts,
                value=_to_float(getattr(row, field_name), field_name),
                session_label=row.session_label,
                quality_flags=(),
            )
        )
    return tuple(points)


def _quality_flag_point(row: BBOInputRow, token: str) -> _FeaturePoint:
    flags = _quality_flags(row.quality_flags)
    normalized_token = token.strip().lower()
    present = normalized_token in flags
    return _FeaturePoint(
        row=row,
        value=1 if present else 0,
        quality_flags=(normalized_token,) if present else (),
    )


def _bad_quote_flag_point(row: BBOInputRow) -> _FeaturePoint:
    semantics = _quote_semantics(row)
    quality_flags = tuple(
        flag
        for flag in _quality_flags(row.quality_flags)
        if flag in {MISSING_BBO_QUALITY_FLAG, BBO_QUARANTINE_QUALITY_FLAG}
    )
    return _FeaturePoint(
        row=row,
        value=1 if semantics.missing_or_abnormal else 0,
        quality_flags=quality_flags,
    )


def _wide_spread_flag_point(row: BBOInputRow, threshold: float) -> _FeaturePoint:
    if not _is_valid_quote(row):
        return _gap_feature_point(row)
    spread_bps = _spread_bps_value(row)
    if spread_bps is None:
        return _gap_feature_point(row, "zero_or_negative_mid")
    return _FeaturePoint(row=row, value=1 if spread_bps > threshold else 0)


def _low_depth_flag_point(row: BBOInputRow, threshold: float) -> _FeaturePoint:
    if not _is_valid_quote(row):
        return _gap_feature_point(row)
    return _FeaturePoint(row=row, value=1 if _top_book_depth(row) < threshold else 0)


def _spread_bps_point(row: BBOInputRow) -> _FeaturePoint:
    spread_bps = _spread_bps_value(row)
    if spread_bps is None:
        return _gap_feature_point(row, "zero_or_negative_mid")
    return _FeaturePoint(row=row, value=spread_bps)


def _spread_bps_value(row: BBOInputRow) -> float | None:
    mid = _to_float(row.mid, "mid")
    if mid <= 0:
        return None
    return _to_float(row.spread, "spread") / mid * 10_000.0


def _top_book_depth(row: BBOInputRow) -> float:
    return _to_float(row.bid_size, "bid_size") + _to_float(row.ask_size, "ask_size")


def _top_book_imbalance_point(row: BBOInputRow) -> _FeaturePoint:
    if not _has_valid_bid_ask_sizes(row):
        return _gap_feature_point(row, "invalid_bbo_size")
    bid_size = _to_float(row.bid_size, "bid_size")
    ask_size = _to_float(row.ask_size, "ask_size")
    return _FeaturePoint(row=row, value=(bid_size - ask_size) / (bid_size + ask_size))


def _microprice_point(row: BBOInputRow) -> _FeaturePoint:
    microprice = _microprice_value(row)
    if microprice is None:
        return _gap_feature_point(row, "invalid_bbo_size")
    return _FeaturePoint(row=row, value=microprice)


def _microprice_minus_mid_point(row: BBOInputRow) -> _FeaturePoint:
    microprice = _microprice_value(row)
    if microprice is None:
        return _gap_feature_point(row, "invalid_bbo_size")
    return _FeaturePoint(row=row, value=microprice - _to_float(row.mid, "mid"))


def _microprice_value(row: BBOInputRow) -> float | None:
    if not _has_valid_bid_ask_sizes(row):
        return None
    bid = _to_float(row.bid, "bid")
    ask = _to_float(row.ask, "ask")
    bid_size = _to_float(row.bid_size, "bid_size")
    ask_size = _to_float(row.ask_size, "ask_size")
    return (ask * bid_size + bid * ask_size) / (bid_size + ask_size)


def _has_valid_bid_ask_sizes(row: BBOInputRow) -> bool:
    bid_size = _to_float(row.bid_size, "bid_size")
    ask_size = _to_float(row.ask_size, "ask_size")
    return bid_size > 0 and ask_size > 0 and bid_size + ask_size > 0


def _is_valid_quote(row: BBOInputRow) -> bool:
    semantics = _quote_semantics(row)
    return not semantics.missing_or_abnormal and semantics.invariants_hold


def _quote_semantics(row: BBOInputRow) -> BBOQuoteSemantics:
    try:
        return bbo_quote_semantics(row)
    except DataFoundationValidationError as exc:
        raise BBOFeatureError(str(exc)) from exc


def _gap_feature_point(
    row: BBOInputRow,
    reason: str | None = None,
    extra_flags: Sequence[str] = (),
) -> _FeaturePoint:
    flags = set(_bbo_gap_flags(row))
    if reason is not None:
        flags.add(reason.strip().lower())
    flags.update(_quality_flags(extra_flags))
    return _FeaturePoint(row=row, value=None, quality_flags=tuple(sorted(flags)))


def _bbo_gap_flags(row: BBOInputRow) -> tuple[str, ...]:
    semantics = _quote_semantics(row)
    flags = {"bbo_gap", *_quality_flags(row.quality_flags)}
    if semantics.missing_bbo:
        flags.add(MISSING_BBO_QUALITY_FLAG)
    if semantics.bbo_quarantined:
        flags.add(BBO_QUARANTINE_QUALITY_FLAG)
    if not semantics.invariants_hold:
        flags.add("bbo_invariant_violation")
    return tuple(sorted(flags))


def _int_parameter(definition: BBOFeatureDefinition, name: str) -> int:
    value = definition.spec.transform.parameters.to_dict().get(name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise BBOFeatureError(f"{name} parameter must be an integer")
    return value


def _float_parameter(definition: BBOFeatureDefinition, name: str) -> float:
    value = definition.spec.transform.parameters.to_dict().get(name)
    if isinstance(value, bool) or not isinstance(value, _NUMERIC_TYPES):
        raise BBOFeatureError(f"{name} parameter must be numeric")
    parsed = float(value)
    if not math.isfinite(parsed):
        raise BBOFeatureError(f"{name} parameter must be finite")
    return parsed


def _bool_parameter(definition: BBOFeatureDefinition, name: str) -> bool:
    value = definition.spec.transform.parameters.to_dict().get(name)
    if type(value) is not bool:
        raise BBOFeatureError(f"{name} parameter must be a bool")
    return value


def _coerce_feature_name(name: BBOFeatureName | str) -> BBOFeatureName:
    try:
        return BBOFeatureName(name)
    except ValueError as exc:
        raise BBOFeatureError(f"unsupported BBO tradability feature: {name}") from exc


def _positive_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise BBOFeatureError(f"{field_name} must be a positive integer")
    return value


def _non_negative_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise BBOFeatureError(f"{field_name} must be a non-negative integer")
    return value


def _non_negative_float(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, _NUMERIC_TYPES):
        raise BBOFeatureError(f"{field_name} must be numeric")
    parsed = float(value)
    if not math.isfinite(parsed) or parsed < 0:
        raise BBOFeatureError(f"{field_name} must be a finite non-negative value")
    return parsed


def _require_aware_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise BBOFeatureError(f"{field_name} must be a timezone-aware datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise BBOFeatureError(f"{field_name} must be timezone-aware")
    return value


def _require_field_name(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BBOFeatureError("field must be a non-empty string")
    return value.strip()


def _to_float(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, _NUMERIC_TYPES):
        raise BBOFeatureError(f"{field_name} must be numeric")
    parsed = float(value)
    if not math.isfinite(parsed):
        raise BBOFeatureError(f"{field_name} must be finite")
    return parsed


def _quality_flags(flags: Sequence[str]) -> tuple[str, ...]:
    if isinstance(flags, str) or not isinstance(flags, Sequence):
        raise BBOFeatureError("quality_flags must be a sequence of strings")
    normalized: list[str] = []
    for flag in flags:
        if not isinstance(flag, str) or not flag.strip():
            raise BBOFeatureError("quality_flags must contain non-empty strings")
        token = flag.strip().lower()
        if token not in normalized:
            normalized.append(token)
    return tuple(normalized)


__all__ = [
    "BBOFeatureDefinition",
    "BBOFeatureError",
    "BBOFeatureName",
    "BBOFeatureSpec",
    "LiquidityQualityFeatureSpec",
    "MicropriceFeatureSpec",
    "SpreadFeatureSpec",
    "TopBookImbalanceFeatureSpec",
    "build_bbo_feature_definition",
    "build_bbo_feature_definitions",
    "compute_bbo_feature",
    "compute_bbo_features",
    "supported_bbo_features",
]
