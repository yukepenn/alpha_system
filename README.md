# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing an
Alpha Research Platform under Frontier Harness Generic `0.3.0-rc1`.

The repository-level campaign pointer targets
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

Current campaign progress: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` is
active. This snapshot reflects the executor-complete state for `FUTSUB-P13`:
Cross-Market Alignment FeaturePack Scaleout, the eighth and final family in the
`feature_materialization` gate after base OHLCV (`FUTSUB-P06`), Session /
Calendar / Maintenance (`FUTSUB-P07`), VWAP / Session Auction (`FUTSUB-P08`),
Regime / Volatility / Compression (`FUTSUB-P09`), Liquidity Sweep / PA
Structure (`FUTSUB-P10`), Volume / Activity (`FUTSUB-P11`), and BBO Tradability
/ Top-Book (`FUTSUB-P12`). The P13 scaleout driver extension, strict
cross-market alignment test, config, and value-free full-window coverage preview
are in place; this executor sandbox could not write the local materialization
area, so Ralph owns any unsandboxed bounded-then-full execute rerun, validation
routing, staging, commit, review routing, PR, CI, merge, and done-check actions.

Active / next work: the `feature_integration` gate begins with `FUTSUB-P14`
FeaturePack Registry Integration, Coverage Audit, and Resolver Smoke, followed
by `FUTSUB-P15` Feature Coverage Matrix and Quality Report.

New durable surfaces in this `FUTSUB-P12` snapshot:

- Generic FeaturePack scaleout driver in `alpha_system.features.scaleout`
- CLI surface: `alpha scaleout feature-pack`
- Cross-Market Alignment scaleout config:
  `configs/features/scaleout/cross_market_alignment.json`
- Cross-Market Alignment value-free coverage evidence under
  `research/futures_substrate_scaleout_v1/feature_packs/cross_market_alignment/`
- Cross-market unit-executor dispatch in the scaleout driver, binding config
  labels to existing governed Cross-Market primitives only
- Strict cross-market intersection support preserving per-instrument
  `available_ts` with no cross-instrument forward-fill

`FUTSUB-P13` adds no raw/provider data reads, re-pulls, runtime diagnostics,
broker surfaces, live surfaces, paper-trading surfaces, order routing, or
deployment behavior. Feature values, registries, checkpoints, canonical data,
and registry backups remain local-only under `ALPHA_DATA_ROOT`; committed
evidence is value-free. Cross-market values must preserve per-instrument
`available_ts`, use exact event-time intersection, and forbid cross-instrument
forward-fill or missing-instrument imputation. No profitability or tradability
claim is made.

## Source Of Truth

- Root campaign pointer: `ACTIVE_CAMPAIGN.md`
- Campaign bundle:
  `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`
- Substrate scaleout docs: `docs/futures_substrate_scaleout/`
- Value-free research evidence root:
  `research/futures_substrate_scaleout_v1/`
- Commit-eligible handoffs:
  `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`

## Safety Boundaries

The project remains research-only and local-first. This campaign does not
authorize live trading, paper trading, broker operations, order routing,
production deployment, account operations, capital allocation, or autonomous
trading behavior.

Artifact discipline is unchanged: explicit staging only, value-free evidence
only, and runtime-tool-surface-only diagnostics. `runs/**` is local-only and
never committed. Raw or canonical data, feature or label values, provider
responses, heavy artifacts, local databases, roll-calendar data, logs, caches,
secrets, and credentials are never committed.

This campaign makes no profitability or tradability claim. Research outputs are
evidence for review only, and later phases must keep value data, local
registries, roll-calendar data, and run-local artifacts out of git.

## Validation Commands

Default local validation commands remain:

```bash
python tools/verify.py --smoke
python tools/verify.py --all
python tools/hooks/canary_runner.py
```

Workflow 2 orchestration, validation routing, review, staging, commit, PR, CI,
merge, and done-check actions are owned by Ralph.
