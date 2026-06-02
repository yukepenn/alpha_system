"""Experiment reproducibility contract primitives only."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from alpha_system.core.contracts import ArtifactPaths, ConfigParameters, VersionMap
from alpha_system.core.enums import DecisionStatus


@dataclass(frozen=True, slots=True, kw_only=True)
class ExperimentSpec:
    experiment_id: str
    run_id: str
    name: str
    owner: str
    code_hash: str
    config_hash: str
    data_version: str
    factor_versions: VersionMap
    label_versions: VersionMap
    engine_version: str
    parameters: ConfigParameters
    artifact_paths: ArtifactPaths
    decision_status: DecisionStatus
    created_at: datetime
