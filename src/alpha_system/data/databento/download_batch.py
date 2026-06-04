"""Databento batch-state check and local raw download tooling."""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType

from alpha_system.data.databento.cost_check import _historical_client_context
from alpha_system.data.databento.manifest_files import _validate_raw_root
from alpha_system.data.databento.request_spec import (
    _require_sha256_hex,
    _require_text,
    _stable_hash,
    write_json_mapping,
)
from alpha_system.data.databento.submit_batch import (
    JobsManifest,
    SubmittedDatabentoJob,
    load_jobs_manifest,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError

DOWNLOAD_MANIFEST_SCHEMA = "alpha_system.databento.download_manifest.v1"
_SAFE_PATH_SEGMENT = re.compile(r"^[A-Za-z0-9._-]+$")


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _safe_path_segment(value: object, field_name: str) -> str:
    segment = _require_text(value, field_name)
    if (
        segment in {".", ".."}
        or ".." in segment
        or "/" in segment
        or "\\" in segment
        or _SAFE_PATH_SEGMENT.fullmatch(segment) is None
    ):
        msg = (
            f"{field_name} must be a single safe path segment using only letters, "
            "digits, '.', '_', and '-'"
        )
        raise DataFoundationValidationError(msg)
    return segment


def _dataset_path_segment(dataset: str) -> str:
    return _safe_path_segment(dataset, "dataset").lower().replace(".", "_")


def _validate_output_root(output_root: Path, env: Mapping[str, str] | None) -> Path:
    source = os.environ if env is None else env
    data_root_value = source.get("ALPHA_DATA_ROOT")
    if data_root_value is None or not data_root_value.strip():
        msg = "ALPHA_DATA_ROOT is required for Databento batch downloads"
        raise DataFoundationValidationError(msg)
    data_root = _validate_raw_root(Path(data_root_value))
    resolved = _validate_raw_root(output_root)
    if resolved != data_root and not _is_relative_to(resolved, data_root):
        msg = "output_root must resolve under ALPHA_DATA_ROOT"
        raise DataFoundationValidationError(msg)
    return resolved


def _download_output_dir(
    *,
    output_root: Path,
    manifest: JobsManifest,
    job: SubmittedDatabentoJob,
) -> Path:
    return (
        output_root
        / "raw"
        / _dataset_path_segment(manifest.dataset)
        / _safe_path_segment(manifest.stype_in, "stype_in")
        / _safe_path_segment(job.schema, "schema")
        / _safe_path_segment(job.job_id, "job_id")
    )


def _validated_download_output_dir(
    *,
    output_root: Path,
    manifest: JobsManifest,
    job: SubmittedDatabentoJob,
) -> Path:
    output_dir = _download_output_dir(
        output_root=output_root,
        manifest=manifest,
        job=job,
    ).resolve(strict=False)
    if output_dir == output_root or not _is_relative_to(output_dir, output_root):
        msg = "download output_dir must resolve strictly under output_root"
        raise DataFoundationValidationError(msg)
    return output_dir


def _job_state(batch: object, job_id: str) -> str:
    list_jobs = getattr(batch, "list_jobs", None)
    if not callable(list_jobs):
        msg = "Databento client must expose batch.list_jobs"
        raise DataFoundationValidationError(msg)
    jobs = list_jobs(states="queued,processing,done", since=None)
    if not isinstance(jobs, Sequence):
        msg = "Databento batch.list_jobs must return a sequence"
        raise DataFoundationValidationError(msg)
    for job in jobs:
        if not isinstance(job, Mapping):
            continue
        if str(job.get("id", "")) == job_id:
            return _require_text(job.get("state"), "job state").lower()
    msg = f"Databento batch job {job_id!r} was not found in queued, processing, or done states"
    raise DataFoundationValidationError(msg)


@dataclass(frozen=True, slots=True, kw_only=True)
class DownloadedDatabentoFile:
    job_id: str
    schema: str
    path: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "job_id", _require_text(self.job_id, "job_id"))
        object.__setattr__(self, "schema", _require_text(self.schema, "schema"))
        object.__setattr__(self, "path", _require_text(self.path, "path"))

    def to_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "job_id": self.job_id,
                "schema": self.schema,
                "path": self.path,
            }
        )


def _normalize_downloaded_files(value: object) -> tuple[DownloadedDatabentoFile, ...]:
    if isinstance(value, Mapping) or not isinstance(value, Sequence):
        msg = "downloaded_files must be a sequence of file records"
        raise DataFoundationValidationError(msg)
    files: list[DownloadedDatabentoFile] = []
    for item in value:
        if isinstance(item, DownloadedDatabentoFile):
            files.append(item)
            continue
        if not isinstance(item, Mapping):
            msg = "downloaded_files entries must be file records"
            raise DataFoundationValidationError(msg)
        files.append(
            DownloadedDatabentoFile(
                job_id=item["job_id"],
                schema=item["schema"],
                path=item["path"],
            )
        )
    return tuple(files)


def compute_download_manifest_hash(
    *,
    jobs_manifest_hash: str,
    output_root: str,
    downloaded_files: Sequence[DownloadedDatabentoFile],
) -> str:
    return _stable_hash(
        {
            "schema": DOWNLOAD_MANIFEST_SCHEMA,
            "jobs_manifest_hash": _require_sha256_hex(
                jobs_manifest_hash,
                "jobs_manifest_hash",
            ),
            "output_root": _require_text(output_root, "output_root"),
            "downloaded_files": tuple(file.to_mapping() for file in downloaded_files),
        }
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class DownloadManifest:
    """Local record of files returned by Databento batch downloads."""

    jobs_manifest_hash: str
    output_root: str
    downloaded_files: tuple[DownloadedDatabentoFile, ...]
    downloaded_at: datetime
    manifest_hash: str | None = None

    def __post_init__(self) -> None:
        jobs_hash = _require_sha256_hex(self.jobs_manifest_hash, "jobs_manifest_hash")
        output_root = _require_text(self.output_root, "output_root")
        downloaded_files = _normalize_downloaded_files(self.downloaded_files)
        downloaded_at = self.downloaded_at
        if downloaded_at.tzinfo is None or downloaded_at.utcoffset() is None:
            msg = "downloaded_at must be timezone-aware"
            raise DataFoundationValidationError(msg)
        computed_hash = compute_download_manifest_hash(
            jobs_manifest_hash=jobs_hash,
            output_root=output_root,
            downloaded_files=downloaded_files,
        )
        if self.manifest_hash is not None:
            supplied_hash = _require_sha256_hex(self.manifest_hash, "manifest_hash")
            if supplied_hash != computed_hash:
                msg = "manifest_hash does not match download manifest content"
                raise DataFoundationValidationError(msg)

        object.__setattr__(self, "jobs_manifest_hash", jobs_hash)
        object.__setattr__(self, "output_root", output_root)
        object.__setattr__(self, "downloaded_files", downloaded_files)
        object.__setattr__(self, "manifest_hash", computed_hash)

    def to_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "schema": DOWNLOAD_MANIFEST_SCHEMA,
                "jobs_manifest_hash": self.jobs_manifest_hash,
                "output_root": self.output_root,
                "downloaded_files": tuple(file.to_mapping() for file in self.downloaded_files),
                "downloaded_at": self.downloaded_at.isoformat(),
                "manifest_hash": self.manifest_hash,
            }
        )


def run_download_batch(
    *,
    jobs_manifest_path: Path,
    output_root: Path,
    client: object | None = None,
    env: Mapping[str, str] | None = None,
    now: datetime | None = None,
) -> DownloadManifest:
    """Download done Databento batch jobs into the local raw data root."""

    manifest = load_jobs_manifest(jobs_manifest_path)
    resolved_output_root = _validate_output_root(output_root, env)
    downloaded: list[DownloadedDatabentoFile] = []

    with _historical_client_context(client=client, env=env, require_raw_write=True) as db_client:
        batch = getattr(db_client, "batch", None)
        download = getattr(batch, "download", None)
        if not callable(download):
            msg = "Databento client must expose batch.download"
            raise DataFoundationValidationError(msg)

        for job in manifest.jobs:
            state = _job_state(batch, job.job_id)
            if state != "done":
                msg = f"Databento batch job {job.job_id!r} is not done; current state: {state}"
                raise DataFoundationValidationError(msg)
            output_dir = _validated_download_output_dir(
                output_root=resolved_output_root,
                manifest=manifest,
                job=job,
            )
            output_dir.mkdir(parents=True, exist_ok=True)
            paths = download(job.job_id, output_dir=output_dir)
            if not isinstance(paths, Sequence):
                msg = "Databento batch.download must return a sequence of paths"
                raise DataFoundationValidationError(msg)
            for path_value in paths:
                path = Path(path_value).expanduser().resolve(strict=False)
                if not _is_relative_to(path, resolved_output_root):
                    msg = "downloaded file path escaped output_root"
                    raise DataFoundationValidationError(msg)
                downloaded.append(
                    DownloadedDatabentoFile(
                        job_id=job.job_id,
                        schema=job.schema,
                        path=path.as_posix(),
                    )
                )

    return DownloadManifest(
        jobs_manifest_hash=manifest.manifest_hash,
        output_root=resolved_output_root.as_posix(),
        downloaded_files=tuple(downloaded),
        downloaded_at=now or datetime.now(UTC),
    )


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download done Databento batch jobs into local raw storage",
    )
    parser.add_argument("--jobs-manifest", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--download-manifest", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI for ``python -m alpha_system.data.databento.download_batch``."""

    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        manifest = run_download_batch(
            jobs_manifest_path=args.jobs_manifest,
            output_root=args.output_root,
            env=os.environ,
        )
        if args.download_manifest is not None:
            write_json_mapping(args.download_manifest, manifest.to_mapping())
    except DataFoundationValidationError as exc:
        print(f"download_batch blocked: {exc}", file=sys.stderr)
        return 2
    return 0


__all__ = [
    "DOWNLOAD_MANIFEST_SCHEMA",
    "DownloadManifest",
    "DownloadedDatabentoFile",
    "compute_download_manifest_hash",
    "run_download_batch",
]


if __name__ == "__main__":
    raise SystemExit(main())
