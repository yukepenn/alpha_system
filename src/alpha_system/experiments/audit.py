"""Read-only registry audit for reproducibility and experiment hardening."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from alpha_system.core.registry import (
    EXPERIMENT_RUN_TABLES,
    REQUIRED_TABLES,
    connect_registry,
    table_names,
)
from alpha_system.experiments.artifact_manifest import classify_artifact_path
from alpha_system.experiments.failure_records import (
    hidden_failed_run_pattern,
    list_failed_runs,
)
from alpha_system.experiments.promotion import (
    decision_status_is_approval,
    promotion_row_has_review_trail,
)
from alpha_system.experiments.run_records import RUN_TABLE_REQUIREMENTS


@dataclass(frozen=True, slots=True)
class AuditFinding:
    """One structured registry audit finding."""

    code: str
    table_name: str
    record_id: str
    severity: str
    message: str
    details: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["details"] = dict(self.details or {})
        return payload


@dataclass(frozen=True, slots=True)
class RegistryAuditResult:
    """Structured output from a read-only registry audit."""

    findings: tuple[AuditFinding, ...]

    @property
    def clean(self) -> bool:
        return not self.findings

    def by_code(self) -> dict[str, tuple[AuditFinding, ...]]:
        grouped: dict[str, list[AuditFinding]] = {}
        for finding in self.findings:
            grouped.setdefault(finding.code, []).append(finding)
        return {code: tuple(items) for code, items in sorted(grouped.items())}

    def to_dict(self) -> dict[str, Any]:
        return {
            "clean": self.clean,
            "finding_count": len(self.findings),
            "findings": [finding.to_dict() for finding in self.findings],
            "codes": {code: len(items) for code, items in self.by_code().items()},
        }


def audit_registry(
    connection: sqlite3.Connection,
    *,
    run_requirements: Mapping[str, Mapping[str, bool]] | None = None,
) -> RegistryAuditResult:
    """Audit registry rows for missing metadata, unsafe artifacts, and review gaps."""
    requirements = run_requirements or RUN_TABLE_REQUIREMENTS
    findings: list[AuditFinding] = []
    present_tables = set(table_names(connection))
    for table in REQUIRED_TABLES:
        if table not in present_tables:
            findings.append(
                AuditFinding(
                    code="missing_table",
                    table_name=table,
                    record_id="registry",
                    severity="high",
                    message=f"required registry table is missing: {table}",
                )
            )

    for table in EXPERIMENT_RUN_TABLES:
        if table not in present_tables:
            continue
        findings.extend(_audit_run_table(connection, table, requirements.get(table, {})))

    if "artifact_manifest" in present_tables:
        findings.extend(_audit_artifact_manifest(connection))
    if "promotion_decisions" in present_tables:
        findings.extend(_audit_promotions(connection))
    return RegistryAuditResult(tuple(findings))


def audit_registry_path(path: str | Path) -> RegistryAuditResult:
    """Open a registry read-only and audit it without creating or mutating it."""
    with connect_registry(path, read_only=True) as connection:
        return audit_registry(connection)


def registry_status_audit_summary(path: str | Path) -> dict[str, Any]:
    """Best-effort audit summary for the read-only registry status CLI."""
    try:
        with connect_registry(path, read_only=True) as connection:
            result = audit_registry(connection)
            failed_runs = list_failed_runs(connection)
    except sqlite3.Error as exc:
        return {
            "audit": {"clean": False, "finding_count": 0, "skipped": True, "error": str(exc)},
            "failed_runs": {"count": 0, "run_ids": []},
            "promotion_decisions": {"approval_without_review": 0},
        }
    promotion_without_review = len(result.by_code().get("promotion_without_review", ()))
    return {
        "audit": result.to_dict(),
        "failed_runs": {
            "count": len(failed_runs),
            "run_ids": [item.run_id for item in failed_runs],
        },
        "promotion_decisions": {
            "approval_without_review": promotion_without_review,
        },
    }


def _audit_run_table(
    connection: sqlite3.Connection,
    table: str,
    requirements: Mapping[str, bool],
) -> tuple[AuditFinding, ...]:
    rows = connection.execute(
        f"""
        SELECT run_id, git_commit, code_hash, config_hash, data_version,
               factor_versions_json, label_versions_json, artifact_paths_json,
               decision_status, warnings_json, status_message
        FROM {table}
        ORDER BY run_id
        """
    ).fetchall()
    findings: list[AuditFinding] = []
    require_factor_versions = bool(requirements.get("require_factor_versions", True))
    require_label_versions = bool(requirements.get("require_label_versions", False))
    for row in rows:
        run_id = str(row["run_id"])
        if not str(row["git_commit"] or "").strip():
            findings.append(_finding("missing_git_commit", table, run_id, "git commit is missing"))
        if not str(row["code_hash"] or "").strip():
            findings.append(_finding("missing_code_hash", table, run_id, "code hash is missing"))
        if not str(row["config_hash"] or "").strip():
            findings.append(_finding("missing_config_hash", table, run_id, "config hash is missing"))
        if not str(row["data_version"] or "").strip():
            findings.append(_finding("missing_data_version", table, run_id, "data version is missing"))

        factor_versions = _loads_dict(row["factor_versions_json"])
        label_versions = _loads_dict(row["label_versions_json"])
        artifact_paths = _loads_dict(row["artifact_paths_json"])
        if require_factor_versions and not factor_versions:
            findings.append(
                _finding("missing_factor_versions", table, run_id, "factor versions are missing")
            )
        if require_label_versions and not label_versions:
            findings.append(
                _finding("missing_label_versions", table, run_id, "label versions are missing")
            )
        if not artifact_paths and not _has_manifest_artifact(connection, run_id):
            findings.append(
                _finding(
                    "missing_artifact_references",
                    table,
                    run_id,
                    "artifact references are missing",
                )
            )
        findings.extend(_audit_path_mapping(table, run_id, artifact_paths))
        if hidden_failed_run_pattern(row):
            findings.append(
                _finding(
                    "hidden_failed_run",
                    table,
                    run_id,
                    "failed run lacks visible failed-step or warning metadata",
                    severity="critical",
                )
            )
    return tuple(findings)


def _audit_artifact_manifest(connection: sqlite3.Connection) -> tuple[AuditFinding, ...]:
    rows = connection.execute(
        """
        SELECT artifact_id, run_id, artifact_path, metadata_json, status_message
        FROM artifact_manifest
        ORDER BY artifact_id
        """
    ).fetchall()
    findings: list[AuditFinding] = []
    for row in rows:
        policy = classify_artifact_path(str(row["artifact_path"]))
        if policy.forbidden:
            findings.append(
                AuditFinding(
                    code="forbidden_artifact_path",
                    table_name="artifact_manifest",
                    record_id=str(row["artifact_id"]),
                    severity="critical",
                    message="artifact manifest path violates commit/artifact policy",
                    details={"path": str(row["artifact_path"]), "warnings": list(policy.warnings)},
                )
            )
        if not policy.commit_safe and not _row_contains_warning(row, "not commit-safe"):
            findings.append(
                AuditFinding(
                    code="artifact_path_missing_warning",
                    table_name="artifact_manifest",
                    record_id=str(row["artifact_id"]),
                    severity="medium",
                    message="not-commit-safe artifact path lacks a warning",
                    details={"path": str(row["artifact_path"])},
                )
            )
    return tuple(findings)


def _audit_promotions(connection: sqlite3.Connection) -> tuple[AuditFinding, ...]:
    rows = connection.execute(
        """
        SELECT decision_id, decision_status, reviewer, rationale,
               artifact_paths_json, metadata_json
        FROM promotion_decisions
        ORDER BY decision_id
        """
    ).fetchall()
    findings: list[AuditFinding] = []
    for row in rows:
        status = str(row["decision_status"])
        if decision_status_is_approval(status) and not promotion_row_has_review_trail(row):
            findings.append(
                AuditFinding(
                    code="promotion_without_review",
                    table_name="promotion_decisions",
                    record_id=str(row["decision_id"]),
                    severity="critical",
                    message="approved promotion decision lacks review trail",
                )
            )
    return tuple(findings)


def _audit_path_mapping(
    table: str,
    run_id: str,
    artifact_paths: Mapping[str, Any],
) -> tuple[AuditFinding, ...]:
    findings: list[AuditFinding] = []
    for key, value in artifact_paths.items():
        if isinstance(value, Mapping):
            values = value.values()
        elif isinstance(value, list | tuple):
            values = value
        else:
            values = (value,)
        for path in values:
            if not isinstance(path, str):
                continue
            policy = classify_artifact_path(path)
            if policy.forbidden:
                findings.append(
                    AuditFinding(
                        code="forbidden_artifact_path",
                        table_name=table,
                        record_id=run_id,
                        severity="critical",
                        message="run artifact path violates commit/artifact policy",
                        details={
                            "artifact_key": str(key),
                            "path": path,
                            "warnings": list(policy.warnings),
                        },
                    )
                )
    return tuple(findings)


def _has_manifest_artifact(connection: sqlite3.Connection, run_id: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM artifact_manifest WHERE run_id = ? LIMIT 1",
        (run_id,),
    ).fetchone()
    return row is not None


def _row_contains_warning(row: sqlite3.Row, needle: str) -> bool:
    text = f"{row['metadata_json']} {row['status_message']}".lower()
    return needle.lower() in text


def _finding(
    code: str,
    table: str,
    record_id: str,
    message: str,
    *,
    severity: str = "high",
) -> AuditFinding:
    return AuditFinding(
        code=code,
        table_name=table,
        record_id=record_id,
        severity=severity,
        message=message,
    )


def _loads_dict(value: str) -> dict[str, Any]:
    try:
        payload = json.loads(value or "{}")
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}
