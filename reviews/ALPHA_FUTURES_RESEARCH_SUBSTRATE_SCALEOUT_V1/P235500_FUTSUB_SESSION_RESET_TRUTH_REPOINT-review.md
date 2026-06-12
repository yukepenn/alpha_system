# Fresh Adversarial Review — P235500_FUTSUB_SESSION_RESET_TRUTH_REPOINT

- Reviewer: Claude (fresh adversarial, Workflow 1)
- Date: 2026-06-11
- Worktree: `/home/yuke_zhang/projects/alpha_system-wf1-session-reset` (branch `repair/session-reset-truth-repoint`, base `origin/main` = `4e7c21e`)
- Diff: uncommitted; 19 modified files + 1 new file (`src/alpha_system/features/session_truth.py`); 964 insertions / 44 deletions
- Baseline worktree integrity: `git diff | sha256sum` = `2e7d590d0f05af17e6e43cd6f9c3d86c861025d6e0ae7603fe6d8f655d15290a`; `git status --porcelain | sha256sum` = `717a63c81487ff157597779ca1dff0b9299368c64ed43af2d7a140afdb1d6b21`. Verified byte-identical after every mutation restore and at review end.

## Verdict: PASS_WITH_WARNINGS

---

## 1. Single truth (PASS)

- `src/alpha_system/features/session_truth.py` is a thin accessor: it loads the
  `session_cme_index_futures_eth` template via
  `data/foundation/sessions.py::load_session_template_by_id` and derives
  `session_contract_parameters()` (identity payload) and `SessionTruthClock`
  (template times converted to seconds) from the loaded template fields. Zero
  hardcoded window constants, zero timezone math, zero DST logic.
- Reference paths (structure/bbo/cross_market `family.py`) call
  `classify_session_timestamp(row.bar_start_ts, template=...)` per row — direct
  delegation. ohlcv reference was already repointed (P194500/P210000), verified
  unchanged in this diff.
- Fast twins derive `_SESSION` in polars from `bar_start_ts` via
  `convert_time_zone(clock.timezone)` + clock-seconds comparison against
  template-derived `rth_open_seconds`/`rth_close_seconds` — generated FROM the
  shared template, not hardcoded. Semantics match the reference exactly:
  `classify_session_timestamp` is binary RTH/ETH, start-inclusive /
  end-exclusive, on wall-clock local time (sessions.py:692-737); maintenance
  breaks do not feed segment_label in either path. Parity is mutation-verified
  (section 5). This polars pattern pre-exists in the P194500 twins
  (`session_calendar_roll.py`, `vwap_session_auction.py`, both untouched).
- No second PnL/value truth: producer fast-path emits values only, gated by the
  parity harness.

## 2. Over-rotation guard (RUN — MATERIAL FINDING, see W1)

Independent cross-version probe (`/tmp/fvid_probe.py`): identical specs built
with `PYTHONPATH=<origin/main src>` vs `PYTHONPATH=<worktree src>`, comparing
`derive_feature_version().feature_version_id`:

| spec | pre/post fvid |
|---|---|
| ohlcv returns reset=False | BIT-IDENTICAL (`fver_643e91dc...`) |
| ohlcv volume_zscore reset=False | BIT-IDENTICAL (`fver_c40ed86a...`) |
| ohlcv rolling_range reset=False | BIT-IDENTICAL (`fver_f5a9433b...`) |
| bbo mid | BIT-IDENTICAL (`fver_19588db5...`) |
| bbo spread | BIT-IDENTICAL (`fver_4ce9dc01...`) |
| structure close_location_value reset=False | **ROTATED** (`278ef6b1` → `2c5cb4e7`) |
| structure prior_high_distance reset=False | **ROTATED** (`7c247e2c` → `54f44b5f`) |
| structure prior_high_distance reset=True | ROTATED (intended) |
| bbo spread_zscore reset=False | **ROTATED** (`655f6c1b` → `4b45b436`) |
| bbo spread_zscore reset=True | ROTATED (intended) |
| cross_market synchronized_returns reset=False | **ROTATED** (`9ef3a16f` → `85cf99bc`) |
| cross_market synchronized_returns reset=True | ROTATED (intended) |

Root cause of the non-intended rotations: `field_roles` was added to
`_input_metadata()` unconditionally in structure and cross_market (and for any
bbo feature declaring `session_label`, i.e. spread_zscore at any reset flag),
and `FeatureInputSpec.input_metadata` is part of `to_identity_dict()`
(contracts.py:154, 383-401). See W1 for disposition. The spec's named
over-rotation examples (ohlcv returns/volume_zscore/rolling_range) and bbo
mid/spread are bit-identical, and session-truth parameters are correctly gated
to session-conditioned specs only (verified: `SESSION_TRUTH_KEYS` disjoint from
reset=False identity parameters, asserted in
`test_remaining_non_session_conditioned_identities_ignore_session_template_changes`).

Stored-value drift check: `FeatureValueRecord` (contracts.py:534) carries no
`session_label` field, and primitives ignore point session labels unless
`reset_on_session=true` — so the reference-path label overwrite is value-inert
for unconditioned features (all pre-existing pinned-value family tests pass
unchanged).

## 3. Session-conditioned rotation (PASS)

`test_remaining_session_conditioned_family_identities_include_template_truth`
asserts, for structure PRIOR_HIGH_DISTANCE, bbo SPREAD_ZSCORE, cross_market
SYNCHRONIZED_RETURNS (all reset=True): session_template_id / timezone / local
RTH window / source present in identity parameters AND fvid differs from the
legacy (parameter-stripped) spec. Mutation B confirms the test fails when the
payload is removed. Cross-version probe confirms real pre/post rotation.

## 4. Absolute-truth tests + fixture honesty (PASS)

- Boundary: `test_structure_reset_and_opening_range_ignore_static_session_label`
  (08:28–08:31 CT spanning RTH open, static "ETH" labels),
  `test_spread_zscore_reset_uses_timestamp_truth_when_session_label_is_static`
  (14:58–15:00 CT spanning RTH close, static "RTH" labels),
  `test_cross_market_return_reset_uses_timestamp_truth_when_session_label_is_static`
  (asserts ["RTH","RTH","ETH"] snapshot labels + session_reset flag). Fast-pack
  fixtures repinned to real boundaries (structure: 14:24Z start → index 6 =
  08:30 CT open; bbo/cross_market/regime/volume: 20:54Z start → index 6 = 15:00
  CT close).
- Fixture honesty: all fixtures use STATIC session labels + REAL timestamps;
  none computes session labels from timestamps. Honest.
- DST: covered at the shared-truth layer
  (`tests/unit/data/test_sessions_calendar.py::test_session_timestamp_classification_is_dst_aware`,
  14:30Z/CST vs 13:30Z/CDT both = 08:30 local RTH open). No family-level or
  fast-twin DST test added in this diff (see W3).
- Resolver acceptance: contract tests call
  `runtime/input_resolver._reject_label_as_live_feature` on the new contracts
  with `field="feature_pack_refs[0]"` and they pass. Independently verified the
  guard genuinely rejects without the marker (section 5, mutation C probe).
  `input_resolver.py` itself is untouched.

## 5. Mutation tests (all run; worktree sha256-verified restored after each)

| name | mutation | expected | observed | result |
|---|---|---|---|---|
| A1 boundary sabotage (open) | `session_truth.py` `rth_open_seconds` +3600 | parity/boundary failures | `test_liquidity_pa_structure_pack_matches_reference...` FAILED (1 failed, 51 passed) | PASS (open-boundary fixture = structure) |
| A1b boundary sabotage (close) | `session_truth.py` `rth_close_seconds` +3600 | parity failures in close-boundary families | 6 FAILED: bbo, cross_market (strict+asof), regime (x2), volume parity tests | PASS |
| A2 constant label (reference) | structure `_session_state` forced `"ETH"` | boundary/parity failures | 3 FAILED: new boundary test, gating test, structure pack parity | PASS |
| B identity payload removal | bbo `_transform_parameters` drops `_session_contract_parameters()` | rotation test fails | 3 FAILED: identity rotation test, bbo contract test, bbo fast pack (PackMaterializerError — fast twin refuses param-less contract) | PASS |
| C role-marker removal | structure `_input_metadata` drops `field_roles` | resolver-acceptance test fails | contract test FAILED (KeyError on `field_roles`); direct probe: `_reject_label_as_live_feature` → `RuntimeInputResolverError: labels must not be exposed as live feature inputs` | PASS |

Every A1+A1b together: each of the 5 repointed fast packs catches a boundary
sabotage on at least one boundary. Final worktree shas equal baseline
(`2e7d590d...` / `717a63c8...`) — byte-identical, no residue.

## 6. Full validation (run by reviewer)

| command | result |
|---|---|
| `pytest tests/unit/features tests/unit/feature_compute_fast_path -q` | 197 passed |
| `pytest tests/unit tests/no_lookahead tests/integration -q` | **2911 passed, 3 failed, 1 skipped** (52.24s) |
| `tools/verify.py --smoke` | rc=0 |
| `tools/hooks/canary_runner.py` | All Frontier canaries passed (incl. governance_future_shift / permuted_labels / optimistic_fill) |

The 3 failures are the known pre-existing local env failures —
`tests/unit/data/test_databento_canonicalize.py::test_databento_canonicalize_quality_coverage_and_register_offline`,
`tests/integration/test_duckdb_query_fixture.py::test_duckdb_query_over_tiny_csv_fixture`,
`tests/integration/test_polars_lazy_fixture.py::test_polars_lazy_transformation_over_tiny_fixture`
— reproduced identically with `PYTHONPATH=<origin/main src>` (3 failed, 4
passed), i.e. independent of this diff.

## 7. Forbidden paths (PASS)

Changed set contains zero paths under `src/alpha_system/labels/**`,
`runtime/input_resolver.py`, `governance/duplicate_exposure.py`,
canonicalize/dataset configs, `research/futures_core_alpha_pilot_v1/**`, or
registry write-path/schema. Tests IMPORT a private resolver symbol but the
module is unmodified.

## 8. Artifact policy (PASS)

Staged set empty (0 files staged). `git ls-files runs` empty. Untracked set =
the one new source file only. No values/SQLite/Parquet/runs artifacts.

---

## Findings

### W1 (warning, material): identity rotation extends beyond session-conditioned contracts

ALL structure-family specs (including point-in-time `close_location_value` and
reset=False variants), ALL cross_market specs, and bbo `spread_zscore` at
reset=False rotate fvid pre/post diff (empirical probe above), because the
`field_roles` marker lands in identity-hashed `input_metadata`. This deviates
from the spec's "Non-session-conditioned features must NOT rotate" sentence
read literally. It is, however, (a) sanctioned by spec scope item 2 ("add
field_roles ... wherever `session_label` is a declared input field" — structure
and cross_market declare it for every feature), (b) functionally REQUIRED:
markerless contracts genuinely trip the resolver guard (proved by direct
probe), so conditionally marking only reset=True specs would leave non-reset
structure/cross_market records resolver-rejected (the exact P27 GAP defect
class), and (c) value-inert (no stored-row drift; FeatureValueRecord has no
session_label). DISPOSITION: accepted with mandatory data-op consequence — the
coordinator data-op phase MUST treat ALL structure + ALL cross_market +
spread_zscore contracts as re-keyed, not only the reset/session-conditioned
list in the executor notes, which understate the blast radius
("Affected reset/session-conditioned packs").

### W2 (warning): no pinned-hash identity regression test

The in-repo over-rotation guard
(`test_remaining_non_session_conditioned_identities_ignore_session_template_changes`)
asserts template-change invariance under the NEW code only; it cannot catch
pre/post metadata churn (it did not catch W1). Pinned fvid hash assertions for
a small set of unconditioned specs remain the gold standard and are absent.
Recommend adding pinned hashes in a follow-up so the next phase that touches
`_input_metadata` rotates loudly instead of silently.

### W3 (warning): no DST coverage for the polars fast-path session derivation

All new family/fast tests and fixtures use winter (CST) timestamps. DST
correctness of the fast `_SESSION` derivation rests transitively on
`convert_time_zone` + the shared-truth DST test. The gap is pre-existing (the
P194500 twins `session_calendar_roll`/`vwap_session_auction` are equally
CDT-untested) and the derivation is template-parameter-driven, but one
summer-boundary parity fixture would close it cheaply.

### I1 (info): `_template_session_label`/`_is_rth`/`_local_seconds` are duplicated
across 4 fast twins (plus the 2 pre-existing twins' variants). Parameter-driven,
so not a second truth, but drift-prone; candidate to hoist into
`features/session_truth.py` or the fast materializer in a later cleanup.

### I2 (info): resolver acceptance is tested via direct private call
(`_reject_label_as_live_feature` + `SimpleNamespace`) rather than a temp-registry
resolve. Adequate and mutation-verified, but couples tests to a private symbol.

### I3 (info): executor skipped validation commands 3–5 per the executor prompt
("full suite runs at review"); reviewer ran all of them — green modulo the 3
named pre-existing env failures. Handoff deviations section is truthful.
