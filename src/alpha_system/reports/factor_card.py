"""Factor-card assembly and deterministic rendering."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from string import Template
from typing import Any

from alpha_system.data.fixture_policy import repository_root_from_module
from alpha_system.data.paths import assert_local_wsl_path
from alpha_system.reports.prohibited_claims import validate_no_prohibited_claims
from alpha_system.reports.report_models import (
    FactorCardReport,
    PromotionRecommendation,
    ReportMetadata,
    ReportModelError,
    ReportWarning,
    StabilitySections,
    advisory_recommendation_note,
)


DEFAULT_MIN_SAMPLE_SIZE = 30
DEFAULT_REPORT_OUTPUT_ROOT = Path("artifacts") / "reports"

_FACTOR_CARD_TEMPLATE = """# Factor Card: ${factor_id}

${advisory_note}

## Metadata
${metadata_table}

## Diagnostic Summary
${diagnostic_summary}

## Stability
${stability_sections}

## Correlation To Existing Factors
${correlation_section}

## Cluster And Recommendation
${recommendation_table}

## Warnings
${warnings_section}

## Limitations
${limitations_section}
"""


def build_factor_card(
    diagnostic_summary: Mapping[str, Any] | Any,
    *,
    reproducibility_metadata: Mapping[str, Any] | None = None,
    promotion_recommendation: str | PromotionRecommendation | None = None,
    factor_cluster_id: str | None = None,
    limitations: Sequence[str] | None = None,
    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE,
) -> FactorCardReport:
    """Assemble a factor card from diagnostics and reproducibility metadata."""
    summary = _summary_mapping(diagnostic_summary)
    metadata_payload = dict(reproducibility_metadata or {})
    diagnostics = _mapping(summary.get("diagnostics"))
    warnings = _report_warnings(summary.get("warnings", ()))

    stability, stability_warnings = _stability_sections(diagnostics)
    warnings.extend(stability_warnings)

    sample_size = _non_negative_int(summary.get("sample_size", 0), "sample_size")
    if sample_size < min_sample_size:
        warnings.append(
            ReportWarning(
                code="insufficient_sample_size",
                message=(
                    f"sample size {sample_size} is below conservative threshold "
                    f"{min_sample_size}"
                ),
            )
        )

    metadata = _metadata_from_summary(summary, metadata_payload)
    recommendation = _recommendation(
        explicit=promotion_recommendation,
        sample_size=sample_size,
        min_sample_size=min_sample_size,
        warnings=warnings,
        no_lookahead_status=metadata.no_lookahead_validation_status,
        review_status=metadata.review_status,
    )
    cluster_id = (
        factor_cluster_id
        or _text(metadata_payload.get("factor_cluster_id"))
        or _text(diagnostics.get("factor_cluster_id"))
        or "not_assigned"
    )
    correlations = _correlation_section(diagnostics)
    if not correlations:
        warnings.append(
            ReportWarning(
                code="missing_correlation_to_existing_factors",
                message="correlation to existing factors was not present in diagnostics",
            )
        )
    default_limitations = (
        "Diagnostics are descriptive evidence only.",
        "Recommendation is advisory and separate from registry status changes.",
        "Sparse, missing, or unstable sections require human review before downstream use.",
    )
    active_limitations = tuple(limitations or default_limitations)

    card = FactorCardReport(
        metadata=metadata,
        stability=stability,
        correlation_to_existing_factors=correlations,
        factor_cluster_id=cluster_id,
        promotion_recommendation=recommendation,
        sample_size=sample_size,
        warnings=tuple(_dedupe_warnings(warnings)),
        diagnostic_summary=_diagnostic_overview(summary, diagnostics),
        limitations=active_limitations,
    )
    validate_no_prohibited_claims(card.to_dict(), context="factor card")
    return card


def render_factor_card_markdown(card: FactorCardReport) -> str:
    """Render a factor card as deterministic Markdown."""
    values = {
        "factor_id": card.metadata.factor_id,
        "advisory_note": advisory_recommendation_note(),
        "metadata_table": _table(card.metadata.to_dict().items()),
        "diagnostic_summary": _json_block(card.diagnostic_summary),
        "stability_sections": _render_stability_sections(card.stability),
        "correlation_section": _json_block(card.correlation_to_existing_factors),
        "recommendation_table": _table(
            (
                ("factor_cluster_id", card.factor_cluster_id),
                ("promotion_recommendation", card.promotion_recommendation.value),
                ("sample_size", card.sample_size),
                ("recommendation_note", advisory_recommendation_note()),
            )
        ),
        "warnings_section": _render_warnings(card.warnings),
        "limitations_section": _bullets(card.limitations),
    }
    rendered = _template("factor_card.md", _FACTOR_CARD_TEMPLATE).substitute(values).rstrip() + "\n"
    validate_no_prohibited_claims(rendered, context="factor card markdown")
    return rendered


def render_factor_card_csv(card: FactorCardReport) -> str:
    """Render a factor card as stable section/field/value CSV."""
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(("section", "field", "value"))
    for field, value in card.metadata.to_dict().items():
        writer.writerow(("metadata", field, _csv_value(value)))
    writer.writerow(("recommendation", "factor_cluster_id", card.factor_cluster_id))
    writer.writerow(
        ("recommendation", "promotion_recommendation", card.promotion_recommendation.value)
    )
    writer.writerow(("recommendation", "sample_size", str(card.sample_size)))
    for field, value in card.stability.to_dict().items():
        writer.writerow(("stability", field, _csv_value(value)))
    writer.writerow(
        (
            "correlation_to_existing_factors",
            "values",
            _csv_value(card.correlation_to_existing_factors),
        )
    )
    for warning in card.warnings:
        writer.writerow(("warnings", warning.code, warning.message))
    writer.writerow(("diagnostic_summary", "values", _csv_value(card.diagnostic_summary)))
    for index, limitation in enumerate(card.limitations, start=1):
        writer.writerow(("limitations", f"limitation_{index}", limitation))
    rendered = output.getvalue()
    validate_no_prohibited_claims(rendered, context="factor card csv")
    return rendered


def write_factor_card(
    card: FactorCardReport,
    output_path: str | Path,
    *,
    output_format: str = "markdown",
) -> Path:
    """Write a factor card to a local-only Markdown or CSV path."""
    path = resolve_report_output_path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "markdown":
        payload = render_factor_card_markdown(card)
    elif output_format == "csv":
        payload = render_factor_card_csv(card)
    else:
        msg = "output_format must be markdown or csv"
        raise ReportModelError(msg)
    path.write_text(payload, encoding="utf-8")
    return path


def resolve_report_output_path(output_path: str | Path) -> Path:
    """Resolve a local-only report output path and keep repo outputs under artifacts."""
    candidate = assert_local_wsl_path(output_path)
    repo_root = repository_root_from_module()
    if _is_relative_to(candidate, repo_root):
        allowed = repo_root / DEFAULT_REPORT_OUTPUT_ROOT
        if not _is_relative_to(candidate, allowed):
            msg = "report outputs inside the repo must stay under artifacts/reports"
            raise ReportModelError(msg)
    return candidate


def default_report_output_path(filename: str) -> Path:
    """Return the conservative local-only default report path."""
    return Path(DEFAULT_REPORT_OUTPUT_ROOT) / filename


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


def _metadata_from_summary(
    summary: Mapping[str, Any],
    metadata: Mapping[str, Any],
) -> ReportMetadata:
    return ReportMetadata(
        factor_id=_required(summary, "factor_id"),
        label_id=_required(summary, "label_id"),
        data_version=_required(summary, "data_version"),
        factor_version=_required(summary, "factor_version"),
        label_version=_required(summary, "label_version"),
        run_manifest_path=(
            _text(metadata.get("run_manifest_path"))
            or _text(metadata.get("manifest_path"))
            or "not_available"
        ),
        code_hash_ref=(
            _text(metadata.get("code_hash_ref"))
            or _text(metadata.get("code_hash"))
            or "not_available"
        ),
        config_hash_ref=(
            _text(metadata.get("config_hash_ref"))
            or _text(metadata.get("config_hash"))
            or "not_available"
        ),
        diagnostic_run_id=_text(summary.get("run_id")) or "not_available",
        diagnostic_engine_version=_text(summary.get("engine_version")) or "not_available",
        no_lookahead_validation_status=(
            _text(metadata.get("no_lookahead_validation_status"))
            or _text(metadata.get("no_lookahead_status"))
            or "not_recorded"
        ),
        review_status=_text(metadata.get("review_status")) or "not_reviewed",
        factor_label_alignment_status=(
            _text(metadata.get("factor_label_alignment_status"))
            or _text(metadata.get("alignment_status"))
            or "reported_not_verified"
        ),
    )


def _stability_sections(diagnostics: Mapping[str, Any]) -> tuple[
    StabilitySections,
    list[ReportWarning],
]:
    stability_payload = _mapping(diagnostics.get("stability"))
    sections = {
        "time_of_day": _first_mapping(stability_payload, "time_of_day"),
        "session_segment": _first_mapping(stability_payload, "session_segment"),
        "monthly": _first_mapping(stability_payload, "monthly"),
        "volatility_regime": _first_mapping(
            stability_payload,
            "volatility_regime",
            "volatility",
        )
        or _first_mapping(diagnostics, "volatility_regime_stability"),
        "liquidity_regime": _first_mapping(
            stability_payload,
            "liquidity_regime",
            "liquidity",
        )
        or _first_mapping(diagnostics, "liquidity_regime_stability"),
    }
    warnings: list[ReportWarning] = []
    for name, payload in list(sections.items()):
        if not payload:
            sections[name] = {"status": "not_available"}
            warnings.append(
                ReportWarning(
                    code=f"missing_{name}_stability",
                    message=f"{name} stability was not present in diagnostics",
                )
            )
    return (
        StabilitySections(
            time_of_day=sections["time_of_day"],
            session_segment=sections["session_segment"],
            monthly=sections["monthly"],
            volatility_regime=sections["volatility_regime"],
            liquidity_regime=sections["liquidity_regime"],
        ),
        warnings,
    )


def _correlation_section(diagnostics: Mapping[str, Any]) -> dict[str, Any]:
    return (
        _first_mapping(diagnostics, "correlation_to_existing_factors")
        or _first_mapping(diagnostics, "factor_correlation")
        or _first_mapping(diagnostics, "correlations_to_existing_factors")
    )


def _diagnostic_overview(summary: Mapping[str, Any], diagnostics: Mapping[str, Any]) -> dict[str, Any]:
    overview: dict[str, Any] = {
        "study_id": summary.get("study_id", "not_available"),
        "sample_size": summary.get("sample_size", 0),
        "missing_label_count": summary.get("missing_label_count", 0),
        "missing_factor_count": summary.get("missing_factor_count", 0),
        "diagnostic_sections": sorted(str(key) for key in diagnostics),
    }
    directional = _mapping(diagnostics.get("directional"))
    if directional:
        overview["directional"] = {
            key: directional[key]
            for key in ("pearson_ic", "rank_ic", "icir")
            if key in directional
        }
    events = _mapping(diagnostics.get("events"))
    if events:
        overview["events"] = {
            key: events[key]
            for key in ("event_study", "sample_size", "false_breakout_rate")
            if key in events
        }
    buckets = _mapping(diagnostics.get("buckets"))
    if buckets:
        overview["buckets"] = {
            key: buckets[key]
            for key in ("bucket_monotonicity", "tail_expectancy", "u_shape_profile")
            if key in buckets
        }
    return overview


def _recommendation(
    *,
    explicit: str | PromotionRecommendation | None,
    sample_size: int,
    min_sample_size: int,
    warnings: Sequence[ReportWarning],
    no_lookahead_status: str,
    review_status: str,
) -> PromotionRecommendation:
    if explicit is not None:
        return PromotionRecommendation.parse(explicit)
    warning_codes = {warning.code for warning in warnings}
    if sample_size < min_sample_size or "insufficient_sample_size" in warning_codes:
        return PromotionRecommendation.NEEDS_MORE_DATA
    lowered_no_lookahead = no_lookahead_status.casefold()
    if lowered_no_lookahead not in {"pass", "passed", "ok", "not_recorded"}:
        return PromotionRecommendation.DO_NOT_PROMOTE
    lowered_review = review_status.casefold()
    if lowered_review in {"failed", "blocked", "rejected"}:
        return PromotionRecommendation.REJECT
    return PromotionRecommendation.CANDIDATE_FOR_REVIEW


def _report_warnings(raw_warnings: Any) -> list[ReportWarning]:
    output: list[ReportWarning] = []
    values = raw_warnings if isinstance(raw_warnings, Sequence) and not isinstance(raw_warnings, str) else ()
    for item in values:
        if isinstance(item, Mapping):
            message = _text(item.get("message")) or json.dumps(item, sort_keys=True, default=str)
            code = _text(item.get("code")) or _slug(message)
            severity = _text(item.get("severity")) or "warning"
        else:
            message = _text(item)
            code = _slug(message)
            severity = "warning"
        if message:
            output.append(ReportWarning(code=code, message=message, severity=severity))
    return output


def _dedupe_warnings(warnings: Sequence[ReportWarning]) -> tuple[ReportWarning, ...]:
    seen: set[tuple[str, str]] = set()
    output: list[ReportWarning] = []
    for warning in warnings:
        key = (warning.code, warning.message)
        if key not in seen:
            seen.add(key)
            output.append(warning)
    return tuple(output)


def _render_stability_sections(stability: StabilitySections) -> str:
    sections = []
    for name, payload in stability.to_dict().items():
        title = name.replace("_", " ").title()
        sections.append(f"### {title}\n{_json_block(payload)}")
    return "\n\n".join(sections)


def _render_warnings(warnings: Sequence[ReportWarning]) -> str:
    if not warnings:
        return "None recorded."
    return _table((warning.code, warning.message) for warning in warnings)


def _table(rows: Sequence[tuple[Any, Any]] | Any) -> str:
    active_rows = tuple(rows)
    output = ["| field | value |", "| --- | --- |"]
    for field, value in active_rows:
        output.append(f"| {_markdown_cell(field)} | {_markdown_cell(value)} |")
    return "\n".join(output)


def _bullets(items: Sequence[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _json_block(payload: Mapping[str, Any]) -> str:
    return "```json\n" + json.dumps(payload, sort_keys=True, indent=2, default=str) + "\n```"


def _template(name: str, fallback: str) -> Template:
    template_path = Path(__file__).resolve().parent / "templates" / name
    if template_path.is_file():
        return Template(template_path.read_text(encoding="utf-8"))
    return Template(fallback)


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _first_mapping(payload: Mapping[str, Any], *keys: str) -> dict[str, Any]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, Mapping):
            return dict(value)
    return {}


def _required(payload: Mapping[str, Any], key: str) -> str:
    value = _text(payload.get(key))
    if not value:
        msg = f"diagnostic summary missing required field: {key}"
        raise ReportModelError(msg)
    return value


def _non_negative_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        msg = f"{field_name} must be a non-negative integer"
        raise ReportModelError(msg)
    try:
        active = int(value)
    except (TypeError, ValueError) as exc:
        msg = f"{field_name} must be a non-negative integer"
        raise ReportModelError(msg) from exc
    if active < 0:
        msg = f"{field_name} must be non-negative"
        raise ReportModelError(msg)
    return active


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _slug(value: str) -> str:
    slug = "".join(char if char.isalnum() else "_" for char in value.casefold())
    collapsed = "_".join(part for part in slug.split("_") if part)
    return collapsed or "warning"


def _markdown_cell(value: Any) -> str:
    text = _csv_value(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _csv_value(value: Any) -> str:
    if isinstance(value, Mapping) or isinstance(value, (list, tuple)):
        return json.dumps(value, sort_keys=True, default=str)
    return str(value)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
