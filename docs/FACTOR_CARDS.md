# Factor Cards

Factor cards are reviewable evidence artifacts built from diagnostic summaries and
reproducibility metadata. They summarize what was measured, what metadata is
available, what warnings were surfaced, and which advisory recommendation was
assigned.

They do not change registry state. A recommendation is not approval; any status
change requires a separate reviewed registry action.

## Required Sections

Each factor card represents:

- diagnostic summary;
- time-of-day stability;
- session segment stability;
- monthly stability;
- volatility regime stability;
- liquidity regime stability;
- correlation to existing factors;
- factor cluster id;
- advisory promotion recommendation;
- sample size and warnings;
- data version, factor version, and label version;
- code and config hash references when available;
- run manifest path;
- no-lookahead validation status;
- review status;
- limitations.

If a diagnostic input does not contain a required section, the card keeps the
section visible with `not_available` status and emits a warning. Missing
metadata is also surfaced as `not_available` or `not_recorded` rather than
silently inferred.

## Recommendation Vocabulary

The recommendation field is closed-set and advisory:

- `reject`
- `needs_more_data`
- `candidate_for_strategy_test`
- `candidate_for_review`
- `do_not_promote`

No recommendation value is an approval. The report generator rejects values
outside the closed set.

## Interpretation

Use factor cards to inspect evidence quality, metadata completeness, warning
state, and version alignment. A card can support review, but it is not a
strategy result, execution result, deployment signal, or registry decision.

Small samples, missing stability sections, missing correlation diagnostics,
version ambiguity, or absent no-lookahead status should be treated as review
items. The conservative default for sparse samples is `needs_more_data`.
