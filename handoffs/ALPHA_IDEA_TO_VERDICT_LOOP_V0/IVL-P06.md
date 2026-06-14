# IVL-P06 Handoff

Campaign: `ALPHA_IDEA_TO_VERDICT_LOOP_V0`  
Phase: `IVL-P06`  
Branch: `auto/alpha_idea_to_verdict_loop_v0/ivl-p06-dogfood-dk-track-b-through-the-loop-no-new-mechanism-feature-label-data-no-promo`  
Base commit observed by executor: `0e7a73d`  
Executor: Codex  
Date: 2026-06-14

## Scope Delivered

- Added a narrow slice-passthrough allow-list in
  `src/alpha_system/governance/idea_draft.py` for:
  `testability_slice`, `testability_slices`, `slice_spec`, `slice_specs`,
  `fast_probe_slice`, `fast_probe_slice_spec`, `slice`, and `slices`.
- The intake validator still rejects every other undeclared top-level field.
- Passthrough slice keys are ignored by governance object construction and do
  not enter the content-hashed `AlphaSpec`, `MechanismCard`, or `SetupSpec`
  identities.
- Added unit coverage proving byte-identical emitted ids with and without
  passthrough slice keys.
- Added CLI coverage for a resolving embedded slice through `alpha idea gate`
  and `alpha idea run`.
- Added DK Track B dogfood idea files, value-free reports, a dogfood README,
  and `docs/IDEA_TO_VERDICT_DOGFOOD.md`.
- Updated `README.md` with a concise IVL-P06 campaign-close snapshot.

## Files Changed

- `src/alpha_system/governance/idea_draft.py`
- `tests/unit/governance/test_idea_draft.py`
- `tests/unit/cli/test_idea_cli.py`
- `tests/integration/test_ivl_dogfood_track_b.py`
- `research/idea_to_verdict_loop_v0/dogfood/track_b_es2024_120m.idea.yaml`
- `research/idea_to_verdict_loop_v0/dogfood/track_b_es2020_120m.idea.yaml`
- `research/idea_to_verdict_loop_v0/dogfood/ES_2024_120m_REPORT.md`
- `research/idea_to_verdict_loop_v0/dogfood/ES_2020_120m_REPORT.md`
- `research/idea_to_verdict_loop_v0/dogfood/README.md`
- `docs/IDEA_TO_VERDICT_DOGFOOD.md`
- `README.md`
- `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P06.md`

No review artifact, verdict artifact, run-local handoff, PR, staged change,
commit, push, or merge was created by Codex.

## Dogfood Results

- `alpha idea gate` on `track_b_es2024_120m.idea.yaml` exited 0.
  - `path_label_two_class` returned `DATA_GAP` with one observed class.
  - `pre_test=true`, `shot_spent=false`, `probe_invoked=false`.
  - `alpha idea run` exited 0, wrote
    `research/idea_to_verdict_loop_v0/dogfood/ES_2024_120m_REPORT.md`, and
    routed to requeue with `promotion_eligible=false` and
    `fabricated_values=false`.
- `alpha idea gate` on `track_b_es2020_120m.idea.yaml` exited 0.
  - `path_label_two_class` returned `PASS` with class counts
    `false=309206`, `true=3950`.
  - The overall gate returned honest `DATA_GAP` because the live registered
    feature packs resolve as `ES_2020_full_year` while the path-label pack is
    `ES_2020_120m`; the resolver correctly reports
    `feature_pack_partition_mismatch`.
  - `alpha idea run` exited 0, wrote
    `research/idea_to_verdict_loop_v0/dogfood/ES_2020_120m_REPORT.md`, and
    routed to requeue with `promotion_eligible=false` and
    `fabricated_values=false`.
- The deterministic integration test supplies value-free resolver handles for
  the ES 2020 slice and proves the PASS -> fast readout -> report -> memory
  path without loading or fabricating data.

## Validation

- `env -u FRONTIER_CREATE_PR -u FRONTIER_ALLOW_AUTOMERGE -u FRONTIER_MERGE_DRY_RUN -u FRONTIER_PARALLEL -u FRONTIER_MAX_PARALLEL_PHASES PYTHONPATH=src python -m pytest tests/unit/governance/test_idea_draft.py tests/unit/cli/test_idea_cli.py tests/integration/test_ivl_dogfood_track_b.py -q`
  - Result: exit 0; `24 passed`.
- `env -u FRONTIER_CREATE_PR -u FRONTIER_ALLOW_AUTOMERGE -u FRONTIER_MERGE_DRY_RUN -u FRONTIER_PARALLEL -u FRONTIER_MAX_PARALLEL_PHASES PYTHONPATH=src python -m pytest tests -k "dogfood or idea or fast_probe or testability_gate" -q`
  - Result: exit 0; `87 passed, 2 skipped, 3609 deselected`.
- `env -u FRONTIER_CREATE_PR -u FRONTIER_ALLOW_AUTOMERGE -u FRONTIER_MERGE_DRY_RUN -u FRONTIER_PARALLEL -u FRONTIER_MAX_PARALLEL_PHASES PYTHONPATH=src python -m pytest tests/unit/research/test_research_no_value_engine.py -q`
  - Result: exit 0; `3 passed`.
- `python -c "import importlib,sys; [sys.exit('numpy/pandas must NOT import') for m in ('numpy','pandas') if importlib.util.find_spec(m)]"`
  - Result: exit 0.
- `PYTHONPATH=src python -m alpha_system.cli.main idea gate research/idea_to_verdict_loop_v0/dogfood/track_b_es2024_120m.idea.yaml`
  - Result: exit 0; Check-3 `DATA_GAP`, `shot_spent=false`.
- `PYTHONPATH=src python -m alpha_system.cli.main idea run research/idea_to_verdict_loop_v0/dogfood/track_b_es2024_120m.idea.yaml --report-output research/idea_to_verdict_loop_v0/dogfood/ES_2024_120m_REPORT.md`
  - Result: exit 0; requeue, `promotion_eligible=false`,
    `fabricated_values=false`.
- `PYTHONPATH=src python -m alpha_system.cli.main idea gate research/idea_to_verdict_loop_v0/dogfood/track_b_es2020_120m.idea.yaml`
  - Result: exit 0; Check-3 `PASS`; overall honest `DATA_GAP` from feature
    partition mismatch.
- `PYTHONPATH=src python -m alpha_system.cli.main idea run research/idea_to_verdict_loop_v0/dogfood/track_b_es2020_120m.idea.yaml --report-output research/idea_to_verdict_loop_v0/dogfood/ES_2020_120m_REPORT.md`
  - Result: exit 0; requeue, `promotion_eligible=false`,
    `fabricated_values=false`.
- `env -u FRONTIER_CREATE_PR -u FRONTIER_ALLOW_AUTOMERGE -u FRONTIER_MERGE_DRY_RUN -u FRONTIER_PARALLEL -u FRONTIER_MAX_PARALLEL_PHASES python tools/verify.py --smoke`
  - Result: exit 0.
- `env -u FRONTIER_CREATE_PR -u FRONTIER_ALLOW_AUTOMERGE -u FRONTIER_MERGE_DRY_RUN -u FRONTIER_PARALLEL -u FRONTIER_MAX_PARALLEL_PHASES python tools/hooks/canary_runner.py`
  - Result: exit 0; all Frontier canaries passed.
- `env -u FRONTIER_CREATE_PR -u FRONTIER_ALLOW_AUTOMERGE -u FRONTIER_MERGE_DRY_RUN -u FRONTIER_PARALLEL -u FRONTIER_MAX_PARALLEL_PHASES python tools/verify.py --boundaries`
  - Result: exit 0.
- `env -u FRONTIER_CREATE_PR -u FRONTIER_ALLOW_AUTOMERGE -u FRONTIER_MERGE_DRY_RUN -u FRONTIER_PARALLEL -u FRONTIER_MAX_PARALLEL_PHASES python tools/verify.py --artifacts`
  - Result: exit 0.
- `env -u ALPHA_DATA_ROOT -u FRONTIER_CREATE_PR -u FRONTIER_ALLOW_AUTOMERGE -u FRONTIER_MERGE_DRY_RUN -u FRONTIER_PARALLEL -u FRONTIER_MAX_PARALLEL_PHASES python tools/verify.py --all`
  - Result: exit 0; `3618 passed, 80 skipped`.
  - Status doctor inside verify reported `WARN` only because this worktree has
    no `runs/<run_id>/state.json` live run directory to reconcile.
- `git ls-files runs`
  - Result: exit 0 with empty output.
- `find reviews/ALPHA_IDEA_TO_VERDICT_LOOP_V0 -maxdepth 3 -type f -print 2>/dev/null || true`
  - Result: exit 0 with empty output.
- `find runs -maxdepth 5 -type f -print 2>/dev/null || true`
  - Result: exit 0 with empty output.

## Skipped Or Substituted Checks

- `git status`, `git diff`, and `git diff --cached --name-only` were not run
  because the executor prompt explicitly forbids them.
- `git add`, `git commit`, and `git push` were not run. All changes are left
  unstaged for Ralph.
- A first `python tools/verify.py --all` run with inherited `ALPHA_DATA_ROOT`
  failed the known environment-sensitive
  `tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only`.
  The clean rerun with `ALPHA_DATA_ROOT` unset passed.
- No Claude review was run; no `review.md` or `verdict.json` was created.

## Explicit Confirmations

- Recognized slice-passthrough keys validate at intake and are consumed
  downstream; unknown non-slice top-level fields still fail closed.
- Emitted `HypothesisCard`, `AlphaSpec`, `MechanismCard`, and `SetupSpec` ids
  are byte-identical with and without passthrough slice keys in the unit test.
- ES 2024 degenerate slice yields Check-3 `DATA_GAP` pre-test and requeues.
- ES 2020 two-class slice yields Check-3 `PASS`; local pack resolution still
  returns honest overall `DATA_GAP` due feature/label partition mismatch, with
  no fabricated values.
- `promotion_eligible=false` throughout; exploratory readouts are refused by the
  promotion guard and canaries are green.
- No new mechanism, feature, label, data, geometry sweep, materialization,
  recompute, scaleout-driver call, registry write, FUTSUB/DK edit, broker,
  paper, live, order-routing, deployment, or promotion action was performed.
- `src/alpha_system/research/**`, `src/alpha_system/core/value_store.py`,
  `src/alpha_system/research/first_light.py`, probe engines, strategy
  templates, FUTSUB trees, and DK tooling were not edited.
- `git ls-files runs` is empty.

## Risks / Caveats

- The real local ES 2020 dogfood did not reach an actual fast-probe row readout
  because the current resolver contract accepts one `partition_id` for both
  feature and label packs, while registered feature packs are full-year and the
  label pack is 120m. This was not repaired in IVL-P06 because it would broaden
  scope beyond the authorized front-door passthrough fix.
- The test suite proves the resolving PASS -> readout path with a value-free
  resolver stub; reviewer should treat the real local ES 2020 command as an
  honest DATA_GAP fallback, not a fabricated PASS.

## Review Request Focus

- Confirm the slice-passthrough allow-list is narrow and does not weaken
  unknown-field rejection.
- Confirm passthrough fields do not enter frozen governance identity inputs.
- Confirm ES 2024 Check-3 `DATA_GAP` is pre-test and requeued.
- Confirm ES 2020 Check-3 `PASS` is represented truthfully and the local overall
  `DATA_GAP` caveat is acceptable.
- Confirm no forbidden path, data artifact, second value truth, promotion path,
  or research claim was introduced.

## Next Recommended Step

Ralph should stage only the commit-eligible paths, run its staged-set policy
checks, then route the YELLOW review. A follow-up campaign, not IVL-P06, should
decide whether the runtime resolver needs an explicit feature-partition versus
label-partition slice contract for real ES full-year feature packs plus 120m
label packs.
