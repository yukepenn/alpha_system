"""Pooled-OOS partition-resolution drift canary (multi-partition fan-out).

Guards the cross-partition OOS pooling rail against a SILENT degeneracy: an idea
declares a feature ``factor_id`` (e.g. ``regime_range_contraction_state``) that
differs from the registry's CANONICAL ``feature_id`` (e.g.
``liquidity_structure_range_contraction``) for that pack. On the AUTHORED
partition the runtime input resolver loads fine because it resolves features BY
``pack_ref`` (the content-hash version id), not by name. But
``research_lane/partition_resolver.py`` fanned the OOS lookup out by the idea's
``factor_id`` against a registry index keyed on the canonical ``feature_id`` --
so every NON-authored partition (and the authored one, when re-resolved) found
ZERO candidates, recorded an honest-looking ``DATA_GAP``, and the pool silently
degenerated to ``coverage <= 1``. Every "cross-year / cross-instrument pooled
OOS" run was VACUOUS (single-partition) even though the data was materialized.

The fix maps each declared pack_ref to the registry's canonical
``(feature_id, feature_set_id)`` identity ONCE (from the authored pack), then
fans the lookup out by that identity. ``feature_set_id`` is part of the identity
because a single canonical ``feature_id`` can be materialized by MULTIPLE feature
sets at one partition; the pair is unique per partition, so this never resolves a
wrong pack.

The drift condition is exercised against a REAL drifted idea
(``evals/canaries/pooled_partition_factor_id_drift/drifted_idea_fixture.json`` --
a copy of a regime conditional-setup idea whose declared ``factor_id`` differs
from the registry's canonical ``feature_id``), over synthetic, value-free fake
registries built across 3 years x 3 instruments. The fixture deliberately keys
each declared feature's canonical identity to a name DIFFERENT from the declared
factor_id, and ships a second feature set sharing the canonical feature_id, so
both drift conditions (factor_id != feature_id AND feature_id ambiguity) hold.

The canary asserts:

1. **No silent single-partition degeneracy.** Fanning the drifted idea over
   ES/NQ/RTY x 2019/2020/2021 yields a ``PooledRunResult`` with
   ``coverage.present_count >= 2`` and ``is_multi_partition_oos == True``. On the
   pre-fix resolver this collapses to coverage <= 1 -- the regression signature.

2. **Each partition resolves its OWN pack, never a wrong one.** Re-resolving the
   AUTHORED partition recovers exactly its declared pack_refs (identity
   preserved); a cross-instrument partition resolves distinct pack_refs / dataset
   versions and the regime set's pack (NOT the decoy sharing the feature_id).

3. **Real gaps STILL fail closed.** A genuinely-absent partition (its feature not
   materialized) raises ``feature_not_materialized_for_partition`` and is recorded
   as missing -- the degeneracy is not "fixed" by masking real gaps.

This is research-only diagnostic plumbing over synthetic inputs. A passing canary
validates the partition-resolution identity contract only and implies NO alpha,
profitability, or tradability claim. The verdict is a deterministic RECORD; the
machine never auto-promotes.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import alpha_system.research_lane.mining_driver as mining_driver_module
import alpha_system.research_lane.partition_resolver as partition_resolver_module
from alpha_system.governance.idea_draft import build_idea_validation_bundle
from alpha_system.research_lane.mining_driver import run_multi_partition_pool
from alpha_system.research_lane.partition_resolver import (
    PartitionResolutionError,
    resolve_partition_slice,
)
from alpha_system.research_lane.slice_spec import SliceSpec

_FIXTURE = (
    Path(__file__).resolve().parents[4]
    / "evals"
    / "canaries"
    / "pooled_partition_factor_id_drift"
    / "drifted_idea_fixture.json"
)

_AUTHORED_SLICE_ID = "ES_2020_120m"
_INSTRUMENTS = ("ES", "NQ", "RTY")
_FAN_YEARS = (2019, 2020, 2021)

# A second feature set that ALSO materializes each declared feature's canonical
# feature_id -- so a feature_id-ONLY lookup is genuinely ambiguous and only the
# (feature_id, feature_set_id) identity resolves uniquely.
_DECOY_FEATURE_SET_ID = "feature_set_decoy_shares_feature_id"


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


# ---------------------------------------------------------------------------
# Drift mapping: declared idea identity -> chosen synthetic registry identity
# ---------------------------------------------------------------------------


def _canonical_feature_id(factor_id: str) -> str:
    """A canonical registry feature_id that DIFFERS from the declared factor_id.

    This reproduces the naming drift WITHOUT depending on the real registry: the
    declared factor_id is never a registry feature_id, so a pre-fix lookup keyed
    by factor_id finds zero candidates at every partition.
    """

    return f"canonical_{factor_id}"


def _primary_feature_set_id(factor_id: str) -> str:
    return f"feature_set_{factor_id}_primary"


@dataclass(frozen=True)
class _FakeFeatureSpec:
    feature_id: str
    feature_request_id: str


@dataclass(frozen=True)
class _FakeFeatureRecord:
    feature_spec: _FakeFeatureSpec
    feature_version_id: str
    feature_set_id: str
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


def _dsv(instrument: str, year: int) -> str:
    return f"dsv_{instrument}_{year}"


def _fver(instrument: str, year: int, feature_set_id: str) -> str:
    return f"fver_{instrument}_{year}_{feature_set_id}"


def _load_drifted_idea(root: Path) -> dict[str, Any]:
    payload = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    payload["slices"][_AUTHORED_SLICE_ID]["data_root"] = str(root)
    # Re-point the AUTHORED slice's declared pack_refs at the synthetic version
    # ids the fake registry will carry, so re-resolving the authored partition
    # recovers exactly these (identity-preservation check). The factor_ids stay
    # the DRIFTED declared names.
    declared = SliceSpec.from_mapping(payload["slices"][_AUTHORED_SLICE_ID])
    feature_authored_packs: dict[str, str] = {}
    for feature in declared.feature_inputs:
        set_id = _primary_feature_set_id(feature.factor_id)
        authored_pack = _fver("ES", 2020, set_id)
        feature_authored_packs[feature.factor_id] = authored_pack
    for feature in payload["slices"][_AUTHORED_SLICE_ID]["features"]:
        feature["pack_ref"] = feature_authored_packs[feature["factor_id"]]
    return payload


def _build_registries(
    payload: dict[str, Any],
    root: Path,
    *,
    instruments=_INSTRUMENTS,
    years=_FAN_YEARS,
    drop: set[tuple[str, str, int]] | None = None,
):
    """Build synthetic value-free fake registries from the idea's declared roles.

    Each (instrument, year) materializes, per declared feature, the canonical
    feature_id under BOTH a primary set and a decoy set sharing the feature_id;
    plus each declared path label. ``drop`` omits a specific (instrument,
    factor_id, year) feature so a partition fails closed for a real gap.
    """

    drop = drop or set()
    declared = SliceSpec.from_mapping(payload["slices"][_AUTHORED_SLICE_ID])
    feature_records: list[_FakeFeatureRecord] = []
    label_records: list[_FakeLabelRecord] = []
    for instrument in instruments:
        for year in years:
            dsv = _dsv(instrument, year)
            feat_partition = f"{instrument}_{year}_full_year"
            label_partition = f"{instrument}_{year}_120m"
            for feature in declared.feature_inputs:
                canonical = _canonical_feature_id(feature.factor_id)
                primary_set = _primary_feature_set_id(feature.factor_id)
                if (instrument, feature.factor_id, year) not in drop:
                    _emit_feature(
                        feature_records,
                        root,
                        feature_id=canonical,
                        feature_set_id=primary_set,
                        version_id=_fver(instrument, year, primary_set),
                        request_id=f"freq_{feature.factor_id}_{instrument}_{year}",
                        partition_id=feat_partition,
                        dataset_version_id=dsv,
                        rel=f"features/{feature.factor_id}/primary/{instrument}_{year}.parquet",
                    )
                # DECOY: SAME canonical feature_id, DIFFERENT feature set.
                decoy_set = f"{_DECOY_FEATURE_SET_ID}_{feature.factor_id}"
                _emit_feature(
                    feature_records,
                    root,
                    feature_id=canonical,
                    feature_set_id=_DECOY_FEATURE_SET_ID,
                    version_id=_fver(instrument, year, decoy_set),
                    request_id=f"freq_decoy_{feature.factor_id}_{instrument}_{year}",
                    partition_id=feat_partition,
                    dataset_version_id=dsv,
                    rel=f"features/{feature.factor_id}/decoy/{instrument}_{year}.parquet",
                )
            for label in declared.label_inputs:
                if (instrument, label.label_id, year) in drop:
                    continue
                rel = f"labels/{instrument}_{year}_{label.label_id}.parquet"
                abs_path = root / rel
                abs_path.parent.mkdir(parents=True, exist_ok=True)
                abs_path.write_text("{}", encoding="utf-8")
                label_records.append(
                    _FakeLabelRecord(
                        label_id=label.label_id,
                        label_spec_id=_lspec_id(year),
                        label_version_id=f"lver_{label.label_id}_{instrument}_{year}",
                        partition_id=label_partition,
                        dataset_version_id=dsv,
                        parquet_path=str(abs_path),
                    )
                )
    return _FakeFeatureRegistry(feature_records), _FakeLabelRegistry(label_records)


def _lspec_id(year: int) -> str:
    return f"lspec_{year:024x}"


def _emit_feature(
    records: list[_FakeFeatureRecord],
    root: Path,
    *,
    feature_id: str,
    feature_set_id: str,
    version_id: str,
    request_id: str,
    partition_id: str,
    dataset_version_id: str,
    rel: str,
) -> None:
    abs_path = root / rel
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    abs_path.write_text("{}", encoding="utf-8")
    records.append(
        _FakeFeatureRecord(
            feature_spec=_FakeFeatureSpec(feature_id, request_id),
            feature_version_id=version_id,
            feature_set_id=feature_set_id,
            partition_id=partition_id,
            dataset_version_id=dataset_version_id,
            parquet_path=str(abs_path),
        )
    )


def _fan_ids(years=_FAN_YEARS, instruments=_INSTRUMENTS) -> list[str]:
    return [f"{inst}_{year}_120m" for inst in instruments for year in years]


def _setup_readout(slice_id: str, required_features: list[str]) -> dict[str, object]:
    return {
        "schema": "alpha_system.research_lane.fast_probe.v1",
        "readout_id": f"fpsetup_{slice_id}",
        "status": "RECORDED",
        "study_kind": "context_not_equal_trigger",
        "stamp": "EXPLORATORY",
        "promotion_eligible": False,
        "mechanism_card": {"required_features": required_features},
        "slice_spec": {"slice_id": slice_id, "study_kind": "context_not_equal_trigger"},
        "row_access": {"status": "resolved_local_only", "fabricated_values": False},
        "power": {"n_eff": 150, "mde_abs_ic": 0.08},
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
                    "conditioned_mean": 0.02,
                    "base_mean": 0.0,
                    "mean_lift": 0.02,
                    "conditioned_n": 150,
                    "base_n": 150,
                }
            }
        },
    }


class _ScopedInjection:
    """Inject fake registries into the resolver index + stub fast_probe.

    Restores originals on exit so the canary leaves no global state behind.
    """

    def __init__(self, feature_reg, label_reg, required_features: list[str]) -> None:
        self._feature_reg = feature_reg
        self._label_reg = label_reg
        self._required_features = required_features
        self._real_index = partition_resolver_module._RegistryIndex
        self._real_probe = mining_driver_module.fast_probe

    def __enter__(self):
        real_index = self._real_index

        def fake_index(*args, **kwargs):
            kwargs["feature_store"] = self._feature_reg
            kwargs["label_registry"] = self._label_reg
            return real_index(*args, **kwargs)

        def fake_probe(card, setup, slice_spec, *, resolver=None, env=None):
            return _setup_readout(slice_spec.slice_id, self._required_features)

        partition_resolver_module._RegistryIndex = fake_index
        mining_driver_module.fast_probe = fake_probe
        return self

    def __exit__(self, *exc) -> None:
        partition_resolver_module._RegistryIndex = self._real_index
        mining_driver_module.fast_probe = self._real_probe


def _required_features(payload: dict[str, Any]) -> list[str]:
    declared = SliceSpec.from_mapping(payload["slices"][_AUTHORED_SLICE_ID])
    return [f.factor_id for f in declared.feature_inputs]


def _check_no_silent_degeneracy(root: Path) -> None:
    """Core guard: the drifted idea fans out to coverage >= 2 (not 1)."""

    payload = _load_drifted_idea(root)
    feature_reg, label_reg = _build_registries(payload, root)
    bundle = build_idea_validation_bundle(payload, source="canary://partition_drift")
    env = {"ALPHA_DATA_ROOT": str(root)}

    with _ScopedInjection(feature_reg, label_reg, _required_features(payload)):
        result = run_multi_partition_pool(
            payload,
            bundle.idea_draft,
            bundle.mechanism_card,
            bundle.setup_spec,
            _fan_ids(),
            env=env,
        )

    _assert(
        result.coverage.present_count >= 2,
        (
            "SILENT DEGENERACY: drifted-factor_id pool collapsed to coverage="
            f"{result.coverage.present_count} (<2). present={result.coverage.present} "
            f"missing={result.coverage.missing}"
        ),
    )
    _assert(
        result.coverage.is_multi_partition,
        "pool must report is_multi_partition_oos=True with >=2 present partitions",
    )
    _assert(
        result.coverage.present_count == len(_fan_ids()),
        (
            "all materialized partitions must resolve: expected "
            f"{len(_fan_ids())} present, got {result.coverage.present_count} "
            f"(missing={result.coverage.missing})"
        ),
    )


def _check_no_wrong_pack_resolution(root: Path) -> None:
    """Each partition resolves its OWN distinct pack; authored identity preserved."""

    payload = _load_drifted_idea(root)
    feature_reg, label_reg = _build_registries(payload, root)
    env = {"ALPHA_DATA_ROOT": str(root)}

    declared_packs = sorted(
        f["pack_ref"] for f in payload["slices"][_AUTHORED_SLICE_ID]["features"]
    )
    authored = resolve_partition_slice(
        payload,
        target_partition=_AUTHORED_SLICE_ID,
        env=env,
        feature_store=feature_reg,
        label_registry=label_reg,
    )
    _assert(
        sorted(authored.feature_pack_refs) == declared_packs,
        (
            "WRONG-PACK: re-resolving authored partition did not recover its own "
            f"packs: {sorted(authored.feature_pack_refs)} != {declared_packs}"
        ),
    )

    other = resolve_partition_slice(
        payload,
        target_partition="NQ_2021_120m",
        env=env,
        feature_store=feature_reg,
        label_registry=label_reg,
    )
    # The cross-instrument partition resolves the PRIMARY-set pack for each declared
    # feature, never the decoy set sharing the canonical feature_id.
    declared = SliceSpec.from_mapping(payload["slices"][_AUTHORED_SLICE_ID])
    for feature in declared.feature_inputs:
        primary_set = _primary_feature_set_id(feature.factor_id)
        expected = _fver("NQ", 2021, primary_set)
        decoy = _fver("NQ", 2021, f"{_DECOY_FEATURE_SET_ID}_{feature.factor_id}")
        _assert(
            expected in other.feature_pack_refs,
            f"target must resolve the primary-set pack {expected}, got "
            f"{sorted(other.feature_pack_refs)}",
        )
        _assert(
            decoy not in other.feature_pack_refs,
            f"WRONG-PACK: target resolved the DECOY feature set pack {decoy}",
        )
    _assert(
        other.dataset_version_id == _dsv("NQ", 2021),
        f"target dataset version must be the NQ_2021 dsv, got {other.dataset_version_id}",
    )
    _assert(
        set(authored.feature_pack_refs).isdisjoint(other.feature_pack_refs),
        "distinct partitions must resolve DISJOINT pack_refs (no shared/copied hashes)",
    )


def _check_real_gap_still_fails_closed(root: Path) -> None:
    """A genuinely-absent partition is recorded DATA_GAP, never masked."""

    payload = _load_drifted_idea(root)
    declared = SliceSpec.from_mapping(payload["slices"][_AUTHORED_SLICE_ID])
    context_factor_id = declared.feature_inputs[0].factor_id
    # Drop the ES_2021 PRIMARY context feature -> only the decoy (different set)
    # remains, so the (feature_id, feature_set_id) identity has no candidate and
    # the partition MUST fail closed.
    feature_reg, label_reg = _build_registries(
        payload, root, drop={("ES", context_factor_id, 2021)}
    )
    env = {"ALPHA_DATA_ROOT": str(root)}

    captured = _CapturedError()
    try:
        resolve_partition_slice(
            payload,
            target_partition="ES_2021_120m",
            env=env,
            feature_store=feature_reg,
            label_registry=label_reg,
        )
    except PartitionResolutionError as exc:
        captured.code = exc.code
    _assert(
        captured.code == "feature_not_materialized_for_partition",
        "real gap must fail closed as feature_not_materialized_for_partition, "
        f"got {captured.code!r}",
    )

    bundle = build_idea_validation_bundle(payload, source="canary://partition_drift_gap")
    with _ScopedInjection(feature_reg, label_reg, _required_features(payload)):
        result = run_multi_partition_pool(
            payload,
            bundle.idea_draft,
            bundle.mechanism_card,
            bundle.setup_spec,
            ["ES_2020_120m", "ES_2021_120m"],
            env=env,
        )
    _assert(
        "ES_2021_120m" in result.coverage.missing,
        f"absent ES_2021 must be MISSING, coverage={result.coverage.to_dict()}",
    )
    _assert(
        "ES_2020_120m" in result.coverage.present,
        f"present ES_2020 must be PRESENT, coverage={result.coverage.to_dict()}",
    )


@dataclass
class _CapturedError:
    code: str | None = None


def run_pooled_partition_factor_id_drift_canary() -> None:
    with TemporaryDirectory(prefix="pooled-partition-drift-canary-") as raw:
        root = Path(raw)
        _check_no_silent_degeneracy(root)
        _check_no_wrong_pack_resolution(root)
        _check_real_gap_still_fails_closed(root)


def main(argv: list[str] | None = None) -> int:
    try:
        run_pooled_partition_factor_id_drift_canary()
    except AssertionError as exc:
        print(f"FAIL pooled_partition_factor_id_drift: {exc}", file=sys.stderr)
        return 1
    print(
        "pooled_partition_factor_id_drift OK: drifted-factor_id idea fans out to "
        "coverage>=2 multi-partition OOS (no silent single-partition collapse), each "
        "partition resolves its OWN pack by (feature_id, feature_set_id) identity "
        "(authored identity preserved, decoy set not mis-resolved), and a genuinely "
        "absent partition still fails closed to DATA_GAP"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
