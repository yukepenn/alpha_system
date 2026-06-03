"""Audit-report assembly for review bundles."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

from alpha_system.reports.bundle_validation import (
    BundleValidationResult,
    validate_bundle_completeness,
)
from alpha_system.reports.claim_checks import validate_no_prohibited_claims


@dataclass(frozen=True, slots=True)
class AuditReport:
    """Document-only audit report for a review bundle."""

    run_id: str
    provenance_complete: bool
    validation: BundleValidationResult
    missing_artifacts: tuple[dict[str, Any], ...]
    failed_runs: tuple[dict[str, Any], ...]
    rejected_configs: tuple[dict[str, Any], ...]
    policy_warnings: tuple[str, ...]
    review_status: str
    promotion_decision_status: str
    no_lookahead_validation_status: str
    known_limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return a stable dictionary representation."""
        payload = asdict(self)
        payload["validation"] = self.validation.to_dict()
        payload["missing_artifacts"] = [dict(item) for item in self.missing_artifacts]
        payload["failed_runs"] = [dict(item) for item in self.failed_runs]
        payload["rejected_configs"] = [dict(item) for item in self.rejected_configs]
        payload["policy_warnings"] = list(self.policy_warnings)
        payload["known_limitations"] = list(self.known_limitations)
        return payload


def build_audit_report(
    bundle: Mapping[str, Any] | Any,
    *,
    validation: BundleValidationResult | None = None,
) -> AuditReport:
    """Build a structured audit report from a review bundle."""
    payload = _mapping(bundle)
    active_validation = validation or validate_bundle_completeness(payload)
    failed_runs = tuple(_normalize_dicts(payload.get("failed_runs", ())))
    if not failed_runs:
        failed_runs = active_validation.surfaced_failed_runs
    warnings = tuple(dict.fromkeys((*_warning_messages(payload), *active_validation.warnings)))
    report = AuditReport(
        run_id=str(payload.get("run_id") or ""),
        provenance_complete=active_validation.valid,
        validation=active_validation,
        missing_artifacts=active_validation.missing_artifacts,
        failed_runs=failed_runs,
        rejected_configs=active_validation.surfaced_rejected_configs,
        policy_warnings=warnings,
        review_status=str(payload.get("review_status") or "not_reviewed"),
        promotion_decision_status=active_validation.promotion_decision_status,
        no_lookahead_validation_status=active_validation.no_lookahead_validation_status,
        known_limitations=tuple(str(item) for item in payload.get("known_limitations", ())),
    )
    validate_no_prohibited_claims(report.to_dict(), context="audit report")
    return report


def render_audit_report_markdown(report: AuditReport) -> str:
    """Render an audit report as deterministic Markdown."""
    sections = [
        f"# Audit Report: {report.run_id}",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| provenance_complete | {report.provenance_complete} |",
        f"| review_status | `{report.review_status}` |",
        f"| promotion_decision_status | `{report.promotion_decision_status}` |",
        f"| no_lookahead_validation_status | `{report.no_lookahead_validation_status}` |",
        "",
        "## Missing Artifacts",
        _json_block(report.missing_artifacts),
        "",
        "## Failed Runs",
        _json_block(report.failed_runs),
        "",
        "## Rejected Configs",
        _json_block(report.rejected_configs),
        "",
        "## Policy Warnings",
        _bullets(report.policy_warnings),
        "",
        "## Validation",
        _json_block(report.validation.to_dict()),
        "",
        "## Known Limitations",
        _bullets(report.known_limitations),
    ]
    rendered = "\n".join(sections).rstrip() + "\n"
    validate_no_prohibited_claims(rendered, context="audit report markdown")
    return rendered


def render_audit_report_csv(report: AuditReport) -> str:
    """Render an audit report as stable section/field/value CSV."""
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(("section", "field", "value"))
    writer.writerow(("metadata", "run_id", report.run_id))
    writer.writerow(("metadata", "provenance_complete", str(report.provenance_complete)))
    writer.writerow(("metadata", "review_status", report.review_status))
    writer.writerow(("metadata", "promotion_decision_status", report.promotion_decision_status))
    writer.writerow(
        (
            "metadata",
            "no_lookahead_validation_status",
            report.no_lookahead_validation_status,
        )
    )
    writer.writerow(("missing_artifacts", "items", _csv_json(report.missing_artifacts)))
    writer.writerow(("failed_runs", "items", _csv_json(report.failed_runs)))
    writer.writerow(("rejected_configs", "items", _csv_json(report.rejected_configs)))
    for warning in report.policy_warnings:
        writer.writerow(("policy_warnings", "warning", warning))
    writer.writerow(("validation", "result", _csv_json(report.validation.to_dict())))
    rendered = output.getvalue()
    validate_no_prohibited_claims(rendered, context="audit report csv")
    return rendered


def _mapping(value: Mapping[str, Any] | Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        value = value.to_dict()
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _normalize_dicts(value: Any) -> tuple[dict[str, Any], ...]:
    if value is None:
        return ()
    if isinstance(value, Mapping):
        return (dict(value),)
    if not isinstance(value, Sequence) or isinstance(value, str | bytes | bytearray):
        return ()
    output: list[dict[str, Any]] = []
    for item in value:
        if hasattr(item, "to_dict"):
            item = item.to_dict()
        if isinstance(item, Mapping):
            output.append(dict(item))
    return tuple(output)


def _warning_messages(payload: Mapping[str, Any]) -> tuple[str, ...]:
    messages: list[str] = []
    for warning in payload.get("warnings", ()) or ():
        if isinstance(warning, Mapping):
            messages.append(str(warning.get("message") or warning.get("code") or ""))
        else:
            messages.append(str(warning))
    return tuple(message for message in messages if message.strip())


def _json_block(value: Any) -> str:
    return "```json\n" + json.dumps(value, sort_keys=True, indent=2, default=str) + "\n```"


def _csv_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, default=str)


def _bullets(values: Sequence[str]) -> str:
    if not values:
        return "None recorded."
    return "\n".join(f"- {value}" for value in values)
