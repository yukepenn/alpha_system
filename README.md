# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing
and validating offline research substrate under Frontier Harness Generic
`0.3.0-rc1`.

## Current Snapshot

The repository-level campaign pointer targets
`DIFFERENTIATED_KILLSHOT_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

`DK-P01` adds five zero-feed, known-ahead `SESSION_CALENDAR_ROLL` flags as
strictly additive members of the existing session family:
`is_opex_day_flag`, `is_quad_witch_day_flag`,
`is_month_end_session_flag`, `is_quarter_end_session_flag`, and
`in_roll_window_flag`. The flags are wired through the reference family and
fast-path pack, with APPROVED FeatureRequest declarations and provenance under
`research/differentiated_substrate_v1/feature_requests/`. Campaign progress is
`2/6` planned phases complete after merge. Next is `DK-P02`, Track A StudySpecs
plus declared-conditioning-factor admission and surrogate-FDR zero-pass.

Safety boundaries are unchanged: this is research-only; there is no real-data
metric in DK-P01, no alpha/profitability/tradability claim, no second
value/accounting truth, no research-to-reference-sim bridge, no single-factor
template edit, no value-engine edit, no FUTSUB/core-pilot artifact edit, no new
dependency, no new paid data, no live trading, no paper trading, no broker
operation, no order routing, and no deployment. `fomc`, `cpi`, and the
overnight family remain deferred.

The committed campaign pointer and README are snapshots. For authoritative
in-flight Workflow 2 state, use `python tools/frontier/status_doctor.py` or the
run-local state owned by Ralph.

## Source Of Truth

- Root campaign pointer: `ACTIVE_CAMPAIGN.md`
- Active campaign bundle: `campaigns/DIFFERENTIATED_KILLSHOT_V1/`
- Campaign overview docs: `docs/differentiated_killshot_v1/`
- Value-free research prep root: `research/differentiated_substrate_v1/`
- Commit-eligible handoffs: `handoffs/DIFFERENTIATED_KILLSHOT_V1/`
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
