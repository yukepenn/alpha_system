"""Review-bundle assembly and local-only writing."""

from __future__ import annotations

import csv
import io
import json
import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from alpha_system.core.registry import (
    EXPERIMENT_RUN_TABLES,
    connect_registry,
    table_names,
)
from alpha_system.data.fixture_policy import repository_root_from_module
from alpha_system.data.paths import assert_local_wsl_path
from alpha_system.experiments.artifact_manifest import (
    classify_artifact_path,
    read_artifact_manifest,
)
from alpha_system.experiments.failure_records import list_failed_runs
from alpha_system.experiments.registry import get_run_record
from alpha_system.experiments.run_records import parse_status_payload
from alpha_system.reports.audit_report import (
    build_audit_report,
    render_audit_report_csv,
    render_audit_report_markdown,
)
from alpha_system.reports.bundle_validation import (
    BundleValidationResult,
    validate_bundle_completeness,
)
from alpha_system.reports.claim_checks import validate_no_prohibited_claims
from alpha_system.reports.source_map import (
    SourceMap,
    build_source_map,
    render_source_map_csv,
    render_source_map_markdown,
)


DEFAULT_REVIEW_BUNDLE_ROOT = Path("artifacts") / "review_bundles"
SUMMARY_FILENAME = "review_bundle_summary.json"


@dataclass(frozen=True, slots=True)
class ReviewBundleWarning:
    """A normalized warning surfaced by a review bundle."""

    code: str
    message: str
    severity: str = "warning"

    def to_dict(self) -> dict[str, str]:
        """Return a stable dictionary representation."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ReviewBundle:
    """In-memory review bundle model."""

    run_id: str
    bundle_type: str
    run_manifest: Mapping[str, Any]
    source_map: SourceMap
    config_hashes: Mapping[str, str]
    code_hashes: Mapping[str, str]
    versions: Mapping[str, Any]
    registry_records: tuple[dict[str, Any], ...]
    diagnostics_summary: Mapping[str, Any]
    backtest_summary: Mapping[str, Any]
    cost_sensitivity: Mapping[str, Any]
    monthly_breakdown: Mapping[str, Any]
    rejected_configs: tuple[dict[str, Any], ...]
    warnings: tuple[ReviewBundleWarning, ...]
    failed_steps: tuple[dict[str, Any], ...]
    failed_runs: tuple[dict[str, Any], ...]
    promotion_decision_status: str
    no_lookahead_validation_status: str
    artifact_manifest: Mapping[str, Any]
    missing_artifacts: tuple[dict[str, Any], ...]
    known_limitations: tuple[str, ...]
    review_status: str
    validation: BundleValidationResult

    def to_dict(self) -> dict[str, Any]:
        """Return a stable dictionary representation."""
        return {
            "run_id": self.run_id,
            "bundle_type": self.bundle_type,
            "run_manifest": dict(self.run_manifest),
            "source_map": self.source_map.to_dict(),
            "config_hashes": dict(self.config_hashes),
            "code_hashes": dict(self.code_hashes),
            "versions": dict(self.versions),
            "registry_records": [dict(item) for item in self.registry_records],
            "diagnostics_summary": dict(self.diagnostics_summary),
            "backtest_summary": dict(self.backtest_summary),
            "cost_sensitivity": dict(self.cost_sensitivity),
            "monthly_breakdown": dict(self.monthly_breakdown),
            "rejected_configs": [dict(item) for item in self.rejected_configs],
            "warnings": [warning.to_dict() for warning in self.warnings],
            "failed_steps": [dict(item) for item in self.failed_steps],
            "failed_runs": [dict(item) for item in self.failed_runs],
            "promotion_decision_status": self.promotion_decision_status,
            "no_lookahead_validation_status": self.no_lookahead_validation_status,
            "artifact_manifest": dict(self.artifact_manifest),
            "missing_artifacts": [dict(item) for item in self.missing_artifacts],
            "known_limitations": list(self.known_limitations),
            "review_status": self.review_status,
            "validation": self.validation.to_dict(),
        }

    def summary_dict(self) -> dict[str, Any]:
        """Return a tiny deterministic summary suitable for local inspection."""
        return {
            "run_id": self.run_id,
            "bundle_type": self.bundle_type,
            "review_status": self.review_status,
            "promotion_decision_status": self.promotion_decision_status,
            "no_lookahead_validation_status": self.no_lookahead_validation_status,
            "versions": dict(self.versions),
            "config_hashes": dict(self.config_hashes),
            "code_hashes": dict(self.code_hashes),
            "warning_count": len(self.warnings),
            "missing_artifact_count": len(self.missing_artifacts),
            "failed_run_count": len(self.failed_runs),
            "rejected_config_count": len(self.rejected_configs),
            "source_file_count": len(self.source_map.source_files),
            "config_file_count": len(self.source_map.config_files),
            "test_file_count": len(self.source_map.test_files),
            "validation": self.validation.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class ReviewBundleWriteResult:
    """Paths written by the local-only review-bundle writer."""

    output_dir: str
    files: Mapping[str, str]

    def to_dict(self) -> dict[str, Any]:
        """Return a stable dictionary representation."""
        return {"output_dir": self.output_dir, "files": dict(self.files)}


def build_review_bundle(
    *,
    run_id: str,
    registry_records: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None = None,
    artifact_manifest: Mapping[str, Any] | Sequence[Mapping[str, Any]] | str | Path | None = None,
    run_manifest: Mapping[str, Any] | str | Path | None = None,
    report_config: Mapping[str, Any] | None = None,
    registry_path: str | Path | None = None,
    source_root: str | Path | None = None,
) -> ReviewBundle:
    """Assemble an in-memory review bundle from explicit inputs."""
    active_run_id = _require_text(run_id, "run_id")
    config = dict(report_config or {})
    root = assert_local_wsl_path(source_root or repository_root_from_module())
    warnings: list[ReviewBundleWarning] = []

    registry_payload = _registry_payload(
        active_run_id,
        registry_path=registry_path,
        explicit_records=registry_records,
    )
    warnings.extend(registry_payload["warnings"])
    run_records = tuple(registry_payload["run_records"])
    promotion_decisions = tuple(registry_payload["promotion_decisions"])
    registry_artifacts = tuple(registry_payload["artifact_manifest"])
    failed_runs = tuple(registry_payload["failed_runs"])

    manifest_payload = _load_run_manifest(run_manifest)
    if not manifest_payload["path"] and run_records:
        manifest_payload = _manifest_from_run_record(run_records[0])
    if not manifest_payload["path"]:
        warnings.append(
            ReviewBundleWarning(
                code="run_manifest_missing",
                message="run manifest path was not provided or discoverable",
            )
        )

    artifact_payload = _load_artifact_manifest(artifact_manifest)
    artifact_entries = tuple(artifact_payload["entries"]) + registry_artifacts
    if not artifact_entries:
        warnings.append(
            ReviewBundleWarning(
                code="artifact_manifest_missing",
                message="artifact manifest entries were not provided or discoverable",
            )
        )

    normalized_artifacts, artifact_warnings = _normalize_artifacts(artifact_entries, root)
    warnings.extend(artifact_warnings)
    missing_artifacts = tuple(entry for entry in normalized_artifacts if entry.get("exists") is False)
    for entry in missing_artifacts:
        warnings.append(
            ReviewBundleWarning(
                code="missing_artifact",
                message=f"missing artifact surfaced: {entry.get('artifact_path') or entry.get('path')}",
            )
        )

    failed_steps = _failed_steps(run_records, manifest_payload["payload"])
    if failed_runs or failed_steps:
        warnings.append(
            ReviewBundleWarning(
                code="failed_run_visibility",
                message="failed runs or failed steps are surfaced in the bundle",
            )
        )

    rejected_configs = _rejected_configs(manifest_payload["payload"], run_records)
    if rejected_configs:
        warnings.append(
            ReviewBundleWarning(
                code="rejected_config_visibility",
                message="rejected configs are surfaced in the bundle",
            )
        )

    versions = _versions(manifest_payload["payload"], run_records, config)
    config_hashes = _hashes("config_hash", manifest_payload["payload"], run_records, config)
    code_hashes = _hashes("code_hash", manifest_payload["payload"], run_records, config)
    promotion_status = _promotion_status(
        manifest_payload["payload"],
        run_records,
        promotion_decisions,
    )
    review_status = _first_text(
        config.get("review_status"),
        manifest_payload["payload"].get("review_status"),
        _metadata_value(run_records, "review_status"),
        default="not_reviewed",
    )
    no_lookahead_status = _first_text(
        config.get("no_lookahead_validation_status"),
        manifest_payload["payload"].get("no_lookahead_validation_status"),
        _metadata_value(run_records, "no_lookahead_validation_status"),
        default="not_recorded",
    )
    source_map = build_source_map(
        run_id=active_run_id,
        source_root=root,
        run_manifest_path=manifest_payload["path"] or None,
        registry_record_reference=registry_payload["reference"],
        artifact_references=normalized_artifacts,
        source_patterns=_sequence_text(config.get("source_patterns")) or None,
        config_patterns=_sequence_text(config.get("config_patterns")) or None,
        test_patterns=_sequence_text(config.get("test_patterns")) or None,
    )

    bundle_payload: dict[str, Any] = {
        "run_id": active_run_id,
        "bundle_type": str(config.get("bundle_type") or "review_bundle"),
        "run_manifest": _manifest_section(manifest_payload),
        "source_map": source_map.to_dict(),
        "config_hashes": config_hashes,
        "code_hashes": code_hashes,
        "versions": versions,
        "registry_records": run_records,
        "diagnostics_summary": _section(manifest_payload["payload"], "diagnostics_summary"),
        "backtest_summary": _section(manifest_payload["payload"], "backtest_summary"),
        "cost_sensitivity": _section(manifest_payload["payload"], "cost_sensitivity"),
        "monthly_breakdown": _section(manifest_payload["payload"], "monthly_breakdown"),
        "rejected_configs": rejected_configs,
        "warnings": [warning.to_dict() for warning in _dedupe_warnings(warnings)],
        "failed_steps": failed_steps,
        "failed_runs": failed_runs,
        "promotion_decision_status": promotion_status,
        "no_lookahead_validation_status": no_lookahead_status,
        "artifact_manifest": {
            "path": artifact_payload["path"],
            "entries": normalized_artifacts,
        },
        "missing_artifacts": missing_artifacts,
        "known_limitations": tuple(
            _sequence_text(config.get("known_limitations"))
            or (
                "The bundle is inspection evidence only.",
                "The bundle does not mutate registry or promotion state.",
                "Missing, failed, and rejected evidence is surfaced for review.",
            )
        ),
        "review_status": review_status,
    }
    validation = validate_bundle_completeness(bundle_payload)
    bundle = ReviewBundle(
        run_id=active_run_id,
        bundle_type=str(bundle_payload["bundle_type"]),
        run_manifest=bundle_payload["run_manifest"],
        source_map=source_map,
        config_hashes=config_hashes,
        code_hashes=code_hashes,
        versions=versions,
        registry_records=tuple(run_records),
        diagnostics_summary=bundle_payload["diagnostics_summary"],
        backtest_summary=bundle_payload["backtest_summary"],
        cost_sensitivity=bundle_payload["cost_sensitivity"],
        monthly_breakdown=bundle_payload["monthly_breakdown"],
        rejected_configs=tuple(rejected_configs),
        warnings=tuple(_dedupe_warnings(warnings)),
        failed_steps=tuple(failed_steps),
        failed_runs=tuple(failed_runs),
        promotion_decision_status=promotion_status,
        no_lookahead_validation_status=no_lookahead_status,
        artifact_manifest=bundle_payload["artifact_manifest"],
        missing_artifacts=tuple(missing_artifacts),
        known_limitations=tuple(bundle_payload["known_limitations"]),
        review_status=review_status,
        validation=validation,
    )
    validate_no_prohibited_claims(bundle.to_dict(), context="review bundle")
    return bundle


def render_review_bundle_markdown(bundle: ReviewBundle) -> str:
    """Render a review bundle as deterministic Markdown."""
    sections = [
        f"# Review Bundle: {bundle.run_id}",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| bundle_type | `{bundle.bundle_type}` |",
        f"| review_status | `{bundle.review_status}` |",
        f"| promotion_decision_status | `{bundle.promotion_decision_status}` |",
        f"| no_lookahead_validation_status | `{bundle.no_lookahead_validation_status}` |",
        "",
        "## Versions",
        _json_block(bundle.versions),
        "",
        "## Hashes",
        _json_block({"config_hashes": bundle.config_hashes, "code_hashes": bundle.code_hashes}),
        "",
        "## Registry Records",
        _json_block(bundle.registry_records),
        "",
        "## Diagnostics Summary",
        _json_block(bundle.diagnostics_summary),
        "",
        "## Backtest Summary",
        _json_block(bundle.backtest_summary),
        "",
        "## Cost Sensitivity",
        _json_block(bundle.cost_sensitivity),
        "",
        "## Monthly Breakdown",
        _json_block(bundle.monthly_breakdown),
        "",
        "## Rejected Configs",
        _json_block(bundle.rejected_configs),
        "",
        "## Missing Artifacts",
        _json_block(bundle.missing_artifacts),
        "",
        "## Failed Runs",
        _json_block(bundle.failed_runs),
        "",
        "## Failed Steps",
        _json_block(bundle.failed_steps),
        "",
        "## Warnings",
        _warnings_table(bundle.warnings),
        "",
        "## Validation",
        _json_block(bundle.validation.to_dict()),
        "",
        "## Known Limitations",
        _bullets(bundle.known_limitations),
    ]
    rendered = "\n".join(sections).rstrip() + "\n"
    validate_no_prohibited_claims(rendered, context="review bundle markdown")
    return rendered


def render_review_bundle_csv(bundle: ReviewBundle) -> str:
    """Render a bundle summary as stable section/field/value CSV."""
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(("section", "field", "value"))
    writer.writerow(("metadata", "run_id", bundle.run_id))
    writer.writerow(("metadata", "bundle_type", bundle.bundle_type))
    writer.writerow(("metadata", "review_status", bundle.review_status))
    writer.writerow(("metadata", "promotion_decision_status", bundle.promotion_decision_status))
    writer.writerow(
        (
            "metadata",
            "no_lookahead_validation_status",
            bundle.no_lookahead_validation_status,
        )
    )
    for field, value in bundle.versions.items():
        writer.writerow(("versions", field, _csv_json(value)))
    writer.writerow(("hashes", "config_hashes", _csv_json(bundle.config_hashes)))
    writer.writerow(("hashes", "code_hashes", _csv_json(bundle.code_hashes)))
    for warning in bundle.warnings:
        writer.writerow(("warnings", warning.code, warning.message))
    writer.writerow(("validation", "result", _csv_json(bundle.validation.to_dict())))
    rendered = output.getvalue()
    validate_no_prohibited_claims(rendered, context="review bundle csv")
    return rendered


def write_review_bundle(
    bundle: ReviewBundle,
    output_dir: str | Path | None = None,
    *,
    include_html: bool = False,
) -> ReviewBundleWriteResult:
    """Write a local-only Markdown/CSV review bundle directory."""
    root = resolve_review_bundle_output_dir(output_dir, run_id=bundle.run_id)
    root.mkdir(parents=True, exist_ok=True)
    audit = build_audit_report(bundle, validation=bundle.validation)
    files = {
        SUMMARY_FILENAME: _write_text(
            root / SUMMARY_FILENAME,
            json.dumps(bundle.summary_dict(), sort_keys=True, indent=2, default=str) + "\n",
        ),
        "review_bundle.md": _write_text(root / "review_bundle.md", render_review_bundle_markdown(bundle)),
        "review_bundle.csv": _write_text(root / "review_bundle.csv", render_review_bundle_csv(bundle)),
        "source_map.md": _write_text(root / "source_map.md", render_source_map_markdown(bundle.source_map)),
        "source_map.csv": _write_text(root / "source_map.csv", render_source_map_csv(bundle.source_map)),
        "audit_report.md": _write_text(root / "audit_report.md", render_audit_report_markdown(audit)),
        "audit_report.csv": _write_text(root / "audit_report.csv", render_audit_report_csv(audit)),
    }
    if include_html:
        files["index.html"] = _write_text(root / "index.html", _static_html(bundle, audit.to_dict()))
    return ReviewBundleWriteResult(
        output_dir=root.as_posix(),
        files={key: path.as_posix() for key, path in sorted(files.items())},
    )


def resolve_review_bundle_output_dir(
    output_dir: str | Path | None,
    *,
    run_id: str,
) -> Path:
    """Resolve a local-only output directory for generated review bundles."""
    candidate = assert_local_wsl_path(output_dir or DEFAULT_REVIEW_BUNDLE_ROOT / _safe_name(run_id))
    repo_root = repository_root_from_module()
    if _is_relative_to(candidate, repo_root):
        allowed = repo_root / DEFAULT_REVIEW_BUNDLE_ROOT
        if not _is_relative_to(candidate, allowed):
            raise ValueError("review bundle outputs inside the repo must stay under artifacts/review_bundles")
    return candidate


def _registry_payload(
    run_id: str,
    *,
    registry_path: str | Path | None,
    explicit_records: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None,
) -> dict[str, Any]:
    warnings: list[ReviewBundleWarning] = []
    run_records = list(_normalize_records(explicit_records))
    artifact_rows: list[dict[str, Any]] = []
    failed_runs: list[dict[str, Any]] = []
    promotion_decisions: list[dict[str, Any]] = []
    reference = "not_available"
    if registry_path is None:
        if not run_records:
            warnings.append(
                ReviewBundleWarning(
                    code="registry_not_provided",
                    message="registry path was not provided; only explicit records are available",
                )
            )
        return {
            "run_records": tuple(run_records),
            "artifact_manifest": tuple(artifact_rows),
            "failed_runs": tuple(failed_runs),
            "promotion_decisions": tuple(promotion_decisions),
            "warnings": tuple(warnings),
            "reference": reference,
        }

    path = assert_local_wsl_path(registry_path)
    reference = path.as_posix()
    if not path.exists():
        warnings.append(
            ReviewBundleWarning(
                code="registry_missing",
                message=f"registry path does not exist: {path.as_posix()}",
            )
        )
        return {
            "run_records": tuple(run_records),
            "artifact_manifest": tuple(artifact_rows),
            "failed_runs": tuple(failed_runs),
            "promotion_decisions": tuple(promotion_decisions),
            "warnings": tuple(warnings),
            "reference": reference,
        }

    try:
        with connect_registry(path, read_only=True) as connection:
            present_tables = set(table_names(connection))
            for table in EXPERIMENT_RUN_TABLES:
                if table not in present_tables:
                    continue
                record = get_run_record(connection, table, run_id)
                if record is not None:
                    run_records.append(_run_record_dict(table, record))
            if "artifact_manifest" in present_tables:
                artifact_rows.extend(read_artifact_manifest(connection, run_id=run_id))
            failed_runs.extend(item.to_dict() for item in list_failed_runs(connection))
            if "promotion_decisions" in present_tables:
                promotion_decisions.extend(_read_promotion_decisions(connection, run_id))
    except sqlite3.Error as exc:
        warnings.append(
            ReviewBundleWarning(
                code="registry_read_failed",
                message=f"registry read failed: {exc}",
            )
        )
    return {
        "run_records": tuple(run_records),
        "artifact_manifest": tuple(artifact_rows),
        "failed_runs": tuple(failed_runs),
        "promotion_decisions": tuple(promotion_decisions),
        "warnings": tuple(warnings),
        "reference": reference,
    }


def _read_promotion_decisions(connection: sqlite3.Connection, run_id: str) -> tuple[dict[str, Any], ...]:
    rows = connection.execute(
        """
        SELECT decision_id, subject_type, subject_id, subject_version, run_id,
               decision_status, decided_at, reviewer, rationale,
               artifact_paths_json, metadata_json, status_message
        FROM promotion_decisions
        WHERE run_id = ?
        ORDER BY decision_id
        """,
        (run_id,),
    ).fetchall()
    output: list[dict[str, Any]] = []
    for row in rows:
        payload = dict(row)
        payload["artifact_paths"] = _loads_mapping(payload.pop("artifact_paths_json", "{}"))
        payload["metadata"] = _loads_mapping(payload.pop("metadata_json", "{}"))
        output.append(payload)
    return tuple(output)


def _run_record_dict(table: str, record: Any) -> dict[str, Any]:
    payload = asdict(record)
    payload["table_name"] = table
    payload["failed_steps"] = parse_status_payload(str(payload.get("status_message") or ""))[
        "failed_steps"
    ]
    return payload


def _load_run_manifest(value: Mapping[str, Any] | str | Path | None) -> dict[str, Any]:
    if value is None:
        return {"path": "", "exists": False, "payload": {}}
    if isinstance(value, Mapping):
        return {
            "path": str(value.get("path") or value.get("run_manifest_path") or ""),
            "exists": True,
            "payload": dict(value),
        }
    path = assert_local_wsl_path(value)
    if not path.exists():
        return {"path": path.as_posix(), "exists": False, "payload": {}}
    return {"path": path.as_posix(), "exists": True, "payload": _read_json_mapping(path)}


def _load_artifact_manifest(
    value: Mapping[str, Any] | Sequence[Mapping[str, Any]] | str | Path | None,
) -> dict[str, Any]:
    if value is None:
        return {"path": "", "entries": ()}
    if isinstance(value, Mapping):
        entries = value.get("entries")
        if entries is None and any(key in value for key in ("artifact_path", "path", "relative_path")):
            entries = (value,)
        return {"path": str(value.get("path") or ""), "entries": tuple(_normalize_records(entries))}
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return {"path": "", "entries": tuple(_normalize_records(value))}
    path = assert_local_wsl_path(value)
    if not path.exists():
        return {
            "path": path.as_posix(),
            "entries": (
                {
                    "artifact_key": "artifact_manifest",
                    "artifact_path": path.as_posix(),
                    "exists": False,
                    "warnings": ("artifact manifest file is missing",),
                },
            ),
        }
    payload = _read_json(path)
    if isinstance(payload, Mapping):
        entries = payload.get("entries", payload.get("artifacts", ()))
        if not entries and any(key in payload for key in ("artifact_path", "path", "relative_path")):
            entries = (payload,)
    elif isinstance(payload, Sequence) and not isinstance(payload, str | bytes | bytearray):
        entries = payload
    else:
        entries = ()
    return {"path": path.as_posix(), "entries": tuple(_normalize_records(entries))}


def _normalize_artifacts(
    entries: Sequence[Mapping[str, Any]],
    root: Path,
) -> tuple[tuple[dict[str, Any], ...], tuple[ReviewBundleWarning, ...]]:
    normalized: list[dict[str, Any]] = []
    warnings: list[ReviewBundleWarning] = []
    for entry in entries:
        payload = dict(entry)
        path = str(
            payload.get("artifact_path")
            or payload.get("path")
            or payload.get("relative_path")
            or ""
        )
        if not path:
            warnings.append(
                ReviewBundleWarning(
                    code="artifact_path_missing",
                    message="artifact manifest entry is missing a path",
                )
            )
            continue
        candidate = Path(path)
        resolved = candidate if candidate.is_absolute() else root / candidate
        exists = bool(payload.get("exists")) if "exists" in payload else resolved.is_file()
        policy = classify_artifact_path(path)
        entry_warnings = list(payload.get("warnings", ()) or ())
        entry_warnings.extend(policy.warnings)
        if not exists:
            entry_warnings.append("artifact file is missing")
        if policy.forbidden:
            warnings.append(
                ReviewBundleWarning(
                    code="artifact_policy_warning",
                    message=f"artifact path policy warning surfaced: {path}",
                )
            )
        payload.update(
            {
                "artifact_key": str(
                    payload.get("artifact_key")
                    or payload.get("artifact_role")
                    or payload.get("artifact_type")
                    or "artifact"
                ),
                "artifact_path": path,
                "exists": exists,
                "path_policy": policy.to_dict(),
                "warnings": tuple(dict.fromkeys(str(item) for item in entry_warnings if str(item).strip())),
            }
        )
        normalized.append(payload)
    sorted_entries = sorted(
        normalized,
        key=lambda item: (str(item["artifact_key"]), str(item["artifact_path"])),
    )
    return tuple(sorted_entries), tuple(warnings)


def _manifest_from_run_record(record: Mapping[str, Any]) -> dict[str, Any]:
    artifact_paths = record.get("artifact_paths")
    if isinstance(artifact_paths, Mapping):
        for key in ("manifest", "run_manifest", "run_manifest_path"):
            if key in artifact_paths:
                return {
                    "path": str(artifact_paths[key]),
                    "exists": False,
                    "payload": {"run_id": record.get("run_id"), **dict(record)},
                }
    return {"path": "", "exists": False, "payload": {"run_id": record.get("run_id"), **dict(record)}}


def _manifest_section(manifest_payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "path": str(manifest_payload.get("path") or ""),
        "exists": bool(manifest_payload.get("exists")),
        "payload": dict(manifest_payload.get("payload") or {}),
    }


def _versions(
    manifest: Mapping[str, Any],
    run_records: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    first = run_records[0] if run_records else {}
    return {
        "data_version": _first_text(
            config.get("data_version"),
            manifest.get("data_version"),
            first.get("data_version"),
            default="",
        ),
        "factor_versions": _first_mapping(
            config.get("factor_versions"),
            manifest.get("factor_versions"),
            first.get("factor_versions"),
        ),
        "label_versions": _first_mapping(
            config.get("label_versions"),
            manifest.get("label_versions"),
            first.get("label_versions"),
        ),
        "engine_version": _first_text(
            config.get("engine_version"),
            manifest.get("engine_version"),
            first.get("engine_version"),
            default="",
        ),
    }


def _hashes(
    field: str,
    manifest: Mapping[str, Any],
    run_records: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
) -> dict[str, str]:
    configured = config.get(f"{field}es")
    if isinstance(configured, Mapping):
        return {str(key): str(value) for key, value in sorted(configured.items())}
    first = run_records[0] if run_records else {}
    value = _first_text(config.get(field), manifest.get(field), first.get(field), default="")
    if not value:
        return {}
    return {field: value}


def _promotion_status(
    manifest: Mapping[str, Any],
    run_records: Sequence[Mapping[str, Any]],
    promotion_decisions: Sequence[Mapping[str, Any]],
) -> str:
    if promotion_decisions:
        statuses = sorted({str(item.get("decision_status") or "") for item in promotion_decisions})
        return ",".join(status for status in statuses if status) or "recorded_without_status"
    first = run_records[0] if run_records else {}
    return _first_text(
        manifest.get("promotion_decision_status"),
        manifest.get("promotion_decision"),
        first.get("promotion_decision_status"),
        default="not_recorded",
    )


def _failed_steps(
    run_records: Sequence[Mapping[str, Any]],
    manifest: Mapping[str, Any],
) -> tuple[dict[str, Any], ...]:
    output: list[dict[str, Any]] = []
    for item in manifest.get("failed_steps", ()) or ():
        if isinstance(item, Mapping):
            output.append(dict(item))
    for record in run_records:
        for step in record.get("failed_steps", ()) or ():
            if isinstance(step, Mapping):
                output.append(dict(step))
    return tuple(output)


def _rejected_configs(
    manifest: Mapping[str, Any],
    run_records: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
    output: list[dict[str, Any]] = []
    for item in manifest.get("rejected_configs", ()) or ():
        if isinstance(item, Mapping):
            output.append(dict(item))
    for record in run_records:
        parameters = record.get("parameters")
        if isinstance(parameters, Mapping):
            for item in parameters.get("rejected_configs", ()) or ():
                if isinstance(item, Mapping):
                    output.append(dict(item))
    return tuple(output)


def _section(manifest: Mapping[str, Any], key: str) -> dict[str, Any]:
    value = manifest.get(key, {})
    return dict(value) if isinstance(value, Mapping) else {}


def _metadata_value(run_records: Sequence[Mapping[str, Any]], key: str) -> str:
    for record in run_records:
        parameters = record.get("parameters")
        if isinstance(parameters, Mapping) and key in parameters:
            return str(parameters[key])
    return ""


def _normalize_records(
    records: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None,
) -> tuple[dict[str, Any], ...]:
    if records is None:
        return ()
    if isinstance(records, Mapping):
        return (dict(records),)
    output: list[dict[str, Any]] = []
    for item in records:
        if isinstance(item, Mapping):
            output.append(dict(item))
    return tuple(output)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_json_mapping(path: Path) -> dict[str, Any]:
    payload = _read_json(path)
    return dict(payload) if isinstance(payload, Mapping) else {}


def _loads_mapping(value: str) -> dict[str, Any]:
    try:
        payload = json.loads(value or "{}")
    except json.JSONDecodeError:
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _sequence_text(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if not isinstance(value, Sequence):
        return ()
    return tuple(str(item) for item in value if str(item).strip())


def _first_mapping(*values: Any) -> dict[str, str]:
    for value in values:
        if isinstance(value, Mapping) and value:
            return {str(key): str(val) for key, val in sorted(value.items())}
    return {}


def _first_text(*values: Any, default: str) -> str:
    for value in values:
        if isinstance(value, Mapping):
            continue
        text = str(value or "").strip()
        if text:
            return text
    return default


def _dedupe_warnings(warnings: Sequence[ReviewBundleWarning]) -> tuple[ReviewBundleWarning, ...]:
    output: dict[tuple[str, str], ReviewBundleWarning] = {}
    for warning in warnings:
        output[(warning.code, warning.message)] = warning
    return tuple(output[key] for key in sorted(output))


def _require_text(value: str, field_name: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    return text


def _safe_name(value: str) -> str:
    safe = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in value)
    return safe or "review_bundle"


def _write_text(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def _json_block(value: Any) -> str:
    return "```json\n" + json.dumps(value, sort_keys=True, indent=2, default=str) + "\n```"


def _csv_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, default=str)


def _warnings_table(warnings: Sequence[ReviewBundleWarning]) -> str:
    if not warnings:
        return "None recorded."
    rows = ["| code | severity | message |", "| --- | --- | --- |"]
    for warning in warnings:
        rows.append(f"| `{warning.code}` | `{warning.severity}` | {warning.message} |")
    return "\n".join(rows)


def _bullets(values: Sequence[str]) -> str:
    if not values:
        return "None recorded."
    return "\n".join(f"- {value}" for value in values)


def _static_html(bundle: ReviewBundle, audit_payload: Mapping[str, Any]) -> str:
    payload = {
        "summary": bundle.summary_dict(),
        "audit": dict(audit_payload),
    }
    body = json.dumps(payload, sort_keys=True, indent=2, default=str)
    return (
        "<!doctype html>\n"
        "<html><head><meta charset=\"utf-8\"><title>Review Bundle</title></head>"
        "<body><pre>"
        + body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        + "</pre></body></html>\n"
    )


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
