# Research Queue And Agent Assignment

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P06`  
Document type: human-facing index

`FUTCORE-P06` seeds the bounded research queue and role-assignment map for the
remaining pilot phases. The artifacts are contract records only. They do not
instantiate agents, start a runner, draft AlphaSpecs, run diagnostics, edit
Agent Factory primitives, read market data, or authorize broker/live/paper/order
behavior.

## Queue Artifacts

| Artifact | Purpose |
| --- | --- |
| `research/futures_core_alpha_pilot_v1/queue/research_queue.md` | Finite `25` task queue for `FUTCORE-P07` through `FUTCORE-P30`, with task id, description, owning role, phase mapping, and budget reference. |
| `research/futures_core_alpha_pilot_v1/queue/role_assignment_map.md` | Exactly-one-owner map for each task plus forbidden-role bindings. |
| `research/futures_core_alpha_pilot_v1/queue/separation_of_duties.md` | Separation invariants tied to Agent Factory role, permission, and separation contracts. |

## Queue Summary

The queue covers:

- five per-family AlphaSpec drafting tasks for `FUTCORE-P07` through
  `FUTCORE-P11`;
- independent AlphaSpec critique and family budget audit in `FUTCORE-P12`;
- data-contract audit and StudySpec pack authoring in `FUTCORE-P13` and
  `FUTCORE-P14`;
- split FeatureRequest and LabelSpec addition tasks for `FUTCORE-P15` under the
  shared `<=5` request cap;
- five family diagnostics tasks plus cost/session/regime consolidations for
  `FUTCORE-P16` through `FUTCORE-P22`;
- no-lookahead and variant-budget audits in `FUTCORE-P23` and `FUTCORE-P24`;
- reviewer verdicts, ledgers, evidence drafts, allowed research-state decision
  records, failure-mode handoffs, and closeout for `FUTCORE-P25` through
  `FUTCORE-P30`.

## Role Summary

Every task owner is one of the ten Agent Factory roles:

- `research_director`
- `hypothesis_scout`
- `alpha_spec_critic`
- `data_contract_auditor`
- `feature_engineer`
- `label_engineer`
- `no_lookahead_auditor`
- `diagnostics_runner`
- `statistical_reviewer`
- `librarian`

The assignments consume the existing contracts in
`src/alpha_system/agent_factory/queue`, `roles`, `permissions`, and
`separation`. No consumed primitive is changed by this phase.

## Separation Invariants

Downstream phases must preserve these invariants:

- drafter != critic;
- critic != statistical reviewer;
- reviewer != promoter;
- implementer != self-reviewer;
- Diagnostics Runner != promoter;
- Librarian records verdict-gated artifacts only after required reviewer
  verdicts;
- human-owned capital/live actions remain outside Agent Factory task ownership.

No Agent Factory role receives a promotion permission grant. `FUTCORE-P28`
records only allowed research states: `REJECT`, `INCONCLUSIVE`, `WATCH`, or
`CANDIDATE_RESEARCH`. `WATCH` and `CANDIDATE_RESEARCH` remain capped at `<=2`
and require reviewer verdict references. They are not paper/live approval,
FactorLibrary promotion, Strategy Reference validation, production readiness, or
capital allocation.

## Budget References

The queue cites the finite campaign budget rather than creating new budget
categories:

- `<=40` AlphaSpec drafts;
- `<=10` approved AlphaSpecs;
- `<=5` new feature or label requests;
- `<=3` diagnostics survivors;
- `<=2` `WATCH` or `CANDIDATE_RESEARCH` outcomes;
- per-study VariantBudget required;
- family budget split `0.40 / 0.20 / 0.15 / 0.15 / 0.10`.

The volume/activity overlay has no standalone queue task or budget.

## Boundaries

The queue is value-free and finite. It contains no market data, feature values,
label values, diagnostics outputs, provider responses, Parquet files, SQLite
files, local DBs, logs, caches, or heavy artifacts.

The pilot remains research-only. The queue does not authorize scaled mining,
continuous autonomous research, FactorLibrary V1, Strategy Reference Validation,
AlphaBook, strategy/backtest/portfolio products, paper/live/broker/order work,
production deployment, capital allocation, or profitability/tradability claims.
