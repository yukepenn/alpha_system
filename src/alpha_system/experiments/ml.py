"""Local ML/factor-combination MVP orchestration."""

from __future__ import annotations

import json
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from alpha_system.core.hashing import hash_config
from alpha_system.experiments.feature_sets import (
    FeatureSetError,
    FeatureSetSpec,
    LabelSpec,
    validate_label_availability,
    validate_label_not_in_features,
)
from alpha_system.experiments.ml_outputs import ScoreOutput, ScoreToPortfolioContract
from alpha_system.experiments.ml_registry import MLRegistryWriteResult, write_ml_run_record
from alpha_system.experiments.model_specs import ML_ENGINE_VERSION, ModelSpec
from alpha_system.experiments.reproducibility import build_reproducibility_metadata
from alpha_system.experiments.scoring import combine_score_outputs, fit_linear_baseline, score_rows
from alpha_system.experiments.splits import SplitWindow, train_validation_split, walk_forward_splits


class MLRunError(ValueError):
    """Raised when an ML MVP run cannot be assembled safely."""


FORBIDDEN_REPO_OUTPUT_ROOTS = (
    "runs",
    "metadata",
    "data",
    "artifacts/ml_experiments",
)
ML_CODE_PATHS = (
    "src/alpha_system/experiments/ml.py",
    "src/alpha_system/experiments/feature_sets.py",
    "src/alpha_system/experiments/splits.py",
    "src/alpha_system/experiments/model_specs.py",
    "src/alpha_system/experiments/scoring.py",
    "src/alpha_system/experiments/ml_outputs.py",
    "src/alpha_system/experiments/ml_registry.py",
)


@dataclass(frozen=True, slots=True)
class SplitConfig:
    """Split configuration for an ML run."""

    split_type: str = "train_validation"
    validation_fraction: float = 0.25
    train_window: int | None = None
    validation_window: int | None = None
    step_size: int | None = None
    purge_gap: int = 0
    embargo_gap: int = 0

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None) -> "SplitConfig":
        payload = {} if payload is None else dict(payload)
        if not isinstance(payload, Mapping):
            raise MLRunError("split config must be a mapping")
        split_type = _optional_text(payload.get("split_type"), "split_type") or "train_validation"
        if split_type not in {"train_validation", "walk_forward"}:
            raise MLRunError("split_type must be train_validation or walk_forward")
        return cls(
            split_type=split_type,
            validation_fraction=_fraction(
                payload.get("validation_fraction", 0.25),
                "validation_fraction",
            ),
            train_window=_optional_positive_int(payload.get("train_window"), "train_window"),
            validation_window=_optional_positive_int(
                payload.get("validation_window"),
                "validation_window",
            ),
            step_size=_optional_positive_int(payload.get("step_size"), "step_size"),
            purge_gap=_non_negative_int(payload.get("purge_gap", 0), "purge_gap"),
            embargo_gap=_non_negative_int(payload.get("embargo_gap", 0), "embargo_gap"),
        )

    def make_windows(self, sample_count: int) -> tuple[SplitWindow, ...]:
        if self.split_type == "train_validation":
            return (
                train_validation_split(
                    sample_count,
                    validation_fraction=self.validation_fraction,
                    purge_gap=self.purge_gap,
                    embargo_gap=self.embargo_gap,
                ),
            )
        if self.train_window is None or self.validation_window is None:
            raise MLRunError("walk_forward split requires train_window and validation_window")
        return walk_forward_splits(
            sample_count,
            train_window=self.train_window,
            validation_window=self.validation_window,
            step_size=self.step_size,
            purge_gap=self.purge_gap,
            embargo_gap=self.embargo_gap,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class MLRunSpec:
    """Validated local ML/factor-combination run spec."""

    run_id: str
    feature_set: FeatureSetSpec
    label_spec: LabelSpec
    model_spec: ModelSpec
    split_config: SplitConfig
    observations: tuple[Mapping[str, Any], ...]
    output_dir: str | None = None
    registry_path: str | None = None
    manifest_path: str | None = None
    contract: ScoreToPortfolioContract = ScoreToPortfolioContract()
    engine_version: str = ML_ENGINE_VERSION

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "MLRunSpec":
        if not isinstance(payload, Mapping):
            raise MLRunError("ML run config root must be a JSON object")
        label_spec_payload = payload.get("label_spec")
        if not isinstance(label_spec_payload, Mapping):
            raise MLRunError("ML run config requires label_spec")
        label_spec = LabelSpec.from_mapping(label_spec_payload)
        feature_set_payload = payload.get("feature_set")
        if not isinstance(feature_set_payload, Mapping):
            raise MLRunError("ML run config requires feature_set")
        feature_set = FeatureSetSpec.from_mapping(feature_set_payload, label_spec=label_spec)
        validate_label_not_in_features(feature_set, label_spec)
        model_spec_payload = payload.get("model_spec")
        if not isinstance(model_spec_payload, Mapping):
            raise MLRunError("ML run config requires model_spec")
        observations = _observations(payload.get("observations", ()))
        return cls(
            run_id=_optional_text(payload.get("run_id"), "run_id")
            or f"ml_{feature_set.feature_set_id}",
            feature_set=feature_set,
            label_spec=label_spec,
            model_spec=ModelSpec.from_mapping(model_spec_payload),
            split_config=SplitConfig.from_mapping(payload.get("split")),
            observations=observations,
            output_dir=_optional_text(payload.get("output_dir"), "output_dir"),
            registry_path=_optional_text(payload.get("registry_path"), "registry_path"),
            manifest_path=_optional_text(payload.get("manifest_path"), "manifest_path"),
            contract=ScoreToPortfolioContract(),
            engine_version=_optional_text(payload.get("engine_version"), "engine_version")
            or ML_ENGINE_VERSION,
        )

    def with_overrides(
        self,
        *,
        data_version: str | None = None,
        factor_versions: Mapping[str, str] | None = None,
        label_version: str | None = None,
        output_dir: str | None = None,
        registry_path: str | None = None,
        instruments: Sequence[str] | None = None,
    ) -> "MLRunSpec":
        feature_set = self.feature_set
        if data_version is not None:
            feature_set = replace(feature_set, data_version=_text(data_version, "data_version"))
        if factor_versions is not None:
            feature_set = FeatureSetSpec.from_mapping(
                {
                    **feature_set.to_dict(),
                    "factor_versions": dict(factor_versions),
                    "features": [
                        {
                            **feature.to_dict(),
                            "factor_version": factor_versions.get(
                                feature.factor_id,
                                feature.factor_version,
                            ),
                        }
                        for feature in feature_set.features
                    ],
                },
                label_spec=self.label_spec,
            )
        if instruments is not None:
            feature_set = replace(feature_set, instruments=tuple(instruments))
        label_spec = self.label_spec
        if label_version is not None:
            label_spec = replace(label_spec, label_version=_text(label_version, "label_version"))
        return replace(
            self,
            feature_set=feature_set,
            label_spec=label_spec,
            output_dir=output_dir or self.output_dir,
            registry_path=registry_path or self.registry_path,
        )

    @property
    def label_versions(self) -> dict[str, str]:
        return {self.label_spec.label_id: self.label_spec.label_version}

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "feature_set": self.feature_set.to_dict(),
            "label_spec": self.label_spec.to_dict(),
            "model_spec": self.model_spec.to_dict(),
            "split": self.split_config.to_dict(),
            "observations": [dict(row) for row in self.observations],
            "output_dir": self.output_dir,
            "registry_path": self.registry_path,
            "manifest_path": self.manifest_path,
            "contract": self.contract.to_dict(),
            "engine_version": self.engine_version,
        }


@dataclass(frozen=True, slots=True)
class MLRunResult:
    """Summary of a local ML MVP run."""

    run_id: str
    output_dir: str
    manifest_path: str
    score_summary_path: str
    registry_path: str | None
    registry_written: bool
    score_output: ScoreOutput
    split_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "output_dir": self.output_dir,
            "manifest_path": self.manifest_path,
            "score_summary_path": self.score_summary_path,
            "registry_path": self.registry_path,
            "registry_written": self.registry_written,
            "score_summary": self.score_output.summary(),
            "split_count": self.split_count,
        }


def load_ml_run_spec(path: str | Path) -> MLRunSpec:
    """Load a JSON ML run config from disk."""
    config_path = Path(path).expanduser().resolve(strict=False)
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    return MLRunSpec.from_mapping(payload)


def run_ml_experiment(spec: MLRunSpec) -> MLRunResult:
    """Run a deterministic local ML/factor-combination fixture experiment."""
    if not spec.observations:
        raise MLRunError("ML run requires fixture observations")
    validate_label_not_in_features(spec.feature_set, spec.label_spec)
    validate_label_availability(spec.observations, spec.label_spec)
    rows = _filter_observations(spec.observations, spec.feature_set.instruments)
    if len(rows) < 2:
        raise MLRunError("ML run requires at least two observations after filtering")

    for row_number, row in enumerate(rows):
        for feature_id in spec.feature_set.feature_ids:
            if feature_id not in row:
                raise MLRunError(f"row {row_number} missing feature {feature_id!r}")
        if spec.label_spec.effective_value_field not in row:
            raise MLRunError(
                f"row {row_number} missing label field "
                f"{spec.label_spec.effective_value_field!r}",
            )

    windows = spec.split_config.make_windows(len(rows))
    fold_outputs: list[ScoreOutput] = []
    for window in windows:
        train_rows = tuple(rows[index] for index in window.train_indices)
        validation_rows = tuple(rows[index] for index in window.validation_indices)
        labels = tuple(row[spec.label_spec.effective_value_field] for row in train_rows)
        fit = fit_linear_baseline(
            spec.model_spec,
            train_rows,
            labels,
            spec.feature_set.feature_ids,
        )
        fold_outputs.append(
            score_rows(
                fit,
                validation_rows,
                run_id=spec.run_id,
                split_id=window.split_id,
                feature_set=spec.feature_set,
                label_spec=spec.label_spec,
            )
        )
    score_output = combine_score_outputs(fold_outputs)

    output_dir = resolve_ml_output_dir(spec.output_dir, run_id=spec.run_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = (
        Path(spec.manifest_path).expanduser().resolve(strict=False)
        if spec.manifest_path is not None
        else output_dir / "manifest.json"
    )
    _ensure_local_output_path(manifest_path)
    score_summary_path = output_dir / "score_summary.json"

    artifact_paths = {
        "manifest_path": manifest_path.as_posix(),
        "score_summary_path": score_summary_path.as_posix(),
    }
    manifest = _manifest_payload(
        spec=spec,
        windows=windows,
        score_output=score_output,
        artifact_paths=artifact_paths,
    )
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    score_summary_path.write_text(
        json.dumps(score_output.summary(), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    registry_written = False
    registry_result: MLRegistryWriteResult | None = None
    if spec.registry_path is not None:
        reproducibility = build_reproducibility_metadata(
            config=spec.to_dict(),
            code_paths=ML_CODE_PATHS,
            data_version=spec.feature_set.data_version,
            factor_versions=spec.feature_set.factor_versions,
            label_versions=spec.label_versions,
            engine_version=spec.engine_version,
        )
        registry_result = write_ml_run_record(
            registry_path=spec.registry_path,
            run_id=spec.run_id,
            reproducibility=reproducibility,
            parameters={
                "feature_set_id": spec.feature_set.feature_set_id,
                "label_id": spec.label_spec.label_id,
                "model_id": spec.model_spec.model_id,
                "model_type": spec.model_spec.model_type,
                "split_type": spec.split_config.split_type,
            },
            artifact_paths=artifact_paths,
            warnings=("local_fixture_research_only",),
        )
        registry_written = registry_result.written

    return MLRunResult(
        run_id=spec.run_id,
        output_dir=output_dir.as_posix(),
        manifest_path=manifest_path.as_posix(),
        score_summary_path=score_summary_path.as_posix(),
        registry_path=None if registry_result is None else registry_result.registry_path,
        registry_written=registry_written,
        score_output=score_output,
        split_count=len(windows),
    )


def resolve_ml_output_dir(path: str | Path | None, *, run_id: str) -> Path:
    """Resolve an ML output directory, defaulting outside the repository."""
    if path is None:
        output_dir = Path(tempfile.gettempdir()) / "alpha_system_ml_experiments" / run_id
    else:
        output_dir = Path(path).expanduser().resolve(strict=False)
    _ensure_local_output_path(output_dir)
    return output_dir


def parse_version_overrides(values: Sequence[str] | None, *, field_name: str) -> dict[str, str] | None:
    """Parse repeated ``name=version`` CLI overrides."""
    if not values:
        return None
    versions: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise MLRunError(f"{field_name} values must use name=version")
        name, version = value.split("=", 1)
        name = name.strip()
        version = version.strip()
        if not name or not version:
            raise MLRunError(f"{field_name} values must include non-empty name and version")
        existing = versions.get(name)
        if existing is not None and existing != version:
            raise MLRunError(f"conflicting version reference for {name}")
        versions[name] = version
    return versions


def _manifest_payload(
    *,
    spec: MLRunSpec,
    windows: Sequence[SplitWindow],
    score_output: ScoreOutput,
    artifact_paths: Mapping[str, str],
) -> dict[str, Any]:
    return {
        "run_id": spec.run_id,
        "engine_version": spec.engine_version,
        "feature_set": spec.feature_set.to_dict(),
        "label_spec": spec.label_spec.to_dict(),
        "model_spec": spec.model_spec.to_dict(),
        "split_windows": [window.to_dict() for window in windows],
        "score_summary": score_output.summary(),
        "score_schema_version": score_output.schema_version,
        "score_to_portfolio_contract": spec.contract.to_dict(),
        "artifact_paths": dict(artifact_paths),
        "config_hash": hash_config(spec.to_dict()),
        "decision_status": "ml_recorded",
        "status_message": "Local fixture research record; reviewed promotion is required.",
    }


def _filter_observations(
    rows: Sequence[Mapping[str, Any]],
    instruments: Sequence[str],
) -> tuple[Mapping[str, Any], ...]:
    if not instruments:
        return tuple(dict(row) for row in rows)
    allowed = set(instruments)
    return tuple(dict(row) for row in rows if str(row.get("instrument", "")) in allowed)


def _observations(value: Any) -> tuple[Mapping[str, Any], ...]:
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise MLRunError("observations must be an explicit list of row mappings")
    rows: list[Mapping[str, Any]] = []
    for row in value:
        if not isinstance(row, Mapping):
            raise MLRunError("observation rows must be mappings")
        rows.append(dict(row))
    return tuple(rows)


def _ensure_local_output_path(path: Path) -> None:
    resolved = path.expanduser().resolve(strict=False)
    repo_root = Path.cwd().resolve()
    try:
        relative = resolved.relative_to(repo_root)
    except ValueError:
        return
    relative_posix = relative.as_posix()
    for root in FORBIDDEN_REPO_OUTPUT_ROOTS:
        if relative_posix == root or relative_posix.startswith(f"{root}/"):
            raise MLRunError(f"ML outputs must remain outside repository-local {root}/ paths")


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MLRunError(f"{field_name} must be a non-empty string")
    return value.strip()


def _optional_text(value: Any, field_name: str) -> str | None:
    if value in (None, ""):
        return None
    return _text(value, field_name)


def _fraction(value: Any, field_name: str) -> float:
    if isinstance(value, bool):
        raise MLRunError(f"{field_name} must be a fraction between 0 and 1")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise MLRunError(f"{field_name} must be a fraction between 0 and 1") from exc
    if not 0 < number < 1:
        raise MLRunError(f"{field_name} must be between 0 and 1")
    return number


def _optional_positive_int(value: Any, field_name: str) -> int | None:
    if value in (None, ""):
        return None
    return _positive_int(value, field_name)


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise MLRunError(f"{field_name} must be positive")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise MLRunError(f"{field_name} must be positive") from exc
    if number <= 0:
        raise MLRunError(f"{field_name} must be positive")
    return number


def _non_negative_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise MLRunError(f"{field_name} must be non-negative")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise MLRunError(f"{field_name} must be non-negative") from exc
    if number < 0:
        raise MLRunError(f"{field_name} must be non-negative")
    return number


def wrap_contract_error(exc: Exception) -> MLRunError:
    """Normalize lower-level contract errors for CLI callers."""
    if isinstance(exc, MLRunError):
        return exc
    if isinstance(exc, FeatureSetError):
        return MLRunError(str(exc))
    return MLRunError(str(exc))
