"""Generate docs/SYSTEM_MAP.md from the repository itself.

The map is intentionally structure-level (anchors, packages, commands, lanes),
not file-level, so it changes only when the system's shape changes. It is the
single navigation page both Claude and Codex load instead of re-discovering
structure each session.

Usage:
    python tools/frontier/system_map.py            # rewrite docs/SYSTEM_MAP.md
    python tools/frontier/system_map.py --check    # exit 1 if committed map drifts

Drift guard: tests/tools/test_system_map.py runs --check, so CI fails whenever
an anchor moves, a package appears, or a command changes without regenerating
the map. A missing anchor is a hard generation error, never a silent omission.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAP_PATH = ROOT / "docs" / "SYSTEM_MAP.md"

# Load-bearing anchors: role -> repo-relative path. Generation fails if one is
# missing so a relocation forces a conscious map update instead of silent rot.
ANCHORS: list[tuple[str, str, str]] = [
    (
        "Reference engine (single PnL/value truth)",
        "src/alpha_system/backtest/reference.py",
        "All value/accounting math. No second truth anywhere.",
    ),
    (
        "Fast path (values only, parity-gated)",
        "src/alpha_system/backtest/fast_path.py",
        "Accelerator; never redefines identity or accounting.",
    ),
    (
        "Parity harness",
        "src/alpha_system/backtest/parity.py",
        "Fast-path vs reference reconciliation; fail closed without parity.",
    ),
    (
        "Feature identity + registry",
        "src/alpha_system/features/registry.py",
        "Content-addressed feature_version_id; serial registry writes.",
    ),
    (
        "Label identity + registry",
        "src/alpha_system/labels/registry.py",
        "Content-addressed label_version_id; serial registry writes.",
    ),
    (
        "Value store",
        "src/alpha_system/core/value_store.py",
        "JSONL+Parquet dual sink; content-hash addressed.",
    ),
    (
        "Input resolver (governance-gated access)",
        "src/alpha_system/runtime/input_resolver.py",
        "Dataset/feature/label resolution; exact-id semantics.",
    ),
    (
        "Promotion gate state machine",
        "src/alpha_system/governance/promotion_gate.py",
        "DRAFT→…→{CANDIDATE,VALIDATED,INCONCLUSIVE,WATCH,REJECTED}; mechanical.",
    ),
    (
        "Trial ledger",
        "src/alpha_system/governance/trial_ledger.py",
        "Every trial counted; contamination flags; variant budgets.",
    ),
    (
        "Unsupported-claims guard",
        "src/alpha_system/governance/claims.py",
        "Blocks alpha/profitability/tradability/production language.",
    ),
    (
        "Negative-control canary harness",
        "src/alpha_system/governance/canaries/harness.py",
        "future_shift / permuted_labels / optimistic_fill executable controls.",
    ),
    (
        "Walk-forward splits (purge/embargo)",
        "src/alpha_system/experiments/splits.py",
        "Chronological train/validation discipline.",
    ),
    (
        "CLI entry (`alpha`)",
        "src/alpha_system/cli/main.py",
        "Command surface; see docs/CLI_REFERENCE.md.",
    ),
    (
        "Workflow 2 driver (Ralph)",
        "tools/frontier/ralph_driver.py",
        "State machine, gates, prompts, merge queue. Change only via spec+review.",
    ),
    (
        "Live-status oracle",
        "tools/frontier/status_doctor.py",
        "Authoritative campaign/phase + pointer-drift checks.",
    ),
    ("Verification entry", "tools/verify.py", "--smoke/--all/--boundaries/--artifacts."),
    (
        "Commit-time guard floor",
        "tools/hooks/pre_commit.py",
        "secret/artifact/bulk-add/test-tamper/boundary guards.",
    ),
    (
        "Safety canary gate",
        "tools/hooks/canary_runner.py",
        "Must pass pre-push and in CI; canaries live in evals/canaries/.",
    ),
]

DO_NOT_TOUCH = [
    "frontier.yaml — control plane (lanes, budgets, providers)",
    ".githooks/ + tools/hooks/ — deterministic commit-time floor",
    "evals/canaries/** — the safety net itself",
    "tools/frontier/ralph_driver.py — Workflow 2 driver / merge gates",
    "tests marked locked / parity goldens — never weaken without spec authorization",
]


def _first_docstring_line(path: Path) -> str:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return ""
    doc = ast.get_docstring(tree) or ""
    return doc.strip().splitlines()[0].strip() if doc.strip() else ""


def src_packages() -> list[tuple[str, str]]:
    pkg_root = ROOT / "src" / "alpha_system"
    rows = []
    for child in sorted(pkg_root.iterdir()):
        if child.is_dir() and (child / "__init__.py").exists():
            rows.append((child.name, _first_docstring_line(child / "__init__.py")))
    return rows


def justfile_recipes() -> list[str]:
    text = (ROOT / "justfile").read_text(encoding="utf-8")
    names = []
    for line in text.splitlines():
        match = re.match(r"^([a-zA-Z0-9_-]+)(?:\s+\$[^:]*)?:(?:$|\s)", line)
        if match and match.group(1) != "set":
            names.append(match.group(1))
    return names


def canaries() -> list[str]:
    canary_dir = ROOT / "evals" / "canaries"
    return sorted(p.name for p in canary_dir.iterdir() if p.is_dir())


def lanes_and_models() -> tuple[list[str], list[tuple[str, str]]]:
    import yaml

    config = yaml.safe_load((ROOT / "frontier.yaml").read_text(encoding="utf-8"))
    lane_names = list((config.get("lanes") or {}).keys())
    models = [
        (name, str(entry.get("model", ""))) for name, entry in (config.get("models") or {}).items()
    ]
    return lane_names, models


def generate() -> str:
    missing = [path for _, path, _ in ANCHORS if not (ROOT / path).exists()]
    if missing:
        raise SystemExit(
            "system_map: missing anchors (relocate happened — update ANCHORS in "
            f"tools/frontier/system_map.py): {missing}"
        )

    lane_names, models = lanes_and_models()
    lines: list[str] = []
    add = lines.append
    add("# System Map (generated)")
    add("")
    add("> GENERATED by `tools/frontier/system_map.py` — do not hand-edit.")
    add("> Regenerate with `just system-map`. CI fails on drift")
    add("> (`tests/tools/test_system_map.py`).")
    add(">")
    add("> Live campaign/phase status is NEVER in this file: run")
    add("> `python tools/frontier/status_doctor.py`. Invariants: `CRITICAL.md`.")
    add("> Constitution: `AGENTS.md`. Docs index: `docs/README.md`.")
    add("")
    add("## Load-bearing anchors")
    add("")
    add("| Role | Path | Note |")
    add("| --- | --- | --- |")
    for role, path, note in ANCHORS:
        add(f"| {role} | `{path}` | {note} |")
    add("")
    add("## Do-not-touch set (change only via spec + fresh review)")
    add("")
    for item in DO_NOT_TOUCH:
        add(f"- {item}")
    add("")
    add("## Source packages (`src/alpha_system/`)")
    add("")
    add("| Package | Purpose |")
    add("| --- | --- |")
    for name, purpose in src_packages():
        add(f"| `{name}` | {purpose} |")
    add("")
    add("## Lanes and models (`frontier.yaml`)")
    add("")
    add(f"- Lanes: {', '.join(lane_names)}")
    for name, model in models:
        add(f"- `{name}`: {model}")
    add("")
    add("## Command surface (`justfile`)")
    add("")
    add("- " + " · ".join(f"`{name}`" for name in justfile_recipes()))
    add("")
    add("## Safety canaries (`evals/canaries/`)")
    add("")
    add("- " + " · ".join(f"`{name}`" for name in canaries()))
    add("")
    add("## Workflow entry points")
    add("")
    add("- Workflow 1 (human-gated): `just frontier-run-workflow1`, specs in `specs/`.")
    add("- Workflow 2 (Ralph strict loop): `just frontier-run-parallel <CAMPAIGN_ID> 3`;")
    add("  resume via `just frontier-resume-run <RUN_ID>`; stop via `just frontier-stop <RUN_ID>`.")
    add("- Pre-handoff gate: `just agent-preflight`.")
    add("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if the committed map drifts")
    args = parser.parse_args(argv)

    content = generate()
    if args.check:
        committed = MAP_PATH.read_text(encoding="utf-8") if MAP_PATH.exists() else ""
        if committed != content:
            print(
                "docs/SYSTEM_MAP.md is stale. Regenerate with: just system-map",
                file=sys.stderr,
            )
            return 1
        print("docs/SYSTEM_MAP.md is current.")
        return 0
    MAP_PATH.write_text(content, encoding="utf-8")
    print(f"wrote {MAP_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
