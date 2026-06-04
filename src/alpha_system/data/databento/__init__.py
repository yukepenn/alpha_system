"""Optional Databento historical-data integration.

The Databento SDK is an optional dependency and is imported lazily by client
factory code only. Importing this package performs no provider calls and reads
no API key.
"""

from alpha_system.data.databento.client import (
    build_historical_client,
    require_databento_api_key,
)

__all__ = [
    "build_historical_client",
    "require_databento_api_key",
]
