"""Data source and local data-root policy placeholders.

DATA-P01 names only. DATA-P02 and DATA-P03 own source-profile, access-mode, and
local root policy behavior.
"""


class DataSourceProfile:
    """DATA-P02 placeholder for a data provider usage-boundary profile."""


class LocalDataRootPolicy:
    """DATA-P02 placeholder for local-only data root policy metadata."""


class DataAccessMode:
    """DATA-P03 placeholder for allowed data access modes."""


__all__ = ["DataAccessMode", "DataSourceProfile", "LocalDataRootPolicy"]
