from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_portfolio_source_does_not_own_execution_accounting_terms() -> None:
    forbidden = re.compile(r"\b(fill|slippage|commission)\b")
    matches: list[str] = []
    for path in sorted((REPO_ROOT / "src" / "alpha_system" / "portfolio").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        for match in forbidden.finditer(text):
            matches.append(f"{path.relative_to(REPO_ROOT)}:{match.group(0)}")

    assert matches == []
