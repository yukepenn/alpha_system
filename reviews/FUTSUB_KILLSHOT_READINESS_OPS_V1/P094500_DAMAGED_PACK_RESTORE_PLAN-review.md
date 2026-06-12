# Adversarial Review: P094500_DAMAGED_PACK_RESTORE_PLAN

- Campaign: `FUTSUB_KILLSHOT_READINESS_OPS_V1`
- Phase: `P094500_DAMAGED_PACK_RESTORE_PLAN` (Yellow, WF1)
- Branch / commit reviewed: `wf1/pack-restore-plan` @ `7d2e5f1`
- Reviewer: fresh adversarial Claude (no executor context)
- Stance: adversarial; every load-bearing claim re-executed against the live
  registry (read-only `file:...?mode=ro`) and via fresh dry-runs (no `--execute`).

## Verdict

**REWORK** — the analysis, provenance table, blocking findings, proof, and
driver fix are all genuine and verified, but the committed tree FAILS the
repo's own CI artifact gate (committed `.csv` files), and the runbook omits
two items the spec/next phase explicitly require (PR #401 supersession note;
deprecate-first step). Bounded repairs listed at the end.

## 1. Provenance completeness — VERIFIED

- `damaged_pack_provenance.csv` = 408 data rows + header (409 lines).
  Family split 240 bbo / 120 session / 48 regime matches the spec's
  10x24 / 5x24 / 2x24 expectation.
- Spot-checked 5 random rows (seed 94500) against the live registry
  read-only: all 5 MATCH on lifecycle_state, value_content_hash,
  partition_id, feature_id, feature_request_id, materialization_plan_id.
- All 408 fvers are still `REGISTERED` in the live registry (408/408).
- Re-ran the committed audit tool fresh: provenance regeneration is
  byte-identical to the committed CSV except the 10 ES_2019 bbo rows that the
  proof legitimately moved from stale to hash_identity (committed CSV is the
  pre-proof baseline, correctly so — it feeds `--baseline-provenance`).
- Fresh summary == committed `damaged_pack_post_bbo_proof_audit.md`
  (bbo 34 identity / 230 stale; regime 72/48; session 120/120).

## 2. Blocking findings — GENUINE, fully reproduced

### 2a. Session union-config rejection (R-036) — reproduced, policy not config error

Fresh dry-run (no `--execute`) of
`configs/features/scaleout/repair/session_calendar_maintenance_union_restore.json`
exits 2 with `session_calendar_maintenance scaleout excludes offline/non-causal
features: bars_to_roll, minutes_to_roll`, failed_count=1, planned_count=0
(fail-closed). Rejection is enforced TWICE in code, so this is policy, not an
executor config misread:

- `src/alpha_system/features/scaleout/driver.py:5487-5494`
  (`_session_definition_builders`): explicit by-name exclusion of
  `bars_to_roll`/`minutes_to_roll`.
- `src/alpha_system/features/scaleout/driver.py:3246-3264`
  (`_require_trusted_scaleout_feature_specs`): rejects any session spec that is
  not live/implementation_eligible/live-window-compatible; the family marks the
  countdowns FUTURE-window `offline_only` with
  `offline_reason: future_roll_transition_countdown`
  (`features/families/session/family.py:339-343, 605-622`).
- This is R-036 ("Roll-countdown features are forward-looking", FUTSUB risk
  register), wired in FUTSUB-P14 (PR #307). The union config including the
  countdowns is CORRECT for a registry-faithful union; the conflict is real.

### 2b. Replacement-fvid previews (identity drift) — reproduced, root cause pinned

Reproduced both previews via fresh dry-runs; previewed fvids match the runbook
exactly and differ from the registered stale fvids:

- Regime ES_2019: preview `base_ohlcv_rolling_range` →
  `fver_8eadbbf…` (registered stale `fver_082cbb…`); `base_ohlcv_returns` →
  `fver_33907b…` (registered stale `fver_01471d…`). The other three regime
  fvids in the preview are bit-identical to registered rows.
- Session ES_2019 (committed 8-name config): `day_of_week` → `fver_fecafaf…`
  (registered `fver_8370819…`); `minutes_to_expiration` and `halt_status_flag`
  likewise drifted; the 5 non-roll features preview EXACTLY the registered
  fvids (those are the 5 hash_identity rows).

**What drifted (identity inputs, proven by in-process contract diff):**
`feature_version_id = fver_<sha256(FeatureSpec.to_identity_dict())>`
(`features/contracts.py:436-456`, request-provenance excluded). Diffing the
registered stale contract (registry `metadata_json.feature_spec`) against the
contract the current code builds:

- `day_of_week`: `transform.parameters` REMOVED `rth_open_time_utc: "14:30"`,
  `rth_close_time_utc: "21:00"`; ADDED `rth_open_time_local: "08:30"`,
  `rth_close_time_local: "15:00"`, `session_template_id:
  "session_cme_index_futures_eth"`, `session_timezone: "America/Chicago"`.
- regime `base_ohlcv_rolling_range` (input-copy spec for `range_expansion`):
  `transform.parameters` ADDED the same four session-template fields plus
  `session_truth_source: "alpha_system.data.foundation.sessions"`.

So the drift is the session-truth/DST identity migration — commit `6018f1a`
(FUTSUB P210000 "session truth joins the feature identity contract", PR #370,
with repoints in PR #376) — NOT template-version or config-hash drift, and NOT
anything this phase did. Bit-identical restore of these slots is impossible by
design; the executor's "cannot restore through current CLI" claims are true.

## 3. ES_2019 bbo proof — VERIFIED, one runbook gap

- Proof CSV (17 rows: 10 bbo + 5 session + 2 regime) checked against the live
  registry: all 10 bbo fvers disk-present under the SAME fver ids, baseline
  hash identity 0/10 (old `sha256:da3ae4…`), current registry↔disk hash
  identity 10/10 (new `sha256:fd92da…`). Session 5 and regime 2 honestly
  reported untouched/stale.
- Sanctioned CLI evidence: checkpoint marker
  `materialization/.../checkpoints/features/pack_restore/bbo_tradability_top_book/units/mbu_cff63bcd382b1b68cd745ce3.json`
  exists under the data root (unit id matches the regression test's golden id);
  registry rows updated in place with `registered_at` preserved — consistent
  with the registry upsert path, not manual SQLite.
- Blast radius confirmed: fresh audit-tool run differs from the committed
  pre-audit ONLY in the 10 ES_2019 bbo rows; pack mtimes show ES_2019 bbo
  values.parquet + manifest written 2026-06-12 ~09:34Z while sibling
  partitions/families retain older mtimes. Only ES_2019 bbo was touched.
- **GAP (required repair 2):** the proof ran BEFORE the bbo bar-grid fix
  (P085901, PR #401, merged 2026-06-12T09:54Z — ~20 minutes AFTER the proof
  write). The runbook's bbo section mentions new-content + `sspec_6088f0`
  re-lock but never states that the full bbo re-materialization must run AFTER
  the grid fix merges and that it SUPERSEDES the proof content — the proof's
  ES_2019 pack itself embeds the pre-fix grid and will be rewritten. The spec's
  scope item 4 explicitly required this bbo note.

## 4. Driver fix — minimal, regression-tested, mutation-killed

- Fix is narrowly scoped: new `materialize_v1_feature_unit_force_recompute`
  helper + `force_recompute` plumbed into `_compute_v1_feature_unit_output` +
  a guarded dispatch in `_execute_stage` only when `force_recompute and
  engine == v1 and executor is materialize_v1_feature_unit`. No behavior change
  for any other path.
- MUTATION TEST: reverted `driver.py` to `origin/main`, ran the test file →
  `test_serial_v1_force_recompute_uses_force_helper` FAILED (1 failed,
  2 passed); restored `7d2e5f1` exactly (clean diff). The new test kills the
  mutant.
- Caveat (warning): the test monkeypatches the force helper, so it proves
  serial-path ROUTING, not the helper's recompute semantics; the live ES_2019
  proof (which required the fix to recompute a single unit) is the
  end-to-end evidence.

## 5. Runbook executability — two omissions (one blocking for the next phase)

- Full-grid commands: complete and correct for all three families (full
  24-partition grids, union configs, `--force-recompute`, verification via the
  committed audit tool with `--baseline-provenance`), session/regime correctly
  marked DO-NOT-RUN with the reproduced blockers, bbo duration estimate traced
  to the measured 97.64s proof.
- **GAP (required repair 3):** the runbook is SILENT on deprecate-first: the
  P090500 overwrite guard (not yet in this base, expected to land) will refuse
  pack rewrites while unrestorable fvers (the 2 session countdowns rejected
  under R-036 and the 3+2 identity-drifted session/regime slots) remain
  `REGISTERED`. The next phase needs the explicit deprecation/re-lock step
  ordered BEFORE the session/regime full grids.

## 6. Artifact policy and handoff truthfulness

- Commit `7d2e5f1` stages exactly 14 explicit paths; `git ls-files runs` is
  empty; no parquet/sqlite/values committed; both CSVs are value-free
  (ids/hashes/counts/paths/commands only); configs under
  `configs/features/scaleout/repair/` are source — fine.
- Validation re-run by reviewer: scaleout unit tests `133 passed` (matches
  handoff); canaries PASS; `verify.py --smoke` PASS (exit 0).
- **BLOCKING (required repair 1):** `just ci-parity` on the COMMITTED tree
  FAILS: `tests/integration/test_no_generated_data_committed.py::
  test_no_generated_data_or_heavy_artifacts_are_tracked` forbids tracked
  `.csv` outside `tests/fixtures/`, and this phase committed
  `research/futures_substrate_scaleout_v1/repair/ES_2019_proof_results.csv`
  and `damaged_pack_provenance.csv` → `1 failed, 3304 passed, 75 skipped`.
  The handoff's "PASS, 3305 passed, 75 skipped" can only have been produced
  before the CSVs were staged/tracked; as committed, the PR will be CI-red.
  The handoff validation table is therefore stale for the final tree (the
  rest of the handoff is accurate and honestly framed as
  "partial completion with blocking findings").

## Required repairs (bounded)

1. Make the committed tree pass its own artifact gate: replace the two tracked
   CSVs with value-free Markdown tables (or relocate CSVs to a local-only
   path and commit `.md` renderings), update the runbook/audit-tool
   `--baseline-provenance` flow accordingly (the tool can keep writing local
   CSVs; they just must not be tracked), and re-run `just ci-parity` to green
   on the committed tree.
2. Add the bbo ordering note to the runbook: full bbo re-materialization runs
   AFTER the P085901 grid fix (PR #401, now merged) is in the executing
   branch; it supersedes the ES_2019 proof content (proof predates the fix);
   `sspec_6088f0` re-lock happens after that re-run.
3. Add the deprecate-first step to the runbook: before session/regime full
   grids (and before the P090500 guard lands), the unrestorable stale fvers
   (2 session countdowns under R-036; 3 session + 2 regime identity-drifted
   slots) must be explicitly deprecated/re-locked, with the decision routed to
   the follow-up phase the handoff already names.

## Warnings (non-blocking)

- The regression test proves routing only (helper monkeypatched); acceptable
  given the live proof, but a small integration test of
  `materialize_v1_feature_unit_force_recompute` against a tmp registry would
  close the gap.
- The audit tool selects families via `parquet_path LIKE '%/<family>/%'`;
  robust for these namespaces but would over-match if a family name ever
  becomes a substring of another path segment.
- Registry re-registration preserves `registered_at` while replacing
  `value_content_hash`; future audits should not use `registered_at` to date
  pack content.

## Post-repair re-verdict

- Re-verdict date: 2026-06-12 (reviewer: fresh post-repair Claude pass)
- Repair commit re-reviewed: `2a4bec5` ("FUTSUB P094500 bounded repair runbook artifacts") on `wf1/pack-restore-plan`
- Verdict history: **REWORK -> PASS_WITH_WARNINGS**

All three required repairs are verified resolved on the committed tree:

1. **Tracked CSVs removed — RESOLVED.** `git ls-files '*.csv'` returns only
   `tests/fixtures/data/synthetic_1min_bars.csv` and
   `tests/fixtures/data/synthetic_ibkr_raw_bars.csv`. The two repair CSVs were
   replaced by value-free Markdown tables with IDENTICAL content: a cell-by-cell
   programmatic diff of `damaged_pack_provenance.md` (408 data rows, same 22
   columns) and `ES_2019_proof_results.md` (17 data rows, same 14 columns)
   against the deleted CSVs at `HEAD~2` shows headers equal and ZERO mismatched
   rows. All references updated: the only remaining `.csv` mention in the
   runbook/handoff/repair docs is the handoff's truthful statement that no
   repair `.csv` artifacts are tracked. `pack_restore_audit.py` now dispatches
   on file suffix (`_read_rows`/`_write_rows` -> `_read_markdown_table`/
   `_write_markdown_table`, with `|`/`\`/newline escaping), so
   `--baseline-provenance` consumes the committed `.md` baseline and CSV remains
   a local-scratch option only; the runbook's verification commands now pass
   `.md` paths throughout.
2. **bbo ordering/supersession note — RESOLVED.** The runbook's "Required
   Execution Order" step 2 reads: "Run full BBO re-materialization only after
   the executing branch contains the P085901 bar-grid fix from PR #401, which
   is now merged on `origin/main`." and continues: "The BBO ES_2019 proof in
   this phase was written before PR #401. It is proof of the sanctioned CLI
   path and blast radius only; it is superseded by the full BBO
   re-materialization after the grid fix. The post-PR-401 BBO run is the
   content that must feed the `sspec_6088f0` re-lock." The bbo full-grid
   section repeats the ordering with both content hashes.
3. **Deprecate-first step — RESOLVED.** New "Deprecate-First Step" section is
   ordered before the session/regime full grids (execution-order step 1),
   forbids manual SQLite, cites the sanctioned P235500 data-op mechanism
   (`FeatureStore.deprecate_feature` -> `FeatureRegistry.deprecate_feature`,
   `feature_deprecation_records` row + lifecycle transition), and gives
   complete command templates (registry backup, write step, registry-API
   verification). Reviewer verified the cited API against the repo WITHOUT
   executing against the live registry: `FeatureStore.deprecate_feature`
   (`src/alpha_system/features/store.py:260`) and
   `FeatureRegistry.deprecate_feature` (`src/alpha_system/features/registry.py:646`)
   exist and accept exactly the kwargs the runbook uses (`reason`,
   `deprecated_by`, `replacement_feature_version_id` defaulting `""`,
   `deprecation_metadata`); `FeatureStore(FeatureRegistry(path))`,
   `resolve_feature(fver, include_deprecated=True)`, `resolve_deprecation`,
   `FeatureRegistryLifecycleState.DEPRECATED`, and
   `deprecation.replacement_feature_version_id` all exist with the cited
   semantics, and the registry path writes the `feature_deprecation_records`
   row as described. The "deprecate exactly 168 rows" target was re-derived
   from the committed provenance table: 48 R-036 countdown rows + 72 session
   identity-migration rows + 48 regime identity-migration rows = 168 (matches).

Gates re-run by reviewer on the repaired tree (`PYTHONPATH=$PWD/src`):

| Gate | Result |
| --- | --- |
| `just ci-parity` (CI venv `~/.venvs/alpha_system_ci`) | **PASS** — `3305 passed, 75 skipped in 73.98s`, exit 0 (previously 1 failed) |
| `tests/integration/test_no_generated_data_committed.py` (focused, CI venv) | PASS — `1 passed` |
| `python tools/hooks/canary_runner.py` | PASS — all Frontier canaries passed |

The handoff was truthfully updated: the stale pre-repair `ci-parity PASS`
claim is explicitly marked as superseded, and a Bounded Repair Update section
documents the conversion, tool change, and repair validation.

Carried-forward warnings (non-blocking, unchanged from the original review):

- Regression test proves serial-path routing only (force helper
  monkeypatched); the live ES_2019 proof remains the end-to-end evidence.
- Audit tool family selection via `parquet_path LIKE '%/<family>/%'` is
  namespace-fragile if a family name ever nests inside another path segment.
- Registry re-registration preserves `registered_at` while replacing
  `value_content_hash`; do not date pack content by `registered_at`.
- New minor observation: the deprecation write step depends on an
  operator-prepared `/tmp/p094500_deprecate_first_pairs.json` mapping; the
  runbook correctly requires it to be reviewed, but the 168 concrete fver ids
  must be extracted from the committed provenance table at execution time
  (the runbook gives the selection criteria, not the expanded list).

**Final verdict: PASS_WITH_WARNINGS.**
