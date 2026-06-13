# Multi-Horizon Mining Requirement Handoff

Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Downstream campaign: `ALPHA_FUTURES_MULTI_HORIZON_ALPHA_MINING_V1`  
Prepared in: `FUTSUB-P32`  
Artifact class: value-free requirement handoff

This handoff defines the substrate and guard requirements that a future
multi-horizon mining campaign may consume from FUTSUB. It does not start mining,
does not create AlphaSpecs or StudySpecs, does not tune parameters, does not run
diagnostics, and does not change any verdict.

## Consumable Substrate Base

FUTSUB exposes a registry-resolved, value-local substrate for ES, NQ, and RTY.
The commit-eligible evidence is value-free and describes the local substrate by
ids, counts, coverage classes, guard counts, and matrix paths.

Current consumable base:

| Surface | Consumable scope | Required context |
| --- | --- | --- |
| DatasetVersions | ES/NQ/RTY, OHLCV-1m, OHLCV dense grid, BBO-1m, accepted years 2019-2026 | 2018 is expected-excluded; 2019 and 2026 warning metadata must travel with every downstream run. |
| Feature families | `base_ohlcv`, `session_calendar_maintenance`, `vwap_session_auction`, `regime_volatility_compression`, `liquidity_sweep_pa_structure`, `volume_activity`, `bbo_tradability_top_book`, `cross_market_alignment` | P15 records 216 family/symbol/year cells: 144 clean, 48 warned, 24 expected-excluded, 0 unexpected gaps. |
| Label surfaces | fixed-base 1m/3m/5m/10m/15m/30m; fixed-extended 60m/120m/240m; session-close; maintenance-flat; cost-adjusted; path | P23 records 1368 active locks and 0 unexpected accepted-window gaps. |
| Guarding | roll-splice and daily maintenance / trade-date break guards | P21 matrices record explicit dropped or bounded windows and zero silently measured crossings. |
| Walk-forward | purged / embargoed runtime split metadata | P24 exposes `STRUCTURAL`, `MEDIUM`, and `FAST` protocol hooks as routing metadata only. |
| N_eff | overlap-aware reporting metadata | P25 requires explicit horizon/cadence/discount metadata and fails closed when it is absent or understated. |
| BBO | top-book proxy quality matrix | BBO is a time-sampled and forward-filled proxy only; not execution truth, passive-fill evidence, queue evidence, or impact evidence. |
| Cross-market | strict-intersection aligned panel matrix | No `asof` aggregate is substrate truth; contributor gaps are availability context, not filled values. |

## Mining Campaign Entry Requirements

Before any mining run starts, the downstream campaign must pre-register:

1. The StudySpec population to be considered.
2. Family budgets and variant budgets.
3. Symbols, years, horizons, session segments, cost surfaces, and BBO /
   cross-market quality filters.
4. DatasetVersion acceptance states and expected exclusions.
5. Feature and label lock-resolution method using exact ids only.
6. Split protocol, purge gap, embargo gap, and half-life protocol.
7. N_eff handling for every overlapping horizon.
8. Roll-splice and maintenance-crossing policy handling.
9. Duplicate-exposure grouping and pooled-hypothesis handling.
10. Stopping rules and reviewer gates.

The mining campaign must be bounded and evidence-selected. It must not become an
open-ended feature zoo, broad parameter search, manual prior screen, or
post-hoc survivor hunt.

## Required Runtime And Resolver Discipline

Downstream mining must consume values only through the sanctioned local
registry and runtime surfaces. Required rules:

- Resolve features by exact `feature_version_id`; no family-name fallback.
- Resolve labels by exact `label_version_id`; no horizon-name fallback.
- Require the DatasetVersion id, partition id, value-store metadata,
  content-hash provenance, and availability timestamps expected by the lock.
- Preserve `available_ts <= decision_ts < label_available_ts`.
- Treat resolver gaps as blocked inputs, not as optional omissions.
- Preserve lifecycle state; deprecated ids must fail closed.
- Do not read raw provider payloads or hand-read local Parquet payloads from
  committed code or artifacts.
- Do not commit feature values, label values, raw/canonical data, local
  registries, SQLite files, Parquet payloads, heavy artifacts, logs, or
  run-local artifacts.

## Required Matrix Inputs

Mining should consume these matrices as availability and quality gates, not as
signal evidence:

- `research/futures_substrate_scaleout_v1/matrices/feature_family_coverage.md`
- `research/futures_substrate_scaleout_v1/matrices/label_family_coverage.md`
- `research/futures_substrate_scaleout_v1/matrices/symbol_horizon_coverage.md`
- `research/futures_substrate_scaleout_v1/matrices/session_horizon_coverage.md`
- `research/futures_substrate_scaleout_v1/matrices/bbo_quality.md`
- `research/futures_substrate_scaleout_v1/matrices/cross_market_alignment.md`
- `research/futures_substrate_scaleout_v1/matrices/roll_window_coverage.md`
- `research/futures_substrate_scaleout_v1/matrices/maintenance_crossing_invalidation.md`

Mandatory interpretations:

- `EE` cells are expected exclusions and must not be backfilled by mining.
- `W` cells are usable only when warning context is preserved.
- `P` cells are coverage facts, not statements that every row is non-null or
  independently sampled.
- Guard-dropped windows are expected guard behavior, not missing alpha evidence.
- BBO quality regimes and spread buckets are diagnostic quality context only.
- Cross-market contributor gaps are availability context and must not be
  smoothed into complete coverage.

## Horizon And Label Requirements

The starting primary research band remains 5m through 30m. Diagnostic 1m/3m,
extended 60m/120m/240m, session-close, maintenance-flat, cost-adjusted, and
path labels may be used only under their documented coverage, guard, and N_eff
contracts.

For every horizon:

- attach or reference the applicable N_eff metadata;
- preserve rows-versus-effective-samples distinction;
- apply purge and embargo metadata;
- carry roll and maintenance guard provenance;
- carry cost-model and BBO-proxy assumptions for cost-adjusted labels;
- record whether the label is fixed-horizon, terminal-event, cost-adjusted, or
  path-dependent;
- avoid treating overlapping rows as independent evidence.

Extended horizons require stronger discounting than shorter horizons at the
same cadence. Session-close and maintenance-flat labels are terminal-event
surfaces and must not be forced into a fixed-forward-horizon interpretation.

## BBO And Cross-Market Requirements

BBO-dependent mining must:

- state that BBO-1m is a sampled and forward-filled top-book proxy;
- preserve the P26 note that accepted BBO rows collapsed to `ETH_NON_RTH` in the
  materialized session split;
- treat `spread_ticks` availability as unavailable in the P26 local pass unless
  a later substrate owner repairs it;
- include worst-cell BBO quality context in diagnostics gating;
- make no passive-fill, queue, impact, execution-quality, or tradability claim.

Cross-market mining must:

- require `alignment_policy=strict_intersection` for FUTSUB substrate inputs;
- reject `asof`-aligned aggregates as substrate truth for this campaign;
- preserve per-instrument availability semantics;
- carry contributor-gap counts as availability context;
- make no relationship-strength, predictive, profitability, or tradability
  claim from the matrix alone.

## Required Mining Outputs

The downstream campaign should produce, at minimum:

- a pre-registered mining population declaration;
- a substrate input manifest listing every consumed matrix, DatasetVersion,
  FeatureVersion, LabelVersion, StudySpec, and warning/exclusion state;
- a variant-budget and duplicate-exposure ledger;
- generated StudySpecs only after scope and budgets are fixed;
- runtime diagnostics summaries with walk-forward and N_eff context;
- a rejected-config / rejected-idea ledger for blocked, duplicate, weak, or
  invalid studies;
- a no-claims interpretation section for every report;
- reviewer-facing evidence bundles that cite value-free paths and do not embed
  values;
- a handoff to Validation Governance before any survivor state can be treated
  as promotion-eligible;
- a handoff to FactorLibrary only for reviewed `WATCH` or
  `CANDIDATE_RESEARCH` survivors, if any.

## Current FUTSUB Verdict Context

`FUTSUB-P29` refreshes the current rerun boundary to `10 REJECT / 0
INCONCLUSIVE / 0 WATCH / 0 CANDIDATE_RESEARCH`. Multi-horizon mining should
treat that as prior evidence and duplicate-exposure context, not as a seed list
for promotion and not as a reason to bypass pre-registration.

The six rerun StudySpecs became resolver-clean and then refreshed to `REJECT`
under P29. Their residual caveats include fail-closed label diagnostics,
near-duplicate liquidity/PA and VWAP/session exposures, BBO proxy limits, and
first-order N_eff metadata that is not session-clustered or autocorrelation
adjusted.

## Explicit Non-Claims

This handoff makes no alpha, profitability, robustness, tradability,
production, paper/live, broker, order-routing, deployment, or
capital-allocation claim. It starts no mining and creates no new AlphaSpec,
StudySpec, factor, signal, strategy, or portfolio object.

