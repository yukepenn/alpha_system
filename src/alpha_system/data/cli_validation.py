"""Thin data CLI adapters around canonical validation/session primitives."""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from alpha_system.core.hashing import canonical_json
from alpha_system.core.registry import connect_registry, init_registry
from alpha_system.data.bar_schema import canonical_bar_columns
from alpha_system.data.build_bars import load_csv_bar_fixture
from alpha_system.data.calendar import load_calendar_config
from alpha_system.data.fixture_policy import (
    FixturePolicyError,
    assert_build_input_allowed,
    assert_generated_output_allowed,
    assert_registry_path_allowed,
    repository_root_from_module,
)
from alpha_system.data.quality import evaluate_data_quality, normalize_quality_flags
from alpha_system.data.sessionize import sessionize_bars
from alpha_system.data.storage import DataDependencyError, write_parquet_bars
from alpha_system.data.validation import (
    BarValidationConfig,
    ValidationResult,
    validate_bars,
)
from alpha_system.data.versions import (
    DatasetVersion,
    config_hash_for_mapping,
    content_hash_for_rows,
    make_dataset_version,
    make_source_version,
    record_dataset_version,
)


VALIDATION_FAILURE_EXIT_CODE = 1
CONFIG_ERROR_EXIT_CODE = 2
DEFAULT_SCHEMA_ID = "canonical_1min_bars_v1"


class DataCliError(RuntimeError):
    """Raised for deterministic CLI configuration or artifact-policy errors."""


@dataclass(frozen=True, slots=True)
class DataCliSummary:
    command: str
    input_path: str
    schema_id: str
    row_count: int
    valid: bool
    validation_issue_counts: Mapping[str, int]
    quality_flag_counts: Mapping[str, int]
    quality_issue_counts: Mapping[str, int]
    calendar_id: str | None = None
    output_path: str | None = None
    manifest_path: str | None = None
    validation_summary_path: str | None = None
    registry_path: str | None = None
    data_version: str | None = None
    messages: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "calendar_id": self.calendar_id,
            "command": self.command,
            "data_version": self.data_version,
            "input_path": self.input_path,
            "manifest_path": self.manifest_path,
            "messages": list(self.messages),
            "output_path": self.output_path,
            "quality_flag_counts": dict(self.quality_flag_counts),
            "quality_issue_counts": dict(self.quality_issue_counts),
            "registry_path": self.registry_path,
            "row_count": self.row_count,
            "schema_id": self.schema_id,
            "valid": self.valid,
            "validation_issue_counts": dict(self.validation_issue_counts),
            "validation_summary_path": self.validation_summary_path,
        }


def run_validate_command(
    *,
    config_path: str | Path,
    input_path: str | Path,
    schema_id: str,
    calendar_id: str | None = None,
    registry_path: str | Path | None = None,
    summary_out: str | Path | None = None,
) -> DataCliSummary:
    """Validate canonical bars and optional session quality via P06/P07 helpers."""
    config = load_cli_config(config_path)
    validation_config = validation_config_from_mapping(config)
    calendar_path = _optional_path(config.get("calendar_config"))
    rows = _load_csv_rows(input_path, validation_config=validation_config)
    active_rows: tuple[dict[str, Any], ...] = tuple(dict(row) for row in rows)
    quality_issue_counts: Counter[str] = Counter()
    messages: list[str] = []
    active_calendar_id: str | None = None

    if calendar_path is not None:
        calendar = load_calendar_config(calendar_path)
        if calendar_id is not None and calendar.calendar_id != calendar_id:
            msg = (
                f"calendar-id {calendar_id!r} does not match "
                f"calendar config {calendar.calendar_id!r}"
            )
            raise DataCliError(msg)
        active_calendar_id = calendar.calendar_id
        try:
            active_rows = sessionize_bars(
                active_rows,
                calendar,
                available_latency=validation_config.available_latency,
                validate_existing_keys=True,
            )
        except ValueError as exc:
            active_rows = tuple(dict(row) for row in rows)
            messages.append(str(exc))
            quality_issue_counts["session_key_mismatch"] += 1
        else:
            quality_report = evaluate_data_quality(
                active_rows,
                calendar,
                latency=validation_config.available_latency,
            )
            active_rows = quality_report.rows
            quality_issue_counts.update(issue.flag for issue in quality_report.issues)
            messages.extend(issue.message for issue in quality_report.issues)

    validation = validate_bars(active_rows, config=validation_config)
    issue_counts = _validation_issue_counts(validation)
    messages.extend(validation.messages())
    valid = validation.valid and not quality_issue_counts

    summary = DataCliSummary(
        command="validate",
        input_path=Path(input_path).as_posix(),
        schema_id=schema_id,
        row_count=len(active_rows),
        valid=valid,
        validation_issue_counts=issue_counts,
        quality_flag_counts=_quality_flag_counts(active_rows),
        quality_issue_counts=dict(quality_issue_counts),
        calendar_id=active_calendar_id,
        messages=tuple(messages),
    )
    summary = _write_summary_if_requested(summary, summary_out)
    if registry_path is not None and summary.valid:
        summary = _record_registry(summary, active_rows, config, registry_path)
    return summary


def run_build_bars_command(
    *,
    input_path: str | Path,
    instrument_config_path: str | Path,
    calendar_config_path: str | Path,
    output_path: str | Path,
    data_version: str,
    registry_path: str | Path | None = None,
    validation_config_path: str | Path | None = None,
) -> DataCliSummary:
    """Build fixture-scale canonical bars and validate the local-only output."""
    repo_root = repository_root_from_module()
    validation_mapping = (
        load_cli_config(validation_config_path)
        if validation_config_path is not None
        else {}
    )
    instrument_mapping = load_cli_config(instrument_config_path)
    validation_config = validation_config_from_mapping(validation_mapping)
    allow_non_fixture = bool(
        validation_mapping.get("allow_non_fixture_input", False)
        or instrument_mapping.get("allow_non_fixture_input", False)
    )
    allowed_input = assert_build_input_allowed(
        input_path,
        repo_root=repo_root,
        allow_non_fixture_input=allow_non_fixture,
    )
    output = assert_generated_output_allowed(
        output_path,
        repo_root=repo_root,
        require_data_dir=True,
    )
    calendar = load_calendar_config(calendar_config_path)
    rows = _load_csv_rows(allowed_input, validation_config=validation_config)
    rows = tuple(dict(row, data_version=data_version) for row in rows)
    sessionized = sessionize_bars(
        rows,
        calendar,
        available_latency=validation_config.available_latency,
        validate_existing_keys=False,
    )
    quality_report = evaluate_data_quality(
        sessionized,
        calendar,
        latency=validation_config.available_latency,
    )
    validation = validate_bars(quality_report.rows, config=validation_config)
    quality_issue_counts = Counter(issue.flag for issue in quality_report.issues)
    valid = validation.valid and not quality_issue_counts
    if not valid:
        messages = list(quality_report.messages())
        messages.extend(validation.messages())
        return DataCliSummary(
            command="build-bars",
            input_path=allowed_input.as_posix(),
            schema_id=DEFAULT_SCHEMA_ID,
            row_count=len(quality_report.rows),
            valid=False,
            validation_issue_counts=_validation_issue_counts(validation),
            quality_flag_counts=_quality_flag_counts(quality_report.rows),
            quality_issue_counts=dict(quality_issue_counts),
            calendar_id=calendar.calendar_id,
            output_path=output.as_posix(),
            data_version=data_version,
            messages=tuple(messages),
        )

    written = _write_bars_output(quality_report.rows, output, validation_config)
    manifest_path = _write_manifest(
        written,
        command="build-bars",
        input_path=allowed_input,
        calendar_id=calendar.calendar_id,
        data_version=data_version,
        row_count=len(quality_report.rows),
        output_format=_output_format(written),
    )
    summary_path = written.with_suffix(written.suffix + ".validation_summary.json")
    summary = DataCliSummary(
        command="build-bars",
        input_path=allowed_input.as_posix(),
        schema_id=DEFAULT_SCHEMA_ID,
        row_count=len(quality_report.rows),
        valid=True,
        validation_issue_counts={},
        quality_flag_counts=_quality_flag_counts(quality_report.rows),
        quality_issue_counts={},
        calendar_id=calendar.calendar_id,
        output_path=written.as_posix(),
        manifest_path=manifest_path.as_posix(),
        validation_summary_path=summary_path.as_posix(),
        data_version=data_version,
    )
    summary_path.write_text(
        json.dumps(summary.to_dict(), sort_keys=True, indent=2),
        encoding="utf-8",
    )
    if registry_path is not None:
        summary = _record_registry(summary, quality_report.rows, validation_mapping, registry_path)
    return summary


def load_cli_config(path: str | Path | None) -> dict[str, Any]:
    """Load a tiny flat JSON/YAML mapping without adding external dependencies."""
    if path is None:
        return {}
    config_path = Path(path)
    if not config_path.exists():
        msg = f"config file does not exist: {config_path.as_posix()}"
        raise DataCliError(msg)
    if config_path.suffix.lower() == ".json":
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            msg = f"config root must be a mapping: {config_path.as_posix()}"
            raise DataCliError(msg)
        return dict(payload)
    return _load_flat_yaml(config_path)


def validation_config_from_mapping(config: Mapping[str, Any]) -> BarValidationConfig:
    """Build the P06 validation config from a CLI config mapping."""
    latency = config.get("available_latency_seconds", config.get("latency_seconds", 0))
    spread_tolerance = config.get("spread_tolerance", "0.000001")
    require_event = config.get("require_event_within_bar", True)
    return BarValidationConfig(
        available_latency=timedelta(seconds=float(latency)),
        spread_tolerance=Decimal(str(spread_tolerance)),
        require_event_within_bar=bool(require_event),
    )


def print_summary(summary: DataCliSummary, *, emit_json: bool = False) -> None:
    """Emit a stable console summary."""
    payload = summary.to_dict()
    if emit_json:
        print(json.dumps(payload, sort_keys=True, indent=2))
        return
    print(f"Data command: {summary.command}")
    print(f"Input: {summary.input_path}")
    print(f"Schema: {summary.schema_id}")
    if summary.calendar_id is not None:
        print(f"Calendar: {summary.calendar_id}")
    print(f"Rows: {summary.row_count}")
    print(f"Status: {'OK' if summary.valid else 'INVALID'}")
    if summary.output_path is not None:
        print(f"Output: {summary.output_path}")
    if summary.manifest_path is not None:
        print(f"Manifest: {summary.manifest_path}")
    if summary.registry_path is not None:
        print(f"Registry: {summary.registry_path}")
    if summary.validation_issue_counts:
        print(f"Validation issues: {dict(summary.validation_issue_counts)}")
    if summary.quality_issue_counts:
        print(f"Quality issues: {dict(summary.quality_issue_counts)}")
    if summary.quality_flag_counts:
        print(f"Quality flags: {dict(summary.quality_flag_counts)}")
    for message in summary.messages[:10]:
        print(f"- {message}")


def run_cli_with_error_handling(callback: Any, *, emit_json: bool = False) -> int:
    """Run a data CLI callback and convert errors into established exit codes."""
    try:
        summary = callback()
    except (DataCliError, FixturePolicyError, OSError, DataDependencyError) as exc:
        print(f"data command error: {exc}", file=sys.stderr)
        return CONFIG_ERROR_EXIT_CODE
    print_summary(summary, emit_json=emit_json)
    return 0 if summary.valid else VALIDATION_FAILURE_EXIT_CODE


def _load_csv_rows(
    input_path: str | Path,
    *,
    validation_config: BarValidationConfig,
) -> tuple[dict[str, Any], ...]:
    path = Path(input_path)
    if path.suffix.lower() != ".csv":
        msg = f"only CSV fixture-scale inputs are supported by this CLI phase: {path}"
        raise DataCliError(msg)
    try:
        return load_csv_bar_fixture(
            path,
            validation_config=validation_config,
            validate=False,
        )
    except (TypeError, ValueError) as exc:
        msg = f"input could not be normalized as canonical bars: {exc}"
        raise DataCliError(msg) from exc


def _validation_issue_counts(result: ValidationResult) -> dict[str, int]:
    counts: Counter[str] = Counter(issue.code for issue in result.issues)
    return dict(counts)


def _quality_flag_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(normalize_quality_flags(row.get("quality_flags")))
    return dict(counts)


def _write_summary_if_requested(
    summary: DataCliSummary,
    summary_out: str | Path | None,
) -> DataCliSummary:
    if summary_out is None:
        return summary
    output = assert_generated_output_allowed(summary_out)
    updated = replace(summary, validation_summary_path=output.as_posix())
    payload = updated.to_dict()
    output.parent.mkdir(parents=True, exist_ok=True)
    suffix = output.suffix.lower()
    if suffix == ".json":
        output.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
    elif suffix in {".md", ".markdown"}:
        output.write_text(_summary_markdown(updated), encoding="utf-8")
    elif suffix == ".csv":
        _write_summary_csv(updated, output)
    else:
        msg = "summary-out must end in .json, .md, or .csv"
        raise DataCliError(msg)
    return updated


def _record_registry(
    summary: DataCliSummary,
    rows: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
    registry_path: str | Path,
) -> DataCliSummary:
    registry = assert_registry_path_allowed(registry_path)
    status = init_registry(registry)
    if not status.valid:
        msg = f"registry is not valid: {status.status_message}"
        raise DataCliError(msg)
    content_hash = content_hash_for_rows(tuple(_json_safe_row(row) for row in rows))
    source = make_source_version(
        "synthetic",
        "fixture",
        content_hash=content_hash,
        metadata={"command": summary.command, "schema_id": summary.schema_id},
    )
    config_hash = config_hash_for_mapping(dict(config))
    if summary.data_version is None:
        record = make_dataset_version(
            "data_cli_validation",
            content_hash=content_hash,
            config_hash=config_hash,
            source_version=source.source_version,
            source_uri=summary.input_path,
            metadata={"command": summary.command, "schema_id": summary.schema_id},
            status_message="data CLI validation summary",
        )
    else:
        record = DatasetVersion(
            data_version=summary.data_version,
            dataset_name=summary.command,
            created_at=source.created_at,
            source_uri=summary.input_path,
            content_hash=content_hash,
            config_hash=config_hash,
            metadata={
                "command": summary.command,
                "schema_id": summary.schema_id,
                "source_version": source.source_version,
            },
            status_message="data CLI validation summary",
        )
    with connect_registry(registry) as connection:
        record_dataset_version(connection, record)
    return replace(
        summary,
        registry_path=registry.as_posix(),
        data_version=record.data_version,
    )


def _write_bars_output(
    rows: Sequence[Mapping[str, Any]],
    output_path: Path,
    validation_config: BarValidationConfig,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix.lower() == ".parquet":
        return write_parquet_bars(rows, output_path, validation_config=validation_config)
    if output_path.suffix.lower() == ".csv":
        _write_csv_bars(rows, output_path)
        return output_path
    msg = "build-bars output must end in .parquet or .csv"
    raise DataCliError(msg)


def _write_csv_bars(rows: Sequence[Mapping[str, Any]], output_path: Path) -> None:
    columns = canonical_bar_columns()
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: _csv_scalar(row.get(column)) for column in columns})


def _write_manifest(
    output_path: Path,
    *,
    command: str,
    input_path: Path,
    calendar_id: str,
    data_version: str,
    row_count: int,
    output_format: str,
) -> Path:
    manifest_path = output_path.with_suffix(output_path.suffix + ".manifest.json")
    payload = {
        "calendar_id": calendar_id,
        "command": command,
        "data_version": data_version,
        "input_path": input_path.as_posix(),
        "local_only": True,
        "output_format": output_format,
        "output_path": output_path.as_posix(),
        "row_count": row_count,
        "schema_id": DEFAULT_SCHEMA_ID,
    }
    manifest_path.write_text(
        json.dumps(payload, sort_keys=True, indent=2),
        encoding="utf-8",
    )
    return manifest_path


def _output_format(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")
    return suffix or "unknown"


def _summary_markdown(summary: DataCliSummary) -> str:
    lines = [
        f"# Data CLI {summary.command} Summary",
        "",
        f"- Input: `{summary.input_path}`",
        f"- Schema: `{summary.schema_id}`",
        f"- Rows: `{summary.row_count}`",
        f"- Status: `{'OK' if summary.valid else 'INVALID'}`",
    ]
    if summary.validation_issue_counts:
        lines.append(f"- Validation issues: `{dict(summary.validation_issue_counts)}`")
    if summary.quality_issue_counts:
        lines.append(f"- Quality issues: `{dict(summary.quality_issue_counts)}`")
    return "\n".join(lines) + "\n"


def _write_summary_csv(summary: DataCliSummary, output: Path) -> None:
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("key", "value"))
        writer.writeheader()
        for key, value in summary.to_dict().items():
            writer.writerow({"key": key, "value": json.dumps(value, sort_keys=True)})


def _load_flat_yaml(path: Path) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if ":" not in line:
            msg = f"unsupported config line in {path.as_posix()}: {raw_line!r}"
            raise DataCliError(msg)
        key, raw_value = line.split(":", 1)
        payload[key.strip()] = _parse_scalar(raw_value.strip())
    return payload


def _parse_scalar(value: str) -> Any:
    if value in {"", "null", "None"}:
        return None
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value.startswith(("'", '"')) and value.endswith(("'", '"')):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def _optional_path(value: Any) -> Path | None:
    if value in (None, ""):
        return None
    return Path(str(value))


def _json_safe_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): _json_safe_value(value) for key, value in row.items()}


def _json_safe_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, tuple):
        return [_json_safe_value(item) for item in value]
    if isinstance(value, list):
        return [_json_safe_value(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _json_safe_value(item) for key, item in value.items()}
    try:
        canonical_json(value)
    except TypeError:
        return str(value)
    return value


def _csv_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, tuple):
        return "|".join(str(item) for item in value)
    if hasattr(value, "isoformat"):
        text = value.isoformat()
        return text.replace("+00:00", "Z")
    return str(value)
