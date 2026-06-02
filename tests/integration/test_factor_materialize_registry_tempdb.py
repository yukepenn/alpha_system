from __future__ import annotations

import sqlite3
from pathlib import Path

from alpha_system.factors.materialize import materialize_factor_values
from tests.fixtures.factors.synthetic import (
    DATA_VERSION,
    make_bars,
    seed_validated_registry,
    validated_factor_spec,
    write_bars_jsonl,
    write_spec_json,
)


def test_materialize_records_temp_registry_entry_without_promotion(tmp_path: Path) -> None:
    spec = validated_factor_spec()
    registry_path = tmp_path / "registry.sqlite3"
    seed_validated_registry(registry_path, spec)
    spec_path = write_spec_json(tmp_path / "validated_factor.json", spec)
    bars_path = write_bars_jsonl(tmp_path / "bars.jsonl", make_bars(["100", "101"]))

    summary = materialize_factor_values(
        spec_path=spec_path,
        canonical_data_path=bars_path,
        data_version=DATA_VERSION,
        output_policy="local-only-persist",
        output_dir=tmp_path / "factor_store",
        registry_path=registry_path,
    )

    assert summary.registry_written is True
    with sqlite3.connect(registry_path) as connection:
        materialized_count = connection.execute(
            """
            SELECT count(*)
            FROM factor_validation_runs
            WHERE decision_status = 'materialized_local'
              AND engine_version = ?
            """,
            (summary.compute_version,),
        ).fetchone()[0]
        promotion_count = connection.execute(
            "SELECT count(*) FROM promotion_decisions"
        ).fetchone()[0]

    assert materialized_count == 1
    assert promotion_count == 0
