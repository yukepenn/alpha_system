# P110000_RELOCK_V2 — Fresh Adversarial Review

- Reviewer: Claude (fresh adversarial reviewer, WF1)
- Phase: `P110000_RELOCK_V2` / Campaign: `FUTSUB_KILLSHOT_READINESS_OPS_V1`
- Branch/commit reviewed: `wf1/relock-v2` @ `2983ed0` (diff vs `origin/main`, 28 files)
- Stance: maximally adversarial — this phase re-issues the kill-shot LOCK CHAIN.
- Verdict: **PASS_WITH_WARNINGS**

All evidence below was independently re-derived by the reviewer (live read-only
registry queries, git-history reconstruction of the old bundle, deterministic
id re-derivation, full validation-suite reruns, and a mutation test). No claim
in the handoff was accepted on prose alone.

## 1. Lock truth — PASS (verified exhaustively, not sampled)

Checked **all 10** new sspecs (superset of the required ≥3 incl. bbo + vwap),
against `ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system` registries
opened `file:...?mode=ro`:

- 4112/4112 feature locks: `feature_version_id` exists, `lifecycle_state=REGISTERED`,
  and `value_content_hash`, `feature_id`, `dataset_version_id`, `partition`,
  `value_record_count` all match the live registry. 0 mismatches.
- 840/840 label locks: same checks incl. per-lock `label_spec_id` vs registry. 0 mismatches.
- BBO grid: all 264 bbo locks (across the bundle) have registry `first_event_ts`
  on the minute grid (`:00` seconds). The handoff's cited spot-check fver
  `fver_09cac6dd…059e51` independently confirmed:
  `bbo_tradability_spread_zscore`, `ES_2019_full_year`,
  `first_event_ts=2019-01-01T23:01:00+00:00`, REGISTERED,
  `registered_at=2026-06-12T02:01:07Z` — i.e. post-#401-grid-fix re-mat content.
- Labels undamaged claim: for each of the 10 old→new pairs, the sorted
  `label_version_id` lists are **identical** old vs new; in fact
  `label_pack_locks` and `dataset_version_locks` are byte-identical (they do
  not appear among changed dataset_scope keys at all).
- Preconditions re-verified: `~/logs/alpha_pipeline/post_restore_v2_audit.txt`
  shows bbo 264/264, regime 120/120, session 192/192 hash-identical with 0
  stale/mismatch/missing/unreadable; `remat_chain.log` ends `rc=0` /
  `CHAIN COMPLETE`; Track-A marker
  `runs/2026-06-07T235209Z…/FUTSUB-P28/track_a_metrics_started.json` is absent.

## 2. Count reconciliation — PASS (independent 448 derivation)

Old bundle reconstructed from `git show origin/main:…/study_specs/<old>.json`:

- Old bundle total feature locks: **4560** (504+648+528+528+600+600+328+328+248+248).
- Countdown locks in the OLD bundle, counted directly:
  `session_calendar_roll_bars_to_roll` = **224**,
  `session_calendar_roll_minutes_to_roll` = **224**, total **448** — matches the
  claimed retirement exactly (8 sspecs × 48 + 2 cross-market × 32).
- Per-sspec: `oldF − newF` equals that sspec's countdown count in every case.
- Set-diff on (feature_id, dataset_version_id, partition): dropped keys are
  countdown-only (0 non-countdown drops), **0 gained** keys. No lock silently
  disappeared beyond the 448 and nothing was silently added.
- Full change taxonomy (reviewer-derived, reconciles the report's 2176):
  720 locks moved to NEW fvers (deprecation replacements: session 672 + regime 48,
  all with new `feature_request_id`s), 1456 kept the same fver with a changed
  `value_content_hash` (bbo 264 + session 1120 + regime 72), 1936 byte-identical.
  720+1456+1936 = 4112. Matches the report's
  `{'deprecation_replacement': 720, 'registry_metadata_refresh': 1456}`.

## 3. ID map completeness and content addressing — PASS

- The old→new map covers exactly the 10 P022000 ids in `origin/main`'s
  study_specs dir and exactly the 10 new files on this branch.
- `generate_study_spec_id()` re-derives the committed `study_spec_id` for
  **all 10** new sspecs (not just one), and each filename matches its id.
- Sealed-holdout `window_id holdwin_3ed860d2e163f8c6e4cbeb66` also re-derives
  via `generate_sealed_holdout_window_id()` from the committed declaration.

## 4. Study semantics unchanged — PASS

For all 10 pairs, the held-fixed fields are deep-equal old vs new:
`alpha_spec_id`, top-level `label_spec_id`, `split_protocol`, `metrics`,
`cost_assumptions`, `variant_budget`, `locked_test_policy`,
`negative_controls`, `stopping_rules`, plus dataset_scope identity fields
(`family`, `target_instruments`, `locked_horizons`,
`declared_primary_horizon`, `campaign_id`, `source_alpha_spec`, `schema_ref`).
Changed dataset_scope keys are exclusively lock/provenance surfaces:
`feature_pack_locks`, `study_input_pack_refs`, `relock_provenance`,
`old_lock_summary`, `resolver_smoke_summary`, `study_pack_status`,
`boundary_contract`, `phase_id`, plus the new `v2_relock_summary`. Zero drift.

## 5. Reference updates — PASS

- `tests/unit/discovery_rigor_floor/test_pooled_track_b_readiness.py`,
  `tests/unit/governance/test_pooled_hypothesis.py`,
  `test_pooled_hypothesis_cli.py`, `test_real_surrogate_calibration_tool.py`:
  RERUN_STUDY_IDS / committed-spec pins updated to V2 ids.
- Track-B templates (`CROSS_HORIZON…`, `CROSS_SYMBOL…`): candidate ids,
  members, and anchor `study_spec_id` updated to V2 ids; still `not_registered`.
- Power memos: diff is **pure addition** (addendum + old→new table + one
  successor line per §3.x study); zero deletions of pre-registered memo text.
- Variant-reconciliation audit and Track-B REGISTERED_RECORD: additive
  supersession addenda.
- Repo-wide grep for each of the 10 old ids: remaining hits are only (a) the
  new sspecs' own `superseded_relock_study_spec_id` provenance, (b) historical
  handoffs/review artifacts, (c) the map/addendum docs themselves. No
  un-updated executable/committed pin remains.

## 6. Holdout intersection contract — PASS

The intersection contract test is
`tests/unit/discovery_rigor_floor/test_rigor_p03_sealed_holdout_declaration.py::test_kill_shot_window_intersects_every_relocked_locked_test_input`
(loads committed sspecs from `research/futures_substrate_scaleout_v1/rerun/study_specs`
and asserts `access_intersects_holdout` per locked-test partition). Re-run
directly: 3 passed.

## 7. Track-B not registered by this phase — PASS

- Diff contains zero `src/**`, `tools/**`, or registry-writing code — only
  tests, research md/json, specs/handoffs, and two config deletions.
- Live `futsub_killshot_track_b/pooled_hypotheses.jsonl` last modified
  1781240815 (05:06Z, before this phase's commit 1781268725) and still anchors
  the **old** P022000 ids — confirming this phase did not register Track-B and
  that coordinator re-registration against V2 ids must precede any Track-A
  metric (handoff states this explicitly).
- Registry mtimes match the handoff exactly (`features.sqlite` 1781266783,
  `labels.sqlite` 1781194502) and predate the phase commit.

## 8. Mutation test — PASS (kill confirmed)

Corrupted one character of the first `value_content_hash` in the bbo sspec
`sspec_533f665ec4ac063dbb664a54.json` →
`pytest tests/unit/futures_substrate_scaleout/test_studyspec_relock_smoke.py`
failed loudly: **4 failed** (governance content-address mismatch via
`GovernanceValidationError` in `study_spec.py:276`, plus the live-registry
validator test). Restored via `git checkout --`; worktree clean; suite re-run
green (6 passed).

## 9. Handoff truthfulness — PASS

All five validation suites re-run by the reviewer; counts match the handoff
exactly:

| Suite | Handoff | Reviewer |
| --- | --- | --- |
| discovery_rigor_floor + governance | 686 passed | 686 passed |
| futures_substrate_scaleout (live registry) | 134 passed | 134 passed |
| canary_runner | all passed | all passed |
| verify.py --smoke | PASS | exit 0 |
| just ci-parity | 3313 passed, 80 skipped | 3313 passed, 80 skipped |

Artifact policy: `git ls-files runs` empty; no sqlite/parquet/log/jsonl in the
commit; commit file list (28) equals the reviewed diff; no force-push; branch
not pushed.

## Findings

- **MINOR-1 (append-only deviation, audit preamble):** the substrate-invariant
  audit edit removed/reworded 2 original preamble lines ("Lock corpus: …" →
  "Original audited lock corpus before P110000_RELOCK_V2 …", "are"→"were")
  instead of being purely additive. The predicates, findings, and counts of the
  original audit are untouched; intent (historical labeling) is preserved.
  Spec asked for "addendum, NOT a rewrite" — this is a borderline clarifying
  edit, not an evidence change.
- **MINOR-2 (sealed-holdout supersession chain gap):** the SEALED declaration
  was edited in place (`futsub_relock_phase_id` + provenance fields), which
  changed the content-addressed `window_id` from `holdwin_bcf16744…` to
  `holdwin_3ed860d2…`. The `superseded_declaration` block still records only
  the original RIGOR-P03 window (`holdwin_d5cba…`); the immediately-superseded
  `holdwin_bcf16744…` is now recoverable only from git history. The holdout
  boundary itself (start 2025-01-01, rolling, 32 locked-test partitions,
  ES/NQ/RTY) is unchanged — verified by diff — so contamination semantics are
  unaffected. Recommend a follow-up addendum (or GATE_INVENTORY note) recording
  the `holdwin_bcf16744…` → `holdwin_3ed860d2…` supersession.
- **MINOR-3 (report bucket naming):** `studyspec_relock.md` labels the 1456
  same-fver lock updates `registry_metadata_refresh`, but all 1456 are
  `value_content_hash` changes (in-place content re-registration under the same
  fver for bbo/regime/session after the repair re-mat). Counts are truthful;
  the label understates the change. Related observation (not a defect of this
  phase): the bbo repair re-registered the same fver ids with new content
  hashes rather than deprecate-first replacement; the relock captured the new
  hashes correctly and the post-restore audit shows registry/pack hash identity.
- **NOTE-1:** `research/discovery_rigor_floor_v1/sealed_holdout/GATE_INVENTORY.md`
  still pins the original `holdwin_d5cba…` — pre-existing staleness from
  P033000, not introduced by this phase.
- **NOTE-2:** deletion of the two v1 union-restore configs is a small scope
  addition beyond spec §3, but it implements P113000 review MINOR-2; the
  active v2 configs and the bbo restore config remain in
  `configs/features/scaleout/repair/`.

## Verdict

**PASS_WITH_WARNINGS** — the lock chain is sound: every committed lock
resolves to the live repaired registry (hash-exact), the 448 retirement is
independently derived and exact, semantics are byte-stable, ids are
content-addressed and reproducible, references are consistently repointed,
validation reproduces, and the chain fails loudly under mutation. Warnings are
the three MINOR findings above; none poisons the evidence chain.
