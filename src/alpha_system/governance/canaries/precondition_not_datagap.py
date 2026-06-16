"""Locking canary: an unmet ENVIRONMENT precondition is NOT a DATA_GAP.

This canary guards the precondition-masquerade fix (PRECONDITION_PREFLIGHT_V1). A
whole class of recurring mis-diagnoses traced to ONE root cause: an unmet
environment/config precondition (an unset / unresolvable ``ALPHA_DATA_ROOT``, or
the wrong interpreter without ``polars``) was silently fail-closed into an
ambiguous ``DATA_GAP`` and then misread as a research / data finding.

It deterministically asserts the two causes stay DISTINGUISHABLE, with NO real
market data, factor values, labels, or materialized store required:

(a) a resolved data root that does NOT exist on disk (and an unset env whose
    default also does not exist) -> the environment preflight returns the
    distinct ``ENVIRONMENT_NOT_CONFIGURED`` status, NEVER ``DATA_GAP``;
(b) the classification boundary: a resolver rejection carrying the TYPED
    data-root precondition reason code maps to ``ENVIRONMENT_NOT_CONFIGURED``,
    while a resolver rejection for a genuinely-absent partition (any other
    reason code) still maps to ``DATA_GAP`` -- the honest absent-data case is
    unchanged;
(c) the rollup: ``ENVIRONMENT_NOT_CONFIGURED`` OUTRANKS ``DATA_GAP`` so a broken
    environment is reported as a misconfiguration, not an absent-data outcome.

It uses a guaranteed-nonexistent temp path for (a) so the assertion is
deterministic regardless of whether the developer box happens to have the
default ``~/alpha_data/alpha_system`` store.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from alpha_system.research_lane.environment_preflight import (
    DATA_ROOT_NOT_FOUND_CODE,
    EnvironmentPreconditionStatus,
    evaluate_environment_preflight,
)
from alpha_system.research_lane.testability_gate import (
    CHECK_FEATURES_MATERIALIZED,
    GateStatus,
    _overall_status,
    _resolver_rejection_check,
)
from alpha_system.runtime.entry_contract import RuntimeEntryStatus
from alpha_system.runtime.input_resolver import (
    RuntimeInputResolverError,
    _data_root_precondition_reason,
    _reason,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _nonexistent_root() -> Path:
    """A path guaranteed not to exist (a fresh temp dir + a missing child)."""

    with tempfile.TemporaryDirectory(prefix="precondition-canary-") as tmp:
        candidate = Path(tmp) / "definitely-absent-data-root"
    # The TemporaryDirectory is removed on exit, so candidate cannot exist.
    return candidate


def _check_nonexistent_root_is_precondition_not_datagap() -> None:
    root = _nonexistent_root()
    _assert(not root.exists(), "canary setup invalid: temp root unexpectedly exists")

    # Explicit nonexistent root.
    explicit = evaluate_environment_preflight(alpha_data_root=root, env={})
    _assert(
        explicit.status is EnvironmentPreconditionStatus.ENVIRONMENT_NOT_CONFIGURED,
        f"explicit nonexistent root must be ENVIRONMENT_NOT_CONFIGURED, got {explicit.status}",
    )
    _assert(
        explicit.status.value != GateStatus.DATA_GAP.value,
        "explicit nonexistent root leaked the DATA_GAP masquerade",
    )
    _assert(
        explicit.issue_code == DATA_ROOT_NOT_FOUND_CODE,
        f"explicit nonexistent root issue_code drifted: {explicit.issue_code}",
    )

    # Unset env whose resolved default ALSO does not exist (pointed at the temp
    # nonexistent path via env, so the assertion holds on any host).
    via_env = evaluate_environment_preflight(env={"ALPHA_DATA_ROOT": root.as_posix()})
    _assert(
        via_env.status is EnvironmentPreconditionStatus.ENVIRONMENT_NOT_CONFIGURED,
        f"env-pointed nonexistent root must be ENVIRONMENT_NOT_CONFIGURED, got {via_env.status}",
    )


def _check_classification_boundary() -> None:
    # (b1) typed data-root precondition reason -> ENVIRONMENT_NOT_CONFIGURED.
    precondition = RuntimeInputResolverError(
        _data_root_precondition_reason(ValueError("ALPHA_DATA_ROOT is required for FeatureRegistry"))
    )
    env_check = _resolver_rejection_check(
        CHECK_FEATURES_MATERIALIZED,
        "feature packs are not resolvable",
        precondition,
    )
    _assert(
        env_check.status is GateStatus.ENVIRONMENT_NOT_CONFIGURED,
        f"typed precondition must classify ENVIRONMENT_NOT_CONFIGURED, got {env_check.status}",
    )

    # (b2) a genuinely-absent partition (any non-precondition reason) -> DATA_GAP.
    absent = RuntimeInputResolverError(
        _reason(
            code="feature_pack_not_found",
            message="feature version is not registered for this partition",
            field="feature_pack_refs",
            state=RuntimeEntryStatus.INPUTS_BLOCKED,
            expected="registered feature version",
            actual="missing",
        )
    )
    gap_check = _resolver_rejection_check(
        CHECK_FEATURES_MATERIALIZED,
        "feature packs are not resolvable",
        absent,
    )
    _assert(
        gap_check.status is GateStatus.DATA_GAP,
        f"genuinely-absent partition must stay DATA_GAP, got {gap_check.status}",
    )


def _check_rollup_ranking() -> None:
    env_check = _resolver_rejection_check(
        CHECK_FEATURES_MATERIALIZED,
        "feature packs are not resolvable",
        RuntimeInputResolverError(_data_root_precondition_reason(ValueError("unset"))),
    )
    gap_check = _resolver_rejection_check(
        CHECK_FEATURES_MATERIALIZED,
        "feature packs are not resolvable",
        RuntimeInputResolverError(
            _reason(
                code="feature_pack_not_found",
                message="missing",
                field="feature_pack_refs",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="registered feature version",
                actual="missing",
            )
        ),
    )
    rolled = _overall_status((gap_check, env_check))
    _assert(
        rolled is GateStatus.ENVIRONMENT_NOT_CONFIGURED,
        f"ENVIRONMENT_NOT_CONFIGURED must outrank DATA_GAP in the rollup, got {rolled}",
    )


def run_precondition_not_datagap_canary() -> None:
    """Run all precondition-vs-DATA_GAP assertions; raise on the first failure."""

    _check_nonexistent_root_is_precondition_not_datagap()
    _check_classification_boundary()
    _check_rollup_ranking()


def main(argv: list[str] | None = None) -> int:
    try:
        run_precondition_not_datagap_canary()
    except AssertionError as exc:
        print(f"FAIL precondition_not_datagap: {exc}", file=sys.stderr)
        return 1
    print(
        "precondition_not_datagap OK: unmet env precondition is "
        "ENVIRONMENT_NOT_CONFIGURED (not DATA_GAP); absent partition still DATA_GAP"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
