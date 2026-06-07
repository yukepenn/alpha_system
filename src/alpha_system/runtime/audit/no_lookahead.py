"""Central no-lookahead audit for resolved research-runtime objects.

The audit inspects value-free runtime handles and scalar probe metadata. It does
not resolve data, read provider artifacts, calculate diagnostics, or retry a
failing run.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from alpha_system.runtime.entry_contract import RuntimeEntryReason, RuntimeEntryStatus
from alpha_system.runtime.input_resolver import (
    LOCKED_PARTITION_IDS,
    SESSION_METADATA_FIELDS,
    FieldRole,
    RuntimeInputPack,
    _is_exempt_session_field,
    _is_forbidden_future_field,
)
from alpha_system.runtime.probe.report import SignalProbeReport
from alpha_system.runtime.probe.spec import SignalProbeSpec

NO_LOOKAHEAD_AUDIT_SCHEMA = "alpha_system.runtime.audit.no_lookahead.v1"

LABEL_AS_FEATURE_TOKENS: frozenset[str] = frozenset(
    {
        "forward_return",
        "horizon_end_ts",
        "label",
        "label_available_ts",
        "label_outcome",
        "label_value",
        "target",
        "y_true",
    }
)
WINDOW_METADATA_KEYS: frozenset[str] = frozenset(
    {
        "feature_window",
        "live_window",
        "window",
        "window_metadata",
        "window_spec",
    }
)


class NoLookaheadRejectionCategory(StrEnum):
    """Rejection taxonomy categories emitted by the audit."""

    LEAKAGE_RISK = "leakage_risk"
    BLOCKED_BY_POLICY = "blocked_by_policy"


class NoLookaheadAuditOutcome(StrEnum):
    """Audit outcomes. Accepted only means point-in-time integrity was checked."""

    POINT_IN_TIME_SAFE = "POINT_IN_TIME_SAFE"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class NoLookaheadAuditReason:
    """Structured no-lookahead rejection reason."""

    code: str
    category: NoLookaheadRejectionCategory | str
    message: str
    field: str
    expected: str
    actual: str
    decision_state: RuntimeEntryStatus | str = RuntimeEntryStatus.INPUTS_BLOCKED

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", _required_text(self.code, "code"))
        object.__setattr__(
            self,
            "category",
            (
                self.category
                if isinstance(self.category, NoLookaheadRejectionCategory)
                else NoLookaheadRejectionCategory(str(self.category))
            ),
        )
        object.__setattr__(self, "message", _required_text(self.message, "message"))
        object.__setattr__(self, "field", _required_text(self.field, "field"))
        object.__setattr__(self, "expected", _required_text(self.expected, "expected"))
        object.__setattr__(self, "actual", _required_text(self.actual, "actual"))
        object.__setattr__(
            self,
            "decision_state",
            (
                self.decision_state
                if isinstance(self.decision_state, RuntimeEntryStatus)
                else RuntimeEntryStatus(str(self.decision_state))
            ),
        )

    def to_runtime_entry_reason(self) -> RuntimeEntryReason:
        """Return the current runtime-compatible reason shape."""

        return RuntimeEntryReason(
            code=self.code,
            message=self.message,
            field=self.field,
            decision_state=self.decision_state,
            expected=self.expected,
            actual=self.actual,
        )

    def to_dict(self) -> dict[str, str]:
        """Return a stable rejection-reason payload."""

        return {
            "code": self.code,
            "category": self.category.value,
            "message": self.message,
            "field": self.field,
            "decision_state": self.decision_state.value,
            "expected": self.expected,
            "actual": self.actual,
        }


@dataclass(frozen=True, slots=True)
class NoLookaheadAuditResult:
    """Visible outcome of the no-lookahead audit."""

    outcome: NoLookaheadAuditOutcome | str
    reasons: tuple[NoLookaheadAuditReason, ...] = ()

    def __post_init__(self) -> None:
        outcome = (
            self.outcome
            if isinstance(self.outcome, NoLookaheadAuditOutcome)
            else NoLookaheadAuditOutcome(str(self.outcome))
        )
        object.__setattr__(self, "outcome", outcome)
        object.__setattr__(self, "reasons", tuple(self.reasons))
        if outcome is NoLookaheadAuditOutcome.REJECTED and not self.reasons:
            raise ValueError("rejected no-lookahead audit results require visible reasons")
        if outcome is NoLookaheadAuditOutcome.POINT_IN_TIME_SAFE and self.reasons:
            raise ValueError("accepted no-lookahead audit results must not carry reasons")

    @property
    def accepted(self) -> bool:
        """Return true when the audit found no leakage-policy violation."""

        return self.outcome is NoLookaheadAuditOutcome.POINT_IN_TIME_SAFE

    @property
    def rejected(self) -> bool:
        """Return true when at least one fail-closed reason was emitted."""

        return self.outcome is NoLookaheadAuditOutcome.REJECTED

    @property
    def rejection_reason(self) -> NoLookaheadAuditReason | None:
        """Return the first visible reason for downstream summary use."""

        return self.reasons[0] if self.reasons else None

    @property
    def runtime_entry_reasons(self) -> tuple[RuntimeEntryReason, ...]:
        """Return reasons in the existing RuntimeEntryReason-compatible shape."""

        return tuple(reason.to_runtime_entry_reason() for reason in self.reasons)

    def to_dict(self) -> dict[str, object]:
        """Return a stable, recordable audit result."""

        return {
            "schema": NO_LOOKAHEAD_AUDIT_SCHEMA,
            "outcome": self.outcome.value,
            "accepted": self.accepted,
            "rejection_reason_records": [reason.to_dict() for reason in self.reasons],
            "integrity_only": True,
            "not_alpha_validation": True,
            "not_strategy_validation": True,
            "not_a_candidate": True,
            "raw_or_heavy_data_embedded": False,
        }


class NoLookaheadRuntimeAudit:
    """Fail-closed point-in-time audit over resolved runtime metadata."""

    def evaluate(
        self,
        *,
        runtime_input_pack: RuntimeInputPack | Mapping[str, Any] | object,
        decision_ts: object,
        signal_probe_spec: SignalProbeSpec | Mapping[str, Any] | object | None = None,
        signal_probe_report: SignalProbeReport | Mapping[str, Any] | object | None = None,
        feature_inputs: Sequence[Mapping[str, Any] | object] = (),
        label_inputs: Sequence[Mapping[str, Any] | object] = (),
        live_feature_windows: Sequence[Mapping[str, Any] | object] = (),
        probe_fill_records: Sequence[Mapping[str, Any] | object] = (),
        partition_scope: Mapping[str, Any] | object | None = None,
        partition_purpose: str | None = None,
        governance_metadata: Mapping[str, Any] | object | None = None,
    ) -> NoLookaheadAuditResult:
        """Inspect resolved runtime inputs and return a visible audit result."""

        reasons: list[NoLookaheadAuditReason] = []
        decision = _parse_ts(decision_ts)
        if decision is None:
            reasons.append(
                _reason(
                    code="decision_ts_missing_or_invalid",
                    category=NoLookaheadRejectionCategory.LEAKAGE_RISK,
                    message="feature availability cannot be audited without a decision timestamp",
                    field="decision_ts",
                    expected="timezone-aware decision timestamp",
                    actual=_actual(decision_ts),
                )
            )

        if not _is_runtime_input_pack_like(runtime_input_pack):
            reasons.append(
                _reason(
                    code="runtime_input_pack_missing",
                    category=NoLookaheadRejectionCategory.BLOCKED_BY_POLICY,
                    message="NoLookaheadRuntimeAudit requires a resolved RuntimeInputPack",
                    field="runtime_input_pack",
                    expected="RuntimeInputPack-like resolved metadata",
                    actual=type(runtime_input_pack).__name__,
                )
            )

        reasons.extend(_feature_availability_reasons(runtime_input_pack, decision))
        reasons.extend(_feature_availability_reasons_for_inputs(feature_inputs, decision))
        reasons.extend(_label_availability_reasons(runtime_input_pack))
        reasons.extend(_label_availability_reasons_for_inputs(label_inputs))
        reasons.extend(
            _label_as_feature_reasons(
                runtime_input_pack=runtime_input_pack,
                signal_probe_spec=signal_probe_spec,
                feature_inputs=feature_inputs,
            )
        )
        reasons.extend(
            _live_window_reasons(
                feature_inputs=feature_inputs,
                live_feature_windows=live_feature_windows,
            )
        )
        reasons.extend(
            _same_bar_fill_reasons(
                signal_probe_spec=signal_probe_spec,
                signal_probe_report=signal_probe_report,
                probe_fill_records=probe_fill_records,
            )
        )
        reasons.extend(
            _locked_partition_reasons(
                runtime_input_pack=runtime_input_pack,
                signal_probe_spec=signal_probe_spec,
                partition_scope=partition_scope,
                partition_purpose=partition_purpose,
                governance_metadata=governance_metadata,
            )
        )

        unique_reasons = _dedupe_reasons(reasons)
        if unique_reasons:
            return NoLookaheadAuditResult(
                outcome=NoLookaheadAuditOutcome.REJECTED,
                reasons=unique_reasons,
            )
        return NoLookaheadAuditResult(outcome=NoLookaheadAuditOutcome.POINT_IN_TIME_SAFE)


def _feature_availability_reasons(
    runtime_input_pack: RuntimeInputPack | Mapping[str, Any] | object,
    decision_ts: datetime | None,
) -> list[NoLookaheadAuditReason]:
    reasons: list[NoLookaheadAuditReason] = []
    for index, feature in enumerate(_sequence_value(runtime_input_pack, "feature_packs")):
        reasons.extend(
            _availability_pair_reasons(
                source=feature,
                prefix=f"runtime_input_pack.feature_packs[{index}]",
                available_names=("first_available_ts", "available_ts"),
                event_names=("first_event_ts", "event_ts"),
                decision_ts=decision_ts,
                missing_code="feature_available_ts_missing",
                invalid_code="feature_available_ts_invalid",
                event_missing_code="feature_event_ts_missing",
                before_event_code="feature_available_ts_precedes_event_ts",
                after_decision_code="feature_available_ts_after_decision_ts",
                label=False,
            )
        )
        reasons.extend(
            _availability_pair_reasons(
                source=feature,
                prefix=f"runtime_input_pack.feature_packs[{index}]",
                available_names=("last_available_ts", "available_ts"),
                event_names=("last_event_ts", "event_ts"),
                decision_ts=decision_ts,
                missing_code="feature_available_ts_missing",
                invalid_code="feature_available_ts_invalid",
                event_missing_code="feature_event_ts_missing",
                before_event_code="feature_available_ts_precedes_event_ts",
                after_decision_code="feature_available_ts_after_decision_ts",
                label=False,
                suffix="last",
            )
        )
    return reasons


def _feature_availability_reasons_for_inputs(
    feature_inputs: Sequence[Mapping[str, Any] | object],
    decision_ts: datetime | None,
) -> list[NoLookaheadAuditReason]:
    reasons: list[NoLookaheadAuditReason] = []
    for index, feature in enumerate(feature_inputs):
        reasons.extend(
            _availability_pair_reasons(
                source=feature,
                prefix=f"feature_inputs[{index}]",
                available_names=("available_ts", "first_available_ts"),
                event_names=("event_ts", "first_event_ts"),
                decision_ts=_parse_ts(_value(feature, "decision_ts")) or decision_ts,
                missing_code="feature_available_ts_missing",
                invalid_code="feature_available_ts_invalid",
                event_missing_code="feature_event_ts_missing",
                before_event_code="feature_available_ts_precedes_event_ts",
                after_decision_code="feature_available_ts_after_decision_ts",
                label=False,
            )
        )
    return reasons


def _label_availability_reasons(
    runtime_input_pack: RuntimeInputPack | Mapping[str, Any] | object,
) -> list[NoLookaheadAuditReason]:
    reasons: list[NoLookaheadAuditReason] = []
    for index, label in enumerate(_sequence_value(runtime_input_pack, "label_packs")):
        reasons.extend(
            _availability_pair_reasons(
                source=label,
                prefix=f"runtime_input_pack.label_packs[{index}]",
                available_names=("first_label_available_ts", "label_available_ts"),
                event_names=("first_event_ts", "event_ts"),
                decision_ts=None,
                missing_code="label_available_ts_missing",
                invalid_code="label_available_ts_invalid",
                event_missing_code="label_event_ts_missing",
                before_event_code="label_available_ts_precedes_event_ts",
                after_decision_code="",
                label=True,
            )
        )
        reasons.extend(
            _availability_pair_reasons(
                source=label,
                prefix=f"runtime_input_pack.label_packs[{index}]",
                available_names=("last_label_available_ts", "label_available_ts"),
                event_names=("last_event_ts", "event_ts"),
                decision_ts=None,
                missing_code="label_available_ts_missing",
                invalid_code="label_available_ts_invalid",
                event_missing_code="label_event_ts_missing",
                before_event_code="label_available_ts_precedes_event_ts",
                after_decision_code="",
                label=True,
                suffix="last",
            )
        )
    return reasons


def _label_availability_reasons_for_inputs(
    label_inputs: Sequence[Mapping[str, Any] | object],
) -> list[NoLookaheadAuditReason]:
    reasons: list[NoLookaheadAuditReason] = []
    for index, label in enumerate(label_inputs):
        reasons.extend(
            _availability_pair_reasons(
                source=label,
                prefix=f"label_inputs[{index}]",
                available_names=("label_available_ts", "first_label_available_ts"),
                event_names=("event_ts", "first_event_ts"),
                decision_ts=None,
                missing_code="label_available_ts_missing",
                invalid_code="label_available_ts_invalid",
                event_missing_code="label_event_ts_missing",
                before_event_code="label_available_ts_precedes_event_ts",
                after_decision_code="",
                label=True,
            )
        )
    return reasons


def _availability_pair_reasons(
    *,
    source: Mapping[str, Any] | object,
    prefix: str,
    available_names: tuple[str, ...],
    event_names: tuple[str, ...],
    decision_ts: datetime | None,
    missing_code: str,
    invalid_code: str,
    event_missing_code: str,
    before_event_code: str,
    after_decision_code: str,
    label: bool,
    suffix: str = "first",
) -> list[NoLookaheadAuditReason]:
    reasons: list[NoLookaheadAuditReason] = []
    available_value = _first_value(source, *available_names, suffix=suffix)
    event_value = _first_value(source, *event_names, suffix=suffix)
    field = f"{prefix}.{available_names[0]}"

    if _is_missing(available_value):
        reasons.append(
            _reason(
                code=missing_code,
                category=NoLookaheadRejectionCategory.LEAKAGE_RISK,
                message=(
                    "label input lacks required label_available_ts"
                    if label
                    else "feature input lacks required available_ts"
                ),
                field=field,
                expected=available_names[0],
                actual="missing",
            )
        )
        return reasons

    available_ts = _parse_ts(available_value)
    if available_ts is None:
        reasons.append(
            _reason(
                code=invalid_code,
                category=NoLookaheadRejectionCategory.LEAKAGE_RISK,
                message=f"{available_names[0]} must be a timezone-aware timestamp",
                field=field,
                expected="timezone-aware timestamp",
                actual=_actual(available_value),
            )
        )
        return reasons

    if _is_missing(event_value):
        reasons.append(
            _reason(
                code=event_missing_code,
                category=NoLookaheadRejectionCategory.LEAKAGE_RISK,
                message="availability ordering requires event_ts metadata",
                field=f"{prefix}.{event_names[0]}",
                expected=event_names[0],
                actual="missing",
            )
        )
        return reasons

    event_ts = _parse_ts(event_value)
    if event_ts is None:
        reasons.append(
            _reason(
                code=f"{event_missing_code}_invalid",
                category=NoLookaheadRejectionCategory.LEAKAGE_RISK,
                message="event_ts must be a timezone-aware timestamp",
                field=f"{prefix}.{event_names[0]}",
                expected="timezone-aware timestamp",
                actual=_actual(event_value),
            )
        )
        return reasons

    if available_ts < event_ts:
        reasons.append(
            _reason(
                code=before_event_code,
                category=NoLookaheadRejectionCategory.LEAKAGE_RISK,
                message=(
                    "label_available_ts must not precede label event_ts"
                    if label
                    else "available_ts must not precede feature event_ts"
                ),
                field=field,
                expected=f">= {event_ts.isoformat()}",
                actual=available_ts.isoformat(),
            )
        )

    horizon_end = _parse_ts(_value(source, "horizon_end_ts"))
    if label and horizon_end is not None and available_ts < horizon_end:
        reasons.append(
            _reason(
                code="label_available_ts_precedes_horizon_end_ts",
                category=NoLookaheadRejectionCategory.LEAKAGE_RISK,
                message="label_available_ts must not precede the forward horizon end",
                field=field,
                expected=f">= {horizon_end.isoformat()}",
                actual=available_ts.isoformat(),
            )
        )

    if not label and decision_ts is not None and after_decision_code and available_ts > decision_ts:
        reasons.append(
            _reason(
                code=after_decision_code,
                category=NoLookaheadRejectionCategory.LEAKAGE_RISK,
                message="feature available_ts is later than the decision timestamp",
                field=field,
                expected=f"<= {decision_ts.isoformat()}",
                actual=available_ts.isoformat(),
            )
        )
    return reasons


def _label_as_feature_reasons(
    *,
    runtime_input_pack: RuntimeInputPack | Mapping[str, Any] | object,
    signal_probe_spec: SignalProbeSpec | Mapping[str, Any] | object | None,
    feature_inputs: Sequence[Mapping[str, Any] | object],
) -> list[NoLookaheadAuditReason]:
    reasons: list[NoLookaheadAuditReason] = []
    feature_ref = (
        _value(signal_probe_spec, "feature_ref") if signal_probe_spec is not None else None
    )
    signal_name = _value(feature_ref, "signal_name")
    if _contains_label_token(signal_name):
        reasons.append(
            _reason(
                code="label_as_feature_input",
                category=NoLookaheadRejectionCategory.LEAKAGE_RISK,
                message="probe feature_ref must not expose a label value as a live signal",
                field="signal_probe_spec.feature_ref.signal_name",
                expected="live feature or signal input",
                actual=str(signal_name),
            )
        )

    study_input_pack = _value(runtime_input_pack, "study_input_pack")
    for index, feature_ref_value in enumerate(
        _sequence_value(study_input_pack, "feature_request_ids")
    ):
        if _contains_label_token(feature_ref_value) or str(feature_ref_value).startswith(
            ("lver_", "lspec_")
        ):
            reasons.append(
                _reason(
                    code="label_as_feature_input",
                    category=NoLookaheadRejectionCategory.LEAKAGE_RISK,
                    message="StudyInputPack feature requests must not reference label handles",
                    field=f"runtime_input_pack.study_input_pack.feature_request_ids[{index}]",
                    expected="feature request id",
                    actual=str(feature_ref_value),
                )
            )

    for index, feature in enumerate(feature_inputs):
        marker = _feature_label_marker(feature)
        if marker is not None:
            reasons.append(
                _reason(
                    code="label_as_feature_input",
                    category=NoLookaheadRejectionCategory.LEAKAGE_RISK,
                    message="live feature input exposes a label-valued field or view",
                    field=f"feature_inputs[{index}]",
                    expected="feature-only live input fields",
                    actual=marker,
                )
            )
    return reasons


def _live_window_reasons(
    *,
    feature_inputs: Sequence[Mapping[str, Any] | object],
    live_feature_windows: Sequence[Mapping[str, Any] | object],
) -> list[NoLookaheadAuditReason]:
    reasons: list[NoLookaheadAuditReason] = []
    windows: list[tuple[str, Mapping[str, Any] | object]] = [
        (f"live_feature_windows[{index}]", window)
        for index, window in enumerate(live_feature_windows)
    ]
    for index, feature in enumerate(feature_inputs):
        for key in WINDOW_METADATA_KEYS:
            nested = _value(feature, key)
            if not _is_missing(nested):
                windows.append((f"feature_inputs[{index}].{key}", nested))

    for field, window in windows:
        if _is_label_window(window):
            continue
        if _is_centered_window(window):
            reasons.append(
                _reason(
                    code="live_feature_centered_window",
                    category=NoLookaheadRejectionCategory.LEAKAGE_RISK,
                    message="centered windows are forbidden for live feature inputs",
                    field=field,
                    expected="causal trailing live-feature window",
                    actual=_window_actual(window),
                )
            )
        if _is_future_window(window):
            reasons.append(
                _reason(
                    code="live_feature_future_window",
                    category=NoLookaheadRejectionCategory.LEAKAGE_RISK,
                    message="forward-looking windows are forbidden for live feature inputs",
                    field=field,
                    expected="causal trailing live-feature window",
                    actual=_window_actual(window),
                )
            )
    return reasons


def _same_bar_fill_reasons(
    *,
    signal_probe_spec: SignalProbeSpec | Mapping[str, Any] | object | None,
    signal_probe_report: SignalProbeReport | Mapping[str, Any] | object | None,
    probe_fill_records: Sequence[Mapping[str, Any] | object],
) -> list[NoLookaheadAuditReason]:
    reasons: list[NoLookaheadAuditReason] = []
    if signal_probe_spec is not None:
        fill_policy = _value(signal_probe_spec, "fill_policy")
        if _is_missing(fill_policy):
            reasons.append(
                _reason(
                    code="probe_fill_policy_missing",
                    category=NoLookaheadRejectionCategory.LEAKAGE_RISK,
                    message="signal probe no-lookahead audit requires fill policy metadata",
                    field="signal_probe_spec.fill_policy",
                    expected="fill policy with delay_bars >= 1 and same-bar disabled",
                    actual="missing",
                )
            )
        else:
            delay = _int_value(_value(fill_policy, "delay_bars"))
            allow_same_bar = _value(fill_policy, "allow_same_bar_fill")
            if delay is None or delay < 1 or allow_same_bar is not False:
                reasons.append(
                    _reason(
                        code="same_bar_fill_policy_allowed",
                        category=NoLookaheadRejectionCategory.LEAKAGE_RISK,
                        message="signal probe fill policy permits same-bar optimistic fills",
                        field="signal_probe_spec.fill_policy",
                        expected="delay_bars >= 1 and allow_same_bar_fill == False",
                        actual=_actual_fill_policy(fill_policy),
                    )
                )

    if signal_probe_report is not None:
        count = _same_bar_count(signal_probe_report)
        if count is None:
            reasons.append(
                _reason(
                    code="probe_same_bar_fill_metadata_missing",
                    category=NoLookaheadRejectionCategory.LEAKAGE_RISK,
                    message="signal probe report must expose same-bar fill count metadata",
                    field="signal_probe_report.position_summary.same_bar_fill_count",
                    expected="same_bar_fill_count == 0",
                    actual="missing",
                )
            )
        elif count > 0:
            reasons.append(
                _reason(
                    code="same_bar_optimistic_fill",
                    category=NoLookaheadRejectionCategory.LEAKAGE_RISK,
                    message="signal probe report contains same-bar optimistic fills",
                    field="signal_probe_report.position_summary.same_bar_fill_count",
                    expected="0",
                    actual=str(count),
                )
            )
        metadata = _value(signal_probe_report, "report_metadata")
        if (
            isinstance(metadata, Mapping)
            and metadata.get("same_bar_optimistic_fill_forbidden") is False
        ):
            reasons.append(
                _reason(
                    code="same_bar_optimistic_fill",
                    category=NoLookaheadRejectionCategory.LEAKAGE_RISK,
                    message="signal probe report metadata does not forbid same-bar fills",
                    field="signal_probe_report.report_metadata.same_bar_optimistic_fill_forbidden",
                    expected="True",
                    actual="False",
                )
            )

    for index, fill in enumerate(probe_fill_records):
        same_bar = _value(fill, "same_bar_fill")
        fill_index = _int_value(_value(fill, "fill_index"))
        origin_index = _int_value(_value(fill, "origin_signal_index"))
        if same_bar is True or (
            fill_index is not None
            and origin_index is not None
            and origin_index >= 0
            and fill_index <= origin_index
        ):
            reasons.append(
                _reason(
                    code="same_bar_optimistic_fill",
                    category=NoLookaheadRejectionCategory.LEAKAGE_RISK,
                    message="probe fill record executes on the same bar or before its signal",
                    field=f"probe_fill_records[{index}]",
                    expected="fill_index > origin_signal_index",
                    actual=f"fill_index={fill_index}, origin_signal_index={origin_index}",
                )
            )
    return reasons


def _locked_partition_reasons(
    *,
    runtime_input_pack: RuntimeInputPack | Mapping[str, Any] | object,
    signal_probe_spec: SignalProbeSpec | Mapping[str, Any] | object | None,
    partition_scope: Mapping[str, Any] | object | None,
    partition_purpose: str | None,
    governance_metadata: Mapping[str, Any] | object | None,
) -> list[NoLookaheadAuditReason]:
    metadata_sources = [
        governance_metadata,
        _value(runtime_input_pack, "governance_metadata"),
    ]
    if signal_probe_spec is not None:
        spec_pack = _value(signal_probe_spec, "runtime_input_pack")
        metadata_sources.append(_value(spec_pack, "governance_metadata"))
    has_contamination_metadata = any(
        _contains_contamination_metadata(source) for source in metadata_sources
    )

    scope_sources: list[tuple[str, object]] = [
        ("runtime_input_pack.partition_scope", _value(runtime_input_pack, "partition_scope"))
    ]
    if partition_scope is not None:
        scope_sources.append(("partition_scope", partition_scope))
    if signal_probe_spec is not None:
        spec_pack = _value(signal_probe_spec, "runtime_input_pack")
        scope_sources.append(
            (
                "signal_probe_spec.runtime_input_pack.partition_scope",
                _value(spec_pack, "partition_scope"),
            )
        )

    reasons: list[NoLookaheadAuditReason] = []
    purpose = _normalize_token(partition_purpose or "")
    for field, scope in scope_sources:
        partition_id = str(_value(scope, "partition_id") or "")
        locked_scope = partition_id in LOCKED_PARTITION_IDS or _contains_locked_marker(scope)
        if not locked_scope:
            continue
        selection_requested = "selection" in purpose or _selection_on_locked_marker(scope)
        if selection_requested:
            reasons.append(
                _reason(
                    code="locked_test_selection_forbidden",
                    category=NoLookaheadRejectionCategory.BLOCKED_BY_POLICY,
                    message="selection on locked-test or shadow partitions is forbidden",
                    field=field,
                    expected="development or validation selection scope",
                    actual=partition_id or _actual(scope),
                )
            )
        if not has_contamination_metadata:
            reasons.append(
                _reason(
                    code="locked_partition_governance_metadata_missing",
                    category=NoLookaheadRejectionCategory.BLOCKED_BY_POLICY,
                    message=(
                        "locked-test or shadow partition use requires governance "
                        "contamination metadata"
                    ),
                    field="governance_metadata",
                    expected="substantive governance contamination metadata",
                    actual="missing",
                )
            )
    return reasons


def _same_bar_count(report: SignalProbeReport | Mapping[str, Any] | object) -> int | None:
    for container_name in ("position_summary", "trade_summary"):
        container = _value(report, container_name)
        value = _value(container, "same_bar_fill_count")
        count = _int_value(value)
        if count is not None:
            return count
    return None


def _feature_label_marker(value: Mapping[str, Any] | object) -> str | None:
    field_roles = _audit_field_roles(value)
    key_names = (
        "field",
        "fields",
        "feature_name",
        "input_fields",
        "input_views",
        "signal_name",
        "source_field",
        "source_fields",
    )
    for key in key_names:
        item = _value(value, key)
        marker = _first_label_marker(item, field_roles=field_roles)
        if marker is not None:
            return f"{key}={marker}"
    if isinstance(value, Mapping):
        for key in value:
            key_text = str(key)
            if _is_forbidden_future_field(key_text):
                return key_text
            if _contains_label_token(key) and not _is_exempt_session_field(
                key_text,
                field_roles,
            ):
                return str(key)
    return None


def _audit_field_roles(value: Mapping[str, Any] | object) -> Mapping[str, object]:
    field_roles = _value(value, "field_roles")
    if not isinstance(field_roles, Mapping):
        return {}
    normalized: dict[str, object] = {}
    for key, item in field_roles.items():
        key_text = str(key)
        if _normalize_token(key_text) in SESSION_METADATA_FIELDS and isinstance(item, FieldRole):
            normalized[key_text] = item.value
        else:
            normalized[key_text] = item
    return normalized


def _first_label_marker(
    value: object,
    *,
    field_roles: Mapping[str, object] | None = None,
) -> str | None:
    if isinstance(value, str) and _is_forbidden_future_field(value):
        return value
    if _contains_label_token(value) and not (
        isinstance(value, str) and _is_exempt_session_field(value, field_roles)
    ):
        return str(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if _is_forbidden_future_field(key_text):
                return key_text
            if _contains_label_token(key) and not _is_exempt_session_field(
                key_text,
                field_roles,
            ):
                return str(key)
            marker = _first_label_marker(item, field_roles=field_roles)
            if marker is not None:
                return marker
    if isinstance(value, Sequence) and not isinstance(value, str):
        for item in value:
            marker = _first_label_marker(item, field_roles=field_roles)
            if marker is not None:
                return marker
    return None


def _is_label_window(value: Mapping[str, Any] | object) -> bool:
    role = _normalize_token(
        _first_not_missing(
            _value(value, "role"),
            _value(value, "input_role"),
            _value(value, "runtime_role"),
            _value(value, "kind"),
        )
    )
    return "label" in role


def _is_centered_window(value: Mapping[str, Any] | object) -> bool:
    if _value(value, "centered") is True or _value(value, "is_centered") is True:
        return True
    mode = _normalize_token(
        _first_not_missing(
            _value(value, "mode"),
            _value(value, "window_mode"),
            _value(value, "window_type"),
        )
    )
    return "center" in mode


def _is_future_window(value: Mapping[str, Any] | object) -> bool:
    for key in ("uses_future", "future_looking", "forward_looking"):
        if _value(value, key) is True:
            return True
    mode = _normalize_token(
        _first_not_missing(
            _value(value, "direction"),
            _value(value, "mode"),
            _value(value, "window_mode"),
            _value(value, "window_type"),
        )
    )
    if "forward" in mode or "future" in mode:
        return True
    for key in ("lookahead_bars", "future_bars", "forward_horizon_bars", "horizon_bars"):
        number = _int_value(_value(value, key))
        if number is not None and number > 0:
            return True
    return False


def _window_actual(value: Mapping[str, Any] | object) -> str:
    details = {
        key: _value(value, key)
        for key in (
            "window_type",
            "window_mode",
            "mode",
            "direction",
            "centered",
            "uses_future",
            "lookahead_bars",
            "forward_horizon_bars",
            "horizon_bars",
        )
        if not _is_missing(_value(value, key))
    }
    return str(details or type(value).__name__)


def _contains_contamination_metadata(value: object) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized_key = _normalize_token(key)
            if "contamination" in normalized_key and not _is_missing(item):
                return True
            if normalized_key == "governance_metadata" and not _is_missing(item):
                return True
            if _contains_contamination_metadata(item):
                return True
    if isinstance(value, Sequence) and not isinstance(value, str):
        return any(_contains_contamination_metadata(item) for item in value)
    return False


def _selection_on_locked_marker(value: object) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized_key = _normalize_token(key)
            if "selection" in normalized_key and _contains_locked_marker(item):
                return True
            if _selection_on_locked_marker(item):
                return True
    if isinstance(value, Sequence) and not isinstance(value, str):
        return any(_selection_on_locked_marker(item) for item in value)
    return False


def _contains_locked_marker(value: object) -> bool:
    if isinstance(value, str):
        normalized = _normalize_token(value)
        return any(_normalize_token(partition) in normalized for partition in LOCKED_PARTITION_IDS)
    if isinstance(value, Mapping):
        return any(
            _contains_locked_marker(key) or _contains_locked_marker(item)
            for key, item in value.items()
        )
    if isinstance(value, Sequence) and not isinstance(value, str):
        return any(_contains_locked_marker(item) for item in value)
    return False


def _is_runtime_input_pack_like(value: object) -> bool:
    return not _is_missing(value) and all(
        not _is_missing(_value(value, field))
        for field in ("feature_packs", "label_packs", "partition_scope")
    )


def _sequence_value(value: object, field: str) -> tuple[object, ...]:
    item = _value(value, field)
    if item is None:
        return ()
    if isinstance(item, str):
        return (item,)
    if isinstance(item, Sequence):
        return tuple(item)
    return ()


def _first_value(source: Mapping[str, Any] | object, *names: str, suffix: str) -> object:
    for name in names:
        value = _value(source, name)
        if not _is_missing(value):
            if isinstance(value, Mapping):
                nested = _value(value, suffix)
                if not _is_missing(nested):
                    return nested
            if isinstance(value, Sequence) and not isinstance(value, str):
                if suffix == "first" and len(value) >= 1:
                    return value[0]
                if suffix == "last" and len(value) >= 2:
                    return value[1]
            return value
    return None


def _value(value: object, field: str) -> object:
    if _is_missing(value):
        return None
    if isinstance(value, Mapping):
        if field in value:
            return value[field]
        if field == "study_input_pack" and isinstance(value.get("study_input_pack"), Mapping):
            return value["study_input_pack"]
        return None
    try:
        return getattr(value, field)
    except (AttributeError, TypeError, ValueError):
        return None


def _first_not_missing(*values: object) -> object:
    for value in values:
        if not _is_missing(value):
            return value
    return None


def _parse_ts(value: object) -> datetime | None:
    if _is_missing(value):
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
        return parsed if parsed.tzinfo is not None else None
    isoformat = getattr(value, "isoformat", None)
    if callable(isoformat):
        try:
            return _parse_ts(isoformat())
        except TypeError:
            return None
    return None


def _int_value(value: object) -> int | None:
    if isinstance(value, bool) or _is_missing(value):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _contains_label_token(value: object) -> bool:
    if not isinstance(value, str):
        return False
    normalized = _normalize_token(value)
    return any(_normalize_token(token) in normalized for token in LABEL_AS_FEATURE_TOKENS)


def _normalize_token(value: object) -> str:
    text = "" if value is None else str(value).strip().lower()
    return "".join(char if char.isalnum() else "_" for char in text)


def _is_missing(value: object) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    return value.strip()


def _reason(
    *,
    code: str,
    category: NoLookaheadRejectionCategory,
    message: str,
    field: str,
    expected: str,
    actual: str,
    decision_state: RuntimeEntryStatus = RuntimeEntryStatus.INPUTS_BLOCKED,
) -> NoLookaheadAuditReason:
    return NoLookaheadAuditReason(
        code=code,
        category=category,
        message=message,
        field=field,
        decision_state=decision_state,
        expected=expected,
        actual=actual,
    )


def _dedupe_reasons(
    reasons: Sequence[NoLookaheadAuditReason],
) -> tuple[NoLookaheadAuditReason, ...]:
    unique: list[NoLookaheadAuditReason] = []
    seen: set[tuple[str, str, str]] = set()
    for reason in reasons:
        key = (reason.code, reason.field, reason.actual)
        if key in seen:
            continue
        seen.add(key)
        unique.append(reason)
    return tuple(unique)


def _actual(value: object) -> str:
    if _is_missing(value):
        return "missing"
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _actual_fill_policy(value: object) -> str:
    return (
        "delay_bars="
        f"{_value(value, 'delay_bars')}, allow_same_bar_fill="
        f"{_value(value, 'allow_same_bar_fill')}"
    )
