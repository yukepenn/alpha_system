"""Anti-rot guard for the canonical operating compass.

Enforces the single-canonical-compass invariant so future agents never face a
"which compass is the truth (V4 / V5 / V6)?" question, and so live-status rot
cannot creep back into the canonical strategy doc. See `docs/OPERATING_COMPASS.md`
§0 (AUTHORITY) — this guard is the machine enforcement referenced there.

Checks:
  1. The canonical compass exists at the FIXED name (no version in the filename).
  2. NO versioned `docs/OPERATING_COMPASS_V*.md` files exist (single canonical).
  3. `AGENTS.md`, `README.md`, `CRITICAL.md` point to the fixed name and not the
     retired versioned name.
  4. The compass defers live status to `status_doctor` and contains no hardcoded
     live-status rot (a phase id, a "merged N/M" count, or a survivor count
     stated as current).
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS = REPO_ROOT / "docs"
COMPASS = DOCS / "OPERATING_COMPASS.md"


def test_canonical_compass_exists_at_fixed_name() -> None:
    assert COMPASS.is_file(), (
        "docs/OPERATING_COMPASS.md (fixed name) must exist — it is the single "
        "canonical strategy/roadmap source of truth (see its §0)."
    )


def test_no_versioned_compass_duplicates() -> None:
    versioned = sorted(p.name for p in DOCS.glob("OPERATING_COMPASS_V*.md"))
    assert not versioned, (
        "Single-canonical invariant: no versioned compass copies allowed; found "
        f"{versioned}. Bump the internal `Version:` line, never the filename."
    )


def test_active_pointers_point_to_fixed_name() -> None:
    for name in ("AGENTS.md", "README.md", "CRITICAL.md"):
        text = (REPO_ROOT / name).read_text(encoding="utf-8")
        assert "docs/OPERATING_COMPASS.md" in text, (
            f"{name} must reference the fixed-name canonical compass "
            "docs/OPERATING_COMPASS.md."
        )
        assert "OPERATING_COMPASS_V4.md" not in text, (
            f"{name} must not reference the retired versioned compass file."
        )


def test_compass_defers_live_status_to_status_doctor() -> None:
    body = COMPASS.read_text(encoding="utf-8")
    assert "status_doctor" in body, (
        "The compass must point readers to `status_doctor` for live run/phase "
        "status (it must never state live status itself)."
    )


# Live-status rot patterns. Deliberately narrow so the survivor-gate LADDER rules
# ("0 survivors (all clean REJECT)", "1 survivor -> ...") — which are timeless
# rules, not a current count — do not trip it. Only a count asserted as *current*
# (as of / currently / today), a live phase id, or a merged-progress count match.
_ROT_PATTERNS = (
    (r"merged\s+\d+\s*/\s*\d+", "hardcoded merged-phase progress count"),
    (r"\bIVL-P0\d\b", "hardcoded live phase id"),
    (r"\b\d+\s+survivors?\b[^.\n]*\b(?:as of|currently|today|right now)\b", "live survivor count stated as current"),
    (r"\bcurrently (?:building|running|on|at|in)\s+(?:IVL|DK|phase|campaign)", "dated live-campaign-status prose"),
)


def test_compass_has_no_live_status_rot() -> None:
    body = COMPASS.read_text(encoding="utf-8")
    hits = []
    for pattern, why in _ROT_PATTERNS:
        for match in re.finditer(pattern, body, flags=re.IGNORECASE):
            hits.append(f"{why}: {match.group(0)!r}")
    assert not hits, (
        "Live-status rot leaked into docs/OPERATING_COMPASS.md. Defer live "
        "phase/run/survivor status to `python tools/frontier/status_doctor.py`; "
        f"never hardcode it. Offenders: {hits}"
    )
