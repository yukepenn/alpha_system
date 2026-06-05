"""Causal ES/NQ/RTY cross-market feature definitions and calculations."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from types import MappingProxyType
from typing import Any

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
from alpha_system.features.input_views import (
    BBOInputRow,
    BBOInputView,
    CanonicalInputViews,
    OHLCVInputRow,
    OHLCVInputView,
)
from alpha_system.features.primitives import (
    PrimitiveResult,
    points_from_trade_rows,
    simple_returns,
)
from alpha_system.features.request_gate import (
    FeatureRequestGateDecision,
    require_feature_request_implementation_allowed,
)
from alpha_system.features.semantics import bbo_quote_semantics
from alpha_system.governance.duplicate_exposure import RegistryReader
from alpha_system.governance.feature_request import FeatureRequest


class CrossMarketFeatureError(ValueError):
    """Raised when Cross-Market family computation fails closed."""


class CrossMarketFeatureName(StrEnum):
    """Supported Cross-Market feature names for FLF-P11."""

    SYNCHRONIZED_RETURNS = "synchronized_returns"
    NQ_MINUS_ES_RETURN_SPREAD = "nq_minus_es_return_spread"
    RTY_MINUS_ES_RETURN_SPREAD = "rty_minus_es_return_spread"
    NQ_ES_ROLLING_BETA_RESIDUAL = "nq_es_rolling_beta_residual"
    RTY_ES_ROLLING_BETA_RESIDUAL = "rty_es_rolling_beta_residual"
    NQ_ES_ROLLING_CORRELATION = "nq_es_rolling_correlation"
    RTY_ES_ROLLING_CORRELATION = "rty_es_rolling_correlation"
    CONFIRMATION_FLAG = "confirmation_flag"
    DIVERGENCE_FLAG = "divergence_flag"
    RISK_ON_ROTATION_PROXY = "risk_on_rotation_proxy"
    RISK_OFF_ROTATION_PROXY = "risk_off_rotation_proxy"


@dataclass(frozen=True, slots=True)
class CrossMarketInputBundle:
    """Per-instrument canonical views for the ES/NQ/RTY cross-market family."""

    ohlcv_by_instrument: Mapping[str, OHLCVInputView]
    bbo_by_instrument: Mapping[str, BBOInputView] | None = None
    dataset_family_id: str | None = None

    def __post_init__(self) -> None:
        ohlcv_views = _normalize_ohlcv_view_mapping(self.ohlcv_by_instrument)
        bbo_views = _normalize_bbo_view_mapping(self.bbo_by_instrument or {})
        dataset_family_id = _optional_text(self.dataset_family_id)
        _validate_input_rows(ohlcv_views, bbo_views)
        _validate_single_dataset_family(ohlcv_views, bbo_views, dataset_family_id)
        object.__setattr__(self, "ohlcv_by_instrument", MappingProxyType(ohlcv_views))
        object.__setattr__(self, "bbo_by_instrument", MappingProxyType(bbo_views))
        object.__setattr__(self, "dataset_family_id", dataset_family_id)


@dataclass(frozen=True, slots=True)
class CrossMarketAlignedSnapshot:
    """One as-of ES/NQ/RTY alignment point keyed by output ``available_ts``."""

    available_ts: datetime
    event_ts: datetime
    rows: Mapping[str, OHLCVInputRow | None]
    returns: Mapping[str, float | None]
    source_available_ts: Mapping[str, tuple[datetime, ...]]
    return_quality_flags: Mapping[str, tuple[str, ...]]
    bbo_quality_flags: tuple[str, ...] = ()
    session_label: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "available_ts",
            _require_aware_datetime(self.available_ts, "CrossMarketAlignedSnapshot.available_ts"),
        )
        object.__setattr__(
            self,
            "event_ts",
            _require_aware_datetime(self.event_ts, "CrossMarketAlignedSnapshot.event_ts"),
        )
        object.__setattr__(self, "rows", MappingProxyType(dict(self.rows)))
        object.__setattr__(self, "returns", MappingProxyType(dict(self.returns)))
        object.__setattr__(
            self,
            "source_available_ts",
            MappingProxyType(
                {
                    market: tuple(
                        _require_aware_datetime(source_ts, "source_available_ts")
                        for source_ts in timestamps
                    )
                    for market, timestamps in self.source_available_ts.items()
                }
            ),
        )
        object.__setattr__(
            self,
            "return_quality_flags",
            MappingProxyType(
                {
                    market: _quality_flags(flags)
                    for market, flags in self.return_quality_flags.items()
                }
            ),
        )
        object.__setattr__(self, "bbo_quality_flags", _quality_flags(self.bbo_quality_flags))
        object.__setattr__(self, "session_label", _optional_text(self.session_label))

    @property
    def quality_flags(self) -> tuple[str, ...]:
        """Return all quality flags surfaced at this alignment point."""

        flags = set(self.bbo_quality_flags)
        for market_flags in self.return_quality_flags.values():
            flags.update(market_flags)
        return tuple(sorted(flags))


@dataclass(frozen=True, slots=True)
class CrossMarketFeatureSpec:
    """Cross-Market family view over a governed FLF-P06 ``FeatureSpec``."""

    feature_spec: FeatureSpec
    feature_name: CrossMarketFeatureName

    def __post_init__(self) -> None:
        if not isinstance(self.feature_spec, FeatureSpec):
            raise CrossMarketFeatureError(
                "CrossMarketFeatureSpec.feature_spec must be a FeatureSpec"
            )
        feature_name = _coerce_feature_name(self.feature_name)
        if self.feature_spec.family is not FeatureFamily.CROSS_MARKET:
            raise CrossMarketFeatureError(
                "CrossMarketFeatureSpec requires FeatureFamily.CROSS_MARKET"
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
class CrossMarketReturnFeatureSpec(CrossMarketFeatureSpec):
    """Synchronized returns and return-spread feature contract."""


@dataclass(frozen=True, slots=True)
class CrossMarketRollingFeatureSpec(CrossMarketFeatureSpec):
    """Rolling beta-residual and correlation feature contract."""


@dataclass(frozen=True, slots=True)
class CrossMarketFlagFeatureSpec(CrossMarketFeatureSpec):
    """Confirmation and divergence flag feature contract."""


@dataclass(frozen=True, slots=True)
class CrossMarketRotationFeatureSpec(CrossMarketFeatureSpec):
    """Risk-on/risk-off rotation proxy feature contract."""


@dataclass(frozen=True, slots=True)
class CrossMarketFeatureDefinition:
    """Approved, versioned Cross-Market feature definition."""

    name: CrossMarketFeatureName
    spec: CrossMarketFeatureSpec
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
    snapshot: CrossMarketAlignedSnapshot
    value: float | int | Mapping[str, float] | None
    quality_flags: tuple[str, ...] = ()


type _Numeric = int | float | Decimal

_NUMERIC_TYPES = (int, float, Decimal)
_MARKETS: tuple[str, str, str] = ("ES", "NQ", "RTY")
_CROSS_MARKET_ENTITY_ID = "ES:NQ:RTY"
_ROLLING_FEATURES = frozenset(
    {
        CrossMarketFeatureName.NQ_ES_ROLLING_BETA_RESIDUAL,
        CrossMarketFeatureName.RTY_ES_ROLLING_BETA_RESIDUAL,
        CrossMarketFeatureName.NQ_ES_ROLLING_CORRELATION,
        CrossMarketFeatureName.RTY_ES_ROLLING_CORRELATION,
    }
)
_RETURN_FEATURES = frozenset(
    {
        CrossMarketFeatureName.SYNCHRONIZED_RETURNS,
        CrossMarketFeatureName.NQ_MINUS_ES_RETURN_SPREAD,
        CrossMarketFeatureName.RTY_MINUS_ES_RETURN_SPREAD,
    }
)
_FLAG_FEATURES = frozenset(
    {
        CrossMarketFeatureName.CONFIRMATION_FLAG,
        CrossMarketFeatureName.DIVERGENCE_FLAG,
    }
)
_ROTATION_FEATURES = frozenset(
    {
        CrossMarketFeatureName.RISK_ON_ROTATION_PROXY,
        CrossMarketFeatureName.RISK_OFF_ROTATION_PROXY,
    }
)
_FIELDS_BY_FEATURE: dict[CrossMarketFeatureName, tuple[str, ...]] = {
    CrossMarketFeatureName.SYNCHRONIZED_RETURNS: ("close",),
    CrossMarketFeatureName.NQ_MINUS_ES_RETURN_SPREAD: ("close",),
    CrossMarketFeatureName.RTY_MINUS_ES_RETURN_SPREAD: ("close",),
    CrossMarketFeatureName.NQ_ES_ROLLING_BETA_RESIDUAL: ("close",),
    CrossMarketFeatureName.RTY_ES_ROLLING_BETA_RESIDUAL: ("close",),
    CrossMarketFeatureName.NQ_ES_ROLLING_CORRELATION: ("close",),
    CrossMarketFeatureName.RTY_ES_ROLLING_CORRELATION: ("close",),
    CrossMarketFeatureName.CONFIRMATION_FLAG: ("close",),
    CrossMarketFeatureName.DIVERGENCE_FLAG: ("close",),
    CrossMarketFeatureName.RISK_ON_ROTATION_PROXY: ("close",),
    CrossMarketFeatureName.RISK_OFF_ROTATION_PROXY: ("close",),
}


def supported_cross_market_features() -> tuple[CrossMarketFeatureName, ...]:
    """Return the complete FLF-P11 Cross-Market feature list."""

    return tuple(CrossMarketFeatureName)


def build_cross_market_feature_definition(
    name: CrossMarketFeatureName | str,
    feature_request: FeatureRequest | Mapping[str, Any] | None,
    registry_reader: RegistryReader | object | None,
    *,
    dataset_version_ids: Sequence[str] = (),
    dataset_family_id: str | None = None,
    window_length: int = 3,
    horizon: int = 1,
    reset_on_session: bool = True,
    ddof: int = 0,
    window: WindowSpec | None = None,
) -> CrossMarketFeatureDefinition:
    """Build one approved Cross-Market feature definition.

    The FLF-P05 request gate is the only admission path. Missing, invalid,
    unapproved, duplicate-blocked, or registry-unchecked requests fail closed.
    """

    feature_name = _coerce_feature_name(name)
    window_length = _positive_int(window_length, "window_length")
    horizon = _positive_int(horizon, "horizon")
    ddof = _non_negative_int(ddof, "ddof")
    if type(reset_on_session) is not bool:
        raise CrossMarketFeatureError("reset_on_session must be a bool")
    dataset_family_id = _optional_text(dataset_family_id)
    _validate_dataset_version_id_family(dataset_version_ids, dataset_family_id)

    gate_decision = require_feature_request_implementation_allowed(
        feature_request,
        registry_reader,
    )
    spec = _feature_spec(
        feature_name,
        gate_decision,
        dataset_version_ids=dataset_version_ids,
        dataset_family_id=dataset_family_id,
        window_length=window_length,
        horizon=horizon,
        reset_on_session=reset_on_session,
        ddof=ddof,
        window=window,
    )
    return CrossMarketFeatureDefinition(
        name=feature_name,
        spec=spec,
        version=spec.derive_feature_version(),
        request_gate_decision=gate_decision,
    )


def build_cross_market_feature_definitions(
    feature_requests: Mapping[CrossMarketFeatureName | str, FeatureRequest | Mapping[str, Any]],
    registry_reader: RegistryReader | object | None,
    **parameters: Any,
) -> tuple[CrossMarketFeatureDefinition, ...]:
    """Build multiple approved Cross-Market feature definitions."""

    return tuple(
        build_cross_market_feature_definition(name, request, registry_reader, **parameters)
        for name, request in feature_requests.items()
    )


def align_cross_market_rows(
    input_views: CrossMarketInputBundle
    | Mapping[str, OHLCVInputView]
    | OHLCVInputView
    | CanonicalInputViews,
    *,
    horizon: int = 1,
    reset_on_session: bool = True,
) -> tuple[CrossMarketAlignedSnapshot, ...]:
    """Build causal ES/NQ/RTY as-of snapshots ordered by ``available_ts``.

    A snapshot at time ``t`` uses, for each instrument, only the latest return
    primitive whose own source rows have ``available_ts <= t``.
    """

    horizon = _positive_int(horizon, "horizon")
    if type(reset_on_session) is not bool:
        raise CrossMarketFeatureError("reset_on_session must be a bool")
    bundle = _coerce_input_bundle(input_views)
    rows_by_market = {
        market: _validated_ohlcv_rows(bundle.ohlcv_by_instrument[market].rows)
        for market in _MARKETS
    }
    returns_by_market = {
        market: simple_returns(
            points_from_trade_rows(rows, "close"),
            horizon,
            reset_on_session=reset_on_session,
        )
        for market, rows in rows_by_market.items()
    }
    timeline = tuple(
        sorted(
            {
                row.available_ts
                for rows in rows_by_market.values()
                for row in rows
            }
        )
    )
    snapshots: list[CrossMarketAlignedSnapshot] = []
    for available_ts in timeline:
        rows_at_t = {
            market: _latest_row_as_of(rows, available_ts)
            for market, rows in rows_by_market.items()
        }
        returns_at_t = {
            market: _latest_result_as_of(returns, available_ts)
            for market, returns in returns_by_market.items()
        }
        current_rows = tuple(row for row in rows_at_t.values() if row is not None)
        event_ts = max((row.event_ts for row in current_rows), default=available_ts)
        snapshots.append(
            CrossMarketAlignedSnapshot(
                available_ts=available_ts,
                event_ts=event_ts,
                rows=rows_at_t,
                returns={
                    market: None if result is None else result.value
                    for market, result in returns_at_t.items()
                },
                source_available_ts={
                    market: () if result is None else tuple(result.source_available_ts)
                    for market, result in returns_at_t.items()
                },
                return_quality_flags={
                    market: _return_result_flags(market, returns_at_t[market], rows_at_t[market])
                    for market in _MARKETS
                },
                bbo_quality_flags=_bbo_quality_flags_at(bundle, available_ts),
                session_label=_snapshot_session_label(rows_at_t),
            )
        )
    return tuple(snapshots)


def compute_cross_market_feature(
    definition: CrossMarketFeatureDefinition,
    input_views: CrossMarketInputBundle
    | Mapping[str, OHLCVInputView]
    | OHLCVInputView
    | CanonicalInputViews,
) -> tuple[FeatureValueRecord, ...]:
    """Compute one Cross-Market feature as in-memory value records.

    Values are returned only to the caller. This function does not materialize,
    persist, register, or write feature values.
    """

    definition = _require_definition(definition)
    snapshots = align_cross_market_rows(
        input_views,
        horizon=_int_parameter(definition, "horizon"),
        reset_on_session=_bool_parameter(definition, "reset_on_session"),
    )
    if definition.name in _ROLLING_FEATURES:
        return _records_from_points(
            definition,
            _rolling_feature_points(definition, snapshots),
        )
    return _records_from_points(
        definition,
        tuple(_point_feature(definition, snapshot) for snapshot in snapshots),
    )


def compute_cross_market_features(
    definitions: Iterable[CrossMarketFeatureDefinition],
    input_views: CrossMarketInputBundle
    | Mapping[str, OHLCVInputView]
    | OHLCVInputView
    | CanonicalInputViews,
) -> dict[CrossMarketFeatureName, tuple[FeatureValueRecord, ...]]:
    """Compute approved Cross-Market definitions against canonical input views."""

    return {
        definition.name: compute_cross_market_feature(definition, input_views)
        for definition in definitions
    }


def _feature_spec(
    name: CrossMarketFeatureName,
    gate_decision: FeatureRequestGateDecision,
    *,
    dataset_version_ids: Sequence[str],
    dataset_family_id: str,
    window_length: int,
    horizon: int,
    reset_on_session: bool,
    ddof: int,
    window: WindowSpec | None,
) -> CrossMarketFeatureSpec:
    if gate_decision.feature_request_id is None:
        raise CrossMarketFeatureError("approved FeatureRequestGateDecision must expose freq_ id")
    feature_window = window or _default_window(name, window_length=window_length)
    parameters = _transform_parameters(
        name,
        dataset_family_id=dataset_family_id,
        window_length=window_length,
        horizon=horizon,
        reset_on_session=reset_on_session,
        ddof=ddof,
    )
    feature_spec = FeatureSpec(
        feature_id=f"cross_market_{name.value}",
        family=FeatureFamily.CROSS_MARKET,
        feature_request_id=gate_decision.feature_request_id,
        inputs=FeatureInputSpec(
            input_views=("canonical_ohlcv",),
            fields=_input_fields(name),
            dataset_version_ids=tuple(dataset_version_ids),
            input_metadata={
                "markets": list(_MARKETS),
                "consumption_surface": (
                    "alpha_system.features.input_views.OHLCVInputView per instrument"
                ),
                "accepted_dataset_version_gate": (
                    "input views are produced upstream from accepted DatasetVersions"
                ),
                "dataset_family_id": dataset_family_id,
                "optional_bbo_quality_surface": (
                    "BBO rows may be supplied for exact available_ts quality flags; "
                    "they are never filled or interpolated"
                ),
                "trade_semantics": "FLF-P04 no_trade rows are gaps for return logic",
            },
        ),
        transform=TransformSpec(
            transform_id=_transform_id(name),
            parameters=parameters,
        ),
        window=feature_window,
        normalization=NormalizationSpec(normalization_id="identity"),
        availability_assumptions={
            "input": "per-instrument canonical OHLCV rows are accepted input-view rows",
            "alignment": (
                "ES, NQ, and RTY are aligned by as-of available_ts; each instrument "
                "contributes only rows with available_ts <= output available_ts"
            ),
            "missingness": (
                "no_trade rows are return gaps; exact-time BBO missingness is flagged "
                "without quote filling"
            ),
        },
        available_ts_derivation_rule=(
            "feature.available_ts = one timestamp from the union of per-instrument "
            "OHLCV available_ts values; source rows and return primitives for every "
            "instrument must have available_ts <= feature.available_ts"
        ),
        live=True,
        implementation_eligible=True,
        contract_metadata={
            "campaign": "ALPHA_FEATURE_LABEL_FOUNDATION_V1",
            "phase": "FLF-P11",
            "materialization": "in_memory_records_only",
            "claims": "cross_market_structure_only_no_alpha_or_tradability_claim",
        },
        request_gate_decision=gate_decision,
    )
    return _wrap_feature_spec(name, feature_spec)


def _wrap_feature_spec(
    name: CrossMarketFeatureName,
    feature_spec: FeatureSpec,
) -> CrossMarketFeatureSpec:
    if name in _RETURN_FEATURES:
        return CrossMarketReturnFeatureSpec(feature_spec=feature_spec, feature_name=name)
    if name in _ROLLING_FEATURES:
        return CrossMarketRollingFeatureSpec(feature_spec=feature_spec, feature_name=name)
    if name in _FLAG_FEATURES:
        return CrossMarketFlagFeatureSpec(feature_spec=feature_spec, feature_name=name)
    if name in _ROTATION_FEATURES:
        return CrossMarketRotationFeatureSpec(feature_spec=feature_spec, feature_name=name)
    return CrossMarketFeatureSpec(feature_spec=feature_spec, feature_name=name)


def _default_window(name: CrossMarketFeatureName, *, window_length: int) -> WindowSpec:
    if name in _ROLLING_FEATURES:
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


def _transform_id(name: CrossMarketFeatureName) -> str:
    return {
        CrossMarketFeatureName.SYNCHRONIZED_RETURNS: "synchronized_returns",
        CrossMarketFeatureName.NQ_MINUS_ES_RETURN_SPREAD: "return_spread",
        CrossMarketFeatureName.RTY_MINUS_ES_RETURN_SPREAD: "return_spread",
        CrossMarketFeatureName.NQ_ES_ROLLING_BETA_RESIDUAL: "rolling_beta_residual",
        CrossMarketFeatureName.RTY_ES_ROLLING_BETA_RESIDUAL: "rolling_beta_residual",
        CrossMarketFeatureName.NQ_ES_ROLLING_CORRELATION: "rolling_correlation",
        CrossMarketFeatureName.RTY_ES_ROLLING_CORRELATION: "rolling_correlation",
        CrossMarketFeatureName.CONFIRMATION_FLAG: "confirmation_flag",
        CrossMarketFeatureName.DIVERGENCE_FLAG: "divergence_flag",
        CrossMarketFeatureName.RISK_ON_ROTATION_PROXY: "risk_on_rotation_proxy",
        CrossMarketFeatureName.RISK_OFF_ROTATION_PROXY: "risk_off_rotation_proxy",
    }[name]


def _transform_parameters(
    name: CrossMarketFeatureName,
    *,
    dataset_family_id: str,
    window_length: int,
    horizon: int,
    reset_on_session: bool,
    ddof: int,
) -> dict[str, object]:
    parameters: dict[str, object] = {
        "feature_name": name.value,
        "markets": list(_MARKETS),
        "horizon": horizon,
        "reset_on_session": reset_on_session,
    }
    if dataset_family_id:
        parameters["dataset_family_id"] = dataset_family_id
    if name in _ROLLING_FEATURES:
        parameters["window_length"] = window_length
        parameters["ddof"] = ddof
        target, benchmark = _rolling_pair(name)
        parameters["target_market"] = target
        parameters["benchmark_market"] = benchmark
    if name in {
        CrossMarketFeatureName.NQ_MINUS_ES_RETURN_SPREAD,
        CrossMarketFeatureName.RTY_MINUS_ES_RETURN_SPREAD,
    }:
        target, benchmark = _spread_pair(name)
        parameters["target_market"] = target
        parameters["benchmark_market"] = benchmark
    return parameters


def _input_fields(name: CrossMarketFeatureName) -> tuple[str, ...]:
    base = (
        "instrument_id",
        "available_ts",
        "event_ts",
        "series_id",
        "data_version",
        "session_label",
        "quality_flags",
        "bbo.quality_flags",
    )
    return tuple(dict.fromkeys((*base, *_FIELDS_BY_FEATURE[name])))


def _coerce_input_bundle(
    input_views: CrossMarketInputBundle
    | Mapping[str, OHLCVInputView]
    | OHLCVInputView
    | CanonicalInputViews,
) -> CrossMarketInputBundle:
    if isinstance(input_views, CrossMarketInputBundle):
        return input_views
    if isinstance(input_views, CanonicalInputViews):
        return CrossMarketInputBundle(
            _split_ohlcv_rows_by_market(input_views.ohlcv),
            _split_bbo_rows_by_market(input_views.bbo),
        )
    if isinstance(input_views, OHLCVInputView):
        return CrossMarketInputBundle(_split_ohlcv_rows_by_market(input_views))
    if isinstance(input_views, Mapping):
        return CrossMarketInputBundle(input_views)
    raise CrossMarketFeatureError(
        "Cross-Market features require CrossMarketInputBundle or canonical input views"
    )


def _normalize_ohlcv_view_mapping(
    views: Mapping[str, OHLCVInputView],
) -> dict[str, OHLCVInputView]:
    if not isinstance(views, Mapping):
        raise CrossMarketFeatureError("ohlcv_by_instrument must be a mapping")
    normalized: dict[str, OHLCVInputView] = {}
    for key, view in views.items():
        market = _coerce_market(key)
        if not isinstance(view, OHLCVInputView):
            raise CrossMarketFeatureError("OHLCV cross-market inputs must be OHLCVInputView")
        normalized[market] = view
    _require_exact_markets(normalized, "ohlcv_by_instrument")
    return {market: normalized[market] for market in _MARKETS}


def _normalize_bbo_view_mapping(
    views: Mapping[str, BBOInputView],
) -> dict[str, BBOInputView]:
    if not isinstance(views, Mapping):
        raise CrossMarketFeatureError("bbo_by_instrument must be a mapping")
    normalized: dict[str, BBOInputView] = {}
    for key, view in views.items():
        market = _coerce_market(key)
        if not isinstance(view, BBOInputView):
            raise CrossMarketFeatureError("BBO cross-market inputs must be BBOInputView")
        normalized[market] = view
    missing = tuple(market for market in normalized if market not in _MARKETS)
    if missing:
        raise CrossMarketFeatureError("bbo_by_instrument contains unsupported markets")
    return {market: normalized[market] for market in _MARKETS if market in normalized}


def _require_exact_markets(views: Mapping[str, object], field_name: str) -> None:
    keys = tuple(views)
    missing = tuple(market for market in _MARKETS if market not in views)
    extra = tuple(key for key in keys if key not in _MARKETS)
    if missing or extra:
        raise CrossMarketFeatureError(
            f"{field_name} must contain exactly ES, NQ, and RTY views"
        )


def _split_ohlcv_rows_by_market(view: OHLCVInputView) -> dict[str, OHLCVInputView]:
    rows_by_market: dict[str, list[OHLCVInputRow]] = {market: [] for market in _MARKETS}
    for row in _validated_ohlcv_rows(view.rows):
        rows_by_market[_market_from_row(row)].append(row)
    return {
        market: OHLCVInputView(tuple(rows))
        for market, rows in rows_by_market.items()
    }


def _split_bbo_rows_by_market(view: BBOInputView) -> dict[str, BBOInputView]:
    rows_by_market: dict[str, list[BBOInputRow]] = {market: [] for market in _MARKETS}
    for row in _validated_bbo_rows(view.rows):
        rows_by_market[_market_from_row(row)].append(row)
    return {
        market: BBOInputView(tuple(rows))
        for market, rows in rows_by_market.items()
        if rows
    }


def _validate_input_rows(
    ohlcv_views: Mapping[str, OHLCVInputView],
    bbo_views: Mapping[str, BBOInputView],
) -> None:
    for market, view in ohlcv_views.items():
        rows = _validated_ohlcv_rows(view.rows)
        if not rows:
            raise CrossMarketFeatureError(f"{market} OHLCV view must contain at least one row")
        if any(not _row_matches_market(row, market) for row in rows):
            raise CrossMarketFeatureError(f"{market} OHLCV view contains another market")
    for market, view in bbo_views.items():
        rows = _validated_bbo_rows(view.rows)
        if any(not _row_matches_market(row, market) for row in rows):
            raise CrossMarketFeatureError(f"{market} BBO view contains another market")


def _validated_ohlcv_rows(rows: Sequence[OHLCVInputRow]) -> tuple[OHLCVInputRow, ...]:
    ordered = tuple(rows)
    for row in ordered:
        if not isinstance(row, OHLCVInputRow):
            raise CrossMarketFeatureError("Cross-Market OHLCV inputs must be OHLCVInputRow")
        _require_aware_datetime(row.available_ts, "OHLCVInputRow.available_ts")
        _require_aware_datetime(row.event_ts, "OHLCVInputRow.event_ts")
        _require_aware_datetime(row.bar_start_ts, "OHLCVInputRow.bar_start_ts")
        _to_float(row.close, "OHLCVInputRow.close")
        _require_text(row.data_version, "OHLCVInputRow.data_version")
        _quality_flags(row.quality_flags)
    return tuple(sorted(ordered, key=lambda row: row.available_ts))


def _validated_bbo_rows(rows: Sequence[BBOInputRow]) -> tuple[BBOInputRow, ...]:
    ordered = tuple(rows)
    for row in ordered:
        if not isinstance(row, BBOInputRow):
            raise CrossMarketFeatureError("Cross-Market BBO inputs must be BBOInputRow")
        _require_aware_datetime(row.available_ts, "BBOInputRow.available_ts")
        _require_aware_datetime(row.event_ts, "BBOInputRow.event_ts")
        _require_text(row.data_version, "BBOInputRow.data_version")
        _quality_flags(row.quality_flags)
    return tuple(sorted(ordered, key=lambda row: row.available_ts))


def _validate_single_dataset_family(
    ohlcv_views: Mapping[str, OHLCVInputView],
    bbo_views: Mapping[str, BBOInputView],
    dataset_family_id: str,
) -> None:
    ids = [
        row.data_version
        for view in ohlcv_views.values()
        for row in view.rows
    ]
    ids.extend(row.data_version for view in bbo_views.values() for row in view.rows)
    _validate_dataset_version_id_family(ids, dataset_family_id)


def _validate_dataset_version_id_family(
    dataset_version_ids: Sequence[str],
    dataset_family_id: str,
) -> None:
    ids = tuple(_require_text(value, "dataset_version_id") for value in dataset_version_ids)
    if not ids:
        return
    if dataset_family_id:
        prefix = f"{dataset_family_id}:"
        if any(value != dataset_family_id and not value.startswith(prefix) for value in ids):
            raise CrossMarketFeatureError(
                "cross-market inputs must use one declared DatasetVersion family"
            )
        return
    families = {_dataset_family_token(value) for value in ids}
    if len(families) > 1:
        raise CrossMarketFeatureError(
            "cross-market inputs must not mix DatasetVersion families"
        )


def _dataset_family_token(value: str) -> str:
    text = _require_text(value, "dataset_version_id")
    for delimiter in (":", "|", "/"):
        if delimiter in text:
            return text.split(delimiter, 1)[0]
    parts = text.split("_")
    if len(parts) >= 3 and parts[0] == "dsv":
        return "_".join(parts[:2])
    return text


def _latest_row_as_of(
    rows: Sequence[OHLCVInputRow],
    available_ts: datetime,
) -> OHLCVInputRow | None:
    latest: OHLCVInputRow | None = None
    for row in rows:
        if row.available_ts <= available_ts:
            latest = row
        else:
            break
    return latest


def _latest_result_as_of(
    results: Sequence[PrimitiveResult],
    available_ts: datetime,
) -> PrimitiveResult | None:
    latest: PrimitiveResult | None = None
    for result in results:
        if result.available_ts <= available_ts:
            latest = result
        else:
            break
    return latest


def _return_result_flags(
    market: str,
    result: PrimitiveResult | None,
    row: OHLCVInputRow | None,
) -> tuple[str, ...]:
    if result is None:
        return (f"{market.lower()}_missing_history", "cross_market_gap")
    flags = set(_quality_flags(result.quality_flags))
    if result.value is None:
        flags.add("cross_market_gap")
        flags.add(f"{market.lower()}_return_gap")
    if row is not None:
        flags.update(_quality_flags(row.quality_flags))
    return tuple(sorted(flags))


def _bbo_quality_flags_at(
    bundle: CrossMarketInputBundle,
    available_ts: datetime,
) -> tuple[str, ...]:
    flags: set[str] = set()
    for market, view in bundle.bbo_by_instrument.items():
        for row in view.rows:
            if row.available_ts != available_ts:
                continue
            try:
                semantics = bbo_quote_semantics(row)
            except DataFoundationValidationError as exc:
                raise CrossMarketFeatureError(str(exc)) from exc
            if semantics.missing_or_abnormal:
                flags.add("bbo_gap")
                flags.add(f"{market.lower()}_bbo_gap")
                flags.update(_quality_flags(row.quality_flags))
    return tuple(sorted(flags))


def _snapshot_session_label(rows_at_t: Mapping[str, OHLCVInputRow | None]) -> str:
    labels = {
        _optional_text(row.session_label).upper()
        for row in rows_at_t.values()
        if row is not None and _optional_text(row.session_label)
    }
    if not labels:
        return ""
    if len(labels) == 1:
        return next(iter(labels))
    return "MIXED"


def _require_definition(
    definition: CrossMarketFeatureDefinition,
) -> CrossMarketFeatureDefinition:
    if not isinstance(definition, CrossMarketFeatureDefinition):
        raise CrossMarketFeatureError("compute requires a CrossMarketFeatureDefinition")
    if definition.spec.family is not FeatureFamily.CROSS_MARKET:
        raise CrossMarketFeatureError("definition must belong to FeatureFamily.CROSS_MARKET")
    if not definition.spec.implementation_eligible:
        raise CrossMarketFeatureError("definition is not implementation eligible")
    if not definition.request_gate_decision.implementation_allowed:
        raise CrossMarketFeatureError("FeatureRequest gate did not admit implementation")
    if definition.version != definition.spec.derive_feature_version():
        raise CrossMarketFeatureError("definition FeatureVersion does not match FeatureSpec")
    if not definition.spec.window.is_live_compatible:
        raise CrossMarketFeatureError("Cross-Market live features require causal windows")
    return definition


def _records_from_points(
    definition: CrossMarketFeatureDefinition,
    points: Sequence[_FeaturePoint],
) -> tuple[FeatureValueRecord, ...]:
    return tuple(
        FeatureValueRecord(
            feature_version_id=definition.feature_version_id,
            entity_id=_CROSS_MARKET_ENTITY_ID,
            event_ts=point.snapshot.event_ts,
            available_ts=point.snapshot.available_ts,
            value=point.value,
            quality_flags=_quality_flags(point.quality_flags),
        )
        for point in points
    )


def _point_feature(
    definition: CrossMarketFeatureDefinition,
    snapshot: CrossMarketAlignedSnapshot,
) -> _FeaturePoint:
    name = definition.name
    if name is CrossMarketFeatureName.SYNCHRONIZED_RETURNS:
        values, flags = _require_returns(snapshot, _MARKETS)
        if values is None:
            return _gap_feature_point(snapshot, "input_gap", flags)
        return _FeaturePoint(snapshot=snapshot, value={market: values[market] for market in _MARKETS}, quality_flags=snapshot.bbo_quality_flags)
    if name in {
        CrossMarketFeatureName.NQ_MINUS_ES_RETURN_SPREAD,
        CrossMarketFeatureName.RTY_MINUS_ES_RETURN_SPREAD,
    }:
        target, benchmark = _spread_pair(name)
        values, flags = _require_returns(snapshot, (target, benchmark))
        if values is None:
            return _gap_feature_point(snapshot, "input_gap", flags)
        return _FeaturePoint(
            snapshot=snapshot,
            value=values[target] - values[benchmark],
            quality_flags=snapshot.bbo_quality_flags,
        )
    if name is CrossMarketFeatureName.CONFIRMATION_FLAG:
        values, flags = _require_returns(snapshot, _MARKETS)
        if values is None:
            return _gap_feature_point(snapshot, "input_gap", flags)
        signs = [_sign(values[market]) for market in _MARKETS]
        return _FeaturePoint(
            snapshot=snapshot,
            value=1 if all(sign > 0 for sign in signs) or all(sign < 0 for sign in signs) else 0,
            quality_flags=snapshot.bbo_quality_flags,
        )
    if name is CrossMarketFeatureName.DIVERGENCE_FLAG:
        values, flags = _require_returns(snapshot, _MARKETS)
        if values is None:
            return _gap_feature_point(snapshot, "input_gap", flags)
        signs = [_sign(values[market]) for market in _MARKETS]
        positive = any(sign > 0 for sign in signs)
        negative = any(sign < 0 for sign in signs)
        return _FeaturePoint(
            snapshot=snapshot,
            value=1 if positive and negative else 0,
            quality_flags=snapshot.bbo_quality_flags,
        )
    if name in _ROTATION_FEATURES:
        values, flags = _require_returns(snapshot, _MARKETS)
        if values is None:
            return _gap_feature_point(snapshot, "input_gap", flags)
        risk_on = ((values["NQ"] - values["ES"]) + (values["RTY"] - values["ES"])) / 2.0
        return _FeaturePoint(
            snapshot=snapshot,
            value=risk_on if name is CrossMarketFeatureName.RISK_ON_ROTATION_PROXY else -risk_on,
            quality_flags=snapshot.bbo_quality_flags,
        )
    raise CrossMarketFeatureError(f"unsupported Cross-Market feature: {definition.name}")


def _rolling_feature_points(
    definition: CrossMarketFeatureDefinition,
    snapshots: Sequence[CrossMarketAlignedSnapshot],
) -> tuple[_FeaturePoint, ...]:
    target, benchmark = _rolling_pair(definition.name)
    window_length = definition.spec.window.length
    reset_on_session = _bool_parameter(definition, "reset_on_session")
    ddof = _int_parameter(definition, "ddof")
    points: list[_FeaturePoint] = []
    for index, snapshot in enumerate(snapshots):
        start = _window_start(
            snapshots,
            index,
            window_length,
            reset_on_session=reset_on_session,
        )
        window = tuple(snapshots[start : index + 1])
        if len(window) < window_length:
            points.append(_gap_feature_point(snapshot, "insufficient_window"))
            continue
        values: list[tuple[float, float]] = []
        gap_flags: set[str] = set()
        for item in window:
            item_values, item_flags = _require_returns(item, (target, benchmark))
            if item_values is None:
                gap_flags.update(item_flags)
                continue
            values.append((item_values[benchmark], item_values[target]))
        if gap_flags or len(values) != len(window):
            points.append(_gap_feature_point(snapshot, "input_gap", tuple(sorted(gap_flags))))
            continue
        if len(values) <= ddof:
            points.append(_gap_feature_point(snapshot, "insufficient_window"))
            continue
        benchmark_values = tuple(pair[0] for pair in values)
        target_values = tuple(pair[1] for pair in values)
        covariance = _covariance(target_values, benchmark_values, ddof)
        benchmark_variance = _variance(benchmark_values, ddof)
        if benchmark_variance == 0:
            points.append(_gap_feature_point(snapshot, "zero_benchmark_variance"))
            continue
        if definition.name in {
            CrossMarketFeatureName.NQ_ES_ROLLING_BETA_RESIDUAL,
            CrossMarketFeatureName.RTY_ES_ROLLING_BETA_RESIDUAL,
        }:
            beta = covariance / benchmark_variance
            points.append(
                _FeaturePoint(
                    snapshot=snapshot,
                    value=target_values[-1] - beta * benchmark_values[-1],
                    quality_flags=snapshot.bbo_quality_flags,
                )
            )
            continue
        target_variance = _variance(target_values, ddof)
        if target_variance == 0:
            points.append(_gap_feature_point(snapshot, "zero_target_variance"))
            continue
        points.append(
            _FeaturePoint(
                snapshot=snapshot,
                value=covariance / math.sqrt(benchmark_variance * target_variance),
                quality_flags=snapshot.bbo_quality_flags,
            )
        )
    return tuple(points)


def _require_returns(
    snapshot: CrossMarketAlignedSnapshot,
    markets: Sequence[str],
) -> tuple[dict[str, float], tuple[str, ...]] | tuple[None, tuple[str, ...]]:
    values: dict[str, float] = {}
    flags: set[str] = set(snapshot.bbo_quality_flags)
    for market in markets:
        value = snapshot.returns[market]
        if value is None:
            flags.add("input_gap")
            flags.update(snapshot.return_quality_flags[market])
            continue
        values[market] = _to_float(value, f"{market} return")
    if len(values) != len(tuple(markets)):
        return None, tuple(sorted(flags))
    return values, tuple(sorted(flags))


def _gap_feature_point(
    snapshot: CrossMarketAlignedSnapshot,
    reason: str,
    extra_flags: Sequence[str] = (),
) -> _FeaturePoint:
    return _FeaturePoint(
        snapshot=snapshot,
        value=None,
        quality_flags=tuple(
            sorted(
                {
                    "cross_market_gap",
                    reason.strip().lower(),
                    *snapshot.bbo_quality_flags,
                    *_quality_flags(extra_flags),
                }
            )
        ),
    )


def _spread_pair(name: CrossMarketFeatureName) -> tuple[str, str]:
    if name is CrossMarketFeatureName.NQ_MINUS_ES_RETURN_SPREAD:
        return "NQ", "ES"
    if name is CrossMarketFeatureName.RTY_MINUS_ES_RETURN_SPREAD:
        return "RTY", "ES"
    raise CrossMarketFeatureError(f"{name.value} is not a return-spread feature")


def _rolling_pair(name: CrossMarketFeatureName) -> tuple[str, str]:
    if name in {
        CrossMarketFeatureName.NQ_ES_ROLLING_BETA_RESIDUAL,
        CrossMarketFeatureName.NQ_ES_ROLLING_CORRELATION,
    }:
        return "NQ", "ES"
    if name in {
        CrossMarketFeatureName.RTY_ES_ROLLING_BETA_RESIDUAL,
        CrossMarketFeatureName.RTY_ES_ROLLING_CORRELATION,
    }:
        return "RTY", "ES"
    raise CrossMarketFeatureError(f"{name.value} is not a rolling pair feature")


def _window_start(
    snapshots: Sequence[CrossMarketAlignedSnapshot],
    index: int,
    window_length: int,
    *,
    reset_on_session: bool,
) -> int:
    start = max(0, index - window_length + 1)
    if not reset_on_session:
        return start
    current_session = snapshots[index].session_label
    for prior_index in range(index - 1, start - 1, -1):
        if snapshots[prior_index].session_label != current_session:
            return prior_index + 1
    return start


def _covariance(
    left_values: Sequence[float],
    right_values: Sequence[float],
    ddof: int,
) -> float:
    denominator = len(left_values) - ddof
    if denominator <= 0:
        raise CrossMarketFeatureError("covariance denominator must be positive")
    left_mean = sum(left_values) / len(left_values)
    right_mean = sum(right_values) / len(right_values)
    return sum(
        (left - left_mean) * (right - right_mean)
        for left, right in zip(left_values, right_values, strict=True)
    ) / denominator


def _variance(values: Sequence[float], ddof: int) -> float:
    denominator = len(values) - ddof
    if denominator <= 0:
        raise CrossMarketFeatureError("variance denominator must be positive")
    mean = sum(values) / len(values)
    return sum((value - mean) ** 2 for value in values) / denominator


def _sign(value: float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def _market_from_row(row: OHLCVInputRow | BBOInputRow) -> str:
    for candidate in (row.instrument_id, row.contract_id, row.series_id):
        text = _optional_text(candidate).upper()
        for market in _MARKETS:
            if text == market or text.startswith(market):
                return market
    raise CrossMarketFeatureError("row does not identify ES, NQ, or RTY")


def _row_matches_market(row: OHLCVInputRow | BBOInputRow, market: str) -> bool:
    try:
        return _market_from_row(row) == market
    except CrossMarketFeatureError:
        return False


def _coerce_market(value: object) -> str:
    text = _require_text(value, "market").upper()
    if text not in _MARKETS:
        raise CrossMarketFeatureError("Cross-Market features support exactly ES, NQ, and RTY")
    return text


def _coerce_feature_name(name: CrossMarketFeatureName | str) -> CrossMarketFeatureName:
    try:
        return CrossMarketFeatureName(name)
    except ValueError as exc:
        raise CrossMarketFeatureError(f"unsupported Cross-Market feature: {name}") from exc


def _int_parameter(definition: CrossMarketFeatureDefinition, name: str) -> int:
    value = definition.spec.transform.parameters.to_dict().get(name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise CrossMarketFeatureError(f"{name} parameter must be an integer")
    return value


def _bool_parameter(definition: CrossMarketFeatureDefinition, name: str) -> bool:
    value = definition.spec.transform.parameters.to_dict().get(name)
    if type(value) is not bool:
        raise CrossMarketFeatureError(f"{name} parameter must be a bool")
    return value


def _positive_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise CrossMarketFeatureError(f"{field_name} must be a positive integer")
    return value


def _non_negative_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise CrossMarketFeatureError(f"{field_name} must be a non-negative integer")
    return value


def _require_aware_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise CrossMarketFeatureError(f"{field_name} must be a timezone-aware datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise CrossMarketFeatureError(f"{field_name} must be timezone-aware")
    return value


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise CrossMarketFeatureError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise CrossMarketFeatureError(f"{field_name} must be non-empty")
    return normalized


def _optional_text(value: object) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise CrossMarketFeatureError("optional text must be a string")
    return value.strip()


def _to_float(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, _NUMERIC_TYPES):
        raise CrossMarketFeatureError(f"{field_name} must be numeric")
    parsed = float(value)
    if not math.isfinite(parsed):
        raise CrossMarketFeatureError(f"{field_name} must be finite")
    return parsed


def _quality_flags(flags: Sequence[str]) -> tuple[str, ...]:
    if isinstance(flags, str) or not isinstance(flags, Sequence):
        raise CrossMarketFeatureError("quality_flags must be a sequence of strings")
    normalized: list[str] = []
    for flag in flags:
        if not isinstance(flag, str) or not flag.strip():
            raise CrossMarketFeatureError("quality_flags must contain non-empty strings")
        token = flag.strip().lower()
        if token not in normalized:
            normalized.append(token)
    return tuple(normalized)


__all__ = [
    "CrossMarketAlignedSnapshot",
    "CrossMarketFeatureDefinition",
    "CrossMarketFeatureError",
    "CrossMarketFeatureName",
    "CrossMarketFeatureSpec",
    "CrossMarketFlagFeatureSpec",
    "CrossMarketInputBundle",
    "CrossMarketReturnFeatureSpec",
    "CrossMarketRollingFeatureSpec",
    "CrossMarketRotationFeatureSpec",
    "align_cross_market_rows",
    "build_cross_market_feature_definition",
    "build_cross_market_feature_definitions",
    "compute_cross_market_feature",
    "compute_cross_market_features",
    "supported_cross_market_features",
]
