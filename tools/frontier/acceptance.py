"""Post-bootstrap acceptance checks for the Frontier harness runtime."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REQUIRED_PATHS = [
    "AGENTS.md",
    "CLAUDE.md",
    "frontier.yaml",
    "campaigns",
    "specs",
    "handoffs",
    "reviews",
    "tools/frontier/ralph_driver.py",
    "tools/frontier/github_utils.py",
    "tools/frontier/merge_gate.py",
    "tests",
]


def run(command: list[str], *, env: dict[str, str] | None = None) -> int:
    print("+ " + " ".join(command))
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(command, cwd=ROOT, env=merged_env, check=False).returncode


def check_required_paths() -> int:
    missing = [path for path in REQUIRED_PATHS if not (ROOT / path).exists()]
    if not missing:
        print("Required Frontier paths are present.")
        return 0
    print("Missing required Frontier paths:")
    for path in missing:
        print(f"- {path}")
    return 1


def has_tests() -> bool:
    tests = ROOT / "tests"
    return tests.exists() and any(path.name.startswith("test_") for path in tests.rglob("*.py"))


def merge_gate_smoke() -> int:
    run_dir = ROOT / "runs" / "acceptance_merge_gate"
    run_dir.mkdir(parents=True, exist_ok=True)
    verdict = run_dir / "verdict.json"
    verdict.write_text(
        json.dumps(
            {
                "schema_version": "frontier-review-verdict-v1",
                "verdict": "PASS",
                "severity": "none",
                "findings": [],
                "required_repairs": [],
                "warnings": [],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return run(
        [
            sys.executable,
            "tools/frontier/merge_gate.py",
            "--campaign-id",
            "ACCEPTANCE",
            "--phase-id",
            "P00",
            "--lane",
            "green",
            "--ci-status",
            "SUCCESS",
            "--verdict-json",
            str(verdict),
            "--run-dir",
            str(run_dir),
            "--dry-run",
        ]
    )


def run_acceptance() -> int:
    status = 0
    status |= check_required_paths()
    status |= run([sys.executable, "tools/frontier/bootstrap.py", "check-config"])
    status |= run([sys.executable, "-m", "compileall", "tools", "tests"])
    if has_tests():
        status |= run([sys.executable, "-m", "pytest"])
    status |= run([sys.executable, "tools/frontier/bootstrap.py", "doctor"])
    status |= run([sys.executable, "tools/hooks/canary_runner.py"])
    status |= run([sys.executable, "tools/verify.py", "--artifacts"])
    status |= run(
        [
            sys.executable,
            "tools/frontier/ralph_driver.py",
            "run",
            "--campaign-id",
            "G005_WORKFLOW2_TOY",
            "--provider-wired",
        ],
        env={"FRONTIER_MOCK_PROVIDERS": "1", "FRONTIER_MAX_PHASES": "1"},
    )
    status |= merge_gate_smoke()
    return 1 if status else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Frontier post-bootstrap acceptance checks.")
    parser.parse_args(argv)
    return run_acceptance()


if __name__ == "__main__":
    raise SystemExit(main())
