# Report Language Policy

Reports must use conservative evidence language. Report text, rendered output,
templates, and caller-provided metadata are validated before emission.

## Prohibited Vocabulary

The generator blocks these exact claim families, including case and punctuation
variants:

- `profitable`
- `tradable`
- `production-ready`
- `guaranteed alpha`
- `market-beating`
- `robust without evidence`
- `approved without review`
- `live-ready`
- `deployable`
- `production candidate`

If blocked vocabulary appears in a report payload or rendered artifact,
generation raises a blocking validation error.

## Allowed Recommendation Vocabulary

The only allowed recommendation values are:

- `reject`
- `needs_more_data`
- `candidate_for_strategy_test`
- `candidate_for_review`
- `do_not_promote`

Recommendations are advisory research guidance only. They must not be rendered
as registry approval or as a status change.

## Validation Behavior

Validation runs on structured report models and rendered Markdown/CSV output.
This catches blocked language from diagnostics, metadata, warnings, limitations,
templates, and generated text. Policy documents and tests may list blocked
vocabulary to define the policy; generated evidence artifacts may not use it.
