# FUTCORE-P16 Cross-Market Diagnostics Reports

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`
Phase: `FUTCORE-P16`
Artifact type: value-free runtime diagnostics report index

The reports in this directory were produced through the Research Runtime tool surface from registry-resolved locked pack references. They contain scalar summaries, ids, hashes, statuses, and limitations only; no row-level market, feature, label, signal, provider, registry, or local Parquet payloads are embedded.

| StudySpec | AlphaSpec | Category | Runtime outcome | Required symbols observed | Report |
| --- | --- | --- | --- | --- | --- |
| `sspec_dde3e64667fe158f9bad527d` | `aspec_0ebd90cecfd475607685b445` | `lead_lag` | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` | ES | [`sspec_dde3e64667fe158f9bad527d.json`](sspec_dde3e64667fe158f9bad527d.json) |
| `sspec_c671fbeeb143512cbc03bc5b` | `aspec_8d9e272e4b78eedcd27f0bec` | `beta_residual` | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` | ES | [`sspec_c671fbeeb143512cbc03bc5b.json`](sspec_c671fbeeb143512cbc03bc5b.json) |
| `sspec_90b28233d828128664588a9a` | `aspec_a41dcccac5552de945aba825` | `rotation` | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` | ES | [`sspec_90b28233d828128664588a9a.json`](sspec_90b28233d828128664588a9a.json) |
| `sspec_7c8fb13628843890c171b122` | `aspec_fa4895a43a80d4eef0a607a4` | `confirmation_divergence` | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` | ES | [`sspec_7c8fb13628843890c171b122.json`](sspec_7c8fb13628843890c171b122.json) |

Family-level result: all four current `cross_market` StudySpecs reached the runtime input resolver, cross-market diagnostics, factor diagnostics, label diagnostics, signal-probe, and cost-stress surfaces. The registry-resolved materialized packs exposed ES observations in the diagnostics view but no NQ or RTY value rows, so cross-market alignment rejected the family diagnostics for missing cross-market legs rather than inferring, forward-filling, or reusing another instrument's values.

The `sspec_90b28233d828128664588a9a` primary `15m` horizon still has a P15 LabelSpec record but no locked materialized Parquet LabelPack in the P03/P14 input pack; the report records that limitation without substituting an unlocked 15m pack.

No promotion, ranking, watch state, candidate state, strategy validation, paper/live/broker action, PR, merge, review artifact, or verdict is recorded here.
