# P050912_SURROGATE_BLOCK_NULLS — Fresh Adversarial Review

- Campaign: `FUTSUB_KILLSHOT_READINESS_OPS_V1`
- Phase: `P050912_SURROGATE_BLOCK_NULLS` (YELLOW)
- Branch: `wf1/surrogate-block-nulls` @ `8f19fe6`, reviewed against `origin/main`
- Reviewer: fresh Claude (Fable 5), adversarial stance, mutation-tested

## VERDICT: PASS_WITH_WARNINGS

Implementation is correct and spec-complete; one mandated mutation survived
(test-strength gap on the bound-statement string, masked by duplication), plus
minor counter-semantics and coverage warnings. No blocking findings.

## Blocking Findings

None.

## Warnings

### W1 — Bound-statement string is duplicated and single-site corruption is test-invisible (mutation 6c SURVIVED)

The required statement "zero passes in K bounds false-pass rate at about 3/K
at 95%" exists in two places:

- `src/alpha_system/governance/surrogate_run.py:702` (core
  `render_value_free_calibration_report`)
- `tools/discovery_rigor_floor/run_real_surrogate_calibration.py:482` (tool
  report header)

The ONLY assertion is a substring check on the tool report
(`tests/unit/discovery_rigor_floor/test_real_surrogate_calibration_tool.py:62`),
and the tool report embeds BOTH copies (`_render_real_report` appends the core
renderer body). Verified empirically: corrupting either copy alone ("true-pass
rate at about 5/K at 90%") leaves all 53 tests green. Consequences: (a) the
core renderer's bound line — the one `alpha governance surrogate-calibrate`
reports carry — has zero regression coverage; (b) the tool report can ship one
corrupted and one intact copy of its central statistical claim without any
test failing. Recommended follow-up (non-blocking): hoist the statement into a
single shared constant and assert it per renderer.

### W2 — Bootstrap `identity_block_count` conflates two meanings

`write_trade_date_block_shuffled_copy` reports ineligible singleton blocks as
`unmatched_block_count`/`unmatched_record_count` (spec-required), but
`write_trade_date_block_bootstrap_copy` adds ineligible singleton blocks
(`surrogate_run.py` length-class `< 2` branch) into the same
`identity_block_count` that also counts genuinely self-sampled eligible
blocks. The recorded trial parameter is therefore ambiguous as audit evidence.
Not a spec violation (unmatched accounting was mandated for shuffle only), but
the counter should be split for honest reporting.

### W3 — With-replacement property is proven via a summary counter, not output values

`test_trade_date_block_bootstrap_resamples_blocks_with_replacement` kills the
mandated permutation mutation through `duplicate_source_block_count > 0`
(summary self-report). A craftier mutation that permutes while preserving the
counter would survive; no assertion inspects the output rows for duplicated
day-blocks. Acceptable now (the mandated mutation is killed), noted for test
hardening.

### W4 — Real resolver constructor path untested; loud-skip test is vacuous when data exists

`run_real_surrogate_calibration` exercises the real
`FeatureLabelPackResolver(alpha_data_root=...)` branch only when no injected
resolver is given; tests always inject `_FakeResolver` (duck-typed call
contract only), and `test_real_local_label_registry_absence_is_loud_skip`
asserts nothing when the registry exists. This matches the spec's sanctioned
synthetic/loud-skip idiom, so it is a warning, not a finding: the first real
coordinator run is the first execution of the real resolution branch.

### W5 — Minor hygiene

- Unused `timedelta` import,
  `tools/discovery_rigor_floor/run_real_surrogate_calibration.py:11` (CI has
  no lint step; cosmetic).
- `_deranged_block_indices` fallback (`surrogate_run.py`, rotation of the last
  shuffled permutation after 128 tries) is not guaranteed fixed-point-free;
  reach probability ~0.63^128, negligible. Note: shuffle `moved_count`
  increments unconditionally per copied block, so it would not catch a
  fixed-point at the class level — the derangement helper is the sole identity
  guard for the shuffle (mutation A confirms tests catch identity).
- Tool bridge fabricates `path_metadata.required_future_bars=1` /
  `observed_future_bars=1` and synthetic `session_id` when converting
  value-store rows to surrogate-scope shape
  (`run_real_surrogate_calibration.py:394-400`). Values are copied verbatim
  (no second value truth) and stay inside the isolated namespace; flagged so
  the coordinator knows these metadata fields are synthetic bridge fields,
  not real label path metadata.
- Trade date = UTC calendar date of `event_ts`; overnight futures sessions
  spanning midnight UTC split across two blocks. Block-boundary dependence
  breakage is inherent to block methods and the derivation matches the spec
  instruction; noted for interpretation of the real run.

## Verified Claims (evidence, not trust)

1. **label_shuffle unchanged / random_target still rejected.**
   `write_label_shuffled_copy` body untouched; output name
   `label_shuffle.jsonl`, trial parameter keys, and
   `surrogate-label-shuffle-seed-<n>` label_version preserved byte-equivalent
   via `_perturbation_output_name` / `_trial_parameters_for_perturbation` /
   `_surrogate_label_version_text`. `run_surrogate_study` rejects
   `RANDOM_TARGET` (`unsupported_surrogate_execution`), as does
   `_write_perturbation_copy`. All 25 canaries (incl. random_target canary)
   pass.
2. **Block shuffle correctness.** Whole equal-length date blocks deranged per
   (group, length-class) via `_deranged_block_indices` (no fixed points);
   `_copy_block_values` moves ONLY `value` positionally onto the skeleton
   (`shuffled = [dict(label) for label in labels]`); `_date_blocks_for_group`
   keeps ascending row order so within-day value sequences move intact —
   the dependence-preserving claim holds; there is no within-day RNG use
   anywhere in the writer. Unmatched length-classes stay in place and are
   counted (`unmatched_block_count`/`unmatched_record_count`, tested).
   Fail-closed `< 2` eligible blocks with the existing
   `insufficient_label_rows_for_shuffle` code.
3. **Bootstrap correctness.** `rng.randrange` per target = with replacement
   within each equal-length class onto the original skeleton; identity
   arrangement rejected (`identity_trade_date_block_bootstrap` when
   `moved_count == 0`); determinism per seed asserted by re-running and
   comparing full summaries and output rows.
4. **Calibration tool uses existing truth.** Lock resolution goes through
   `FeatureLabelPackResolver.resolve_label_packs` /
   `resolve_feature_packs` + registry record APIs
   (`run_real_surrogate_calibration.py:286-320`); no new resolution logic.
   `require_isolated_namespace` enforced; staged JSONL lives under the
   namespace; `_reject_production_registry_report_path` blocks
   `ALPHA_DATA_ROOT/registry` writes; report is value-free and contains
   declared K, per-config counts, zero-pass verdict, and the exact bound
   statement.
5. **event_ts is the right field.** `LabelValueRecord` declares `event_ts`
   (`src/alpha_system/labels/version.py:587`) and serializes it in
   `to_dict()` (`version.py:651`); `label_available_ts` is the post-horizon
   availability guard (must be >= `horizon_end_ts`, `version.py:617-620`) and
   would mis-block by availability date. Missing/invalid `event_ts`
   fails closed (`missing_label_block_timestamp` /
   `invalid_label_block_timestamp`, tested).
6. **Scope/artifacts.** Diff touches exactly the 7 allowed files; no gate
   semantics changed; no `src/alpha_system/{features,labels,runtime}/**`
   edits; `git ls-files runs` empty; no heavy artifacts; research-only
   language throughout.

## Mutation Tests (run in worktree, restored to committed state after each)

| # | Mutation | Expectation | Result |
|---|---|---|---|
| A | `_deranged_block_indices` returns identity (blocks stay in place) | tests FAIL | KILLED — `test_trade_date_block_shuffle_preserves_skeleton_and_within_day_order` failed |
| B | Bootstrap samples without replacement (`rng.sample` permutation) | tests FAIL | KILLED — `test_trade_date_block_bootstrap_resamples_blocks_with_replacement` failed ("no duplicate bootstrap seed found") |
| C1 | Corrupt bound statement in `render_value_free_calibration_report` (surrogate_run.py:702) | tests FAIL | SURVIVED — 53 passed (→ W1) |
| C2 | Corrupt bound statement in tool header (run_real_surrogate_calibration.py:482) | tests FAIL | SURVIVED — 53 passed (→ W1) |

`git status --short` verified clean after each restoration.

## Validation Reproduced (handoff counts are truthful)

| Command | Handoff claim | Reproduced |
|---|---|---|
| `pytest tests/unit/governance -q` (research venv) | 638 passed | 638 passed |
| `pytest tests/unit/governance/test_surrogate_run.py tests/unit/discovery_rigor_floor -q` | 35 passed (rigor floor) | 53 passed combined (18 surrogate + 35 rigor floor) |
| `python tools/hooks/canary_runner.py` | 25 canaries pass | "All Frontier canaries passed." |
| `python tools/verify.py --smoke` | exit 0 | exit 0 |
| `just ci-parity` (CI venv) | 3300 passed, 75 skipped | 3300 passed, 75 skipped |
| `git ls-files runs` | empty | empty |
