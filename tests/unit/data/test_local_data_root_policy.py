from __future__ import annotations

from pathlib import Path

import pytest

from alpha_system.data.foundation.sources import (
    DEFAULT_ALLOWED_SUBDIRS,
    DEFAULT_FORBIDDEN_REPO_PATHS,
    DEFAULT_MAX_FILE_POLICY,
    DataFoundationValidationError,
    LocalDataRootPolicy,
    require_local_data_root_policy,
)


def _outside_repo_root(name: str = "alpha_system_unit_test_root") -> Path:
    return Path.home() / "alpha_data" / name


def _policy(root: str | Path, **overrides: object) -> LocalDataRootPolicy:
    fields: dict[str, object] = {
        "data_root": root,
        "must_be_local": True,
        "must_be_ignored": True,
        "forbidden_repo_paths": DEFAULT_FORBIDDEN_REPO_PATHS,
        "allowed_subdirs": DEFAULT_ALLOWED_SUBDIRS,
        "max_file_policy": DEFAULT_MAX_FILE_POLICY,
    }
    fields.update(overrides)
    return LocalDataRootPolicy(**fields)


def test_local_data_root_policy_accepts_valid_outside_repo_root_without_existing() -> None:
    root = _outside_repo_root("alpha_system_unit_nonexistent_root")

    policy = _policy(root)

    assert policy.data_root == root.expanduser().resolve(strict=False)
    assert policy.must_be_local is True
    assert policy.must_be_ignored is True
    assert "raw" in policy.allowed_subdirs
    assert "canonical" in policy.allowed_subdirs
    assert policy.max_file_policy["oversize_action"] == "fail_closed"


def test_local_data_root_policy_reads_alpha_data_root_from_env() -> None:
    root = _outside_repo_root("alpha_system_env_root")

    policy = LocalDataRootPolicy.from_env({"ALPHA_DATA_ROOT": root.as_posix()})

    assert policy.data_root == root.expanduser().resolve(strict=False)


def test_local_data_root_policy_uses_suggested_default_when_env_missing() -> None:
    policy = LocalDataRootPolicy.from_env({})

    assert policy.data_root == (Path.home() / "alpha_data" / "alpha_system").resolve(
        strict=False
    )


def test_local_data_root_policy_rejects_missing_required_fields() -> None:
    with pytest.raises(TypeError):
        LocalDataRootPolicy(data_root=_outside_repo_root())  # type: ignore[call-arg]


@pytest.mark.parametrize(
    "repo_relative_root",
    [
        "data/raw",
        "data/canonical",
        "data/cache",
        "metadata",
        "artifacts",
        "src",
    ],
)
def test_local_data_root_policy_rejects_in_repo_roots(repo_relative_root: str) -> None:
    repo_root = Path(__file__).resolve().parents[3]

    with pytest.raises(DataFoundationValidationError, match="outside the repository"):
        _policy(repo_root / repo_relative_root)


@pytest.mark.parametrize(
    "unsafe_root",
    [
        "/mnt/c/Users/example/alpha_data",
        "/mnt/d/alpha_data",
        "/mnt/e/alpha_data",
        "/tmp/alpha_system_data",
        "/var/tmp/alpha_system_data",
        "//server/share/alpha_system_data",
    ],
)
def test_local_data_root_policy_rejects_mounted_network_and_temp_paths(
    unsafe_root: str,
) -> None:
    with pytest.raises(DataFoundationValidationError):
        _policy(unsafe_root)


@pytest.mark.parametrize(
    "unsafe_root",
    [
        Path.home() / "OneDrive" / "alpha_data",
        Path.home() / "Dropbox" / "alpha_data",
        Path.home() / "Google Drive" / "alpha_data",
        Path.home() / "Windows-synced folders" / "alpha_data",
    ],
)
def test_local_data_root_policy_rejects_cloud_synced_paths(unsafe_root: Path) -> None:
    with pytest.raises(DataFoundationValidationError):
        _policy(unsafe_root)


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    [
        ("data_root", ""),
        ("must_be_local", False),
        ("must_be_ignored", False),
        ("forbidden_repo_paths", ()),
        ("forbidden_repo_paths", ("../data",)),
        ("allowed_subdirs", ()),
        ("allowed_subdirs", ("../raw",)),
        ("max_file_policy", {"max_bytes_per_file": 0, "oversize_action": "fail_closed"}),
        ("max_file_policy", {"max_bytes_per_file": 1, "oversize_action": "warn"}),
    ],
)
def test_local_data_root_policy_rejects_invalid_policy_fields(
    field_name: str,
    bad_value: object,
) -> None:
    with pytest.raises(DataFoundationValidationError):
        _policy(_outside_repo_root(), **{field_name: bad_value})


def test_missing_local_data_root_policy_blocks_raw_writes() -> None:
    with pytest.raises(DataFoundationValidationError, match="blocks raw writes"):
        require_local_data_root_policy(None)


def test_valid_local_data_root_policy_satisfies_raw_write_precondition() -> None:
    policy = _policy(_outside_repo_root("alpha_system_raw_write_guard"))

    assert require_local_data_root_policy(policy) is policy
