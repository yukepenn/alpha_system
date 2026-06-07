# Cross-Market Diagnostics

`FUTCORE-P16` records value-free cross-market diagnostics for the four current
approved `cross_market` StudySpecs from `FUTCORE-P14`, with `FUTCORE-P15`
minimal primitive records treated as input-binding context only.

Reports:

| StudySpec | Category | Runtime outcome | Report |
| --- | --- | --- | --- |
| `sspec_dde3e64667fe158f9bad527d` | lead-lag | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` | `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/sspec_dde3e64667fe158f9bad527d.json` |
| `sspec_c671fbeeb143512cbc03bc5b` | beta-residual | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` | `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/sspec_c671fbeeb143512cbc03bc5b.json` |
| `sspec_90b28233d828128664588a9a` | rotation | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` | `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/sspec_90b28233d828128664588a9a.json` |
| `sspec_7c8fb13628843890c171b122` | confirmation-divergence | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` | `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/sspec_7c8fb13628843890c171b122.json` |

Directory index:

- `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/INDEX.md`

Runtime outcome: all four StudySpecs reached the Research Runtime input
resolver, cross-market diagnostics, factor diagnostics, label diagnostics,
signal-probe, and cost-stress surfaces. The registry-resolved materialized
packs exposed ES observations in the diagnostics view but no NQ or RTY value
rows, so no aligned ES/NQ/RTY snapshot was created. The runtime did not infer,
forward-fill, or reuse another instrument's values.

The reports include timestamp-alignment summaries per instrument pair and
cross-market missingness splits by required instrument and session view. Cost
diagnostics cover `base`, `stress_1`, `stress_2`, and `double_cost`; `zero_cost`
is recorded as diagnostic-only and not a promotion basis.

The `sspec_90b28233d828128664588a9a` primary `15m` horizon still has a P15
LabelSpec record but no locked materialized Parquet LabelPack in the P03/P14
input pack. The report records that limitation without substituting an unlocked
15m pack.

The reports contain scalar summaries, ids, hashes, statuses, and limitations
only. They make no promotion decision and record no paper/live/broker/order
action.
