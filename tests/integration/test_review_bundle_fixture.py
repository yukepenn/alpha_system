from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from tests.unit.reports.review_bundle_fixtures import (
    REPO_ROOT,
    run_manifest_payload,
    write_artifact_manifest,
    write_run_manifest,
)


SRC_ROOT = REPO_ROOT / "src"


def _env_with_src_path() -> dict[str, str]:
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(SRC_ROOT) if not pythonpath else os.pathsep.join([str(SRC_ROOT), pythonpath])
    )
    return env


def test_report_build_cli_writes_local_review_bundle_fixture(tmp_path) -> None:
    run_manifest = write_run_manifest(tmp_path, run_manifest_payload("cli_bundle_fixture"))
    artifact_manifest = write_artifact_manifest(tmp_path)
    output_dir = tmp_path / "review_bundle"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alpha_system.cli",
            "report",
            "build",
            "--run-id",
            "cli_bundle_fixture",
            "--artifact-manifest",
            artifact_manifest.as_posix(),
            "--run-manifest",
            run_manifest.as_posix(),
            "--output-dir",
            output_dir.as_posix(),
            "--source-root",
            REPO_ROOT.as_posix(),
        ],
        cwd=REPO_ROOT,
        env=_env_with_src_path(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["output_dir"] == output_dir.as_posix()
    summary_path = output_dir / "review_bundle_summary.json"
    assert summary_path.is_file()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["run_id"] == "cli_bundle_fixture"
    assert summary["validation"]["missing_required_versions"] == []
    assert (output_dir / "source_map.md").is_file()
    assert (output_dir / "audit_report.md").is_file()
