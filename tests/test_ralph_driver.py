from __future__ import annotations

import ast
import json
import re
import shutil
from pathlib import Path

import pytest

from tools.frontier import ralph_driver


REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_CAMPAIGN_ID = "SAMPLE_WORKFLOW2_CAMPAIGN"


def copy_campaign(tmp_root: Path, campaign_id: str) -> None:
    source = REPO_ROOT / "campaigns" / campaign_id
    target = tmp_root / "campaigns" / campaign_id
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)


def write_sample_campaign(tmp_root: Path, campaign_id: str = SAMPLE_CAMPAIGN_ID) -> None:
    campaign_dir = tmp_root / "campaigns" / campaign_id
    campaign_dir.mkdir(parents=True, exist_ok=True)
    (campaign_dir / "GOAL.md").write_text(f"# {campaign_id}\n\nExercise generic Workflow 2.\n", encoding="utf-8")
    (campaign_dir / "PHASE_PLAN.md").write_text(
        "# Phase Plan\n\n| Phase | Name | Lane | Dependencies |\n"
        "| --- | --- | --- | --- |\n"
        "| P00 | Prepare fixture | YELLOW | none |\n"
        "| P01 | Validate fixture | GREEN | P00 |\n",
        encoding="utf-8",
    )
    (campaign_dir / "campaign.yaml").write_text(
        f"""campaign_id: "{campaign_id}"
workflow: "workflow2"
default_lane: "yellow"
limits:
  max_phases: 2
phases:
  - id: "P00"
    name: "Prepare fixture"
    lane: "YELLOW"
    dependencies: []
  - id: "P01"
    name: "Validate fixture"
    lane: "GREEN"
    dependencies: ["P00"]
""",
        encoding="utf-8",
    )
    for name in ("ACCEPTANCE.md", "RISK_REGISTER.md", "RUNBOOK.md"):
        (campaign_dir / name).write_text(f"# {name}\n\nLocal test fixture.\n", encoding="utf-8")


def latest_run(tmp_root: Path, campaign_id: str) -> Path:
    matches = sorted((tmp_root / "runs").glob(f"*{campaign_id}*"))
    assert matches
    return matches[-1]


def pass_count(run_dir: Path) -> int:
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    return sum(1 for phase in state["phases"] if phase["status"] == "PASS")


def state_json(run_dir: Path) -> dict:
    return json.loads((run_dir / "state.json").read_text(encoding="utf-8"))


def stub_validation(monkeypatch) -> None:
    monkeypatch.setattr(
        ralph_driver,
        "run_validation_commands",
        lambda: (True, "# Validation\n\nMock validation passed.\n"),
    )


def test_generic_campaign_yaml_phases_are_loaded(tmp_path, monkeypatch) -> None:
    write_sample_campaign(tmp_path)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)

    campaign = ralph_driver.load_ledger_campaign(SAMPLE_CAMPAIGN_ID)

    assert campaign.campaign_id == SAMPLE_CAMPAIGN_ID
    assert [phase.phase_id for phase in campaign.phases] == ["P00", "P01"]
    assert campaign.phases[0].name == "Prepare fixture"
    assert campaign.phases[0].lane == "YELLOW"
    assert campaign.phases[1].dependencies == ("P00",)


def test_ledger_only_run_creates_required_artifacts(tmp_path, monkeypatch) -> None:
    write_sample_campaign(tmp_path)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)

    status = ralph_driver.run_campaign(SAMPLE_CAMPAIGN_ID, None, "yellow", ledger_only=True)

    assert status == 0
    run_dir = latest_run(tmp_path, SAMPLE_CAMPAIGN_ID)
    for name in (
        "RUN_GOAL.md",
        "PHASE_PLAN.md",
        "state.json",
        "events.jsonl",
        "progress.txt",
        "costs.jsonl",
        "RUN_SUMMARY.md",
        "STOP",
    ):
        assert (run_dir / name).is_file(), name

    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    assert state["campaign_id"] == SAMPLE_CAMPAIGN_ID
    assert state["workflow"] == "workflow2"
    assert state["driver"] == ralph_driver.LEDGER_ONLY_DRIVER
    assert state["status"] == "LEDGER_ONLY_READY"
    assert len(state["phases"]) == 2
    assert all(phase["status"] == "PENDING" for phase in state["phases"])
    assert all(phase["execution_mode"] == "ledger_only" for phase in state["phases"])
    assert state["phase_execution_performed"] is False
    assert state["external_providers_called"] is False
    assert state["network_used"] is False
    assert state["github_operations_performed"] is False
    assert state["auto_merge_performed"] is False
    assert state["broker_or_trading_operations_performed"] is False


def test_provider_wired_env_max_phases_one_runs_exactly_one_mock_phase(tmp_path, monkeypatch) -> None:
    write_sample_campaign(tmp_path)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.setenv("FRONTIER_MOCK_PROVIDERS", "1")
    monkeypatch.setenv("FRONTIER_MAX_PHASES", "1")
    stub_validation(monkeypatch)

    status = ralph_driver.main(
        [
            "run",
            "--campaign-id",
            SAMPLE_CAMPAIGN_ID,
            "--provider-wired",
        ]
    )

    assert status == 0
    run_dir = latest_run(tmp_path, SAMPLE_CAMPAIGN_ID)
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    assert state["driver"] == ralph_driver.PROVIDER_WIRED_DRIVER
    assert state["max_phases_requested"] == 1
    assert state["max_phases_source"] == "env"
    assert state["status"] == "STOPPED"
    assert pass_count(run_dir) == 1
    assert state["phases"][0]["status"] == "PASS"
    assert state["phases"][1]["status"] == "PENDING"
    assert (run_dir / "STOP").is_file()
    assert (run_dir / "phases/P00/spec_prompt.md").is_file()
    assert (run_dir / "phases/P00/executor_output.md").is_file()
    assert (run_dir / "phases/P00/validation.md").is_file()
    assert (run_dir / "phases/P00/review.md").is_file()
    assert (run_dir / "phases/P00/verdict.json").is_file()
    assert (run_dir / "phases/P00/done_check.json").is_file()
    assert (run_dir / "phases/P00/ci_status.json").is_file()
    assert (run_dir / "phases/P00/merge_gate.json").is_file()
    assert (run_dir / "heartbeat.json").is_file()


def test_provider_wired_default_mock_campaign_is_not_hard_coded_to_one_phase(tmp_path, monkeypatch) -> None:
    write_sample_campaign(tmp_path)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.setenv("FRONTIER_MOCK_PROVIDERS", "1")
    monkeypatch.delenv("FRONTIER_MAX_PHASES", raising=False)
    stub_validation(monkeypatch)

    status = ralph_driver.run_campaign(SAMPLE_CAMPAIGN_ID, None, "yellow", provider_wired=True)

    assert status == 0
    run_dir = latest_run(tmp_path, SAMPLE_CAMPAIGN_ID)
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    assert state["max_phases_source"] == "campaign"
    assert state["max_phases_requested"] == 2
    assert state["status"] == "COMPLETED"
    assert pass_count(run_dir) == 2
    assert (run_dir / "STOP").is_file()
    assert (run_dir / "campaign_done_check.json").is_file()


def test_mock_review_rework_then_repair_passes(tmp_path, monkeypatch) -> None:
    write_sample_campaign(tmp_path)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.setenv("FRONTIER_MOCK_PROVIDERS", "1")
    monkeypatch.setenv("FRONTIER_MAX_PHASES", "1")
    stub_validation(monkeypatch)
    responses = iter(
        [
            "# Review\n\n- Must repair mock issue.\n\nVERDICT: REWORK\n",
            "# Review\n\n- Repair accepted.\n\nVERDICT: PASS\n",
        ]
    )
    monkeypatch.setattr(ralph_driver, "mock_review_text", lambda phase: next(responses))

    status = ralph_driver.run_campaign(SAMPLE_CAMPAIGN_ID, None, "yellow", provider_wired=True)

    assert status == 0
    run_dir = latest_run(tmp_path, SAMPLE_CAMPAIGN_ID)
    state = state_json(run_dir)
    assert state["repair_attempts"]["P00"] == 1
    assert state["phases"][0]["status"] == "PASS"
    assert (run_dir / "phases/P00/repair_attempts/001/repair_verdict.json").is_file()


def test_repair_attempts_are_capped(tmp_path, monkeypatch) -> None:
    write_sample_campaign(tmp_path)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.setenv("FRONTIER_MOCK_PROVIDERS", "1")
    monkeypatch.setenv("FRONTIER_MAX_PHASES", "1")
    monkeypatch.setenv("FRONTIER_MAX_REPAIR_ATTEMPTS", "1")
    stub_validation(monkeypatch)
    monkeypatch.setattr(
        ralph_driver,
        "mock_review_text",
        lambda phase: "# Review\n\n- Still incomplete.\n\nVERDICT: REWORK\n",
    )

    status = ralph_driver.run_campaign(SAMPLE_CAMPAIGN_ID, None, "yellow", provider_wired=True)

    assert status == 0
    run_dir = latest_run(tmp_path, SAMPLE_CAMPAIGN_ID)
    state = state_json(run_dir)
    assert state["status"] == "STOPPED"
    assert state["phases"][0]["status"] == "BLOCKED"
    assert state["repair_attempts"]["P00"] == 1


def test_resume_from_spec_ready_continues_without_regenerating_spec(tmp_path, monkeypatch) -> None:
    write_sample_campaign(tmp_path)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.setenv("FRONTIER_MOCK_PROVIDERS", "1")
    stub_validation(monkeypatch)
    campaign = ralph_driver.load_ledger_campaign(SAMPLE_CAMPAIGN_ID)
    run_dir = ralph_driver.initialize_provider_wired_run(campaign, 1, "test")
    state = state_json(run_dir)
    phase = state["phases"][0]
    phase["status"] = "SPEC_READY"
    state["current_phase_id"] = "P00"
    phase_dir = run_dir / "phases/P00"
    phase_dir.mkdir(parents=True)
    (phase_dir / "spec.md").write_text("# Existing Spec\n", encoding="utf-8")
    ralph_driver.write_state(run_dir, state)

    status = ralph_driver.continue_provider_wired_run(run_dir, state, 1, "test")

    assert status == 0
    assert (phase_dir / "spec.md").read_text(encoding="utf-8") == "# Existing Spec\n"
    assert state_json(run_dir)["phases"][0]["status"] == "PASS"


def test_resume_from_executed_continues_to_review(tmp_path, monkeypatch) -> None:
    write_sample_campaign(tmp_path)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.setenv("FRONTIER_MOCK_PROVIDERS", "1")
    stub_validation(monkeypatch)
    campaign = ralph_driver.load_ledger_campaign(SAMPLE_CAMPAIGN_ID)
    run_dir = ralph_driver.initialize_provider_wired_run(campaign, 1, "test")
    state = state_json(run_dir)
    phase = state["phases"][0]
    phase["status"] = "EXECUTED"
    state["current_phase_id"] = "P00"
    phase_dir = run_dir / "phases/P00"
    phase_dir.mkdir(parents=True)
    (phase_dir / "spec.md").write_text("# Existing Spec\n", encoding="utf-8")
    (phase_dir / "executor_output.md").write_text("# Existing Execution\n", encoding="utf-8")
    ralph_driver.write_state(run_dir, state)

    status = ralph_driver.continue_provider_wired_run(run_dir, state, 1, "test")

    assert status == 0
    assert (phase_dir / "validation.md").is_file()
    assert state_json(run_dir)["phases"][0]["status"] == "PASS"


def test_claude_headless_streams_large_review_prompt(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("FRONTIER_MOCK_PROVIDERS", raising=False)
    monkeypatch.setenv("FRONTIER_CLAUDE_CMD", "claude")
    calls = []

    class FakeRunner:
        def __init__(self, root: Path) -> None:
            self.root = root

        def run(self, command, **kwargs):
            from tools.frontier.command_runner import CommandResult as RunnerResult

            calls.append((list(command), kwargs))
            return RunnerResult(
                command=list(command),
                return_code=0,
                stdout="# Review\n\nVERDICT: PASS\n",
                stderr="",
                duration_ms=0,
            )

    monkeypatch.setattr(ralph_driver, "CommandRunner", FakeRunner)
    prompt = "# Review Prompt\n\n" + ("x" * 200_000)

    result = ralph_driver.claude_headless(prompt, root=tmp_path)

    assert result.returncode == 0
    command, kwargs = calls[0]
    assert kwargs["stdin_text"] == prompt
    assert prompt not in command
    assert sum(len(part) for part in command) < 1000


def test_run_lock_prevents_duplicate_driver(tmp_path) -> None:
    run_dir = tmp_path / "runs/run1"
    run_dir.mkdir(parents=True)

    with ralph_driver.run_lock(run_dir):
        with pytest.raises(RuntimeError):
            with ralph_driver.run_lock(run_dir):
                pass


def test_stop_prevents_next_phase(tmp_path, monkeypatch) -> None:
    write_sample_campaign(tmp_path)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.setenv("FRONTIER_MOCK_PROVIDERS", "1")
    campaign = ralph_driver.load_ledger_campaign(SAMPLE_CAMPAIGN_ID)
    run_dir = ralph_driver.initialize_provider_wired_run(campaign, 1, "test")
    state = state_json(run_dir)
    (run_dir / "STOP").write_text("stop\n", encoding="utf-8")

    status = ralph_driver.continue_provider_wired_run(run_dir, state, 1, "test")

    assert status == 0
    assert state_json(run_dir)["status"] == "STOPPED"
    assert pass_count(run_dir) == 0


def test_budget_stop(tmp_path, monkeypatch) -> None:
    write_sample_campaign(tmp_path)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.setenv("FRONTIER_MOCK_PROVIDERS", "1")
    monkeypatch.setenv("FRONTIER_MAX_RUN_MINUTES", "1")
    campaign = ralph_driver.load_ledger_campaign(SAMPLE_CAMPAIGN_ID)
    run_dir = ralph_driver.initialize_provider_wired_run(campaign, 1, "test")
    state = state_json(run_dir)
    state["started_at"] = "2000-01-01T00:00:00Z"
    ralph_driver.write_state(run_dir, state)

    status = ralph_driver.continue_provider_wired_run(run_dir, state, 1, "test")

    assert status == 0
    assert state_json(run_dir)["status"] == "STOPPED"


def test_g005_toy_campaign_still_completes(tmp_path, monkeypatch) -> None:
    copy_campaign(tmp_path, ralph_driver.TOY_CAMPAIGN_ID)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)

    status = ralph_driver.run_campaign(ralph_driver.TOY_CAMPAIGN_ID, None, "green")

    assert status == 0
    run_dir = latest_run(tmp_path, ralph_driver.TOY_CAMPAIGN_ID)
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    assert state["campaign_id"] == ralph_driver.TOY_CAMPAIGN_ID
    assert state["driver"] == "ralph_local_toy_v1"
    assert state["status"] == "COMPLETED"
    assert [phase["status"] for phase in state["phases"]] == ["PASS", "PASS", "PASS"]
    assert (tmp_path / "docs/toy_workflow2/phase_a.md").is_file()
    assert (tmp_path / "docs/toy_workflow2/phase_b.md").is_file()
    assert (tmp_path / "docs/toy_workflow2/summary.md").is_file()


def recipe_body(justfile_text: str, recipe_name: str) -> str:
    pattern = re.compile(rf"^{re.escape(recipe_name)}(?:\s[^:]*)?:\n((?:    .+\n)+)", re.MULTILINE)
    match = pattern.search(justfile_text)
    assert match is not None, recipe_name
    return match.group(1)


def test_just_command_semantics_are_provider_wired() -> None:
    text = (REPO_ROOT / "justfile").read_text(encoding="utf-8")

    run_campaign = recipe_body(text, "frontier-run-campaign")
    run_next = recipe_body(text, "frontier-run-next")
    run_mock = recipe_body(text, "frontier-run-campaign-mock")
    next_mock = recipe_body(text, "frontier-run-next-mock")
    ledger = recipe_body(text, "frontier-run-campaign-ledger")
    overnight = recipe_body(text, "frontier-run-overnight")
    heartbeat = recipe_body(text, "frontier-heartbeat")
    acceptance = recipe_body(text, "frontier-acceptance")

    assert "--provider-wired" in run_campaign
    assert "FRONTIER_MAX_PHASES=1" not in run_campaign
    assert "--provider-wired" in run_next
    assert "FRONTIER_MAX_PHASES=1" in run_next
    assert "FRONTIER_MOCK_PROVIDERS=1" in run_mock
    assert "--provider-wired" in run_mock
    assert "FRONTIER_MOCK_PROVIDERS=1" in next_mock
    assert "FRONTIER_MAX_PHASES=1" in next_mock
    assert "--ledger-only" in ledger
    assert "FRONTIER_RUN_MODE=overnight" in overnight
    assert "heartbeat.json" in heartbeat
    assert "tools/frontier/acceptance.py" in acceptance


def test_frontier_ci_installs_test_dependencies_and_handles_no_tests() -> None:
    workflow = (REPO_ROOT / ".github/workflows/frontier-ci.yml").read_text(encoding="utf-8")

    assert "python -m pip install pytest pyyaml jinja2" in workflow
    assert "find tests -type f" in workflow
    assert "python -m pytest" in workflow
    assert "No tests configured yet" in workflow


def test_ralph_driver_has_no_provider_or_network_imports() -> None:
    source = (REPO_ROOT / "tools/frontier/ralph_driver.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_roots = {
        "anthropic",
        "github",
        "ghapi",
        "httpx",
        "ibapi",
        "openai",
        "requests",
        "socket",
        "urllib",
        "urllib3",
        "webbrowser",
    }
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    assert forbidden_roots.isdisjoint(imported_roots)
