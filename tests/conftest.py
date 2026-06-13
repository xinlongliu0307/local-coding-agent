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
