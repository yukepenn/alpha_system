from __future__ import annotations

from pathlib import Path

import pytest

from alpha_system.experiments.ml import MLRunError, MLRunSpec, resolve_ml_output_dir, run_ml_experiment


def test_ml_outputs_default_to_temp_root() -> None:
    output_dir = resolve_ml_output_dir(None, run_id="artifact_policy")

    assert Path("artifacts/ml_experiments").resolve() not in output_dir.parents
    assert "alpha_system_ml_experiments" in output_dir.as_posix()


def test_ml_rejects_repository_ml_artifact_root() -> None:
    with pytest.raises(MLRunError, match="artifacts/ml_experiments"):
        resolve_ml_output_dir("artifacts/ml_experiments/example", run_id="blocked")


def test_ml_run_writes_json_only_in_temp_output(tmp_path: Path) -> None:
    result = run_ml_experiment(MLRunSpec.from_mapping(_payload(tmp_path / "ml")))
    written = sorted(path.suffix for path in Path(result.output_dir).iterdir())

    assert written == [".json", ".json"]
    assert not list(Path(result.output_dir).glob("*.pkl"))
    assert not list(Path(result.output_dir).glob("*.joblib"))


def _payload(output_dir: Path) -> dict[str, object]:
    return {
        "run_id": "ml_artifact_policy",
        "output_dir": output_dir.as_posix(),
        "feature_set": {
            "feature_set_id": "fixture",
            "data_version": "data:v1",
            "factor_versions": {"momentum_3": "factor:v1"},
            "features": [{"factor_id": "momentum_3"}],
        },
        "label_spec": {"label_id": "forward_return_1", "label_version": "label:v1"},
        "model_spec": {"model_id": "ridge", "model_type": "ridge_baseline"},
        "split": {"validation_fraction": 0.5},
        "observations": [
            {
                "instrument": "SYNTH",
                "decision_ts": "2026-01-02T10:00:00Z",
                "label_available_ts": "2026-01-02T09:59:00Z",
                "momentum_3": 0.1,
                "forward_return_1": 0.01,
            },
            {
                "instrument": "SYNTH",
                "decision_ts": "2026-01-02T10:01:00Z",
                "label_available_ts": "2026-01-02T10:00:00Z",
                "momentum_3": 0.2,
                "forward_return_1": 0.02,
            },
        ],
    }
