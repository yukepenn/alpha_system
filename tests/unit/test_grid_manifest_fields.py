from __future__ import annotations

import json
from pathlib import Path

from alpha_system.experiments.grid_config import GridSpec
from alpha_system.experiments.runner import run_grid


def test_grid_manifest_contains_required_reproducibility_fields(tmp_path: Path) -> None:
    result = run_grid(GridSpec.from_mapping(_payload(tmp_path)))
    manifest = json.loads(Path(result.output_paths.manifest_path).read_text(encoding="utf-8"))

    for field in (
        "run_id",
        "timestamp",
        "git_commit",
        "git_dirty",
        "code_hash",
        "config_hash",
        "data_version",
        "factor_versions",
        "label_versions",
        "engine_version",
        "parameters",
        "artifact_paths",
        "decision_status",
        "warnings",
        "failed_steps",
    ):
        assert field in manifest
    assert manifest["run_id"] == "grid_manifest_fields"
    assert manifest["decision_status"] == "research_evidence_only"


def _payload(tmp_path: Path) -> dict[str, object]:
    return {
        "grid_id": "manifest_fields",
        "run_id": "grid_manifest_fields",
        "strategy_version": "strategy:v1",
        "data_version": "data:v1",
        "factor_versions": {"fixture_factor": "v1"},
        "label_versions": {"fixture_label": "v1"},
        "output_dir": (tmp_path / "grid").as_posix(),
        "max_combinations": 1,
        "parameter_space": {
            "factor": {"lookback": [2]},
            "strategy": {"direction": ["long"]},
            "risk": {"default_quantity": ["1"]},
            "management": {"eod_flat": [True]},
            "execution": {"fixed_bps": ["1"]},
        },
    }
