# Track-B Pooled-Hypothesis Pre-Registration Template

This template is for FUTSUB kill-shot coordination. It is not a registration,
does not inspect Track A metrics, and must be filled and registered before any
Track A metric marker exists.

Live schema: `alpha_system.governance.pooled_hypothesis.PooledHypothesisRecord`.
A filled payload must map field-for-field to that schema and then be registered
with `alpha governance register-pooled-hypothesis`.

## Ordering Rule

1. Confirm the Track A metrics-started marker does not exist.
2. Fill the payload fields below.
3. Generate `pooled_hypothesis_id` from the final payload.
4. Register with a metrics-started marker path. If the marker exists, new
   registration fails closed.
5. Only after at least one `cross_symbol` and one `cross_horizon` record are
   registered and `track_b_minimum_satisfied()` returns true may Track A metric
   inspection begin.

## Schema-Aligned Payload

```json
{
  "pooled_hypothesis_id": "GENERATE_WITH_generate_pooled_hypothesis_id_AFTER_FILLING_FIELDS",
  "mechanism_rationale": "REQUIRED_NON_VAGUE_MECHANISM_RATIONALE",
  "pool_kind": "cross_symbol_OR_cross_horizon",
  "members": [
    "FIXED_STUDY_OR_COMPONENT_REF_1",
    "FIXED_STUDY_OR_COMPONENT_REF_2"
  ],
  "aggregation_rule": "equal_weight_mean",
  "horizons": [
    "5m"
  ],
  "sessions": [
    "rth"
  ],
  "symbols": [
    "ES",
    "NQ",
    "RTY"
  ],
  "registered_at": "UTC_TIMESTAMP_BEFORE_TRACK_A_METRICS",
  "registered_before_metrics": true,
  "variant_ledger_record": {
    "variant_id": "POOLED_VARIANT_ID",
    "alpha_spec_id": "LINKED_ALPHA_SPEC_ID",
    "study_spec_id": "ANCHOR_STUDY_SPEC_ID_OR_MEMBER_BASE",
    "family_id": "POOLED_TRACK_B_FAMILY_ID",
    "attempt_count": 1,
    "trial_ids": [
      "PRE_METRIC_POOLED_REGISTRATION_TRIAL_REF"
    ],
    "status": "PLANNED",
    "created_at": "MATCH_REGISTERED_AT"
  }
}
```

## Field Mapping

| Template field | Live schema field | Fill rule |
|---|---|---|
| `pooled_hypothesis_id` | `pooled_hypothesis_id` | Generate after every other field is final. Edits create a new hypothesis. |
| `mechanism_rationale` | `mechanism_rationale` | Required non-vague mechanism text. Do not mention observed Track A metrics. |
| `pool_kind` | `pool_kind` | Closed enum: `cross_symbol`, `cross_horizon`, or `cross_family`; FUTSUB minimum requires at least `cross_symbol` and `cross_horizon`. |
| `members` | `members` | Fixed immutable member list. No post-hoc add/drop/reweight. |
| `aggregation_rule` | `aggregation_rule` | Closed enum; current allowed value is `equal_weight_mean`. |
| `horizons` | `horizons` | Fixed horizon set for the hypothesis. |
| `sessions` | `sessions` | Fixed session set. |
| `symbols` | `symbols` | Fixed symbol set. |
| `registered_at` | `registered_at` | UTC timestamp strictly before Track A metrics start. |
| `registered_before_metrics` | `registered_before_metrics` | Must be true only after checking the metrics marker is absent. |
| `variant_ledger_record` | `variant_ledger_record` | Exactly one linked `VariantLedgerRecord` with `status=PLANNED`, `created_at=registered_at`, and an anchor member. |

## Minimum Check

The kill-shot minimum is:

```python
from alpha_system.governance.pooled_hypothesis import track_b_minimum_satisfied

assert track_b_minimum_satisfied(registered_records, kill_shot_study_set)
```

The minimum is not satisfied by draft templates. Existing draft examples live at
`research/discovery_rigor_floor_v1/track_b/CROSS_SYMBOL_POOLED_HYPOTHESIS_TEMPLATE.json`
and
`research/discovery_rigor_floor_v1/track_b/CROSS_HORIZON_POOLED_HYPOTHESIS_TEMPLATE.json`.

No pooled result rewrites Track A. Track A and Track B are reported separately,
and this template makes no alpha, profitability, tradability, or production
claim.
