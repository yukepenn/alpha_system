"""DK-P03 no-second-PnL rail: research/ imports no value engine.

The Track A scorer is a pure research probe. It must not import
``backtest`` / ``management`` / ``fast_path`` / ``core.value_store`` (the value
engine), must not open a Parquet, and must not compute a PnL/equity value. The
value loader lives only on the tools/runtime side and injects rows in.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_RESEARCH_DIR = _REPO_ROOT / "src" / "alpha_system" / "research"
_SCORER = _RESEARCH_DIR / "track_a_scorer.py"

_FORBIDDEN_MODULE_RES = (
    re.compile(r"(?:alpha_system\.)?backtest(?:\.|$)"),
    re.compile(r"(?:alpha_system\.)?management(?:\.|$)"),
    re.compile(r"(?:alpha_system\.)?fast_path(?:\.|$)"),
    re.compile(r"(?:alpha_system\.)?core\.value_store(?:\.|$)"),
)


def _imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


def test_track_a_scorer_imports_no_value_engine() -> None:
    modules = _imported_modules(_SCORER)
    for module in modules:
        for pattern in _FORBIDDEN_MODULE_RES:
            assert not pattern.search(module), (
                f"research/track_a_scorer.py must not import the value engine: {module}"
            )


def test_no_research_module_imports_value_engine() -> None:
    offenders: list[str] = []
    for py_file in _RESEARCH_DIR.rglob("*.py"):
        for module in _imported_modules(py_file):
            for pattern in _FORBIDDEN_MODULE_RES:
                if pattern.search(module):
                    offenders.append(f"{py_file.name}:{module}")
    assert not offenders, f"research/ imports a forbidden value engine module: {offenders}"


def test_track_a_scorer_does_not_open_parquet_or_define_pnl() -> None:
    source = _SCORER.read_text(encoding="utf-8")
    # No Parquet/registry IO from the pure scorer.
    assert "read_parquet" not in source
    assert "load_parquet_values" not in source
    assert "open_parquet" not in source
    # No second PnL/value truth defined here.
    assert "def compute_pnl" not in source
    assert "def build_equity_curve" not in source
    assert "realized_pnl" not in source
