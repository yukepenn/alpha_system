# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing
and validating offline research substrate under Frontier Harness Generic
`0.3.0-rc1`.

## Current Snapshot

The repository-level campaign pointer targets
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

Post-`FUTSUB-P33` snapshot: the final acceptance audit and semantic done-check
artifacts exist, and
`campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/CLOSEOUT.md` records
the campaign verdict as `BLOCKED`. The block is committed review provenance:
the substrate evidence, P30 artifact audit, and P31/P32 downstream handoffs are
present, but the acceptance contract requires committed Yellow-lane review
artifacts that are missing for most named FUTSUB phases.

New closeout docs are
`campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/CLOSEOUT.md`,
`docs/futures_substrate_scaleout/CLOSEOUT.md`, and the value-free closeout
indexes under `research/futures_substrate_scaleout_v1/closeout/`. The
Validation Governance, FactorLibrary, and Multi-Horizon Mining handoffs remain
the downstream requirement handoffs for the next coordinator-owned work.

The refreshed `FUTSUB-P29` boundary remains `10 REJECT / 0 INCONCLUSIVE / 0
WATCH / 0 CANDIDATE_RESEARCH`, with retained caveats around label diagnostics,
duplicate within-family exposures, and BBO proxy limits. There is no next phase
within this campaign until the coordinator resolves the closeout block and then
updates `ACTIVE_CAMPAIGN.md`.

The committed campaign pointer and README are snapshots. For authoritative
in-flight Workflow 2 state, use `python tools/frontier/status_doctor.py` or the
run-local state owned by Ralph.

## Source Of Truth

- Root campaign pointer: `ACTIVE_CAMPAIGN.md`
- Active campaign bundle:
  `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`
- Value-free research evidence root:
  `research/futures_substrate_scaleout_v1/`
- Commit-eligible handoffs:
  `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`
- Strategy and roadmap compass: `docs/OPERATING_COMPASS_V4.md`

## Safety Boundaries

The project remains research-only and local-first. This campaign does not
authorize live trading, paper trading, broker operations, order routing,
deployment, account operations, funding decisions, or autonomous trading
behavior.

Artifact discipline is unchanged: explicit staging only and value-free evidence
only. `runs/**` is local-only and never committed. Raw or canonical data,
feature or label values, provider responses, heavy artifacts, local databases,
logs, caches, secrets, and credentials are never committed.

The FUTSUB rerun gate does not authorize new AlphaSpecs, parameter tuning,
Strategy Reference validation, FactorLibrary ingestion, AlphaBook construction,
paper/live behavior, broker access, deployment, market-performance claims, or
execution-readiness claims. Local feature/label values and registries remain
outside git under `ALPHA_DATA_ROOT`. Workflow 2 orchestration, validation
routing, review, staging, commit, PR, CI, merge, and done-check actions are owned
by Ralph.
