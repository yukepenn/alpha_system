"""Lock the single-PnL-truth invariant.

The reference backtest engine is the only authoritative PnL/value accounting. The
fast backtest path is permitted ONLY because it is parity-gated against the
reference. This test fails if that parity harness or its tests are removed, which
is how a "second PnL truth" would silently slip in. (A grep guard is deliberately
not used: PnL is legitimately *consumed* across many modules, so pattern-matching
would false-positive; the real guarantee is reference<->fast parity.)
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "alpha_system" / "backtest"
PARITY_TESTS = ROOT / "tests" / "parity"


def test_reference_and_fast_path_modules_exist() -> None:
    assert (SRC / "reference.py").exists(), "reference engine (PnL truth) must exist"
    assert (SRC / "fast_path.py").exists(), "fast path must exist"
    assert (SRC / "parity.py").exists(), "fast<->reference parity module must exist"


def test_parity_module_binds_reference_to_fast_path() -> None:
    text = (SRC / "parity.py").read_text(encoding="utf-8")
    assert "run_reference_backtest" in text, "parity must invoke the reference engine"
    assert "run_fast_path_backtest" in text, "parity must invoke the fast path"


def test_parity_tests_present_and_cover_equity_and_fail_closed() -> None:
    assert PARITY_TESTS.is_dir(), "tests/parity/ must exist"
    names = {p.name for p in PARITY_TESTS.glob("test_*parity*.py")}
    assert any("equity" in n for n in names), "equity-curve parity test must exist"
    # An unsupported fast feature must fail closed (fall back to reference, never
    # silently diverge) - this is the guardrail against a second accounting truth.
    assert (PARITY_TESTS / "test_unsupported_fast_feature_fail_closed.py").exists()
    assert len(names) >= 5, f"expected a parity suite, found only {sorted(names)}"
