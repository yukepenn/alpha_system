# FUTCORE-P26 Ledgers

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P26`  
Durable docs page for the pilot TrialLedger and RejectedIdeaLedger

P26 adds value-free ledger records under
`research/futures_core_alpha_pilot_v1/ledgers/**`. The records cite upstream
StudySpecs, AlphaSpecs, diagnostics, consolidations, audits, critiques, and P25
verdicts by repo-relative path. They do not duplicate value data and do not make
or imply a promotion decision.

## Structure

- `trial_ledger/trial_ledger.json` is the TrialLedger aggregate.
- `trial_ledger/records/*.json` contains one validated `TrialLedgerRecord` per
  recorded study-level attempt or explicit variant-cell attempt.
- `rejected_idea_ledger/rejected_idea_ledger.json` is the
  `ResearchGraveyardLedger` aggregate.
- `rejected_idea_ledger/records/*.json` contains one validated
  `RejectedIdeaRecord` per rejected idea event.
- `INDEX.md` records the detailed reconciliation and record paths.

## Reconciliation

| Item | Count |
| --- | ---: |
| AlphaSpec drafts reconciled | 40 |
| StudySpecs reconciled | 10 |
| TrialLedger records | 16 |
| P12 non-accepted AlphaSpecs recorded as rejected | 30 |
| Accepted StudySpecs rejected before P25 | 4 |
| P25 reviewer-rejected ideas | 0 |
| RejectedIdeaLedger records | 34 |
| P25 `INCONCLUSIVE` verdicts carried forward without P26 promotion | 6 |
| P24 explicit observed variant cells | 8 |
| Declared StudySpec variant slots | 40 |

The ledger reconciliation is complete: every StudySpec-bound trial has a
TrialLedger record, every P12 non-accepted AlphaSpec has a RejectedIdeaLedger
record, every accepted StudySpec rejected before P25 has a RejectedIdeaLedger
record, and P25 contributes no additional reviewer-rejected records.

## Boundaries

These ledgers are evidence recording only. They contain ids, statuses, reason
categories, duplicate-exposure group hints, counts, hashes, and path references.
They contain no raw rows, feature or label values, provider payloads, heavy
artifacts, local databases, run-local artifacts, profitability claims,
tradability claims, broker/live/paper/deployment behavior, or promotion state.
