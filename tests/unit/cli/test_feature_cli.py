from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

from alpha_system.data.foundation.sources import DataFoundationValidationError

PROVIDER_CLIENT_MODULES = (
    "alpha_system.data.databento.client",
    "alpha_system.data.ibkr.connector",
    "alpha_system.data.ibkr._connection",
)
HASH_0 = "0" * 64
HASH_1 = "1" * 64


def _main_cli():
    return importlib.import_module("alpha_system.cli.main")


def _feature_cli():
    return importlib.import_module("alpha_system.cli.feature")


def _feature_plan_args(tmp_path: Path) -> list[str]:
    return [
        "feature",
        "plan",
        "--registry-path",
        (tmp_path / "features.sqlite").as_posix(),
        "--feature-set-id",
        "feature_set_cli_fixture",
        "--feature-set-version",
        "v1",
        "--dataset-registry",
        (tmp_path / "datasets.sqlite").as_posix(),
        "--dataset-version-id",
        "dsv_cli_fixture_v1",
        "--quality-report",
        (tmp_path / "quality.json").as_posix(),
        "--coverage-report",
        (tmp_path / "coverage.json").as_posix(),
        "--source-manifest",
        (tmp_path / "manifest.json").as_posix(),
        "--code-hash",
        HASH_0,
        "--config-hash",
        HASH_1,
        "--partition",
        "development_partition",
        "--alpha-data-root",
        (tmp_path / "alpha_data").as_posix(),
    ]


def test_feature_command_is_registered_and_import_clean() -> None:
    for module_name in PROVIDER_CLIENT_MODULES:
        sys.modules.pop(module_name, None)

    parser = _main_cli().build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["feature", "list", "--help"])

    assert exc_info.value.code == 0
    assert all(module_name not in sys.modules for module_name in PROVIDER_CLIENT_MODULES)


def test_feature_materialize_defaults_to_dry_run(tmp_path: Path) -> None:
    parser = _main_cli().build_parser()
    args = parser.parse_args(
        [
            "feature",
            "materialize",
            *_feature_plan_args(tmp_path)[2:],
        ]
    )

    assert args.dry_run is True
    assert args.handler is _feature_cli().run_materialize


def test_feature_plan_fails_closed_when_feature_set_is_missing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = _main_cli().build_parser()
    args = parser.parse_args(_feature_plan_args(tmp_path))

    status = _feature_cli().run_plan(args)
    captured = capsys.readouterr()

    assert status == 2
    assert "feature command error:" in captured.err
    assert "local feature registry path is required" in captured.err


def test_feature_plan_fails_closed_when_dataset_version_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    feature_cli = _feature_cli()
    parser = _main_cli().build_parser()
    args = parser.parse_args(_feature_plan_args(tmp_path))

    monkeypatch.setattr(feature_cli, "_feature_set_from_registry", lambda _args: object())

    def missing_dataset(_args: object) -> object:
        raise DataFoundationValidationError("DatasetVersion not found")

    monkeypatch.setattr(feature_cli, "_resolve_accepted_dataset", missing_dataset)

    status = feature_cli.run_plan(args)
    captured = capsys.readouterr()

    assert status == 2
    assert "DatasetVersion not found" in captured.err
    assert all(module_name not in sys.modules for module_name in PROVIDER_CLIENT_MODULES)
