from __future__ import annotations

import importlib
import socket
import sys
from pathlib import Path

import pytest


CREDENTIAL_ENV_NAMES = (
    "ALPACA_API_KEY",
    "ALPACA_SECRET_KEY",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "BROKER_API_KEY",
    "BROKER_SECRET",
    "IBKR_ACCOUNT",
    "OPENAI_API_KEY",
    "POLYGON_API_KEY",
)


def _clear_alpha_system_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "alpha_system" or module_name.startswith("alpha_system."):
            del sys.modules[module_name]


def _forbid_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("network access was attempted")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)
    monkeypatch.setattr(socket, "socket", blocked)


def test_import_requires_no_local_data_network_or_credentials(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    for name in CREDENTIAL_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    _forbid_network(monkeypatch)
    _clear_alpha_system_modules()

    assert not Path("data").exists()
    assert not Path("metadata").exists()

    module = importlib.import_module("alpha_system")

    assert module.__name__ == "alpha_system"


def test_cli_help_requires_no_local_data_network_or_credentials(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    for name in CREDENTIAL_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    _forbid_network(monkeypatch)

    assert not Path("data").exists()
    assert not Path("metadata").exists()

    from alpha_system.cli.main import main

    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    captured = capsys.readouterr()
    assert exc_info.value.code == 0
    assert "usage:" in captured.out.lower()
