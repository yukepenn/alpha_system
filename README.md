# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing
and validating offline research substrate under Frontier Harness Generic
`0.3.0-rc1`.

## Current Snapshot

The repository-level campaign pointer targets
`STRATEGY_SHAPED_RESEARCH_LANE_V0`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

`SSRL-P00` is the documentation-only bootstrap phase. After this phase merges,
campaign progress is `1/5` phases complete. The active / next phase is
`SSRL-P01` -- SetupSpec + MechanismCard contracts, YELLOW.

Durable docs added by `SSRL-P00` are
`docs/strategy_shaped_lane/REUSE_MAP.md` and
`docs/strategy_shaped_lane/V0_SCOPE.md`. They lock reuse of the existing path
labels, path-outcome diagnostics, single-factor template, governance spec chain,
variant ledger, rejected-idea ledger, surrogate-FDR machinery, and power helpers.

Safety boundaries are unchanged: EXPLORATORY output is not promotion evidence;
there is no research-to-reference-sim bridge and no second PnL truth; the
single-factor path remains additive-only and unchanged; V0 is bounded and is not
a grid; there is no live trading, paper trading, broker operation, order routing,
deployment, new paid data, or new runtime dependency.

The committed campaign pointer and README are snapshots. For authoritative
in-flight Workflow 2 state, use `python tools/frontier/status_doctor.py` or the
run-local state owned by Ralph.

## Source Of Truth

- Root campaign pointer: `ACTIVE_CAMPAIGN.md`
- Active campaign bundle: `campaigns/SHIP_REFIT_V1/`
- Campaign overview docs: `docs/ship_refit_v1/`
- Value-free research evidence root:
  `research/ship_refit_v1/`
- Commit-eligible handoffs: `handoffs/SHIP_REFIT_V1/`
- Strategy and roadmap compass: `docs/OPERATING_COMPASS_V4.md`

## Safety Boundaries

The project remains research-only and local-first. `SHIP_REFIT_V1` authorizes
harness and diagnostics hardening only. It does not authorize live trading,
paper trading, broker operations, order routing, deployment, account operations,
funding decisions, or autonomous trading behavior.

Artifact discipline is unchanged: explicit staging only and value-free evidence
only. `runs/**` is local-only and never committed. Raw or canonical data,
feature or label values, provider responses, heavy artifacts, local databases,
logs, caches, secrets, and credentials are never committed.

The refit does not authorize new alpha ideation, FactorLibrary ingestion,
AlphaBook construction, paper/live behavior, broker access, deployment,
profitability claims, tradability claims, or execution-readiness claims.
`pyproject.toml` dependencies remain empty, so numpy, pandas, and polars stay
absent. Truth-chain invariants are preserved, including the sanctioned reference
engine as the only value/accounting truth. Workflow 2 orchestration, validation
routing, review, staging, commit, PR, CI, merge, and done-check actions are owned
by Ralph.
