# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing
and validating offline research substrate under Frontier Harness Generic
`0.3.0-rc1`.

## Current Snapshot

The active non-mock campaign is `ALPHA_IDEA_TO_VERDICT_LOOP_V0`, a seven-phase
IVL-P00..P06 assembly of the researcher-facing idea-to-verdict loop. IVL-P01
adds the front door:

- `alpha idea validate <idea.yaml>` emits a value-free canonical object family:
  `IdeaDraft` lineage sidecar, HypothesisCard parent, AlphaSpec trunk, and an
  EXPLORATORY MechanismCard; a SetupSpec is emitted only for
  `study_kind=context_not_equal_trigger`.
- `src/alpha_system/governance/idea_draft.py` holds the intake-only
  `study_kind` discriminator and object lineage. The frozen governance schemas
  (`AlphaSpec`, `MechanismCard`, `SetupSpec`) remain byte-unchanged.
- `src/alpha_system/governance/track_a_migration.py` migrates the eight legacy
  Track-A document cards into value-free canonical records under
  `research/idea_to_verdict_loop_v0/`, preserving each legacy slug as
  `source="track_a:<slug>"`.

After IVL-P01, the next phase is IVL-P02, the executable testability gate. The
campaign remains GREEN/YELLOW only and research-only: no alpha, profitability,
tradability, or production claim; no second value/accounting truth; no broker,
paper, live, order-routing, deployment, paid-data sourcing, or FactorLibrary
promotion. FactorLibrary remains survivor-only.

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
