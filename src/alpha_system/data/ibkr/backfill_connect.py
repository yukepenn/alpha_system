"""Thin operator CLI for gated read-only IBKR historical backfills."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from alpha_system.data.foundation.ibkr import IBKRConnectionProfile
from alpha_system.data.foundation.requests import HistoricalRequestManifest, RequestPacingPolicy
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.data.ibkr._connection import (
    connection_doctor_blocked_message,
    gate_read_only_ibkr_access,
)
from alpha_system.data.ibkr._json_utils import json_ready_base as _json_ready
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


def _print_summary(summary: object) -> None:
    payload = summary.to_mapping() if hasattr(summary, "to_mapping") else summary
    print(json.dumps(_json_ready(payload), indent=2, sort_keys=True))


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
        profile, access_mode, doctor = gate_read_only_ibkr_access(
            os.environ,
            reachability_probe=probe,
        )

        manifest = _load_manifest(args.manifest)
        pacing_policy = _load_pacing_policy(args.pacing_policy)
        max_chunks = args.max_chunks if args.max_chunks is not None else manifest.chunk_count

        if not doctor.reachable:
            print(
                connection_doctor_blocked_message(
                    profile,
                    doctor.failure_reason,
                    connector_name="backfill",
                ),
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
                connection_doctor_blocked_message(
                    profile,
                    f"{type(exc).__name__}: {exc}",
                    connector_name="backfill",
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
