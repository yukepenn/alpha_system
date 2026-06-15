"""Unit tests for the BROAD_MINING_DRIVER_V0 multi-partition pooled mining driver.

These exercise the INTEGRATION seam without requiring unmaterialized data: the
per-partition ``fast_probe`` is replaced by synthetic readouts so the pooling math,
the partition-coverage honesty, the missing-partition fail-closed DATA_GAP, the
family-FDR routing of the pooled verdict, and the unattended loop's idempotent skip
are all tested deterministically.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from alpha_system.governance.family_fdr_ledger import FamilyFdrLedger
from alpha_system.governance.idea_draft import build_idea_validation_bundle
from alpha_system.research_lane import mining_driver as mining_driver_module
from alpha_system.research_lane.mining_driver import (
    MiningDriverError,
    PartitionCoverage,
    already_recorded_alpha_spec_ids,
    mine_ideas,
    run_multi_partition_pool,
)

FIXTURE_IDEA = Path("research/idea_to_verdict_loop_v0/fixtures/day_of_week.idea.yaml")
TIMESTAMP = "2026-06-14T00:00:00Z"


def _bundle():
    return build_idea_validation_bundle(
        json.loads(FIXTURE_IDEA.read_text(encoding="utf-8")),
        source=FIXTURE_IDEA.as_posix(),
    )


def _slice_payload(slice_id: str) -> dict[str, object]:
    """A minimal VALID SliceSpec payload (fast_probe is mocked; only slice_id read)."""

    return {
        "slice_id": slice_id,
        "study_kind": "context_not_equal_trigger",
        "dataset_version_id": "dsv_unit",
        "partition_id": slice_id,
        "instrument_id": "ES",
        "session_id": "ES:RTH",
        "data_version": "dsv_unit",
        "features": [
            {
                "role": "context",
                "factor_id": "ctx_factor",
                "factor_version": "v1",
                "pack_ref": "fver_unit_ctx",
            },
            {
                "role": "trigger",
                "factor_id": "trg_factor",
                "factor_version": "v1",
                "pack_ref": "fver_unit_trg",
            },
        ],
        "labels": [
            {"role": "path", "label_id": "path_unit", "pack_ref": "lver_unit"},
        ],
    }


def _slices(slice_ids) -> dict[str, dict[str, object]]:
    return {sid: _slice_payload(sid) for sid in slice_ids}


def _setup_readout(
    *,
    slice_id: str,
    mean_lift: float | None,
    n_eff: int = 400,
    run_count: int = 200,
    gate_pass_count: int = 0,
    status: str = "RECORDED",
) -> dict[str, object]:
    """A synthetic setup-lane RECORDED readout carrying a net-excursion mean_lift."""

    return {
        "schema": "alpha_system.research_lane.fast_probe.v1",
        "readout_id": f"fpsetup_{slice_id}",
        "status": status,
        "study_kind": "context_not_equal_trigger",
        "stamp": "EXPLORATORY",
        "promotion_eligible": False,
        "slice_spec": {"slice_id": slice_id, "study_kind": "context_not_equal_trigger"},
        "row_access": {"status": "resolved_local_only", "fabricated_values": False},
        "power": {"n_eff": n_eff, "mde_abs_ic": 0.08},
        "surrogate_fdr_gate": {
            "gate_status": "PASSED",
            "threshold_verdict": "zero-pass-met",
            "run_count": run_count,
            "gate_pass_count": gate_pass_count,
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


def _data_gap_readout(*, slice_id: str) -> dict[str, object]:
    """A synthetic honest DATA_GAP readout for a missing/unmaterialized partition."""

    return {
        "schema": "alpha_system.research_lane.fast_probe.v1",
        "readout_id": f"fpgap_{slice_id}",
        "status": "INCONCLUSIVE",
        "issue_code": "DATA_GAP",
        "study_kind": "context_not_equal_trigger",
        "stamp": "EXPLORATORY",
        "promotion_eligible": False,
        "slice_spec": {"slice_id": slice_id, "study_kind": "context_not_equal_trigger"},
        "row_access": {"status": "unresolved", "fabricated_values": False},
        "surrogate_fdr_gate": {
            "gate_status": "BLOCKED",
            "threshold_verdict": "CALIBRATION_BLOCKED",
        },
        "power": {"n_eff": 0, "mde_abs_ic": None},
    }


def _patch_probe(monkeypatch, readouts_by_slice: dict[str, dict[str, object]]) -> list[str]:
    """Replace fast_probe with a synthetic per-slice lookup; record call order."""

    calls: list[str] = []

    def fake_fast_probe(card, setup, slice_spec, *, resolver=None, env=None):
        slice_id = slice_spec.slice_id
        calls.append(slice_id)
        if slice_id not in readouts_by_slice:
            raise AssertionError(f"unexpected slice probed: {slice_id}")
        return readouts_by_slice[slice_id]

    monkeypatch.setattr(mining_driver_module, "fast_probe", fake_fast_probe)
    return calls


# ---------------------------------------------------------------------------
# Multi-partition pooling correctness
# ---------------------------------------------------------------------------


def test_multi_partition_pool_aggregates_equal_weight_mean(monkeypatch) -> None:
    bundle = _bundle()
    readouts = {
        "ES_2020_120m": _setup_readout(slice_id="ES_2020_120m", mean_lift=0.01, n_eff=100),
        "ES_2021_120m": _setup_readout(slice_id="ES_2021_120m", mean_lift=0.03, n_eff=200),
        "ES_2022_120m": _setup_readout(slice_id="ES_2022_120m", mean_lift=0.05, n_eff=300),
    }
    calls = _patch_probe(monkeypatch, readouts)

    result = run_multi_partition_pool(
        {"slices": _slices(readouts)},
        bundle.idea_draft,
        bundle.mechanism_card,
        bundle.setup_spec,
        list(readouts),
        created_at=TIMESTAMP,
    )

    assert calls == ["ES_2020_120m", "ES_2021_120m", "ES_2022_120m"]
    # equal-weight mean of 0.01, 0.03, 0.05 == 0.03; n_eff sums (100+200+300) == 600.
    assert result.pooled_metric is not None
    assert result.pooled_metric["pooled_result"]["point_estimate"] == pytest.approx(0.03)
    assert result.pooled_metric["pooled_result"]["n_eff"] == 600
    assert result.coverage.present_count == 3
    assert result.coverage.is_multi_partition is True
    assert result.pooled_hypothesis_id is not None
    assert result.pooled_verdict == "INCONCLUSIVE"


def test_pool_two_partitions_matches_aggregate_pooled_metric(monkeypatch) -> None:
    bundle = _bundle()
    readouts = {
        "ES_2020_120m": _setup_readout(slice_id="ES_2020_120m", mean_lift=-0.004, n_eff=412),
        "NQ_2020_120m": _setup_readout(slice_id="NQ_2020_120m", mean_lift=-0.002, n_eff=388),
    }
    _patch_probe(monkeypatch, readouts)

    result = run_multi_partition_pool(
        {"slices": _slices(readouts)},
        bundle.idea_draft,
        bundle.mechanism_card,
        bundle.setup_spec,
        list(readouts),
        created_at=TIMESTAMP,
    )

    assert result.pooled_metric["pooled_result"]["point_estimate"] == pytest.approx(-0.003)
    assert result.pooled_metric["pooled_result"]["n_eff"] == 800
    assert result.coverage.present == ("ES_2020_120m", "NQ_2020_120m")


# ---------------------------------------------------------------------------
# Partition-coverage reporting + missing-partition fail-closed DATA_GAP
# ---------------------------------------------------------------------------


def test_partition_coverage_records_missing_partitions_present(monkeypatch) -> None:
    bundle = _bundle()
    readouts = {
        "ES_2020_120m": _setup_readout(slice_id="ES_2020_120m", mean_lift=0.02, n_eff=500),
        "ES_2021_120m": _data_gap_readout(slice_id="ES_2021_120m"),
        "ES_2022_120m": _data_gap_readout(slice_id="ES_2022_120m"),
    }
    _patch_probe(monkeypatch, readouts)

    result = run_multi_partition_pool(
        {"slices": _slices(readouts)},
        bundle.idea_draft,
        bundle.mechanism_card,
        bundle.setup_spec,
        list(readouts),
        created_at=TIMESTAMP,
    )

    # One present partition -> coverage=1, NOT multi-partition OOS, but still pooled
    # (degenerate pool of 1) with explicit honest coverage.
    assert result.coverage.declared_count == 3
    assert result.coverage.present == ("ES_2020_120m",)
    assert set(result.coverage.missing) == {"ES_2021_120m", "ES_2022_120m"}
    assert result.coverage.is_multi_partition is False
    assert result.pooled_metric["pooled_result"]["point_estimate"] == pytest.approx(0.02)
    payload = result.to_dict()
    assert payload["partition_coverage"]["is_multi_partition_oos"] is False
    assert payload["partition_coverage"]["present_count"] == 1


def test_all_partitions_missing_fails_closed_with_data_gap(monkeypatch) -> None:
    bundle = _bundle()
    readouts = {
        "ES_2020_120m": _data_gap_readout(slice_id="ES_2020_120m"),
        "ES_2021_120m": _data_gap_readout(slice_id="ES_2021_120m"),
    }
    _patch_probe(monkeypatch, readouts)

    result = run_multi_partition_pool(
        {"slices": _slices(readouts)},
        bundle.idea_draft,
        bundle.mechanism_card,
        bundle.setup_spec,
        list(readouts),
        created_at=TIMESTAMP,
    )

    # Fail closed: no poolable component -> DATA_GAP pooled verdict, NO pooled metric,
    # NO route (the run never fabricates a pooled statistic from absent data).
    assert result.pooled_verdict == "DATA_GAP"
    assert result.pooled_metric is None
    assert result.pooled_hypothesis_id is None
    assert result.route is None
    assert result.coverage.present_count == 0
    assert set(result.coverage.missing) == {"ES_2020_120m", "ES_2021_120m"}


def test_undeclared_partition_fails_closed_not_aborts(monkeypatch) -> None:
    bundle = _bundle()
    # ES_2099_120m is NOT declared in the idea's slice set -> it must fail closed as a
    # DATA_GAP partition outcome (substrate absent), NOT abort the whole pooled run.
    readouts = {
        "ES_2020_120m": _setup_readout(slice_id="ES_2020_120m", mean_lift=0.02, n_eff=500),
    }
    _patch_probe(monkeypatch, readouts)

    result = run_multi_partition_pool(
        {"slices": _slices(["ES_2020_120m"])},
        bundle.idea_draft,
        bundle.mechanism_card,
        bundle.setup_spec,
        ["ES_2020_120m", "ES_2099_120m"],
        created_at=TIMESTAMP,
    )

    assert result.coverage.present == ("ES_2020_120m",)
    assert result.coverage.missing == ("ES_2099_120m",)
    undeclared = next(o for o in result.partition_outcomes if o.slice_id == "ES_2099_120m")
    assert undeclared.present is False
    assert undeclared.issue_code == "DATA_GAP"
    assert result.pooled_metric is not None  # the one present partition still pools (coverage=1)


def test_present_but_null_mean_lift_is_not_poolable(monkeypatch) -> None:
    bundle = _bundle()
    readouts = {
        "ES_2020_120m": _setup_readout(slice_id="ES_2020_120m", mean_lift=None),
    }
    _patch_probe(monkeypatch, readouts)

    result = run_multi_partition_pool(
        {"slices": _slices(readouts)},
        bundle.idea_draft,
        bundle.mechanism_card,
        bundle.setup_spec,
        list(readouts),
        created_at=TIMESTAMP,
    )

    assert result.pooled_verdict == "DATA_GAP"
    assert result.coverage.present_count == 0


def test_empty_partition_set_raises() -> None:
    bundle = _bundle()
    with pytest.raises(MiningDriverError):
        run_multi_partition_pool(
            {"slices": {}},
            bundle.idea_draft,
            bundle.mechanism_card,
            bundle.setup_spec,
            [],
        )


# ---------------------------------------------------------------------------
# Pooled verdict routes through the family-FDR gate
# ---------------------------------------------------------------------------


def test_pooled_verdict_routes_through_family_fdr_to_shelf(monkeypatch, tmp_path) -> None:
    bundle = _bundle()
    readouts = {
        "ES_2020_120m": _setup_readout(
            slice_id="ES_2020_120m", mean_lift=0.02, n_eff=500, run_count=2000
        ),
        "ES_2021_120m": _setup_readout(
            slice_id="ES_2021_120m", mean_lift=0.03, n_eff=600, run_count=2000
        ),
    }
    _patch_probe(monkeypatch, readouts)
    ledger_path = tmp_path / "family_fdr_ledger.jsonl"
    ledger_path.touch()

    result = run_multi_partition_pool(
        {"slices": _slices(readouts)},
        bundle.idea_draft,
        bundle.mechanism_card,
        bundle.setup_spec,
        list(readouts),
        created_at=TIMESTAMP,
        family_fdr_ledger_path=ledger_path,
    )

    # A high-resolution surrogate (run_count=2000) on a singleton pooled family clears
    # the family-FDR gate -> the pooled signal reaches the reviewer shelf with the
    # family-FDR verdict attached, and the family-FDR ledger recorded the entry.
    assert result.route is not None
    assert result.route.action == "reviewer_pending_shelf"
    assert result.route.promotion_eligible is False
    attachment = result.route.memory_record.get("family_fdr_verdict")
    assert attachment is not None
    assert attachment["provisional"] is True
    recorded = FamilyFdrLedger(ledger_path).load_records()
    assert len(recorded) == 1


def test_pooled_verdict_routes_to_requeue_when_surrogate_unresolved(
    monkeypatch, tmp_path
) -> None:
    bundle = _bundle()
    # A low surrogate run_count (=2) both fails to resolve the corrected threshold AND
    # its per-test p (1/3) does not clear it -> the family-FDR gate routes the pooled
    # signal to requeue (not graveyard), reproducing the reviewer's REWORK logic.
    readouts = {
        "ES_2020_120m": _setup_readout(
            slice_id="ES_2020_120m", mean_lift=0.02, n_eff=500, run_count=2
        ),
        "ES_2021_120m": _setup_readout(
            slice_id="ES_2021_120m", mean_lift=0.03, n_eff=600, run_count=2
        ),
    }
    _patch_probe(monkeypatch, readouts)
    ledger_path = tmp_path / "family_fdr_ledger.jsonl"
    ledger_path.touch()

    result = run_multi_partition_pool(
        {"slices": _slices(readouts)},
        bundle.idea_draft,
        bundle.mechanism_card,
        bundle.setup_spec,
        list(readouts),
        created_at=TIMESTAMP,
        family_fdr_ledger_path=ledger_path,
    )

    assert result.route is not None
    assert result.route.action == "requeue"
    assert result.route.memory_record.get("family_fdr_requeue_reason") is not None


# ---------------------------------------------------------------------------
# The unattended loop skips already-recorded ideas (idempotent / resumable)
# ---------------------------------------------------------------------------


def test_mine_ideas_skips_already_recorded(monkeypatch, tmp_path) -> None:
    bundle = _bundle()
    readouts = {
        "ES_2020_120m": _setup_readout(slice_id="ES_2020_120m", mean_lift=0.02, n_eff=500),
    }
    _patch_probe(monkeypatch, readouts)
    memory_dir = tmp_path / "research_memory"
    memory_dir.mkdir()
    payload = {"slices": _slices(["ES_2020_120m"])}

    def fake_load(path):
        return payload

    def fake_build(loaded, source):
        return _bundle()

    # First pass mines + persists.
    first = mine_ideas(
        [FIXTURE_IDEA.as_posix()],
        partition_policy=["ES_2020_120m"],
        persist=True,
        memory_dir=memory_dir,
        load_idea=fake_load,
        build_bundle=fake_build,
    )
    assert first.results[0].status == "mined"
    assert first.results[0].present_count == 1
    recorded = already_recorded_alpha_spec_ids(memory_dir=memory_dir)
    assert bundle.idea_draft.alpha_spec_id in recorded

    # Second pass (resume) skips the already-recorded idea: fast_probe is NOT called.
    second_calls: list[str] = []

    def fail_probe(card, setup, slice_spec, *, resolver=None, env=None):
        second_calls.append(slice_spec.slice_id)
        raise AssertionError("a skipped idea must not be re-probed")

    monkeypatch.setattr(mining_driver_module, "fast_probe", fail_probe)
    second = mine_ideas(
        [FIXTURE_IDEA.as_posix()],
        partition_policy=["ES_2020_120m"],
        persist=True,
        memory_dir=memory_dir,
        load_idea=fake_load,
        build_bundle=fake_build,
    )
    assert second.results[0].status == "skipped"
    assert second_calls == []


def test_mine_ideas_summary_counts_routes(monkeypatch, tmp_path) -> None:
    readouts = {
        "ES_2020_120m": _setup_readout(slice_id="ES_2020_120m", mean_lift=0.02, n_eff=500),
    }
    _patch_probe(monkeypatch, readouts)
    payload = {"slices": _slices(["ES_2020_120m"])}

    summary = mine_ideas(
        [FIXTURE_IDEA.as_posix()],
        partition_policy=["ES_2020_120m"],
        persist=False,
        memory_dir=tmp_path / "research_memory",
        load_idea=lambda path: payload,
        build_bundle=lambda loaded, source: _bundle(),
        skip_recorded=False,
    )

    payload_summary = summary.to_dict()
    assert payload_summary["idea_count"] == 1
    assert payload_summary["status_counts"]["mined"] == 1
    assert sum(payload_summary["route_counts"].values()) == 1


def test_mine_ideas_records_error_without_aborting(monkeypatch, tmp_path) -> None:
    def boom_load(path):
        raise ValueError("synthetic load failure")

    summary = mine_ideas(
        ["one.idea.yaml", "two.idea.yaml"],
        persist=False,
        memory_dir=tmp_path / "research_memory",
        load_idea=boom_load,
        build_bundle=lambda loaded, source: _bundle(),
        skip_recorded=False,
    )

    # The loop records an error per idea and does not abort the batch.
    assert len(summary.results) == 2
    assert all(result.status == "error" for result in summary.results)
    assert summary.to_dict()["status_counts"]["error"] == 2


def test_partition_coverage_dataclass_shape() -> None:
    coverage = PartitionCoverage(
        declared=("a", "b", "c"), present=("a",), missing=("b", "c")
    )
    assert coverage.declared_count == 3
    assert coverage.present_count == 1
    assert coverage.is_multi_partition is False
    assert coverage.to_dict()["is_multi_partition_oos"] is False
