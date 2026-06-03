"""Release-validation report variant built from review-bundle primitives."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

from alpha_system.reports.audit_report import AuditReport, build_audit_report
from alpha_system.reports.claim_checks import validate_no_prohibited_claims
from alpha_system.reports.review_bundle import ReviewBundle


@dataclass(frozen=True, slots=True)
class ReleaseValidationReport:
    """Document-only release-validation report."""

    run_id: str
    release_validation_id: str
    audit_report: AuditReport
    bundle_summary: Mapping[str, Any]
    warnings: tuple[str, ...]
    known_limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return a stable dictionary representation."""
        payload = asdict(self)
        payload["audit_report"] = self.audit_report.to_dict()
        payload["bundle_summary"] = dict(self.bundle_summary)
        payload["warnings"] = list(self.warnings)
        payload["known_limitations"] = list(self.known_limitations)
        return payload


def build_release_validation_report(
    bundle: ReviewBundle,
    *,
    release_validation_id: str | None = None,
) -> ReleaseValidationReport:
    """Build a release-validation report without taking any release action."""
    audit = build_audit_report(bundle, validation=bundle.validation)
    warnings = tuple(
        dict.fromkeys(
            (
                "release validation report is document-only",
                *audit.policy_warnings,
            )
        )
    )
    report = ReleaseValidationReport(
        run_id=bundle.run_id,
        release_validation_id=release_validation_id or f"{bundle.run_id}:release_validation",
        audit_report=audit,
        bundle_summary=bundle.summary_dict(),
        warnings=warnings,
        known_limitations=(
            "This report does not perform release, deploy, broker, paper, or live actions.",
            "This report summarizes review evidence and local validation status only.",
        ),
    )
    validate_no_prohibited_claims(report.to_dict(), context="release validation report")
    return report


def render_release_validation_report_markdown(report: ReleaseValidationReport) -> str:
    """Render a release-validation report as deterministic Markdown."""
    sections = [
        f"# Release Validation Report: {report.release_validation_id}",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| run_id | `{report.run_id}` |",
        f"| provenance_complete | {report.audit_report.provenance_complete} |",
        f"| review_status | `{report.audit_report.review_status}` |",
        "",
        "## Bundle Summary",
        _json_block(report.bundle_summary),
        "",
        "## Audit Summary",
        _json_block(report.audit_report.to_dict()),
        "",
        "## Warnings",
        _bullets(report.warnings),
        "",
        "## Known Limitations",
        _bullets(report.known_limitations),
    ]
    rendered = "\n".join(sections).rstrip() + "\n"
    validate_no_prohibited_claims(rendered, context="release validation report markdown")
    return rendered


def _json_block(value: Any) -> str:
    return "```json\n" + json.dumps(value, sort_keys=True, indent=2, default=str) + "\n```"


def _bullets(values: tuple[str, ...]) -> str:
    if not values:
        return "None recorded."
    return "\n".join(f"- {value}" for value in values)
