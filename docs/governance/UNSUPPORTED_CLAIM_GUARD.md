# Unsupported-Claim Guard

## Purpose

`alpha_system.governance.claims` is the governance text guard for research reports,
templates, summaries, and handoff-style text. It rejects unsupported research-output
claims and rejects malformed text input instead of treating undecidable input as clean.

The guard is a governance control only. It does not run studies, inspect market data,
rank factors, or create evidence.

## Prohibited Claim Taxonomy

The blocked-language taxonomy has these categories:

- Blocked-language taxonomy category `alpha_validity`: phrase forms that state a research object proves, validates, finds, or generates alpha.
- Blocked-language taxonomy category `profitability`: phrase forms that state profit, profitability, positive PnL, or market-beating behavior.
- Blocked-language taxonomy category `tradability`: phrase forms that state a research object is tradable, can be traded, or is suitable for trading.
- Blocked-language taxonomy category `robustness`: phrase forms that state a result is robust or stable across contexts without a reviewed claim standard.
- Blocked-language taxonomy category `production_readiness`: phrase forms that state production readiness, deployability, or production use.
- Blocked-language taxonomy category `paper_readiness`: phrase forms that state readiness for paper-trading use.
- Blocked-language taxonomy category `live_readiness`: phrase forms that state readiness for live use or live execution.
- Blocked-language taxonomy category `broker_readiness`: phrase forms that state broker execution readiness, order-routing readiness, or safety to route orders.
- Blocked-language taxonomy category `real_data_readiness`: phrase forms that state the artifact is ready for real data.

These words may appear in blocked-language policy text, taxonomy descriptions, and
explicit no-claims language. They must not appear as affirmative statements about a
research output.

## Fail-Closed Contract

Use `validate_no_unsupported_claims(text, context=...)` before accepting generated or
edited governance report text. The function:

- accepts only decoded, non-empty strings;
- rejects non-string roots, empty strings, replacement characters, NUL bytes, and other
  non-whitespace control characters;
- returns `None` only when the text is decidable and contains no unsupported claim;
- raises `UnsupportedClaimError`, a `GovernanceValidationError` subclass, for malformed
  input or blocked claim language.

`UnsupportedClaimError.to_dict()` exposes validation `issues` plus structured
`violations`. Each violation records the category, pattern id, matched text, line,
column, and local snippet.

## Documented Allowlist

The allowlist is local and explicit. It is not a silent bypass for whole files. A blocked
term is allowed only when the local sentence fits one of these non-asserting contexts:

- explicit no-claims or no-assertion statements
- blocked-language policy, taxonomy, or vocabulary catalogs
- guard or detector statements that reject blocked claim vocabulary
- governance object identifiers such as AlphaSpec and alpha_spec_id

The governance-identifier context is limited to `AlphaSpec` and `alpha_spec_id`.
Repository, package, generic alpha, or shortened identifier names are not allowlisted.
Guard-behavior sentences must name the guard or detector and explicitly describe
blocking, detecting, rejecting, or preventing blocked claim vocabulary, terms, phrases,
assertions, or categories. General report text such as validation or template
requirements is not allowlisted and is still rejected if it contains a blocked claim.

The standard no-claims sentence is:

```text
This report is not evidence of alpha validity, profitability, tradability, robustness, production readiness, paper readiness, live readiness, broker readiness, or readiness for real data.
```

## Governance Report Templates

`templates/governance/evidence_governance_report.template.md` requires these sections:

- `Evidence References`
- `Limitations`
- `No-Claims Language`
- `Required Checks`

The template includes the standard no-claims sentence and requires rendered reports to be
checked by `validate_no_unsupported_claims` before they are used as governance artifacts.
The template does not grant review status, state transition status, or any market-result
claim.
