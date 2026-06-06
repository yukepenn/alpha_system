# Runtime Report Card: {{ diagnostics_family }} Diagnostics

Compact summaries and references only.

## Status
| Field | Value |
| --- | --- |
| Status | {{ status }} |
| Next required gate | {{ next_required_gate }} |
| Data scope | summaries, version ids, statuses, reasons, and refs |

## References
| Field | Value |
| --- | --- |
| report id | {{ report_id }} |
| report hash | {{ report_hash }} |
| diagnostics run spec id | {{ diagnostics_run_spec_id }} |
| dataset version id | {{ dataset_version_id }} |

## Coverage Summary
| Field | Value |
| --- | --- |
| sample count | {{ sample_count }} |
| coverage ratio | {{ coverage_ratio }} |

## Quality Summary
| Field | Value |
| --- | --- |
| gate count | {{ gate_count }} |
| complete | {{ complete }} |

## Quality Gates
| Field | Value |
| --- | --- |
| {{ gate_name }} status | {{ gate_status }} |
| {{ gate_name }} summary | {{ gate_summary }} |

Gate statuses are descriptive run checks only.

## Visible Reasons
| Field | Value |
| --- | --- |
| Reason 1 code | {{ reason_code }} |
| Reason 1 decision state | {{ reason_state }} |
| Reason 1 message | {{ reason_message }} |
