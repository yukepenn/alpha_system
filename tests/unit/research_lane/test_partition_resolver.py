"""Unit tests for PARTITION_RESOLVER_V0 cross-partition SliceSpec resolution.

These exercise the resolution seam WITHOUT a heavy real registry: lightweight
fake feature/label registries expose the same public REGISTERED-record read
methods the resolver uses (``read_registered_parquet_features`` /
``read_label_records``) over a synthetic on-disk fixture tree of 2-3 partitions.
The resolver then synthesizes complete SliceSpecs whose pack refs point at the
TARGET partition's versions; a missing factor/label for a partition fails closed
with a typed error; and the mining driver fans a setup idea over the resolved
partitions (a partition's data absent -> honest DATA_GAP, never fabricated).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from alpha_system.research_lane import mining_driver as mining_driver_module
from alpha_system.research_lane.mining_driver import run_multi_partition_pool
from alpha_system.research_lane.partition_resolver import (
    PartitionResolutionError,
    TargetPartition,
    resolve_partition_setup,
    resolve_partition_slice,
    resolve_partition_slices,
)

FIXTURE_IDEA = Path(
    "research/idea_to_verdict_loop_v0/pa_setup/"
    "prior_session_high_sweep_and_reclaim_es2020_120m_net_excursion.idea.yaml"
)


# ---------------------------------------------------------------------------
# Lightweight fake registry records + stores
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _FakeFeatureSpec:
    feature_id: str
    feature_request_id: str


@dataclass(frozen=True)
class _FakeFeatureRecord:
    feature_spec: _FakeFeatureSpec
    feature_version_id: str
    partition_id: str
    dataset_version_id: str
    parquet_path: str | None

    @property
    def feature_request_id(self) -> str:
        return self.feature_spec.feature_request_id


@dataclass(frozen=True)
class _FakeLabelRecord:
    label_id: str
    label_spec_id: str
    label_version_id: str
    partition_id: str
    dataset_version_id: str
    parquet_path: str | None
    lifecycle_state: str = "REGISTERED"


class _FakeFeatureRegistry:
    def __init__(self, records: list[_FakeFeatureRecord]) -> None:
        self._records = records

    def read_registered_parquet_features(self) -> tuple[_FakeFeatureRecord, ...]:
        return tuple(r for r in self._records if r.parquet_path is not None)


class _FakeLabelRegistry:
    def __init__(self, records: list[_FakeLabelRecord]) -> None:
        self._records = records

    def read_label_records(self) -> tuple[_FakeLabelRecord, ...]:
        return tuple(self._records)


# ---------------------------------------------------------------------------
# Synthetic fixture: idea template + on-disk tree + registries for 3 partitions
# ---------------------------------------------------------------------------


_DSV_BY_YEAR = {
    2019: "dsv_year_2019",
    2020: "dsv_year_2020",
    2021: "dsv_year_2021",
}


def _lspec_id(year: int) -> str:
    """A governance-valid LABEL_SPEC id (``<prefix>_<24-hex>``) per year."""

    return f"lspec_{year:024x}"

_FACTORS = ("ctx_factor", "trg_factor")
_FACTOR_TOKEN = {"ctx_factor": "ctx", "trg_factor": "trg"}
_LABELS = ("path_mfe", "path_mae")
_LABEL_TOKEN = {"path_mfe": "mfe", "path_mae": "mae"}


def _idea_payload() -> dict[str, object]:
    """A minimal net_excursion idea declaring ONLY the ES_2020_120m slice."""

    return {
        "study_kind": "context_not_equal_trigger",
        "setup_spec": {
            "entry_context": {
                "factor_id": "ctx_factor",
                "factor_version": "v1_base_ctx",
                "operator": ">=",
                "threshold": 0.0,
                "value_field": "normalized_value",
            },
            "event_trigger": {
                "factor_id": "trg_factor",
                "factor_version": "v1_base_trg",
                "operator": ">",
                "threshold": 0.0,
                "value_field": "normalized_value",
            },
            "path_label": "lspec_2020",
            "horizon": "120m",
        },
        "slices": {
            "ES_2020_120m": _declared_slice_payload(),
        },
    }


def _declared_slice_payload() -> dict[str, object]:
    return {
        "slice_id": "ES_2020_120m",
        "study_kind": "context_not_equal_trigger",
        "dataset_version_id": "dsv_year_2020",
        "data_version": "dsv_year_2020",
        "partition_id": "ES_2020_120m",
        "instrument_id": "ES",
        "session_id": "ES:RTH",
        "outcome_label_type": "net_excursion",
        "required_future_bars": 120,
        "horizon_seconds": 7200,
        "surrogate_run_count": 1000,
        "family_id": "fam_demo",
        "variant_id": "var_demo",
        "features": [
            {
                "role": "context",
                "factor_id": "ctx_factor",
                "factor_version": "v1_base_ctx",
                "relative_path": "features/ctx/ES_2020.parquet",
                "pack_ref": "fver_ctx_2020",
                "feature_request_id": "freq_ctx",
            },
            {
                "role": "trigger",
                "factor_id": "trg_factor",
                "factor_version": "v1_base_trg",
                "relative_path": "features/trg/ES_2020.parquet",
                "pack_ref": "fver_trg_2020",
                "feature_request_id": "freq_trg",
            },
        ],
        "labels": [
            {
                "role": "path",
                "label_id": "path_mfe",
                "relative_path": "labels/ES_2020_mfe.parquet",
                "pack_ref": "lver_mfe_2020",
                "label_spec_id": "lspec_2020",
            },
            {
                "role": "path",
                "label_id": "path_mae",
                "relative_path": "labels/ES_2020_mae.parquet",
                "pack_ref": "lver_mae_2020",
                "label_spec_id": "lspec_2020",
            },
        ],
        "label_version_map": {
            "lver_mfe_2020": ["mfe_by_horizon", "float"],
            "lver_mae_2020": ["mae_by_horizon", "float"],
        },
    }


def _build_registries(root: Path, years=(2019, 2020, 2021), *, drop=()):
    """Build fake registries + on-disk parquet stubs for the given years.

    ``drop`` is a set of (kind, factor_id, year) tuples whose records are
    omitted, so a target partition fails closed for a genuinely-absent factor.
    """

    feature_records: list[_FakeFeatureRecord] = []
    label_records: list[_FakeLabelRecord] = []
    for year in years:
        dsv = _DSV_BY_YEAR[year]
        feat_partition = f"ES_{year}_full_year"
        label_partition = f"ES_{year}_120m"
        for factor in _FACTORS:
            if ("feature", factor, year) in drop:
                continue
            rel = f"features/{factor}/ES_{year}.parquet"
            abs_path = root / rel
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            abs_path.write_text("{}", encoding="utf-8")
            feature_records.append(
                _FakeFeatureRecord(
                    feature_spec=_FakeFeatureSpec(factor, f"freq_{factor}"),
                    feature_version_id=f"fver_{_FACTOR_TOKEN[factor]}_{year}",
                    partition_id=feat_partition,
                    dataset_version_id=dsv,
                    parquet_path=str(abs_path),
                )
            )
        for label in _LABELS:
            if ("label", label, year) in drop:
                continue
            rel = f"labels/ES_{year}_{_LABEL_TOKEN[label]}.parquet"
            abs_path = root / rel
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            abs_path.write_text("{}", encoding="utf-8")
            label_records.append(
                _FakeLabelRecord(
                    label_id=label,
                    label_spec_id=f"lspec_{year}",
                    label_version_id=f"lver_{_LABEL_TOKEN[label]}_{year}",
                    partition_id=label_partition,
                    dataset_version_id=dsv,
                    parquet_path=str(abs_path),
                )
            )
    return _FakeFeatureRegistry(feature_records), _FakeLabelRegistry(label_records)


# ---------------------------------------------------------------------------
# Resolution correctness
# ---------------------------------------------------------------------------


def test_resolves_complete_slice_for_target_partition(tmp_path) -> None:
    feature_reg, label_reg = _build_registries(tmp_path)
    payload = _idea_payload()
    payload["slices"]["ES_2020_120m"]["data_root"] = str(tmp_path)

    spec = resolve_partition_slice(
        payload,
        target_partition="ES_2021_120m",
        env={"ALPHA_DATA_ROOT": str(tmp_path)},
        feature_store=feature_reg,
        label_registry=label_reg,
    )

    assert spec.slice_id == "ES_2021_120m"
    assert spec.partition_id == "ES_2021_120m"
    assert spec.instrument_id == "ES"
    assert spec.dataset_version_id == "dsv_year_2021"
    # Pack refs point at the TARGET partition's versions, NOT ES_2020's hashes.
    assert set(spec.feature_pack_refs) == {"fver_ctx_2021", "fver_trg_2021"}
    assert set(spec.label_pack_refs) == {"lver_mfe_2021", "lver_mae_2021"}
    assert set(spec.label_spec_ids) == {"lspec_2021"}
    # Binding semantics (mfe/mae by horizon) carried onto the resolved lvers.
    bindings = spec.label_version_map
    assert bindings["lver_mfe_2021"].label_type == "mfe_by_horizon"
    assert bindings["lver_mae_2021"].label_type == "mae_by_horizon"
    # Outcome + horizon config inherited from the template.
    assert spec.outcome_label_type == "net_excursion"
    assert spec.required_future_bars == 120
    assert spec.surrogate_run_count == 1000


def test_declared_partition_resolves_to_declared_versions(tmp_path) -> None:
    feature_reg, label_reg = _build_registries(tmp_path)
    payload = _idea_payload()
    payload["slices"]["ES_2020_120m"]["data_root"] = str(tmp_path)

    spec = resolve_partition_slice(
        payload,
        target_partition="ES_2020_120m",
        env={"ALPHA_DATA_ROOT": str(tmp_path)},
        feature_store=feature_reg,
        label_registry=label_reg,
    )
    # Re-resolving the AUTHORED partition recovers its own declared versions.
    assert set(spec.feature_pack_refs) == {"fver_ctx_2020", "fver_trg_2020"}
    assert set(spec.label_pack_refs) == {"lver_mfe_2020", "lver_mae_2020"}


def test_batch_resolves_multiple_partitions(tmp_path) -> None:
    feature_reg, label_reg = _build_registries(tmp_path)
    payload = _idea_payload()
    payload["slices"]["ES_2020_120m"]["data_root"] = str(tmp_path)

    specs = resolve_partition_slices(
        payload,
        ["ES_2019_120m", "ES_2020_120m", "ES_2021_120m"],
        env={"ALPHA_DATA_ROOT": str(tmp_path)},
        feature_store=feature_reg,
        label_registry=label_reg,
    )
    assert [s.slice_id for s in specs] == [
        "ES_2019_120m",
        "ES_2020_120m",
        "ES_2021_120m",
    ]
    assert specs[0].dataset_version_id == "dsv_year_2019"
    assert specs[2].dataset_version_id == "dsv_year_2021"


# ---------------------------------------------------------------------------
# Fail-closed behaviour
# ---------------------------------------------------------------------------


def test_missing_feature_for_partition_fails_closed(tmp_path) -> None:
    feature_reg, label_reg = _build_registries(
        tmp_path, drop={("feature", "trg_factor", 2021)}
    )
    payload = _idea_payload()
    payload["slices"]["ES_2020_120m"]["data_root"] = str(tmp_path)

    with pytest.raises(PartitionResolutionError) as exc:
        resolve_partition_slice(
            payload,
            target_partition="ES_2021_120m",
            env={"ALPHA_DATA_ROOT": str(tmp_path)},
            feature_store=feature_reg,
            label_registry=label_reg,
        )
    assert exc.value.code == "feature_not_materialized_for_partition"


def test_missing_label_for_partition_fails_closed(tmp_path) -> None:
    feature_reg, label_reg = _build_registries(
        tmp_path, drop={("label", "path_mfe", 2021)}
    )
    payload = _idea_payload()
    payload["slices"]["ES_2020_120m"]["data_root"] = str(tmp_path)

    with pytest.raises(PartitionResolutionError) as exc:
        resolve_partition_slice(
            payload,
            target_partition="ES_2021_120m",
            env={"ALPHA_DATA_ROOT": str(tmp_path)},
            feature_store=feature_reg,
            label_registry=label_reg,
        )
    assert exc.value.code == "label_not_materialized_for_partition"


def test_absent_year_fails_closed(tmp_path) -> None:
    feature_reg, label_reg = _build_registries(tmp_path)
    payload = _idea_payload()
    payload["slices"]["ES_2020_120m"]["data_root"] = str(tmp_path)

    with pytest.raises(PartitionResolutionError):
        resolve_partition_slice(
            payload,
            target_partition="ES_2099_120m",
            env={"ALPHA_DATA_ROOT": str(tmp_path)},
            feature_store=feature_reg,
            label_registry=label_reg,
        )


def test_malformed_target_partition_fails_closed() -> None:
    with pytest.raises(PartitionResolutionError) as exc:
        TargetPartition.from_slice_id("not_a_partition")
    assert exc.value.code == "malformed_target_partition"


def test_ambiguous_feature_for_partition_fails_closed(tmp_path) -> None:
    feature_reg, label_reg = _build_registries(tmp_path)
    # Inject a SECOND REGISTERED ctx_factor record at the same partition.
    feature_reg._records.append(
        _FakeFeatureRecord(
            feature_spec=_FakeFeatureSpec("ctx_factor", "freq_ctx"),
            feature_version_id="fver_ctx_2021_dupe",
            partition_id="ES_2021_full_year",
            dataset_version_id="dsv_year_2021",
            parquet_path=str(tmp_path / "features/ctx/ES_2021_dupe.parquet"),
        )
    )
    payload = _idea_payload()
    payload["slices"]["ES_2020_120m"]["data_root"] = str(tmp_path)

    with pytest.raises(PartitionResolutionError) as exc:
        resolve_partition_slice(
            payload,
            target_partition="ES_2021_120m",
            env={"ALPHA_DATA_ROOT": str(tmp_path)},
            feature_store=feature_reg,
            label_registry=label_reg,
        )
    assert exc.value.code == "ambiguous_feature_for_partition"


# ---------------------------------------------------------------------------
# Setup retargeting
# ---------------------------------------------------------------------------


def test_resolve_partition_setup_retargets_path_label(tmp_path) -> None:
    from alpha_system.governance.idea_draft import build_idea_validation_bundle

    payload = json.loads(FIXTURE_IDEA.read_text(encoding="utf-8"))
    bundle = build_idea_validation_bundle(payload, source=FIXTURE_IDEA.as_posix())

    # Build a target slice whose path labels resolve to a DIFFERENT spec id.
    from alpha_system.research_lane.slice_spec import SliceSpec

    target_spec = SliceSpec.from_mapping(
        {
            **json.loads(json.dumps(payload["slices"]["ES_2020_120m"])),
            "slice_id": "ES_2021_120m",
            "partition_id": "ES_2021_120m",
            "labels": [
                {**lbl, "label_spec_id": _lspec_id(2021)}
                for lbl in payload["slices"]["ES_2020_120m"]["labels"]
            ],
        }
    )
    retargeted = resolve_partition_setup(bundle.setup_spec, target_spec)
    assert retargeted.path_label == _lspec_id(2021)
    # The deterministic setup id is re-derived (content changed).
    assert retargeted.setup_spec_id != bundle.setup_spec.setup_spec_id


def test_resolve_partition_setup_none_passthrough() -> None:
    from alpha_system.research_lane.slice_spec import SliceSpec

    target_spec = SliceSpec.from_mapping(_declared_slice_payload())
    assert resolve_partition_setup(None, target_spec) is None


# ---------------------------------------------------------------------------
# Driver fan-out over RESOLVED (undeclared) partitions
# ---------------------------------------------------------------------------


def _real_bundle_and_registries(tmp_path, *, years):
    """Build a VALID bundle from the real fixture idea + synthetic registries.

    The registries are keyed by the fixture's OWN declared factor/label ids so
    the resolver can synthesize each target year's slice from the same family.
    """

    from alpha_system.governance.idea_draft import build_idea_validation_bundle
    from alpha_system.research_lane.slice_spec import SliceSpec

    payload = json.loads(FIXTURE_IDEA.read_text(encoding="utf-8"))
    payload["slices"]["ES_2020_120m"]["data_root"] = str(tmp_path)
    bundle = build_idea_validation_bundle(payload, source="unit://partition_resolver")
    declared = SliceSpec.from_mapping(payload["slices"]["ES_2020_120m"])

    feature_records: list[_FakeFeatureRecord] = []
    label_records: list[_FakeLabelRecord] = []
    for year in years:
        dsv = f"dsv_year_{year}"
        for feat in declared.feature_inputs:
            rel = f"features/{feat.factor_id}/ES_{year}.parquet"
            abs_path = tmp_path / rel
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            abs_path.write_text("{}", encoding="utf-8")
            feature_records.append(
                _FakeFeatureRecord(
                    feature_spec=_FakeFeatureSpec(
                        feat.factor_id, feat.feature_request_id or "freq"
                    ),
                    feature_version_id=f"fver_{feat.role}_{year}",
                    partition_id=f"ES_{year}_full_year",
                    dataset_version_id=dsv,
                    parquet_path=str(abs_path),
                )
            )
        for lbl in declared.label_inputs:
            rel = f"labels/ES_{year}_{lbl.label_id}.parquet"
            abs_path = tmp_path / rel
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            abs_path.write_text("{}", encoding="utf-8")
            label_records.append(
                _FakeLabelRecord(
                    label_id=lbl.label_id,
                    label_spec_id=_lspec_id(year),
                    label_version_id=f"lver_{lbl.label_id}_{year}",
                    partition_id=f"ES_{year}_120m",
                    dataset_version_id=dsv,
                    parquet_path=str(abs_path),
                )
            )
    return (
        payload,
        bundle,
        _FakeFeatureRegistry(feature_records),
        _FakeLabelRegistry(label_records),
    )


def _patch_resolver_registries(monkeypatch, feature_reg, label_reg):
    """Force the resolver's _RegistryIndex to use the synthetic fake registries."""

    import alpha_system.research_lane.partition_resolver as pr_mod

    real_index = pr_mod._RegistryIndex

    def fake_index(*args, **kwargs):
        kwargs["feature_store"] = feature_reg
        kwargs["label_registry"] = label_reg
        return real_index(*args, **kwargs)

    monkeypatch.setattr(pr_mod, "_RegistryIndex", fake_index)


def test_driver_fans_setup_idea_over_resolved_partitions(tmp_path, monkeypatch) -> None:
    payload, bundle, feature_reg, label_reg = _real_bundle_and_registries(
        tmp_path, years=(2019, 2020, 2021)
    )
    _patch_resolver_registries(monkeypatch, feature_reg, label_reg)
    monkeypatch.setenv("ALPHA_DATA_ROOT", str(tmp_path))

    probed: list[str] = []

    def fake_probe(card, setup, slice_spec, *, resolver=None, env=None):
        probed.append(slice_spec.slice_id)
        return _setup_readout(slice_id=slice_spec.slice_id, mean_lift=0.02, n_eff=150)

    monkeypatch.setattr(mining_driver_module, "fast_probe", fake_probe)

    result = run_multi_partition_pool(
        payload,
        bundle.idea_draft,
        bundle.mechanism_card,
        bundle.setup_spec,
        ["ES_2019_120m", "ES_2020_120m", "ES_2021_120m"],
        env={"ALPHA_DATA_ROOT": str(tmp_path)},
    )

    # All three partitions resolved (the two undeclared ones via the resolver).
    assert sorted(probed) == ["ES_2019_120m", "ES_2020_120m", "ES_2021_120m"]
    assert result.coverage.present_count == 3
    assert result.coverage.is_multi_partition


def test_driver_records_data_gap_for_unmaterialized_partition(tmp_path, monkeypatch) -> None:
    # Only 2019/2020 materialized -> 2021 must fail closed to DATA_GAP, not abort.
    payload, bundle, feature_reg, label_reg = _real_bundle_and_registries(
        tmp_path, years=(2019, 2020)
    )
    _patch_resolver_registries(monkeypatch, feature_reg, label_reg)
    monkeypatch.setenv("ALPHA_DATA_ROOT", str(tmp_path))

    def fake_probe(card, setup, slice_spec, *, resolver=None, env=None):
        return _setup_readout(slice_id=slice_spec.slice_id, mean_lift=0.02, n_eff=150)

    monkeypatch.setattr(mining_driver_module, "fast_probe", fake_probe)

    result = run_multi_partition_pool(
        payload,
        bundle.idea_draft,
        bundle.mechanism_card,
        bundle.setup_spec,
        ["ES_2020_120m", "ES_2021_120m"],
        env={"ALPHA_DATA_ROOT": str(tmp_path)},
    )

    assert "ES_2021_120m" in result.coverage.missing
    assert "ES_2020_120m" in result.coverage.present
    assert result.coverage.present_count == 1


def _setup_readout(*, slice_id, mean_lift, n_eff):
    return {
        "schema": "alpha_system.research_lane.fast_probe.v1",
        "readout_id": f"fpsetup_{slice_id}",
        "status": "RECORDED",
        "study_kind": "context_not_equal_trigger",
        "stamp": "EXPLORATORY",
        "promotion_eligible": False,
        # A real setup readout carries the mechanism_card whose required_features
        # name the signal's factor identity (see fast_probe readout builders); the
        # router fails loud rather than fabricate an "unknown_factor" identity.
        "mechanism_card": {"required_features": ["trg_factor"]},
        "slice_spec": {"slice_id": slice_id, "study_kind": "context_not_equal_trigger"},
        "row_access": {"status": "resolved_local_only", "fabricated_values": False},
        "power": {"n_eff": n_eff, "mde_abs_ic": 0.08},
        "surrogate_fdr_gate": {
            "gate_status": "PASSED",
            "threshold_verdict": "zero-pass-met",
            "run_count": 1000,
            "gate_pass_count": 0,
            "error_count": 0,
            "promotion_evidence": False,
        },
        "readout": {
            "diagnostics": {
                "continuous_outcome_mean_lift": {
                    "outcome_label_type": "net_excursion",
                    "conditioned_mean": mean_lift,
                    "base_mean": 0.0,
                    "mean_lift": mean_lift,
                    "conditioned_n": n_eff,
                    "base_n": n_eff,
                }
            }
        },
    }
