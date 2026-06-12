# Adversarial Review — P113000_RESTORE_EXEC_CONFIGS

- Campaign: FUTSUB_KILLSHOT_READINESS_OPS_V1
- Phase: P113000_RESTORE_EXEC_CONFIGS
- Branch / commit reviewed: `wf1/restore-exec-configs` @ `bef0fbb` (one ahead of `origin/main` @ `0c2fce4`)
- Reviewer: fresh adversarial Claude reviewer (no prior context from execution)
- Date: 2026-06-12
- Verdict: **PASS_WITH_WARNINGS**

## Scope Reviewed

`git diff origin/main`: 6 files — two new v2 restore configs, the phase handoff,
`research/futures_substrate_scaleout_v1/repair/PACK_RESTORE_RUNBOOK.md` updates,
the force-recompute mixed-context fix in
`src/alpha_system/features/scaleout/driver.py`, and one new regression test in
`tests/unit/futures_substrate_scaleout/scaleout/test_bbo_tradability_scaleout_driver.py`.
No `--execute` was run by the phase; this review also ran no `--execute`.

## 1. Root-Cause Quality — CONFIRMED INDEPENDENTLY

The handoff's mechanism is correct and the v2 configs pass the gate for exactly
the stated reason, not an incidental one.

Verified against current code:

- Gate entry: `evaluate_feature_request_gate` at
  `src/alpha_system/features/request_gate.py:168`; duplicate check invoked at
  `:194` (`check_duplicate_exposure`); blocking rejection message
  ("duplicate-exposure guard found a blocking exposure") in the reject block at
  `:225-:234` (handoff cites `:223` — same block, off by a few lines, cosmetic).
- Request signature `_request_signature` at
  `src/alpha_system/governance/duplicate_exposure.py:281` builds exposure
  identity from `formula_sketch.exposure_family|exposure|family|factor_id|name`
  plus inputs/operation/window/tokens, exactly as described. Entry signature at
  `:313`; blocking rule at `:361` (`_duplicate_finding`: exact exposure-family /
  identity match, or request inputs naming an existing factor); same
  operation/window/input overlap is only a WARNING at `:387`
  (`_equivalent_finding`).
- The guard sees only `REGISTERED` rows: `read_factor_versions` at
  `src/alpha_system/features/registry.py:747` filters
  `lifecycle_state = 'REGISTERED'`; adapter `_duplicate_exposure_registry_entry`
  at `:1317`.
- Scaleout requests put per-unit exposure family
  (`{family}_{partition_id}_{name}`) in both `requested_inputs` and
  `formula_sketch`: session `:5577`, regime `:5880`, BBO `:6464` in
  `driver.py` (all verified).
- Old failure path verified: `_existing_v1_feature_context_for_force_recompute`
  previously returned `None` if ANY preview fvid was unresolved; the caller then
  rebuilt the WHOLE family via `_feature_definitions_for_unit(config, unit,
  store.registry)`, gate-checking every feature against the live registry. The
  still-`REGISTERED` unchanged rows self-match their own exposure families →
  blocking duplicate → the coordinator's observed failure on every unit.

Independent confirmation of the mixed-set premise against the live registry
(read-only, `mode=ro`): the v2 session preview is 120 fvids currently
`REGISTERED` + 72 missing; regime is 72 `REGISTERED` + 48 missing. Exactly the
mix the old helper bailed on. The fix reuses stored, previously gate-checked
request payloads for the registered fvids (never re-entering the gate, which
would self-match) and rebuilds only missing fvids against the live registry,
where the deprecated rows are invisible to the guard — so the fresh
replacement requests pass. Both halves verified empirically (section 3).

Important confirmation: the v2 configs are NOT the fix. Config diff v1→v2 is
only `phase_id`, `dry_run_preview_ref`, the session countdown removal (10→8
names), and a `targeting.feature_groups` block; the collision is resolved by
the driver change. The handoff says this plainly. The `targeting` block is
parsed and validated against `governed_scope` (`driver.py:556`, `:590`,
`_group_mapping` with `allowed_names`) but does not alter full-window
selection — it enables later targeted runs only (consumed at `:7378-:7386`).
`phase_id` does not enter feature_version_id identity (proven by the 0-mismatch
pointer check below: pointers written under P094500 previews equal P113000
previews).

## 2. V2 Config Safety — VERIFIED (read-only against live registry)

Live registry (`/home/yuke_zhang/alpha_data/alpha_system/registry/features.sqlite`, `mode=ro`):

- Session pack (`features/materialized/futures_substrate_scaleout_v1/session_calendar_maintenance`),
  currently `REGISTERED`: 5 names × 24 partitions (`session_id`,
  `minutes_from_rth_open`, `minutes_to_rth_close`, `rth_segment_flag`,
  `eth_segment_flag`). v2 governed_scope = those 5 + the 3 deprecated-with-
  replacement names (`day_of_week`, `minutes_to_expiration`,
  `halt_status_flag`) = 8. **Superset of REGISTERED — no subset hazard.**
  Countdowns (`bars_to_roll`, `minutes_to_roll`) excluded per R-036; their 48
  deprecation rows have empty replacement pointers (verified).
- Regime pack, currently `REGISTERED`: `base_ohlcv_trendiness`,
  `base_ohlcv_atr`, `liquidity_structure_range_contraction` (3 names × 24).
  v2 governed_scope (5 names) maps onto those 3 plus the two deprecated
  pack-local input copies: `range_expansion` → primitive `ohlcv.rolling_range`
  (`driver.py:5981`) and `momentum_reversion_state` → primitive `ohlcv.returns`
  (`driver.py:5988`) — bindings verified in code. **Superset — no subset
  hazard; the pack does not shrink.**
- Value namespaces and pack paths in both v2 configs are byte-identical to the
  committed v1 repair configs and match the live
  `materialization_output_path` namespaces. No new value locations. Checkpoint
  roots unchanged from v1 (`.../checkpoints/features/pack_restore/<family>`).
- Session offline-feature guard (`_require_trusted_scaleout_feature_specs`)
  runs on BOTH the reuse path and the rebuild path (`driver.py:3229`), so
  countdowns cannot re-enter via reused specs.

## 3. Replacement Pointers — REPRODUCED, 0 MISMATCHES

Re-ran both dry-runs myself (no `--execute`, exact handoff commands):

- Session: `dry_run=true`, 24/24 accepted/planned, 0 failed, 8 features/unit.
- Regime: `dry_run=true`, 24/24 accepted/planned, 0 failed, 5 features/unit.

Read-only deprecation cross-check: 168 rows with reason
`P094500 damaged-pack restore deprecate-first...`,
`deprecated_by=coordinator/P094500_deprecate_first` (note: the operator tag
lives in `metadata_json.deprecated_by`, not the `reason` column). Breakdown
matches the handoff exactly: session 72 with-replacement (3 names × 24) + 48
no-replacement R-036 countdowns; regime 48 with-replacement (2 names × 24).
Every non-empty `replacement_feature_version_id` appears in the v2 dry-run
preview for the SAME family and partition: **0 mismatches across 120
pointers.** None of the 120 replacement fvids is registered yet (all genuinely
missing, to be created by the restore).

I also reproduced the read-only force-recompute prepare probe against the live
registry: session `prepared_units=24`, feature count 8, reused_existing=120,
fresh_built=72; regime `prepared_units=24`, feature count 5, reused_existing=72,
fresh_built=48. All 120 fresh declarations passed the live duplicate gate (the
deprecated rows are no longer visible to it), and full
`_prepare_v1_worker_job(..., force_recompute=True)` succeeded for all 48 units
with no writes. This is the direct empirical proof of the stated root cause and
fix mechanism.

## 4. Driver Fix — MINIMAL, MUTATION-TESTED

The fix is confined to `_existing_v1_feature_context_for_force_recompute` (+
threading `alpha_data_root` from `_prepare_v1_worker_job`). It reuses the
pre-existing `_fresh_v1_declaration_for_version` (already used by targeted
repair at `driver.py:2979`) rather than inventing a second build path. The
per-unit duplicate-feature-id fail-close (`duplicate V1 feature selection`)
is retained, and a new fail-close was added for a fresh rebuild returning no
request payload.

Mutations performed (both restored exactly; `git status` clean, worktree diff
vs `bef0fbb` empty):

- **M1 (full revert)**: `git checkout origin/main -- src/alpha_system/features/scaleout/driver.py`
  → `test_force_recompute_context_allows_mixed_existing_and_missing_fvids`
  **FAILED** (old signature). KILLED.
- **M2 (surgical behavior revert)**: kept the new signature, re-inserted
  `if existing is None: return None` → new test **FAILED** (context collapses
  to `None`), other 3 tests in the file pass. KILLED — the test catches the
  behavior, not just the signature change.

## 5. Transitional Red Honesty — VERIFIED, NOT A DIFF REGRESSION

- Reproduced locally on this branch:
  `tests/unit/futures_substrate_scaleout` → 1 failed, 133 passed (matches
  handoff). The single failure is
  `test_committed_locks_resolve_against_live_registry_and_feature_validator`
  raising `RuntimeInputResolverError: feature_pack lifecycle_state must be
  REGISTERED for runtime resolution` — exactly the deprecated-fvid class
  (committed sspecs lock fvids that the P094500 deprecate-first data operation
  deprecated; expected until RELOCK_V2).
- Ran the same test in a scratch worktree at `origin/main` (`0c2fce4`):
  **identical failure.** The red is data-state-driven, pre-existing, and not
  introduced by this diff (the diff touches only scaleout driver
  force-recompute prep, configs, runbook, handoff, and a scaleout test — none
  consumed by the relock resolver path).
- `just ci-parity` reproduced: **1 failed, 3312 passed, 77 skipped** — same
  single relock failure (matches handoff).
- GitHub CI skip mechanism confirmed: the failing test calls
  `skip_unless_local_registry` (`tests/_helpers/local_data.py`) on
  `<data_root>/registry/features.sqlite`; CI runners have no local registry, so
  the test skips with the sanctioned `LOCAL DATA SKIP` reason. Note the branch
  is unpushed, so no GitHub CI run exists yet for `bef0fbb`; the skip guard is
  the mechanism that will keep CI green.

## 6. Runbook — VERIFIED

Both family sections now carry: write-free validation command + coordinator
`--execute` command pointing at the v2 configs; deprecation evidence cited
(`coordinator/P094500_deprecate_first`, 2026-06-12T10:32Z, 72/48/48 counts —
all reproduced against the registry); the old Blocked text preserved verbatim
under "Superseded P094500 blocker history" with the old fver pairs; explicit
note that the old v1 config commands are superseded.

## 7. Artifact Policy + Truthfulness — VERIFIED

- Commit `bef0fbb` contains exactly the 6 in-scope files; no `runs/` paths
  (`git ls-files runs` empty), no data/DB/parquet/log artifacts.
- `tools/hooks/canary_runner.py`: all canaries pass. `tools/verify.py --smoke`:
  exit 0. New regression test file: 4 passed.
- Every quantitative claim in the handoff that I reproduced matched: dry-run
  24/24+24/24 with 8/5 features per unit, prepare probe 24/24 both families,
  pointer mismatches 0, unit suite 1f/133p, ci-parity 1f/3312p/77s, first
  failing class = deprecated regime fvid. No overclaim found; the handoff
  states honestly that no `--execute` was run.

## Findings

- **MAJOR**: none.
- **MINOR-1**: No committed spec file for P113000 under
  `specs/FUTSUB_KILLSHOT_READINESS_OPS_V1/` (prior phases each have one); the
  prompt-spec exists only in the handoff context. Confirmed true.
- **MINOR-2**: The superseded v1 union-restore configs remain committed beside
  the v2 configs; nothing mechanical prevents executing the stale v1 commands.
  Mitigated by the runbook's explicit supersession and the handoff's review
  focus; consider deleting or marking the v1 configs in RELOCK_V2 cleanup.
- **MINOR-3**: Handoff cites `request_gate.py:223` for the coordinator error
  string; the message literal is at `:230-:232` (same reject block). Cosmetic.
- **NOTE-1**: The reuse path intentionally bypasses the duplicate gate using
  stored checked payloads. Acceptable: payloads were gate-checked at original
  registration, the trusted-spec guard still runs on the reuse path, and the
  per-unit duplicate-id fail-close is retained.
- **NOTE-2**: `targeting.feature_groups` does not affect the full-window
  restore run (validated-but-informational for these commands); it exists to
  enable later targeted runs.
- **NOTE-3**: GitHub CI for this branch has not run yet (unpushed); local
  ci-parity red is the sanctioned transitional class only.

## Verdict

**PASS_WITH_WARNINGS** — root cause independently confirmed in code and
empirically against the live registry; v2 scopes are supersets of the
REGISTERED sets with identical value namespaces; 0 pointer mismatches
reproduced; driver fix minimal with the regression test killing both full and
surgical mutations; the only red is the pre-existing deprecated-fvid
transitional class, identical on `origin/main`.
