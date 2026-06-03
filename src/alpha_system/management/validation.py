"""Management config loading, validation, and artifact-safe summaries."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from alpha_system.data.fixture_policy import repository_root_from_module
from alpha_system.data.paths import assert_local_wsl_path
from alpha_system.management.spec import ManagementSpec, ManagementSpecError


MAX_GRID_PARAMETERS = 16
MAX_GRID_VALUES_PER_PARAMETER = 20
MAX_GRID_COMBINATIONS = 500
FORBIDDEN_SUMMARY_SUFFIXES = (
    ".parquet",
    ".arrow",
    ".feather",
    ".sqlite",
    ".sqlite3",
    ".db",
    ".db-journal",
    ".wal",
    ".log",
)


class ManagementValidationError(ValueError):
    """Raised when management config validation fails."""


@dataclass(frozen=True, slots=True)
class ManagementValidationResult:
    valid: bool
    management_id: str
    bounded_grid: bool
    grid_combinations: int
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "management_id": self.management_id,
            "bounded_grid": self.bounded_grid,
            "grid_combinations": self.grid_combinations,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "execution_deferred_to": "ASV1-P21",
        }


def load_management_config(path: str | Path) -> Mapping[str, Any]:
    """Load a JSON or small YAML management config."""
    config_path = Path(path).expanduser().resolve(strict=False)
    text = config_path.read_text(encoding="utf-8")
    if config_path.suffix.lower() == ".json":
        payload = json.loads(text)
    else:
        payload = _parse_simple_yaml(text)
    if not isinstance(payload, Mapping):
        raise ManagementValidationError("management config root must be a mapping")
    return payload


def validate_management_config(payload: Mapping[str, Any]) -> ManagementValidationResult:
    """Validate management config and bounded grid metadata."""
    try:
        spec_payload = payload.get("management", payload)
        spec = ManagementSpec.from_mapping(spec_payload)
        bounded, combinations = validate_management_grid_definition(payload.get("management_grid"))
    except (ManagementSpecError, ManagementValidationError) as exc:
        return ManagementValidationResult(
            valid=False,
            management_id=str(payload.get("management_id", "management:invalid")),
            bounded_grid=False,
            grid_combinations=0,
            errors=(str(exc),),
        )
    return ManagementValidationResult(
        valid=True,
        management_id=spec.management_id,
        bounded_grid=bounded,
        grid_combinations=combinations,
        warnings=("management grid execution is deferred to ASV1-P21",),
    )


def validate_management_grid_definition(value: Any) -> tuple[bool, int]:
    """Validate that a management grid declaration is finite and bounded."""
    if value in (None, False):
        return True, 1
    grid = _mapping(value, "management_grid")
    parameters = grid.get("parameters", {})
    parameters = _mapping(parameters, "management_grid.parameters")
    if len(parameters) > MAX_GRID_PARAMETERS:
        raise ManagementValidationError("management_grid has too many parameters")
    combinations = 1
    for name, values in parameters.items():
        active_values = _bounded_values(values, str(name))
        combinations *= len(active_values)
        if combinations > MAX_GRID_COMBINATIONS:
            raise ManagementValidationError("management_grid exceeds bounded combination limit")
    return True, combinations


def write_validation_summary(path: str | Path, result: ManagementValidationResult) -> Path:
    """Write a tiny validation summary to an explicit local-only temp path."""
    candidate = assert_local_wsl_path(path)
    if candidate.suffix.lower() != ".json" or candidate.suffix.lower() in FORBIDDEN_SUMMARY_SUFFIXES:
        raise ManagementValidationError("management validation summary must be a JSON file")
    repo_root = repository_root_from_module()
    if _is_relative_to(candidate, repo_root):
        raise ManagementValidationError("management validation summaries must be temp/local paths outside the repo")
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(json.dumps(result.to_dict(), sort_keys=True, indent=2), encoding="utf-8")
    return candidate


def _bounded_values(value: Any, name: str) -> tuple[Any, ...]:
    if value in (None, "", "*"):
        raise ManagementValidationError(f"management_grid parameter {name} is unbounded")
    if isinstance(value, Mapping):
        if "values" not in value:
            raise ManagementValidationError(f"management_grid parameter {name} must use explicit values")
        value = value["values"]
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        values = tuple(value)
    else:
        raise ManagementValidationError(f"management_grid parameter {name} must be an explicit value list")
    if not values:
        raise ManagementValidationError(f"management_grid parameter {name} has no values")
    if len(values) > MAX_GRID_VALUES_PER_PARAMETER:
        raise ManagementValidationError(f"management_grid parameter {name} has too many values")
    if any(item in (None, "", "*") for item in values):
        raise ManagementValidationError(f"management_grid parameter {name} contains an unbounded value")
    return values


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    """Parse the small mapping-only YAML subset used by repo examples."""
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if ":" not in stripped:
            raise ManagementValidationError(f"unsupported YAML line: {raw_line!r}")
        key, value = stripped.split(":", 1)
        key = key.strip()
        if not key:
            raise ManagementValidationError(f"empty YAML key in line: {raw_line!r}")
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        value = value.strip()
        if value == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _yaml_scalar(value)
    return root


def _yaml_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none"}:
        return None
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def _mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ManagementValidationError(f"{field_name} must be a mapping")
    return value


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
