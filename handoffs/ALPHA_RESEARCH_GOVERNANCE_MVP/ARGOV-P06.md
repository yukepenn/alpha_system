# ARGOV-P06 Handoff — LabelSpec and Label Leakage Guard

## Summary

Implemented the `LabelSpec` governance contract in
`alpha_system.governance.label_spec` using ARGOV-P02 typed IDs, canonical
serialization, deterministic round trips, and fail-closed structured validation.

Implemented the label-leakage guard in
`alpha_system.governance.label_leakage_guard`. The guard consumes only a
validated `LabelSpec` and injected feature-reference metadata. It blocks direct
label-as-feature overlap, declared label aliases/transforms, and
availability-time look-ahead violations. Missing or ambiguous feature
availability metadata produces a blocking finding rather than a clean result.

This phase added governance protocol metadata, tests, tiny synthetic fixtures,
docs, and the README snapshot only. It did not materialize labels, compute label
values, ingest real data, run diagnostics, run a backtest, add candidate or
library status, or introduce broker/live/paper/order-routing behavior.

## LabelSpec Contract

`LabelSpec` carries all campaign-required fields:

- `label_spec_id`
- `horizon`
- `path_rules`
- `cost_model`
- `target_stop_rules`
- `availability_time`
- `forbidden_feature_overlap`
- `leakage_checks`

`alpha_spec_id` is allowed as an optional owning `AlphaSpec` reference. When
present, it must be a well-formed `aspec_...` ID and is included in the
deterministic `lspec_...` content ID.

Validation is fail-closed:

- missing, null, empty, unknown, malformed, or non-serializable fields raise
  `GovernanceValidationError` with structured issues;
- `label_spec_id` must match deterministic `LabelSpec` content;
- `horizon` must be explicit;
- `availability_time` must be timezone-aware ISO-8601;
- `path_rules`, `cost_model`, `target_stop_rules`, and
  `forbidden_feature_overlap` must contain explicit non-empty metadata;
- `leakage_checks` must include `label_as_feature` and `availability_time`;
- serialization round trips deterministically through the ARGOV-P02 canonical
  serialization primitive.

`LabelSpec` is metadata only. It implies no label quality, predictive value,
alpha validity, profitability, tradability, candidate status, factor-library
entry, implementation permission, or production readiness.

## Leakage Guard

The guard exposes:

- `check_label_leakage(label_spec, feature_references) -> LabelLeakageResult`

Each `LabelLeakageFinding` has:

- `kind`: `LABEL_AS_FEATURE` or `LOOKAHEAD`
- `severity`: `BLOCKING`
- `offending_reference`
- `rationale`

`LabelLeakageResult.clean` and `LabelLeakageResult.blocked` are derived from the
finding list, so a blocking finding cannot be coerced to clean.

Guard behavior:

- direct feature references that match `forbidden_feature_overlap` are blocked;
- declared aliases and transforms are blocked;
- feature `information_time` at or after label `availability_time` is blocked;
- missing, malformed, or ambiguous feature availability metadata fails closed
  with a blocking `LOOKAHEAD` finding;
- the guard never reads real data or computes labels/features.

## No-Lookahead Tests

Added `tests/no_lookahead/test_label_leakage_guard.py` with synthetic injected
faults:

- direct label-as-feature overlap is blocked;
- declared transform alias overlap is blocked;
- feature information time equal to the label availability time is blocked;
- missing availability metadata fails closed;
- a clean synthetic feature set with information time before label availability
  passes without findings.

## Staged Files

Exact staged files after explicit staging:

- `README.md`
- `docs/governance/LABEL_LEAKAGE_GUARD.md`
- `docs/governance/LABEL_SPEC.md`
- `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P06.md`
- `src/alpha_system/governance/__init__.py`
- `src/alpha_system/governance/label_leakage_guard.py`
- `src/alpha_system/governance/label_spec.py`
- `tests/fixtures/governance/label_leakage_features.json`
- `tests/fixtures/governance/label_spec_valid.json`
- `tests/no_lookahead/test_label_leakage_guard.py`
- `tests/unit/governance/test_label_spec.py`
- `tests/unit/governance/test_package_skeleton.py`

No `runs/**` path is staged.

## Validation Results

Spec-requested validation:

- `git status --short` — passed before staging. Output showed only allowed
  ARGOV-P06 paths:

```text
 M README.md
 M src/alpha_system/governance/__init__.py
 M src/alpha_system/governance/label_spec.py
 M tests/unit/governance/test_package_skeleton.py
?? docs/governance/LABEL_LEAKAGE_GUARD.md
?? docs/governance/LABEL_SPEC.md
?? src/alpha_system/governance/label_leakage_guard.py
?? tests/fixtures/governance/label_leakage_features.json
?? tests/fixtures/governance/label_spec_valid.json
?? tests/no_lookahead/test_label_leakage_guard.py
?? tests/unit/governance/test_label_spec.py
```

- `python tools/verify.py --smoke` — passed with exit 0 and no output.

- `python -m pytest tests/unit/governance/test_label_spec.py -q` — passed:

```text
........................                                                 [100%]
24 passed in 0.02s
```

- `python -m pytest tests/no_lookahead/test_label_leakage_guard.py -q` —
  passed:

```text
.....                                                                    [100%]
5 passed in 0.01s
```

- `python -m pytest tests/unit/governance -q` — passed:

```text
........................................................................ [ 65%]
......................................                                   [100%]
110 passed in 0.10s
```

- `python -m pytest tests/no_lookahead -q` — passed:

```text
.......................................................                  [100%]
55 passed in 0.30s
```

- `test -f docs/governance/LABEL_SPEC.md` — passed with exit 0 and no output.
- `test -f docs/governance/LABEL_LEAKAGE_GUARD.md` — passed with exit 0 and no
  output.
- `git ls-files runs` — passed with empty output.
- `find data -type f ! -name README.md ! -name ".gitkeep" -print` — passed
  with empty output.
- `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` —
  passed with empty output.
- `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` — passed
  with empty output.

Additional local inspection:

- `git diff --check` — passed with exit 0 and no output.

Skipped checks: none of the spec-requested commands were skipped.

## Artifact Policy

- `git ls-files runs` returned empty.
- `git diff --cached --name-only` contains no `runs/` path after explicit
  staging.
- The `data`, `metadata`, and Parquet audits returned empty output.
- No forbidden data, raw/canonical/factor/label/cache data, local DB, DB
  journal, WAL, Parquet, Arrow, Feather, log, cache, model binary, heavy
  artifact, or run artifact is staged.
- No run-local `handoff.md` under
  `runs/2026-06-03T135209Z_ALPHA_RESEARCH_GOVERNANCE_MVP/phases/ARGOV-P06/`
  was created or staged.
- No run-local `review.md`, `verdict.json`, `checks.json`, or
  `repair_attempts/` artifact was created or staged by Codex.

## Staging Discipline

- Explicit staging only.
- The staged set was built with explicit file paths.
- `git add .` was not used.
- `git add -A` was not used.
- No force push was performed.
- No PR was created.
- No merge was performed.

## Scope Confirmation

- No label materialization, label value computation, feature computation, real
  data ingestion, diagnostics, backtest, strategy optimization, portfolio
  allocation, candidate/library/promotion path, CLI, registry integration,
  executable canary runner integration, PR creation, or merge scope was
  introduced.
- No edits were made to `src/alpha_system/factors/**`,
  `src/alpha_system/execution/broker/**`, `src/alpha_system/broker/**`,
  `src/alpha_system/live/**`, `live/**`, `paper/**`, or order-routing paths.
- Tests were added only under authorized governance and no-lookahead paths.
  Existing tests were not weakened, skipped, deleted, or relaxed.
- Fixtures are tiny synthetic governance metadata only; they are not real market
  data, computed label values, computed factor values, research evidence, or
  alpha evidence.
- No broker, live, paper, order-routing, deployment, alpha-search,
  factor-computation, label-quality, alpha, profitability, tradability,
  paper-readiness, live-readiness, broker-readiness, capital-allocation,
  production-readiness, candidate-status, or factor-library-entry claim was
  introduced.

## Review Boundary

No Claude review was run by Codex. No `review.md` or `verdict.json` was created.
Ralph owns validation orchestration, independent review routing, verdict
parsing, PR creation, CI, merge gates, semantic done-checks, and phase PASS
marking.
