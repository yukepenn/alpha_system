# ASV1-P13 Handoff

## Phase

- Phase ID: `ASV1-P13`
- Phase name: Factor Card and Report Generation
- Campaign: `ALPHA_SYSTEM_V1`
- Lane: Yellow
- Branch: `auto/alpha_system_v1/asv1-p13-factor-card-and-report-generation`
- Worktree: `/home/yuke_zhang/projects/alpha_system`
- Run directory: `runs/2026-06-02T012007Z_ALPHA_SYSTEM_V1/phases/ASV1-P13` (local-only)

## Scope Completed

Implemented report generation over existing diagnostic summaries:

- factor-card report models, assembly, Markdown rendering, CSV rendering, local-only output path policy, and warning generation;
- study-report assembly and rendering over one or more factor-card models;
- closed advisory promotion recommendation vocabulary;
- blocking prohibited-claim detection over structured report payloads and rendered Markdown/CSV;
- minimal `src/alpha_system/cli/report.py` command module for factor-card and study-report generation;
- minimal top-level report subparser registration in `src/alpha_system/cli/main.py`;
- Markdown templates for factor cards and study reports;
- conservative report config under `configs/reports/factor_card.yaml`;
- durable docs for factor-card interpretation and report language policy;
- focused unit and integration tests, including negative prohibited-claim and insufficient-sample paths;
- tiny synthetic report fixture helper under `tests/fixtures/reports/**`, documented as correctness-only and not market evidence.

No diagnostics were re-implemented. No strategy, backtest, cost, portfolio, management, execution, broker, live, paper, order-routing, registry promotion, deployment, reviewer, `review.md`, `verdict.json`, PR, merge, or PASS-marking scope was introduced.

## Repair Summary

The review found one blocking defect: the generated spec required the top-level
`alpha report build` help path, but `src/alpha_system/cli/main.py` did not
register the existing report subparser. This repair adds the narrow registration
only. The import is local to `build_parser()` so standalone
`python -m alpha_system.cli.report ...` execution remains warning-free.

## Files Created / Changed

Curated changed paths for this handoff:

```text
configs/reports/factor_card.yaml
docs/FACTOR_CARDS.md
docs/REPORT_LANGUAGE_POLICY.md
handoffs/ASV1-P13.md
src/alpha_system/cli/main.py
src/alpha_system/cli/report.py
src/alpha_system/reports/factor_card.py
src/alpha_system/reports/prohibited_claims.py
src/alpha_system/reports/report_models.py
src/alpha_system/reports/study_report.py
src/alpha_system/reports/templates/factor_card.md
src/alpha_system/reports/templates/study_report.md
tests/fixtures/reports/README.md
tests/fixtures/reports/__init__.py
tests/fixtures/reports/synthetic.py
tests/integration/test_factor_card_fixture_output.py
tests/integration/test_study_report_fixture_output.py
tests/unit/test_factor_card_metadata.py
tests/unit/test_factor_card_recommendations.py
tests/unit/test_factor_card_review_status.py
tests/unit/test_factor_card_sections.py
tests/unit/test_factor_card_stability_sections.py
tests/unit/test_factor_card_warnings.py
tests/unit/test_report_artifact_policy.py
tests/unit/test_report_language_policy.py
tests/unit/test_report_prohibited_claims.py
```

Commit status: repaired in the working tree. The run-local P13 spec was amended
after review to authorize `src/alpha_system/cli/main.py` for the minimal report
subparser registration required by the phase's own top-level CLI validation.
No PR, merge, reviewer, verdict, or PASS marking was performed by Codex.

## Report Section Coverage

| Required field / section | Implementation |
| --- | --- |
| Time-of-day stability | `FactorCardReport.stability.time_of_day`; Markdown/CSV rendered |
| Session segment stability | `FactorCardReport.stability.session_segment`; Markdown/CSV rendered |
| Monthly stability | `FactorCardReport.stability.monthly`; Markdown/CSV rendered |
| Volatility regime stability | `FactorCardReport.stability.volatility_regime`; missing input becomes visible warning |
| Liquidity regime stability | `FactorCardReport.stability.liquidity_regime`; missing input becomes visible warning |
| Correlation to existing factors | `correlation_to_existing_factors`; missing input becomes visible warning |
| Factor cluster id | explicit metadata/diagnostic value or `not_assigned` |
| Promotion recommendation | closed enum only; advisory note rendered |
| Sample size | model field and rendered recommendation table / CSV |
| Warnings | normalized `ReportWarning` records and rendered table |
| Data/factor/label versions | `ReportMetadata` required fields |
| Code/config hash references | `code_hash_ref` / `config_hash_ref`, `not_available` when absent |
| Run manifest path | `run_manifest_path`, `not_available` when absent |
| No-lookahead validation status | `no_lookahead_validation_status` required metadata field |
| Review status | `review_status` required metadata field |
| Diagnostic summary | compact deterministic diagnostic overview |
| Limitations section | required tuple, rendered in Markdown/CSV |

## Recommendation Vocabulary

Allowed values are exactly:

```text
reject
needs_more_data
candidate_for_strategy_test
candidate_for_review
do_not_promote
```

`PromotionRecommendation.parse()` rejects any other value. Rendered reports state
that recommendations are advisory research guidance only and that registry status
changes require a separate reviewed action. No recommendation value renders as an
approval or registry status change.

## Prohibited-Claim Enforcement

`src/alpha_system/reports/prohibited_claims.py` blocks:

```text
profitable
tradable
production-ready
guaranteed alpha
market-beating
robust without evidence
approved without review
live-ready
deployable
production candidate
```

Detection is case-insensitive and normalizes punctuation/underscore/hyphen
variants. Validation runs on structured factor-card and study-report payloads and
on rendered Markdown/CSV output. Tests cover every blocked phrase, punctuation
variants, metadata injection, and the closed recommendation vocabulary.

## Templates

- `src/alpha_system/reports/templates/factor_card.md` renders metadata, diagnostic summary, all stability sections, correlation, recommendation, warnings, and limitations.
- `src/alpha_system/reports/templates/study_report.md` renders an aggregate factor table, study warnings, factor detail JSON blocks, and limitations.

The renderers have internal fallback templates so source execution remains
deterministic if package-data wiring is changed later.

## Fixtures

Committed fixture helpers:

```text
tests/fixtures/reports/README.md      185 bytes
tests/fixtures/reports/__init__.py     43 bytes
tests/fixtures/reports/synthetic.py  3886 bytes
```

These are tiny deterministic synthetic correctness helpers only. Integration
tests generate Markdown/CSV outputs in pytest temp directories; no generated
report output fixture or report bundle is committed.

## Validation Results

```text
find runs/2026-06-02T012007Z_ALPHA_SYSTEM_V1 -name STOP -print
PASS - returned empty; no STOP file was active.

python -m pytest tests/unit/test_factor_card_sections.py tests/unit/test_factor_card_metadata.py tests/unit/test_factor_card_stability_sections.py tests/unit/test_factor_card_warnings.py tests/unit/test_factor_card_recommendations.py tests/unit/test_factor_card_review_status.py tests/unit/test_report_prohibited_claims.py tests/unit/test_report_language_policy.py tests/unit/test_report_artifact_policy.py tests/integration/test_factor_card_fixture_output.py tests/integration/test_study_report_fixture_output.py
PASS - 47 passed.

python -m pytest tests/unit tests/integration
PASS - 287 passed.

python -m pytest tests/unit/test_factor_card_sections.py tests/unit/test_factor_card_metadata.py tests/unit/test_report_prohibited_claims.py
PASS - 21 passed.

python -m compileall src
PASS - exit 0.

git status --short
PASS/INSPECTED - showed the curated ASV1-P13 staged paths plus the repaired
`src/alpha_system/cli/main.py` registrar before final staging.

git add -- handoffs/ASV1-P13.md src/alpha_system/cli/main.py
PASS - staged the handoff update and minimal top-level CLI registrar by explicit
path after the run-local P13 spec was amended to authorize the registrar.

git diff --cached --name-only
PASS/INSPECTED - returned no `runs/**` paths and includes only the curated P13
source/docs/config/tests/fixture/handoff paths plus `src/alpha_system/cli/main.py`.

python -m alpha_system.cli report build --help
FAIL - exit 1; ModuleNotFoundError: No module named 'alpha_system'. This shell has the repo source uninstalled and no PYTHONPATH set.

PYTHONPATH=src python -m alpha_system.cli report build --help
PASS - top-level `alpha_system.cli` now registers `report` and renders the build help.

PYTHONPATH=src python -m alpha_system.cli.report build --help
PASS - standalone report module help rendered factor-card / study-report arguments
without the prior runpy warning.

python tools/verify.py --smoke
PASS - exit 0.

python tools/hooks/canary_runner.py
PASS - all Frontier canaries passed.

python tools/verify.py --all
FAIL - 455 passed, 7 failed in existing Frontier/GitHub driver tests
(`tests/test_github_utils.py`, `tests/test_ralph_driver.py`). These failures are
outside ASV1-P13 report generation and were not repaired in this bounded attempt.

find artifacts -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true
PASS - returned empty.

find . -path ./tests/fixtures -prune -o -type f \( -name "*.parquet" -o -name "*.arrow" -o -name "*.feather" \) -print
PASS - returned empty.

find . -type f \( -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.db" -o -name "*.db-journal" -o -name "*.wal" \) -print
PASS - returned empty.

git ls-files runs
PASS - returned empty.

python -m ruff check src tests || true
UNAVAILABLE - `ruff` is not installed (`No module named ruff`).

python -m mypy src || true
UNAVAILABLE - `mypy` is not installed (`No module named mypy`).

alpha report build --help || true
UNAVAILABLE - console script is not installed (`alpha: command not found`).

git diff --check
PASS - returned empty.
```

## Artifact Policy

`runs/**` remains local-only. No run-local handoff, review, verdict, checks,
executor notes, or repair artifact was staged or committed. `git ls-files runs`
returned empty.

No full report bundle, generated report directory, heavy HTML, plot/image binary,
SQLite/DB/journal/WAL file, Parquet/Arrow/Feather file, raw data, canonical data,
log, or cache file was staged or committed. Pytest-created `__pycache__` files
are ignored local caches and were not staged.

Generated report outputs are local-only by policy. Repo-relative report outputs
inside the repository are rejected unless they stay under `artifacts/reports`;
tests write generated reports only to pytest temp directories.

## Risks Addressed

- R-014: blocked report-language vocabulary plus negative tests.
- R-034: closed advisory recommendation vocabulary and rendered advisory note.
- R-015: no registry promotion writes and no approval/status-change workflow.
- R-005: data/factor/label versions, alignment status, hashes, manifest path,
  no-lookahead status, and review status are surfaced.
- R-013/R-025: no generated report bundles committed; artifact-policy tests and
  audits returned clean.
- R-036: tests include missing-section, sparse-sample, and blocked-language paths.
- R-017: no test skips/xfails or weakened assertions were introduced.

## Known Limitations

- The bare `python -m alpha_system.cli ...` command requires installation or
  `PYTHONPATH=src` in this src-layout shell. With `PYTHONPATH=src`, the repaired
  top-level `report build --help` path passes.
- `python tools/verify.py --all` currently fails in existing Frontier/GitHub
  driver tests outside ASV1-P13; the ASV1-P13 unit and integration envelope
  passes.
- The report layer consumes diagnostics as supplied. It does not compute new
  diagnostic metrics or infer absent volatility/liquidity/correlation evidence.
- YAML config is a conservative checked-in default; no new YAML parser dependency
  was added.
- No Claude review, semantic done-check, PR, CI, merge, or PASS marking was run
  by Codex.

## Review Focus

Please review:

- conservative report language and prohibited-claim enforcement;
- recommendation discipline and separation from registry status changes;
- required metadata completeness and handling of missing hashes/manifest values;
- stability/correlation/cluster coverage and missing-section warning behavior;
- the minimal `src/alpha_system/cli/main.py` report registration and top-level
  CLI help behavior under the project import environment;
- fixture adequacy and absence of report bundle or artifact creep;
- absence of broker/live/paper/order-routing/backtest/execution scope creep.

## Recommended Next State

Return to Ralph for validation routing and fresh review/done-check. Codex did
not mark the phase PASS.
