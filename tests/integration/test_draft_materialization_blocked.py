from __future__ import annotations

from pathlib import Path

import pytest

from alpha_system.factors.materialize import (
    FactorMaterializationError,
    materialize_factor_values,
)
from tests.fixtures.factors.synthetic import (
    DATA_VERSION,
    factor_spec,
    make_bars,
    write_bars_jsonl,
    write_spec_json,
)


def test_draft_materialization_is_blocked_by_default(tmp_path: Path) -> None:
    spec = factor_spec(status="draft", validation_artifact_path=None)
    spec_path = write_spec_json(tmp_path / "draft_factor.json", spec)
    bars_path = write_bars_jsonl(tmp_path / "bars.jsonl", make_bars(["100", "101"]))
    output_dir = tmp_path / "blocked_store"

    with pytest.raises(FactorMaterializationError, match="draft"):
        materialize_factor_values(
            spec_path=spec_path,
            canonical_data_path=bars_path,
            data_version=DATA_VERSION,
            output_policy="local-only-persist",
            output_dir=output_dir,
        )

    assert not output_dir.exists()
