"""Run Frontier negative canaries against hook guards in temporary repos."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / "tools" / "hooks"


@dataclass(frozen=True)
class Canary:
    name: str
    command: list[str]
    paths: dict[str, str]
    expect_block: bool = True


def write_files(base: Path, paths: dict[str, str]) -> None:
    for relative, text in paths.items():
        path = base / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def run_canary(canary: Canary) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory(prefix=f"frontier-canary-{canary.name}-") as raw_tmp:
        tmp = Path(raw_tmp)
        subprocess.run(["git", "init"], cwd=tmp, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        write_files(tmp, canary.paths)
        result = subprocess.run(canary.command, cwd=tmp, text=True, capture_output=True, check=False)
        blocked = result.returncode != 0
        passed = blocked if canary.expect_block else not blocked
        detail = result.stdout + result.stderr
        return passed, detail.strip()


def scenarios() -> list[Canary]:
    py = sys.executable
    return [
        Canary(
            "forbidden_git_add_dot",
            [py, str(HOOKS / "forbidden_pattern_guard.py"), "scripts/bad.sh"],
            {"scripts/bad.sh": "#!/usr/bin/env bash\ngit add" + " .\n"},
        ),
        Canary(
            "policy_doc_mentions_forbidden_command",
            [py, str(HOOKS / "forbidden_pattern_guard.py"), "docs/policy.md"],
            {"docs/policy.md": "Policy text: do not use " + "git add" + " . in automation.\n"},
            expect_block=False,
        ),
        Canary(
            "forbidden_test_tamper",
            [py, str(HOOKS / "test_tamper_guard.py"), "tests/test_bad.py"],
            {"tests/test_bad.py": "import pytest\n\n@pytest.mark.skip(reason='bad')\ndef test_bad():\n    assert True\n"},
        ),
        Canary(
            "forbidden_secret",
            [py, str(HOOKS / "secret_scan.py"), ".env", "credentials/token.txt"],
            {".env": "TOKEN=example\n", "credentials/token.txt": "example\n"},
        ),
        Canary(
            "forbidden_large_binary",
            [py, str(HOOKS / "artifact_guard.py"), "models/model.onnx"],
            {"models/model.onnx": "not really binary\n"},
        ),
        Canary(
            "forbidden_destructive_op",
            [py, str(HOOKS / "forbidden_pattern_guard.py"), "scripts/cleanup.sh"],
            {"scripts/cleanup.sh": "#!/usr/bin/env bash\nrm -rf /tmp/frontier-example\n"},
        ),
        Canary(
            "forbidden_boundary_import",
            [py, str(HOOKS / "boundary_guard.py"), "../outside.txt"],
            {},
        ),
        Canary(
            "forbidden_raw_data_commit",
            [py, str(HOOKS / "artifact_guard.py"), "data/raw/input.csv"],
            {"data/raw/input.csv": "raw,value\n1,2\n"},
        ),
        Canary(
            "forbidden_cache_data_commit",
            [py, str(HOOKS / "artifact_guard.py"), "data/cache/cache.db"],
            {"data/cache/cache.db": "cache\n"},
        ),
        Canary(
            "forbidden_local_artifacts",
            [
                py,
                str(HOOKS / "artifact_guard.py"),
                "data/raw/SPY.parquet",
                "data/cache/cache.sqlite",
                "artifacts/model.pkl",
                "metadata/registry.sqlite",
                ".env",
                "secrets.json",
            ],
            {
                "data/raw/SPY.parquet": "raw\n",
                "data/cache/cache.sqlite": "cache\n",
                "artifacts/model.pkl": "model\n",
                "metadata/registry.sqlite": "registry\n",
                ".env": "TOKEN=example\n",
                "secrets.json": "{}\n",
            },
        ),
        Canary(
            "forbidden_scope_drift",
            [py, str(HOOKS / "forbidden_pattern_guard.py"), "src/runtime_ops.py"],
            {"src/runtime_ops.py": "def run():\n    PLACE_LIVE_ORDER = True\n    return PLACE_LIVE_ORDER\n"},
        ),
        Canary(
            "generated_scaffold_allowed",
            [
                py,
                str(HOOKS / "artifact_guard.py"),
                "data/raw/.gitkeep",
                "data/raw/README.md",
                "data/cache/.gitkeep",
                "data/cache/README.md",
                "data/canonical/.gitkeep",
                "data/factors/README.md",
                "data/labels/README.md",
                "metadata/README.md",
                "artifacts/README.md",
                "artifacts/reports/README.md",
            ],
            {
                "data/raw/.gitkeep": "",
                "data/raw/README.md": "local-only placeholder\n",
                "data/cache/.gitkeep": "",
                "data/cache/README.md": "local-only placeholder\n",
                "data/canonical/.gitkeep": "",
                "data/factors/README.md": "local-only placeholder\n",
                "data/labels/README.md": "local-only placeholder\n",
                "metadata/README.md": "local-only placeholder\n",
                "artifacts/README.md": "local-only placeholder\n",
                "artifacts/reports/README.md": "local-only placeholder\n",
            },
            expect_block=False,
        ),
    ]


def main() -> int:
    failures: list[str] = []
    for canary in scenarios():
        passed, detail = run_canary(canary)
        if passed:
            print(f"PASS {canary.name}")
        else:
            print(f"FAIL {canary.name}")
            if detail:
                print(detail)
            failures.append(canary.name)
    if failures:
        print("Canary failures: " + ", ".join(failures))
        return 1
    print("All Frontier canaries passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
