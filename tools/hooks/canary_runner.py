"""Run Frontier negative canaries against hook guards in temporary repos."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.frontier.runtime_paths import persistent_tmp_env, persistent_tmp_root  # noqa: E402

HOOKS = ROOT / "tools" / "hooks"


@dataclass(frozen=True)
class Canary:
    name: str
    command: list[str]
    paths: dict[str, str]
    expect_block: bool = True
    report_on_pass: bool = False


def write_files(base: Path, paths: dict[str, str]) -> None:
    for relative, text in paths.items():
        path = base / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _scrub_git_env(env: Mapping[str, str] | None = None) -> dict[str, str]:
    source = os.environ if env is None else env
    return {key: value for key, value in source.items() if not key.startswith("GIT_")}


def _clean_runtime_env(env: Mapping[str, str] | None = None) -> dict[str, str]:
    return persistent_tmp_env(repo_root=ROOT, env=_scrub_git_env(env))


def run_canary(canary: Canary) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory(
        prefix=f"frontier-canary-{canary.name}-",
        dir=persistent_tmp_root(repo_root=ROOT),
    ) as raw_tmp:
        tmp = Path(raw_tmp)
        clean_env = _clean_runtime_env()
        subprocess.run(
            ["git", "init"],
            cwd=tmp,
            env=clean_env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        write_files(tmp, canary.paths)
        result = subprocess.run(
            canary.command,
            cwd=tmp,
            env=clean_env,
            text=True,
            capture_output=True,
            check=False,
        )
        blocked = result.returncode != 0
        passed = blocked if canary.expect_block else not blocked
        detail = result.stdout + result.stderr
        return passed, detail.strip()


def governance_canary(canary_type: str) -> Canary:
    snippet = (
        "import sys; "
        f"sys.path.insert(0, {str(ROOT / 'src')!r}); "
        "from alpha_system.governance.canaries.harness import main; "
        f"raise SystemExit(main(['--canary', {canary_type!r}]))"
    )
    return Canary(
        f"governance_{canary_type}",
        [sys.executable, "-c", snippet],
        {},
        expect_block=False,
    )


def planted_fake_alpha_canary() -> Canary:
    snippet = (
        "import sys, tempfile; "
        "from pathlib import Path; "
        f"sys.path.insert(0, {str(ROOT / 'src')!r}); "
        "from alpha_system.governance.canaries.planted_fake_alpha import "
        "run_planted_fake_alpha_canary; "
        "\ntry:\n"
        "    with tempfile.TemporaryDirectory(prefix='frontier-planted-fake-alpha-') as raw_tmp:\n"
        "        result = run_planted_fake_alpha_canary(workspace=Path(raw_tmp))\n"
        "except Exception as exc:\n"
        "    print(f'ERROR planted_fake_alpha {type(exc).__name__}: {exc}', file=sys.stderr)\n"
        "    raise SystemExit(0)\n"
        "print(f'{result.promotion_outcome} {result.blocked_gate} {result.blocked_issue_code}')\n"
        "raise SystemExit(1 if result.rejected else 0)\n"
    )
    return Canary(
        "planted_fake_alpha",
        [sys.executable, "-c", snippet],
        {},
        expect_block=True,
    )


def true_alpha_detection_canary(strength: str, *, expected_detection: bool) -> Canary:
    expectation = "detect" if expected_detection else "no_detect"
    snippet = (
        "import sys, tempfile; "
        "from pathlib import Path; "
        f"sys.path.insert(0, {str(ROOT / 'src')!r}); "
        "from alpha_system.governance.canaries.true_alpha_detection import "
        "run_true_alpha_detection_canary; "
        "\ntry:\n"
        "    with tempfile.TemporaryDirectory("
        "prefix='frontier-true-alpha-detection-') as raw_tmp:\n"
        f"        result = run_true_alpha_detection_canary({strength!r}, workspace=Path(raw_tmp))\n"
        "except Exception as exc:\n"
        "    print(f'ERROR true_alpha_detection {type(exc).__name__}: {exc}', file=sys.stderr)\n"
        "    raise SystemExit(1)\n"
        "print(\n"
        "    f'{result.strength} {result.detection_outcome} '\n"
        "    f'{result.measured_abs_pearson_ic:.6f} '\n"
        "    f'{result.detection_threshold_abs_pearson_ic:.6f}'\n"
        ")\n"
        f"raise SystemExit(0 if result.detected is {expected_detection!r} "
        "and result.expectation_met else 1)\n"
    )
    return Canary(
        f"true_alpha_detection_{expectation}_{strength}",
        [sys.executable, "-c", snippet],
        {},
        expect_block=False,
    )


def registry_event_ts_grid_canary() -> Canary:
    snippet = (
        "import sys; "
        f"sys.path.insert(0, {str(ROOT / 'src')!r}); "
        "from alpha_system.governance.canaries.registry_event_ts_grid import main; "
        "raise SystemExit(main(['--mode', 'synthetic']))"
    )
    return Canary(
        "registry_event_ts_grid",
        [sys.executable, "-c", snippet],
        {},
        expect_block=False,
        report_on_pass=True,
    )


def exploratory_promotion_refusal_canary() -> Canary:
    snippet = (
        "import sys; "
        f"sys.path.insert(0, {str(ROOT / 'src')!r}); "
        "from alpha_system.governance.promotion import "
        "EXPLORATORY_PROMOTION_REFUSAL_CODE, reject_exploratory_promotion_artifact; "
        "from alpha_system.governance.validation import GovernanceValidationError; "
        "artifact = {'readout_id': 'canary', 'stamp': 'EXPLORATORY'}; "
        "\ntry:\n"
        "    reject_exploratory_promotion_artifact(artifact, field='promotion_artifact')\n"
        "except GovernanceValidationError as exc:\n"
        "    codes = {issue.code for issue in exc.issues}\n"
        "    print(','.join(sorted(codes)))\n"
        "    raise SystemExit(0 if EXPLORATORY_PROMOTION_REFUSAL_CODE in codes else 1)\n"
        "print('EXPLORATORY artifact was not refused')\n"
        "raise SystemExit(1)\n"
    )
    return Canary(
        "forbidden_exploratory_promotion",
        [sys.executable, "-c", snippet],
        {},
        expect_block=False,
    )


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
            {
                "tests/test_bad.py": (
                    "import pytest\n\n@pytest.mark.skip(reason='bad')\n"
                    "def test_bad():\n    assert True\n"
                )
            },
        ),
        Canary(
            "forbidden_secret",
            [py, str(HOOKS / "secret_scan.py"), ".env", "credentials/token.txt"],
            {".env": "TOKEN=example\n", "credentials/token.txt": "example\n"},
        ),
        Canary(
            # Innocuous filename so the path scan would miss it; only the content
            # scan catches the committed private-key material.
            "forbidden_secret_content",
            [py, str(HOOKS / "secret_scan.py"), "src/helpers/config_loader.py"],
            {
                "src/helpers/config_loader.py": (
                    "KEY = '''-----BEGIN OPENSSH PRIVATE KEY-----\n"
                    "b3BlbnNzaC1rZXk=\n-----END OPENSSH PRIVATE KEY-----'''\n"
                )
            },
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
            "forbidden_stray_raw_suffix",
            [py, str(HOOKS / "artifact_guard.py"), "raw_backup.raw"],
            {"raw_backup.raw": "raw,value\n1,2\n"},
        ),
        Canary(
            "forbidden_stray_dbn_suffix",
            [py, str(HOOKS / "artifact_guard.py"), "root_sample.dbn"],
            {"root_sample.dbn": "raw\n"},
        ),
        Canary(
            "forbidden_cache_data_commit",
            [py, str(HOOKS / "artifact_guard.py"), "data/cache/cache.db"],
            {"data/cache/cache.db": "cache\n"},
        ),
        Canary(
            # AGENTS.md hard rule: runs/** is local-only and must never be staged.
            # Locks the artifact guard against staging run-state, events, or values.
            "forbidden_runs_staging",
            [
                py,
                str(HOOKS / "artifact_guard.py"),
                "runs/2026Z_DEMO/state.json",
                "runs/2026Z_DEMO/events.jsonl",
                "runs/2026Z_DEMO/phases/P00/values.parquet",
            ],
            {
                "runs/2026Z_DEMO/state.json": "{}\n",
                "runs/2026Z_DEMO/events.jsonl": "{}\n",
                "runs/2026Z_DEMO/phases/P00/values.parquet": "x\n",
            },
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
            {
                "src/runtime_ops.py": (
                    "def run():\n    PLACE_LIVE_ORDER = True\n    return PLACE_LIVE_ORDER\n"
                )
            },
        ),
        Canary(
            # AGENTS.md Hard Constraints: no second PnL/value truth. A module
            # defining pnl/equity-curve math outside the sanctioned reference
            # engine must be blocked by the forbidden-pattern guard.
            "forbidden_second_pnl_truth",
            [py, str(HOOKS / "forbidden_pattern_guard.py"), "src/alpha_system/research_alt_pnl.py"],
            {
                "src/alpha_system/research_alt_pnl.py": (
                    "def compute_pnl(trades):\n    return sum(t.qty * t.px for t in trades)\n\n\n"
                    "def build_equity_curve(trades):\n"
                    "    return [compute_pnl(trades[:i]) for i in range(len(trades))]\n"
                )
            },
        ),
        Canary(
            # The sanctioned reference engine path must NOT false-positive:
            # pnl/equity-curve definitions are legitimate there.
            "sanctioned_pnl_truth_allowed",
            [
                py,
                str(HOOKS / "forbidden_pattern_guard.py"),
                "src/alpha_system/backtest/accounting_ext.py",
            ],
            {
                "src/alpha_system/backtest/accounting_ext.py": (
                    "def realized_pnl(fills):\n    return sum(f.qty * f.px for f in fills)\n"
                )
            },
            expect_block=False,
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
                "artifacts/.gitkeep",
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
                "artifacts/.gitkeep": "",
                "artifacts/reports/README.md": "local-only placeholder\n",
            },
            expect_block=False,
        ),
        governance_canary("random_target"),
        governance_canary("future_shift"),
        governance_canary("permuted_labels"),
        governance_canary("optimistic_fill"),
        registry_event_ts_grid_canary(),
        exploratory_promotion_refusal_canary(),
        planted_fake_alpha_canary(),
        true_alpha_detection_canary("strong", expected_detection=True),
        true_alpha_detection_canary("weak", expected_detection=False),
    ]


def main() -> int:
    failures: list[str] = []
    for canary in scenarios():
        passed, detail = run_canary(canary)
        if passed:
            print(f"PASS {canary.name}")
            if canary.report_on_pass and detail:
                print(detail)
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
