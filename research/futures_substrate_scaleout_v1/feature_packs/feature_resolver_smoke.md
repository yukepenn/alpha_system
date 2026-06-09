# Feature Resolver Smoke

Value-free resolver smoke for `FUTSUB-P14`. It resolves representative feature locks through the runtime resolver and verifies the corresponding current trusted-config registry rows are backed by current Parquet sidecars without reading feature values.

- Generated: `2026-06-09T19:39:12+00:00`
- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase: `FUTSUB-P14`
- Overall status: `PASS`
- Resolver: `alpha_system.runtime.input_resolver.FeatureLabelPackResolver.resolve_feature_packs`
- Fail-closed probe: absent exact `fver_...` lock returned code `feature_pack_not_found`
- Fail-closed message: `FeatureStore did not resolve the requested feature pack`
- Trusted session representative: `session_calendar_roll_session_id` (not `session_calendar_roll_bars_to_roll` or `session_calendar_roll_minutes_to_roll`)

## Representative Locks

| Family | Feature id | FeatureVersion | DatasetVersion | Partition | Rows | Available ts | Status |
| --- | --- | --- | --- | --- | ---: | --- | --- |
| base_ohlcv | base_ohlcv_log_returns | fver_3215a58d2c8c92afa1c5748bb68771f957697e837625f5fced0907825fd839a3 | dsv_databento_ohlcv_05404069799decb0 | NQ_2024_full_year | 346992 | 2024-01-01T23:01:05+00:00 -> 2024-12-31T22:00:05+00:00 | PASS |
| session_calendar_maintenance | session_calendar_roll_session_id | fver_c4a5b31ab6cf2a4b2d153fa40ee6cf52cdb4710437418c549a01af274cc6637e | dsv_databento_ohlcv_dense_2024_v1 | NQ_2024_full_year | 347085 | 2024-01-01T23:01:05+00:00 -> 2024-12-31T22:00:05+00:00 | PASS |
| vwap_session_auction | base_ohlcv_anchored_vwap | fver_00315e11d199109b128f78651315231231de90c07bc76da7b925c5321ddd35fe | dsv_databento_ohlcv_05404069799decb0 | RTY_2024_full_year | 333540 | 2024-01-01T23:01:05+00:00 -> 2024-12-31T22:00:05+00:00 | PASS |
| regime_volatility_compression | base_ohlcv_returns | fver_bb016b77709e32d912ec2c35b1b3a23fc024a5c18c3b29dc0dddd8ddb033be5b | dsv_databento_ohlcv_05404069799decb0 | ES_2024_full_year | 346858 | 2024-01-01T23:01:05+00:00 -> 2024-12-31T22:00:05+00:00 | PASS |
| liquidity_sweep_pa_structure | liquidity_structure_close_location_value | fver_112edf3ee4994d9b63a1a6524827a17af52a7d18d4cc13a6726b458ac104ce3d | dsv_databento_ohlcv_05404069799decb0 | ES_2024_full_year | 346858 | 2024-01-01T23:01:05+00:00 -> 2024-12-31T22:00:05+00:00 | PASS |
| volume_activity | base_ohlcv_range_position | fver_3c166eb0eeae1b4ccd82380d54bc7a4f2d5926935327955d85a0f161c1148454 | dsv_databento_ohlcv_05404069799decb0 | ES_2024_full_year | 346858 | 2024-01-01T23:01:05+00:00 -> 2024-12-31T22:00:05+00:00 | PASS |
| bbo_tradability_top_book | bbo_tradability_bad_quote_flag | fver_024ed7e353c75c3108667bc029050ca7d673389df98b67ee6415de624317a4af | dsv_databento_bbo_f9e1d70a04d9dae4 | NQ_2024_full_year | 346992 | 2024-01-01T23:01:05+00:00 -> 2024-12-31T22:00:05+00:00 | PASS |
| cross_market_alignment | cross_market_confirmation_flag | fver_b9d318eb8342a911c191d0622b869d17255702b3183351a0bb45fdeb0e0c31aa | dsv_databento_ohlcv_dense_2024_v1 | ES_NQ_RTY_2024_full_year | 347084 | 2024-01-01T23:01:05+00:00 -> 2024-12-31T22:00:05+00:00 | PASS |

## Checks

- Every representative lock resolved by exact `feature_version_id`; no fuzzy name fallback was used.
- Every resolved handle matched the expected DatasetVersion, FeatureRequest id, and partition id.
- Every representative registry row referenced a local Parquet store with a sidecar content hash matching the registry record.
- The stale/absent exact-lock probe failed closed with `feature_pack_not_found`.
- `session_label` is accepted only as session metadata when explicit `field_roles` or a generic `session_metadata_role: SESSION_METADATA_POINT_IN_TIME` marker can be converted into `SESSION_METADATA` field roles; arbitrary unrole-tagged live feature inputs remain fail-closed.
- Offline-only session roll countdown features are not used as trusted resolver-smoke representatives.

## Issues

- None.
