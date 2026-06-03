from __future__ import annotations

import json
from pathlib import Path

from alpha_system.governance.label_leakage_guard import (
    LabelLeakageFindingKind,
    LabelLeakageSeverity,
    check_label_leakage,
)
from alpha_system.governance.label_spec import validate_label_spec


LABEL_SPEC_FIXTURE = Path("tests/fixtures/governance/label_spec_valid.json")
FEATURE_FIXTURE = Path("tests/fixtures/governance/label_leakage_features.json")


def load_label_spec() -> dict[str, object]:
    return json.loads(LABEL_SPEC_FIXTURE.read_text(encoding="utf-8"))


def load_features() -> dict[str, list[dict[str, object]]]:
    return json.loads(FEATURE_FIXTURE.read_text(encoding="utf-8"))


def test_label_as_feature_overlap_is_blocked() -> None:
    label_spec = validate_label_spec(load_label_spec())
    features = load_features()["label_as_feature"]

    result = check_label_leakage(label_spec, features)

    assert result.blocked is True
    assert result.clean is False
    assert any(
        finding.kind is LabelLeakageFindingKind.LABEL_AS_FEATURE
        and finding.severity is LabelLeakageSeverity.BLOCKING
        for finding in result.findings
    )
    assert result.findings[0].offending_reference["reference"] == "synthetic_forward_return_5d"


def test_forbidden_transform_alias_is_blocked() -> None:
    label_spec = validate_label_spec(load_label_spec())
    features = load_features()["transform_alias"]

    result = check_label_leakage(label_spec, features)

    assert result.blocked is True
    assert any(
        finding.kind is LabelLeakageFindingKind.LABEL_AS_FEATURE
        for finding in result.findings
    )


def test_feature_at_label_availability_time_is_lookahead_blocked() -> None:
    label_spec = validate_label_spec(load_label_spec())
    features = load_features()["lookahead_features"]

    result = check_label_leakage(label_spec, features)

    assert result.blocked is True
    assert any(
        finding.kind is LabelLeakageFindingKind.LOOKAHEAD
        and finding.severity is LabelLeakageSeverity.BLOCKING
        for finding in result.findings
    )


def test_missing_availability_metadata_fails_closed() -> None:
    label_spec = validate_label_spec(load_label_spec())
    features = load_features()["missing_availability"]

    result = check_label_leakage(label_spec, features)

    assert result.blocked is True
    assert result.findings[0].kind is LabelLeakageFindingKind.LOOKAHEAD
    assert "fails closed" in result.findings[0].rationale


def test_clean_feature_set_passes_without_findings() -> None:
    label_spec = validate_label_spec(load_label_spec())
    features = load_features()["clean_features"]

    result = check_label_leakage(label_spec, features)

    assert result.clean is True
    assert result.blocked is False
    assert result.features_checked == 1
    assert result.findings == ()
