"""Content-addressing identity invariants for FeatureVersion.

These tests pin the keystone fix: a feature's content-addressed identity
(feature_version_id) must be a pure function of the COMPUTATIONAL contract and
independent of registry state / request provenance (feature_request_id).
"""

from __future__ import annotations

from datetime import UTC, datetime, time

import pytest

import alpha_system.features.families.bbo.family as bbo_family
import alpha_system.features.families.cross_market.family as cross_market_family
import alpha_system.features.families.ohlcv.family as ohlcv_family
import alpha_system.features.families.structure.family as structure_family
from alpha_system.data.foundation.sessions import (
    SessionTemplate,
    load_session_template_by_id,
)
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
from alpha_system.features.families.bbo import (
    BBOFeatureName,
    build_bbo_feature_definition,
)
from alpha_system.features.families.cross_market import (
    CrossMarketFeatureName,
    build_cross_market_feature_definition,
)
from alpha_system.features.families.structure import (
    StructureFeatureName,
    build_structure_feature_definition,
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
SESSION_TRUTH_KEYS = frozenset(
    {
        "session_template_id",
        "session_timezone",
        "rth_open_time_local",
        "rth_close_time_local",
        "session_truth_source",
    }
)


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


@pytest.mark.parametrize(
    "feature_name",
    (
        OHLCVFeatureName.RETURNS,
        OHLCVFeatureName.VWAP,
    ),
)
def test_session_conditioned_ohlcv_identity_includes_template_truth(
    feature_name: OHLCVFeatureName,
) -> None:
    request = _feature_request(exposure_family=f"session_truth_{feature_name.value}")
    definition = build_ohlcv_feature_definition(
        feature_name,
        request,
        _EmptyRegistryReader(),
        dataset_version_ids=("dsv_fixture",),
        window_length=2,
        reset_on_session=True,
    )

    parameters = definition.spec.to_identity_dict()["transform"]["parameters"]
    expected = _session_truth_parameters()

    for key, value in expected.items():
        assert parameters[key] == value

    legacy_parameters = {
        key: value
        for key, value in parameters.items()
        if key not in SESSION_TRUTH_KEYS
    }
    legacy_spec = _copy_spec_with_transform_parameters(definition, legacy_parameters)

    assert (
        definition.spec.derive_feature_version().feature_version_id
        != legacy_spec.derive_feature_version().feature_version_id
    )


@pytest.mark.parametrize(
    "feature_name",
    (
        OHLCVFeatureName.RETURNS,
        OHLCVFeatureName.VOLUME_ZSCORE,
        OHLCVFeatureName.ROLLING_RANGE,
    ),
)
def test_non_session_conditioned_ohlcv_identity_ignores_session_template_changes(
    monkeypatch: pytest.MonkeyPatch,
    feature_name: OHLCVFeatureName,
) -> None:
    base_request = _feature_request(
        exposure_family=f"non_session_conditioned_{feature_name.value}"
    )
    base = build_ohlcv_feature_definition(
        feature_name,
        base_request,
        _EmptyRegistryReader(),
        dataset_version_ids=("dsv_fixture",),
        window_length=2,
        reset_on_session=False,
    )

    def _alternate_template(
        template_id: str = "session_cme_index_futures_eth",
        path: object | None = None,
    ) -> SessionTemplate:
        del template_id, path
        return SessionTemplate(
            template_id="session_cme_index_futures_eth",
            timezone="America/Chicago",
            rth_start=time(9, 0),
            rth_end=time(15, 0),
            eth_start=time(17, 0),
            eth_end=time(16, 0),
            maintenance_breaks=(),
            source="synthetic unit test",
        )

    monkeypatch.setattr(ohlcv_family, "load_session_template_by_id", _alternate_template)
    variant = build_ohlcv_feature_definition(
        feature_name,
        base_request,
        _EmptyRegistryReader(),
        dataset_version_ids=("dsv_fixture",),
        window_length=2,
        reset_on_session=False,
    )

    assert (
        base.version.feature_version_id
        == variant.version.feature_version_id
    )
    assert SESSION_TRUTH_KEYS.isdisjoint(
        variant.spec.to_identity_dict()["transform"]["parameters"]
    )


def test_remaining_session_conditioned_family_identities_include_template_truth() -> None:
    definitions = (
        build_structure_feature_definition(
            StructureFeatureName.PRIOR_HIGH_DISTANCE,
            _feature_request(exposure_family="session_truth_structure_prior_high"),
            _EmptyRegistryReader(),
            dataset_version_ids=("dsv_fixture",),
            window_length=2,
            reset_on_session=True,
        ),
        build_bbo_feature_definition(
            BBOFeatureName.SPREAD_ZSCORE,
            _feature_request(exposure_family="session_truth_bbo_spread_zscore"),
            _EmptyRegistryReader(),
            dataset_version_ids=("dsv_fixture",),
            window_length=2,
            reset_on_session=True,
        ),
        build_cross_market_feature_definition(
            CrossMarketFeatureName.SYNCHRONIZED_RETURNS,
            _feature_request(exposure_family="session_truth_cross_market_returns"),
            _EmptyRegistryReader(),
            dataset_version_ids=("dsv_fixture",),
            window_length=2,
            reset_on_session=True,
        ),
    )

    for definition in definitions:
        spec = _feature_spec_from_definition(definition)
        parameters = spec.to_identity_dict()["transform"]["parameters"]
        expected = _session_truth_parameters()

        for key, value in expected.items():
            assert parameters[key] == value

        legacy_parameters = {
            key: value
            for key, value in parameters.items()
            if key not in SESSION_TRUTH_KEYS
        }
        legacy_spec = _copy_spec_with_transform_parameters(definition, legacy_parameters)

        assert (
            spec.derive_feature_version().feature_version_id
            != legacy_spec.derive_feature_version().feature_version_id
        )


def test_remaining_non_session_conditioned_identities_ignore_session_template_changes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    structure_request = _feature_request(
        exposure_family="non_session_conditioned_structure_prior_high"
    )
    bbo_request = _feature_request(exposure_family="non_session_conditioned_bbo_mid")
    cross_request = _feature_request(
        exposure_family="non_session_conditioned_cross_market_returns"
    )
    base_structure = build_structure_feature_definition(
        StructureFeatureName.PRIOR_HIGH_DISTANCE,
        structure_request,
        _EmptyRegistryReader(),
        dataset_version_ids=("dsv_fixture",),
        window_length=2,
        reset_on_session=False,
    )
    base_bbo = build_bbo_feature_definition(
        BBOFeatureName.MID,
        bbo_request,
        _EmptyRegistryReader(),
        dataset_version_ids=("dsv_fixture",),
        reset_on_session=False,
    )
    base_cross = build_cross_market_feature_definition(
        CrossMarketFeatureName.SYNCHRONIZED_RETURNS,
        cross_request,
        _EmptyRegistryReader(),
        dataset_version_ids=("dsv_fixture",),
        window_length=2,
        reset_on_session=False,
    )

    def _alternate_template(
        template_id: str = "session_cme_index_futures_eth",
        path: object | None = None,
    ) -> SessionTemplate:
        del template_id, path
        return SessionTemplate(
            template_id="session_cme_index_futures_eth",
            timezone="America/Chicago",
            rth_start=time(9, 0),
            rth_end=time(15, 0),
            eth_start=time(17, 0),
            eth_end=time(16, 0),
            maintenance_breaks=(),
            source="synthetic unit test",
        )

    monkeypatch.setattr(structure_family, "default_session_template", _alternate_template)
    monkeypatch.setattr(bbo_family, "default_session_template", _alternate_template)
    monkeypatch.setattr(cross_market_family, "default_session_template", _alternate_template)

    variant_structure = build_structure_feature_definition(
        StructureFeatureName.PRIOR_HIGH_DISTANCE,
        structure_request,
        _EmptyRegistryReader(),
        dataset_version_ids=("dsv_fixture",),
        window_length=2,
        reset_on_session=False,
    )
    variant_bbo = build_bbo_feature_definition(
        BBOFeatureName.MID,
        bbo_request,
        _EmptyRegistryReader(),
        dataset_version_ids=("dsv_fixture",),
        reset_on_session=False,
    )
    variant_cross = build_cross_market_feature_definition(
        CrossMarketFeatureName.SYNCHRONIZED_RETURNS,
        cross_request,
        _EmptyRegistryReader(),
        dataset_version_ids=("dsv_fixture",),
        window_length=2,
        reset_on_session=False,
    )

    for base, variant in (
        (base_structure, variant_structure),
        (base_bbo, variant_bbo),
        (base_cross, variant_cross),
    ):
        assert (
            _feature_spec_from_definition(base).derive_feature_version().feature_version_id
            == _feature_spec_from_definition(variant).derive_feature_version().feature_version_id
        )
        assert SESSION_TRUTH_KEYS.isdisjoint(
            _feature_spec_from_definition(variant).to_identity_dict()["transform"]["parameters"]
        )


def test_current_production_feature_version_ids_are_pinned() -> None:
    # These pins are deliberate: they break loudly on any identity-affecting
    # contract change. An intentional identity rotation must update the pins in
    # the same reviewed commit that explains and justifies the rotation.
    registry_reader = _EmptyRegistryReader()
    dataset_version_ids = ("dsv_identity_pin_fixture_v1",)
    cases = (
        (
            "liquidity_structure_range_contraction",
            build_structure_feature_definition(
                StructureFeatureName.RANGE_CONTRACTION,
                _feature_request(exposure_family="identity_pin_structure_range_contraction"),
                registry_reader,
                dataset_version_ids=dataset_version_ids,
                window_length=3,
                reset_on_session=True,
            ),
            "fver_a1563521cb4502061b49aa43a7e1a7e214eb28b851e141373afd5ab051d68193",
        ),
        (
            "bbo_tradability_spread_zscore",
            build_bbo_feature_definition(
                BBOFeatureName.SPREAD_ZSCORE,
                _feature_request(exposure_family="identity_pin_bbo_spread_zscore"),
                registry_reader,
                dataset_version_ids=dataset_version_ids,
                window_length=20,
                reset_on_session=True,
                ddof=0,
            ),
            "fver_a57f8ed781684175d20e811d2838ce3645e81ce3721727289c088c5f7476fc7c",
        ),
        (
            "base_ohlcv_atr",
            build_ohlcv_feature_definition(
                OHLCVFeatureName.ATR,
                _feature_request(exposure_family="identity_pin_base_ohlcv_atr"),
                registry_reader,
                dataset_version_ids=dataset_version_ids,
                window_length=20,
                reset_on_session=True,
                ddof=0,
            ),
            "fver_1cdc51e5e8eb1a63ab5b2962a58ab17877eb0763d7cb718ca1713a55232acbb6",
        ),
        (
            "cross_market_synchronized_returns",
            build_cross_market_feature_definition(
                CrossMarketFeatureName.SYNCHRONIZED_RETURNS,
                _feature_request(
                    exposure_family="identity_pin_cross_market_synchronized_returns"
                ),
                registry_reader,
                dataset_version_ids=dataset_version_ids,
                window_length=3,
                horizon=1,
                reset_on_session=True,
                ddof=0,
                alignment_policy="strict_intersection",
            ),
            "fver_718940f677baf1e341a61981be35a8d8759cb783d31628857cbc3c1d04417f28",
        ),
        (
            "base_ohlcv_opening_range",
            build_ohlcv_feature_definition(
                OHLCVFeatureName.OPENING_RANGE,
                _feature_request(exposure_family="identity_pin_base_ohlcv_opening_range"),
                registry_reader,
                dataset_version_ids=dataset_version_ids,
                window_length=1,
                horizon=1,
                opening_range_minutes=30,
                reset_on_session=True,
                ddof=0,
            ),
            "fver_63e9a398ac627ab8c753211a6340b1a414dde4a1eac2e89f5f6dab0f1ca646ff",
        ),
        (
            "base_ohlcv_returns",
            build_ohlcv_feature_definition(
                OHLCVFeatureName.RETURNS,
                _feature_request(exposure_family="identity_pin_base_ohlcv_returns"),
                registry_reader,
                dataset_version_ids=dataset_version_ids,
                window_length=1,
                horizon=1,
                reset_on_session=False,
                ddof=0,
            ),
            "fver_e2dd0b72669c8fefc78e8e64251bfa5df8046771dd5364a3af79ced1a1fb02af",
        ),
        (
            "base_ohlcv_volume_zscore",
            build_ohlcv_feature_definition(
                OHLCVFeatureName.VOLUME_ZSCORE,
                _feature_request(exposure_family="identity_pin_base_ohlcv_volume_zscore"),
                registry_reader,
                dataset_version_ids=dataset_version_ids,
                window_length=20,
                horizon=1,
                reset_on_session=False,
                ddof=0,
            ),
            "fver_ad8838af64b53590a1869135b1b8cb42380661b035b82d6eed00e46a80bb4d2b",
        ),
    )

    assert {
        case_name: definition.feature_version_id
        for case_name, definition, _expected in cases
    } == {case_name: expected for case_name, _definition, expected in cases}


def _session_truth_parameters() -> dict[str, str]:
    template = load_session_template_by_id()
    return {
        "session_template_id": template.template_id,
        "session_timezone": template.timezone,
        "rth_open_time_local": template.rth_start.isoformat(timespec="minutes"),
        "rth_close_time_local": template.rth_end.isoformat(timespec="minutes"),
        "session_truth_source": "alpha_system.data.foundation.sessions",
    }


def _copy_spec_with_transform_parameters(
    definition: object,
    parameters: dict[str, object],
) -> FeatureSpec:
    spec = _feature_spec_from_definition(definition)
    return FeatureSpec(
        feature_id=spec.feature_id,
        family=spec.family,
        feature_request_id=spec.feature_request_id,
        inputs=spec.inputs,
        transform=TransformSpec(
            transform_id=spec.transform.transform_id,
            parameters=parameters,
        ),
        window=spec.window,
        normalization=spec.normalization,
        availability_assumptions=spec.availability_assumptions,
        available_ts_derivation_rule=spec.available_ts_derivation_rule,
        live=spec.live,
        implementation_eligible=spec.implementation_eligible,
        contract_metadata=spec.contract_metadata,
        request_gate_decision=getattr(definition, "request_gate_decision"),
    )


def _feature_spec_from_definition(definition: object) -> FeatureSpec:
    bound_spec = getattr(definition, "spec")
    spec = getattr(bound_spec, "feature_spec", bound_spec)
    assert isinstance(spec, FeatureSpec)
    return spec


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
