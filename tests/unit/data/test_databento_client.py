from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from alpha_system.data.databento.client import (
    build_historical_client,
    require_databento_api_key,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError


def test_require_databento_api_key_raises_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABENTO_API_KEY", raising=False)

    with pytest.raises(DataFoundationValidationError, match="DATABENTO_API_KEY"):
        require_databento_api_key()


def test_require_databento_api_key_accepts_passed_runtime_env() -> None:
    assert require_databento_api_key({"DATABENTO_API_KEY": "example-runtime-value"}) == (
        "example-runtime-value"
    )


def test_databento_client_import_is_lazy_for_sdk() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    src_path = repo_root / "src"
    pythonpath = src_path.as_posix()
    if os.environ.get("PYTHONPATH"):
        pythonpath = f"{pythonpath}{os.pathsep}{os.environ['PYTHONPATH']}"
    code = (
        "import sys; "
        "import alpha_system.data.databento.client as c; "
        "assert c.__name__ == 'alpha_system.data.databento.client'; "
        "assert 'databento' not in sys.modules, 'databento imported eagerly'; "
        "print('ok')"
    )

    env = {key: value for key, value in os.environ.items() if key != "DATABENTO_API_KEY"}
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
        cwd=repo_root,
        env={**env, "PYTHONPATH": pythonpath},
    )

    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout


def test_build_historical_client_accepts_injected_fake_without_sdk_or_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABENTO_API_KEY", raising=False)
    sys.modules.pop("databento", None)
    fake_client = object()

    with build_historical_client(databento=fake_client) as client:
        assert client is fake_client

    assert "databento" not in sys.modules
