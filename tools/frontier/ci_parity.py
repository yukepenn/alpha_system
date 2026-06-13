#!/usr/bin/env python3
"""Run the local test suite in the same minimal dependency surface as CI."""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
import venv
from collections.abc import Iterable
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.frontier.runtime_paths import persistent_tmp_root

REQUIREMENTS = ROOT / "tools/frontier/ci_parity_requirements.txt"
DEFAULT_VENV = Path("~/.venvs/alpha_system_ci").expanduser()
OPTIONAL_MODULES = ("databento", "duckdb", "ib_insync", "numpy", "pandas", "polars", "pyarrow")
IMPORT_NAMES = {"pyyaml": "yaml"}


def read_requirements() -> list[str]:
    deps: list[str] = []
    for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        value = line.split("#", 1)[0].strip()
        if value:
            deps.append(value)
    return deps


def venv_path() -> Path:
    return Path(os.environ.get("FRONTIER_CI_PARITY_VENV", str(DEFAULT_VENV))).expanduser()


def venv_python(path: Path) -> Path:
    return path / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def pip_available(python: Path) -> bool:
    result = subprocess.run(
        [str(python), "-m", "pip", "--version"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def run(command: list[str], *, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    print("+ " + shlex.join(command), flush=True)
    return subprocess.run(command, cwd=cwd, text=True, check=False)


def create_venv(path: Path) -> Path:
    python = venv_python(path)
    if python.exists():
        if not pip_available(python):
            print(f"ERROR: CI parity venv at {path} exists but cannot run `python -m pip`.", file=sys.stderr)
            print(
                "Install python3.12-venv/ensurepip support and recreate the venv, or point "
                "FRONTIER_CI_PARITY_VENV at a valid pip-capable venv.",
                file=sys.stderr,
            )
            raise SystemExit(2)
        return python
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Creating CI parity venv: {path}", flush=True)
        venv.EnvBuilder(with_pip=True, clear=False, symlinks=True).create(path)
    except OSError as exc:
        print(f"ERROR: cannot create CI parity venv at {path}: {exc}", file=sys.stderr)
        print(
            "The default parity venv path must be writable, or set FRONTIER_CI_PARITY_VENV "
            "to an explicit writable path for a sandboxed probe.",
            file=sys.stderr,
        )
        raise SystemExit(2) from None
    except SystemExit as exc:
        print(f"ERROR: failed to create CI parity venv at {path}.", file=sys.stderr)
        print(
            "Install python3.12-venv/ensurepip support (or bootstrap with `virtualenv <path>` "
            "when ensurepip is unavailable), then rerun `just ci-parity`.",
            file=sys.stderr,
        )
        raise SystemExit(exc.code or 2) from None
    if not pip_available(python):
        print(f"ERROR: created CI parity venv at {path}, but `python -m pip` is unavailable.", file=sys.stderr)
        print("Install python3.12-venv/ensurepip support, then recreate the venv.", file=sys.stderr)
        raise SystemExit(2)
    return python


def dep_import_name(dep: str) -> str:
    name = dep.split("==", 1)[0].split(">=", 1)[0].split("<", 1)[0].strip().lower()
    return IMPORT_NAMES.get(name, name.replace("-", "_"))


def missing_deps(python: Path, deps: Iterable[str]) -> list[str]:
    missing: list[str] = []
    for dep in deps:
        module = dep_import_name(dep)
        probe = subprocess.run(
            [str(python), "-c", f"import {module}"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if probe.returncode != 0:
            missing.append(dep)
    return missing


def wheel_dirs() -> list[Path]:
    frontier_tmp = persistent_tmp_root()
    roots: list[Path] = []
    for raw in os.environ.get("FRONTIER_CI_PARITY_WHEEL_DIR", "").split(os.pathsep):
        if raw.strip():
            roots.append(Path(raw).expanduser())
    roots.extend(
        [
            ROOT / "tools/frontier/wheels",
            ROOT / "wheelhouse",
            Path("~/.cache/pip").expanduser(),
            Path("~/.cache/uv").expanduser(),
            frontier_tmp / "wheelhouse",
            frontier_tmp / "wheels",
        ]
    )

    found: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        for wheel in root.rglob("*.whl"):
            parent = wheel.parent.resolve()
            if parent not in seen:
                seen.add(parent)
                found.append(parent)
    return found


def install_from_local_wheels(python: Path, dirs: list[Path]) -> bool:
    if not dirs:
        return False
    command = [str(python), "-m", "pip", "install", "--no-index"]
    for directory in dirs:
        command.extend(["--find-links", str(directory)])
    command.extend(["-r", str(REQUIREMENTS)])
    return run(command).returncode == 0


def install_from_network(python: Path) -> bool:
    upgrade = run([str(python), "-m", "pip", "install", "--upgrade", "pip"])
    if upgrade.returncode != 0:
        return False
    return run([str(python), "-m", "pip", "install", "-r", str(REQUIREMENTS)]).returncode == 0


def assert_no_optional_modules(python: Path) -> bool:
    script = "\n".join(
        [
            "import importlib.util",
            f"mods = {OPTIONAL_MODULES!r}",
            "present = [m for m in mods if importlib.util.find_spec(m) is not None]",
            "print('\\n'.join(present))",
            "raise SystemExit(1 if present else 0)",
        ]
    )
    result = subprocess.run(
        [str(python), "-c", script],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return True
    print(
        "CI parity venv contains optional/non-CI modules; refusing to run because it could hide CI failures:",
        file=sys.stderr,
    )
    print(result.stdout.strip(), file=sys.stderr)
    print(f"Remove {venv_path()} and rebuild it from the pinned CI parity deps.", file=sys.stderr)
    return False


def ensure_venv() -> Path:
    deps = read_requirements()
    path = venv_path()
    python = create_venv(path)
    missing = missing_deps(python, deps)
    if missing:
        dirs = wheel_dirs()
        if install_from_local_wheels(python, dirs):
            missing = missing_deps(python, deps)
        if missing and os.environ.get("FRONTIER_CI_PARITY_ALLOW_NETWORK") == "1":
            if install_from_network(python):
                missing = missing_deps(python, deps)
        if missing:
            searched = ", ".join(str(path) for path in dirs) or "none found"
            print("ERROR: CI parity bootstrap could not satisfy the pinned deps offline.", file=sys.stderr)
            print(f"Missing deps: {', '.join(missing)}", file=sys.stderr)
            print(f"Local wheel/cache dirs searched: {searched}", file=sys.stderr)
            print(
                "The recipe did not fall back to the research venv or system site-packages, "
                "because that would not match GitHub CI. Pre-seed local wheels via "
                "FRONTIER_CI_PARITY_WHEEL_DIR or rerun with FRONTIER_CI_PARITY_ALLOW_NETWORK=1.",
                file=sys.stderr,
            )
            raise SystemExit(2)
    if not assert_no_optional_modules(python):
        raise SystemExit(2)
    return python


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run pytest in the CI-parity venv.")
    parser.add_argument("pytest_args", nargs=argparse.REMAINDER)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    pytest_args = list(args.pytest_args)
    if pytest_args and pytest_args[0] == "--":
        pytest_args = pytest_args[1:]
    python = ensure_venv()
    return run([str(python), "-m", "pytest", *pytest_args]).returncode


if __name__ == "__main__":
    raise SystemExit(main())
