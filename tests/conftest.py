"""Shared pytest fixtures for the test suite."""

from __future__ import annotations

import pytest

from agent.workspace import set_workspace_root


@pytest.fixture
def workspace(tmp_path):
    """Set the agent's workspace root to this test's tmp_path.

    File tools confine operations to the workspace root. Tests that operate
    on tmp_path files must declare tmp_path as the root, or the confinement
    correctly refuses them. The root is reset after the test so the
    module-level state does not leak between tests.
    """
    set_workspace_root(str(tmp_path))
    yield tmp_path
    set_workspace_root(None)


from agent.loop import run_task as _run_task
from agent.mode import Mode


def run_task_quiet(task, model, **overrides):
    """Invoke run_task with all optional behaviours suppressed by default.

    Tests of core loop behaviour rarely want the summary, snapshot,
    reading-order declaration, or conversation condensation, and must
    otherwise disable each by hand. This helper defaults all of them off and
    runs non-verbosely, so a test states only what it cares about. Any
    default may be overridden by passing the corresponding keyword, e.g.
    include_summary=True for a test that asserts on the summary.

    A session must be supplied by the caller when one is needed, since the
    approval cadence is usually part of what a loop test is exercising; if no
    session is given, run_task constructs its default.
    """
    defaults = {
        "verbose": False,
        "include_summary": False,
        "enable_snapshot": False,
        "declare_reading_order": False,
        "enable_condensation": False,
    }
    defaults.update(overrides)
    return _run_task(task, model=model, **defaults)


import pytest


@pytest.fixture
def run_quiet():
    """Provide the run_task_quiet helper to tests as a fixture."""
    return run_task_quiet
