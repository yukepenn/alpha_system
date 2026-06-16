"""Unit tests for the append-only family-FDR ledger and fail-closed validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from alpha_system.governance.family_fdr_correction import FDR_METHOD_BONFERRONI
from alpha_system.governance.family_fdr_ledger import (
    FamilyFdrLedger,
    FamilyFdrLedgerRecord,
    create_family_fdr_ledger_record,
    evaluate_family_fdr,
    family_batch_key,
    generate_family_fdr_ledger_record_id,
    validate_family_fdr_ledger,
    validate_family_fdr_ledger_record,
)
from alpha_system.governance.validation import GovernanceValidationError

TIMESTAMP = "2026-06-15T00:00:00Z"


def _entries() -> list[dict[str, object]]:
    # "strong": resolution-adequate and corrected-significant -> eligible.
    # "weak": clearly non-significant (large per-test p) -> not eligible.
    return [
        {"idea_key": "strong", "p_value": 0.0001, "run_count": 10_000},
        {"idea_key": "weak", "p_value": 0.9, "run_count": 10_000},
    ]


def _empty_ledger(tmp_path: Path) -> Path:
    path = tmp_path / "family_fdr.jsonl"
    path.write_text("", encoding="utf-8")
    return path


def test_family_batch_key_anchors_declared_family_across_alpha_specs() -> None:
    # A DECLARED family (family_id != alpha_spec_id) anchors the batch key on the
    # family_id so co-mined variants carrying DISTINCT alpha_spec_ids co-correct as
    # ONE m=N family (the pre-registered counted-variant group). Anchoring on
    # alpha_spec_id would split a declared family into families-of-one -> no
    # cross-variant multiplicity tax (gate-weakening under-correction).
    key_a = family_batch_key(alpha_spec_id="AS1", slice_id="S1", family_id="F1")
    key_b = family_batch_key(alpha_spec_id="AS2", slice_id="S1", family_id="F1")
    assert key_a == "F1::S1::F1"
    assert key_a == key_b  # distinct alpha_specs, one declared family -> one batch


def test_family_batch_key_keeps_singletons_separate() -> None:
    # An UNDECLARED singleton falls back to family_id == alpha_spec_id; the anchor
    # stays the alpha_spec_id so distinct singletons remain honest families-of-one
    # and are NEVER merged (no false-merge of ideas that did not declare a family).
    key_a = family_batch_key(alpha_spec_id="AS1", slice_id="S1", family_id="AS1")
    key_b = family_batch_key(alpha_spec_id="AS2", slice_id="S1", family_id="AS2")
    assert key_a == "AS1::S1::AS1"
    assert key_a != key_b


def test_evaluate_family_fdr_builds_records() -> None:
    evaluation = evaluate_family_fdr(
        family_id="F1",
        slice_id="ES_2020_120m",
        alpha_spec_id="AS1",
        entries=_entries(),
        alpha_fw=0.10,
        method=FDR_METHOD_BONFERRONI,
        created_at=TIMESTAMP,
    )
    assert evaluation.family_size == 2
    assert len(evaluation.records) == 2
    by_key = {v.idea_key: v for v in evaluation.verdicts}
    assert by_key["strong"].eligible is True
    # F1 is a DECLARED family (F1 != AS1) -> the batch key anchors on the family_id.
    assert all(r.batch_key == "F1::ES_2020_120m::F1" for r in evaluation.records)


def test_validate_family_fdr_ledger_persists_and_is_idempotent(tmp_path: Path) -> None:
    path = _empty_ledger(tmp_path)
    evaluation = validate_family_fdr_ledger(
        family_id="F1",
        slice_id="ES_2020_120m",
        alpha_spec_id="AS1",
        entries=_entries(),
        family_fdr_ledger_path=path,
        alpha_fw=0.10,
        method=FDR_METHOD_BONFERRONI,
        created_at=TIMESTAMP,
    )
    ledger = FamilyFdrLedger(path)
    assert len(ledger.load_records()) == 2
    assert len({r.record_id for r in ledger.load_records()}) == 2

    # Re-running the same batch must not duplicate records (idempotent by record_id).
    validate_family_fdr_ledger(
        family_id="F1",
        slice_id="ES_2020_120m",
        alpha_spec_id="AS1",
        entries=_entries(),
        family_fdr_ledger_path=path,
        alpha_fw=0.10,
        method=FDR_METHOD_BONFERRONI,
        created_at=TIMESTAMP,
    )
    assert len(ledger.load_records()) == 2
    summary = ledger.summary()
    assert summary["batch_count"] == 1
    assert summary["record_count"] == 2
    assert evaluation.eligible_count == 1


def test_no_persist_leaves_ledger_empty(tmp_path: Path) -> None:
    path = _empty_ledger(tmp_path)
    validate_family_fdr_ledger(
        family_id="F1",
        slice_id="S1",
        alpha_spec_id="AS1",
        entries=_entries(),
        family_fdr_ledger_path=path,
        persist=False,
        created_at=TIMESTAMP,
    )
    assert FamilyFdrLedger(path).load_records() == ()


def test_record_round_trip() -> None:
    evaluation = evaluate_family_fdr(
        family_id="F1",
        slice_id="S1",
        alpha_spec_id="AS1",
        entries=_entries(),
        created_at=TIMESTAMP,
    )
    record = evaluation.records[0]
    restored = validate_family_fdr_ledger_record(record.to_dict())
    assert restored == record
    from_json = FamilyFdrLedgerRecord.from_canonical_json(record.to_canonical_json())
    assert from_json == record


def test_missing_ledger_file_is_fail_closed(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist.jsonl"
    with pytest.raises(GovernanceValidationError):
        validate_family_fdr_ledger(
            family_id="F1",
            slice_id="S1",
            alpha_spec_id="AS1",
            entries=_entries(),
            family_fdr_ledger_path=missing,
            created_at=TIMESTAMP,
        )


def test_missing_ledger_path_is_fail_closed() -> None:
    with pytest.raises(GovernanceValidationError):
        validate_family_fdr_ledger(
            family_id="F1",
            slice_id="S1",
            alpha_spec_id="AS1",
            entries=_entries(),
            family_fdr_ledger_path=None,
            created_at=TIMESTAMP,
        )


def test_tampered_record_id_is_rejected() -> None:
    record = create_family_fdr_ledger_record(
        family_id="F1",
        slice_id="S1",
        alpha_spec_id="AS1",
        idea_key="strong",
        p_value=0.0001,
        run_count=10_000,
        verdict=evaluate_family_fdr(
            family_id="F1",
            slice_id="S1",
            alpha_spec_id="AS1",
            entries=[{"idea_key": "strong", "p_value": 0.0001, "run_count": 10_000}],
            created_at=TIMESTAMP,
        ).verdicts[0],
        created_at=TIMESTAMP,
    )
    payload = record.to_dict()
    payload["record_id"] = "FamilyFdrLedgerRecord:deadbeef"
    with pytest.raises(GovernanceValidationError):
        validate_family_fdr_ledger_record(payload)


def test_batch_key_mismatch_is_rejected() -> None:
    record = create_family_fdr_ledger_record(
        family_id="F1",
        slice_id="S1",
        alpha_spec_id="AS1",
        idea_key="strong",
        p_value=0.0001,
        run_count=10_000,
        verdict=evaluate_family_fdr(
            family_id="F1",
            slice_id="S1",
            alpha_spec_id="AS1",
            entries=[{"idea_key": "strong", "p_value": 0.0001, "run_count": 10_000}],
            created_at=TIMESTAMP,
        ).verdicts[0],
        created_at=TIMESTAMP,
    )
    payload = record.to_dict()
    payload["batch_key"] = "WRONG::KEY::HERE"
    payload["record_id"] = generate_family_fdr_ledger_record_id(payload)
    with pytest.raises(GovernanceValidationError):
        validate_family_fdr_ledger_record(payload)


def test_corrupt_ledger_row_is_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "family_fdr.jsonl"
    path.write_text("not valid json\n", encoding="utf-8")
    with pytest.raises(GovernanceValidationError):
        FamilyFdrLedger(path).load_records()
