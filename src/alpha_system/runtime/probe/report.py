"""Signal Probe report contracts.

Reports are scalar-only, descriptive fast-path screens. They deliberately do
not represent strategy validation, a candidate, a backtest, or promotion.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, cast

from alpha_system.governance.serialization import (
    GovernanceSerializationError,
    JsonValue,
    canonical_serialize,
    deserialize,
)
from alpha_system.governance.serialization import (
    content_hash as governance_content_hash,
)
from alpha_system.runtime.contracts.run_record import RunRejectionReason, StudyRunResultState
from alpha_system.runtime.cost import CostSensitivityReport
from alpha_system.runtime.diagnostics.contracts import DiagnosticsReportRef
from alpha_system.runtime.probe.spec import (
    SignalProbeSpec,
    SignalProbeSpecRef,
)

PROBE_REPORT_SCHEMA = "alpha_system.runtime.probe.report.v1"
PROBE_REPORT_KIND = "signal_probe_report"
PROBE_REPORT_ID_PREFIX = "preport"
SIGNAL_PROBE_ALLOWED_STATES: frozenset[StudyRunResultState] = frozenset(
    {
        StudyRunResultState.SIGNAL_PROBE_COMPLETE,
        StudyRunResultState.REJECTED,
        StudyRunResultState.INCONCLUSIVE,
        StudyRunResultState.BLOCKED,
    }
)
SIGNAL_PROBE_TERMINAL_FAILURE_STATES: frozenset[StudyRunResultState] = frozenset(
    {
        StudyRunResultState.REJECTED,
        StudyRunResultState.INCONCLUSIVE,
        StudyRunResultState.BLOCKED,
    }
)

type JsonScalar = None | bool | int | float | str
ScalarItems = tuple[tuple[str, JsonScalar], ...]


class SignalProbeReportContractError(ValueError):
    """Raised when a SignalProbeReport would violate the probe contract."""


@dataclass(frozen=True, slots=True)
class ThresholdProbeSummary:
    """Scalar stability summary for one declared threshold."""

    threshold: Decimal
    trade_count: int
    turnover: Decimal
    gross_expectancy_proxy: Decimal | None
    double_cost_expectancy_proxy: Decimal | None
    drawdown_proxy: Decimal
    stable_under_double_cost: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "threshold", _positive_decimal(self.threshold, "threshold"))
        _non_negative_int(self.trade_count, "trade_count")
        object.__setattr__(self, "turnover", _non_negative_decimal(self.turnover, "turnover"))
        object.__setattr__(
            self,
            "gross_expectancy_proxy",
            _optional_decimal(self.gross_expectancy_proxy, "gross_expectancy_proxy"),
        )
        object.__setattr__(
            self,
            "double_cost_expectancy_proxy",
            _optional_decimal(
                self.double_cost_expectancy_proxy,
                "double_cost_expectancy_proxy",
            ),
        )
        object.__setattr__(
            self,
            "drawdown_proxy",
            _non_negative_decimal(self.drawdown_proxy, "drawdown_proxy"),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a scalar threshold summary."""

        return {
            "threshold": _decimal_text(self.threshold),
            "trade_count": self.trade_count,
            "turnover": _decimal_text(self.turnover),
            "gross_expectancy_proxy": _optional_decimal_text(self.gross_expectancy_proxy),
            "double_cost_expectancy_proxy": _optional_decimal_text(
                self.double_cost_expectancy_proxy
            ),
            "drawdown_proxy": _decimal_text(self.drawdown_proxy),
            "stable_under_double_cost": self.stable_under_double_cost,
        }


@dataclass(frozen=True, slots=True, init=False)
class SignalProbeReport:
    """Descriptive signal-probe report with mandatory cost-stress evidence."""

    report_id: str
    report_kind: str
    signal_probe_spec_ref: SignalProbeSpecRef
    status: StudyRunResultState
    lineage_refs_json: str
    position_summary_items: ScalarItems
    trade_summary_items: ScalarItems
    cost_aware_expectancy_items: ScalarItems
    drawdown_proxy_items: ScalarItems
    stability_summary_items: ScalarItems
    threshold_summaries: tuple[ThresholdProbeSummary, ...]
    cost_sensitivity_report_ref: DiagnosticsReportRef
    cost_stress_evidence_state: str
    limitations: tuple[str, ...]
    rejection_reasons: tuple[RunRejectionReason, ...]
    report_metadata_items: ScalarItems
    report_hash: str
    fast_path: bool
    not_strategy_validation: bool
    not_a_candidate: bool

    def __init__(
        self,
        *,
        signal_probe_spec_ref: SignalProbeSpec | SignalProbeSpecRef | Mapping[str, Any],
        status: StudyRunResultState | str,
        lineage_refs: Mapping[str, str],
        position_summary: Mapping[str, JsonScalar],
        trade_summary: Mapping[str, JsonScalar],
        cost_aware_expectancy_proxy: Mapping[str, JsonScalar],
        drawdown_proxy: Mapping[str, JsonScalar],
        stability_summary: Mapping[str, JsonScalar],
        threshold_summaries: Sequence[ThresholdProbeSummary | Mapping[str, Any]],
        cost_sensitivity_report: CostSensitivityReport,
        limitations: Sequence[str],
        rejection_reasons: Sequence[RunRejectionReason | Mapping[str, Any]] = (),
        report_metadata: Mapping[str, JsonScalar] | None = None,
    ) -> None:
        spec_ref = _coerce_spec_ref(signal_probe_spec_ref)
        normalized_status = _coerce_status(status)
        if not isinstance(cost_sensitivity_report, CostSensitivityReport):
            raise SignalProbeReportContractError(
                "SignalProbeReport requires an accompanying CostSensitivityReport"
            )
        cost_sensitivity_report.double_cost_summary
        if normalized_status is StudyRunResultState.SIGNAL_PROBE_COMPLETE and (
            cost_sensitivity_report.status is not StudyRunResultState.DIAGNOSTICS_COMPLETE
        ):
            raise SignalProbeReportContractError(
                "SIGNAL_PROBE_COMPLETE requires completed double_cost cost stress evidence"
            )

        reasons = tuple(_coerce_rejection_reason(reason) for reason in rejection_reasons)
        if normalized_status in SIGNAL_PROBE_TERMINAL_FAILURE_STATES and not reasons:
            raise SignalProbeReportContractError(
                "terminal probe states require at least one visible rejection reason"
            )

        normalized_thresholds = tuple(
            _coerce_threshold_summary(item) for item in threshold_summaries
        )
        if not normalized_thresholds:
            raise SignalProbeReportContractError("threshold_summaries must not be empty")
        normalized_limitations = _text_sequence(limitations, field="limitations")
        lineage_json = _canonical_string_mapping(lineage_refs, field="lineage_refs")
        position_items = _scalar_items(position_summary, field="position_summary")
        trade_items = _scalar_items(trade_summary, field="trade_summary")
        expectancy_items = _scalar_items(
            cost_aware_expectancy_proxy,
            field="cost_aware_expectancy_proxy",
        )
        drawdown_items = _scalar_items(drawdown_proxy, field="drawdown_proxy")
        stability_items = _scalar_items(stability_summary, field="stability_summary")
        metadata_items = _scalar_items(report_metadata or {}, field="report_metadata")
        cost_ref = cost_sensitivity_report.to_ref()
        evidence_state = (
            "COST_STRESS_COMPLETE"
            if cost_sensitivity_report.status is StudyRunResultState.DIAGNOSTICS_COMPLETE
            else f"COST_STRESS_{cost_sensitivity_report.status.value}"
        )
        payload = {
            "schema": PROBE_REPORT_SCHEMA,
            "report_kind": PROBE_REPORT_KIND,
            "signal_probe_spec_ref": spec_ref.to_dict(),
            "status": normalized_status.value,
            "lineage_refs": _json_dict(lineage_json, field="lineage_refs"),
            "position_summary": dict(position_items),
            "trade_summary": dict(trade_items),
            "cost_aware_expectancy_proxy": dict(expectancy_items),
            "drawdown_proxy": dict(drawdown_items),
            "stability_summary": dict(stability_items),
            "threshold_summaries": [summary.to_dict() for summary in normalized_thresholds],
            "cost_sensitivity_report_ref": cost_ref.to_dict(),
            "cost_stress_evidence_state": evidence_state,
            "limitations": list(normalized_limitations),
            "rejection_reason_records": [reason.to_dict() for reason in reasons],
            "report_metadata": dict(metadata_items),
            "fast_path": True,
            "not_strategy_validation": True,
            "not_a_candidate": True,
            "not_a_backtest": True,
            "promotion_basis_allowed": False,
            "raw_or_heavy_data_embedded": False,
        }
        digest = governance_content_hash(cast(JsonValue, payload))

        object.__setattr__(self, "report_id", f"{PROBE_REPORT_ID_PREFIX}_{digest[:24]}")
        object.__setattr__(self, "report_kind", PROBE_REPORT_KIND)
        object.__setattr__(self, "signal_probe_spec_ref", spec_ref)
        object.__setattr__(self, "status", normalized_status)
        object.__setattr__(self, "lineage_refs_json", lineage_json)
        object.__setattr__(self, "position_summary_items", position_items)
        object.__setattr__(self, "trade_summary_items", trade_items)
        object.__setattr__(self, "cost_aware_expectancy_items", expectancy_items)
        object.__setattr__(self, "drawdown_proxy_items", drawdown_items)
        object.__setattr__(self, "stability_summary_items", stability_items)
        object.__setattr__(self, "threshold_summaries", normalized_thresholds)
        object.__setattr__(self, "cost_sensitivity_report_ref", cost_ref)
        object.__setattr__(self, "cost_stress_evidence_state", evidence_state)
        object.__setattr__(self, "limitations", normalized_limitations)
        object.__setattr__(self, "rejection_reasons", reasons)
        object.__setattr__(self, "report_metadata_items", metadata_items)
        object.__setattr__(self, "report_hash", digest)
        object.__setattr__(self, "fast_path", True)
        object.__setattr__(self, "not_strategy_validation", True)
        object.__setattr__(self, "not_a_candidate", True)

    @property
    def lineage_refs(self) -> dict[str, str]:
        """Return lineage references as a defensive mapping."""

        return {key: str(value) for key, value in _json_dict(self.lineage_refs_json).items()}

    @property
    def position_summary(self) -> dict[str, JsonScalar]:
        """Return scalar position summary fields."""

        return dict(self.position_summary_items)

    @property
    def trade_summary(self) -> dict[str, JsonScalar]:
        """Return scalar trade summary fields."""

        return dict(self.trade_summary_items)

    @property
    def cost_aware_expectancy_proxy(self) -> dict[str, JsonScalar]:
        """Return per-profile cost-aware expectancy proxies."""

        return dict(self.cost_aware_expectancy_items)

    @property
    def drawdown_proxy(self) -> dict[str, JsonScalar]:
        """Return scalar drawdown proxy fields."""

        return dict(self.drawdown_proxy_items)

    @property
    def stability_summary(self) -> dict[str, JsonScalar]:
        """Return bounded threshold-neighborhood stability fields."""

        return dict(self.stability_summary_items)

    @property
    def report_metadata(self) -> dict[str, JsonScalar]:
        """Return scalar report metadata fields."""

        return dict(self.report_metadata_items)

    @property
    def rejection_reason(self) -> RunRejectionReason | None:
        """Return the first visible probe-local reason, if present."""

        return self.rejection_reasons[0] if self.rejection_reasons else None

    def to_dict(self) -> dict[str, object]:
        """Return the signal probe report payload without raw or heavy data."""

        return {
            "schema": PROBE_REPORT_SCHEMA,
            "report_id": self.report_id,
            "report_kind": self.report_kind,
            "signal_probe_spec_ref": self.signal_probe_spec_ref.to_dict(),
            "status": self.status.value,
            "lineage_refs": self.lineage_refs,
            "position_summary": self.position_summary,
            "trade_summary": self.trade_summary,
            "cost_aware_expectancy_proxy": self.cost_aware_expectancy_proxy,
            "drawdown_proxy": self.drawdown_proxy,
            "stability_summary": self.stability_summary,
            "threshold_summaries": [summary.to_dict() for summary in self.threshold_summaries],
            "cost_sensitivity_report_ref": self.cost_sensitivity_report_ref.to_dict(),
            "cost_stress_evidence_state": self.cost_stress_evidence_state,
            "limitations": list(self.limitations),
            "rejection_reason_records": [reason.to_dict() for reason in self.rejection_reasons],
            "report_metadata": self.report_metadata,
            "report_hash": self.report_hash,
            "fast_path": True,
            "not_strategy_validation": True,
            "not_a_candidate": True,
            "not_a_backtest": True,
            "promotion_basis_allowed": False,
            "raw_or_heavy_data_embedded": False,
        }


def _coerce_spec_ref(value: SignalProbeSpec | SignalProbeSpecRef | Mapping[str, Any]):
    if isinstance(value, SignalProbeSpec):
        return value.to_ref()
    if isinstance(value, SignalProbeSpecRef):
        return value
    if isinstance(value, Mapping):
        _reject_extra_keys(value, allowed={"signal_probe_spec_id", "content_hash"}, field="spec")
        return SignalProbeSpecRef(
            signal_probe_spec_id=value.get("signal_probe_spec_id"),
            content_hash=value.get("content_hash"),
        )
    raise SignalProbeReportContractError(
        "signal_probe_spec_ref must be SignalProbeSpec, SignalProbeSpecRef, or mapping"
    )


def _coerce_status(value: StudyRunResultState | str) -> StudyRunResultState:
    if isinstance(value, StudyRunResultState):
        state = value
    elif isinstance(value, str):
        try:
            state = StudyRunResultState(value)
        except ValueError as exc:
            raise SignalProbeReportContractError(f"unsupported probe status: {value}") from exc
    else:
        raise SignalProbeReportContractError("status must be StudyRunResultState or str")
    if state not in SIGNAL_PROBE_ALLOWED_STATES:
        allowed = ", ".join(sorted(item.value for item in SIGNAL_PROBE_ALLOWED_STATES))
        raise SignalProbeReportContractError(f"probe status must be one of: {allowed}")
    return state


def _coerce_threshold_summary(
    value: ThresholdProbeSummary | Mapping[str, Any],
) -> ThresholdProbeSummary:
    if isinstance(value, ThresholdProbeSummary):
        return value
    if isinstance(value, Mapping):
        _reject_extra_keys(
            value,
            allowed={
                "threshold",
                "trade_count",
                "turnover",
                "gross_expectancy_proxy",
                "double_cost_expectancy_proxy",
                "drawdown_proxy",
                "stable_under_double_cost",
            },
            field="threshold_summary",
        )
        return ThresholdProbeSummary(
            threshold=_decimal(value.get("threshold"), "threshold"),
            trade_count=int(value.get("trade_count", 0)),
            turnover=_decimal(value.get("turnover", "0"), "turnover"),
            gross_expectancy_proxy=_optional_decimal(
                value.get("gross_expectancy_proxy"),
                "gross_expectancy_proxy",
            ),
            double_cost_expectancy_proxy=_optional_decimal(
                value.get("double_cost_expectancy_proxy"),
                "double_cost_expectancy_proxy",
            ),
            drawdown_proxy=_decimal(value.get("drawdown_proxy", "0"), "drawdown_proxy"),
            stable_under_double_cost=bool(value.get("stable_under_double_cost", False)),
        )
    raise SignalProbeReportContractError(
        "threshold_summaries must contain ThresholdProbeSummary objects or mappings"
    )


def _coerce_rejection_reason(value: RunRejectionReason | Mapping[str, Any]) -> RunRejectionReason:
    if isinstance(value, RunRejectionReason):
        return value
    if not isinstance(value, Mapping):
        raise SignalProbeReportContractError(
            f"rejection reason must be RunRejectionReason or mapping, got {type(value).__name__}"
        )
    _reject_extra_keys(value, allowed={"code", "message"}, field="rejection_reasons")
    return RunRejectionReason(code=value.get("code"), message=value.get("message"))


def _scalar_items(value: Mapping[str, JsonScalar], *, field: str) -> ScalarItems:
    items: list[tuple[str, JsonScalar]] = []
    for key, item in value.items():
        if not isinstance(key, str) or not key.strip():
            raise SignalProbeReportContractError(f"{field} keys must be non-empty strings")
        if not _is_json_scalar(item):
            raise SignalProbeReportContractError(f"{field}.{key} must be a JSON scalar")
        items.append((key, item))
    return tuple(sorted(items))


def _canonical_string_mapping(value: Mapping[str, str], *, field: str) -> str:
    try:
        return canonical_serialize(
            cast(JsonValue, {str(key): str(item) for key, item in value.items()})
        )
    except GovernanceSerializationError as exc:
        raise SignalProbeReportContractError(f"{field} must be JSON-compatible: {exc}") from exc


def _json_dict(text: str, *, field: str = "lineage_refs") -> dict[str, JsonValue]:
    try:
        value = deserialize(text)
    except GovernanceSerializationError as exc:
        raise SignalProbeReportContractError(f"{field} must be serialized JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise SignalProbeReportContractError(f"{field} must serialize to a mapping")
    return dict(value)


def _text_sequence(values: Sequence[str], *, field: str) -> tuple[str, ...]:
    if isinstance(values, str) or not values:
        raise SignalProbeReportContractError(f"{field} must be a non-empty text sequence")
    result = tuple(_required_text(value, field=field) for value in values)
    if not result:
        raise SignalProbeReportContractError(f"{field} must not be empty")
    return result


def _reject_extra_keys(value: Mapping[str, Any], *, allowed: set[str], field: str) -> None:
    extra = set(value) - allowed
    if extra:
        raise SignalProbeReportContractError(
            f"{field} contains unsupported fields: {', '.join(sorted(extra))}"
        )


def _required_text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SignalProbeReportContractError(f"{field} is required")
    return value.strip()


def _is_json_scalar(value: object) -> bool:
    return value is None or isinstance(value, bool | int | float | str)


def _non_negative_int(value: object, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SignalProbeReportContractError(f"{field} must be a non-negative integer")


def _decimal(value: object, field: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise SignalProbeReportContractError(f"{field} must be numeric")
    try:
        active = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise SignalProbeReportContractError(f"{field} must be numeric") from exc
    if not active.is_finite():
        raise SignalProbeReportContractError(f"{field} must be finite")
    return active


def _optional_decimal(value: object, field: str) -> Decimal | None:
    if value is None:
        return None
    return _decimal(value, field)


def _non_negative_decimal(value: object, field: str) -> Decimal:
    active = _decimal(value, field)
    if active < Decimal("0"):
        raise SignalProbeReportContractError(f"{field} must be non-negative")
    return active


def _positive_decimal(value: object, field: str) -> Decimal:
    active = _decimal(value, field)
    if active <= Decimal("0"):
        raise SignalProbeReportContractError(f"{field} must be positive")
    return active


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")


def _optional_decimal_text(value: Decimal | None) -> str | None:
    return None if value is None else _decimal_text(value)


__all__ = [
    "PROBE_REPORT_KIND",
    "PROBE_REPORT_SCHEMA",
    "SignalProbeReport",
    "SignalProbeReportContractError",
    "ThresholdProbeSummary",
]
