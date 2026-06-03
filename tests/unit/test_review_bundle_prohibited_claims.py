from __future__ import annotations

import pytest

from alpha_system.reports.claim_checks import find_claim_violations
from alpha_system.reports.prohibited_claims import ProhibitedClaimError
from alpha_system.reports.review_bundle import build_review_bundle
from tests.unit.reports.review_bundle_fixtures import (
    REPO_ROOT,
    registry_record,
    run_manifest_payload,
    write_artifact_manifest,
    write_run_manifest,
)


def test_review_bundle_blocks_prohibited_claim_language(tmp_path) -> None:
    payload = run_manifest_payload()
    payload["review_status"] = "profitable"

    with pytest.raises(ProhibitedClaimError):
        build_review_bundle(
            run_id="review_bundle_fixture",
            registry_records=(registry_record(),),
            artifact_manifest=write_artifact_manifest(tmp_path),
            run_manifest=write_run_manifest(tmp_path, payload),
            source_root=REPO_ROOT,
        )


def test_claim_checker_flags_context_sensitive_language() -> None:
    violations = find_claim_violations("The candidate is approved.")

    assert any(violation.code == "blocked_claim:approved_without_review" for violation in violations)
    assert any(
        violation.code == "blocked_claim:robust_without_evidence"
        for violation in find_claim_violations("The result is robust.")
    )
