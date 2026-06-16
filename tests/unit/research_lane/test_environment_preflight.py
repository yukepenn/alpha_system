from __future__ import annotations

import importlib.util
from pathlib import Path

from alpha_system.research_lane.environment_preflight import (
    DATA_ROOT_NOT_FOUND_CODE,
    POLARS_MISSING_CODE,
    EnvironmentPreconditionStatus,
    env_with_resolved_data_root,
    evaluate_environment_preflight,
)

# Host independence: the preflight checks the ``polars`` interpreter dependency
# BEFORE the on-disk data root. CI's pytest interpreter is a bare ``python`` WITHOUT
# ``polars`` (the same reason the pre-existing ``test_polars_lazy_fixture`` /
# ``test_duckdb_query_fixture`` fail there), while the research venv HAS polars.
# These tests therefore assert the host-independent INVARIANT unconditionally and
# branch only the polars-DEPENDENT expectations on the real interpreter state -- the
# same contract the precondition canary asserts.
_POLARS_IMPORTABLE = importlib.util.find_spec("polars") is not None


def test_existing_root_status_is_host_dependent_only_on_polars(tmp_path: Path) -> None:
    # An existing data root is CONFIGURED only when the EARLIER polars precondition is
    # also met. On a polars-less interpreter the dependency precondition fires first
    # and the result is ENVIRONMENT_NOT_CONFIGURED (data_dependency_missing) -- still
    # NEVER a DATA_GAP. Assert the polars-conditioned outcome so this holds on any host.
    result = evaluate_environment_preflight(alpha_data_root=tmp_path, env={})

    assert result.status.value != "DATA_GAP"
    if _POLARS_IMPORTABLE:
        assert result.status is EnvironmentPreconditionStatus.CONFIGURED
        assert result.configured is True
        assert result.data_root == tmp_path
        assert result.issue_code is None
    else:
        assert result.status is EnvironmentPreconditionStatus.ENVIRONMENT_NOT_CONFIGURED
        assert result.configured is False
        assert result.issue_code == POLARS_MISSING_CODE


def test_nonexistent_root_is_environment_not_configured_not_datagap(tmp_path: Path) -> None:
    missing = tmp_path / "absent-data-root"
    assert not missing.exists()

    result = evaluate_environment_preflight(alpha_data_root=missing, env={})

    # INVARIANT (asserted on any host): an unmet precondition is
    # ENVIRONMENT_NOT_CONFIGURED and is NEVER a DATA_GAP.
    assert result.status is EnvironmentPreconditionStatus.ENVIRONMENT_NOT_CONFIGURED
    assert result.configured is False
    assert result.status.value != "DATA_GAP"
    assert "DATA_GAP" in (result.message or "")
    # The specific issue_code depends on which precondition fires first: WITH polars
    # the nonexistent root is reached (alpha_data_root_not_found); WITHOUT polars the
    # earlier dependency precondition fires (data_dependency_missing). Both are
    # ENVIRONMENT_NOT_CONFIGURED.
    if _POLARS_IMPORTABLE:
        assert result.issue_code == DATA_ROOT_NOT_FOUND_CODE
        assert missing.as_posix() in (result.message or "")
    else:
        assert result.issue_code == POLARS_MISSING_CODE


def test_env_var_nonexistent_root_is_environment_not_configured(tmp_path: Path) -> None:
    missing = tmp_path / "via-env-absent"
    result = evaluate_environment_preflight(env={"ALPHA_DATA_ROOT": missing.as_posix()})

    # ENVIRONMENT_NOT_CONFIGURED on any host (data root absent and/or polars missing);
    # the resolved root is the env-pointed path regardless of which precondition fires.
    assert result.status is EnvironmentPreconditionStatus.ENVIRONMENT_NOT_CONFIGURED
    assert result.status.value != "DATA_GAP"
    assert result.data_root == missing


def test_to_dict_mirrors_overall_status_key(tmp_path: Path) -> None:
    missing = tmp_path / "absent"
    payload = evaluate_environment_preflight(alpha_data_root=missing, env={}).to_dict()

    assert payload["status"] == "ENVIRONMENT_NOT_CONFIGURED"
    assert payload["verdict"] == "ENVIRONMENT_NOT_CONFIGURED"
    expected_issue_code = DATA_ROOT_NOT_FOUND_CODE if _POLARS_IMPORTABLE else POLARS_MISSING_CODE
    assert payload["issue_code"] == expected_issue_code


def test_env_with_resolved_data_root_pins_resolved_root(tmp_path: Path) -> None:
    result = evaluate_environment_preflight(alpha_data_root=tmp_path, env={})
    merged = env_with_resolved_data_root(result, env={"OTHER": "keep"})

    assert merged["ALPHA_DATA_ROOT"] == tmp_path.as_posix()
    assert merged["OTHER"] == "keep"
