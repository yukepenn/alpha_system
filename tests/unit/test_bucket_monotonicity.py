from __future__ import annotations

from alpha_system.research.buckets import bucket_forward_returns, bucket_monotonicity


def test_bucket_monotonicity_detects_increasing_profile() -> None:
    observations = [
        {"factor_value": index, "label_value": index / 100}
        for index in range(1, 7)
    ]

    buckets = bucket_forward_returns(observations, bucket_count=3)
    result = bucket_monotonicity(buckets)

    assert [bucket["n"] for bucket in buckets] == [2, 2, 2]
    assert result["is_monotonic"] is True
    assert result["direction"] == "increasing"


def test_bucket_monotonicity_detects_mixed_profile() -> None:
    result = bucket_monotonicity(
        [
            {"bucket": 1, "n": 2, "mean_return": 0.02},
            {"bucket": 2, "n": 2, "mean_return": -0.01},
            {"bucket": 3, "n": 2, "mean_return": 0.03},
        ]
    )

    assert result["is_monotonic"] is False
    assert result["sign_changes"] == 1
