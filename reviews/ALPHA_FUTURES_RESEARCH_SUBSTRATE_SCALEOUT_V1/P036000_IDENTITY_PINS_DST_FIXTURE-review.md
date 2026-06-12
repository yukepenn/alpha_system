# Adversarial Review: P036000_IDENTITY_PINS_DST_FIXTURE

- Campaign: ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1
- Phase: P036000_IDENTITY_PINS_DST_FIXTURE (W2/W3 closeout, lane yellow)
- Reviewer: fresh adversarial Claude review (Workflow 1)
- Worktree: `/home/yuke_zhang/projects/alpha_system-wf1-identity-pins`
  (branch `test/identity-pins-dst`, HEAD `819c153`, diff UNCOMMITTED)
- Spec: `specs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/P036000_IDENTITY_PINS_DST_FIXTURE-w2-w3-closeout.md`
- Date: 2026-06-11

## Verdict: PASS_WITH_WARNINGS

All six review checks pass on deterministic evidence. Warnings are
informational coverage-boundary notes, not defects; no repair routing needed.

## Check 1 — Scope: tests + fixtures only, zero src changes — PASS

`git status --porcelain` shows exactly four paths, all under `tests/`:

```text
 M tests/fixtures/feature_compute_fast_path/README.md
 M tests/unit/features/test_feature_identity_invariant.py
?? tests/fixtures/feature_compute_fast_path/dst_session_boundary.py
?? tests/unit/feature_compute_fast_path/test_dst_session_boundary_pack.py
```

`git diff --name-only -- src` and `git status --porcelain -- src` are both
empty. Tracked-file diff is +117 lines across the two modified test/fixture
files; the two new files are untracked test/fixture modules.

## Check 2 — Pin truth: pins equal production-derived fvids — PASS

Construction path (read, not trusted): the pin test
`test_current_production_feature_version_ids_are_pinned` calls the REAL
production family builders imported from `alpha_system.features.families.*`
(`build_structure_feature_definition`, `build_bbo_feature_definition`,
`build_ohlcv_feature_definition`, `build_cross_market_feature_definition`).
No hand-constructed spec dicts; the comparison is a single dict-equality over
all seven cases so every pin is asserted (no early-exit masking).

Coverage: 5 session-conditioned cases (`liquidity_structure_range_contraction`,
`bbo_tradability_spread_zscore`, `base_ohlcv_atr`,
`cross_market_synchronized_returns`, `base_ohlcv_opening_range`, all
`reset_on_session=True`) + 2 unconditioned (`base_ohlcv_returns`,
`base_ohlcv_volume_zscore`, `reset_on_session=False`) — matches the spec list
exactly. Required loud-break comment block is present above the cases.

Independent spot-check (script, venv python, `PYTHONPATH=src`): built the
structure spec via the production builder with the test's exact args, then
recomputed the digest WITHOUT `FeatureVersion.derive`/`content_hash` — raw
`hashlib.sha256` over `json.dumps(..., sort_keys=True, separators=(",", ":"))`
of `{"algorithm": "feature_version_sha256_v1", "feature_contract":
spec.to_identity_dict()}`:

```text
builder fvid           fver_a1563521cb4502061b49aa43a7e1a7e214eb28b851e141373afd5ab051d68193
independent sha256     fver_a1563521cb4502061b49aa43a7e1a7e214eb28b851e141373afd5ab051d68193
pin                    fver_a1563521cb4502061b49aa43a7e1a7e214eb28b851e141373afd5ab051d68193
```

All three equal. Second pin (`base_ohlcv_returns`,
`fver_e2dd0b72...`) also confirmed equal to the builder output. Sensitivity
probes: `dataset_version_ids` DO enter identity (changing the dsv flips the
fvid); `exposure_family`/request provenance do NOT (identity hashes
`to_identity_dict()`, which drops `feature_request_id`). Conditioned spec
identity payload contains all five session-truth keys
(`session_template_id`, `session_timezone`, `rth_open_time_local`,
`rth_close_time_local`, `session_truth_source`); unconditioned `returns`
payload contains none — so a session-template change flips exactly the five
conditioned pins, which is the W1-class regression this phase exists to catch.

## Check 3 — Fixture honesty + DST coverage — PASS

`tests/fixtures/feature_compute_fast_path/dst_session_boundary.py`:

- Every row carries STATIC `session_label = "ETH"`; no session classification
  is computed anywhere in the fixture (only timestamp arithmetic to lay out
  bars at offsets -2..+22 minutes around each RTH open).
- Timestamps span the March 2024 transition week — Fri 2024-03-08 14:30Z
  (EST regime) and Mon 2024-03-11 13:30Z (EDT regime, transition 2024-03-10) —
  plus a pure summer EDT day, Tue 2024-07-02 13:30Z.
- Boundary flip: `test_dst_fixture_session_classification_flips_utc_open_edges`
  asserts via PRODUCTION `classify_session_timestamp` that open-minus-1-minute
  is ETH and the open itself is RTH at 14:30Z (EST day) and at 13:30Z (both
  EDT days), and that `rth_open_ts` equals each expected UTC open.
- Parity per repointed family: structure (RANGE_CONTRACTION), bbo
  (SPREAD_ZSCORE), regime/ohlcv (ATR), volume (VOLUME_ZSCORE), cross_market
  (SYNCHRONIZED_RETURNS, strict_intersection over ES/NQ/RTY) — all with
  `reset_on_session=True`, all asserted fast-vs-reference at tolerance 1e-12,
  with `_assert_records_cover_dst_boundaries` proving the three RTH-open event
  timestamps are present in the compared records.
- The static label is load-bearing, not decorative: the reference path derives
  segments per-row from the session template
  (`families/structure/family.py: _session_states -> _session_state(row,
  template)`, `classify_session_timestamp` imported at line 18) and the fast
  path derives them in polars from `bar_start_ts` vs the template RTH clock
  (`features/fast/liquidity_pa_structure.py: _is_rth/_template_session_label`,
  same pattern in `cross_market_panel.py` etc.). Neither path can satisfy the
  reset semantics from the fixture's constant "ETH" label.

## Check 4 — Mutation tests (restored byte-identical) — PASS

Baseline sha256:

```text
0a359f921cb9de7540d2d3ffac38665d1ef46ba22f8dfefaa62f11dc03ccab16  tests/unit/features/test_feature_identity_invariant.py
e121e778ffa7e042e117e28476cf61f7bad5911247dfe21c78e6d39137c5c69c  tests/fixtures/feature_compute_fast_path/dst_session_boundary.py
```

- (a) Perturbed one hex char of the structure pin (`fver_a156...` ->
  `fver_b156...`): pin test FAILED (`1 failed in 0.12s`). Restored; sha256
  identical to baseline.
- (b) Shifted the fixture's pre-DST RTH open by one hour (14:30Z -> 15:30Z):
  DST flip test FAILED (`test_dst_fixture_session_classification_flips_utc_open_edges`,
  AssertionError at line 68; `1 failed, 1 passed`). Restored; sha256 identical
  to baseline. Note: the parity test stayed green under this mutation — a
  uniform timestamp shift keeps fast and reference mutually consistent by
  construction, so boundary TRUTH is carried by the flip test against
  production `classify_session_timestamp`, which is exactly what failed.
- (c) Source sabotage is impossible without src edits; verified instead that
  the parity test consumes the REAL paths via imports: reference =
  `compute_{structure,bbo,ohlcv,cross_market}_feature` from
  `alpha_system.features.families.*` over `build_{ohlcv,bbo}_input_view`;
  fast = `PackMaterializer`/`build_fast_feature_pack` from
  `alpha_system.features.fast`. No mocks, no reimplemented session logic in
  the test.
- Post-restore: both test files green (`20 passed in 0.40s`).

## Check 5 — Validation commands (venv `~/.venvs/alpha_system_research`) — PASS

- `pytest tests/unit/features tests/unit/feature_compute_fast_path -q`:
  **200 passed in 4.12s** (includes the 3 new tests: 1 pin + 2 DST).
- `python tools/hooks/canary_runner.py`: **23 PASS**, "All Frontier canaries
  passed.", exit 0.
- `python tools/verify.py --smoke`: exit 0.

Executor's extra `verify.py --all` reported 3 local failures
(`test_duckdb_query_fixture`, `test_polars_lazy_fixture`,
`test_databento_canonicalize_quality_coverage_and_register_offline`) — all in
integration/data areas this tests-only diff does not touch; honestly reported
in the notes and outside this phase's required validation set.

## Check 6 — Git hygiene — PASS

`git diff --cached --name-only` empty (nothing staged); `git ls-files runs`
empty; no commit was made (diff is working-tree only, as specified).

## Warnings (informational, no repair required)

1. **Pins guard the derivation contract, not literal production-registry
   fvids.** `dataset_version_ids` enter identity and the pins use a fixed
   synthetic `dsv_identity_pin_fixture_v1`, so the pinned hex values are not
   the fvids of any materialized production feature. They DO flip on any
   identity-affecting change to the family builders, FeatureSpec contract,
   canonical serialization, or session template (verified empirically), which
   is the stated W2 purpose and matches the file's existing test idiom. A
   change confined to how production assembles dataset_version_ids outside the
   builders would not flip pins — accepted coverage boundary.
2. **Parity is uniform-shift-insensitive by construction** (mutation (b)
   evidence): the DST boundary truth lives in the flip test, the cross-regime
   consistency in the parity test. Together they cover the spec's claim; alone
   neither would.
3. **Worktree base is 2 commits behind origin/main** (`819c153` vs `97cf79d`);
   delta is docs/campaign-only (`OPERATING_COMPASS_V4.md`, RIGOR campaign
   files) — verified to touch no `src/` or `tests/` path, so pins are current
   against origin/main.

## Evidence basis

All findings above are from commands run in this review session (git
status/diff/ls-files, pytest, canary_runner, verify --smoke, sha256sum,
independent hash recomputation script) — not from the executor's notes.
Executor notes at `/tmp/identity_pins_notes.md` were cross-checked and found
truthful (counts, file list, pin values, validation results all reproduce).
