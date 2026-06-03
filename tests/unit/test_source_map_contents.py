from __future__ import annotations

from alpha_system.reports.source_map import build_source_map
from tests.unit.reports.review_bundle_fixtures import REPO_ROOT


def test_source_map_includes_relevant_source_files() -> None:
    source_map = build_source_map(run_id="source_map_fixture", source_root=REPO_ROOT)
    paths = {entry.path for entry in source_map.source_files}

    assert "src/alpha_system/reports/review_bundle.py" in paths
    assert "src/alpha_system/reports/source_map.py" in paths
    assert "src/alpha_system/reports/audit_report.py" in paths
    assert "src/alpha_system/cli/report.py" in paths
    assert all(entry.exists for entry in source_map.source_files)
    assert all(entry.content_hash for entry in source_map.source_files)
