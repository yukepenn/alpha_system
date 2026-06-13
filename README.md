# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing
and validating offline research substrate under Frontier Harness Generic
`0.3.0-rc1`.

## Current Snapshot

The repository-level campaign pointer targets
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

Post-`FUTSUB-P29` snapshot: 30 of 34 FUTSUB phases are complete after merge,
and the `rerun` gate (`FUTSUB-P27`...`FUTSUB-P29`) is closed. `FUTSUB-P27`
re-locked the Core Pilot StudySpecs against the full substrate, `FUTSUB-P28`
produced value-free rerun diagnostics, and `FUTSUB-P29` refreshed the honest
promotion boundary in
`research/futures_substrate_scaleout_v1/rerun/verdict_refresh.md` and
`docs/futures_substrate_scaleout/VERDICT_REFRESH.md`.

The refreshed boundary is `10 REJECT / 0 INCONCLUSIVE / 0 WATCH / 0
CANDIDATE_RESEARCH`. The six previously `INCONCLUSIVE` rerun studies are now
`REJECT` based on resolver-clean, value-free diagnostics evidence and retained
caveats, including the label diagnostics fail-closed
`label_coverage_missingness_gate`, duplicate within-family exposures, and BBO
proxy limits. The next planned phase is `FUTSUB-P30` - Artifact Audit and
Local-Only Value Verification.

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
production deployment, account operations, capital allocation, or autonomous
trading behavior.

Artifact discipline is unchanged: explicit staging only and value-free evidence
only. `runs/**` is local-only and never committed. Raw or canonical data,
feature or label values, provider responses, heavy artifacts, local databases,
logs, caches, secrets, and credentials are never committed.

The FUTSUB rerun gate does not authorize new AlphaSpecs, parameter tuning,
Strategy Reference validation, FactorLibrary ingestion, AlphaBook construction,
paper/live behavior, broker access, production deployment, profitability
claims, or tradability claims. Local feature/label values and registries remain
outside git under `ALPHA_DATA_ROOT`. Workflow 2 orchestration, validation
routing, review, staging, commit, PR, CI, merge, and done-check actions are
owned by Ralph.
