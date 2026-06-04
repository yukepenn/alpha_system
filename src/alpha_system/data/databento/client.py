"""Lazy Databento historical client helpers.

This module performs no provider calls at import time. The Databento SDK is an
optional dependency loaded only when a real historical client is requested.
"""

from __future__ import annotations

import os
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from types import ModuleType

from alpha_system.data.foundation.sources import DataFoundationValidationError

_DATABENTO_EXTRA_INSTALL_HINT = (
    'python -m venv .venv && .venv/bin/pip install -e ".[databento]"'
)
_DATABENTO_TARGET_INSTALL_HINT = (
    "python -m pip install --target ~/.alpha_databento_libs databento "
    "and run with PYTHONPATH=src:~/.alpha_databento_libs"
)
_DATABENTO_API_KEY_ENV = "DATABENTO_API_KEY"


def _load_databento() -> ModuleType:
    """Import ``databento`` only when a real historical client path needs it."""

    try:
        import databento
    except ImportError as exc:
        msg = (
            "databento is required for real Databento historical pulls; install it with "
            f"{_DATABENTO_EXTRA_INSTALL_HINT}; fallback: {_DATABENTO_TARGET_INSTALL_HINT}"
        )
        raise ImportError(msg) from exc
    return databento


def require_databento_api_key(env: Mapping[str, str] | None = None) -> str:
    """Return the Databento API key from runtime env, or fail without revealing it."""

    source = os.environ if env is None else env
    try:
        value = source[_DATABENTO_API_KEY_ENV]
    except KeyError as exc:
        msg = "DATABENTO_API_KEY is required for Databento historical client construction"
        raise DataFoundationValidationError(msg) from exc

    if not isinstance(value, str) or not value.strip():
        msg = "DATABENTO_API_KEY must be set to a non-empty runtime environment value"
        raise DataFoundationValidationError(msg)
    return value


@contextmanager
def build_historical_client(
    env: Mapping[str, str] | None = None,
    *,
    databento: object | None = None,
) -> Iterator[object]:
    """Yield an injected fake client or lazily build ``databento.Historical()``."""

    if databento is not None:
        yield databento
        return

    require_databento_api_key(env)
    databento_module = _load_databento()
    client = databento_module.Historical()
    try:
        yield client
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            close_result = close()
            if hasattr(close_result, "__await__"):
                msg = "Databento Historical.close returned an awaitable in a sync context"
                raise RuntimeError(msg)


__all__ = [
    "build_historical_client",
    "require_databento_api_key",
]
