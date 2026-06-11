# P183000_FUTSUB_SESSION_SEGMENT_REPAIR — Fresh Adversarial Yellow Review

- Reviewer: Claude (fresh adversarial Yellow-lane reviewer)
- Reviewed at: 2026-06-11
- Target: uncommitted working tree of `/home/yuke_zhang/projects/alpha_system_wt/session-repair`
  (branch `repair/futsub-session-segmentation`, base `origin/main` @ `e520c6e`)
- Spec: `specs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/P183000_FUTSUB_SESSION_SEGMENT_REPAIR-rth-segmentation-single-truth.md`
- Verdict: **PASS_WITH_WARNINGS**

## 1. Absolute-truth tests (not parity theater) — PASS

The new tests assert timestamp-derived expectations, independently of the
canonical `session_label` input:

- `tests/unit/data/test_sessions_calendar.py::test_session_timestamp_classification_is_dst_aware`
  pins both DST regimes. I manually recomputed both: 2024-01-10 Chicago is CST
  (UTC-6) so RTH open 08:30 CT = **14:30 UTC**; 2024-07-10 is CDT (UTC-5) so
  08:30 CT = **13:30 UTC**. The test asserts exactly those UTC instants for
  `rth_open_ts`/`rth_close_ts` (close 21:00 / 20:00 UTC respectively) plus the
  local renderings `08:30 CST` / `08:30 CDT`.
- `...::test_session_timestamp_classification_handles_rth_bar_start_edges`
  pins 08:30 inclusive (RTH, minutes 0/390), 14:59 (RTH, 389/1), 15:00
  exclusive (ETH, nulls) at America/Chicago, and trade-date rollover at 17:00
  local (`ES_c_0:2024-01-11:ETH`).
- `tests/unit/features/families/session/test_session_family.py::test_session_position_features_ignore_static_session_label_for_rth_truth`
  feeds rows whose `session_label` is statically `"ETH"` (the real-data
  degenerate condition) at UTC instants spanning EST and EDT and asserts
  rth/eth flags, minutes_from/to (null outside, correct inside), session_id
  segmentation, and the outside_rth/before/after quality flags.
- `tests/unit/feature_compute_fast_path/test_session_calendar_roll_pack.py::_assert_fixture_coverage`
  now pins exact absolute value vectors for the reference side of the parity
  fixture (with provenance comment), so parity can no longer bless a
  degenerate pair.
- `tests/unit/feature_compute_fast_path/test_vwap_session_auction_pack.py::test_vwap_opening_range_uses_timestamp_rth_when_session_label_is_static_eth`
  forces every fixture row's label to `"ETH"` and asserts `opening_range` is
  non-null on RTH rows from the fast pack — the exact downstream defect
  (0-non-null of 346,858 ES rows) reproduced and repaired.

### Mutation tests (performed by reviewer, restored byte-identically)

Pristine copies were saved before each mutation; restoration verified with
`diff -q` against the saved executor versions and a re-run of the affected
tests (green).

| Mutation | Site | Result |
|---|---|---|
| A: `rth_segment_flag` reads canonical `session_label` again (reference engine, `families/session/family.py`) | label-copy defect class | **2 tests FAIL**: `test_session_position_features_ignore_static_session_label_for_rth_truth` + `test_session_calendar_roll_pack_matches_reference_on_synthetic_fixture` (absolute fixture pins) |
| B: drop `convert_time_zone` in fast twin `_local_bar_start` (`fast/session_calendar_roll.py`) | fixed-UTC defect class | **1 test FAIL**: parity vs the now-correct reference (`parity_harness.py:209`) |
| C: drop `astimezone` in shared `classify_session_timestamp` (`data/foundation/sessions.py`) | corrupt the shared truth itself — parity can never catch this | **2 tests FAIL**: `test_session_timestamp_classification_is_dst_aware` + the family absolute test |

All three defect classes are detected; the test suite is not parity theater.

## 2. Single truth, no third copy — PASS with one residual (warning)

- Grep for `14:30|21:00|08:30|15:00` over the three consumer files
  (`families/session/family.py`, `fast/session_calendar_roll.py`,
  `fast/vwap_session_auction.py`): **zero hits**. All windows come from
  `load_session_template_by_id` / `classify_session_timestamp` in
  `data/foundation/sessions.py`, backed by
  `configs/data/session_templates_and_calendar.json`
  (`session_cme_index_futures_eth`: America/Chicago, rth 08:30–15:00,
  eth 17:00→16:00, maintenance 16:00–17:00).
- The old fixed-UTC parameter defaults are gone; `rth_open_time_local`/
  `rth_close_time_local` + `session_template_id`/`session_timezone` are
  recorded in transform parameters and **cross-validated against the template,
  failing closed on mismatch in both engines** (reference
  `_session_template_for_definition`, fast `_validate_session_calendar_roll_feature`
  and `_session_template_from_parameters`).
- `src/alpha_system/labels/**` is untouched (`git diff` + `git status` clean for
  that subtree). The handoff records the labels-adoption follow-up explicitly.
- Semantic agreement with the labels truth verified: same timezone
  (America/Chicago), same RTH window (08:30/15:00), same maintenance window,
  and the same trade-date rollover rule (labels `_cme_trade_date` rolls at
  >= 17:00 local; feature `_template_trade_date` rolls at >= eth_start 17:00).
- **Boundary-inclusion difference (flagged, informational)**: labels
  `_is_close_out_terminal_candidate` (fixed_horizon/family.py:962) treats an
  event at exactly 15:00 CT as RTH-eligible (`<= _RTH_SESSION_CLOSE`,
  inclusive) for the SESSION_CLOSE close-out **anchor**, while the new feature
  truth is bar-start `[08:30, 15:00)` exclusive. These are different objects
  (event-ts anchor eligibility vs bar-start segment membership), so it is not
  a present contradiction — but the recorded labels-adoption follow-up MUST
  carry this note so adoption does not silently shift close-out anchoring by
  one bar.
- **Residual second consumer (WARNING W1)**: the reference OHLCV family
  `src/alpha_system/features/families/ohlcv/family.py` — the reference twin of
  the `vwap_session_auction` fast pack — still derives RTH/ETH membership for
  rth_flag/eth_flag/opening_range/overnight_range/anchored_vwap from
  `row.session_label` (lines ~719–869). On real canonical data (label
  statically `"ETH"`), the repaired fast pack and this reference engine now
  diverge by construction for RTH-conditioned outputs; fixture parity passes
  only because the fixture labels were aligned with timestamps. The spec
  deliberately scoped only the fast `_IS_RTH` repair and the handoff records
  this residual honestly in Risks. This is acceptable for the phase but must
  be a tracked follow-up BEFORE any reference recomputation/reconciliation of
  vwap features on real data is treated as authoritative.

## 3. Forbidden paths — PASS

- `git diff origin/main` touches exactly 9 files; none under
  `src/alpha_system/labels/**`, none in `data/databento/canonicalize.py`, no
  dataset configs, no registry write-paths.
- `data/foundation/sessions.py` diff is **purely additive**: 0 removed lines
  (verified by grep on the diff). New constant, `SessionWindowState`,
  `load_session_template_by_id`, `classify_session_timestamp`,
  `session_segment_id`, two private helpers, `__all__` additions. No existing
  function body changed ⇒ canonicalize-time/quarantine behavior is unchanged
  by construction.

## 4. Fast-path discipline — PASS

- Both fast files remain values-only producers (no registry/value writes
  added; expressions only).
- The Polars logic uses `dt.convert_time_zone(rth_clock.timezone)` (true IANA
  conversion, DST handled by Polars' tz machinery), NOT a fixed offset —
  confirmed in both `_local_bar_start` implementations, and behaviorally by
  mutation B and by the suite passing for both EST and EDT fixtures.
- **WARNING W2 (latent, no real-data exposure)**: fast `_template_trade_date`
  uses `local + polars.duration(days=1)` (physical 24h) where the reference
  uses calendar-date `+ timedelta(days=1)`. Across a spring-forward
  transition, a bar with local wall time in [23:00, 24:00) would land two
  calendar dates ahead in the fast path. Trigger window is Saturday
  23:00–24:00 CT before a Sunday 02:00 transition — CME index futures are
  closed then (Fri 16:00 → Sun 17:00), so no real bar can hit it; fixtures
  cannot catch it either. Recommend `dt.offset_by("1d")` in a follow-up for
  exactness.
- Minor: reference `_rth_minutes_point` final
  `return _point(row, None, ("outside_rth", negative_flag))` is unreachable
  dead code (the two prior branches exhaust the non-RTH cases). Harmless.

## 5. No assertion weakening — PASS

Every modified test/fixture inspected:

- `tests/fixtures/feature_compute_fast_path/vwap_session_auction.py`: rows 8/9
  moved 15:00→21:00 UTC **with a P183000 provenance comment** (scenario
  "ETH at/after close" preserved under the corrected America/Chicago close).
  Row 0 label `"HALT"`→`"ETH"`: the static HALT label was part of the old
  fiction (canonical session_label is a coverage descriptor; halt truth lives
  in `halt_status_flag`, which is unchanged and separately tested in
  `test_session_family.py` and the session pack). Acceptable; noted.
- `test_vwap_session_auction_pack.py`: `no_overnight_range`→`no_overnight_trade`
  for row 0 is a consequence of that label change (row 0 is now an ETH
  no-trade row); both flags are real engine outputs (ohlcv family lines
  814/822, fast lines 505/510) and the exact-tuple assertion form is retained
  — no weakening. New static-ETH fast test ADDS coverage.
- `test_session_calendar_roll_pack.py` / `test_session_family.py`: additions
  only (absolute pins + parameter-contract pins incl. asserting the OLD
  `rth_*_time_utc` keys are gone), with provenance comments. No assertion
  deleted or relaxed anywhere in the diff; spec section 6 authorization
  covers the two fixture expectation updates and is cited via provenance
  notes.

## 6. Validation truth (re-run by reviewer in the worktree) — PASS, matches handoff exactly

- `pytest tests/unit/features -q` → `128 passed`
- `pytest tests/unit -k "session or vwap or rth" -q` → `119 passed, 2498 deselected`
- `pytest tests/unit tests/no_lookahead tests/integration -q` →
  `3 failed, 2853 passed, 1 skipped` — the 3 failures are exactly the known
  pre-existing env failures: `test_databento_canonicalize_quality_coverage_and_register_offline`,
  `test_duckdb_query_over_tiny_csv_fixture`,
  `test_polars_lazy_transformation_over_tiny_fixture`.
- `python tools/verify.py --smoke` → pass.
- `python tools/hooks/canary_runner.py .` → `All Frontier canaries passed.`
- All re-runs after mutation restoration confirmed green.

## 7. Artifact policy + language — PASS

- `git ls-files runs` → empty. No SQLite/Parquet/values/heavy artifacts in the
  diff. Staged set empty (changes intentionally uncommitted for review).
- Handoff and new docstrings are diagnostic/research-only in tone; no
  alpha/profitability/tradability claims. Handoff validation counts are
  truthful (reproduced exactly) and risks are honestly recorded.

## Findings summary

| ID | Severity | Finding |
|---|---|---|
| W1 | medium | Reference OHLCV family (`families/ohlcv/family.py`) still derives RTH/ETH from static `session_label`; fast vwap now diverges from its reference twin on real data for RTH-conditioned features. Spec-scoped residual, honestly recorded; needs a tracked follow-up before reference recomputation/reconciliation of vwap features on real data, and before P28 vwap alpha specs treat reference-engine RTH conditioning as truthful. |
| W2 | low | Fast `_template_trade_date` uses physical `duration(days=1)` vs reference calendar-day addition; divergence only possible Sat 23:00–24:00 CT before a DST shift, when CME is closed. Use `dt.offset_by("1d")` in a follow-up. |
| N1 | info | Labels close-out anchor is 15:00-inclusive (event-ts eligibility) vs feature segment truth [08:30,15:00) bar-start exclusive — different objects, not a contradiction; must be noted in the recorded labels-adoption follow-up. |
| N2 | info | Unreachable final return in reference `_rth_minutes_point`; HALT-labeled row scenario removed from vwap fixture (halt truth covered by unchanged `halt_status_flag` tests). |

## Required repairs (non-blocking follow-ups, not in-phase rework)

1. Track a follow-up phase to repoint `families/ohlcv/family.py`
   session-conditioned reference helpers (rth_flag/eth_flag/opening_range/
   overnight_range/anchored_vwap/session_minute) at
   `data.foundation.sessions.classify_session_timestamp` (W1).
2. Include the 15:00-inclusive close-out anchor note (N1) in the recorded
   labels-adoption follow-up.
3. Optional exactness fix: `dt.offset_by("1d")` for fast trade-date rollover (W2).

## Verdict

**PASS_WITH_WARNINGS** — the repair establishes a single tz-aware session
truth consumed by all three in-scope engines, the new tests assert absolute
timestamp-derived expectations that demonstrably kill all three defect classes
under mutation, forbidden paths are untouched, validation reproduces exactly,
and the handoff is truthful. Warnings are the spec-scoped ohlcv-reference
residual (W1), a latent unreachable trade-date edge (W2), and a boundary note
for the labels-adoption follow-up (N1).
