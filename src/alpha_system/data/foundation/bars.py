"""Raw, parsed, and canonical bar placeholders.

DATA-P01 names only. DATA-P10, DATA-P14, and DATA-P15 own parser,
canonicalization, timestamp, and quality behavior.
"""


class RawDataObject:
    """DATA-P10 placeholder for an immutable local provider response."""


class ParsedBarRecord:
    """DATA-P14 placeholder for a provider-shaped parsed bar record."""


class CanonicalBarRecord:
    """DATA-P15 placeholder for a research-ready canonical bar record."""


class TimestampSemanticsPolicy:
    """DATA-P15 placeholder for canonical timestamp semantics."""


__all__ = [
    "CanonicalBarRecord",
    "ParsedBarRecord",
    "RawDataObject",
    "TimestampSemanticsPolicy",
]
