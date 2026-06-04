"""Thin operator CLI for the optional live read-only IBKR smoke connector."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence

from alpha_system.data.foundation.ibkr import IBKRConnectionProfile
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.data.ibkr._connection import (
    connection_doctor_blocked_message,
    gate_read_only_ibkr_access,
)
from alpha_system.data.ibkr._json_utils import json_ready_base as _json_ready
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


def _print_summary(summary: object) -> None:
    payload = summary.to_mapping() if hasattr(summary, "to_mapping") else summary
    print(json.dumps(_json_ready(payload), indent=2, sort_keys=True))


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
        profile, access_mode, doctor = gate_read_only_ibkr_access(
            os.environ,
            reachability_probe=probe,
        )
        if not doctor.reachable:
            print(
                connection_doctor_blocked_message(profile, doctor.failure_reason),
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
                connection_doctor_blocked_message(
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
