---
campaign_id: ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1
phase_id: P151500_FUTSUB_P22_LIFECYCLE_ENFORCEMENT
lane: yellow
status: in_progress
---

# P151500_FUTSUB_P22_LIFECYCLE_ENFORCEMENT: deprecated label locks must fail closed

## Purpose

FUTSUB-P22's fresh review (run-local review.md, F1, 2026-06-11T15:04Z) proved
the production resolver does NOT fail closed on a DEPRECATED
`label_version_id`:

- `src/alpha_system/labels/registry.py` `resolve_label` /
  `resolve_label_by_version` return the row with no lifecycle filter
  (`_fetch_record_row` selects by id only); the `is_deprecated` helper is
  never called by the runtime path.
- `src/alpha_system/runtime/input_resolver.py`
  `FeatureLabelPackResolver.resolve_label_packs` raises
  `label_pack_not_found` only when the registry returns `None`; the
  `LabelPackHandle.lifecycle_state` field is carried unvalidated and no
  REGISTERED-state enforcement exists in the module.

Consequence: a StudySpec lock referencing one of the 48 deprecated close-out
ids (or the 96+ other sanctioned deprecations from the 2026-06-11 identity
repairs) resolves into a full active handle. P22's repair records this as an
explicit gap; this phase closes it. Coordinator-routed per the reviewer's
Required Repair 1 ("routed to the coordinator for lifecycle enforcement; do
not fix resolver/registry code inside P22").

## Scope (in-bounds)

1. **Runtime enforcement (the gate)**: in
   `src/alpha_system/runtime/input_resolver.py`, enforce
   `lifecycle_state == "REGISTERED"` for every resolved label pack handle.
   A DEPRECATED (or any non-REGISTERED) record must produce a CLOSED failure
   with a distinct reason (e.g. `label_pack_deprecated`, carrying the
   `replacement_label_version_id` from the registry record when present so
   the error is actionable). Unknown id behavior (`label_pack_not_found`)
   unchanged.
2. **Registry lifecycle-aware resolver**: in
   `src/alpha_system/labels/registry.py`, add an explicit lifecycle-aware
   resolution path (e.g. `resolve_active_label(...)` or an
   `include_deprecated: bool = False` parameter on `resolve_label`) so the
   runtime resolver's enforcement reads lifecycle from the registry record,
   not from convention. The RAW by-id resolution must remain available for
   audit/deprecation tooling (deprecate_label, audits read deprecated rows
   by design). No schema change; no write-path change.
3. **Feature-side symmetry check**: inspect the analogous feature pack
   resolution path; if the same gap exists for feature registries, close it
   identically in the same module(s); if it does not exist, record why in
   the handoff (one paragraph, file:line).
4. **Real tests, no fixture theater**: add NEW unit tests (own test file(s),
   e.g. `tests/unit/labels/test_registry_lifecycle_resolution.py` and/or a
   resolver-layer test) that drive the PRODUCTION registry + resolver path
   (real `LabelRegistry` on a temp SQLite with one REGISTERED and one
   DEPRECATED row — values local/synthetic) and assert: (a) the deprecated
   id produces the closed failure with the replacement pointer surfaced;
   (b) the REGISTERED id still resolves; (c) raw by-id audit access still
   returns the deprecated record. Fixtures must contain NO deprecation
   filtering of their own — the production check is the thing under test.
   Neutering the lifecycle check must fail these tests.

## Hard constraints

- FORBIDDEN: `labels/engine.py`, `labels/families/**`, `labels/fast/**`,
  `labels/roll_guard.py`, `labels/version.py`, any value/accounting math,
  any registry write-path or schema change. This phase is resolver-read-path
  enforcement only.
- The deprecation API (`deprecate_label`) and audit tooling must continue to
  see deprecated rows; only RUNTIME pack resolution fails closed.
- No assertion deleted or weakened; the P22 repair's honest
  "gap exists" test may be UPDATED to assert the new fail-closed behavior
  (that is the point), provenance noted in the test docstring.
- No values/SQLite/runs committed; explicit staging only.
- AMENDED 2026-06-11T15:15Z: P22's re-review BLOCKED on this exact substrate
  defect (run-local review.md routing items 1-3), so this phase executes NOW
  against current main — P22 cannot merge without it. P22's own worktree
  artifacts (its smoke-test probe flip back to fail-closed + the three
  report/README gap-note refreshes) stay with P22's re-run after this fix
  merges; they are NOT in this phase's scope.

## Admissibility decision (coordinator, 2026-06-11T15:45Z, recorded per review)

Runtime pack resolution admits `lifecycle_state == "REGISTERED"` ONLY.
`READY_FOR_STUDY` is a designed-but-never-wired label-enum state (no
production writer exists — registration defaults REGISTERED, only
`deprecate_label` transitions state; zero rows in canonical registries;
absent from the feature enum). Admitting an unproducible state would be an
untestable open gate. Decision: keep REGISTERED-only enforcement; amend the
`docs/feature_label_foundation/` description accordingly (dated note: state
reserved, not runtime-admissible until a promotion API exists and explicitly
extends admissibility); sweep remaining READY_FOR_STUDY fixtures on
gate-routed paths. If a future phase ships a promotion API, extending
admissibility is a one-line, explicitly-reviewed change.

## Out of scope (coordinator data operation, not this phase)

W1 disposition: the 956 stale cost_adjusted rows from earlier P19 runs
(old BBO DatasetVersion ids, still REGISTERED) will be deprecated by the
coordinator via the sanctioned `deprecate_label` API with replacement
pointers + registry backup AFTER this phase merges, so the new enforcement
immediately protects against their accidental resolution. Local-only data
op; recorded value-free in the coordinator ledger, not committed.

## Validation

```bash
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/futures_substrate_scaleout/labels -q
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit -k "registry or resolver" -q
python tools/verify.py --smoke
python tools/hooks/canary_runner.py
```

## Done criteria

- A DEPRECATED label lock fed to the production resolver produces a closed,
  reasoned failure (test proves it against the real `LabelRegistry`, no
  fixture-side filtering).
- Registry exposes lifecycle-aware resolution; raw by-id access preserved
  for audit tooling.
- Feature-side symmetry verified (closed or explained).
- P22 gap records carry the dated closure note.
- All listed validation green; fresh adversarial review verdict PASS or
  PASS_WITH_WARNINGS under `reviews/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`.
