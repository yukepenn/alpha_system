# Data Source Profile Contract

`DataSourceProfile` is the data-foundation record that describes a provider and the
usage modes the repository may or may not use for that provider. It is a local
policy object only. It does not connect to a provider, read credentials, pull data,
write data, or create any broker, account, paper, live, order, or execution surface.

## Required Fields

| Field | Meaning |
| --- | --- |
| `source_id` | Stable source identifier. DATA-P02 requires the `dsrc_` prefix. |
| `provider_name` | Human-readable provider name. |
| `provider_type` | Provider category, such as `historical_data_provider`. |
| `allowed_modes` | Non-empty set of modes this data source may be used for. |
| `forbidden_modes` | Non-empty set of modes this data source must not be used for. |
| `requires_authorization` | Boolean marker for explicit authorization before provider use. |
| `market_data_permissions_note` | Factual note about provider permission or availability limits. |
| `created_at` | Timezone-aware creation timestamp for the policy record. |

Construction validates fail-closed. Missing fields, empty mode sets, invalid strings,
non-boolean authorization flags, naive timestamps, overlapping allowed/forbidden
modes, or allowed modes that imply broker, execution, order, account, paper, live,
real-time, or data-completeness capability raise hard validation errors.

## IBKR Profile

DATA-P02 defines IBKR only as a read-only historical data source profile:

```text
source_id: dsrc_ibkr_historical
provider_type: historical_data_provider
allowed_modes:
  - historical_data
  - read_only_historical
forbidden_modes include:
  - broker
  - broker_readiness
  - execution
  - execution_permission
  - orders
  - order_routing
  - account
  - account_access
  - positions
  - paper_trading
  - live_trading
  - real_time_market_data
  - data_completeness_claim
requires_authorization: true
```

The allowed and forbidden mode sets must remain disjoint. Adding an order,
account, paper, live, real-time, execution, broker, or completeness mode to
`allowed_modes` is invalid.

## No-Implication Rules

`DataSourceProfile` records do not imply:

- broker readiness;
- execution permission;
- account access;
- order routing;
- paper or live operation;
- real-time feed availability;
- data coverage or data completeness.

Provider permissions and availability can limit historical data. A source profile
only states the local usage boundary for a provider; later phases own connection
profiles, request manifests, pacing, local raw storage, coverage, and quality checks.
