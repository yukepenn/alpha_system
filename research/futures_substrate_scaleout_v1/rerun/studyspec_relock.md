# FUTSUB-P27 Core Pilot StudySpec Re-lock Report

Value-free report for `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` / `FUTSUB-P27`. The original Core Pilot StudySpecs under `research/futures_core_alpha_pilot_v1/**` were read as inputs only; the re-issued locks live under `research/futures_substrate_scaleout_v1/rerun/study_specs/`.

## Result

StudySpec resolver-smoke: PASS

- Original accepted StudySpecs classified: 10
- Re-locked StudySpecs written: 8
- Named gaps retained: 2
- Feature locks resolved for committed re-locks: 3408
- Label locks resolved for committed re-locks: 648
- `alpha_system.governance.feature_lock_validation.validate_feature_locks`: PASS for 3408 committed feature locks
- Deliberate unresolvable probe: PASS, resolver returned `feature_pack_not_found` for `fver_0000000000000000000000000000000000000000000000000000000000000000`
- DatasetVersion policy: all committed locks point to `ACCEPTED` or `ACCEPTED_WITH_WARNINGS` DatasetVersions for 2019-2026; values and registries remain local-only under `ALPHA_DATA_ROOT`

The smoke used `runtime.input_resolver.FeatureLabelPackResolver.resolve_feature_packs` and `resolve_label_packs` for every committed lock. It checked exact IDs, lifecycle state, expected DatasetVersion, expected partition, expected FeatureRequest or LabelSpec, and local Parquet file presence under `ALPHA_DATA_ROOT`; no feature, label, market, return, signal, or cost values are embedded here.

## Per-StudySpec Summary

| Original StudySpec | Re-lock StudySpec | Prior state | Family | Targets | Horizons | Feature locks | Label locks | P28 scope |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sspec_dde3e64667fe158f9bad527d | sspec_44c3ee4595987af664e7c0d7 | REJECT | cross_market | NQ,ES | 5m,10m,30m | 248 | 48 | audit-only |
| sspec_c671fbeeb143512cbc03bc5b | sspec_983a98603f6369127405cb33 | REJECT | cross_market | NQ,ES,RTY | 5m,10m,30m | 328 | 72 | audit-only |
| sspec_90b28233d828128664588a9a | sspec_b5ed14fe095c6eeeb1def00e | REJECT | cross_market | RTY,ES,NQ | 5m,10m,15m,30m | 328 | 96 | audit-only |
| sspec_7c8fb13628843890c171b122 | sspec_88a1be32841d4fd955e3f5ee | REJECT | cross_market | NQ,ES | 5m,10m,30m | 248 | 48 | audit-only |
| sspec_69c22ec5847395ac8e81b5b6 | sspec_b780acc576267566cabfe28a | INCONCLUSIVE | vwap_session | ES,NQ,RTY | 5m,10m,15m,30m | 528 | 96 | yes |
| sspec_aff70fcbc4b7ff226fcc8149 | sspec_1d54b7d14ae9c4a1d7453a81 | INCONCLUSIVE | vwap_session | ES,NQ,RTY | 5m,10m,15m,30m | 528 | 96 | yes |
| sspec_267cc052e37668339c38d179 | named_gap | INCONCLUSIVE | regime | ES,NQ,RTY | 5m,10m,15m,30m | 504 | 96 | blocked |
| sspec_27bf1262b0bd23d27191cc86 | sspec_cde8480dfa70919cfdf224f4 | INCONCLUSIVE | liquidity_pa | ES,NQ,RTY | 5m,10m,15m,30m | 600 | 96 | yes |
| sspec_02c400a561891171a33c0c66 | sspec_b3b188f263c9abbc128faa80 | INCONCLUSIVE | liquidity_pa | ES,NQ,RTY | 5m,10m,15m,30m | 600 | 96 | yes |
| sspec_9f6f741192a4b534f06e51c0 | named_gap | INCONCLUSIVE | bbo_tradability | ES,NQ,RTY | 5m,10m,15m,30m | 648 | 96 | blocked |

## Resolvable-Study List

| Previously INCONCLUSIVE StudySpec | Family | Classification | Counts | Gap or evidence |
| --- | --- | --- | --- | --- |
| sspec_69c22ec5847395ac8e81b5b6 | vwap_session | RELOCKED -> sspec_b780acc576267566cabfe28a | F=528; L=96 | resolved_by_runtime_resolver_and_feature_lock_validator |
| sspec_aff70fcbc4b7ff226fcc8149 | vwap_session | RELOCKED -> sspec_1d54b7d14ae9c4a1d7453a81 | F=528; L=96 | resolved_by_runtime_resolver_and_feature_lock_validator |
| sspec_267cc052e37668339c38d179 | regime | GAPPED | F_attempted=504; L_attempted=96 | liquidity_structure_range_contraction/fver_96c95feb85d852292f8e9452393a626caa40cc9a106e8d110a9a5264912e322f/ES_2019_full_year: label_as_feature_input:feature_pack_refs[0]:session_label; liquidity_structure_range_contraction/fver_051bd83bbdce0ffb2ddde58d4f9c4c0174ffa7c164e6105c1d9321daf4591247/ES_2020_full_year: label_as_feature_input:feature_pack_refs[0]:session_label; liquidity_structure_range_contraction/fver_21e089f5db0c2733380aba20343b7ae680d9b5c8f1228fd6ce1d30fb46841863/ES_2021_full_year: label_as_feature_input:feature_pack_refs[0]:session_label |
| sspec_27bf1262b0bd23d27191cc86 | liquidity_pa | RELOCKED -> sspec_cde8480dfa70919cfdf224f4 | F=600; L=96 | resolved_by_runtime_resolver_and_feature_lock_validator |
| sspec_02c400a561891171a33c0c66 | liquidity_pa | RELOCKED -> sspec_b3b188f263c9abbc128faa80 | F=600; L=96 | resolved_by_runtime_resolver_and_feature_lock_validator |
| sspec_9f6f741192a4b534f06e51c0 | bbo_tradability | GAPPED | F_attempted=648; L_attempted=96 | bbo_tradability_spread_zscore/fver_e9f8d217c136b5d604242337f982d3a226914d4e8fcbd3b8a3197f404b3f2585/ES_2019_full_year: label_as_feature_input:feature_pack_refs[0]:session_label; bbo_tradability_spread_zscore/fver_c2d010f12dc4170229ab78a5faa1fcdfa1d74ab055456fffb96a0a08d8236243/ES_2020_full_year: label_as_feature_input:feature_pack_refs[0]:session_label; bbo_tradability_spread_zscore/fver_60583fbcf7a4775fbcabf9021008053a6aa2017c65d1212044f9e68a27e52d89/ES_2021_full_year: label_as_feature_input:feature_pack_refs[0]:session_label |

P28 may re-run only the prior-INCONCLUSIVE StudySpecs classified above as `RELOCKED`: `sspec_69c22ec5847395ac8e81b5b6`, `sspec_aff70fcbc4b7ff226fcc8149`, `sspec_27bf1262b0bd23d27191cc86`, and `sspec_02c400a561891171a33c0c66`. The four prior-REJECT cross-market StudySpecs are re-locked for a complete audit baseline, not for a new promotion decision in P28.

## Named Gaps

- `sspec_267cc052e37668339c38d179` (`regime`): `regime_volatility_compression` includes `liquidity_structure_range_contraction` records that fail closed in `resolve_feature_packs` with `label_as_feature_input` because `session_label` is present as an input field without the accepted session metadata role marker on those current records. Attempted locks: 504 feature, 96 label.
- `sspec_9f6f741192a4b534f06e51c0` (`bbo_tradability`): `bbo_tradability_top_book` includes `bbo_tradability_spread_zscore` records that fail closed in `resolve_feature_packs` with `label_as_feature_input` for the same `session_label` role condition. Attempted locks: 648 feature, 96 label.

These are explicit substrate/tooling gaps. This phase did not materialize replacements, mutate registries, hand-patch lock JSON, or weaken resolver semantics.

## Contract Notes

- Held fixed: `alpha_spec_id`, top-level `label_spec_id`, `split_protocol`, metrics, costs, variant budget, locked-test policy, negative controls, and stopping rules.
- Re-issued: dataset-scope DatasetVersion locks, feature pack locks, label pack locks, and StudyInputPack references.
- The top-level `StudySpec.label_spec_id` remains the original Core Pilot governance anchor. Dataset-scope label locks carry the current per-year registry `label_spec_id` values required by the live `lver_...` identities.
- Re-lock artifacts are value-free. Local resolver paths and raw/materialized values are not committed.
- FUTSUB-P28 inherits the P24/P25 walk-forward and N_eff context documented in `docs/futures_substrate_scaleout/WALK_FORWARD_WIRING.md` and `docs/futures_substrate_scaleout/N_EFF.md`.
