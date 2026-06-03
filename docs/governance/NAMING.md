# Governance Naming Contract

`ARGOV-P01` fixes the canonical names and path conventions for the
`ALPHA_RESEARCH_GOVERNANCE_MVP` governance layer. Later ARGOV phases may add object
schemas and behavior, but they must preserve these object names, ID prefixes, module
names, and directory roots unless this contract is explicitly updated.

This document is a naming contract only. It does not define validation behavior,
serialization behavior, registry integration, CLI behavior, trading readiness, alpha
validity, profitability, or tradability.

## Canonical Objects And ID Prefixes

Object names must match `campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/campaign.yaml` under
`governance_objects` exactly.

Canonical governance IDs use the form `<prefix>_<token>`. `ARGOV-P02` owns the token
format and ID-generation behavior. This phase fixes only the prefixes.

| Object name | ID prefix | Canonical module |
| --- | --- | --- |
| `HypothesisCard` | `hyp` | `alpha_system.governance.hypothesis_card` |
| `AlphaSpec` | `aspec` | `alpha_system.governance.alpha_spec` |
| `FeatureRequest` | `freq` | `alpha_system.governance.feature_request` |
| `LabelSpec` | `lspec` | `alpha_system.governance.label_spec` |
| `StudySpec` | `sspec` | `alpha_system.governance.study_spec` |
| `TrialLedgerRecord` | `trial` | `alpha_system.governance.trial_ledger` |
| `EvidenceBundle` | `evb` | `alpha_system.governance.evidence_bundle` |
| `RejectedIdeaRecord` | `rej` | `alpha_system.governance.rejected_idea` |
| `PromotionDecision` | `prom` | `alpha_system.governance.promotion` |
| `ReviewerVerdict` | `rver` | `alpha_system.governance.reviewer_verdict` |
| `NegativeControlResult` | `nctrl` | `alpha_system.governance.canaries` |
| `AlphaBookRecord` | `abook` | `alpha_system.governance.registry` |

`AlphaBookRecord` remains a lightweight future-compatibility pointer. Its name and
prefix must not imply capital allocation, live status, production approval, or the
future Portfolio AlphaBook.

## Python Package And Module Names

The governance package root is:

```text
src/alpha_system/governance/
```

Python modules use lower snake_case names:

- `ids.py`
- `serialization.py`
- `validation.py`
- `alpha_spec.py`
- `hypothesis_card.py`
- `feature_request.py`
- `label_spec.py`
- `study_spec.py`
- `trial_ledger.py`
- `evidence_bundle.py`
- `rejected_idea.py`
- `promotion.py`
- `reviewer_verdict.py`
- `canaries/`
- `registry.py`
- `claims.py`
- `report.py`

The top-level package import is `alpha_system.governance`. Importing it must not
perform network access, filesystem writes, credential reads, registry writes, data
ingestion, broker calls, order routing, validation, or report generation.

## Test Names

Governance unit tests live under:

```text
tests/unit/governance/
```

Test files use `test_<subject>.py`. The skeleton import smoke test is:

```text
tests/unit/governance/test_package_skeleton.py
```

No tests outside `tests/unit/governance/` are introduced by `ARGOV-P01`.

Future no-lookahead governance canary tests, when authorized by later phases, use:

```text
tests/no_lookahead/
```

`ARGOV-P01` reserves that naming root only; it does not add files there.

## Documentation, Config, And Template Names

Governance docs live under:

```text
docs/governance/
```

Durable governance docs use clear topic names. Campaign-level overview docs may use
uppercase names such as `GOVERNANCE_OVERVIEW.md` and `NAMING.md`. Object-specific
docs added later should use the canonical object name or a precise governance topic.

Governance configs live under:

```text
configs/governance/
```

Governance config files added later should use lower snake_case names and `.yaml`
when structured configuration is required. `ARGOV-P01` adds only a documented
placeholder README.

Governance templates live under:

```text
templates/governance/
```

Governance templates added later should use lower snake_case names and include the
object or report subject in the filename, for example
`alpha_spec.template.yaml` or `governance_report.template.md`. `ARGOV-P01` adds
only a documented placeholder README.

## Artifact Naming And Commit Boundaries

Commit-eligible phase handoffs for this campaign live under:

```text
handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/
```

Commit-eligible review artifacts, when authored by the independent reviewer, live
under:

```text
reviews/ALPHA_RESEARCH_GOVERNANCE_MVP/
```

Workflow 2 run artifacts are local-only. Nothing under `runs/` is commit-eligible,
including run-local handoffs, reviews, verdicts, checks, repair attempts, state
files, ledgers, summaries, or STOP files.

No governance naming convention may be used to imply alpha validity, profitability,
tradability, paper readiness, live readiness, broker readiness, capital allocation,
or production readiness.
