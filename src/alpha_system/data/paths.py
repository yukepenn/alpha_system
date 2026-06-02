"""Local-only data path helpers for the data layer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DATA_DIR = "data"
RAW_DIR = "raw"
CANONICAL_DIR = "canonical"
FACTORS_DIR = "factors"
LABELS_DIR = "labels"
CACHE_DIR = "cache"

DATA_SUBDIRS: tuple[str, ...] = (
    RAW_DIR,
    CANONICAL_DIR,
    FACTORS_DIR,
    LABELS_DIR,
    CACHE_DIR,
)

LOCAL_SYNC_MARKERS: tuple[str, ...] = (
    "onedrive",
    "dropbox",
    "google drive",
    "googledrive",
)


@dataclass(frozen=True, slots=True)
class DataLayerPaths:
    """Resolved repo-local data directories without creating files."""

    repo_root: Path

    @classmethod
    def from_repo_root(cls, repo_root: str | Path = ".") -> "DataLayerPaths":
        return cls(repo_root=Path(repo_root).expanduser().resolve(strict=False))

    @property
    def data_root(self) -> Path:
        return self.repo_root / DATA_DIR

    @property
    def raw(self) -> Path:
        return self.data_root / RAW_DIR

    @property
    def canonical(self) -> Path:
        return self.data_root / CANONICAL_DIR

    @property
    def factors(self) -> Path:
        return self.data_root / FACTORS_DIR

    @property
    def labels(self) -> Path:
        return self.data_root / LABELS_DIR

    @property
    def cache(self) -> Path:
        return self.data_root / CACHE_DIR

    def subdir(self, name: str) -> Path:
        if name not in DATA_SUBDIRS:
            msg = f"{name!r} is not a supported data subdirectory"
            raise ValueError(msg)
        return self.data_root / name


def is_windows_mount_path(path: str | Path) -> bool:
    normalized = Path(path).as_posix().lower()
    return normalized.startswith(("/mnt/c/", "/mnt/d/", "/mnt/e/"))


def is_synced_or_network_path(path: str | Path) -> bool:
    lowered = Path(path).as_posix().lower()
    return lowered.startswith(("//", "\\\\")) or any(
        marker in lowered for marker in LOCAL_SYNC_MARKERS
    )


def is_local_wsl_path(path: str | Path) -> bool:
    return not is_windows_mount_path(path) and not is_synced_or_network_path(path)


def assert_local_wsl_path(path: str | Path) -> Path:
    resolved = Path(path).expanduser().resolve(strict=False)
    if not is_local_wsl_path(resolved):
        msg = f"{resolved.as_posix()} is not an allowed local WSL2 path"
        raise ValueError(msg)
    return resolved


def assert_repo_relative_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        msg = f"{candidate.as_posix()} must be repo-relative"
        raise ValueError(msg)
    if any(part == ".." for part in candidate.parts):
        msg = f"{candidate.as_posix()} must not traverse outside the repo"
        raise ValueError(msg)
    if is_windows_mount_path(candidate) or is_synced_or_network_path(candidate):
        msg = f"{candidate.as_posix()} is not an allowed local-relative path"
        raise ValueError(msg)
    return candidate


def resolve_data_subpath(
    subdir: str,
    relative_path: str | Path = "",
    *,
    repo_root: str | Path = ".",
) -> Path:
    """Resolve a path below one of the local data subdirectories."""
    relative = assert_repo_relative_path(relative_path)
    roots = DataLayerPaths.from_repo_root(repo_root)
    return assert_local_wsl_path(roots.subdir(subdir) / relative)


def fixture_data_path(relative_path: str | Path, *, repo_root: str | Path = ".") -> Path:
    """Resolve a tiny synthetic fixture data path under tests/fixtures/data."""
    relative = assert_repo_relative_path(relative_path)
    root = Path(repo_root).expanduser().resolve(strict=False)
    return assert_local_wsl_path(root / "tests" / "fixtures" / "data" / relative)


def is_commit_eligible_fixture(path: str | Path) -> bool:
    normalized = Path(path).as_posix()
    return normalized.startswith("tests/fixtures/data/")
