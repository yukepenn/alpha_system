from __future__ import annotations

from pathlib import Path

from alpha_system.research_lane.environment_preflight import (
    DATA_ROOT_NOT_FOUND_CODE,
    EnvironmentPreconditionStatus,
    env_with_resolved_data_root,
    evaluate_environment_preflight,
)


def test_explicit_existing_root_is_configured(tmp_path: Path) -> None:
    result = evaluate_environment_preflight(alpha_data_root=tmp_path, env={})

    assert result.status is EnvironmentPreconditionStatus.CONFIGURED
    assert result.configured is True
    assert result.data_root == tmp_path
    assert result.issue_code is None


def test_nonexistent_root_is_environment_not_configured_not_datagap(tmp_path: Path) -> None:
    missing = tmp_path / "absent-data-root"
    assert not missing.exists()

    result = evaluate_environment_preflight(alpha_data_root=missing, env={})

    assert result.status is EnvironmentPreconditionStatus.ENVIRONMENT_NOT_CONFIGURED
    assert result.configured is False
    # The whole point of the fix: this is NEVER a DATA_GAP.
    assert result.status.value != "DATA_GAP"
    assert result.issue_code == DATA_ROOT_NOT_FOUND_CODE
    assert "DATA_GAP" in (result.message or "")
    assert missing.as_posix() in (result.message or "")


def test_env_var_nonexistent_root_is_environment_not_configured(tmp_path: Path) -> None:
    missing = tmp_path / "via-env-absent"
    result = evaluate_environment_preflight(env={"ALPHA_DATA_ROOT": missing.as_posix()})

    assert result.status is EnvironmentPreconditionStatus.ENVIRONMENT_NOT_CONFIGURED
    assert result.data_root == missing


def test_to_dict_mirrors_overall_status_key(tmp_path: Path) -> None:
    missing = tmp_path / "absent"
    payload = evaluate_environment_preflight(alpha_data_root=missing, env={}).to_dict()

    assert payload["status"] == "ENVIRONMENT_NOT_CONFIGURED"
    assert payload["verdict"] == "ENVIRONMENT_NOT_CONFIGURED"
    assert payload["issue_code"] == DATA_ROOT_NOT_FOUND_CODE


def test_env_with_resolved_data_root_pins_resolved_root(tmp_path: Path) -> None:
    result = evaluate_environment_preflight(alpha_data_root=tmp_path, env={})
    merged = env_with_resolved_data_root(result, env={"OTHER": "keep"})

    assert merged["ALPHA_DATA_ROOT"] == tmp_path.as_posix()
    assert merged["OTHER"] == "keep"
