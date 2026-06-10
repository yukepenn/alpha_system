# LCFP-P07 Parity / No-Lookahead / Guard Report

This value-free report summarizes the consolidated synthetic parity gate added
in LCFP-P07. It contains no per-row label values, raw data, canonical data,
registry output, Parquet, SQLite, logs, caches, or run-local artifacts.

## Scope

The P07 suite extends the shared parity harness and adds:

- `tests/unit/label_compute_fast_path/test_parity_matrix_suite.py`
- `tests/no_lookahead/label_fast_path/test_fast_label_available_ts.py`

The suite reuses the P03/P04/P05 synthetic fixtures and the reference label
families as the oracle. The fast path emits values under reference-derived
`label_version_id`s only.

## Family Coverage

| Family | Labels | Compared synthetic records | Null records | Flagged records | Max abs diff | Max median abs diff | Tolerance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| fixed_horizon | 14 | 8074 | 36 | 36 | 0 | 0 | exact |
| session_maintenance | 2 | 6 | 0 | 0 | 0 | 0 | exact |
| cost_adjusted | 2 | 10 | 6 | 6 | 0 | 0 | abs=1e-12, rel=1e-12 |
| path | 4 | 52 | 6 | 22 | 0 | 0 | abs=1e-12, rel=1e-12 |

Total compared synthetic records: 8142 across 22 label definitions.

## Dimension Matrix

| Family | Value | `label_available_ts` | Identity | Roll guard | Maintenance guard | Gap / missingness | Extra family dimensions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| fixed_horizon | exact | exact | exact `label_spec_id` + `label_version_id` | exact default DROP plus policy test | exact drop behavior | exact no-trade and BBO flags | `HorizonOverlapMetadata` preserved |
| session_maintenance | exact | exact | exact `label_spec_id` + `label_version_id` | exact drop behavior | exact close-out terminal behavior | exact session-gap omission | session-close / maintenance-flat terminal scope |
| cost_adjusted | tolerance below; observed diff 0 | exact | exact `label_spec_id` + `label_version_id` | not applicable to this family fixture | exact reference behavior for maintenance-crossing window | exact entry/terminal BBO gap flags | sanctioned `alpha_system.backtest.costs` primitives consumed read-only |
| path | tolerance below; observed diff 0 | exact | exact `label_spec_id` + `label_version_id` | exact default DROP plus policy test | exact drop behavior | exact no-trade source omission | same-bar policy variants and barrier-never-touched timeout |

## Required Case Set

The committed tests exercise these required synthetic cases:

| Required case | Coverage |
| --- | --- |
| Roll-crossing rows | fixed-horizon, session/maintenance, path default DROP; direct `RollCrossPolicy` DROP/TRUNCATE/FLAG/INVALID terminal-disposition parity against `evaluate_roll_guard` |
| Maintenance-crossing rows | fixed-horizon, session/maintenance terminal behavior, cost-adjusted reference behavior, path guard DROP |
| Session gaps | session-close omission and path no-trade source omission |
| Same-bar ambiguous bars | path `ambiguous`, `target_first`, and `stop_first` policy variants |
| BBO missing rows | fixed midprice source/terminal BBO flags and cost-adjusted entry/terminal BBO gap flags |
| Barrier never touched | path triple-barrier timeout / `horizon_no_barrier` |
| Horizon overlap / N_eff | fixed-horizon metadata version, label id, horizon minutes, raw row count, and effective sample count |
| Identity parity | every fast record uses the reference-derived `LabelContractSpec` `label_version_id` |
| No-lookahead | every emitted fast record has exact reference `label_available_ts`, never before `horizon_end_ts`; pack contracts remain labels-only over canonical input views |

## Tolerances

- Fixed-horizon and session/maintenance labels use exact value parity.
- Cost-adjusted labels use `abs=1e-12, rel=1e-12`. Justification: the reference
  path computes from `Decimal` BBO input-view rows while the fast path consumes
  a float shared panel before applying the sanctioned cost primitives. Observed
  max and median abs diff in the P07 synthetic suite are both 0.
- Path labels use `abs=1e-12, rel=1e-12`. Justification: the reference path
  family computes from `Decimal` OHLCV input-view rows while the fast path
  consumes a float shared panel. Boolean barrier outputs, timestamps, identity,
  event sets, quality flags, and guard dispositions remain exact. Observed max
  and median abs diff in the P07 synthetic suite are both 0.

No tolerance is used to hide a known divergence.

## Optional Dependencies

The consolidated fast-label parity and no-lookahead tests call
`pytest.importorskip("polars")` because the fast label materializer uses the
optional Polars dependency. In the research environment with Polars installed,
the suite executes real synthetic parity checks. In environments without Polars,
the tests skip visibly rather than falling back to a weakened assertion path.

## Residual Gaps

No residual gap remains for the required P07 synthetic parity dimensions. This
report does not claim benchmark readiness, production label materialization
acceptance, alpha value, profitability, tradability, execution quality, broker
integration, live trading, or paper trading. Benchmark/readiness remains
LCFP-P08 scope.
