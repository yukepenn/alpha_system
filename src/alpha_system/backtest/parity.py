"""Deterministic fast/reference parity checking for ASV1-P19."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from alpha_system.backtest.fast_path import (
    FAST_PATH_MODE_ACCELERATED,
    FAST_PATH_MODE_REFERENCE_FALLBACK,
    FastPathRun,
    run_fast_path_backtest,
)
from alpha_system.backtest.parity_cases import ParityCase, ParityTolerance, parity_cases
from alpha_system.backtest.reference import run_reference_backtest
from alpha_system.backtest.results import ReferenceBacktestResult
from alpha_system.management.integration import run_reference_backtest_with_management


class ParityError(ValueError):
    """Raised when parity certification cannot be used safely."""


class FastPathGridGateError(ParityError):
    """Raised when grid code requests uncertified fast-path features."""


@dataclass(frozen=True, slots=True)
class ParityDifference:
    """One deterministic difference between reference and fast output."""

    domain: str
    path: str
    reference: Any
    candidate: Any

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "path": self.path,
            "reference": self.reference,
            "candidate": self.candidate,
        }


@dataclass(frozen=True, slots=True)
class ParityCaseResult:
    """Result of running one parity case."""

    case_id: str
    features: tuple[str, ...]
    fast_mode: str
    expected_mode: str
    passed: bool
    tolerance: ParityTolerance
    differences: tuple[ParityDifference, ...]
    reference_result: ReferenceBacktestResult
    fast_run: FastPathRun

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "features": list(self.features),
            "fast_mode": self.fast_mode,
            "expected_mode": self.expected_mode,
            "passed": self.passed,
            "tolerance": self.tolerance.to_dict(),
            "differences": [difference.to_dict() for difference in self.differences],
        }


@dataclass(frozen=True, slots=True)
class ParityCertification:
    """Parity certification result that later grid code can require."""

    phase_id: str
    certified: bool
    case_results: tuple[ParityCaseResult, ...]

    @property
    def accelerated_features(self) -> tuple[str, ...]:
        features: set[str] = set()
        for result in self.case_results:
            if result.passed and result.fast_mode == FAST_PATH_MODE_ACCELERATED:
                features.update(result.features)
        return tuple(sorted(features))

    @property
    def reference_fallback_features(self) -> tuple[str, ...]:
        features: set[str] = set()
        for result in self.case_results:
            if result.passed and result.fast_mode == FAST_PATH_MODE_REFERENCE_FALLBACK:
                features.update(result.features)
        return tuple(sorted(features))

    @property
    def failed_cases(self) -> tuple[str, ...]:
        return tuple(result.case_id for result in self.case_results if not result.passed)

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase_id": self.phase_id,
            "certified": self.certified,
            "accelerated_features": list(self.accelerated_features),
            "reference_fallback_features": list(self.reference_fallback_features),
            "failed_cases": list(self.failed_cases),
            "case_results": [result.to_dict() for result in self.case_results],
        }


def run_parity_case(case: ParityCase) -> ParityCaseResult:
    """Run one parity case against reference and fast path."""

    reference_result = _run_reference_case(case)
    fast_run = run_fast_path_backtest(
        bars=case.bars,
        signals=case.signals,
        config=case.config,
        management_spec=case.management_spec,
        requested_features=case.features,
        initial_cash=case.initial_cash,
        instrument_multipliers=case.resolved_instrument_multipliers,
        run_id=case.run_id,
        allow_reference_fallback=True,
    )
    differences = compare_reference_and_fast(
        reference_result,
        fast_run.result,
        tolerance=case.tolerance,
    )
    if fast_run.mode != case.expected_mode:
        differences = (
            *differences,
            ParityDifference(
                domain="mode",
                path="fast_mode",
                reference=case.expected_mode,
                candidate=fast_run.mode,
            ),
        )
    return ParityCaseResult(
        case_id=case.case_id,
        features=case.features,
        fast_mode=fast_run.mode,
        expected_mode=case.expected_mode,
        passed=not differences,
        tolerance=case.tolerance,
        differences=tuple(differences),
        reference_result=reference_result,
        fast_run=fast_run,
    )


def certify_parity(cases: Iterable[ParityCase] | None = None) -> ParityCertification:
    """Run all requested parity cases and return a reusable certification."""

    case_results = tuple(run_parity_case(case) for case in (tuple(cases) if cases is not None else parity_cases()))
    return ParityCertification(
        phase_id="ASV1-P19",
        certified=all(result.passed for result in case_results),
        case_results=case_results,
    )


def assert_grid_fast_path_allowed(
    certification: ParityCertification,
    required_features: Iterable[str],
) -> None:
    """Fail closed unless required features have accelerated parity certification."""

    requested = frozenset(str(feature) for feature in required_features)
    accelerated = frozenset(certification.accelerated_features)
    missing = tuple(sorted(requested.difference(accelerated)))
    if not certification.certified:
        msg = f"fast path parity certification has failed cases: {', '.join(certification.failed_cases)}"
        raise FastPathGridGateError(msg)
    if missing:
        msg = f"fast path grid use requires accelerated parity for: {', '.join(missing)}"
        raise FastPathGridGateError(msg)


def compare_reference_and_fast(
    reference: ReferenceBacktestResult,
    candidate: ReferenceBacktestResult,
    *,
    tolerance: ParityTolerance,
) -> tuple[ParityDifference, ...]:
    """Compare parity domains using deterministic serialized result payloads."""

    differences: list[ParityDifference] = []
    reference_payload = _parity_payload(reference)
    candidate_payload = _parity_payload(candidate)
    for domain in ("summary", "trades", "equity_curve", "fills"):
        differences.extend(
            _diff_values(
                domain=domain,
                path=domain,
                reference=reference_payload[domain],
                candidate=candidate_payload[domain],
                tolerance=_domain_tolerance(domain, tolerance),
            )
        )
    return tuple(differences)


def stable_result_digest(result: ReferenceBacktestResult) -> str:
    """Return stable JSON text for deterministic parity assertions."""

    return json.dumps(_parity_payload(result), sort_keys=True, separators=(",", ":"))


def _run_reference_case(case: ParityCase) -> ReferenceBacktestResult:
    if case.management_spec is not None:
        return run_reference_backtest_with_management(
            bars=case.bars,
            signals=case.signals,
            management_spec=case.management_spec,
            config=case.config,
            initial_cash=case.initial_cash,
            instrument_multipliers=case.resolved_instrument_multipliers,
            run_id=case.run_id,
        )
    return run_reference_backtest(
        bars=case.bars,
        signals=case.signals,
        config=case.config,
        initial_cash=case.initial_cash,
        instrument_multipliers=case.resolved_instrument_multipliers,
        run_id=case.run_id,
        output_dir=None,
        registry_path=None,
        run_manifest_path=None,
        write_outputs=False,
    )


def _parity_payload(result: ReferenceBacktestResult) -> dict[str, Any]:
    payload = result.to_dict()
    return {
        "summary": payload["summary"],
        "trades": payload["trades"],
        "equity_curve": payload["equity_curve"],
        "fills": payload["fills"],
    }


def _diff_values(
    *,
    domain: str,
    path: str,
    reference: Any,
    candidate: Any,
    tolerance: Decimal,
) -> tuple[ParityDifference, ...]:
    if isinstance(reference, Mapping) and isinstance(candidate, Mapping):
        differences: list[ParityDifference] = []
        keys = sorted(set(reference).union(candidate))
        for key in keys:
            differences.extend(
                _diff_values(
                    domain=domain,
                    path=f"{path}.{key}",
                    reference=reference.get(key),
                    candidate=candidate.get(key),
                    tolerance=tolerance,
                )
            )
        return tuple(differences)
    if isinstance(reference, Sequence) and not isinstance(reference, str) and isinstance(candidate, Sequence) and not isinstance(candidate, str):
        differences = []
        if len(reference) != len(candidate):
            differences.append(
                ParityDifference(
                    domain=domain,
                    path=f"{path}.length",
                    reference=len(reference),
                    candidate=len(candidate),
                )
            )
        for index, (left, right) in enumerate(zip(reference, candidate, strict=False)):
            differences.extend(
                _diff_values(
                    domain=domain,
                    path=f"{path}[{index}]",
                    reference=left,
                    candidate=right,
                    tolerance=tolerance,
                )
            )
        return tuple(differences)
    if _equal_with_tolerance(reference, candidate, tolerance):
        return ()
    return (
        ParityDifference(
            domain=domain,
            path=path,
            reference=reference,
            candidate=candidate,
        ),
    )


def _equal_with_tolerance(reference: Any, candidate: Any, tolerance: Decimal) -> bool:
    if reference == candidate:
        return True
    left = _optional_decimal(reference)
    right = _optional_decimal(candidate)
    if left is not None and right is not None:
        return abs(left - right) <= tolerance
    return False


def _optional_decimal(value: Any) -> Decimal | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _domain_tolerance(domain: str, tolerance: ParityTolerance) -> Decimal:
    if domain == "summary":
        return tolerance.summary_decimal
    if domain == "trades":
        return tolerance.trade_decimal
    if domain == "equity_curve":
        return tolerance.equity_decimal
    if domain == "fills":
        return tolerance.fill_decimal
    return Decimal("0")


__all__ = [
    "FastPathGridGateError",
    "ParityCaseResult",
    "ParityCertification",
    "ParityDifference",
    "ParityError",
    "assert_grid_fast_path_allowed",
    "certify_parity",
    "compare_reference_and_fast",
    "run_parity_case",
    "stable_result_digest",
]
