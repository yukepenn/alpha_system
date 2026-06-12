# Track-B Pooled-Hypothesis Registration Record (Value-Free)

Date: 2026-06-12
Registered by: coordinator (FUTSUB kill-shot resume handoff step 4)
Marker check: `runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/phases/FUTSUB-P28/track_a_metrics_started.json`
absent at registration time (verified 2026-06-12T05:06:10Z, before any Track-A
metric exists).

This record is value-free: ids, timestamps, statuses, and commands only.
Registries are local-only per artifact policy; this committed record carries
the deterministic ids for audit.

## P110000_RELOCK_V2 Supersession

The records below are historical P022000-anchor registrations. P110000_RELOCK_V2
supersedes the anchor StudySpec and the kill-shot member StudySpec set before
Track-A metrics started. Post-P110000 Track-B evidence requires fresh pooled
hypothesis registrations against the V2 StudySpec ids.

| P022000 re-lock anchor | P110000_RELOCK_V2 successor |
| --- | --- |
| `sspec_652fcc23a6f725b405612b8e` | `sspec_f6cbd88caa0445f0f56d81fd` |
| `sspec_676a012a4a4cdf3d169cd981` | `sspec_1604b063f3a3401208ee0239` |
| `sspec_1d87dfbe3d24810720f75014` | `sspec_dec89a327a9c50957adca780` |
| `sspec_c2114a3c6c90595350151af0` | `sspec_840e8342564226f2c3257903` |
| `sspec_950ad6bb7063928d9ff8ea4f` | `sspec_c237c6a8ce40c2585836fae0` |
| `sspec_6088f0ed5b02b161bfb54943` | `sspec_533f665ec4ac063dbb664a54` |

The two `poolhyp_*` ids below should not be used as post-P110000 execution
contracts; they remain audit evidence that Track-B was registered before the
earlier P022000 Track-A boundary.

## Registered Records

| pooled_hypothesis_id | pool_kind | anchor study | members | horizons | symbols | registered_at |
|---|---|---|---|---|---|---|
| `poolhyp_67427c04adfc2dc97fd42bc5` | cross_symbol | `sspec_652fcc23a6f725b405612b8e` | `#symbol=ES`, `#symbol=NQ`, `#symbol=RTY` | 5m | ES, NQ, RTY | 2026-06-12T05:06:10Z |
| `poolhyp_797417343726708a0d2d9939` | cross_horizon | `sspec_652fcc23a6f725b405612b8e` | `#horizon=5m`, `#horizon=15m`, `#horizon=30m` | 5m, 15m, 30m | ES | 2026-06-12T05:06:10Z |

## Linked Ledger Entries (PLANNED, pre-metric)

| variant_id | trial_id | alpha_spec_id |
|---|---|---|
| `pooled-track-b-cross-symbol-v1` | `trial_1b8ca7e8f2b837b9887e7121` | `aspec_2982c385e0fae9ebcdc22a2d` |
| `pooled-track-b-cross-horizon-v1` | `trial_84ffee90a2153e7fe9fe12fa` | `aspec_2982c385e0fae9ebcdc22a2d` |

## Registry Locations (local-only, never committed)

- `/home/yuke_zhang/alpha_data/alpha_system/futsub_killshot_track_b/pooled_hypotheses.jsonl`
- `/home/yuke_zhang/alpha_data/alpha_system/futsub_killshot_track_b/pooled_variant_ledger.jsonl`
- `/home/yuke_zhang/alpha_data/alpha_system/futsub_killshot_track_b/pooled_registration_trials.jsonl`

## Minimum Check

`track_b_minimum_satisfied(registered_records, kill_shot_study_set)` returned
`True` over the six re-locked rerun candidate ids plus the registered member
refs (all member refs anchor to kill-shot candidates), mirroring
`tests/unit/discovery_rigor_floor/test_pooled_track_b_readiness.py`.

Registration commands (executed 2026-06-12, exit 0):

```bash
alpha governance register-pooled-hypothesis <payload> \
  --registry-path .../pooled_hypotheses.jsonl \
  --variant-ledger-path .../pooled_variant_ledger.jsonl \
  --metrics-started-marker runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/phases/FUTSUB-P28/track_a_metrics_started.json
alpha governance pooled-hypotheses list --registry-path .../pooled_hypotheses.jsonl --json  # count: 2
```

No alpha, profitability, tradability, or production claim is made; pooled
hypotheses are pre-registered evidence contracts only.
