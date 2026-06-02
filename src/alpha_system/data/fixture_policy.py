"""Local fixture and generated-artifact policy for data CLI commands."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from alpha_system.core.registry import is_local_only_registry_path
from alpha_system.data.paths import assert_local_wsl_path


FIXTURE_SIZE_LIMIT_BYTES = 64 * 1024
FIXTURE_ROOT = Path("tests") / "fixtures" / "data"
LOCAL_OUTPUT_ROOT = "data"
PROTECTED_COMMIT_DIRS: tuple[str, ...] = (
    "src",
    "tests",
    "docs",
    "configs",
    "handoffs",
    "reviews",
    "campaigns",
    "specs",
    "decisions",
    "metadata",
    "artifacts",
    "runs",
)
SYNTHETIC_MARKERS: tuple[str, ...] = ("synthetic",)
CORRECTNESS_MARKERS: tuple[str, ...] = (
    "correctness_only",
    "correctness-only",
    "correctness fixture",
    "correctness data",
)


class FixturePolicyError(ValueError):
    """Raised when a fixture or generated output violates local policy."""


@dataclass(frozen=True, slots=True)
class FixturePolicyCheck:
    path: Path
    size_bytes: int
    fixture_root: Path
    synthetic: bool
    deterministic: bool

    @property
    def allowed(self) -> bool:
        return self.synthetic and self.deterministic


def repository_root_from_module() -> Path:
    """Return the repository root containing this installed source tree."""
    return Path(__file__).resolve().parents[3]


def resolve_local_path(path: str | Path) -> Path:
    """Resolve a path and reject synced, Windows-mounted, or network paths."""
    return assert_local_wsl_path(path)


def fixture_root(*, repo_root: str | Path | None = None) -> Path:
    """Return the committed tiny data fixture root."""
    root = Path(repo_root) if repo_root is not None else repository_root_from_module()
    return root.expanduser().resolve(strict=False) / FIXTURE_ROOT


def is_allowed_fixture_path(
    path: str | Path,
    *,
    repo_root: str | Path | None = None,
) -> bool:
    """Return whether a path resolves under ``tests/fixtures/data``."""
    candidate = resolve_local_path(path)
    root = fixture_root(repo_root=repo_root)
    return _is_relative_to(candidate, root)


def check_fixture_file(
    path: str | Path,
    *,
    repo_root: str | Path | None = None,
) -> FixturePolicyCheck:
    """Validate path, size, and text markers for a committed tiny fixture."""
    candidate = resolve_local_path(path)
    root = fixture_root(repo_root=repo_root)
    if not _is_relative_to(candidate, root):
        msg = f"{candidate.as_posix()} is not under {root.as_posix()}"
        raise FixturePolicyError(msg)
    if not candidate.is_file():
        msg = f"{candidate.as_posix()} is not a fixture file"
        raise FixturePolicyError(msg)
    size = candidate.stat().st_size
    if size > FIXTURE_SIZE_LIMIT_BYTES:
        msg = (
            f"{candidate.as_posix()} is {size} bytes; "
            f"fixture limit is {FIXTURE_SIZE_LIMIT_BYTES} bytes"
        )
        raise FixturePolicyError(msg)

    text = _read_fixture_text(candidate)
    lowered = text.lower()
    synthetic = any(marker in lowered for marker in SYNTHETIC_MARKERS)
    deterministic = (
        "deterministic" in lowered
        or any(marker in lowered for marker in CORRECTNESS_MARKERS)
    )
    if not synthetic or not deterministic:
        msg = (
            f"{candidate.as_posix()} must be documented synthetic, "
            "deterministic correctness data"
        )
        raise FixturePolicyError(msg)
    return FixturePolicyCheck(
        path=candidate,
        size_bytes=size,
        fixture_root=root,
        synthetic=synthetic,
        deterministic=deterministic,
    )


def assert_build_input_allowed(
    path: str | Path,
    *,
    repo_root: str | Path | None = None,
    allow_non_fixture_input: bool = False,
) -> Path:
    """Validate build-bars input policy and return the resolved input path."""
    candidate = resolve_local_path(path)
    if allow_non_fixture_input:
        if not candidate.is_file():
            msg = f"{candidate.as_posix()} is not an input file"
            raise FixturePolicyError(msg)
        return candidate
    check_fixture_file(candidate, repo_root=repo_root)
    return candidate


def assert_generated_output_allowed(
    path: str | Path,
    *,
    repo_root: str | Path | None = None,
    require_data_dir: bool = False,
) -> Path:
    """Validate that a generated output path is local-only and non-committed."""
    candidate = resolve_local_path(path)
    root = (
        Path(repo_root).expanduser().resolve(strict=False)
        if repo_root is not None
        else repository_root_from_module()
    )

    if _is_relative_to(candidate, fixture_root(repo_root=root)):
        msg = "generated outputs must not be written under tests/fixtures/data"
        raise FixturePolicyError(msg)

    if _is_relative_to(candidate, root):
        relative = candidate.relative_to(root)
        first = relative.parts[0] if relative.parts else ""
        if first in PROTECTED_COMMIT_DIRS and first != LOCAL_OUTPUT_ROOT:
            msg = f"generated outputs are not allowed under committed {first}/ paths"
            raise FixturePolicyError(msg)

    if require_data_dir and LOCAL_OUTPUT_ROOT not in candidate.parts:
        msg = "build-bars output must resolve under a local-only data directory"
        raise FixturePolicyError(msg)

    return candidate


def assert_registry_path_allowed(
    path: str | Path,
    *,
    repo_root: str | Path | None = None,
) -> Path:
    """Validate that a data CLI registry target is temp/local and untracked."""
    candidate = resolve_local_path(path)
    if not is_local_only_registry_path(candidate):
        msg = f"{candidate.as_posix()} is not an allowed local registry path"
        raise FixturePolicyError(msg)

    root = (
        Path(repo_root).expanduser().resolve(strict=False)
        if repo_root is not None
        else repository_root_from_module()
    )
    if _is_relative_to(candidate, root):
        msg = "data CLI registry writes must use a temp/local path outside the repo"
        raise FixturePolicyError(msg)
    return candidate


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _read_fixture_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        msg = f"{path.as_posix()} must have text metadata documenting fixture policy"
        raise FixturePolicyError(msg) from exc
