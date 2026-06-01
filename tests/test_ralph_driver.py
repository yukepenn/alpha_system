from __future__ import annotations

import ast
import json
import shutil
from pathlib import Path

from tools.frontier import ralph_driver


REPO_ROOT = Path(__file__).resolve().parents[1]


def copy_campaign(tmp_root: Path, campaign_id: str) -> None:
    source = REPO_ROOT / "campaigns" / campaign_id
    target = tmp_root / "campaigns" / campaign_id
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)


def latest_run(tmp_root: Path, campaign_id: str) -> Path:
    matches = sorted((tmp_root / "runs").glob(f"*{campaign_id}*"))
    assert matches
    return matches[-1]


def pass_count(run_dir: Path) -> int:
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    return sum(1 for phase in state["phases"] if phase["status"] == "PASS")


def stub_validation(monkeypatch) -> None:
    monkeypatch.setattr(
        ralph_driver,
        "run_validation_commands",
        lambda: (True, "# Validation\n\nMock validation passed.\n"),
    )


def test_parse_asv1_phase_plan_extracts_all_alpha_system_v1_phases() -> None:
    campaign_dir = REPO_ROOT / "campaigns" / ralph_driver.ALPHA_SYSTEM_V1_CAMPAIGN_ID
    campaign_yaml = ralph_driver.load_campaign_yaml(ralph_driver.ALPHA_SYSTEM_V1_CAMPAIGN_ID, campaign_dir)
    phase_plan = (campaign_dir / "PHASE_PLAN.md").read_text(encoding="utf-8")

    phases = ralph_driver.parse_asv1_phase_plan(phase_plan, campaign_yaml)

    assert [phase.phase_id for phase in phases] == [f"ASV1-P{index:02d}" for index in range(30)]
    assert phases[0].name == "Repo and Harness Bootstrap Policy"
    assert phases[0].lane == "YELLOW"
    assert phases[0].dependencies == ()
    assert phases[6].dependencies == ("ASV1-P04", "ASV1-P05")
    assert phases[28].lane == "GREEN"
    assert phases[-1].phase_id == "ASV1-P29"


def test_alpha_system_v1_ledger_only_run_creates_required_artifacts(tmp_path, monkeypatch) -> None:
    copy_campaign(tmp_path, ralph_driver.ALPHA_SYSTEM_V1_CAMPAIGN_ID)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)

    status = ralph_driver.run_campaign(
        ralph_driver.ALPHA_SYSTEM_V1_CAMPAIGN_ID,
        None,
        "yellow",
        ledger_only=True,
    )

    assert status == 0
    run_dir = latest_run(tmp_path, ralph_driver.ALPHA_SYSTEM_V1_CAMPAIGN_ID)
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
    assert state["campaign_id"] == ralph_driver.ALPHA_SYSTEM_V1_CAMPAIGN_ID
    assert state["workflow"] == "workflow2"
    assert state["driver"] == ralph_driver.LEDGER_ONLY_DRIVER
    assert state["status"] == "LEDGER_ONLY_READY"
    assert state["current_phase_id"] is None
    assert state["stop_requested"] is False
    assert state["created_at"]
    assert len(state["phases"]) == 30
    assert state["phases"][0]["phase_id"] == "ASV1-P00"
    assert state["phases"][-1]["phase_id"] == "ASV1-P29"
    assert all(phase["status"] == "PENDING" for phase in state["phases"])
    assert all(phase["execution_mode"] == "ledger_only" for phase in state["phases"])
    assert all({"spec", "handoff", "review", "verdict"} <= set(phase["artifact_paths"]) for phase in state["phases"])
    assert state["phase_execution_performed"] is False
    assert state["external_providers_called"] is False
    assert state["network_used"] is False
    assert state["github_operations_performed"] is False
    assert state["auto_merge_performed"] is False
    assert state["broker_or_trading_operations_performed"] is False

    event_names = [
        json.loads(line)["event"]
        for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert event_names == ["RUN_INIT", "CAMPAIGN_LOAD", "PHASES_LEDGERED", "STOP_WRITTEN"]
    costs = [json.loads(line) for line in (run_dir / "costs.jsonl").read_text(encoding="utf-8").splitlines()]
    assert costs == [
        {
            "campaign_id": ralph_driver.ALPHA_SYSTEM_V1_CAMPAIGN_ID,
            "cost_usd": 0.0,
            "driver": ralph_driver.LEDGER_ONLY_DRIVER,
            "model": None,
            "note": "ledger_only_no_provider_calls",
            "provider": "none",
            "timestamp": costs[0]["timestamp"],
        }
    ]

    assert ralph_driver.resume(state["run_id"]) == 0
    resumed = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    assert resumed["status"] == "STOPPED"
    assert resumed["stop_requested"] is True
    assert all(phase["status"] == "PENDING" for phase in resumed["phases"])


def test_provider_wired_cli_max_phases_one_runs_exactly_one_mock_phase(tmp_path, monkeypatch) -> None:
    copy_campaign(tmp_path, ralph_driver.ALPHA_SYSTEM_V1_CAMPAIGN_ID)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.setenv("FRONTIER_MOCK_PROVIDERS", "1")
    monkeypatch.delenv("FRONTIER_MAX_PHASES", raising=False)
    stub_validation(monkeypatch)

    status = ralph_driver.main(
        [
            "run",
            "--campaign-id",
            ralph_driver.ALPHA_SYSTEM_V1_CAMPAIGN_ID,
            "--provider-wired",
            "--max-phases",
            "1",
        ]
    )

    assert status == 0
    run_dir = latest_run(tmp_path, ralph_driver.ALPHA_SYSTEM_V1_CAMPAIGN_ID)
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    assert state["driver"] == ralph_driver.PROVIDER_WIRED_DRIVER
    assert state["max_phases_requested"] == 1
    assert state["max_phases_source"] == "cli"
    assert state["status"] == "STOPPED"
    assert pass_count(run_dir) == 1
    assert state["phases"][0]["status"] == "PASS"
    assert state["phases"][1]["status"] == "PENDING"
    assert (run_dir / "STOP").is_file()
    assert (run_dir / "phases/ASV1-P00/spec_prompt.md").is_file()
    assert (run_dir / "phases/ASV1-P00/executor_output.md").is_file()
    assert (run_dir / "phases/ASV1-P00/validation.md").is_file()
    assert (run_dir / "phases/ASV1-P00/review.md").is_file()
    assert (run_dir / "phases/ASV1-P00/verdict.json").is_file()


def test_provider_wired_env_max_phases_one_runs_exactly_one_mock_phase(tmp_path, monkeypatch) -> None:
    copy_campaign(tmp_path, ralph_driver.ALPHA_SYSTEM_V1_CAMPAIGN_ID)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.setenv("FRONTIER_MOCK_PROVIDERS", "1")
    monkeypatch.setenv("FRONTIER_MAX_PHASES", "1")
    stub_validation(monkeypatch)

    status = ralph_driver.main(
        [
            "run",
            "--campaign-id",
            ralph_driver.ALPHA_SYSTEM_V1_CAMPAIGN_ID,
            "--provider-wired",
        ]
    )

    assert status == 0
    run_dir = latest_run(tmp_path, ralph_driver.ALPHA_SYSTEM_V1_CAMPAIGN_ID)
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    assert state["max_phases_requested"] == 1
    assert state["max_phases_source"] == "env"
    assert pass_count(run_dir) == 1


def test_provider_wired_default_mock_campaign_is_not_hard_coded_to_one_phase(tmp_path, monkeypatch) -> None:
    copy_campaign(tmp_path, ralph_driver.ALPHA_SYSTEM_V1_CAMPAIGN_ID)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.setenv("FRONTIER_MOCK_PROVIDERS", "1")
    monkeypatch.delenv("FRONTIER_MAX_PHASES", raising=False)
    stub_validation(monkeypatch)

    status = ralph_driver.run_campaign(
        ralph_driver.ALPHA_SYSTEM_V1_CAMPAIGN_ID,
        None,
        "yellow",
        provider_wired=True,
    )

    assert status == 0
    run_dir = latest_run(tmp_path, ralph_driver.ALPHA_SYSTEM_V1_CAMPAIGN_ID)
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    assert state["max_phases_source"] == "campaign"
    assert state["max_phases_requested"] == 30
    assert state["status"] == "COMPLETED"
    assert pass_count(run_dir) == 30
    assert (run_dir / "STOP").is_file()


def test_provider_wired_mock_can_advance_multiple_phases_with_limit(tmp_path, monkeypatch) -> None:
    copy_campaign(tmp_path, ralph_driver.ALPHA_SYSTEM_V1_CAMPAIGN_ID)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.setenv("FRONTIER_MOCK_PROVIDERS", "1")
    monkeypatch.delenv("FRONTIER_MAX_PHASES", raising=False)
    stub_validation(monkeypatch)

    status = ralph_driver.run_campaign(
        ralph_driver.ALPHA_SYSTEM_V1_CAMPAIGN_ID,
        None,
        "yellow",
        provider_wired=True,
        max_phases=3,
    )

    assert status == 0
    run_dir = latest_run(tmp_path, ralph_driver.ALPHA_SYSTEM_V1_CAMPAIGN_ID)
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    assert state["max_phases_requested"] == 3
    assert state["max_phases_source"] == "cli"
    assert pass_count(run_dir) == 3
    assert state["phases"][3]["status"] == "PENDING"


def test_provider_wired_resume_stop_prevents_further_execution(tmp_path, monkeypatch) -> None:
    copy_campaign(tmp_path, ralph_driver.ALPHA_SYSTEM_V1_CAMPAIGN_ID)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.setenv("FRONTIER_MOCK_PROVIDERS", "1")
    monkeypatch.delenv("FRONTIER_MAX_PHASES", raising=False)
    stub_validation(monkeypatch)

    status = ralph_driver.run_campaign(
        ralph_driver.ALPHA_SYSTEM_V1_CAMPAIGN_ID,
        None,
        "yellow",
        provider_wired=True,
        max_phases=1,
    )
    assert status == 0
    run_dir = latest_run(tmp_path, ralph_driver.ALPHA_SYSTEM_V1_CAMPAIGN_ID)
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))

    assert ralph_driver.resume(state["run_id"], provider_wired=True, max_phases=1) == 0

    resumed = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    assert pass_count(run_dir) == 1
    assert resumed["phases"][1]["status"] == "PENDING"


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
