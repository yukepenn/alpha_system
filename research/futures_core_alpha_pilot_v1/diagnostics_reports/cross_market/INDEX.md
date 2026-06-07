# FUTCORE-P16 Cross-Market Diagnostics Reports

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`
Phase: `FUTCORE-P16`
Artifact type: value-free runtime diagnostics report index

The reports in this directory were produced through the Research Runtime tool surface from registry-resolved locked pack references. They contain scalar summaries, ids, hashes, statuses, and limitations only; no row-level market, feature, label, signal, or provider payloads are embedded.

| StudySpec | AlphaSpec | Category | Runtime outcome | Required symbols observed | Report |
| --- | --- | --- | --- | --- | --- |
| `sspec_ac883ec0b962f4ae4f25e190` | `aspec_0ebd90cecfd475607685b445` | `lead_lag` | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` | ES | [`sspec_ac883ec0b962f4ae4f25e190.json`](sspec_ac883ec0b962f4ae4f25e190.json) |
| `sspec_16f6de31387d8289d0fbb394` | `aspec_8d9e272e4b78eedcd27f0bec` | `beta_residual` | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` | ES | [`sspec_16f6de31387d8289d0fbb394.json`](sspec_16f6de31387d8289d0fbb394.json) |
| `sspec_fc7b0408e59a83f2e69714d3` | `aspec_a41dcccac5552de945aba825` | `rotation` | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` | ES | [`sspec_fc7b0408e59a83f2e69714d3.json`](sspec_fc7b0408e59a83f2e69714d3.json) |
| `sspec_6fe5fa12b333d19ea95915d2` | `aspec_fa4895a43a80d4eef0a607a4` | `confirmation_divergence` | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` | ES | [`sspec_6fe5fa12b333d19ea95915d2.json`](sspec_6fe5fa12b333d19ea95915d2.json) |

Family-level result: all four cross-market StudySpecs reached the runtime surfaces, but the locked materialized packs supplied ES observations only. Cross-market alignment therefore rejected the family diagnostics for missing NQ/RTY observations rather than inferring, forward-filling, or reusing another instrument's values.

No promotion, ranking, watch state, candidate state, strategy validation, paper/live/broker action, PR, merge, review artifact, or verdict is recorded here.
