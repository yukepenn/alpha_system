"""Batch planning placeholders for data ingestion.

DATA-P01 names only. DATA-P08 and DATA-P09 own chunking and micro-batch behavior.
"""


class SymbolBatchPlan:
    """DATA-P08 placeholder for a symbol batch plan."""


class MicroBatchPolicy:
    """DATA-P09 placeholder for a micro-batch policy."""


__all__ = ["MicroBatchPolicy", "SymbolBatchPlan"]
