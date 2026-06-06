# Runtime Report Card: Reference Handoff

Compact summaries and references only.

## Status
| Field | Value |
| --- | --- |
| Status | {{ decision_state }} |
| Next required gate | {{ next_required_gate }} |
| Data scope | summaries, version ids, statuses, reasons, and refs |

## Labels
| Field | Value |
| --- | --- |
| Posture | descriptive only |
| Reference label | handoff package - not Reference validation |

## References
| Field | Value |
| --- | --- |
| run id | {{ run_id }} |
| handoff id | {{ handoff_id }} |
| handoff hash | {{ handoff_hash }} |
| study spec id | {{ study_spec_id }} |

## Handoff Refs
| Field | Value |
| --- | --- |
| evidence draft id | {{ evidence_draft_id }} |
| evidence draft hash | {{ evidence_draft_hash }} |
| runtime artifact manifest id | {{ artifact_manifest_id }} |
| runtime artifact manifest hash | {{ artifact_manifest_hash }} |

Reference handoff is a package only; it is not Reference validation.

## Cost Profiles
| Field | Value |
| --- | --- |
| base cost multiplier | {{ base_cost_multiplier }} |
| base slippage multiplier | {{ base_slippage_multiplier }} |
| double_cost cost multiplier | {{ double_cost_multiplier }} |
| double_cost slippage multiplier | {{ double_cost_slippage_multiplier }} |
