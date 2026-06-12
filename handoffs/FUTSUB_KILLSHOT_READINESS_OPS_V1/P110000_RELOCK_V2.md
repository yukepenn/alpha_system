# P110000_RELOCK_V2 Handoff

- Branch: `wf1/relock-v2`
- Phase: `P110000_RELOCK_V2`
- Campaign: `FUTSUB_KILLSHOT_READINESS_OPS_V1`
- Commit status: this handoff is included in the explicit-path phase commit, so
  the final hash is reported outside the file after commit creation.

## Scope Completed

- Verified repair preconditions before relock:
  - `~/logs/alpha_pipeline/post_restore_v2_audit.txt` reports
    `bbo_tradability_top_book` 264/264, `regime_volatility_compression` 120/120,
    and `session_calendar_maintenance` 192/192 hash-identical, with zero stale,
    missing, unreadable, or hash-mismatch rows.
  - Track-A marker
    `runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/phases/FUTSUB-P28/track_a_metrics_started.json`
    is absent in this worktree; `runs/` is absent here.
  - Registry mtimes were unchanged by the relock path:
    `features.sqlite` `1781266783`, `labels.sqlite` `1781194502`.
- Re-locked all 10 committed rerun StudySpecs against current `REGISTERED`
  registry successors under `ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system`.
- Reused the P022000 sanctioned relock method:
  `FeatureLabelPackResolver.resolve_feature_packs`,
  `FeatureLabelPackResolver.resolve_label_packs`,
  `alpha_system.governance.study_spec.create_study_spec`, and
  `alpha_system.governance.feature_lock_validation.validate_feature_locks`.
  I found no committed standalone P022000 driver script in this worktree; the
  relock used the exact API path documented by the P022000 spec, handoff, and
  review, with registry reads only and repo JSON/report writes only.
- Wrote a V2 bundle containing 4112 feature locks and 840 label locks, all
  resolving to `REGISTERED` records. The BBO spot-check confirmed
  `bbo_tradability_spread_zscore` first event timestamp
  `2019-01-01T23:01:00+00:00` on the minute grid.
- Retired 448 reviewed R-036 no-replacement locks for
  `session_calendar_roll_bars_to_roll` and
  `session_calendar_roll_minutes_to_roll` rather than substituting them.
- Updated durable references:
  - `research/futures_substrate_scaleout_v1/rerun/studyspec_relock.md`
  - Track-B templates and tests
  - power memo, VariantLedger reconciliation, substrate-invariant audit, and
    Track-B registered record addenda
  - sealed holdout declaration relock selector and deterministic window id
- Removed superseded v1 session/regime union-restore configs per P113000 review
  MINOR-2:
  - `configs/features/scaleout/repair/regime_volatility_compression_union_restore.json`
  - `configs/features/scaleout/repair/session_calendar_maintenance_union_restore.json`

## Old To New StudySpec Map

| Original StudySpec | P022000 StudySpec | P110000_RELOCK_V2 StudySpec |
| --- | --- | --- |
| `sspec_267cc052e37668339c38d179` | `sspec_1d87dfbe3d24810720f75014` | `sspec_dec89a327a9c50957adca780` |
| `sspec_9f6f741192a4b534f06e51c0` | `sspec_6088f0ed5b02b161bfb54943` | `sspec_533f665ec4ac063dbb664a54` |
| `sspec_69c22ec5847395ac8e81b5b6` | `sspec_652fcc23a6f725b405612b8e` | `sspec_f6cbd88caa0445f0f56d81fd` |
| `sspec_aff70fcbc4b7ff226fcc8149` | `sspec_676a012a4a4cdf3d169cd981` | `sspec_1604b063f3a3401208ee0239` |
| `sspec_02c400a561891171a33c0c66` | `sspec_950ad6bb7063928d9ff8ea4f` | `sspec_c237c6a8ce40c2585836fae0` |
| `sspec_27bf1262b0bd23d27191cc86` | `sspec_c2114a3c6c90595350151af0` | `sspec_840e8342564226f2c3257903` |
| `sspec_c671fbeeb143512cbc03bc5b` | `sspec_cc38daf30253587e6dec3ab3` | `sspec_40b1e1ce9862f5a562e6d038` |
| `sspec_90b28233d828128664588a9a` | `sspec_d97a87458dbe72da1f27bfab` | `sspec_b0819e731590426d895bb969` |
| `sspec_dde3e64667fe158f9bad527d` | `sspec_da1bba367710c983b2ca644f` | `sspec_19cbe3c2c973ef68130b6224` |
| `sspec_7c8fb13628843890c171b122` | `sspec_f7d6578e623fe3f278649e47` | `sspec_ce82701b939a8e969a7758da` |

## Validation

- `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/discovery_rigor_floor tests/unit/governance -q`
  - PASS: 686 passed in 3.58s
- `ALPHA_DATA_ROOT=$HOME/alpha_data/alpha_system PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/futures_substrate_scaleout -q`
  - PASS: 134 passed in 22.34s
- `PYTHONPATH=$PWD/src python tools/hooks/canary_runner.py`
  - PASS: all Frontier canaries passed
- `PYTHONPATH=$PWD/src python tools/verify.py --smoke`
  - PASS
- `PYTHONPATH=$PWD/src just ci-parity`
  - PASS via `/home/yuke_zhang/.venvs/alpha_system_ci/bin/python`: 3313 passed,
    80 skipped in 76.80s

## Non-Runs

- No push and no PR, per executor instruction.
- No registry write or materialization command was run by this phase.
- `python tools/verify.py --all` was not run because the phase specified
  smoke plus CI-parity validation, and CI-parity ran the full CI pytest suite.

## Risks And Caveats

- Track-B records registered at `2026-06-12T05:06:10Z` remain historical
  P022000-anchor records. The coordinator must register replacement Track-B
  pooled hypotheses against the P110000 V2 ids before any Track-A metric starts.
- Old P022000 ids intentionally remain in historical docs, review artifacts, and
  `superseded_relock_study_spec_id` provenance fields. Current execution pins
  and templates point at the V2 ids.
- The sealed holdout content-address changed to
  `holdwin_3ed860d2e163f8c6e4cbeb66` because the partition selector now names
  `P110000_RELOCK_V2`; the start date, rolling policy, symbols, partitions, and
  value-free boundary remain unchanged.

## Review Focus

- Confirm the V2 StudySpecs reference current `REGISTERED` feature/label
  successors and preserve original governance parameters.
- Confirm R-036 no-replacement retirements are acceptable and no second value
  truth or data artifact entered git.
- Confirm Track-B and sealed-holdout reference updates are sufficient to avoid
  stale P022 execution anchors.
- Confirm P113000 MINOR-2 cleanup removed only superseded v1 session/regime
  restore configs and left the active v2 configs plus BBO config intact.

## Next Recommended Step

Run semantic review for P110000_RELOCK_V2. If accepted, re-register Track-B
pooled hypotheses against the V2 StudySpecs before removing any Track-A stop or
starting FUTSUB-P28 metrics.
