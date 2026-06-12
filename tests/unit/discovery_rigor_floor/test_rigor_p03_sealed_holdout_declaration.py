from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from alpha_system.governance.sealed_holdout import (
    SealedHoldoutRegistry,
    SealedHoldoutStatus,
    access_intersects_holdout,
)
from alpha_system.governance.study_spec import StudySpec

DECLARATION_PATH = Path(
    "research/discovery_rigor_floor_v1/sealed_holdout/kill_shot_sealed_holdout_window.json"
)
RELOCKED_STUDY_SPEC_DIR = Path("research/futures_substrate_scaleout_v1/rerun/study_specs")
LOCKED_TEST_START = "2025-01-01"
LOCKED_TEST_START_TS = f"{LOCKED_TEST_START}T00:00:00"


def test_kill_shot_sealed_holdout_declaration_validates_value_free() -> None:
    registry = SealedHoldoutRegistry(DECLARATION_PATH)

    window = registry.active_window()

    assert window.window_id == "holdwin_bcf16744d03b8546a219fcd1"
    assert window.status is SealedHoldoutStatus.SEALED
    assert window.start_date == LOCKED_TEST_START
    assert window.end_date is None
    assert window.rolling is True
    assert window.provenance is not None
    assert window.provenance["value_free"] is True
    assert window.provenance["phase_id"] == "P033000_HOLDOUT_WINDOW_COVERAGE"
    assert window.provenance["relocked_studyspec_count"] == 10
    assert window.provenance["locked_test_partition_count"] == 32
    assert "docs/OPERATING_COMPASS_V4.md" in str(window.provenance["compass_ref"])
    assert window.partition_spec["dataset_family"] == [
        "futures_core_alpha_pilot_v1",
        "futures_substrate_scaleout_v1",
    ]
    assert window.partition_spec["symbols"] == ["ES", "NQ", "RTY"]
    assert window.superseded_declaration is not None
    assert (
        window.superseded_declaration["window_id"]
        == "holdwin_d5cba50af19976275ab26f34"
    )
    assert (
        window.redeclaration_reason is not None
        and "P033000_HOLDOUT_WINDOW_COVERAGE" in window.redeclaration_reason
    )


def test_kill_shot_window_intersects_every_relocked_locked_test_input() -> None:
    window = SealedHoldoutRegistry(DECLARATION_PATH).active_window()
    specs = _load_relocked_specs()

    assert len(specs) == 10

    seen_symbols: set[str] = set()
    seen_partitions: set[str] = set()
    checked_partition_accesses = 0
    for spec in specs:
        locks = _locked_test_dataset_locks(spec)
        assert locks
        locked_partitions = sorted(
            {partition for lock in locks for partition in lock["partitions"]}
        )

        for symbol in spec.dataset_scope["target_instruments"]:
            seen_symbols.add(str(symbol))
            assert access_intersects_holdout(
                window,
                access_start_date=LOCKED_TEST_START,
                access_partition_spec=_access_partition_spec(
                    spec,
                    locks=locks,
                    symbols=[str(symbol)],
                    partitions=locked_partitions,
                ),
            ), spec.study_spec_id

        for lock in locks:
            lock_partition_spec = _access_partition_spec(
                spec,
                locks=[lock],
                symbols=[str(symbol) for symbol in spec.dataset_scope["target_instruments"]],
                partitions=[str(partition) for partition in lock["partitions"]],
            )
            for partition in lock["partitions"]:
                seen_partitions.add(str(partition))
                assert access_intersects_holdout(
                    window,
                    access_start_date=_date_part(str(lock["start_ts"])),
                    access_end_date=_date_part(str(lock["end_ts"])),
                    access_partition_spec={
                        **lock_partition_spec,
                        "futsub_locked_test_partitions": [str(partition)],
                    },
                ), f"{spec.study_spec_id} {partition}"
                checked_partition_accesses += 1

    assert seen_symbols == {"ES", "NQ", "RTY"}
    assert len(seen_partitions) == 32
    assert checked_partition_accesses > 0


def test_kill_shot_window_contract_is_non_vacuous_and_temporally_bounded() -> None:
    window = SealedHoldoutRegistry(DECLARATION_PATH).active_window()
    first_spec = _load_relocked_specs()[0]
    first_lock = _locked_test_dataset_locks(first_spec)[0]
    matching_partition = str(first_lock["partitions"][0])
    matching_scope = _access_partition_spec(
        first_spec,
        locks=[first_lock],
        symbols=["ES"],
        partitions=[matching_partition],
    )

    assert access_intersects_holdout(
        window,
        access_start_date="2026-06-12",
        access_end_date="2027-01-01",
        access_partition_spec=matching_scope,
    )
    assert not access_intersects_holdout(
        window,
        access_start_date="2024-01-01",
        access_end_date="2024-12-31",
        access_partition_spec=matching_scope,
    )
    assert not access_intersects_holdout(
        window,
        access_start_date=LOCKED_TEST_START,
        access_partition_spec={
            **matching_scope,
            "dataset_family": "outside_research_family",
            "futsub_study_families": ["outside_family"],
            "symbols": ["CL"],
            "target_instruments": ["CL"],
        },
    )


def _load_relocked_specs() -> tuple[StudySpec, ...]:
    paths = sorted(RELOCKED_STUDY_SPEC_DIR.glob("sspec_*.json"))
    return tuple(StudySpec.from_mapping(_load_json(path)) for path in paths)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _locked_test_dataset_locks(spec: StudySpec) -> tuple[Mapping[str, Any], ...]:
    return tuple(
        lock
        for lock in spec.dataset_scope["dataset_version_locks"]
        if str(lock["start_ts"]) >= LOCKED_TEST_START_TS
    )


def _access_partition_spec(
    spec: StudySpec,
    *,
    locks: Iterable[Mapping[str, Any]],
    symbols: list[str],
    partitions: list[str],
) -> dict[str, object]:
    scope = spec.dataset_scope
    locks = tuple(locks)
    return {
        "dataset_family": "futures_substrate_scaleout_v1",
        "futsub_campaign_id": scope["campaign_id"],
        "futsub_locked_test_partitions": sorted(partitions),
        "futsub_relock_phase_id": scope["relock_provenance"]["relock_phase_id"],
        "futsub_schema_ids": sorted({str(lock["schema_id"]) for lock in locks}),
        "futsub_sources": sorted({str(lock["source"]) for lock in locks}),
        "futsub_study_families": [str(scope["family"])],
        "split_role": "locked_test",
        "symbols": sorted(symbols),
        "target_instruments": sorted(symbols),
    }


def _date_part(timestamp: str) -> str:
    return timestamp.split("T", 1)[0]
