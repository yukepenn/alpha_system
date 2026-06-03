# Instrument Master

The instrument master is the durable metadata contract for stable instrument identity. It exists so multi-symbol research does not treat raw symbols as unique identities.

## Stable Identity

`instrument_id` is the internal identity used by universe configs, factors, labels, signals, portfolio targets, and experiment metadata. Raw symbols are metadata and may be reused across venues, currencies, or instrument lifecycles.

`src/alpha_system/core/instrument_master.py` defines:

- `InstrumentMasterRecord`,
- `InstrumentMasterCatalog`,
- `load_instrument_master`,
- required-field and active-date helpers.

`src/alpha_system/core/instruments.py` provides stable identity helpers and deterministic identity hashing.

## Required Fields

| Field | Preserved |
| --- | --- |
| `instrument_id` | yes |
| `symbol` | yes |
| `asset_class` | yes |
| `exchange` | yes |
| `currency` | yes |
| `timezone` | yes |
| `tick_size` | yes |
| `lot_size` | yes |
| `multiplier` | yes |
| `start_date` | yes |
| `end_date` | yes |
| `corporate_action_policy` | yes |
| `metadata` | yes |

Records validate non-empty identity fields, recognized asset classes, recognized corporate-action policies, positive tick/lot/multiplier values, valid IANA timezones, and active-date ordering.

## Symbol Resolution

`InstrumentMasterCatalog.resolve_symbol(...)` can resolve a symbol to `instrument_id` only when the match is unique. Exchange, currency, and active date can be supplied to disambiguate.

If multiple active records match the same symbol, resolution raises an error. This is intentional: callers must not promote symbol strings to identity.

## Universe Use

`UniverseSpec.from_mapping(..., instrument_master=catalog)` can fill universe member metadata from the master. The resulting member still stores `instrument_id`, asset class, exchange, currency, timezone, active dates, data version, and metadata used in deterministic universe hashing.

Instrument metadata such as currency, multiplier, tick size, lot size, and corporate-action policy is preserved for review and future portfolio/data handling. This phase does not implement FX conversion, corporate-action adjustment engines, or production multi-asset allocation.
