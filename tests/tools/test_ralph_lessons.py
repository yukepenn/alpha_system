"""Lessons must be injected into every Workflow 2 provider prompt.

Hard-won run-recovery knowledge lives in .claude/skills/project-skill/lessons.md;
these tests pin the wiring so it cannot silently regress to write-only.
"""

from __future__ import annotations

from pathlib import Path

from tools.frontier import ralph_driver


def test_lessons_section_reads_repo_lessons() -> None:
    section = ralph_driver.lessons_prompt_section()
    assert "Validated lessons from prior runs" in section
    assert "data, not policy" in section


def test_lessons_section_is_empty_when_file_missing(monkeypatch) -> None:
    monkeypatch.setattr(ralph_driver, "LESSONS_FILE", Path("/nonexistent/lessons.md"))
    assert ralph_driver.lessons_prompt_section() == ""


def test_all_provider_prompts_carry_lessons() -> None:
    phase = {"phase_id": "TEST-P00", "title": "test", "lane": "yellow", "dependencies": []}
    prompts = [
        ralph_driver.spec_generation_prompt(phase, "TEST_CAMPAIGN"),
        ralph_driver.executor_prompt(phase, "spec", ralph_driver.ROOT / "runs" / "x"),
        ralph_driver.review_prompt(phase, "TEST_CAMPAIGN", "spec", "exec", "validation"),
        ralph_driver.done_check_prompt(
            phase, "TEST_CAMPAIGN", "spec", "exec", "validation", "review", "PASS", "handoff"
        ),
        ralph_driver.repair_prompt(phase, "spec", "review", "validation"),
    ]
    for prompt in prompts:
        assert "Validated lessons from prior runs" in prompt
