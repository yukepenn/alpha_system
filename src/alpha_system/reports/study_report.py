"""Study-report assembly and deterministic rendering."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from string import Template
from typing import Any

from alpha_system.reports.factor_card import (
    build_factor_card,
    resolve_report_output_path,
)
from alpha_system.reports.prohibited_claims import validate_no_prohibited_claims
from alpha_system.reports.report_models import (
    PromotionRecommendation,
    ReportModelError,
    ReportWarning,
    StudyFactorSummary,
    StudyReport,
    advisory_recommendation_note,
)


_STUDY_REPORT_TEMPLATE = """# Study Report: ${study_id}

${advisory_note}

## Factor Summary
${factor_summary_table}

## Warnings
${warnings_section}

## Factor Details
${factor_details}

## Limitations
${limitations_section}
"""


def build_study_report(
    diagnostic_summaries: Sequence[Mapping[str, Any] | Any],
    *,
    study_id: str | None = None,
    reproducibility_metadata: Mapping[str, Any] | None = None,
    promotion_recommendations: Mapping[str, str | PromotionRecommendation] | None = None,
    factor_cluster_ids: Mapping[str, str] | None = None,
    limitations: Sequence[str] | None = None,
    min_sample_size: int = 30,
) -> StudyReport:
    """Build a study report from one or more diagnostic summaries."""
    if not diagnostic_summaries:
        msg = "study report requires at least one diagnostic summary"
        raise ReportModelError(msg)

    metadata_payload = dict(reproducibility_metadata or {})
    recommendations = dict(promotion_recommendations or {})
    clusters = dict(factor_cluster_ids or {})
    cards = []
    summaries = []
    for diagnostic_summary in diagnostic_summaries:
        summary_mapping = _summary_mapping(diagnostic_summary)
        factor_id = str(summary_mapping.get("factor_id", "")).strip()
        if not factor_id:
            msg = "diagnostic summary missing required field: factor_id"
            raise ReportModelError(msg)
        card = build_factor_card(
            summary_mapping,
            reproducibility_metadata=_metadata_for_factor(factor_id, metadata_payload),
            promotion_recommendation=recommendations.get(factor_id),
            factor_cluster_id=clusters.get(factor_id),
            min_sample_size=min_sample_size,
        )
        cards.append(card)
        summaries.append(
            StudyFactorSummary(
                factor_id=card.metadata.factor_id,
                factor_version=card.metadata.factor_version,
                label_version=card.metadata.label_version,
                data_version=card.metadata.data_version,
                sample_size=card.sample_size,
                promotion_recommendation=card.promotion_recommendation,
                warning_count=len(card.warnings),
                no_lookahead_validation_status=card.metadata.no_lookahead_validation_status,
                review_status=card.metadata.review_status,
            )
        )

    active_study_id = study_id or _first_study_id(diagnostic_summaries) or "study_report"
    default_limitations = (
        "This report summarizes diagnostics and does not change registry status.",
        "Recommendations are advisory and require separate review before status changes.",
        "Cross-factor comparisons depend on aligned versions and surfaced warnings.",
    )
    study = StudyReport(
        study_id=active_study_id,
        factor_summaries=tuple(summaries),
        factor_cards=tuple(cards),
        warnings=_study_warnings(cards),
        limitations=tuple(limitations or default_limitations),
    )
    validate_no_prohibited_claims(study.to_dict(), context="study report")
    return study


def render_study_report_markdown(report: StudyReport) -> str:
    """Render a study report as deterministic Markdown."""
    values = {
        "study_id": report.study_id,
        "advisory_note": advisory_recommendation_note(),
        "factor_summary_table": _summary_table(report.factor_summaries),
        "warnings_section": _warnings_section(report.warnings),
        "factor_details": _factor_details(report),
        "limitations_section": _bullets(report.limitations),
    }
    rendered = _template("study_report.md", _STUDY_REPORT_TEMPLATE).substitute(values).rstrip() + "\n"
    validate_no_prohibited_claims(rendered, context="study report markdown")
    return rendered


def render_study_report_csv(report: StudyReport) -> str:
    """Render a study report as stable section/field/value CSV."""
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(("section", "field", "value"))
    writer.writerow(("metadata", "study_id", report.study_id))
    writer.writerow(("metadata", "factor_count", str(len(report.factor_summaries))))
    for item in report.factor_summaries:
        payload = item.to_dict()
        field_prefix = f"factor:{item.factor_id}"
        for field, value in payload.items():
            writer.writerow(("factor_summary", f"{field_prefix}:{field}", str(value)))
    for warning in report.warnings:
        writer.writerow(("warnings", warning.code, warning.message))
    for card in report.factor_cards:
        writer.writerow(("factor_card", card.metadata.factor_id, _csv_value(card.to_dict())))
    for index, limitation in enumerate(report.limitations, start=1):
        writer.writerow(("limitations", f"limitation_{index}", limitation))
    rendered = output.getvalue()
    validate_no_prohibited_claims(rendered, context="study report csv")
    return rendered


def write_study_report(
    report: StudyReport,
    output_path: str | Path,
    *,
    output_format: str = "markdown",
) -> Path:
    """Write a study report to a local-only Markdown or CSV path."""
    path = resolve_report_output_path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "markdown":
        payload = render_study_report_markdown(report)
    elif output_format == "csv":
        payload = render_study_report_csv(report)
    else:
        msg = "output_format must be markdown or csv"
        raise ReportModelError(msg)
    path.write_text(payload, encoding="utf-8")
    return path


def _summary_mapping(diagnostic_summary: Mapping[str, Any] | Any) -> dict[str, Any]:
    if hasattr(diagnostic_summary, "to_dict"):
        payload = diagnostic_summary.to_dict()
    elif isinstance(diagnostic_summary, Mapping):
        payload = dict(diagnostic_summary)
    else:
        msg = "diagnostic_summary must be a mapping or expose to_dict()"
        raise ReportModelError(msg)
    if isinstance(payload.get("summary"), Mapping):
        payload = dict(payload["summary"])
    return payload


def _metadata_for_factor(factor_id: str, metadata: Mapping[str, Any]) -> dict[str, Any]:
    output = {
        key: value
        for key, value in metadata.items()
        if key not in {"factors", factor_id} and not isinstance(value, Mapping)
    }
    by_factor = metadata.get("factors")
    if isinstance(by_factor, Mapping) and isinstance(by_factor.get(factor_id), Mapping):
        output.update(dict(by_factor[factor_id]))
    if isinstance(metadata.get(factor_id), Mapping):
        output.update(dict(metadata[factor_id]))
    return output


def _first_study_id(diagnostic_summaries: Sequence[Mapping[str, Any] | Any]) -> str:
    first = _summary_mapping(diagnostic_summaries[0])
    return str(first.get("study_id", "")).strip()


def _study_warnings(cards: Sequence[Any]) -> tuple[ReportWarning, ...]:
    total_warnings = sum(len(card.warnings) for card in cards)
    if not total_warnings:
        return ()
    return (
        ReportWarning(
            code="factor_card_warnings_present",
            message=f"{total_warnings} factor-card warnings require review",
        ),
    )


def _summary_table(items: Sequence[StudyFactorSummary]) -> str:
    rows = [
        (
            "factor_id",
            "factor_version",
            "label_version",
            "data_version",
            "sample_size",
            "promotion_recommendation",
            "warning_count",
            "no_lookahead_validation_status",
            "review_status",
        )
    ]
    for item in items:
        payload = item.to_dict()
        rows.append(tuple(str(payload[column]) for column in rows[0]))
    header = "| " + " | ".join(rows[0]) + " |"
    separator = "| " + " | ".join("---" for _ in rows[0]) + " |"
    body = ["| " + " | ".join(_markdown_cell(value) for value in row) + " |" for row in rows[1:]]
    return "\n".join([header, separator, *body])


def _warnings_section(warnings: Sequence[ReportWarning]) -> str:
    if not warnings:
        return "None recorded."
    output = ["| code | message |", "| --- | --- |"]
    for warning in warnings:
        output.append(f"| {_markdown_cell(warning.code)} | {_markdown_cell(warning.message)} |")
    return "\n".join(output)


def _factor_details(report: StudyReport) -> str:
    sections = []
    for card in report.factor_cards:
        sections.append(
            "### "
            + card.metadata.factor_id
            + "\n"
            + "```json\n"
            + json.dumps(card.to_dict(), sort_keys=True, indent=2, default=str)
            + "\n```"
        )
    return "\n\n".join(sections)


def _bullets(items: Sequence[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _template(name: str, fallback: str) -> Template:
    template_path = Path(__file__).resolve().parent / "templates" / name
    if template_path.is_file():
        return Template(template_path.read_text(encoding="utf-8"))
    return Template(fallback)


def _markdown_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _csv_value(value: Any) -> str:
    if isinstance(value, Mapping) or isinstance(value, (list, tuple)):
        return json.dumps(value, sort_keys=True, default=str)
    return str(value)
