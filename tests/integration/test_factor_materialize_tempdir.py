from __future__ import annotations

import json
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


def test_validated_factor_materializes_to_tempdir_only(tmp_path: Path) -> None:
    spec = validated_factor_spec()
    registry_path = tmp_path / "registry.sqlite3"
    seed_validated_registry(registry_path, spec)
    spec_path = write_spec_json(tmp_path / "factor.json", spec)
    bars_path = write_bars_jsonl(tmp_path / "bars.jsonl", make_bars(["100", "101", "103"]))
    output_dir = tmp_path / "factor_store"

    summary = materialize_factor_values(
        spec_path=spec_path,
        canonical_data_path=bars_path,
        data_version=DATA_VERSION,
        output_policy="local-only-persist",
        output_dir=output_dir,
        registry_path=registry_path,
    )

    assert summary.persisted is True
    assert summary.record_count == 3
    assert summary.value_path is not None
    assert Path(summary.value_path).is_file()
    assert summary.manifest_path is not None
    manifest = json.loads(Path(summary.manifest_path).read_text(encoding="utf-8"))
    assert manifest["data_version"] == DATA_VERSION
    assert manifest["compute_version"] == "factor_compute_sdk_mvp_v1"
    assert manifest["code_hash"] == spec.code_hash
    assert manifest["config_hash"] == spec.config_hash

    values = [
        json.loads(line)
        for line in Path(summary.value_path).read_text(encoding="utf-8").splitlines()
    ]
    assert [value["value"] for value in values] == [None, 1.0, 2.0]
    assert Path(summary.value_path).is_relative_to(output_dir)
