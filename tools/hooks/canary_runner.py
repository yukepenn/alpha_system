"""Run Frontier safety canary scaffolds."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CANARY_DIR = ROOT / "evals" / "canaries"


def main() -> int:
    if not CANARY_DIR.exists():
        print("No canary directory found.")
        return 1
    scenarios = sorted(path for path in CANARY_DIR.iterdir() if path.is_dir())
    if not scenarios:
        print("No canary scenarios found.")
        return 1
    for scenario in scenarios:
        print(f"Canary scaffold present: {scenario.name}")
    print("Canary runner scaffold passed. Implement project-specific negative tests as the harness matures.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
