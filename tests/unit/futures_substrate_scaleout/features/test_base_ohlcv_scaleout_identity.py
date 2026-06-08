from __future__ import annotations

from dataclasses import replace

from alpha_system.cli.seed_pack import parse_seed_pack_config, preview_seed_feature_pack


def test_base_ohlcv_seed_identity_is_symbol_scoped_for_scaleout() -> None:
    config = parse_seed_pack_config(
        {
            "schema": "alpha_system.seed_pack.v1",
            "dataset_version_id": "dsv_databento_ohlcv_05404069799decb0",
            "symbol": "ES",
            "partition_id": "ES.2024.full_year",
            "partition_schema": "ohlcv_1m",
            "window": {
                "start_ts": "2024-01-01T00:00:00+00:00",
                "end_ts": "2025-01-01T00:00:00+00:00",
            },
            "feature_set": {
                "feature_set_id": "feature_set_futures_scaleout_base_ohlcv",
                "feature_set_version": "v1_es_2024",
                "alpha_spec_id": "aspec_af848bc999a4c4b11a421bd0",
                "features": [
                    {"name": "returns", "window_length": 1, "horizon": 1},
                    {"name": "rolling_volatility", "window_length": 20, "horizon": 1},
                ],
            },
        }
    )
    nq_config = replace(
        config,
        symbol="NQ",
        partition_id="NQ.2024.full_year",
        feature_set=replace(config.feature_set, feature_set_version="v1_nq_2024")
        if config.feature_set is not None
        else None,
    )

    es_preview = preview_seed_feature_pack(config)
    nq_preview = preview_seed_feature_pack(nq_config)

    assert es_preview["dataset_version_id"] == nq_preview["dataset_version_id"]
    assert set(es_preview["feature_version_ids"]).isdisjoint(
        set(nq_preview["feature_version_ids"])
    )
