"""Structured, value-free Agent Factory tool results."""

from __future__ import annotations

from dataclasses import dataclass, fields
from enum import StrEnum
from typing import Any

MAX_RESULT_TEXT_LENGTH = 1024
MAX_SUMMARY_TEXT_LENGTH = 2048

FORBIDDEN_RESULT_MARKERS: tuple[str, ...] = (
    "raw_payload",
    "provider_payload",
    "provider bytes",
    "db_rows",
    "embedded_file_contents",
    "file_contents",
    "raw bars",
    "raw_bar",
    "raw quotes",
    "raw_quote",
    "raw ticks",
    "raw_tick",
    "raw market",
    "bar records",
    "quote records",
    "tick records",
    "dataframe",
    "data_frame",
    "pandas",
    "polars",
    "pyarrow",
    "ndarray",
    "numpy",
    "array(",
    "base64",
    "data/raw/",
    "data/canonical/",
    "data/factors/",
    "data/labels/",
    "data/cache/",
    "metadata/",
)
FORBIDDEN_HEAVY_SUFFIXES: tuple[str, ...] = (
    ".parquet",
    ".arrow",
    ".feather",
    ".dbn",
    ".zst",
    ".sqlite",
    ".sqlite3",
    ".db",
    ".wal",
    ".npy",
    ".npz",
    ".pkl",
    ".joblib",
    ".onnx",
    ".log",
)
RAW_OBJECT_MODULE_PREFIXES: frozenset[str] = frozenset({"numpy", "pandas", "polars", "pyarrow"})


class AgentToolStatus(StrEnum):
    """Enumerated status values every agent-facing tool result must use."""

    OK = "OK"
    BLOCKED = "BLOCKED"
    REJECTED = "REJECTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    WARN = "WARN"


@dataclass(frozen=True, slots=True)
class AgentToolResult:
    """Single structured result envelope for all Agent Factory tools.

    The fields are intentionally narrow. They carry ids, refs, short summaries,
    rejection/blocking notes, artifact refs, and the next gate only.
    """

    status: AgentToolStatus
    role: str
    request_id: str
    alpha_spec_id: str | None
    study_spec_id: str | None
    dataset_version_id: str | None
    feature_pack_refs: tuple[str, ...]
    label_pack_refs: tuple[str, ...]
    runtime_run_id: str | None
    diagnostics_summary: str | None
    cost_summary: str | None
    rejection_reasons: tuple[str, ...]
    blocking_findings: tuple[str, ...]
    next_required_gate: str
    artifacts: tuple[str, ...]
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", _coerce_status(self.status))
        _validate_text("role", self.role)
        _validate_text("request_id", self.request_id)
        _validate_optional_text("alpha_spec_id", self.alpha_spec_id)
        _validate_optional_text("study_spec_id", self.study_spec_id)
        _validate_optional_text("dataset_version_id", self.dataset_version_id)
        _validate_text_tuple("feature_pack_refs", self.feature_pack_refs)
        _validate_text_tuple("label_pack_refs", self.label_pack_refs)
        _validate_optional_text("runtime_run_id", self.runtime_run_id)
        _validate_optional_text(
            "diagnostics_summary",
            self.diagnostics_summary,
            max_length=MAX_SUMMARY_TEXT_LENGTH,
        )
        _validate_optional_text(
            "cost_summary",
            self.cost_summary,
            max_length=MAX_SUMMARY_TEXT_LENGTH,
        )
        _validate_text_tuple("rejection_reasons", self.rejection_reasons)
        _validate_text_tuple("blocking_findings", self.blocking_findings)
        _validate_text("next_required_gate", self.next_required_gate)
        _validate_text_tuple("artifacts", self.artifacts)
        _validate_text_tuple("limitations", self.limitations)


AGENT_TOOL_RESULT_FIELDS: tuple[str, ...] = tuple(field.name for field in fields(AgentToolResult))


def _coerce_status(value: object) -> AgentToolStatus:
    _reject_raw_object("status", value)
    if isinstance(value, AgentToolStatus):
        return value
    if isinstance(value, str):
        _validate_text("status", value)
        try:
            return AgentToolStatus(value)
        except ValueError as error:
            raise ValueError(f"unknown AgentToolStatus: {value}") from error
    raise TypeError("status must be an AgentToolStatus")


def _validate_optional_text(
    field_name: str,
    value: object,
    *,
    max_length: int = MAX_RESULT_TEXT_LENGTH,
) -> None:
    _reject_raw_object(field_name, value)
    if value is None:
        return
    _validate_text(field_name, value, max_length=max_length)


def _validate_text(
    field_name: str,
    value: object,
    *,
    max_length: int = MAX_RESULT_TEXT_LENGTH,
) -> None:
    _reject_raw_object(field_name, value)
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a str")
    if value != value.strip() or not value:
        raise ValueError(f"{field_name} must be non-empty without surrounding whitespace")
    if len(value) > max_length:
        raise ValueError(f"{field_name} exceeds structured result text length")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{field_name} must be a single-line structured string")
    _reject_raw_or_heavy_text(field_name, value)


def _validate_text_tuple(field_name: str, value: object) -> None:
    _reject_raw_object(field_name, value)
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple[str, ...]")
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must not contain duplicates")
    for item in value:
        _validate_text(field_name, item)


def _reject_raw_or_heavy_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(marker in lowered for marker in FORBIDDEN_RESULT_MARKERS):
        raise ValueError(f"{field_name} contains a forbidden raw/heavy payload marker")
    if any(suffix in lowered for suffix in FORBIDDEN_HEAVY_SUFFIXES):
        raise ValueError(f"{field_name} contains a forbidden heavy artifact reference")


def _reject_raw_object(field_name: str, value: Any) -> None:
    if isinstance(value, (bytes, bytearray, memoryview)):
        raise TypeError(f"{field_name} must not contain bytes")
    module_root = type(value).__module__.split(".", 1)[0]
    if module_root in RAW_OBJECT_MODULE_PREFIXES:
        raise TypeError(f"{field_name} must not contain dataframe or array objects")
