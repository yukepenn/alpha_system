# End-to-End Feature/Label Dry Run

FLF-P30 exercises the Feature/Label substrate end to end in a local-only dry run.
The CI-safe path uses a tiny synthetic accepted DatasetVersion fixture by
default. Operators may repeat the same substrate path against one already-local,
accepted DatasetVersion slice when `$ALPHA_DATA_ROOT` and the local registry are
available.

This summary is row-free. It contains no raw rows, canonical rows, feature
values, label values, provider responses, registry database contents, or local
artifact paths.

## Path Exercised

The integration test under `tests/integration/feature_label/` drives:

```text
FeatureRequest (freq_, APPROVED)
  -> FeatureSpec / FeatureVersion with available_ts derivation
  -> feature materialization under temporary ALPHA_DATA_ROOT
  -> FeatureRegistry metadata plus feature quality and coverage reports
  -> LabelSpec (lspec_) / LabelVersion with label_available_ts policy
  -> label materialization under temporary ALPHA_DATA_ROOT
  -> label leakage and availability audit
  -> StudySpec Input Pack validation
  -> FLF-P28 CLI dry-run surfaces
```

The CLI portion uses dry-run planning/reporting surfaces only:

- `alpha feature materialize --dry-run`
- `alpha label materialize --dry-run`
- `alpha label input-pack`
- `alpha label leakage-audit`

## Invariants Checked

- Dataset consumption resolves through the accepted DatasetVersion registry path
  and canonical mapping loaders; no raw provider files or external provider
  calls are used.
- Feature requests are approved through the governance gate, and duplicate
  exposure evidence is consumed from governance.
- Every produced feature value carries timezone-aware `available_ts` at or after
  `event_ts`.
- Every produced label value carries timezone-aware `label_available_ts` at or
  after `horizon_end_ts`.
- The label leakage guard and leakage audit pass for safe live feature
  references; no label-as-feature path is admitted.
- BBO missingness and quarantine are surfaced through `missing_bbo` and
  `bbo_quarantined`; quote-derived values on those rows are not forward-filled.
- The synthetic dense-grid no-trade row carries `has_trade=false`,
  `synthetic=true`, `quality_flags=["no_trade"]`, and zero volume, and it is
  not treated as a trade bar.
- Feature and label outputs are written only under a temporary
  `ALPHA_DATA_ROOT`; nothing is written into the repository tree.
- The StudySpec Input Pack validates against existing `FeatureRequest`,
  `LabelSpec`, `AlphaSpec`, and `StudySpec` contracts without changing the
  StudySpec schema.
- Prohibited MVP states such as `ALPHA_VALIDATED`, `STRATEGY_READY`,
  `LIVE_READY`, `PROFITABLE`, `TRADABLE`, and `PRODUCTION_READY` remain outside
  the feature and label registry lifecycle states.

The feature coverage report is intentionally consumed in the test. For scalar
feature values the existing coverage reporter cannot infer a session identifier
from the value payload, so it records the fail-closed
`SESSION_COVERAGE_UNRESOLVED` coverage finding. The dry run treats that as a
documented coverage-report warning, not as alpha evidence or production
readiness.

## Operator Command

CI-safe synthetic dry run:

```bash
python -m pytest tests/integration/feature_label -q
```

Optional local accepted-DatasetVersion dry run when the local registry and data
slice are already present:

```bash
export ALPHA_DATA_ROOT=~/alpha_data/alpha_system
alpha feature dry-run --dataset dsv_databento_ohlcv_<hex> --small --local-only
```

If `$ALPHA_DATA_ROOT` or the local accepted DatasetVersion registry is absent,
record `PASS_WITH_WARNINGS` and use the synthetic fixture path above. Absence of
local data on a CI runner is expected and does not permit provider calls, raw
provider access, or committed values.

## Boundary

This dry run demonstrates substrate wiring only. It makes no alpha,
profitability, tradability, strategy, backtest, portfolio, broker, paper, live,
order-routing, account, deployment, or production-readiness claim.
