from __future__ import annotations

import pytest

from alpha_system.experiments.version_refs import (
    DataVersionRef,
    EngineVersionRef,
    VersionRefError,
    VersionReferences,
    validate_version_map,
)


def test_structured_version_references_validate() -> None:
    refs = VersionReferences(
        data_version="data:v1",
        factor_versions={"factor_a": "v1"},
        label_versions={"label_a": "v1"},
        engine_version="engine:v1",
    )

    refs.validate_requirements(require_factor_versions=True, require_label_versions=True)
    assert DataVersionRef("data:v1").data_version == "data:v1"
    assert EngineVersionRef("engine:v1").engine_version == "engine:v1"


def test_empty_or_malformed_version_references_are_rejected() -> None:
    with pytest.raises(VersionRefError, match="data_version"):
        DataVersionRef("")
    with pytest.raises(VersionRefError, match="invalid"):
        validate_version_map({"factor a": "v1"}, "factor_versions")


def test_required_factor_and_label_maps_are_enforced() -> None:
    refs = VersionReferences(
        data_version="data:v1",
        factor_versions={},
        label_versions={},
        engine_version="engine:v1",
    )

    with pytest.raises(VersionRefError, match="factor_versions"):
        refs.validate_requirements(require_factor_versions=True, require_label_versions=False)
    with pytest.raises(VersionRefError, match="label_versions"):
        refs.validate_requirements(require_factor_versions=False, require_label_versions=True)
