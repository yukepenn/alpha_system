"""Executable synthetic governance negative-control canary harness."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from types import MappingProxyType
from typing import Any, cast

from alpha_system.backtest.conservative_semantics import (
    ConservativeSemanticsError,
    signal_fill_bar_is_allowed,
)
from alpha_system.backtest.execution_config import ExecutionConfig, ExecutionConfigError
from alpha_system.governance.canaries.catalog import (
    NegativeControlType,
    REQUIRED_NEGATIVE_CONTROL_TYPES,
    expected_failure_for_canary_type,
)
from alpha_system.governance.canaries.negative_control_result import (
    NegativeControlPassFail,
    NegativeControlResult,
    create_negative_control_result,
)
from alpha_system.governance.label_leakage_guard import (
    LabelLeakageFindingKind,
    check_label_leakage,
)

CanaryFixture = Mapping[str, Any]
CanaryGuard = Callable[[CanaryFixture], bool]

EXECUTABLE_NEGATIVE_CONTROL_TYPES = (
    NegativeControlType.RANDOM_TARGET,
    NegativeControlType.PERMUTED_LABELS,
    NegativeControlType.FUTURE_SHIFT,
    NegativeControlType.OPTIMISTIC_FILL,
)

DEFAULT_CANARY_FIXTURE_PATHS: Mapping[NegativeControlType, Path] = MappingProxyType(
    {
        NegativeControlType.RANDOM_TARGET: Path(
            "evals/canaries/random_target/synthetic_fixture.json"
        ),
        NegativeControlType.FUTURE_SHIFT: Path(
            "evals/canaries/future_shift/synthetic_fixture.json"
        ),
        NegativeControlType.PERMUTED_LABELS: Path(
            "evals/canaries/permuted_labels/synthetic_fixture.json"
        ),
        NegativeControlType.OPTIMISTIC_FILL: Path(
            "evals/canaries/optimistic_fill/synthetic_fixture.json"
        ),
    }
)

_MISSED_RESULT_BY_TYPE = MappingProxyType(
    {
        NegativeControlType.RANDOM_TARGET: "guard_accepted_known_bad_random_target_signal",
        NegativeControlType.FUTURE_SHIFT: "guard_missed_future_shift_lookahead",
        NegativeControlType.PERMUTED_LABELS: "guard_accepted_known_bad_permuted_label_signal",
        NegativeControlType.OPTIMISTIC_FILL: "guard_accepted_known_bad_optimistic_fill_assumption",
    }
)


def load_default_canary_fixture(
    canary_type: NegativeControlType | str,
) -> CanaryFixture:
    """Load the tiny synthetic default fixture for one executable canary."""

    active_type = _executable_canary_type(canary_type)
    fixture_path = _repo_root() / DEFAULT_CANARY_FIXTURE_PATHS[active_type]
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        msg = f"canary fixture root must be a mapping: {fixture_path}"
        raise ValueError(msg)
    return cast(CanaryFixture, payload)


def run_governance_canary(
    canary_type: NegativeControlType | str,
    fixture: CanaryFixture | None = None,
    *,
    random_target_guard: CanaryGuard | None = None,
    future_shift_guard: CanaryGuard | None = None,
    label_leakage_guard: CanaryGuard | None = None,
    optimistic_fill_guard: CanaryGuard | None = None,
) -> NegativeControlResult:
    """Run one executable governance canary and return a validated result."""

    active_type = _executable_canary_type(canary_type)
    if active_type is NegativeControlType.RANDOM_TARGET:
        return run_random_target_canary(
            fixture,
            guard=random_target_guard,
        )
    if active_type is NegativeControlType.FUTURE_SHIFT:
        return run_future_shift_canary(
            fixture,
            guard=future_shift_guard,
        )
    if active_type is NegativeControlType.PERMUTED_LABELS:
        return run_label_leakage_canary(
            fixture,
            guard=label_leakage_guard,
        )
    return run_optimistic_fill_canary(
        fixture,
        guard=optimistic_fill_guard,
    )


def run_required_governance_canaries() -> tuple[NegativeControlResult, ...]:
    """Run all required executable governance canaries in canonical order."""

    return tuple(
        run_governance_canary(canary_type)
        for canary_type in EXECUTABLE_NEGATIVE_CONTROL_TYPES
    )


def run_random_target_canary(
    fixture: CanaryFixture | None = None,
    *,
    guard: CanaryGuard | None = None,
) -> NegativeControlResult:
    """Run the seeded random-target canary over a synthetic fixture."""

    active_fixture = fixture or load_default_canary_fixture(
        NegativeControlType.RANDOM_TARGET
    )
    return _result_for_guard_outcome(
        canary_type=NegativeControlType.RANDOM_TARGET,
        fixture=active_fixture,
        guard=guard or _random_target_guard,
    )


def run_future_shift_canary(
    fixture: CanaryFixture | None = None,
    *,
    guard: CanaryGuard | None = None,
) -> NegativeControlResult:
    """Run the no-lookahead future-shift canary over a synthetic fixture."""

    active_fixture = fixture or load_default_canary_fixture(
        NegativeControlType.FUTURE_SHIFT
    )
    return _result_for_guard_outcome(
        canary_type=NegativeControlType.FUTURE_SHIFT,
        fixture=active_fixture,
        guard=guard or _future_shift_guard,
    )


def run_label_leakage_canary(
    fixture: CanaryFixture | None = None,
    *,
    guard: CanaryGuard | None = None,
) -> NegativeControlResult:
    """Run the label-integrity canary through the label-leakage guard."""

    active_fixture = fixture or load_default_canary_fixture(
        NegativeControlType.PERMUTED_LABELS
    )
    return _result_for_guard_outcome(
        canary_type=NegativeControlType.PERMUTED_LABELS,
        fixture=active_fixture,
        guard=guard or _label_leakage_guard,
    )


def run_optimistic_fill_canary(
    fixture: CanaryFixture | None = None,
    *,
    guard: CanaryGuard | None = None,
) -> NegativeControlResult:
    """Run the optimistic-fill canary through execution-assumption guards."""

    active_fixture = fixture or load_default_canary_fixture(
        NegativeControlType.OPTIMISTIC_FILL
    )
    return _result_for_guard_outcome(
        canary_type=NegativeControlType.OPTIMISTIC_FILL,
        fixture=active_fixture,
        guard=guard or _optimistic_fill_guard,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for local canary-runner integration."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--canary",
        action="append",
        choices=tuple(canary_type.value for canary_type in EXECUTABLE_NEGATIVE_CONTROL_TYPES),
        help="Executable governance canary to run. May be provided more than once.",
    )
    args = parser.parse_args(argv)
    requested = tuple(
        args.canary
        or (canary_type.value for canary_type in EXECUTABLE_NEGATIVE_CONTROL_TYPES)
    )

    results = tuple(run_governance_canary(canary_type) for canary_type in requested)
    for result in results:
        print(f"{result.pass_fail.value} {result.canary_type.value} {result.observed_result}")
    return 0 if all(result.guard_caught_injected_fault for result in results) else 1


def _result_for_guard_outcome(
    *,
    canary_type: NegativeControlType,
    fixture: CanaryFixture,
    guard: CanaryGuard,
) -> NegativeControlResult:
    expected_failure = expected_failure_for_canary_type(canary_type)
    guard_caught_fault = bool(guard(fixture))
    observed_result = (
        expected_failure
        if guard_caught_fault
        else _MISSED_RESULT_BY_TYPE[canary_type]
    )
    return create_negative_control_result(
        canary_type=canary_type,
        expected_failure=expected_failure,
        observed_result=observed_result,
        pass_fail=(
            NegativeControlPassFail.PASS
            if guard_caught_fault
            else NegativeControlPassFail.FAIL
        ),
        related_study_or_evidence=_required_text(fixture, "related_study_or_evidence"),
        notes=_result_notes(fixture, guard_caught_fault=guard_caught_fault),
    )


def _random_target_guard(fixture: CanaryFixture) -> bool:
    replacement = _required_mapping(fixture, "target_replacement")
    if _required_text(replacement, "mode") != "seeded_random_target":
        return False
    _required_text(replacement, "replaces")

    seed = _required_int(fixture, "seed")
    sample_count = _required_int(fixture, "sample_count")
    if sample_count < 2:
        msg = "random-target canary sample_count must be at least 2"
        raise ValueError(msg)
    expected_digest = _required_text(fixture, "random_target_digest")
    if _seeded_random_target_digest(seed=seed, sample_count=sample_count) != expected_digest:
        return False

    outcome = _required_mapping(fixture, "pipeline_outcome")
    if _required_bool(outcome, "surviving_signal"):
        return False
    decision = _required_text(outcome, "decision")
    reason = _required_text(outcome, "reason")
    return decision in {"BLOCKED", "REJECTED"} and reason == "seeded_random_target_no_surviving_signal"


def _future_shift_guard(fixture: CanaryFixture) -> bool:
    result = check_label_leakage(
        _required_mapping(fixture, "label_spec"),
        _required_sequence(fixture, "features"),
    )
    return result.blocked and any(
        finding.kind is LabelLeakageFindingKind.LOOKAHEAD
        for finding in result.findings
    )


def _label_leakage_guard(fixture: CanaryFixture) -> bool:
    result = check_label_leakage(
        _required_mapping(fixture, "label_spec"),
        _required_sequence(fixture, "features"),
    )
    return result.blocked and any(
        finding.kind is LabelLeakageFindingKind.LABEL_AS_FEATURE
        for finding in result.findings
    )


def _optimistic_fill_guard(fixture: CanaryFixture) -> bool:
    config_rejected = False
    try:
        ExecutionConfig.from_mapping(_required_mapping(fixture, "execution_config"))
    except (ConservativeSemanticsError, ExecutionConfigError):
        config_rejected = True

    fill = _required_mapping(fixture, "same_bar_fill")
    same_bar_blocked = not signal_fill_bar_is_allowed(
        signal_bar_index=int(fill["signal_bar_index"]),
        fill_bar_index=int(fill["fill_bar_index"]),
    )
    return config_rejected and same_bar_blocked


def _seeded_random_target_digest(*, seed: int, sample_count: int) -> str:
    rng = random.Random(seed)
    target = [rng.choice((-1, 1)) for _ in range(sample_count)]
    payload = {
        "sample_count": sample_count,
        "seed": seed,
        "target": target,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _result_notes(fixture: CanaryFixture, *, guard_caught_fault: bool) -> str:
    outcome = (
        "guard caught the injected known-bad fault"
        if guard_caught_fault
        else "guard missed the injected known-bad fault"
    )
    return (
        f"{_required_text(fixture, 'fixture_id')}: "
        f"{_required_text(fixture, 'notes')} Outcome: {outcome}."
    )


def _executable_canary_type(canary_type: NegativeControlType | str) -> NegativeControlType:
    active_type = NegativeControlType(canary_type)
    if active_type not in EXECUTABLE_NEGATIVE_CONTROL_TYPES:
        supported = ", ".join(canary.value for canary in EXECUTABLE_NEGATIVE_CONTROL_TYPES)
        msg = (
            f"{active_type.value} is catalogued but not executable; "
            f"supported: {supported}"
        )
        raise ValueError(msg)
    return active_type


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "evals" / "canaries").is_dir():
            return parent
    msg = "could not locate repository root containing evals/canaries"
    raise FileNotFoundError(msg)


def _required_mapping(fixture: CanaryFixture, field: str) -> Mapping[str, Any]:
    value = fixture.get(field)
    if not isinstance(value, Mapping):
        msg = f"canary fixture field {field!r} must be a mapping"
        raise ValueError(msg)
    return cast(Mapping[str, Any], value)


def _required_sequence(fixture: CanaryFixture, field: str) -> Sequence[Any]:
    value = fixture.get(field)
    if isinstance(value, str) or not isinstance(value, Sequence):
        msg = f"canary fixture field {field!r} must be a sequence"
        raise ValueError(msg)
    return value


def _required_text(fixture: CanaryFixture, field: str) -> str:
    value = fixture.get(field)
    if not isinstance(value, str) or not value.strip():
        msg = f"canary fixture field {field!r} must be a non-empty string"
        raise ValueError(msg)
    return value.strip()


def _required_int(fixture: CanaryFixture, field: str) -> int:
    value = fixture.get(field)
    if type(value) is not int:
        msg = f"canary fixture field {field!r} must be an integer"
        raise ValueError(msg)
    return value


def _required_bool(fixture: CanaryFixture, field: str) -> bool:
    value = fixture.get(field)
    if type(value) is not bool:
        msg = f"canary fixture field {field!r} must be a boolean"
        raise ValueError(msg)
    return value


if tuple(canary.value for canary in EXECUTABLE_NEGATIVE_CONTROL_TYPES) != (
    REQUIRED_NEGATIVE_CONTROL_TYPES
):
    msg = "executable negative controls must exactly match the required catalog order"
    raise RuntimeError(msg)


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "CanaryFixture",
    "CanaryGuard",
    "DEFAULT_CANARY_FIXTURE_PATHS",
    "EXECUTABLE_NEGATIVE_CONTROL_TYPES",
    "load_default_canary_fixture",
    "main",
    "run_future_shift_canary",
    "run_governance_canary",
    "run_label_leakage_canary",
    "run_optimistic_fill_canary",
    "run_random_target_canary",
    "run_required_governance_canaries",
]
