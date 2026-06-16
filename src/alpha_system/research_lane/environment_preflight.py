"""Loud, distinct environment preconditions for the idea run / mine entrypoints.

This module exists to make an UNMET ENVIRONMENT precondition LOUD and DISTINCT
from a genuine ``DATA_GAP``. A whole class of recurring mis-diagnoses traced back
to one root cause: an unmet environment/config precondition (an unset
``ALPHA_DATA_ROOT``, a data root that does not exist on disk, or the wrong Python
interpreter without ``polars``) was silently fail-closed into an ambiguous
``DATA_GAP`` and then misread downstream as "data absent / research direction
null / driver broken".

The preflight here resolves the data root through the single canonical resolver
(:func:`alpha_system.data.foundation.sources.resolve_alpha_data_root`) and then
checks two preconditions WITHOUT loading any values:

1. ``polars`` must be importable -- data-layer ops require the research venv.
2. The resolved data root must exist as a directory on disk.

When a precondition is UNMET it returns a distinct
:class:`EnvironmentPreconditionStatus.ENVIRONMENT_NOT_CONFIGURED` result with an
ACTIONABLE message; this status is NEVER ``DATA_GAP``. When all preconditions are
met it returns ``CONFIGURED`` together with the resolved root, so the caller can
inject ``ALPHA_DATA_ROOT`` into the registry/probe env (so the core registry path
resolves the same known-good root the tools already default to).
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from alpha_system.data.foundation.sources import resolve_alpha_data_root
from alpha_system.data.storage import dependency_available

# Machine-readable issue codes (typed, not string-spelunked) for the two distinct
# unmet-precondition causes the preflight can surface.
DATA_ROOT_NOT_FOUND_CODE = "alpha_data_root_not_found"
POLARS_MISSING_CODE = "data_dependency_missing"

# Required data-layer dependency. The producer fast-path + registry parquet reads
# all require ``polars``; a plain interpreter without it fail-closes everywhere.
_REQUIRED_DEPENDENCY = "polars"


class EnvironmentPreconditionStatus(StrEnum):
    """Distinct preflight verdict, deliberately disjoint from gate DATA_GAP."""

    CONFIGURED = "CONFIGURED"
    ENVIRONMENT_NOT_CONFIGURED = "ENVIRONMENT_NOT_CONFIGURED"


@dataclass(frozen=True, slots=True)
class EnvironmentPreflightResult:
    """Result of the data-ops environment preflight.

    ``status`` is the one load-bearing field: ``ENVIRONMENT_NOT_CONFIGURED`` means
    an unmet environment precondition (NOT a data finding). ``data_root`` is the
    resolved (not necessarily existing) root; ``issue_code`` / ``message`` carry the
    actionable detail when blocked.
    """

    status: EnvironmentPreconditionStatus
    data_root: Path
    issue_code: str | None = None
    message: str | None = None

    @property
    def configured(self) -> bool:
        return self.status is EnvironmentPreconditionStatus.CONFIGURED

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "verdict": self.status.value,
            "data_root": self.data_root.as_posix(),
            "issue_code": self.issue_code,
            "message": self.message,
        }


def evaluate_environment_preflight(
    *,
    alpha_data_root: str | os.PathLike[str] | None = None,
    env: Mapping[str, str] | None = None,
) -> EnvironmentPreflightResult:
    """Check the data-ops environment preconditions without loading values.

    Resolution order for the root is the canonical
    explicit -> ``ALPHA_DATA_ROOT`` env -> default. The polars check fires first
    because a missing interpreter dependency masks every downstream resolution.
    """

    data_root = resolve_alpha_data_root(alpha_data_root, env)

    if not dependency_available(_REQUIRED_DEPENDENCY):
        return EnvironmentPreflightResult(
            status=EnvironmentPreconditionStatus.ENVIRONMENT_NOT_CONFIGURED,
            data_root=data_root,
            issue_code=POLARS_MISSING_CODE,
            message=(
                f"data ops require the research venv: {_REQUIRED_DEPENDENCY!r} is "
                "not importable in the current interpreter. Re-run with "
                "~/.venvs/alpha_system_research/bin/python (NOT a bare `python`). "
                "This is an unmet ENVIRONMENT precondition, not a DATA_GAP."
            ),
        )

    if not data_root.is_dir():
        return EnvironmentPreflightResult(
            status=EnvironmentPreconditionStatus.ENVIRONMENT_NOT_CONFIGURED,
            data_root=data_root,
            issue_code=DATA_ROOT_NOT_FOUND_CODE,
            message=(
                f"the resolved ALPHA_DATA_ROOT does not exist as a directory: "
                f"{data_root.as_posix()!r}. Set ALPHA_DATA_ROOT to the local "
                "materialized store (default ~/alpha_data/alpha_system) before "
                "running data ops. This is an unmet ENVIRONMENT precondition, not "
                "a DATA_GAP."
            ),
        )

    return EnvironmentPreflightResult(
        status=EnvironmentPreconditionStatus.CONFIGURED,
        data_root=data_root,
    )


def env_with_resolved_data_root(
    result: EnvironmentPreflightResult,
    env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return an env mapping with ``ALPHA_DATA_ROOT`` pinned to the resolved root.

    Used after a CONFIGURED preflight so the registry/probe path resolves the
    SAME known-good root the preflight checked, even when the caller's process env
    had ``ALPHA_DATA_ROOT`` unset (relying on the canonical default). This makes
    the core registry path match the tool defaults instead of fail-closing.
    """

    source = os.environ if env is None else env
    merged = dict(source)
    merged["ALPHA_DATA_ROOT"] = result.data_root.as_posix()
    return merged


__all__ = [
    "DATA_ROOT_NOT_FOUND_CODE",
    "POLARS_MISSING_CODE",
    "EnvironmentPreconditionStatus",
    "EnvironmentPreflightResult",
    "env_with_resolved_data_root",
    "evaluate_environment_preflight",
]
