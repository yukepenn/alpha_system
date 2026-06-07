"""Content-addressing identity invariants for FeatureVersion.

These tests pin the keystone fix: a feature's content-addressed identity
(feature_version_id) must be a pure function of the COMPUTATIONAL contract and
independent of registry state / request provenance (feature_request_id).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from alpha_system.features.contracts import (
    FeatureFamily,
    FeatureInputSpec,
    FeatureLineageRecord,
    FeatureSpec,
    FeatureVersion,
    NormalizationSpec,
    TransformSpec,
    WindowCausality,
    WindowKind,
    WindowSpec,
)
from alpha_system.features.families.ohlcv import (
    OHLCVFeatureName,
    build_ohlcv_feature_definition,
)
from alpha_system.features.request_gate import evaluate_feature_request_gate
from alpha_system.governance.duplicate_exposure import (
    ExposureCheckResult,
    ExposureRegistryStatus,
)
from alpha_system.governance.feature_request import (
    FeatureRequest,
    FeatureRequestApprovalStatus,
    create_feature_request,
)

ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd0"


class _EmptyRegistryReader:
    """Registry reader reporting an empty (EMPTY-status) registry population."""

    def read_factor_versions(self) -> list[dict[str, object]]:
        return []


class _PopulatedRegistryReader:
    """Registry reader reporting a populated (CHECKED-status) registry.

    The single entry never matches the feature under test, so the duplicate
    exposure guard admits the request but reports CHECKED rather than EMPTY,
    which is exactly how the gate regenerates a different feature_request_id at
    materialize time once the registry is non-empty.
    """

    def read_factor_versions(self) -> list[dict[str, object]]:
        return [
            {
                "factor_id": "fac_unrelated_population",
                "name": "unrelated_population",
                "description": "unrelated registry occupant",
                "metadata": {"exposure_family": "totally_unrelated_family"},
                "parameters": {},
                "factor_version": 1,
            }
        ]


def _feature_request(*, exposure_family: str) -> FeatureRequest:
    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    return create_feature_request(
        alpha_spec_id=ALPHA_SPEC_ID,
        requested_inputs=[exposure_family],
        formula_sketch={
            "exposure_family": exposure_family,
            "inputs": ["synthetic_close"],
            "operation": "pct_change",
            "window": 1,
        },
        availability_assumptions={
            "timing": "synthetic feature inputs are available after fixture bars close"
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": ["synthetic_close"],
            "source": "tiny synthetic fixture fields only",
        },
        approval_status=FeatureRequestApprovalStatus.APPROVED,
    )


def _two_distinct_request_ids() -> tuple[str, str]:
    """Return two distinct governed feature_request_id values."""

    first = _feature_request(exposure_family="exposure_family_alpha").feature_request_id
    second = _feature_request(exposure_family="exposure_family_beta").feature_request_id
    assert first != second
    return first, second


def _feature_spec(
    *,
    feature_request_id: str,
    feature_id: str = "base_ohlcv_close_return_1m",
    transform_id: str = "close_return",
    transform_parameters: dict[str, object] | None = None,
    window_length: int = 1,
    fields: tuple[str, ...] = ("close", "available_ts"),
) -> FeatureSpec:
    return FeatureSpec(
        feature_id=feature_id,
        family=FeatureFamily.BASE_OHLCV,
        feature_request_id=feature_request_id,
        inputs=FeatureInputSpec(
            input_views=("canonical_ohlcv",),
            fields=fields,
            dataset_version_ids=("dsv_fixture",),
        ),
        transform=TransformSpec(
            transform_id=transform_id,
            parameters=transform_parameters or {"lag": 1},
        ),
        window=WindowSpec(
            kind=WindowKind.ROLLING,
            length=window_length,
            causality=WindowCausality.CAUSAL,
            offline_only=False,
        ),
        normalization=NormalizationSpec(normalization_id="identity"),
        availability_assumptions={
            "source": "canonical OHLCV available_ts from accepted DatasetVersion"
        },
        available_ts_derivation_rule="feature.available_ts = max(input.available_ts)",
        live=True,
    )


def test_to_identity_dict_excludes_feature_request_id() -> None:
    request_id, _ = _two_distinct_request_ids()
    spec = _feature_spec(feature_request_id=request_id)
    contract = spec.to_contract_dict()
    identity = spec.to_identity_dict()
    assert "feature_request_id" in contract
    assert "feature_request_id" not in identity
    # Identity is the contract minus exactly the request-provenance key.
    expected = {k: v for k, v in contract.items() if k != "feature_request_id"}
    assert identity == expected


def test_identity_is_independent_of_feature_request_id() -> None:
    # The exact bug: same computational feature, different request provenance.
    request_a, request_b = _two_distinct_request_ids()
    spec_a = _feature_spec(feature_request_id=request_a)
    spec_b = _feature_spec(feature_request_id=request_b)
    assert spec_a.feature_request_id != spec_b.feature_request_id
    assert (
        spec_a.derive_feature_version().feature_version_id
        == spec_b.derive_feature_version().feature_version_id
    )


def test_identity_is_deterministic_across_calls() -> None:
    request_id, _ = _two_distinct_request_ids()
    spec = _feature_spec(feature_request_id=request_id)
    first = FeatureVersion.derive(spec).feature_version_id
    second = FeatureVersion.derive(spec).feature_version_id
    assert first == second


@pytest.mark.parametrize(
    "overrides",
    [
        {"feature_id": "base_ohlcv_close_return_other"},
        {"transform_id": "log_return"},
        {"transform_parameters": {"lag": 2}},
        {"window_length": 5},
        {"fields": ("open", "available_ts")},
    ],
)
def test_collision_sensitivity_preserved(overrides: dict[str, object]) -> None:
    # Any change to a computational field must change the identity.
    request_id, _ = _two_distinct_request_ids()
    base = _feature_spec(feature_request_id=request_id)
    variant = _feature_spec(feature_request_id=request_id, **overrides)
    assert (
        base.derive_feature_version().feature_version_id
        != variant.derive_feature_version().feature_version_id
    )


def test_lineage_round_trip_validates_with_matching_version_and_request() -> None:
    request_id, _ = _two_distinct_request_ids()
    spec = _feature_spec(feature_request_id=request_id)
    version = spec.derive_feature_version()
    lineage = FeatureLineageRecord(
        feature_version=version,
        feature_spec=spec,
        feature_request_id=spec.feature_request_id,
        contract_provenance={"phase": "identity-invariant"},
    )
    # Field match invariant still holds: lineage request id == spec request id.
    assert lineage.feature_request_id == spec.feature_request_id
    assert lineage.feature_version == version


def test_ohlcv_family_identity_is_registry_state_independent() -> None:
    # Drive the real ohlcv family build path against an EMPTY-state request and a
    # CHECKED-state request (different feature_request_id, because the gate
    # regenerates it from registry population) for the SAME feature. The
    # resulting feature_version_id must be identical.
    empty_reader = _EmptyRegistryReader()
    populated_reader = _PopulatedRegistryReader()

    base_request = _feature_request(exposure_family="exposure_family_state_test")

    # EMPTY-state request id vs CHECKED-state request id for the SAME feature.
    empty_decision = evaluate_feature_request_gate(base_request, empty_reader)
    checked_decision = evaluate_feature_request_gate(base_request, populated_reader)
    empty_state_request = empty_decision.checked_feature_request
    checked_state_request = checked_decision.checked_feature_request
    assert empty_state_request is not None
    assert checked_state_request is not None
    # The two request ids differ purely because of registry state (EMPTY vs
    # CHECKED exposure notes leak into the request id). This is the bug source.
    assert (
        empty_state_request.feature_request_id
        != checked_state_request.feature_request_id
    )

    empty_definition = build_ohlcv_feature_definition(
        OHLCVFeatureName.RTH_FLAG,
        empty_state_request,
        empty_reader,
        dataset_version_ids=("dsv_fixture",),
        window_length=1,
        reset_on_session=False,
    )
    checked_definition = build_ohlcv_feature_definition(
        OHLCVFeatureName.RTH_FLAG,
        checked_state_request,
        populated_reader,
        dataset_version_ids=("dsv_fixture",),
        window_length=1,
        reset_on_session=False,
    )

    # Sanity: the underlying specs carry different request provenance...
    assert (
        empty_definition.spec.feature_request_id
        != checked_definition.spec.feature_request_id
    )
    # ...yet content-addressed identity is identical.
    assert (
        empty_definition.version.feature_version_id
        == checked_definition.version.feature_version_id
    )


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
