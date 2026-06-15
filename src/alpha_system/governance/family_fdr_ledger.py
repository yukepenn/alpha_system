"""Append-only JSONL ledger for cross-idea family-FDR corrections (Stage A).

Mirrors ``governance/variant_ledger.py``: a fail-closed JSONL ledger of
validated records, an idempotent ``append_records``, a value-free ``summary``,
an ``evaluate_family_fdr`` evaluator (mirroring ``evaluate_family_budget``), and
a fail-closed ``validate_family_fdr_ledger`` entry point (mirroring
``validate_variant_and_family_budget``: load -> evaluate -> optionally persist).

Each ``FamilyFdrLedgerRecord`` records one idea's outcome inside one co-mined
batch: the batch identity ``(family_id, slice_id, alpha_spec_id)``, the idea's
``(idea_key, p_value, run_count)``, and the corrected ``FamilyFdrVerdict``. The
batch identity is ``(alpha_spec_id, slice_id)`` + ``family_id`` -- no invented
YAML ``batch_id`` (per DESIGN section 2.4).

This is research-only diagnostic plumbing. It defines no PnL/value truth, makes
NO profitability/tradability/alpha claim, and is NOT wired into any live verdict
path in Stage A. The corrected verdict is a deterministic RECORD; the machine
NEVER auto-promotes.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from alpha_system.governance.family_fdr_correction import (
    DEFAULT_FDR_ALPHA,
    DEFAULT_FDR_METHOD,
    FamilyFdrVerdict,
    correct_family,
)
from alpha_system.governance.serialization import (
    GovernanceSerializationError,
    JsonValue,
    canonical_serialize,
    content_hash,
    deserialize,
)
from alpha_system.governance.validation import (
    ExpectedType,
    GovernanceValidationError,
    ValidationIssue,
    require_mapping,
    validate_schema,
)

FAMILY_FDR_LEDGER_RECORD_ID_PREFIX = "FamilyFdrLedgerRecord"
FAMILY_FDR_LEDGER_RECORD_REQUIRED_FIELDS = (
    "record_id",
    "family_id",
    "slice_id",
    "batch_key",
    "alpha_spec_id",
    "idea_key",
    "p_value",
    "run_count",
    "verdict",
    "created_at",
)
FAMILY_FDR_LEDGER_RECORD_FIELD_TYPES: dict[str, ExpectedType] = {
    "record_id": str,
    "family_id": str,
    "slice_id": str,
    "batch_key": str,
    "alpha_spec_id": str,
    "idea_key": str,
    "p_value": (int, float),
    "run_count": int,
    "verdict": dict,
    "created_at": str,
}
# Fields hashed into the deterministic record_id (everything but the id itself).
FAMILY_FDR_LEDGER_RECORD_ID_COMPONENT_FIELDS = tuple(
    field for field in FAMILY_FDR_LEDGER_RECORD_REQUIRED_FIELDS if field != "record_id"
)
_VAGUE_TEXT = {
    "",
    "-",
    "n/a",
    "na",
    "none",
    "null",
    "tbd",
    "todo",
    "unknown",
    "placeholder",
}


def family_batch_key(*, alpha_spec_id: str, slice_id: str, family_id: str) -> str:
    """Deterministic co-mined batch identity ``(alpha_spec_id, slice_id, family_id)``.

    No invented YAML ``batch_id`` -- the batch is the set of ideas sharing an
    AlphaSpec, slice, and family (DESIGN section 2.4).
    """

    return f"{alpha_spec_id}::{slice_id}::{family_id}"


@dataclass(frozen=True, slots=True)
class FamilyFdrLedgerRecord:
    """Validated append-only record of one idea's family-FDR correction outcome."""

    record_id: str
    family_id: str
    slice_id: str
    batch_key: str
    alpha_spec_id: str
    idea_key: str
    p_value: float
    run_count: int
    verdict: FamilyFdrVerdict
    created_at: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> FamilyFdrLedgerRecord:
        """Build a ``FamilyFdrLedgerRecord`` from a mapping after validation."""

        return validate_family_fdr_ledger_record(payload)

    @classmethod
    def from_canonical_json(cls, text: str) -> FamilyFdrLedgerRecord:
        """Deserialize canonical JSON and validate the resulting record."""

        value = deserialize(text)
        mapping = require_mapping(value, object_name="FamilyFdrLedgerRecord")
        return validate_family_fdr_ledger_record(mapping)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible representation."""

        return {
            "record_id": self.record_id,
            "family_id": self.family_id,
            "slice_id": self.slice_id,
            "batch_key": self.batch_key,
            "alpha_spec_id": self.alpha_spec_id,
            "idea_key": self.idea_key,
            "p_value": self.p_value,
            "run_count": self.run_count,
            "verdict": self.verdict.to_dict(),
            "created_at": self.created_at,
        }

    def to_canonical_json(self) -> str:
        """Serialize the validated record through the canonical primitive."""

        return canonical_serialize(self.to_dict())


@dataclass(frozen=True, slots=True)
class FamilyFdrEvaluation:
    """Result of evaluating one co-mined batch's family-FDR correction."""

    family_id: str
    slice_id: str
    batch_key: str
    method: str
    alpha_fw: float
    family_size: int
    verdicts: tuple[FamilyFdrVerdict, ...]
    records: tuple[FamilyFdrLedgerRecord, ...]

    @property
    def eligible_count(self) -> int:
        """Number of ideas eligible (corrected-significant AND resolution-adequate)."""

        return sum(1 for verdict in self.verdicts if verdict.eligible)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a value-free summary of the batch correction outcome."""

        return {
            "family_id": self.family_id,
            "slice_id": self.slice_id,
            "batch_key": self.batch_key,
            "method": self.method,
            "alpha_fw": self.alpha_fw,
            "family_size": self.family_size,
            "eligible_count": self.eligible_count,
            "verdicts": [verdict.to_dict() for verdict in self.verdicts],
        }


class FamilyFdrLedger:
    """Append-friendly JSONL persistence for validated family-FDR records."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = resolve_family_fdr_ledger_path(path)

    def load_records(self) -> tuple[FamilyFdrLedgerRecord, ...]:
        """Read all JSONL records fail-closed from the ledger path."""

        _require_existing_file(self.path)
        records: list[FamilyFdrLedgerRecord] = []
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise GovernanceValidationError(
                ValidationIssue(
                    field="family_fdr_ledger_path",
                    code="family_fdr_ledger_read_failed",
                    message="FamilyFdrLedger path could not be read",
                    expected="readable text JSONL ledger",
                    actual=f"{self.path}: {exc}",
                )
            ) from exc
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                value = deserialize(line)
                mapping = require_mapping(value, object_name="FamilyFdrLedgerRecord")
                records.append(validate_family_fdr_ledger_record(mapping))
            except (GovernanceSerializationError, GovernanceValidationError) as exc:
                raise GovernanceValidationError(
                    ValidationIssue(
                        field=f"family_fdr_ledger_path:{line_number}",
                        code="invalid_family_fdr_ledger_row",
                        message="FamilyFdrLedger row is not a valid canonical record",
                        expected="canonical FamilyFdrLedgerRecord JSON line",
                        actual=str(exc),
                    )
                ) from exc
        return tuple(records)

    def require_writable(self) -> None:
        """Fail closed unless the ledger exists and can be appended to."""

        _require_existing_file(self.path)
        _require_writable_file(self.path)

    def append_records(
        self,
        records: Iterable[FamilyFdrLedgerRecord],
    ) -> tuple[FamilyFdrLedgerRecord, ...]:
        """Append records not already represented by deterministic record_id."""

        existing = self.load_records()
        self.require_writable()
        existing_keys = {record.record_id for record in existing}
        to_append: list[FamilyFdrLedgerRecord] = []
        seen: set[str] = set(existing_keys)
        for record in records:
            if record.record_id in seen:
                continue
            seen.add(record.record_id)
            to_append.append(record)
        if not to_append:
            return ()
        try:
            with self.path.open("a", encoding="utf-8") as handle:
                for record in to_append:
                    handle.write(record.to_canonical_json())
                    handle.write("\n")
        except OSError as exc:
            raise GovernanceValidationError(
                ValidationIssue(
                    field="family_fdr_ledger_path",
                    code="family_fdr_ledger_append_failed",
                    message="FamilyFdrLedger path could not be appended",
                    expected="appendable text JSONL ledger",
                    actual=f"{self.path}: {exc}",
                )
            ) from exc
        return tuple(to_append)

    def summary(self) -> dict[str, JsonValue]:
        """Return a value-free summary of ledger contents by batch."""

        records = self.load_records()
        batches: dict[str, dict[str, Any]] = {}
        for record in records:
            item = batches.setdefault(
                record.batch_key,
                {
                    "family_id": record.family_id,
                    "slice_id": record.slice_id,
                    "alpha_spec_id": record.alpha_spec_id,
                    "idea_keys": set(),
                    "eligible_count": 0,
                    "record_count": 0,
                },
            )
            item["idea_keys"].add(record.idea_key)
            if record.verdict.eligible:
                item["eligible_count"] += 1
            item["record_count"] += 1
        batch_payload = {
            batch_key: {
                "family_id": values["family_id"],
                "slice_id": values["slice_id"],
                "alpha_spec_id": values["alpha_spec_id"],
                "idea_count": len(values["idea_keys"]),
                "idea_keys": sorted(values["idea_keys"]),
                "eligible_count": int(values["eligible_count"]),
                "record_count": int(values["record_count"]),
            }
            for batch_key, values in sorted(batches.items())
        }
        return {
            "ledger_path": str(self.path),
            "record_count": len(records),
            "batch_count": len(batch_payload),
            "batches": batch_payload,
        }


def resolve_family_fdr_ledger_path(path: str | Path | None = None) -> Path:
    """Resolve the explicitly supplied ledger path fail-closed."""

    if path is None or _normalize_text(path) in _VAGUE_TEXT:
        raise GovernanceValidationError(
            ValidationIssue(
                field="family_fdr_ledger_path",
                code="missing_family_fdr_ledger_path",
                message="FamilyFdrLedger path is required for fail-closed enforcement",
                expected="explicit path to an existing writable FamilyFdrLedger JSONL file",
                actual="missing",
            )
        )
    return Path(path).expanduser()


def generate_family_fdr_ledger_record_id(payload: Mapping[str, Any]) -> str:
    """Generate a deterministic record_id from the record's content fields."""

    mapping = require_mapping(payload, object_name="FamilyFdrLedgerRecord")
    components = {
        field: mapping[field]
        for field in FAMILY_FDR_LEDGER_RECORD_ID_COMPONENT_FIELDS
        if field in mapping
    }
    digest = content_hash(components)
    return f"{FAMILY_FDR_LEDGER_RECORD_ID_PREFIX}:{digest}"


def validate_family_fdr_ledger_record(payload: Mapping[str, Any]) -> FamilyFdrLedgerRecord:
    """Validate a ``FamilyFdrLedgerRecord`` mapping fail-closed and return a record."""

    mapping = validate_schema(
        payload,
        required_fields=FAMILY_FDR_LEDGER_RECORD_REQUIRED_FIELDS,
        field_types=FAMILY_FDR_LEDGER_RECORD_FIELD_TYPES,
        allowed_fields=FAMILY_FDR_LEDGER_RECORD_REQUIRED_FIELDS,
        object_name="FamilyFdrLedgerRecord",
    )

    issues: list[ValidationIssue] = []
    for field in ("family_id", "slice_id", "batch_key", "alpha_spec_id", "idea_key"):
        issues.extend(_validate_text_value(mapping[field], field=field))
    issues.extend(_validate_p_value(mapping["p_value"]))
    issues.extend(_validate_run_count(mapping["run_count"]))
    issues.extend(_validate_utc_timestamp(mapping["created_at"], field="created_at"))

    expected_batch_key = family_batch_key(
        alpha_spec_id=str(mapping["alpha_spec_id"]),
        slice_id=str(mapping["slice_id"]),
        family_id=str(mapping["family_id"]),
    )
    if mapping["batch_key"] != expected_batch_key:
        issues.append(
            ValidationIssue(
                field="batch_key",
                code="batch_key_mismatch",
                message="batch_key must equal (alpha_spec_id, slice_id, family_id) identity",
                expected=expected_batch_key,
                actual=str(mapping["batch_key"]),
            )
        )

    verdict = _parse_verdict(mapping["verdict"], issues)
    if verdict is not None:
        if verdict.idea_key != mapping["idea_key"]:
            issues.append(
                ValidationIssue(
                    field="verdict",
                    code="verdict_idea_key_mismatch",
                    message="verdict.idea_key must match the record idea_key",
                    expected=str(mapping["idea_key"]),
                    actual=verdict.idea_key,
                )
            )
        if float(verdict.p_value) != float(mapping["p_value"]):
            issues.append(
                ValidationIssue(
                    field="verdict",
                    code="verdict_p_value_mismatch",
                    message="verdict.p_value must match the record p_value",
                    expected=str(mapping["p_value"]),
                    actual=str(verdict.p_value),
                )
            )

    if not issues:
        expected_id = generate_family_fdr_ledger_record_id(mapping)
        if mapping["record_id"] != expected_id:
            issues.append(
                ValidationIssue(
                    field="record_id",
                    code="family_fdr_ledger_record_id_mismatch",
                    message="record_id must match deterministic FamilyFdrLedgerRecord content",
                    expected=expected_id,
                    actual=str(mapping["record_id"]),
                )
            )

    if issues:
        raise GovernanceValidationError(issues)
    assert verdict is not None
    return FamilyFdrLedgerRecord(
        record_id=mapping["record_id"],
        family_id=mapping["family_id"],
        slice_id=mapping["slice_id"],
        batch_key=mapping["batch_key"],
        alpha_spec_id=mapping["alpha_spec_id"],
        idea_key=mapping["idea_key"],
        p_value=float(mapping["p_value"]),
        run_count=mapping["run_count"],
        verdict=verdict,
        created_at=mapping["created_at"],
    )


def create_family_fdr_ledger_record(
    *,
    family_id: str,
    slice_id: str,
    alpha_spec_id: str,
    idea_key: str,
    p_value: float,
    run_count: int,
    verdict: FamilyFdrVerdict,
    created_at: str,
) -> FamilyFdrLedgerRecord:
    """Build a validated record with a deterministic content-addressed record_id."""

    batch_key = family_batch_key(
        alpha_spec_id=alpha_spec_id,
        slice_id=slice_id,
        family_id=family_id,
    )
    payload: dict[str, JsonValue] = {
        "family_id": family_id,
        "slice_id": slice_id,
        "batch_key": batch_key,
        "alpha_spec_id": alpha_spec_id,
        "idea_key": idea_key,
        "p_value": p_value,
        "run_count": run_count,
        "verdict": verdict.to_dict(),
        "created_at": created_at,
    }
    payload["record_id"] = generate_family_fdr_ledger_record_id(payload)
    return validate_family_fdr_ledger_record(payload)


def evaluate_family_fdr(
    *,
    family_id: str,
    slice_id: str,
    alpha_spec_id: str,
    entries: Iterable[Mapping[str, Any] | Any],
    alpha_fw: float = DEFAULT_FDR_ALPHA,
    method: str = DEFAULT_FDR_METHOD,
    created_at: str | None = None,
) -> FamilyFdrEvaluation:
    """Run ``correct_family`` for one co-mined batch and build ledger records.

    Mirrors ``variant_ledger.evaluate_family_budget``: pure evaluation that
    returns the per-idea verdicts plus deterministic ledger records (not yet
    persisted -- ``validate_family_fdr_ledger`` persists when authorized).
    """

    _require_text(family_id, field="family_id")
    _require_text(slice_id, field="slice_id")
    _require_text(alpha_spec_id, field="alpha_spec_id")
    active_created_at = created_at or utc_now_iso()
    _raise_if_issues(_validate_utc_timestamp(active_created_at, field="created_at"))

    materialized = list(entries)
    verdicts = correct_family(materialized, alpha_fw=alpha_fw, method=method)

    parsed_inputs = _parse_entry_inputs(materialized)
    records = tuple(
        create_family_fdr_ledger_record(
            family_id=family_id,
            slice_id=slice_id,
            alpha_spec_id=alpha_spec_id,
            idea_key=verdict.idea_key,
            p_value=parsed_inputs[verdict.idea_key],
            run_count=_run_count_for(materialized, verdict.idea_key),
            verdict=verdict,
            created_at=active_created_at,
        )
        for verdict in verdicts
    )
    batch_key = family_batch_key(
        alpha_spec_id=alpha_spec_id,
        slice_id=slice_id,
        family_id=family_id,
    )
    method_value = verdicts[0].method if verdicts else method
    alpha_value = verdicts[0].alpha_fw if verdicts else alpha_fw
    return FamilyFdrEvaluation(
        family_id=family_id,
        slice_id=slice_id,
        batch_key=batch_key,
        method=method_value,
        alpha_fw=alpha_value,
        family_size=len(verdicts),
        verdicts=verdicts,
        records=records,
    )


def validate_family_fdr_ledger(
    *,
    family_id: str,
    slice_id: str,
    alpha_spec_id: str,
    entries: Iterable[Mapping[str, Any] | Any],
    family_fdr_ledger_path: str | Path | None,
    alpha_fw: float = DEFAULT_FDR_ALPHA,
    method: str = DEFAULT_FDR_METHOD,
    created_at: str | None = None,
    persist: bool = True,
) -> FamilyFdrEvaluation:
    """Fail-closed entry: load ledger -> evaluate batch -> optionally persist.

    Mirrors ``variant_ledger.validate_variant_and_family_budget``. The ledger
    file must exist and be writable (fail-closed); the corrected verdicts are
    computed and, when ``persist`` is True, appended idempotently.
    """

    ledger = FamilyFdrLedger(family_fdr_ledger_path)
    ledger.load_records()
    ledger.require_writable()
    evaluation = evaluate_family_fdr(
        family_id=family_id,
        slice_id=slice_id,
        alpha_spec_id=alpha_spec_id,
        entries=entries,
        alpha_fw=alpha_fw,
        method=method,
        created_at=created_at,
    )
    if persist:
        ledger.append_records(evaluation.records)
    return evaluation


def utc_now_iso() -> str:
    """Return a second-resolution UTC ISO-8601 timestamp ending in Z."""

    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_entry_inputs(entries: list[Mapping[str, Any] | Any]) -> dict[str, float]:
    """Re-derive each idea's effective p_value (mirrors ``correct_family``)."""

    from alpha_system.governance.family_fdr_correction import surrogate_p_upper_bound

    result: dict[str, float] = {}
    for entry in entries:
        get = entry.get if isinstance(entry, Mapping) else (lambda k, e=entry: getattr(e, k, None))
        idea_key = get("idea_key")
        if not isinstance(idea_key, str):
            continue
        p_value = get("p_value")
        if p_value is None:
            gate_pass = get("gate_pass_count")
            run_count = get("run_count")
            if isinstance(gate_pass, int) and isinstance(run_count, int):
                result[idea_key] = surrogate_p_upper_bound(gate_pass, run_count)
        elif isinstance(p_value, int | float) and not isinstance(p_value, bool):
            result[idea_key] = float(p_value)
    return result


def _run_count_for(entries: list[Mapping[str, Any] | Any], idea_key: str) -> int:
    for entry in entries:
        get = entry.get if isinstance(entry, Mapping) else (lambda k, e=entry: getattr(e, k, None))
        if get("idea_key") == idea_key:
            run_count = get("run_count")
            if isinstance(run_count, int):
                return run_count
    return 0


def _parse_verdict(value: Any, issues: list[ValidationIssue]) -> FamilyFdrVerdict | None:
    if not isinstance(value, Mapping):
        issues.append(
            ValidationIssue(
                field="verdict",
                code="invalid_verdict_type",
                message="FamilyFdrLedgerRecord.verdict must be a mapping",
                expected="FamilyFdrVerdict mapping",
                actual=type(value).__name__,
            )
        )
        return None
    try:
        return FamilyFdrVerdict.from_dict(value)
    except (KeyError, TypeError, ValueError) as exc:
        issues.append(
            ValidationIssue(
                field="verdict",
                code="invalid_verdict",
                message="FamilyFdrLedgerRecord.verdict is not a valid FamilyFdrVerdict",
                expected="FamilyFdrVerdict mapping",
                actual=str(exc),
            )
        )
        return None


def _validate_text_value(value: object, *, field: str) -> list[ValidationIssue]:
    if not isinstance(value, str) or _normalize_text(value) in _VAGUE_TEXT:
        return [
            ValidationIssue(
                field=field,
                code="empty_required_field",
                message=f"{field} must be an explicit non-empty string",
                expected="non-empty explicit string",
                actual=str(value),
            )
        ]
    return []


def _validate_p_value(value: object) -> list[ValidationIssue]:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return [
            ValidationIssue(
                field="p_value",
                code="invalid_p_value",
                message="FamilyFdrLedgerRecord.p_value must be a number in [0, 1]",
                expected="float in [0, 1]",
                actual=str(value),
            )
        ]
    p_value = float(value)
    if p_value < 0.0 or p_value > 1.0:
        return [
            ValidationIssue(
                field="p_value",
                code="invalid_p_value",
                message="FamilyFdrLedgerRecord.p_value must be in [0, 1]",
                expected="float in [0, 1]",
                actual=str(value),
            )
        ]
    return []


def _validate_run_count(value: object) -> list[ValidationIssue]:
    if type(value) is not int or value < 0:
        return [
            ValidationIssue(
                field="run_count",
                code="invalid_run_count",
                message="FamilyFdrLedgerRecord.run_count must be a non-negative integer",
                expected="int >= 0",
                actual=str(value),
            )
        ]
    return []


def _validate_utc_timestamp(value: object, *, field: str) -> list[ValidationIssue]:
    if not isinstance(value, str) or not value.endswith("Z"):
        return [
            ValidationIssue(
                field=field,
                code="invalid_utc_timestamp",
                message=f"{field} must be an ISO-8601 UTC timestamp ending in Z",
                expected="YYYY-MM-DDTHH:MM:SSZ",
                actual=str(value),
            )
        ]
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return [
            ValidationIssue(
                field=field,
                code="invalid_utc_timestamp",
                message=f"{field} must be a parseable ISO-8601 UTC timestamp",
                expected="YYYY-MM-DDTHH:MM:SSZ",
                actual=value,
            )
        ]
    if parsed.tzinfo is None or parsed.utcoffset() != datetime.now(UTC).utcoffset():
        return [
            ValidationIssue(
                field=field,
                code="invalid_utc_timestamp",
                message=f"{field} must use UTC timezone",
                expected="UTC timestamp ending in Z",
                actual=value,
            )
        ]
    return []


def _require_text(value: object, *, field: str) -> None:
    issues = _validate_text_value(value, field=field)
    if issues:
        raise GovernanceValidationError(issues)


def _raise_if_issues(issues: list[ValidationIssue]) -> None:
    if issues:
        raise GovernanceValidationError(issues)


def _require_existing_file(path: Path) -> None:
    if not path.exists() or not path.is_file():
        raise GovernanceValidationError(
            ValidationIssue(
                field="family_fdr_ledger_path",
                code="missing_family_fdr_ledger",
                message="FamilyFdrLedger file is required for fail-closed enforcement",
                expected="existing text JSONL ledger file",
                actual=str(path),
            )
        )


def _require_writable_file(path: Path) -> None:
    try:
        mode = path.stat().st_mode
    except OSError as exc:
        raise GovernanceValidationError(
            ValidationIssue(
                field="family_fdr_ledger_path",
                code="unwritable_family_fdr_ledger",
                message="FamilyFdrLedger file permissions could not be inspected",
                expected="writable text JSONL ledger file",
                actual=f"{path}: {exc}",
            )
        ) from exc
    if mode & 0o222 == 0:
        raise GovernanceValidationError(
            ValidationIssue(
                field="family_fdr_ledger_path",
                code="unwritable_family_fdr_ledger",
                message="FamilyFdrLedger file must be writable before enforcement",
                expected="writable text JSONL ledger file",
                actual=str(path),
            )
        )
    try:
        with path.open("a", encoding="utf-8"):
            pass
    except OSError as exc:
        raise GovernanceValidationError(
            ValidationIssue(
                field="family_fdr_ledger_path",
                code="unwritable_family_fdr_ledger",
                message="FamilyFdrLedger file could not be opened for append",
                expected="writable text JSONL ledger file",
                actual=f"{path}: {exc}",
            )
        ) from exc


def _normalize_text(value: object) -> str:
    if isinstance(value, str):
        return " ".join(value.strip().lower().split())
    return str(value).strip().lower()


__all__ = [
    "FAMILY_FDR_LEDGER_RECORD_ID_COMPONENT_FIELDS",
    "FAMILY_FDR_LEDGER_RECORD_ID_PREFIX",
    "FAMILY_FDR_LEDGER_RECORD_REQUIRED_FIELDS",
    "FamilyFdrEvaluation",
    "FamilyFdrLedger",
    "FamilyFdrLedgerRecord",
    "create_family_fdr_ledger_record",
    "evaluate_family_fdr",
    "family_batch_key",
    "generate_family_fdr_ledger_record_id",
    "resolve_family_fdr_ledger_path",
    "utc_now_iso",
    "validate_family_fdr_ledger",
    "validate_family_fdr_ledger_record",
]
