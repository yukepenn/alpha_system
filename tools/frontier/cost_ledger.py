"""Append-only cost ledger helper."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def append(run_id: str, provider: str, model: str, estimated_usd: float) -> int:
    path = ROOT / "runs" / run_id / "costs.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(UTC).isoformat(),
        "provider": provider,
        "model": model,
        "estimated_usd": estimated_usd,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")
    print(f"Appended cost estimate to {path.relative_to(ROOT)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Append a Frontier cost ledger entry.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--estimated-usd", type=float, required=True)
    args = parser.parse_args(argv)
    return append(args.run_id, args.provider, args.model, args.estimated_usd)


if __name__ == "__main__":
    raise SystemExit(main())
