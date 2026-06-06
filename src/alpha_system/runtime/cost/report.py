"""Cost sensitivity report facade over the shared diagnostics report contract."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from alpha_system.runtime.contracts.run_record import RunRejectionReason, StudyRunResultState
from alpha_system.runtime.cost.model_version import CostModelVersion
from alpha_system.runtime.diagnostics.contracts import DiagnosticsFamily
from alpha_system.runtime.diagnostics.report import DiagnosticsReport

COST_SENSITIVITY_REPORT_KIND = "cost_sensitivity_report"
ZERO = Decimal("0")

type JsonScalar = None | bool | int | float | str


class CostSensitivityReportError(ValueError):
    """Raised when a cost sensitivity report would violate runtime constraints."""


@dataclass(frozen=True, slots=True)
class CostProfileSummary:
    """Scalar per-profile cost/slippage sensitivity summary."""

    profile_name: str
    fill_count: int
    bbo_fill_count: int
    cost_total: Decimal
    slippage_proxy_total: Decimal
    combined_cost_slippage_proxy: Decimal
    cost_multiplier: Decimal
    slippage_multiplier: Decimal
    bbo_spread_crossing_used: bool
    bbo_unavailable_fallback_used: bool
    zero_cost_diagnostic_only: bool
    promotion_basis_allowed: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile_name", _required_text(self.profile_name, "profile_name"))
        _non_negative_int(self.fill_count, "fill_count")
        _non_negative_int(self.bbo_fill_count, "bbo_fill_count")
        object.__setattr__(self, "cost_total", _non_negative_decimal(self.cost_total, "cost_total"))
        object.__setattr__(
            self,
            "slippage_proxy_total",
            _non_negative_decimal(self.slippage_proxy_total, "slippage_proxy_total"),
        )
        object.__setattr__(
            self,
            "combined_cost_slippage_proxy",
            _non_negative_decimal(
                self.combined_cost_slippage_proxy,
                "combined_cost_slippage_proxy",
            ),
        )
        object.__setattr__(
            self,
            "cost_multiplier",
            _positive_decimal(self.cost_multiplier, "cost_multiplier"),
        )
        object.__setattr__(
            self,
            "slippage_multiplier",
            _positive_decimal(self.slippage_multiplier, "slippage_multiplier"),
        )
        if self.promotion_basis_allowed is not False:
            raise CostSensitivityReportError("cost stress cannot be a promotion basis")

    def to_dict(self) -> dict[str, object]:
        """Return a scalar-only profile summary."""

        return {
            "profile_name": self.profile_name,
            "fill_count": self.fill_count,
            "bbo_fill_count": self.bbo_fill_count,
            "cost_total": _decimal_text(self.cost_total),
            "slippage_proxy_total": _decimal_text(self.slippage_proxy_total),
            "combined_cost_slippage_proxy": _decimal_text(
                self.combined_cost_slippage_proxy
            ),
            "cost_multiplier": _decimal_text(self.cost_multiplier),
            "slippage_multiplier": _decimal_text(self.slippage_multiplier),
            "bbo_spread_crossing_used": self.bbo_spread_crossing_used,
            "bbo_unavailable_fallback_used": self.bbo_unavailable_fallback_used,
            "zero_cost_diagnostic_only": self.zero_cost_diagnostic_only,
            "promotion_basis_allowed": False,
        }


@dataclass(frozen=True, slots=True)
class CostSessionSummary:
    """Scalar per-session contribution to one cost-stress profile."""

    profile_name: str
    session_label: str
    fill_count: int
    cost_total: Decimal
    slippage_proxy_total: Decimal
    combined_cost_slippage_proxy: Decimal
    session_cost_multiplier: Decimal
    session_slippage_multiplier: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile_name", _required_text(self.profile_name, "profile_name"))
        object.__setattr__(
            self,
            "session_label",
            _required_text(self.session_label, "session_label"),
        )
        _non_negative_int(self.fill_count, "fill_count")
        object.__setattr__(self, "cost_total", _non_negative_decimal(self.cost_total, "cost_total"))
        object.__setattr__(
            self,
            "slippage_proxy_total",
            _non_negative_decimal(self.slippage_proxy_total, "slippage_proxy_total"),
        )
        object.__setattr__(
            self,
            "combined_cost_slippage_proxy",
            _non_negative_decimal(
                self.combined_cost_slippage_proxy,
                "combined_cost_slippage_proxy",
            ),
        )
        object.__setattr__(
            self,
            "session_cost_multiplier",
            _positive_decimal(self.session_cost_multiplier, "session_cost_multiplier"),
        )
        object.__setattr__(
            self,
            "session_slippage_multiplier",
            _positive_decimal(
                self.session_slippage_multiplier,
                "session_slippage_multiplier",
            ),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a scalar-only session summary."""

        return {
            "profile_name": self.profile_name,
            "session_label": self.session_label,
            "fill_count": self.fill_count,
            "cost_total": _decimal_text(self.cost_total),
            "slippage_proxy_total": _decimal_text(self.slippage_proxy_total),
            "combined_cost_slippage_proxy": _decimal_text(
                self.combined_cost_slippage_proxy
            ),
            "session_cost_multiplier": _decimal_text(self.session_cost_multiplier),
            "session_slippage_multiplier": _decimal_text(
                self.session_slippage_multiplier
            ),
        }


@dataclass(frozen=True, slots=True)
class CostSensitivityReport:
    """Cost-family report with a shared RT-P06 DiagnosticsReport core."""

    diagnostics_report: DiagnosticsReport
    cost_model_version: CostModelVersion
    profile_summaries: tuple[CostProfileSummary, ...]
    session_breakdown: tuple[CostSessionSummary, ...]
    cost_gradient_items: tuple[tuple[str, JsonScalar], ...]
    slippage_labeled_proxy: bool = True
    bbo_spread_crossing_used: bool = False
    bbo_unavailable_fallback_used: bool = False

    def __post_init__(self) -> None:
        if self.diagnostics_report.diagnostics_family is not DiagnosticsFamily.COST:
            raise CostSensitivityReportError("diagnostics_report must be for the COST family")
        if self.diagnostics_report.report_kind != COST_SENSITIVITY_REPORT_KIND:
            raise CostSensitivityReportError("diagnostics_report must use cost_sensitivity_report")
        if not isinstance(self.cost_model_version, CostModelVersion):
            raise CostSensitivityReportError("cost_model_version must be a CostModelVersion")
        object.__setattr__(
            self,
            "profile_summaries",
            tuple(_coerce_profile_summary(item) for item in self.profile_summaries),
        )
        object.__setattr__(
            self,
            "session_breakdown",
            tuple(_coerce_session_summary(item) for item in self.session_breakdown),
        )
        if "double_cost" not in {summary.profile_name for summary in self.profile_summaries}:
            raise CostSensitivityReportError("double_cost profile summary is required")
        if self.slippage_labeled_proxy is not True:
            raise CostSensitivityReportError("slippage must be labeled as a proxy")
        if any(summary.promotion_basis_allowed for summary in self.profile_summaries):
            raise CostSensitivityReportError("profile summaries cannot permit promotion basis")

    @property
    def status(self) -> StudyRunResultState:
        """Return the shared diagnostics terminal status."""

        return self.diagnostics_report.status

    @property
    def limitations(self) -> tuple[str, ...]:
        """Return explicit limitations from the shared report."""

        return self.diagnostics_report.limitations

    @property
    def rejection_reasons(self) -> tuple[RunRejectionReason, ...]:
        """Return visible failure or inconclusive reasons."""

        return self.diagnostics_report.rejection_reasons

    @property
    def rejection_reason(self) -> RunRejectionReason | None:
        """Return the first visible rejection reason, if present."""

        return self.rejection_reasons[0] if self.rejection_reasons else None

    @property
    def cost_gradient(self) -> dict[str, JsonScalar]:
        """Return scalar gradient summaries keyed by profile transition."""

        return dict(self.cost_gradient_items)

    @property
    def double_cost_summary(self) -> CostProfileSummary:
        """Return the required double-cost profile summary."""

        for summary in self.profile_summaries:
            if summary.profile_name == "double_cost":
                return summary
        raise CostSensitivityReportError("double_cost profile summary is required")

    def to_ref(self):
        """Return the underlying diagnostics report reference."""

        return self.diagnostics_report.to_ref()

    def to_dict(self) -> dict[str, object]:
        """Return the cost sensitivity payload without embedding raw inputs."""

        payload = self.diagnostics_report.to_dict()
        payload.update(
            {
                "report_type": "CostSensitivityReport",
                "cost_model_version": self.cost_model_version.to_dict(),
                "slippage_labeled_proxy": True,
                "bbo_spread_crossing_used": self.bbo_spread_crossing_used,
                "bbo_unavailable_fallback_used": self.bbo_unavailable_fallback_used,
                "zero_cost_diagnostic_only": self.cost_model_version.zero_cost_diagnostic_only,
                "promotion_basis_allowed": False,
                "profile_summaries": [
                    summary.to_dict() for summary in self.profile_summaries
                ],
                "double_cost_summary": self.double_cost_summary.to_dict(),
                "session_breakdown": [
                    summary.to_dict() for summary in self.session_breakdown
                ],
                "cost_gradient": self.cost_gradient,
            }
        )
        return payload


def _coerce_profile_summary(value: CostProfileSummary) -> CostProfileSummary:
    if not isinstance(value, CostProfileSummary):
        raise CostSensitivityReportError("profile summaries must be CostProfileSummary")
    return value


def _coerce_session_summary(value: CostSessionSummary) -> CostSessionSummary:
    if not isinstance(value, CostSessionSummary):
        raise CostSensitivityReportError("session summaries must be CostSessionSummary")
    return value


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CostSensitivityReportError(f"{field} is required")
    return value.strip()


def _non_negative_int(value: object, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CostSensitivityReportError(f"{field} must be a non-negative integer")


def _decimal(value: object, field: str) -> Decimal:
    if isinstance(value, bool):
        raise CostSensitivityReportError(f"{field} must be numeric")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise CostSensitivityReportError(f"{field} must be numeric") from exc


def _non_negative_decimal(value: object, field: str) -> Decimal:
    active = _decimal(value, field)
    if active < ZERO:
        raise CostSensitivityReportError(f"{field} must be non-negative")
    return active


def _positive_decimal(value: object, field: str) -> Decimal:
    active = _decimal(value, field)
    if active <= ZERO:
        raise CostSensitivityReportError(f"{field} must be positive")
    return active


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")


__all__ = [
    "COST_SENSITIVITY_REPORT_KIND",
    "CostProfileSummary",
    "CostSensitivityReport",
    "CostSensitivityReportError",
    "CostSessionSummary",
]
