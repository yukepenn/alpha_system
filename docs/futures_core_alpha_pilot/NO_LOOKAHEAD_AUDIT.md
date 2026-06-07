# No-Lookahead Audit

`FUTCORE-P23` adds the value-free No-Lookahead / Label Leakage / Same-Bar
Optimism audit for the futures core alpha pilot.

Primary report:

- `research/futures_core_alpha_pilot_v1/audits/no_lookahead/no_lookahead_audit.md`

The audit covers the exact P22 set: six non-rejected
`diagnostic_survivors_for_consolidation` StudySpecs plus the four retained
cross-market rejected-source StudySpecs. It records, by StudySpec id/hash and
family, the `available_ts`, `label_available_ts`, same-bar, cross-instrument,
and session-context guard checks, then assigns temporal-validity flags from the
approved failure-mode set.

The report is documentation-only and value-free. It adds no diagnostics runner,
reader, primitive, command, feature value data, label value data, review
verdict, promotion decision, paper/live/broker/order behavior, or
profitability/tradability claim. `zero_cost` remains diagnostic-only and never a
promotion basis.
