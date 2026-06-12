# Review: P034000_POOLED_TRACK_B — pooled evaluation + mandatory Track-B registration

- Campaign: DISCOVERY_RIGOR_FLOOR_V1
- Phase: P034000_POOLED_TRACK_B (lane: yellow)
- Reviewer: fresh adversarial Claude review (independent of executor)
- Worktree reviewed: `/home/yuke_zhang/projects/alpha_system-wf1-session-reset`, branch `feat/pooled-track-b` at `819c153`, diff UNCOMMITTED
- Spec: `specs/DISCOVERY_RIGOR_FLOOR_V1/P034000_POOLED_TRACK_B-pooled-evaluation-and-mandatory-registration.md`
- Implementation sha256 (reviewed state):
  `03eee65e3bcb261dd3a80443d9b8f0f69d0bafc3960d0257cd17908b204497a5  src/alpha_system/governance/pooled_hypothesis.py`

## Verdict

**REWORK** — one MAJOR finding (F1, pre-metric ordering bypass by self-declared
backdated `registered_at`, empirically demonstrated) plus two bounded test-coverage
gaps (F2, F3). Everything else is solid: the content address covers the full
contract, the registry refusal + diff surfacing works and is mutation-resistant,
the aggregation rule is a closed enum, the VariantLedger linkage composes with
the real RIGOR-P02 API, all required validation is green, and all four mandated
mutation tests are caught by the suite. The fixes are small and surgical.

## 1. §2.1 structural enforcement (content address, refusal, append-only, closed enum)

- **Hash coverage — full contract, verified.**
  `POOLED_HYPOTHESIS_ID_COMPONENT_FIELDS` = every required field except
  `pooled_hypothesis_id` itself: `mechanism_rationale`, `pool_kind`, `members`,
  `aggregation_rule` (the weights rule), `horizons`, `sessions`, `symbols`,
  `registered_at`, `registered_before_metrics`, `variant_ledger_record`
  (pooled_hypothesis.py:53-55). No contract field is excluded from the hash.
  `validate_schema(..., allowed_fields=POOLED_HYPOTHESIS_REQUIRED_FIELDS)`
  (line 399-405) rejects any extra field (`unknown_field`), so there is no
  post-hoc-mutable side channel outside the hash. ID = sha256 over canonical
  JSON of `{components, kind, prefix}` via pre-existing
  `generate_governance_id` (ids.py:106-136), prefix `poolhyp` registered in the
  existing prefix table (ids.py diff, +2 lines).
- **Registry refusal + diff surfacing — verified.** `register()` compares
  `canonical_serialize(incoming_mapping)` against the prior record's canonical
  JSON for an existing id and raises `pooled_hypothesis_payload_conflict` with
  `_diff_summary` of changed field paths (lines 316-330). Identical payload
  re-registration is idempotent (appended=False, 0 new VariantLedger rows) —
  proven by `test_registry_refuses_modified_payload_under_existing_id`.
- **Append-only — verified.** The only write in the module is
  `self.path.open("a", ...)` (line 343); grep for `"w"` open / `write_text` /
  `unlink` / `os.replace` / `shutil` over pooled_hypothesis.py: no hits. The
  registry file must pre-exist and be writable (fail-closed), and every loaded
  row is re-validated, so a hand-edited row poisons the registry loudly
  (`invalid_pooled_hypothesis_registry_row`). Note: append-only is a code-level
  guarantee; the JSONL file itself is only externally anchored once committed.
- **Closed enums — verified.** `PoolKind` (cross_symbol|cross_horizon|cross_family)
  and `PooledAggregationRule` (equal_weight_mean only) are `StrEnum`s; free-form
  values fail (`invalid_pool_kind` / `invalid_pooled_aggregation_rule`), and
  `aggregate_pooled_metric` re-checks the rule defensively (lines 533-542).
  No free-code weights path exists; equal weights are implied by the enum.

## 2. Pre-metric ordering — comparison direction correct, but bypassable (F1)

Direction itself is correct: `ensure_registration_precedes_metrics` refuses when
`registered >= started_at` (line 510-519), i.e. `registered_at` must be strictly
before the marker timestamp; absent marker allows registration; unreadable/empty/
non-timestamp marker fails closed. CLI surfaces the refusal (exit 2,
`pooled_registration_after_metrics_started`), tested at unit + CLI level.

**F1 (MAJOR): a NEW registration attempted after the marker exists is ACCEPTED if
its self-declared `registered_at` is backdated before the marker timestamp.**
Empirical probe (fresh registry, marker containing `2026-06-12T12:00:00Z` already
on disk, new payload with `registered_at=2026-06-12T11:00:00Z`, valid
content-addressed id):

```text
BACKDATED NEW REGISTRATION AFTER MARKER EXISTS: ACCEPTED, appended = True
```

`registered_at` is chosen freely by the registrant and is the only thing compared
against the marker; no wall-clock or registration-event anchor exists. So the
§2.1-forbidden act — registering a pool after Track-A metrics started ("pool
shopping" with knowledge of results) — is not structurally impossible; it only
requires writing an earlier timestamp into your own payload. The content hash
does not help (a backdated payload is just a different, valid id). The boolean
`registered_before_metrics` is likewise self-attested (validation requires it to
be literally `true`, so it carries no information).

Bounded fix (preserves all existing tests and idempotent resume):
in `PooledHypothesisRegistry.register()`, when the metrics-started marker file
EXISTS, refuse any **new** append outright (registration window closed),
regardless of declared `registered_at`; keep the timestamp comparison for the
existing-identical-record path (re-validation/resume of records already in the
registry). Optionally also refuse `registered_at` in the future relative to
wall clock at append time. Add a regression test: marker present + backdated
new payload → refused.

(Mitigation in current state: the timestamp comparison is the literal spec text,
and once the registry JSONL is committed, git history externally anchors when
each line appeared. But the phase's stated purpose is structural enforcement at
the gate, and the kill-shot runner that writes this marker is the next thing on
the roadmap — this gate should be closed before any Track-A metric exists.)

## 3. VariantLedger linkage — composes, exactly one, no fork

- `variant_ledger.py` is untouched (not in `git status`); pooled module imports
  the real RIGOR-P02 `VariantLedger`/`validate_variant_ledger_record` and appends
  through `VariantLedger.append_records`, which dedupes by variant/study/trial
  key (variant_ledger.py:332-359) — idempotent re-registration appends 0 rows
  (asserted in test: ledger length stays 1).
- The schema admits exactly one `variant_ledger_record` (dict, required); it must
  be status `PLANNED`, `created_at` must equal `registered_at`, and its
  `study_spec_id` must anchor to a fixed member (lines 823-866). The linked
  record is inside the content hash, so it is immutable with the contract.
- Observation (no action): registry path and ledger path are independent
  caller-supplied paths, consistent with the existing explicit-path governance
  CLI pattern; "exactly one entry" is enforced per ledger file, with the
  canonical paths fixed by gate-time tooling, not this module.

## 4. track_b_minimum_satisfied() and DRAFT templates

- Requires ≥1 `cross_symbol` AND ≥1 `cross_horizon` valid record whose members
  are a subset of the kill-shot study set (lines 577-595); single-kind and
  wrong-study-set cases are negatively tested.
- Every record passed in is fully re-validated (`_coerce_pooled_records`), so the
  DRAFT templates **cannot** satisfy it. Empirically verified for both templates:
  the wrapper payload is rejected (`missing_required_field`, `unknown_field` —
  `template_status`, `not_registered`, etc. are not allowed fields) and the inner
  `registration_payload_template` is rejected (`invalid_field_type` — placeholder
  sentinels: non-bool `registered_before_metrics`, plus non-Z timestamps and a
  non-`poolhyp` id behind it). Templates are clearly marked
  `"template_status": "DRAFT_NOT_REGISTERED"`, `"not_registered": true`, and
  reference exactly the 6 re-locked rerun sspec ids (asserted by
  `test_track_b_templates_are_draft_not_registered_and_reference_relocked_ids`).
- **F3 (MINOR):** no test pins the unregistrability itself — add a test feeding
  both template payloads (wrapper and inner) to
  `validate_pooled_hypothesis_record` and asserting rejection, so future template
  edits cannot silently become registrable.

## 5. aggregate_pooled_metric() — pure, pool + components, value-free

- No I/O anywhere in the function; consumes a validated record + component metric
  records (metric_name / point_estimate / se / n_eff / metadata). Equal-weight
  mean; SE = sqrt(sum se²)/n; n_eff summed; result `to_dict()` reports
  `pooled_result` AND all `components` (§2.1 ALLOWED). No PnL/value math — it
  aggregates abstract study metric records only; features/labels/runtime are
  untouched (git status confirms).
- Component set must EXACTLY match fixed membership (no drop/add/duplicate —
  `pooled_component_membership_mismatch`, negatively tested) and exactly one
  metric name is allowed. Cherry-picking components is structurally refused.

## 6. Mutation tests (all restored byte-identical; see verdict JSON for sha256)

| # | Mutation | Result |
|---|----------|--------|
| a | Neutralize registry refusal (`if False and canonical_serialize(...) != ...`) | CAUGHT — `test_registry_refuses_modified_payload_under_existing_id` FAILED (pytest.raises not triggered); 1 failed, 5 passed |
| b | Exclude `members` from `POOLED_HYPOTHESIS_ID_COMPONENT_FIELDS` | CAUGHT — `test_pooled_hypothesis_record_round_trips_and_id_changes` FAILED at the `id != original` assertion; 1 failed, 7 passed |
| b′ (extra probe) | Exclude `horizons`,`sessions`,`symbols` from the hash | **NOT caught — 10 passed** (→ F2) |
| c | `track_b_minimum_satisfied` returns `or` instead of `and` | CAUGHT — `test_track_b_minimum_requires_cross_symbol_and_cross_horizon` FAILED; 1 failed, 7 passed |
| d | Disable marker refusal (`if False and registered >= started_at`) | CAUGHT — unit AND CLI marker tests FAILED; 2 failed, 6 passed |

**F2 (MINOR, fold into rework):** hash-coverage mutation resistance exists only
for `members`. Excluding the horizon/session/symbol sets (and by extension
mechanism/aggregation_rule/registered_at) from the id components passes the whole
suite. The runtime conflict check still compares full canonical payloads, so
same-id edits remain refused today, but the "edits = new hypothesis" property
would silently degrade under refactor. Add one test asserting
`set(POOLED_HYPOTHESIS_ID_COMPONENT_FIELDS) == set(POOLED_HYPOTHESIS_REQUIRED_FIELDS) - {"pooled_hypothesis_id"}`
and/or a per-field perturbation loop asserting the id changes for every
contract field.

## 7. Validation runs (research venv `~/.venvs/alpha_system_research`)

- `pytest tests/unit/governance -q` → **614 passed** (2.88s)
- `pytest tests/unit/discovery_rigor_floor -q` → **17 passed** (0.10s)
- combined post-restore re-run → **631 passed**
- `tools/hooks/canary_runner.py` → **23 PASS** lines, "All Frontier canaries
  passed." (23, not 21: RIGOR-P04 added canaries incl. `planted_fake_alpha` —
  count is current main behavior, not a regression)
- `tools/verify.py --smoke` → exit 0
- Venv note (recurring): the venv resolves `alpha_system` to the main repo;
  pytest in the worktree is safe via pyproject `pythonpath=["src"]`; ad-hoc
  probes were run with explicit `PYTHONPATH=src`.

## 8. Artifact policy / boundaries / language

- Nothing staged (`git diff --cached --name-only` → 0); `git ls-files runs` → 0.
- Diff confined to: governance module (new pooled_hypothesis.py + 2-line ids.py
  + 1-line `__init__.py`), CLI additions, 4 test files, 2 DRAFT templates under
  `research/discovery_rigor_floor_v1/track_b/`. No features/labels/runtime
  edits; promotion_gate.py untouched; no second PnL/value truth.
- Research-only language: grep for alpha/profitability/tradability/production
  claims over templates + module → no hits. Template rationales say
  "Template only: register one mechanism-based ... hypothesis", no edge claims.
- Cosmetic (no action required): unreachable `len(sessions) < 1` branch in
  `_validate_pool_kind_shape` (empty sessions already rejected upstream);
  `payload` name shadowing in `run_register_pooled_hypothesis`; the
  `registered_before_metrics` skip inside `track_b_minimum_satisfied` is dead
  code (validation already requires `true`); VariantLedger append precedes the
  registry append, so a crash in between leaves an orphan ledger row (idempotent
  retry heals it).

## Required rework (bounded)

1. F1: marker-present ⇒ refuse all NEW registry appends regardless of declared
   `registered_at` (keep timestamp comparison for already-registered identical
   payloads); regression test: marker exists + backdated new payload → refused.
2. F2: hash-coverage test pinning every contract field into
   `POOLED_HYPOTHESIS_ID_COMPONENT_FIELDS` (or per-field id-perturbation loop).
3. F3: test asserting both DRAFT template payloads (wrapper + inner) fail
   `validate_pooled_hypothesis_record`.

## REWORK resolution (re-review)

Re-reviewed 2026-06-11 by a fresh reviewer against the repaired uncommitted diff
in `/home/yuke_zhang/projects/alpha_system-wf1-session-reset` (branch
`feat/pooled-track-b` @ `819c153`). Repaired implementation sha256:
`938fae481db7666f4aa9974ae6f5d713c4cab233578bbedeb0fdb96a045671eb  src/alpha_system/governance/pooled_hypothesis.py`

**Verdict upgraded: REWORK → PASS_WITH_WARNINGS.** All three findings resolved
and independently re-verified:

- **F1 RESOLVED.** `register()` now calls
  `_refuse_new_registration_when_metrics_started()` on the new-registration path
  (pooled_hypothesis.py:340): if the metrics-started marker file EXISTS, every
  NEW registration is refused outright (`pooled_registration_window_closed`) —
  no timestamp comparison, so the self-declared `registered_at` is irrelevant.
  The existing-identical-record resume path keeps
  `ensure_registration_precedes_metrics()` (line 331), exactly per the bounded
  fix. The reviewer re-ran the ORIGINAL backdating probe (fresh registry, marker
  `2026-06-12T12:00:00Z` on disk, new valid payload with
  `registered_at=2026-06-12T11:00:00Z`): **REFUSED**,
  code `pooled_registration_window_closed`, and both the registry JSONL and the
  VariantLedger JSONL remained 0 bytes (the guard fires before the ledger
  append, so the F1 path can no longer create an orphan ledger row either).
  Regression test
  `test_registry_refuses_backdated_new_registration_after_metrics_marker_exists`
  pins the refusal code plus zero-write behavior.
- **F1 mutation check.** Temporarily removed the
  `_refuse_new_registration_when_metrics_started()` call (restoring the old
  timestamp-comparison-only behavior): the regression test FAILED
  (`Failed: DID NOT RAISE` at line 214, 1 failed). Restored; sha256 before and
  after byte-identical (`938fae48…`).
- **F2 RESOLVED.** `test_pooled_hypothesis_id_changes_for_each_contract_component`
  asserts `set(POOLED_HYPOTHESIS_ID_COMPONENT_FIELDS) ==
  set(POOLED_HYPOTHESIS_REQUIRED_FIELDS) - {"pooled_hypothesis_id"}` AND runs a
  per-field `poolhyp_` id-perturbation loop over `mechanism_rationale`,
  `members`, `horizons`, `sessions`, `symbols`, `aggregation_rule` (monkeypatched
  extended enum to perturb the closed rule). Reviewer spot-flip of `sessions`
  (`rth`→`eth`): `poolhyp_51e971b83c28d029…` → `poolhyp_d52333902ea0f018…`,
  different id. The b′ probe class from the original review is now caught.
- **F3 RESOLVED.** `test_track_b_draft_templates_are_unregistrable_as_is` feeds
  both templates' wrapper payloads (asserts `missing_required_field` +
  `unknown_field`) and the inner `registration_payload_template` (asserts
  `invalid_field_type`) to `validate_pooled_hypothesis_record`.

Re-validation (research venv): `tests/unit/governance` → **616 passed** (was
614; +2), `tests/unit/discovery_rigor_floor` → **18 passed** (was 17; +1),
combined → **634 passed in 2.96s**; `canary_runner.py` → **23 PASS**, "All
Frontier canaries passed."; `verify.py --smoke` → exit 0. Nothing staged,
`git ls-files runs` empty.

Remaining warnings: the O1 observations stand (caller-supplied paths fixed by
gate-time tooling; cosmetic items unchanged). The optional wall-clock
future-`registered_at` refusal from the fix sketch was not implemented and is
not required — marker presence alone now closes the window.
