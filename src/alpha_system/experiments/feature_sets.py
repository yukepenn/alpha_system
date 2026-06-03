"""Feature-set and label-reference contracts for local ML experiments."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from typing import Any

from alpha_system.experiments.version_refs import VersionRefError, validate_version_map


class FeatureSetError(ValueError):
    """Raised when an ML feature or label contract is incomplete or unsafe."""


RAW_FEATURE_KEYS = frozenset(
    {
        "raw_column",
        "raw_columns",
        "column",
        "columns",
        "source_column",
        "source_columns",
        "expression",
        "expr",
        "dataframe_column",
    }
)
RAW_SOURCE_VALUES = frozenset(
    {
        "raw",
        "ad_hoc",
        "adhoc",
        "bar",
        "bars",
        "ohlcv",
        "dataset",
        "dataframe",
        "canonical",
    }
)
LABEL_SOURCE_VALUES = frozenset({"label", "labels", "target", "outcome"})


@dataclass(frozen=True, slots=True)
class LabelSpec:
    """Reference to a versioned label input; labels are never features."""

    label_id: str
    label_version: str
    label_available_ts_field: str = "label_available_ts"
    decision_ts_field: str = "decision_ts"
    value_field: str | None = None
    horizon_bars: int = 1
    available_lag_bars: int = 0

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "LabelSpec":
        if not isinstance(payload, Mapping):
            raise FeatureSetError("label_spec must be a mapping")
        label_id = _text(payload.get("label_id"), "label_id")
        label_version = _text(payload.get("label_version"), "label_version")
        return cls(
            label_id=label_id,
            label_version=label_version,
            label_available_ts_field=_optional_text(
                payload.get("label_available_ts_field"),
                "label_available_ts_field",
            )
            or "label_available_ts",
            decision_ts_field=_optional_text(payload.get("decision_ts_field"), "decision_ts_field")
            or "decision_ts",
            value_field=_optional_text(payload.get("value_field"), "value_field"),
            horizon_bars=_non_negative_int(payload.get("horizon_bars", 1), "horizon_bars"),
            available_lag_bars=_non_negative_int(
                payload.get("available_lag_bars", 0),
                "available_lag_bars",
            ),
        )

    @property
    def effective_value_field(self) -> str:
        return self.value_field or self.label_id

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class FeatureReference:
    """One versioned factor feature consumed by an ML run."""

    factor_id: str
    factor_version: str
    feature_name: str | None = None
    transform: str = "identity"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, Any],
        *,
        factor_versions: Mapping[str, str],
        label_ids: Sequence[str] = (),
    ) -> "FeatureReference":
        if not isinstance(payload, Mapping):
            raise FeatureSetError("feature entries must be mappings")
        reject_raw_feature_payload(payload)
        source = _optional_text(payload.get("source"), "feature.source")
        if source is not None and source.lower() not in {"factor", "factor_version"}:
            if source.lower() in LABEL_SOURCE_VALUES:
                raise FeatureSetError("labels cannot be used as ML features")
            raise FeatureSetError("features must reference versioned factor inputs only")

        if "label_id" in payload or "label_version" in payload:
            raise FeatureSetError("labels cannot be used as ML features")
        factor_id = _optional_text(payload.get("factor_id"), "feature.factor_id") or _optional_text(
            payload.get("factor"),
            "feature.factor",
        )
        if factor_id is None:
            raise FeatureSetError("feature requires factor_id")
        if factor_id in set(label_ids):
            raise FeatureSetError("label ids cannot appear in feature references")
        if factor_id not in factor_versions:
            raise FeatureSetError(f"feature {factor_id!r} is missing a factor version reference")
        factor_version = _optional_text(
            payload.get("factor_version"),
            "feature.factor_version",
        ) or _optional_text(payload.get("version"), "feature.version")
        if factor_version is None:
            factor_version = factor_versions[factor_id]
        if factor_version != factor_versions[factor_id]:
            raise FeatureSetError(f"feature {factor_id!r} does not match factor_versions")

        return cls(
            factor_id=factor_id,
            factor_version=factor_version,
            feature_name=_optional_text(payload.get("feature_name"), "feature.feature_name")
            or _optional_text(payload.get("name"), "feature.name"),
            transform=_optional_text(payload.get("transform"), "feature.transform") or "identity",
            metadata=_metadata(payload.get("metadata")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class FeatureSetSpec:
    """A factor-version-only ML feature declaration."""

    feature_set_id: str
    data_version: str
    factor_versions: Mapping[str, str]
    features: tuple[FeatureReference, ...]
    description: str = ""
    universe: str | None = None
    instruments: tuple[str, ...] = ()

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, Any],
        *,
        label_spec: LabelSpec | None = None,
    ) -> "FeatureSetSpec":
        if not isinstance(payload, Mapping):
            raise FeatureSetError("feature_set must be a mapping")
        reject_raw_feature_payload(payload)
        if "raw_features" in payload:
            raise FeatureSetError("raw ad hoc feature columns are not allowed")

        required = ("feature_set_id", "data_version", "factor_versions", "features")
        missing = tuple(field_name for field_name in required if _missing(payload.get(field_name)))
        if missing:
            raise FeatureSetError(f"feature_set missing required fields: {', '.join(missing)}")

        try:
            factor_versions = validate_version_map(
                payload["factor_versions"],
                "factor_versions",
                allow_empty=False,
            )
        except VersionRefError as exc:
            raise FeatureSetError(str(exc)) from exc

        label_ids = (label_spec.label_id,) if label_spec is not None else _label_ids(payload)
        raw_features = payload["features"]
        if isinstance(raw_features, str) or not isinstance(raw_features, Sequence):
            raise FeatureSetError("features must be an explicit list of factor references")
        features = tuple(
            FeatureReference.from_mapping(
                feature,
                factor_versions=factor_versions,
                label_ids=label_ids,
            )
            for feature in raw_features
        )
        if not features:
            raise FeatureSetError("feature_set must include at least one feature")
        duplicate_ids = _duplicates(feature.factor_id for feature in features)
        if duplicate_ids:
            raise FeatureSetError(f"duplicate feature factor ids: {', '.join(duplicate_ids)}")

        return cls(
            feature_set_id=_text(payload["feature_set_id"], "feature_set_id"),
            data_version=_text(payload["data_version"], "data_version"),
            factor_versions=factor_versions,
            features=features,
            description=_optional_text(payload.get("description"), "description") or "",
            universe=_optional_text(payload.get("universe"), "universe"),
            instruments=_text_tuple(payload.get("instruments", ()), "instruments"),
        )

    @property
    def feature_ids(self) -> tuple[str, ...]:
        return tuple(feature.factor_id for feature in self.features)

    def validate_against_label(self, label_spec: LabelSpec) -> None:
        if label_spec.label_id in self.factor_versions or label_spec.label_id in self.feature_ids:
            raise FeatureSetError("label ids cannot appear in ML feature sets")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["factor_versions"] = dict(self.factor_versions)
        payload["features"] = [feature.to_dict() for feature in self.features]
        payload["instruments"] = list(self.instruments)
        return payload


def reject_raw_feature_payload(payload: Mapping[str, Any]) -> None:
    """Reject raw/ad hoc feature declarations before they reach a model run."""
    keys = {str(key) for key in payload}
    raw_keys = sorted(keys.intersection(RAW_FEATURE_KEYS))
    if raw_keys:
        raise FeatureSetError(f"raw ad hoc feature columns are not allowed: {', '.join(raw_keys)}")
    for source_key in ("source", "source_type", "feature_source", "input_source"):
        source = payload.get(source_key)
        if isinstance(source, str):
            lowered = source.strip().lower()
            if lowered in RAW_SOURCE_VALUES:
                raise FeatureSetError("features must reference versioned factor inputs only")
            if lowered in LABEL_SOURCE_VALUES:
                raise FeatureSetError("labels cannot be used as ML features")


def validate_label_not_in_features(feature_set: FeatureSetSpec, label_spec: LabelSpec) -> None:
    """Raise when a label is included in a feature set."""
    feature_set.validate_against_label(label_spec)


def validate_label_availability(
    rows: Sequence[Mapping[str, Any]],
    label_spec: LabelSpec,
) -> None:
    """Require label availability timestamps to be no later than decision timestamps."""
    for row_number, row in enumerate(rows):
        if label_spec.decision_ts_field not in row:
            raise FeatureSetError(
                f"row {row_number} missing {label_spec.decision_ts_field!r}",
            )
        if label_spec.label_available_ts_field not in row:
            raise FeatureSetError(
                f"row {row_number} missing {label_spec.label_available_ts_field!r}",
            )
        decision_ts = _time_key(row[label_spec.decision_ts_field])
        available_ts = _time_key(row[label_spec.label_available_ts_field])
        if available_ts > decision_ts:
            raise FeatureSetError(
                "label availability violates decision-time discipline "
                f"at row {row_number}",
            )


def _label_ids(payload: Mapping[str, Any]) -> tuple[str, ...]:
    candidates: list[str] = []
    for key in ("label_id", "target", "label"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            candidates.append(value.strip())
    label_spec = payload.get("label_spec")
    if isinstance(label_spec, Mapping):
        value = label_spec.get("label_id")
        if isinstance(value, str) and value.strip():
            candidates.append(value.strip())
    return tuple(dict.fromkeys(candidates))


def _duplicates(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    duplicate: set[str] = set()
    for value in values:
        if value in seen:
            duplicate.add(value)
        seen.add(value)
    return tuple(sorted(duplicate))


def _metadata(value: Any) -> Mapping[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise FeatureSetError("feature metadata must be a mapping")
    return dict(value)


def _text_tuple(value: Any, field_name: str) -> tuple[str, ...]:
    if value in (None, ""):
        return ()
    if isinstance(value, str):
        return (_text(value, field_name),)
    if not isinstance(value, Sequence):
        raise FeatureSetError(f"{field_name} must be a string or sequence of strings")
    return tuple(_text(item, field_name) for item in value)


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FeatureSetError(f"{field_name} must be a non-empty string")
    return value.strip()


def _optional_text(value: Any, field_name: str) -> str | None:
    if value in (None, ""):
        return None
    return _text(value, field_name)


def _non_negative_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise FeatureSetError(f"{field_name} must be a non-negative integer")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise FeatureSetError(f"{field_name} must be a non-negative integer") from exc
    if number < 0:
        raise FeatureSetError(f"{field_name} must be non-negative")
    return number


def _missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, Mapping | Sequence):
        return len(value) == 0
    return False


def _time_key(value: Any) -> tuple[int, float | str]:
    if isinstance(value, datetime):
        active = value
        if active.tzinfo is None:
            active = active.replace(tzinfo=timezone.utc)
        return (0, active.timestamp())
    if isinstance(value, date):
        return (0, datetime(value.year, value.month, value.day, tzinfo=timezone.utc).timestamp())
    if isinstance(value, int | float) and not isinstance(value, bool):
        return (0, float(value))
    text = str(value).strip()
    if not text:
        raise FeatureSetError("timestamp values must be non-empty")
    try:
        active = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return (1, text)
    if active.tzinfo is None:
        active = active.replace(tzinfo=timezone.utc)
    return (0, active.timestamp())
