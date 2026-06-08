# Feature Compute Fast Path

This directory is the durable documentation index for
`FEATURE_COMPUTE_FAST_PATH_V1`.

- `OVERVIEW.md` summarizes the campaign purpose, parity-first discipline, and
  hard boundaries.
- `PACK_MATERIALIZER.md` documents the P01 fast engine contract, identity
  guarantee, persistence path, parity harness, and optional-dependency policy.
- `ENGINE_PROVENANCE_RECONCILIATION.md` documents the P12
  `producer_engine_id` / `value_schema_version` registry provenance fields and
  the no-silent-engine-mixing reconciliation policy.
- `TARGETED_SCALEOUT.md` documents the P11 targeting flags, dry-run estimate,
  execute-selected-only contract, and skip-completed semantics.
- `campaigns/FEATURE_COMPUTE_FAST_PATH_V1/` contains the authoritative campaign
  contract bundle and per-phase plan.
- `research/feature_compute_fast_path_v1/` is the value-free evidence root for
  later parity, benchmark, and reconciliation summaries.

`FCFP-P01` adds the `src/alpha_system/features/fast/` engine core and the
synthetic reference-parity harness under `tests/unit/feature_compute_fast_path/`.
It adds no production family pack, no CLI command, no real-data backfill, no
feature/label values, no broker/live/paper behavior, and no heavy artifacts.

`FCFP-P02` adds the first production family pack, `base_ohlcv`, under
`src/alpha_system/features/fast/`. Its synthetic parity test covers the six
governed Base OHLCV features and its value-free report lives under
`research/feature_compute_fast_path_v1/parity/base_ohlcv/`.

`FCFP-P03` adds the `session_calendar_roll` pack for the governed Session /
Calendar / Roll family. Its synthetic parity test covers exact integer/string
values, row timing, entity ids, feature-version identity, sorted quality flags,
RTH/ETH session edges, roll proximity, synthetic no-trade position-only flags,
and absent optional expiration/status metadata.

`FCFP-P04` adds the `vwap_session_auction` pack for the governed VWAP /
session-auction features in the Base OHLCV reference family. Its synthetic
parity test covers session-reset VWAP, RTH-anchored VWAP, distance to VWAP,
opening range, overnight range, the RTH opening-window boundary, ETH-to-RTH
overnight carry, and exact gap reasons including `zero_vwap`.

`FCFP-P05` adds the `regime_vol_compression` pack for governed ATR,
trendiness, and range-contraction features. Its synthetic parity test covers
reset-on-session rolling warm-up, a no-trade input gap, flat-close
`zero_movement` trendiness gaps, and the structure-family exclusive
prior-window range-contraction path.

`FCFP-P06` adds the `liquidity_pa_structure` pack for governed liquidity-sweep
and price-action structure primitives. Its synthetic parity test covers prior
extremes, opening-range distances, sweep and failed-breakout flags,
close-location value, wick rejection, range contraction, session resets,
input gaps, and zero-range guards.

`FCFP-P07` adds the `volume_activity` pack as a composite over existing
governed OHLCV and structure primitives: rolling volume, volume z-score,
session minute, rolling range, range position, trendiness, close-location
value, and wick rejection. Its synthetic parity test covers reset-on-session
rolling warm-up, an input gap, session-boundary reset behavior, zero-range
structure guards, values, availability, quality flags, and reference identity.

`FCFP-P08` adds the `bbo_tradability` pack for governed BBO tradability /
top-book proxy features. Its synthetic parity test covers spread, top-book
depth and imbalance, microprice, missing/quarantined BBO flags, wide-spread and
low-depth flags, session-reset spread z-score behavior, availability, quality
flags, and reference identity.

`FCFP-P09` adds the `cross_market` aligned-panel pack for the governed
ES/NQ/RTY Cross-Market family. Its synthetic parity test covers the
`strict_intersection` no-forward-fill policy, max-across-instruments
`available_ts`, optional exact-time BBO flags, no-trade and session-reset return
gaps, rolling beta-residual / correlation gap rows, and reference identity.

`FCFP-P11` adds targeted / incremental selection to `alpha scaleout
feature-pack`. Materialization can be selected by family, feature id, configured
feature group, label selector, symbols, years, and DatasetVersion ids. Dry-run
emits value-free unit, row, and time estimates; execute mode runs selected units
only; completed units are skipped through checkpoint plus official registry
truth.
`FCFP-P10` adds `src/alpha_system/labels/fast/`, including the V1
multi-horizon fixed-horizon label pack and label materializer. Its synthetic
parity test covers every currently governed fixed-horizon close and midprice
label, exact `label_available_ts`, terminal-row exclusion, gap / guard flags,
reference `label_version_id` identity, value-free N_eff / horizon-overlap
metadata, and serial `LabelRegistry` registration through the existing label
keystone path. Longer ungoverned horizons remain a governance gap.

`FCFP-P12` records feature producer provenance as a first-class registry record
field, keeps value-schema versioning separate from identity, and defines the
reference-output reconciliation policy. Existing valid reference outputs remain
the parity reference when V1 is identical or within documented tolerance; beyond
tolerance blocks silent mixing until a V1 bug fix, explicit schema bump, or
official keystone re-materialization path is used.
