from __future__ import annotations

from alpha_system.reports.source_map import build_source_map
from tests.unit.reports.review_bundle_fixtures import REPO_ROOT


def test_source_map_includes_report_config_files() -> None:
    source_map = build_source_map(run_id="source_map_config_fixture", source_root=REPO_ROOT)
    paths = {entry.path for entry in source_map.config_files}

    assert "configs/reports/review_bundle.yaml" in paths
    assert all(entry.exists for entry in source_map.config_files)
