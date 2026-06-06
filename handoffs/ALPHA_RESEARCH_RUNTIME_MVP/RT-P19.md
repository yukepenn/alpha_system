# ALPHA_RESEARCH_RUNTIME_MVP / RT-P19 Handoff

## Repair summary

Bounded repair attempt addressed Claude review finding B1 only. The ignored
`**/cache/` path collision was removed from the commit-eligible implementation
surface by moving the runtime cache policy module from the ignored package path
to `src/alpha_system/runtime/cache_policy.py` and moving its tests to
`tests/unit/runtime/test_cache_policy.py`.

Docs, README, tests, and this handoff now refer to
`alpha_system.runtime.cache_policy`. The old ignored Python source/test files
under `src/alpha_system/runtime/cache/` and `tests/unit/runtime/cache/` were
removed from collection; ignored bytecode directories may remain local-only.

No Claude call, reviewer run, `review.md`, `verdict.json`, PR, merge,
live/paper/broker operation, deployment, or phase PASS marking was performed.

## Curated file list for explicit staging

- `README.md`
- `docs/research_runtime/CACHE_AND_ARTIFACTS.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P19.md`
- `src/alpha_system/runtime/artifact_policy.py`
- `src/alpha_system/runtime/cache_policy.py`
- `tests/unit/runtime/test_artifact_policy.py`
- `tests/unit/runtime/test_cache_policy.py`

No `runs/` path is included. No review artifacts are included.

## Implementation summary

RT-P19 adds a pure runtime artifact policy at
`alpha_system.runtime.artifact_policy`. The classifier takes value-free output
descriptors and returns `commit_allowed` vs `local_only`, manifest flags,
reasons, and forbidden output classes. It keeps heavy/value-bearing/provider
responses/local DBs/logs/caches/`runs/**` outputs local-only, and only marks
small curated row-free summaries as commit-eligible.

RT-P19 also adds `alpha_system.runtime.cache_policy`, with `RuntimeCachePolicy`
and supporting immutable metadata contracts. The policy derives deterministic
derived-summary cache keys from dataset, feature, label, code, config, optional
cost-model, and run-scope lineage. Lookup classification is metadata-only:
`hit`, `miss`, or `stale`. Cache root resolution prefers local data roots
outside the repository tree and can classify explicit `runs/**` roots as
local-only run artifacts.

The change is additive and orchestration-only. It performs no diagnostics,
probe, grid, cost, provider, broker, live, paper, deployment, daemon,
scheduler, or distributed-cache work.

## Tests and docs

Added focused tests covering:

- heavy/value-bearing/provider/DB/log/cache outputs classified local-only;
- only small curated row-free summaries classified `commit_allowed`;
- `runs/**` never classified commit-eligible;
- cache keys change when dataset, feature, label, code, config, or run-scope
  lineage changes;
- hit/miss/stale lookup decisions;
- cache roots resolving outside the repo tree for local data roots;
- in-repo local data roots rejected;
- explicit `runs/**` roots classified local-only;
- value-bearing cache summary kinds rejected.

Added `docs/research_runtime/CACHE_AND_ARTIFACTS.md` documenting the
commit-eligible/local-only partition, lineage-keyed invalidation, storage-root
policy, and no-claim/no-provider/no-broker boundary.

Updated `README.md` with the compact RT-P19 snapshot, next phase pointer
(`RT-P20`), new durable modules/docs, and unchanged safety boundaries.

## Git status

`git status --short` after repair and before explicit staging:

```text
 M README.md
?? docs/research_runtime/CACHE_AND_ARTIFACTS.md
?? handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P19.md
?? src/alpha_system/runtime/artifact_policy.py
?? src/alpha_system/runtime/cache_policy.py
?? tests/unit/runtime/test_artifact_policy.py
?? tests/unit/runtime/test_cache_policy.py
```

`git status --short` after explicit staging:

```text
M  README.md
A  docs/research_runtime/CACHE_AND_ARTIFACTS.md
A  handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P19.md
A  src/alpha_system/runtime/artifact_policy.py
A  src/alpha_system/runtime/cache_policy.py
A  tests/unit/runtime/test_artifact_policy.py
A  tests/unit/runtime/test_cache_policy.py
```

`git diff --cached --name-only` after explicit staging:

```text
README.md
docs/research_runtime/CACHE_AND_ARTIFACTS.md
handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P19.md
src/alpha_system/runtime/artifact_policy.py
src/alpha_system/runtime/cache_policy.py
tests/unit/runtime/test_artifact_policy.py
tests/unit/runtime/test_cache_policy.py
```

## Validation

- `python -m ruff format src/alpha_system/runtime/artifact_policy.py src/alpha_system/runtime/cache_policy.py tests/unit/runtime/test_artifact_policy.py tests/unit/runtime/test_cache_policy.py`
  - Result: exit 0; `4 files left unchanged`.
- `python -m ruff check src/alpha_system/runtime/artifact_policy.py src/alpha_system/runtime/cache_policy.py tests/unit/runtime/test_artifact_policy.py tests/unit/runtime/test_cache_policy.py`
  - Result: exit 0; `All checks passed!`.
- `if git check-ignore -q -- src/alpha_system/runtime/cache_policy.py tests/unit/runtime/test_cache_policy.py src/alpha_system/runtime/artifact_policy.py tests/unit/runtime/test_artifact_policy.py docs/research_runtime/CACHE_AND_ARTIFACTS.md handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P19.md README.md; then echo 'ignored commit-eligible path'; exit 1; else test $? -eq 1; fi`
  - Result: exit 1; invalid command form, `fatal: --quiet is only valid with a single pathname`.
  - Follow-up used a per-path loop.
- `for path in src/alpha_system/runtime/cache_policy.py tests/unit/runtime/test_cache_policy.py src/alpha_system/runtime/artifact_policy.py tests/unit/runtime/test_artifact_policy.py docs/research_runtime/CACHE_AND_ARTIFACTS.md handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P19.md README.md; do if git check-ignore -q -- "$path"; then echo "ignored: $path"; exit 1; fi; done`
  - Result: exit 0 with empty output; every curated path is trackable.
- `rg --pcre2 -n "alpha_system\\.runtime\\.cache(?!_policy)|src/alpha_system/runtime/cache/|tests/unit/runtime/cache/test_policy|tests/unit/runtime/cache(\\s|$)|cache/__init__|cache/policy|test_policy.py" README.md docs/research_runtime/CACHE_AND_ARTIFACTS.md handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P19.md tests/unit/runtime/test_cache_policy.py src/alpha_system/runtime/cache_policy.py`
  - Result: exit 0; remaining matches are intentional handoff mentions of the
    replaced ignored paths and the cache metadata schema string.
- `find README.md docs/research_runtime/CACHE_AND_ARTIFACTS.md handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P19.md src/alpha_system/runtime/artifact_policy.py src/alpha_system/runtime/cache_policy.py tests/unit/runtime/test_artifact_policy.py tests/unit/runtime/test_cache_policy.py -type f -size +1M -print`
  - Result: exit 0 with empty output.
- `find README.md docs/research_runtime/CACHE_AND_ARTIFACTS.md handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P19.md src/alpha_system/runtime/artifact_policy.py src/alpha_system/runtime/cache_policy.py tests/unit/runtime/test_artifact_policy.py tests/unit/runtime/test_cache_policy.py -type f \( -name '*.parquet' -o -name '*.arrow' -o -name '*.feather' -o -name '*.dbn' -o -name '*.zst' -o -name '*.sqlite' -o -name '*.db' -o -name '*.wal' -o -name '*.log' \) -print`
  - Result: exit 0 with empty output.
- `python -m pytest tests/unit/runtime/test_cache_policy.py tests/unit/runtime/test_artifact_policy.py -q`
  - Result: exit 0; `26 passed in 0.04s`.
- `python -c "import alpha_system.runtime.artifact_policy"`
  - Result: exit 1; `ModuleNotFoundError: No module named 'alpha_system'`.
  - Reason: bare Python in this executor shell does not include `src/` on
    `PYTHONPATH`; this matches the prior source-layout caveat.
- `PYTHONPATH=src python -c "import alpha_system.runtime.artifact_policy; import alpha_system.runtime.cache_policy"`
  - Result: exit 0.
- `test -f docs/research_runtime/CACHE_AND_ARTIFACTS.md`
  - Result: exit 0.
- `python -m pytest tests/unit/runtime -q`
  - Result: exit 0; `197 passed in 0.38s`.
- `python tools/verify.py --smoke`
  - Result: exit 0 with no stdout.
- `python tools/hooks/canary_runner.py`
  - Result: exit 0; all Frontier canaries passed.
- `git ls-files runs`
  - Result: exit 0 with empty output.
- `git add README.md docs/research_runtime/CACHE_AND_ARTIFACTS.md handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P19.md src/alpha_system/runtime/artifact_policy.py src/alpha_system/runtime/cache_policy.py tests/unit/runtime/test_artifact_policy.py tests/unit/runtime/test_cache_policy.py`
  - Result: exit 0.
- `git diff --cached --name-only`
  - Result: exit 0; exact staged list shown above.
- `git diff --cached --name-only | rg '^runs/' || true`
  - Result: exit 0 with empty output.
- `git diff --cached --name-only | rg '(\\.parquet$|\\.arrow$|\\.feather$|\\.dbn$|\\.zst$|\\.sqlite$|\\.db$|\\.wal$|\\.log$|^data/(raw|canonical|factors|labels|cache)/|^metadata/|^artifacts/)' || true`
  - Result: exit 0 with empty output.
- `git diff --cached --check`
  - Result: exit 0.
- `python tools/verify.py --all`
  - Result: exit 1; `13 failed, 2366 passed in 36.48s`.
  - Failures were in existing Frontier/GitHub driver tests:
    `tests/test_github_utils.py::test_dry_run_pr_does_not_call_network` and
    12 `tests/test_ralph_driver.py` provider-wired / push-block / DAG-wave
    tests. The repaired runtime tests passed inside this broader run.

## Artifact audit

- `git ls-files runs` returned empty output.
- `git diff --cached --name-only` contains no `runs/` path.
- `git diff --cached --name-only` contains no heavy artifact, value data, DB,
  log, metadata, `data/**`, or `artifacts/**` path.
- The curated staging list contains no `runs/` path and no data/raw,
  data/canonical, data/factors, data/labels, data/cache, metadata DB, artifact
  bundle, parquet, arrow, feather, DBN, ZST, broker, live, paper,
  order-routing, provider-call, or deployment path.
- `git check-ignore` per-path audit confirmed the replacement source and test
  files are not ignored by `.gitignore`.
- Ignored Python bytecode cache directories may remain under runtime/test
  paths; they are local-only, excluded by `.gitignore`, and not staged.

## Caveats and review needs

- The generated spec named `src/alpha_system/runtime/cache/**` and
  `tests/unit/runtime/cache/**`; the repair intentionally substitutes
  trackable paths to close review finding B1 without loosening `.gitignore` or
  forcing ignored files into git.
- The exact bare import command from the generated spec fails in this executor
  shell unless `PYTHONPATH=src` is supplied. The source-layout import succeeds,
  and pytest uses the repo test configuration.
- `RuntimeArtifactManifest` and the RT-P18 CLI were not edited because they are
  outside the generated allowed-path list for this executor. The new policy
  exposes manifest flags and equivalent classification for consumers to use.
- Yellow-lane independent review artifacts are still required before merge, but
  Codex was explicitly forbidden from calling Claude, running reviewer, or
  creating `review.md` / `verdict.json`.
- After the explicit staging audit, Codex updated this handoff with the staged
  audit details but could not re-stage that final handoff edit or commit:
  `git add handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P19.md && git diff --cached --name-only && git diff --cached --check && git status --short`
  failed with `fatal: Unable to create '/home/yuke_zhang/projects/alpha_system/.git/worktrees/alpha_system-alpha_research_runtime_mvp-rt-p19/index.lock': Read-only file system`.
  The real gitdir for this worktree resolves outside the writable root at
  `/home/yuke_zhang/projects/alpha_system/.git/worktrees/alpha_system-alpha_research_runtime_mvp-rt-p19`.
  The cached staged set remains the seven curated paths listed above; this
  handoff file has an unstaged follow-up edit containing the final audit.
