from __future__ import annotations

import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]


def _workflow_ci_deps() -> list[str]:
    workflow = yaml.safe_load((ROOT / ".github/workflows/frontier-ci.yml").read_text(encoding="utf-8"))
    for job in workflow["jobs"].values():
        for step in job["steps"]:
            if step.get("name") != "Install Python test dependencies":
                continue
            for line in step["run"].splitlines():
                match = re.fullmatch(r"\s*python -m pip install (?!.*--upgrade)(?P<deps>.+)\s*", line)
                if match:
                    return match.group("deps").split()
    raise AssertionError("Could not find CI Python test dependency install line")


def _pinned_ci_parity_deps() -> list[str]:
    deps: list[str] = []
    requirements = ROOT / "tools/frontier/ci_parity_requirements.txt"
    for line in requirements.read_text(encoding="utf-8").splitlines():
        value = line.split("#", 1)[0].strip()
        if value:
            deps.append(value)
    return deps


def test_ci_parity_requirements_match_frontier_ci_workflow() -> None:
    assert [dep.lower() for dep in _pinned_ci_parity_deps()] == [
        dep.lower() for dep in _workflow_ci_deps()
    ]
