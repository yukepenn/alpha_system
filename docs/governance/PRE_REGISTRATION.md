# HypothesisCard And Pre-Registration

`ARGOV-P04` defines the `HypothesisCard` governance object and the pure
`DRAFT -> REGISTERED` registration precondition for linking a validated card to
a validated `AlphaSpec`.

This protocol is governance metadata only. It does not search for alpha, ingest
real data, compute factors, run diagnostics, approve implementation by itself,
create candidate status, add anything to a factor library, validate a result,
or imply profitability, tradability, paper readiness, live readiness, capital
allocation, production readiness, or deployment approval.

## HypothesisCard

Every `HypothesisCard` must include these fields from the campaign contract:

- `hypothesis_id`
- `title`
- `family`
- `rationale`
- `expected_mechanism`
- `falsification_criteria`
- `risks`
- `author`
- `created_at`

`hypothesis_id` must be a deterministic `hyp_...` governance ID generated from
the complete card content other than the ID itself. Changing the rationale,
expected mechanism, falsification criteria, risks, author, or timestamp changes
the expected ID.

Validation is fail-closed. The validator rejects non-mapping roots, missing or
null required fields, undeclared fields, malformed IDs, IDs that do not match
the deterministic content, empty or placeholder text, terse substantive text,
empty criteria or risk lists, malformed or timezone-free timestamps, and content
that cannot be represented as strict canonical JSON. Valid records round-trip
through canonical JSON without implicit defaults, field dropping, or type
coercion.

## Falsification Anchor

`falsification_criteria` is mandatory and must be substantive. Each entry must
describe a condition that can reject or block the idea in a later governance
step. Empty entries, placeholder entries such as `TBD`, and narrative-only text
without a rejection or blocking condition fail validation.

The falsification anchor records what would count against the idea before
implementation work is considered. It is not evidence, not approval, and not a
statement that the idea is valid.

## Registration Linkage

`validate_pre_registration(...)` is the pure precondition for the
`DRAFT -> REGISTERED` transition. It requires:

- a valid `HypothesisCard`;
- a valid `AlphaSpec`;
- an `AlphaSpec.hypothesis_id` that exactly matches the validated card's
  `hypothesis_id`.

The function returns the validated linked pair only when all preconditions hold.
Missing objects, invalid objects, unsupported transition names, or mismatched
IDs raise structured governance validation errors.

The pre-registration check performs no I/O, writes no registry record, persists
nothing, grants no implementation permission, runs no study, and creates no
candidate or factor-library entry. Later phases wire additional lifecycle
objects and persistence.

## Template

Use `templates/governance/hypothesis_card.template.yaml` as a human-readable
starting point. The template is not a validated object until every placeholder
is replaced with explicit, substantive governance metadata and a deterministic
`hypothesis_id`.
