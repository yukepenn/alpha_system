# P210000_FUTSUB_SESSION_PROVENANCE_IDENTITY — Fresh Adversarial Review

- Reviewer: Claude (fresh adversarial Yellow-lane review)
- Date: 2026-06-11
- Worktree: `/home/yuke_zhang/projects/alpha_system_wt/session-identity`
- Branch: `repair/futsub-session-identity`, base `origin/main` @ `6a4244d` (uncommitted diff, 6 files, +268/-3)
- Spec: `specs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/P210000_FUTSUB_SESSION_PROVENANCE_IDENTITY-session-truth-in-feature-contracts.md`
- Verdict: **PASS_WITH_WARNINGS**

## Scope of the diff (verified)

- `src/alpha_system/features/families/ohlcv/family.py`: `_transform_parameters` now injects
  the session-truth provenance block (`session_template_id`, `session_timezone`,
  `rth_open_time_local`, `rth_close_time_local`, `session_truth_source`) for
  `reset_on_session=True` features in addition to the pre-existing `_SESSION_TRUTH_FEATURES`
  set (new helper `_requires_session_truth_parameters`). Transform parameters are part of
  `FeatureSpec.to_identity_dict()` (verified in `features/contracts.py:383-456`), so this
  rotates `feature_version_id` for session-conditioned contracts only.
- `src/alpha_system/features/fast/vwap_session_auction.py`: new fail-closed guard
  `_validate_session_contract_parameters` — every governed pack FeatureSpec must carry
  provenance matching the live template (`load_session_template_by_id()` default =
  `session_cme_index_futures_eth`, same constant family.py uses).
- Tests: additive-only changes to `test_feature_identity_invariant.py` (rotation +
  over-rotation tests), `test_feature_store.py` (temp-registry supersession test),
  and a 3-line test-isolation pre-clear in `test_feature_cli.py` / `test_label_cli.py`.

Important context fact (verified via `git log -S`): the `_SESSION_TRUTH_FEATURES`
provenance injection for the vwap pack feature names landed at base in P194500
(#369, commit `6a4244d`). This phase's identity delta is therefore the
`reset_on_session=True` extension, the fast-pack guard, and the test/proof layer.
The vwap-pack fvids themselves are unchanged by THIS diff (they already rotated at
the P194500 merge) — recorded below because it matters for supersession bookkeeping.

## Adversarial check results

### 1. Identity rotation correctness — mutation-tested: PASS

Mutation tests executed in the worktree (files backed up, restored, md5-verified):

- **M1 (strip the new rotation)**: reverted `_requires_session_truth_parameters` to
  `name in _SESSION_TRUTH_FEATURES` only →
  `test_session_conditioned_ohlcv_identity_includes_template_truth[returns]` **FAILED**
  (KeyError on missing provenance). 1 failed / 21 passed. Restored exactly.
- **M2 (corrupt a resolved window in the identity payload)**: hardcoded
  `rth_open_time_local="03:33"` in `_session_contract_parameters` → **6 FAILURES**:
  both new identity tests (`[returns]`, `[vwap]`) AND all 4
  `test_vwap_session_auction_pack.py` tests (the new pack guard rejected the
  mismatching specs with `PackMaterializerError`). Restored exactly.

M2 also proves the parity lock: the fast vwap pack consumes the SAME
`build_ohlcv_feature_definition`-built FeatureSpecs as the reference twin (verified
in pack tests and `scaleout/driver.py` builder paths), and the pack guard fails
closed if spec provenance drifts from the live session truth used by the pack's
own `_session_clock()`. Same contract → same identity inputs → same fvid.

### 2. Over-rotation guard — independently verified cross-version: PASS

Computed fvids with a probe script under (a) the worktree code and (b) a pristine
`git archive origin/main` export (src+tests+configs+pyproject) in /tmp, using the
exact `build_ohlcv_feature_definition` path the tests use:

| probe contract | base @ 6a4244d | this diff | result |
|---|---|---|---|
| RETURNS, reset_on_session=False | `fver_643e91dc…2c7d5bc8` | `fver_643e91dc…2c7d5bc8` | IDENTICAL (no churn) |
| ROLLING_VOLATILITY, reset_on_session=False | `fver_720a55e3…b368c29` | `fver_720a55e3…b368c29` | IDENTICAL (no churn) |
| RETURNS, reset_on_session=True | `fver_f68f8b70…d4d07dde` | `fver_7253ba9e…051a9f0f` | ROTATED (intended) |
| VWAP, reset_on_session=True | `fver_f67a4b23…91cfb66` | `fver_f67a4b23…91cfb66` | IDENTICAL (already rotated at P194500 base) |

No uncontrolled identity churn: unconditioned features are bit-identical before vs
after; only `reset_on_session=True` contracts rotate in this diff. The pre-existing
invariant tests in `test_feature_identity_invariant.py` were NOT weakened — the diff
is additive only (imports + new tests; existing test bodies untouched). Note the
suite contains no literal pinned fvid constants (none existed at base either), so
the cross-version stability above is reviewer-verified, not test-pinned (W2 below).

### 3. Supersession end-to-end: PASS

`test_session_truth_supersession_registers_new_id_after_deprecating_old_id` uses a
real `FeatureStore(FeatureRegistry(tmp_path / "features.sqlite"))`: registers the
legacy-id row, derives a provably different new id, deprecates the old id with
`replacement_feature_version_id` pointing at the new id, registers the new id, then
asserts `count_feature_records() == 2`, old row `DEPRECATED` / new row `REGISTERED`,
`resolve_active_feature(old) is None`, `resolve_active_feature(new)` live, and the
deprecation record round-trips. No fixture-side filtering. Registry write-path/schema
untouched (only the existing sanctioned `deprecate_feature` / `register_materialized_feature`
API is exercised).

### 4. CLI test modifications: LEGITIMATE (not identity-related)

Both `test_feature_cli.py` and `test_label_cli.py` changes are the identical 3-line
pattern: pop `PROVIDER_CLIENT_MODULES` from `sys.modules` at the start of
`test_*_plan_fails_closed_when_dataset_version_is_missing`, mirroring the pre-clear
already used by sibling tests in the same files (lines 62/143-149). The tests'
final assertion (`module not in sys.modules` after the plan call) is intact and
unweakened — the pre-clear removes order-dependence under the spec-required
`-k "identity or version or vwap or ohlcv or session"` selection. No expectation
about identity strings changed; **no label-side identity change exists**:
`git diff --name-only` confirms zero files under `src/alpha_system/labels/**`.

### 5. Forbidden paths: CLEAN

Diff touches exactly 6 files. `src/alpha_system/labels/**`, canonicalize/dataset
configs, registry write-paths/schema, and `governance/duplicate_exposure.py` are all
untouched. The fast-pack file is `features/fast/**` (allowed producer path) and emits
values only behind the existing parity gate.

### 6. Validation truth — re-run by reviewer in the worktree: CONFIRMED

- `pytest tests/unit/features -q` → **135 passed** (matches handoff).
- `pytest tests/unit -k "identity or version or vwap or ohlcv or session" -q` →
  **262 passed, 2363 deselected** (matches handoff).
- `pytest tests/unit tests/no_lookahead tests/integration -q` →
  **3 failed, 2861 passed, 1 skipped**; failures are exactly the 3 known env
  failures (databento_canonicalize, duckdb_query_fixture, polars_lazy_fixture).
- `python tools/verify.py --smoke` → PASS.
- `python tools/hooks/canary_runner.py` → 21 canaries, "All Frontier canaries passed."
- Post-restore re-run: `tests/unit/features tests/unit/feature_compute_fast_path
  tests/unit/cli` → 235 passed (worktree left green and byte-identical: md5 of both
  src files matches the as-found state; diffstat still 6 files +268/-3; nothing staged).

### 7. Artifact policy: CLEAN

`git ls-files runs` empty; nothing staged; no SQLite/Parquet/values in the diff
(the supersession test registry is tmp_path-only); handoff/spec language is
research-only (no alpha/tradability claims). Handoff is truthful — every validation
count reproduced exactly.

## Findings

### Warnings (no repair required to merge)

- **W1 — fast-pack session guard has zero direct test coverage.** Mutation M3
  (deleting the `_validate_session_contract_parameters(...)` call from
  `_validate_vwap_session_auction_feature`) survives the ENTIRE selected suite
  (446 tests `-k "identity or version or vwap or ohlcv or session or fast or pack"`,
  plus all of `tests/unit/features` + `tests/unit/feature_compute_fast_path`).
  The guard only fires today because family-built specs always carry correct
  provenance; as a standalone fail-closed defense it can silently disappear.
  Recommended follow-up: one negative test feeding the pack a spec stripped of
  provenance and asserting `PackMaterializerError` /
  `supports_vwap_session_auction_pack(...) is False`.
- **W2 — over-rotation stability is reviewer-verified, not test-pinned.** The
  no-churn test compares fvids under a monkeypatched template within the current
  code; it cannot catch a future accidental rotation of unconditioned contracts.
  A pinned literal fvid for one unconditioned probe contract would make the
  invariant durable. (Cross-version stability was independently verified above.)
- **W3 — spec scope item 2 (session pack already-rotated verification) is not
  recorded in the handoff.** The session pack was correctly left alone, but the
  handoff should state that the consistency check was performed.
- **W4 — supersession bookkeeping nuance for the coordinator.** The vwap-pack fvid
  rotation took effect at the P194500 merge (base), not this diff; this diff adds
  the `reset_on_session=True` rotation. Coordinator deprecation of stale REGISTERED
  rows must therefore cover BOTH the vwap-pack ids (stale since P194500) and the
  reset-on-session OHLCV ids (stale as of this merge).

### Required repairs

None.

## Mutation test summary

| Mutation | Expected | Observed | Caught |
|---|---|---|---|
| M1: strip reset_on_session provenance injection (family.py) | new identity test fails | `…includes_template_truth[returns]` FAILED (1/22) | YES |
| M2: corrupt `rth_open_time_local` in identity payload (family.py) | identity tests fail | 6 FAILED: identity `[returns]`+`[vwap]` + 4 vwap pack tests (guard fired) | YES |
| M3: delete pack guard call (vwap_session_auction.py) | some test fails | 446/446 + 187/187 passed | **NO → W1** |

All mutations restored exactly (md5-verified against pre-mutation backups);
final worktree state identical to as-found (same diffstat, clean index, untracked
spec+handoff intact).

## Verdict

**PASS_WITH_WARNINGS** — the session-truth identity contract is correct,
mutation-verified, parity-locked between the fast pack and the reference twin,
provably free of identity churn for unconditioned features, and the supersession
flow is proven end-to-end on a real temp registry. Warnings W1–W4 are
coverage/bookkeeping follow-ups, none blocking.
