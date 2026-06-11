# FUTSUB-P23 Symbol-Horizon Coverage Matrix

Value-free symbol x horizon rollup for the current label substrate. This report
contains only registry statuses, lock counts, and coverage metadata.

## Inputs And Legend

Input evidence and status codes match
`research/futures_substrate_scaleout_v1/matrices/label_family_coverage.md`.
`Required labels/year` counts all applicable active label versions for a
symbol/horizon/year cell after family rollup:

- `1m` and `3m`: fixed-base plus two cost-adjusted variants = `3`.
- `5m` through `30m`: fixed-base, two cost-adjusted variants, and four path
  variants = `7`.
- `60m` through `240m`: fixed-extended, two cost-adjusted variants, and four
  path variants = `7`.
- `session_close` and `maintenance_flat`: close-out label only = `1`.

All accepted-window cells resolve. `2018` remains the only expected exclusion;
`2019` and `2026` resolve with warning metadata.

## Matrix

| Symbol | Horizon | Families present | Required labels/year | Active locks 2019-2026 | 2018 | 2019 | 2020-2025 | 2026 | Notes |
| --- | --- | --- | ---: | ---: | --- | --- | --- | --- | --- |
| `ES` | `1m` | `fixed_base`, `cost_adjusted` | 3 | 24 | `EE` | `W` | `P` | `W` | all applicable family cells resolve |
| `ES` | `3m` | `fixed_base`, `cost_adjusted` | 3 | 24 | `EE` | `W` | `P` | `W` | all applicable family cells resolve |
| `ES` | `5m` | `fixed_base`, `cost_adjusted`, `path` | 7 | 56 | `EE` | `W` | `P` | `W` | all applicable family cells resolve |
| `ES` | `10m` | `fixed_base`, `cost_adjusted`, `path` | 7 | 56 | `EE` | `W` | `P` | `W` | all applicable family cells resolve |
| `ES` | `15m` | `fixed_base`, `cost_adjusted`, `path` | 7 | 56 | `EE` | `W` | `P` | `W` | all applicable family cells resolve |
| `ES` | `30m` | `fixed_base`, `cost_adjusted`, `path` | 7 | 56 | `EE` | `W` | `P` | `W` | all applicable family cells resolve |
| `ES` | `60m` | `fixed_extended`, `cost_adjusted`, `path` | 7 | 56 | `EE` | `W` | `P` | `W` | all applicable family cells resolve |
| `ES` | `120m` | `fixed_extended`, `cost_adjusted`, `path` | 7 | 56 | `EE` | `W` | `P` | `W` | all applicable family cells resolve |
| `ES` | `240m` | `fixed_extended`, `cost_adjusted`, `path` | 7 | 56 | `EE` | `W` | `P` | `W` | all applicable family cells resolve |
| `ES` | `session_close` | `close_out` | 1 | 8 | `EE` | `W` | `P` | `W` | close-out terminal label only |
| `ES` | `maintenance_flat` | `close_out` | 1 | 8 | `EE` | `W` | `P` | `W` | close-out terminal label only |
| `NQ` | `1m` | `fixed_base`, `cost_adjusted` | 3 | 24 | `EE` | `W` | `P` | `W` | all applicable family cells resolve |
| `NQ` | `3m` | `fixed_base`, `cost_adjusted` | 3 | 24 | `EE` | `W` | `P` | `W` | all applicable family cells resolve |
| `NQ` | `5m` | `fixed_base`, `cost_adjusted`, `path` | 7 | 56 | `EE` | `W` | `P` | `W` | all applicable family cells resolve |
| `NQ` | `10m` | `fixed_base`, `cost_adjusted`, `path` | 7 | 56 | `EE` | `W` | `P` | `W` | all applicable family cells resolve |
| `NQ` | `15m` | `fixed_base`, `cost_adjusted`, `path` | 7 | 56 | `EE` | `W` | `P` | `W` | all applicable family cells resolve |
| `NQ` | `30m` | `fixed_base`, `cost_adjusted`, `path` | 7 | 56 | `EE` | `W` | `P` | `W` | all applicable family cells resolve |
| `NQ` | `60m` | `fixed_extended`, `cost_adjusted`, `path` | 7 | 56 | `EE` | `W` | `P` | `W` | all applicable family cells resolve |
| `NQ` | `120m` | `fixed_extended`, `cost_adjusted`, `path` | 7 | 56 | `EE` | `W` | `P` | `W` | all applicable family cells resolve |
| `NQ` | `240m` | `fixed_extended`, `cost_adjusted`, `path` | 7 | 56 | `EE` | `W` | `P` | `W` | all applicable family cells resolve |
| `NQ` | `session_close` | `close_out` | 1 | 8 | `EE` | `W` | `P` | `W` | close-out terminal label only |
| `NQ` | `maintenance_flat` | `close_out` | 1 | 8 | `EE` | `W` | `P` | `W` | close-out terminal label only |
| `RTY` | `1m` | `fixed_base`, `cost_adjusted` | 3 | 24 | `EE` | `W` | `P` | `W` | all applicable family cells resolve |
| `RTY` | `3m` | `fixed_base`, `cost_adjusted` | 3 | 24 | `EE` | `W` | `P` | `W` | all applicable family cells resolve |
| `RTY` | `5m` | `fixed_base`, `cost_adjusted`, `path` | 7 | 56 | `EE` | `W` | `P` | `W` | all applicable family cells resolve |
| `RTY` | `10m` | `fixed_base`, `cost_adjusted`, `path` | 7 | 56 | `EE` | `W` | `P` | `W` | all applicable family cells resolve |
| `RTY` | `15m` | `fixed_base`, `cost_adjusted`, `path` | 7 | 56 | `EE` | `W` | `P` | `W` | all applicable family cells resolve |
| `RTY` | `30m` | `fixed_base`, `cost_adjusted`, `path` | 7 | 56 | `EE` | `W` | `P` | `W` | all applicable family cells resolve |
| `RTY` | `60m` | `fixed_extended`, `cost_adjusted`, `path` | 7 | 56 | `EE` | `W` | `P` | `W` | all applicable family cells resolve |
| `RTY` | `120m` | `fixed_extended`, `cost_adjusted`, `path` | 7 | 56 | `EE` | `W` | `P` | `W` | all applicable family cells resolve |
| `RTY` | `240m` | `fixed_extended`, `cost_adjusted`, `path` | 7 | 56 | `EE` | `W` | `P` | `W` | all applicable family cells resolve |
| `RTY` | `session_close` | `close_out` | 1 | 8 | `EE` | `W` | `P` | `W` | close-out terminal label only |
| `RTY` | `maintenance_flat` | `close_out` | 1 | 8 | `EE` | `W` | `P` | `W` | close-out terminal label only |

## Gap List

- Expected exclusions: all symbol/horizon rows are `EE` for 2018 because the
  required DatasetVersion is `BLOCKED`.
- Warned but present: all 2019 and 2026 symbol/horizon rows are `W`.
- Unexpected gaps: none.
