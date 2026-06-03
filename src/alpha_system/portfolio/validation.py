"""Portfolio config validation and artifact-safe summaries."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from alpha_system.data.fixture_policy import repository_root_from_module
from alpha_system.data.paths import assert_local_wsl_path
from alpha_system.portfolio.spec import PortfolioSpec, PortfolioSpecError


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


class PortfolioValidationError(ValueError):
    """Raised when portfolio validation fails."""


@dataclass(frozen=True, slots=True)
class PortfolioValidationResult:
    valid: bool
    portfolio_id: str
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "portfolio_id": self.portfolio_id,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "portfolio_scope": "target_sizing_and_exposure_constraints",
        }


def load_portfolio_config(path: str | Path) -> Mapping[str, Any]:
    config_path = Path(path).expanduser().resolve(strict=False)
    text = config_path.read_text(encoding="utf-8")
    if config_path.suffix.lower() == ".json":
        payload = json.loads(text)
    else:
        payload = _parse_simple_yaml(text)
    if not isinstance(payload, Mapping):
        raise PortfolioValidationError("portfolio config root must be a mapping")
    return payload


def validate_portfolio_config(payload: Mapping[str, Any]) -> PortfolioValidationResult:
    try:
        spec = PortfolioSpec.from_mapping(payload)
    except (PortfolioSpecError, PortfolioValidationError) as exc:
        return PortfolioValidationResult(
            valid=False,
            portfolio_id=str(payload.get("portfolio_id", "portfolio:invalid")),
            errors=(str(exc),),
        )
    return PortfolioValidationResult(
        valid=True,
        portfolio_id=spec.portfolio_id,
        warnings=(
            "sector and asset constraints are contract-only",
            "correlation-aware allocation is contract-only",
        ),
    )


def write_validation_summary(path: str | Path, result: PortfolioValidationResult) -> Path:
    candidate = assert_local_wsl_path(path)
    if candidate.suffix.lower() != ".json" or candidate.suffix.lower() in FORBIDDEN_SUMMARY_SUFFIXES:
        raise PortfolioValidationError("portfolio validation summary must be a JSON file")
    repo_root = repository_root_from_module()
    if _is_relative_to(candidate, repo_root):
        raise PortfolioValidationError("portfolio validation summaries must be temp/local paths outside the repo")
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(json.dumps(result.to_dict(), sort_keys=True, indent=2), encoding="utf-8")
    return candidate


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if ":" not in stripped:
            raise PortfolioValidationError(f"unsupported YAML line: {raw_line!r}")
        key, value = stripped.split(":", 1)
        key = key.strip()
        if not key:
            raise PortfolioValidationError(f"empty YAML key in line: {raw_line!r}")
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


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
