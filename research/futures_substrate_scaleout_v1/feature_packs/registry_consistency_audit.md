# FeaturePack Registry Consistency Audit

Value-free registry audit for `FUTSUB-P14`. It contains metadata, counts, ids, and PASS/FAIL status only; no feature values, provider responses, SQLite payloads, or Parquet contents are embedded.

- Generated: `2026-06-09T15:23:04+00:00`
- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase: `FUTSUB-P14`
- Overall status: `PASS`
- Producer engine required: `alpha_system.features.fast.pack_materializer.v1`
- Value schema required: `alpha_system.features.fast.values.v1`
- Eligible DatasetVersion states: `ACCEPTED`, `ACCEPTED_WITH_WARNINGS`
- 2018 blocked DatasetVersions are excluded by the acceptance-lock policy; no 2018 feature units are registered in this audit.

## Family Summary

| Family | Accepted units | Completed | Skipped | Failed | Registry records | Materialized units | Feature ids | DatasetVersions | Value rows | States | Producer | Parquet hash |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base_ohlcv | 24 | 21 | 3 | 0 | 144 | 24 | 6 | 8 | 46102260 | ACCEPTED, ACCEPTED_WITH_WARNINGS | V1 fast | PASS |
| session_calendar_maintenance | 24 | 21 | 3 | 0 | 240 | 24 | 10 | 8 | 78487950 | ACCEPTED, ACCEPTED_WITH_WARNINGS | V1 fast | PASS |
| vwap_session_auction | 24 | 21 | 3 | 0 | 144 | 24 | 6 | 8 | 46102260 | ACCEPTED, ACCEPTED_WITH_WARNINGS | V1 fast | PASS |
| regime_volatility_compression | 24 | 21 | 3 | 0 | 120 | 24 | 5 | 8 | 38418550 | ACCEPTED, ACCEPTED_WITH_WARNINGS | V1 fast | PASS |
| liquidity_sweep_pa_structure | 24 | 21 | 3 | 0 | 216 | 24 | 9 | 8 | 69153390 | ACCEPTED, ACCEPTED_WITH_WARNINGS | V1 fast | PASS |
| volume_activity | 24 | 21 | 3 | 0 | 192 | 24 | 8 | 8 | 61469680 | ACCEPTED, ACCEPTED_WITH_WARNINGS | V1 fast | PASS |
| bbo_tradability_top_book | 24 | 21 | 3 | 0 | 264 | 24 | 11 | 8 | 84520810 | ACCEPTED, ACCEPTED_WITH_WARNINGS | V1 fast | PASS |
| cross_market_alignment | 8 | 7 | 1 | 0 | 88 | 8 | 11 | 8 | 28778827 | ACCEPTED, ACCEPTED_WITH_WARNINGS | V1 fast | PASS |

## Checks

- Keystone identity: every audited registry row resolves by exact `feature_version_id` and carries a registered FeatureSpec-derived identity.
- Content hash: every audited Parquet sidecar manifest matches the registry `value_content_hash`.
- Provenance: every audited row uses the V1 fast producer engine; no reference/V1 mixing was detected inside any family.
- Dataset gate: every audited row traces to `ACCEPTED` or `ACCEPTED_WITH_WARNINGS` DatasetVersion metadata.
- Store format: every audited row is Parquet-backed; JSONL remains smoke/audit tier only.
- BBO semantics: `bbo_tradability_top_book` is represented as a time-sampled, forward-filled tradability proxy; this report makes no execution-truth claim.
- Cross-market semantics: `cross_market_alignment` registers one ES/NQ/RTY aligned panel unit per accepted year and preserves per-instrument availability metadata by policy.

## Issues

- None.
