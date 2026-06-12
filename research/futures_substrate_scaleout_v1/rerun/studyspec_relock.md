# P022000 Core Pilot StudySpec Re-lock Rerun Report

Value-free report for `P022000_FUTSUB_RELOCK_RERUN` in `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`. The original Core Pilot StudySpecs under `research/futures_core_alpha_pilot_v1/**` were read as inputs only; the re-issued locks live under `research/futures_substrate_scaleout_v1/rerun/study_specs/`.

## Result

StudySpec resolver-smoke: PASS

- Original accepted StudySpecs classified: 10
- Re-locked StudySpecs written: 10
- Named gaps retained: 0
- Prior-INCONCLUSIVE studies re-locked: 6/6
- Prior-REJECT cross-market audit-only re-locks: 4/4
- Feature locks resolved for committed re-locks: 4560
- Label locks resolved for committed re-locks: 840
- `alpha_system.governance.feature_lock_validation.validate_feature_locks`: PASS for 4560 committed feature locks
- Deliberate unresolvable probe: PASS, resolver returned `feature_pack_not_found` for `fver_0000000000000000000000000000000000000000000000000000000000000000`
- DatasetVersion policy: all committed locks point to `ACCEPTED` or `ACCEPTED_WITH_WARNINGS` DatasetVersions for 2019-2026; values and registries remain local-only under `ALPHA_DATA_ROOT`

The smoke used `runtime.input_resolver.FeatureLabelPackResolver.resolve_feature_packs` and `resolve_label_packs` for every committed lock, grouped by DatasetVersion and partition. It checked exact IDs, lifecycle state, expected DatasetVersion, expected partition, expected FeatureRequest or LabelSpec, and metadata required for local Parquet-backed values; no feature, label, market, return, signal, or cost values are embedded here.

## Per-StudySpec Summary

| Original StudySpec | Re-lock StudySpec | Prior state | Family | Targets | Horizons | Feature locks | Label locks | Classification | P28 scope |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- | --- |
| `sspec_dde3e64667fe158f9bad527d` | `sspec_da1bba367710c983b2ca644f` | REJECT | cross_market | NQ,ES | 5m,10m,30m | 248 | 48 | RELOCKED -> sspec_da1bba367710c983b2ca644f | audit-only |
| `sspec_c671fbeeb143512cbc03bc5b` | `sspec_cc38daf30253587e6dec3ab3` | REJECT | cross_market | NQ,ES,RTY | 5m,10m,30m | 328 | 72 | RELOCKED -> sspec_cc38daf30253587e6dec3ab3 | audit-only |
| `sspec_90b28233d828128664588a9a` | `sspec_d97a87458dbe72da1f27bfab` | REJECT | cross_market | RTY,ES,NQ | 5m,10m,15m,30m | 328 | 96 | RELOCKED -> sspec_d97a87458dbe72da1f27bfab | audit-only |
| `sspec_7c8fb13628843890c171b122` | `sspec_f7d6578e623fe3f278649e47` | REJECT | cross_market | NQ,ES | 5m,10m,30m | 248 | 48 | RELOCKED -> sspec_f7d6578e623fe3f278649e47 | audit-only |
| `sspec_69c22ec5847395ac8e81b5b6` | `sspec_652fcc23a6f725b405612b8e` | INCONCLUSIVE | vwap_session | ES,NQ,RTY | 5m,10m,15m,30m | 528 | 96 | RELOCKED -> sspec_652fcc23a6f725b405612b8e | rerun candidate |
| `sspec_aff70fcbc4b7ff226fcc8149` | `sspec_676a012a4a4cdf3d169cd981` | INCONCLUSIVE | vwap_session | ES,NQ,RTY | 5m,10m,15m,30m | 528 | 96 | RELOCKED -> sspec_676a012a4a4cdf3d169cd981 | rerun candidate |
| `sspec_267cc052e37668339c38d179` | `sspec_1d87dfbe3d24810720f75014` | INCONCLUSIVE | regime | ES,NQ,RTY | 5m,10m,15m,30m | 504 | 96 | RELOCKED -> sspec_1d87dfbe3d24810720f75014 | rerun candidate |
| `sspec_27bf1262b0bd23d27191cc86` | `sspec_c2114a3c6c90595350151af0` | INCONCLUSIVE | liquidity_pa | ES,NQ,RTY | 5m,10m,15m,30m | 600 | 96 | RELOCKED -> sspec_c2114a3c6c90595350151af0 | rerun candidate |
| `sspec_02c400a561891171a33c0c66` | `sspec_950ad6bb7063928d9ff8ea4f` | INCONCLUSIVE | liquidity_pa | ES,NQ,RTY | 5m,10m,15m,30m | 600 | 96 | RELOCKED -> sspec_950ad6bb7063928d9ff8ea4f | rerun candidate |
| `sspec_9f6f741192a4b534f06e51c0` | `sspec_6088f0ed5b02b161bfb54943` | INCONCLUSIVE | bbo_tradability | ES,NQ,RTY | 5m,10m,15m,30m | 648 | 96 | RELOCKED -> sspec_6088f0ed5b02b161bfb54943 | rerun candidate |

## Prior-INCONCLUSIVE Classification

| Previously INCONCLUSIVE StudySpec | Family | Classification | Counts | Gap or evidence |
| --- | --- | --- | --- | --- |
| `sspec_69c22ec5847395ac8e81b5b6` | vwap_session | RELOCKED -> `sspec_652fcc23a6f725b405612b8e` | F=528; L=96 | resolved_by_runtime_resolver_and_feature_lock_validator |
| `sspec_aff70fcbc4b7ff226fcc8149` | vwap_session | RELOCKED -> `sspec_676a012a4a4cdf3d169cd981` | F=528; L=96 | resolved_by_runtime_resolver_and_feature_lock_validator |
| `sspec_267cc052e37668339c38d179` | regime | RELOCKED -> `sspec_1d87dfbe3d24810720f75014` | F=504; L=96 | prior gap `label_as_feature_input:feature_pack_refs[0]:session_label` resolved by current live registry records carrying `field_roles.session_label = SESSION_METADATA` through FeatureSpec input metadata |
| `sspec_27bf1262b0bd23d27191cc86` | liquidity_pa | RELOCKED -> `sspec_c2114a3c6c90595350151af0` | F=600; L=96 | resolved_by_runtime_resolver_and_feature_lock_validator |
| `sspec_02c400a561891171a33c0c66` | liquidity_pa | RELOCKED -> `sspec_950ad6bb7063928d9ff8ea4f` | F=600; L=96 | resolved_by_runtime_resolver_and_feature_lock_validator |
| `sspec_9f6f741192a4b534f06e51c0` | bbo_tradability | RELOCKED -> `sspec_6088f0ed5b02b161bfb54943` | F=648; L=96 | prior gap `label_as_feature_input:feature_pack_refs[0]:session_label` resolved by current live registry records carrying `field_roles.session_label = SESSION_METADATA` through FeatureSpec input metadata |

P28 may re-run the 6 prior-INCONCLUSIVE StudySpecs classified above as `RELOCKED`. The four prior-REJECT cross-market StudySpecs are re-locked for a complete audit baseline, not for a new promotion decision in P28.

## Named Gaps

None. The two prior `label_as_feature_input:feature_pack_refs[0]:session_label` gaps now resolve fail-closed-clean through the runtime resolver against current `REGISTERED` records.

## Superseded P27 Artifacts

The prior FUTSUB-P27 re-lock JSON files were removed from `research/futures_substrate_scaleout_v1/rerun/study_specs/` and replaced by the ten `P022000_FUTSUB_RELOCK_RERUN` StudySpecs above. `research/futures_core_alpha_pilot_v1/**` was not mutated.

## Contract Notes

- Held fixed: `alpha_spec_id`, top-level `label_spec_id`, `split_protocol`, metrics, costs, variant budget, locked-test policy, negative controls, and stopping rules.
- Re-issued: dataset-scope DatasetVersion locks, feature pack locks, label pack locks, and StudyInputPack references.
- The top-level `StudySpec.label_spec_id` remains the original Core Pilot governance anchor. Dataset-scope label locks carry the current per-year registry `label_spec_id` values required by the live `lver_...` identities.
- Re-lock artifacts are value-free. Local resolver paths and raw/materialized values are not committed.
