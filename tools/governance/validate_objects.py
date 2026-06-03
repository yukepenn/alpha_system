"""Batch governance object validation helper."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from alpha_system.cli.governance import (  # noqa: E402
    governance_exception_payload,
    validate_alpha_spec_files,
    validate_governance_object_file,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python tools/governance/validate_objects.py",
        description="Validate local governance JSON objects through fail-closed validators.",
    )
    parser.add_argument(
        "--object",
        action="append",
        default=[],
        metavar="KIND:PATH",
        help="Validate one object file by canonical kind; repeat for multiple files.",
    )
    parser.add_argument(
        "--alpha-spec",
        help="AlphaSpec JSON file for DRAFT->REGISTERED pre-registration validation.",
    )
    parser.add_argument(
        "--hypothesis-card",
        help="HypothesisCard JSON file for DRAFT->REGISTERED pre-registration validation.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.object and not (args.alpha_spec or args.hypothesis_card):
        parser.error("provide --object or both --alpha-spec and --hypothesis-card")
    if bool(args.alpha_spec) != bool(args.hypothesis_card):
        parser.error("--alpha-spec and --hypothesis-card must be provided together")

    try:
        validations: list[dict[str, object]] = []
        for item in args.object:
            kind, path = _parse_object_arg(item)
            validations.append(validate_governance_object_file(path, kind).to_dict())
        if args.alpha_spec and args.hypothesis_card:
            hypothesis, alpha = validate_alpha_spec_files(args.alpha_spec, args.hypothesis_card)
            validations.append(
                {
                    "object_kind": "AlphaSpecWithHypothesisCard",
                    "alpha_spec_id": alpha.alpha_spec_id,
                    "hypothesis_id": hypothesis.hypothesis_id,
                    "validated_transition": "DRAFT->REGISTERED",
                }
            )
    except Exception as exc:  # noqa: BLE001 - tool emits structured fail-closed errors.
        print(
            json.dumps(
                governance_exception_payload("validate-objects", exc),
                sort_keys=True,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2

    print(
        json.dumps(
            {
                "status": "ok",
                "command": "validate-objects",
                "validation_count": len(validations),
                "validations": validations,
            },
            sort_keys=True,
            indent=2,
        )
    )
    return 0


def _parse_object_arg(value: str) -> tuple[str, str]:
    if ":" not in value:
        msg = "--object must use KIND:PATH"
        raise ValueError(msg)
    kind, path = value.split(":", 1)
    if not kind or not path:
        msg = "--object must include both KIND and PATH"
        raise ValueError(msg)
    return kind, path


if __name__ == "__main__":
    raise SystemExit(main())
