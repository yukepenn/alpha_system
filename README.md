# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing
and validating offline research substrate under Frontier Harness Generic
`0.3.0-rc1`.

## Current Snapshot

The repository-level campaign pointer targets
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

`REFERENCE_LABEL_PARALLEL_COMPUTE_V1` is closed as historical context: it added
an opt-in reference-worker path, measured workers=8 at 2.14x for
`cost_adjusted`, and kept default reference workers at 1 outside the documented
FUTSUB-P19 resume deviation.

Current campaign progress:
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` is the active Workflow 2
campaign. This `FUTSUB-P21` executor snapshot produced value-free
roll-splice and maintenance-crossing guard audit artifacts for all five
materialized LabelPack families. The audit demonstrates the guards on a 2024
June approximate roll boundary and a January 2024 daily maintenance break, and
records zero silently measured boundary crossings in the matrices. The
`label_integration` gate `FUTSUB-P21`...`FUTSUB-P23` is open and remains
Ralph/reviewer-gated.

Active / next phase after Ralph review and merge: `FUTSUB-P22` - LabelPack
Registry Integration, Coverage Audit, and Resolver Smoke.

New durable surfaces through this `FUTSUB-P21` executor snapshot:

- `docs/futures_substrate_scaleout/ROLL_GUARD_AUDIT.md` records the audit
  method, approximate-calendar caveat, per-family policy provenance,
  demonstrations, findings, and non-claims.
- `research/futures_substrate_scaleout_v1/matrices/roll_window_coverage.md`
  and `maintenance_crossing_invalidation.md` are value-free guard matrices
  with per-family x symbol x year counts, policy/version ids, and the
  approximate-calendar qualification.
- `research/futures_substrate_scaleout_v1/roll_guard/roll_guard_audit.md`
  records current local registry accounting, 2024 roll-week and
  maintenance-break demonstrations, and bounded value-store sample-read
  results.
- `tests/unit/futures_substrate_scaleout/labels/test_roll_maintenance_guard_audit.py`
  proves the audit detection logic fails closed on a planted silently measured
  crossing window and accepts guarded non-crossing windows.
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P21.md`
  records validation, evidence, findings, and artifact policy for reviewer and
  coordinator use.

The committed campaign pointer and README are snapshots. For authoritative
in-flight Workflow 2 state, use `python tools/frontier/status_doctor.py` or the
run-local state owned by Ralph.

## Source Of Truth

- Root campaign pointer: `ACTIVE_CAMPAIGN.md`
- Campaign bundle: `campaigns/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/`
- Value-free research evidence root:
  `research/reference_label_parallel_compute_v1/`
- Commit-eligible handoffs:
  `handoffs/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/`
- Campaign bundle: `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`
- Futures substrate scaleout docs: `docs/futures_substrate_scaleout/`
- Value-free research evidence root: `research/futures_substrate_scaleout_v1/`
- Commit-eligible handoffs:
  `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`

## Safety Boundaries

The project remains research-only and local-first. This campaign does not
authorize live trading, paper trading, broker operations, order routing,
production deployment, account operations, capital allocation, or autonomous
trading behavior.

The per-row reference label engine remains the correctness oracle. Registry
writes remain parent-only and serial. Label values, registries, manifests,
checkpoints, roll-calendar data, and SQLite files stay local-only under
`ALPHA_DATA_ROOT`; labels must never silently cross a quarterly roll or the
daily maintenance / trade-date break. The roll calendar is analytic and
approximate, not provider-exact splice truth. Resolver semantics remain
exact-id and fail-closed, with no fuzzy fallback.

Artifact discipline is unchanged: explicit staging only and value-free evidence
only. `runs/**` is local-only and never committed. Raw or canonical data,
feature or label values, provider responses, heavy artifacts, local databases,
logs, caches, secrets, and credentials are never committed.

This campaign makes no alpha, profitability, tradability, execution-quality, or
production-trading claim. Workflow 2 orchestration, validation routing, review,
staging, commit, PR, CI, merge, and done-check actions are owned by Ralph.
