"""Frontier Workflow 2 state-machine constants."""

from __future__ import annotations

STATES = [
    "RUN_INIT",
    "CAMPAIGN_LOAD",
    "PHASE_SELECT",
    "SPEC_GENERATE",
    "SPEC_VALIDATE",
    "WORKTREE_CREATE",
    "CODEX_EXECUTE",
    "CHECKS_RUN",
    "HANDOFF_VALIDATE",
    "CLAUDE_REVIEW",
    "VERDICT_PARSE",
    "PR_CREATE",
    "CI_WAIT",
    "MERGE_GATE",
    "MERGE",
    "DONE_CHECK",
    "NEXT_PHASE",
    "CAMPAIGN_DONE_CHECK",
    "RUN_SUMMARY",
    "RUN_BLOCKED",
]

TERMINAL_STATES = {"RUN_SUMMARY", "RUN_BLOCKED"}


def is_terminal(state: str) -> bool:
    return state in TERMINAL_STATES
