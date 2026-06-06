# ALPHA_RESEARCH_RUNTIME_MVP / RT-P18 Handoff

## Curated file list for Ralph staging

Codex staged no files. Per the executor override, Ralph should stage only these
commit-eligible paths if accepting this phase:

- `src/alpha_system/cli/runtime.py`
- `src/alpha_system/cli/main.py`
- `tests/unit/cli/test_runtime.py`
- `docs/research_runtime/CLI.md`
- `README.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P18.md`

No `runs/` path is included. No review artifacts, `review.md`, or
`verdict.json` were created by Codex.

## Implementation summary

RT-P18 adds `alpha_system.cli.runtime` and registers it additively in
`alpha_system.cli.main`. The new `alpha runtime` group exposes:

- `plan`
- `validate-inputs`
- `run-diagnostics`
- `run-label-diagnostics`
- `run-signal-probe`
- `run-cost-stress`
- `build-evidence-draft`
- `build-reference-handoff`
- `summarize`
- `inspect`
- `replay-summary`

The CLI is a thin local JSON-envelope adapter over existing runtime modules. It
parses local inputs, dispatches existing runtime entry points and constructors,
and renders compact JSON or text summaries. Runtime imports are lazy inside
handlers so `--help` and missing-input validation paths do not dispatch runtime
work.

## Scope and safety boundary

- Registration is additive; existing top-level command groups remain present.
- The CLI does not add runtime math, diagnostics logic, cost logic, grid logic,
  audit logic, evidence semantics, handoff semantics, or decision semantics.
- The CLI performs no provider call, network call, broker operation, live/paper
  operation, order routing, deployment, daemon, scheduler, or background work.
- CLI output and docs keep the no-claim posture: descriptive summaries only,
  no promotion or trading-readiness assertion.
- No consumed primitive package under governance, research, experiments,
  backtest, feature, label, or data scope was edited.

## Tests and docs

Added `tests/unit/cli/test_runtime.py` covering:

- runtime module import;
- `runtime --help`;
- every runtime subcommand `--help`;
- additive registration with existing command groups still present;
- help paths do not dispatch handlers;
- every runtime subcommand returns a clean non-zero exit on missing `--input`;
- a valid `validate-inputs` JSON envelope dispatches the existing runtime entry
  contract and emits JSON;
- `summarize` remains value-free and local JSON only.

Added `docs/research_runtime/CLI.md` documenting the command surface, inputs,
outputs, local-only / CI-safe posture, and no-provider / no-claim boundary.

Updated `README.md` to record RT-P18 progress, the new `alpha runtime` command
group, `alpha_system.cli.runtime`, `docs/research_runtime/CLI.md`, and unchanged
safety boundaries. The update is a compact snapshot and does not include run
details or local artifact paths.

## Validation

- `sed -n '1,220p' .codex/skills/frontier-execute/SKILL.md`
  - Result: exit 0; Frontier execute skill loaded.
- `test -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/STOP && printf 'STOP_PRESENT\n' || printf 'STOP_ABSENT\n'`
  - Result: exit 0; `STOP_ABSENT`.
- `test -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/phases/RT-P18/STOP && printf 'PHASE_STOP_PRESENT\n' || printf 'PHASE_STOP_ABSENT\n'`
  - Result: exit 0; `PHASE_STOP_ABSENT`.
- Read-only context inspection via `sed`, `find`, and `rg` over `AGENTS.md`,
  `frontier.yaml`, `ACTIVE_CAMPAIGN.md`,
  `campaigns/ALPHA_RESEARCH_RUNTIME_MVP/**`, RT-P17 handoff, existing CLI
  modules, existing runtime modules, docs, and tests.
  - Result: exit 0 except:
    - `rg ... runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/phases/RT-P18 ...`
      returned exit 2 because the run-local RT-P18 phase directory was absent.
    - `sed -n '1,260p' runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/phases/RT-P18/spec.md`
      returned exit 2 because the run-local spec file was absent.
  - The executable RT-P18 spec was supplied inline by the user and was used as
    authority.
- `python -m py_compile src/alpha_system/cli/runtime.py src/alpha_system/cli/main.py`
  - Result: exit 0.
- `python -m ruff format src/alpha_system/cli/runtime.py src/alpha_system/cli/main.py tests/unit/cli/test_runtime.py`
  - Result: exit 0; first run reformatted `src/alpha_system/cli/runtime.py`.
- `python -m ruff check src/alpha_system/cli/runtime.py src/alpha_system/cli/main.py tests/unit/cli/test_runtime.py`
  - Result: exit 1 initially; import ordering in `tests/unit/cli/test_runtime.py`.
- `python -m ruff check --fix tests/unit/cli/test_runtime.py`
  - Result: exit 0; one import-order issue fixed.
- `python -m ruff check src/alpha_system/cli/runtime.py src/alpha_system/cli/main.py tests/unit/cli/test_runtime.py`
  - Result after fix: exit 0; all checks passed.
- `python -m pytest tests/unit/cli/test_runtime.py -q`
  - Result: exit 1 initially; two failures:
    - runtime group help lacked a parser description;
    - `run-label-diagnostics` imported a symbol not exported by the package
      namespace before checking missing input.
  - Fixes:
    - added runtime parser description;
    - moved handler imports after `_load_mapping` so missing-input paths do not
      import runtime modules;
    - imported label diagnostics from its defining runtime module.
- `python -m ruff format src/alpha_system/cli/runtime.py tests/unit/cli/test_runtime.py && python -m ruff check src/alpha_system/cli/runtime.py src/alpha_system/cli/main.py tests/unit/cli/test_runtime.py && python -m pytest tests/unit/cli/test_runtime.py -q`
  - Result after fixes: exit 0; `28 passed in 0.40s`.
- `python -c "import alpha_system.cli.runtime"`
  - Result: exit 1; `ModuleNotFoundError: No module named 'alpha_system'`.
  - Reason: bare Python in this executor shell does not include `src/` on
    `PYTHONPATH`.
- `python -m alpha_system runtime --help`
  - Result: exit 1; `/usr/bin/python: No module named alpha_system`.
  - Reason: same source-layout `PYTHONPATH` issue.
- `PYTHONPATH=src python -c "import alpha_system.cli.runtime"`
  - Result: exit 0.
- `PYTHONPATH=src python -m alpha_system runtime --help`
  - Result: exit 0; help lists all planned runtime subcommands.
- `PYTHONPATH=src python -m alpha_system --help`
  - Result: exit 0; top-level help lists existing groups plus `runtime`.
- `python tools/verify.py --smoke`
  - Result: exit 0 with no stdout.
- `python -m pytest tests/unit/cli/test_runtime.py -q`
  - Result: exit 0; `28 passed in 0.41s`.
- `python -m pytest tests/unit/cli -q`
  - Result: exit 0; `41 passed in 1.03s`.
- `test -f docs/research_runtime/CLI.md`
  - Result: exit 0.
- `git ls-files runs`
  - Result: exit 0 with empty output.
- `git ls-files | grep -E '\.(parquet|arrow|feather|dbn|zst|sqlite|db|wal|log)$' | grep -v '^tests/fixtures/' || echo "no committed heavy/db/log artifacts"`
  - Result: exit 0; `no committed heavy/db/log artifacts`.
- Scoped changed-file scans for large files, data/artifact files, non-fixture
  parquet files, forbidden provider/heavy-reader references, and prohibited
  runtime-state literals.
  - Result: exit 0; no large files, data files, artifact files, non-fixture
    parquet files, or prohibited runtime-state literals found in changed source,
    test, and docs files. Provider/broker/live/paper terms only appear in
    safety-boundary wording.

Skipped:

- `git status --short`
  - Reason: explicitly forbidden by the executor safety override.
- `git diff --cached --name-only`
  - Reason: explicitly forbidden by the executor safety override; Codex staged
    no files.
- `git add`, `git commit`, `git push`, PR creation, merge, Claude review,
  `review.md`, and `verdict.json`
  - Reason: explicitly forbidden by the executor safety override; Ralph owns
    staging, commit, validation orchestration, review, verdict parsing, PR, CI,
    and merge gates.

## Artifact audit

- `git ls-files runs` returned empty output.
- The committed-heavy-artifact scan returned `no committed heavy/db/log
  artifacts`.
- Scoped size and local artifact scans returned empty output.
- No files were staged by Codex; therefore this executor introduced no staged
  `runs/` path and no staged forbidden data/cache/log/DB/heavy artifact.
- The Ralph staging list above contains no `runs/` path and no data/raw,
  data/canonical, data/factors, data/labels, data/cache, metadata DB, artifact
  bundle, parquet, arrow, feather, DBN, ZST, broker, live, paper, order-routing,
  provider-call, or deployment path.
- Because `git status` and `git diff --cached` are explicitly forbidden to this
  executor, the exact staged set could not be independently printed by Codex.

## Caveats and review needs

- The exact bare Python import/help commands in the generated spec fail in this
  executor shell unless `PYTHONPATH=src` is supplied. The source-path import and
  help commands pass, and pytest uses the repo test configuration.
- The run-local RT-P18 spec file was absent; the inline generated spec supplied
  by the user was used as the executable phase contract.
- Yellow-lane independent review artifacts are still required before merge, but
  Codex was explicitly forbidden from calling Claude, running reviewer, or
  creating `review.md` / `verdict.json`.
