"""Frontier review schema scaffold."""

from __future__ import annotations

VALID_VERDICTS = ["PASS", "PASS_WITH_WARNINGS", "REWORK", "BLOCKED"]
REQUIRED_REVIEW_SECTIONS = ["Findings", "Questions", "Validation Notes", "Verdict"]
