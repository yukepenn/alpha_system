"""Markdown report cards for value-free runtime contract objects."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, cast

from alpha_system.runtime.decisions.states import (
    RuntimeDecisionStateError,
    coerce_runtime_decision_state,
    is_prohibited_mvp_state_value,
)

type JsonScalar = None | bool | int | float | str
type JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


PROHIBITED_MVP_STATES: frozenset[str] = frozenset(
    {
        "ALPHA_VALIDATED",
        "FACTOR_PROMOTED",
        "STRATEGY_READY",
        "PORTFOLIO_READY",
        "LIVE_READY",
        "PAPER_READY",
        "PROFITABLE",
        "TRADABLE",
        "PRODUCTION_READY",
    }
)

PROHIBITED_RENDER_PHRASES: tuple[str, ...] = (
    "alpha validated",
    "alpha validation",
    "validated alpha",
    "factor promoted",
    "promoted factor",
    "strategy ready",
    "portfolio ready",
    "live ready",
    "paper ready",
    "production ready",
    "production-ready",
    "promotion",
    "referencecandidatehandoff",
    "profitable",
    "profitability",
    "strategy",
    "tradable",
    "tradability",
)

HEAVY_RENDER_TOKENS: tuple[str, ...] = (
    ".arrow",
    ".dbn",
    ".feather",
    ".npy",
    ".npz",
    ".parquet",
    ".sqlite",
    ".wal",
    ".zst",
    "canonical_bars",
    "canonical bars",
    "dataframe",
    "feature_values",
    "feature values",
    "label_values",
    "label values",
    "market_values",
    "market values",
    "provider_response",
    "provider response",
    "provider_rows",
    "provider rows",
    "raw_values",
    "raw values",
    "value_array",
    "value array",
    "value_table",
    "value table",
)
NORMALIZED_LIMITATION_TEXT = "Upstream no-claim limitation recorded."

SUMMARY_SECTION_KEYS: tuple[tuple[str, str], ...] = (
    ("coverage_summary", "Coverage Summary"),
    ("quality_summary", "Quality Summary"),
    ("label_distribution_summary", "Label Distribution Summary"),
    ("label_horizon_coverage", "Label Horizon Coverage"),
    ("label_class_balance", "Label Class Balance"),
    ("label_mfe_mae_summary", "Label MFE MAE Summary"),
    ("label_path_ambiguity_summary", "Label Path Ambiguity Summary"),
    ("label_available_ts_validity", "Label Availability Summary"),
    ("label_cost_adjustment_sanity", "Label Cost Adjustment Summary"),
    ("label_coverage_missingness", "Label Coverage Missingness"),
    ("cost_gradient", "Cost Gradient Summary"),
)

REFERENCE_KEYS: frozenset[str] = frozenset(
    {
        "content_hash",
        "cost_model_hash",
        "cost_model_version",
        "cost_model_version_id",
        "dataset_admissibility_state",
        "dataset_lineage_ref",
        "dataset_version_hash",
        "dataset_version_id",
        "diagnostics_run_spec_id",
        "draft_hash",
        "draft_id",
        "handoff_hash",
        "handoff_id",
        "manifest_hash",
        "manifest_id",
        "record_hash",
        "record_id",
        "report_hash",
        "report_id",
        "run_id",
        "source_hash",
        "source_id",
        "study_run_spec_id",
    }
)

SKIPPED_KEYS: frozenset[str] = frozenset(
    {
        "alpha_spec_id",
        "descriptive_only",
        "diagnostic_pass_is_alpha_validation",
        "governance_evidence_input",
        "governance_evidence_input_json",
        "not_alpha_validation",
        "non_promotional",
        "promotion_basis_allowed",
        "raw_or_heavy_data_embedded",
        "schema",
        "strategy_not_validated",
        "value_free",
    }
)


class RuntimeReportCardError(ValueError):
    """Raised when a report card cannot be rendered within runtime boundaries."""


class _SupportsToDict(Protocol):
    def to_dict(self) -> Mapping[str, Any]:
        """Return the existing contract payload."""


@dataclass(frozen=True, slots=True)
class RuntimeRunSummary:
    """Compact run-level summary consumed by ``RuntimeReportCard``.

    This object is presentation-only. It stores ids, statuses, reasons,
    artifact references, and gate labels, but never stores observation arrays or
    materialized feature/label values.
    """

    run_id: str
    status: str
    study_spec_id: str | None = None
    research_spec_id: str | None = None
    dataset_version_id: str | None = None
    feature_pack_version_ids: tuple[str, ...] = field(default_factory=tuple)
    label_pack_version_ids: tuple[str, ...] = field(default_factory=tuple)
    artifact_refs: tuple[Mapping[str, JsonScalar], ...] = field(default_factory=tuple)
    rejection_reasons: tuple[Mapping[str, JsonScalar], ...] = field(default_factory=tuple)
    limitations: tuple[str, ...] = field(default_factory=tuple)
    next_required_gate: str | None = None
    fast_path: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "run_id", _required_text(self.run_id, "run_id"))
        object.__setattr__(self, "status", _state_text(self.status))
        object.__setattr__(
            self,
            "study_spec_id",
            _optional_text(self.study_spec_id, "study_spec_id"),
        )
        object.__setattr__(
            self,
            "research_spec_id",
            _optional_text(self.research_spec_id, "research_spec_id"),
        )
        object.__setattr__(
            self,
            "dataset_version_id",
            _optional_text(self.dataset_version_id, "dataset_version_id"),
        )
        object.__setattr__(
            self,
            "feature_pack_version_ids",
            _text_tuple(self.feature_pack_version_ids, "feature_pack_version_ids"),
        )
        object.__setattr__(
            self,
            "label_pack_version_ids",
            _text_tuple(self.label_pack_version_ids, "label_pack_version_ids"),
        )
        object.__setattr__(
            self,
            "artifact_refs",
            tuple(_scalar_mapping(ref, "artifact_refs") for ref in self.artifact_refs),
        )
        object.__setattr__(
            self,
            "rejection_reasons",
            tuple(
                _scalar_mapping(reason, "rejection_reasons") for reason in self.rejection_reasons
            ),
        )
        object.__setattr__(self, "limitations", _text_tuple(self.limitations, "limitations"))
        object.__setattr__(
            self,
            "next_required_gate",
            _optional_text(self.next_required_gate, "next_required_gate"),
        )

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a scalar-only report-card input payload."""

        payload: dict[str, JsonValue] = {
            "object_type": "RuntimeRunSummary",
            "run_id": self.run_id,
            "status": self.status,
            "feature_pack_version_ids": list(self.feature_pack_version_ids),
            "label_pack_version_ids": list(self.label_pack_version_ids),
            "artifact_refs": [dict(ref) for ref in self.artifact_refs],
            "rejection_reason_records": [dict(reason) for reason in self.rejection_reasons],
            "limitations": list(self.limitations),
            "next_required_gate": self.next_required_gate or _default_next_gate(self.status),
            "fast_path": self.fast_path,
            "fast_path_label": (
                "fast_path_non_reference" if self.fast_path else "standard_reference_gate_required"
            ),
            "descriptive_only": True,
            "raw_or_heavy_data_embedded": False,
        }
        if self.study_spec_id is not None:
            payload["study_spec_id"] = self.study_spec_id
        if self.research_spec_id is not None:
            payload["research_spec_id"] = self.research_spec_id
        if self.dataset_version_id is not None:
            payload["dataset_version_id"] = self.dataset_version_id
        return payload


@dataclass(frozen=True, slots=True)
class RuntimeReportCard:
    """Render compact Markdown cards from existing runtime contract objects."""

    max_items_per_section: int = 8

    def __post_init__(self) -> None:
        if self.max_items_per_section < 1:
            raise RuntimeReportCardError("max_items_per_section must be positive")

    def render(
        self,
        value: object,
        *,
        title: str | None = None,
        next_required_gate: str | None = None,
        fast_path: bool | None = None,
    ) -> str:
        """Render one contract object as a descriptive Markdown report card."""

        payload = _payload(value)
        card_title = _safe_text(title or _display_kind(value, payload), "title")
        status = _status_from_payload(payload)
        gate = _safe_text(
            next_required_gate or _next_gate_from_payload(payload) or _default_next_gate(status),
            "next_required_gate",
        )

        lines = [
            f"# Runtime Report Card: {card_title}",
            "",
            "Compact summaries and references only.",
            "",
            "## Status",
        ]
        lines.extend(
            _table(
                (
                    ("Status", status),
                    ("Next required gate", gate),
                    ("Data scope", "summaries, version ids, statuses, reasons, and refs"),
                )
            )
        )

        labels = _labels(payload, fast_path=fast_path)
        if labels:
            lines.extend(("", "## Labels"))
            lines.extend(_table(labels))

        identity = _identity_rows(payload)
        if identity:
            lines.extend(("", "## References"))
            lines.extend(_table(identity[: self.max_items_per_section]))

        lineage = _lineage_rows(payload)
        if lineage:
            lines.extend(("", "## Lineage"))
            lines.extend(_table(lineage[: self.max_items_per_section]))

        for key, heading in SUMMARY_SECTION_KEYS:
            section_rows = _summary_rows(payload.get(key))
            if section_rows:
                lines.extend(("", f"## {heading}"))
                lines.extend(_table(section_rows[: self.max_items_per_section]))

        gate_rows = _quality_gate_rows(payload)
        if gate_rows:
            lines.extend(("", "## Quality Gates"))
            lines.extend(_table(gate_rows[: self.max_items_per_section]))
            lines.append("")
            lines.append("Gate statuses are descriptive run checks only.")

        profile_rows = _cost_profile_rows(payload)
        if profile_rows:
            lines.extend(("", "## Cost Profiles"))
            lines.extend(_table(profile_rows[: self.max_items_per_section]))
            lines.append("")
            lines.append("Cost and slippage entries are stress summaries and proxy labels.")

        evidence_rows = _evidence_section_rows(payload)
        if evidence_rows:
            lines.extend(("", "## Evidence Sections"))
            lines.extend(_table(evidence_rows[: self.max_items_per_section]))
            lines.append("")
            lines.append("EvidenceDraft is a draft input, not a candidate.")

        handoff_rows = _handoff_ref_rows(payload)
        if handoff_rows:
            lines.extend(("", "## Handoff Refs"))
            lines.extend(_table(handoff_rows[: self.max_items_per_section]))
            lines.append("")
            lines.append("Reference handoff is a package only; it is not Reference validation.")

        reason_rows = _reason_rows(payload)
        if reason_rows:
            lines.extend(("", "## Visible Reasons"))
            lines.extend(_table(reason_rows[: self.max_items_per_section]))

        artifact_rows = _artifact_rows(payload)
        if artifact_rows:
            lines.extend(("", "## Artifact Refs"))
            lines.extend(_table(artifact_rows[: self.max_items_per_section]))

        limitation_rows = _limitation_rows(payload)
        if limitation_rows:
            lines.extend(("", "## Limitations"))
            lines.extend(f"- {item}" for _, item in limitation_rows[: self.max_items_per_section])

        markdown = "\n".join(lines).rstrip() + "\n"
        _assert_render_safe(markdown)
        return markdown

    def render_many(
        self,
        values: Sequence[object],
        *,
        title: str = "Runtime Report Cards",
        next_required_gate: str | None = None,
    ) -> str:
        """Render a deterministic bundle of report cards."""

        if isinstance(values, str) or not isinstance(values, Sequence):
            raise RuntimeReportCardError("values must be a finite sequence")
        heading = _safe_text(title, "title")
        cards = [
            self.render(value, next_required_gate=next_required_gate).strip() for value in values
        ]
        markdown = f"# {heading}\n\n" + "\n\n---\n\n".join(cards) + "\n"
        _assert_render_safe(markdown)
        return markdown


def render_runtime_report_card(
    value: object,
    *,
    title: str | None = None,
    next_required_gate: str | None = None,
    fast_path: bool | None = None,
) -> str:
    """Convenience wrapper around ``RuntimeReportCard.render``."""

    return RuntimeReportCard().render(
        value,
        title=title,
        next_required_gate=next_required_gate,
        fast_path=fast_path,
    )


def _payload(value: object) -> dict[str, Any]:
    if isinstance(value, RuntimeRunSummary):
        return dict(value.to_dict())
    if isinstance(value, Mapping):
        return dict(value)
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        payload = to_dict()
        if not isinstance(payload, Mapping):
            raise RuntimeReportCardError("to_dict() must return a mapping")
        return dict(payload)
    raise RuntimeReportCardError(f"unsupported report-card input: {type(value).__name__}")


def _display_kind(value: object, payload: Mapping[str, Any]) -> str:
    if payload.get("object_type") == "RuntimeRunSummary":
        return "Runtime Run Summary"
    if payload.get("report_type") == "FactorDiagnosticsReport":
        return "Factor Diagnostics"
    if payload.get("report_type") == "CostSensitivityReport":
        return "Cost Sensitivity"
    if "label_distribution_summary" in payload:
        return "Label Diagnostics"
    if "draft_id" in payload:
        return "Evidence Draft"
    if "handoff_id" in payload:
        return "Reference Handoff"
    if {"code", "message", "decision_state", "stage"}.issubset(payload):
        return "Rejection Reason"
    return type(value).__name__.removesuffix("Report")


def _status_from_payload(payload: Mapping[str, Any]) -> str:
    candidates: tuple[Any, ...] = (
        payload.get("status"),
        payload.get("result_state"),
        payload.get("decision_state"),
        _nested(payload.get("decision"), "state"),
    )
    for candidate in candidates:
        if candidate is not None:
            return _state_text(candidate)
    return "UNSPECIFIED"


def _next_gate_from_payload(payload: Mapping[str, Any]) -> str | None:
    direct = payload.get("next_required_gate")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    requirement = payload.get("reference_requirements")
    if isinstance(requirement, Mapping):
        gate = requirement.get("next_required_gate")
        if isinstance(gate, str) and gate.strip():
            return gate.strip()
    return None


def _default_next_gate(status: object) -> str:
    state = _state_text(status)
    if state in {"REJECTED", "INCONCLUSIVE", "BLOCKED"}:
        return "Resolve visible reasons before rerun"
    if state == "DIAGNOSTICS_COMPLETE":
        return "Cost stress or evidence draft gate"
    if state in {"SIGNAL_PROBE_COMPLETE", "COST_STRESS_COMPLETE"}:
        return "Evidence draft gate"
    if state == "EVIDENCE_DRAFT_READY":
        return "Reference handoff gate"
    if state == "REFERENCE_HANDOFF_READY":
        return "Independent Reference review gate"
    if state == "UNSPECIFIED":
        return "Runtime plan gate"
    return "Next runtime gate from plan"


def _labels(
    payload: Mapping[str, Any],
    *,
    fast_path: bool | None,
) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = [("Posture", "descriptive only")]
    effective_fast_path = fast_path if fast_path is not None else bool(payload.get("fast_path"))
    if effective_fast_path or payload.get("fast_path_label") == "fast_path_non_reference":
        rows.append(("Path label", "fast path - non-Reference"))
    if payload.get("not_reference_truth") is True:
        rows.append(("Reference label", "draft input - not Reference truth"))
    if payload.get("not_reference_validation") is True:
        rows.append(("Reference label", "handoff package - not Reference validation"))
    if payload.get("not_finalized_evidence_bundle") is True:
        rows.append(("Evidence label", "draft input only"))
    return rows


def _identity_rows(payload: Mapping[str, Any]) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for key in (
        "run_id",
        "record_id",
        "report_id",
        "draft_id",
        "handoff_id",
        "study_spec_id",
        "research_spec_id",
        "report_hash",
        "record_hash",
        "draft_hash",
        "handoff_hash",
    ):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            rows.append((_display_key(key), value.strip()))

    for key in ("diagnostics_run_spec_ref", "study_run_spec_ref", "manifest_ref"):
        value = payload.get(key)
        if isinstance(value, Mapping):
            rows.extend(_mapping_rows(value, allowed=REFERENCE_KEYS))
    return rows


def _lineage_rows(payload: Mapping[str, Any]) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for key in ("lineage_refs", "version_lineage"):
        value = payload.get(key)
        if isinstance(value, Mapping):
            rows.extend(_mapping_rows(value, allowed=REFERENCE_KEYS))
            for nested_key in ("feature_pack_versions", "label_pack_versions"):
                nested = value.get(nested_key)
                if isinstance(nested, Sequence) and not isinstance(nested, str):
                    rows.append((_display_key(nested_key), str(len(nested))))

    for key in (
        "dataset_version_id",
        "cost_model_version",
        "cost_model_version_ref",
    ):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            rows.append((_display_key(key), value.strip()))
        elif isinstance(value, Mapping):
            rows.extend(_mapping_rows(value, allowed=REFERENCE_KEYS))

    for key in ("feature_pack_version_ids", "label_pack_version_ids"):
        value = payload.get(key)
        if isinstance(value, Sequence) and not isinstance(value, str) and value:
            rows.append((_display_key(key), ", ".join(_safe_text(item, key) for item in value)))
    return rows


def _summary_rows(value: object) -> list[tuple[str, str]]:
    if not isinstance(value, Mapping):
        return []
    return _mapping_rows(value)


def _quality_gate_rows(payload: Mapping[str, Any]) -> list[tuple[str, str]]:
    gates = payload.get("quality_gates")
    if not isinstance(gates, Sequence) or isinstance(gates, str):
        return []
    rows: list[tuple[str, str]] = []
    for index, gate in enumerate(gates, start=1):
        if not isinstance(gate, Mapping):
            continue
        name = _safe_text(gate.get("name") or gate.get("gate_id") or f"gate_{index}", "gate")
        status = _state_text(gate.get("status", "UNSPECIFIED"))
        summary = _safe_text(gate.get("summary", ""), "summary")
        rows.append((f"{name} status", status))
        if summary:
            rows.append((f"{name} summary", summary))
    return rows


def _cost_profile_rows(payload: Mapping[str, Any]) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    profiles = payload.get("profile_summaries") or payload.get("cost_profile_refs")
    if isinstance(profiles, Sequence) and not isinstance(profiles, str):
        for profile in profiles:
            if not isinstance(profile, Mapping):
                continue
            name = _safe_text(profile.get("profile_name", "profile"), "profile_name")
            cost_multiplier = _safe_text(profile.get("cost_multiplier", ""), "cost_multiplier")
            slippage_multiplier = _safe_text(
                profile.get("slippage_multiplier", ""),
                "slippage_multiplier",
            )
            rows.append((f"{name} cost multiplier", cost_multiplier))
            rows.append((f"{name} slippage multiplier", slippage_multiplier))
            zero_cost = profile.get("zero_cost_diagnostic_only")
            if isinstance(zero_cost, bool):
                rows.append((f"{name} zero-cost label", "yes" if zero_cost else "no"))
    double_summary = payload.get("double_cost_summary")
    if isinstance(double_summary, Mapping):
        rows.append(("double_cost profile", "present"))
    if payload.get("slippage_labeled_proxy") is True:
        rows.append(("Slippage label", "proxy"))
    return rows


def _evidence_section_rows(payload: Mapping[str, Any]) -> list[tuple[str, str]]:
    sections = payload.get("sections")
    if not isinstance(sections, Sequence) or isinstance(sections, str):
        return []
    rows: list[tuple[str, str]] = []
    for section in sections:
        if not isinstance(section, Mapping):
            continue
        name = _safe_text(section.get("section_name", "section"), "section_name")
        rows.append((f"{name} status", _state_text(section.get("status", "UNSPECIFIED"))))
        ref = section.get("source_ref")
        if isinstance(ref, Mapping):
            source_id = ref.get("source_id")
            source_hash = ref.get("source_hash")
            if isinstance(source_id, str):
                rows.append((f"{name} source id", source_id))
            if isinstance(source_hash, str):
                rows.append((f"{name} source hash", source_hash))
    return rows


def _handoff_ref_rows(payload: Mapping[str, Any]) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for key in (
        "evidence_draft_ref",
        "study_run_manifest_ref",
        "runtime_artifact_manifest_ref",
        "no_lookahead_audit_ref",
        "cost_model_version_ref",
    ):
        value = payload.get(key)
        if isinstance(value, Mapping):
            role = _safe_text(value.get("role", _display_key(key)), key)
            source_id = value.get("source_id")
            source_hash = value.get("source_hash")
            if isinstance(source_id, str):
                rows.append((f"{role} id", source_id))
            if isinstance(source_hash, str):
                rows.append((f"{role} hash", source_hash))

    refs = payload.get("diagnostics_report_refs")
    if isinstance(refs, Sequence) and not isinstance(refs, str):
        rows.append(("Diagnostics refs", str(len(refs))))
    return rows


def _reason_rows(payload: Mapping[str, Any]) -> list[tuple[str, str]]:
    if {"code", "message", "decision_state", "stage"}.issubset(payload):
        reasons: Sequence[Mapping[str, Any]] = (payload,)
    else:
        reasons = cast(Sequence[Mapping[str, Any]], payload.get("rejection_reason_records", ()))
        decision = payload.get("decision")
        if isinstance(decision, Mapping) and not reasons:
            raw_reasons = decision.get("reasons")
            if isinstance(raw_reasons, Sequence) and not isinstance(raw_reasons, str):
                reasons = cast(Sequence[Mapping[str, Any]], raw_reasons)

    if isinstance(reasons, str) or not isinstance(reasons, Sequence):
        return []

    rows: list[tuple[str, str]] = []
    for index, reason in enumerate(reasons, start=1):
        if not isinstance(reason, Mapping):
            continue
        prefix = f"Reason {index}"
        for key in ("code", "decision_state", "stage", "source_code", "source_id", "message"):
            value = reason.get(key)
            if isinstance(value, str) and value.strip():
                rows.append((f"{prefix} {_display_key(key)}", _state_or_text(key, value)))
    return rows


def _artifact_rows(payload: Mapping[str, Any]) -> list[tuple[str, str]]:
    artifacts = payload.get("artifact_refs") or payload.get("artifact_manifest")
    if not isinstance(artifacts, Sequence) or isinstance(artifacts, str):
        return []
    rows: list[tuple[str, str]] = []
    for index, artifact in enumerate(artifacts, start=1):
        if not isinstance(artifact, Mapping):
            continue
        prefix = f"Artifact {index}"
        for key in ("artifact_id", "artifact_type", "content_hash", "source_id", "source_hash"):
            value = artifact.get(key)
            if isinstance(value, str) and value.strip():
                rows.append((f"{prefix} {_display_key(key)}", value.strip()))
    return rows


def _limitation_rows(payload: Mapping[str, Any]) -> list[tuple[str, str]]:
    limitations = payload.get("limitations")
    if not isinstance(limitations, Sequence) or isinstance(limitations, str):
        return []
    rows: list[tuple[str, str]] = []
    for index, value in enumerate(limitations, start=1):
        if not isinstance(value, str) or not value.strip():
            continue
        lowered = value.lower()
        if _contains_prohibited_claim(lowered) or _contains_heavy_marker(lowered):
            rows.append((f"Limitation {index}", NORMALIZED_LIMITATION_TEXT))
        else:
            rows.append((f"Limitation {index}", _safe_text(value, "limitation")))
    return rows


def _mapping_rows(
    value: Mapping[str, Any],
    *,
    allowed: frozenset[str] | None = None,
) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for key in sorted(value):
        if key in SKIPPED_KEYS:
            continue
        if allowed is not None and key not in allowed:
            continue
        item = value[key]
        if _is_scalar(item):
            rows.append((_display_key(key), _state_or_text(key, item)))
    return rows


def _table(rows: Sequence[tuple[str, object]]) -> list[str]:
    output = ["| Field | Value |", "| --- | --- |"]
    output.extend(
        f"| {_escape_cell(_safe_text(key, 'table key'))} | "
        f"{_escape_cell(_safe_text(value, 'table value'))} |"
        for key, value in rows
    )
    return output


def _nested(value: object, key: str) -> object | None:
    if isinstance(value, Mapping):
        return value.get(key)
    return None


def _state_or_text(key: str, value: object) -> str:
    if key in {"status", "result_state", "decision_state", "state"}:
        return _state_text(value)
    return _safe_text(value, key)


def _state_text(value: object) -> str:
    text = _enum_value(value).strip().upper()
    if not text:
        raise RuntimeReportCardError("state text is required")
    if is_prohibited_mvp_state_value(text):
        raise RuntimeReportCardError(f"prohibited MVP state cannot be rendered: {text}")
    try:
        return coerce_runtime_decision_state(text).value
    except RuntimeDecisionStateError:
        if text in PROHIBITED_MVP_STATES:
            raise RuntimeReportCardError(
                f"prohibited MVP state cannot be rendered: {text}"
            ) from None
        return text


def _safe_text(value: object, field: str) -> str:
    text = _enum_value(value).strip()
    if "\n" in text or "\r" in text:
        raise RuntimeReportCardError(f"{field} must be one line")
    lowered = text.lower()
    if _contains_prohibited_claim(lowered):
        raise RuntimeReportCardError(f"{field} contains prohibited claim language")
    if _contains_heavy_marker(lowered):
        raise RuntimeReportCardError(f"{field} contains raw or heavy data marker")
    return text


def _required_text(value: object, field: str) -> str:
    text = _safe_text(value, field)
    if not text:
        raise RuntimeReportCardError(f"{field} is required")
    return text


def _optional_text(value: object, field: str) -> str | None:
    if value is None:
        return None
    return _required_text(value, field)


def _text_tuple(values: Sequence[object], field: str) -> tuple[str, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise RuntimeReportCardError(f"{field} must be a sequence")
    return tuple(_required_text(value, field) for value in values)


def _scalar_mapping(value: Mapping[str, JsonScalar], field: str) -> Mapping[str, JsonScalar]:
    if not isinstance(value, Mapping):
        raise RuntimeReportCardError(f"{field} entries must be mappings")
    return {
        _required_text(key, f"{field}.key"): _scalar_value(item, f"{field}.{key}")
        for key, item in value.items()
    }


def _scalar_value(value: object, field: str) -> JsonScalar:
    if _is_scalar(value):
        if isinstance(value, str):
            return _safe_text(value, field)
        return cast(JsonScalar, value)
    raise RuntimeReportCardError(f"{field} must be scalar")


def _is_scalar(value: object) -> bool:
    return value is None or isinstance(value, bool | int | float | str)


def _enum_value(value: object) -> str:
    if isinstance(value, Enum):
        return str(value.value)
    return "" if value is None else str(value)


def _display_key(key: str) -> str:
    replacements = {
        "alpha_spec_id": "research spec id",
        "bbo_available": "BBO available",
        "bbo_fill_count": "BBO fill count",
        "config_hash": "config hash",
        "content_hash": "content hash",
        "cost_model_hash": "cost model hash",
        "cost_model_version": "cost model version",
        "cost_model_version_id": "cost model version id",
        "dataset_admissibility_state": "dataset admissibility state",
        "dataset_lineage_ref": "dataset lineage ref",
        "dataset_version_hash": "dataset version hash",
        "dataset_version_id": "dataset version id",
        "diagnostics_run_spec_id": "diagnostics run spec id",
        "feature_pack_version_ids": "feature pack version ids",
        "feature_pack_versions": "feature pack ref count",
        "label_pack_version_ids": "label pack version ids",
        "label_pack_versions": "label pack ref count",
        "source_code": "source code",
        "source_hash": "source hash",
        "source_id": "source id",
        "study_run_spec_id": "study run spec id",
        "study_spec_id": "study spec id",
        "zero_cost_diagnostic_only": "zero-cost diagnostic only",
    }
    return replacements.get(key, key.replace("_", " "))


def _escape_cell(value: str) -> str:
    return value.replace("|", "\\|")


def _assert_render_safe(markdown: str) -> None:
    upper = markdown.upper()
    for state in PROHIBITED_MVP_STATES:
        if state in upper:
            raise RuntimeReportCardError(f"rendered output contains prohibited state: {state}")
    lowered = markdown.lower()
    if _contains_prohibited_claim(lowered):
        raise RuntimeReportCardError("rendered output contains prohibited claim language")
    if _contains_heavy_marker(lowered):
        raise RuntimeReportCardError("rendered output contains raw or heavy data marker")


def _contains_prohibited_claim(lowered_text: str) -> bool:
    return any(phrase in lowered_text for phrase in PROHIBITED_RENDER_PHRASES)


def _contains_heavy_marker(lowered_text: str) -> bool:
    return any(token in lowered_text for token in HEAVY_RENDER_TOKENS)


__all__ = [
    "RuntimeReportCard",
    "RuntimeReportCardError",
    "RuntimeRunSummary",
    "render_runtime_report_card",
]
