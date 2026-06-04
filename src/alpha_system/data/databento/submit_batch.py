"""Databento paid batch submission guarded by prior cost proof."""

from __future__ import annotations

import argparse
import math
import os
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import MappingProxyType

from alpha_system.data.databento.cost_check import (
    CostManifest,
    _coerce_request_spec,
    _historical_client_context,
    load_cost_manifest,
)
from alpha_system.data.databento.request_spec import (
    DATABENTO_ALLOWED_SCHEMAS,
    DatabentoRequestSpec,
    _require_sha256_hex,
    _require_text,
    _stable_hash,
    load_json_mapping,
    request_spec_hash,
    write_json_mapping,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError

JOBS_MANIFEST_SCHEMA = "alpha_system.databento.jobs_manifest.v1"
STYPE_OUT_INSTRUMENT_ID = "instrument_id"
DATABENTO_SUBMIT_HARD_CAP_USD = 110.0
DATABENTO_COST_MANIFEST_MAX_AGE = timedelta(hours=24)


def _normalize_job_id(value: object) -> str:
    job_id = _require_text(value, "job_id")
    if "/" in job_id or "\\" in job_id or job_id in {".", ".."}:
        msg = "job_id must be a single safe path segment"
        raise DataFoundationValidationError(msg)
    return job_id


def _normalize_job_records(value: object) -> tuple[SubmittedDatabentoJob, ...]:
    if isinstance(value, Mapping) or not isinstance(value, Sequence):
        msg = "jobs must be a non-empty sequence of job records"
        raise DataFoundationValidationError(msg)
    jobs = tuple(
        item
        if isinstance(item, SubmittedDatabentoJob)
        else SubmittedDatabentoJob.from_mapping(item)
        for item in value
    )
    if not jobs:
        msg = "jobs must not be empty"
        raise DataFoundationValidationError(msg)
    job_ids = [job.job_id for job in jobs]
    duplicates = sorted(job_id for job_id in set(job_ids) if job_ids.count(job_id) > 1)
    if duplicates:
        msg = "jobs contains duplicate job ids: " + ", ".join(duplicates)
        raise DataFoundationValidationError(msg)
    return jobs


def _normalize_text_tuple(value: object, field_name: str) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        msg = f"{field_name} must be a non-empty sequence of strings"
        raise DataFoundationValidationError(msg)
    normalized = tuple(_require_text(item, field_name) for item in value)
    if not normalized:
        msg = f"{field_name} must not be empty"
        raise DataFoundationValidationError(msg)
    return normalized


def _parse_submitted_at(value: object) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        raw = _require_text(value, "submitted_at")
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as exc:
            msg = "submitted_at must be an ISO-8601 timezone-aware datetime"
            raise DataFoundationValidationError(msg) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        msg = "submitted_at must be timezone-aware"
        raise DataFoundationValidationError(msg)
    return parsed


def compute_jobs_manifest_hash(
    *,
    request_spec_digest: str,
    jobs: Sequence[SubmittedDatabentoJob],
    dataset: str,
    symbols: Sequence[str],
    stype_in: str,
    start: str,
    end: str,
    encoding: str,
    compression: str,
) -> str:
    return _stable_hash(
        {
            "schema": JOBS_MANIFEST_SCHEMA,
            "request_spec_hash": _require_sha256_hex(
                request_spec_digest,
                "request_spec_hash",
            ),
            "jobs": tuple(job.to_mapping() for job in _normalize_job_records(jobs)),
            "dataset": _require_text(dataset, "dataset"),
            "symbols": _normalize_text_tuple(symbols, "symbols"),
            "stype_in": _require_text(stype_in, "stype_in"),
            "start": _require_text(start, "start"),
            "end": _require_text(end, "end"),
            "encoding": _require_text(encoding, "encoding"),
            "compression": _require_text(compression, "compression"),
        }
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class SubmittedDatabentoJob:
    """One Databento batch job id returned for one schema."""

    job_id: str
    schema: str

    def __post_init__(self) -> None:
        schema = _require_text(self.schema, "schema")
        if schema not in DATABENTO_ALLOWED_SCHEMAS:
            allowed = ", ".join(DATABENTO_ALLOWED_SCHEMAS)
            msg = f"schema must be one of {allowed}"
            raise DataFoundationValidationError(msg)
        object.__setattr__(self, "job_id", _normalize_job_id(self.job_id))
        object.__setattr__(self, "schema", schema)

    @classmethod
    def from_mapping(cls, values: object) -> SubmittedDatabentoJob:
        if not isinstance(values, Mapping):
            msg = "job record must be a mapping"
            raise DataFoundationValidationError(msg)
        missing = tuple(field for field in ("job_id", "schema") if field not in values)
        if missing:
            msg = "SubmittedDatabentoJob missing required fields: " + ", ".join(missing)
            raise DataFoundationValidationError(msg)
        return cls(job_id=values["job_id"], schema=values["schema"])

    def to_mapping(self) -> Mapping[str, object]:
        return MappingProxyType({"job_id": self.job_id, "schema": self.schema})


@dataclass(frozen=True, slots=True, kw_only=True)
class JobsManifest:
    """Manifest of paid Databento batch job ids."""

    request_spec_hash: str
    jobs: tuple[SubmittedDatabentoJob, ...]
    dataset: str
    symbols: tuple[str, ...]
    stype_in: str
    start: str
    end: str
    encoding: str
    compression: str
    submitted_at: datetime
    manifest_hash: str | None = None

    def __post_init__(self) -> None:
        request_digest = _require_sha256_hex(self.request_spec_hash, "request_spec_hash")
        jobs = _normalize_job_records(self.jobs)
        dataset = _require_text(self.dataset, "dataset")
        symbols = _normalize_text_tuple(self.symbols, "symbols")
        stype_in = _require_text(self.stype_in, "stype_in")
        start = _require_text(self.start, "start")
        end = _require_text(self.end, "end")
        encoding = _require_text(self.encoding, "encoding")
        compression = _require_text(self.compression, "compression")
        submitted_at = _parse_submitted_at(self.submitted_at)
        computed_hash = compute_jobs_manifest_hash(
            request_spec_digest=request_digest,
            jobs=jobs,
            dataset=dataset,
            symbols=symbols,
            stype_in=stype_in,
            start=start,
            end=end,
            encoding=encoding,
            compression=compression,
        )
        if self.manifest_hash is not None:
            supplied_hash = _require_sha256_hex(self.manifest_hash, "manifest_hash")
            if supplied_hash != computed_hash:
                msg = "manifest_hash does not match jobs manifest content"
                raise DataFoundationValidationError(msg)

        object.__setattr__(self, "request_spec_hash", request_digest)
        object.__setattr__(self, "jobs", jobs)
        object.__setattr__(self, "dataset", dataset)
        object.__setattr__(self, "symbols", symbols)
        object.__setattr__(self, "stype_in", stype_in)
        object.__setattr__(self, "start", start)
        object.__setattr__(self, "end", end)
        object.__setattr__(self, "encoding", encoding)
        object.__setattr__(self, "compression", compression)
        object.__setattr__(self, "submitted_at", submitted_at)
        object.__setattr__(self, "manifest_hash", computed_hash)

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> JobsManifest:
        if values.get("schema") != JOBS_MANIFEST_SCHEMA:
            msg = f"jobs manifest schema must be {JOBS_MANIFEST_SCHEMA}"
            raise DataFoundationValidationError(msg)
        required = (
            "request_spec_hash",
            "jobs",
            "dataset",
            "symbols",
            "stype_in",
            "start",
            "end",
            "encoding",
            "compression",
            "submitted_at",
            "manifest_hash",
        )
        missing = tuple(field for field in required if field not in values)
        if missing:
            msg = "JobsManifest missing required fields: " + ", ".join(missing)
            raise DataFoundationValidationError(msg)
        return cls(
            request_spec_hash=values["request_spec_hash"],
            jobs=_normalize_job_records(values["jobs"]),
            dataset=values["dataset"],
            symbols=values["symbols"],
            stype_in=values["stype_in"],
            start=values["start"],
            end=values["end"],
            encoding=values["encoding"],
            compression=values["compression"],
            submitted_at=values["submitted_at"],
            manifest_hash=values["manifest_hash"],
        )

    def to_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "schema": JOBS_MANIFEST_SCHEMA,
                "request_spec_hash": self.request_spec_hash,
                "jobs": tuple(job.to_mapping() for job in self.jobs),
                "dataset": self.dataset,
                "symbols": self.symbols,
                "stype_in": self.stype_in,
                "start": self.start,
                "end": self.end,
                "encoding": self.encoding,
                "compression": self.compression,
                "submitted_at": self.submitted_at.isoformat(),
                "manifest_hash": self.manifest_hash,
            }
        )


def load_jobs_manifest(path: Path) -> JobsManifest:
    return JobsManifest.from_mapping(load_json_mapping(path))


def write_jobs_manifest(manifest: JobsManifest, output_path: Path) -> Path:
    return write_json_mapping(output_path, manifest.to_mapping())


def _default_jobs_manifest_path(cost_manifest_path: Path) -> Path:
    suffix = cost_manifest_path.suffix
    if suffix:
        return cost_manifest_path.with_suffix(f".jobs{suffix}")
    return cost_manifest_path.with_name(f"{cost_manifest_path.name}.jobs.json")


def _normalize_submit_hard_cap(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        msg = "submit_hard_cap_usd must be a non-negative finite USD number"
        raise DataFoundationValidationError(msg)
    cap = float(value)
    if not math.isfinite(cap) or cap < 0:
        msg = "submit_hard_cap_usd must be a non-negative finite USD number"
        raise DataFoundationValidationError(msg)
    if cap > DATABENTO_SUBMIT_HARD_CAP_USD:
        msg = "submit_hard_cap_usd must not exceed DATABENTO_SUBMIT_HARD_CAP_USD"
        raise DataFoundationValidationError(msg)
    return round(cap, 6)


def _require_aware_datetime(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        msg = f"{field_name} must be timezone-aware"
        raise DataFoundationValidationError(msg)
    return value


def _require_cost_manifest_fresh(
    *,
    cost_manifest: CostManifest,
    now: datetime,
    max_age: timedelta,
) -> None:
    if not isinstance(max_age, timedelta) or max_age.total_seconds() < 0:
        msg = "cost_manifest_max_age must be a non-negative timedelta"
        raise DataFoundationValidationError(msg)
    current = _require_aware_datetime(now, "now").astimezone(UTC)
    created_at = cost_manifest.created_at.astimezone(UTC)
    if current - created_at > max_age:
        msg = "cost manifest is stale; re-run cost_check before submitting"
        raise DataFoundationValidationError(msg)


def _require_submit_cost_proof(
    *,
    request_spec: DatabentoRequestSpec,
    cost_manifest: CostManifest,
    now: datetime,
    submit_hard_cap_usd: float = DATABENTO_SUBMIT_HARD_CAP_USD,
    cost_manifest_max_age: timedelta = DATABENTO_COST_MANIFEST_MAX_AGE,
) -> None:
    submit_hard_cap = _normalize_submit_hard_cap(submit_hard_cap_usd)
    request_digest = request_spec_hash(request_spec)
    if cost_manifest.request_spec_hash != request_digest:
        msg = "cost manifest request_spec_hash does not match this request spec"
        raise DataFoundationValidationError(msg)
    if cost_manifest.under_budget is not True:
        msg = "cost manifest is not under budget; refusing paid Databento batch submit"
        raise DataFoundationValidationError(msg)
    if cost_manifest.total_usd > cost_manifest.max_cost_usd:
        msg = "cost manifest total exceeds max_cost_usd; refusing paid Databento batch submit"
        raise DataFoundationValidationError(msg)
    if cost_manifest.total_usd > submit_hard_cap:
        msg = "cost manifest total_usd exceeds Databento submit hard cap"
        raise DataFoundationValidationError(msg)
    if cost_manifest.max_cost_usd > submit_hard_cap:
        msg = "cost manifest max_cost_usd exceeds Databento submit hard cap"
        raise DataFoundationValidationError(msg)
    _require_cost_manifest_fresh(
        cost_manifest=cost_manifest,
        now=now,
        max_age=cost_manifest_max_age,
    )


def run_submit_batch(
    *,
    request_spec: DatabentoRequestSpec | Mapping[str, object],
    cost_manifest_path: Path,
    client: object | None = None,
    env: Mapping[str, str] | None = None,
    output_path: Path | None = None,
    now: datetime | None = None,
    submit_hard_cap_usd: float = DATABENTO_SUBMIT_HARD_CAP_USD,
    cost_manifest_max_age: timedelta = DATABENTO_COST_MANIFEST_MAX_AGE,
) -> JobsManifest:
    """Submit one paid Databento batch job per schema after cost proof validation."""

    spec = _coerce_request_spec(request_spec)
    cost_manifest = load_cost_manifest(cost_manifest_path)
    submitted_at = now or datetime.now(UTC)
    _require_submit_cost_proof(
        request_spec=spec,
        cost_manifest=cost_manifest,
        now=submitted_at,
        submit_hard_cap_usd=submit_hard_cap_usd,
        cost_manifest_max_age=cost_manifest_max_age,
    )

    jobs: list[SubmittedDatabentoJob] = []
    with _historical_client_context(client=client, env=env, require_raw_write=True) as db_client:
        batch = getattr(db_client, "batch", None)
        submit_job = getattr(batch, "submit_job", None)
        if not callable(submit_job):
            msg = "Databento client must expose batch.submit_job"
            raise DataFoundationValidationError(msg)
        for schema in spec.schemas:
            job = submit_job(
                dataset=spec.dataset,
                symbols=list(spec.symbols),
                schema=schema,
                start=spec.start.isoformat(),
                end=spec.end.isoformat(),
                encoding=spec.encoding,
                compression=spec.compression,
                split_symbols=False,
                split_duration="day",
                delivery="download",
                stype_in=spec.stype_in,
                stype_out=STYPE_OUT_INSTRUMENT_ID,
            )
            if not isinstance(job, Mapping) or "id" not in job:
                msg = "Databento batch.submit_job must return a job mapping with id"
                raise DataFoundationValidationError(msg)
            jobs.append(SubmittedDatabentoJob(job_id=job["id"], schema=schema))

    manifest = JobsManifest(
        request_spec_hash=request_spec_hash(spec),
        jobs=tuple(jobs),
        dataset=spec.dataset,
        symbols=spec.symbols,
        stype_in=spec.stype_in,
        start=spec.start.isoformat(),
        end=spec.end.isoformat(),
        encoding=spec.encoding,
        compression=spec.compression,
        submitted_at=submitted_at,
    )
    write_jobs_manifest(manifest, output_path or _default_jobs_manifest_path(cost_manifest_path))
    return manifest


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Submit Databento batch jobs after validating a cost manifest",
    )
    parser.add_argument("--request-spec", type=Path, required=True)
    parser.add_argument("--cost-manifest", type=Path, required=True)
    parser.add_argument("--output", "-o", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI for ``python -m alpha_system.data.databento.submit_batch``."""

    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        spec = DatabentoRequestSpec.from_mapping(load_json_mapping(args.request_spec))
        run_submit_batch(
            request_spec=spec,
            cost_manifest_path=args.cost_manifest,
            env=os.environ,
            output_path=args.output,
        )
    except DataFoundationValidationError as exc:
        print(f"submit_batch blocked: {exc}", file=sys.stderr)
        return 2
    return 0


__all__ = [
    "DATABENTO_COST_MANIFEST_MAX_AGE",
    "DATABENTO_SUBMIT_HARD_CAP_USD",
    "JOBS_MANIFEST_SCHEMA",
    "STYPE_OUT_INSTRUMENT_ID",
    "JobsManifest",
    "SubmittedDatabentoJob",
    "compute_jobs_manifest_hash",
    "load_jobs_manifest",
    "run_submit_batch",
    "write_jobs_manifest",
]


if __name__ == "__main__":
    raise SystemExit(main())
