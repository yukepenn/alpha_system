"""ML experiment registry integration for local SQLite registries."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from alpha_system.core.registry import connect_registry, init_registry
from alpha_system.experiments.model_specs import ML_ENGINE_VERSION
from alpha_system.experiments.registry import RunRecord, insert_run_record
from alpha_system.experiments.reproducibility import ReproducibilityMetadata


ML_RUN_TABLE = "ml_runs"


@dataclass(frozen=True, slots=True)
class MLRegistryWriteResult:
    """Result of writing an ML run record."""

    registry_path: str
    run_id: str
    table_name: str = ML_RUN_TABLE
    written: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def write_ml_run_record(
    *,
    registry_path: str | Path,
    run_id: str,
    reproducibility: ReproducibilityMetadata,
    parameters: Mapping[str, Any],
    artifact_paths: Mapping[str, str],
    warnings: Sequence[str] = (),
    status_message: str = "ML research run recorded; review is required for promotion.",
) -> MLRegistryWriteResult:
    """Write one local-only ``ml_runs`` record to a SQLite registry."""
    init_registry(registry_path)
    record = RunRecord(
        run_id=run_id,
        timestamp=datetime.now(timezone.utc),
        git_commit=reproducibility.git_commit,
        git_dirty=reproducibility.git_dirty,
        code_hash=reproducibility.code_hash,
        config_hash=reproducibility.config_hash,
        data_version=reproducibility.data_version,
        factor_versions=reproducibility.factor_versions,
        label_versions=reproducibility.label_versions,
        engine_version=reproducibility.engine_version or ML_ENGINE_VERSION,
        parameters=parameters,
        artifact_paths=artifact_paths,
        decision_status="ml_recorded",
        warnings=tuple(warnings),
        status_message=status_message,
    )
    with connect_registry(registry_path) as connection:
        insert_run_record(connection, ML_RUN_TABLE, record)
    return MLRegistryWriteResult(
        registry_path=Path(registry_path).expanduser().resolve(strict=False).as_posix(),
        run_id=run_id,
    )
