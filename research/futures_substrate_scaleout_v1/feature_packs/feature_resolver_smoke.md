# Feature Resolver Smoke

Value-free resolver smoke for `FUTSUB-P14`. It resolves representative feature locks through the runtime resolver and verifies the corresponding registry rows are backed by current Parquet sidecars without reading feature values.

- Generated: `2026-06-09T15:46:00+00:00`
- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase: `FUTSUB-P14`
- Overall status: `PASS`
- Resolver: `alpha_system.runtime.input_resolver.FeatureLabelPackResolver.resolve_feature_packs`
- Fail-closed probe: absent exact `fver_...` lock returned code `feature_pack_not_found`
- Fail-closed message: `FeatureStore did not resolve the requested feature pack`

## Representative Locks

| Family | Feature id | FeatureVersion | DatasetVersion | Partition | Rows | Available ts | Status |
| --- | --- | --- | --- | --- | ---: | --- | --- |
| base_ohlcv | base_ohlcv_log_returns | fver_3215a58d2c8c92afa1c5748bb68771f957697e837625f5fced0907825fd839a3 | dsv_databento_ohlcv_05404069799decb0 | NQ_2024_full_year | 346992 | 2024-01-01T23:01:05+00:00 -> 2024-12-31T22:00:05+00:00 | PASS |
| session_calendar_maintenance | session_calendar_roll_bars_to_roll | fver_3afd64e2e01a6491901a50e7396115e7484d93562b8032e21e2db552ef52706b | dsv_databento_ohlcv_dense_2024_v1 | NQ_2024_full_year | 347085 | 2024-01-01T23:01:05+00:00 -> 2024-12-31T22:00:05+00:00 | PASS |
| vwap_session_auction | base_ohlcv_anchored_vwap | fver_00315e11d199109b128f78651315231231de90c07bc76da7b925c5321ddd35fe | dsv_databento_ohlcv_05404069799decb0 | RTY_2024_full_year | 333540 | 2024-01-01T23:01:05+00:00 -> 2024-12-31T22:00:05+00:00 | PASS |
| regime_volatility_compression | base_ohlcv_atr | fver_01b55b064ce54ec0f3757fb2befd4316c6ecdd3cb54dfff6c29914be486f04db | dsv_databento_ohlcv_05404069799decb0 | ES_2024_full_year | 346858 | 2024-01-01T23:01:05+00:00 -> 2024-12-31T22:00:05+00:00 | PASS |
| liquidity_sweep_pa_structure | liquidity_structure_close_location_value | fver_112edf3ee4994d9b63a1a6524827a17af52a7d18d4cc13a6726b458ac104ce3d | dsv_databento_ohlcv_05404069799decb0 | ES_2024_full_year | 346858 | 2024-01-01T23:01:05+00:00 -> 2024-12-31T22:00:05+00:00 | PASS |
| volume_activity | base_ohlcv_range_position | fver_3c166eb0eeae1b4ccd82380d54bc7a4f2d5926935327955d85a0f161c1148454 | dsv_databento_ohlcv_05404069799decb0 | ES_2024_full_year | 346858 | 2024-01-01T23:01:05+00:00 -> 2024-12-31T22:00:05+00:00 | PASS |
| bbo_tradability_top_book | bbo_tradability_bad_quote_flag | fver_024ed7e353c75c3108667bc029050ca7d673389df98b67ee6415de624317a4af | dsv_databento_bbo_f9e1d70a04d9dae4 | NQ_2024_full_year | 346992 | 2024-01-01T23:01:05+00:00 -> 2024-12-31T22:00:05+00:00 | PASS |
| cross_market_alignment | cross_market_confirmation_flag | fver_b9d318eb8342a911c191d0622b869d17255702b3183351a0bb45fdeb0e0c31aa | dsv_databento_ohlcv_dense_2024_v1 | ES_NQ_RTY_2024_full_year | 347084 | 2024-01-01T23:01:05+00:00 -> 2024-12-31T22:00:05+00:00 | PASS |

## Checks

- Every representative lock resolved by exact `feature_version_id`; no fuzzy name fallback was used.
- Every resolved handle matched the expected DatasetVersion, FeatureRequest id, and partition id.
- Every representative registry row referenced a local Parquet store with a sidecar content hash matching the registry record.
- The stale/absent lock probe failed closed with `feature_pack_not_found`.
- `session_label` is accepted only as session metadata when explicit `field_roles` or a generic `session_metadata_role: SESSION_METADATA_POINT_IN_TIME` marker can be converted into `SESSION_METADATA` field roles; arbitrary unrole-tagged live feature inputs remain fail-closed.

## Issues

- None.
