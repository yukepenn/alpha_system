"""Context != trigger exploratory probes over materialized path labels."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from alpha_system.core.hashing import hash_config
from alpha_system.governance.ids import GovernanceIdKind, generate_governance_id
from alpha_system.governance.mechanism_card import EXPLORATORY_STAMP
from alpha_system.governance.serialization import JsonValue
from alpha_system.governance.setup_spec import SetupSpec, validate_setup_spec
from alpha_system.governance.study_spec import StudyBudgetStatus
from alpha_system.governance.surrogate_run import (
    CALIBRATION_BLOCKED,
    ZERO_PASS_MET,
    SurrogateGateStatus,
)
from alpha_system.governance.variant_ledger import (
    VariantLedgerRecord,
    VariantLedgerStatus,
    evaluate_family_budget,
    validate_variant_ledger_record,
)
from alpha_system.labels.spec import LabelSpec
from alpha_system.labels.validation import validate_label_record
from alpha_system.research.diagnostics import _optional_label_index
from alpha_system.research.events import (
    post_event_mfe_mae,
    target_before_stop_probability,
)
from alpha_system.research.study_config import StudyConfig
from alpha_system.runtime.diagnostics.power import (
    build_ic_power_statement,
    minimum_detectable_abs_ic,
)

SUPPORTED_PREDICATE_OPERATORS = frozenset({">", ">=", "<", "<=", "==", "!="})
SUPPORTED_VALUE_FIELDS = frozenset({"value", "normalized_value"})
PATH_LABEL_BINDING_KEYS = (
    "path_label",
    "path_label_id",
    "label_spec_id",
    "setup_path_label",
    "path_label_binding",
)


class ConditionalProbeError(ValueError):
    """Raised when an exploratory conditional probe cannot run safely."""


@dataclass(frozen=True, slots=True)
class ConditionalPredicate:
    """One factor predicate compiled from a `SetupSpec` mapping."""

    factor_id: str
    factor_version: str
    value_field: str
    operator: str
    threshold: float

    def evaluate(self, factor: Mapping[str, Any]) -> bool:
        """Evaluate this predicate against one factor-value mapping."""

        value = _factor_metric(factor, self.value_field)
        return _compare(value, self.operator, self.threshold)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return JSON-compatible predicate metadata."""

        return {
            "factor_id": self.factor_id,
            "factor_version": self.factor_version,
            "value_field": self.value_field,
            "operator": self.operator,
            "threshold": self.threshold,
        }


@dataclass(frozen=True, slots=True)
class ConditionalProbeSpec:
    """Compiled executable contract for one context != trigger probe."""

    setup_spec_id: str
    stamp: str
    path_label: str
    context: ConditionalPredicate
    trigger: ConditionalPredicate
    allowed_variants: tuple[str, ...]
    fixed_geometry: dict[str, JsonValue]

    def to_dict(self) -> dict[str, JsonValue]:
        """Return JSON-compatible probe metadata."""

        return {
            "setup_spec_id": self.setup_spec_id,
            "stamp": self.stamp,
            "path_label": self.path_label,
            "context": self.context.to_dict(),
            "trigger": self.trigger.to_dict(),
            "allowed_variants": list(self.allowed_variants),
            "fixed_geometry": dict(self.fixed_geometry),
        }


@dataclass(frozen=True, slots=True)
class ConditionalProbeObservationSet:
    """Aligned label-backed rows before and after context conditioning."""

    aligned_observations: tuple[dict[str, Any], ...]
    conditioned_observations: tuple[dict[str, Any], ...]
    missing_context_count: int
    missing_trigger_count: int

    def to_dict(self) -> dict[str, JsonValue]:
        """Return count-only alignment metadata."""

        return {
            "aligned_observation_count": len(self.aligned_observations),
            "conditioned_observation_count": len(self.conditioned_observations),
            "missing_context_count": self.missing_context_count,
            "missing_trigger_count": self.missing_trigger_count,
        }


@dataclass(frozen=True, slots=True)
class ConditionalProbeReadout:
    """EXPLORATORY readout for one bounded conditional probe."""

    readout_id: str
    setup_spec_id: str
    stamp: str
    path_label: str
    context_factor_id: str
    trigger_factor_id: str
    variant_id: str
    outcome_source: str
    fixed_geometry: dict[str, JsonValue]
    observation_counts: dict[str, JsonValue]
    diagnostics: dict[str, JsonValue]
    variant_ledger_binding: dict[str, JsonValue]
    surrogate_fdr_gate: dict[str, JsonValue]
    power: dict[str, JsonValue]
    promotion_eligible: bool = False

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a JSON-compatible readout."""

        return {
            "readout_id": self.readout_id,
            "setup_spec_id": self.setup_spec_id,
            "stamp": self.stamp,
            "path_label": self.path_label,
            "context_factor_id": self.context_factor_id,
            "trigger_factor_id": self.trigger_factor_id,
            "variant_id": self.variant_id,
            "outcome_source": self.outcome_source,
            "fixed_geometry": dict(self.fixed_geometry),
            "observation_counts": dict(self.observation_counts),
            "diagnostics": dict(self.diagnostics),
            "variant_ledger_binding": dict(self.variant_ledger_binding),
            "surrogate_fdr_gate": dict(self.surrogate_fdr_gate),
            "power": dict(self.power),
            "promotion_eligible": self.promotion_eligible,
        }


def compile_setup_spec_to_conditional_probe(
    setup_spec: SetupSpec | Mapping[str, Any],
) -> ConditionalProbeSpec:
    """Compile a validated `SetupSpec` into a context != trigger probe."""

    active_setup = _coerce_setup_spec(setup_spec)
    if active_setup.stamp != EXPLORATORY_STAMP:
        msg = "conditional probes only accept EXPLORATORY SetupSpec records"
        raise ConditionalProbeError(msg)

    context = _predicate_from_mapping(active_setup.entry_context, field="entry_context")
    trigger = _predicate_from_mapping(active_setup.event_trigger, field="event_trigger")
    if context.factor_id == trigger.factor_id:
        msg = "SetupSpec entry_context and event_trigger must use separate factors"
        raise ConditionalProbeError(msg)

    return ConditionalProbeSpec(
        setup_spec_id=active_setup.setup_spec_id,
        stamp=active_setup.stamp,
        path_label=active_setup.path_label,
        context=context,
        trigger=trigger,
        allowed_variants=tuple(active_setup.allowed_variants),
        fixed_geometry={
            "stop": dict(active_setup.stop),
            "target": dict(active_setup.target),
            "hold_time": dict(active_setup.hold_time),
            "horizon": active_setup.horizon,
        },
    )


def build_path_label_observation_set(
    probe: ConditionalProbeSpec,
    *,
    context_factor_values: Iterable[Mapping[str, Any]],
    trigger_factor_values: Iterable[Mapping[str, Any]],
    path_labels: Iterable[LabelSpec | Mapping[str, Any]],
    label_version: str | None = None,
    data_version: str | None = None,
) -> ConditionalProbeObservationSet:
    """Align separate factor rows with materialized path-label outcome fields."""

    labels = _bound_path_labels(path_labels, probe.path_label)
    active_label_version = _infer_label_version(labels, explicit=label_version)
    active_data_version = _infer_data_version(labels, explicit=data_version)
    config = StudyConfig(
        study_id=f"conditional_probe:{probe.setup_spec_id}",
        factor_id=probe.trigger.factor_id,
        factor_version=probe.trigger.factor_version,
        label_id=probe.path_label,
        label_version=active_label_version,
        data_version=active_data_version,
        factor_values_path="/tmp/conditional_probe_factor_values.jsonl",
        labels_path="/tmp/conditional_probe_labels.jsonl",
        diagnostic_types=("events",),
    )
    optional_index = _optional_label_index(labels, config)
    context_index = _factor_index(context_factor_values, probe.context)
    trigger_index = _factor_index(trigger_factor_values, probe.trigger)

    aligned: list[dict[str, Any]] = []
    conditioned: list[dict[str, Any]] = []
    missing_context_count = 0
    missing_trigger_count = 0
    for label_key, path_outcomes in sorted(
        optional_index.items(),
        key=lambda item: (
            item[0][0],
            item[0][1].isoformat(),
            item[0][2],
            item[0][3],
            item[0][4],
            item[0][5],
        ),
    ):
        (
            instrument_id,
            event_ts,
            session_id,
            horizon_seconds,
            row_data_version,
            row_label_version,
        ) = label_key
        factor_key = (instrument_id, event_ts, session_id, row_data_version)
        context_factor = context_index.get(factor_key)
        trigger_factor = trigger_index.get(factor_key)
        if context_factor is None:
            missing_context_count += 1
            continue
        if trigger_factor is None:
            missing_trigger_count += 1
            continue

        context_passed = probe.context.evaluate(context_factor)
        trigger_passed = probe.trigger.evaluate(trigger_factor)
        target_before_stop = path_outcomes.get("target_before_stop")
        row = {
            "instrument_id": instrument_id,
            "event_ts": event_ts,
            "session_id": session_id,
            "bar_index": int(trigger_factor["bar_index"]),
            "horizon_seconds": int(horizon_seconds),
            "data_version": row_data_version,
            "label_version": row_label_version,
            "path_label": probe.path_label,
            "context_factor_id": probe.context.factor_id,
            "context_factor_value": _factor_metric(
                context_factor,
                probe.context.value_field,
            ),
            "context_passed": context_passed,
            "regime_filter": context_passed,
            "trigger_factor_id": probe.trigger.factor_id,
            "trigger_factor_value": _factor_metric(
                trigger_factor,
                probe.trigger.value_field,
            ),
            "event_trigger": trigger_passed,
            "factor_value": _factor_metric(trigger_factor, probe.trigger.value_field),
            "label_value": _target_label_value(target_before_stop),
            "forward_return": _target_label_value(target_before_stop),
        }
        row.update(path_outcomes)
        aligned.append(row)
        if context_passed:
            conditioned.append(row)

    if not aligned:
        msg = "conditional probe found no aligned context/trigger/path-label rows"
        raise ConditionalProbeError(msg)
    if not conditioned:
        msg = "conditional probe context predicate selected no path-label rows"
        raise ConditionalProbeError(msg)
    return ConditionalProbeObservationSet(
        aligned_observations=tuple(aligned),
        conditioned_observations=tuple(conditioned),
        missing_context_count=missing_context_count,
        missing_trigger_count=missing_trigger_count,
    )


def evaluate_setup_conditional_probe(
    setup_spec: SetupSpec | Mapping[str, Any],
    *,
    context_factor_values: Iterable[Mapping[str, Any]],
    trigger_factor_values: Iterable[Mapping[str, Any]],
    path_labels: Iterable[LabelSpec | Mapping[str, Any]],
    family_id: str,
    family_budget: int,
    surrogate_run_count: int,
    variant_id: str | None = None,
    existing_variant_records: Iterable[VariantLedgerRecord | Mapping[str, Any]] = (),
    surrogate_gate_pass_count: int = 0,
    surrogate_error_count: int = 0,
    label_version: str | None = None,
    data_version: str | None = None,
    created_at: str | None = None,
) -> ConditionalProbeReadout:
    """Run one bounded EXPLORATORY context != trigger probe."""

    active_setup = _coerce_setup_spec(setup_spec)
    probe = compile_setup_spec_to_conditional_probe(active_setup)
    active_variant_id = _variant_id(variant_id, probe.allowed_variants)
    observation_set = build_path_label_observation_set(
        probe,
        context_factor_values=context_factor_values,
        trigger_factor_values=trigger_factor_values,
        path_labels=path_labels,
        label_version=label_version,
        data_version=data_version,
    )
    surrogate_gate = build_surrogate_zero_pass_gate(
        run_count=surrogate_run_count,
        gate_pass_count=surrogate_gate_pass_count,
        error_count=surrogate_error_count,
    )
    _require_zero_pass_surrogate_gate(surrogate_gate)
    variant_binding = bind_probe_variant_budget(
        setup_spec=active_setup,
        variant_id=active_variant_id,
        family_id=family_id,
        family_budget=family_budget,
        existing_variant_records=existing_variant_records,
        created_at=created_at,
    )
    if variant_binding["family_budget_check"]["status"] != StudyBudgetStatus.RESPECTED.value:
        msg = "conditional probe family budget is overrun"
        raise ConditionalProbeError(msg)

    conditioned = observation_set.conditioned_observations
    diagnostics: dict[str, JsonValue] = {
        "target_before_stop_probability": target_before_stop_probability(conditioned),
        "post_event_mfe_mae": post_event_mfe_mae(conditioned),
    }
    power = build_ic_power_statement(
        n_eff=len(conditioned),
        scope="per_factor",
        factor_id=probe.trigger.factor_id,
        factor_version=probe.trigger.factor_version,
    )
    power["minimum_detectable_abs_ic"] = minimum_detectable_abs_ic(len(conditioned))
    readout_payload = {
        "setup_spec_id": probe.setup_spec_id,
        "path_label": probe.path_label,
        "variant_id": active_variant_id,
        "diagnostics": diagnostics,
        "counts": observation_set.to_dict(),
        "variant_ledger_binding": variant_binding,
        "surrogate_fdr_gate": surrogate_gate,
        "power": power,
    }
    return ConditionalProbeReadout(
        readout_id=f"cprobe_{hash_config(readout_payload)[:24]}",
        setup_spec_id=probe.setup_spec_id,
        stamp=EXPLORATORY_STAMP,
        path_label=probe.path_label,
        context_factor_id=probe.context.factor_id,
        trigger_factor_id=probe.trigger.factor_id,
        variant_id=active_variant_id,
        outcome_source="materialized_path_labels",
        fixed_geometry=dict(probe.fixed_geometry),
        observation_counts=observation_set.to_dict(),
        diagnostics=diagnostics,
        variant_ledger_binding=variant_binding,
        surrogate_fdr_gate=surrogate_gate,
        power=power,
        promotion_eligible=False,
    )


def bind_probe_variant_budget(
    *,
    setup_spec: SetupSpec | Mapping[str, Any],
    variant_id: str,
    family_id: str,
    family_budget: int,
    existing_variant_records: Iterable[VariantLedgerRecord | Mapping[str, Any]] = (),
    created_at: str | None = None,
) -> dict[str, JsonValue]:
    """Create value-free VariantLedger/family-budget binding metadata."""

    active_setup = _coerce_setup_spec(setup_spec)
    current = build_probe_variant_ledger_record(
        active_setup,
        variant_id=variant_id,
        family_id=family_id,
        created_at=created_at,
    )
    existing = tuple(_coerce_variant_record(record) for record in existing_variant_records)
    family_check = evaluate_family_budget(
        family_id=family_id,
        family_budget=family_budget,
        records=existing + (current,),
    )
    return {
        "variant_record": current.to_dict(),
        "family_budget_check": family_check.to_dict(),
        "existing_record_count": len(existing),
    }


def build_probe_variant_ledger_record(
    setup_spec: SetupSpec | Mapping[str, Any],
    *,
    variant_id: str,
    family_id: str,
    created_at: str | None = None,
) -> VariantLedgerRecord:
    """Build a valid VariantLedgerRecord for an exploratory probe readout."""

    active_setup = _coerce_setup_spec(setup_spec)
    active_variant_id = _variant_id(variant_id, tuple(active_setup.allowed_variants))
    active_created_at = created_at or _utc_now_seconds()
    alpha_spec_id = generate_governance_id(
        GovernanceIdKind.ALPHA_SPEC,
        {
            "exploratory_setup_spec_id": active_setup.setup_spec_id,
            "stamp": active_setup.stamp,
        },
    )
    study_spec_id = generate_governance_id(
        GovernanceIdKind.STUDY_SPEC,
        {
            "exploratory_setup_spec_id": active_setup.setup_spec_id,
            "path_label": active_setup.path_label,
            "variant_id": active_variant_id,
        },
    )
    trial_id = generate_governance_id(
        GovernanceIdKind.TRIAL_LEDGER_RECORD,
        {
            "exploratory_setup_spec_id": active_setup.setup_spec_id,
            "path_label": active_setup.path_label,
            "variant_id": active_variant_id,
        },
    )
    return validate_variant_ledger_record(
        {
            "variant_id": active_variant_id,
            "alpha_spec_id": alpha_spec_id,
            "study_spec_id": study_spec_id,
            "family_id": family_id,
            "attempt_count": 1,
            "trial_ids": [trial_id],
            "status": VariantLedgerStatus.COMPLETED.value,
            "created_at": active_created_at,
        }
    )


def build_surrogate_zero_pass_gate(
    *,
    run_count: int,
    gate_pass_count: int,
    error_count: int,
) -> dict[str, JsonValue]:
    """Return the surrogate-FDR zero-pass gate attached to a readout."""

    active_run_count = _non_negative_int(run_count, "run_count")
    active_gate_pass_count = _non_negative_int(gate_pass_count, "gate_pass_count")
    active_error_count = _non_negative_int(error_count, "error_count")
    passed = (
        active_run_count > 0
        and active_gate_pass_count == 0
        and active_error_count == 0
    )
    return {
        "gate_status": (
            SurrogateGateStatus.PASSED.value
            if passed
            else SurrogateGateStatus.BLOCKED.value
        ),
        "threshold_verdict": ZERO_PASS_MET if passed else CALIBRATION_BLOCKED,
        "run_count": active_run_count,
        "gate_pass_count": active_gate_pass_count,
        "error_count": active_error_count,
        "promotion_evidence": False,
    }


def _coerce_setup_spec(value: SetupSpec | Mapping[str, Any]) -> SetupSpec:
    if isinstance(value, SetupSpec):
        return validate_setup_spec(value.to_dict())
    return validate_setup_spec(value)


def _predicate_from_mapping(
    payload: Mapping[str, Any],
    *,
    field: str,
) -> ConditionalPredicate:
    factor_id = _text(payload.get("factor_id"), f"{field}.factor_id")
    factor_version = _text(payload.get("factor_version"), f"{field}.factor_version")
    value_field = _text(payload.get("value_field", "normalized_value"), f"{field}.value_field")
    if value_field not in SUPPORTED_VALUE_FIELDS:
        msg = f"{field}.value_field must be one of: {', '.join(sorted(SUPPORTED_VALUE_FIELDS))}"
        raise ConditionalProbeError(msg)
    operator = _text(payload.get("operator"), f"{field}.operator")
    if operator not in SUPPORTED_PREDICATE_OPERATORS:
        msg = (
            f"{field}.operator must be one of: "
            f"{', '.join(sorted(SUPPORTED_PREDICATE_OPERATORS))}"
        )
        raise ConditionalProbeError(msg)
    return ConditionalPredicate(
        factor_id=factor_id,
        factor_version=factor_version,
        value_field=value_field,
        operator=operator,
        threshold=_numeric(payload.get("threshold"), f"{field}.threshold"),
    )


def _bound_path_labels(
    labels: Iterable[LabelSpec | Mapping[str, Any]],
    path_label: str,
) -> tuple[LabelSpec, ...]:
    normalized = tuple(validate_label_record(label) for label in labels)
    bound = tuple(label for label in normalized if _label_bound_to_path(label, path_label))
    if not bound:
        msg = "conditional probe found no materialized labels bound to SetupSpec.path_label"
        raise ConditionalProbeError(msg)
    return bound


def _label_bound_to_path(label: LabelSpec, path_label: str) -> bool:
    if label.label_id == path_label:
        return True
    metadata = dict(label.path_metadata)
    return any(str(metadata.get(key, "")) == path_label for key in PATH_LABEL_BINDING_KEYS)


def _infer_label_version(labels: tuple[LabelSpec, ...], *, explicit: str | None) -> str:
    if explicit is not None:
        return _text(explicit, "label_version")
    versions = {str(label.path_metadata.get("label_version", "")) for label in labels}
    versions.discard("")
    if len(versions) != 1:
        msg = "conditional probe labels must have exactly one label_version"
        raise ConditionalProbeError(msg)
    return next(iter(versions))


def _infer_data_version(labels: tuple[LabelSpec, ...], *, explicit: str | None) -> str:
    if explicit is not None:
        return _text(explicit, "data_version")
    versions = {label.data_version for label in labels}
    if len(versions) != 1:
        msg = "conditional probe labels must have exactly one data_version"
        raise ConditionalProbeError(msg)
    return next(iter(versions))


def _factor_index(
    factor_values: Iterable[Mapping[str, Any]],
    predicate: ConditionalPredicate,
) -> dict[tuple[str, datetime, str, str], Mapping[str, Any]]:
    output: dict[tuple[str, datetime, str, str], Mapping[str, Any]] = {}
    for factor in factor_values:
        if str(factor.get("factor_id", "")) != predicate.factor_id:
            continue
        if str(factor.get("factor_version", "")) != predicate.factor_version:
            continue
        key = (
            _text(factor.get("instrument_id"), "factor.instrument_id"),
            _datetime_value(factor.get("event_ts"), "factor.event_ts"),
            _text(factor.get("session_id"), "factor.session_id"),
            _text(factor.get("data_version"), "factor.data_version"),
        )
        if key in output:
            msg = f"duplicate factor row for conditional probe key: {key}"
            raise ConditionalProbeError(msg)
        output[key] = factor
    if not output:
        msg = f"no factor rows found for {predicate.factor_id}@{predicate.factor_version}"
        raise ConditionalProbeError(msg)
    return output


def _factor_metric(factor: Mapping[str, Any], value_field: str) -> float:
    if value_field not in SUPPORTED_VALUE_FIELDS:
        msg = "factor predicate value_field must be value or normalized_value"
        raise ConditionalProbeError(msg)
    metric = factor.get(value_field)
    if metric is None and value_field == "normalized_value":
        metric = factor.get("value")
    return _numeric(metric, f"factor.{value_field}")


def _target_label_value(value: object) -> float | None:
    if value is None:
        return None
    return 1.0 if bool(value) else 0.0


def _compare(left: float, operator: str, right: float) -> bool:
    if operator == ">":
        return left > right
    if operator == ">=":
        return left >= right
    if operator == "<":
        return left < right
    if operator == "<=":
        return left <= right
    if operator == "==":
        return left == right
    if operator == "!=":
        return left != right
    msg = f"unsupported predicate operator: {operator}"
    raise ConditionalProbeError(msg)


def _variant_id(value: str | None, allowed_variants: tuple[str, ...]) -> str:
    if not allowed_variants:
        msg = "SetupSpec.allowed_variants must contain at least one variant"
        raise ConditionalProbeError(msg)
    active = allowed_variants[0] if value is None else _text(value, "variant_id")
    if active not in allowed_variants:
        msg = "variant_id must be listed in SetupSpec.allowed_variants"
        raise ConditionalProbeError(msg)
    return active


def _coerce_variant_record(
    value: VariantLedgerRecord | Mapping[str, Any],
) -> VariantLedgerRecord:
    if isinstance(value, VariantLedgerRecord):
        return validate_variant_ledger_record(value.to_dict())
    return validate_variant_ledger_record(value)


def _require_zero_pass_surrogate_gate(gate: Mapping[str, Any]) -> None:
    if gate.get("threshold_verdict") != ZERO_PASS_MET:
        msg = "conditional probe readout requires surrogate-FDR ZERO_PASS_MET"
        raise ConditionalProbeError(msg)


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        msg = f"{field} must be non-empty text"
        raise ConditionalProbeError(msg)
    return value.strip()


def _numeric(value: object, field: str) -> float:
    if isinstance(value, bool) or value is None:
        msg = f"{field} must be numeric"
        raise ConditionalProbeError(msg)
    if isinstance(value, int | float):
        return float(value)
    msg = f"{field} must be numeric"
    raise ConditionalProbeError(msg)


def _non_negative_int(value: object, field: str) -> int:
    if isinstance(value, bool):
        msg = f"{field} must be a non-negative integer"
        raise ConditionalProbeError(msg)
    try:
        number = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        msg = f"{field} must be a non-negative integer"
        raise ConditionalProbeError(msg) from exc
    if number < 0:
        msg = f"{field} must be a non-negative integer"
        raise ConditionalProbeError(msg)
    return number


def _datetime_value(value: object, field: str) -> datetime:
    if isinstance(value, datetime):
        active = value
    elif isinstance(value, str):
        try:
            active = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            msg = f"{field} must be ISO-8601 datetime text"
            raise ConditionalProbeError(msg) from exc
    else:
        msg = f"{field} must be datetime or ISO-8601 text"
        raise ConditionalProbeError(msg)
    if active.tzinfo is None or active.utcoffset() is None:
        msg = f"{field} must be timezone-aware"
        raise ConditionalProbeError(msg)
    return active.astimezone(UTC)


def _utc_now_seconds() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


__all__ = [
    "ConditionalPredicate",
    "ConditionalProbeError",
    "ConditionalProbeObservationSet",
    "ConditionalProbeReadout",
    "ConditionalProbeSpec",
    "bind_probe_variant_budget",
    "build_path_label_observation_set",
    "build_probe_variant_ledger_record",
    "build_surrogate_zero_pass_gate",
    "compile_setup_spec_to_conditional_probe",
    "evaluate_setup_conditional_probe",
]
