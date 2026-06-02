"""Lifecycle-gated local-only factor materialization."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from alpha_system.core.git_info import capture_git_info
from alpha_system.core.hashing import canonical_json, hash_config
from alpha_system.core.registry import connect_registry, init_registry
from alpha_system.data.fixture_policy import FixturePolicyError, assert_registry_path_allowed
from alpha_system.factors.base import build_factor_from_spec
from alpha_system.factors.compute import COMPUTE_VERSION, compute_factor_values
from alpha_system.factors.io import (
    FactorStoreWrite,
    filter_bars,
    read_canonical_bars,
    write_run_manifest,
    write_factor_values,
)
from alpha_system.factors.lifecycle import (
    can_materialize_long_term,
    requires_recorded_validation_review,
    requires_review_backed_promotion,
)
from alpha_system.factors.registry import (
    has_review_backed_promotion,
    has_reviewed_validation,
)
from alpha_system.factors.spec import FactorSpec, compute_factor_config_hash
from alpha_system.factors.validation import load_factor_spec_config


class FactorMaterializationError(ValueError):
    """Raised when materialization is not permitted or cannot complete."""


@dataclass(frozen=True, slots=True)
class FactorMaterializationSummary:
    factor_id: str
    factor_version: str
    status: str
    data_version: str
    compute_version: str
    output_policy: str
    record_count: int
    persisted: bool
    value_path: str | None
    manifest_path: str | None
    registry_path: str | None
    registry_written: bool
    code_hash: str
    config_hash: str
    run_id: str
    quality_flag_counts: Mapping[str, int]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["quality_flag_counts"] = dict(self.quality_flag_counts)
        return payload


def materialize_factor_values(
    *,
    spec_path: str | Path,
    canonical_data_path: str | Path,
    data_version: str,
    output_policy: str = "dry-run",
    output_dir: str | Path | None = None,
    registry_path: str | Path | None = None,
    manifest_out: str | Path | None = None,
    compute_version: str = COMPUTE_VERSION,
    instrument_id: str | None = None,
    session_id: str | None = None,
    start_ts: str | datetime | None = None,
    end_ts: str | datetime | None = None,
) -> FactorMaterializationSummary:
    """Compute and optionally persist eligible factor values locally."""
    if output_policy not in {"dry-run", "local-only-persist"}:
        msg = "output_policy must be dry-run or local-only-persist"
        raise FactorMaterializationError(msg)

    payload = load_factor_spec_config(spec_path)
    spec = FactorSpec.from_mapping(payload)
    computed_config_hash = compute_factor_config_hash(payload)
    if computed_config_hash != spec.config_hash:
        msg = (
            "config_hash mismatch: "
            f"expected {spec.config_hash}, computed {computed_config_hash}"
        )
        raise FactorMaterializationError(msg)
    active_registry_path = _validated_registry_path(registry_path)
    _assert_lifecycle_allows_materialization(
        spec,
        output_policy=output_policy,
        registry_path=active_registry_path,
    )

    bars = filter_bars(
        read_canonical_bars(canonical_data_path),
        instrument_id=instrument_id,
        session_id=session_id,
        start_ts=start_ts,
        end_ts=end_ts,
    )
    factor = build_factor_from_spec(spec)
    values = compute_factor_values(
        spec,
        factor,
        bars,
        data_version=data_version,
        compute_version=compute_version,
    )
    run_id = _run_id(spec, data_version=data_version, compute_version=compute_version)
    manifest = _manifest_payload(
        spec=spec,
        data_version=data_version,
        compute_version=compute_version,
        output_policy=output_policy,
        run_id=run_id,
        values=values,
    )

    write_result: FactorStoreWrite | None = None
    manifest_path: Path | None = None
    if output_policy == "local-only-persist":
        write_result = write_factor_values(
            values,
            output_dir=output_dir,
            manifest=manifest,
            manifest_path=manifest_out,
        )
        manifest_path = write_result.manifest_path
    elif manifest_out is not None:
        manifest_path = write_run_manifest(manifest, manifest_out)

    registry_written = False
    if output_policy == "local-only-persist" and active_registry_path is not None:
        _record_registry_entry(
            active_registry_path,
            spec,
            run_id=run_id,
            data_version=data_version,
            compute_version=compute_version,
            output_paths={} if write_result is None else {
                "factor_values": write_result.values_path.as_posix(),
                "run_manifest": write_result.manifest_path.as_posix(),
            },
        )
        registry_written = True

    return FactorMaterializationSummary(
        factor_id=spec.factor_id,
        factor_version=spec.version,
        status=spec.status.value,
        data_version=data_version,
        compute_version=compute_version,
        output_policy=output_policy,
        record_count=len(values),
        persisted=output_policy == "local-only-persist",
        value_path=None if write_result is None else write_result.values_path.as_posix(),
        manifest_path=None if manifest_path is None else manifest_path.as_posix(),
        registry_path=None if active_registry_path is None else active_registry_path.as_posix(),
        registry_written=registry_written,
        code_hash=spec.code_hash,
        config_hash=spec.config_hash,
        run_id=run_id,
        quality_flag_counts=_quality_counts(values),
    )


def print_materialization_summary(
    summary: FactorMaterializationSummary,
    *,
    emit_json: bool = False,
) -> None:
    """Emit a stable materialization console summary."""
    if emit_json:
        print(json.dumps(summary.to_dict(), sort_keys=True, indent=2))
        return
    print("Factor command: materialize")
    print(f"Factor: {summary.factor_id}")
    print(f"Version: {summary.factor_version}")
    print(f"Status: {summary.status}")
    print(f"Output policy: {summary.output_policy}")
    print(f"Records: {summary.record_count}")
    print(f"Persisted: {'yes' if summary.persisted else 'no'}")
    if summary.value_path is not None:
        print(f"Values: {summary.value_path}")
    if summary.manifest_path is not None:
        print(f"Manifest: {summary.manifest_path}")
    if summary.registry_path is not None:
        print(f"Registry: {summary.registry_path}")
        print(f"Registry written: {'yes' if summary.registry_written else 'no'}")


def _assert_lifecycle_allows_materialization(
    spec: FactorSpec,
    *,
    output_policy: str,
    registry_path: Path | None,
) -> None:
    if output_policy != "local-only-persist":
        return
    if not can_materialize_long_term(spec.status):
        msg = f"{spec.status.value} factors cannot be materialized by default"
        raise FactorMaterializationError(msg)
    if requires_recorded_validation_review(spec.status):
        if registry_path is None or not has_reviewed_validation(registry_path, spec):
            msg = "materialization requires reviewed validation evidence in registry"
            raise FactorMaterializationError(msg)
    if requires_review_backed_promotion(spec.status):
        if registry_path is None or not has_review_backed_promotion(registry_path, spec):
            msg = "approved materialization requires review-backed promotion evidence"
            raise FactorMaterializationError(msg)


def _validated_registry_path(path: str | Path | None) -> Path | None:
    if path is None:
        return None
    try:
        return assert_registry_path_allowed(path)
    except FixturePolicyError as exc:
        raise FactorMaterializationError(str(exc)) from exc


def _record_registry_entry(
    registry_path: Path,
    spec: FactorSpec,
    *,
    run_id: str,
    data_version: str,
    compute_version: str,
    output_paths: Mapping[str, str],
) -> None:
    status = init_registry(registry_path)
    if not status.valid:
        msg = f"registry is not valid: {status.status_message}"
        raise FactorMaterializationError(msg)
    git_info = capture_git_info(Path.cwd())
    with connect_registry(registry_path) as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO factor_validation_runs (
                run_id,
                timestamp,
                git_commit,
                git_dirty,
                code_hash,
                config_hash,
                data_version,
                factor_versions_json,
                label_versions_json,
                engine_version,
                parameters_json,
                artifact_paths_json,
                decision_status,
                warnings_json,
                status_message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                _utc_now(),
                git_info.commit,
                None if git_info.dirty is None else int(git_info.dirty),
                spec.code_hash,
                spec.config_hash,
                data_version,
                canonical_json({spec.factor_id: spec.version}),
                "{}",
                compute_version,
                canonical_json(dict(spec.parameters)),
                canonical_json(dict(output_paths)),
                "materialized_local",
                "[]",
                "local-only factor materialization; no approval or promotion",
            ),
        )


def _manifest_payload(
    *,
    spec: FactorSpec,
    data_version: str,
    compute_version: str,
    output_policy: str,
    run_id: str,
    values: Sequence[Any],
) -> dict[str, Any]:
    return {
        "code_hash": spec.code_hash,
        "compute_version": compute_version,
        "config_hash": spec.config_hash,
        "data_version": data_version,
        "factor_id": spec.factor_id,
        "factor_version": spec.version,
        "output_policy": output_policy,
        "quality_flag_counts": dict(_quality_counts(values)),
        "record_count": len(values),
        "run_id": run_id,
        "status": spec.status.value,
    }


def _quality_counts(values: Sequence[Any]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for value in values:
        for flag in value.quality_flags:
            counts[flag] += 1
    return dict(counts)


def _run_id(spec: FactorSpec, *, data_version: str, compute_version: str) -> str:
    digest = hash_config(
        {
            "compute_version": compute_version,
            "config_hash": spec.config_hash,
            "data_version": data_version,
            "factor_id": spec.factor_id,
            "factor_version": spec.version,
        }
    )
    return f"factor-materialize:{spec.factor_id}:{spec.version}:{digest[:16]}"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
