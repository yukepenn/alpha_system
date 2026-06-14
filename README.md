# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing
and validating offline research substrate under Frontier Harness Generic
`0.3.0-rc1`.

## Current Snapshot

The repository-level campaign pointer targets
`STRATEGY_SHAPED_RESEARCH_LANE_V0`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

`SSRL-P03` adds the first-light worked example for the strategy-shaped lane: a
range-contraction context plus a separate failed-high-breakout trigger declared
as `MechanismCard` -> `SetupSpec`, compiled through the unchanged SSRL-P02
conditional probe path, and stamped EXPLORATORY. The executor recorded an honest
`DATA_GAP` for the real row slice because matching local materialization
manifests were present but no sanctioned Parquet reader module was importable in
the sandbox. `SSRL-P03` also records the value-free de-stack read for
`vwap_session.factor_session_minute` through the unchanged single-factor
template. After this phase merges, campaign progress is `4/5` phases complete.
The next phase is `SSRL-P04` -- trusted-handoff scaffold, AI-researcher
happy-path, and `PA_GRAMMAR_SUBSTRATE_V1` naming docs, YELLOW.

Durable docs added by `SSRL-P00` are
`docs/strategy_shaped_lane/REUSE_MAP.md` and
`docs/strategy_shaped_lane/V0_SCOPE.md`. They lock reuse of the existing path
labels, path-outcome diagnostics, single-factor template, governance spec chain,
variant ledger, rejected-idea ledger, surrogate-FDR machinery, and power helpers.
Durable governance modules added by `SSRL-P01` are
`src/alpha_system/governance/mechanism_card.py` and
`src/alpha_system/governance/setup_spec.py`. Durable `SSRL-P02` surfaces are
`src/alpha_system/strategies/templates.py`,
`src/alpha_system/research/conditional_probe.py`,
`docs/strategy_shaped_lane/CONDITIONAL_PROBE.md`, and the
`forbidden_exploratory_promotion` canary. Durable `SSRL-P03` surfaces are
`src/alpha_system/research/first_light.py`,
`docs/strategy_shaped_lane/FIRST_LIGHT.md`, and the value-free evidence under
`research/strategy_shaped_lane_v0/`.

Safety boundaries are unchanged: EXPLORATORY output is not promotion evidence;
the trusted promotion path refuses EXPLORATORY-stamped artifacts; there is no
research-to-reference-sim bridge and no second PnL truth; the single-factor path
remains byte-unchanged and additive-only; outcomes come from path labels only;
there is no new runtime dependency, engine change, live trading, paper trading,
broker operation, order routing, deployment, new paid data, or promotion
eligibility.

The committed campaign pointer and README are snapshots. For authoritative
in-flight Workflow 2 state, use `python tools/frontier/status_doctor.py` or the
run-local state owned by Ralph.

## Source Of Truth

- Root campaign pointer: `ACTIVE_CAMPAIGN.md`
- Active campaign bundle: `campaigns/STRATEGY_SHAPED_RESEARCH_LANE_V0/`
- Campaign overview docs: `docs/strategy_shaped_lane/`
- Value-free research evidence root:
  `research/strategy_shaped_lane_v0/`
- Commit-eligible handoffs: `handoffs/STRATEGY_SHAPED_RESEARCH_LANE_V0/`
- Strategy and roadmap compass: `docs/OPERATING_COMPASS_V4.md`

## Safety Boundaries

The project remains research-only and local-first.
`STRATEGY_SHAPED_RESEARCH_LANE_V0` authorizes the governed EXPLORATORY
strategy-shaped research lane only. It does not authorize live trading, paper
trading, broker operations, order routing, deployment, account operations,
funding decisions, or autonomous trading behavior.

Artifact discipline is unchanged: explicit staging only and value-free evidence
only. `runs/**` is local-only and never committed. Raw or canonical data,
feature or label values, provider responses, heavy artifacts, local databases,
logs, caches, secrets, and credentials are never committed.

The strategy-shaped lane does not authorize FactorLibrary ingestion, AlphaBook
construction, paper/live behavior, broker access, deployment, profitability
claims, tradability claims, or execution-readiness claims.
`pyproject.toml` dependencies remain empty, so numpy, pandas, and polars stay
absent. Truth-chain invariants are preserved, including the sanctioned reference
engine as the only value/accounting truth. Workflow 2 orchestration, validation
routing, review, staging, commit, PR, CI, merge, and done-check actions are owned
by Ralph.
