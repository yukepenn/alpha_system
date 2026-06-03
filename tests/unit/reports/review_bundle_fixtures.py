from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from alpha_system.reports.review_bundle import ReviewBundle, build_review_bundle


REPO_ROOT = Path(__file__).resolve().parents[3]


def run_manifest_payload(run_id: str = "review_bundle_fixture") -> dict[str, Any]:
    return {
        "run_id": run_id,
        "data_version": "data:v1",
        "factor_versions": {"fixture_factor": "factor:v1"},
        "label_versions": {"fixture_label": "label:v1"},
        "engine_version": "fixture_engine_v1",
        "config_hash": "config-hash-v1",
        "code_hash": "code-hash-v1",
        "diagnostics_summary": {"sample_size": 12, "warning_count": 1},
        "backtest_summary": {"trade_count": 0},
        "cost_sensitivity": {"not_applicable": True},
        "monthly_breakdown": {"2026-01": {"rows": 2}},
        "rejected_configs": (),
        "failed_steps": (),
        "warnings": ("fixture warning",),
        "promotion_decision_status": "not_recorded",
        "no_lookahead_validation_status": "passed",
        "review_status": "review_pending",
    }


def registry_record(run_id: str = "review_bundle_fixture") -> dict[str, Any]:
    return {
        "table_name": "study_runs",
        "run_id": run_id,
        "code_hash": "code-hash-v1",
        "config_hash": "config-hash-v1",
        "data_version": "data:v1",
        "factor_versions": {"fixture_factor": "factor:v1"},
        "label_versions": {"fixture_label": "label:v1"},
        "engine_version": "fixture_engine_v1",
        "artifact_paths": {"summary": "docs/REVIEW_BUNDLES.md"},
        "decision_status": "research_evidence_only",
        "warnings": (),
        "parameters": {},
        "status_message": "",
        "failed_steps": (),
    }


def write_run_manifest(tmp_path: Path, payload: dict[str, Any] | None = None) -> Path:
    manifest_path = tmp_path / "run_manifest.json"
    manifest_path.write_text(
        json.dumps(payload or run_manifest_payload(), sort_keys=True, indent=2),
        encoding="utf-8",
    )
    return manifest_path


def write_artifact_manifest(tmp_path: Path, entries: list[dict[str, Any]] | None = None) -> Path:
    manifest_path = tmp_path / "artifact_manifest.json"
    manifest_path.write_text(
        json.dumps({"entries": entries or existing_artifact_entries()}, sort_keys=True, indent=2),
        encoding="utf-8",
    )
    return manifest_path


def existing_artifact_entries() -> list[dict[str, Any]]:
    return [
        {
            "artifact_key": "diagnostics_summary",
            "artifact_path": "docs/REVIEW_BUNDLES.md",
            "artifact_role": "tiny_fixture_reference",
            "content_hash": "",
            "warnings": (),
        }
    ]


def build_fixture_bundle(tmp_path: Path, *, run_id: str = "review_bundle_fixture") -> ReviewBundle:
    run_manifest = write_run_manifest(tmp_path, run_manifest_payload(run_id))
    artifact_manifest = write_artifact_manifest(tmp_path)
    return build_review_bundle(
        run_id=run_id,
        registry_records=(registry_record(run_id),),
        artifact_manifest=artifact_manifest,
        run_manifest=run_manifest,
        source_root=REPO_ROOT,
    )
