"""Thin operator CLI for gated read-only IBKR historical backfills."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from types import MappingProxyType

from alpha_system.data.foundation.ibkr import IBKRClientIdPolicy, IBKRConnectionProfile
from alpha_system.data.foundation.requests import HistoricalRequestManifest, RequestPacingPolicy
from alpha_system.data.foundation.sources import DataAccessMode, DataFoundationValidationError
from alpha_system.data.ibkr.backfill import run_local_backfill_resume_drill
from alpha_system.data.ibkr.connector import open_ibkr_historical_boundary
from alpha_system.data.ibkr.pull import ReachabilityProbe, probe_ibkr_host_port

DEFAULT_BACKFILL_PACING_POLICY_PATH = (
    Path(__file__).resolve(strict=False).parents[4]
    / "configs"
    / "data"
    / "request_pacing_policy_to_be_verified.json"
)


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Live read-only IBKR historical resumable backfill connector",
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument(
        "--pacing-policy",
        type=Path,
        default=DEFAULT_BACKFILL_PACING_POLICY_PATH,
    )
    parser.add_argument("--batch", default="ibkr_resumable_backfill")
    parser.add_argument("--max-chunks", type=int)
    return parser.parse_args(argv)


def _require_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if isinstance(value, str) or not isinstance(value, Mapping):
        msg = f"{field_name} must be a JSON object"
        raise DataFoundationValidationError(msg)
    return value


def _load_json_mapping(path: Path) -> Mapping[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        msg = f"could not load JSON config: {path.as_posix()}"
        raise DataFoundationValidationError(msg) from exc
    return _require_mapping(payload, path.as_posix())


def _load_manifest(path: Path) -> HistoricalRequestManifest:
    return HistoricalRequestManifest.from_mapping(_load_json_mapping(path))


def _load_pacing_policy(path: Path) -> RequestPacingPolicy:
    return RequestPacingPolicy.from_mapping(_load_json_mapping(path))


def _json_ready(value: object) -> object:
    if isinstance(value, Mapping | MappingProxyType):
        return {str(key): _json_ready(nested) for key, nested in value.items()}
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    if hasattr(value, "value") and isinstance(value.value, str):
        return value.value
    if value is None or isinstance(value, bool | int | float | str):
        return value
    msg = f"value {value!r} is not JSON-stable"
    raise DataFoundationValidationError(msg)


def _print_summary(summary: object) -> None:
    payload = summary.to_mapping() if hasattr(summary, "to_mapping") else summary
    print(json.dumps(_json_ready(payload), indent=2, sort_keys=True))


def _connection_doctor_blocked_message(
    profile: IBKRConnectionProfile,
    failure_reason: str | None,
) -> str:
    reason = failure_reason or "unreachable"
    return (
        "IBKR read-only backfill connector blocked: connection doctor could not reach "
        f"{profile.host}:{profile.port} ({reason}). Set ALPHA_IBKR_HOST to a "
        "Windows-reachable address or enable WSL2 mirrored networking; host/port are "
        "NOT changed automatically."
    )


def main(
    argv: Sequence[str] | None = None,
    *,
    reachability_probe: ReachabilityProbe | None = None,
) -> int:
    """Run the gated read-only IBKR resumable backfill connector."""

    args = _parse_args(sys.argv[1:] if argv is None else argv)
    profile: IBKRConnectionProfile | None = None
    probe = reachability_probe or probe_ibkr_host_port
    try:
        profile = IBKRConnectionProfile.from_env(os.environ)
        IBKRClientIdPolicy.default().validate_client_id(profile.client_id)
        access_mode = DataAccessMode.authorized_pull()
        access_mode.validate_runtime_env(os.environ, ci=None)

        manifest = _load_manifest(args.manifest)
        pacing_policy = _load_pacing_policy(args.pacing_policy)
        max_chunks = args.max_chunks if args.max_chunks is not None else manifest.chunk_count

        doctor = probe(profile)
        if not doctor.reachable:
            print(
                _connection_doctor_blocked_message(profile, doctor.failure_reason),
                file=sys.stderr,
            )
            return 2

        with open_ibkr_historical_boundary(
            profile,
            access_mode,
            env=os.environ,
        ) as boundary:
            summary = run_local_backfill_resume_drill(
                boundary=boundary,
                manifest=manifest,
                pacing_policy=pacing_policy,
                access_mode=access_mode,
                env=os.environ,
                ci=None,
                execute=True,
                max_chunks=max_chunks,
                interrupt_after_chunks=manifest.chunk_count,
                batch=args.batch,
                reachability_probe=probe,
            )
    except OSError as exc:
        if profile is None:
            print(f"IBKR read-only backfill connector blocked: {exc}", file=sys.stderr)
        else:
            print(
                _connection_doctor_blocked_message(
                    profile,
                    f"{type(exc).__name__}: {exc}",
                ),
                file=sys.stderr,
            )
        return 2
    except (DataFoundationValidationError, ImportError) as exc:
        print(f"IBKR read-only backfill connector blocked: {exc}", file=sys.stderr)
        return 2

    _print_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
