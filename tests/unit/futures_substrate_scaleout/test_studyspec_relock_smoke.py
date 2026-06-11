from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from alpha_system.governance.feature_lock_validation import (
    FeatureLockValidationError,
    extract_feature_version_ids,
)
from alpha_system.governance.study_spec import StudySpec
from alpha_system.runtime.input_resolver import (
    FeatureLabelPackResolver,
    RuntimeInputResolverError,
)

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

    assert len(specs) == 8
    assert all(isinstance(spec, StudySpec) for spec in specs)


def test_relocked_studyspecs_preserve_original_ids_and_parameters() -> None:
    originals = {payload["study_spec_id"]: payload for payload in _load_json(ORIGINAL_STUDY_SPECS)}

    for spec in _load_relocked_specs():
        original_id = spec.dataset_scope["relock_provenance"]["original_study_spec_id"]
        original = originals[original_id]
        for field in HELD_FIXED_FIELDS:
            assert getattr(spec, field) == original[field]

        assert spec.study_spec_id != original_id
        assert spec.dataset_scope["relock_provenance"]["original_study_spec_id"] == original_id
        assert spec.dataset_scope["relock_provenance"]["relock_phase_id"] == "FUTSUB-P27"


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


def test_relock_report_records_smoke_pass_and_all_inconclusive_classifications() -> None:
    report = RELOCK_REPORT.read_text(encoding="utf-8")

    assert "StudySpec resolver-smoke: PASS" in report
    assert "## Resolvable-Study List" in report
    assert "feature_pack_not_found" in report
    for study_spec_id in PRIOR_INCONCLUSIVE_IDS:
        assert study_spec_id in report


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


class _EmptyFeatureStore:
    def resolve_active_feature(self, feature_version_id: object) -> None:
        return None

    def resolve_feature_by_version(self, feature_version_id: object) -> None:
        return None
