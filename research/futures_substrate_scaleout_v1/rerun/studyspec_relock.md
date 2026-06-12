# P110000 Core Pilot StudySpec Re-lock V2 Report

Value-free report for `P110000_RELOCK_V2` in `FUTSUB_KILLSHOT_READINESS_OPS_V1`. The P022000 re-locked StudySpecs under `research/futures_substrate_scaleout_v1/rerun/study_specs/` were read as inputs; this v2 bundle re-issues locks against the repaired live registry after P094500/P113000 pack restore completion.

## Result

StudySpec resolver-smoke: PASS

- Superseded P022000 StudySpecs classified: 10
- Re-locked V2 StudySpecs written: 10
- Named gaps retained: 0
- Prior-INCONCLUSIVE studies re-locked: 6/6
- Prior-REJECT cross-market audit-only re-locks: 4/4
- Feature locks resolved for committed V2 re-locks: 4112
- Label locks resolved for committed V2 re-locks: 840
- Deprecated R-036 session countdown locks retired without replacement: 448
- Replacement/metadata refreshed feature locks: 2176 ({'deprecation_replacement': 720, 'registry_metadata_refresh': 1456})
- `alpha_system.governance.feature_lock_validation.validate_feature_locks`: PASS for committed V2 feature locks
- Deliberate unresolvable probe: PASS, resolver returns `feature_pack_not_found` for a synthetic `fver_000...` in the smoke test
- BBO grid spot-check: `fver_09cac6dd76ef9bc2ab7b0ed8743b6ae2dcd6c4c268b60157bb6d568650059e51` first_event_ts `2019-01-01T23:01:00+00:00` is minute-grid
- Registry write surface: read-only FeatureRegistry/LabelRegistry resolution; only committed JSON/report files in this repo were written

The smoke used `runtime.input_resolver.FeatureLabelPackResolver.resolve_feature_packs` and `resolve_label_packs` for every committed lock, grouped by DatasetVersion and partition. It checked exact IDs, lifecycle state, expected DatasetVersion, expected partition, expected FeatureRequest or LabelSpec, and metadata required for local Parquet-backed values; no feature, label, market, return, signal, or cost values are embedded here.

## Old -> New StudySpec Map

| Original StudySpec | P022000 StudySpec | P110000 V2 StudySpec | Old F | New F | Old L | New L | R-036 retired |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `sspec_267cc052e37668339c38d179` | `sspec_1d87dfbe3d24810720f75014` | `sspec_dec89a327a9c50957adca780` | 504 | 456 | 96 | 96 | 48 |
| `sspec_9f6f741192a4b534f06e51c0` | `sspec_6088f0ed5b02b161bfb54943` | `sspec_533f665ec4ac063dbb664a54` | 648 | 600 | 96 | 96 | 48 |
| `sspec_69c22ec5847395ac8e81b5b6` | `sspec_652fcc23a6f725b405612b8e` | `sspec_f6cbd88caa0445f0f56d81fd` | 528 | 480 | 96 | 96 | 48 |
| `sspec_aff70fcbc4b7ff226fcc8149` | `sspec_676a012a4a4cdf3d169cd981` | `sspec_1604b063f3a3401208ee0239` | 528 | 480 | 96 | 96 | 48 |
| `sspec_02c400a561891171a33c0c66` | `sspec_950ad6bb7063928d9ff8ea4f` | `sspec_c237c6a8ce40c2585836fae0` | 600 | 552 | 96 | 96 | 48 |
| `sspec_27bf1262b0bd23d27191cc86` | `sspec_c2114a3c6c90595350151af0` | `sspec_840e8342564226f2c3257903` | 600 | 552 | 96 | 96 | 48 |
| `sspec_c671fbeeb143512cbc03bc5b` | `sspec_cc38daf30253587e6dec3ab3` | `sspec_40b1e1ce9862f5a562e6d038` | 328 | 280 | 72 | 72 | 48 |
| `sspec_90b28233d828128664588a9a` | `sspec_d97a87458dbe72da1f27bfab` | `sspec_b0819e731590426d895bb969` | 328 | 280 | 96 | 96 | 48 |
| `sspec_dde3e64667fe158f9bad527d` | `sspec_da1bba367710c983b2ca644f` | `sspec_19cbe3c2c973ef68130b6224` | 248 | 216 | 48 | 48 | 32 |
| `sspec_7c8fb13628843890c171b122` | `sspec_f7d6578e623fe3f278649e47` | `sspec_ce82701b939a8e969a7758da` | 248 | 216 | 48 | 48 | 32 |

## Per-StudySpec Summary

| Original StudySpec | V2 StudySpec | Prior state | Family | Targets | Horizons | Feature locks | Label locks | Classification | P28 scope |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- | --- |
| `sspec_02c400a561891171a33c0c66` | `sspec_c237c6a8ce40c2585836fae0` | INCONCLUSIVE | liquidity_pa | ES,NQ,RTY | 5m,10m,15m,30m | 552 | 96 | RELOCKED -> sspec_c237c6a8ce40c2585836fae0 | rerun candidate |
| `sspec_267cc052e37668339c38d179` | `sspec_dec89a327a9c50957adca780` | INCONCLUSIVE | regime | ES,NQ,RTY | 5m,10m,15m,30m | 456 | 96 | RELOCKED -> sspec_dec89a327a9c50957adca780 | rerun candidate |
| `sspec_27bf1262b0bd23d27191cc86` | `sspec_840e8342564226f2c3257903` | INCONCLUSIVE | liquidity_pa | ES,NQ,RTY | 5m,10m,15m,30m | 552 | 96 | RELOCKED -> sspec_840e8342564226f2c3257903 | rerun candidate |
| `sspec_69c22ec5847395ac8e81b5b6` | `sspec_f6cbd88caa0445f0f56d81fd` | INCONCLUSIVE | vwap_session | ES,NQ,RTY | 5m,10m,15m,30m | 480 | 96 | RELOCKED -> sspec_f6cbd88caa0445f0f56d81fd | rerun candidate |
| `sspec_7c8fb13628843890c171b122` | `sspec_ce82701b939a8e969a7758da` | REJECT | cross_market | NQ,ES | 5m,10m,30m | 216 | 48 | RELOCKED -> sspec_ce82701b939a8e969a7758da | audit-only |
| `sspec_90b28233d828128664588a9a` | `sspec_b0819e731590426d895bb969` | REJECT | cross_market | RTY,ES,NQ | 5m,10m,15m,30m | 280 | 96 | RELOCKED -> sspec_b0819e731590426d895bb969 | audit-only |
| `sspec_9f6f741192a4b534f06e51c0` | `sspec_533f665ec4ac063dbb664a54` | INCONCLUSIVE | bbo_tradability | ES,NQ,RTY | 5m,10m,15m,30m | 600 | 96 | RELOCKED -> sspec_533f665ec4ac063dbb664a54 | rerun candidate |
| `sspec_aff70fcbc4b7ff226fcc8149` | `sspec_1604b063f3a3401208ee0239` | INCONCLUSIVE | vwap_session | ES,NQ,RTY | 5m,10m,15m,30m | 480 | 96 | RELOCKED -> sspec_1604b063f3a3401208ee0239 | rerun candidate |
| `sspec_c671fbeeb143512cbc03bc5b` | `sspec_40b1e1ce9862f5a562e6d038` | REJECT | cross_market | NQ,ES,RTY | 5m,10m,30m | 280 | 72 | RELOCKED -> sspec_40b1e1ce9862f5a562e6d038 | audit-only |
| `sspec_dde3e64667fe158f9bad527d` | `sspec_19cbe3c2c973ef68130b6224` | REJECT | cross_market | NQ,ES | 5m,10m,30m | 216 | 48 | RELOCKED -> sspec_19cbe3c2c973ef68130b6224 | audit-only |

## Prior-INCONCLUSIVE Classification

| Previously INCONCLUSIVE StudySpec | Family | Classification | Counts | Gap or evidence |
| --- | --- | --- | --- | --- |
| `sspec_02c400a561891171a33c0c66` | liquidity_pa | RELOCKED -> `sspec_c237c6a8ce40c2585836fae0` | F=552; L=96 | resolved_by_runtime_resolver_and_feature_lock_validator_against_repaired_registry |
| `sspec_267cc052e37668339c38d179` | regime | RELOCKED -> `sspec_dec89a327a9c50957adca780` | F=456; L=96 | prior session_label role gap remains resolved; repaired registry locks are REGISTERED and resolver-clean |
| `sspec_27bf1262b0bd23d27191cc86` | liquidity_pa | RELOCKED -> `sspec_840e8342564226f2c3257903` | F=552; L=96 | resolved_by_runtime_resolver_and_feature_lock_validator_against_repaired_registry |
| `sspec_69c22ec5847395ac8e81b5b6` | vwap_session | RELOCKED -> `sspec_f6cbd88caa0445f0f56d81fd` | F=480; L=96 | resolved_by_runtime_resolver_and_feature_lock_validator_against_repaired_registry |
| `sspec_9f6f741192a4b534f06e51c0` | bbo_tradability | RELOCKED -> `sspec_533f665ec4ac063dbb664a54` | F=600; L=96 | prior session_label role gap remains resolved; repaired registry locks are REGISTERED and resolver-clean |
| `sspec_aff70fcbc4b7ff226fcc8149` | vwap_session | RELOCKED -> `sspec_1604b063f3a3401208ee0239` | F=480; L=96 | resolved_by_runtime_resolver_and_feature_lock_validator_against_repaired_registry |

P28 may re-run only after coordinator-owned Track-B re-registration points at the V2 ids and before any Track-A metric starts. The four prior-REJECT cross-market StudySpecs remain re-locked for a complete audit baseline only, not for a new promotion decision.

## Named Gaps

None. The P022000 locks that were deprecated by the repair either resolve to current REGISTERED replacements or, for the reviewed R-036 offline/non-causal countdown features, are retired without replacement and omitted from the V2 StudyInputPack refs.

## R-036 Retirements

| Feature ID | Retired locks | Reason |
| --- | ---: | --- |
| `session_calendar_roll_bars_to_roll` | 224 | P094500 deprecate-first reviewed no-replacement R-036 offline/non-causal countdown |
| `session_calendar_roll_minutes_to_roll` | 224 | P094500 deprecate-first reviewed no-replacement R-036 offline/non-causal countdown |

## Contract Notes

- Held fixed: `alpha_spec_id`, top-level `label_spec_id`, `split_protocol`, metrics, costs, variant budget, locked-test policy, negative controls, and stopping rules.
- Re-issued: dataset-scope feature pack locks, label pack locks, StudyInputPack references, and relock provenance.
- The top-level `StudySpec.label_spec_id` remains the original Core Pilot governance anchor. Dataset-scope label locks carry the current per-year registry `label_spec_id` values required by the live `lver_...` identities.
- Re-lock artifacts are value-free. Local resolver paths and raw/materialized values are not committed.
