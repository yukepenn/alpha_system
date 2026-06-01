"""Frontier review verdict schema and conservative parser."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


VALID_VERDICTS = {"PASS", "PASS_WITH_WARNINGS", "REWORK", "BLOCKED"}
PASSING_VERDICTS = {"PASS", "PASS_WITH_WARNINGS"}
VERDICT_RE = re.compile(r"^\s*VERDICT\s*:\s*(PASS_WITH_WARNINGS|PASS|REWORK|BLOCKED)\s*$", re.IGNORECASE | re.MULTILINE)
VALID_DONE_CHECKS = {"PASS", "PASS_WITH_WARNINGS", "REWORK", "BLOCKED"}
DONE_CHECK_RE = re.compile(
    r"^\s*DONE_CHECK\s*:\s*(PASS_WITH_WARNINGS|PASS|REWORK|BLOCKED)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


@dataclass(frozen=True)
class ReviewVerdict:
    verdict: str
    severity: str
    findings: list[str]
    required_repairs: list[str]
    warnings: list[str]
    raw_review_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DoneCheckVerdict:
    verdict: str
    findings: list[str]
    warnings: list[str]
    raw_path: str | None = None

    @property
    def passing(self) -> bool:
        return self.verdict in PASSING_VERDICTS

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _bullet_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith(("- ", "* ")):
            lines.append(stripped[2:].strip())
    return lines


def _severity(verdict: str, text: str) -> str:
    lowered = text.lower()
    if verdict == "BLOCKED":
        return "critical"
    if verdict == "REWORK":
        return "high"
    if "critical" in lowered:
        return "critical"
    if "warning" in lowered or verdict == "PASS_WITH_WARNINGS":
        return "warning"
    return "none"


def _required_repairs(text: str) -> list[str]:
    repairs: list[str] = []
    for line in _bullet_lines(text):
        lowered = line.lower()
        if any(token in lowered for token in ("must", "required", "repair", "fix", "failed", "blocker")):
            repairs.append(line)
    return repairs


def _warnings(text: str) -> list[str]:
    warnings: list[str] = []
    for line in _bullet_lines(text):
        if "warn" in line.lower() or "caution" in line.lower():
            warnings.append(line)
    return warnings


def parse_review_text(text: str, raw_review_path: Path | str | None = None) -> ReviewVerdict:
    matches = [match.group(1).upper() for match in VERDICT_RE.finditer(text)]
    unique = sorted(set(matches))
    if len(unique) != 1:
        return ReviewVerdict(
            verdict="BLOCKED",
            severity="critical",
            findings=["Review verdict was missing or ambiguous."],
            required_repairs=["Produce exactly one VERDICT line."],
            warnings=[],
            raw_review_path=str(raw_review_path) if raw_review_path else None,
        )

    verdict = unique[0]
    bullets = _bullet_lines(text)
    repairs = _required_repairs(text)
    warnings = _warnings(text)
    findings = bullets or ([] if verdict in PASSING_VERDICTS else ["Review did not include detailed findings."])
    if verdict == "PASS_WITH_WARNINGS" and not warnings:
        warnings = ["Review passed with warnings but did not enumerate warning bullets."]
    return ReviewVerdict(
        verdict=verdict,
        severity=_severity(verdict, text),
        findings=findings,
        required_repairs=repairs if verdict in {"REWORK", "BLOCKED"} else [],
        warnings=warnings,
        raw_review_path=str(raw_review_path) if raw_review_path else None,
    )


def parse_done_check_text(text: str, raw_path: Path | str | None = None) -> DoneCheckVerdict:
    matches = [match.group(1).upper() for match in DONE_CHECK_RE.finditer(text)]
    unique = sorted(set(matches))
    if len(unique) != 1:
        return DoneCheckVerdict(
            verdict="BLOCKED",
            findings=["Done-check verdict was missing or ambiguous."],
            warnings=[],
            raw_path=str(raw_path) if raw_path else None,
        )
    verdict = unique[0]
    bullets = _bullet_lines(text)
    warnings = _warnings(text)
    findings = bullets or ([] if verdict in PASSING_VERDICTS else ["Done-check did not include detailed findings."])
    if verdict == "PASS_WITH_WARNINGS" and not warnings:
        warnings = ["Done-check passed with warnings but did not enumerate warning bullets."]
    return DoneCheckVerdict(
        verdict=verdict,
        findings=findings,
        warnings=warnings,
        raw_path=str(raw_path) if raw_path else None,
    )


def load_verdict(path: Path) -> ReviewVerdict:
    data = json.loads(path.read_text(encoding="utf-8"))
    verdict = data.get("verdict")
    if verdict not in VALID_VERDICTS:
        raise ValueError(f"Invalid verdict {verdict!r}. Expected one of {sorted(VALID_VERDICTS)}.")
    return ReviewVerdict(
        verdict=verdict,
        severity=str(data.get("severity", "unknown")),
        findings=list(data.get("findings", [])),
        required_repairs=list(data.get("required_repairs", [])),
        warnings=list(data.get("warnings", [])),
        raw_review_path=data.get("raw_review_path"),
    )


def validate(path: Path) -> int:
    try:
        verdict = load_verdict(path)
    except (json.JSONDecodeError, ValueError) as error:
        print(str(error))
        return 1
    print(f"Verdict {verdict.verdict} is valid.")
    return 0


def parse_to_file(review_path: Path, output_path: Path) -> int:
    parsed = parse_review_text(review_path.read_text(encoding="utf-8"), review_path)
    output_path.write_text(json.dumps(parsed.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Parsed {parsed.verdict} into {output_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate or parse Frontier review verdict JSON.")
    parser.add_argument("path", type=Path, nargs="?")
    parser.add_argument("--parse-review", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.parse_review:
        output = args.output or args.parse_review.with_name("verdict.json")
        return parse_to_file(args.parse_review, output)
    if not args.path:
        parser.print_help()
        return 0
    return validate(args.path)


if __name__ == "__main__":
    raise SystemExit(main())
