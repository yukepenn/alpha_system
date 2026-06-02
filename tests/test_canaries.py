from __future__ import annotations

from tools.hooks.canary_runner import main, scenarios


def test_canary_runner_negative_cases_pass() -> None:
    assert main() == 0


def test_canary_scenarios_cover_artifact_placeholders_and_real_data() -> None:
    by_name = {canary.name: canary for canary in scenarios()}

    assert by_name["generated_scaffold_allowed"].expect_block is False
    assert "data/raw/.gitkeep" in by_name["generated_scaffold_allowed"].paths
    assert "data/cache/README.md" in by_name["generated_scaffold_allowed"].paths
    assert "data/labels/README.md" in by_name["generated_scaffold_allowed"].paths
    assert "metadata/README.md" in by_name["generated_scaffold_allowed"].paths
    assert "artifacts/README.md" in by_name["generated_scaffold_allowed"].paths
    assert "artifacts/.gitkeep" in by_name["generated_scaffold_allowed"].paths
    assert "artifacts/reports/README.md" in by_name["generated_scaffold_allowed"].paths
    assert by_name["forbidden_raw_data_commit"].expect_block is True
    assert by_name["forbidden_cache_data_commit"].expect_block is True
    assert by_name["forbidden_local_artifacts"].expect_block is True
    assert "data/raw/SPY.parquet" in by_name["forbidden_local_artifacts"].paths
    assert "data/cache/cache.sqlite" in by_name["forbidden_local_artifacts"].paths
    assert "artifacts/model.pkl" in by_name["forbidden_local_artifacts"].paths
    assert "metadata/registry.sqlite" in by_name["forbidden_local_artifacts"].paths
    assert ".env" in by_name["forbidden_local_artifacts"].paths
    assert "secrets.json" in by_name["forbidden_local_artifacts"].paths
