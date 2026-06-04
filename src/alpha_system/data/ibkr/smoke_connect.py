"""Thin operator CLI for the optional live read-only IBKR smoke connector."""

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
from alpha_system.data.foundation.sources import DataAccessMode, DataFoundationValidationError
from alpha_system.data.ibkr.connector import open_ibkr_historical_boundary
from alpha_system.data.ibkr.pull import (
    DEFAULT_SMOKE_BATCH_ID,
    ReachabilityProbe,
    probe_ibkr_host_port,
    run_ibkr_smoke_pull,
)


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Live read-only IBKR historical smoke connector",
    )
    parser.add_argument("--batch", default=DEFAULT_SMOKE_BATCH_ID)
    parser.add_argument("--max-chunks", type=int, default=1)
    return parser.parse_args(argv)


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
        "IBKR read-only smoke connector blocked: connection doctor could not reach "
        f"{profile.host}:{profile.port} ({reason}). Set ALPHA_IBKR_HOST to a "
        "Windows-reachable address or enable WSL2 mirrored networking; host/port are "
        "NOT changed automatically."
    )


def main(
    argv: Sequence[str] | None = None,
    *,
    reachability_probe: ReachabilityProbe | None = None,
) -> int:
    """Run the gated one-chunk live read-only IBKR smoke connector."""

    args = _parse_args(sys.argv[1:] if argv is None else argv)
    profile: IBKRConnectionProfile | None = None
    probe = reachability_probe or probe_ibkr_host_port
    try:
        profile = IBKRConnectionProfile.from_env(os.environ)
        IBKRClientIdPolicy.default().validate_client_id(profile.client_id)
        access_mode = DataAccessMode.authorized_pull()
        access_mode.validate_runtime_env(os.environ, ci=None)
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
            summary = run_ibkr_smoke_pull(
                boundary=boundary,
                execute=True,
                env=os.environ,
                ci=None,
                max_chunks=args.max_chunks,
                batch=args.batch,
                reachability_probe=probe,
                use_default_manifest=True,
                use_default_pacing_policy=True,
            )
    except OSError as exc:
        if profile is None:
            print(f"IBKR read-only smoke connector blocked: {exc}", file=sys.stderr)
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
        print(f"IBKR read-only smoke connector blocked: {exc}", file=sys.stderr)
        return 2

    _print_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
