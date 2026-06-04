from __future__ import annotations

import pytest

from tools.hooks import artifact_guard


@pytest.mark.parametrize(
    "path",
    [
        "runs/r1/RUN_SUMMARY.md",
        "metadata/local.sqlite",
        "data/raw/es.csv",
        "raw_backup.raw",
        "data/raw/x.raw",
        "shadow.arrow",
        "data/canonical/bars.parquet",
        "artifacts/generated/report.json",
        "models/model.pkl",
        ".env",
        "secrets.json",
        "logs/run.log",
        ".frontier/upgrade_reports/x.md",
    ],
)
def test_forbidden_artifacts(path: str) -> None:
    assert artifact_guard.forbidden(path) is True


@pytest.mark.parametrize(
    "path",
    [
        "artifacts/README.md",
        "data/raw/README.md",
        "data/canonical/.gitkeep",
        "docs/V0_1_VALIDATION.md",
        "handoffs/ASV1-P29.md",
        "evals/v0_1/ARTIFACT_AUDIT_SUMMARY.md",
        "tools/verify.py",
        "pyproject.toml",
    ],
)
def test_allowed_curated_paths(path: str) -> None:
    assert artifact_guard.forbidden(path) is False
