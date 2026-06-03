"""IBKR historical-data boundary placeholders.

DATA-P01 names only. DATA-P03 and DATA-P04 own read-only data-source and
connection-doctor behavior. This module performs no network access and reads no
credentials at import time.
"""


class IBKRConnectionProfile:
    """DATA-P04 placeholder for historical-data connection settings."""


class IBKRClientIdPolicy:
    """DATA-P04 placeholder for the data-client ID namespace policy."""


def run_connection_doctor(*_args: object, **_kwargs: object) -> None:
    """DATA-P04 placeholder for the future read-only connection doctor."""

    raise NotImplementedError("DATA-P04 owns the IBKR connection-doctor implementation.")


__all__ = ["IBKRClientIdPolicy", "IBKRConnectionProfile", "run_connection_doctor"]
