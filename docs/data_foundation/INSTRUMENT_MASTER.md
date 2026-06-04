# Futures Instrument Master

`DATA-P05` adds the root-level futures instrument master for the
`ALPHA_DATA_FOUNDATION_V1` data foundation.

The instrument master is local configuration and validation logic only. It does
not connect to IBKR, request contract details, select a current contract, assert
tradability, or certify execution sizing.

## Record

`InstrumentMasterRecord` lives in
`src/alpha_system/data/foundation/instruments.py`. It carries the campaign
required fields:

| Field | Meaning |
| --- | --- |
| `root_symbol` | Root futures symbol, such as `ES`. |
| `ib_symbol` | IBKR root symbol for the futures root. |
| `exchange` | Exchange identifier recorded for the root. |
| `currency` | Contract currency. |
| `asset_class` | Instrument class, currently `index_future` for these anchors. |
| `sec_type` | IBKR security type, `FUT` for these records. |
| `point_value` | Contract multiplier per index point, stored as `Decimal`. |
| `tick_size` | Minimum price increment, stored as `Decimal`. |
| `tick_value` | Exact `tick_size x point_value`, stored as `Decimal`. |
| `multiplier` | IBKR contract multiplier anchor, stored as `Decimal`. |
| `timezone` | Explicit IANA timezone, never implicit local time. |
| `session_template_id` | Identifier reference for DATA-P12 session templates. |
| `roll_policy_id` | Identifier reference for DATA-P13 roll policies. |
| `source` | Provenance identifier for the anchor values. |
| `source_retrieved_at` | Timezone-aware timestamp for when the anchor values were recorded. |

The record deliberately does not carry `trading_class`, `con_id`, contract month,
expiration, current-contract state, or tradability state. Those belong to later
dated-contract phases.

## Anchors

The six DATA-P05 anchors are encoded in
`configs/data/futures_instrument_master.json`. They are marked:

```text
anchor_status: to_be_verified_economic_anchor
certification_status: not_production_certified
source: dsrc_campaign_goal_contract_economics
```

| Root | Point value | Tick size | Tick value | Multiplier |
| --- | ---: | ---: | ---: | ---: |
| `ES` | `50` | `0.25` | `12.50` | `50` |
| `NQ` | `20` | `0.25` | `5.00` | `20` |
| `RTY` | `50` | `0.10` | `5.00` | `50` |
| `MES` | `5` | `0.25` | `1.25` | `5` |
| `MNQ` | `2` | `0.25` | `0.50` | `2` |
| `M2K` | `5` | `0.10` | `0.50` | `5` |

All six records use `America/Chicago`, `CME`, `USD`, `index_future`, and `FUT`.
The session and roll fields are identifier references only:
`session_cme_index_futures_eth` and `roll_cme_index_futures_quarterly`. The
actual session templates and roll policies are owned by later phases.

## Verification

Construction validates fail-closed:

- missing required fields from config mappings raise `DataFoundationValidationError`;
- `point_value`, `tick_size`, `tick_value`, and `multiplier` must be positive exact
  decimals;
- `tick_value` must equal `tick_size * point_value` exactly;
- `timezone` must be explicit and loadable as an IANA timezone;
- `source_retrieved_at` must be timezone-aware;
- config metadata must keep the to-be-verified, not-production-certified posture.

Unit tests under `tests/unit/data/test_instrument_master.py` assert the exact
economics for `ES`, `NQ`, `RTY`, `MES`, `MNQ`, and `M2K`, including one per-root
`tick_value == tick_size * point_value` check.

These checks verify internal consistency and provenance recording. They do not
turn the anchors into production-certified values, do not assert provider
availability, and do not imply alpha, profitability, tradability, paper trading,
live trading, broker readiness, account access, or order-routing scope.
