# Adversarial Review: P090500_PACK_OVERWRITE_GUARD

- Campaign: FUTSUB_KILLSHOT_READINESS_OPS_V1
- Phase: P090500_PACK_OVERWRITE_GUARD (registry-aware write-once guard)
- Branch / commit: `wf1/pack-overwrite-guard` @ `25aa4e3` (one commit ahead of origin/main)
- Reviewer: fresh adversarial Claude review (WF1)
- Date: 2026-06-12
- Verdict: **PASS_WITH_WARNINGS**

## Scope reviewed

Spec `specs/FUTSUB_KILLSHOT_READINESS_OPS_V1/P090500_PACK_OVERWRITE_GUARD-registry-aware-write-once.md`,
handoff, full `git diff origin/main` (9 files, +951/-1), independent write-site
sweep, live read-only pack-audit, three mutation tests, and reproduction of all
handoff validation claims.

## 1. Write-site coverage (independent sweep)

Independent grep for `write_parquet_values|to_parquet|write_parquet(` across
`src/alpha_system/**` finds exactly two feature-side Parquet value-store
writers, and both are guarded:

- `src/alpha_system/features/fast/materializer.py::_write_records` (line ~456)
  — guard before `write_parquet_values`, inside the not-`parquet_is_current`
  branch (a skipped identical write is not a replacement; correct).
- `src/alpha_system/features/engine/materialization.py::_write_records_idempotently`
  (line ~653) — same placement.

All known replacement vectors route through these two functions:

- scaleout fast path: V1 workers -> `PackMaterializer.materialize_pack` ->
  `_write_records` (guarded);
- scaleout reference/per-feature path: `driver.py` imports the engine
  `_write_records_idempotently` (guarded);
- seed/materialize CLI (`alpha feature materialize --execute`): engine or fast
  writer (guarded).

No `shutil`/`os.replace`/rename path swaps a registered Parquet outside these
writers (the only `temp_path.replace(path)` calls are the atomic-write tails
inside the writers themselves). Non-feature Parquet writers
(`data/databento/canonicalize.py`, `data/storage.py`) write canonical data,
not registered feature packs. Label writers (`labels/engine.py:804`,
`labels/fast/materializer.py:1450`) are NOT guarded — disclosed in the handoff
as out of this feature-scoped spec; see W2.

## 2. Guard semantics

`require_registered_feature_pack_superset` (`features/pack_integrity.py`):

- queries live registry REGISTERED rows only
  (`registry.py::read_registered_parquet_features`, SQL filter
  `lifecycle_state = 'REGISTERED'`; `DEPRECATED` rows excluded by
  construction, so deprecate-first works — verified by inspection of
  `FeatureRegistryLifecycleState` + `deprecate_feature`);
- normalized-path equality (`expanduser().resolve().as_posix()`) on both sides;
- refuses unless incoming fver set is a superset; error names path, missing
  fvers, and the remediation "deprecate first or run full-scope config";
- NO override: no `--allow-shrink`-style flag, no env-var bypass
  (grep for allow-shrink/skip-guard/getenv in pack_integrity and the CLI:
  none). The only knob found is the internal
  `register_pack(reconcile_after_register=...)` kwarg — see W3; it affects
  reconciliation placement only, never the pre-write guard.

## 3. Post-write reconciliation

`reconcile_registered_feature_pack_path` re-loads the Parquet rows from disk,
recomputes the content hash (does NOT trust the sidecar manifest), and raises
`PackIntegrityError` (test fails loudly) on any missing REGISTERED fver or
hash mismatch. Enforced after registration at three sites:

- `PackMaterializer.register_pack` (fast pack path, default on);
- `driver.py::_materialize_unit_per_feature` (per-feature reference path);
- `driver.py::_register_v1_worker_output` (serial V1 registration; the
  intermediate one-feature fresh registrations pass
  `reconcile_after_register=False` and the unit-level reconcile runs after all
  refreshes — correct placement, since mid-refresh registry state is
  legitimately mixed-hash).

## 4. pack-audit tool — live read-only run

`alpha scaleout pack-audit` is read-only (registry opened
`file:...?mode=ro`; values loaded, never written; ids/counts only — value-free
output). Run against the LIVE registry
(`--alpha-data-root /home/yuke_zhang/alpha_data/alpha_system`):

### Live pack-audit evidence

Output: `~/logs/alpha_pipeline/pack_audit_live.json` (JSON re-parsed and
re-tallied independently by this review; CLI exited `rc=2`, i.e. non-zero on
detected damage — fail-loud as designed).

- `total_path_count=176`, `clean=81`, `stale-registry=71`, `benign-extra=24`
  (top-level counts match an independent recount of the 176 entries).
- **stale-registry by family** — exactly the three families damaged in the
  incident: `bbo_tradability_top_book` 23, `regime_volatility_compression` 24,
  `session_calendar_maintenance` 24 (23+24+24=71).
- Damage signature matches the subset-overwrite incident: sample stale entry
  has 11 registered fvers vs 1 on disk (10 missing). The 398 missing fvers
  across the 71 paths are also listed under `hash_mismatch` (missing ⊆
  mismatch in this snapshot); `read_error` is empty on all 71 — files exist
  and are readable, they are just fver-shrunk.
- **benign-extra** is entirely `volume_activity` (24 paths) — extra on-disk
  fvers with no registered counterpart, correctly classified as non-damage.

**Race caveat (important):** this audit RACED the live repair operations
(deprecate-first of 168 fvers at 10:32Z, full re-materialization
10:33–10:55Z), so the counts are a **mid-repair snapshot**, not a final
state. They directionally confirm the tool detects all three classification
classes (clean / stale-registry / benign-extra) on real damage in the live
registry, but they must not be read as the post-repair state.

**Post-repair cross-check (separate tool):**
`tools/futures_substrate_scaleout/pack_restore_audit.py` at 10:55Z reports
bbo 264/264 hash-identical, session 120/120, regime 72/72, stale=0 — the
repair completed and the damage classes audited above are now cleared.

## 5. Full-scope behavior unchanged

- Diff adds only one test file (`tests/unit/features/test_pack_overwrite_guard.py`);
  zero existing tests modified.
- `tests/unit/futures_substrate_scaleout tests/unit/features`: **281 passed**
  (matches handoff).
- Superset/full-scope runs take the same code path with one additional
  read-only registry query before a write that was already happening;
  values, hashing, identity, and registration semantics untouched.
- `just ci-parity` (CI venv): **3304 passed, 78 skipped** — reproduced exactly.

## 6. Mutation tests (all killed; tree restored)

| Mutation | Change | Expected | Result |
|---|---|---|---|
| A | superset comparison disabled (`if missing and False`) | subset-refusal test fails | **FAILED as required** (`test_registered_pack_subset_rewrite_is_refused_and_superset_allowed`) |
| B | `reconcile_registered_feature_pack_path` made a no-op (`return` first) | tamper test fails | **FAILED as required** (`test_register_pack_reconciliation_catches_tampered_file`) |
| C | stale-registry classified as clean | classification test fails | **FAILED as required** (`test_pack_audit_reports_stale_registry_benign_extra_and_clean`) |

Each mutation reverted via `git checkout --`; `git status` clean afterward.

## 7. Handoff truthfulness

Every checkable claim reproduced:

- focused guard tests: 3 passed — confirmed;
- 281 passed (scaleout+features) — confirmed;
- canaries: all pass — confirmed;
- `verify.py --smoke` / `--artifacts` / `--boundaries`: exit 0 — confirmed;
- ci-parity 3304 passed / 78 skipped — confirmed;
- `verify.py --all` caveat: both
  `tests/integration/test_duckdb_query_fixture.py` and
  `tests/integration/test_polars_lazy_fixture.py` fail identically here
  (tuple-vs-list assertions in the research venv where optional duckdb/polars
  are importable). The diff touches zero integration tests and zero modules
  those tests import, so the failures are pre-existing on origin/main, and the
  same tests pass in the CI-parity venv run above. Caveat is honest.

## 8. Artifact policy and scope

- `git ls-files runs` empty; no sqlite/db/parquet/arrow/feather/log in the
  commit; explicit-path staging; single scoped commit; no force-push.
- Scope: only the spec'd files changed; research-only language throughout;
  no schema change; no new dependencies.

## Findings

- **W1 (warning, follow-up required): DUAL-mode JSONL twin is overwritten
  before the guard fires.** In both guarded writers the JSONL pack
  (`values.jsonl` = `plan.output_path`, the registry's
  `materialization_output_path`, read by
  `features/reports.py::_load_jsonl_feature_observations`) is written by
  `_write_jsonl_if_changed` BEFORE `require_registered_feature_pack_superset`
  runs in the Parquet branch. A subset run via `alpha feature materialize`
  (CLI default `--value-store dual`, `cli/feature.py:235`) is refused for
  Parquet — the canonical value truth is protected — but the JSONL tier of the
  pack has already been shrunk by the time the run fails. The incident vector
  itself is fully closed (scaleout configs are PARQUET-only by validation,
  `driver.py:564`). Fix is a trivial hoist: evaluate the superset guard at the
  top of `_write_records` / `_write_records_idempotently` before any store is
  written.
- **W2 (warning, follow-up): label pack writers remain unguarded**
  (`labels/fast/materializer.py:1450`, `labels/engine.py:804`). Same
  structural hazard class exists for label packs (lver-grained). Out of this
  feature-scoped spec and disclosed in the handoff, but should get its own
  phase before any label-side force-recompute data-op.
- **W3 (minor): `reconcile_after_register` kwarg** on
  `PackMaterializer.register_pack` is an internal way to skip reconciliation.
  Its single `False` caller reconciles at unit level afterward, and it is not
  CLI-exposed; acceptable, but future callers could silently skip — consider
  making it private or asserting a caller-side reconcile.
- **W4 (minor): no explicit deprecate-then-rewrite test.** The
  deprecated-first path is correct by construction (SQL lifecycle filter) but
  untested; a one-case test would pin it.
- **Observation:** unreadable/missing files are reported as `stale-registry`
  with all registered fvers listed missing + `read_error` populated —
  fail-loud, correct for repair accounting.
- **Observation:** live pack-audit is slow (full row load + hash per path,
  minutes on the live root); acceptable for a repair-proof tool, worth noting
  in ops docs.

## Verdict

**PASS_WITH_WARNINGS.** The incident class (registry-subset Parquet pack
rewrite) is structurally refused at every feature-side Parquet write site with
no override; post-write reconciliation is loud and mutation-proof; pack-audit
correctly classifies the live damage. W1 (DUAL JSONL ordering) and W2 (label
writers) are real residual hazards that need small follow-ups but do not
reopen the incident vector.
