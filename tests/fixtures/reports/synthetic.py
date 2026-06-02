"""Tiny deterministic report fixtures."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def diagnostic_summary(
    *,
    factor_id: str = "fixture_close_delta",
    factor_version: str = "factor:v1",
    label_version: str = "label:v1",
    data_version: str = "data:v1",
    sample_size: int = 42,
) -> dict[str, Any]:
    """Return a synthetic DiagnosticSummary-shaped mapping."""
    return {
        "run_id": f"study_{factor_id}",
        "study_id": "synthetic_report_study",
        "factor_id": factor_id,
        "factor_version": factor_version,
        "label_id": "forward_return_1m",
        "label_version": label_version,
        "data_version": data_version,
        "engine_version": "intraday_factor_diagnostics_v1",
        "sample_size": sample_size,
        "missing_label_count": 1,
        "missing_factor_count": 0,
        "warnings": ("synthetic warning for review",),
        "diagnostics": {
            "directional": {
                "pearson_ic": {"ic": 0.12, "n": sample_size},
                "rank_ic": {"ic": 0.1, "n": sample_size},
                "icir": {"icir": 0.5, "n": sample_size},
            },
            "events": {
                "sample_size": {"n": sample_size},
                "event_study": {"event_count": 7, "n": sample_size},
                "false_breakout_rate": {"rate": 0.2, "n": sample_size},
            },
            "buckets": {
                "bucket_monotonicity": {"is_monotonic": False, "n": sample_size},
                "tail_expectancy": {"left": -0.01, "right": 0.02},
            },
            "stability": {
                "time_of_day": {
                    "09:30": {"n": 21, "mean_forward_return": 0.001, "pearson_ic": 0.1},
                    "10:30": {"n": 21, "mean_forward_return": -0.001, "pearson_ic": -0.02},
                },
                "session_segment": {
                    "segment_1": {"n": 14, "mean_forward_return": 0.0, "pearson_ic": 0.05},
                    "segment_2": {"n": 14, "mean_forward_return": 0.001, "pearson_ic": 0.1},
                    "segment_3": {"n": 14, "mean_forward_return": -0.001, "pearson_ic": -0.03},
                },
                "monthly": {
                    "2026-01": {"n": 20, "mean_forward_return": 0.002, "pearson_ic": 0.12},
                    "2026-02": {"n": 22, "mean_forward_return": -0.001, "pearson_ic": 0.01},
                },
                "volatility_regime": {
                    "low": {"n": 20, "mean_forward_return": 0.001, "pearson_ic": 0.08},
                    "high": {"n": 22, "mean_forward_return": -0.002, "pearson_ic": -0.04},
                },
                "liquidity_regime": {
                    "deep": {"n": 24, "mean_forward_return": 0.001, "pearson_ic": 0.09},
                    "thin": {"n": 18, "mean_forward_return": -0.001, "pearson_ic": -0.01},
                },
            },
            "correlation_to_existing_factors": {
                "fixture_momentum": {"pearson": 0.2, "rank": 0.18, "n": sample_size}
            },
            "factor_cluster_id": "cluster_01",
        },
    }


def report_metadata() -> dict[str, str]:
    """Return synthetic reproducibility metadata for reports."""
    return {
        "run_manifest_path": "artifacts/factor_studies/run_manifest.json",
        "code_hash_ref": "code:abc123",
        "config_hash_ref": "config:def456",
        "no_lookahead_validation_status": "passed",
        "review_status": "review_pending",
        "factor_label_alignment_status": "matched",
    }


def without_diagnostic(summary: dict[str, Any], *path: str) -> dict[str, Any]:
    """Return a copy with a nested diagnostic field removed."""
    output = deepcopy(summary)
    active: dict[str, Any] = output
    for key in path[:-1]:
        active = active[key]
    active.pop(path[-1], None)
    return output
