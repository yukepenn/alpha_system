"""ML/factor-combination CLI command group."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from alpha_system.experiments.ml import (
    MLRunError,
    MLRunSpec,
    load_ml_run_spec,
    parse_version_overrides,
    run_ml_experiment,
    wrap_contract_error,
)


def run_ml_cli(args: argparse.Namespace) -> int:
    """Run ``alpha ml run`` on local fixture inputs."""
    try:
        spec = _load_spec_from_args(args).with_overrides(
            data_version=args.data_version,
            factor_versions=parse_version_overrides(
                args.factor_version,
                field_name="--factor-version",
            ),
            label_version=args.label_version,
            output_dir=args.output_dir,
            registry_path=args.registry_path,
            instruments=args.instrument,
        )
        result = run_ml_experiment(spec)
    except (OSError, ValueError, TypeError) as exc:
        error = wrap_contract_error(exc) if not isinstance(exc, MLRunError) else exc
        print(f"ml command error: {error}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
        return 0

    print("ML command: run")
    print(f"Run: {result.run_id}")
    print(f"Scores: {result.score_output.summary()['score_count']}")
    print(f"Splits: {result.split_count}")
    print(f"Manifest: {result.manifest_path}")
    print(f"Score summary: {result.score_summary_path}")
    if result.registry_path is not None:
        print(f"Registry: {result.registry_path}")
        print(f"Registry written: {'yes' if result.registry_written else 'no'}")
    return 0


def _load_spec_from_args(args: argparse.Namespace) -> MLRunSpec:
    config_path = args.config or args.config_path
    if config_path is not None:
        if any((args.feature_set, args.label_spec, args.model_spec, args.split_config)):
            raise MLRunError("provide either --config/CONFIG_PATH or separate spec files")
        return load_ml_run_spec(config_path)
    if not (args.feature_set and args.label_spec and args.model_spec):
        raise MLRunError("provide a config path or feature, label, and model spec files")
    payload = {
        "run_id": args.run_id,
        "feature_set": _load_json_object(args.feature_set),
        "label_spec": _load_json_object(args.label_spec),
        "model_spec": _load_json_object(args.model_spec),
        "split": _load_json_object(args.split_config) if args.split_config else {},
        "observations": _load_json_array(args.observations) if args.observations else [],
    }
    return MLRunSpec.from_mapping(payload)


def _load_json_object(path: str) -> dict[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise MLRunError(f"{path} must contain a JSON object")
    return payload


def _load_json_array(path: str) -> list[object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise MLRunError(f"{path} must contain a JSON array")
    return payload


def register_subparser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the ``alpha ml`` command group."""
    ml_parser = subparsers.add_parser(
        "ml",
        help="Run local ML/factor-combination experiments on versioned factor inputs.",
    )
    ml_subparsers = ml_parser.add_subparsers(dest="ml_command")

    run_parser = ml_subparsers.add_parser(
        "run",
        help="Run a deterministic local ML/factor-combination MVP experiment.",
    )
    run_parser.add_argument(
        "config_path",
        nargs="?",
        help="Path to a JSON ML run config.",
    )
    run_parser.add_argument(
        "--config",
        help="Path to a JSON ML run config.",
    )
    run_parser.add_argument(
        "--run-id",
        help="Run id used when assembling separate spec files.",
    )
    run_parser.add_argument(
        "--feature-set",
        help="Path to a JSON FeatureSetSpec.",
    )
    run_parser.add_argument(
        "--label-spec",
        help="Path to a JSON LabelSpec reference.",
    )
    run_parser.add_argument(
        "--model-spec",
        help="Path to a JSON ModelSpec.",
    )
    run_parser.add_argument(
        "--split-config",
        help="Path to a JSON split config.",
    )
    run_parser.add_argument(
        "--observations",
        help="Path to tiny JSON fixture observations.",
    )
    run_parser.add_argument(
        "--data-version",
        help="Override the declared data version.",
    )
    run_parser.add_argument(
        "--factor-version",
        action="append",
        help="Declared factor version as factor_id=version; repeat for multiple factors.",
    )
    run_parser.add_argument(
        "--label-version",
        help="Override the declared label version.",
    )
    run_parser.add_argument(
        "--instrument",
        action="append",
        help="Optional instrument selector; repeat for multiple instruments.",
    )
    run_parser.add_argument(
        "--registry-path",
        help="Optional temp/local SQLite registry path outside repository data roots.",
    )
    run_parser.add_argument(
        "--output-dir",
        help="Optional local output directory outside repository artifact roots.",
    )
    run_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON console summary.",
    )
    run_parser.set_defaults(handler=run_ml_cli)
