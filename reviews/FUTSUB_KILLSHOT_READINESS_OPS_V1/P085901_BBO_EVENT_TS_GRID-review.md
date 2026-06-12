# Adversarial Review: P085901_BBO_EVENT_TS_GRID

- Campaign: `FUTSUB_KILLSHOT_READINESS_OPS_V1`
- Phase: `P085901_BBO_EVENT_TS_GRID` (Yellow)
- Branch: `wf1/bbo-grid` @ `38ae871` (one commit ahead of `origin/main`)
- Reviewer: fresh Claude (adversarial stance), 2026-06-12
- Verdict: **PASS_WITH_WARNINGS**

## Scope reviewed

`git diff origin/main` (16 files): bbo family reference + fast emission,
bbo/dst test fixtures + tests, new `registry_event_ts_grid` canary module +
package exports + canary_runner registration + synthetic fixture + README,
`docs/FACTOR_COMPUTE.md` contract, regenerated `docs/SYSTEM_MAP.md`, spec,
handoff.

## Checks performed (deterministic evidence)

### 1. Both paths fixed identically — PASS

- Reference: `src/alpha_system/features/families/bbo/family.py` lines 638
  (`_feature_value_record`), 701 and 711 (spread-zscore `PrimitivePoint`s,
  gap and value branches) all emit `row.bar_end_ts`. `grep` shows no
  remaining `row.event_ts` emission site in the family (line 567 is input
  validation only — correct, event_ts stays an input property).
- Fast: `src/alpha_system/features/fast/bbo_tradability.py:317` builds the
  internal `_EVENT_TS` alias from `bar_end_ts`; `:106 event_ts_expr` and the
  `:321 _BAR_END_TS` alias both derive from the same column, so every fast
  emission uses the bar grid. `event_ts` remains a required input column
  (input property), consistent with the written contract.
- Parity still covers event_ts: `tests/unit/feature_compute_fast_path/parity_harness.py`
  `_record_key` includes `event_ts`, and `assert_feature_records_match`
  requires key-set equality. The pack test additionally asserts BOTH
  reference and fast emitted event_ts tuples equal the fixture `bar_end_ts`
  values. `parity_harness.py` itself is untouched (no weakening).

### 2. available_ts, quality_flags, values untouched — PASS

Diff over `features/**` contains only the three reference `event_ts=`
lines and the one fast alias line. `available_ts` (canonical
`bar_end_ts + latency`, `canonicalize.py:1015`), quality flags, and value
math are unchanged.

### 3. PIT (no lookahead) — PASS, constraint cited

`src/alpha_system/data/databento/canonicalize.py:999-1001` quarantines any
BBO row unless `bar_start_ts <= event_ts <= bar_end_ts`
("Databento BBO ts_event outside OHLCV minute quarantined"). Therefore
`bar_end_ts >= quote event_ts` always holds for canonical BBO input, and
re-stamping to `bar_end_ts` claims the observation later-or-equal — strictly
conservative. `available_ts` (the actual PIT gate) is untouched.

### 4. Fixture updates preserve assertion strength — PASS (strengthened)

Fixtures move input quote timestamps OFF the minute boundary
(`bar_end - 200ms`), and the tests add guards that the input is genuinely
off-grid (`assert any(row["event_ts"] != row["bar_end_ts"] ...)` /
`assert any(row.event_ts != row.bar_end_ts ...)`) plus explicit emitted
== bar_end_ts assertions on both paths. No assertions deleted, no tolerance
loosened.

### 5. Grid canary — PASS (live run executed by reviewer)

- Follows the canary_runner idiom: registered in `scenarios()` with
  `expect_block=False, report_on_pass=True`; `run_canary` pass logic
  (`passed = blocked if expect_block else not blocked`) handles it correctly.
- Allowlist is a visible module-level tuple
  (`REGISTRY_EVENT_TS_GRID_ALLOWLIST`) with named entries + reason codes
  (`BBO_PENDING_RE_MATERIALIZATION`, `COST_SPREAD_LABEL_MIRROR_DEFECT`);
  removal of an entry is a one-line deletion. ALLOW lines are printed
  (visible-not-failing).
- CI mode uses the committed synthetic fixture; full
  `tools/hooks/canary_runner.py` run is green including the new canary
  (`scanned=3 off_grid=4 allowed_debt=4 violations=0`).
- **Live mode run by this reviewer, READ-ONLY**
  (`sqlite3 ... ?mode=ro`, `ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system`):
  `PASS registry_event_ts_grid scanned=2680 off_grid=528 allowed_debt=528 violations=0`,
  exit 0. All 528 allowed issues are `family=bbo_tradability`
  (264 REGISTERED bbo registrations x first/last), all carrying
  `reason=BBO_PENDING_RE_MATERIALIZATION` — the bbo debt is flagged via the
  allowlist exactly as specified.
- Live skip is loud (`SKIP ... ALPHA_DATA_ROOT is unset`), covered by tests.

### 6. Identity claim "fvids do not rotate" — PROVEN

`tests/unit/features/test_feature_identity_invariant.py`
(`test_current_production_feature_version_ids_are_pinned`) pins literal
`fver_...` hashes including `bbo_tradability_spread_zscore` and passes on
this branch (18 passed). Emitted event_ts is value content, not identity
payload; the handoff claim is backed by deterministic pins, not prose.

### 7. Mutation tests (restored after each; tree clean at end)

- **Mutation A** — reverted all three reference-path `event_ts` emission
  lines back to `row.event_ts` (fast path left fixed): parity/pack tests
  FAIL as required —
  `test_bbo_tradability_pack_matches_reference_on_synthetic_fixture` FAILED,
  `test_all_bbo_features_are_gated_versioned_causal_and_available` FAILED
  (2 failed, 9 passed). Restored via `git checkout --`; suite green again
  (11 passed); `git status` clean.
- **Mutation B** — synthetic fixture with a NON-allowlisted off-grid entry
  (`family=base_ohlcv`, `first_event_ts=...:00.500000`): canary CLI exits 1
  with `FAIL ... violations=1` and a VIOLATION line naming family and pack.
  (Temp fixture under /tmp; repo untouched.)

### 8. Scope and handoff truthfulness — PASS

- Diff confined to bbo family (both paths) + tests/fixtures + canary +
  docs + spec/handoff. No other family, no engine, no diagnostics-join, no
  canonical-layer change.
- Handoff "16 passed, 2 skipped" reproduces as 18 passed under the research
  venv: the 2 skips are `pytest.importorskip("polars")` under the system
  python the handoff used — environment difference, not weakening; the
  research-venv run is strictly stronger.
- Reviewer re-ran: focused suite 18 passed; features+fast-path+futsub
  332 passed; governance 645 passed; `verify.py --smoke` exit 0;
  `just ci-parity` 3309 passed / 75 skipped (matches handoff);
  `git ls-files runs` empty.
- Minor cosmetic string re-wraps in `tools/hooks/canary_runner.py`
  (line-length): verified behavior-neutral by string-concatenation
  equivalence and by the green canary run. Mild formatting creep, accepted.

## Findings (warnings)

- **W1 — dead grandfather entry for cost/spread labels (masking risk).**
  Live registry today: 432 REGISTERED `cost_adjusted` label registrations,
  **zero** off-grid; all 938 off-grid `cost_adjusted` rows are DEPRECATED
  (the spec's "469 cost/spread-adjusted registrations" debt was evidently
  repaired/deprecated before this phase ran). The
  `COST_SPREAD_LABEL_MIRROR_DEFECT` allowlist entry has `id_prefix=""` and
  therefore grandfathers the ENTIRE `cost_adjusted` family: any FUTURE
  off-grid cost_adjusted registration would be silently allowed.
  Recommendation: delete that one allowlist line (the design makes it a
  one-line change) in the re-materialization follow-up, and verify with a
  live-mode run.
- **W2 — silent zero-row scan on schema drift.** `_read_registry_rows`
  returns `()` when the expected table is absent, so a renamed registry
  table would make live mode pass while scanning nothing. Verified today
  that `feature_registry_records` / `label_registry_records` exist in the
  live registries, so coverage is real now; prefer a loud skip/error on a
  missing table in a follow-up.
- **W3 — stale debt narrative.** Handoff/README state the cost/spread label
  debt persists "until repaired and re-locked"; the live registry shows it
  already repaired. Codex disclosed honestly that it could not run live
  mode (no ALPHA_DATA_ROOT in the worktree), so this is staleness, not
  untruthfulness.

## Verdict

**PASS_WITH_WARNINGS** — both emission paths fixed and parity-gated
(mutation-proven), PIT conservative with the canonical constraint cited,
contract written, canary live-verified against the real registry with
visible allowlisted bbo debt and a proven non-allowlisted fail path,
identity pins green, validation reproduced. W1-W3 are follow-up hygiene,
none blocks merge.
