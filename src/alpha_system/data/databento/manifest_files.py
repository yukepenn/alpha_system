"""Immutable Databento raw file manifest with file hashes and sizes."""

from __future__ import annotations

import argparse
import hashlib
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType

from alpha_system.core.registry import is_local_only_registry_path
from alpha_system.data.databento.request_spec import (
    DATABENTO_ALLOWED_SCHEMAS,
    _require_sha256_hex,
    _require_text,
    _stable_hash,
    load_json_mapping,
    write_json_mapping,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.data.ibkr.materialize import _repo_root, _validate_data_root

FILE_MANIFEST_SCHEMA = "alpha_system.databento.file_manifest.v1"
_DATABENTO_RAW_SUFFIXES = (".dbn.zst", ".dbn.zstd")


def _validate_raw_root(raw_root: Path) -> Path:
    resolved = _validate_data_root(raw_root, _repo_root())
    local_probe = resolved / "databento_file_manifest.sqlite"
    if not is_local_only_registry_path(local_probe):
        msg = f"raw_root is not local-only: {resolved.as_posix()}"
        raise DataFoundationValidationError(msg)
    return resolved


def _is_databento_raw_file(path: Path) -> bool:
    name = path.name.lower()
    return any(name.endswith(suffix) for suffix in _DATABENTO_RAW_SUFFIXES)


def _infer_schema_and_job(relative_path: Path) -> tuple[str, str]:
    parts = relative_path.parts
    for index, part in enumerate(parts):
        if part in DATABENTO_ALLOWED_SCHEMAS:
            if index + 1 >= len(parts):
                msg = f"raw file path lacks job id after schema: {relative_path.as_posix()}"
                raise DataFoundationValidationError(msg)
            return part, _require_text(parts[index + 1], "job_id")
    msg = f"raw file path lacks an allowed Databento schema segment: {relative_path.as_posix()}"
    raise DataFoundationValidationError(msg)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalize_size(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        msg = "size_bytes must be a non-negative integer"
        raise DataFoundationValidationError(msg)
    return value


def _normalize_file_records(value: object) -> tuple[DatabentoFileRecord, ...]:
    if isinstance(value, Mapping) or not isinstance(value, Sequence):
        msg = "files must be a sequence of file records"
        raise DataFoundationValidationError(msg)
    return tuple(
        item if isinstance(item, DatabentoFileRecord) else DatabentoFileRecord.from_mapping(item)
        for item in value
    )


def compute_file_manifest_hash(
    *,
    raw_root: str,
    files: Sequence[DatabentoFileRecord],
) -> str:
    return _stable_hash(
        {
            "schema": FILE_MANIFEST_SCHEMA,
            "raw_root": _require_text(raw_root, "raw_root"),
            "files": tuple(file.to_mapping() for file in _normalize_file_records(files)),
        }
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class DatabentoFileRecord:
    """One hashed Databento raw DBN/Zstd file."""

    relative_path: str
    schema: str
    job_id: str
    sha256: str
    size_bytes: int

    def __post_init__(self) -> None:
        schema = _require_text(self.schema, "schema")
        if schema not in DATABENTO_ALLOWED_SCHEMAS:
            allowed = ", ".join(DATABENTO_ALLOWED_SCHEMAS)
            msg = f"schema must be one of {allowed}"
            raise DataFoundationValidationError(msg)
        object.__setattr__(
            self,
            "relative_path",
            _require_text(self.relative_path, "relative_path"),
        )
        object.__setattr__(self, "schema", schema)
        object.__setattr__(self, "job_id", _require_text(self.job_id, "job_id"))
        object.__setattr__(self, "sha256", _require_sha256_hex(self.sha256, "sha256"))
        object.__setattr__(self, "size_bytes", _normalize_size(self.size_bytes))

    @classmethod
    def from_mapping(cls, values: object) -> DatabentoFileRecord:
        if not isinstance(values, Mapping):
            msg = "file record must be a mapping"
            raise DataFoundationValidationError(msg)
        required = ("relative_path", "schema", "job_id", "sha256", "size_bytes")
        missing = tuple(field for field in required if field not in values)
        if missing:
            msg = "DatabentoFileRecord missing required fields: " + ", ".join(missing)
            raise DataFoundationValidationError(msg)
        return cls(
            relative_path=values["relative_path"],
            schema=values["schema"],
            job_id=values["job_id"],
            sha256=values["sha256"],
            size_bytes=values["size_bytes"],
        )

    def to_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "relative_path": self.relative_path,
                "schema": self.schema,
                "job_id": self.job_id,
                "sha256": self.sha256,
                "size_bytes": self.size_bytes,
            }
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class DatabentoFileManifest:
    """Immutable manifest over downloaded Databento DBN/Zstd files."""

    raw_root: str
    files: tuple[DatabentoFileRecord, ...]
    file_count: int
    total_bytes: int
    created_at: datetime
    manifest_hash: str | None = None

    def __post_init__(self) -> None:
        raw_root = _require_text(self.raw_root, "raw_root")
        files = _normalize_file_records(self.files)
        file_count = _normalize_size(self.file_count)
        total_bytes = _normalize_size(self.total_bytes)
        created_at = self.created_at
        if created_at.tzinfo is None or created_at.utcoffset() is None:
            msg = "created_at must be timezone-aware"
            raise DataFoundationValidationError(msg)
        if file_count != len(files):
            msg = "file_count must equal len(files)"
            raise DataFoundationValidationError(msg)
        if total_bytes != sum(file.size_bytes for file in files):
            msg = "total_bytes must equal the sum of file sizes"
            raise DataFoundationValidationError(msg)
        computed_hash = compute_file_manifest_hash(raw_root=raw_root, files=files)
        if self.manifest_hash is not None:
            supplied_hash = _require_sha256_hex(self.manifest_hash, "manifest_hash")
            if supplied_hash != computed_hash:
                msg = "manifest_hash does not match Databento file manifest content"
                raise DataFoundationValidationError(msg)

        object.__setattr__(self, "raw_root", raw_root)
        object.__setattr__(self, "files", files)
        object.__setattr__(self, "file_count", file_count)
        object.__setattr__(self, "total_bytes", total_bytes)
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "manifest_hash", computed_hash)

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> DatabentoFileManifest:
        if values.get("schema") != FILE_MANIFEST_SCHEMA:
            msg = f"file manifest schema must be {FILE_MANIFEST_SCHEMA}"
            raise DataFoundationValidationError(msg)
        required = (
            "raw_root",
            "files",
            "file_count",
            "total_bytes",
            "created_at",
            "manifest_hash",
        )
        missing = tuple(field for field in required if field not in values)
        if missing:
            msg = "DatabentoFileManifest missing required fields: " + ", ".join(missing)
            raise DataFoundationValidationError(msg)
        created_at = values["created_at"]
        if not isinstance(created_at, datetime):
            raw_created_at = _require_text(created_at, "created_at")
            try:
                created_at = datetime.fromisoformat(raw_created_at.replace("Z", "+00:00"))
            except ValueError as exc:
                msg = "created_at must be an ISO-8601 timezone-aware datetime"
                raise DataFoundationValidationError(msg) from exc
        return cls(
            raw_root=values["raw_root"],
            files=_normalize_file_records(values["files"]),
            file_count=values["file_count"],
            total_bytes=values["total_bytes"],
            created_at=created_at,
            manifest_hash=values["manifest_hash"],
        )

    def to_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "schema": FILE_MANIFEST_SCHEMA,
                "raw_root": self.raw_root,
                "files": tuple(file.to_mapping() for file in self.files),
                "file_count": self.file_count,
                "total_bytes": self.total_bytes,
                "created_at": self.created_at.isoformat(),
                "manifest_hash": self.manifest_hash,
            }
        )


def _build_file_manifest(raw_root: Path, *, now: datetime | None = None) -> DatabentoFileManifest:
    records: list[DatabentoFileRecord] = []
    for path in sorted(path for path in raw_root.rglob("*") if path.is_file()):
        if not _is_databento_raw_file(path):
            continue
        relative = path.relative_to(raw_root)
        schema, job_id = _infer_schema_and_job(relative)
        records.append(
            DatabentoFileRecord(
                relative_path=relative.as_posix(),
                schema=schema,
                job_id=job_id,
                sha256=_file_sha256(path),
                size_bytes=path.stat().st_size,
            )
        )

    return DatabentoFileManifest(
        raw_root=raw_root.as_posix(),
        files=tuple(records),
        file_count=len(records),
        total_bytes=sum(record.size_bytes for record in records),
        created_at=now or datetime.now(UTC),
    )


def run_manifest_files(
    *,
    raw_root: Path,
    output_path: Path,
    now: datetime | None = None,
) -> DatabentoFileManifest:
    """Hash downloaded Databento raw files and write an immutable manifest."""

    resolved_raw_root = _validate_raw_root(raw_root)
    manifest = _build_file_manifest(resolved_raw_root, now=now)
    if output_path.exists():
        existing = DatabentoFileManifest.from_mapping(load_json_mapping(output_path))
        if existing.manifest_hash != manifest.manifest_hash:
            msg = "existing Databento file manifest has different content; refusing overwrite"
            raise DataFoundationValidationError(msg)
        return existing
    write_json_mapping(output_path, manifest.to_mapping())
    return manifest


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create an immutable Databento raw file hash manifest",
    )
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--output", "-o", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI for ``python -m alpha_system.data.databento.manifest_files``."""

    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        run_manifest_files(raw_root=args.raw_root, output_path=args.output)
    except DataFoundationValidationError as exc:
        print(f"manifest_files blocked: {exc}", file=sys.stderr)
        return 2
    return 0


__all__ = [
    "FILE_MANIFEST_SCHEMA",
    "DatabentoFileManifest",
    "DatabentoFileRecord",
    "compute_file_manifest_hash",
    "run_manifest_files",
]


if __name__ == "__main__":
    raise SystemExit(main())
