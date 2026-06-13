# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing
and validating offline research substrate under Frontier Harness Generic
`0.3.0-rc1`.

## Current Snapshot

The repository-level campaign pointer targets
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

Current campaign progress is in the `rerun` gate. `FUTSUB-P27` re-locked the
Core Pilot StudySpecs against the full substrate, and the `FUTSUB-P28` repair
attempt now has value-free rerun evidence under
`research/futures_substrate_scaleout_v1/rerun/` plus the docs page
`docs/futures_substrate_scaleout/CORE_PILOT_RERUN.md`.

The P28 repair re-executed all six prior-INCONCLUSIVE V2 StudySpecs under the
research interpreter with `ALPHA_DATA_ROOT` set. All feature and label locks
resolved through the local runtime resolver, current registered Parquet value
stores loaded, and runtime factor diagnostics completed over real in-memory
observation samples with N_eff and purged/embargoed walk-forward context. This
is evidence only: label diagnostics still fail closed at
`label_coverage_missingness_gate`, and Ralph owns validation routing, review,
staging, commit, PR/CI, merge, and done-check handling. The next planned phase
remains `FUTSUB-P29` - Honest Verdict Refresh and Scaleout Evidence Summary -
after Ralph/review handling.

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

FUTSUB-P28 does not authorize new AlphaSpecs, parameter tuning, verdict refresh,
promotion, Strategy Reference validation, AlphaBook construction, paper/live
behavior, broker access, production deployment, or any profitability or
tradability claim. Local feature/label values and registries remain outside git
under `ALPHA_DATA_ROOT`. Workflow 2 orchestration, validation routing, review,
staging, commit, PR, CI, merge, and done-check actions are owned by Ralph.
