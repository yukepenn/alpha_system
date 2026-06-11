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
campaign. This `FUTSUB-P22` executor snapshot audits the `FUTSUB-P16`...
`FUTSUB-P20` LabelPack materialization gate inside the `label_integration`
gate: all current dry-run label locks resolve by exact id, deprecated close-out
stale rows are excluded from the active surface, and the resolver-smoke
fail-closed probes cover absent, mutated, fuzzy-name, and deprecated exact-id
lock cases.

Active / next phase is Ralph-owned. The nominal next phase remains `FUTSUB-P23`
- Label Coverage Matrix and Horizon Quality Report, completing the
`label_integration` gate before the `wiring_and_matrices` gate
(`FUTSUB-P24`...`FUTSUB-P26`) begins after Ralph validation and Yellow-lane
review complete.

New durable surfaces through this `FUTSUB-P22` executor snapshot:

- `docs/futures_substrate_scaleout/LABEL_INTEGRATION.md` summarizes the
  integrated label substrate, resolver contract, overlap/N_eff provenance, and
  safety boundaries.
- `research/futures_substrate_scaleout_v1/label_packs/registry_integration_audit.md`
  records required registry field presence, identity and metadata checks,
  DatasetVersion acceptance state confirmation, guard provenance, deprecated-row
  disposition, and explicit gap classification.
- `research/futures_substrate_scaleout_v1/label_packs/label_resolver_smoke.md`
  records the value-free resolver-smoke matrix and fail-closed probes.
- `tests/unit/futures_substrate_scaleout/labels/test_label_resolver_smoke.py`
  proves exact label locks resolve against a tiny synthetic fixture, absent /
  mutated / fuzzy refs fail closed, and deprecated exact-id refs fail closed.
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P22.md`
  records validation, audit outcome, gaps, and artifact
  policy for coordinator use.

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
approximate, not provider-exact splice truth. Resolver semantics remain exact-id
with no fuzzy fallback; P22 also verifies deprecated exact-id refs fail closed.

Artifact discipline is unchanged: explicit staging only and value-free evidence
only. `runs/**` is local-only and never committed. Raw or canonical data,
feature or label values, provider responses, heavy artifacts, local databases,
logs, caches, secrets, and credentials are never committed.

This campaign makes no alpha, profitability, tradability, execution-quality, or
production-trading claim. Workflow 2 orchestration, validation routing, review,
staging, commit, PR, CI, merge, and done-check actions are owned by Ralph.
