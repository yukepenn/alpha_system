from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from alpha_system.governance.alpha_spec import generate_alpha_spec_id
from alpha_system.governance.evidence_bundle import EvidenceBundle, create_evidence_bundle
from alpha_system.governance.promotion import (
    PromotionDecisionOutcome,
    PromotionLifecycleState,
    create_promotion_decision,
)
from alpha_system.governance.registry import GovernanceRegistry
from alpha_system.governance.reviewer_verdict import ReviewerVerdict, create_reviewer_verdict
from alpha_system.governance.study_spec import StudySpec
from alpha_system.governance.trial_ledger import (
    TrialLedgerRecord,
    TrialStatus,
    create_trial_ledger_record,
)

FIXTURE_ROOT = Path("tests/fixtures/governance")
HYPOTHESIS_FIXTURE = FIXTURE_ROOT / "hypothesis_card_valid.json"
ALPHA_FIXTURE = FIXTURE_ROOT / "alpha_spec_valid.json"
STUDY_FIXTURE = FIXTURE_ROOT / "study_spec_valid.json"

ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd0"
STUDY_SPEC_ID = "sspec_438ceffd40855205de5497f0"
IMPLEMENTER_ID = "codex:argov-p16-executor"
IMPLEMENTER_ROLE = "codex_executor"
REVIEWER_ID = "claude:independent-governance-reviewer"
REVIEWER_ROLE = "claude_reviewer"
CODE_HASH = "a" * 64
CONFIG_HASH = "b" * 64
MANIFEST_HASH = "c" * 64
TIMESTAMP = "2026-06-03T13:52:09Z"


def _run_alpha(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    return subprocess.run(
        [sys.executable, "-m", "alpha_system.cli", *args],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
    return path


def _linked_alpha_spec(tmp_path: Path) -> Path:
    hypothesis = _load_json(HYPOTHESIS_FIXTURE)
    alpha = _load_json(ALPHA_FIXTURE)
    alpha["hypothesis_id"] = hypothesis["hypothesis_id"]
    alpha["alpha_spec_id"] = generate_alpha_spec_id(alpha)
    return _write_json(tmp_path / "linked-alpha-spec.json", alpha)


def _trial_record(
    *,
    run_id: str,
    variant_id: str,
    status: TrialStatus = TrialStatus.COMPLETED,
    failure_reason: str | None = None,
) -> TrialLedgerRecord:
    return create_trial_ledger_record(
        alpha_spec_id=ALPHA_SPEC_ID,
        study_spec_id=STUDY_SPEC_ID,
        run_id=run_id,
        variant_id=variant_id,
        status=status,
        parameters={"threshold": 0.25, "window": 20},
        metrics_summary={} if status is not TrialStatus.COMPLETED else {"coverage": 0.75},
        failure_reason=failure_reason,
        oos_touched_flag=False,
        locked_test_contamination_flag=False,
        code_hash=CODE_HASH,
        config_hash=CONFIG_HASH,
    )


def _reviewer_verdict(
    *,
    reviewer_id: str = REVIEWER_ID,
) -> ReviewerVerdict:
    return create_reviewer_verdict(
        reviewer_id=reviewer_id,
        role=REVIEWER_ROLE,
        independence_statement="Reviewer identity and role are independent from the implementer.",
        verdict="PASS",
        blocking_issues=[],
        warnings=["Synthetic governance review only; no market claim is made."],
        checked_artifacts=["src/alpha_system/cli/governance.py"],
        checked_commands=["python -m pytest tests/integration/governance -q"],
        timestamp=TIMESTAMP,
    )


def _evidence_bundle(
    records: tuple[TrialLedgerRecord, ...],
    verdict: ReviewerVerdict,
) -> EvidenceBundle:
    return create_evidence_bundle(
        alpha_spec_id=ALPHA_SPEC_ID,
        study_spec_id=STUDY_SPEC_ID,
        trial_ids=[record.trial_id for record in records],
        data_version="synthetic-data-v1",
        factor_version="synthetic-factor-v1",
        label_version="synthetic-label-v1",
        code_hash=CODE_HASH,
        config_hash=CONFIG_HASH,
        diagnostics_summary={
            "diagnostics_run_ref": "diagnostics-run-cli-smoke",
            "metric_set": "synthetic governance smoke metrics",
        },
        negative_control_results=[
            {
                "control_name": "permuted labels control",
                "result": "failed closed",
                "summary": "synthetic control did not create admissible evidence",
            }
        ],
        limitations=["synthetic metadata fixture only"],
        artifact_manifest=[
            {
                "logical_name": "diagnostics summary",
                "role": "diagnostics_summary",
                "reference": "local/evidence/diagnostics-summary.json",
                "content_hash": MANIFEST_HASH,
            }
        ],
        reviewer_verdict_reference=verdict.reviewer_verdict_id,
    )


def test_governance_cli_end_to_end_smoke(tmp_path: Path) -> None:
    registry_path = tmp_path / "governance.sqlite3"
    alpha_path = _linked_alpha_spec(tmp_path)
    completed = _trial_record(run_id="diagnostics-run-cli-smoke-1", variant_id="variant-a")
    failed = _trial_record(
        run_id="diagnostics-run-cli-smoke-2",
        variant_id="variant-b",
        status=TrialStatus.FAILED,
        failure_reason="synthetic dependency check failed before metrics existed",
    )
    verdict = _reviewer_verdict()
    bundle = _evidence_bundle((completed, failed), verdict)
    decision = create_promotion_decision(
        alpha_spec_id=ALPHA_SPEC_ID,
        evidence_bundle_id=bundle.evidence_bundle_id,
        trial_ledger_refs=[completed.trial_id, failed.trial_id],
        previous_state=PromotionLifecycleState.REVIEWED,
        next_state=PromotionLifecycleState.CANDIDATE,
        decision=PromotionDecisionOutcome.CANDIDATE,
        rationale="Synthetic governance metadata supports this controlled state transition.",
        reviewer_verdict_id=verdict.reviewer_verdict_id,
        warnings=["This decision is not live, capital, or production approval."],
        timestamp=TIMESTAMP,
    )
    completed_path = _write_json(tmp_path / "completed-trial.json", completed.to_dict())
    failed_path = _write_json(tmp_path / "failed-trial.json", failed.to_dict())
    bundle_path = _write_json(tmp_path / "evidence-bundle.json", bundle.to_dict())
    verdict_path = _write_json(tmp_path / "reviewer-verdict.json", verdict.to_dict())
    decision_path = _write_json(tmp_path / "promotion-decision.json", decision.to_dict())

    registry = GovernanceRegistry(registry_path)
    registry.save(StudySpec.from_mapping(_load_json(STUDY_FIXTURE)), "DIAGNOSTICS_ALLOWED")

    validate_result = _run_alpha(
        [
            "governance",
            "validate-spec",
            str(alpha_path),
            "--hypothesis-card",
            str(HYPOTHESIS_FIXTURE),
        ]
    )
    assert validate_result.returncode == 0, validate_result.stderr

    for trial_path in (completed_path, failed_path):
        trial_result = _run_alpha(
            [
                "governance",
                "register-trial",
                "--registry-path",
                str(registry_path),
                str(trial_path),
            ]
        )
        assert trial_result.returncode == 0, trial_result.stderr

    evidence_result = _run_alpha(
        [
            "governance",
            "build-evidence",
            "--registry-path",
            str(registry_path),
            str(bundle_path),
        ]
    )
    assert evidence_result.returncode == 0, evidence_result.stderr

    review_result = _run_alpha(
        [
            "governance",
            "review",
            "--registry-path",
            str(registry_path),
            "--implementer-id",
            IMPLEMENTER_ID,
            "--implementer-role",
            IMPLEMENTER_ROLE,
            str(verdict_path),
        ]
    )
    assert review_result.returncode == 0, review_result.stderr

    promote_result = _run_alpha(
        [
            "governance",
            "promote",
            "--registry-path",
            str(registry_path),
            "--implementer-id",
            IMPLEMENTER_ID,
            "--implementer-role",
            IMPLEMENTER_ROLE,
            str(decision_path),
        ]
    )
    assert promote_result.returncode == 0, promote_result.stderr

    entry = GovernanceRegistry(registry_path).get(decision.promotion_id)
    assert entry.latest_lifecycle_state == "CANDIDATE"


def test_governance_cli_validate_feature_locks_ok_and_fail_closed(tmp_path: Path) -> None:
    # Register real features through the seed operator, then validate locks via CLI.
    from datetime import UTC, datetime, timedelta
    from typing import Any

    from alpha_system.cli.seed_pack import parse_seed_pack_config, run_seed_feature_pack
    from alpha_system.core.value_store import ValueStoreFormat
    from alpha_system.data.foundation.datasets import (
        CoverageReport,
        DataQualityReport,
        ReportStatus,
    )

    dataset_id = "dsv_cli_lock_smoke_v1"
    window_start = "2024-01-02T14:30:00+00:00"
    window_end = "2024-01-02T15:30:00+00:00"

    config = parse_seed_pack_config(
        {
            "schema": "alpha_system.seed_pack.v1",
            "dataset_version_id": dataset_id,
            "partition_schema": "ohlcv_1m",
            "symbol": "ES",
            "partition_id": "development_partition",
            "window": {"start_ts": window_start, "end_ts": window_end},
            "feature_set": {
                "feature_set_id": "fset_cli_lock_smoke",
                "feature_set_version": "v1",
                "alpha_spec_id": ALPHA_SPEC_ID,
                "features": [{"name": "returns", "window_length": 1, "horizon": 1}],
            },
        }
    )

    def _dt(value: str) -> datetime:
        return datetime.fromisoformat(value).astimezone(UTC)

    def _rows() -> tuple[dict[str, Any], ...]:
        start = _dt(window_start)
        out: list[dict[str, Any]] = []
        for index in range(30):
            bar_start = start + timedelta(minutes=index)
            bar_end = bar_start + timedelta(minutes=1)
            close = f"{100.0 + index:.2f}"
            out.append(
                {
                    "instrument_id": "ES",
                    "contract_id": "ESM4",
                    "series_id": "ES_c_0",
                    "bar_start_ts": bar_start.isoformat(),
                    "bar_end_ts": bar_end.isoformat(),
                    "event_ts": bar_end.isoformat(),
                    "available_ts": (bar_end + timedelta(seconds=1)).isoformat(),
                    "ingested_at": (bar_end + timedelta(seconds=2)).isoformat(),
                    "open": close,
                    "high": close,
                    "low": close,
                    "close": close,
                    "volume": "10",
                    "source": "dsrc_databento_historical",
                    "source_request_id": "req_fixture_1",
                    "data_version": dataset_id,
                    "quality_flags": (),
                    "session_label": "RTH",
                }
            )
        return tuple(out)

    def _quality_coverage(cfg: Any, rows: Any, *, repo_root: Any):
        passing = {"count": 0, "status": ReportStatus.PASSING.value, "blocking": False}
        cov = {
            "status": ReportStatus.PASSING.value,
            "blocking": False,
            "expected_count": 1,
            "observed_count": 1,
            "missing_count": 0,
        }
        part = dict(cov)
        part["missing_interval_count"] = 0
        part["incomplete_chunk_count"] = 0
        quality = DataQualityReport(
            quality_report_id=f"qr_{cfg.dataset_version_id}",
            dataset_version_id=cfg.dataset_version_id,
            gap_summary=dict(passing),
            duplicate_summary=dict(passing),
            non_monotonic_summary=dict(passing),
            ohlc_errors=dict(passing),
            zero_negative_price_errors=dict(passing),
            zero_volume_anomalies=dict(passing),
            dst_anomalies=dict(passing),
            session_coverage=dict(passing),
            roll_discontinuities=dict(passing),
            provider_error_summary=dict(passing),
            bbo_missing_metric=dict(passing),
            abnormal_spread_summary=dict(passing),
            status=ReportStatus.PASSING,
        )
        coverage = CoverageReport(
            coverage_report_id=f"cr_{cfg.dataset_version_id}",
            dataset_version_id=cfg.dataset_version_id,
            symbol_coverage=dict(cov),
            contract_coverage=dict(cov),
            session_coverage=dict(cov),
            partition_coverage=part,
            missing_intervals=(),
            incomplete_chunks=(),
        )
        return quality, coverage

    summary = run_seed_feature_pack(
        config,
        alpha_data_root=tmp_path / "alpha_data",
        canonical_root=tmp_path / "unused_canonical",
        datasets_registry_path=tmp_path / "registry" / "datasets.sqlite",
        bar_rows=_rows(),
        quality_coverage_builder=_quality_coverage,
        value_store_format=ValueStoreFormat.JSONL,
    )
    registry_path = tmp_path / "alpha_data" / "registry" / "features.sqlite"
    version_ids = list(summary["feature_version_ids"])

    ok_locks = _write_json(
        tmp_path / "locks_ok.json",
        {"feature_pack_locks": [{"feature_version_id": vid} for vid in version_ids]},
    )
    ok_result = _run_alpha(
        [
            "governance",
            "validate-feature-locks",
            "--locks",
            str(ok_locks),
            "--registry-path",
            str(registry_path),
        ]
    )
    assert ok_result.returncode == 0, ok_result.stderr
    ok_payload = json.loads(ok_result.stdout)
    assert ok_payload["ok"] is True
    assert ok_payload["stale_lock_count"] == 0

    missing = "fver_" + ("0" * 64)
    stale_locks = _write_json(
        tmp_path / "locks_stale.json",
        {"feature_pack_locks": [{"feature_version_id": missing}]},
    )
    stale_result = _run_alpha(
        [
            "governance",
            "validate-feature-locks",
            "--locks",
            str(stale_locks),
            "--registry-path",
            str(registry_path),
        ]
    )
    assert stale_result.returncode == 2
    assert missing in stale_result.stderr


def test_governance_cli_self_review_smoke_fails_closed(tmp_path: Path) -> None:
    verdict_path = _write_json(
        tmp_path / "self-review.json",
        _reviewer_verdict(reviewer_id=IMPLEMENTER_ID).to_dict(),
    )

    result = _run_alpha(
        [
            "governance",
            "review",
            "--registry-path",
            str(tmp_path / "governance.sqlite3"),
            "--implementer-id",
            IMPLEMENTER_ID,
            "--implementer-role",
            IMPLEMENTER_ROLE,
            str(verdict_path),
        ]
    )

    assert result.returncode == 2
    payload = json.loads(result.stderr)
    assert any(issue["code"] == "reviewer_self_approval" for issue in payload["issues"])
