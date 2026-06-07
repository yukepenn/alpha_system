# AGENT-P19 Executor Handoff

Campaign: `ALPHA_AGENT_FACTORY_MVP`
Phase: `AGENT-P19` - Agent Prompt and Skill Assets
Executor: Codex

## Scope Executed

Created the AGENT-P19 prompt source-of-truth directory and ten per-role prompt
/ skill templates under `templates/agent_factory/prompts/`. Each role prompt
states the `AgentRole` contract fields: purpose, readable inputs, callable
tools, producible structured `AgentToolResult` outputs, allowed decisions,
forbidden decisions/actions, required handoff format, reviewer-independence
rules, and expected failure/rejection modes.

Updated the root `README.md` with a compact campaign snapshot for the
`assets_and_bridge` gate and the new prompt index surface. The snapshot keeps
the safety boundaries unchanged: contracts/templates only, no autonomous
agent, no continuous research runner, no alpha/factor/strategy scope, no
broker/live/paper/order scope, accepted-DatasetVersion-only through
`resolve_dataset_version`, and runtime/governance/registry primitives consumed
rather than edited.

## Executor Staging

No files were staged by the executor. The executor prompt explicitly forbade
`git add`, `git commit`, `git push`, `git status`, and `git diff`, and required
all changes to remain unstaged for the Ralph driver.

Expected explicit commit-eligible file list for Ralph staging:

- `README.md`
- `templates/agent_factory/prompts/README.md`
- `templates/agent_factory/prompts/research_director.md`
- `templates/agent_factory/prompts/hypothesis_scout.md`
- `templates/agent_factory/prompts/alpha_spec_critic.md`
- `templates/agent_factory/prompts/data_contract_auditor.md`
- `templates/agent_factory/prompts/feature_engineer.md`
- `templates/agent_factory/prompts/label_engineer.md`
- `templates/agent_factory/prompts/no_lookahead_auditor.md`
- `templates/agent_factory/prompts/diagnostics_runner.md`
- `templates/agent_factory/prompts/statistical_reviewer.md`
- `templates/agent_factory/prompts/librarian.md`
- `handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P19.md`

## `git status --short`

Skipped. The executor prompt explicitly forbade running `git status`.

## Commands Run

Context and contract inspection:

- `sed -n '1,220p' .codex/skills/frontier-execute/SKILL.md` - exit 0; read Frontier executor skill.
- `sed -n '1,240p' frontier.yaml` - exit 0; read control-plane rules.
- `sed -n '1,200p' ACTIVE_CAMPAIGN.md` - exit 0; read campaign pointer; not edited.
- `rg --files campaigns specs handoffs reviews docs templates src tests tools | sed -n '1,240p'` - exit 0; inspected repo surfaces.
- `rg -n "AgentRole|AgentToolResult|resolve_dataset_version|DatasetVersion|tool registry|tool_registry|permission|queue|memory|rejected|research memory|librarian|research_director|hypothesis_scout|alpha_spec_critic|data_contract_auditor|feature_engineer|label_engineer|no_lookahead_auditor|diagnostics_runner|statistical_reviewer" src docs specs campaigns templates tests tools -S` - exit 0; located role, tool, queue, memory, and template references.
- `find templates/agent_factory -maxdepth 3 -type f | sort` - exit 0; found existing template roots.
- `sed -n '1,220p' src/alpha_system/agent_factory/roles/contracts.py` - exit 0; read `AgentRole`.
- `sed -n '1,260p' src/alpha_system/agent_factory/tools/contracts.py` - exit 0; read tool contract fields.
- `sed -n '1,260p' src/alpha_system/agent_factory/tools/results.py` - exit 0; read `AgentToolResult`.
- `sed -n '1,240p' docs/agent_factory/NAMING.md` - exit 0; read naming/index policy.
- `sed -n '1,260p' src/alpha_system/agent_factory/roles/research_director.py` - exit 0; read role contract.
- `sed -n '1,260p' src/alpha_system/agent_factory/roles/hypothesis_scout.py` - exit 0; read role contract.
- `sed -n '1,260p' src/alpha_system/agent_factory/roles/alpha_spec_critic.py` - exit 0; read role contract.
- `sed -n '1,300p' src/alpha_system/agent_factory/roles/data_contract_auditor.py` - exit 0; read role contract.
- `sed -n '1,260p' src/alpha_system/agent_factory/roles/feature_engineer.py` - exit 0; read role contract.
- `sed -n '1,260p' src/alpha_system/agent_factory/roles/label_engineer.py` - exit 0; read role contract.
- `sed -n '1,280p' src/alpha_system/agent_factory/roles/no_lookahead_auditor.py` - exit 0; read role contract.
- `sed -n '1,300p' src/alpha_system/agent_factory/roles/diagnostics_runner.py` - exit 0; read role contract.
- `sed -n '1,300p' src/alpha_system/agent_factory/roles/statistical_reviewer.py` - exit 0; read role contract.
- `sed -n '1,320p' src/alpha_system/agent_factory/roles/librarian.py` - exit 0; read role contract.
- `python - <<'PY' ...` role registry extraction - exit 1; failed because `alpha_system` was not on `PYTHONPATH`.
- `PYTHONPATH=src python - <<'PY' ... registry.all_role_ids()` - exit 1; failed because registry exposes `all_roles()`, not `all_role_ids()`.
- `PYTHONPATH=src python - <<'PY' ... registry.all_roles()` - exit 0; extracted full role contract fields and callable tool names.
- `git ls-files templates/agent_factory/roles templates/agent_factory/README.md README.md handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P19.md templates/agent_factory/prompts` - exit 0; confirmed existing role templates are tracked from prior phases and prompt files were not yet tracked.
- `sed -n '1,240p' README.md` - exit 0; read root README before snapshot edit.
- `sed -n '1,220p' templates/agent_factory/README.md` - exit 0; read template root index.
- `sed -n '1,220p' campaigns/ALPHA_AGENT_FACTORY_MVP/PHASE_PLAN.md` - exit 0; read campaign phase plan.
- `sed -n '1,240p' campaigns/ALPHA_AGENT_FACTORY_MVP/ACCEPTANCE.md` - exit 0; read acceptance criteria.
- `mkdir -p templates/agent_factory/prompts handoffs/ALPHA_AGENT_FACTORY_MVP` - exit 0; created allowed output directories.

Post-edit structure checks:

- `find templates/agent_factory/prompts -maxdepth 1 -type f | sort` - exit 0; listed `README.md` plus all ten role prompt files.
- `sed -n '1,220p' templates/agent_factory/prompts/README.md` - exit 0; inspected prompt index.
- `sed -n '1,190p' README.md` - exit 0; inspected README snapshot.
- `rg -n "Purpose|Readable Inputs|Callable Tools|Producible Outputs|Allowed Decisions|Forbidden Decisions|Required Handoff Format|Reviewer-Independence Rules|Expected Failure" templates/agent_factory/prompts/*.md` - exit 0; every role prompt contains the required contract sections.

Requested validation:

- `python tools/verify.py --smoke` - exit 0.
- `test -f templates/agent_factory/prompts/README.md` - exit 0.
- `test -d templates/agent_factory/prompts` - exit 0.
- `git ls-files runs` - exit 0 with empty output.
- Per-role prompt presence loop - exit 0; output:
  - `prompt OK: research_director`
  - `prompt OK: hypothesis_scout`
  - `prompt OK: alpha_spec_critic`
  - `prompt OK: data_contract_auditor`
  - `prompt OK: feature_engineer`
  - `prompt OK: label_engineer`
  - `prompt OK: no_lookahead_auditor`
  - `prompt OK: diagnostics_runner`
  - `prompt OK: statistical_reviewer`
  - `prompt OK: librarian`
- Prompt scatter check:
  `grep -RIl "AgentRole\|reviewer-independence\|forbidden decisions" templates/agent_factory 2>/dev/null | grep -v "^templates/agent_factory/prompts/" || echo "no scattered prompt assets outside templates/agent_factory/prompts/"` - exit 0; output: `no scattered prompt assets outside templates/agent_factory/prompts/`.

## Skipped Checks

- `git status --short` - skipped because the executor prompt forbade `git status`.
- `git diff --staged -- README.md` - skipped because the executor prompt forbade `git diff` and no staging was performed.
- `git diff --cached --name-only` - skipped because the executor prompt forbade `git diff` and Ralph owns authoritative staging/audit.
- Claude review, `review.md`, and `verdict.json` - skipped by executor instruction; Ralph owns review routing.

## Artifact Audit

- `git ls-files runs` returned empty.
- No `runs/**` file was created or edited by this executor.
- No run-local handoff was written.
- No `.claude/agents/**`, `docs/agent_factory/**`, `src/**`, `ACTIVE_CAMPAIGN.md`, data, cache, DB, log, or heavy artifact path was edited by this executor.
- No files were staged. The expected Ralph staging list contains only allowed prompt assets, the root README snapshot, and this commit-eligible handoff; it contains no `runs/**`, forbidden, heavy, DB, cache, or log path.

## README Snapshot Confirmation

The `README.md` snapshot is factual and compact. It states that the
`assets_and_bridge` gate is in progress, names `AGENT-P19` and next Wave 3
work, lists the new prompt asset surface, and restates unchanged safety
boundaries. It does not include run-local details, local artifact paths, or
alpha/profitability/tradability/broker/live/paper/deployment claims.

## Caveats

- The executor did not self-approve the phase and did not create review
  artifacts.
- Because the executor prompt forbade `git status` and `git diff`, the staged
  set and cached diff audits must be performed by Ralph after explicit staging.
