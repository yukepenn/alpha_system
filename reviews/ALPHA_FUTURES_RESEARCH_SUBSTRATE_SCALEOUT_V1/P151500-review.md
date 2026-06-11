# P151500_FUTSUB_P22_LIFECYCLE_ENFORCEMENT — Adversarial Yellow Review

- Campaign: ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1
- Phase: P151500_FUTSUB_P22_LIFECYCLE_ENFORCEMENT (deprecated lock fail-closed)
- Reviewed: uncommitted working-tree diff in worktree
  `/home/yuke_zhang/projects/alpha_system_wt/p22-lifecycle`
  (branch `repair/p22-lifecycle-enforcement`, base `origin/main` @ 6f405bc)
- Reviewer: fresh adversarial Claude (Yellow lane), 2026-06-11
- Spec: `specs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/P151500_FUTSUB_P22_LIFECYCLE_ENFORCEMENT-deprecated-lock-fail-closed.md`

## Verdict: REWORK

The core enforcement is real, correctly placed, mutation-verified, and honest
— but the diff breaks 3 unmodified tests (2 no-lookahead guard tests + the
runtime integration smoke) that pass at base, because READY_FOR_STUDY fixtures
outside the executor's edit set now hit the new lifecycle gate. CI runs the
full `python -m pytest` suite (`.github/workflows/frontier-ci.yml:31-34`), so
this diff is CI-red as written. The phase cannot merge until the collateral
fixtures and the READY_FOR_STUDY doc contradiction are resolved.

---

## 1. READY_FOR_STUDY admissibility (special scrutiny #1)

Determination: **READY_FOR_STUDY is a designed-but-never-wired pack-level
state. REGISTERED-only enforcement rejects no real row today, so this is not a
BLOCKING wrong-rejection — but it inverts the documented design and the change
ships in a half-converted state (REWORK finding F2/F3 below).**

Evidence:

- Enum membership: `LabelRegistryLifecycleState` includes `READY_FOR_STUDY`
  (`src/alpha_system/labels/registry.py:64-69`). The feature enum does NOT —
  `FeatureRegistryLifecycleState` is `{REGISTERED, DEPRECATED}` only
  (`src/alpha_system/features/registry.py:68-72`). So feature-side
  REGISTERED-only enforcement exactly matches the feature enum.
- It is pack-level, not StudySpec-level: it lives on the label registry record
  (`LabelRegistryRecord.lifecycle_state`, `labels/registry.py:158-160`), and
  the docs describe it as a registry/substrate-object state.
- NO production writer exists. Registration defaults to `REGISTERED`
  (`labels/registry.py:158-160`); `register_label_materialization` passes the
  default or the pre-existing state (`labels/registry.py:460`); the only
  lifecycle transition in the codebase is `deprecate_label` → `DEPRECATED`
  (`labels/registry.py:686`). `grep -rn READY_FOR_STUDY src/ tools/ cli/`
  finds only the enum line `labels/registry.py:68`. There is no promotion or
  transition API anywhere.
- Canonical registries (coordinator ground truth, verified read-only
  2026-06-11): labels = {REGISTERED: 2324, DEPRECATED: 49}, features =
  {REGISTERED: 1408}. Zero READY_FOR_STUDY rows.
- BUT the documented design says the opposite of the new rule:
  `docs/feature_label_foundation/LABEL_STORE.md:78-83` ("`READY_FOR_STUDY`
  means a governed future `StudySpec` consumer may reference the registered
  label version"), `guide/safety_semantics.md:120` ("Only `READY_FOR_STUDY` is
  the terminal study-consumable state"), `guide/request_to_study.md:85`,
  `README.md:150`. Strictly read, the docs designate READY_FOR_STUDY — not
  REGISTERED — as the study-consumable state. Operational reality (every real
  row that has ever resolved at runtime is REGISTERED) and the spec mandate
  ("any non-REGISTERED record must produce a CLOSED failure") both went the
  other way.
- Mitigating: if a promotion path is ever built, a READY_FOR_STUDY pack fails
  CLOSED with a reasoned `label_pack_not_registered` (expected=REGISTERED,
  actual=READY_FOR_STUDY) — loud, not silent. Nothing is wrongly resolved.

Conclusion: not blocking on wrong-rejection grounds (no writer, no rows,
closed reasoned failure), but the doc/code contradiction plus the fixture
breakage below requires rework before merge (see F2/F3).

## 2. Fixture honesty + mutation tests (special scrutiny #2) — PASS

The new test file `tests/unit/labels/test_registry_lifecycle_resolution.py`
drives a REAL `LabelRegistry` on temp SQLite (line 40), deprecates via the
production `deprecate_label` API (lines 45-50, 73-78), and routes through the
production `resolve_runtime_input_pack` + `FeatureLabelPackResolver` with the
real registry as `label_registry` (lines 143-146). The only stub is the
feature-side store (lines 183-188), which contains NO lifecycle filtering —
it is a plain dict lookup. No fixture-side deprecation filtering anywhere.
(Minor: it persists synthetic records via private `registry._persist_label`
— acceptable for a synthetic fixture, noted only.)

Mutation results (performed by reviewer, restored exactly — md5 of
`input_resolver.py` matches pre-mutation backup; registry restores verified by
re-running the 28-test target set green):

- Mutation A — neutered `_require_registered_pack_lifecycle` in
  `src/alpha_system/runtime/input_resolver.py` (early `return` before the
  state comparison): `test_runtime_resolver_fails_closed_for_deprecated_label_with_replacement`
  FAILED and the feature-side
  `test_deprecated_feature_pack_blocks_with_replacement_pointer`
  (tests/unit/runtime/test_input_resolver.py) FAILED. 2 failed, 2 passed.
- Mutation B — neutered the registry-level REGISTERED filter in BOTH
  `labels/registry.py` and `features/registry.py` (`include_deprecated=False`
  branch removed):
  `test_label_registry_keeps_raw_audit_access_and_registered_active_resolution`
  FAILED and `tests/unit/features/test_feature_store.py::test_deprecation_preserves_lineage_and_excludes_prohibited_states`
  FAILED. 2 failed, 2 passed.

The production checks are demonstrably what produce the failures, on both the
label and feature sides, at both the resolver and registry layers.

## 3. Assertion weakening (special scrutiny #3) — PASS

- `tests/unit/features/test_feature_store.py` (+2/-0): two NEW assertions
  added (lines 493-494: active/registered resolution returns None after
  deprecation). Nothing deleted or relaxed.
- `tests/unit/runtime/fail_closed/test_runtime_fail_closed.py` (+2/-2): only
  two fixture `lifecycle_state` literals flipped READY_FOR_STUDY→REGISTERED
  (lines 547, 620). No assertion touched. Justified by the new admissibility
  rule — these fixtures flow through the production resolver and must be
  runtime-admissible for the other fail-closed cases to exercise their
  intended gates.
- `tests/unit/runtime/test_input_resolver.py` (+30/-2): adds the new
  feature-side deprecated test; adds `replacement_feature_version_id` field to
  the `_FeatureRecord` stub; flips one `_LabelRecord` fixture default. No
  assertion deleted/relaxed.
- `src/alpha_system/runtime/dry_run.py` (+2/-2): READY_FOR_STUDY→REGISTERED in
  the synthetic dry-run harness's `_LabelRecord` default (line 953) and the
  value-free audit-report literal (line 1084). dry_run.py is the synthetic
  runtime smoke harness (fabricated `_LabelRecord`/`_FeatureStore` records,
  lines 930-960); the change keeps its synthetic record admissible under the
  new gate. Read-path only; no value/accounting math.

## 4. Forbidden paths (special scrutiny #4) — PASS

Diff touches exactly 8 tracked files + 3 untracked. NONE of
`labels/engine.py`, `labels/families/**`, `labels/fast/**`,
`labels/roll_guard.py`, `labels/version.py` are touched. The
`labels/registry.py` and `features/registry.py` diffs are read-path only:
every changed/added line is in `resolve_*` methods (`include_deprecated`
keyword + three new resolver entry points); no INSERT/UPDATE/CREATE/ALTER, no
`_persist_*`, no `deprecate_*`, no schema change in the diff (verified by
grep over the diff). No value/accounting math anywhere.

## 5. Audit access preserved (special scrutiny #5) — PASS

- `resolve_label` / `resolve_label_by_version` default
  `include_deprecated=True` → raw by-id reads still return DEPRECATED rows
  (proven by the new test, line 52-57 and 87).
- `deprecate_label`'s own read uses raw `self.resolve_label(...)`
  (`labels/registry.py:746` via `is_deprecated`, and the idempotency read at
  `labels/registry.py:434` uses the raw default) — the deprecation flow that
  recently deprecated the 48+1 rows is unaffected.
- The scaleout driver's registry reads
  (`src/alpha_system/features/scaleout/driver.py:1512,1830,4181,4227,7136`)
  call `registry.resolve_label(id)` with the raw default — checkpoint/resume
  behavior unchanged.

## 6. Error semantics (special scrutiny #6) — PASS

- DEPRECATED → `label_pack_deprecated` / `feature_pack_deprecated`,
  `INPUTS_BLOCKED`, with `replacement_label_version_id=` /
  `replacement_feature_version_id=` surfaced in `actual` (from the record
  field first, falling back to the registry deprecation record —
  `input_resolver.py` `_label_replacement_id` / `_feature_replacement_id`).
  Proven against the real registry deprecation metadata path.
- Other non-REGISTERED → `*_pack_not_registered` closed failure.
- Missing `lifecycle_state` → `*_pack_lifecycle_state_missing` (this REPLACES
  the old silent `getattr(record, "lifecycle_state", "REGISTERED")` default in
  `_feature_handle_from_record` / `_label_handle_from_record` — a genuine
  fail-closed strengthening).
- Unknown id → `label_pack_not_found` / `feature_pack_not_found` raise BEFORE
  the lifecycle gate; untouched by the diff.
- No silent fallback: `_resolve_label_record` / `_resolve_feature_record` try
  the active resolver first and fall back to raw ONLY so the gate
  (`_require_registered_pack_lifecycle`, called at the only two consumer sites
  `input_resolver.py:458→470` and `532→544`) can emit the reasoned deprecated
  failure instead of a misleading not_found. A deprecated record can reach the
  gate but never a handle: the gate precedes `_feature_handle_from_record` /
  `_label_handle_from_record`. Minor note: `_pack_lifecycle_state` normalizes
  via `.strip().upper()`, so lowercase "registered" is admissible —
  acceptable normalization, recorded for completeness.

## 7. Validation truth (special scrutiny #7) — handoff claims REPRODUCED, but the validation set was insufficient

Reviewer re-ran everything in the worktree:

| Command | Result | Handoff claim |
|---|---|---|
| pytest new lifecycle file + test_input_resolver + test_feature_store + fail_closed | 28 passed | consistent (3+8+6 reported individually) |
| pytest tests/unit -k "registry or resolver" -q | **74 passed, 2520 deselected** | 74 passed — MATCH |
| pytest tests/unit/futures_substrate_scaleout/labels -q | 37 passed | 37 passed — MATCH |
| python tools/verify.py --smoke | exit 0 | PASS — MATCH |
| python tools/hooks/canary_runner.py | all canaries passed | PASS — MATCH |
| pytest tests/unit -q (FULL, reviewer-added) | 1 failed, 2592 passed, 1 skipped — the failure (`tests/unit/data/test_databento_canonicalize.py`) also fails at base with the diff stashed → PRE-EXISTING env issue, not this diff | not run by executor |
| pytest tests/no_lookahead tests/integration -q (reviewer-added) | **5 failed**, 235 passed | not run by executor |

Stash-baseline triage of the 5: `test_duckdb_query_fixture` and
`test_polars_lazy_fixture` fail at base too (pre-existing local env/library,
the known CI-green-local-red pattern). The other 3 PASS at base and FAIL only
with this diff:

1. `tests/no_lookahead/research_runtime/test_input_resolver_available_ts.py::test_label_available_ts_must_not_precede_label_event_ts`
   — expected `label_available_ts_precedes_event_ts`, got
   `{label_pack_not_registered}` (fixture `_LabelRecord` default
   READY_FOR_STUDY at line 199 now trips the lifecycle gate BEFORE the
   no-lookahead availability gate).
2. Same file `::test_missing_feature_or_label_availability_timestamp_blocks`
   — `label_available_ts_missing` shadowed by `label_pack_not_registered`.
3. `tests/integration/runtime/test_smoke.py::test_smoke_resolves_dataset_version_and_builds_value_free_runtime_summary`
   — smoke degrades PASS→PASS_WITH_WARNINGS (fixture lifecycle READY_FOR_STUDY
   at line 167).

These are not pre-existing. CI runs the full `python -m pytest`
(`.github/workflows/frontier-ci.yml:31-34`), so this branch is CI-red. The
handoff is truthful about what it ran (every listed claim reproduced exactly),
but the spec's validation list did not cover the suites the change breaks; the
handoff's implicit "validation green" does not hold repo-wide.

Two no-lookahead guard tests now passing-for-the-wrong-reason-or-failing is
itself a guard-integrity concern: the lifecycle gate fires before the
availability gates for any non-REGISTERED fixture, so those no-lookahead
assertions stop exercising their intended checks until the fixtures are
flipped.

## 8. Artifact policy (special scrutiny #8) — PASS

- `git ls-files runs` → empty.
- Diff contains no SQLite/Parquet/values/heavy artifacts; new files are one
  test, one spec, one handoff (all text).
- Research-only language throughout; no alpha/tradability claims.
- All changes left unstaged per handoff; nothing committed.

---

## Findings

- **F1 (REWORK, must fix before merge)**: diff breaks 3 unmodified tests that
  pass at base — `tests/no_lookahead/research_runtime/test_input_resolver_available_ts.py`
  (2 tests, fixture line 199) and `tests/integration/runtime/test_smoke.py`
  (fixture line 167) — because READY_FOR_STUDY runtime-positive fixtures
  outside the executor's edit set now hit the new gate first. CI runs full
  pytest; branch is CI-red.
- **F2 (REWORK, design/doc reconciliation)**: REGISTERED-only runtime
  admissibility contradicts the committed design docs, which designate
  READY_FOR_STUDY as "the terminal study-consumable state"
  (`docs/feature_label_foundation/LABEL_STORE.md:78-83`,
  `guide/safety_semantics.md:120`, `guide/request_to_study.md:85`,
  `README.md:150`). Because READY_FOR_STUDY has no production writer
  (registration defaults REGISTERED, `labels/registry.py:158-160`; only
  `deprecate_label` transitions state) and zero canonical rows, REGISTERED-only
  is defensible — but it must be a recorded decision with the docs amended,
  not a silent inversion.
- **F3 (warning)**: remaining READY_FOR_STUDY fixtures not converted
  (`tests/no_lookahead/test_session_label_guard.py:288`,
  `tests/no_lookahead/research_runtime/test_no_lookahead_runtime_audit.py:172`,
  `tests/unit/runtime/audit/test_no_lookahead_audit.py:162`,
  `tests/unit/runtime/probe/test_signal_probe_runtime.py:195`,
  `tests/unit/runtime/diagnostics/label/test_label_diagnostics_runtime.py:165,255`,
  `tests/integration/feature_label/test_e2e_dryrun.py:304,353,946`). Some do
  not route through the gate (they currently pass), but they encode the
  contradicted admissibility convention and will rot.
- **F4 (note)**: `_pack_lifecycle_state` case-normalizes
  (`.strip().upper()`), so lowercase lifecycle strings are admitted as
  REGISTERED. Acceptable; recorded.
- **F5 (note)**: new test file uses private `registry._persist_label` to seed
  synthetic rows; fine for a fixture, but a public test-seeding helper would
  be cleaner.

## Required repairs

1. Make the full suite green (modulo the 3 pre-existing local env failures:
   duckdb fixture, polars fixture, databento_canonicalize): flip the
   READY_FOR_STUDY fixtures in
   `tests/no_lookahead/research_runtime/test_input_resolver_available_ts.py:199`
   and `tests/integration/runtime/test_smoke.py:167` to REGISTERED (or change
   the admissible-state decision, see repair 2) so the no-lookahead
   availability gates are exercised again. Re-run
   `pytest tests/unit tests/no_lookahead tests/integration -q` and report
   counts in the handoff.
2. Record the admissibility decision: either (a) keep REGISTERED-only and
   amend `docs/feature_label_foundation/{LABEL_STORE.md,README.md,guide/*}`
   (plus a `decisions/` entry) so "terminal study-consumable state" no longer
   contradicts the runtime gate and sweep/justify the remaining
   READY_FOR_STUDY fixtures (F3), or (b) admit
   {REGISTERED, READY_FOR_STUDY} at runtime and keep the docs. Option (a)
   matches the spec mandate and operational reality; either way it must be
   explicit and committed in the same phase.
3. Update the handoff validation section with the full-suite results and the
   pre-existing-failure triage so the next reviewer is not pointed at a
   narrow green set.

## What is solid (keep as-is)

The enforcement core needs no rework: gate placement before handle
construction, deprecated→`*_pack_deprecated` with replacement pointer from
real deprecation metadata, unknown-id path untouched, raw audit access
preserved at every call site (deprecate tooling + scaleout driver verified),
feature-side symmetry closed identically, missing-lifecycle fail-closed
strengthening, and mutation-verified tests on the real registry at both
layers.

---

## Repair delta re-review (fresh delta reviewer, 2026-06-11)

Scope: ONLY the bounded-repair delta in worktree
`/home/yuke_zhang/projects/alpha_system_wt/p22-lifecycle` (branch
`repair/p22-lifecycle-enforcement`, base `origin/main` @ 6f405bc, all changes
unstaged). The enforcement core was mutation-verified in the original review
and was NOT re-reviewed; it is byte-stable: the diff stat grew from the
reviewed 306(+)/19(−) to 330(+)/32(−), and the +24/−13 delta is exactly the 5
docs amendments (+22/−11) plus the two one-line fixture flips (+2/−2). No
src/ file changed since the original review.

### Repair 1 — broken fixtures (F1): VERIFIED FIXED

- `tests/no_lookahead/research_runtime/test_input_resolver_available_ts.py:199`
  and `tests/integration/runtime/test_smoke.py:167`: each diff is exactly one
  fixture-default flip `READY_FOR_STUDY` → `REGISTERED`. No assertion added,
  deleted, or relaxed anywhere in the repair delta (`git diff` of both files
  is 1 line each; docs/handoff contain no assertions).
- Original assertions restored AND exercised: the availability-gate reason
  codes (`label_available_ts_precedes_event_ts` line 46,
  `feature_available_ts_missing`/`label_available_ts_missing` lines 58-59)
  can only be produced by the availability gates, which are now reached
  because the fixture is admissible; `test_smoke.py:62` asserts
  `RuntimeSmokeStatus.PASS` (strict, unweakened). Targeted run: both files
  `8 passed in 0.21s`.

### Repair 2 — admissibility decision recorded (F2): VERIFIED

- Spec section "Admissibility decision (coordinator, 2026-06-11T15:45Z)"
  exists in
  `specs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/P151500_FUTSUB_P22_LIFECYCLE_ENFORCEMENT-deprecated-lock-fail-closed.md:85-97`
  (committed-eligible) and records: REGISTERED-only, READY_FOR_STUDY
  reserved/no-writer/zero-rows, one-line reviewed extension if a promotion
  API ever ships.
- All 5 contradicting docs amended with a dated (2026-06-11) note:
  `docs/feature_label_foundation/LABEL_STORE.md`, `README.md`,
  `guide/README.md`, `guide/request_to_study.md`, `guide/safety_semantics.md`.
  Each note states exactly the verified facts: reserved, no production
  writer, runtime resolution admits REGISTERED only, not runtime-admissible
  until a reviewed promotion API explicitly extends admissibility, and
  preserves the research-only "not a result claim" language. No overclaiming
  (claims match the original review's own code-level findings: enum-only
  membership `labels/registry.py:68`, registration defaults REGISTERED, only
  `deprecate_label` transitions, zero canonical rows).
- Note: no separate `decisions/` entry was added; the decision is durably
  recorded in the committed spec section + 5 docs. Recorded as a warning, not
  a blocker — the spec is itself a committed durable record and the repair
  contract anchored to the spec section.

### Repair 2b — remaining READY_FOR_STUDY fixture sweep (F3): VERIFIED NOT GATE-ROUTED

`grep -rn READY_FOR_STUDY tests/ --include='*.py'` → 10 references, each
audited for gate-routing (does the record flow through
`FeatureLabelPackResolver`/`resolve_runtime_input_pack`?):

1. `tests/no_lookahead/test_session_label_guard.py:288` — direct
   `LabelPackHandle(...)` construction (post-gate output object) fed to the
   session-label guard; file imports only
   handle/pack dataclasses + `_reject_label_as_live_feature` from
   input_resolver, zero calls to the resolver. NOT gate-routed.
2. `tests/unit/runtime/audit/test_no_lookahead_audit.py:162` — direct
   `LabelPackHandle` in `_label_pack()`; imports only
   `FeaturePackHandle/LabelPackHandle/RuntimeInputPack`. NOT gate-routed.
3. `tests/no_lookahead/research_runtime/test_no_lookahead_runtime_audit.py:172`
   — identical direct-construction pattern, same imports. NOT gate-routed.
4. `tests/unit/runtime/probe/test_signal_probe_runtime.py:195` — direct
   `RuntimeInputPack(... label_packs=(LabelPackHandle(...),))` construction
   in `_input_pack()`; no resolver call. NOT gate-routed.
5. `tests/unit/runtime/diagnostics/label/test_label_diagnostics_runtime.py:165`
   — direct `RuntimeInputPack` construction in `_runtime_input_pack()`; NOT
   gate-routed. `:255` is a plain string in a synthetic
   `LabelLeakageAuditReport` dict (pure data). NOT gate-routed.
6. `tests/integration/feature_label/test_e2e_dryrun.py:304/306` —
   `dataclasses.replace` on a registry record + enum-membership assertions
   (governance lifecycle progression, no resolver import anywhere in the
   file); `:353/:946` are expected lifecycle-progression tuple literals.
   NOT gate-routed.

The gate has exactly two consumer entry points
(`input_resolver.py:470` and `:544`, both inside the resolver before handle
construction) — none of the 10 references reach them. No missed repair; all
gate-routed fixtures were already flipped in the reviewed core diff.

### Repair 3 — handoff truthfulness: VERIFIED

`handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/P151500_FUTSUB_P22_LIFECYCLE_ENFORCEMENT.md`
gained a "Bounded repair attempt 1 validation" section claiming full suite
`3 failed, 2830 passed, 1 skipped` with the 3 named failures, base-archive
triage reproducing all 3 at `6f405bc`, repaired files `8 passed`, smoke +
canaries PASS. Re-reviewer reproduced every claim (below); the base triage is
additionally consistent with the original review's own stash-baseline.

### Independent validation (re-run by this reviewer in the worktree)

| Command | Result |
|---|---|
| `pytest tests/unit tests/no_lookahead tests/integration -q` | **3 failed, 2830 passed, 1 skipped** — failures are exactly the 3 pre-existing env issues (`test_databento_canonicalize.py::test_databento_canonicalize_quality_coverage_and_register_offline`, `test_duckdb_query_fixture.py::test_duckdb_query_over_tiny_csv_fixture`, `test_polars_lazy_fixture.py::test_polars_lazy_transformation_over_tiny_fixture`), all proven failing at base. The 3 F1 diff-caused failures are GONE. |
| repaired files (`test_input_resolver_available_ts.py` + `test_smoke.py`) | 8 passed |
| `python tools/verify.py --smoke` | exit 0 |
| `python tools/hooks/canary_runner.py` | all Frontier canaries passed |
| `git ls-files runs` | empty |
| `git diff --check` | clean |

### Artifact policy: PASS

`git ls-files runs` empty; tracked delta = 5 docs + 2 test fixtures only;
untracked = spec + handoff + one test file (all text); no values/SQLite/
Parquet/heavy artifacts; research-only language throughout; everything
unstaged.

### Final verdict: PASS_WITH_WARNINGS

All 3 required repairs verified complete; branch is suite-green modulo the 3
proven pre-existing env failures. Warnings carried (non-blocking): (W1) no
separate `decisions/` entry — decision recorded in spec + docs only; (W2)
the 10 remaining READY_FOR_STUDY fixtures depict a now-reserved state on
non-gate paths (harmless, justified above, but they will read oddly against
the amended docs); (W3) original F4 (case-normalization) and F5 (private
`_persist_label` seeding) notes stand.
