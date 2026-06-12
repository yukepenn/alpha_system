from __future__ import annotations

from collections import defaultdict
import json
import os
import re
from pathlib import Path
from typing import Any

import pytest

from alpha_system.governance.feature_lock_validation import (
    FeatureLockValidationError,
    extract_feature_version_ids,
    validate_feature_locks,
)
from alpha_system.governance.study_spec import StudySpec
from alpha_system.runtime.input_resolver import (
    FeatureLabelPackResolver,
    RuntimeInputResolverError,
)
from tests._helpers.local_data import skip_unless_local_registry

REPO_ROOT = Path(__file__).resolve().parents[3]
ORIGINAL_STUDY_SPECS = (
    REPO_ROOT / "research/futures_core_alpha_pilot_v1/study_specs/study_specs.json"
)
RELOCK_DIR = REPO_ROOT / "research/futures_substrate_scaleout_v1/rerun"
RELOCK_STUDY_SPECS = RELOCK_DIR / "study_specs"
RELOCK_REPORT = RELOCK_DIR / "studyspec_relock.md"
FEATURE_VERSION_RE = re.compile(r"^fver_[a-f0-9]{64}$")
LABEL_VERSION_RE = re.compile(r"^lver_[a-f0-9]{64}$")
DATASET_VERSION_RE = re.compile(r"^dsv_[A-Za-z0-9_]+$")
PATH_KEYS = {"parquet_path", "materialization_output_path", "provider_path"}
PRIOR_INCONCLUSIVE_IDS = {
    "sspec_69c22ec5847395ac8e81b5b6",
    "sspec_aff70fcbc4b7ff226fcc8149",
    "sspec_267cc052e37668339c38d179",
    "sspec_27bf1262b0bd23d27191cc86",
    "sspec_02c400a561891171a33c0c66",
    "sspec_9f6f741192a4b534f06e51c0",
}
EXPECTED_ORIGINAL_IDS = PRIOR_INCONCLUSIVE_IDS | {
    "sspec_dde3e64667fe158f9bad527d",
    "sspec_c671fbeeb143512cbc03bc5b",
    "sspec_90b28233d828128664588a9a",
    "sspec_7c8fb13628843890c171b122",
}
HELD_FIXED_FIELDS = (
    "alpha_spec_id",
    "label_spec_id",
    "split_protocol",
    "metrics",
    "cost_assumptions",
    "variant_budget",
    "locked_test_policy",
    "negative_controls",
    "stopping_rules",
)


def test_relocked_studyspecs_parse_through_governance_contract() -> None:
    specs = _load_relocked_specs()

    assert len(specs) == 10
    assert all(isinstance(spec, StudySpec) for spec in specs)
    assert {
        spec.dataset_scope["relock_provenance"]["original_study_spec_id"]
        for spec in specs
    } == EXPECTED_ORIGINAL_IDS


def test_relocked_studyspecs_preserve_original_ids_and_parameters() -> None:
    originals = {payload["study_spec_id"]: payload for payload in _load_json(ORIGINAL_STUDY_SPECS)}

    for spec in _load_relocked_specs():
        original_id = spec.dataset_scope["relock_provenance"]["original_study_spec_id"]
        original = originals[original_id]
        for field in HELD_FIXED_FIELDS:
            assert getattr(spec, field) == original[field]

        assert spec.study_spec_id != original_id
        assert spec.dataset_scope["relock_provenance"]["original_study_spec_id"] == original_id
        assert (
            spec.dataset_scope["relock_provenance"]["relock_phase_id"]
            == "P110000_RELOCK_V2"
        )


def test_reissued_locks_are_well_formed_value_free_and_accepted() -> None:
    for spec in _load_relocked_specs():
        scope = spec.dataset_scope
        dataset_locks = scope["dataset_version_locks"]
        assert dataset_locks
        for dataset_lock in dataset_locks:
            assert DATASET_VERSION_RE.fullmatch(dataset_lock["dataset_version_id"])
            assert dataset_lock["acceptance_state"] in {
                "ACCEPTED",
                "ACCEPTED_WITH_WARNINGS",
            }

        for lock in scope["feature_pack_locks"]:
            assert FEATURE_VERSION_RE.fullmatch(lock["feature_version_id"])
            assert lock["feature_request_id"].startswith("freq_")
            assert DATASET_VERSION_RE.fullmatch(lock["dataset_version_id"])
            assert lock["lifecycle_state"] == "REGISTERED"
            assert lock["value_store_format"] == "parquet"
            assert lock["value_content_hash"].startswith("sha256:")
            assert int(lock["value_record_count"]) > 0
            assert not PATH_KEYS.intersection(lock)

        for lock in scope["label_pack_locks"]:
            assert LABEL_VERSION_RE.fullmatch(lock["label_version_id"])
            assert lock["label_spec_id"].startswith("lspec_")
            assert DATASET_VERSION_RE.fullmatch(lock["dataset_version_id"])
            assert lock["lifecycle_state"] == "REGISTERED"
            assert lock["value_store_format"] == "parquet"
            assert lock["value_content_hash"].startswith("sha256:")
            assert int(lock["value_record_count"]) > 0
            assert not PATH_KEYS.intersection(lock)

    assert sum(len(spec.dataset_scope["feature_pack_locks"]) for spec in _load_relocked_specs()) == 4112
    assert sum(len(spec.dataset_scope["label_pack_locks"]) for spec in _load_relocked_specs()) == 840


def test_committed_locks_resolve_against_live_registry_and_feature_validator() -> None:
    data_root = _alpha_data_root()
    feature_registry = skip_unless_local_registry(
        lambda: data_root / "registry/features.sqlite",
        reason="live local registry absent (CI environment); lock resolution validated locally; see studyspec_relock.md report",
    )
    label_registry = data_root / "registry/labels.sqlite"
    assert label_registry.exists()

    resolver = FeatureLabelPackResolver(alpha_data_root=data_root)
    all_feature_locks: list[dict[str, Any]] = []

    for spec in _load_relocked_specs():
        scope = spec.dataset_scope
        all_feature_locks.extend(scope["feature_pack_locks"])
        _resolve_feature_locks(resolver, scope)
        _resolve_label_locks(resolver, scope)

    report = validate_feature_locks(all_feature_locks, registry_path=feature_registry)
    assert report.ok
    assert report.to_dict()["lock_count"] == 4112
    assert report.to_dict()["resolved_count"] == 4112
    assert report.to_dict()["stale_lock_count"] == 0


def test_relock_report_records_smoke_pass_and_all_inconclusive_classifications() -> None:
    report = RELOCK_REPORT.read_text(encoding="utf-8")

    assert "StudySpec resolver-smoke: PASS" in report
    assert "Prior-INCONCLUSIVE studies re-locked: 6/6" in report
    assert "Feature locks resolved for committed V2 re-locks: 4112" in report
    assert "Label locks resolved for committed V2 re-locks: 840" in report
    assert "Deprecated R-036 session countdown locks retired without replacement: 448" in report
    assert "## Prior-INCONCLUSIVE Classification" in report
    assert "feature_pack_not_found" in report
    assert "Named Gaps\n\nNone." in report
    for study_spec_id in PRIOR_INCONCLUSIVE_IDS:
        assert study_spec_id in report
        assert f"{study_spec_id}` |" in report


def test_synthetic_unresolvable_lock_fails_closed_without_fuzzy_fallback() -> None:
    with pytest.raises(FeatureLockValidationError):
        extract_feature_version_ids([{"feature_version_id": "not_a_feature_version"}])

    resolver = FeatureLabelPackResolver(feature_store=_EmptyFeatureStore())
    with pytest.raises(RuntimeInputResolverError) as exc_info:
        resolver.resolve_feature_packs(
            ("fver_" + "0" * 64,),
            expected_dataset_version_id="dsv_databento_ohlcv_05404069799decb0",
            expected_feature_request_ids=(),
            partition_id="ES_2024_full_year",
        )

    assert exc_info.value.reason.code == "feature_pack_not_found"


def _load_relocked_specs() -> tuple[StudySpec, ...]:
    paths = sorted(RELOCK_STUDY_SPECS.glob("sspec_*.json"))
    assert paths
    return tuple(StudySpec.from_mapping(_load_json(path)) for path in paths)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _alpha_data_root() -> Path:
    return Path(
        os.environ.get("ALPHA_DATA_ROOT", "~/alpha_data/alpha_system")
    ).expanduser()


def _resolve_feature_locks(
    resolver: FeatureLabelPackResolver,
    scope: dict[str, Any],
) -> None:
    expected_request_ids = tuple(scope["study_input_pack_refs"]["feature_request_ids"])
    for (dataset_version_id, partition_id), locks in _locks_by_dataset_partition(
        scope["feature_pack_locks"]
    ).items():
        handles = resolver.resolve_feature_packs(
            tuple(lock["feature_version_id"] for lock in locks),
            expected_dataset_version_id=dataset_version_id,
            expected_feature_request_ids=expected_request_ids,
            partition_id=partition_id,
        )
        assert len(handles) == len(locks)


def _resolve_label_locks(
    resolver: FeatureLabelPackResolver,
    scope: dict[str, Any],
) -> None:
    expected_label_spec_ids = tuple(scope["study_input_pack_refs"]["label_spec_ids"])
    for (dataset_version_id, partition_id), locks in _locks_by_dataset_partition(
        scope["label_pack_locks"]
    ).items():
        handles = resolver.resolve_label_packs(
            tuple(lock["label_version_id"] for lock in locks),
            expected_dataset_version_id=dataset_version_id,
            expected_label_spec_ids=expected_label_spec_ids,
            partition_id=partition_id,
        )
        assert len(handles) == len(locks)


def _locks_by_dataset_partition(
    locks: list[dict[str, Any]],
) -> dict[tuple[str, str], list[dict[str, Any]]]:
    groups: defaultdict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for lock in locks:
        groups[(lock["dataset_version_id"], lock["partition"])].append(lock)
    return dict(groups)


class _EmptyFeatureStore:
    def resolve_active_feature(self, feature_version_id: object) -> None:
        return None

    def resolve_feature_by_version(self, feature_version_id: object) -> None:
        return None
