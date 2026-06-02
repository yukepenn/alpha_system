"""SQLite-backed factor registry helpers."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from alpha_system.core.git_info import capture_git_info
from alpha_system.core.hashing import canonical_json, hash_config
from alpha_system.core.registry import connect_registry, init_registry
from alpha_system.factors.spec import FactorSpec


class FactorRegistryError(ValueError):
    """Raised when factor registry operations violate registry policy."""


REVIEWED_VALIDATION_STATUSES: frozenset[str] = frozenset(
    {
        "accepted",
        "approved",
        "pass",
        "pass_with_warnings",
        "reviewed",
        "validated",
    }
)

REVIEW_BACKED_PROMOTION_STATUSES: frozenset[str] = frozenset(
    {
        "accepted",
        "approved",
        "pass",
        "pass_with_warnings",
    }
)


def register_factor_spec(
    registry_path: str | Path,
    spec: FactorSpec,
    *,
    status_message: str = "factor spec validation",
) -> None:
    """Register a factor identity and unique factor version."""
    registry = _init_valid_registry(registry_path)
    git_info = capture_git_info(Path.cwd())
    with connect_registry(registry) as connection:
        if factor_version_exists(connection, spec.factor_id, spec.version):
            msg = f"factor version already exists: {spec.factor_id} {spec.version}"
            raise FactorRegistryError(msg)

        now = _utc_now()
        metadata = {
            "evaluation_type": spec.evaluation_type.value,
            "factor_type": spec.factor_type.value,
            "frequency": spec.frequency.value,
            "input_fields": [field.to_dict() for field in spec.input_fields],
            "session_reset": spec.session_reset,
            "warmup_bars": spec.warmup_bars,
        }
        connection.execute(
            """
            INSERT INTO factor_registry (
                factor_id,
                name,
                owner,
                description,
                status,
                created_at,
                updated_at,
                metadata_json,
                status_message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(factor_id) DO UPDATE SET
                name = excluded.name,
                owner = excluded.owner,
                description = excluded.description,
                status = excluded.status,
                updated_at = excluded.updated_at,
                metadata_json = excluded.metadata_json,
                status_message = excluded.status_message
            """,
            (
                spec.factor_id,
                spec.name,
                spec.owner,
                spec.description,
                spec.status.value,
                spec.created_at.isoformat().replace("+00:00", "Z"),
                now,
                canonical_json(metadata),
                status_message,
            ),
        )
        connection.execute(
            """
            INSERT INTO factor_versions (
                factor_id,
                factor_version,
                created_at,
                git_commit,
                git_dirty,
                code_hash,
                config_hash,
                data_version,
                parameters_json,
                artifact_paths_json,
                decision_status,
                status_message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                spec.factor_id,
                spec.version,
                spec.created_at.isoformat().replace("+00:00", "Z"),
                git_info.commit,
                _git_dirty_value(git_info.dirty),
                spec.code_hash,
                spec.config_hash,
                str(spec.parameters.get("data_version", "")),
                canonical_json(dict(spec.parameters)),
                canonical_json(_artifact_paths(spec)),
                spec.status.value,
                status_message,
            ),
        )


def factor_version_exists(
    connection: sqlite3.Connection,
    factor_id: str,
    factor_version: str,
) -> bool:
    """Return whether a factor version is already registered."""
    row = connection.execute(
        """
        SELECT 1
        FROM factor_versions
        WHERE factor_id = ? AND factor_version = ?
        """,
        (factor_id, factor_version),
    ).fetchone()
    return row is not None


def get_factor_version(
    registry_path: str | Path,
    factor_id: str,
    factor_version: str,
) -> dict[str, Any] | None:
    """Read a factor version, including deprecated versions."""
    registry = Path(registry_path)
    with connect_registry(registry, read_only=True) as connection:
        row = connection.execute(
            """
            SELECT
                r.factor_id,
                r.name,
                r.owner,
                r.description,
                r.status AS registry_status,
                r.metadata_json,
                v.factor_version,
                v.created_at,
                v.git_commit,
                v.git_dirty,
                v.code_hash,
                v.config_hash,
                v.data_version,
                v.parameters_json,
                v.artifact_paths_json,
                v.decision_status,
                v.status_message
            FROM factor_versions v
            JOIN factor_registry r ON r.factor_id = v.factor_id
            WHERE v.factor_id = ? AND v.factor_version = ?
            """,
            (factor_id, factor_version),
        ).fetchone()
    if row is None:
        return None
    payload = dict(row)
    payload["metadata"] = _loads(payload.pop("metadata_json"))
    payload["parameters"] = _loads(payload.pop("parameters_json"))
    payload["artifact_paths"] = _loads(payload.pop("artifact_paths_json"))
    return payload


def record_factor_validation_run(
    registry_path: str | Path,
    spec: FactorSpec,
    *,
    run_id: str,
    decision_status: str = "accepted",
    reviewer: str = "reviewed",
    status_message: str = "factor validation reviewed",
) -> None:
    """Record a reviewed factor validation run for lifecycle gating tests."""
    registry = _init_valid_registry(registry_path)
    git_info = capture_git_info(Path.cwd())
    metadata = {"reviewer": reviewer}
    artifact_paths = _artifact_paths(spec)
    artifact_paths["review_metadata"] = metadata
    with connect_registry(registry) as connection:
        connection.execute(
            """
            INSERT INTO factor_validation_runs (
                run_id,
                timestamp,
                git_commit,
                git_dirty,
                code_hash,
                config_hash,
                data_version,
                factor_versions_json,
                label_versions_json,
                engine_version,
                parameters_json,
                artifact_paths_json,
                decision_status,
                warnings_json,
                status_message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                _utc_now(),
                git_info.commit,
                _git_dirty_value(git_info.dirty),
                spec.code_hash,
                spec.config_hash,
                str(spec.parameters.get("data_version", "")),
                canonical_json({spec.factor_id: spec.version}),
                "{}",
                "factor_registry_v1",
                canonical_json(dict(spec.parameters)),
                canonical_json(artifact_paths),
                decision_status,
                "[]",
                status_message,
            ),
        )


def has_reviewed_validation(
    registry_path: str | Path,
    spec: FactorSpec,
) -> bool:
    """Return whether the registry contains reviewed validation evidence."""
    try:
        with connect_registry(registry_path, read_only=True) as connection:
            rows = connection.execute(
                """
                SELECT factor_versions_json, artifact_paths_json, decision_status
                FROM factor_validation_runs
                WHERE code_hash = ? AND config_hash = ?
                """,
                (spec.code_hash, spec.config_hash),
            ).fetchall()
    except sqlite3.Error:
        return False
    for row in rows:
        versions = _loads(row["factor_versions_json"])
        artifacts = _loads(row["artifact_paths_json"])
        status = str(row["decision_status"]).lower()
        if versions.get(spec.factor_id) != spec.version:
            continue
        if status not in REVIEWED_VALIDATION_STATUSES:
            continue
        if not artifacts.get("validation_artifact_path"):
            continue
        return True
    return False


def record_promotion_decision(
    registry_path: str | Path,
    spec: FactorSpec,
    *,
    decision_status: str = "approved",
    reviewer: str,
    rationale: str,
    decision_id: str | None = None,
    artifact_paths: Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
    run_id: str = "",
) -> str:
    """Record a review-backed promotion decision for a factor version."""
    if not reviewer.strip():
        msg = "promotion reviewer must be non-empty"
        raise FactorRegistryError(msg)
    if not rationale.strip():
        msg = "promotion rationale must be non-empty"
        raise FactorRegistryError(msg)

    registry = _init_valid_registry(registry_path)
    active_artifacts = dict(artifact_paths or _artifact_paths(spec))
    active_metadata = dict(metadata or {})
    active_metadata["review_backed"] = True
    active_decision_id = decision_id or _promotion_decision_id(
        spec,
        decision_status=decision_status,
        reviewer=reviewer,
        rationale=rationale,
    )
    with connect_registry(registry) as connection:
        connection.execute(
            """
            INSERT INTO promotion_decisions (
                decision_id,
                subject_type,
                subject_id,
                subject_version,
                run_id,
                decision_status,
                decided_at,
                reviewer,
                rationale,
                artifact_paths_json,
                metadata_json,
                status_message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                active_decision_id,
                "factor",
                spec.factor_id,
                spec.version,
                run_id,
                decision_status,
                _utc_now(),
                reviewer,
                rationale,
                canonical_json(active_artifacts),
                canonical_json(active_metadata),
                "review-backed factor promotion decision",
            ),
        )
    return active_decision_id


def has_review_backed_promotion(
    registry_path: str | Path,
    spec: FactorSpec,
) -> bool:
    """Return whether approval is backed by explicit reviewer metadata."""
    try:
        with connect_registry(registry_path, read_only=True) as connection:
            rows = connection.execute(
                """
                SELECT decision_status, reviewer, rationale, metadata_json
                FROM promotion_decisions
                WHERE subject_type = 'factor'
                  AND subject_id = ?
                  AND subject_version = ?
                """,
                (spec.factor_id, spec.version),
            ).fetchall()
    except sqlite3.Error:
        return False
    for row in rows:
        status = str(row["decision_status"]).lower()
        metadata = _loads(row["metadata_json"])
        if status not in REVIEW_BACKED_PROMOTION_STATUSES:
            continue
        if not str(row["reviewer"]).strip() or not str(row["rationale"]).strip():
            continue
        if metadata.get("review_backed") is not True:
            continue
        return True
    return False


def _init_valid_registry(registry_path: str | Path) -> Path:
    registry = Path(registry_path)
    status = init_registry(registry)
    if not status.valid:
        msg = f"registry is not valid: {status.status_message}"
        raise FactorRegistryError(msg)
    return registry


def _artifact_paths(spec: FactorSpec) -> dict[str, Any]:
    if spec.validation_artifact_path is None:
        return {}
    return {"validation_artifact_path": spec.validation_artifact_path}


def _loads(value: str) -> dict[str, Any]:
    payload = json.loads(value or "{}")
    if isinstance(payload, dict):
        return payload
    return {}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _git_dirty_value(value: bool | None) -> int | None:
    if value is None:
        return None
    return 1 if value else 0


def _promotion_decision_id(
    spec: FactorSpec,
    *,
    decision_status: str,
    reviewer: str,
    rationale: str,
) -> str:
    digest = hash_config(
        {
            "decision_status": decision_status,
            "factor_id": spec.factor_id,
            "rationale": rationale,
            "reviewer": reviewer,
            "version": spec.version,
        }
    )
    return f"promotion:{spec.factor_id}:{spec.version}:{digest[:16]}"
