# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing an
Alpha Research Platform under Frontier Harness Generic `0.3.0-rc1`.

The repository-level campaign pointer targets
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

Current campaign progress: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` is
active. This snapshot reflects the executor-complete state for `FUTSUB-P09`:
Regime / Volatility / Compression FeaturePack Scaleout within the
`feature_materialization` gate, following base OHLCV (`FUTSUB-P06`), Session /
Calendar / Maintenance (`FUTSUB-P07`), and VWAP / Session Auction
(`FUTSUB-P08`). Ralph owns validation routing, staging, commit, review routing,
PR, CI, merge, and done-check actions.

Active / next work: remaining `feature_materialization` FeaturePack phases,
beginning with `FUTSUB-P10` Liquidity Sweep / PA Structure FeaturePack
Scaleout, then `FUTSUB-P11` through `FUTSUB-P13`.

New durable surfaces in this `FUTSUB-P09` snapshot:

- Generic FeaturePack scaleout driver in `alpha_system.features.scaleout`
- CLI surface: `alpha scaleout feature-pack`
- Regime / volatility / compression scaleout config:
  `configs/features/scaleout/regime_volatility_compression.json`
- Regime / volatility / compression value-free coverage evidence under
  `research/futures_substrate_scaleout_v1/feature_packs/regime_volatility_compression/`
- Regime / volatility / compression unit-executor dispatch in the scaleout
  driver, plus symbol-scoped structure identity metadata for mixed
  OHLCV/structure FeaturePack bindings

`FUTSUB-P09` adds no raw/provider data reads, re-pulls, runtime diagnostics,
broker surfaces, live surfaces, paper-trading surfaces, order routing, or
deployment behavior. Feature values, registries, checkpoints, canonical data,
and registry backups remain local-only under `ALPHA_DATA_ROOT`; committed
evidence is value-free. Regime/volatility/compression features are research
substrate inputs only, not profitability or tradability evidence.

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
