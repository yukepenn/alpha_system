from __future__ import annotations

from pathlib import Path

import pytest

from alpha_system.data.fixture_policy import (
    FIXTURE_SIZE_LIMIT_BYTES,
    FixturePolicyError,
    assert_build_input_allowed,
    assert_generated_output_allowed,
    assert_registry_path_allowed,
    check_fixture_file,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "data" / "synthetic_1min_bars.csv"


def test_existing_data_fixture_is_tiny_synthetic_and_deterministic() -> None:
    check = check_fixture_file(FIXTURE_PATH, repo_root=REPO_ROOT)

    assert check.allowed
    assert check.size_bytes < FIXTURE_SIZE_LIMIT_BYTES
    assert check.synthetic
    assert check.deterministic


def test_build_input_refuses_non_fixture_without_explicit_override(tmp_path: Path) -> None:
    local_input = tmp_path / "candidate.csv"
    local_input.write_text("synthetic deterministic correctness_only\n", encoding="utf-8")

    with pytest.raises(FixturePolicyError, match="not under"):
        assert_build_input_allowed(local_input, repo_root=REPO_ROOT)

    assert assert_build_input_allowed(
        local_input,
        repo_root=REPO_ROOT,
        allow_non_fixture_input=True,
    ) == local_input.resolve()


def test_fixture_policy_enforces_markers_and_size_threshold(tmp_path: Path) -> None:
    fixture_root = tmp_path / "tests" / "fixtures" / "data"
    fixture_root.mkdir(parents=True)
    missing_markers = fixture_root / "plain.csv"
    missing_markers.write_text("not market data\n", encoding="utf-8")

    with pytest.raises(FixturePolicyError, match="synthetic"):
        check_fixture_file(missing_markers, repo_root=tmp_path)

    too_large = fixture_root / "too_large.csv"
    too_large.write_text(
        "synthetic deterministic correctness_only\n"
        + ("x" * FIXTURE_SIZE_LIMIT_BYTES),
        encoding="utf-8",
    )
    with pytest.raises(FixturePolicyError, match="fixture limit"):
        check_fixture_file(too_large, repo_root=tmp_path)


def test_generated_outputs_reject_committed_paths(tmp_path: Path) -> None:
    with pytest.raises(FixturePolicyError, match="committed docs"):
        assert_generated_output_allowed(
            REPO_ROOT / "docs" / "generated_summary.json",
            repo_root=REPO_ROOT,
        )

    with pytest.raises(FixturePolicyError, match="tests/fixtures/data"):
        assert_generated_output_allowed(
            REPO_ROOT / "tests" / "fixtures" / "data" / "generated.csv",
            repo_root=REPO_ROOT,
        )

    allowed = assert_generated_output_allowed(
        tmp_path / "data" / "canonical" / "bars.csv",
        repo_root=REPO_ROOT,
        require_data_dir=True,
    )
    assert allowed == tmp_path / "data" / "canonical" / "bars.csv"


def test_registry_path_must_be_temp_local_and_outside_repo(tmp_path: Path) -> None:
    allowed = assert_registry_path_allowed(tmp_path / "registry.sqlite3", repo_root=REPO_ROOT)
    assert allowed == tmp_path / "registry.sqlite3"

    with pytest.raises(FixturePolicyError, match="outside the repo"):
        assert_registry_path_allowed(
            REPO_ROOT / "metadata" / "registry.sqlite3",
            repo_root=REPO_ROOT,
        )
