from __future__ import annotations

import pytest

from alpha_system.reports.review_bundle import resolve_review_bundle_output_dir
from tests.unit.reports.review_bundle_fixtures import REPO_ROOT, build_fixture_bundle


def test_review_bundle_repo_output_must_stay_under_local_artifacts_root() -> None:
    with pytest.raises(ValueError):
        resolve_review_bundle_output_dir(REPO_ROOT / "docs" / "bundle", run_id="blocked")


def test_review_bundle_temp_output_is_allowed(tmp_path) -> None:
    path = resolve_review_bundle_output_dir(tmp_path / "bundle", run_id="allowed")

    assert path == tmp_path / "bundle"


def test_review_bundle_summary_does_not_write_full_bundle_by_default(tmp_path) -> None:
    bundle = build_fixture_bundle(tmp_path)

    assert bundle.summary_dict()["missing_artifact_count"] == 0
