"""Correlation utilities for comparing a factor to existing factors."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from alpha_system.research.ic import pearson_ic, rank_ic


def correlation_to_existing_factor(
    candidate_values: Iterable[Any],
    existing_values: Iterable[Any],
) -> dict[str, float | int | None]:
    """Return Pearson and rank correlation to one existing factor."""
    pearson = pearson_ic(candidate_values, existing_values)
    rank = rank_ic(candidate_values, existing_values)
    return {"pearson": pearson["ic"], "rank": rank["ic"], "n": pearson["n"]}


def correlations_to_existing_factors(
    candidate_values: Iterable[Any],
    existing_factor_values: Mapping[str, Iterable[Any]],
) -> dict[str, dict[str, float | int | None]]:
    """Return correlations to multiple named existing factors."""
    candidate = tuple(candidate_values)
    return {
        factor_id: correlation_to_existing_factor(candidate, tuple(values))
        for factor_id, values in sorted(existing_factor_values.items())
    }
