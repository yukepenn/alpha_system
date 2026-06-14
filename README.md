# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing
and validating offline research substrate under Frontier Harness Generic
`0.3.0-rc1`.

## Current Snapshot

The active non-mock campaign is `ALPHA_IDEA_TO_VERDICT_LOOP_V0`, a seven-phase
IVL-P00..P06 assembly of the researcher-facing idea-to-verdict loop. IVL-P05 is
complete after IVL-P00..P04 established the role map, intake validator,
executable pre-test gate, generic fast exploratory lane bridge, and governed
verdict report renderer:

- `alpha idea validate <idea.yaml>` emits a value-free canonical object family:
  `IdeaDraft` lineage sidecar, HypothesisCard parent, AlphaSpec trunk, and an
  EXPLORATORY MechanismCard; a SetupSpec is emitted only for
  `study_kind=context_not_equal_trigger`.
- `alpha idea testability <idea.yaml>` and alias
  `alpha idea gate <idea.yaml> [--slice <id>]` return pre-test
  PASS/FAIL/DATA_GAP checks before any probe shot is spent.
- `src/alpha_system/governance/idea_draft.py` holds the intake-only
  `study_kind` discriminator and object lineage. The frozen governance schemas
  (`AlphaSpec`, `MechanismCard`, `SetupSpec`) remain byte-unchanged.
- `src/alpha_system/governance/track_a_migration.py` migrates the eight legacy
  Track-A document cards into value-free canonical records under
  `research/idea_to_verdict_loop_v0/`, preserving each legacy slug as
  `source="track_a:<slug>"`.
- `src/alpha_system/research_lane/testability_gate.py` lives outside
  `research/` and checks materialized feature handles, label/path-label handles,
  path-label class non-degeneracy, N_eff/MDE plus dedup declaration, and
  available_ts plus surrogate-FDR readiness without loading values.
- `src/alpha_system/research_lane/slice_spec.py` defines the bounded,
  de-hardcoded fast-probe slice descriptor: root resolution, governed pack refs
  or relative paths, instrument/session/data version, and label-version map.
- `src/alpha_system/research_lane/fast_probe.py` loads an already-materialized
  bounded slice with `core.value_store.load_parquet_values`, validates supplied
  pack refs through `FeatureLabelPackResolver`, maps rows to the governance
  row schema, and feeds the unchanged probe engines in memory.
- `src/alpha_system/research_lane/verdict_report.py` renders a governed
  human-readable `REPORT.md` from precomputed intake, testability, and fast
  readout summaries; `alpha idea report <idea.yaml> --testability-json <path>
  --fast-readout-json <path>` exposes the renderer without running a probe.
- `src/alpha_system/research_lane/memory_router.py` routes governed verdicts to
  value-free memory records: REJECT to the rejected-idea graveyard keyed by the
  minted AlphaSpec id, DATA_GAP to requeue, and WATCH/CANDIDATE only through
  reviewer-gated promotion inputs.
- `alpha idea run <idea.yaml>` now composes validate, testability, fast probe
  when the pre-test gate passes, report rendering, and memory routing. A
  DATA_GAP gate short-circuits before a probe shot is spent.
- `src/alpha_system/research/conditional_probe.py` now has an additive
  >=2-distinct-class guard for conditioned path-label rows.

After IVL-P05, the next phase is IVL-P06: dogfood the assembled loop on the
DK Track B fixture. The campaign remains GREEN/YELLOW only and
research-only: no alpha, profitability, tradability, or production claim; no
second value/accounting truth; `research/` imports no value engine; exploratory
readouts are never auto-promoted; no materialize, scaleout-driver, paid-data,
broker, paper, live, order-routing, deployment, or FactorLibrary promotion.
FactorLibrary remains survivor-only, exploratory outputs keep
`promotion_eligible` false, and the frozen governance schemas remain
byte-unchanged.

The committed campaign pointer and README are snapshots. For authoritative
in-flight Workflow 2 state, use `python tools/frontier/status_doctor.py` or the
run-local state owned by Ralph.

## Source Of Truth

- Root campaign pointer: `ACTIVE_CAMPAIGN.md`
- Active campaign bundle: `campaigns/ALPHA_IDEA_TO_VERDICT_LOOP_V0/`
- Canonical IVL map: `docs/IDEA_TO_VERDICT_SCHEMA_MAP.md`
- Value-free IVL migration root: `research/idea_to_verdict_loop_v0/`
- Commit-eligible handoffs: `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/`
- Strategy and roadmap compass: `docs/OPERATING_COMPASS_V4.md`

## Safety Boundaries

The project remains research-only and local-first.
`DIFFERENTIATED_KILLSHOT_V1` authorizes a differentiated-substrate research
kill-shot only. It does not authorize live trading, paper trading, broker
operations, order routing, deployment, account operations, funding decisions, or
autonomous trading behavior.

Artifact discipline is unchanged: explicit staging only and value-free evidence
only. `runs/**` is local-only and never committed. Raw or canonical data,
feature or label values, provider responses, heavy artifacts, local databases,
logs, caches, secrets, and credentials are never committed.

This campaign does not authorize FactorLibrary ingestion, AlphaBook
construction, paper/live behavior, broker access, deployment, economic-use
claims, execution-readiness claims, paid-feed onboarding, or promotion.
`pyproject.toml` dependencies remain empty, so numpy, pandas, and polars stay
absent. Truth-chain invariants are preserved, including the sanctioned reference
engine as the only value/accounting truth. Workflow 2 orchestration, validation
routing, review, staging, commit, PR, CI, merge, and done-check actions are owned
by Ralph.
