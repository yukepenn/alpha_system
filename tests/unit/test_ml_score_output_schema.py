from __future__ import annotations

from alpha_system.experiments.ml_outputs import SCORE_SCHEMA_VERSION, ScoreOutput, ScoreRecord


def test_ml_score_output_schema_requires_versioned_fields() -> None:
    record = ScoreRecord(
        run_id="ml",
        split_id="split",
        instrument="SYNTH",
        decision_ts="2026-01-02T10:00:00Z",
        score=0.1,
        feature_set_id="fixture",
        model_id="ridge",
        data_version="data:v1",
        factor_versions={"momentum_3": "factor:v1"},
        label_version="label:v1",
    )
    output = ScoreOutput(records=(record,))

    assert output.schema_version == SCORE_SCHEMA_VERSION
    assert output.summary()["score_count"] == 1
    assert output.to_dict()["records"][0]["factor_versions"] == {"momentum_3": "factor:v1"}
