"""Pooled Track-B hypothesis registration and value-free aggregation."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from alpha_system.governance.ids import (
    GovernanceIdError,
    GovernanceIdKind,
    generate_governance_id,
    validate_governance_id,
)
from alpha_system.governance.serialization import (
    GovernanceSerializationError,
    JsonValue,
    canonical_serialize,
    deserialize,
)
from alpha_system.governance.validation import (
    ExpectedType,
    GovernanceValidationError,
    ValidationIssue,
    require_mapping,
    validate_required_fields,
    validate_schema,
)
from alpha_system.governance.variant_ledger import (
    VariantLedger,
    VariantLedgerRecord,
    VariantLedgerStatus,
    validate_variant_ledger_record,
)

POOLED_HYPOTHESIS_REQUIRED_FIELDS = (
    "pooled_hypothesis_id",
    "mechanism_rationale",
    "pool_kind",
    "members",
    "aggregation_rule",
    "horizons",
    "sessions",
    "symbols",
    "registered_at",
    "registered_before_metrics",
    "variant_ledger_record",
)
POOLED_HYPOTHESIS_ID_COMPONENT_FIELDS = tuple(
    field for field in POOLED_HYPOTHESIS_REQUIRED_FIELDS if field != "pooled_hypothesis_id"
)
POOLED_HYPOTHESIS_FIELD_TYPES: dict[str, ExpectedType] = {
    "pooled_hypothesis_id": str,
    "mechanism_rationale": str,
    "pool_kind": str,
    "members": list,
    "aggregation_rule": str,
    "horizons": list,
    "sessions": list,
    "symbols": list,
    "registered_at": str,
    "registered_before_metrics": bool,
    "variant_ledger_record": dict,
}

METRICS_MARKER_TIMESTAMP_FIELDS = (
    "metrics_started_at",
    "track_a_metrics_started_at",
    "created_at",
)
POOLED_REGISTRY_DEFAULT_PATH = (
    "research/discovery_rigor_floor_v1/track_b/pooled_hypotheses.jsonl"
)
_VAGUE_TEXT = {
    "",
    "-",
    "n/a",
    "na",
    "none",
    "null",
    "tbd",
    "todo",
    "unknown",
    "placeholder",
    "to be defined",
    "to be determined",
    "unbounded",
    "unlimited",
}
_VAGUE_PHRASES = (
    "add later",
    "figure out later",
    "look into",
    "maybe useful",
    "might work",
    "needs research",
    "not sure",
    "some signal",
    "to be added",
)


class PoolKind(StrEnum):
    """Closed Track-B pooled-hypothesis types."""

    CROSS_SYMBOL = "cross_symbol"
    CROSS_HORIZON = "cross_horizon"
    CROSS_FAMILY = "cross_family"


class PooledAggregationRule(StrEnum):
    """Closed aggregation rules allowed for pooled evaluation."""

    EQUAL_WEIGHT_MEAN = "equal_weight_mean"


@dataclass(frozen=True, slots=True)
class PooledHypothesisRecord:
    """Immutable governance contract for a pre-declared pooled hypothesis."""

    pooled_hypothesis_id: str
    mechanism_rationale: str
    pool_kind: PoolKind
    members: tuple[str, ...]
    aggregation_rule: PooledAggregationRule
    horizons: tuple[str, ...]
    sessions: tuple[str, ...]
    symbols: tuple[str, ...]
    registered_at: str
    registered_before_metrics: bool
    variant_ledger_record: VariantLedgerRecord

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> PooledHypothesisRecord:
        """Build a pooled hypothesis record after fail-closed validation."""

        return validate_pooled_hypothesis_record(payload)

    @classmethod
    def from_canonical_json(cls, text: str) -> PooledHypothesisRecord:
        """Deserialize canonical JSON and validate the pooled hypothesis record."""

        value = deserialize(text)
        mapping = require_mapping(value, object_name="PooledHypothesisRecord")
        return validate_pooled_hypothesis_record(mapping)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible representation."""

        return {
            "pooled_hypothesis_id": self.pooled_hypothesis_id,
            "mechanism_rationale": self.mechanism_rationale,
            "pool_kind": self.pool_kind.value,
            "members": list(self.members),
            "aggregation_rule": self.aggregation_rule.value,
            "horizons": list(self.horizons),
            "sessions": list(self.sessions),
            "symbols": list(self.symbols),
            "registered_at": self.registered_at,
            "registered_before_metrics": self.registered_before_metrics,
            "variant_ledger_record": self.variant_ledger_record.to_dict(),
        }

    def to_canonical_json(self) -> str:
        """Serialize the validated record through canonical JSON."""

        return canonical_serialize(self.to_dict())


@dataclass(frozen=True, slots=True)
class ComponentMetricRecord:
    """Value-free component metric input for pooled aggregation."""

    component_ref: str
    metric_name: str
    point_estimate: float
    standard_error: float | None
    n_eff: int | None
    metadata: Mapping[str, JsonValue]

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> ComponentMetricRecord:
        """Validate a component metric mapping."""

        return validate_component_metric_record(payload)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible representation."""

        return {
            "component_ref": self.component_ref,
            "metric_name": self.metric_name,
            "point_estimate": self.point_estimate,
            "standard_error": self.standard_error,
            "n_eff": self.n_eff,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class PooledMetricResult:
    """Value-free pooled metric output including component evidence."""

    pooled_hypothesis_id: str
    aggregation_rule: PooledAggregationRule
    metric_name: str
    point_estimate: float
    standard_error: float | None
    n_eff: int | None
    components: tuple[ComponentMetricRecord, ...]

    def to_dict(self) -> dict[str, JsonValue]:
        """Return pooled result and every component used to compute it."""

        return {
            "pooled_hypothesis_id": self.pooled_hypothesis_id,
            "aggregation_rule": self.aggregation_rule.value,
            "pooled_result": {
                "metric_name": self.metric_name,
                "point_estimate": self.point_estimate,
                "standard_error": self.standard_error,
                "n_eff": self.n_eff,
            },
            "components": [component.to_dict() for component in self.components],
        }


@dataclass(frozen=True, slots=True)
class PooledHypothesisRegistrationResult:
    """Registration outcome with pooled and VariantLedger append counts."""

    record: PooledHypothesisRecord
    appended: bool
    variant_ledger_appended_count: int

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a JSON-compatible registration summary."""

        return {
            "pooled_hypothesis": self.record.to_dict(),
            "appended": self.appended,
            "variant_ledger_appended_count": self.variant_ledger_appended_count,
        }


class PooledHypothesisRegistry:
    """Append-only JSONL registry for immutable pooled hypothesis registrations."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = resolve_pooled_hypothesis_registry_path(path)

    def load_records(self) -> tuple[PooledHypothesisRecord, ...]:
        """Read all registered pooled hypotheses fail-closed."""

        _require_existing_file(self.path, field="pooled_hypothesis_registry_path")
        records: list[PooledHypothesisRecord] = []
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise GovernanceValidationError(
                ValidationIssue(
                    field="pooled_hypothesis_registry_path",
                    code="pooled_hypothesis_registry_read_failed",
                    message="PooledHypothesis registry path could not be read",
                    expected="readable text JSONL registry",
                    actual=f"{self.path}: {exc}",
                )
            ) from exc
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                value = deserialize(line)
                mapping = require_mapping(value, object_name="PooledHypothesisRecord")
                records.append(validate_pooled_hypothesis_record(mapping))
            except (GovernanceSerializationError, GovernanceValidationError) as exc:
                raise GovernanceValidationError(
                    ValidationIssue(
                        field=f"pooled_hypothesis_registry_path:{line_number}",
                        code="invalid_pooled_hypothesis_registry_row",
                        message="PooledHypothesis registry row is not a valid canonical record",
                        expected="canonical PooledHypothesisRecord JSON line",
                        actual=str(exc),
                    )
                ) from exc
        return tuple(records)

    def register(
        self,
        payload: PooledHypothesisRecord | Mapping[str, Any],
        *,
        variant_ledger_path: str | Path | None,
        metrics_started_marker_path: str | Path | None = None,
    ) -> PooledHypothesisRegistrationResult:
        """Append one pooled hypothesis and exactly one linked VariantLedger entry."""

        _require_existing_file(self.path, field="pooled_hypothesis_registry_path")
        _require_writable_file(self.path, field="pooled_hypothesis_registry_path")
        variant_ledger = VariantLedger(variant_ledger_path)
        variant_ledger.require_writable()

        incoming_mapping = (
            payload.to_dict() if isinstance(payload, PooledHypothesisRecord) else payload
        )
        incoming_mapping = require_mapping(
            incoming_mapping,
            object_name="PooledHypothesisRecord",
        )
        existing = self.load_records()
        existing_by_id = {record.pooled_hypothesis_id: record for record in existing}
        incoming_id = incoming_mapping.get("pooled_hypothesis_id")
        if isinstance(incoming_id, str) and incoming_id in existing_by_id:
            prior = existing_by_id[incoming_id]
            if canonical_serialize(incoming_mapping) != prior.to_canonical_json():
                raise GovernanceValidationError(
                    ValidationIssue(
                        field="pooled_hypothesis_id",
                        code="pooled_hypothesis_payload_conflict",
                        message=(
                            "PooledHypothesis registry refuses modified payload under "
                            "an existing pooled_hypothesis_id"
                        ),
                        expected="identical canonical payload or new content-addressed ID",
                        actual=_diff_summary(prior.to_dict(), incoming_mapping),
                    )
                )
            ensure_registration_precedes_metrics(prior, metrics_started_marker_path)
            appended_variant = variant_ledger.append_records((prior.variant_ledger_record,))
            return PooledHypothesisRegistrationResult(
                record=prior,
                appended=False,
                variant_ledger_appended_count=len(appended_variant),
        )

        record = validate_pooled_hypothesis_record(incoming_mapping)
        _refuse_new_registration_when_metrics_started(metrics_started_marker_path)
        ensure_registration_precedes_metrics(record, metrics_started_marker_path)
        appended_variant = variant_ledger.append_records((record.variant_ledger_record,))
        try:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(record.to_canonical_json())
                handle.write("\n")
        except OSError as exc:
            raise GovernanceValidationError(
                ValidationIssue(
                    field="pooled_hypothesis_registry_path",
                    code="pooled_hypothesis_registry_append_failed",
                    message="PooledHypothesis registry path could not be appended",
                    expected="appendable text JSONL registry",
                    actual=f"{self.path}: {exc}",
                )
            ) from exc
        return PooledHypothesisRegistrationResult(
            record=record,
            appended=True,
            variant_ledger_appended_count=len(appended_variant),
        )


def resolve_pooled_hypothesis_registry_path(path: str | Path | None = None) -> Path:
    """Resolve the explicitly supplied pooled-hypothesis registry path."""

    if path is None or _normalize_text(path) in _VAGUE_TEXT:
        raise GovernanceValidationError(
            ValidationIssue(
                field="pooled_hypothesis_registry_path",
                code="missing_pooled_hypothesis_registry_path",
                message="PooledHypothesis registry path is required",
                expected="explicit path to an existing writable JSONL registry",
                actual="missing",
            )
        )
    return Path(path).expanduser()


def generate_pooled_hypothesis_id(payload: Mapping[str, Any]) -> str:
    """Generate the deterministic pooled-hypothesis ID from contract fields."""

    mapping = validate_required_fields(
        payload,
        POOLED_HYPOTHESIS_ID_COMPONENT_FIELDS,
        object_name="PooledHypothesisRecord",
    )
    components = {
        field: _id_component(field, mapping[field])
        for field in POOLED_HYPOTHESIS_ID_COMPONENT_FIELDS
    }
    return generate_governance_id(GovernanceIdKind.POOLED_HYPOTHESIS_RECORD, components)


def validate_pooled_hypothesis_record(
    payload: Mapping[str, Any],
) -> PooledHypothesisRecord:
    """Validate a pooled hypothesis registration fail-closed."""

    mapping = validate_schema(
        payload,
        required_fields=POOLED_HYPOTHESIS_REQUIRED_FIELDS,
        field_types=POOLED_HYPOTHESIS_FIELD_TYPES,
        allowed_fields=POOLED_HYPOTHESIS_REQUIRED_FIELDS,
        object_name="PooledHypothesisRecord",
    )

    issues: list[ValidationIssue] = []
    issues.extend(_validate_pooled_hypothesis_id(mapping))
    issues.extend(
        _validate_substantive_text(
            mapping["mechanism_rationale"],
            field="mechanism_rationale",
            minimum_chars=40,
        )
    )
    pool_kind = _parse_pool_kind(mapping["pool_kind"], issues)
    aggregation_rule = _parse_aggregation_rule(mapping["aggregation_rule"], issues)
    members = _validate_member_refs(mapping["members"], issues)
    horizons = _validate_fixed_text_list(mapping["horizons"], "horizons", issues)
    sessions = _validate_fixed_text_list(mapping["sessions"], "sessions", issues)
    symbols = _validate_fixed_text_list(mapping["symbols"], "symbols", issues)
    issues.extend(_validate_utc_timestamp(mapping["registered_at"], field="registered_at"))
    if mapping["registered_before_metrics"] is not True:
        issues.append(
            ValidationIssue(
                field="registered_before_metrics",
                code="pooled_hypothesis_not_attested_before_metrics",
                message="pooled hypothesis must attest registration before Track-A metrics",
                expected="true",
                actual=str(mapping["registered_before_metrics"]),
            )
        )
    variant_ledger_record = _validate_linked_variant_ledger_record(
        mapping["variant_ledger_record"],
        registered_at=mapping["registered_at"],
        members=members,
        issues=issues,
    )
    issues.extend(_validate_pool_kind_shape(pool_kind, horizons, sessions, symbols))
    issues.extend(_validate_canonical_serializable(mapping))
    if not issues:
        expected_id = generate_pooled_hypothesis_id(mapping)
        if mapping["pooled_hypothesis_id"] != expected_id:
            issues.append(
                ValidationIssue(
                    field="pooled_hypothesis_id",
                    code="pooled_hypothesis_id_mismatch",
                    message=(
                        "PooledHypothesisRecord.pooled_hypothesis_id must match "
                        "deterministic contract content"
                    ),
                    expected=expected_id,
                    actual=str(mapping["pooled_hypothesis_id"]),
                )
            )

    if issues:
        raise GovernanceValidationError(issues)

    assert pool_kind is not None
    assert aggregation_rule is not None
    assert members is not None
    assert horizons is not None
    assert sessions is not None
    assert symbols is not None
    assert variant_ledger_record is not None
    return PooledHypothesisRecord(
        pooled_hypothesis_id=mapping["pooled_hypothesis_id"],
        mechanism_rationale=mapping["mechanism_rationale"],
        pool_kind=pool_kind,
        members=members,
        aggregation_rule=aggregation_rule,
        horizons=horizons,
        sessions=sessions,
        symbols=symbols,
        registered_at=mapping["registered_at"],
        registered_before_metrics=mapping["registered_before_metrics"],
        variant_ledger_record=variant_ledger_record,
    )


def ensure_registration_precedes_metrics(
    record: PooledHypothesisRecord | Mapping[str, Any],
    metrics_started_marker_path: str | Path | None,
) -> None:
    """Fail if the Track-A metrics marker exists and predates registration."""

    active_record = (
        validate_pooled_hypothesis_record(record)
        if isinstance(record, Mapping)
        else validate_pooled_hypothesis_record(record.to_dict())
    )
    if metrics_started_marker_path is None:
        return
    marker_path = Path(metrics_started_marker_path).expanduser()
    if not marker_path.exists():
        return
    if not marker_path.is_file():
        raise GovernanceValidationError(
            ValidationIssue(
                field="metrics_started_marker_path",
                code="invalid_metrics_started_marker",
                message="metrics-started marker must be a file when present",
                expected="absent marker or file containing a UTC timestamp",
                actual=str(marker_path),
            )
        )
    started_at = _read_metrics_started_at(marker_path)
    registered = _utc_datetime(active_record.registered_at, field="registered_at")
    if registered >= started_at:
        raise GovernanceValidationError(
            ValidationIssue(
                field="registered_at",
                code="pooled_registration_after_metrics_started",
                message="pooled hypothesis registration must precede Track-A metrics",
                expected=f"registered_at < {started_at.isoformat().replace('+00:00', 'Z')}",
                actual=active_record.registered_at,
            )
        )


def _refuse_new_registration_when_metrics_started(
    metrics_started_marker_path: str | Path | None,
) -> None:
    if metrics_started_marker_path is None:
        return
    marker_path = Path(metrics_started_marker_path).expanduser()
    if not marker_path.exists():
        return
    raise GovernanceValidationError(
        ValidationIssue(
            field="metrics_started_marker_path",
            code="pooled_registration_window_closed",
            message=(
                "new pooled hypothesis registrations are closed once the "
                "Track-A metrics-started marker exists"
            ),
            expected="absent metrics-started marker for new registration",
            actual=str(marker_path),
        )
    )


def aggregate_pooled_metric(
    record: PooledHypothesisRecord | Mapping[str, Any],
    component_metrics: Iterable[ComponentMetricRecord | Mapping[str, Any]],
) -> PooledMetricResult:
    """Aggregate component metrics under the declared fixed rule."""

    active_record = (
        validate_pooled_hypothesis_record(record)
        if isinstance(record, Mapping)
        else validate_pooled_hypothesis_record(record.to_dict())
    )
    if active_record.aggregation_rule is not PooledAggregationRule.EQUAL_WEIGHT_MEAN:
        raise GovernanceValidationError(
            ValidationIssue(
                field="aggregation_rule",
                code="unsupported_pooled_aggregation_rule",
                message="pooled aggregation only supports equal_weight_mean in this phase",
                expected=PooledAggregationRule.EQUAL_WEIGHT_MEAN.value,
                actual=active_record.aggregation_rule.value,
            )
        )
    components = _coerce_component_metrics(component_metrics)
    _validate_component_membership(active_record, components)
    metric_names = {component.metric_name for component in components}
    if len(metric_names) != 1:
        raise GovernanceValidationError(
            ValidationIssue(
                field="metric_name",
                code="mixed_component_metric_names",
                message="pooled aggregation requires exactly one metric name",
                expected="all components share one metric_name",
                actual=", ".join(sorted(metric_names)),
            )
        )
    count = len(components)
    pooled_estimate = sum(component.point_estimate for component in components) / count
    standard_error = None
    if all(component.standard_error is not None for component in components):
        standard_error = math.sqrt(
            sum(float(component.standard_error) ** 2 for component in components)
        ) / count
    n_eff = None
    if all(component.n_eff is not None for component in components):
        n_eff = sum(int(component.n_eff) for component in components)
    return PooledMetricResult(
        pooled_hypothesis_id=active_record.pooled_hypothesis_id,
        aggregation_rule=active_record.aggregation_rule,
        metric_name=next(iter(metric_names)),
        point_estimate=pooled_estimate,
        standard_error=standard_error,
        n_eff=n_eff,
        components=tuple(sorted(components, key=lambda component: component.component_ref)),
    )


def track_b_minimum_satisfied(
    records: Iterable[PooledHypothesisRecord | Mapping[str, Any]],
    kill_shot_study_set: Iterable[str],
) -> bool:
    """Return true when Track B has cross-symbol and cross-horizon registrations."""

    kill_set = _validate_kill_shot_study_set(kill_shot_study_set)
    has_cross_symbol = False
    has_cross_horizon = False
    for record in _coerce_pooled_records(records):
        if not record.registered_before_metrics:
            continue
        if not set(record.members).issubset(kill_set):
            continue
        if record.pool_kind is PoolKind.CROSS_SYMBOL:
            has_cross_symbol = True
        elif record.pool_kind is PoolKind.CROSS_HORIZON:
            has_cross_horizon = True
    return has_cross_symbol and has_cross_horizon


def validate_component_metric_record(payload: Mapping[str, Any]) -> ComponentMetricRecord:
    """Validate one value-free component metric record."""

    mapping = validate_schema(
        payload,
        required_fields=(
            "component_ref",
            "metric_name",
            "point_estimate",
            "metadata",
        ),
        field_types={
            "component_ref": str,
            "metric_name": str,
            "point_estimate": (int, float),
            "standard_error": (int, float, type(None)),
            "n_eff": (int, type(None)),
            "metadata": dict,
        },
        allowed_fields=(
            "component_ref",
            "metric_name",
            "point_estimate",
            "standard_error",
            "n_eff",
            "metadata",
        ),
        object_name="ComponentMetricRecord",
    )
    missing_nullable = [
        ValidationIssue(
            field=field,
            code="missing_required_field",
            message=f"ComponentMetricRecord.{field} is required",
            expected="present value or explicit null",
            actual="missing",
        )
        for field in ("standard_error", "n_eff")
        if field not in mapping
    ]
    if missing_nullable:
        raise GovernanceValidationError(missing_nullable)
    issues: list[ValidationIssue] = []
    issues.extend(_validate_text_value(mapping["component_ref"], field="component_ref"))
    issues.extend(_validate_text_value(mapping["metric_name"], field="metric_name"))
    point_estimate = _validate_finite_float(
        mapping["point_estimate"],
        field="point_estimate",
        issues=issues,
    )
    standard_error = None
    if mapping["standard_error"] is not None:
        standard_error = _validate_finite_float(
            mapping["standard_error"],
            field="standard_error",
            issues=issues,
        )
        if standard_error is not None and standard_error < 0:
            issues.append(
                ValidationIssue(
                    field="standard_error",
                    code="negative_standard_error",
                    message="ComponentMetricRecord.standard_error must be non-negative",
                    expected="non-negative finite number or null",
                    actual=str(mapping["standard_error"]),
                )
            )
    n_eff = None
    if mapping["n_eff"] is not None:
        if type(mapping["n_eff"]) is not int or mapping["n_eff"] <= 0:
            issues.append(
                ValidationIssue(
                    field="n_eff",
                    code="invalid_n_eff",
                    message="ComponentMetricRecord.n_eff must be positive when present",
                    expected="positive int or null",
                    actual=str(mapping["n_eff"]),
                )
            )
        else:
            n_eff = mapping["n_eff"]
    issues.extend(_validate_metadata_mapping(mapping["metadata"], field="metadata"))
    issues.extend(_validate_component_metric_serializable(mapping))
    if issues:
        raise GovernanceValidationError(issues)
    assert point_estimate is not None
    return ComponentMetricRecord(
        component_ref=mapping["component_ref"],
        metric_name=mapping["metric_name"],
        point_estimate=point_estimate,
        standard_error=standard_error,
        n_eff=n_eff,
        metadata=dict(mapping["metadata"]),
    )


def _id_component(field: str, value: Any) -> JsonValue:
    if field == "pool_kind":
        return PoolKind(value).value
    if field == "aggregation_rule":
        return PooledAggregationRule(value).value
    if field == "variant_ledger_record":
        return validate_variant_ledger_record(value).to_dict()
    return value


def _validate_pooled_hypothesis_id(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    try:
        validate_governance_id(
            mapping["pooled_hypothesis_id"],
            expected_kind=GovernanceIdKind.POOLED_HYPOTHESIS_RECORD,
        )
    except GovernanceIdError as exc:
        return [
            ValidationIssue(
                field="pooled_hypothesis_id",
                code=exc.issue.code,
                message=exc.issue.message,
                expected=GovernanceIdKind.POOLED_HYPOTHESIS_RECORD.value,
                actual=str(exc.issue.value),
            )
        ]
    return []


def _parse_pool_kind(value: object, issues: list[ValidationIssue]) -> PoolKind | None:
    try:
        return PoolKind(value)
    except ValueError:
        issues.append(
            ValidationIssue(
                field="pool_kind",
                code="invalid_pool_kind",
                message="PooledHypothesisRecord.pool_kind must be declared",
                expected=" | ".join(item.value for item in PoolKind),
                actual=str(value),
            )
        )
        return None


def _parse_aggregation_rule(
    value: object,
    issues: list[ValidationIssue],
) -> PooledAggregationRule | None:
    try:
        return PooledAggregationRule(value)
    except ValueError:
        issues.append(
            ValidationIssue(
                field="aggregation_rule",
                code="invalid_pooled_aggregation_rule",
                message="PooledHypothesisRecord.aggregation_rule must be declared",
                expected=" | ".join(item.value for item in PooledAggregationRule),
                actual=str(value),
            )
        )
        return None


def _validate_member_refs(values: list[Any], issues: list[ValidationIssue]) -> tuple[str, ...] | None:
    members = _validate_fixed_text_list(values, "members", issues, minimum_count=2)
    if members is None:
        return None
    for index, member in enumerate(members):
        if member.startswith("sspec_"):
            anchor = member.split("#", maxsplit=1)[0]
            try:
                validate_governance_id(anchor, expected_kind=GovernanceIdKind.STUDY_SPEC)
            except GovernanceIdError as exc:
                issues.append(
                    ValidationIssue(
                        field=f"members[{index}]",
                        code=exc.issue.code,
                        message=exc.issue.message,
                        expected=GovernanceIdKind.STUDY_SPEC.value,
                        actual=str(exc.issue.value),
                    )
                )
    return members


def _validate_fixed_text_list(
    values: list[Any],
    field: str,
    issues: list[ValidationIssue],
    *,
    minimum_count: int = 1,
) -> tuple[str, ...] | None:
    if len(values) < minimum_count:
        issues.append(
            ValidationIssue(
                field=field,
                code="empty_required_field",
                message=f"PooledHypothesisRecord.{field} must declare fixed members",
                expected=f"at least {minimum_count} entries",
                actual=str(len(values)),
            )
        )
        return None
    seen: set[str] = set()
    result: list[str] = []
    for index, value in enumerate(values):
        item_field = f"{field}[{index}]"
        item_issues = _validate_text_value(value, field=item_field)
        if item_issues:
            issues.extend(item_issues)
            continue
        assert isinstance(value, str)
        if value in seen:
            issues.append(
                ValidationIssue(
                    field=item_field,
                    code="duplicate_fixed_pool_member",
                    message=f"PooledHypothesisRecord.{field} must not contain duplicates",
                    expected="unique fixed entries",
                    actual=value,
                )
            )
            continue
        seen.add(value)
        result.append(value)
    return tuple(result) if not any(issue.field.startswith(field) for issue in issues) else None


def _validate_linked_variant_ledger_record(
    value: Mapping[str, Any],
    *,
    registered_at: str,
    members: tuple[str, ...] | None,
    issues: list[ValidationIssue],
) -> VariantLedgerRecord | None:
    try:
        record = validate_variant_ledger_record(value)
    except GovernanceValidationError as exc:
        issues.extend(exc.issues)
        return None
    if record.status is not VariantLedgerStatus.PLANNED:
        issues.append(
            ValidationIssue(
                field="variant_ledger_record.status",
                code="pooled_variant_ledger_status_not_planned",
                message="pooled VariantLedger linkage must be registered before results",
                expected=VariantLedgerStatus.PLANNED.value,
                actual=record.status.value,
            )
        )
    if record.created_at != registered_at:
        issues.append(
            ValidationIssue(
                field="variant_ledger_record.created_at",
                code="pooled_variant_ledger_timestamp_mismatch",
                message="pooled VariantLedger linkage timestamp must match registered_at",
                expected=registered_at,
                actual=record.created_at,
            )
        )
    member_anchors = {member.split("#", maxsplit=1)[0] for member in members or ()}
    if members is not None and record.study_spec_id not in member_anchors:
        issues.append(
            ValidationIssue(
                field="variant_ledger_record.study_spec_id",
                code="pooled_variant_ledger_anchor_not_member",
                message="pooled VariantLedger linkage must anchor to a fixed member",
                expected=", ".join(members),
                actual=record.study_spec_id,
            )
        )
    return record


def _validate_pool_kind_shape(
    pool_kind: PoolKind | None,
    horizons: tuple[str, ...] | None,
    sessions: tuple[str, ...] | None,
    symbols: tuple[str, ...] | None,
) -> list[ValidationIssue]:
    if pool_kind is None or horizons is None or sessions is None or symbols is None:
        return []
    issues: list[ValidationIssue] = []
    if pool_kind is PoolKind.CROSS_SYMBOL and len(symbols) < 2:
        issues.append(
            ValidationIssue(
                field="symbols",
                code="cross_symbol_pool_requires_multiple_symbols",
                message="cross-symbol pooled hypotheses must fix at least two symbols",
                expected=">= 2 symbols",
                actual=str(len(symbols)),
            )
        )
    if pool_kind is PoolKind.CROSS_HORIZON and len(horizons) < 2:
        issues.append(
            ValidationIssue(
                field="horizons",
                code="cross_horizon_pool_requires_multiple_horizons",
                message="cross-horizon pooled hypotheses must fix at least two horizons",
                expected=">= 2 horizons",
                actual=str(len(horizons)),
            )
        )
    if pool_kind is PoolKind.CROSS_FAMILY:
        # Family membership is expressed through fixed members; no extra free-form family rule.
        return issues
    if len(sessions) < 1:
        issues.append(
            ValidationIssue(
                field="sessions",
                code="pooled_hypothesis_missing_session_set",
                message="pooled hypotheses must fix the session set before metrics",
                expected="at least one session",
                actual="0",
            )
        )
    return issues


def _validate_substantive_text(
    value: object,
    *,
    field: str,
    minimum_chars: int,
) -> list[ValidationIssue]:
    issues = _validate_text_value(value, field=field)
    if issues:
        return issues
    assert isinstance(value, str)
    normalized = _normalize_text(value)
    if len(value.strip()) < minimum_chars:
        return [
            ValidationIssue(
                field=field,
                code="too_short_required_field",
                message=f"{field} must be substantive enough for review",
                expected=f"at least {minimum_chars} characters",
                actual=str(len(value.strip())),
            )
        ]
    for phrase in _VAGUE_PHRASES:
        if phrase in normalized:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="vague_required_field",
                    message=f"{field} must be mechanism-based, not vague",
                    expected="specific mechanism rationale",
                    actual=value,
                )
            )
            break
    return issues


def _validate_text_value(value: object, *, field: str) -> list[ValidationIssue]:
    if not isinstance(value, str) or _normalize_text(value) in _VAGUE_TEXT:
        return [
            ValidationIssue(
                field=field,
                code="empty_required_field",
                message=f"{field} must be an explicit non-empty string",
                expected="non-empty explicit string",
                actual=str(value),
            )
        ]
    return []


def _validate_metadata_mapping(value: Mapping[str, Any], *, field: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for key, item in value.items():
        if not isinstance(key, str) or _normalize_text(key) in _VAGUE_TEXT:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="invalid_metadata_key",
                    message=f"{field} keys must be explicit strings",
                    expected="non-empty explicit string key",
                    actual=str(key),
                )
            )
        if item is None:
            issues.append(
                ValidationIssue(
                    field=f"{field}.{key}",
                    code="null_metadata_value",
                    message=f"{field} values must be explicit when present",
                    expected="JSON value other than null",
                    actual="NoneType",
                )
            )
    return issues


def _validate_canonical_serializable(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    try:
        canonical_serialize(
            {
                field: _id_component(field, mapping[field])
                for field in POOLED_HYPOTHESIS_REQUIRED_FIELDS
            }
        )
    except (GovernanceSerializationError, GovernanceValidationError, ValueError) as exc:
        return [
            ValidationIssue(
                field="$",
                code="pooled_hypothesis_not_canonical",
                message="PooledHypothesisRecord must be canonically serializable",
                expected="canonical JSON-compatible PooledHypothesisRecord",
                actual=str(exc),
            )
        ]
    return []


def _validate_component_metric_serializable(
    mapping: Mapping[str, Any],
) -> list[ValidationIssue]:
    try:
        canonical_serialize(
            {
                "component_ref": mapping["component_ref"],
                "metric_name": mapping["metric_name"],
                "point_estimate": float(mapping["point_estimate"]),
                "standard_error": (
                    None
                    if mapping["standard_error"] is None
                    else float(mapping["standard_error"])
                ),
                "n_eff": mapping["n_eff"],
                "metadata": dict(mapping["metadata"]),
            }
        )
    except GovernanceSerializationError as exc:
        return [
            ValidationIssue(
                field=exc.issue.path,
                code=exc.issue.code,
                message=exc.issue.message,
                expected="canonical JSON-compatible ComponentMetricRecord",
                actual=exc.issue.path,
            )
        ]
    return []


def _validate_finite_float(
    value: int | float,
    *,
    field: str,
    issues: list[ValidationIssue],
) -> float | None:
    if isinstance(value, bool):
        issues.append(
            ValidationIssue(
                field=field,
                code="invalid_number_type",
                message=f"ComponentMetricRecord.{field} must be numeric",
                expected="finite int or float",
                actual="bool",
            )
        )
        return None
    number = float(value)
    if not math.isfinite(number):
        issues.append(
            ValidationIssue(
                field=field,
                code="non_finite_number",
                message=f"ComponentMetricRecord.{field} must be finite",
                expected="finite int or float",
                actual=str(value),
            )
        )
        return None
    return number


def _coerce_component_metrics(
    values: Iterable[ComponentMetricRecord | Mapping[str, Any]],
) -> tuple[ComponentMetricRecord, ...]:
    if isinstance(values, Mapping) or isinstance(values, str) or values is None:
        raise GovernanceValidationError(
            ValidationIssue(
                field="component_metrics",
                code="invalid_component_metrics_type",
                message="component metrics must be an iterable",
                expected="iterable of ComponentMetricRecord or mapping",
                actual=type(values).__name__,
            )
        )
    return tuple(
        validate_component_metric_record(
            value.to_dict() if isinstance(value, ComponentMetricRecord) else value
        )
        for value in values
    )


def _validate_component_membership(
    record: PooledHypothesisRecord,
    components: tuple[ComponentMetricRecord, ...],
) -> None:
    if not components:
        raise GovernanceValidationError(
            ValidationIssue(
                field="component_metrics",
                code="missing_component_metrics",
                message="pooled aggregation requires one metric record per fixed member",
                expected=", ".join(record.members),
                actual="0",
            )
        )
    component_refs = [component.component_ref for component in components]
    if len(component_refs) != len(set(component_refs)):
        raise GovernanceValidationError(
            ValidationIssue(
                field="component_ref",
                code="duplicate_component_metric",
                message="component metrics must contain one row per fixed member",
                expected="unique component_ref values",
                actual=", ".join(sorted(component_refs)),
            )
        )
    expected = set(record.members)
    actual = set(component_refs)
    if expected != actual:
        raise GovernanceValidationError(
            ValidationIssue(
                field="component_metrics",
                code="pooled_component_membership_mismatch",
                message="component metrics must exactly match fixed pooled membership",
                expected=", ".join(sorted(expected)),
                actual=", ".join(sorted(actual)),
            )
        )


def _coerce_pooled_records(
    values: Iterable[PooledHypothesisRecord | Mapping[str, Any]],
) -> tuple[PooledHypothesisRecord, ...]:
    if isinstance(values, Mapping) or isinstance(values, str) or values is None:
        raise GovernanceValidationError(
            ValidationIssue(
                field="records",
                code="invalid_pooled_records_type",
                message="pooled records must be an iterable",
                expected="iterable of PooledHypothesisRecord or mapping",
                actual=type(values).__name__,
            )
        )
    return tuple(
        validate_pooled_hypothesis_record(
            value.to_dict() if isinstance(value, PooledHypothesisRecord) else value
        )
        for value in values
    )


def _validate_kill_shot_study_set(values: Iterable[str]) -> set[str]:
    if isinstance(values, str) or values is None:
        raise GovernanceValidationError(
            ValidationIssue(
                field="kill_shot_study_set",
                code="invalid_kill_shot_study_set",
                message="kill-shot study set must be an iterable of fixed refs",
                expected="iterable of member refs",
                actual=type(values).__name__,
            )
        )
    result: set[str] = set()
    issues: list[ValidationIssue] = []
    for index, value in enumerate(values):
        if not isinstance(value, str) or _normalize_text(value) in _VAGUE_TEXT:
            issues.append(
                ValidationIssue(
                    field=f"kill_shot_study_set[{index}]",
                    code="invalid_kill_shot_study_ref",
                    message="kill-shot study set entries must be explicit refs",
                    expected="non-empty string",
                    actual=str(value),
                )
            )
            continue
        result.add(value)
    if not result:
        issues.append(
            ValidationIssue(
                field="kill_shot_study_set",
                code="empty_kill_shot_study_set",
                message="kill-shot study set must not be empty",
                expected="at least one fixed ref",
                actual="0",
            )
        )
    if issues:
        raise GovernanceValidationError(issues)
    return result


def _read_metrics_started_at(path: Path) -> datetime:
    try:
        text = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise GovernanceValidationError(
            ValidationIssue(
                field="metrics_started_marker_path",
                code="metrics_started_marker_read_failed",
                message="metrics-started marker could not be read",
                expected="readable marker file",
                actual=f"{path}: {exc}",
            )
        ) from exc
    if not text:
        raise GovernanceValidationError(
            ValidationIssue(
                field="metrics_started_marker_path",
                code="empty_metrics_started_marker",
                message="metrics-started marker must contain a UTC timestamp",
                expected="JSON object with metrics_started_at or plain UTC timestamp",
                actual="empty",
            )
        )
    timestamp = text
    try:
        value = deserialize(text)
    except GovernanceSerializationError:
        value = None
    if isinstance(value, Mapping):
        for field in METRICS_MARKER_TIMESTAMP_FIELDS:
            if isinstance(value.get(field), str):
                timestamp = value[field]
                break
        else:
            raise GovernanceValidationError(
                ValidationIssue(
                    field="metrics_started_marker_path",
                    code="missing_metrics_started_at",
                    message="metrics-started marker JSON must declare a timestamp",
                    expected="metrics_started_at, track_a_metrics_started_at, or created_at",
                    actual=", ".join(str(key) for key in value.keys()),
                )
            )
    elif isinstance(value, str):
        timestamp = value
    return _utc_datetime(timestamp, field="metrics_started_marker_path")


def _utc_datetime(value: str, *, field: str) -> datetime:
    issues = _validate_utc_timestamp(value, field=field)
    if issues:
        raise GovernanceValidationError(issues)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _validate_utc_timestamp(value: object, *, field: str) -> list[ValidationIssue]:
    if not isinstance(value, str) or not value.endswith("Z"):
        return [
            ValidationIssue(
                field=field,
                code="invalid_utc_timestamp",
                message=f"{field} must be an ISO-8601 UTC timestamp ending in Z",
                expected="YYYY-MM-DDTHH:MM:SSZ",
                actual=str(value),
            )
        ]
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return [
            ValidationIssue(
                field=field,
                code="invalid_utc_timestamp",
                message=f"{field} must be a parseable ISO-8601 UTC timestamp",
                expected="YYYY-MM-DDTHH:MM:SSZ",
                actual=value,
            )
        ]
    if parsed.tzinfo is None or parsed.utcoffset() != datetime.now(UTC).utcoffset():
        return [
            ValidationIssue(
                field=field,
                code="invalid_utc_timestamp",
                message=f"{field} must use UTC timezone",
                expected="UTC timestamp ending in Z",
                actual=value,
            )
        ]
    return []


def _require_existing_file(path: Path, *, field: str) -> None:
    if not path.exists() or not path.is_file():
        raise GovernanceValidationError(
            ValidationIssue(
                field=field,
                code=f"missing_{field}",
                message=f"{field} file is required for fail-closed pooled registration",
                expected="existing text JSONL file",
                actual=str(path),
            )
        )


def _require_writable_file(path: Path, *, field: str) -> None:
    try:
        mode = path.stat().st_mode
    except OSError as exc:
        raise GovernanceValidationError(
            ValidationIssue(
                field=field,
                code=f"unwritable_{field}",
                message=f"{field} permissions could not be inspected",
                expected="writable text JSONL file",
                actual=f"{path}: {exc}",
            )
        ) from exc
    if mode & 0o222 == 0:
        raise GovernanceValidationError(
            ValidationIssue(
                field=field,
                code=f"unwritable_{field}",
                message=f"{field} file must be writable before registration",
                expected="writable text JSONL file",
                actual=str(path),
            )
        )
    try:
        with path.open("a", encoding="utf-8"):
            pass
    except OSError as exc:
        raise GovernanceValidationError(
            ValidationIssue(
                field=field,
                code=f"unwritable_{field}",
                message=f"{field} file could not be opened for append",
                expected="writable text JSONL file",
                actual=f"{path}: {exc}",
            )
        ) from exc


def _diff_summary(
    prior: Mapping[str, Any],
    incoming: Mapping[str, Any],
    *,
    prefix: str = "$",
) -> str:
    differences: list[str] = []
    keys = sorted(set(prior) | set(incoming))
    for key in keys:
        left_missing = key not in prior
        right_missing = key not in incoming
        path = f"{prefix}.{key}"
        if left_missing or right_missing:
            differences.append(path)
            continue
        left = prior[key]
        right = incoming[key]
        if isinstance(left, Mapping) and isinstance(right, Mapping):
            nested = _diff_summary(left, right, prefix=path)
            if nested:
                differences.extend(nested.split(", "))
        elif left != right:
            differences.append(path)
    return ", ".join(differences[:12])


def _normalize_text(value: object) -> str:
    if isinstance(value, str):
        return " ".join(value.strip().lower().split())
    return str(value).strip().lower()


__all__ = [
    "METRICS_MARKER_TIMESTAMP_FIELDS",
    "POOLED_HYPOTHESIS_REQUIRED_FIELDS",
    "POOLED_REGISTRY_DEFAULT_PATH",
    "ComponentMetricRecord",
    "PoolKind",
    "PooledAggregationRule",
    "PooledHypothesisRecord",
    "PooledHypothesisRegistrationResult",
    "PooledHypothesisRegistry",
    "PooledMetricResult",
    "aggregate_pooled_metric",
    "ensure_registration_precedes_metrics",
    "generate_pooled_hypothesis_id",
    "resolve_pooled_hypothesis_registry_path",
    "track_b_minimum_satisfied",
    "validate_component_metric_record",
    "validate_pooled_hypothesis_record",
]
