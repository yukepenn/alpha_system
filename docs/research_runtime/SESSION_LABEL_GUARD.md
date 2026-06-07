# Session Label Guard

`session_label` is a point-in-time session-context field, not a training target.
The runtime resolver and no-lookahead audit therefore allow it only when the
feature input contract explicitly declares:

```python
input_metadata = {
    "field_roles": {
        "session_label": "SESSION_METADATA",
    }
}
```

The declaration alone is not enough. A field is exempt from label-token checks
only when all of these are true:

- The normalized field name is in the canonical point-in-time session metadata
  set: `session_label`, `session_segment`, `rth_flag`, `eth_flag`,
  `session_minute`, or `minutes_from_rth_open`.
- `FeatureSpec.inputs.input_metadata["field_roles"]` maps that field to
  `SESSION_METADATA`.
- The feature input still carries valid point-in-time availability metadata,
  including an `available_ts` that does not precede `event_ts` or exceed the
  decision timestamp.

Membership in the canonical session set is not a string whitelist. Missing role
metadata fails closed, so a bare field named `session_label` is still rejected as
label-like leakage.

True labels and forward-looking fields remain blocked regardless of any role
declaration. The forbidden set includes forward returns, triple-barrier targets,
label values/outcomes, label availability timestamps, horizon-end timestamps,
`y_true`, `target`, `fwd_ret*`, and final-session values such as
`final_session_high`, `final_session_low`, and `final_session_vwap`.

This guard fixes only the false-positive around declared point-in-time session
metadata. It does not weaken label leakage protection for target fields,
label handles, future outcomes, or intraday fields that require knowing the
completed session.
