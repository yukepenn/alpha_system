# Cross-Market Diagnostics

`FUTCORE-P16` records value-free cross-market diagnostics for the four
approved `cross_market` StudySpecs from `FUTCORE-P14`.

Reports:

| StudySpec | Category | Report |
| --- | --- | --- |
| `sspec_ac883ec0b962f4ae4f25e190` | lead-lag | `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/sspec_ac883ec0b962f4ae4f25e190.json` |
| `sspec_16f6de31387d8289d0fbb394` | beta-residual | `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/sspec_16f6de31387d8289d0fbb394.json` |
| `sspec_fc7b0408e59a83f2e69714d3` | rotation | `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/sspec_fc7b0408e59a83f2e69714d3.json` |
| `sspec_6fe5fa12b333d19ea95915d2` | confirmation-divergence | `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/sspec_6fe5fa12b333d19ea95915d2.json` |

Directory index:

- `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/INDEX.md`

Runtime outcome: all four StudySpecs reached the Research Runtime diagnostics,
signal-probe, and cost surfaces. The cross-market alignment diagnostic rejected
the runs because the locked materialized packs supplied ES observations only;
NQ and RTY observations were absent, so no aligned ES/NQ/RTY snapshot was
created. The runtime did not infer, forward-fill, or reuse another
instrument's values.

The reports contain scalar summaries, ids, hashes, statuses, and limitations
only. They make no promotion decision and record no paper/live/broker/order
action.
