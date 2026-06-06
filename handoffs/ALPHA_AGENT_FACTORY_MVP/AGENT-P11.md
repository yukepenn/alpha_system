# Handoff - AGENT-P11: Feature Engineer and Label Engineer Role Contracts

## Branch And Commit Context

- Phase: `AGENT-P11`
- Campaign: `ALPHA_AGENT_FACTORY_MVP`
- Executor: Codex
- Codex staging/commit/push: none. Per executor safety rules, Codex did not
  run `git add`, `git commit`, `git push`, create a PR, merge, call Claude, run
  reviewer, create `review.md`, create `verdict.json`, or mark the phase as
  accepted.

## Explicit File List For Ralph Staging

Codex left all changes unstaged. If Ralph accepts this executor output, stage
only these commit-eligible paths explicitly:

- `src/alpha_system/agent_factory/roles/feature_engineer.py`
- `src/alpha_system/agent_factory/roles/label_engineer.py`
- `tests/unit/agent_factory/roles/test_feature_engineer.py`
- `tests/unit/agent_factory/roles/test_label_engineer.py`
- `docs/agent_factory/roles/feature_engineer.md`
- `docs/agent_factory/roles/label_engineer.md`
- `templates/agent_factory/roles/feature_engineer.md`
- `templates/agent_factory/roles/label_engineer.md`
- `README.md`
- `handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P11.md`

No `runs/` path should be staged. No review artifact was created by Codex;
`reviews/ALPHA_AGENT_FACTORY_MVP/AGENT-P11/**` remains reviewer-owned.

## Scope Completed

- Added the contracts-only `feature_engineer` role module.
- Added the contracts-only `label_engineer` role module.
- Both roles self-register through the AGENT-P03 discovery registry at import
  time without editing `roles/__init__.py` or `roles/registry.py`.
- Both roles derive `callable_tools` from
  `permission_for(ROLE_ID).tool.allowed_tool_ids` and fail closed if the matrix
  grants materialization, runtime, review, promotion, broker, paper, or live
  tooling.
- Both role contracts populate purpose, readable inputs, callable tools,
  producible outputs, allowed decisions, forbidden decisions, handoff format,
  reviewer-independence rules, and failure modes.
- Both contracts encode accepted-`DatasetVersion` boundaries, no raw/external
  provider access, no self-review, no promotion, no broad materialization, no
  value commits, no label-as-feature, `FEATURE_LABEL_PARQUET_SINK_V1`, and
  `SESSION_LABEL_GUARD_FIX_V1` blockers.
- Added focused unit tests for registration, validation, populated fields,
  permission-matrix linkage, forbidden-boundary coverage, value-free outputs,
  and shared role-file isolation.
- Added durable role docs and operating prompt templates.
- Updated the root README campaign snapshot compactly for AGENT-P11.

No autonomous agent, runner, alpha search, diagnostics, implementation,
materialization, value computation, promotion, review, broker, paper, live,
order, deployment, provider, or raw-data operation was performed.

## Git Status

- `git status --short`: skipped. The executor prompt explicitly forbade running
  `git status`, `git diff`, `git add`, `git commit`, and `git push`.
- `git diff --cached --name-only`: skipped. The executor prompt explicitly
  forbade running `git diff`, and Codex staged no files.
- Staged-set audit: no staging was performed by Codex. Ralph owns authoritative
  staging and staged-set validation.

## Validation Commands

| Command | Result |
| --- | --- |
| `test ! -f runs/2026-06-06T193514Z_ALPHA_AGENT_FACTORY_MVP/STOP` | Exit 0; no active run STOP file at that path. |
| `test ! -f runs/2026-06-06T193514Z_ALPHA_AGENT_FACTORY_MVP/phases/AGENT-P11/STOP` | Exit 0; no active phase STOP file at that path. |
| `python -c "import alpha_system.agent_factory.roles.feature_engineer, alpha_system.agent_factory.roles.label_engineer"` | Exit 1; failed with `ModuleNotFoundError: No module named 'alpha_system'` because this shell does not put `src/` on `PYTHONPATH` for bare `python -c`. |
| `PYTHONPATH=src python -c "import alpha_system.agent_factory.roles.feature_engineer, alpha_system.agent_factory.roles.label_engineer; from alpha_system.agent_factory.roles import registry; assert registry.get('feature_engineer').role_id == 'feature_engineer'; assert registry.get('label_engineer').role_id == 'label_engineer'"` | Exit 0. |
| `python tools/verify.py --smoke` | Exit 0. |
| `python -m pytest tests/unit/agent_factory/roles/test_feature_engineer.py tests/unit/agent_factory/roles/test_label_engineer.py -q` | Exit 0; `14 passed in 0.04s`. |
| `test -f docs/agent_factory/roles/feature_engineer.md` | Exit 0. |
| `test -f docs/agent_factory/roles/label_engineer.md` | Exit 0. |
| `test -f templates/agent_factory/roles/feature_engineer.md` | Exit 0. |
| `test -f templates/agent_factory/roles/label_engineer.md` | Exit 0. |
| `git ls-files runs` | Exit 0; output was empty. |
| `rg -n "feature_engineer\|label_engineer" src/alpha_system/agent_factory/roles/__init__.py src/alpha_system/agent_factory/roles/registry.py` | Exit 1 with empty output; neither shared role package nor registry file hard-codes these role ids. |
| `find reviews -path '*AGENT-P11*' -print` | Exit 0 with empty output; Codex created no review artifacts. |
| `find src/alpha_system/agent_factory/roles tests/unit/agent_factory/roles docs/agent_factory/roles templates/agent_factory/roles handoffs/ALPHA_AGENT_FACTORY_MVP -type f \( -name '*.parquet' -o -name '*.arrow' -o -name '*.feather' -o -name '*.dbn' -o -name '*.zst' -o -name '*.sqlite' -o -name '*.db' -o -name '*.wal' -o -name '*.log' \) -print` | Exit 0 with empty output; no heavy/db/log artifact found under phase-owned paths. |
| `find runs -path '*AGENT-P11*' -print` | Exit 1; `runs` is absent in this worktree, so no run-local AGENT-P11 artifact was found. |

## Inspection Commands Run

These read-only commands were used to follow local patterns and scope:

- `sed -n '1,220p' .codex/skills/frontier-execute/SKILL.md`
- `pwd`
- `rg --files src/alpha_system/agent_factory/roles tests/unit/agent_factory/roles docs/agent_factory/roles templates/agent_factory/roles`
- `sed -n '1,220p' frontier.yaml`
- `sed -n '1,120p' ACTIVE_CAMPAIGN.md`
- `sed -n '1,260p' src/alpha_system/agent_factory/roles/contracts.py`
- `sed -n '1,220p' src/alpha_system/agent_factory/roles/registry.py`
- `sed -n '1,260p' src/alpha_system/agent_factory/roles/research_director.py`
- `sed -n '1,260p' src/alpha_system/agent_factory/roles/hypothesis_scout.py`
- `sed -n '1,280p' src/alpha_system/agent_factory/roles/alpha_spec_critic.py`
- `rg -n "def permission_for|feature_engineer|label_engineer|feature.request|label.validate_spec|allowed_tool_ids" src/alpha_system/agent_factory`
- `sed -n '1,260p' tests/unit/agent_factory/roles/test_research_director.py`
- `sed -n '1,280p' tests/unit/agent_factory/roles/test_hypothesis_scout.py`
- `sed -n '1,280p' tests/unit/agent_factory/roles/test_alpha_spec_critic.py`
- `sed -n '1,260p' src/alpha_system/agent_factory/permissions/matrix.py`
- `sed -n '1,280p' src/alpha_system/agent_factory/permissions/model.py`
- `sed -n '1,220p' docs/agent_factory/roles/research_director.md`
- `sed -n '1,260p' docs/agent_factory/roles/hypothesis_scout.md`
- `sed -n '1,240p' templates/agent_factory/roles/research_director.md`
- `sed -n '1,260p' templates/agent_factory/roles/hypothesis_scout.md`
- `sed -n '1,220p' README.md`
- `find handoffs -maxdepth 3 -type d`
- `find reviews -maxdepth 3 -type d`
- `sed -n '220,520p' src/alpha_system/agent_factory/roles/hypothesis_scout.py`
- `sed -n '1,220p' src/alpha_system/agent_factory/tools/results.py`
- `sed -n '1,220p' tests/unit/agent_factory/roles/test_contracts.py`
- `sed -n '1,220p' tests/unit/agent_factory/roles/test_registry.py`
- `sed -n '1,220p' handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P07.md`
- `sed -n '1,220p' handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P08.md`
- `sed -n '1,260p' docs/agent_factory/ROLES.md`
- `sed -n '1,260p' docs/agent_factory/PERMISSIONS.md`
- `sed -n '1,260p' docs/agent_factory/TOOLS.md`

## Skipped Checks

- `git status --short`: skipped because the executor prompt forbade running
  `git status`.
- `git diff --cached --name-only`: skipped because the executor prompt forbade
  running `git diff`; no staging was performed by Codex.
- `python tools/verify.py --all`: skipped because this phase added disjoint
  role modules, tests, docs, templates, and a README snapshot only; no shared
  behavior appeared affected beyond import-time self-registration.
- `python tools/hooks/canary_runner.py`: skipped for the same reason; no
  enforcement or boundary logic was changed.
- Review/`verdict.json`: skipped because the executor prompt explicitly forbade
  calling Claude, running reviewer, creating `review.md`, creating
  `verdict.json`, marking the phase accepted, creating a PR, or merging.

## Artifact Audit

- `git ls-files runs` returned empty output.
- No `runs/**` path is commit-eligible or listed for Ralph staging.
- No run-local handoff was written; this commit-eligible handoff is the only
  handoff written by Codex for AGENT-P11.
- No review artifact was created by Codex.
- No heavy/db/log artifact was found under the phase-owned paths inspected.
- No raw/canonical/factor/label/cache data path was created or edited.
- Codex staged no paths, so Codex staged no data/heavy/DB paths. Ralph should
  perform the authoritative staged-set audit before commit.

## Caveats And Review Focus

- The literal bare `python -c` import command cannot resolve the repository
  `src/` layout in this shell. The same import and registry lookup succeeded
  with `PYTHONPATH=src`, and targeted pytest passed.
- The current AGENT-P04 permission matrix grants the Feature Engineer
  `feature.reference_seed_pack`, `feature.draft_request`, and
  `feature.validate_request`; it grants the Label Engineer
  `label.reference_seed_pack`, `label.draft_spec`, and `label.validate_spec`.
  The role contracts intentionally derive from those matrix entries rather than
  hard-code the tool list as authority.
- The run artifact directory named in the executor prompt is absent in this
  worktree. STOP checks still fail closed by testing the expected STOP paths,
  and no run-local AGENT-P11 artifact was found.
