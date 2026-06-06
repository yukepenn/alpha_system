"""Shared pytest fixtures for the alpha_system test suite.

Test hermeticity for Frontier env vars
--------------------------------------
The Frontier Workflow 2 driver runs the test suite (``python tools/verify.py
--all``) inside a subprocess that exports merge-arming environment variables
such as ``FRONTIER_CREATE_PR=1``, ``FRONTIER_ALLOW_AUTOMERGE=1`` and
``FRONTIER_MERGE_DRY_RUN=0`` (see the ``frontier-run*`` justfile recipes).

Several driver/github_utils unit tests assert *default-off* behaviour and read
those variables directly, so an ambient value silently flips the code under
test and turns ``verify.py --all`` into a false negative (this masqueraded as
"13 failed" during both the ALPHA_FEATURE_LABEL_FOUNDATION_V1 and
ALPHA_RESEARCH_RUNTIME_MVP campaign closeouts, while a clean-env run passed).

Clearing ``FRONTIER_*`` before every test makes the suite hermetic regardless of
how it is invoked. A test that needs one of these variables sets it explicitly
(``monkeypatch.setenv(...)``), which still wins because this autouse fixture runs
first during setup.
"""

from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def _isolate_frontier_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(os.environ):
        if key.startswith("FRONTIER_"):
            monkeypatch.delenv(key, raising=False)
