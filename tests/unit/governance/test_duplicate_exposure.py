from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from alpha_system.governance.duplicate_exposure import (
    ExposureCheckResult,
    ExposureFindingKind,
    ExposureFindingSeverity,
    ExposureRegistryStatus,
    apply_duplicate_exposure_notes,
    check_duplicate_exposure,
    find_duplicate_exposures,
)
from alpha_system.governance.feature_request import (
    FeatureRequest,
    FeatureRequestApprovalStatus,
    create_feature_request,
)


REGISTRY_FIXTURE_PATH = Path("tests/fixtures/governance/duplicate_exposure_registry.json")
ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd0"


class ReadOnlyRegistrySpy:
    def __init__(self, entries: list[dict[str, Any]]) -> None:
        self.entries = entries
        self.read_calls = 0
        self.write_calls: list[str] = []

    def read_factor_versions(self) -> list[dict[str, Any]]:
        self.read_calls += 1
        return deepcopy(self.entries)

    def register_factor_spec(self, *_args: object, **_kwargs: object) -> None:
        self.write_calls.append("register_factor_spec")
        raise AssertionError("guard attempted to mutate the registry")

    def record_factor_validation_run(self, *_args: object, **_kwargs: object) -> None:
        self.write_calls.append("record_factor_validation_run")
        raise AssertionError("guard attempted to record validation")

    def record_promotion_decision(self, *_args: object, **_kwargs: object) -> None:
        self.write_calls.append("record_promotion_decision")
        raise AssertionError("guard attempted to record promotion")


class UnavailableRegistry:
    def read_factor_versions(self) -> list[dict[str, Any]]:
        raise RuntimeError("synthetic registry unavailable")


def load_registry_fixture() -> list[dict[str, Any]]:
    return json.loads(REGISTRY_FIXTURE_PATH.read_text(encoding="utf-8"))


def make_request(
    *,
    requested_inputs: list[str],
    formula_sketch: dict[str, object],
) -> FeatureRequest:
    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    return create_feature_request(
        alpha_spec_id=ALPHA_SPEC_ID,
        requested_inputs=requested_inputs,
        formula_sketch=formula_sketch,
        availability_assumptions={
            "timing": "synthetic feature inputs are available only after fixture bars close"
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": ["synthetic_close"],
            "source": "tiny synthetic fixture fields only",
        },
    )


def test_clear_duplicate_is_flagged_blocking_and_updates_notes() -> None:
    request = make_request(
        requested_inputs=["synthetic_close_return_1d"],
        formula_sketch={
            "exposure_family": "synthetic_close_return_1d",
            "inputs": ["synthetic_close"],
            "operation": "pct_change",
            "window": 1,
        },
    )
    registry = ReadOnlyRegistrySpy(load_registry_fixture())

    result = check_duplicate_exposure(request, registry)

    assert registry.read_calls == 1
    assert registry.write_calls == []
    assert result.registry_status is ExposureRegistryStatus.CHECKED
    assert result.registry_entries_checked == 2
    assert len(result.findings) == 1
    finding = result.findings[0]
    assert finding.kind is ExposureFindingKind.DUPLICATE
    assert finding.severity is ExposureFindingSeverity.BLOCKING
    assert finding.matched_registry_reference["factor_id"] == "synthetic_close_return_1d"
    assert finding.matched_registry_reference["factor_version"] == "v1"

    updated = apply_duplicate_exposure_notes(request, result)

    assert updated.approval_status == FeatureRequestApprovalStatus.BLOCKED_DUPLICATE.value
    assert updated.duplicate_or_equivalent_exposure_notes["findings"][0]["severity"] == "BLOCKING"


def test_equivalent_exposure_is_flagged_warning() -> None:
    request = make_request(
        requested_inputs=["synthetic_close_standard_score_20d"],
        formula_sketch={
            "exposure_family": "synthetic_close_standard_score_20d",
            "inputs": ["synthetic_close"],
            "operation": "standard_score",
            "window": 20,
        },
    )
    registry = ReadOnlyRegistrySpy(load_registry_fixture())

    findings = find_duplicate_exposures(request, registry)

    assert registry.read_calls == 1
    assert registry.write_calls == []
    assert len(findings) == 1
    assert findings[0].kind is ExposureFindingKind.EQUIVALENT
    assert findings[0].severity is ExposureFindingSeverity.WARNING
    assert findings[0].matched_registry_reference["factor_id"] == "synthetic_close_zscore_20d"


def test_distinct_request_is_not_flagged() -> None:
    request = make_request(
        requested_inputs=["synthetic_volume_rank_5d"],
        formula_sketch={
            "exposure_family": "synthetic_volume_rank_5d",
            "inputs": ["synthetic_volume"],
            "operation": "rank",
            "window": 5,
        },
    )
    registry = ReadOnlyRegistrySpy(load_registry_fixture())

    result = check_duplicate_exposure(request, registry)

    assert registry.read_calls == 1
    assert registry.write_calls == []
    assert result.findings == ()
    assert result.registry_status is ExposureRegistryStatus.CHECKED


def test_unavailable_registry_degrades_without_crashing_or_clean_claim() -> None:
    request = make_request(
        requested_inputs=["synthetic_close_return_1d"],
        formula_sketch={
            "exposure_family": "synthetic_close_return_1d",
            "inputs": ["synthetic_close"],
            "operation": "pct_change",
            "window": 1,
        },
    )

    result = check_duplicate_exposure(request, UnavailableRegistry())

    assert result.findings == ()
    assert result.registry_status is ExposureRegistryStatus.UNAVAILABLE
    assert "unavailable" in result.to_notes()["summary"]
