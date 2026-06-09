# FeaturePack Registry Consistency Audit

Value-free registry audit for `FUTSUB-P14`. It contains metadata, counts, ids, and PASS/FAIL status only; no feature values, provider responses, SQLite payloads, or Parquet contents are embedded.

- Generated: `2026-06-09T19:39:12+00:00`
- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase: `FUTSUB-P14`
- Overall status: `PASS`
- Producer engine required: `alpha_system.features.fast.pack_materializer.v1`
- Value schema required: `alpha_system.features.fast.values.v1`
- Eligible DatasetVersion states: `ACCEPTED`, `ACCEPTED_WITH_WARNINGS`
- 2018 blocked DatasetVersions are excluded by the acceptance-lock policy; no current trusted-config 2018 feature units are registered in this audit.
- Trusted current-config registry rows audited: `1360`
- Offline-only session roll countdown rows not certified by this audit: `48`

## Family Summary

| Family | Accepted units | Trusted registry records | Materialized units | Feature ids | DatasetVersions | Value rows | States | Producer | Schema | Store | Lifecycle | Metadata | Parquet hash | Session marker |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| base_ohlcv | 24 | 144 | 24 | 6 | 8 | 46102260 | ACCEPTED, ACCEPTED_WITH_WARNINGS | PASS | PASS | PASS | PASS | PASS | PASS | n/a |
| session_calendar_maintenance | 24 | 192 | 24 | 8 | 8 | 62790360 | ACCEPTED, ACCEPTED_WITH_WARNINGS | PASS | PASS | PASS | PASS | PASS | PASS | PASS (192/192) |
| vwap_session_auction | 24 | 144 | 24 | 6 | 8 | 46102260 | ACCEPTED, ACCEPTED_WITH_WARNINGS | PASS | PASS | PASS | PASS | PASS | PASS | n/a |
| regime_volatility_compression | 24 | 120 | 24 | 5 | 8 | 38418550 | ACCEPTED, ACCEPTED_WITH_WARNINGS | PASS | PASS | PASS | PASS | PASS | PASS | n/a |
| liquidity_sweep_pa_structure | 24 | 216 | 24 | 9 | 8 | 69153390 | ACCEPTED, ACCEPTED_WITH_WARNINGS | PASS | PASS | PASS | PASS | PASS | PASS | PASS (216/216) |
| volume_activity | 24 | 192 | 24 | 8 | 8 | 61469680 | ACCEPTED, ACCEPTED_WITH_WARNINGS | PASS | PASS | PASS | PASS | PASS | PASS | n/a |
| bbo_tradability_top_book | 24 | 264 | 24 | 11 | 8 | 84520810 | ACCEPTED, ACCEPTED_WITH_WARNINGS | PASS | PASS | PASS | PASS | PASS | PASS | n/a |
| cross_market_alignment | 8 | 88 | 8 | 11 | 8 | 28778827 | ACCEPTED, ACCEPTED_WITH_WARNINGS | PASS | PASS | PASS | PASS | PASS | PASS | PASS (88/88) |

## Checks

- Keystone identity: every audited row is selected by the current scaleout config deterministic FeatureVersion preview and resolves by exact `feature_version_id`.
- Content hash: every audited Parquet sidecar manifest matches the registry `value_content_hash`.
- Provenance: every audited row uses the V1 fast producer engine; no reference/V1 mixing was detected in the trusted current-config rows.
- Dataset gate: every audited row traces to `ACCEPTED` or `ACCEPTED_WITH_WARNINGS` DatasetVersion metadata.
- Store format: every audited row is Parquet-backed; JSONL remains smoke/audit tier only.
- Session metadata role: `session_calendar_maintenance`, `liquidity_sweep_pa_structure`, and `cross_market_alignment` trusted rows carry `session_metadata_role: SESSION_METADATA_POINT_IN_TIME` in registry metadata.
- Session roll countdown features `session_calendar_roll_bars_to_roll` and `session_calendar_roll_minutes_to_roll` are offline-only/non-causal and are excluded from the trusted current-config audit and resolver-smoke representative set.
- BBO semantics: `bbo_tradability_top_book` is represented as a time-sampled, forward-filled tradability proxy; this report makes no execution-truth claim.
- Cross-market semantics: `cross_market_alignment` registers one ES/NQ/RTY aligned panel unit per accepted year and preserves per-instrument availability metadata by policy.

## Issues

- None.
