#!/usr/bin/env python3
"""Promote run-local Workflow 2 review records to the commit-eligible tree.

The Ralph driver keeps per-phase reviewer artifacts run-local under
``runs/<RUN_ID>/phases/<PHASE_ID>/{review.md,verdict.json}``. The campaign
acceptance gates ``yellow_phase_reviews_present_for_yellow_phases`` and
``review_verdicts_PASS_or_PASS_WITH_WARNINGS_for_merged_phases`` require those
records committed under ``reviews/<CAMPAIGN_ID>/<PHASE_ID>/``.

This coordinator helper copies the run-local records into ``reviews/`` so a
campaign closeout does not have to do it by hand (as was needed for the
ALPHA_RESEARCH_RUNTIME_MVP closeout). It only copies; explicit staging and
commit remain the coordinator's responsibility.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REVIEW_FILES = ("review.md", "verdict.json")


def promote_reviews(run_dir: Path, campaign_id: str, dest_root: Path) -> list[str]:
    """Copy each phase's run-local review records into ``reviews/<campaign>/``.

    Returns the sorted list of phase ids whose records were promoted.
    """

    phases_dir = run_dir / "phases"
    if not phases_dir.is_dir():
        raise FileNotFoundError(f"No phases directory under run dir: {phases_dir}")

    promoted: list[str] = []
    for phase_dir in sorted(p for p in phases_dir.iterdir() if p.is_dir()):
        sources = [phase_dir / name for name in REVIEW_FILES]
        if not all(src.is_file() for src in sources):
            continue
        out_dir = dest_root / campaign_id / phase_dir.name
        out_dir.mkdir(parents=True, exist_ok=True)
        for src in sources:
            shutil.copy2(src, out_dir / src.name)
        promoted.append(phase_dir.name)
    return promoted


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, help="Path to runs/<RUN_ID>.")
    parser.add_argument("--campaign-id", required=True, help="Campaign id, e.g. ALPHA_RESEARCH_RUNTIME_MVP.")
    parser.add_argument(
        "--dest-root",
        default=str(ROOT / "reviews"),
        help="Commit-eligible reviews root (default: <repo>/reviews).",
    )
    args = parser.parse_args(argv)

    run_dir = Path(args.run_dir)
    if not run_dir.is_absolute():
        run_dir = (ROOT / run_dir).resolve()
    dest_root = Path(args.dest_root)
    if not dest_root.is_absolute():
        dest_root = (ROOT / dest_root).resolve()

    promoted = promote_reviews(run_dir, args.campaign_id, dest_root)
    if not promoted:
        print("No run-local review records found to promote.")
        return 1
    rel = dest_root.relative_to(ROOT) if dest_root.is_relative_to(ROOT) else dest_root
    print(f"Promoted {len(promoted)} review record(s) into {rel}/{args.campaign_id}/:")
    for phase_id in promoted:
        print(f"  - {phase_id}")
    print("Stage the new reviews/ paths explicitly and commit; never stage runs/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
